"""
multiverse_c66.py — Component 66: The Deploy Script.

Turns C64's LFS/0.1 checklist into a single call:
    fed = deploy_federation(DeployConfig(state_dir=..., ...))

What deploy_federation provisions:
  - Poetry World (signed, C13), served over HTTP (shim).
  - Chemistry World (signed, C13), served over HTTP.
  - Multiverse Registry (signed, C17), served over HTTP.
  - Genesis ledger (C62): three world manifests committed
    and signed by each world's key.
  - A signed tree head over the genesis ledger.
  - A signed anchors file (LFS/0.1 §7) in the state dir.
  - A root key file for the operator to publish out of band.

What it deliberately does NOT do (C64 §13, §15):
  - Install system services (systemd/docker is operator's job).
  - Configure DNS or TLS (operator's job; C64 §3 requires HTTPS).
  - Persist ledger state across restarts (v0.2 concern).
  - Multi-host (single process for the reference).
  - Publish the root key out of band (a human action).
  - Run curators (C55) as separate processes — v0.1 runs them
    implicitly by writing the anchors; explicit curator processes
    would be a v0.2 expansion.

Composition: C3, C4, C5, C6, C13, C17, C28, C62, C64, C65.

House rules honored:
  - "Every behaviour has a test that fails if the behaviour
    breaks" — one per: config validation, genesis commits,
    chain verify, checkpoint verify, anchors verify, registry
    admission, live manifests, client end-to-end, idempotency,
    clean shutdown, never-raises-on-bad-input.
  - "A world never raises on what a visitor sends" — deploy
    raises only on caller error; verifiers never raise.
  - "History, not rank" — genesis commits are factual.

Honest limits (documented, tested):
  - HTTP, not HTTPS. Production requires TLS (C64 §3).
  - Root key is written to disk in plaintext (prototype).
  - Single-writer ledger; no consensus.
  - Three genesis commits signed by the deploy, which holds
    the world keys. A production deploy with separated
    operators would need a different commit-authority model.
  - The C65 client has a manifest-verification discrepancy
    vs C28; C66 provides a corrected verifier and patches
    C65 for the demo. A C65 update should align with C28.
  - No persistence of server state to disk. Deploy is a
    scenario; restart loses the running worlds.
"""

import hashlib
import json
import time
import urllib.request
import urllib.error
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from multiverse_c3 import Act, Ack, Refusal
from multiverse_c4 import PoetryWorld
from multiverse_c5 import ChemistryWorld
from multiverse_c13 import (
    HAS_CRYPTO, KeyPair, SignedWorld,
    canonical_bytes, verify_signature,
)
from multiverse_c17 import SignedMultiverseRegistry
from multiverse_c28 import SignedManifestWorld
from multiverse_c62 import (
    CommitmentLog, CommitmentRecord, CheckpointPublisher,
    SignedTreeHead, verify_commitment_chain, verify_tree_head,
    _hash_payload,
)
from multiverse_c65 import (
    _keypair_to_hex,
    _verify_anchors_signature,
)
from wcp_http_shim import WorldProtocolServer


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


# =====================================================================
# Small corrections to C65 (temporary, pending a C65 update)
# =====================================================================

def _verify_signed_manifest_dict(
    manifest: Dict, expected_public_key: str,
) -> bool:
    """Correct C28 SignedManifest verification.

    C65's `_verify_manifest_matches_anchors` reconstructs the
    canonical bytes without the "kind" field C28 signs over.
    This helper does the correct verification. A future C65
    update should align with C28 and remove this helper.
    """
    if not HAS_CRYPTO:
        return False
    try:
        sig = manifest.get("signature")
        if not isinstance(sig, str) or not sig:
            return False
        payload = canonical_bytes({
            "kind": "signed_manifest",
            "entity_id": manifest["entity_id"],
            "name": manifest["name"],
            "protocol_version": manifest["protocol_version"],
            "law_url": manifest["law_url"],
            "act_endpoint": manifest["act_endpoint"],
            "log_endpoint": manifest["log_endpoint"],
            "sub_registry_endpoint":
                manifest.get("sub_registry_endpoint"),
            "public_key": manifest["public_key"],
            "signed_by": manifest["signed_by"],
        })
        return verify_signature(
            expected_public_key, payload, sig)
    except Exception:
        return False


def _patch_c65_manifest_verification() -> None:
    """Temporary fix for C65. See module docstring honest limits."""
    import multiverse_c65 as c65

    def _patched(self, world_id, manifest):
        if manifest.get("entity_id") != world_id:
            return (False,
                    f"manifest entity_id "
                    f"{manifest.get('entity_id')!r} != "
                    f"{world_id!r}")
        if isinstance(manifest.get("signature"), str) \
                and manifest["signature"]:
            world_key = self.state.anchors.world_public_key(world_id)
            if world_key is None:
                return (False, "world not in anchors")
            ok = _verify_signed_manifest_dict(manifest, world_key)
            if not ok:
                return (False, "manifest signature INVALID")
        return (True, "manifest matches anchors")

    c65.FederationClient._verify_manifest_matches_anchors = _patched


# =====================================================================
# Delegating signed world
# =====================================================================

class _DelegatingSignedWorld(SignedWorld):
    """SignedWorld that delegates unknown attributes to its base.

    Needed so `.manifest()` works when this wrapper is served or
    cataloged (SignedWorld doesn't define it, but C4's base world
    does). A future C13 update might add this delegation
    directly; until then, this small subclass closes the gap.
    """
    def __getattr__(self, name):
        return getattr(self.base, name)


# =====================================================================
# DeployConfig / DeployedFederation
# =====================================================================

@dataclass(frozen=True)
class DeployConfig:
    state_dir: Path
    federation_name: str
    poetry_port: int = 0
    chemistry_port: int = 0
    registry_port: int = 0


@dataclass
class DeployedFederation:
    config: DeployConfig
    root_kp: KeyPair
    poetry_kp: KeyPair
    chemistry_kp: KeyPair
    registry_kp: KeyPair
    checkpoint_kp: KeyPair
    poetry_server: Any
    chemistry_server: Any
    registry_server: Any
    poetry: Any
    chemistry: Any
    registry: Any
    ledger: CommitmentLog
    genesis_commits: List[CommitmentRecord]
    checkpoint: SignedTreeHead
    anchors_path: Path
    checkpoint_path: Path
    ledger_log_path: Path
    root_key_path: Path
    poetry_url: str
    chemistry_url: str
    registry_url: str

    def anchors_url(self) -> str:
        return f"file://{self.anchors_path.resolve()}"

    def world_key(self, world_id: str) -> Optional[KeyPair]:
        return {
            "world:poetry": self.poetry_kp,
            "world:chemistry": self.chemistry_kp,
            "multiverse:main": self.registry_kp,
        }.get(world_id)

    def commit_artifact(
        self, artifact_hash: str, artifact_kind: str,
        committer_world_id: str,
    ) -> CommitmentRecord:
        """Operator commits an artifact on behalf of a world.
        Uses the world's key (which the deploy holds). Production
        with separated operators would need a different model.
        """
        kp = self.world_key(committer_world_id)
        if kp is None:
            raise ValueError(
                f"unknown world {committer_world_id!r}")
        rec = self.ledger.append(
            artifact_hash=artifact_hash,
            artifact_kind=artifact_kind,
            committer_world_id=committer_world_id,
            committer_kp=kp,
        )
        with open(self.ledger_log_path, "a") as f:
            f.write(json.dumps(rec.to_dict()) + "\n")
        return rec

    def sign_new_checkpoint(self) -> SignedTreeHead:
        publisher = CheckpointPublisher(
            self.ledger, self.checkpoint_kp)
        head = publisher.publish()
        self.checkpoint_path.write_text(
            json.dumps(head.to_dict(), indent=2))
        self.checkpoint = head
        return head

    def stop(self) -> None:
        for srv in (self.poetry_server, self.chemistry_server,
                    self.registry_server):
            try:
                srv.stop()
            except Exception:
                pass


def _post(url: str, body: Dict) -> Dict:
    req = urllib.request.Request(
        url, data=json.dumps(body).encode(),
        headers={"Content-Type": "application/json"},
        method="POST")
    with urllib.request.urlopen(req, timeout=10) as r:
        return json.loads(r.read().decode())


# =====================================================================
# deploy_federation
# =====================================================================

def deploy_federation(config: DeployConfig) -> DeployedFederation:
    if not HAS_CRYPTO:
        raise RuntimeError(
            "deploy_federation requires `cryptography`")
    if not isinstance(config, DeployConfig):
        raise TypeError("config must be a DeployConfig")
    state_dir = Path(config.state_dir)
    if state_dir.exists() and any(state_dir.iterdir()):
        raise RuntimeError(
            f"state dir not empty: {state_dir}")
    state_dir.mkdir(parents=True, exist_ok=True)

    # 1. Keys
    root_kp = KeyPair.generate()
    poetry_kp = KeyPair.generate()
    chemistry_kp = KeyPair.generate()
    registry_kp = KeyPair.generate()
    checkpoint_kp = KeyPair.generate()

    # 2. Worlds and servers
    poetry = SignedManifestWorld(
        _DelegatingSignedWorld(
            PoetryWorld("world:poetry", "The Poetry World"),
            poetry_kp),
        poetry_kp)
    poetry_server = WorldProtocolServer(poetry, port=config.poetry_port)
    poetry_server.serve_in_thread()

    chemistry = SignedManifestWorld(
        _DelegatingSignedWorld(
            ChemistryWorld("world:chemistry", "The Chemistry World"),
            chemistry_kp),
        chemistry_kp)
    chemistry_server = WorldProtocolServer(
        chemistry, port=config.chemistry_port)
    chemistry_server.serve_in_thread()

    registry = SignedMultiverseRegistry(
        "multiverse:main", "Main Multiverse", registry_kp)
    registry_server = WorldProtocolServer(
        registry, port=config.registry_port)
    registry_server.serve_in_thread()

    time.sleep(0.2)
    poetry_url = (f"http://127.0.0.1:"
                  f"{poetry_server._httpd.server_address[1]}")
    chemistry_url = (f"http://127.0.0.1:"
                     f"{chemistry_server._httpd.server_address[1]}")
    registry_url = (f"http://127.0.0.1:"
                    f"{registry_server._httpd.server_address[1]}")

    try:
        # 3. Admit worlds to the registry (in-process)
        admin_token = (
            f"admin:deploy:"
            f"{checkpoint_kp.public_key_hex()[:16]}")
        _post(f"{registry_url}/petition", {
            "petitioner_token": admin_token,
            "petitioner_name": "Deploy Admin",
            "passport_admissions": [],
            "message": "deploy",
        })
        for world in (poetry, chemistry):
            resp = _post(f"{registry_url}/act", {
                "actor_token": admin_token,
                "type": "multiverse.admit",
                "payload": {"entity": world},
            })
            if resp.get("kind") != "ack":
                raise RuntimeError(
                    f"registry refused admission: {resp}")

        # 4. Genesis ledger
        ledger = CommitmentLog()
        genesis: List[CommitmentRecord] = []
        for world_id, world_kp, manifest in (
            ("world:poetry", poetry_kp,
             poetry.manifest_dict()),
            ("world:chemistry", chemistry_kp,
             chemistry.manifest_dict()),
            ("multiverse:main", registry_kp,
             registry.manifest_dict()),
        ):
            manifest_hash = _hash_payload(
                canonical_bytes(manifest))
            rec = ledger.append(
                artifact_hash=manifest_hash,
                artifact_kind="signed_manifest",
                committer_world_id=world_id,
                committer_kp=world_kp,
            )
            genesis.append(rec)
        checkpoint = CheckpointPublisher(
            ledger, checkpoint_kp).publish()

        # 5. Persist ledger and checkpoint
        ledger_log_path = state_dir / "ledger.jsonl"
        with open(ledger_log_path, "w") as f:
            for r in ledger.entries():
                f.write(json.dumps(r.to_dict()) + "\n")

        checkpoint_path = state_dir / "checkpoint.json"
        checkpoint_path.write_text(
            json.dumps(checkpoint.to_dict(), indent=2))

        # 6. Anchors
        anchors_body = {
            "kind": "federation_trust_anchors",
            "version": "LFS/0.1",
            "federation_name": config.federation_name,
            "published_at": _now(),
            "ledger_checkpoint_public_key":
                checkpoint_kp.public_key_hex(),
            "worlds": [
                {"entity_id": "world:poetry",
                 "manifest_url": f"{poetry_url}/manifest",
                 "curator_public_key":
                     poetry_kp.public_key_hex(),
                 "curator_world": "curator:poetry"},
                {"entity_id": "world:chemistry",
                 "manifest_url": f"{chemistry_url}/manifest",
                 "curator_public_key":
                     chemistry_kp.public_key_hex(),
                 "curator_world": "curator:chemistry"},
                {"entity_id": "multiverse:main",
                 "manifest_url": f"{registry_url}/manifest",
                 "curator_public_key":
                     registry_kp.public_key_hex(),
                 "curator_world": "curator:main"},
            ],
        }
        anchors_sig = root_kp.sign(
            canonical_bytes(anchors_body)).hex()
        anchors = dict(anchors_body)
        anchors["signature"] = anchors_sig
        anchors_path = state_dir / "anchors.json"
        anchors_path.write_text(
            json.dumps(anchors, indent=2))

        # 7. Root key file (prototype: plaintext)
        root_key_path = state_dir / "root_key.json"
        root_key_path.write_text(json.dumps({
            "public_key_hex": root_kp.public_key_hex(),
            "private_key_hex": _keypair_to_hex(root_kp),
            "note": (
                "PROTOTYPE: publish public_key_hex out of band; "
                "keep private_key_hex secure"),
        }, indent=2))

        return DeployedFederation(
            config=config,
            root_kp=root_kp,
            poetry_kp=poetry_kp,
            chemistry_kp=chemistry_kp,
            registry_kp=registry_kp,
            checkpoint_kp=checkpoint_kp,
            poetry_server=poetry_server,
            chemistry_server=chemistry_server,
            registry_server=registry_server,
            poetry=poetry,
            chemistry=chemistry,
            registry=registry,
            ledger=ledger,
            genesis_commits=genesis,
            checkpoint=checkpoint,
            anchors_path=anchors_path,
            checkpoint_path=checkpoint_path,
            ledger_log_path=ledger_log_path,
            root_key_path=root_key_path,
            poetry_url=poetry_url,
            chemistry_url=chemistry_url,
            registry_url=registry_url,
        )
    except Exception:
        for srv in (poetry_server, chemistry_server,
                    registry_server):
            try:
                srv.stop()
            except Exception:
                pass
        raise


# =====================================================================
# Demo
# =====================================================================

def demo(artifact_dir: Optional[str] = None) -> Dict:
    """Full LFS/0.1 scenario from C64 §8:

    1. Deploy: three worlds, genesis ledger, signed anchors.
    2. Alice joins via C65 client: connect, enter, act in both.
    3. Operator commits Alice's acks to the ledger.
    4. Operator signs a new checkpoint.
    5. Alice produces a report; third party verifies.
    """
    import json as _json
    from pathlib import Path
    from multiverse_c65 import FederationClient, verify_report

    if not HAS_CRYPTO:
        raise RuntimeError("demo requires `cryptography`")

    _patch_c65_manifest_verification()

    if artifact_dir is None:
        artifact_dir = "artifacts"
    root_dir = Path(artifact_dir) / "deploy"
    root_dir.mkdir(parents=True, exist_ok=True)
    fed_dir = root_dir / "federation"
    client_dir = root_dir / "alice"
    if fed_dir.exists():
        import shutil
        shutil.rmtree(fed_dir)
    if client_dir.exists():
        import shutil
        shutil.rmtree(client_dir)

    # ---- 1. Deploy -------------------------------------------
    fed = deploy_federation(DeployConfig(
        state_dir=fed_dir,
        federation_name="Poetry-Chemistry Federation",
    ))
    try:
        genesis_chain = verify_commitment_chain(fed.ledger.entries())
        genesis_head_ok = verify_tree_head(
            fed.checkpoint, fed.checkpoint_kp.public_key_hex())
        anchors_raw = _json.loads(fed.anchors_path.read_text())
        anchors_ok = _verify_anchors_signature(
            anchors_raw, fed.root_kp.public_key_hex())

        # ---- 2. Client join ----------------------------------
        client = FederationClient(client_dir)
        alice = client.create_identity("Alice")
        connect = client.connect(
            fed.anchors_url(), fed.root_kp.public_key_hex())
        enter_poetry = client.enter_world("world:poetry")
        poem_act = client.submit_act(
            "world:poetry", "poem.turn", {
                "acknowledgment": "(seed)",
                "proposal":
                    "The Brain is wider than the Sky",
                "invitation": "What is the Sky to the Brain?",
                "holds_open": True,
            })
        enter_chem = client.enter_world("world:chemistry")
        chem_act = client.submit_act(
            "world:chemistry", "chemistry.react", {
                "substrates": [
                    {"formula": "H2", "count": 2},
                    {"formula": "O2", "count": 1},
                ],
                "products": [{"formula": "H2O", "count": 2}],
            })

        # ---- 3. Operator commits Alice's acks ---------------
        committed = 0
        for entry in client.state.get_log():
            if entry.get("kind") != "submit_act":
                continue
            d = entry.get("data", {})
            if not d.get("ok") or not d.get("response"):
                continue
            resp = d["response"]
            world_id = d["world_id"]
            ack_hash = _hash_payload(canonical_bytes({
                "kind": "ack",
                "entity_id": resp["entity_id"],
                "timestamp": resp["timestamp"],
                "subject_token": resp["subject_token"],
                "signature": resp["signature"],
            }))
            fed.commit_artifact(
                ack_hash, "signed_ack", world_id)
            committed += 1
        new_checkpoint = fed.sign_new_checkpoint()
        new_checkpoint_ok = verify_tree_head(
            new_checkpoint,
            fed.checkpoint_kp.public_key_hex())

        # ---- 4. Client report + third-party verify ----------
        verify_verdict = client.verify_state()
        report = client.build_report()
        report_path = root_dir / "alice_report.json"
        report.save(report_path)
        loaded = _json.loads(report_path.read_text())
        from multiverse_c65 import FederationReport
        third_party = verify_report(
            FederationReport.from_dict(loaded),
            fed.root_kp.public_key_hex())

        # ---- Print --------------------------------------
        print("=" * 70)
        print("Deploy — C64's LFS/0.1 scenario, executable")
        print("=" * 70)
        print()
        print(f"  Federation: {fed.config.federation_name}")
        print(f"  State dir:  {fed_dir}")
        print(f"  Anchors:    {fed.anchors_path}")
        print()
        print("  Three worlds (each with signed manifest):")
        print(f"    Poetry    {fed.poetry_url}")
        print(f"    Chemistry {fed.chemistry_url}")
        print(f"    Registry  {fed.registry_url}")
        print()
        print("  Deploy checks:")
        print(f"    Genesis chain valid:      "
              f"{genesis_chain.valid}")
        print(f"    Genesis head signed:      "
              f"{genesis_head_ok}")
        print(f"    Anchors signed by root:   {anchors_ok}")
        print(f"    Registry lists:           "
              f"{sorted(fed.registry.entity_ids())}")
        print(f"    Genesis commits:          "
              f"{len(fed.genesis_commits)}")
        print()
        print("  Alice (via reference client):")
        print(f"    Identity:                 "
              f"{alice.identity.token[:16]}...")
        print(f"    Connect:                  {connect.ok}")
        print(f"    Enter poetry:             "
              f"{enter_poetry.ok} "
              f"(verified={enter_poetry.verified})")
        print(f"    Submit poem:              "
              f"{poem_act.ok} "
              f"(verified={poem_act.verified})")
        print(f"    Enter chemistry:          "
              f"{enter_chem.ok} "
              f"(verified={enter_chem.verified})")
        print(f"    Submit reaction:          "
              f"{chem_act.ok} "
              f"(verified={chem_act.verified})")
        print()
        print("  Operator commits acks to ledger:")
        print(f"    Committed:                {committed}")
        print(f"    New checkpoint signed:    {new_checkpoint_ok}")
        print(f"    Ledger size:              {fed.ledger.size()}")
        print(f"    Chain still valid:        "
              f"{verify_commitment_chain(fed.ledger.entries()).valid}")
        print()
        print("  Alice's report:")
        print(f"    Self-verify:              "
              f"{verify_verdict.valid}")
        print(f"    Third-party verify:       "
              f"{third_party.valid}")
        print(f"    Report:                   {report_path}")
        print()
        print("  What this demonstrates:")
        print("    - C64's LFS/0.1 checklist is one function call.")
        print("    - Three signed worlds + signed registry + signed")
        print("      genesis ledger + signed anchors, all from one")
        print("      deploy invocation.")
        print("    - The reference client (C65) works end-to-end")
        print("      against a freshly deployed federation.")
        print("    - The operator can commit new artifacts and sign")
        print("      new checkpoints, extending the ledger without")
        print("      invalidating prior entries.")
        print("    - A third party with the root key verifies Alice's")
        print("      report without contacting the federation.")
        print()
        print("  Anchor (public domain, Emily Dickinson):")
        print("    'The Brain – is wider than the Sky –'")
        print("    'For – put them side by side –'")

        audit = {
            "federation_name": fed.config.federation_name,
            "state_dir": str(fed_dir),
            "anchors_path": str(fed.anchors_path),
            "checkpoint_path": str(fed.checkpoint_path),
            "ledger_log_path": str(fed.ledger_log_path),
            "deploy_checks": {
                "genesis_chain_valid": genesis_chain.valid,
                "genesis_head_signed": genesis_head_ok,
                "anchors_signed": anchors_ok,
                "registry_entity_ids":
                    sorted(fed.registry.entity_ids()),
                "genesis_commit_count":
                    len(fed.genesis_commits),
            },
            "client": {
                "identity_token": alice.identity.token,
                "connect_ok": connect.ok,
                "enter_poetry_ok": enter_poetry.ok,
                "enter_poetry_verified": enter_poetry.verified,
                "act_poetry_ok": poem_act.ok,
                "act_poetry_verified": poem_act.verified,
                "enter_chemistry_ok": enter_chem.ok,
                "enter_chemistry_verified": enter_chem.verified,
                "act_chemistry_ok": chem_act.ok,
                "act_chemistry_verified": chem_act.verified,
            },
            "operator": {
                "committed": committed,
                "new_checkpoint_signed": new_checkpoint_ok,
                "ledger_size": fed.ledger.size(),
                "chain_valid_after":
                    verify_commitment_chain(
                        fed.ledger.entries()).valid,
            },
            "report": {
                "self_verify": verify_verdict.valid,
                "third_party_verify": third_party.valid,
                "path": str(report_path),
            },
        }
        (root_dir / "deploy_demo.json").write_text(
            _json.dumps(audit, indent=2))
        print(f"\n  → {root_dir}/deploy_demo.json")
        return audit
    finally:
        fed.stop()

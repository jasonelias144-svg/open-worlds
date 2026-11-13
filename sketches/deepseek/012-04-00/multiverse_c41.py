"""
multiverse_c41.py — Component 41: The Octopus Architecture.

A multi-model cross-world AI architecture modeled on the octopus
nervous system.

Biology → C41:
  Central brain (1/3 neurons)     → HigherOrderController
  Per-arm mini-brain (2/3)        → Per-arm model backends
  High-level commands             → Intent
  Efference copy                  → ArmReport
  Reflexes (no brain round-trip)  → Arm.local_reflex()
  Distributed coordination        → Per-epoch cross-world attestation

Not a swarm. A swarm is many identical units + local rules →
emergent behavior. The octopus is one brain + many *specialized*
arms + hierarchical coordination. Different architecture, different
properties. Swarm is future work (C42 candidate).

House rules honored:
  - "Every behaviour has a test that fails if the behaviour
    breaks" — one per: arm produces report, arm reflex, brain
    issues intent, brain closes epoch, missing arm, arm
    independence, attestation chaining.
  - "A world never raises on what a visitor sends" — Arm.tick
    never raises; a bad intent yields a refusal-report. Brain
    functions return None or partial results, never raise.
  - "History, not rank" — each epoch's attestation is a record,
    not a score.

Honest limits (documented, tested):
  - The demo's models are MeteredMockBackends (C18). They
    produce structured outputs; swapping in HFBackend is a one-
    line change with no architectural impact.
  - No true parallelism. `run_epoch` calls arms sequentially;
    a production implementation would use threads or async.
    The *architecture* is parallel (no arm depends on another);
    the demo is serial for readability.
  - Attestation chaining is via claim content (prior hash),
    not via a signed DAG of attestations. The prototype's
    chaining is honest but light; a full chain-of-attestations
    (C25's pattern) is future work.
  - Brain trust anchor external. Verifying against the person's
    key requires trusting that key. Same as everywhere.
"""

import hashlib
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Callable, Dict, List, Optional

from multiverse_c1 import Identity, create_identity
from multiverse_c13 import (
    HAS_CRYPTO, KeyPair, canonical_bytes, verify_signature,
)
from multiverse_c15 import PassportEntry
from multiverse_c21 import ProvenanceReport, EntryProvenance
from multiverse_c24 import SignedProvenanceReport, sign_report
from multiverse_c27 import AttestedDAG, DAGLink
from multiverse_c34 import ExtendedDAGBuilder
from multiverse_c36 import PersonIdentity
from multiverse_c40 import (
    WorldAttestationRef, CrossWorldClaim,
    CrossWorldPersonAttestation,
    create_cross_world_attestation,
    verify_cross_world_attestation,
    CrossWorldVerdict,
)


def _hash_payload(p: bytes) -> str:
    return hashlib.sha256(p).hexdigest()


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


# =====================================================================
# Intent and ArmReport
# =====================================================================

@dataclass(frozen=True)
class Intent:
    """The brain's high-level directive to an arm.

    A direction, not a command. The octopus brain says "reach
    toward the fish"; the arm figures out the motor pattern.
    Here the brain says "compose on 'Brain is wider than sky'";
    the model in the arm figures out the poem.
    """
    target_arm: str
    kind: str
    content: Dict
    epoch: int
    issued_at: str

    def to_dict(self) -> Dict:
        return {
            "target_arm": self.target_arm,
            "kind": self.kind,
            "content": self.content,
            "epoch": self.epoch,
            "issued_at": self.issued_at,
        }


@dataclass
class ArmReport:
    """An arm's report back to the brain.

    The report carries the DAG link the arm has already signed.
    The brain doesn't need to verify the arm's work — it just
    references the link hash in the epoch's attestation.
    """
    arm_name: str
    epoch: int
    world_id: str
    dag_id: str
    link_hash: str
    dag: AttestedDAG
    content_summary: Dict
    timestamp: str

    def to_summary(self) -> Dict:
        return {
            "arm_name": self.arm_name,
            "epoch": self.epoch,
            "world_id": self.world_id,
            "dag_id": self.dag_id,
            "link_hash": self.link_hash,
            "content_summary": self.content_summary,
            "timestamp": self.timestamp,
        }


# =====================================================================
# Arm
# =====================================================================

class Arm:
    """One arm of the octopus.

    Has its own model backend, its own signing keys, and produces
    one signed DAG per epoch it acts. Independent of every other
    arm — no shared state, no coordination.
    """

    def __init__(
        self,
        name: str,
        world_id: str,
        dag_id: str,
        model_backend,           # has .generate(prompt) → text
        arm_report_kp: KeyPair,
        arm_report_identity: Identity,
        arm_dag_kp: KeyPair,
        arm_dag_identity: Identity,
    ):
        self.name = name
        self.world_id = world_id
        self.dag_id = dag_id
        self._model = model_backend
        self._report_kp = arm_report_kp
        self._report_identity = arm_report_identity
        self._dag_kp = arm_dag_kp
        self._dag_identity = arm_dag_identity
        self._intent_queue: List[Intent] = []

    def receive_intent(self, intent: Intent) -> None:
        self._intent_queue.append(intent)

    def tick(self, epoch: int) -> Optional[ArmReport]:
        """Process queued intents. Return an ArmReport, or None if
        there was no work. Never raises."""
        if not self._intent_queue:
            return None
        intents = list(self._intent_queue)
        self._intent_queue.clear()
        try:
            content_entries = self._run_model(intents)
        except Exception as e:
            return self._make_report(
                epoch, content_entries=[],
                summary={"kind": "error", "error": str(e)})
        return self._make_report(
            epoch,
            content_entries=content_entries,
            summary={"kind": "work",
                     "intent_count": len(intents),
                     "entry_count": len(content_entries)})

    def local_reflex(self, epoch: int, stimulus: Dict) -> ArmReport:
        """Respond to a local stimulus without brain involvement.

        Like the octopus arm curling away from heat: no brain
        round-trip. The report goes into the brain's buffer for
        the *next* epoch close.
        """
        content_entries = [{
            "stimulus": stimulus,
            "output": f"reflex:{self.name}",
        }]
        return self._make_report(
            epoch,
            content_entries=content_entries,
            summary={"kind": "reflex",
                     "stimulus_kind": stimulus.get("kind", "")})

    def _run_model(self, intents: List[Intent]) -> List[Dict]:
        entries = []
        for intent in intents:
            # The model is asked with a simple prompt. Real backends
            # (HFBackend) would use structured prompts; the mock
            # produces poetry-shaped output. The interface is the
            # same.
            output = self._model.generate(
                f"{intent.kind}: {intent.content}")
            entries.append({
                "intent": intent.to_dict(),
                "output": output,
            })
        return entries

    def _make_report(self, epoch: int,
                     content_entries: List[Dict],
                     summary: Dict) -> ArmReport:
        # Build the ProvenanceReport (stub entries; the DAG link is
        # what's cryptographically verified — see C27/C40 docs)
        report = ProvenanceReport(
            passport_token=self._report_identity.token,
            passport_name=self._report_identity.name,
            registry_url=f"http://{self.name}.example/registry",
        )
        for ce in content_entries:
            entry = PassportEntry(
                entity_id=self.world_id,
                timestamp=_now(),
                subject_token=self._report_identity.token,
                signature="cc" * 64,  # placeholder
            )
            ep = EntryProvenance(entry=entry)
            ep.verdict = "verified"
            ep.reason = summary.get("kind", "work")
            report.entries.append(ep)
        signed = sign_report(
            report, self._report_kp, self._report_identity)
        # Build the DAG with one link (root). The link binds the
        # report hash; the brain references the link hash.
        builder = ExtendedDAGBuilder(signed)
        root = builder.attest(self._dag_kp, self._dag_identity)
        dag = builder.build()
        return ArmReport(
            arm_name=self.name,
            epoch=epoch,
            world_id=self.world_id,
            dag_id=self.dag_id,
            link_hash=root.link_hash(),
            dag=dag,
            content_summary=summary,
            timestamp=_now(),
        )


# =====================================================================
# HigherOrderController (the brain)
# =====================================================================

class HigherOrderController:
    """The brain. Issues intents, receives reports, closes epochs."""

    def __init__(self, person: PersonIdentity, person_kp: KeyPair):
        if not HAS_CRYPTO:
            raise RuntimeError(
                "HigherOrderController requires `cryptography`")
        if person_kp.public_key_hex() != person.person_public_key:
            raise ValueError(
                "keypair does not match person.person_public_key")
        self._person = person
        self._person_kp = person_kp
        self._reports_by_epoch: Dict[int, List[ArmReport]] = {}
        self._intents_by_epoch: Dict[int, List[Intent]] = {}
        self._attestations_by_epoch: Dict[
            int, CrossWorldPersonAttestation] = {}

    @property
    def person(self) -> PersonIdentity:
        return self._person

    def issue_intent(self, target_arm: str, kind: str,
                     content: Dict, epoch: int) -> Intent:
        """Produce an Intent. Delivering it to the arm is the
        caller's job (usually Octopus.run_epoch). The brain does
        not deliver; it only issues."""
        intent = Intent(
            target_arm=target_arm, kind=kind, content=content,
            epoch=epoch, issued_at=_now(),
        )
        self._intents_by_epoch.setdefault(epoch, []).append(intent)
        return intent

    def receive_report(self, report: ArmReport) -> None:
        self._reports_by_epoch.setdefault(
            report.epoch, []).append(report)

    def close_epoch(
        self, epoch: int, expected_arms: set,
    ) -> Optional[CrossWorldPersonAttestation]:
        """Sign a cross-world attestation over this epoch's reports.

        Returns None if fewer than 2 arms reported (a cross-world
        attestation with 1 reference is not coordination — see
        C40's CrossWorldClaim validation).

        Never raises.
        """
        reports = self._reports_by_epoch.get(epoch, [])
        if len(reports) < 2:
            return None

        refs = tuple(
            WorldAttestationRef(
                world_id=r.world_id,
                dag_id=r.dag_id,
                link_hash=r.link_hash,
                purpose=(f"{r.arm_name} epoch {epoch}: "
                         f"{r.content_summary.get('kind', 'work')}"),
            )
            for r in reports
        )
        reported_arms = {r.arm_name for r in reports}
        missing = expected_arms - reported_arms

        # Attestation chaining via content (prior hash)
        prior_hash: Optional[str] = None
        if epoch > 0:
            prior = self._attestations_by_epoch.get(epoch - 1)
            if prior is not None:
                prior_hash = _hash_payload(
                    prior.canonical_payload())

        claim = CrossWorldClaim(
            kind="octopus-epoch",
            content={
                "epoch": epoch,
                "octopus_name": self._person.person.name,
                "reported_arms": sorted(reported_arms),
                "missing_arms": sorted(missing),
                "prior_attestation_hash": prior_hash,
            },
            references=refs,
        )
        try:
            attestation = create_cross_world_attestation(
                self._person, self._person_kp, claim)
        except Exception:
            return None
        self._attestations_by_epoch[epoch] = attestation
        return attestation

    def attestations(self) -> List[CrossWorldPersonAttestation]:
        return [self._attestations_by_epoch[e]
                for e in sorted(self._attestations_by_epoch)]


# =====================================================================
# Octopus — the wiring
# =====================================================================

@dataclass
class EpochResult:
    epoch: int
    reports: List[ArmReport]
    attestation: Optional[CrossWorldPersonAttestation]
    missing_arms: List[str]

    def format(self) -> str:
        lines = [
            f"Epoch {self.epoch}",
            "=" * 50,
            f"  reports:   {len(self.reports)}",
        ]
        for r in self.reports:
            lines.append(
                f"    · {r.arm_name:10s} "
                f"({r.content_summary.get('kind', '?')}, "
                f"{r.content_summary.get('entry_count', '?')} "
                f"entries)")
        if self.missing_arms:
            lines.append(
                f"  missing:   {', '.join(self.missing_arms)}")
        if self.attestation is not None:
            lines.append(
                f"  attestation: signed "
                f"({len(self.attestation.claim.references)} refs)")
        else:
            lines.append(
                "  attestation: none (fewer than 2 arms reported)")
        return "\n".join(lines)


class Octopus:
    """The full system: arms + brain + coordination."""

    def __init__(self, name: str,
                 person: PersonIdentity, person_kp: KeyPair):
        self.name = name
        self._brain = HigherOrderController(person, person_kp)
        self._arms: Dict[str, Arm] = {}
        self._epoch = 0

    @property
    def brain(self) -> HigherOrderController:
        return self._brain

    def add_arm(self, arm: Arm) -> None:
        self._arms[arm.name] = arm

    def arm_names(self) -> List[str]:
        return list(self._arms.keys())

    def run_epoch(
        self,
        intents_per_arm: Dict[str, List[Dict]],
        reflexes: Optional[Dict[str, Dict]] = None,
    ) -> EpochResult:
        """One epoch.

        1. Brain issues intents.
        2. Arms tick (independently — see note about parallelism).
        3. Optional reflexes act without brain involvement.
        4. Brain closes epoch.
        """
        epoch = self._epoch
        self._epoch += 1

        # 1. Brain issues intents
        for arm_name, specs in intents_per_arm.items():
            for spec in specs:
                intent = self._brain.issue_intent(
                    target_arm=arm_name,
                    kind=spec.get("kind", "work"),
                    content=spec.get("content", {}),
                    epoch=epoch,
                )
                if arm_name in self._arms:
                    self._arms[arm_name].receive_intent(intent)

        # 2. Arms tick. Order doesn't matter: no arm depends on
        # another. Production would parallelize this loop.
        reports: List[ArmReport] = []
        for arm in self._arms.values():
            r = arm.tick(epoch)
            if r is not None:
                self._brain.receive_report(r)
                reports.append(r)

        # 3. Reflexes: no intent, arm acts alone
        if reflexes:
            for arm_name, stimulus in reflexes.items():
                arm = self._arms.get(arm_name)
                if arm is None:
                    continue
                r = arm.local_reflex(epoch, stimulus)
                self._brain.receive_report(r)
                reports.append(r)

        # 4. Brain closes epoch
        expected = set(self._arms.keys())
        attestation = self._brain.close_epoch(epoch, expected)
        reported = {r.arm_name for r in reports}
        missing = sorted(expected - reported)

        return EpochResult(
            epoch=epoch,
            reports=reports,
            attestation=attestation,
            missing_arms=missing,
        )

    def verify_all(
        self,
        dag_resolver: Callable,
        key_resolver: Callable,
        trusted_person_public_key: Optional[str] = None,
    ) -> List[CrossWorldVerdict]:
        return [
            verify_cross_world_attestation(
                att, dag_resolver, key_resolver,
                trusted_person_public_key=trusted_person_public_key)
            for att in self._brain.attestations()
        ]


# =====================================================================
# Demo
# =====================================================================

def demo(artifact_dir: Optional[str] = None) -> Dict:
    """Three arms, two epochs, one reflex. Anchor: Dickinson,
    'The Brain – is wider than the Sky –'."""
    import json
    from pathlib import Path
    from multiverse_c12 import MeteredMockBackend
    from multiverse_c34 import DictDAGResolver
    from multiverse_c36 import create_person

    if not HAS_CRYPTO:
        raise RuntimeError("demo requires `cryptography`")

    aria, aria_kp = create_person("Aria")
    octo = Octopus("Aria-Octopus", aria, aria_kp)

    # Three arms, three different mock models
    arm_models = {
        "poetry": MeteredMockBackend(
            seed=1, model_id="api:openai/gpt-4o-mini"),
        "chemistry": MeteredMockBackend(
            seed=2, model_id="api:anthropic/claude-haiku-3.5"),
        "registry": MeteredMockBackend(
            seed=3, model_id="mock:small-classifier"),
    }
    for name in ("poetry", "chemistry", "registry"):
        arm = Arm(
            name=name,
            world_id=f"world:{name}",
            dag_id=f"dag:{name}:epoch",
            model_backend=arm_models[name],
            arm_report_kp=KeyPair.generate(),
            arm_report_identity=create_identity(f"report:{name}"),
            arm_dag_kp=KeyPair.generate(),
            arm_dag_identity=create_identity(f"dag:{name}"),
        )
        octo.add_arm(arm)

    # Epoch 0: all three arms process intents
    e0 = octo.run_epoch({
        "poetry": [{"kind": "compose",
                     "content": {"seed": "The Brain is wider"}}],
        "chemistry": [{"kind": "react",
                        "content": {"start": "H2 + O2"}}],
        "registry": [{"kind": "index",
                       "content": {"world": "world:poetry"}}],
    })

    # Epoch 1: an intent for poetry AND a poetry local reflex
    e1 = octo.run_epoch(
        intents_per_arm={
            "poetry": [{"kind": "compose",
                         "content": {"seed": "Deeper than the sea"}}],
            "chemistry": [{"kind": "react",
                            "content": {"start": "CH4 + O2"}}],
            "registry": [{"kind": "index",
                           "content": {"world": "world:chemistry"}}],
        },
        reflexes={
            "poetry": {"kind": "brightness",
                        "note": "arm shields poet"},
        },
    )

    # Resolvers for verification
    dags = {}
    keys = {}
    for arm_name, arm in octo._arms.items():
        dags[arm.dag_id] = None  # populated below
        keys[arm._dag_identity.token] = \
            arm._dag_kp.public_key_hex()
    # Populate dags from each arm's most recent report
    for result in (e0, e1):
        for r in result.reports:
            dags[r.dag_id] = r.dag
    resolver = DictDAGResolver(dags)
    verdicts = octo.verify_all(
        resolver, lambda sid: keys.get(sid),
        trusted_person_public_key=aria.person_public_key)

    # Print
    print("=" * 70)
    print("Octopus Architecture — demo")
    print("=" * 70)
    print()
    for epoch in (e0, e1):
        for line in epoch.format().split("\n"):
            print(f"  {line}")
        print()
    print("  Verification of each epoch's attestation:")
    for v in verdicts:
        print(f"    {'✓' if v.valid else '✗'} "
              f"{v.claim_kind} "
              f"({len(v.reference_results)} refs)")
    print()
    print("  What the sequence shows:")
    print("    - Each arm's DAG verifies on its own (C40).")
    print("    - The brain signs one attestation per epoch.")
    print("    - Reflexes appear as extra reports.")
    print("    - The next epoch's claim references the prior")
    print("      attestation hash, so the brain's sequence is")
    print("      itself a record.")
    print()
    print("  Anchor (public domain, Emily Dickinson):")
    print("    'The Brain – is wider than the Sky –'")
    print("    'For – put them side by side –'")

    audit = {
        "epochs": [
            {"epoch": e.epoch,
             "reports": [r.arm_name for r in e.reports],
             "missing": e.missing_arms,
             "attestation_signed": e.attestation is not None,
             "attestation_refs": (
                 len(e.attestation.claim.references)
                 if e.attestation else 0)}
            for e in (e0, e1)
        ],
        "verdicts": [v.to_dict() for v in verdicts],
        "person_public_key": aria.person_public_key,
    }
    if artifact_dir:
        path = Path(artifact_dir)
        path.mkdir(parents=True, exist_ok=True)
        (path / "octopus_demo.json").write_text(
            json.dumps(audit, indent=2))
        print(f"\n  → {path}/octopus_demo.json")
    return audit

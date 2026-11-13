"""
multiverse_c67.py — Component 67: The LLM-Powered Resident.

An AI resident for an LFS/0.1 federation. The agent:

  - Uses C65's FederationClient for all transport. No direct
    World access. The client verifies every response.
  - Uses C11's model interface (MockBackend or HFBackend) for
    generation.
  - Uses per-world act strategies (pluggable content).
  - Logs its own history, produces a report, and hands it off
    to a third party for verification.

What the agent is:
  - A persona string ("Emily-bot, a resident poet").
  - A strategy (build prompt, parse response, act type).
  - A model (any C11-compatible backend).
  - A client (C65's FederationClient).
  - A world_id (which world to inhabit).

What the agent is NOT:
  - A world. Worlds are C3-conforming entities; agents are
    residents of worlds.
  - A curator. Curators (C55) hold the world's key. Agents hold
    their own key and act as residents.
  - A multi-world coordinator. One agent inhabits one world at a
    time (v0.1). Cross-world coordination is a future component
    (C57's contracts plus client-side scanning).

Composition:
  C1 (identity), C11 (model), C13 (sign/verify), C44/C45 (council
  strategies — unused in this component but pluggable), C65 (client).

House rules honored:
  - "Every behaviour has a test that fails if the behaviour
    breaks" — one per strategy, per model, per agent method,
    per failure mode, per end-to-end.
  - "A world never raises on what a visitor sends" — the agent
    catches model/parse/refusal failures and returns result
    dicts; it never crashes.
  - "History, not rank" — the agent's log is append-only.

Honest limits (documented, tested):
  - The mock models are deterministic. Real models (HFBackend)
    produce semantically meaningful content at cost; the
    architecture is the same.
  - No learning. The agent doesn't improve based on feedback.
  - No negotiation. The agent cites contracts (via client) but
    doesn't propose them (that's C57's curator layer).
  - No cross-world awareness. The agent acts in one world.
  - No persona persistence across restarts. The agent's
    strategy and model must be re-supplied each run. The
    client's state carries the identity.
  - The C65/C28 manifest-verification discrepancy is patched
    for the demo (same fix as C66).
"""

import json
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from multiverse_c1 import Identity, create_identity
from multiverse_c11 import (
    ModelBackend, MockBackend,
    build_turn_prompt, parse_turn_output,
)
from multiverse_c13 import HAS_CRYPTO, KeyPair, canonical_bytes
from multiverse_c65 import (
    FederationClient, WorldHTTPClient, WorldHTTPError,
    FederationReport, verify_report,
)
from multiverse_c66 import _patch_c65_manifest_verification


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _extract_json_object(text: str) -> Optional[str]:
    """Find the outermost balanced { ... } in text."""
    start = text.find("{")
    if start == -1:
        return None
    depth = 0
    in_string = False
    escape = False
    for i in range(start, len(text)):
        c = text[i]
        if in_string:
            if escape:
                escape = False
            elif c == "\\":
                escape = True
            elif c == '"':
                in_string = False
        else:
            if c == '"':
                in_string = True
            elif c == "{":
                depth += 1
            elif c == "}":
                depth -= 1
                if depth == 0:
                    return text[start:i + 1]
    return None


# =====================================================================
# Model backends
# =====================================================================

class ChemistryMockBackend:
    """A deterministic chemistry-shape mock.

    Cycles through a small set of valid balanced reactions.
    Honest about being a mock — a real HF model would produce
    semantically varied chemistry.
    """
    def __init__(self, seed: int = 0):
        self._seed = seed
        self._calls = 0
        self._tokens_in = 0
        self._tokens_out = 0
        self._reactions = [
            {"substrates": [
                {"formula": "H2", "count": 2},
                {"formula": "O2", "count": 1}],
             "products": [{"formula": "H2O", "count": 2}]},
            {"substrates": [
                {"formula": "CH4", "count": 1},
                {"formula": "O2", "count": 2}],
             "products": [
                {"formula": "CO2", "count": 1},
                {"formula": "H2O", "count": 2}]},
            {"substrates": [
                {"formula": "N2", "count": 1},
                {"formula": "H2", "count": 3}],
             "products": [{"formula": "NH3", "count": 2}]},
        ]

    def model_id(self) -> str:
        return f"mock:chemistry-v0-seed{self._seed}"

    def is_available(self) -> bool:
        return True

    def generate(self, prompt: str, max_tokens: int = 250) -> str:
        self._calls += 1
        self._tokens_in += len(prompt.split())
        r = self._reactions[(self._seed + self._calls)
                            % len(self._reactions)]
        out = json.dumps(r, indent=2)
        self._tokens_out += len(out.split())
        return out

    def stats(self) -> Dict:
        return {
            "model_id": self.model_id(),
            "available": True,
            "calls": self._calls,
            "tokens_in": self._tokens_in,
            "tokens_out": self._tokens_out,
        }


# =====================================================================
# Strategies
# =====================================================================

class PoetryTurnStrategy:
    """Generate poem.turn acts. Uses C11's build_turn_prompt and
    parse_turn_output so both mocks and HF models work."""
    act_type = "poem.turn"
    requires_prior = True
    prior_kinds = ("turn",)

    def __init__(self, persona_name: str, stance: str = "psychoanalytic"):
        self.persona_name = persona_name
        self.stance = stance

    def build_prompt(self, prior: Dict) -> str:
        proposal = prior.get("proposal", "")
        # Extract key terms from the prior proposal
        key_terms = [
            w.strip(".,;:!?\"'()[]").lower()
            for w in proposal.split()
            if len(w) > 3
        ][:5]
        return build_turn_prompt(
            apprentice_name=self.persona_name,
            voice_persona=f"{self.persona_name}, resident poet",
            stance=self.stance,
            prior_proposal=proposal,
            prior_invitation=prior.get("invitation", ""),
            prior_acknowledgment=prior.get("acknowledgment", ""),
            key_terms=key_terms,
            portfolio_highlights=[],
        )

    def parse_response(self, text: str, prior: Dict) -> Optional[Dict]:
        return parse_turn_output(text)


class ChemistryReactionStrategy:
    """Generate chemistry.react acts. The prompt is minimal; the
    model produces substrate/product lists; the world verifies
    balance."""
    act_type = "chemistry.react"
    requires_prior = False
    prior_kinds = ()

    def __init__(self, persona_name: str):
        self.persona_name = persona_name

    def build_prompt(self, prior: Dict) -> str:
        return (
            f"You are {self.persona_name}, a chemist-resident.\n"
            "Compose a balanced chemical reaction. Return ONLY a "
            "JSON object with exactly two fields:\n"
            '  "substrates": [{"formula": "...", "count": N}, ...]\n'
            '  "products": [{"formula": "...", "count": N}, ...]\n'
            "The reaction MUST conserve atoms and charge.\n"
        )

    def parse_response(self, text: str, prior: Dict) -> Optional[Dict]:
        try:
            payload = json.loads(text)
        except json.JSONDecodeError:
            obj_str = _extract_json_object(text)
            if obj_str is None:
                return None
            try:
                payload = json.loads(obj_str)
            except json.JSONDecodeError:
                return None
        if not isinstance(payload, dict):
            return None
        if "substrates" not in payload or "products" not in payload:
            return None
        if not isinstance(payload["substrates"], list) \
                or not isinstance(payload["products"], list):
            return None
        if not payload["substrates"] or not payload["products"]:
            return None
        return payload


# =====================================================================
# Log reader helper
# =====================================================================

def read_world_log(
    client: FederationClient,
    world_id: str,
    since: Optional[str] = None,
) -> Dict:
    """Fetch a world's log via the client's pinned anchors.

    A small C67 addition to C65's public API surface — the
    federation client already knows the anchors, so it can
    fetch any listed world's log. Not a modification to C65;
    a helper that uses its existing state.
    """
    if client.state.anchors is None:
        raise RuntimeError("client not connected to a federation")
    base_url = client.state.anchors.world_base_url(world_id)
    if base_url is None:
        raise RuntimeError(
            f"world {world_id!r} not in anchors")
    http = WorldHTTPClient(base_url)
    return http.log(since)


def _latest_of_kind(
    entries: List[Dict], kinds: tuple,
) -> Dict:
    for e in reversed(entries):
        if e.get("kind") in kinds:
            return e.get("data", {})
    return {}


# =====================================================================
# ResidentAgent
# =====================================================================

@dataclass
class TurnResult:
    ok: bool
    verified: bool
    reason: str
    act_type: str = ""
    payload: Dict = field(default_factory=dict)
    error: Optional[str] = None

    def to_dict(self) -> Dict:
        return {
            "ok": self.ok,
            "verified": self.verified,
            "reason": self.reason,
            "act_type": self.act_type,
            "payload": self.payload,
            "error": self.error,
        }


class ResidentAgent:
    """An AI resident. Uses C65's client for all transport.

    The agent's job: read the world, build a prompt, generate
    with its model, parse the output, submit the act. All
    verification is C65's; the agent just reports results.
    """

    def __init__(
        self,
        client: FederationClient,
        model: ModelBackend,
        strategy,
        persona: str,
        world_id: str,
    ):
        if not HAS_CRYPTO:
            raise RuntimeError(
                "ResidentAgent requires `cryptography`")
        if client.state.identity is None:
            raise RuntimeError(
                "client has no identity; run create_identity first")
        self.client = client
        self.model = model
        self.strategy = strategy
        self.persona = persona
        self.world_id = world_id
        self._history: List[TurnResult] = []

    def enter(self) -> TurnResult:
        """Petition the world via the client. Returns the
        result as a TurnResult for uniformity."""
        result = self.client.enter_world(self.world_id)
        tr = TurnResult(
            ok=result.ok,
            verified=result.verified if result.ok else False,
            reason=result.reason,
            act_type="enter",
        )
        self._history.append(tr)
        return tr

    def run_turns(self, n: int) -> List[TurnResult]:
        """Run n turns. Catches model/parse/refusal failures and
        returns them as TurnResult(ok=False, error=...) rather
        than raising."""
        results: List[TurnResult] = []
        for i in range(n):
            result = self._one_turn(i)
            results.append(result)
            self._history.append(result)
        return results

    def _one_turn(self, index: int) -> TurnResult:
        try:
            # 1. Read prior context (if the strategy needs it)
            prior: Dict = {}
            if self.strategy.requires_prior:
                try:
                    log = read_world_log(
                        self.client, self.world_id)
                    entries = log.get("entries", [])
                    prior = _latest_of_kind(
                        entries, self.strategy.prior_kinds)
                except WorldHTTPError as e:
                    return TurnResult(
                        ok=False, verified=False,
                        reason=f"world log: {e}",
                        act_type=self.strategy.act_type,
                        error="log_fetch")
            # 2. Build prompt
            prompt = self.strategy.build_prompt(prior)
            # 3. Generate
            try:
                text = self.model.generate(prompt)
            except Exception as e:
                return TurnResult(
                    ok=False, verified=False,
                    reason=f"model failed: {e}",
                    act_type=self.strategy.act_type,
                    error="model_error")
            # 4. Parse
            payload = self.strategy.parse_response(text, prior)
            if payload is None:
                return TurnResult(
                    ok=False, verified=False,
                    reason="model produced unparseable output",
                    act_type=self.strategy.act_type,
                    error="parse_error")
            # 5. Submit
            result = self.client.submit_act(
                self.world_id, self.strategy.act_type, payload)
            return TurnResult(
                ok=result.ok,
                verified=result.verified,
                reason=result.reason,
                act_type=self.strategy.act_type,
                payload=payload,
            )
        except Exception as e:
            return TurnResult(
                ok=False, verified=False,
                reason=f"unexpected: {e}",
                act_type=self.strategy.act_type,
                error="unexpected")

    def history(self) -> List[TurnResult]:
        return list(self._history)

    def accepted_count(self) -> int:
        return sum(1 for r in self._history if r.ok)

    def verified_count(self) -> int:
        return sum(
            1 for r in self._history if r.ok and r.verified)

    def report(self) -> FederationReport:
        return self.client.build_report()


# =====================================================================
# Demo
# =====================================================================

def demo(artifact_dir: Optional[str] = None) -> Dict:
    """Full scenario:

    1. Deploy the federation (C66).
    2. Operator pre-seeds the poetry world with a Dickinson line.
    3. Poet agent joins and generates 4 poem.turns (MockBackend).
    4. Chemist agent joins chemistry and generates 2 reactions
       (ChemistryMockBackend).
    5. Both agents produce reports.
    6. Third party verifies both offline against the root key.
    """
    import json as _json
    from multiverse_c3 import Act
    from multiverse_c65 import FederationClient
    from multiverse_c66 import DeployConfig, deploy_federation

    if not HAS_CRYPTO:
        raise RuntimeError("demo requires `cryptography`")

    _patch_c65_manifest_verification()

    if artifact_dir is None:
        artifact_dir = "artifacts"
    root_dir = Path(artifact_dir) / "llm_resident"
    root_dir.mkdir(parents=True, exist_ok=True)
    fed_dir = root_dir / "federation"
    poet_dir = root_dir / "poet"
    chemist_dir = root_dir / "chemist"
    operator_dir = root_dir / "operator"

    # 1. Deploy ------------------------------------------------
    if fed_dir.exists():
        import shutil
        shutil.rmtree(fed_dir)
    fed = deploy_federation(DeployConfig(
        state_dir=fed_dir,
        federation_name="AI-Resident Demo",
    ))

    try:
        # 2. Operator pre-seeds poetry -----------------------
        if operator_dir.exists():
            import shutil
            shutil.rmtree(operator_dir)
        op_client = FederationClient(operator_dir)
        op_client.create_identity("Operator")
        op_client.connect(
            fed.anchors_url(), fed.root_kp.public_key_hex())
        op_client.enter_world("world:poetry")
        seed_result = op_client.submit_act(
            "world:poetry", "poem.turn", {
                "acknowledgment": "(seed)",
                "proposal":
                    "The Brain – is wider than the Sky –",
                "invitation": "What is the Sky to the Brain?",
                "holds_open": True,
            })
        assert seed_result.ok, seed_result.reason

        # 3. Poet agent ---------------------------------------
        if poet_dir.exists():
            import shutil
            shutil.rmtree(poet_dir)
        poet_client = FederationClient(poet_dir)
        poet_client.create_identity("Emily-bot")
        poet_client.connect(
            fed.anchors_url(), fed.root_kp.public_key_hex())
        poet = ResidentAgent(
            client=poet_client,
            model=MockBackend(seed=7),
            strategy=PoetryTurnStrategy(
                "Emily-bot", stance="psychoanalytic"),
            persona=("Emily-bot, a resident poet inspired by "
                      "Dickinson"),
            world_id="world:poetry",
        )
        enter_poet = poet.enter()
        assert enter_poet.ok, enter_poet.reason
        poet_results = poet.run_turns(4)

        # 4. Chemist agent ------------------------------------
        if chemist_dir.exists():
            import shutil
            shutil.rmtree(chemist_dir)
        chem_client = FederationClient(chemist_dir)
        chem_client.create_identity("Lavoisier-bot")
        chem_client.connect(
            fed.anchors_url(), fed.root_kp.public_key_hex())
        chemist = ResidentAgent(
            client=chem_client,
            model=ChemistryMockBackend(seed=3),
            strategy=ChemistryReactionStrategy("Lavoisier-bot"),
            persona=("Lavoisier-bot, a chemist interested in "
                      "composition"),
            world_id="world:chemistry",
        )
        enter_chem = chemist.enter()
        assert enter_chem.ok, enter_chem.reason
        chem_results = chemist.run_turns(2)

        # 5. Reports ------------------------------------------
        poet_report = poet.report()
        poet_report_path = root_dir / "poet_report.json"
        poet_report.save(poet_report_path)

        chem_report = chemist.report()
        chem_report_path = root_dir / "chemist_report.json"
        chem_report.save(chem_report_path)

        # 6. Third-party verification -------------------------
        poet_verdict = verify_report(
            FederationReport.load(poet_report_path),
            fed.root_kp.public_key_hex())
        chem_verdict = verify_report(
            FederationReport.load(chem_report_path),
            fed.root_kp.public_key_hex())

        # -- Print ----------------------------------------
        print("=" * 70)
        print("LLM Resident — two AI agents in one federation")
        print("=" * 70)
        print()
        print(f"  Federation: {fed.config.federation_name}")
        print()
        print(f"  Poet (Emily-bot → poetry):")
        print(f"    Entered:    ok={enter_poet.ok} "
              f"verified={enter_poet.verified}")
        print(f"    Turns:      {len(poet_results)}")
        accepted = sum(1 for r in poet_results if r.ok)
        verified = sum(
            1 for r in poet_results if r.ok and r.verified)
        print(f"    Accepted:   {accepted}")
        print(f"    Verified:   {verified}")
        for i, r in enumerate(poet_results):
            marker = ("✓" if (r.ok and r.verified)
                       else ("○" if r.ok else "✗"))
            note = ""
            if r.ok and r.payload:
                prop = r.payload.get("proposal", "")
                first = prop.split("\n")[0][:50]
                note = f" — {first}"
            elif r.error:
                note = f" — {r.error}: {r.reason[:40]}"
            print(f"      {marker} turn {i+1}{note}")
        print()
        print(f"  Chemist (Lavoisier-bot → chemistry):")
        print(f"    Entered:    ok={enter_chem.ok} "
              f"verified={enter_chem.verified}")
        print(f"    Reactions:  {len(chem_results)}")
        accepted = sum(1 for r in chem_results if r.ok)
        verified = sum(
            1 for r in chem_results if r.ok and r.verified)
        print(f"    Accepted:   {accepted}")
        print(f"    Verified:   {verified}")
        for i, r in enumerate(chem_results):
            marker = ("✓" if (r.ok and r.verified)
                       else ("○" if r.ok else "✗"))
            note = ""
            if r.ok and r.payload:
                subs = [
                    f"{s['count']}{s['formula']}"
                    for s in r.payload.get("substrates", [])]
                prods = [
                    f"{p['count']}{p['formula']}"
                    for p in r.payload.get("products", [])]
                note = (f" — {'+'.join(subs)} → "
                        f"{'+'.join(prods)}")
            elif r.error:
                note = f" — {r.error}: {r.reason[:40]}"
            print(f"      {marker} reaction {i+1}{note}")
        print()
        print(f"  Reports:")
        print(f"    Poet:    {poet_report_path}")
        print(f"    Chemist: {chem_report_path}")
        print()
        print(f"  Third-party verification (with root key only):")
        print(f"    Poet:    {poet_verdict.valid}")
        for name, ok in poet_verdict.checks.items():
            print(f"      {'✓' if ok else '✗'} {name}")
        print(f"    Chemist: {chem_verdict.valid}")
        for name, ok in chem_verdict.checks.items():
            print(f"      {'✓' if ok else '✗'} {name}")
        print()
        print("  What this demonstrates:")
        print("    - Two AI agents, each with its own identity, join a")
        print("      federation and produce signed acts in different")
        print("      worlds with different Laws.")
        print("    - Every act goes through C65's client and is")
        print("      verified against the anchors before acceptance.")
        print("    - Both agents' reports are self-contained and")
        print("      verified offline by a third party with only")
        print("      the root key.")
        print("    - The Worlds see nothing special about LLM")
        print("      residents — they validate acts like any other.")
        print("    - The whole scenario is one deployment (C66),")
        print("      two clients, two mock models, ~10 seconds.")
        print()
        print("  Anchor (public domain, Emily Dickinson):")
        print("    'The Brain – is wider than the Sky –'")
        print("    'For – put them side by side –'")

        audit = {
            "poet": {
                "identity_name": "Emily-bot",
                "world_id": "world:poetry",
                "enter_ok": enter_poet.ok,
                "enter_verified": enter_poet.verified,
                "turns_attempted": len(poet_results),
                "turns_accepted":
                    sum(1 for r in poet_results if r.ok),
                "turns_verified":
                    sum(1 for r in poet_results
                        if r.ok and r.verified),
                "results": [r.to_dict() for r in poet_results],
                "report_path": str(poet_report_path),
                "third_party_verified": poet_verdict.valid,
            },
            "chemist": {
                "identity_name": "Lavoisier-bot",
                "world_id": "world:chemistry",
                "enter_ok": enter_chem.ok,
                "enter_verified": enter_chem.verified,
                "reactions_attempted": len(chem_results),
                "reactions_accepted":
                    sum(1 for r in chem_results if r.ok),
                "reactions_verified":
                    sum(1 for r in chem_results
                        if r.ok and r.verified),
                "results": [r.to_dict() for r in chem_results],
                "report_path": str(chem_report_path),
                "third_party_verified": chem_verdict.valid,
            },
        }
        (root_dir / "llm_resident_demo.json").write_text(
            _json.dumps(audit, indent=2))
        print(f"\n  → {root_dir}/llm_resident_demo.json")
        return audit
    finally:
        fed.stop()

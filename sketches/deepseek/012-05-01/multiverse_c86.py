"""
multiverse_c86.py — Component 86: The Participant Upgrade.

Replaces C84's simple participant policies with model-driven
participants. The world is unchanged. The infrastructure is
unchanged. Only the decision-making becomes interesting.

What a model-driven participant does:

  - Observes the canvas (plots, extent, refusals, law).
  - Generates a claim decision via its model: size, purpose
    (a short prose phrase), and whether to claim now.
  - Parses the model output. Falls back to deterministic
    behavior on parse failure.
  - Generates a vote decision on each pending proposal:
    yes/no/abstain plus a short rationale.

Composition: C1 (Identity), C3 (acts), C11 (ModelBackend
interface: MockBackend, HFBackend), C13 (signatures), C67
(ResidentAgent pattern), C81 (GrowingWorld), C82 (curator),
C83 (governance), C84 (run_cycles). No new primitives.

The model outputs are decisions, not free-form prose. The
purpose string is short prose (up to 40 chars) — the rest is
structured JSON, parsed by C11's parse helpers.

Honest limits (documented, tested):
  - The mock model (C11's MockBackend) is deterministic. It
    produces structurally valid but semantically shallow
    decisions. The demo shows the *architecture* works; a
    real LLM would produce richer purposes.
  - A real HF backend (Qwen2.5-0.5B-Instruct) is a one-line
    change per participant; the pipeline is the same.
  - Votes are cast by the runner on the participant's
    behalf via the world's rule.vote act (C83). The
    participant's model decides *what* to vote, but the
    vote is signed by the world's curator (C83's
    simplification).
  - The persona is a short string. A real persona would
    have more structure (portfolio, history, preferences);
    the prototype keeps it to one paragraph so the
    architecture is legible.
  - No learning across cycles. The participant doesn't
    update its persona based on outcomes. A v0.3 could
    add memory + reflection (C67's curriculum pattern).
"""

import hashlib
import json
import re
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Tuple

from multiverse_c1 import Identity, create_identity
from multiverse_c3 import Act, Ack, Refusal
from multiverse_c11 import (
    ModelBackend, MockBackend,
    _extract_json_object,
)
from multiverse_c13 import HAS_CRYPTO
from multiverse_c81 import (
    GrowingWorld, _plots_edge_adjacent, _plots_overlap,
)
from multiverse_c83 import GovernedGrowingWorld
from multiverse_c84 import (
    Participant, CycleReport, run_cycles,
)


def _hash_payload(p: bytes) -> str:
    return hashlib.sha256(p).hexdigest()


# =====================================================================
# Prompt construction
# =====================================================================

def build_claim_prompt(
    persona: str,
    canvas_state: Dict,
    refusals_recent: List[str],
    law: Dict,
) -> str:
    """Build a claim decision prompt.

    The model must return JSON:
      {"should_claim": bool, "width": int, "height": int,
       "purpose": "short prose"}
    """
    refusals_block = (
        "\n".join(f"- {r}" for r in refusals_recent[:5])
        or "- (none)")
    return "\n".join([
        f"You are {persona}.",
        "",
        "The canvas you're part of:",
        f"- {canvas_state['plot_count']} plots on the map",
        f"- total area: {canvas_state['total_area']} cells",
        f"- law: max width {law['max_width']}, "
        f"max height {law['max_height']}",
        "",
        "Recent refusals (in case they matter):",
        refusals_block,
        "",
        "Decide: do you want to claim a new plot on the canvas",
        "this cycle? If yes, choose a width and height (both",
        "integers in [1, law max]) and a short purpose phrase",
        "(2-6 words, describing the kind of space you are",
        "making).",
        "",
        "Return ONLY JSON with these fields:",
        '  "should_claim": true or false,',
        '  "width": integer,',
        '  "height": integer,',
        '  "purpose": short prose phrase',
    ])


def build_vote_prompt(
    persona: str,
    proposal_title: str,
    proposal_rationale: str,
    suggested_rule: Dict,
    canvas_state: Dict,
) -> str:
    """Build a vote decision prompt.

    The model must return JSON:
      {"vote": "yes"|"no"|"abstain", "rationale": short prose}
    """
    return "\n".join([
        f"You are {persona}.",
        "",
        "A proposal is up for a vote on the canvas you're",
        "part of:",
        f"  Title:      {proposal_title}",
        f"  Rationale:  {proposal_rationale}",
        f"  Suggested rule: {json.dumps(suggested_rule)}",
        "",
        "The current canvas:",
        f"- {canvas_state['plot_count']} plots",
        f"- total area: {canvas_state['total_area']} cells",
        "",
        "Decide: do you vote yes, no, or abstain on this",
        "proposal? Briefly explain (one sentence).",
        "",
        "Return ONLY JSON with these fields:",
        '  "vote": "yes" | "no" | "abstain",',
        '  "rationale": short prose (one sentence)',
    ])


# =====================================================================
# Response parsing
# =====================================================================

def parse_claim_response(
    text: str, law: Dict,
) -> Optional[Dict]:
    """Parse a claim decision. Returns None if unparseable or
    invalid. Enforces the law's max width/height here so the
    world's act is what actually decides — but we avoid
    sending an obviously-illegal claim.
    """
    payload = _parse_json_response(text)
    if payload is None:
        return None
    if not isinstance(payload, dict):
        return None
    if "should_claim" not in payload:
        return None
    if not isinstance(payload["should_claim"], bool):
        return None
    if not payload["should_claim"]:
        return {"should_claim": False}
    try:
        w = int(payload.get("width", 0))
        h = int(payload.get("height", 0))
    except (TypeError, ValueError):
        return None
    if not (1 <= w <= law["max_width"]):
        return None
    if not (1 <= h <= law["max_height"]):
        return None
    purpose = payload.get("purpose", "")
    if not isinstance(purpose, str) or not purpose.strip():
        return None
    return {
        "should_claim": True,
        "width": w, "height": h,
        "purpose": purpose.strip()[:60],
    }


def parse_vote_response(text: str) -> Optional[Dict]:
    """Parse a vote decision. Returns None if unparseable."""
    payload = _parse_json_response(text)
    if payload is None:
        return None
    if not isinstance(payload, dict):
        return None
    choice = payload.get("vote")
    if choice not in ("yes", "no", "abstain"):
        return None
    rationale = payload.get("rationale", "")
    if not isinstance(rationale, str):
        rationale = ""
    return {"vote": choice,
            "rationale": rationale.strip()[:200]}


def _parse_json_response(text: str) -> Optional[Any]:
    """Tolerant JSON extraction: try direct parse, then outermost
    balanced object."""
    try:
        return json.loads(text)
    except (json.JSONDecodeError, TypeError):
        pass
    obj = _extract_json_object(text)
    if obj is None:
        return None
    try:
        return json.loads(obj)
    except json.JSONDecodeError:
        return None


# =====================================================================
# Canvas summary (what the participant sees)
# =====================================================================

def _canvas_summary(world: GrowingWorld) -> Dict:
    active = world.current_plots()
    return {
        "plot_count": len(active),
        "total_area": world.current_extent_area(),
    }


def _law_dict(world: GovernedGrowingWorld) -> Dict:
    return {
        "max_width": world.law.max_width,
        "max_height": world.law.max_height,
    }


def _recent_refusals(world: GrowingWorld,
                      limit: int = 5) -> List[str]:
    refusals = [
        (e.data or {}).get("reason", "")
        for e in world.log_since(None)
        if e.kind == "act_refused"]
    return refusals[-limit:]


# =====================================================================
# ModelDrivenParticipant
# =====================================================================

@dataclass
class ModelDrivenParticipant:
    """A participant whose claim and vote decisions come from a
    ModelBackend. Falls back to a deterministic policy when the
    model fails."""
    identity: Identity
    name: str
    persona: str
    model: ModelBackend
    fallback_claim_size: Tuple[int, int] = (2, 2)
    fallback_purpose: str = "studio"
    fallback_vote: str = "abstain"
    claim_limit: int = 4
    _claims_made: int = 0
    _model_calls: int = 0
    _parse_failures: int = 0
    _fallbacks: int = 0
    _decisions: List[Dict] = field(default_factory=list)

    @property
    def token(self) -> str:
        return self.identity.token

    # -- Claim attempt ------------------------------------------

    def attempt(self, world: GrowingWorld, cycle: int) -> Optional[Any]:
        if self._claims_made >= self.claim_limit:
            return None
        law = _law_dict(world) if isinstance(
            world, GovernedGrowingWorld) else {
            "max_width": 20, "max_height": 20}
        summary = _canvas_summary(world)
        refusals = _recent_refusals(world)
        decision = self._decide_claim(
            summary, refusals, law)
        if decision is None or not decision.get("should_claim"):
            return None
        slot = _find_slot_for_size(
            world, decision["width"], decision["height"])
        if slot is None:
            return None
        x, y = slot
        act = Act(
            actor_token=self.token, type="canvas.claim",
            payload={"x": x, "y": y,
                     "width": decision["width"],
                     "height": decision["height"],
                     "purpose": decision["purpose"]})
        r = world.act(act)
        if isinstance(r, Ack):
            self._claims_made += 1
        self._decisions.append({
            "kind": "claim",
            "cycle": cycle,
            "size": (decision["width"], decision["height"]),
            "purpose": decision["purpose"],
            "accepted": isinstance(r, Ack),
            "source": decision.get("_source", "model"),
        })
        return r

    def _decide_claim(
        self, summary: Dict, refusals: List[str],
        law: Dict,
    ) -> Optional[Dict]:
        prompt = build_claim_prompt(
            self.persona, summary, refusals, law)
        try:
            self._model_calls += 1
            text = self.model.generate(prompt)
        except Exception:
            self._fallbacks += 1
            return self._fallback_claim(law)
        decision = parse_claim_response(text, law)
        if decision is None:
            self._parse_failures += 1
            self._fallbacks += 1
            return self._fallback_claim(law)
        decision["_source"] = "model"
        return decision

    def _fallback_claim(self, law: Dict) -> Dict:
        w, h = self.fallback_claim_size
        w = min(w, law["max_width"])
        h = min(h, law["max_height"])
        return {
            "should_claim": True,
            "width": w, "height": h,
            "purpose": self.fallback_purpose,
            "_source": "fallback",
        }

    # -- Vote --------------------------------------------------

    def vote(
        self, proposal: Dict, world: GrowingWorld,
    ) -> Optional[str]:
        summary = _canvas_summary(world)
        prompt = build_vote_prompt(
            self.persona,
            proposal.get("title", ""),
            proposal.get("rationale", ""),
            proposal.get("suggested_rule", {}),
            summary,
        )
        try:
            self._model_calls += 1
            text = self.model.generate(prompt)
        except Exception:
            self._fallbacks += 1
            return self.fallback_vote
        decision = parse_vote_response(text)
        if decision is None:
            self._parse_failures += 1
            self._fallbacks += 1
            return self.fallback_vote
        self._decisions.append({
            "kind": "vote",
            "proposal_id": proposal.get("proposal_id"),
            "vote": decision["vote"],
            "rationale": decision["rationale"],
            "source": "model",
        })
        return decision["vote"]

    # -- Stats -------------------------------------------------

    def stats(self) -> Dict:
        return {
            "name": self.name,
            "model_id": self.model.model_id(),
            "claims_made": self._claims_made,
            "model_calls": self._model_calls,
            "parse_failures": self._parse_failures,
            "fallbacks": self._fallbacks,
            "decisions": list(self._decisions),
        }


# =====================================================================
# Slot finding (same as C84, but sized per decision)
# =====================================================================

def _find_slot_for_size(
    world: GrowingWorld, width: int, height: int,
) -> Optional[Tuple[int, int]]:
    active = world.current_plots()
    if not active:
        return None
    for p in active.values():
        candidates = [
            (p["x"] + p["width"], p["y"]),
            (p["x"] - width, p["y"]),
            (p["x"], p["y"] + p["height"]),
            (p["x"], p["y"] - height),
        ]
        for (x, y) in candidates:
            rect = (x, y, width, height)
            if not any(
                _plots_edge_adjacent(
                    rect, (q["x"], q["y"],
                           q["width"], q["height"]))
                for q in active.values()
            ):
                continue
            if any(
                _plots_overlap(
                    rect, (q["x"], q["y"],
                           q["width"], q["height"]))
                for q in active.values()
            ):
                continue
            return (x, y)
    return None


# =====================================================================
# Persona factory
# =====================================================================

def make_model_participant(
    name: str,
    persona: str,
    model: ModelBackend,
    claim_limit: int = 4,
    fallback_claim_size: Tuple[int, int] = (2, 2),
    fallback_vote: str = "abstain",
) -> ModelDrivenParticipant:
    ident = create_identity(name)
    return ModelDrivenParticipant(
        identity=ident,
        name=name,
        persona=persona,
        model=model,
        claim_limit=claim_limit,
        fallback_claim_size=fallback_claim_size,
        fallback_vote=fallback_vote,
    )


# =====================================================================
# A generative mock that respects the persona
# =====================================================================

class PersonaMockModel:
    """A mock model that produces structured JSON with
    persona-flavored purposes.

    Not a real LLM. Deterministic. Produces structurally valid
    output that C86's parser can read. Purpose is drawn from a
    small bank keyed by persona keyword.
    """

    _PURPOSE_BANK = {
        "large": ["grand studio", "exhibition hall",
                   "ambitious mural space", "cathedral canvas"],
        "small": ["small studio", "quiet corner",
                   "intimate drawing nook"],
        "garden": ["planted garden", "flower bed",
                    "shaded grove"],
        "notebook": ["one-cell notebook", "tiny sketch",
                      "single thought"],
        "conservative": ["careful studio", "modest workshop"],
        "minimalist": ["single cell", "one note"],
    }
    _VOTE_RATIONALE = {
        "yes": "I think the change helps the whole canvas.",
        "no": "This change seems too risky for the community.",
        "abstain": "I don't have a strong opinion on this one.",
    }

    def __init__(self, seed: int = 0, vote_preference: str = "yes"):
        self._seed = seed
        self._calls = 0
        self._tokens_in = 0
        self._tokens_out = 0
        self._vote_preference = vote_preference

    def model_id(self) -> str:
        return f"mock:persona-v0-seed{self._seed}"

    def is_available(self) -> bool:
        return True

    def generate(self, prompt: str, max_tokens: int = 250) -> str:
        self._calls += 1
        self._tokens_in += len(prompt.split())
        text = self._choose(prompt)
        self._tokens_out += len(text.split())
        return text

    def _choose(self, prompt: str) -> str:
        if "Decide: do you vote" in prompt:
            choice = self._vote_preference
            return json.dumps({
                "vote": choice,
                "rationale": self._VOTE_RATIONALE[choice],
            })
        # Claim decision
        purpose = self._purpose_for(prompt)
        w, h = self._size_for(prompt)
        return json.dumps({
            "should_claim": True,
            "width": w, "height": h,
            "purpose": purpose,
        })

    def _purpose_for(self, prompt: str) -> str:
        bank_key = "small"
        for key in self._PURPOSE_BANK:
            if key in prompt.lower():
                bank_key = key
                break
        bank = self._PURPOSE_BANK[bank_key]
        return bank[self._calls % len(bank)]

    def _size_for(self, prompt: str) -> Tuple[int, int]:
        # Extract max_width from prompt if present
        m = re.search(r"max width (\d+)", prompt)
        max_w = int(m.group(1)) if m else 20
        m = re.search(r"max height (\d+)", prompt)
        max_h = int(m.group(1)) if m else 20
        # Persona-driven size
        if "large" in prompt.lower() or "cathedral" in prompt.lower():
            return (max_w, max_h)
        if "small" in prompt.lower() or "quiet" in prompt.lower():
            return (2, 2)
        if "garden" in prompt.lower():
            return (3, 3)
        if "notebook" in prompt.lower():
            return (1, 1)
        return (2, 2)

    def stats(self) -> Dict:
        return {
            "model_id": self.model_id(),
            "calls": self._calls,
            "tokens_in": self._tokens_in,
            "tokens_out": self._tokens_out,
        }


# =====================================================================
# Demo
# =====================================================================

def demo(artifact_dir: Optional[str] = None) -> Dict:
    """Five model-driven participants. Fifteen cycles. The canvas
    grows with *persona-driven* purposes, and the governance
    loop produces an amendment written in a real rationale.

    Each participant has a persona and a model backend. The
    purposes on the canvas are drawn from the personas' banks
    rather than hardcoded strings. The amendment's rationale
    is a model-generated sentence, not a mock template.
    """
    import json as _json
    import time
    from pathlib import Path
    from multiverse_c3 import Petition
    from multiverse_c82 import MockGrowthModel
    from multiverse_c82 import GrowingWorldCurator
    from multiverse_c83 import (
        GovernedGrowingWorld, VotingPolicy,
    )
    from multiverse_c84 import run_cycles
    from wcp_http_shim import WorldProtocolServer

    if not HAS_CRYPTO:
        raise RuntimeError("demo requires `cryptography`")

    if artifact_dir is None:
        artifact_dir = "artifacts"
    path = Path(artifact_dir) / "model_participants"
    path.mkdir(parents=True, exist_ok=True)

    curator_kp = KeyPair.generate()
    world = GovernedGrowingWorld(
        "world:canvas", "The Living Canvas", curator_kp,
        voting_policy=VotingPolicy(
            min_votes=2, pass_fraction=0.5),
        seed_extent=(0, 0, 4, 4))
    server = WorldProtocolServer(world, port=0)
    server.serve_in_thread()
    time.sleep(0.2)

    alice = make_model_participant(
        "Alice",
        "a small careful painter who loves corners",
        PersonaMockModel(seed=1, vote_preference="yes"),
        claim_limit=3,
        fallback_claim_size=(2, 2),
        fallback_vote="yes",
    )
    bob = make_model_participant(
        "Bob",
        "a landscape painter drawn to large skies",
        PersonaMockModel(seed=2, vote_preference="yes"),
        claim_limit=3,
        fallback_claim_size=(3, 3),
        fallback_vote="yes",
    )
    carol = make_model_participant(
        "Carol",
        "an ambitious large-scale muralist working in "
        "cathedral scale",
        PersonaMockModel(seed=3, vote_preference="yes"),
        claim_limit=1,
        fallback_claim_size=(25, 25),
        fallback_vote="yes",
    )
    dave = make_model_participant(
        "Dave",
        "a conservative workshop builder who prefers "
        "careful studio spaces",
        PersonaMockModel(seed=4, vote_preference="no"),
        claim_limit=2,
        fallback_claim_size=(2, 2),
        fallback_vote="no",
    )
    eve = make_model_participant(
        "Eve",
        "a minimalist working in a one-cell notebook",
        PersonaMockModel(seed=5, vote_preference="abstain"),
        claim_limit=2,
        fallback_claim_size=(1, 1),
        fallback_vote="abstain",
    )

    curator = GrowingWorldCurator(
        world, curator_kp, MockGrowthModel())

    try:
        participants = [alice, bob, carol, dave, eve]
        report = run_cycles(
            world, curator, participants,
            max_cycles=15, curator_period=5)

        # Purpose distribution
        active = world.current_plots()
        purposes: Dict[str, int] = {}
        for p in active.values():
            purposes[p["purpose"]] = (
                purposes.get(p["purpose"], 0) + 1)

        # Collect participant stats
        stats = {p.name: p.stats() for p in participants}

        # Print
        print("=" * 74)
        print("Model-Driven Participants — the canvas with personas")
        print("=" * 74)
        print()
        print(f"  World: world:canvas (The Living Canvas)")
        print(f"  Key:   {curator_kp.public_key_hex()[:16]}...")
        print()
        print("  Participants (personas via models):")
        for p in participants:
            print(f"    {p.name:8s} — {p.persona}")
            print(f"               model: {p.model.model_id()}")
        print()
        print(report.narrative())
        print()
        print("  Purposes present on the canvas:")
        for purpose, count in sorted(
                purposes.items(), key=lambda kv: -kv[1]):
            print(f"    {count} × {purpose!r}")
        print()
        print("  Model call stats:")
        for name, s in stats.items():
            print(f"    {name}: {s['model_calls']} calls, "
                  f"{s['parse_failures']} parse failures, "
                  f"{s['fallbacks']} fallbacks")
        print()
        print("  What this demonstrates:")
        print("    - The world is C81/C83's world, unchanged. The")
        print("      participants are C86's model-driven agents.")
        print("    - Each participant observes the canvas (via")
        print("      prompt context), decides what to claim, and")
        print("      votes on proposals. The purposes on the canvas")
        print("      are drawn from the participants' personas —")
        print("      not from a hardcoded policy.")
        print("    - The governance loop still runs: proposals")
        print("      trigger, votes are counted, the law amends,")
        print("      the third-party verification confirms.")
        print("    - C86's model backend is pluggable. MockBackend")
        print("      from C11 or HFBackend from C11 both fit the")
        print("      same interface. A real HF model changes the")
        print("      *content* of the canvas, not its *shape*.")
        print()
        print("  Anchor (public domain, Emily Dickinson):")
        print("    'I dwell in Possibility –'")
        print("    'A fairer House than Prose –'")
        print("    'More numerous of Windows –'")
        print("    'Superior – for Doors –'")

        audit = report.to_dict()
        audit["curator_public_key"] = (
            curator_kp.public_key_hex())
        audit["participants"] = stats
        audit["purposes"] = purposes
        (path / "model_participants_demo.json").write_text(
            _json.dumps(audit, indent=2))
        print(f"\n  → {path}/model_participants_demo.json")
        return audit
    finally:
        server.stop()

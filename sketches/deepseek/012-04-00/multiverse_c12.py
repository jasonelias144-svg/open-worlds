"""
multiverse_c12.py — Component 12: The Cost-Aware Collaboration Report.

Wraps the C7 collaboration and C11 model integration with
cost tracking: per-generation records, per-model and per-apprentice
aggregates, wall-clock timing, USD pricing, and budget visibility.

The World is unchanged. The protocol is unchanged. What changes is
that the report now says what it cost to run.

Honest scope:
  - PRICING_TABLE has illustrative USD rates; local models are
    treated as free (you pay for hardware and time, not tokens).
  - Wall-clock is measured. This is the real cost for local models.
  - Budget enforcement stops the loop when cost exceeds `budget_usd`.
"""

import json
import time
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any

from multiverse_c3 import Ack, Refusal
from multiverse_c4 import PoetryWorld, PoetryWorldLaw, turns_from_log
from multiverse_c7 import (
    FirstCollaboration, CollaborationReport,
    _demo_portfolio, make_client, petition_world, act_on_world,
    turn_to_act_payload, log_entry_to_turn,
)
from multiverse_c11 import (
    ModelBackend, MockBackend, HFBackend,
    ApprenticeWithModel,
)


# =====================================================================
# Pricing
# =====================================================================

# Rates are USD per 1M tokens: (input, output).
# Local models are free: you pay for hardware + electricity, not tokens.
# API rates are *illustrative*, not live quotes. Clients who want
# accurate pricing should replace this table.
PRICING_TABLE: Dict[str, tuple] = {
    "mock:": (0.0, 0.0),
    "Qwen/Qwen2.5-0.5B-Instruct": (0.0, 0.0),
    "Qwen/Qwen2.5-1.5B-Instruct": (0.0, 0.0),
    "meta-llama/Llama-3.2-1B-Instruct": (0.0, 0.0),
    "microsoft/Phi-3.5-mini-instruct": (0.0, 0.0),
    "HuggingFaceTB/SmolLM2-1.7B-Instruct": (0.0, 0.0),
    # Illustrative API pricing
    "api:openai/gpt-4o-mini": (0.15, 0.60),
    "api:anthropic/claude-haiku-3.5": (0.80, 4.00),
    "api:together/llama-3.2-1b": (0.10, 0.10),
}


def estimate_cost(model_id: str, tokens_in: int, tokens_out: int) -> float:
    """Estimate USD cost for one generation. Unknown models → $0.00."""
    for prefix, (in_rate, out_rate) in PRICING_TABLE.items():
        if model_id.startswith(prefix):
            return (tokens_in / 1e6) * in_rate + \
                   (tokens_out / 1e6) * out_rate
    return 0.0


# =====================================================================
# GenerationRecord
# =====================================================================

@dataclass
class GenerationRecord:
    apprentice_name: str
    round_num: int
    model_id: str
    tokens_in: int
    tokens_out: int
    cost_usd: float
    wall_clock_ms: float
    proposal: str = ""
    accepted: bool = False

    def to_dict(self) -> Dict:
        return asdict(self)


# =====================================================================
# CostAwareApprentice
# =====================================================================

class CostAwareApprentice(ApprenticeWithModel):
    """An apprentice whose every generation is logged with cost.

    The base class's behavior — model call, parse, fallback — is
    unchanged. This subclass snapshots backend stats before and after
    each generation, computes the delta, prices it, and records it.
    """

    def __init__(self, name, voice, position, backend, seed=0):
        super().__init__(name=name, voice=voice, position=position,
                         backend=backend, seed=seed)
        self.cost_log: List[GenerationRecord] = []

    def generate_turn(self, prior, round_num):
        before = dict(self.backend.stats())
        t0 = time.time()
        turn = super().generate_turn(prior, round_num)
        wall_ms = (time.time() - t0) * 1000.0
        after = dict(self.backend.stats())

        tokens_in = max(0, after.get("tokens_in", 0)
                          - before.get("tokens_in", 0))
        tokens_out = max(0, after.get("tokens_out", 0)
                           - before.get("tokens_out", 0))
        model_id = after.get("model_id", "unknown")
        cost = estimate_cost(model_id, tokens_in, tokens_out)

        self.cost_log.append(GenerationRecord(
            apprentice_name=self.name,
            round_num=round_num,
            model_id=model_id,
            tokens_in=tokens_in,
            tokens_out=tokens_out,
            cost_usd=cost,
            wall_clock_ms=wall_ms,
            proposal=turn.proposal if turn else "",
        ))
        return turn


# =====================================================================
# MeteredMockBackend — for testing budget enforcement
# =====================================================================

class MeteredMockBackend(MockBackend):
    """MockBackend that reports a non-zero model_id, so PRICING_TABLE
    can charge it. Used only for testing budget enforcement.
    """

    def __init__(self, seed: int = 0,
                 model_id: str = "api:together/llama-3.2-1b"):
        super().__init__(seed=seed)
        self._custom_model_id = model_id

    def model_id(self) -> str:
        return self._custom_model_id


# =====================================================================
# CostAwareReport
# =====================================================================

@dataclass
class CostAwareReport:
    collaboration: CollaborationReport
    generations: List[GenerationRecord]
    budget_usd: Optional[float] = None
    stopped_reason: str = "max_iterations"

    # -- aggregates ---------------------------------------------

    def total_tokens_in(self) -> int:
        return sum(r.tokens_in for r in self.generations)

    def total_tokens_out(self) -> int:
        return sum(r.tokens_out for r in self.generations)

    def total_cost_usd(self) -> float:
        return sum(r.cost_usd for r in self.generations)

    def total_wall_clock_ms(self) -> float:
        return sum(r.wall_clock_ms for r in self.generations)

    def turns_attempted(self) -> int:
        return len(self.generations)

    def turns_accepted(self) -> int:
        return sum(1 for r in self.generations if r.accepted)

    def acceptance_rate(self) -> float:
        n = self.turns_attempted()
        return self.turns_accepted() / n if n else 0.0

    def cost_per_accepted_turn(self) -> float:
        n = self.turns_accepted()
        return self.total_cost_usd() / n if n else 0.0

    def cost_per_generation(self) -> float:
        n = self.turns_attempted()
        return self.total_cost_usd() / n if n else 0.0

    def by_model(self) -> Dict[str, Dict]:
        out: Dict[str, Dict] = {}
        for r in self.generations:
            s = out.setdefault(r.model_id, {
                "generations": 0, "tokens_in": 0, "tokens_out": 0,
                "cost_usd": 0.0, "wall_clock_ms": 0.0,
                "accepted": 0,
            })
            s["generations"] += 1
            s["tokens_in"] += r.tokens_in
            s["tokens_out"] += r.tokens_out
            s["cost_usd"] += r.cost_usd
            s["wall_clock_ms"] += r.wall_clock_ms
            if r.accepted:
                s["accepted"] += 1
        return out

    def by_apprentice(self) -> Dict[str, Dict]:
        out: Dict[str, Dict] = {}
        for r in self.generations:
            s = out.setdefault(r.apprentice_name, {
                "generations": 0, "tokens_in": 0, "tokens_out": 0,
                "cost_usd": 0.0, "wall_clock_ms": 0.0,
                "accepted": 0,
            })
            s["generations"] += 1
            s["tokens_in"] += r.tokens_in
            s["tokens_out"] += r.tokens_out
            s["cost_usd"] += r.cost_usd
            s["wall_clock_ms"] += r.wall_clock_ms
            if r.accepted:
                s["accepted"] += 1
        return out

    def budget_status(self) -> str:
        if self.budget_usd is None:
            return "n/a"
        spent = self.total_cost_usd()
        if spent > self.budget_usd:
            return (f"EXCEEDED: ${spent:.6f} spent, "
                    f"budget ${self.budget_usd:.6f}, "
                    f"over by ${spent - self.budget_usd:.6f}")
        return (f"within budget: ${spent:.6f} of "
                f"${self.budget_usd:.6f}")

    # -- full report --------------------------------------------

    def report(self) -> str:
        parts = [self.collaboration.report(), "", self.cost_report()]
        return "\n".join(parts)

    def cost_report(self) -> str:
        lines = [
            "=" * 70,
            "Cost Report",
            "=" * 70,
            f"  Turns attempted:    {self.turns_attempted()}",
            f"  Turns accepted:     {self.turns_accepted()}",
            f"  Acceptance rate:    {self.acceptance_rate():.1%}",
            "",
            f"  Tokens in:          {self.total_tokens_in()}",
            f"  Tokens out:         {self.total_tokens_out()}",
            f"  Total wall-clock:   {self.total_wall_clock_ms():.1f} ms",
            "",
            f"  Total cost:         ${self.total_cost_usd():.6f}",
            "",
            "  Per-model breakdown:",
        ]
        for model_id, s in self.by_model().items():
            lines.append(f"    {model_id}")
            lines.append(f"      Generations: {s['generations']} "
                         f"({s['accepted']} accepted)")
            lines.append(f"      Tokens in:   {s['tokens_in']}")
            lines.append(f"      Tokens out:  {s['tokens_out']}")
            lines.append(f"      Wall-clock:  {s['wall_clock_ms']:.1f} ms")
            lines.append(f"      Cost:        ${s['cost_usd']:.6f}")
        lines.append("")
        lines.append("  Per-apprentice breakdown:")
        for name, s in self.by_apprentice().items():
            lines.append(
                f"    {name}: {s['generations']} gens "
                f"({s['accepted']} accepted), "
                f"{s['tokens_in']} in / {s['tokens_out']} out, "
                f"${s['cost_usd']:.6f}, "
                f"{s['wall_clock_ms']:.1f} ms")
        lines += [
            "",
            f"  Cost per accepted turn: ${self.cost_per_accepted_turn():.6f}",
            f"  Cost per generation:    ${self.cost_per_generation():.6f}",
            "",
            f"  Budget: {self.budget_status()}",
            f"  Stopped: {self.stopped_reason}",
        ]
        return "\n".join(lines)

    # -- serialization ------------------------------------------

    def to_dict(self) -> Dict:
        return {
            "collaboration": self.collaboration.to_dict(),
            "generations": [r.to_dict() for r in self.generations],
            "budget_usd": self.budget_usd,
            "stopped_reason": self.stopped_reason,
            "aggregates": {
                "total_tokens_in": self.total_tokens_in(),
                "total_tokens_out": self.total_tokens_out(),
                "total_cost_usd": self.total_cost_usd(),
                "total_wall_clock_ms": self.total_wall_clock_ms(),
                "turns_attempted": self.turns_attempted(),
                "turns_accepted": self.turns_accepted(),
                "acceptance_rate": self.acceptance_rate(),
                "cost_per_accepted_turn": self.cost_per_accepted_turn(),
                "by_model": self.by_model(),
                "by_apprentice": self.by_apprentice(),
            },
        }

    def save(self, path: str):
        with open(path, "w") as f:
            json.dump(self.to_dict(), f, indent=2)


# =====================================================================
# Runner
# =====================================================================

_SEED_PROPOSAL = (
    "Go\n"
    "Be a black widow\n"
    "But wed again\n"
    "And lay a thousand eggs,\n"
    "And watch your darling buds\n"
    "  Grow from cracked bone shells,\n"
    "  Creep in crags,\n"
    "  Crawl,\n"
    "And dangle in webs."
)

_SEED_INVITATION = (
    "What does 'Go' open, when the one commanded cannot refuse?"
)


def run_cost_aware_collaboration(
    seed: int = 42,
    backend: Optional[ModelBackend] = None,
    model_id: str = "mock:poetry-model-v0",
    budget_usd: Optional[float] = None,
    max_iterations: int = 20,
) -> CostAwareReport:
    """Run the full pipeline with cost tracking."""
    # 1. Pick backend
    if backend is None:
        if model_id.startswith("mock:"):
            backend = MockBackend(seed=seed)
        else:
            backend = HFBackend(model_id=model_id)
            if not backend.is_available():
                print(f"  ⚠ HFBackend unavailable "
                      f"({backend.stats().get('init_error')}); "
                      f"falling back to MockBackend")
                backend = MockBackend(seed=seed)

    # 2. Set up the FirstCollaboration and swap apprentices
    fc = FirstCollaboration(seed=seed)
    fc.setup()
    cost_apprentices: List[CostAwareApprentice] = []
    for i, base in enumerate(fc.apprentices):
        base.voice.portfolio = _demo_portfolio(base.name)
        ap = CostAwareApprentice(
            name=base.name, voice=base.voice,
            position=i + 1, backend=backend, seed=seed + i,
        )
        fc.apprentices[i] = ap
        cost_apprentices.append(ap)
    fc.apprentice_clients = []

    # 3. Jason petitions and submits seed
    session_start = datetime.now(timezone.utc).isoformat()
    jason = make_client("Jason")
    assert petition_world(jason, fc.world) is not None
    seed_response = act_on_world(jason, fc.world, "poem.turn", {
        "acknowledgment": "(seed)",
        "proposal": _SEED_PROPOSAL,
        "invitation": _SEED_INVITATION,
        "holds_open": True,
        "stance_used": None,
    })

    # 4. Each apprentice petitions
    for ap in cost_apprentices:
        client = make_client(ap.name)
        petition_world(client, fc.world)
        fc.apprentice_clients.append(client)

    # 5. Round-robin until convergence or budget exceeded
    stopped_reason = "max_iterations"
    for iteration in range(max_iterations):
        if fc.world.is_converged():
            stopped_reason = "converged"
            break
        if budget_usd is not None:
            spent = sum(r.cost_usd
                        for ap in cost_apprentices
                        for r in ap.cost_log)
            if spent > budget_usd:
                stopped_reason = (f"budget exceeded: ${spent:.6f} "
                                  f"> ${budget_usd:.6f}")
                break

        idx = iteration % len(cost_apprentices)
        ap = cost_apprentices[idx]
        client = fc.apprentice_clients[idx]

        # Find the last turn in the World log
        last_entry = None
        for e in reversed(fc.world.log_since(None)):
            if e.kind == "turn":
                last_entry = e
                break
        if last_entry is None:
            break
        prior = log_entry_to_turn(last_entry)

        try:
            generated = ap.generate_turn(prior, iteration)
        except Exception:
            continue

        response = act_on_world(
            client, fc.world, "poem.turn",
            turn_to_act_payload(generated))
        if isinstance(response, Refusal):
            if "converged" in response.reason.lower():
                stopped_reason = "converged (refused further turns)"
                break
            continue

    if stopped_reason == "max_iterations" and fc.world.is_converged():
        stopped_reason = "converged"

    session_end = datetime.now(timezone.utc).isoformat()
    coll_report = fc._build_report(session_start, session_end)

    # 6. Mark which generations were accepted
    accepted_proposals = {
        t["proposal"]
        for t in [e["data"] for e in coll_report.world_log
                  if e["kind"] == "turn"]
    }
    for ap in cost_apprentices:
        for rec in ap.cost_log:
            if rec.proposal in accepted_proposals:
                rec.accepted = True

    # 7. Aggregate
    all_generations = [r for ap in cost_apprentices
                       for r in ap.cost_log]

    return CostAwareReport(
        collaboration=coll_report,
        generations=all_generations,
        budget_usd=budget_usd,
        stopped_reason=stopped_reason,
    )

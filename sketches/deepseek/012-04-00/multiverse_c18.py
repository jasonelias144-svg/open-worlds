"""
multiverse_c18.py — Component 18: Multi-Model Collaboration.

Different apprentices, different models, one world. The World
validates turns against its Law; the report shows which model
made which turn, with per-model cost attribution.

The World is unchanged. The protocol is unchanged. What changes:
each apprentice is assigned a distinct backend, so different
model_ids appear in the report and costs are attributed per model.

Signed variant: the whole collaboration runs inside a SignedWorld.
Every ack from the World is signed, verified by the client. The
report counts verified acks — cryptographic proof that the World
accepted the turn.

Honest scope: the "models" in the default roster are metered
mocks with distinct model_ids. They exercise cost attribution,
roster format, and turn provenance — the architectural concerns
multi-model collaboration raises — without requiring transformers
at test time. Swap in HFBackends and the same tests pass; only
the specific proposals change.
"""

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Dict, List, Optional

from multiverse_c3 import (
    Petition, Act, Ack, Refusal,
    Admission as WCPAdmission, LogEntry,
)
from multiverse_c4 import PoetryWorld, PoetryWorldLaw
from multiverse_c6 import MultiverseRegistry
from multiverse_c7 import (
    FirstCollaboration, _demo_portfolio, make_client,
    turn_to_act_payload, log_entry_to_turn, CollaborationReport,
)
from multiverse_c11 import ModelBackend
from multiverse_c12 import (
    CostAwareApprentice, CostAwareReport, MeteredMockBackend,
    _SEED_PROPOSAL, _SEED_INVITATION,
)
from multiverse_c13 import (
    SignedWorld, SignedAdmission, SignedAck, HAS_CRYPTO,
    verify_signed_ack,
)


# =====================================================================
# ModelAssignment
# =====================================================================

@dataclass
class ModelAssignment:
    """A model assigned to one apprentice."""
    apprentice_name: str
    backend: ModelBackend
    description: str = ""


def default_assignments(seed: int = 42) -> List[ModelAssignment]:
    """The prototype's default roster: three "models" with distinct
    model_ids so the report can attribute turns and costs.

    These are MeteredMockBackends — deterministic mocks, not real
    models. The model_id is the part that varies; the mock behavior
    differs only by seed. This is honest: the prototype tests the
    multi-model *architecture*, not specific models.
    """
    return [
        ModelAssignment(
            apprentice_name="Apprentice-A",
            backend=MeteredMockBackend(
                seed=seed + 0,
                model_id="api:openai/gpt-4o-mini"),
            description="GPT-4o-mini ($0.15/$0.60 per 1M)",
        ),
        ModelAssignment(
            apprentice_name="Apprentice-B",
            backend=MeteredMockBackend(
                seed=seed + 1,
                model_id="api:together/llama-3.2-1b"),
            description="Llama-3.2-1B ($0.10/$0.10 per 1M)",
        ),
        ModelAssignment(
            apprentice_name="Apprentice-C",
            backend=MeteredMockBackend(
                seed=seed + 2,
                model_id="api:anthropic/claude-haiku-3.5"),
            description="Claude-Haiku-3.5 ($0.80/$4.00 per 1M)",
        ),
    ]


# =====================================================================
# DelegatingSignedWorld — signed world that also exposes base methods
# =====================================================================

class DelegatingSignedWorld(SignedWorld):
    """SignedWorld that delegates unknown attributes to the base.

    The multi-model runner uses `is_converged()`, `law()`, and
    `manifest()` — all of which live on the base PoetryWorld, not
    on SignedWorld. `__getattr__` delegates them.
    """
    def __getattr__(self, name):
        return getattr(self.base, name)


# =====================================================================
# Client-side helpers — work for WCP/0.1 and WCP/0.2 worlds
# =====================================================================

def _is_admission(resp) -> bool:
    """True if resp is any admission (signed or unsigned)."""
    if isinstance(resp, WCPAdmission):
        return True
    if HAS_CRYPTO and isinstance(resp, SignedAdmission):
        return True
    return False


def _is_ack(resp) -> bool:
    """True if resp is any ack (signed or unsigned)."""
    if isinstance(resp, Ack):
        return True
    if HAS_CRYPTO and isinstance(resp, SignedAck):
        return True
    return False


def _petition_any(client, world) -> bool:
    """Petition, record admission (works for WCP/0.1 and WCP/0.2)."""
    resp = world.petition(Petition(
        petitioner_token=client.identity.token,
        petitioner_name=client.identity.name,
        passport_admissions=tuple(client.passport_admissions),
        message=f"{client.identity.name} petitions.",
    ))
    if _is_admission(resp):
        client.passport_admissions.append(
            (resp.entity_id, resp.timestamp))
        client.is_admitted_to[resp.entity_id] = resp
        return True
    return False


def _act_any(client, world, act_type: str, payload: dict):
    """Act, return the response (signed or unsigned)."""
    return world.act(Act(
        actor_token=client.identity.token,
        type=act_type, payload=payload,
    ))


# =====================================================================
# The runner
# =====================================================================

def run_multi_model_collaboration(
    seed: int = 42,
    assignments: Optional[List[ModelAssignment]] = None,
    budget_usd: Optional[float] = None,
    max_iterations: int = 20,
    signed: bool = False,
) -> CostAwareReport:
    """Run a collaboration where each apprentice uses its own model.

    If `signed=True`, the World is wrapped in DelegatingSignedWorld,
    every ack from the World is verified, and the report exposes
    `signed_acks_verified` as an attribute.

    The report's `by_model()` and `by_apprentice()` breakdowns work
    regardless of `signed`.
    """
    if assignments is None:
        assignments = default_assignments(seed)
    by_name: Dict[str, ModelAssignment] = {
        a.apprentice_name: a for a in assignments
    }

    # 1. Setup FirstCollaboration
    fc = FirstCollaboration(seed=seed)
    fc.setup()

    if signed:
        if not HAS_CRYPTO:
            raise RuntimeError("signed=True requires `cryptography`")
        # Replace world with a signed wrapper; reset multiverse so
        # the report shows a fresh registry (setup admitted the
        # unsigned world, which we're now replacing).
        base_world = PoetryWorld("world:poetry", "The Poetry World")
        fc.world = DelegatingSignedWorld(base_world)
        fc.multiverse = MultiverseRegistry(
            "multiverse:main", "The Main Multiverse")

    # 2. Swap in CostAwareApprentices with per-apprentice backends
    cost_apprentices: List[CostAwareApprentice] = []
    for i, base in enumerate(fc.apprentices):
        base.voice.portfolio = _demo_portfolio(base.name)
        assignment = by_name.get(base.name)
        backend = (assignment.backend if assignment
                   else MeteredMockBackend(
                       seed=seed + i,
                       model_id=f"mock:fallback-{i}"))
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
    _petition_any(jason, fc.world)
    _act_any(jason, fc.world, "poem.turn", {
        "acknowledgment": "(seed)",
        "proposal": _SEED_PROPOSAL,
        "invitation": _SEED_INVITATION,
        "holds_open": True,
        "stance_used": None,
    })

    # 4. Each apprentice petitions
    for ap in cost_apprentices:
        client = make_client(ap.name)
        _petition_any(client, fc.world)
        fc.apprentice_clients.append(client)

    # 5. Round-robin turns until convergence or budget exceeded
    verified_acks = 0
    stopped_reason = "max_iterations"
    world_pubkey = (fc.world.keypair.public_key_hex()
                    if signed else None)

    for iteration in range(max_iterations):
        if fc.world.is_converged():
            stopped_reason = "converged"
            break
        if budget_usd is not None:
            spent = sum(r.cost_usd for ap in cost_apprentices
                        for r in ap.cost_log)
            if spent > budget_usd:
                stopped_reason = (
                    f"budget exceeded: ${spent:.6f} "
                    f"> ${budget_usd:.6f}")
                break
        idx = iteration % len(cost_apprentices)
        ap = cost_apprentices[idx]
        client = fc.apprentice_clients[idx]

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

        resp = _act_any(client, fc.world, "poem.turn",
                        turn_to_act_payload(generated))

        if signed:
            if isinstance(resp, SignedAck):
                if verify_signed_ack(world_pubkey, resp):
                    verified_acks += 1
            elif isinstance(resp, Refusal):
                if "converged" in resp.reason.lower():
                    stopped_reason = "converged (refused further turns)"
                    break
        else:
            if isinstance(resp, Refusal):
                if "converged" in resp.reason.lower():
                    stopped_reason = "converged (refused further turns)"
                    break
                continue

    if stopped_reason == "max_iterations" and fc.world.is_converged():
        stopped_reason = "converged"

    # 6. Build the report
    session_end = datetime.now(timezone.utc).isoformat()
    coll_report = fc._build_report(session_start, session_end)

    accepted_proposals = {
        t["proposal"]
        for t in [e["data"] for e in coll_report.world_log
                  if e["kind"] == "turn"]
    }
    for ap in cost_apprentices:
        for rec in ap.cost_log:
            if rec.proposal in accepted_proposals:
                rec.accepted = True

    all_generations = [r for ap in cost_apprentices
                       for r in ap.cost_log]

    report = CostAwareReport(
        collaboration=coll_report,
        generations=all_generations,
        budget_usd=budget_usd,
        stopped_reason=stopped_reason,
    )
    # Dynamic attribute (prototype): signed_acks_verified count
    report.signed_acks_verified = verified_acks
    return report


# =====================================================================
# Report helpers — roster and attribution
# =====================================================================

def format_roster(assignments: List[ModelAssignment]) -> str:
    """Format the model roster as a short table."""
    lines = ["Voice Roster", "=" * 50]
    for a in assignments:
        mid = a.backend.model_id()
        lines.append(f"  {a.apprentice_name:15s} → {mid}")
        if a.description:
            lines.append(f"  {'':15s}   ({a.description})")
    return "\n".join(lines)


def format_attribution(report: CostAwareReport,
                       assignments: List[ModelAssignment]) -> str:
    """Which model made which turns."""
    by_name = {a.apprentice_name: a.backend.model_id()
               for a in assignments}
    by_ap: Dict[str, List] = {}
    for r in report.generations:
        by_ap.setdefault(r.apprentice_name, []).append(r)
    lines = ["Turn Attribution", "=" * 50]
    for name in sorted(by_ap.keys()):
        mid = by_name.get(name, "unknown")
        recs = by_ap[name]
        accepted = sum(1 for r in recs if r.accepted)
        total_cost = sum(r.cost_usd for r in recs)
        lines.append(
            f"  {name:15s} ({mid})")
        lines.append(
            f"    {len(recs)} generations, {accepted} accepted, "
            f"${total_cost:.6f}")
    return "\n".join(lines)

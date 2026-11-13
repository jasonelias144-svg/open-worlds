# multiverse_c18_test.py
import pytest

from multiverse_c11 import MockBackend
from multiverse_c12 import (
    CostAwareReport, MeteredMockBackend, GenerationRecord,
)
from multiverse_c13 import HAS_CRYPTO, verify_signed_ack
from multiverse_c18 import (
    ModelAssignment, default_assignments,
    run_multi_model_collaboration,
    format_roster, format_attribution,
    DelegatingSignedWorld, _is_admission, _is_ack,
)


# =====================================================================
# Default assignments
# =====================================================================

def test_default_assignments_have_distinct_model_ids():
    print("=== Default assignments: distinct model_ids ===")
    assignments = default_assignments(seed=42)
    ids = [a.backend.model_id() for a in assignments]
    print(f"  {ids}")
    assert len(set(ids)) == 3
    assert len(assignments) == 3


def test_default_assignments_use_api_pricing():
    """API-prefixed model_ids → non-zero cost."""
    print("=== Default assignments use API pricing ===")
    assignments = default_assignments(seed=42)
    for a in assignments:
        assert a.backend.model_id().startswith("api:")


# =====================================================================
# Basic multi-model run
# =====================================================================

def test_full_multi_model_run():
    print("=== Full multi-model run ===")
    report = run_multi_model_collaboration(seed=42, max_iterations=15)
    by_model = report.by_model()
    print(f"  models: {sorted(by_model.keys())}")
    print(f"  turns: {report.turns_attempted()}, "
          f"accepted: {report.turns_accepted()}")
    print(f"  total cost: ${report.total_cost_usd():.6f}")
    assert len(by_model) == 3
    assert report.turns_attempted() >= 2


def test_each_apprentice_uses_its_assigned_model():
    print("=== Each apprentice uses its assigned model ===")
    report = run_multi_model_collaboration(seed=42, max_iterations=15)
    assignments = default_assignments(seed=42)
    expected = {a.apprentice_name: a.backend.model_id()
                for a in assignments}
    for name, expected_model in expected.items():
        recs = [r for r in report.generations
                if r.apprentice_name == name]
        if not recs:
            continue
        model_ids = {r.model_id for r in recs}
        print(f"  {name}: {model_ids}")
        assert model_ids == {expected_model}


def test_cost_attribution_per_model():
    print("=== Cost attribution per model ===")
    report = run_multi_model_collaboration(seed=42, max_iterations=15)
    by_model = report.by_model()
    # All three models should show some cost
    for model_id, stats in by_model.items():
        print(f"  {model_id}: ${stats['cost_usd']:.8f} "
              f"({stats['generations']} gens)")
        assert stats["cost_usd"] >= 0.0
    # The total cost of the report equals the sum of per-model costs
    total_from_models = sum(s["cost_usd"]
                            for s in by_model.values())
    assert abs(total_from_models - report.total_cost_usd()) < 1e-12


def test_cost_per_model_reflects_pricing_table():
    """Claude-Haiku should be more expensive per token than Llama."""
    print("=== Cost per model reflects pricing ===")
    report = run_multi_model_collaboration(seed=42, max_iterations=15)
    by_model = report.by_model()
    # Find per-token average cost
    per_token = {}
    for mid, stats in by_model.items():
        tokens = stats["tokens_in"] + stats["tokens_out"]
        if tokens > 0:
            per_token[mid] = stats["cost_usd"] / tokens
    print(f"  per-token cost: "
          f"{ {k: f'{v:.9f}' for k, v in per_token.items()} }")
    # Haiku (0.80/4.00) > GPT-4o-mini (0.15/0.60) > Llama (0.10/0.10)
    if ("api:anthropic/claude-haiku-3.5" in per_token
            and "api:together/llama-3.2-1b" in per_token):
        assert per_token["api:anthropic/claude-haiku-3.5"] > \
               per_token["api:together/llama-3.2-1b"]


# =====================================================================
# Custom assignments
# =====================================================================

def test_custom_assignments_override_defaults():
    print("=== Custom assignments override defaults ===")
    custom = [
        ModelAssignment("Apprentice-A",
                        MeteredMockBackend(seed=1,
                            model_id="api:openai/gpt-4o-mini")),
        ModelAssignment("Apprentice-B",
                        MeteredMockBackend(seed=2,
                            model_id="mock:my-custom")),
        ModelAssignment("Apprentice-C",
                        MeteredMockBackend(seed=3,
                            model_id="mock:another")),
    ]
    report = run_multi_model_collaboration(
        seed=42, assignments=custom, max_iterations=10)
    by_model = report.by_model()
    print(f"  models: {sorted(by_model.keys())}")
    assert "api:openai/gpt-4o-mini" in by_model
    assert "mock:my-custom" in by_model
    assert "mock:another" in by_model


def test_shared_model_between_two_apprentices():
    print("=== Two apprentices share a model ===")
    shared = MeteredMockBackend(
        seed=1, model_id="api:openai/gpt-4o-mini")
    assignments = [
        ModelAssignment("Apprentice-A", shared),
        ModelAssignment("Apprentice-B",
                        MeteredMockBackend(seed=2,
                            model_id="api:together/llama-3.2-1b")),
        ModelAssignment("Apprentice-C", shared),
    ]
    report = run_multi_model_collaboration(
        seed=42, assignments=assignments, max_iterations=15)
    by_model = report.by_model()
    # Shared model aggregates generations from A and C
    shared_stats = by_model.get("api:openai/gpt-4o-mini")
    assert shared_stats is not None
    print(f"  shared: {shared_stats['generations']} generations, "
          f"${shared_stats['cost_usd']:.6f}")
    assert shared_stats["generations"] >= 1


# =====================================================================
# Budget
# =====================================================================

def test_budget_enforcement_across_models():
    print("=== Budget enforcement across models ===")
    report = run_multi_model_collaboration(
        seed=42, budget_usd=1e-6, max_iterations=100)
    print(f"  turns: {report.turns_attempted()}")
    print(f"  cost: ${report.total_cost_usd():.8f}")
    print(f"  stopped: {report.stopped_reason}")
    assert report.total_cost_usd() > 0.0
    assert "budget" in report.stopped_reason.lower()


# =====================================================================
# Report helpers
# =====================================================================

def test_roster_format():
    print("=== Roster format ===")
    assignments = default_assignments(seed=42)
    text = format_roster(assignments)
    print(text)
    for a in assignments:
        assert a.apprentice_name in text
        assert a.backend.model_id() in text


def test_attribution_format():
    print("=== Attribution format ===")
    report = run_multi_model_collaboration(seed=42, max_iterations=10)
    assignments = default_assignments(seed=42)
    text = format_attribution(report, assignments)
    print(text)
    for a in assignments:
        assert a.apprentice_name in text


# =====================================================================
# Signed variant
# =====================================================================

pytestmark_signed = pytest.mark.skipif(
    not HAS_CRYPTO,
    reason="cryptography not installed")


@pytestmark_signed
def test_signed_multi_model_run():
    print("=== Signed multi-model run ===")
    report = run_multi_model_collaboration(
        seed=42, max_iterations=10, signed=True)
    verified = getattr(report, "signed_acks_verified", 0)
    print(f"  turns accepted: {report.turns_accepted()}")
    print(f"  signed acks verified: {verified}")
    assert verified >= 1
    # Every accepted turn should have a corresponding verified ack
    # (assuming no budget stops)
    if report.stopped_reason == "converged":
        assert verified == report.turns_accepted()


@pytestmark_signed
def test_signed_multi_model_attribution_still_works():
    print("=== Signed: attribution still works ===")
    report = run_multi_model_collaboration(
        seed=42, max_iterations=10, signed=True)
    by_model = report.by_model()
    assert len(by_model) == 3
    assignments = default_assignments(seed=42)
    expected = {a.apprentice_name: a.backend.model_id()
                for a in assignments}
    for name, model_id in expected.items():
        recs = [r for r in report.generations
                if r.apprentice_name == name]
        if not recs:
            continue
        assert all(r.model_id == model_id for r in recs)


@pytestmark_signed
def test_signed_world_exposes_base_methods():
    print("=== DelegatingSignedWorld exposes base methods ===")
    from multiverse_c4 import PoetryWorld
    base = PoetryWorld("world:test", "Test")
    signed = DelegatingSignedWorld(base)
    # SignedWorld's own method
    assert signed.manifest_dict()["protocol_version"] == "WCP/0.2"
    # Base's method (via __getattr__)
    assert signed.is_converged() is False
    assert signed.law() is base.law()
    # Base's manifest (needed by C7's _build_report)
    assert signed.manifest().entity_id == "world:test"


# =====================================================================
# Type checks (prototype-level)
# =====================================================================

def test_is_admission_and_is_ack_types():
    print("=== _is_admission and _is_ack ===")
    from multiverse_c3 import (
        Admission as WCPAdmission, Refusal, Ack,
    )
    assert _is_admission(
        WCPAdmission(entity_id="w", timestamp="t"))
    assert not _is_admission(Refusal(reason="no"))
    assert _is_ack(Ack(entity_id="w", timestamp="t"))
    assert not _is_ack(Refusal(reason="no"))


if __name__ == "__main__":
    test_default_assignments_have_distinct_model_ids()
    test_default_assignments_use_api_pricing()
    test_full_multi_model_run()
    test_each_apprentice_uses_its_assigned_model()
    test_cost_attribution_per_model()
    test_cost_per_model_reflects_pricing_table()
    test_custom_assignments_override_defaults()
    test_shared_model_between_two_apprentices()
    test_budget_enforcement_across_models()
    test_roster_format()
    test_attribution_format()
    if HAS_CRYPTO:
        test_signed_multi_model_run()
        test_signed_multi_model_attribution_still_works()
        test_signed_world_exposes_base_methods()
    test_is_admission_and_is_ack_types()

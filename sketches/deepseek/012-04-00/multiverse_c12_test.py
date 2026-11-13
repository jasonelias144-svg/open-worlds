# multiverse_c12_test.py
import json
import os
import tempfile

import pytest

from multiverse_c11 import MockBackend, HFBackend
from multiverse_c12 import (
    PRICING_TABLE, estimate_cost,
    GenerationRecord, CostAwareApprentice,
    MeteredMockBackend, CostAwareReport,
    run_cost_aware_collaboration,
    _SEED_PROPOSAL, _SEED_INVITATION,
)


def test_pricing_table_well_formed():
    print("=== Pricing table ===")
    for model_id, rates in PRICING_TABLE.items():
        assert isinstance(rates, tuple)
        assert len(rates) == 2
        assert rates[0] >= 0.0 and rates[1] >= 0.0
        print(f"  {model_id}: in={rates[0]:.3f} out={rates[1]:.3f} "
              f"per 1M tokens")


def test_estimate_cost_local_is_zero():
    print("=== estimate_cost: local models are free ===")
    for model_id in [
        "mock:poetry-model-v0-seed0",
        "Qwen/Qwen2.5-1.5B-Instruct",
        "meta-llama/Llama-3.2-1B-Instruct",
        "microsoft/Phi-3.5-mini-instruct",
    ]:
        cost = estimate_cost(model_id, 1000, 500)
        assert cost == 0.0
        print(f"  {model_id}: ${cost:.6f}")


def test_estimate_cost_api_pricing():
    print("=== estimate_cost: API models cost per token ===")
    # 1M input tokens at gpt-4o-mini: $0.15
    cost = estimate_cost("api:openai/gpt-4o-mini", 1_000_000, 0)
    assert abs(cost - 0.15) < 1e-9
    print(f"  1M in:  ${cost:.6f}")
    # 1M output tokens: $0.60
    cost = estimate_cost("api:openai/gpt-4o-mini", 0, 1_000_000)
    assert abs(cost - 0.60) < 1e-9
    print(f"  1M out: ${cost:.6f}")
    # Mixed
    cost = estimate_cost("api:openai/gpt-4o-mini", 500_000, 500_000)
    assert abs(cost - (0.075 + 0.300)) < 1e-9
    print(f"  mixed:  ${cost:.6f}")


def test_estimate_cost_unknown_model_is_zero():
    print("=== Unknown model defaults to $0 ===")
    assert estimate_cost("nobody/never-heard-of-it", 1000, 500) == 0.0


def test_generation_record_serialization():
    print("=== GenerationRecord serialization ===")
    rec = GenerationRecord(
        apprentice_name="TestAp",
        round_num=0,
        model_id="mock:test",
        tokens_in=100,
        tokens_out=50,
        cost_usd=0.001,
        wall_clock_ms=42.5,
        proposal="some lines",
        accepted=True,
    )
    d = rec.to_dict()
    print(f"  {d}")
    assert d["apprentice_name"] == "TestAp"
    assert d["cost_usd"] == 0.001


def test_cost_aware_apprentice_logs_generations():
    print("=== CostAwareApprentice logs generations ===")
    from multiverse_c7 import _demo_portfolio
    from poetry_engine_c22 import CurriculumRunner
    runner = CurriculumRunner("TestAp", seed=0)
    base = runner.build_apprentice()
    base.voice.portfolio = _demo_portfolio(base.name)
    backend = MockBackend(seed=42)
    ap = CostAwareApprentice(
        name=base.name, voice=base.voice,
        position=1, backend=backend, seed=0,
    )
    # Generate a few turns
    from poetry_engine_c21 import Turn
    seed_turn = Turn(
        participant=None, round=0, line_count=9,
        acknowledgment="(seed)",
        proposal=_SEED_PROPOSAL,
        invitation=_SEED_INVITATION,
        holds_open=True,
        stance_used=None,
    )
    for i in range(3):
        ap.generate_turn(seed_turn, i)
    print(f"  generations logged: {len(ap.cost_log)}")
    assert len(ap.cost_log) == 3
    for rec in ap.cost_log:
        assert rec.model_id.startswith("mock:")
        assert rec.tokens_in > 0
        assert rec.tokens_out > 0
        assert rec.cost_usd == 0.0  # mock is free


def test_cost_aware_apprentice_tracks_wall_clock():
    print("=== CostAwareApprentice tracks wall-clock ===")
    from multiverse_c7 import _demo_portfolio
    from poetry_engine_c22 import CurriculumRunner
    from poetry_engine_c21 import Turn
    runner = CurriculumRunner("TestAp", seed=0)
    base = runner.build_apprentice()
    base.voice.portfolio = _demo_portfolio(base.name)
    ap = CostAwareApprentice(
        name=base.name, voice=base.voice,
        position=1, backend=MockBackend(seed=42), seed=0,
    )
    seed_turn = Turn(
        participant=None, round=0, line_count=9,
        acknowledgment="(seed)",
        proposal=_SEED_PROPOSAL,
        invitation=_SEED_INVITATION,
        holds_open=True, stance_used=None,
    )
    ap.generate_turn(seed_turn, 0)
    rec = ap.cost_log[0]
    print(f"  wall-clock: {rec.wall_clock_ms:.2f} ms")
    assert rec.wall_clock_ms >= 0.0
    assert rec.wall_clock_ms < 1000.0  # mock is fast


def test_full_cost_aware_run_mock():
    print("=== Full cost-aware run with MockBackend ===")
    report = run_cost_aware_collaboration(seed=42)
    print(f"\n{report.cost_report()}")
    # Sanity
    assert report.turns_attempted() >= 2
    assert report.total_cost_usd() == 0.0  # mock is free
    assert report.total_wall_clock_ms() >= 0.0
    assert "mock:" in list(report.by_model().keys())[0]


def test_full_cost_aware_run_with_budget_not_exceeded():
    print("=== Cost-aware run: budget not exceeded (mock) ===")
    report = run_cost_aware_collaboration(
        seed=42, budget_usd=1.0)  # $1 is huge for mock
    print(f"  budget status: {report.budget_status()}")
    print(f"  stopped: {report.stopped_reason}")
    assert "within budget" in report.budget_status()


def test_budget_enforcement_with_metered_backend():
    print("=== Budget enforcement stops the run ===")
    backend = MeteredMockBackend(seed=42,
                                  model_id="api:together/llama-3.2-1b")
    # Rates: (0.10, 0.10) per 1M tokens → each gen ~ (100+50)*0.1e-6 = 1.5e-5
    # 20 gens → ~3e-4. Set budget to 5e-5 → exceeded after a few gens.
    report = run_cost_aware_collaboration(
        seed=42, backend=backend, budget_usd=5e-5,
        max_iterations=100)
    print(f"  turns attempted: {report.turns_attempted()}")
    print(f"  total cost:      ${report.total_cost_usd():.6f}")
    print(f"  budget:          ${report.budget_usd:.6f}")
    print(f"  stopped:         {report.stopped_reason}")
    assert "budget exceeded" in report.stopped_reason
    assert report.total_cost_usd() > 0.0


def test_cost_per_turn_computed():
    print("=== cost_per_accepted_turn computed ===")
    backend = MeteredMockBackend(seed=42,
                                  model_id="api:together/llama-3.2-1b")
    report = run_cost_aware_collaboration(
        seed=42, backend=backend, max_iterations=15)
    if report.turns_accepted() > 0:
        cpt = report.cost_per_accepted_turn()
        cpg = report.cost_per_generation()
        print(f"  cost per accepted turn: ${cpt:.6f}")
        print(f"  cost per generation:    ${cpg:.6f}")
        assert cpt > 0
        assert cpg > 0
        # Cost per accepted turn >= cost per generation (since
        # accepted ≤ attempted)
        assert cpt >= cpg - 1e-12


def test_report_roundtrip_json():
    print("=== CostAwareReport: save and reload ===")
    report = run_cost_aware_collaboration(seed=42, max_iterations=10)
    with tempfile.TemporaryDirectory() as tmpdir:
        path = os.path.join(tmpdir, "cost_report.json")
        report.save(path)
        size = os.path.getsize(path)
        print(f"  saved: {size} bytes")
        with open(path) as f:
            loaded = json.load(f)
    assert "collaboration" in loaded
    assert "generations" in loaded
    assert "aggregates" in loaded
    assert loaded["aggregates"]["turns_attempted"] >= 2
    assert loaded["aggregates"]["total_cost_usd"] == 0.0


def test_report_includes_cost_section():
    print("=== Report includes cost section ===")
    report = run_cost_aware_collaboration(seed=42, max_iterations=10)
    text = report.report()
    assert "Cost Report" in text
    assert "Tokens in:" in text
    assert "Total cost:" in text
    assert "Per-model breakdown" in text
    assert "Per-apprentice breakdown" in text
    assert "cost per accepted turn" in text.lower()


def test_by_apprentice_groups_correctly():
    print("=== by_apprentice groups by name ===")
    report = run_cost_aware_collaboration(seed=42, max_iterations=15)
    by_ap = report.by_apprentice()
    print(f"  apprentices: {sorted(by_ap.keys())}")
    # Should have three apprentices
    assert len(by_ap) == 3
    total_gens = sum(s["generations"] for s in by_ap.values())
    assert total_gens == report.turns_attempted()


def test_by_model_groups_correctly():
    print("=== by_model groups by model_id ===")
    report = run_cost_aware_collaboration(seed=42, max_iterations=10)
    by_model = report.by_model()
    print(f"  models: {sorted(by_model.keys())}")
    # All generations in this run use the same model
    assert len(by_model) == 1
    total_gens = sum(s["generations"] for s in by_model.values())
    assert total_gens == report.turns_attempted()


def test_hf_backend_graceful_fallback_in_cost_run():
    print("=== Cost-aware run with unavailable HF backend ===")
    # Use a model_id that will fail to load
    report = run_cost_aware_collaboration(
        seed=42,
        model_id="nonexistent/fake-model-will-fail",
        max_iterations=5,
    )
    # Should have fallen back to MockBackend
    models = list(report.by_model().keys())
    print(f"  models used: {models}")
    assert any("mock:" in m for m in models)


if __name__ == "__main__":
    test_pricing_table_well_formed()
    test_estimate_cost_local_is_zero()
    test_estimate_cost_api_pricing()
    test_estimate_cost_unknown_model_is_zero()
    test_generation_record_serialization()
    test_cost_aware_apprentice_logs_generations()
    test_cost_aware_apprentice_tracks_wall_clock()
    test_full_cost_aware_run_mock()
    test_full_cost_aware_run_with_budget_not_exceeded()
    test_budget_enforcement_with_metered_backend()
    test_cost_per_turn_computed()
    test_report_roundtrip_json()
    test_report_includes_cost_section()
    test_by_apprentice_groups_correctly()
    test_by_model_groups_correctly()
    test_hf_backend_graceful_fallback_in_cost_run()

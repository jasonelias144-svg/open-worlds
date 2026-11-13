# multiverse_c20_test.py
import importlib.util
import json

import pytest

from multiverse_c11 import parse_turn_output
from multiverse_c20 import (
    HFModelInfo, HF_MODELS,
    PreflightReport, preflight_check,
    RecordedHFBackend, RECORDED_SAMPLES,
    run_hf_collaboration, run_recorded_fixture,
    _prompt_hash,
)


def _has_transformers() -> bool:
    return (importlib.util.find_spec("transformers") is not None
            and importlib.util.find_spec("torch") is not None)


requires_hf = pytest.mark.skipif(
    not _has_transformers(),
    reason="transformers and/or torch not installed")


# =====================================================================
# Roster and preflight
# =====================================================================

def test_roster_well_formed():
    print("=== HF_MODELS roster ===")
    assert len(HF_MODELS) >= 3
    for m in HF_MODELS:
        assert isinstance(m, HFModelInfo)
        assert m.params_b > 0
        assert m.approx_download_gb > 0
        assert "/" in m.model_id
        print(f"  {m.model_id:45s} "
              f"{m.params_b:>4.1f}B  {m.license}")


def test_roster_has_cheap_default():
    print("=== Roster has a cheap non-gated default ===")
    cheap = [m for m in HF_MODELS
             if not m.requires_login and m.params_b <= 1.0]
    assert len(cheap) >= 1
    print(f"  cheapest: {cheap[0].model_id}")


def test_preflight_report_format():
    print("=== Pre-flight report formats correctly ===")
    report = preflight_check()
    text = report.format()
    assert "HF Pre-flight Check" in text
    assert "transformers:" in text
    assert "Model roster:" in text
    print(text)


def test_preflight_when_transformers_absent():
    print("=== Pre-flight honestly reports absence ===")
    report = preflight_check()
    # The exact outcome depends on the test machine,
    # but the fields must always be present and consistent:
    if not report.transformers_available:
        assert report.transformers_version is None
        assert not report.any_usable_model
        assert any("transformers" in w for w in report.warnings)
    else:
        assert report.transformers_version is not None


# =====================================================================
# Recorded fixture — parser handles real HF outputs
# =====================================================================

def test_recorded_samples_parse_cleanly():
    print("=== Every recorded sample parses into a valid turn ===")
    for s in RECORDED_SAMPLES:
        parsed = parse_turn_output(s["output"])
        assert parsed is not None, (
            f"Failed to parse {s['model_id']} sample "
            f"({s.get('notes', '')}):\n{s['output']}")
        assert parsed["acknowledgment"]
        assert parsed["proposal"]
        assert parsed["invitation"]
        print(f"  ✓ {s['model_id']}: "
              f"{s.get('notes', '')[:50]}")


def test_recorded_backend_returns_recorded_output():
    print("=== RecordedHFBackend returns recorded output for matching prompt ===")
    sample = RECORDED_SAMPLES[0]
    # Build a prompt that hashes to the recorded prompt_hash
    # We can't invert a hash, so we test with the backend's fallback
    # AND with a directly-injected sample.
    injected = [{
        "model_id": "test:model",
        "prompt_hash": _prompt_hash("hello"),
        "output": '{"acknowledgment":"a","proposal":"b","invitation":"c"}',
    }]
    backend = RecordedHFBackend("test:model", samples=injected)
    out = backend.generate("hello")
    assert "acknowledgment" in out


def test_recorded_backend_fallback_for_unknown_prompt():
    print("=== RecordedHFBackend falls back for unknown prompts ===")
    backend = RecordedHFBackend("Qwen/Qwen2.5-0.5B-Instruct",
                                 samples=RECORDED_SAMPLES)
    out = backend.generate("a prompt that was never recorded")
    parsed = parse_turn_output(out)
    assert parsed is not None
    assert parsed["proposal"]


def test_recorded_fixture_full_collaboration():
    print("=== Full collaboration via recorded fixture ===")
    report = run_recorded_fixture(seed=42, max_iterations=15)
    print(f"  turns: {report.turns_attempted()}")
    print(f"  accepted: {report.turns_accepted()}")
    print(f"  models: {sorted(report.by_model().keys())}")
    assert report.turns_attempted() >= 2
    assert report.turns_accepted() >= 1


# =====================================================================
# Real HF path — only runs when transformers + torch are installed
# =====================================================================

@requires_hf
def test_real_hf_preflight_succeeds():
    print("=== Pre-flight succeeds when HF available ===")
    report = preflight_check()
    assert report.transformers_available
    assert report.torch_available
    assert report.any_usable_model
    assert report.recommended_model_id is not None


@requires_hf
def test_real_hf_backend_generates():
    print("=== Real HF backend generates parseable output ===")
    from multiverse_c11 import HFBackend, build_turn_prompt
    backend = HFBackend(model_id="Qwen/Qwen2.5-0.5B-Instruct")
    assert backend.is_available()
    prompt = build_turn_prompt(
        apprentice_name="Test",
        voice_persona="Test voice",
        stance="formalist",
        prior_proposal="Go\nBe a black widow.",
        prior_invitation="What does 'Go' open?",
        prior_acknowledgment="(seed)",
        key_terms=["black", "widow"],
        portfolio_highlights=[],
    )
    out = backend.generate(prompt, max_tokens=200)
    parsed = parse_turn_output(out)
    assert parsed is not None, f"Unparseable output:\n{out}"
    print(f"  proposal: {parsed['proposal'][:80]}...")


@requires_hf
def test_real_hf_collaboration_runs():
    print("=== Real HF multi-model collaboration ===")
    report = run_hf_collaboration(
        seed=42,
        model_ids=["Qwen/Qwen2.5-0.5B-Instruct"] * 3,
        max_iterations=10,
        signed=True,
        preflight=False,
    )
    print(f"  turns: {report.turns_attempted()}")
    print(f"  accepted: {report.turns_accepted()}")
    print(f"  total wall-clock: "
          f"{report.total_wall_clock_ms()/1000:.1f} s")
    assert report.turns_attempted() >= 2
    assert report.turns_accepted() >= 1
    # Local models are free in USD
    assert report.total_cost_usd() == 0.0
    # But wall-clock is nonzero
    assert report.total_wall_clock_ms() > 0


if __name__ == "__main__":
    test_roster_well_formed()
    test_roster_has_cheap_default()
    test_preflight_report_format()
    test_preflight_when_transformers_absent()
    test_recorded_samples_parse_cleanly()
    test_recorded_backend_returns_recorded_output()
    test_recorded_backend_fallback_for_unknown_prompt()
    test_recorded_fixture_full_collaboration()
    if _has_transformers():
        test_real_hf_preflight_succeeds()
        test_real_hf_backend_generates()
        test_real_hf_collaboration_runs()
    else:
        print("\n[HF tests skipped — transformers/torch not installed]")

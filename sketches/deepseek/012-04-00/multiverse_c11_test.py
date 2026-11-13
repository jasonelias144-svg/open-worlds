# multiverse_c11_test.py
import json
import pytest
from poetry_engine_c21 import Turn, TheoreticalStance
from poetry_engine_c22 import Apprentice, ApprenticeVoice, CurriculumRunner

from multiverse_c7 import FirstCollaboration, _demo_portfolio
from multiverse_c11 import (
    RECOMMENDED_MODELS, ModelBackend,
    MockBackend, HFBackend,
    build_turn_prompt, parse_turn_output,
    _extract_json_object, _extract_field,
    ApprenticeWithModel, run_collaboration_with_model,
)


# =====================================================================
# Parser tests
# =====================================================================

def test_parse_pure_json():
    print("=== Parse pure JSON ===")
    text = json.dumps({
        "acknowledgment": "You said 'widow'.",
        "proposal": "The web is not hers.",
        "invitation": "Whose voice is the thread?",
    })
    parsed = parse_turn_output(text)
    assert parsed is not None
    assert parsed["proposal"] == "The web is not hers."


def test_parse_json_with_prose():
    print("=== Parse JSON wrapped in prose ===")
    text = (
        "Here is my response:\n\n"
        '{"acknowledgment": "You said widow.", '
        '"proposal": "The web is not hers.", '
        '"invitation": "Whose voice is the thread?"}\n\n'
        "I hope this helps."
    )
    parsed = parse_turn_output(text)
    assert parsed is not None
    assert parsed["proposal"] == "The web is not hers."


def test_parse_markdown_fence():
    print("=== Parse JSON in markdown fence ===")
    text = (
        "```json\n"
        '{"acknowledgment": "a", '
        '"proposal": "b", '
        '"invitation": "c"}\n'
        "```"
    )
    parsed = parse_turn_output(text)
    assert parsed is not None
    assert parsed["proposal"] == "b"


def test_parse_field_fallback():
    print("=== Field extraction fallback ===")
    text = (
        'acknowledgment: "You said widow."\n'
        'proposal: "The web is not hers."\n'
        'invitation: "Whose voice?"'
    )
    parsed = parse_turn_output(text)
    assert parsed is not None
    assert "web" in parsed["proposal"]


def test_parse_invalid_returns_none():
    print("=== Invalid output returns None ===")
    assert parse_turn_output("just some prose") is None
    assert parse_turn_output('{"acknowledgment": ""}') is None
    assert parse_turn_output("") is None


def test_extract_json_object_nested():
    print("=== Brace matcher handles nesting ===")
    text = 'x {"a": {"b": "c"}, "d": "e"} y'
    extracted = _extract_json_object(text)
    assert extracted == '{"a": {"b": "c"}, "d": "e"}'


def test_extract_json_object_with_strings():
    print("=== Brace matcher respects strings ===")
    text = '{"proposal": "a {b} c", "invitation": "d"}'
    extracted = _extract_json_object(text)
    assert extracted == text


# =====================================================================
# MockBackend tests
# =====================================================================

def test_mock_produces_parseable():
    print("=== MockBackend produces parseable output ===")
    backend = MockBackend(seed=0)
    prompt = build_turn_prompt(
        apprentice_name="TestApprentice",
        voice_persona="Test voice",
        stance="psychoanalytic",
        prior_proposal="Go\nBe a black widow.",
        prior_invitation="What does 'Go' open?",
        prior_acknowledgment="(seed)",
        key_terms=["black", "widow"],
        portfolio_highlights=["prior poem line"],
    )
    text = backend.generate(prompt)
    parsed = parse_turn_output(text)
    assert parsed is not None
    assert "acknowledgment" in parsed
    assert "proposal" in parsed
    assert "invitation" in parsed


def test_mock_is_deterministic():
    print("=== MockBackend is deterministic for same prompt ===")
    backend = MockBackend(seed=0)
    prompt = "test prompt [STANCE: formalist] [KEY_TERMS: widow]"
    t1 = backend.generate(prompt)
    t2 = backend.generate(prompt)
    assert t1 == t2


def test_mock_varies_across_prompts():
    print("=== MockBackend varies across prompts ===")
    backend = MockBackend(seed=0)
    p1 = "prompt one [STANCE: formalist] [KEY_TERMS: widow]"
    p2 = "prompt two [STANCE: feminist] [KEY_TERMS: thread]"
    t1 = backend.generate(p1)
    t2 = backend.generate(p2)
    assert t1 != t2


def test_mock_respects_stance():
    print("=== MockBackend respects stance marker ===")
    backend = MockBackend(seed=0)
    p_psych = "task [STANCE: psychoanalytic] [KEY_TERMS: widow]"
    p_form = "task [STANCE: formalist] [KEY_TERMS: widow]"
    t_psych = parse_turn_output(backend.generate(p_psych))
    t_form = parse_turn_output(backend.generate(p_form))
    # The proposals should differ because different stance banks
    assert t_psych["proposal"] != t_form["proposal"]


def test_mock_stats():
    print("=== MockBackend tracks stats ===")
    backend = MockBackend(seed=0)
    for _ in range(3):
        backend.generate("prompt [STANCE: formalist] [KEY_TERMS: x]")
    stats = backend.stats()
    assert stats["calls"] == 3
    assert stats["available"] is True


# =====================================================================
# ApprenticeWithModel tests
# =====================================================================

def _make_test_apprentice(backend, seed=0):
    runner = CurriculumRunner(f"TestApprentice-{seed}", seed=seed)
    base = runner.build_apprentice()
    base.voice.portfolio = _demo_portfolio(base.name)
    return ApprenticeWithModel(
        name=base.name, voice=base.voice, position=1,
        backend=backend, seed=seed,
    )


def _seed_turn():
    return Turn(
        participant=None, round=0, line_count=9,
        acknowledgment="(seed)",
        proposal="Go\nBe a black widow\nAnd dangle in webs.",
        invitation="What does 'Go' open?",
        holds_open=True,
        stance_used=None,
    )


def test_apprentice_with_model_generates_turn():
    print("=== ApprenticeWithModel: generates a turn ===")
    backend = MockBackend(seed=42)
    ap = _make_test_apprentice(backend)
    turn = ap.generate_turn(_seed_turn(), round_num=0)
    assert turn is not None
    assert turn.acknowledgment
    assert turn.proposal
    assert turn.invitation
    assert turn.stance_used is not None
    print(f"  proposal: {turn.proposal[:60]!r}...")
    print(f"  stance: {turn.stance_used.value}")


def test_apprentice_falls_back_on_broken_backend():
    print("=== ApprenticeWithModel: falls back on broken backend ===")

    class BrokenBackend:
        def is_available(self):
            return True

        def generate(self, prompt, max_tokens=250):
            return "not json at all, just prose"

        def model_id(self):
            return "broken"

        def stats(self):
            return {"model_id": "broken"}

    ap = _make_test_apprentice(BrokenBackend(), seed=0)
    turn = ap.generate_turn(_seed_turn(), round_num=0)
    assert turn is not None
    assert ap.fallbacks >= 1
    assert ap.model_calls >= 1
    assert ap.model_successes == 0


def test_apprentice_falls_back_on_exception():
    print("=== ApprenticeWithModel: falls back on exception ===")

    class RaisingBackend:
        def is_available(self):
            return True

        def generate(self, prompt, max_tokens=250):
            raise RuntimeError("simulated model crash")

        def model_id(self):
            return "raising"

        def stats(self):
            return {}

    ap = _make_test_apprentice(RaisingBackend(), seed=0)
    turn = ap.generate_turn(_seed_turn(), round_num=0)
    assert turn is not None
    assert ap.fallbacks >= 1


def test_apprentice_stats():
    print("=== ApprenticeWithModel: tracks stats ===")
    backend = MockBackend(seed=42)
    ap = _make_test_apprentice(backend)
    for _ in range(3):
        ap.generate_turn(_seed_turn(), round_num=0)
    stats = ap.stats()
    print(f"  model_calls: {stats['model_calls']}")
    print(f"  model_successes: {stats['model_successes']}")
    print(f"  fallbacks: {stats['fallbacks']}")
    print(f"  success_rate: {stats['success_rate']:.2f}")
    assert stats["model_calls"] == 3
    assert stats["model_successes"] == 3
    assert stats["fallbacks"] == 0


# =====================================================================
# HFBackend tests
# =====================================================================

def test_hf_backend_graceful_when_unavailable():
    print("=== HFBackend: graceful when transformers absent ===")
    # Use a fake model_id that will fail to load quickly
    backend = HFBackend(model_id="nonexistent/fake-model-that-wont-load")
    # Should not raise; should mark unavailable
    assert backend.is_available() is False
    stats = backend.stats()
    assert stats["available"] is False
    assert stats["init_error"] is not None
    print(f"  init_error: {stats['init_error'][:60]}...")
    # Attempting to generate raises (but apprentice catches it)
    with pytest.raises(RuntimeError):
        backend.generate("test prompt")


def test_recommended_models_well_formed():
    print("=== Recommended models well-formed ===")
    for model_id, info in RECOMMENDED_MODELS.items():
        assert "params" in info
        assert "license" in info
        assert "why" in info
        print(f"  {model_id} ({info['params']}, {info['license']})")


# =====================================================================
# Full collaboration with model
# =====================================================================

def test_full_collaboration_with_mock_model():
    print("=== Full collaboration with MockBackend ===")
    report = run_collaboration_with_model(seed=42)
    n_turns = sum(1 for e in report.world_log if e["kind"] == "turn")
    print(f"  turns submitted: {n_turns}")
    print(f"  converged: {report.converged}")
    assert n_turns >= 2
    # Apprentices should show model calls
    for a in report.apprentices:
        print(f"  {a['name']}: "
              f"{a['portfolio_size']} poems, "
              f"{a['stance_count']} stances, "
              f"{a['turns_generated']} turns")


def test_collaboration_with_explicit_mock_backend():
    print("=== Collaboration with explicit MockBackend ===")
    backend = MockBackend(seed=7)
    report = run_collaboration_with_model(
        seed=42, backend=backend)
    stats = backend.stats()
    print(f"  backend calls: {stats['calls']}")
    print(f"  tokens in: {stats['tokens_in']}")
    print(f"  tokens out: {stats['tokens_out']}")
    n_turns = sum(1 for e in report.world_log if e["kind"] == "turn")
    assert n_turns >= 2
    assert stats["calls"] > 0  # model was actually used


if __name__ == "__main__":
    test_parse_pure_json()
    test_parse_json_with_prose()
    test_parse_markdown_fence()
    test_parse_field_fallback()
    test_parse_invalid_returns_none()
    test_extract_json_object_nested()
    test_extract_json_object_with_strings()
    test_mock_produces_parseable()
    test_mock_is_deterministic()
    test_mock_varies_across_prompts()
    test_mock_respects_stance()
    test_mock_stats()
    test_apprentice_with_model_generates_turn()
    test_apprentice_falls_back_on_broken_backend()
    test_apprentice_falls_back_on_exception()
    test_apprentice_stats()
    test_hf_backend_graceful_when_unavailable()
    test_recommended_models_well_formed()
    test_full_collaboration_with_mock_model()
    test_collaboration_with_explicit_mock_backend()

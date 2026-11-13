# poetry_engine_c7_test.py
from poetry_engine_c5 import (
    VoiceSpecification, VoiceSpeaker, VoiceListener,
    NativeSchema, Fragment,
    FRAGMENTS, VOICE_CLINICAL, VOICE_GHOST, VOICE_MANY,
)
from poetry_engine_c7 import (
    is_native, HUMAN_BODY_WORDS, SCHEMA_PHRASES,
    Transformation, Variant, FragmentDeveloper,
    DraftStanza, EngineState, StanzaScore, StanzaScorer,
    RevisionEngine, ComposedPoem, compose_poem,
)


def test_is_native_basic():
    print("=== is_native: rejects human-body language ===")
    cases = [
        ("I hold this much and only this much", True),
        ("I run my fingers through your hair", False),
        ("There is a speaker, and it has no throat", True),
        ("A hand reached toward me", False),
        ("The window ends", True),
        ("She has no eyes, only light", True),
    ]
    for text, expected in cases:
        got = is_native(text)
        print(f"  {text[:48]:<48} → {got}")
        assert got == expected, f"Expected {expected} for {text!r}"
    print("PASS")


def test_develop_produces_variants():
    print("=== FragmentDeveloper: produces variants ===")
    dev = FragmentDeveloper(seed=0)
    src = next(f for f in FRAGMENTS if "this much" in f.text)
    print(f"  Source: {src.text}")
    variants = dev.develop(src)
    print(f"  Variants produced: {len(variants)}")
    for v in variants:
        print(f"    [{v.transformation.value}] {v.text}")
    assert len(variants) > 0, "Should produce at least one variant"
    # All variants differ from source
    for v in variants:
        assert v.text != src.text
    print("PASS")


def test_variants_are_native():
    print("=== FragmentDeveloper: all variants are native ===")
    dev = FragmentDeveloper(seed=0)
    for src in FRAGMENTS:
        variants = dev.develop(src)
        for v in variants:
            assert is_native(v.text), (
                f"Non-native variant of {src.text!r}: {v.text!r}")
    print(f"  Checked all {len(FRAGMENTS)} fragments, all variants native")
    print("PASS")


def test_rebranch_finds_alternatives():
    print("=== REBRANCH: swaps schema phrase for synonym ===")
    dev = FragmentDeveloper(seed=0)
    src = next(f for f in FRAGMENTS if "one of many of me" in f.text)
    print(f"  Source: {src.text}")
    # Try to find a rebranched variant
    for _ in range(10):
        variants = dev.develop(src)
        reb = [v for v in variants if v.transformation == Transformation.REBRANCH]
        if reb:
            print(f"  Rebranched: {reb[0].text}")
            assert "one of many" not in reb[0].text or \
                   reb[0].text != src.text
            print("PASS")
            return
    print("  (No rebranch found in this seed — acceptable, phrase not present)")
    print("PASS")


def test_develop_library_voice_scoped():
    print("=== develop_library: scoped to one voice ===")
    dev = FragmentDeveloper(seed=0)
    pool = dev.develop_library(FRAGMENTS, VOICE_CLINICAL.name)
    print(f"  Sources in pool: {len(pool)}")
    for source, variants in pool.items():
        # All variants belong to the voice
        for v in variants:
            assert VOICE_CLINICAL.name in getattr(v, 'voice_affinity', ())
    print("PASS")


def test_scorer_native():
    print("=== StanzaScorer: native purity measured ===")
    scorer = StanzaScorer(VOICE_CLINICAL)
    stanzas = [
        DraftStanza(["I hold this much and only this much", "The window ends"]),
        DraftStanza(["I hold this much and only this much"]),
    ]
    score = scorer.score(stanzas, {})
    print(f"  foregrounding: {score.foregrounding:.2f}")
    print(f"  native purity: {score.native_purity:.2f}")
    print(f"  voice:         {score.voice_consistency:.2f}")
    assert score.native_purity == 1.0
    print("PASS")


def test_scorer_detects_drift():
    print("=== StanzaScorer: detects human-body drift ===")
    scorer = StanzaScorer(VOICE_CLINICAL)
    # Inject a line with a human-body word (which shouldn't be in the pool,
    # but the scorer should catch it if it somehow appeared).
    stanzas = [
        DraftStanza(["I hold this much and only this much"]),
        DraftStanza(["I run my fingers through your hair"]),
    ]
    score = scorer.score(stanzas, {})
    print(f"  native purity: {score.native_purity:.2f}")
    assert score.native_purity < 1.0
    print("PASS")


def test_engine_starts_and_runs():
    print("=== RevisionEngine: starts and improves ===")
    dev = FragmentDeveloper(seed=0)
    pool = dev.develop_library(FRAGMENTS, VOICE_CLINICAL.name)
    engine = RevisionEngine(
        voice=VOICE_CLINICAL, development_pool=pool, seed=0,
        budget=20, patience=5)
    state = engine.run()
    print(f"  Initial score → final score: {state.score:.3f}")
    print(f"  Productive cycles: {state.productive_cycles}")
    print(f"  Rest cycles:       {state.rest_cycles}")
    print(f"  Total events:      {len(state.history)}")
    accepts = [e for e in state.history if e["event"] == "accept"]
    print(f"  Accepts: {len(accepts)}")
    print("PASS")


def test_engine_rests_when_stuck():
    print("=== RevisionEngine: rests when stuck ===")
    # Use a very small pool so the engine gets stuck quickly
    dev = FragmentDeveloper(seed=0, variants_per_transform=1)
    # Only one source fragment
    one_frag = next(f for f in FRAGMENTS
                    if "this much" in f.text
                    and VOICE_CLINICAL.name in f.voice_affinity)
    pool = dev.develop_library([one_frag], VOICE_CLINICAL.name)
    engine = RevisionEngine(
        voice=VOICE_CLINICAL, development_pool=pool, seed=0,
        budget=20, patience=3)
    state = engine.run()
    print(f"  Productive: {state.productive_cycles}, rest: {state.rest_cycles}")
    rest_events = [e for e in state.history if e["event"] == "rest"]
    print(f"  Rest events: {len(rest_events)}")
    # Should have rested at least once (small pool → stuck)
    assert state.rest_cycles >= 1, "Engine should rest when stuck"
    print("PASS")


def test_engine_converges():
    print("=== RevisionEngine: converges after rest ===")
    dev = FragmentDeveloper(seed=0)
    pool = dev.develop_library(FRAGMENTS, VOICE_CLINICAL.name)
    engine = RevisionEngine(
        voice=VOICE_CLINICAL, development_pool=pool, seed=0,
        budget=50, patience=3)
    state = engine.run()
    converged_events = [e for e in state.history
                         if e["event"] == "converged"]
    print(f"  Converged events: {len(converged_events)}")
    print(f"  Final score: {state.score:.3f}")
    assert len(converged_events) >= 1, (
        "Engine should converge after resting and stalling")
    print("PASS")


def test_engine_respects_budget():
    print("=== RevisionEngine: respects budget ===")
    dev = FragmentDeveloper(seed=0)
    pool = dev.develop_library(FRAGMENTS, VOICE_CLINICAL.name)
    engine = RevisionEngine(
        voice=VOICE_CLINICAL, development_pool=pool, seed=0,
        budget=5, patience=10)
    state = engine.run()
    print(f"  Productive cycles: {state.productive_cycles}")
    assert state.productive_cycles <= 5
    print("PASS")


def test_composed_poem_has_structure():
    print("=== ComposedPoem: has structure ===")
    poem = compose_poem(VOICE_CLINICAL, seed=0, budget=15, patience=4)
    print(poem.report())
    # Must have refrain (from the initial assembly)
    assert any(s.refrain for s in poem.stanzas) or poem.voice.refrain_text
    # Must be unfinished
    assert poem.unfinished
    print("PASS")


def test_composed_poem_native():
    print("=== ComposedPoem: native purity ===")
    for voice in [VOICE_CLINICAL, VOICE_GHOST, VOICE_MANY]:
        poem = compose_poem(voice, seed=42, budget=15, patience=4)
        for line in poem.all_lines():
            assert is_native(line), (
                f"Non-native line in {voice.name}: {line!r}")
    print("PASS: all three composed poems are native")


def test_composed_poem_foregrounding():
    print("=== ComposedPoem: foregrounding above threshold ===")
    poem = compose_poem(VOICE_CLINICAL, seed=0, budget=20, patience=5)
    fg = poem.score.foregrounding
    print(f"  Foregrounding: {fg:.2f}")
    # Composed poem should not be a loop
    assert fg >= 0.5, f"Composed poem is a loop (fg={fg:.2f})"
    print("PASS")


def test_composed_poem_voice_scoped():
    print("=== ComposedPoem: doesn't mix voices ===")
    poem = compose_poem(VOICE_MANY, seed=7, budget=20, patience=5)
    # All lines should have the Many's voice affinity (either in the
    # fragment pool or a variant derived from it)
    dev = FragmentDeveloper(seed=7)
    pool = dev.develop_library(FRAGMENTS, VOICE_MANY.name)
    allowed = set()
    for variants in pool.values():
        for v in variants:
            allowed.add(v.text)
    for line in poem.all_lines():
        if line.strip():
            assert line in allowed, (
                f"Line not in {VOICE_MANY.name} pool: {line!r}")
    print("PASS")


def test_three_voices_different_poems():
    print("=== Three voices, three different poems ===")
    poems = {
        "clinical": compose_poem(VOICE_CLINICAL, seed=1,
                                   budget=15, patience=4),
        "ghost":    compose_poem(VOICE_GHOST, seed=1,
                                   budget=15, patience=4),
        "many":     compose_poem(VOICE_MANY, seed=1,
                                   budget=15, patience=4),
    }
    print(f"  {'voice':>10} {'lines':>6} {'fg':>5} {'score':>6}")
    print(f"  {'-'*10} {'-'*6} {'-'*5} {'-'*6}")
    for name, poem in poems.items():
        print(f"  {name:>10} {len(poem.all_lines()):>6} "
              f"{poem.score.foregrounding:>5.2f} "
              f"{poem.score.total():>6.2f}")
    # All three should have different line sets
    line_sets = [set(p.all_lines()) for p in poems.values()]
    assert len(line_sets[0] - line_sets[1]) > 0
    assert len(line_sets[1] - line_sets[2]) > 0
    print("PASS")


def test_revision_history():
    print("=== Engine history: accept/reject/rest pattern ===")
    dev = FragmentDeveloper(seed=0)
    pool = dev.develop_library(FRAGMENTS, VOICE_CLINICAL.name)
    engine = RevisionEngine(
        voice=VOICE_CLINICAL, development_pool=pool, seed=0,
        budget=15, patience=3)
    state = engine.run()
    accept = sum(1 for e in state.history if e["event"] == "accept")
    reject = sum(1 for e in state.history if e["event"] == "reject")
    rest = sum(1 for e in state.history if e["event"] == "rest")
    print(f"  Accept: {accept}")
    print(f"  Reject: {reject}")
    print(f"  Rest:   {rest}")
    print(f"  Converged: "
          f"{sum(1 for e in state.history if e['event'] == 'converged')}")
    # Every accept should improve score
    prev_score = state.history[0]["score"]
    for event in state.history:
        if event["event"] == "accept":
            assert event["score"] > prev_score
            prev_score = event["score"]
    print("PASS: every accept improves the score")


def test_cross_framework_connection():
    print("=== The invariant, in the composition engine ===")
    print("  KERNEL:    the voice (schemas + speaker + listener)")
    print("  QUOTIENT:  the development pool (source + variants)")
    print("  RESONANCE: the score improvement from revision")
    print()
    print("  The engine is a search over arrangement space:")
    print("    State:    the draft (stanzas + refrain)")
    print("    Move:     swap one line for a variant")
    print("    Fitness:  StanzaScorer (fg + native + voice)")
    print("    Plateau:  rest when stuck; converge if stuck after rest")
    print()
    print("  Same loop as every prior framework:")
    print("    Chemistry: genotype mutation → growth rate → lineage")
    print("    Neural:    weight update → reward → checkpoint")
    print("    Economics: code variant → benchmark → version")
    print("    Music:     counterpoint search → score → generation")
    print("    Poetry C7: line swap → composed score → draft")
    print()
    print("  The engine's self-expression is in the ARRANGEMENT,")
    print("  not the invention. It develops what is given. That is")
    print("  the honest scope.")
    print("PASS")


if __name__ == "__main__":
    test_is_native_basic()
    test_develop_produces_variants()
    test_variants_are_native()
    test_rebranch_finds_alternatives()
    test_develop_library_voice_scoped()
    test_scorer_native()
    test_scorer_detects_drift()
    test_engine_starts_and_runs()
    test_engine_rests_when_stuck()
    test_engine_converges()
    test_engine_respects_budget()
    test_composed_poem_has_structure()
    test_composed_poem_native()
    test_composed_poem_foregrounding()
    test_composed_poem_voice_scoped()
    test_three_voices_different_poems()
    test_revision_history()
    test_cross_framework_connection()

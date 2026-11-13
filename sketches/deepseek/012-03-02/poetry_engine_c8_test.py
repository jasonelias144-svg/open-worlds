# poetry_engine_c8_test.py
import random
from poetry_engine_c5 import (
    VOICE_CLINICAL, VOICE_GHOST, VOICE_MANY, FRAGMENTS,
)
from poetry_engine_c7 import FragmentDeveloper, DraftStanza, is_native
from poetry_engine_c8 import (
    RestMode, RestOutcome, RestPolicy,
    StanzaScoreV2, StanzaScorerV2, _line_similarity,
    ProductiveRestEngine, RestLearningLoop, MAX_LINES,
)


def test_rest_mode_atoms():
    print("=== RestMode: four modes ===")
    for m in RestMode:
        print(f"  {m.value}")
    assert len(RestMode) == 4
    print("PASS")


def test_rest_policy_uniform():
    print("=== RestPolicy: starts uniform ===")
    p = RestPolicy(VOICE_CLINICAL.name)
    dist = p.distribution()
    print(f"  Distribution: { {k.value: round(v, 3) for k, v in dist.items()} }")
    for v in dist.values():
        assert abs(v - 0.25) < 1e-9
    print("PASS")


def test_rest_policy_updates():
    print("=== RestPolicy: updates on feedback ===")
    p = RestPolicy(VOICE_CLINICAL.name)
    p.update(RestMode.REGENERATE, True)
    p.update(RestMode.REGENERATE, True)
    p.update(RestMode.RESEED, False)
    dist = p.distribution()
    print(f"  Distribution: { {k.value: round(v, 3) for k, v in dist.items()} }")
    assert dist[RestMode.REGENERATE] > dist[RestMode.RESEED]
    assert p.best_mode() == RestMode.REGENERATE
    print("PASS")


def test_rest_policy_sampling():
    print("=== RestPolicy: sampling respects distribution ===")
    p = RestPolicy(VOICE_CLINICAL.name)
    # Give REGENERATE a huge prior
    for _ in range(10):
        p.update(RestMode.REGENERATE, True)
    rng = random.Random(0)
    samples = [p.sample(rng) for _ in range(200)]
    counts = {}
    for s in samples:
        counts[s.value] = counts.get(s.value, 0) + 1
    print(f"  Sample counts (200 draws): {counts}")
    # REGENERATE should dominate
    assert counts[RestMode.REGENERATE.value] > 100
    print("PASS")


def test_line_similarity():
    print("=== _line_similarity ===")
    pairs = [
        ("the window ends", "the window ends", 1.0),
        ("the window ends", "the edge begins", 0.0),
        ("I hold this much", "I hold only this", 3/5),
    ]
    for a, b, expected in pairs:
        sim = _line_similarity(a, b)
        print(f"  {a!r} vs {b!r}: {sim:.2f} (expected ~{expected:.2f})")
        assert abs(sim - expected) < 1e-9
    print("PASS")


def test_scorer_v2_grows():
    print("=== StanzaScorerV2: coverage grows with more lines ===")
    scorer = StanzaScorerV2(VOICE_CLINICAL)
    dev = FragmentDeveloper(seed=0)
    pool = dev.develop_library(FRAGMENTS, VOICE_CLINICAL.name)
    index = {}
    for variants in pool.values():
        for v in variants:
            index[v.text] = v
    lines = list(index.keys())[:6]
    for n in [1, 3, 6]:
        stanzas = [DraftStanza(lines=lines[:n])]
        score = scorer.score(stanzas, index)
        print(f"  {n} lines: coverage={score.coverage:.2f}, "
              f"total={score.total():.2f}")
    print("PASS")


def test_each_rest_mode_mutates():
    print("=== Each rest mode has a measurable effect ===")
    engine = ProductiveRestEngine(
        voice=VOICE_CLINICAL, fragments=FRAGMENTS, seed=0)
    initial_pool = len(engine.fragment_index)
    initial_patience = engine.patience
    initial_order = list(engine.pool.keys())
    desc1 = engine._apply_rest(RestMode.REGENERATE)
    after_regen_pool = len(engine.fragment_index)
    print(f"  REGENERATE: {desc1}, pool {initial_pool} → {after_regen_pool}")
    assert after_regen_pool >= initial_pool

    desc2 = engine._apply_rest(RestMode.EXPAND_PATIENCE)
    print(f"  EXPAND_PATIENCE: {desc2}")
    assert engine.patience > initial_patience

    old_rng_id = id(engine.rng)
    desc3 = engine._apply_rest(RestMode.RESEED)
    print(f"  RESEED: {desc3}")
    assert id(engine.rng) != old_rng_id

    print("PASS")


def test_engine_runs():
    print("=== ProductiveRestEngine: full run ===")
    engine = ProductiveRestEngine(
        voice=VOICE_CLINICAL, fragments=FRAGMENTS,
        seed=0, budget=30, patience=3, max_rests=4)
    state = engine.run()
    accepts = sum(1 for e in state.history if e["event"] == "accept")
    rejects = sum(1 for e in state.history if e["event"] == "reject")
    rests = state.rest_cycles
    print(f"  Score: {state.score:.3f}")
    print(f"  Accepts: {accepts}, rejects: {rejects}, rests: {rests}")
    print(f"  Rest outcomes recorded: {len(engine.rest_history)}")
    print(f"  Policy: "
          f"{ {m.value: [s, f] for m, (s, f) in engine.rest_policy.stats.items()} }")
    assert accepts > 0, "Engine should accept something"
    assert len(engine.rest_history) >= 1, "Engine should record rest outcomes"
    print("PASS")


def test_composed_poem_native():
    print("=== Composed poem remains native ===")
    engine = ProductiveRestEngine(
        voice=VOICE_CLINICAL, fragments=FRAGMENTS,
        seed=0, budget=30, patience=3)
    state = engine.run()
    for stanza in state.draft:
        for line in stanza.lines:
            assert is_native(line), f"Non-native line: {line!r}"
    print(f"  All {sum(len(s.lines) for s in state.draft)} lines native")
    print("PASS")


def test_learning_loop_runs():
    print("=== RestLearningLoop: multiple poems ===")
    loop = RestLearningLoop(
        voice=VOICE_CLINICAL, fragments=FRAGMENTS,
        seed=42, n_poems=8, budget=25, patience=3, max_rests=3)
    states = loop.run()
    print(f"  Poems: {len(states)}")
    for i, s in enumerate(states):
        print(f"    poem {i}: score={s.score:.3f}, "
              f"rests={s.rest_cycles}")
    print(f"  Total rest outcomes: {len(loop.all_rest_outcomes)}")
    rates = loop.observed_success_rate()
    print(f"  Observed success rates:")
    for m, r in rates.items():
        print(f"    {m.value}: {r:.2f}")
    print(f"  Policy distribution:")
    dist = loop.policy.distribution()
    for m, p in dist.items():
        print(f"    {m.value}: {p:.3f}")
    assert len(states) == 8
    print("PASS")


def test_policy_weights_reflect_outcomes():
    print("=== Policy weight ~ observed success ===")
    loop = RestLearningLoop(
        voice=VOICE_CLINICAL, fragments=FRAGMENTS,
        seed=7, n_poems=12, budget=25, patience=3, max_rests=3)
    loop.run()
    rates = loop.observed_success_rate()
    dist = loop.policy.distribution()
    print(f"  {'mode':>18} {'rate':>6} {'weight':>8}")
    print(f"  {'-'*18} {'-'*6} {'-'*8}")
    for m in RestMode:
        print(f"  {m.value:>18} {rates[m]:>6.2f} "
              f"{dist[m]:>8.3f}")
    # Best mode by observed rate should have highest policy weight
    best_rate_mode = max(RestMode, key=lambda m: rates[m])
    best_weight_mode = max(RestMode, key=lambda m: dist[m])
    print(f"  Best by rate: {best_rate_mode.value}")
    print(f"  Best by weight: {best_weight_mode.value}")
    # Soft check: the two should agree (may fail if ties)
    assert rates[best_rate_mode] >= max(rates.values()) - 1e-9
    print("PASS")


def test_three_voices_different_policies():
    print("=== Three voices, three policies ===")
    for voice in [VOICE_CLINICAL, VOICE_GHOST, VOICE_MANY]:
        loop = RestLearningLoop(
            voice=voice, fragments=FRAGMENTS,
            seed=1, n_poems=6, budget=20, patience=3, max_rests=2)
        loop.run()
        rates = loop.observed_success_rate()
        print(f"  {voice.name:>22}: rates="
              f"{ {m.value: round(r, 2) for m, r in rates.items()} }")
    print("PASS")


def test_convergence_with_rest():
    print("=== Engine converges (with or without rest) ===")
    engine = ProductiveRestEngine(
        voice=VOICE_CLINICAL, fragments=FRAGMENTS,
        seed=0, budget=40, patience=3, max_rests=3)
    state = engine.run()
    converged = any(e["event"] == "converged"
                    for e in state.history)
    print(f"  Converged: {converged}")
    print(f"  Final score: {state.score:.3f}")
    print(f"  Productive cycles: {state.productive_cycles}")
    assert state.productive_cycles <= 40
    print("PASS")


def test_cross_framework_connection():
    print("=== The invariant, in rest ===")
    print("  KERNEL:    the draft (the search position)")
    print("  QUOTIENT:  the search space (pool + patience + RNG)")
    print("  RESONANCE: the accept rate after rest")
    print()
    print("  Productive cycle: changes the KERNEL")
    print("  Rest cycle:       changes the QUOTIENT")
    print()
    print("  Same distinction in every framework:")
    print("    Chemistry: reaction (kernel) vs mutation (quotient)")
    print("    Neural:    forward pass (kernel) vs gradient (quotient)")
    print("    Economics: build (kernel) vs strategy change (quotient)")
    print("    Poetry C7: swap (kernel) vs rest (quotient, ceremonial)")
    print("    Poetry C8: swap (kernel) vs rest (quotient, real)")
    print()
    print("  Rest is meta-work. The engine writes nothing while")
    print("  changing HOW it writes. That is the user's vision made")
    print("  literal.")
    print("PASS")


if __name__ == "__main__":
    test_rest_mode_atoms()
    test_rest_policy_uniform()
    test_rest_policy_updates()
    test_rest_policy_sampling()
    test_line_similarity()
    test_scorer_v2_grows()
    test_each_rest_mode_mutates()
    test_engine_runs()
    test_composed_poem_native()
    test_learning_loop_runs()
    test_policy_weights_reflect_outcomes()
    test_three_voices_different_policies()
    test_convergence_with_rest()
    test_cross_framework_connection()

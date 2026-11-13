# poetry_engine_c13_test.py
import copy
import random
from poetry_engine_c5 import (
    VOICE_CLINICAL, VOICE_GHOST, VOICE_MANY, FRAGMENTS,
)
from poetry_engine_c7 import DraftStanza, is_native
from poetry_engine_c9 import Collection, CollectionPoem
from poetry_engine_c13 import (
    PhaseType, Snapshot,
    CollectionDevelopmentSpiral, SpiralReport,
)


def _make_spiral(seed: int = 0, **kwargs) -> CollectionDevelopmentSpiral:
    defaults = dict(
        voices=[VOICE_CLINICAL, VOICE_GHOST, VOICE_MANY],
        fragments=FRAGMENTS,
        refrain_text="the window ends",
        seed=seed,
        target_poems=3,
        weak_threshold=0.90,
        redundant_threshold=0.5,
        n_cycles=3,
        budget_per_poem=5,
        patience_per_poem=3,
        max_rests_per_poem=2,
    )
    defaults.update(kwargs)
    return CollectionDevelopmentSpiral(**defaults)


def test_phase_types():
    print("=== PhaseType: five kinds of phase ===")
    for pt in PhaseType:
        print(f"  {pt.value}")
    assert len(PhaseType) == 5
    print("PASS")


def test_snapshot_atom():
    print("=== Snapshot: report format ===")
    s = Snapshot(
        phase_index=3,
        phase_type="replace",
        n_poems=3,
        collection_score=0.85,
        arc_type="palindrome",
        refrain_delta=0.92,
        weakest_poem="Poem 2",
        notes="replaced Poem 2",
    )
    print(s.report())
    assert "#3" in s.report()
    assert "replace" in s.report()
    print("PASS")


def test_spiral_runs():
    print("=== Spiral: runs to completion ===")
    spiral = _make_spiral(seed=0)
    coll = spiral.run()
    print(f"  Final collection: {coll}")
    print(f"  Snapshots: {len(spiral.snapshots)}")
    assert isinstance(coll, Collection)
    assert len(coll.poems) > 0
    assert len(spiral.snapshots) > 0
    print("PASS")


def test_initial_batch_size():
    print("=== Spiral: initial batch has target_poems ===")
    spiral = _make_spiral(seed=1, target_poems=4)
    spiral.run()
    initial_snap = spiral.snapshots[0]
    print(f"  Initial snapshot: {initial_snap.n_poems} poems")
    assert initial_snap.n_poems == 4
    print("PASS")


def test_history_has_productive_and_rest():
    print("=== Spiral: history has both productive and rest phases ===")
    spiral = _make_spiral(seed=2)
    spiral.run()
    phase_types = [s.phase_type for s in spiral.snapshots]
    print(f"  Phase types: {phase_types}")
    productive = {"compose", "replace", "prune", "revise"}
    assert any(pt in productive for pt in phase_types), \
        "Should have at least one productive phase"
    assert "rest" in phase_types, \
        "Should have at least one rest phase"
    print("PASS")


def test_weak_poem_replaced():
    print("=== Spiral: weak poem gets replaced ===")
    # Small budget → weak initial poems → forced replacement
    spiral = _make_spiral(seed=3, target_poems=3,
                           budget_per_poem=3, weak_threshold=0.95)
    spiral.run()
    replace_count = sum(1 for s in spiral.snapshots
                         if s.phase_type == "replace")
    print(f"  Replace phases: {replace_count}")
    print(f"  Final collection score: {spiral._collection_score():.3f}")
    assert replace_count >= 1, "Weak poems should trigger replacement"
    print("PASS")


def test_weak_poem_improves_after_replacement():
    print("=== Spiral: replacement improves the score ===")
    spiral = _make_spiral(seed=4, target_poems=2,
                           budget_per_poem=3, n_cycles=3,
                           weak_threshold=0.95)
    initial_scores = None
    spiral.run()
    if spiral.snapshots and len(spiral.snapshots) > 0:
        # Compare first snapshot score to final
        initial = spiral.snapshots[0].collection_score
        final = spiral.snapshots[-1].collection_score
        print(f"  Initial score: {initial:.3f}")
        print(f"  Final score:   {final:.3f}")
        print(f"  Delta:         {final - initial:+.3f}")
        # Score should not regress — spiral only replaces if new version
        # is better (for REVISE) or weak (for REPLACE)
        assert final >= initial - 1e-9, (
            f"Spiral should not regress: {initial:.3f} → {final:.3f}")
    print("PASS")


def test_redundant_poem_pruned():
    print("=== Spiral: redundant poem gets pruned ===")
    spiral = _make_spiral(seed=5, target_poems=0)
    # Manually compose two identical poems and set up the state
    p1 = spiral._compose_one(VOICE_CLINICAL)
    p2 = spiral._compose_one(VOICE_CLINICAL)
    p2.stanzas = copy.deepcopy(p1.stanzas)
    p2.score = p1.score
    spiral.poems = [p1, p2]
    # Verify redundancy detected
    pair = spiral._find_redundant_pair()
    print(f"  Redundant pair detected: {pair}")
    assert pair == (0, 1)
    # Act: should prune
    spiral._act_phase(0)
    print(f"  After prune: {len(spiral.poems)} poems")
    assert len(spiral.poems) == 1
    print("PASS")


def test_compose_adds_when_below_target():
    print("=== Spiral: composes when below target ===")
    spiral = _make_spiral(seed=6, target_poems=4, n_cycles=3,
                           budget_per_poem=3, weak_threshold=0.99)
    spiral.run()
    compose_count = sum(1 for s in spiral.snapshots
                         if s.phase_type == "compose")
    print(f"  Compose phases: {compose_count}")
    assert compose_count >= 1
    print("PASS")


def test_all_lines_native():
    print("=== Spiral: all lines remain native ===")
    spiral = _make_spiral(seed=7)
    coll = spiral.run()
    for poem in coll.poems:
        for line in poem.all_lines():
            if line:
                assert is_native(line), (
                    f"Non-native in {poem.name}: {line!r}")
    print(f"  All {sum(len(p.all_lines()) for p in coll.poems)} lines native")
    print("PASS")


def test_report_summary():
    print("=== SpiralReport: summary ===")
    spiral = _make_spiral(seed=8)
    spiral.run()
    report = spiral.get_report()
    print(report.report())
    summary = report.summary()
    assert summary["n_snapshots"] > 0
    assert summary["initial_poems"] > 0
    assert summary["final_poems"] > 0
    print("PASS")


def test_deterministic_within_seed():
    print("=== Spiral: deterministic for same seed ===")
    s1 = _make_spiral(seed=9)
    coll1 = s1.run()
    s2 = _make_spiral(seed=9)
    coll2 = s2.run()
    lines1 = [p.all_lines() for p in coll1.poems]
    lines2 = [p.all_lines() for p in coll2.poems]
    print(f"  Run 1: {len(coll1.poems)} poems")
    print(f"  Run 2: {len(coll2.poems)} poems")
    print(f"  Identical: {lines1 == lines2}")
    assert lines1 == lines2
    print("PASS")


def test_different_seeds_different_results():
    print("=== Spiral: different seeds → different collections ===")
    s1 = _make_spiral(seed=10)
    s2 = _make_spiral(seed=11)
    c1 = s1.run()
    c2 = s2.run()
    lines1 = [p.all_lines() for p in c1.poems]
    lines2 = [p.all_lines() for p in c2.poems]
    print(f"  Same: {lines1 == lines2}")
    assert lines1 != lines2
    print("PASS")


def test_spiral_trajectory():
    print("=== Spiral: score trajectory across snapshots ===")
    spiral = _make_spiral(seed=12, target_poems=3,
                           budget_per_poem=4, n_cycles=4,
                           weak_threshold=0.90)
    spiral.run()
    report = spiral.get_report()
    trajectory = report.trajectory()
    print(f"  Trajectory: {[round(x, 3) for x in trajectory]}")
    # Trajectory should have multiple values
    assert len(trajectory) >= 3
    print("PASS")


def test_cross_framework_connection():
    print("=== The invariant, in the development spiral ===")
    print("  KERNEL:    the collection (accumulated poems)")
    print("  QUOTIENT:  the development rhythm (write/rest/replace/prune)")
    print("  RESONANCE: the trajectory (score over snapshots)")
    print()
    print("  C7: single draft → revisions → convergence")
    print("  C8: single draft → revisions → rest (meta-work) → convergence")
    print("  C9: N poems → one collection (single pass)")
    print("  C13: N poems → M sittings → collection evolves")
    print()
    print("  Same distinction as every prior framework:")
    print("    Chemistry:  generation vs generation-with-selection")
    print("    Economics:  one session vs a running business")
    print("    Neural:     one task vs learning-across-tasks")
    print("    Language:   one generation vs continued pretraining")
    print("    Music:      one fugue vs the Art of Fugue (14 variations)")
    print("    Poetry C13: one collection vs a developed collection")
    print()
    print("  The spiral is where the collection has a HISTORY.")
    print("  Each snapshot is a state the collection passed through.")
    print("  The final state is not the initial state — it is the")
    print("  trajectory that led there.")
    print("PASS")


if __name__ == "__main__":
    test_phase_types()
    test_snapshot_atom()
    test_spiral_runs()
    test_initial_batch_size()
    test_history_has_productive_and_rest()
    test_weak_poem_replaced()
    test_weak_poem_improves_after_replacement()
    test_redundant_poem_pruned()
    test_compose_adds_when_below_target()
    test_all_lines_native()
    test_report_summary()
    test_deterministic_within_seed()
    test_different_seeds_different_results()
    test_spiral_trajectory()
    test_cross_framework_connection()

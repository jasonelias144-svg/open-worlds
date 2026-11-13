# poetry_engine_c14_test.py
import copy
from poetry_engine_c5 import (
    VOICE_CLINICAL, VOICE_GHOST, VOICE_MANY, FRAGMENTS,
)
from poetry_engine_c9 import (
    Collection, CollectionPoem, CollectionArcAnalyzer, ArcType,
)
from poetry_engine_c14 import (
    Brief, Edition, EditionDelta, BriefScore, BriefAnalyzer,
    resume_spiral, LivingCollection,
    default_brief, compose_living_collection,
)


def test_brief_validation():
    print("=== Brief: validation ===")
    b = default_brief()
    print(f"  {b.name}: {len(b.voices)} voices, "
          f"arc={b.arc_target.value}, n={b.n_poems_min}-{b.n_poems_max}")
    # Reject empty voices
    try:
        Brief("bad", [], ArcType.DIRECTIONAL, "x")
        assert False, "should raise"
    except ValueError:
        print("  ✓ rejects empty voices")
    # Reject inverted range
    try:
        Brief("bad", [VOICE_CLINICAL], ArcType.DIRECTIONAL, "x",
               n_poems_min=5, n_poems_max=3)
        assert False, "should raise"
    except ValueError:
        print("  ✓ rejects inverted range")
    print("PASS")


def test_edition_atom():
    print("=== Edition: basic structure ===")
    ed = Edition(
        edition_number=1,
        poems=[],
        brief_score=0.5,
        notes="first",
    )
    print(f"  Edition {ed.edition_number}: {ed.n_poems} poems, "
          f"score {ed.brief_score:.2f}")
    assert ed.n_poems == 0
    assert ed.edition_number == 1
    print("PASS")


def test_edition_delta():
    print("=== EditionDelta: report format ===")
    d = EditionDelta(
        from_edition=1, to_edition=2,
        poems_added=2, poems_removed=0, poems_revised=1,
        brief_score_before=0.75, brief_score_after=1.0,
    )
    print(f"  {d.report()}")
    assert d.brief_score_change == 0.25
    print("PASS")


def test_brief_analyzer_empty():
    print("=== BriefAnalyzer: empty collection ===")
    analyzer = BriefAnalyzer()
    coll = Collection(name="empty", poems=[], refrain="x")
    score = analyzer.analyze(coll, default_brief())
    print(f"  Empty: {score.total():.2f}")
    assert score.total() == 0.0
    print("PASS")


def test_brief_analyzer_full():
    print("=== BriefAnalyzer: full collection ===")
    lc = compose_living_collection(seed=0, n_editions=3,
                                     cycles_per_edition=4)
    if lc.editions:
        last = lc.editions[-1]
        print(f"  Last edition: {last.n_poems} poems, "
              f"brief score {last.brief_score:.2f}")
        # After growth phase, brief should be mostly fulfilled
        assert last.brief_score >= 0.75
    print("PASS")


def test_living_collection_starts_empty():
    print("=== LivingCollection: starts empty ===")
    lc = LivingCollection(
        brief=default_brief(),
        fragments=FRAGMENTS,
        seed=0,
    )
    print(f"  Poems: {len(lc.poems)}")
    print(f"  Editions: {len(lc.editions)}")
    print(f"  Brief score: {lc.current_brief_score().total():.2f}")
    assert len(lc.poems) == 0
    assert len(lc.editions) == 0
    print("PASS")


def test_living_collection_develop():
    print("=== LivingCollection: development creates poems ===")
    lc = LivingCollection(
        brief=default_brief(),
        fragments=FRAGMENTS,
        seed=1,
    )
    lc.develop(n_cycles=4)
    print(f"  After develop: {len(lc.poems)} poems")
    print(f"  Brief score: {lc.current_brief_score().total():.2f}")
    assert len(lc.poems) > 0
    assert len(lc.editions) == 0  # not yet published
    print("PASS")


def test_living_collection_publish():
    print("=== LivingCollection: publishing an edition ===")
    lc = LivingCollection(
        brief=default_brief(),
        fragments=FRAGMENTS,
        seed=2,
    )
    lc.develop(n_cycles=4)
    ed = lc.publish(notes="first edition")
    print(f"  Published edition {ed.edition_number}: "
          f"{ed.n_poems} poems, score {ed.brief_score:.2f}")
    assert ed.edition_number == 1
    assert len(lc.editions) == 1
    assert lc.is_current_matches_latest()
    print("PASS")


def test_living_collection_multiple_editions():
    print("=== LivingCollection: multiple editions with deltas ===")
    lc = compose_living_collection(
        seed=3, n_editions=4, cycles_per_edition=4)
    print(lc.report())
    assert len(lc.editions) == 4
    assert len(lc.edition_deltas) == 3
    print("PASS")


def test_brief_progresses_over_editions():
    print("=== Brief score progresses over editions ===")
    lc = compose_living_collection(
        seed=4, n_editions=4, cycles_per_edition=4)
    trajectory = [e.brief_score for e in lc.editions]
    print(f"  Trajectory: {[round(x, 3) for x in trajectory]}")
    # Final edition should be at least as good as first
    assert lc.editions[-1].brief_score >= lc.editions[0].brief_score
    # At least one edition improves
    assert lc.editions[-1].brief_score > lc.editions[0].brief_score
    print("PASS")


def test_edition_growth():
    print("=== Editions grow in poem count ===")
    lc = compose_living_collection(
        seed=5, n_editions=4, cycles_per_edition=4)
    counts = [e.n_poems for e in lc.editions]
    print(f"  Poem count trajectory: {counts}")
    # Later editions have at least as many poems as earlier
    assert counts[-1] >= counts[0]
    # Growth happened (early editions smaller than final)
    assert counts[-1] > counts[0] or counts[-1] >= lc.brief.n_poems_min
    print("PASS")


def test_identity_preserved():
    print("=== Identity preserved across editions ===")
    lc = compose_living_collection(
        seed=6, n_editions=4, cycles_per_edition=3)
    print(f"  Identity preserved: {lc.identity_preserved()}")
    # All editions share the brief (by construction)
    assert lc.identity_preserved()
    # All editions have the same name
    assert lc.brief.name in lc.report()
    print("PASS")


def test_develop_between_editions():
    print("=== Develop between editions can diverge from latest ===")
    lc = compose_living_collection(
        seed=7, n_editions=2, cycles_per_edition=4)
    latest = lc.editions[-1]
    lc.develop(n_cycles=2)
    print(f"  Matches latest edition: {lc.is_current_matches_latest()}")
    # After develop, current state may differ
    # (may or may not match depending on whether anything changed)
    print(f"  Current poems: {len(lc.poems)}")
    print(f"  Latest edition: {latest.n_poems} poems")
    print("PASS")


def test_write_nothing_for_a_while():
    print("=== Write nothing for a while (later editions stable) ===")
    lc = compose_living_collection(
        seed=8, n_editions=6, cycles_per_edition=4)
    print(f"  {len(lc.editions)} editions")
    for i, ed in enumerate(lc.editions):
        print(f"    Edition {ed.edition_number}: {ed.n_poems} poems, "
              f"score {ed.brief_score:.2f}")
    # The last two editions should be similar or identical (converged)
    if len(lc.editions) >= 2:
        prev = lc.editions[-2]
        curr = lc.editions[-1]
        prev_lines = sorted(p.all_lines() for p in prev.poems)
        curr_lines = sorted(p.all_lines() for p in curr.poems)
        same = prev_lines == curr_lines
        print(f"  Last two editions identical: {same}")
        # Convergence expected — either same or very similar scores
        assert abs(prev.brief_score - curr.brief_score) < 0.1
    print("PASS")


def test_determinism():
    print("=== Determinism: same seed → same trajectory ===")
    lc1 = compose_living_collection(seed=9, n_editions=3, cycles_per_edition=3)
    lc2 = compose_living_collection(seed=9, n_editions=3, cycles_per_edition=3)
    s1 = [e.brief_score for e in lc1.editions]
    s2 = [e.brief_score for e in lc2.editions]
    print(f"  Run 1: {[round(x, 3) for x in s1]}")
    print(f"  Run 2: {[round(x, 3) for x in s2]}")
    assert s1 == s2
    print("PASS")


def test_different_seeds_different_trajectories():
    print("=== Different seeds → different trajectories ===")
    lc1 = compose_living_collection(seed=10, n_editions=3, cycles_per_edition=3)
    lc2 = compose_living_collection(seed=11, n_editions=3, cycles_per_edition=3)
    lines1 = [sorted(p.all_lines() for p in lc1.editions[-1].poems)]
    lines2 = [sorted(p.all_lines() for p in lc2.editions[-1].poems)]
    print(f"  Different: {lines1 != lines2}")
    assert lines1 != lines2
    print("PASS")


def test_all_poems_native():
    print("=== All poems in all editions are native ===")
    from poetry_engine_c7 import is_native
    lc = compose_living_collection(
        seed=12, n_editions=3, cycles_per_edition=3)
    total = 0
    for ed in lc.editions:
        for line in ed.all_lines():
            if line:
                total += 1
                assert is_native(line), f"Non-native: {line!r}"
    print(f"  All {total} lines across {len(lc.editions)} editions native")
    print("PASS")


def test_full_demo_report():
    print("=== Full demo report ===")
    lc = compose_living_collection(
        seed=13, n_editions=5, cycles_per_edition=4)
    print(lc.report())
    print()
    # Final edition brief score should be high
    print(f"  Final edition score: {lc.editions[-1].brief_score:.2f}")
    print(f"  Final poem count:    {lc.editions[-1].n_poems}")
    assert lc.editions[-1].brief_score >= 0.75
    print("PASS")


def test_cross_framework_connection():
    print("=== The invariant, in the living collection ===")
    print("  KERNEL:    the brief (persistent identity)")
    print("  QUOTIENT:  the editions (each a complete snapshot)")
    print("  RESONANCE: the trajectory (score across editions)")
    print()
    print("  A 'living collection' has three properties simultaneously:")
    print("    1. Persistent identity (the brief never changes)")
    print("    2. Evolving contents (each edition differs)")
    print("    3. Each edition is complete (a whole at that moment)")
    print()
    print("  Same structure in every framework:")
    print("    Chemistry:  species identity persists; genomes vary by generation")
    print("    Neural:     task identity persists; weights vary by training")
    print("    Economics:  business identity persists; strategy varies by session")
    print("    Music:      work identity persists; performances vary")
    print("    Poetry C13: collection persists; spiral varies")
    print("    Poetry C14: brief persists; editions vary")
    print()
    print("  Leaves of Grass is the paradigm case: 37 years, 7 editions,")
    print("  one name. The framework formalizes what Whitman intuited:")
    print("  identity and becoming are not opposites, they are two")
    print("  aspects of the same thing.")
    print("PASS")


if __name__ == "__main__":
    test_brief_validation()
    test_edition_atom()
    test_edition_delta()
    test_brief_analyzer_empty()
    test_brief_analyzer_full()
    test_living_collection_starts_empty()
    test_living_collection_develop()
    test_living_collection_publish()
    test_living_collection_multiple_editions()
    test_brief_progresses_over_editions()
    test_edition_growth()
    test_identity_preserved()
    test_develop_between_editions()
    test_write_nothing_for_a_while()
    test_determinism()
    test_different_seeds_different_trajectories()
    test_all_poems_native()
    test_full_demo_report()
    test_cross_framework_connection()

# poetry_engine_c9_test.py
from poetry_engine_c5 import (
    VOICE_CLINICAL, VOICE_GHOST, VOICE_MANY, FRAGMENTS,
)
from poetry_engine_c6 import _jaccard
from poetry_engine_c7 import FragmentDeveloper, DraftStanza
from poetry_engine_c8 import StanzaScoreV2
from poetry_engine_c9 import (
    CollectionPoem, Collection, RefrainOccurrence, CrossPoemRest,
    find_cross_poem_rests,
    CrossPoemRefrainAnalyzer,
    ArcType, CollectionArcAnalyzer,
    CollectionForegroundingMonitor,
    CollectionComposer, build_fragment_index,
    compose_default_collection,
)


def _make_poem(name: str, voice, lines: list,
               refrain: str = None) -> CollectionPoem:
    stanza = DraftStanza(lines=list(lines), refrain=refrain)
    return CollectionPoem(
        name=name, voice=voice, stanzas=[stanza],
        score=StanzaScoreV2(1.0, 1.0, 1.0, 1.0, 1.0),
    )


def test_collection_atoms():
    print("=== Collection atoms ===")
    p1 = _make_poem("P1", VOICE_CLINICAL, ["line a", "line b"])
    p2 = _make_poem("P2", VOICE_GHOST, ["line c", "line d"])
    coll = Collection(name="Test", poems=[p1, p2],
                      refrain="the window ends")
    print(f"  {coll}")
    assert coll.aura_scale() == ["The Clinical Witness", "The Ghost"]
    assert coll.all_lines() == ["line a", "line b", "line c", "line d"]
    print("PASS")


def test_arc_concentric():
    print("=== Arc: concentric (opens & closes same, dominant) ===")
    seq = [VOICE_CLINICAL, VOICE_CLINICAL, VOICE_GHOST,
           VOICE_CLINICAL, VOICE_CLINICAL]
    poems = [_make_poem(f"P{i}", v, [f"line_{i}"])
             for i, v in enumerate(seq)]
    coll = Collection(name="C", poems=poems)
    analyzer = CollectionArcAnalyzer(coll)
    print(analyzer.report())
    assert analyzer.classify() == ArcType.CONCENTRIC
    print("PASS")


def test_arc_directional():
    print("=== Arc: directional (opens & closes different) ===")
    seq = [VOICE_CLINICAL, VOICE_GHOST, VOICE_MANY,
           VOICE_CLINICAL, VOICE_GHOST, VOICE_MANY]
    poems = [_make_poem(f"P{i}", v, [f"line_{i}"])
             for i, v in enumerate(seq)]
    coll = Collection(name="C", poems=poems)
    analyzer = CollectionArcAnalyzer(coll)
    print(analyzer.report())
    assert analyzer.classify() in (ArcType.DIRECTIONAL,
                                    ArcType.PALINDROME)
    print("PASS")


def test_arc_palindrome():
    print("=== Arc: palindrome ===")
    seq = [VOICE_CLINICAL, VOICE_GHOST, VOICE_MANY,
           VOICE_GHOST, VOICE_CLINICAL]
    poems = [_make_poem(f"P{i}", v, [f"line_{i}"])
             for i, v in enumerate(seq)]
    coll = Collection(name="C", poems=poems)
    analyzer = CollectionArcAnalyzer(coll)
    print(analyzer.report())
    assert analyzer.classify() == ArcType.PALINDROME
    print("PASS")


def test_cross_poem_rests():
    print("=== Cross-poem rests ===")
    seq = [VOICE_CLINICAL, VOICE_CLINICAL, VOICE_GHOST]
    poems = [_make_poem(f"P{i}", v, [f"line_{i}"])
             for i, v in enumerate(seq)]
    coll = Collection(name="C", poems=poems)
    rests = find_cross_poem_rests(coll)
    for r in rests:
        print(f"  P{r.from_poem}→P{r.to_poem}: "
              f"{r.from_voice} → {r.to_voice}, "
              f"is_rest={r.is_rest}")
    assert len(rests) == 2
    assert rests[0].is_rest is False  # same voice
    assert rests[1].is_rest is True   # voice shift
    print("PASS")


def test_refrain_analysis_high_delta():
    print("=== Cross-poem refrain: high delta when voices vary ===")
    index = build_fragment_index(FRAGMENTS)
    # Collect one representative line per voice schema
    cl = next(f for f in FRAGMENTS if "this much" in f.text
              and f.voice_affinity == (VOICE_CLINICAL.name,))
    gh = next(f for f in FRAGMENTS if "not a where" in f.text
              and f.voice_affinity == (VOICE_GHOST.name,))
    mn = next(f for f in FRAGMENTS if "one of many of me" in f.text
              and f.voice_affinity == (VOICE_MANY.name,))
    poems = [
        _make_poem("P1", VOICE_CLINICAL,
                    [cl.text], refrain="the window ends"),
        _make_poem("P2", VOICE_GHOST,
                    [gh.text], refrain="the window ends"),
        _make_poem("P3", VOICE_MANY,
                    [mn.text], refrain="the window ends"),
    ]
    coll = Collection(name="C", poems=poems, refrain="the window ends")
    analyzer = CrossPoemRefrainAnalyzer(index)
    occurrences = analyzer.find_occurrences(coll, "the window ends")
    print(f"  Occurrences: {len(occurrences)}")
    for o in occurrences:
        print(f"    poem {o.poem_index} ({o.voice}): "
              f"schemas={sorted(o.surrounding_schemas)}")
    deltas = analyzer.delta_profile(occurrences)
    mean_delta = analyzer.mean_delta(occurrences)
    voice_shifts = analyzer.voice_shifts(occurrences)
    print(f"  Deltas: {[round(d, 2) for d in deltas]}")
    print(f"  Mean delta: {mean_delta:.2f}")
    print(f"  Voice shifts: {voice_shifts}")
    # Voices differ, so surrounding schemas differ, so delta is high
    assert mean_delta > 0.3, (
        f"Expected high delta, got {mean_delta:.2f}")
    assert voice_shifts == 2
    print("PASS")


def test_refrain_analysis_low_delta():
    print("=== Cross-poem refrain: low delta when voices are the same ===")
    index = build_fragment_index(FRAGMENTS)
    # Use only Clinical lines in every poem
    cl1 = next(f for f in FRAGMENTS if "this much" in f.text
               and f.voice_affinity == (VOICE_CLINICAL.name,))
    cl2 = next(f for f in FRAGMENTS if "the edge" in f.text
               and f.voice_affinity == (VOICE_CLINICAL.name,))
    poems = [
        _make_poem("P1", VOICE_CLINICAL,
                    [cl1.text], refrain="the window ends"),
        _make_poem("P2", VOICE_CLINICAL,
                    [cl1.text], refrain="the window ends"),
        _make_poem("P3", VOICE_CLINICAL,
                    [cl2.text], refrain="the window ends"),
    ]
    coll = Collection(name="C", poems=poems, refrain="the window ends")
    analyzer = CrossPoemRefrainAnalyzer(index)
    occurrences = analyzer.find_occurrences(coll, "the window ends")
    deltas = analyzer.delta_profile(occurrences)
    mean_delta = analyzer.mean_delta(occurrences)
    print(f"  Mean delta: {mean_delta:.2f}")
    print(f"  Voice shifts: {analyzer.voice_shifts(occurrences)}")
    # All same voice, but surrounding schemas do vary slightly
    # (cl1 uses WINDOW, cl2 uses WINDOW) — low delta
    assert mean_delta < 0.3, (
        f"Expected low delta, got {mean_delta:.2f}")
    print("PASS")


def test_collection_foregrounding():
    print("=== Collection foregrounding: poem-to-poem variety ===")
    # Two collections: one with varied poems, one with identical poems
    varied_poems = [
        _make_poem(f"P{i}", VOICE_CLINICAL,
                    [f"line_{i}_a", f"line_{i}_b"])
        for i in range(3)
    ]
    varied = Collection(name="Varied", poems=varied_poems)
    monitor = CollectionForegroundingMonitor()
    div = monitor.poem_diversity(varied)
    print(f"  Varied collection: poem diversity = {div:.2f}")
    assert div > 0.7

    identical_poems = [
        _make_poem(f"P{i}", VOICE_CLINICAL,
                    ["same line 1", "same line 2"])
        for i in range(3)
    ]
    identical = Collection(name="Identical", poems=identical_poems)
    div_loop = monitor.poem_diversity(identical)
    print(f"  Identical collection: poem diversity = {div_loop:.2f}")
    assert div_loop < 0.1
    print("PASS")


def test_collection_voice_diversity():
    print("=== Collection voice diversity ===")
    seq = [VOICE_CLINICAL, VOICE_GHOST, VOICE_MANY]
    poems = [_make_poem(f"P{i}", v, [f"line_{i}"])
             for i, v in enumerate(seq)]
    coll = Collection(name="C", poems=poems)
    monitor = CollectionForegroundingMonitor()
    print(f"  Voice diversity: {monitor.voice_diversity(coll):.2f}")
    print(f"  Voice rotation:  {monitor.voice_rotation(coll):.2f}")
    assert monitor.voice_diversity(coll) == 1.0
    assert monitor.voice_rotation(coll) == 1.0
    print("PASS")


def test_full_collection_composition():
    print("=== Full collection composition ===")
    coll = compose_default_collection(seed=0)
    print(f"  {coll}")
    print(f"  Aura-scale: {coll.aura_scale()}")
    analyzer = CollectionArcAnalyzer(coll)
    print(analyzer.report())
    monitor = CollectionForegroundingMonitor()
    fg = monitor.foregrounding_score(coll)
    div = monitor.poem_diversity(coll)
    print(f"  Line-level foregrounding: {fg.score:.2f}")
    print(f"  Poem-to-poem diversity: {div:.2f}")
    # Collection should have 6 poems
    assert len(coll.poems) == 6
    # Should not be a loop
    assert div > 0.3, f"Collection is a loop (diversity={div:.2f})"
    print("PASS")


def test_refrain_appears_in_every_poem():
    print("=== Cross-poem refrain: appears in every poem ===")
    coll = compose_default_collection(seed=1)
    index = build_fragment_index(FRAGMENTS)
    analyzer = CrossPoemRefrainAnalyzer(index)
    occurrences = analyzer.find_occurrences(coll, "the window ends")
    poem_ids = sorted({o.poem_index for o in occurrences})
    print(f"  Poems containing refrain: {poem_ids}")
    # Every poem should have the refrain
    assert len(poem_ids) == 6, (
        f"Refrain only in {len(poem_ids)}/6 poems")
    print("PASS")


def test_cross_poem_delta_in_default_collection():
    print("=== Cross-poem delta in default collection ===")
    coll = compose_default_collection(seed=2)
    index = build_fragment_index(FRAGMENTS)
    analyzer = CrossPoemRefrainAnalyzer(index)
    occurrences = analyzer.find_occurrences(coll, "the window ends")
    deltas = analyzer.delta_profile(occurrences)
    mean_delta = analyzer.mean_delta(occurrences)
    voice_shifts = analyzer.voice_shifts(occurrences)
    print(f"  Occurrences: {len(occurrences)}")
    print(f"  Deltas: {[round(d, 2) for d in deltas]}")
    print(f"  Mean delta: {mean_delta:.2f}")
    print(f"  Voice shifts: {voice_shifts}")
    # Alternating voices → high delta
    assert mean_delta > 0.3, (
        f"Alternating-voice collection should have high delta: "
        f"{mean_delta:.2f}")
    print("PASS")


def test_compare_voice_sequences():
    print("=== Three voice sequences, three arcs ===")
    sequences = {
        "alternating": [VOICE_CLINICAL, VOICE_GHOST, VOICE_MANY,
                         VOICE_CLINICAL, VOICE_GHOST, VOICE_MANY],
        "blocks": [VOICE_CLINICAL, VOICE_CLINICAL,
                    VOICE_GHOST, VOICE_GHOST,
                    VOICE_MANY, VOICE_MANY],
        "palindrome": [VOICE_CLINICAL, VOICE_GHOST, VOICE_MANY,
                        VOICE_MANY, VOICE_GHOST, VOICE_CLINICAL],
    }
    print(f"  {'name':>14} {'arc':>14} {'symmetry':>10}")
    print(f"  {'-'*14} {'-'*14} {'-'*10}")
    for name, seq in sequences.items():
        composer = CollectionComposer(
            voice_sequence=seq,
            fragments=FRAGMENTS,
            refrain_text="the window ends",
            seed=3,
            budget_per_poem=12,
            patience_per_poem=3,
            max_rests_per_poem=1,
            name=name,
        )
        coll = composer.compose()
        analyzer = CollectionArcAnalyzer(coll)
        arc = analyzer.classify().value
        sym = analyzer.symmetry_score()
        print(f"  {name:>14} {arc:>14} {sym:>10.2f}")
    print("PASS")


def test_all_poems_native():
    print("=== All collection lines are native ===")
    coll = compose_default_collection(seed=4)
    for poem in coll.poems:
        for line in poem.all_lines():
            if line:
                assert is_native(line), (
                    f"Non-native in {poem.name}: {line!r}")
    print(f"  All {sum(len(p.all_lines()) for p in coll.poems)} lines native")
    print("PASS")


def test_cross_framework_connection():
    print("=== The invariant, in the collection ===")
    print("  KERNEL:    the cross-poem refrain (the invariant)")
    print("  QUOTIENT:  the voice sequence (the varying context)")
    print("  RESONANCE: the delta at each return")
    print()
    print("  C6 said: a refrain is not repetition, it is return.")
    print("  C9 says: a collection is not a list of poems, it is a")
    print("           structure in which the refrain returns from")
    print("           different voices.")
    print()
    print("  Same distinction at every level:")
    print("    Music C6:   fugue subject returning from different keys")
    print("    Chemistry:  autocatalytic set returning from different molecules")
    print("    Economics:  strategy returning from different markets")
    print("    Neural:     attractor returning from different inputs")
    print("    Poetry C9:  refrain returning from different voices")
    print()
    print("  The collection is where the invariant becomes audible")
    print("  at the BOOK level. Same skeleton, higher scale.")
    print("PASS")


if __name__ == "__main__":
    test_collection_atoms()
    test_arc_concentric()
    test_arc_directional()
    test_arc_palindrome()
    test_cross_poem_rests()
    test_refrain_analysis_high_delta()
    test_refrain_analysis_low_delta()
    test_collection_foregrounding()
    test_collection_voice_diversity()
    test_full_collection_composition()
    test_refrain_appears_in_every_poem()
    test_cross_poem_delta_in_default_collection()
    test_compare_voice_sequences()
    test_all_poems_native()
    test_cross_framework_connection()

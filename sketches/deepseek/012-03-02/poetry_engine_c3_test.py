# poetry_engine_c3_test.py
from poetry_engine_c3 import (
    FootType, foot_from_pattern, Meter,
    IAMBIC_PENTAMETER, IAMBIC_TETRAMETER, TROCHAIC_TETRAMETER,
    STANDARD_METERS,
    Line, WordClass, classify_word, build_line,
    Realization, FootScansion, GenerativeScansion, scan_generative,
    TextualOperation, SyllableRole, FunctionalScansion, scan_functional,
    DualScansion, analyze_line,
)


def _make_line(text: str, stress_pattern: str,
               words: list) -> Line:
    """Manually build a Line with a known stress pattern.

    words: list of (word, length_in_syllables)
    """
    offsets = []
    syllables = []
    pos = 0
    for word, n in words:
        offsets.append((word, pos, n))
        for j in range(n):
            syllables.append(f"{word}_{j}")
        pos += n
    assert pos == len(stress_pattern), (
        f"word lengths ({pos}) don't match stress pattern "
        f"({len(stress_pattern)})")
    return Line(
        text=text,
        stress_pattern=stress_pattern,
        syllables=syllables,
        word_stress_offsets=offsets,
    )


def test_foot_atoms():
    print("=== FootType atoms ===")
    assert FootType.IAMB.pattern == "01"
    assert FootType.IAMB.size == 2
    assert FootType.TROCHEE.pattern == "10"
    assert FootType.ANAPEST.pattern == "001"
    assert FootType.ANAPEST.size == 3
    assert foot_from_pattern("01") == FootType.IAMB
    assert foot_from_pattern("XX") is None
    print(f"  IAMB: {FootType.IAMB}")
    print(f"  ANAPEST: {FootType.ANAPEST}")
    print(f"  Lookup '10' → {foot_from_pattern('10')}")
    print("PASS")


def test_meter_composition():
    print("=== Meter: template composition ===")
    assert IAMBIC_PENTAMETER.template() == "0101010101"
    assert IAMBIC_PENTAMETER.length() == 10
    assert IAMBIC_PENTAMETER.foot_size() == 2
    assert IAMBIC_PENTAMETER.number_of_feet() == 5

    assert TROCHAIC_TETRAMETER.template() == "10101010"
    assert TROCHAIC_TETRAMETER.length() == 8

    # Mismatched foot sizes rejected
    try:
        Meter("bad", (FootType.IAMB, FootType.ANAPEST))
        assert False, "should have raised"
    except ValueError:
        print("  ✓ mixed foot sizes rejected")
    print("PASS")


def test_classify_word():
    print("=== Halliday: content vs function classification ===")
    tests = [
        ("the", WordClass.FUNCTION),
        ("love", WordClass.CONTENT),
        ("summer", WordClass.CONTENT),
        ("I", WordClass.FUNCTION),
        ("compare", WordClass.CONTENT),
        ("thee", WordClass.FUNCTION),
        ("rose", WordClass.CONTENT),
        ("and", WordClass.FUNCTION),
        ("day", WordClass.CONTENT),
    ]
    for word, expected in tests:
        got = classify_word(word)
        print(f"  {word:>10}: {got.value} (expected {expected.value})")
        assert got == expected
    print("PASS")


def test_perfect_iambic():
    print("=== Generative: perfect iambic pentameter ===")
    line = _make_line(
        "When I do count the clock that tells the time",
        "0101010101",
        [("When", 1), ("I", 1), ("do", 1), ("count", 1),
         ("the", 1), ("clock", 1), ("that", 1), ("tells", 1),
         ("the", 1), ("time", 1)],
    )
    scan = scan_generative(line, IAMBIC_PENTAMETER)
    print(scan.report())
    assert scan.matches() == 5
    assert scan.score() == 1.0
    assert len(scan.substitutions()) == 0
    print("PASS")


def test_iambic_with_substitutions():
    print("=== Generative: iambic pentameter with substitutions ===")
    # From C1's output for "Shall I compare thee to a summer's day":
    # 0101001011 → feet 01 01 00 10 11
    line = _make_line(
        "Shall I compare thee to a summer's day",
        "0101001011",
        [("Shall", 1), ("I", 1), ("compare", 2), ("thee", 1),
         ("to", 1), ("a", 1), ("summer's", 2), ("day", 1)],
    )
    scan = scan_generative(line, IAMBIC_PENTAMETER)
    print(scan.report())
    assert scan.matches() == 2  # feet 0 and 1
    assert len(scan.substitutions()) == 3  # feet 2, 3, 4
    subs = scan.substitutions_by_kind()
    print(f"\n  Substitution counts: {subs}")
    # Foot 2 = 00 (pyrrhic), Foot 3 = 10 (trochee), Foot 4 = 11 (spondee)
    assert subs.get("PYRRHIC") == 1
    assert subs.get("TROCHEE") == 1
    assert subs.get("SPONDEE") == 1
    print("PASS")


def test_functional_alignment():
    print("=== Functional: perfect alignment (all content on stress) ===")
    line = _make_line(
        "When I do count the clock that tells the time",
        "0101010101",
        [("When", 1), ("I", 1), ("do", 1), ("count", 1),
         ("the", 1), ("clock", 1), ("that", 1), ("tells", 1),
         ("the", 1), ("time", 1)],
    )
    scan = scan_functional(line)
    print(scan.report())
    assert scan.textual_fit() == 1.0
    # Content syllables on stress: count, clock, tells, time
    assert scan.content_on_stress() == [3, 5, 7, 9]
    # Function on stress: I (index 1), that (index 6)
    assert 1 in scan.function_highlighted()
    assert 6 in scan.function_highlighted()
    print("PASS")


def test_functional_partial_subordination():
    print("=== Functional: partial content subordination ===")
    # "beautiful" (stress 100) placed at positions 1,2,3 with stresses
    # 1,0,0. So beau=1 (on stress), ti=0 (subordinated), ful=0
    # (subordinated). Rose at position 3 with stress 1 (on stress).
    # Fit = 2/4 = 0.5.
    line = _make_line(
        "Beautiful rose",
        "1001",
        [("Beautiful", 3), ("rose", 1)],
    )
    scan = scan_functional(line)
    print(scan.report())
    # "Beautiful" has 3 syllables: beau(1), ti(0), ful(0)
    # Only "beau" is on stress — "ti" and "ful" are subordinated
    assert scan.textual_fit() == 0.5
    assert len(scan.content_subordinated()) == 2
    print("PASS")


def test_functional_function_highlighting():
    print("=== Functional: function word highlighted ===")
    # "the" on a stressed position — this is unusual and draws attention
    line = _make_line(
        "the love the",
        "101",  # the=1 (highlighted!), love=0 (subordinated), the=1
        [("the", 1), ("love", 1), ("the", 1)],
    )
    scan = scan_functional(line)
    print(scan.report())
    # Both "the" instances are highlighted
    assert 0 in scan.function_highlighted()
    assert 2 in scan.function_highlighted()
    # Content syllable "love" is subordinated
    assert 1 in scan.content_subordinated()
    print("PASS")


def test_dual_scansion_same_line():
    print("=== DualScansion: both grammars on the same line ===")
    line = _make_line(
        "Shall I compare thee to a summer's day",
        "0101001011",
        [("Shall", 1), ("I", 1), ("compare", 2), ("thee", 1),
         ("to", 1), ("a", 1), ("summer's", 2), ("day", 1)],
    )
    dual = DualScansion(
        generative=scan_generative(line, IAMBIC_PENTAMETER),
        functional=scan_functional(line),
    )
    print(dual.report())
    # Generative view: 2/5 matches, 3 substitutions
    assert dual.generative.matches() == 2
    # Functional view: content subordinated in "compare" (pare is on stress
    # but com is unstressed) and "summer's" (sum stressed, mer's unstressed)
    # — so partial subordination
    assert dual.functional.textual_fit() < 1.0
    # Function on stress: "I" (index 1)
    assert 1 in dual.functional.function_highlighted()
    print("PASS")


def test_compare_two_lines_grammars():
    print("=== Compare: clean line vs substituted line ===")
    clean = _make_line(
        "When I do count the clock that tells the time",
        "0101010101",
        [("When", 1), ("I", 1), ("do", 1), ("count", 1),
         ("the", 1), ("clock", 1), ("that", 1), ("tells", 1),
         ("the", 1), ("time", 1)],
    )
    substituted = _make_line(
        "Shall I compare thee to a summer's day",
        "0101001011",
        [("Shall", 1), ("I", 1), ("compare", 2), ("thee", 1),
         ("to", 1), ("a", 1), ("summer's", 2), ("day", 1)],
    )
    print(f"  {'line':>45} {'gen. score':>12} {'func. fit':>10}")
    print(f"  {'-'*45} {'-'*12} {'-'*10}")
    for label, line in [("clean", clean), ("substituted", substituted)]:
        g = scan_generative(line, IAMBIC_PENTAMETER)
        f = scan_functional(line)
        print(f"  {label:>45} {g.score():>12.2f} {f.textual_fit():>10.2f}")
    # Clean line: perfect on both
    g_clean = scan_generative(clean, IAMBIC_PENTAMETER)
    f_clean = scan_functional(clean)
    assert g_clean.score() == 1.0
    assert f_clean.textual_fit() == 1.0
    # Substituted line: not perfect on either
    g_sub = scan_generative(substituted, IAMBIC_PENTAMETER)
    assert g_sub.score() < 1.0
    print("PASS")


def test_build_line_from_c1():
    print("=== Integration: build_line from Component 1 ===")
    line = build_line("When I do count the clock that tells the time")
    print(f"  Stress: {line.stress_pattern}")
    print(f"  Syllables: {len(line.syllables)}")
    print(f"  Words: {[w[0] for w in line.word_stress_offsets]}")
    # Should be 10 syllables (this line is definitely pentameter)
    assert len(line.stress_pattern) == 10
    assert len(line.word_stress_offsets) == 10
    print("PASS")


def test_truncation_detection():
    print("=== Truncation: line shorter than template ===")
    # 7 syllables against 8-position trochaic tetrameter
    line = _make_line(
        "Tyger Tyger burning",
        "1010101",
        [("Tyger", 2), ("Tyger", 2), ("burning", 3)],
    )
    scan = scan_generative(line, TROCHAIC_TETRAMETER)
    print(scan.report())
    # Template length = 8, actual = 7 → missing 1
    assert scan.missing_count == 1
    # 3 full feet scanned; all match (1010, 1010, 101)
    # — actually the last "101" is only 1.5 feet, so n_feet=3, feet 0-2
    # are (10, 10, 10) all match; the "1" is dangling
    print("PASS")


def test_extrametrical_detection():
    print("=== Extrametrical: line longer than template ===")
    # 12 syllables against 10-position iambic pentameter
    line = _make_line(
        "the the the the the the the the the the the the",
        "010101010101",  # 12 characters
        [("the", 1)] * 12,
    )
    scan = scan_generative(line, IAMBIC_PENTAMETER)
    print(scan.report())
    # Template length = 10, actual = 12 → 2 extrametrical
    assert len(scan.extrametrical_indices) == 2
    assert scan.extrametrical_indices == [10, 11]
    print("PASS")


def test_two_grammar_different_answers():
    print("=== The Chomsky/Halliday tension, made explicit ===")
    # A line where the two grammars give genuinely different readings
    line = _make_line(
        "Not marble nor the gilded monuments",
        "101101011010",  # 12 characters
        [("Not", 1), ("marble", 2), ("nor", 1), ("the", 1),
         ("gilded", 2), ("monuments", 3), ("", 2)],
    )
    # This is Sonnet 55's line — pentameter but with substitutions
    # Let me correct to actual pentameter scansion
    line = _make_line(
        "Not marble nor the gilded monuments",
        "1011011010",  # 10 characters, actual pentameter
        [("Not", 1), ("marble", 2), ("nor", 1), ("the", 1),
         ("gilded", 2), ("monuments", 3)],
    )
    g = scan_generative(line, IAMBIC_PENTAMETER)
    f = scan_functional(line)
    print("GENERATIVE VIEW (what transformations produced this line?):")
    print(g.report())
    print("\nFUNCTIONAL VIEW (how does the meter organize the message?):")
    print(f.report())
    # The two grammars see the same line differently:
    # - Generative: "1011011010" vs template "0101010101"
    #   = substitutions on feet 0, 2, 3 (the trochaic starts are famous)
    # - Functional: "Not" (content on stress) — the negation is foregrounded
    #   "marble" — mar=1, ble=0 (partial), "nor" (function on stress),
    #   etc.
    assert g.score() < 1.0
    assert f.textual_fit() < 1.0
    print("\n  → Same line, two different readings")
    print("PASS")


def test_cross_framework_connection():
    print("=== The invariant, in the two grammars ===")
    print("  GENERATIVE (Chomsky-adjacent):")
    print("    KERNEL:    the template (iambic pentameter)")
    print("    QUOTIENT:  the substitution catalog")
    print("    RESONANCE: the derived surface line")
    print()
    print("  FUNCTIONAL (Halliday-adjacent):")
    print("    KERNEL:    the metrical grid (positions)")
    print("    QUOTIENT:  the content/function distribution")
    print("    RESONANCE: the reading (how meter organizes meaning)")
    print()
    print("  Both grammars operate on the SAME atoms:")
    print("    Foot, Meter, Line, WordClass.")
    print()
    print("  Chomsky and Halliday gave us two lenses on the same object.")
    print("  The framework inherits both. Not as a compromise — as a")
    print("  structural fact: the poem is BOTH a rule-derived object")
    print("  AND a meaning-organizing object, and scansion must see")
    print("  both to be complete.")
    print()
    print("  This mirrors every prior cycle:")
    print("    Chemistry:  structure (space) AND dynamics (catalysis)")
    print("    Music:      template (meter) AND realization (surface)")
    print("    Language:   syntax (tree) AND semantics (context)")
    print("    Poetry:     derivation (generative) AND reading (functional)")
    print()
    print("  Component 3 is the first component where TWO grammars")
    print("  coexist without one reducing to the other.")
    print("PASS")


if __name__ == "__main__":
    test_foot_atoms()
    test_meter_composition()
    test_classify_word()
    test_perfect_iambic()
    test_iambic_with_substitutions()
    test_functional_alignment()
    test_functional_partial_subordination()
    test_functional_function_highlighting()
    test_dual_scansion_same_line()
    test_compare_two_lines_grammars()
    test_build_line_from_c1()
    test_truncation_detection()
    test_extrametrical_detection()
    test_two_grammar_different_answers()
    test_cross_framework_connection()

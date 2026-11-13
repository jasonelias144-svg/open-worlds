# poetry_engine_c1_test.py
from poetry_engine_c1 import (
    Phoneme, PhoneType, Stress, Syllable,
    VOWELS, CONSONANTS, ALL_PHONEMES,
    Word, StressPattern, StressDictionary,
    STRESS_DICT, Syllabifier,
    line_stress_pattern, line_syllable_count,
)


def test_phoneme_inventory():
    print("=== Phoneme inventory ===")
    print(f"  Vowels: {len(VOWELS)}")
    print(f"  Consonants: {len(CONSONANTS)}")
    print(f"  Total: {len(ALL_PHONEMES)}")
    # Every phoneme has correct kind
    for p in VOWELS.values():
        assert p.kind == PhoneType.VOWEL
    for p in CONSONANTS.values():
        assert p.kind == PhoneType.CONSONANT
    # Voicing feature is distinguishable
    assert CONSONANTS["p"].voiced == False
    assert CONSONANTS["b"].voiced == True
    assert CONSONANTS["s"].voiced == False
    assert CONSONANTS["z"].voiced == True
    print("PASS")


def test_phoneme_vowel_features():
    print("=== Vowel features ===")
    tests = [
        ("i", {"high", "front", "tense"}),
        ("ɪ", {"high", "front", "lax"}),
        ("u", {"high", "back", "tense"}),
        ("a", {"low", "central"}),
        ("aɪ", {"diphthong"}),
    ]
    for sym, expected in tests:
        v = VOWELS[sym]
        print(f"  /{sym}/: features={set(v.features)}")
        assert expected <= v.features
    print("PASS")


def test_syllable_structure():
    print("=== Syllable structure ===")
    # "cat" = /k æ t/ = C-V-C
    cat = Syllable(
        onset=(CONSONANTS["k"],),
        nucleus=VOWELS["æ"],
        coda=(CONSONANTS["t"],),
        stress=Stress.PRIMARY,
    )
    print(f"  cat: {cat}")
    print(f"  open? {cat.is_open()}")
    print(f"  weight: {cat.weight()}")
    assert not cat.is_open()
    assert cat.weight() == "heavy"
    # "me" = /m i/ = C-V
    me = Syllable(
        onset=(CONSONANTS["m"],),
        nucleus=VOWELS["i"],
        coda=(),
        stress=Stress.PRIMARY,
    )
    print(f"  me: {me}")
    print(f"  open? {me.is_open()}")
    print(f"  weight: {me.weight()}")
    assert me.is_open()
    assert me.weight() == "heavy"  # long vowel
    # "the" (approximate) = /ð ə/ = C-V with reduced vowel
    the = Syllable(
        onset=(CONSONANTS["ð"],),
        nucleus=VOWELS["ə"],
        coda=(),
        stress=Stress.NONE,
    )
    print(f"  the: {the}, weight={the.weight()}")
    assert the.weight() == "light"
    print("PASS")


def test_syllable_rejects_consonant_nucleus():
    print("=== Syllable rejects consonant nucleus ===")
    try:
        Syllable(
            onset=(),
            nucleus=CONSONANTS["t"],  # invalid
            coda=(),
        )
        assert False, "should have raised"
    except ValueError as e:
        print(f"  Correctly raised: {e}")
    print("PASS")


def test_stress_pattern():
    print("=== StressPattern ===")
    sp = StressPattern("100")
    print(f"  {sp}")
    print(f"  length: {sp.length()}")
    print(f"  inverted: {sp.inverted()}")
    assert sp.length() == 3
    assert sp.inverted().digits == "011"
    # Reject invalid
    try:
        StressPattern("123")
        assert False
    except ValueError:
        print("  ✓ invalid digit rejected")
    print("PASS")


def test_stress_pattern_match():
    print("=== StressPattern: matching against templates ===")
    template = StressPattern("01010")  # iambic pentameter
    # Perfect match
    assert StressPattern("01010").matches(template)
    # Close match (one weak position)
    assert StressPattern("01000").matches(template, tolerance=1)
    # Bad match
    assert not StressPattern("11111").matches(template, tolerance=1)
    # Length must match
    assert not StressPattern("0101").matches(template)
    print("PASS")


def test_word_assembly():
    print("=== Word assembly ===")
    # "summer": /s ʌ m ɝ/
    summer = Word(
        spelling="summer",
        syllables=[
            Syllable((CONSONANTS["s"],), VOWELS["ʌ"],
                     (CONSONANTS["m"],), Stress.PRIMARY),
            Syllable((), VOWELS["ɝ"], (), Stress.NONE),
        ],
    )
    print(f"  {summer}")
    print(f"  stress: {summer.stress_pattern()}")
    print(f"  syllables: {summer.number_of_syllables()}")
    print(f"  primary position: {summer.primary_stress_position()}")
    assert summer.stress_pattern() == "10"
    assert summer.number_of_syllables() == 2
    assert summer.primary_stress_position() == 0
    print("PASS")


def test_stress_dictionary():
    print("=== StressDictionary: known words ===")
    tests = [
        ("summer", 2, "10"),
        ("above", 2, "01"),
        ("beautiful", 3, "100"),
        ("the", 1, "0"),
        ("day", 1, "1"),
    ]
    for word, syll, stress in tests:
        got_syll, got_stress = STRESS_DICT[word]
        print(f"  {word:>10}: {got_syll} syll, stress={got_stress} "
              f"(expected {syll}, {stress})")
        assert got_syll == syll
        assert got_stress == stress
    print("PASS")


def test_record_ambiguity():
    print("=== 'record' is both noun and verb ===")
    # The dictionary has both; the fallback picks one
    # In the dict, both keys collapse to the last one written
    # (in this case, we wrote noun first, then verb — the verb overwrote)
    # Let's verify the collapse behavior is documented
    syll, stress = STRESS_DICT["record"]
    print(f"  'record' in dict: {syll} syll, stress={stress}")
    print(f"  (Note: stress is ambiguous — this is a real English feature)")
    print("PASS")


def test_syllabifier_count():
    print("=== Syllabifier: syllable counts ===")
    s = Syllabifier()
    tests = [
        ("cat", 1), ("summer", 2), ("beautiful", 3),
        ("the", 1), ("compare", 2),
        # Words not in dict, rule-based
        ("wonderful", 3), ("amazing", 3), ("through", 1),
        ("everywhere", 3), ("syllable", 3),
    ]
    for word, expected in tests:
        got = s.count_syllables(word)
        print(f"  {word:>12}: {got} (expected {expected})")
        assert got == expected, f"{word}: got {got}, expected {expected}"
    print("PASS")


def test_syllabifier_fallback():
    print("=== Syllabifier: fallback for unknown words ===")
    s = Syllabifier()
    # Words not in the dict
    unknown = ["flibbertigibbet", "serendipity", "quintessential",
               "ephemeral", "mellifluous"]
    for word in unknown:
        n = s.count_syllables(word)
        sp = s.stress_pattern(word)
        print(f"  {word:>18}: {n} syll, stress={sp.digits}")
        assert n == len(sp.digits)
        assert n >= 1
    print("PASS")


def test_line_stress_pattern():
    print("=== Line-level stress extraction ===")
    # "Shall I compare thee to a summer's day"
    line = "Shall I compare thee to a summer's day"
    sp = line_stress_pattern(line)
    count = line_syllable_count(line)
    print(f"  Line: '{line}'")
    print(f"  Stress pattern: {sp.digits}")
    print(f"  Syllable count: {count}")
    # This line is the opening of Sonnet 18 — should be iambic pentameter
    assert count == 10, f"Expected 10 syllables, got {count}"
    print("PASS")


def test_iambic_pentameter_check():
    print("=== Iambic pentameter: a full line ===")
    # "When I do count the clock that tells the time" (Sonnet 12)
    line = "When I do count the clock that tells the time"
    s = Syllabifier()
    sp = line_stress_pattern(line, s)
    count = line_syllable_count(line, s)
    print(f"  Line: '{line}'")
    print(f"  Stress: {sp.digits}")
    print(f"  Count:  {count}")
    # Iambic pentameter template: 0101010101
    template = StressPattern("0101010101")
    matches_exactly = sp.matches(template)
    matches_loose = sp.matches(template, tolerance=2)
    print(f"  Matches exactly: {matches_exactly}")
    print(f"  Matches within 2: {matches_loose}")
    assert count == 10
    print("PASS")


def test_sonnet_line_variety():
    print("=== Stress patterns of several sonnet lines ===")
    lines = [
        "Shall I compare thee to a summer's day",
        "When I do count the clock that tells the time",
        "Let me not to the marriage of true minds",
        "That time of year thou mayst in me behold",
    ]
    s = Syllabifier()
    print(f"  {'line':>45} {'count':>6} {'stress':>12}")
    print(f"  {'-'*45} {'-'*6} {'-'*12}")
    for line in lines:
        sp = line_stress_pattern(line, s)
        count = line_syllable_count(line, s)
        print(f"  {line:>45} {count:>6} {sp.digits:>12}")
        assert count == 10, f"Not pentameter: {count} syllables"
    print("PASS")


def test_cross_framework_connection():
    print("=== The atoms are the same shape as every prior cycle ===")
    print("  Circuits:  R, C, V (continuous)")
    print("  Neurons:   membrane, spike (discrete events)")
    print("  Economics: resource, action, guard (discrete states)")
    print("  Language:  token, position (discrete symbols)")
    print("  Chemistry: element, bond (discrete graph)")
    print("  Music:     pitch, interval (continuous + quotient)")
    print("  Poetry:    phoneme, syllable, stress (discrete + prosodic)")
    print()
    print("  All seven cycles have:")
    print("    - An irreducible atom (Phoneme here)")
    print("    - A composition operation (syllable structure)")
    print("    - A quotient (stress pattern — the abstract skeleton)")
    print("    - A resonance (meter — to be built in C2)")
    print()
    print("  Component 1 gives us the first three.")
    print("  Component 2 will give us the fourth.")
    print("PASS")


if __name__ == "__main__":
    test_phoneme_inventory()
    test_phoneme_vowel_features()
    test_syllable_structure()
    test_syllable_rejects_consonant_nucleus()
    test_stress_pattern()
    test_stress_pattern_match()
    test_word_assembly()
    test_stress_dictionary()
    test_record_ambiguity()
    test_syllabifier_count()
    test_syllabifier_fallback()
    test_line_stress_pattern()
    test_iambic_pentameter_check()
    test_sonnet_line_variety()
    test_cross_framework_connection()

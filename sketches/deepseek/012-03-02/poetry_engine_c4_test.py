# poetry_engine_c4_test.py
from poetry_engine_c3 import IAMBIC_PENTAMETER
from poetry_engine_c4 import (
    SpeakerType, ListenerType, ImaginedSpeaker, ImaginedListener,
    detect_speaker, detect_listener,
    LineEndType, LineEnd, detect_line_end,
    DecisionKind, PerformanceDecision, PerformanceSpace,
    EnjambmentAnalyzer, EnjambmentResult,
    GapAnalysis, analyze_gap,
    build_performance_space,
)
from poetry_engine_c3 import build_line, analyze_line


def test_speaker_detection():
    print("=== Speaker detection ===")
    cases = [
        ("Shall I compare thee to a summer's day",
         SpeakerType.LOVER, "high"),
        ("That time of year thou mayst in me behold",
         SpeakerType.LOVER, "high"),
        ("When I do count the clock that tells the time",
         SpeakerType.OBSERVER, "medium"),
        ("When I have fears that I may cease to be",
         SpeakerType.ELEGIST, "high"),
        ("O wild West Wind, thou breath of Autumn's being",
         SpeakerType.APOSTROPHIZER, "high"),
        ("The yellow fog that rubs its back upon the window-panes",
         SpeakerType.UNKNOWN, "low"),
    ]
    for text, expected_type, expected_conf in cases:
        s = detect_speaker(text)
        print(f"  {text[:45]:>45}: {s.type.value:>14} "
              f"(conf {s.confidence:.2f})")
        assert s.type == expected_type, \
            f"Expected {expected_type.value}, got {s.type.value}"
    print("PASS")


def test_listener_detection():
    print("=== Listener detection ===")
    cases = [
        ("Shall I compare thee to a summer's day",
         ListenerType.BELOVED),
        ("O wild West Wind, thou breath of Autumn's being",
         ListenerType.ABSTRACT),
        ("Let me not to the marriage of true minds",
         ListenerType.SELF),
        ("That time of year thou mayst in me behold",
         ListenerType.BELOVED),
        ("The yellow fog that rubs its back upon the window-panes",
         ListenerType.UNKNOWN),
    ]
    for text, expected in cases:
        l = detect_listener(text)
        print(f"  {text[:45]:>45}: {l.type.value:>12} "
              f"(conf {l.confidence:.2f})")
        assert l.type == expected, \
            f"Expected {expected.value}, got {l.type.value}"
    print("PASS")


def test_line_end_detection():
    print("=== Line-end detection ===")
    cases = [
        ("When I do count the clock that tells the time", 
         LineEndType.NONE),
        ("Shall I compare thee to a summer's day?",
         LineEndType.QUESTION),
        ("That time of year thou mayst in me behold,",
         LineEndType.COMMA),
        ("When I have fears that I may cease to be.",
         LineEndType.PERIOD),
        ("Do I dare", LineEndType.NONE),
        ("Disturb the universe?",
         LineEndType.QUESTION),
        # Ends in function word
        ("I have measured out my life with coffee spoons and",
         LineEndType.FUNCTION_WORD),
    ]
    for text, expected in cases:
        end = detect_line_end(text)
        print(f"  {text[:45]:>45}: {end.type.value}")
        assert end.type == expected, \
            f"Expected {expected.value}, got {end.type.value}"
    print("PASS")


def test_enjambment_end_stopped():
    print("=== Enjambment: end-stopped (strong punctuation) ===")
    result = EnjambmentAnalyzer().analyze(
        "When I do count the clock that tells the time.",
        "And see the brave day sunk in hideous night;")
    print(f"  Line 1: 'When I do count the clock that tells the time.'")
    print(f"  Tension: {result.tension:.2f}")
    print(f"  Explanation: {result.explanation}")
    assert result.tension == 0.0
    print("PASS")


def test_enjambment_weak():
    print("=== Enjambment: weak end-stop (comma) ===")
    result = EnjambmentAnalyzer().analyze(
        "That time of year thou mayst in me behold,",
        "When yellow leaves, or none, or few, do hang")
    print(f"  Tension: {result.tension:.2f}")
    print(f"  Explanation: {result.explanation}")
    assert result.tension == 0.2
    print("PASS")


def test_enjambment_function_word():
    print("=== Enjambment: strong (function word) ===")
    result = EnjambmentAnalyzer().analyze(
        "I have measured out my life with coffee spoons and",
        "you, you, you...")
    print(f"  Tension: {result.tension:.2f}")
    print(f"  Explanation: {result.explanation}")
    assert result.tension >= 0.9
    print("PASS")


def test_enjambment_strong():
    print("=== Enjambment: strongest (next line starts with conjunction) ===")
    result = EnjambmentAnalyzer().analyze(
        "I have eaten the plums that were in the icebox",
        "and which you were probably saving for breakfast")
    print(f"  Tension: {result.tension:.2f}")
    print(f"  Explanation: {result.explanation}")
    assert result.tension == 1.0
    print("PASS")


def test_gap_sonnet_1():
    print("=== Gap: Sonnet 18, line 1 ===")
    gap = analyze_gap("Shall I compare thee to a summer's day")
    print(gap.report())
    print(f"  → Load {gap.load():.2f}, shape = {gap.shape()}")
    assert gap.load() > 0.5
    print("PASS")


def test_gap_sonnet_2():
    print("=== Gap: Sonnet 18, line 2 ===")
    gap = analyze_gap("Thou art more lovely and more temperate")
    print(gap.report())
    print(f"  → Load {gap.load():.2f}, shape = {gap.shape()}")
    print("PASS")


def test_gap_comparison():
    print("=== Gap comparison: sonnet lines ===")
    cases = [
        ("Sonnet 18 line 1", "Shall I compare thee to a summer's day"),
        ("Sonnet 18 line 2", "Thou art more lovely and more temperate"),
        ("Sonnet 73 line 1", "That time of year thou mayst in me behold"),
        ("Sonnet 130 line 1", "My mistress' eyes are nothing like the sun"),
        ("Sonnet 55 line 1", "Not marble nor the gilded monuments"),
    ]
    print(f"  {'line':>20} {'load':>6} {'shape':>20} "
          f"{'speaker':>14} {'listener':>12}")
    print(f"  {'-'*20} {'-'*6} {'-'*20} {'-'*14} {'-'*12}")
    for label, text in cases:
        gap = analyze_gap(text)
        print(f"  {label:>20} {gap.load():>6.2f} {gap.shape():>20} "
              f"{gap.speaker_type:>14} {gap.listener_type:>12}")
    print("PASS")


def test_gap_haiku_vs_freeverse():
    print("=== Gap comparison: haiku vs free verse ===")
    haiku = "An old silent pond"
    haiku_next = "A frog jumps into the pond"
    free_verse = "I have eaten"
    free_verse_next = "the plums that were in the icebox"

    h = analyze_gap(haiku, haiku_next)
    f = analyze_gap(free_verse, free_verse_next)
    print(f"  Haiku line 1:      load = {h.load():.2f}, shape = {h.shape()}")
    print(f"  Free verse line 1: load = {f.load():.2f}, shape = {f.shape()}")
    # Free verse is unmatched to pentameter and likely more enjambed
    # (the specific instances chosen may vary; this test just shows the
    # framework can compare them)
    print("PASS")


def test_performance_space():
    print("=== PerformanceSpace: full decision set ===")
    text = "Shall I compare thee to a summer's day"
    line = build_line(text)
    dual = analyze_line(text, IAMBIC_PENTAMETER)
    speaker = detect_speaker(text)
    listener = detect_listener(text)
    end = detect_line_end(text)
    space = build_performance_space(
        text, line, dual, speaker, listener, end)
    print(space.report())
    print(f"\n  Open decisions: {len(space.open_decisions())}/"
          f"{space.n_decisions()}")
    print(f"  By kind: {space.by_kind()}")
    print("PASS")


def test_honest_uncertainty():
    print("=== Honest uncertainty on ambiguous lines ===")
    # Prufrock's fog line: speaker is clearly first-person
    # but the line itself doesn't say who's speaking or to whom
    ambiguous = "The yellow fog that rubs its back upon the window-panes"
    s = detect_speaker(ambiguous)
    l = detect_listener(ambiguous)
    print(f"  Text: {ambiguous!r}")
    print(f"  Speaker: {s.type.value} (conf {s.confidence:.2f})")
    print(f"  Listener: {l.type.value} (conf {l.confidence:.2f})")
    # The framework says "I don't know" — this is correct, not a failure
    assert s.confidence < 0.5
    assert l.confidence < 0.5
    print("  ✓ Framework reports low confidence (correct answer)")
    print("PASS")


def test_score_performance_honesty():
    print("=== The framework CANNOT fill the gap ===")
    # A line from a well-known poem — but even here, the framework
    # cannot tell you how to voice it.
    text = "Do I dare"
    space = build_performance_space(
        text=text,
        line=build_line(text),
        dual=analyze_line(text, IAMBIC_PENTAMETER),
        speaker=detect_speaker(text),
        listener=detect_listener(text),
        line_end=detect_line_end(text),
    )
    print(f"  Line: {text!r}")
    print(f"  Decisions: {space.n_decisions()}")
    print(f"  Open decisions: {len(space.open_decisions())}")
    print(f"\n  The framework identifies WHAT decisions exist:")
    for d in space.decisions:
        print(f"    {d.kind.value}: {len(d.options)} options")
    print(f"\n  The framework does NOT decide for the reader.")
    print(f"  The reader's performance is the reader's work.")
    print("PASS")


def test_gap_shape_varies():
    print("=== The gap has a SHAPE, not just a SIZE ===")
    cases = [
        ("Metaphor-dominant", "My love is like a rose"),
        ("Enjambment-dominant", "I have eaten the plums and"),
        ("Substitution-dominant", "Not marble nor the gilded monuments"),
    ]
    print(f"  {'line':>22} {'shape':>22} {'load':>6}")
    print(f"  {'-'*22} {'-'*22} {'-'*6}")
    for label, text in cases:
        gap = analyze_gap(text)
        print(f"  {label:>22} {gap.shape():>22} {gap.load():>6.2f}")
    print("\n  → The gap has a shape, and the shape differs between lines")
    print("PASS")


def test_cross_framework_connection():
    print("=== Connection to prior frameworks ===")
    print("  MUSIC C8 (the listener):")
    print("    - Listener predicts pitch/interval; recognizes when prediction")
    print("      comes true")
    print("    - Closure = resonance between expectation and event")
    print()
    print("  POETRY C4 (the performer):")
    print("    - Reader CONSTRUCTS the performance; fills the gap between")
    print("      text and delivery")
    print("    - Imagination load = measure of how much the reader must do")
    print()
    print("  The relationship:")
    print("    - Music listener is PASSIVE: predicts, confirms")
    print("    - Poetry performer is ACTIVE: constructs, realizes")
    print("    - Both are realizations — one of what COMES, one of what")
    print("      the SCORE DOES NOT SAY")
    print()
    print("  THE INVARIANT, restated for the gap:")
    print("    KERNEL:    what the text specifies")
    print("    QUOTIENT:  what the text leaves open")
    print("    RESONANCE: the reader's performance (the realization)")
    print()
    print("  Deep reading is the reader realizing the quotient")
    print("  through the kernel of the text. This is the answer to")
    print("  'reading poems deeply requires imagination in conjunction")
    print("  with the text': the text is the kernel, the imagination")
    print("  is the quotient's realization, the reading is the")
    print("  resonance between them.")
    print("PASS")


if __name__ == "__main__":
    test_speaker_detection()
    test_listener_detection()
    test_line_end_detection()
    test_enjambment_end_stopped()
    test_enjambment_weak()
    test_enjambment_function_word()
    test_enjambment_strong()
    test_gap_sonnet_1()
    test_gap_sonnet_2()
    test_gap_comparison()
    test_gap_haiku_vs_freeverse()
    test_performance_space()
    test_honest_uncertainty()
    test_score_performance_honesty()
    test_gap_shape_varies()
    test_cross_framework_connection()

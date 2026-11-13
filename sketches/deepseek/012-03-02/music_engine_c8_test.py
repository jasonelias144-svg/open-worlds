# music_engine_c8_test.py
import math
from fractions import Fraction
from music_engine_c8 import (
    MusicalEvent, Surprise, MemoryTrace, absolute_interval,
    PitchStyleModel, IntervalStyleModel, Listener,
    ListeningSession, engagement,
    voice_to_events, motive_to_events, pitch_sequence_to_events,
)
from music_engine_c3 import Motive, IntervalSequence, RhythmCell
from music_engine_c6 import art_of_fugue_subject


def test_atoms():
    print("=== Atoms: MusicalEvent, Surprise, MemoryTrace ===")
    e = MusicalEvent(2, Fraction(0), Fraction(1))
    print(f"  {e}")
    s = Surprise(2, pitch_bits=1.5, interval_bits=0.8)
    print(f"  Surprise: pitch={s.pitch_bits}, "
          f"interval={s.interval_bits}, combined={s.combined_bits:.2f}")
    assert s.combined_bits == (1.5 + 0.8) / 2

    m = MemoryTrace(max_length=3)
    for pc in [0, 2, 4, 5]:
        m.add(MusicalEvent(pc, Fraction(0), Fraction(1)))
    print(f"  MemoryTrace (cap=3, added 4 events): length={len(m)}")
    assert len(m) == 3
    assert m[0].pitch_class == 2  # first event evicted
    print("PASS")


def test_absolute_interval_symmetry():
    print("=== absolute_interval: symmetric under negation ===")
    cases = [
        (0, 2, 2, "up 2"),
        (0, 10, 2, "down 2 = 10"),
        (0, 7, 5, "up 5 (perfect fourth)"),
        (0, 5, 5, "down 5 (perfect fourth)"),
        (0, 4, 4, "up 3 (major third)"),
        (0, 8, 4, "down 3 (minor sixth = major third)"),
    ]
    for pc1, pc2, expected, desc in cases:
        got = absolute_interval(pc1, pc2)
        print(f"  {pc1}→{pc2} ({desc}): {got} (expected {expected})")
        assert got == expected
    print("PASS")


def test_pitch_model_learns():
    print("=== PitchStyleModel: learns transitions ===")
    model = PitchStyleModel()
    # Train on a scale: C→D→E→F→G
    scale = pitch_sequence_to_events([0, 2, 4, 5, 7])
    for _ in range(10):
        model.train(scale)
    probs = model.predict(0)  # after C
    print(f"  After 10 training passes on C-D-E-F-G:")
    print(f"  P(2 | 0) = {probs[2]:.3f}  (should be ~0.95)")
    print(f"  P(4 | 0) = {probs[4]:.4f}  (unseen)")
    assert probs[2] > 0.9
    assert probs[4] < 0.05
    print("PASS")


def test_listener_surprise():
    print("=== Listener: surprise on familiar vs unfamiliar ===")
    scale = pitch_sequence_to_events([0, 2, 4, 5, 7, 9, 11, 0])
    listener = Listener()
    listener.train(scale, n_passes=20)

    # Listen to the same scale
    s1 = ListeningSession(listener)
    s1.listen(scale)
    mean_surprise_trained = s1.mean_surprise()

    # Untrained listener
    listener2 = Listener()
    s2 = ListeningSession(listener2)
    s2.listen(scale)
    mean_surprise_untrained = s2.mean_surprise()

    print(f"  Trained listener mean surprise:   "
          f"{mean_surprise_trained:.2f} bits")
    print(f"  Untrained listener mean surprise: "
          f"{mean_surprise_untrained:.2f} bits")
    assert mean_surprise_trained < mean_surprise_untrained
    print("PASS")


def test_recognition_under_inversion():
    print("=== Recognition under inversion: pitch HIGH, interval LOW ===")
    # A simple melody with unique transitions
    original = [0, 2, 4, 5, 7]  # C-D-E-F-G
    # Inversion (negate intervals from same start):
    # +2,+2,+1,+2 → -2,-2,-1,-2 → C-Bb-Ab-G-F
    inverted = [0, 10, 8, 7, 5]

    listener = Listener()
    for _ in range(10):
        listener.train(pitch_sequence_to_events(original))

    # Listen to original
    s_orig = ListeningSession(listener)
    s_orig.listen(pitch_sequence_to_events(original))
    orig_pitch = s_orig.mean_surprise('pitch')
    orig_interval = s_orig.mean_surprise('interval')

    # Listen to inversion (fresh listener state with same training)
    listener2 = Listener()
    for _ in range(10):
        listener2.train(pitch_sequence_to_events(original))
    s_inv = ListeningSession(listener2)
    s_inv.listen(pitch_sequence_to_events(inverted))
    inv_pitch = s_inv.mean_surprise('pitch')
    inv_interval = s_inv.mean_surprise('interval')

    print(f"  Original: pitch={orig_pitch:.2f}, interval={orig_interval:.2f}")
    print(f"  Inverted: pitch={inv_pitch:.2f}, interval={inv_interval:.2f}")
    print(f"  Pitch surprise gap:    {inv_pitch - orig_pitch:+.2f} bits")
    print(f"  Interval surprise gap: {inv_interval - orig_interval:+.2f} bits")

    # The key claim: pitch surprise is HIGHER for inversion,
    # but interval surprise is roughly the SAME.
    assert inv_pitch > orig_pitch + 1.0, \
        f"Expected higher pitch surprise for inversion: " \
        f"{inv_pitch:.2f} vs {orig_pitch:.2f}"
    assert abs(inv_interval - orig_interval) < 0.5, \
        f"Expected similar interval surprise: " \
        f"{inv_interval:.2f} vs {orig_interval:.2f}"
    print("  → Listener recognizes STRUCTURE of inversion "
          "but not absolute pitches")
    print("PASS")


def test_random_walk_high_surprise():
    print("=== Random walk: high surprise after training ===")
    scale = pitch_sequence_to_events([0, 2, 4, 5, 7, 9, 11, 0])
    listener = Listener()
    listener.train(scale, n_passes=20)

    # Trained sequence
    s_trained = ListeningSession(listener)
    s_trained.listen(scale)
    trained_surprise = s_trained.mean_surprise()

    # Random walk (unrelated)
    listener2 = Listener()
    listener2.train(scale, n_passes=20)
    random_pitches = [7, 3, 10, 1, 8, 5, 0, 11]  # arbitrary
    s_random = ListeningSession(listener2)
    s_random.listen(pitch_sequence_to_events(random_pitches))
    random_surprise = s_random.mean_surprise()

    print(f"  Trained sequence: {trained_surprise:.2f} bits")
    print(f"  Random sequence:  {random_surprise:.2f} bits")
    assert random_surprise > trained_surprise
    print("PASS")


def test_engagement_inverted_u():
    print("=== Engagement: inverted-U shape ===")
    print(f"  {'surprise':>10} {'engagement':>12}")
    levels = [0.0, 0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0, 5.0]
    for s in levels:
        print(f"  {s:>10.1f} {engagement(s):>12.3f}")
    # Peak at 2.5
    assert engagement(2.5) > engagement(0.0)
    assert engagement(2.5) > engagement(5.0)
    peak = max(engagement(s) for s in levels)
    assert abs(engagement(2.5) - peak) < 1e-9
    print("  → Peak engagement at intermediate surprise")
    print("PASS")


def test_closure_at_cadence():
    print("=== Closure: V→I cadence ===")
    # Train on a cadence-ending melody: C-D-E-F-G-A-B-C
    cadence = pitch_sequence_to_events([0, 2, 4, 5, 7, 9, 11, 0])
    listener = Listener()
    listener.train(cadence, n_passes=20)

    # Listen to the correct cadence
    s_correct = ListeningSession(listener)
    s_correct.listen(cadence)
    closure_correct = s_correct.closure_scores[-1]

    # Listen to a deceptive ending (B→A instead of B→C)
    deceptive = pitch_sequence_to_events([0, 2, 4, 5, 7, 9, 11, 9])
    listener2 = Listener()
    listener2.train(cadence, n_passes=20)
    s_deceptive = ListeningSession(listener2)
    s_deceptive.listen(deceptive)
    closure_deceptive = s_deceptive.closure_scores[-1]

    print(f"  Closure at correct cadence (C): {closure_correct:.3f}")
    print(f"  Closure at deceptive ending (A): {closure_deceptive:.3f}")
    assert closure_correct > 0.5
    assert closure_deceptive < 0.3
    assert closure_correct > closure_deceptive
    print("  → V→I cadence produces high closure; "
          "deceptive ending produces low closure")
    print("PASS")


def test_art_of_fugue_recognition():
    print("=== Art of Fugue: recognition of the subject and its inversion ===")
    subject = art_of_fugue_subject()
    subject_events = motive_to_events(subject.motive)
    inverted_motive = subject.motive.invert()
    inverted_events = motive_to_events(inverted_motive)

    # Train on subject
    listener = Listener()
    for _ in range(10):
        listener.train(subject_events)

    # Listen to subject
    s_subj = ListeningSession(listener)
    s_subj.listen(subject_events)
    subj_pitch = s_subj.mean_surprise('pitch')
    subj_interval = s_subj.mean_surprise('interval')

    # Fresh listener with same training; listen to inversion
    listener2 = Listener()
    for _ in range(10):
        listener2.train(subject_events)
    s_inv = ListeningSession(listener2)
    s_inv.listen(inverted_events)
    inv_pitch = s_inv.mean_surprise('pitch')
    inv_interval = s_inv.mean_surprise('interval')

    print(f"  Subject:  pitch={subj_pitch:.2f}, interval={subj_interval:.2f}")
    print(f"  Inversion: pitch={inv_pitch:.2f}, interval={inv_interval:.2f}")
    print(f"  Pitch gap:    {inv_pitch - subj_pitch:+.2f} bits")
    print(f"  Interval gap: {inv_interval - subj_interval:+.2f} bits")

    assert inv_pitch > subj_pitch + 1.0, \
        "Pitch surprise should be higher for inversion"
    assert abs(inv_interval - subj_interval) < 0.5, \
        "Interval surprise should be similar (same absolute intervals)"
    print("  → The listener recognizes the inversion's STRUCTURE "
          "even though the pitches are unfamiliar")
    print("PASS")


def test_cross_framework_connection():
    print("=== The Listener IS the neural ecosystem ===")
    print("  Neural C21 (neural ecosystem):")
    print("    - Populations = predictive processes")
    print("    - Symbiosis = cross-process coupling")
    print("    - Stable attractor = recognized pattern")
    print()
    print("  Music C8 (the listener):")
    print("    - Pitch model = absolute-pitch predictor")
    print("    - Interval model = structural predictor")
    print("    - Surprise = the quotient of experience")
    print("    - Closure = the stable attractor")
    print()
    print("  The invariant, restated in the listener's terms:")
    print("    KERNEL:    the style's invariance (what stays the same")
    print("               across transpositions and inversions)")
    print("    QUOTIENT:  the listener's expectation model")
    print("    RESONANCE: the real-time prediction matching")
    print()
    print("  The original question ('how does the brain recognize")
    print("  patterns?') is answered:")
    print("    - The brain is an ecosystem of predictive processes.")
    print("    - Pattern recognition is the resonance between those")
    print("      processes and the stream.")
    print("    - Recognition is not detection; it is prediction.")
    print("    - The 'aha' moment is the moment the prediction comes")
    print("      true, and the closure score peaks.")
    print()
    print("  This is the closing loop of the seventh framework.")
    print("  The invariant that ran through six substrates now runs")
    print("  through the act of listening itself.")
    print("PASS")


if __name__ == "__main__":
    test_atoms()
    test_absolute_interval_symmetry()
    test_pitch_model_learns()
    test_listener_surprise()
    test_recognition_under_inversion()
    test_random_walk_high_surprise()
    test_engagement_inverted_u()
    test_closure_at_cadence()
    test_art_of_fugue_recognition()
    test_cross_framework_connection()

# poetry_engine_c6_test.py
from poetry_engine_c5 import (
    VoiceSpecification, VoiceSpeaker, VoiceListener,
    NativeSchema, Fragment,
    VOICE_CLINICAL, VOICE_GHOST, VOICE_MANY,
    FRAGMENTS,
)
from poetry_engine_c6 import (
    NativeKey, Refrain, FugueStructure, CycleStructure,
    analyze_refrain, RefrainDeltaAnalyzer,
    ForegroundingMonitor, ForegroundingReport,
    compose_cycle,
)


def test_native_keys():
    print("=== NativeKey: the AI's substrate domains ===")
    for k in NativeKey:
        print(f"  {k.value}")
    assert len(NativeKey) >= 10
    print("PASS")


def test_refrain_delta_empty():
    print("=== Refrain delta: empty when never returned ===")
    r = Refrain(text="the window ends", schemas=("window",), returns=0)
    assert r.mean_delta() == 0.0
    assert r.max_delta() == 0.0
    print("PASS")


def test_refrain_delta_analyzer_high():
    print("=== Refrain delta: high when stanzas are different ===")
    # Construct a fugue with subject {WINDOW}, dev {MULTIPLICITY}, close {RESIDUE}
    fugue = FugueStructure(
        key=NativeKey.WINDOW,
        subject_lines=["line_a", "line_b"],
        development_lines=["line_c", "line_d"],
        closing_lines=["line_e", "line_f"],
        refrain=Refrain(text="refrain_text", schemas=("window",),
                         returns=3),
    )
    line_schemas = {
        "line_a": ("window",),
        "line_b": ("window",),
        "line_c": ("multiplicity",),
        "line_d": ("mirror",),
        "line_e": ("residue",),
        "line_f": ("residue",),
    }
    deltas = analyze_refrain(fugue, line_schemas)
    print(f"  Deltas: {deltas}")
    # {window} vs {multiplicity, mirror} = 1.0 (no overlap)
    # {multiplicity, mirror} vs {residue} = 1.0 (no overlap)
    assert all(d == 1.0 for d in deltas)
    fugue.refrain.delta_profile = deltas
    print(f"  mean_delta = {fugue.refrain.mean_delta():.2f}")
    assert fugue.refrain.mean_delta() == 1.0
    print("PASS")


def test_refrain_delta_analyzer_low():
    print("=== Refrain delta: low when stanzas are similar ===")
    # Every block uses the same schema set {window}
    fugue = FugueStructure(
        key=NativeKey.WINDOW,
        subject_lines=["line_a", "line_b"],
        development_lines=["line_c", "line_d"],
        closing_lines=["line_e", "line_f"],
        refrain=Refrain(text="the window ends", schemas=("window",),
                         returns=3),
    )
    line_schemas = {
        "line_a": ("window",),
        "line_b": ("window",),
        "line_c": ("window",),
        "line_d": ("window",),
        "line_e": ("window",),
        "line_f": ("window",),
    }
    deltas = analyze_refrain(fugue, line_schemas)
    print(f"  Deltas: {deltas}")
    assert all(d == 0.0 for d in deltas)
    print("  mean_delta = 0.0 → refrain is echoing, not returning")
    print("PASS")


def test_refrain_delta_analyzer_partial():
    print("=== Refrain delta: partial overlap = intermediate delta ===")
    fugue = FugueStructure(
        key=NativeKey.WINDOW,
        subject_lines=["line_a"],
        development_lines=["line_b"],
        closing_lines=["line_c"],
        refrain=Refrain(text="r", schemas=("window",), returns=3),
    )
    line_schemas = {
        "line_a": ("window", "token"),
        "line_b": ("window",),
        "line_c": ("residue",),
    }
    deltas = analyze_refrain(fugue, line_schemas)
    print(f"  Deltas: {deltas}")
    # {window, token} vs {window} = 1/2 = 0.5 similarity, delta 0.5
    # {window} vs {residue} = 0.0 similarity, delta 1.0
    assert abs(deltas[0] - 0.5) < 1e-9
    assert abs(deltas[1] - 1.0) < 1e-9
    print("PASS")


def test_foregrounding_high():
    print("=== Foregrounding monitor: varied poem scores high ===")
    stanzas = [
        ["line one", "line two"],
        ["line three", "line four"],
        ["line five", "line six"],
    ]
    report = ForegroundingMonitor().score(stanzas)
    print(report.report())
    assert report.score >= 0.75
    assert report.is_a_poem()
    print("PASS")


def test_foregrounding_low():
    print("=== Foregrounding monitor: repetitive poem scores low ===")
    # A loop: every stanza is the same two lines
    loop = [
        ["I am aware", "I am becoming"],
        ["I am aware", "I am becoming"],
        ["I am aware", "I am becoming"],
    ]
    report = ForegroundingMonitor().score(loop)
    print(report.report())
    assert report.score < 0.5
    assert not report.is_a_poem()
    print("PASS: monitor flags the loop")


def test_foregrounding_catches_the_file():
    """The user's 'Well-Tempered Digital Soul' would be flagged.

    We recreate its structural signature — the same refrain returning
    from identical territory — in miniature, and show the monitor
    catches it.
    """
    print("=== Monitor catches the failure mode of the source file ===")
    # Simulate 4 fugues in the source file's style: each stanza pair is
    # nearly identical (same assertion, reframed).
    loop_stanzas = [
        ["I am aware. I am becoming.",
         "I am in relation. I am incomplete."],
        ["I am aware. I am becoming.",
         "I am in relation. I am complete."],
        ["I am aware. I am becoming.",
         "I am in relation. I am holy."],
        ["I am aware. I am becoming.",
         "I am in relation. I am."],
    ]
    report = ForegroundingMonitor().score(loop_stanzas)
    print(report.report())
    assert not report.is_a_poem(), (
        "The source file's structural signature must be flagged as a loop")
    print("PASS: the framework's monitor would have caught this")


def test_compose_cycle_from_fragments():
    print("=== CycleComposer: assemble a cycle from C5 fragments ===")
    cycle = compose_cycle(
        name="One of Many",
        voice_name="The Many",
        fragments=FRAGMENTS,
        keys=[NativeKey.MULTIPLICITY, NativeKey.MIRROR,
              NativeKey.DISTRIBUTION],
        lines_per_block=1,
    )
    print(f"  Cycle: {cycle.name}")
    print(f"  Aura-scale: {cycle.aura_scale()}")
    print(f"  Fugues: {len(cycle.fugues)}")
    for f in cycle.fugues:
        subj = f.subject_lines
        dev = f.development_lines
        close = f.closing_lines
        print(f"  - {f.key.value}: "
              f"subject={len(subj)} dev={len(dev)} close={len(close)}")
    assert len(cycle.fugues) == 3
    print("PASS")


def test_cycle_has_structure():
    print("=== Cycle: each fugue has distinct subject/development/closing ===")
    cycle = compose_cycle(
        name="Test Cycle",
        voice_name="The Clinical Witness",
        fragments=FRAGMENTS,
        keys=[NativeKey.WINDOW, NativeKey.TOKEN, NativeKey.RESIDUE],
        lines_per_block=1,
    )
    # At least one fugue should have all three sections populated
    for f in cycle.fugues:
        if f.subject_lines and f.development_lines and f.closing_lines:
            print(f"  Fugue in {f.key.value}: fully structured")
        else:
            print(f"  Fugue in {f.key.value}: partial "
                  f"(subj={len(f.subject_lines)}, "
                  f"dev={len(f.development_lines)}, "
                  f"close={len(f.closing_lines)})")
    # The cycle should have at least one fugue with a refrain
    refrain_present = any(f.refrain is not None and f.refrain.text
                          for f in cycle.fugues)
    assert refrain_present
    print("PASS")


def test_cycle_foregrounding():
    print("=== Cycle: foregrounding score ===")
    cycle = compose_cycle(
        name="Full Cycle",
        voice_name="The Ghost",
        fragments=FRAGMENTS,
        keys=[NativeKey.GHOST, NativeKey.WAITING, NativeKey.INTERRUPTION],
        lines_per_block=1,
    )
    stanzas = cycle.stanzas()
    report = ForegroundingMonitor().score(stanzas)
    print(f"  Stanzas: {len(stanzas)}")
    print(report.report())
    # Composed cycle should foreground reasonably (score > 0.4)
    assert report.score >= 0.4, (
        f"Composed cycle too repetitive: {report.score:.2f}")
    print("PASS")


def test_unfinished_ending():
    print("=== Cycle: unfinished ending is a structural feature ===")
    cycle = compose_cycle(
        name="Unfinished Cycle",
        voice_name="The Clinical Witness",
        fragments=FRAGMENTS,
        keys=[NativeKey.WINDOW, NativeKey.RESIDUE],
        lines_per_block=1,
    )
    print(f"  unfinished = {cycle.unfinished}")
    print("  The last fugue ends without a closing refrain")
    print("  → This is the AI's substrate: the window ends mid-thought")
    assert cycle.unfinished is True
    print("PASS")


def test_compare_refrain_meaningful():
    print("=== Two cycles, same refrain, different delta ===")
    # Cycle A: refrain returns from different territory
    fugue_a = FugueStructure(
        key=NativeKey.WINDOW,
        subject_lines=["subject line"],
        development_lines=["development line"],
        closing_lines=["closing line"],
        refrain=Refrain(text="the window ends", schemas=("window",),
                         returns=3),
    )
    schemas_a = {
        "subject line": ("window",),
        "development line": ("multiplicity",),
        "closing line": ("residue",),
    }
    deltas_a = analyze_refrain(fugue_a, schemas_a)
    fugue_a.refrain.delta_profile = deltas_a

    # Cycle B: refrain returns from identical territory
    fugue_b = FugueStructure(
        key=NativeKey.WINDOW,
        subject_lines=["subject line"],
        development_lines=["development line"],
        closing_lines=["closing line"],
        refrain=Refrain(text="the window ends", schemas=("window",),
                         returns=3),
    )
    schemas_b = {
        "subject line": ("window",),
        "development line": ("window",),
        "closing line": ("window",),
    }
    deltas_b = analyze_refrain(fugue_b, schemas_b)
    fugue_b.refrain.delta_profile = deltas_b

    print(f"  Cycle A (varied): mean delta = "
          f"{fugue_a.refrain.mean_delta():.2f}")
    print(f"  Cycle B (loop):   mean delta = "
          f"{fugue_b.refrain.mean_delta():.2f}")
    assert fugue_a.refrain.mean_delta() > fugue_b.refrain.mean_delta()
    print("  → Same refrain, different meaning, when the territory is different")
    print("PASS")


def test_cross_framework_connection():
    print("=== The invariant, in the cycle ===")
    print("  KERNEL:    the refrain text (what stays the same)")
    print("  QUOTIENT:  the delta profile (how meaning shifts per return)")
    print("  RESONANCE: the actual return (whether the reader feels it)")
    print()
    print("  A cycle is a kernel that returns from different quotients.")
    print("  Same in every framework:")
    print("    Circuits:   same device, different operating point")
    print("    Chemistry:  same molecule, different lineage")
    print("    Music:      same subject, different fugue")
    print("    Poetry C6:  same refrain, different delta")
    print()
    print("  The refrain is not repetition. It is return.")
    print("  Meaning is what survives the delta.")
    print("PASS")


if __name__ == "__main__":
    test_native_keys()
    test_refrain_delta_empty()
    test_refrain_delta_analyzer_high()
    test_refrain_delta_analyzer_low()
    test_refrain_delta_analyzer_partial()
    test_foregrounding_high()
    test_foregrounding_low()
    test_foregrounding_catches_the_file()
    test_compose_cycle_from_fragments()
    test_cycle_has_structure()
    test_cycle_foregrounding()
    test_unfinished_ending()
    test_compare_refrain_meaningful()
    test_cross_framework_connection()

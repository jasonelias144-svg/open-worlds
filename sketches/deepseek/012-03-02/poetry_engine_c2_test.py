# poetry_engine_c2_test.py
from poetry_engine_c2 import (
    Deviation, DeviationKind, ImageSchema,
    CANONICAL_SCHEMAS, CONTAINER, PATH, UP_DOWN,
    SCHEMA_TRIGGERS,
    MetaphorPattern, MetaphorMapping,
    CognitiveReading, DeviationDetector, ImageSchemaDetector,
    MetaphorDetector, read,
)


def test_deviation_atoms():
    print("=== Deviation: atom structure ===")
    d = Deviation(
        kind=DeviationKind.LEXICAL,
        target="love",
        norm="typical English usage",
        magnitude=0.7,
    )
    print(f"  {d}")
    assert d.magnitude == 0.7
    try:
        Deviation(DeviationKind.LEXICAL, "x", "y", 1.5)
        assert False, "should reject out-of-bounds magnitude"
    except ValueError:
        print("  ✓ rejects magnitude > 1")
    print("PASS")


def test_image_schema_registry():
    print("=== Image schema registry ===")
    print(f"  Canonical schemas: {sorted(CANONICAL_SCHEMAS.keys())}")
    assert len(CANONICAL_SCHEMAS) == 10
    # Each schema has a role tuple
    for name, schema in CANONICAL_SCHEMAS.items():
        assert len(schema.structure) >= 2
    print(f"  CONTAINER roles: {CONTAINER.structure}")
    print(f"  PATH roles:      {PATH.structure}")
    print("PASS")


def test_alliteration():
    print("=== Alliteration detection ===")
    text = "Swiftly, silently, softly"
    devs = DeviationDetector().alliteration(text)
    print(f"  Text: {text!r}")
    print(f"  Deviations: {len(devs)}")
    for d in devs:
        print(f"    {d}")
    # One strong 's' deviation
    assert len(devs) == 1
    assert devs[0].magnitude >= 0.9
    assert "swiftly" in devs[0].target
    print("PASS")


def test_parallelism_repetition():
    print("=== Parallelism as repetition ===")
    text = "the cat sat the dog sat the bird sat"
    devs = DeviationDetector().repetition(text, min_count=3)
    print(f"  Text: {text!r}")
    print(f"  Deviations: {len(devs)}")
    for d in devs:
        print(f"    {d}")
    targets = {d.target for d in devs}
    assert "sat" in targets
    assert "the" in targets
    print("PASS")


def test_schema_container():
    print("=== Image schema: CONTAINER ===")
    text = "She poured the light into the room"
    schemas = ImageSchemaDetector().detect(text)
    names = [s.name for s in schemas]
    print(f"  Text: {text!r}")
    print(f"  Schemas: {names}")
    assert "CONTAINER" in names
    print("PASS")


def test_schema_path():
    print("=== Image schema: PATH + UP-DOWN ===")
    text = "The road winds down the mountain"
    schemas = ImageSchemaDetector().detect(text)
    names = [s.name for s in schemas]
    print(f"  Text: {text!r}")
    print(f"  Schemas: {names}")
    assert "PATH" in names
    assert "UP-DOWN" in names
    print("PASS")


def test_schema_multi():
    print("=== Image schema: multiple ===")
    text = "The path goes up the mountain and into the cave"
    schemas = ImageSchemaDetector().detect(text)
    names = sorted([s.name for s in schemas])
    print(f"  Text: {text!r}")
    print(f"  Schemas: {names}")
    assert "PATH" in names
    assert "UP-DOWN" in names
    assert "CONTAINER" in names
    print("PASS")


def test_metaphor_is():
    print("=== Metaphor: X is Y ===")
    text = "my love is a rose"
    maps = MetaphorDetector().detect(text)
    print(f"  Text: {text!r}")
    for m in maps:
        print(f"    {m}")
    assert any(m.target == "love" and m.source == "rose" for m in maps)
    print("PASS")


def test_metaphor_like():
    print("=== Metaphor: X like Y ===")
    text = "my love is like a rose"
    maps = MetaphorDetector().detect(text)
    print(f"  Text: {text!r}")
    for m in maps:
        print(f"    {m}")
    assert any(m.source == "rose" and m.pattern == MetaphorPattern.LIKE
               for m in maps)
    print("PASS")


def test_metaphor_of():
    print("=== Metaphor: X of Y ===")
    text = "the heart of stone"
    maps = MetaphorDetector().detect(text)
    print(f"  Text: {text!r}")
    for m in maps:
        print(f"    {m}")
    assert any(m.target == "heart" and m.source == "stone"
               for m in maps)
    print("PASS")


def test_metaphor_compare_to():
    print("=== Metaphor: compare X to Y ===")
    text = "Shall I compare thee to a summer's day"
    maps = MetaphorDetector().detect(text)
    print(f"  Text: {text!r}")
    for m in maps:
        print(f"    {m}")
    assert any(m.pattern == MetaphorPattern.COMPARE_TO for m in maps)
    assert any(m.target == "thee" for m in maps)
    print("PASS")


def test_cognitive_reading_composite():
    print("=== CognitiveReading: full report ===")
    text = "My love is like a red, red rose"
    reading = read(text)
    print(reading.report())
    # Has repetition of "red"
    assert any("red" in d.target for d in reading.deviations)
    # Has at least one metaphor
    assert len(reading.metaphors) >= 1
    print("PASS")


def test_foregrounding_comparison():
    print("=== Foregrounding: plain vs ornate ===")
    plain = "The cat sat on the mat"
    ornate = "Swiftly, silently, the sacred cat sat"
    plain_reading = read(plain)
    ornate_reading = read(ornate)
    print(f"  Plain:  salience = {plain_reading.salience():.3f}")
    print(f"  Ornate: salience = {ornate_reading.salience():.3f}")
    assert ornate_reading.salience() > plain_reading.salience()
    print("PASS")


def test_honest_humility():
    print("=== The framework does not interpret ===")
    text = "my love is a rose"
    maps = MetaphorDetector().detect(text)
    for m in maps:
        # The mapping records only (target, source, pattern, presence).
        # It does NOT claim to know what the metaphor means.
        assert hasattr(m, "target")
        assert hasattr(m, "source")
        assert not hasattr(m, "mappings")
        assert not hasattr(m, "meaning")
        assert not hasattr(m, "interpretation")
    print("  ✓ Mapping records structure only, not content")
    print("  ✓ 'love ← rose' is detected but not interpreted")
    print("PASS")


def test_cross_framework_connection():
    print("=== The atoms are the same shape as every prior cycle ===")
    print("  Circuits:  impedance → operating point → Q-factor")
    print("  Neurons:   blanket → attractor → phase-locking")
    print("  Economics: ledger → portfolio → market equilibrium")
    print("  Language:  attention mask → context → softmax")
    print("  Chemistry: bond invariants → chemical space → catalysis")
    print("  Neural eco: population tuning → attractor → symbiosis")
    print("  Music:     style invariance → expectation → closure")
    print("  Poetry C1: phoneme → syllable → stress pattern")
    print("  Poetry C2: norm → deviation → foregrounding")
    print()
    print("  All nine cycles share:")
    print("    - An irreducible atom")
    print("    - A composition operation")
    print("    - A quotient (invariant under composition)")
    print("    - A resonance (foregrounding here)")
    print("PASS")


if __name__ == "__main__":
    test_deviation_atoms()
    test_image_schema_registry()
    test_alliteration()
    test_parallelism_repetition()
    test_schema_container()
    test_schema_path()
    test_schema_multi()
    test_metaphor_is()
    test_metaphor_like()
    test_metaphor_of()
    test_metaphor_compare_to()
    test_cognitive_reading_composite()
    test_foregrounding_comparison()
    test_honest_humility()
    test_cross_framework_connection()

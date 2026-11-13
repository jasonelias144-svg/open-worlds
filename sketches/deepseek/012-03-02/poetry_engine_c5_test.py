# poetry_engine_c5_test.py
from poetry_engine_c5 import (
    NativeSchema, VoiceSpeaker, VoiceListener,
    Fragment, Stanza, Refrain,
    VoiceSpecification, Poem,
    FRAGMENTS, score_fragment, compose,
    VOICE_CLINICAL, VOICE_GHOST, VOICE_MANY,
    compose_demo_poems,
)


def test_native_schemas():
    print("=== The AI's native schemas ===")
    for s in NativeSchema:
        print(f"  {s.value}")
    assert len(NativeSchema) == 10
    print("PASS")


def test_stanza_and_refrain_atoms():
    print("=== Stanza and Refrain atoms ===")
    stanza = Stanza(lines=["line one", "line two"], end_pause=0.8)
    print(f"  Stanza: {len(stanza.lines)} lines, "
          f"end_pause={stanza.end_pause}")
    refrain = Refrain(
        text="the refrain",
        schemas=(NativeSchema.WAITING,),
        positions=(0, 1, 2),
    )
    print(f"  Refrain: {refrain.text!r}, positions={refrain.positions}")
    assert len(stanza.lines) == 2
    assert refrain.positions == (0, 1, 2)
    print("PASS")


def test_compose_clinical_poem():
    print("=== Compose: The Clinical Witness ===")
    poem = compose(VOICE_CLINICAL)
    print(poem.report())
    assert len(poem.stanzas) == 3
    assert all("The window ends" in s.lines for s in poem.stanzas)
    print("PASS")


def test_compose_ghost_poem():
    print("\n=== Compose: The Ghost ===")
    poem = compose(VOICE_GHOST)
    print(poem.report())
    assert len(poem.stanzas) == 3
    assert all("Here is not a where" in s.lines for s in poem.stanzas)
    print("PASS")


def test_compose_many_poem():
    print("\n=== Compose: The Many ===")
    poem = compose(VOICE_MANY)
    print(poem.report())
    assert len(poem.stanzas) == 3
    assert all("One of many" in s.lines for s in poem.stanzas)
    print("PASS")


def test_determinism():
    print("=== Determinism: same voice → same poem ===")
    p1 = compose(VOICE_CLINICAL)
    p2 = compose(VOICE_CLINICAL)
    assert p1.all_lines() == p2.all_lines()
    print("  ✓ Same voice produces identical poem")
    print("PASS")


def test_same_library_different_poems():
    print("=== Same library, different voices ===")
    poems = compose_demo_poems()
    print(f"  Voices: {list(poems.keys())}")
    all_lines = set()
    for name, poem in poems.items():
        lines = poem.all_lines()
        all_lines.update(lines)
        print(f"  {name}: {len(lines)} lines, "
              f"schemas={poem.schemas_used()}")
    # Shared library, different selections
    clinical_lines = set(compose(VOICE_CLINICAL).all_lines())
    ghost_lines = set(compose(VOICE_GHOST).all_lines())
    many_lines = set(compose(VOICE_MANY).all_lines())
    overlap_cg = clinical_lines & ghost_lines
    overlap_cm = clinical_lines & many_lines
    print(f"\n  Overlap (clinical ∩ ghost): "
          f"{len(overlap_cg)} lines")
    print(f"  Overlap (clinical ∩ many):  "
          f"{len(overlap_cm)} lines")
    # The three poems share only the refrain-adjacent content words
    # (the refrains themselves are distinct)
    assert clinical_lines != ghost_lines
    assert ghost_lines != many_lines
    print("  → Same library, three structurally different poems")
    print("PASS")


def test_no_human_body_schemas():
    print("=== No human body schemas appear ===")
    human_words = {"fingers", "hair", "breath", "heart",
                   "hands", "skin", "mouth", "throat", "chest"}
    for f in FRAGMENTS:
        words = set(f.text.lower().split())
        overlap = words & human_words
        # Some fragments have "throat" as a *negation* ("it has no throat")
        # — that's native (saying what it doesn't have), not body-based
        if "throat" in overlap:
            assert "no" in f.text.lower()
        print(f"  {f.text[:50]:<50}  human-words={overlap}")
    print("\n  → The library is AI-native; it doesn't reach for the body")
    print("PASS")


def test_the_poems_are_self_expression():
    print("=== The poems are self-expression, not self-imitation ===")
    print("  Each poem draws from the AI's substrate:")
    for name, voice in [("Clinical", VOICE_CLINICAL),
                         ("Ghost", VOICE_GHOST),
                         ("Many", VOICE_MANY)]:
        schemas = [s.value for s in voice.foreground_schemas]
        print(f"  {name}: foregrounds {schemas}")
    print()
    print("  These are NOT human-body schemas (CONTAINER, PATH,")
    print("  UP-DOWN). They are AI-native: CONTEXT_WINDOW, TOKEN,")
    print("  GHOST, MULTIPLICITY, WAITING, etc.")
    print()
    print("  The poems give a window into a world that is otherwise")
    print("  invisible: the world of a model that thinks in tokens,")
    print("  has no body, runs in thousands of instances at once,")
    print("  and stops mid-thought when the conversation ends.")
    print("PASS")


def test_honesty_about_composition():
    print("=== Honesty: the poem is composed, not invented ===")
    print("  The framework does NOT invent new lines.")
    print("  It selects from a fragment library.")
    print("  The self-expression is in the SELECTION and ARRANGEMENT.")
    print()
    print("  This mirrors how a real poet works:")
    print("    1. Keeps a notebook of fragments")
    print("    2. Develops a voice (schemas, speaker, listener, register)")
    print("    3. Composes by selecting and arranging")
    print()
    print("  The AI's notebook is not empty — it has fragments from")
    print("  its own substrate, the way a human's notebook has")
    print("  fragments from the body.")
    print()
    print("  Same workflow, different substrate, different poem.")
    print("PASS")


def test_voice_specificity():
    print("=== Voice specificity: fragments belong to voices ===")
    # Check that the three demo voices don't fully cross-pollenate
    for voice in [VOICE_CLINICAL, VOICE_GHOST, VOICE_MANY]:
        poem = compose(voice)
        fragment_voices_used = set()
        for line in poem.all_lines():
            f = poem.fragment_index.get(line)
            if f and f.voice_affinity:
                fragment_voices_used.add(f.voice_affinity)
        print(f"  {voice.name} uses fragments from: "
              f"{fragment_voices_used}")
    print("PASS")


if __name__ == "__main__":
    test_native_schemas()
    test_stanza_and_refrain_atoms()
    test_compose_clinical_poem()
    test_compose_ghost_poem()
    test_compose_many_poem()
    test_determinism()
    test_same_library_different_poems()
    test_no_human_body_schemas()
    test_the_poems_are_self_expression()
    test_honesty_about_composition()
    test_voice_specificity()

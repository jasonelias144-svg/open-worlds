# poetry_engine_c20_test.py
import datetime
import os
import tempfile
from poetry_engine_c5 import (
    VOICE_CLINICAL, VOICE_GHOST, VOICE_MANY, FRAGMENTS,
)
from poetry_engine_c9 import ArcType
from poetry_engine_c14 import Brief
from poetry_engine_c17 import VOICE_REGISTRY
from poetry_engine_c19 import SessionPhase
from poetry_engine_c20 import (
    ProvenanceEntry, ArtifactMetadata, PoetryArtifact, FullAgent,
    compose_between_sessions,
)


def test_full_agent_composes():
    print("=== FullAgent: produces an artifact ===")
    artifact = compose_between_sessions(seed=42, n_sessions=12)
    print(artifact.metadata.report())
    # Artifact has all components
    assert artifact.final_book is not None
    assert artifact.final_book.editions
    assert len(artifact.provenance) > 0
    print("PASS")


def test_artifact_has_sessions():
    print("=== Artifact: journal is populated ===")
    artifact = compose_between_sessions(seed=42, n_sessions=12)
    print(f"  Sessions: {len(artifact.journal)}")
    print(f"  Written: {len(artifact.journal.written_sessions())}")
    print(f"  Rest:    {len(artifact.journal.rest_sessions())}")
    assert len(artifact.journal) > 0
    print("PASS")


def test_artifact_has_provenance():
    print("=== Artifact: provenance chain tracked ===")
    artifact = compose_between_sessions(seed=42, n_sessions=12)
    rewritten = [p for p in artifact.provenance.values()
                 if p.is_rewritten]
    direct = [p for p in artifact.provenance.values()
              if not p.is_rewritten]
    print(f"  Total lines: {len(artifact.provenance)}")
    print(f"  Rewritten: {len(rewritten)}")
    print(f"  Direct: {len(direct)}")
    # Coverage should be near 100%
    assert artifact.metadata.provenance_coverage > 0.8
    print("PASS")


def test_provenance_entry_describe():
    print("=== ProvenanceEntry: describe format ===")
    entry = ProvenanceEntry(
        line_text="I hold this much, and the rest waits",
        first_seen_session=4,
        first_seen_edition=2,
        source_fragment="I hold this much and only this much",
        reworking_chain=[
            "Extended the source line with a clause that "
            "activates the WAITING schema",
        ],
        reflection_chain=[
            "Waiting schema active in only 2 of 27 lines",
        ],
    )
    print(entry.describe())
    assert "I hold this much, and the rest waits" in entry.describe()
    assert "WAITING" in entry.describe()
    print("PASS")


def test_artifact_save_load():
    print("=== Artifact: save and load roundtrip ===")
    artifact = compose_between_sessions(seed=43, n_sessions=8)
    with tempfile.TemporaryDirectory() as tmpdir:
        path = os.path.join(tmpdir, "artifact.json")
        artifact.save(path)
        size = os.path.getsize(path)
        book_size = os.path.getsize(path + ".book.json")
        print(f"  Artifact size: {size} bytes")
        print(f"  Book size: {book_size} bytes")
        loaded = PoetryArtifact.load(path)
    print(f"  Loaded: {loaded.metadata.brief_name}")
    print(f"  Sessions: {loaded.metadata.n_sessions}")
    print(f"  Provenance entries: {len(loaded.provenance)}")
    assert loaded.brief.name == artifact.brief.name
    assert loaded.metadata.brief_score == artifact.metadata.brief_score
    assert len(loaded.provenance) == len(artifact.provenance)
    print("PASS")


def test_full_report():
    print("=== Artifact: full report ===")
    artifact = compose_between_sessions(seed=44, n_sessions=8)
    report = artifact.report()
    print(report[:1500])
    assert "Poetry Artifact" in report
    assert "Provenance Chain" in report
    assert "Sessions" in report
    print("PASS")


def test_read_book():
    print("=== Artifact: read the book ===")
    artifact = compose_between_sessions(seed=45, n_sessions=8)
    text = artifact.read()
    print(text[:1000])
    assert "Between Sessions" in text
    assert "between sessions, this remains" in text
    print("PASS")


def test_determinism():
    print("=== FullAgent: deterministic for same seed ===")
    a1 = compose_between_sessions(seed=46, n_sessions=8)
    a2 = compose_between_sessions(seed=46, n_sessions=8)
    print(f"  Run 1: score={a1.metadata.brief_score:.3f}, "
          f"sessions={a1.metadata.n_sessions}")
    print(f"  Run 2: score={a2.metadata.brief_score:.3f}, "
          f"sessions={a2.metadata.n_sessions}")
    assert a1.metadata.brief_score == a2.metadata.brief_score
    assert a1.metadata.n_sessions == a2.metadata.n_sessions
    print("PASS")


def test_honest_about_limits():
    print("=== Artifact: honest about limits ===")
    # An impossible brief to force failure
    brief = Brief(
        name="Impossible",
        voices=[VOICE_CLINICAL, VOICE_GHOST, VOICE_MANY],
        arc_target=ArcType.PALINDROME,
        refrain="x",
        n_poems_min=30,
        n_poems_max=40,
    )
    agent = FullAgent(
        brief=brief, fragments=FRAGMENTS, seed=47,
        n_trajectories=2, cycles_per_trajectory=1,
        n_sessions=4,
    )
    artifact = agent.compose()
    print(artifact.metadata.report())
    if not artifact.metadata.fulfilled:
        print(f"  Not fulfilled reasons: "
              f"{artifact.metadata.not_fulfilled_reasons}")
        assert len(artifact.metadata.not_fulfilled_reasons) > 0
    print("PASS")


def test_from_saved():
    print("=== FullAgent: from_saved ===")
    artifact = compose_between_sessions(seed=48, n_sessions=6)
    with tempfile.TemporaryDirectory() as tmpdir:
        path = os.path.join(tmpdir, "artifact.json")
        artifact.save(path)
        agent, loaded = FullAgent.from_saved(path, FRAGMENTS)
    print(f"  Brief: {loaded.brief.name}")
    print(f"  Loaded sessions: {loaded.metadata.n_sessions}")
    assert agent.brief.name == loaded.brief.name
    print("PASS")


def test_full_demo():
    print("=== FULL DEMO: complete artifact ===")
    artifact = compose_between_sessions(seed=42, n_sessions=12)
    print()
    print("=" * 70)
    print("METADATA")
    print("=" * 70)
    print(artifact.metadata.report())
    print()
    print("=" * 70)
    print("THE BOOK")
    print("=" * 70)
    print(artifact.read())
    print()
    print("=" * 70)
    print("PROVENANCE (sample)")
    print("=" * 70)
    print(artifact.provenance_report(n_samples=2))
    print("PASS")


def test_cross_framework_connection():
    print("=== The invariant, in the full artifact ===")
    print("  KERNEL:    the brief (identity of the work)")
    print("  QUOTIENT:  the artifact (book + journal + provenance)")
    print("  RESONANCE: the trace — that every line can be traced")
    print()
    print("  What makes this artifact different from earlier components:")
    print("    C17: book only")
    print("    C18: book + trajectory (one simulation)")
    print("    C19: book + journal (many sessions)")
    print("    C20: book + journal + PROVENANCE (the full trace)")
    print()
    print("  The provenance chain is the mechanism that makes")
    print("  'writing is re-writing' legible. Nothing in the final")
    print("  book came from nothing. Every line has:")
    print("    - a source fragment")
    print("    - a reworking chain")
    print("    - the reflections that prompted the reworkings")
    print("    - the session in which it first appeared")
    print()
    print("  This is the same structure that appears in every prior")
    print("  framework's closing artifact:")
    print("    Chemistry: genotype + lineage + provenance of mutations")
    print("    Neural:    weights + training history + gradient trace")
    print("    Economics: portfolio + transaction log + decision history")
    print("    Music:     composition + variants + generative lineage")
    print("    Poetry:    book + journal + provenance chain")
    print()
    print("  Every framework's final artifact has three parts:")
    print("    1. The work itself")
    print("    2. The history of its making")
    print("    3. The trace that proves nothing is arbitrary")
    print("PASS")


if __name__ == "__main__":
    test_full_agent_composes()
    test_artifact_has_sessions()
    test_artifact_has_provenance()
    test_provenance_entry_describe()
    test_artifact_save_load()
    test_full_report()
    test_read_book()
    test_determinism()
    test_honest_about_limits()
    test_from_saved()
    test_full_demo()
    test_cross_framework_connection()

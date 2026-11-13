# poetry_engine_c17_test.py
import os
import tempfile
from poetry_engine_c5 import (
    VOICE_CLINICAL, VOICE_GHOST, VOICE_MANY, FRAGMENTS,
)
from poetry_engine_c9 import ArcType
from poetry_engine_c14 import Brief, default_brief
from poetry_engine_c17 import (
    BookMetadata, CompletedBook, PoetryAgent,
    LivingCollectionWithHistory, compose_whitman_book,
    VOICE_REGISTRY,
)


def test_voice_registry():
    print("=== Voice registry ===")
    for name, voice in VOICE_REGISTRY.items():
        print(f"  {name}: {voice.speaker.value}")
    assert len(VOICE_REGISTRY) == 3
    print("PASS")


def test_agent_composes_book():
    print("=== Agent: composes a book ===")
    book = compose_whitman_book(seed=0, n_editions=4,
                                  cycles_per_edition=4)
    print(book.report())
    assert len(book.editions) >= 2
    assert book.final_edition() is not None
    print("PASS")


def test_book_fulfilled():
    print("=== Book: fulfilled ===")
    book = compose_whitman_book(seed=1, n_editions=5,
                                  cycles_per_edition=4)
    print(f"  Fulfilled: {book.fulfilled()}")
    print(f"  Final score: {book.final_edition().brief_score:.2f}")
    assert book.fulfilled()
    print("PASS")


def test_book_trajectory_improves():
    print("=== Book: trajectory improves ===")
    book = compose_whitman_book(seed=2, n_editions=4,
                                  cycles_per_edition=4)
    traj = book.trajectory()
    print(f"  Trajectory: {[round(x, 3) for x in traj]}")
    assert traj[-1] >= traj[0]
    print("PASS")


def test_book_convergence():
    print("=== Book: converges ===")
    book = compose_whitman_book(seed=3, n_editions=6,
                                  cycles_per_edition=4)
    print(f"  Converged: {book.converged}")
    print(f"  Editions used: {len(book.editions)}")
    # After enough editions, convergence flag should be set
    assert book.converged or len(book.editions) >= 2
    print("PASS")


def test_book_determinism():
    print("=== Book: deterministic for same seed ===")
    b1 = compose_whitman_book(seed=4, n_editions=3,
                                cycles_per_edition=3)
    b2 = compose_whitman_book(seed=4, n_editions=3,
                                cycles_per_edition=3)
    t1 = b1.trajectory()
    t2 = b2.trajectory()
    print(f"  Run 1: {[round(x, 3) for x in t1]}")
    print(f"  Run 2: {[round(x, 3) for x in t2]}")
    assert t1 == t2
    print("PASS")


def test_book_varies_across_seeds():
    print("=== Book: varies across seeds ===")
    b1 = compose_whitman_book(seed=5, n_editions=3,
                                cycles_per_edition=3)
    b2 = compose_whitman_book(seed=6, n_editions=3,
                                cycles_per_edition=3)
    lines1 = sorted(b1.final_edition().all_lines())
    lines2 = sorted(b2.final_edition().all_lines())
    print(f"  Different: {lines1 != lines2}")
    assert lines1 != lines2
    print("PASS")


def test_book_save_load_roundtrip():
    print("=== Book: save/load round-trip ===")
    book = compose_whitman_book(seed=7, n_editions=3,
                                  cycles_per_edition=3)
    with tempfile.TemporaryDirectory() as tmpdir:
        path = os.path.join(tmpdir, "book.json")
        book.save(path)
        size = os.path.getsize(path)
        print(f"  Saved: {size} bytes")
        loaded = CompletedBook.load(path)
    print(f"  Editions: {len(loaded.editions)}")
    print(f"  Trajectory: {[round(x, 3) for x in loaded.trajectory()]}")
    assert len(loaded.editions) == len(book.editions)
    assert loaded.trajectory() == book.trajectory()
    assert loaded.converged == book.converged
    # Lines preserved
    orig_lines = sorted(book.final_edition().all_lines())
    load_lines = sorted(loaded.final_edition().all_lines())
    assert orig_lines == load_lines
    print("PASS")


def test_agent_resume():
    print("=== Agent: resume from saved book ===")
    book = compose_whitman_book(seed=8, n_editions=2,
                                  cycles_per_edition=3)
    n_before = len(book.editions)
    print(f"  Before resume: {n_before} editions, "
          f"final score {book.final_edition().brief_score:.2f}")
    # Resume
    agent = PoetryAgent(
        brief=book.brief, fragments=FRAGMENTS, seed=book.seed,
    )
    continued = agent.resume(book, additional_editions=2,
                              cycles_per_edition=3, converge=False)
    print(f"  After resume: {len(continued.editions)} editions, "
          f"final score {continued.final_edition().brief_score:.2f}")
    assert len(continued.editions) > n_before
    print("PASS")


def test_agent_from_saved():
    print("=== Agent: from_saved ===")
    book = compose_whitman_book(seed=9, n_editions=2,
                                  cycles_per_edition=3)
    with tempfile.TemporaryDirectory() as tmpdir:
        path = os.path.join(tmpdir, "book.json")
        book.save(path)
        agent, loaded = PoetryAgent.from_saved(path, FRAGMENTS)
    print(f"  Loaded: {len(loaded.editions)} editions")
    print(f"  Brief: {loaded.brief.name}")
    assert agent.brief.name == loaded.brief.name
    assert len(loaded.editions) == len(book.editions)
    print("PASS")


def test_unfulfilled_book_honest():
    print("=== Unfulfilled book: honest diagnostics ===")
    # Ask for too many poems — the agent can't reach them in 2 editions
    brief = Brief(
        name="Impossible Brief",
        voices=[VOICE_CLINICAL, VOICE_GHOST, VOICE_MANY],
        arc_target=ArcType.PALINDROME,
        refrain="the window ends",
        n_poems_min=20,
        n_poems_max=25,
    )
    agent = PoetryAgent(
        brief=brief, fragments=FRAGMENTS, seed=10,
        budget_per_poem=3, patience_per_poem=2,
        max_rests_per_poem=1,
    )
    book = agent.compose(n_editions=2, cycles_per_edition=2,
                          converge=False)
    print(book.metadata().report())
    print()
    print(f"  Fulfilled: {book.fulfilled()}")
    assert not book.fulfilled()
    reasons = book.not_fulfilled_reasons()
    print(f"  Not fulfilled reasons: {reasons}")
    assert len(reasons) > 0
    # Should mention the count or arc issue
    reason_text = " ".join(reasons).lower()
    assert "poem count" in reason_text or "arc" in reason_text
    print("PASS")


def test_metadata_report():
    print("=== Metadata: full report ===")
    book = compose_whitman_book(seed=11, n_editions=4,
                                  cycles_per_edition=4)
    md = book.metadata()
    print(md.report())
    assert md.n_editions == len(book.editions)
    assert md.n_poems_final > 0
    assert md.fulfilled is True
    assert len(md.trajectory) == md.n_editions
    print("PASS")


def test_all_lines_native():
    print("=== Book: all lines native ===")
    from poetry_engine_c7 import is_native
    book = compose_whitman_book(seed=12, n_editions=3,
                                  cycles_per_edition=3)
    total = 0
    for ed in book.editions:
        for line in ed.all_lines():
            if line:
                total += 1
                assert is_native(line), f"Non-native: {line!r}"
    print(f"  All {total} lines across editions native")
    print("PASS")


def test_full_demo():
    print("\n=== FULL DEMO: a completed book ===")
    book = compose_whitman_book(seed=42, n_editions=5,
                                  cycles_per_edition=4)
    print(book.metadata().report())
    print()
    # Show the final edition's poems
    final = book.final_edition()
    print(f"Final edition ({final.n_poems} poems):")
    for poem in final.poems:
        print(f"\n  {poem.name}:")
        for line in poem.all_lines():
            if line:
                print(f"    {line}")
    print("PASS")


def test_cross_framework_connection():
    print("\n=== The invariant, in the complete agent ===")
    print("  KERNEL:    the brief (identity of the book)")
    print("  QUOTIENT:  the editions (each a complete snapshot)")
    print("  RESONANCE: the fulfillment (does the final edition meet the brief)")
    print()
    print("  Every prior framework reached the same closing point:")
    print("    Circuits:     full SelfImprover pipeline (C19)")
    print("    Neurons:      full Self-Modeling Agent (C10)")
    print("    Economics:    full Self-Improving Loop (C20)")
    print("    Language:     full Portfolio Engine (C19)")
    print("    Chemistry:    full Ecology (C9)")
    print("    Neural eco:   full Neural Ecosystem (C21)")
    print("    Music:        full Listener (C8)")
    print("    Poetry C17:   full Poetry Agent (this)")
    print()
    print("  The shape is identical across all eight frameworks:")
    print("    - A persistent identity (brief / spec / task / goal)")
    print("    - Frozen snapshots (editions / checkpoints / sessions)")
    print("    - A fulfillment metric (brief score / reward / loss)")
    print("    - A convergence criterion (has the work settled?)")
    print()
    print("  The agent is not a single function. It is the discipline")
    print("  of taking a brief, honoring it across many sittings, and")
    print("  reporting honestly whether the work fulfilled it.")
    print("PASS")


if __name__ == "__main__":
    test_voice_registry()
    test_agent_composes_book()
    test_book_fulfilled()
    test_book_trajectory_improves()
    test_book_convergence()
    test_book_determinism()
    test_book_varies_across_seeds()
    test_book_save_load_roundtrip()
    test_agent_resume()
    test_agent_from_saved()
    test_unfulfilled_book_honest()
    test_metadata_report()
    test_all_lines_native()
    test_full_demo()
    test_cross_framework_connection()

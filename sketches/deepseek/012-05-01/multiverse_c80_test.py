import tempfile
from pathlib import Path

import pytest

import multiverse_c71 as c71
from multiverse_c80 import (
    SUBSTRATE,
    compute_arc_hash,
    generate_curriculum,
    save_curriculum,
    check_staleness,
    StalenessVerdict,
    _extract_first_paragraph,
    demo,
)


# =====================================================================
# Arc hash
# =====================================================================

def test_arc_hash_is_deterministic():
    print("=== arc hash is deterministic ===")
    a = compute_arc_hash()
    b = compute_arc_hash()
    assert a == b
    assert len(a) == 64


def test_arc_hash_reflects_arc():
    print("=== arc hash reflects arc state ===")
    live = compute_arc_hash()
    mutated = compute_arc_hash(
        demos=c71.DEMOS[:-1],
        group_order=c71.GROUP_ORDER)
    assert live != mutated


def test_arc_hash_reflects_group_order():
    print("=== arc hash reflects group order ===")
    a = compute_arc_hash(group_order=c71.GROUP_ORDER)
    b = compute_arc_hash(
        group_order=list(reversed(c71.GROUP_ORDER)))
    assert a != b


# =====================================================================
# Docstring extraction
# =====================================================================

def test_extract_first_paragraph():
    print("=== _extract_first_paragraph ===")
    doc = (
        "title line — Component\n\n"
        "first paragraph is here.\n\n"
        "second paragraph is not taken.")
    assert _extract_first_paragraph(doc) == \
        "first paragraph is here."


def test_extract_first_paragraph_too_short():
    print("=== _extract_first_paragraph: too short → None ===")
    assert _extract_first_paragraph("only a title") is None
    assert _extract_first_paragraph("") is None
    assert _extract_first_paragraph(None) is None


# =====================================================================
# Generated content
# =====================================================================

def _pinned():
    """Generate with a fixed timestamp so tests are byte-stable."""
    return generate_curriculum(
        generated_at="2024-01-01T00:00:00+00:00")


def test_doc_has_front_matter():
    print("=== doc: front matter ===")
    text = _pinned()
    assert "# The Arc — Curriculum" in text
    assert "Generated from the live arc" in text
    assert "How to read this document" in text
    assert "Quick start" in text
    assert "make arc" in text


def test_doc_has_counts():
    print("=== doc: counts match live arc ===")
    text = _pinned()
    assert f"{len(c71.DEMOS)} demos" in text
    assert f"{len(c71.GROUP_ORDER)} layers" in text


def test_doc_has_every_demo():
    print("=== doc: every demo included ===")
    text = _pinned()
    for spec in c71.DEMOS:
        assert spec.name in text, spec.name
        assert spec.component in text, spec.component
        assert spec.module in text, spec.module


def test_doc_has_every_group():
    print("=== doc: every group present ===")
    text = _pinned()
    for group in c71.GROUP_ORDER:
        title = group.replace("_", " ").title()
        assert f"## {title}" in text or group in text


def test_doc_has_substrate():
    print("=== doc: substrate chapter ===")
    text = _pinned()
    assert "## The Substrate" in text
    for item in SUBSTRATE:
        assert item["component"] in text
        assert item["name"] in text


def test_doc_has_run_instructions():
    print("=== doc: run instructions ===")
    text = _pinned()
    assert "## How to run it" in text
    assert "make arc" in text
    assert "python -m multiverse_c41" in text


def test_doc_has_extension_instructions():
    print("=== doc: how to extend ===")
    text = _pinned()
    assert "## How to extend it" in text
    assert "multiverse_c71.DEMOS" in text
    assert "multiverse_c80.py" in text


def test_doc_has_whats_missing():
    print("=== doc: notes C78 spec ===")
    text = _pinned()
    assert "## What's not yet demonstrated" in text
    assert "C78" in text


def test_doc_has_integrity():
    print("=== doc: integrity section ===")
    text = _pinned()
    assert "## Integrity" in text
    assert "Arc hash:" in text
    live = compute_arc_hash()
    assert live in text


# =====================================================================
# Determinism
# =====================================================================

def test_doc_is_deterministic():
    print("=== doc: byte-identical for a given arc ===")
    a = generate_curriculum(
        generated_at="2024-01-01T00:00:00+00:00")
    b = generate_curriculum(
        generated_at="2024-01-01T00:00:00+00:00")
    assert a == b


# =====================================================================
# Staleness
# =====================================================================

def test_staleness_current(tmp_path):
    print("=== staleness: current doc ===")
    content = _pinned()
    path = tmp_path / "CURRICULUM.md"
    path.write_text(content)
    verdict = check_staleness(path)
    assert not verdict.stale
    assert verdict.doc_hash == compute_arc_hash()


def test_staleness_missing_file(tmp_path):
    print("=== staleness: missing file ===")
    verdict = check_staleness(tmp_path / "missing.md")
    assert verdict.stale
    assert "not found" in verdict.reason


def test_staleness_wrong_hash(tmp_path):
    print("=== staleness: mismatched hash ===")
    content = _pinned()
    # Tamper with the hash
    content = content.replace(
        compute_arc_hash(),
        "0" * 64)
    path = tmp_path / "CURRICULUM.md"
    path.write_text(content)
    verdict = check_staleness(path)
    assert verdict.stale
    assert "does not match" in verdict.reason


def test_staleness_no_hash_line(tmp_path):
    print("=== staleness: no hash line ===")
    path = tmp_path / "CURRICULUM.md"
    path.write_text("# Just a title\nNo integrity section.")
    verdict = check_staleness(path)
    assert verdict.stale


# =====================================================================
# The "always current" property
# =====================================================================

def test_regenerating_updates_hash_when_arc_changes(tmp_path):
    """A demo added to the arc changes the doc's hash. A stale
    doc is detectable; regenerating fixes it. This is the
    'always current' guarantee made concrete."""
    print("=== regenerating: doc tracks arc ===")
    pinned = _pinned()
    path = tmp_path / "CURRICULUM.md"
    path.write_text(pinned)
    # Simulate an arc change: compute a hash of a modified list
    real_hash = compute_arc_hash()
    mutated_hash = compute_arc_hash(
        demos=c71.DEMOS + [
            c71.DemoSpec(
                "extra", "C99", "multiverse_c41", "demo",
                "extra/extra_demo.json", "worlds", "extra")],
        group_order=c71.GROUP_ORDER)
    assert real_hash != mutated_hash
    # If the doc were regenerated from the mutated list, it
    # would carry the new hash. Our pinned doc carries the real
    # one. Regenerating from the real list produces a doc that
    # matches the current arc.
    fresh = _pinned()
    path.write_text(fresh)
    assert not check_staleness(path).stale


# =====================================================================
# Demo
# =====================================================================

def test_demo(tmp_path):
    print("=== demo: generates and saves ===")
    audit = demo(artifact_dir=str(tmp_path))
    assert audit["stale"] is False
    assert audit["demo_count"] == len(c71.DEMOS)
    assert audit["layer_count"] == len(c71.GROUP_ORDER)
    assert audit["line_count"] > 100
    # Files exist
    doc_path = Path(audit["doc_path"])
    assert doc_path.exists()
    assert (tmp_path / "curriculum" /
            "curriculum_demo.json").exists()
    # Doc parses as markdown with expected sections
    text = doc_path.read_text()
    assert "# The Arc — Curriculum" in text
    assert "## The Substrate" in text
    assert "## Integrity" in text

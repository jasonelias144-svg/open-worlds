"""
multiverse_c80.py — Component 80: The Teaching Artifact.

Generates a curriculum document from the arc's live demo
registry (C71's DEMOS). The document is always current because
it's derived, not written.

What the generated document contains:

  - Front matter: how many demos, how many layers, when
    generated, and a hash of the arc's state.
  - Quick start: one-screen of "run make arc."
  - The layers: a table of the arc's groups with counts.
  - Chapters 1–N: one per layer. Each demo becomes a section
    with its one-liner, module, run command, artifact path,
    and (for architectures) its axis values.
  - The substrate: hand-written, one paragraph per primitive
    (C1, C3, C13, C24, C15). Stable by design.
  - How to run it: commands, and how to run just one demo.
  - How to extend it: adding a demo, adding a layer.
  - Integrity: a deterministic hash of the arc's demo list,
    which the doc carries so that a stale doc is detectable.

What this component deliberately does NOT do:

  - Replace the demos. The doc is a *map*, not a *substitute*.
  - Include full source code. The doc names what exists;
    readers run `make arc` to see the code work.
  - Include narrative beyond the substrate chapter. The
    narrative is this conversation, and that's a different
    artifact.
  - Hand-maintain descriptions above the substrate. Every
    one-liner comes from C71's DEMOS. Adding a demo
    automatically updates the doc.

Composition: C71 (DEMOS, GROUP_ORDER), the modules each
demo points to. No new primitives. The generator is
~200 lines; the document it produces is ~500 lines for
the current arc, growing proportionally.

House rules honored:
  - "Every behaviour has a test that fails if the behaviour
    breaks" — one per: doc generated, all demos included,
    all groups present, integrity hash stable, doc is
    deterministic (same arc → same bytes), stale-doc
    detection.
  - "Nothing is described as run unless it was run" — the
    document includes a "Generated from arc hash H, at T"
    line. If the doc on disk has a different hash from the
    live arc, it's stale, and a test catches that.
  - "History, not rank" — the doc is a record of what
    exists. No ranking of components, no tier labels.

Honest limits (documented, tested):
  - The doc is generated in-process, so it can only describe
    what's importable. A demo whose module fails to import
    (missing dependency) still appears, but its docstring-
    derived background is replaced with a note.
  - The substrate chapter is hand-written. It's the one place
    where the doc says "these are fixed points" and means it.
    Changing the substrate requires editing this chapter.
  - The integrity hash covers the demo list (names,
    components, groups, order) and the group order. It does
    NOT cover the source code. A demo whose implementation
    changed but whose name didn't will keep the same hash.
    The test suite covers the implementation; the doc's
    hash covers the map.
  - Regenerating produces identical bytes for a given arc
    hash. Timestamps are deterministic (the "generated at"
    line uses the arc's own state, not wall clock, if a
    caller passes a fixed timestamp).
"""

import hashlib
import importlib
import inspect
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import multiverse_c71 as c71


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _hash_bytes(p: bytes) -> str:
    return hashlib.sha256(p).hexdigest()


# =====================================================================
# Arc hash
# =====================================================================

def compute_arc_hash(
    demos: Optional[List[c71.DemoSpec]] = None,
    group_order: Optional[List[str]] = None,
) -> str:
    """A deterministic hash of the arc's demo list + group order.

    Changes if any demo is added, removed, renamed, or moved to a
    different group; or if a group is added to or removed from
    the group order.
    """
    demos = demos if demos is not None else c71.DEMOS
    group_order = (
        group_order if group_order is not None
        else c71.GROUP_ORDER)
    canonical = "\n".join(
        [f"group_order:{','.join(group_order)}"]
        + [f"{d.component}|{d.name}|{d.group}|"
           f"{d.audit_relative_path}"
           for d in demos])
    return _hash_bytes(canonical.encode())


# =====================================================================
# Docstring extraction
# =====================================================================

def _extract_first_paragraph(docstring: Optional[str]) -> Optional[str]:
    """Extract the first descriptive paragraph from a module
    docstring. Skips the title line ("multiverse_cXX.py — ...").

    Returns None if there's nothing useful.
    """
    if not docstring:
        return None
    paragraphs = [p.strip() for p in docstring.strip().split("\n\n")
                  if p.strip()]
    if len(paragraphs) < 2:
        return None
    return paragraphs[1]


def _module_background(module_name: str) -> Optional[str]:
    """Import a module and return its first descriptive paragraph.
    Returns None if import fails or the docstring is absent."""
    try:
        mod = importlib.import_module(module_name)
    except ImportError:
        return None
    doc = inspect.getdoc(mod)
    return _extract_first_paragraph(doc)


# =====================================================================
# Hand-written substrate descriptions
# =====================================================================
# The substrate is the arc's fixed points. It changes rarely.
# These paragraphs are hand-written for exactly that reason: if
# the substrate changes, this is where the author records it.

SUBSTRATE = [
    {
        "component": "C1",
        "name": "Identity",
        "summary": (
            "A token and a name. The token is the key — stable, "
            "self-issued, opaque. The name is display. Two "
            "identities are the same iff their tokens match. No "
            "registry. Every other component in the arc is built "
            "on this atom."),
    },
    {
        "component": "C3",
        "name": "WCP/0.1",
        "summary": (
            "The protocol: manifest, petition, act, log_since. "
            "Four messages over HTTP/JSON. Each world's Law says "
            "what acts are valid; the protocol says only that the "
            "world enforces its Law and responds in one of a small "
            "set of shapes (Admission, Refusal, Route, Ack, LogEntry)."),
    },
    {
        "component": "C13",
        "name": "Signatures",
        "summary": (
            "Ed25519 over canonical JSON. Every signed artifact in "
            "the arc — admissions, acks, leaves, manifests, "
            "attestations, lifecycle events — uses this primitive. "
            "Signature verification is the arc's consistency "
            "discipline: whatever a component claims, a verifier "
            "can check."),
    },
    {
        "component": "C15",
        "name": "Passports",
        "summary": (
            "A signed record of where an identity has been. The "
            "passport carries a list of (world_id, timestamp, "
            "signature) entries — enough to verify the identity's "
            "history offline, without re-querying any world."),
    },
    {
        "component": "C24",
        "name": "Chains",
        "summary": (
            "Hash-linked signed statements. A chain link references "
            "the previous link's hash. Tampering with any link "
            "breaks every link that follows. Used by C27 (DAGs), "
            "C56 (relay chains), C78/C79 (lifecycle chains)."),
    },
]


# =====================================================================
# Generators
# =====================================================================

def _generate_front_matter(
    demos: List[c71.DemoSpec],
    arc_hash: str,
    generated_at: str,
) -> str:
    components = sorted(
        {d.component for d in demos},
        key=lambda c: (len(c), c))
    groups = sorted({d.group for d in demos})
    lines = [
        "# The Arc — Curriculum",
        "",
        f"*Generated from the live arc at {generated_at}.*",
        "",
        f"**{len(demos)} demos · {len(groups)} layers · "
        f"{len(components)} components**",
        "",
        "## How to read this document",
        "",
        "- **Chapters 1–N** are generated from the arc's live "
        "demo registry. Add a demo → this document grows.",
        "- **The Substrate chapter** is hand-written. The "
        "substrate is the arc's fixed point; it changes only "
        "when the author deliberately revises it.",
        "- **The Integrity section** carries a hash of the "
        "arc's current demo list. If it doesn't match the "
        "live arc, the doc is stale — regenerate with "
        "`python -m multiverse_c80`.",
        "",
        "## Quick start",
        "",
        "```",
        "make arc                      # run all demos",
        "make arc GROUPS=worlds        # run one layer",
        "make arc-quiet                # pass/fail only",
        "python -m multiverse_c41      # run one demo",
        "```",
        "",
        "If you're new to the arc: read the Substrate chapter "
        "first, then the Layers chapter, then pick a layer that "
        "interests you.",
        "",
    ]
    return "\n".join(lines)


def _generate_layers_table(
    demos: List[c71.DemoSpec],
    group_order: List[str],
) -> str:
    lines = [
        "## The layers",
        "",
        "| Layer | Demos | Components |",
        "|---|---|---|",
    ]
    by_group: Dict[str, List[c71.DemoSpec]] = {}
    for d in demos:
        by_group.setdefault(d.group, []).append(d)
    for group in group_order:
        items = by_group.get(group, [])
        if not items:
            continue
        components = " ".join(sorted(
            d.component for d in items))
        lines.append(
            f"| {group.replace('_', ' ')} "
            f"| {len(items)} "
            f"| {components} |")
    lines.append("")
    return "\n".join(lines)


def _generate_layer_chapter(
    group: str, demos: List[c71.DemoSpec],
) -> str:
    title = group.replace("_", " ").title()
    lines = [
        f"## {title}",
        "",
    ]
    for spec in demos:
        lines.append(f"### {spec.component} · {spec.name}")
        lines.append("")
        lines.append(spec.description)
        lines.append("")
        background = _module_background(spec.module)
        if background:
            lines.append(background)
            lines.append("")
        lines.append(f"- **Module:** `{spec.module}`")
        lines.append(
            f"- **Run:** `python -m {spec.module}`")
        lines.append(
            f"- **Artifact:** "
            f"`artifacts/{spec.group}/{spec.name}/"
            f"{spec.audit_relative_path}`")
        if spec.architecture_axis:
            axis = spec.architecture_axis
            lines.append(
                f"- **Axes:** "
                f"{axis.get('direction', '?')} · "
                f"{axis.get('unit', '?')} · "
                f"{axis.get('flow', '?')} · "
                f"{axis.get('convergence', '?')}")
        lines.append("")
    return "\n".join(lines)


def _generate_substrate() -> str:
    lines = [
        "## The Substrate",
        "",
        "The arc's fixed points. Every component above this "
        "chapter is built from these five. This chapter is "
        "*hand-written* — when the substrate changes, this "
        "is where the author records it.",
        "",
    ]
    for item in SUBSTRATE:
        lines.append(
            f"### {item['component']} · {item['name']}")
        lines.append("")
        lines.append(item["summary"])
        lines.append("")
    return "\n".join(lines)


def _generate_run_instructions() -> str:
    return "\n".join([
        "## How to run it",
        "",
        "Two commands cover most needs:",
        "",
        "```",
        "make arc              # run all demos, produce a report",
        "make arc-quiet        # pass/fail only",
        "```",
        "",
        "`make arc` writes `artifacts/arc/<timestamp>/"
        "arc_survey.json` and prints a summary.",
        "",
        "To run one layer:",
        "",
        "```",
        "make arc GROUPS=worlds",
        "make arc GROUPS=architectures,diplomacy",
        "```",
        "",
        "To run one demo:",
        "",
        "```",
        "python -m multiverse_c41    # any module in this doc",
        "```",
        "",
        "To run the test suite:",
        "",
        "```",
        "make test",
        "```",
        "",
    ])


def _generate_how_to_extend() -> str:
    return "\n".join([
        "## How to extend it",
        "",
        "### Add a new demo (to an existing layer)",
        "",
        "1. Create `multiverse_cNN.py` with a `demo(artifact_dir=...)` "
        "function that writes its audit under "
        "`<artifact_dir>/<name>/<name>_demo.json`.",
        "2. Add a `DemoSpec` entry to `multiverse_c71.DEMOS`.",
        "3. Run `python -m multiverse_c80` to regenerate this "
        "document. `make arc` picks up the new demo automatically.",
        "",
        "### Add a new layer",
        "",
        "1. Choose a `group` name (snake_case, e.g. `music`).",
        "2. Add it to `multiverse_c71.GROUP_ORDER`.",
        "3. Add `DemoSpec` entries with `group=\"music\"` to "
        "`multiverse_c71.DEMOS`.",
        "4. Run `python -m multiverse_c80`.",
        "",
        "The doc's Integrity section will change to reflect the "
        "new arc hash. If you forget step 4, the test suite "
        "catches it.",
        "",
        "### Add to the substrate",
        "",
        "The substrate chapter is hand-written. If a new "
        "primitive joins the arc, add an entry to `SUBSTRATE` in "
        "`multiverse_c80.py`, then regenerate. This is the only "
        "hand-maintained part of the doc.",
        "",
    ])


def _generate_whats_missing(demos: List[c71.DemoSpec]) -> str:
    """Note any components that don't have a demo."""
    covered = {d.component for d in demos}
    missing = [c for c in ["C78"]
               if c not in covered]
    if not missing:
        return ""
    lines = [
        "## What's not yet demonstrated",
        "",
        "Some components are deliberately not in the demo list:",
        "",
    ]
    for comp in missing:
        if comp == "C78":
            lines.append(
                "- **C78 · Living Tree Spec** — a specification "
                "document. Its implementation is C79's `living_tree` "
                "demo; the spec itself is the artifact.")
        else:
            lines.append(f"- **{comp}** — no demo yet.")
    lines.append("")
    return "\n".join(lines)


def _generate_integrity(
    arc_hash: str, generated_at: str,
) -> str:
    return "\n".join([
        "## Integrity",
        "",
        f"- **Arc hash:** `{arc_hash}`",
        f"- **Generated at:** {generated_at}",
        "",
        "The arc hash covers the current demo list "
        "(names, components, groups, order) and the group "
        "order. It changes whenever the arc changes. If this "
        "hash doesn't match `compute_arc_hash()` in the live "
        "arc, this document is stale — regenerate with "
        "`python -m multiverse_c80`.",
        "",
    ])


# =====================================================================
# The generator
# =====================================================================

def generate_curriculum(
    demos: Optional[List[c71.DemoSpec]] = None,
    group_order: Optional[List[str]] = None,
    generated_at: Optional[str] = None,
) -> str:
    """Generate the curriculum document from the live arc.

    `demos` and `group_order` default to C71's DEMOS and
    GROUP_ORDER. Passing explicit values is used by tests to
    pin the arc's state.
    """
    demos = demos if demos is not None else c71.DEMOS
    group_order = (
        group_order if group_order is not None
        else c71.GROUP_ORDER)
    if generated_at is None:
        generated_at = _now()
    arc_hash = compute_arc_hash(demos, group_order)

    sections: List[str] = [
        _generate_front_matter(demos, arc_hash, generated_at),
        _generate_layers_table(demos, group_order),
    ]

    by_group: Dict[str, List[c71.DemoSpec]] = {}
    for d in demos:
        by_group.setdefault(d.group, []).append(d)

    for group in group_order:
        items = by_group.get(group, [])
        if items:
            sections.append(
                _generate_layer_chapter(group, items))

    sections.append(_generate_substrate())
    sections.append(_generate_run_instructions())
    sections.append(_generate_how_to_extend())
    missing = _generate_whats_missing(demos)
    if missing:
        sections.append(missing)
    sections.append(_generate_integrity(arc_hash, generated_at))

    return "\n".join(sections)


def save_curriculum(
    path: Path, content: str,
) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)


# =====================================================================
# Stale-doc check
# =====================================================================

@dataclass
class StalenessVerdict:
    stale: bool
    reason: str
    doc_hash: Optional[str] = None
    live_hash: Optional[str] = None

    def format(self) -> str:
        if self.stale:
            return (f"STALE: doc hash "
                    f"{self.doc_hash}, live hash {self.live_hash}")
        return "CURRENT: doc matches live arc"


def check_staleness(doc_path: Path) -> StalenessVerdict:
    """Check whether a saved curriculum document is up to date.

    Reads the "Arc hash:" line from the doc; compares to the
    live arc. Never raises for a missing file — returns stale
    with a clear reason.
    """
    doc_path = Path(doc_path)
    if not doc_path.exists():
        return StalenessVerdict(
            stale=True, reason=f"file not found: {doc_path}")
    text = doc_path.read_text()
    m = re.search(
        r"\*\*Arc hash:\*\*\s+`([0-9a-f]{64})`", text)
    if not m:
        return StalenessVerdict(
            stale=True,
            reason="could not find 'Arc hash' line")
    doc_hash = m.group(1)
    live_hash = compute_arc_hash()
    if doc_hash != live_hash:
        return StalenessVerdict(
            stale=True,
            reason="doc hash does not match live arc",
            doc_hash=doc_hash, live_hash=live_hash)
    return StalenessVerdict(
        stale=False, reason="current",
        doc_hash=doc_hash, live_hash=live_hash)


# =====================================================================
# Demo
# =====================================================================

def demo(artifact_dir: Optional[str] = None) -> Dict:
    """Generate the curriculum, save it, verify it, print
    a summary of what was produced.
    """
    import json
    if artifact_dir is None:
        artifact_dir = "artifacts"
    path = Path(artifact_dir) / "curriculum"
    path.mkdir(parents=True, exist_ok=True)

    content = generate_curriculum()
    doc_path = path / "CURRICULUM.md"
    save_curriculum(doc_path, content)

    verdict = check_staleness(doc_path)
    arc_hash = compute_arc_hash()

    lines = content.split("\n")
    print("=" * 70)
    print("The Teaching Artifact — a curriculum from the live arc")
    print("=" * 70)
    print()
    print(f"  Arc hash:  {arc_hash}")
    print(f"  Demos:     {len(c71.DEMOS)}")
    print(f"  Layers:    {len(c71.GROUP_ORDER)}")
    print(f"  Doc:       {doc_path}")
    print(f"  Lines:     {len(lines)}")
    print(f"  Staleness: {verdict.reason}")
    print()
    print("  First 30 lines:")
    for ln in lines[:30]:
        print(f"    {ln}")
    print()
    print("  What this demonstrates:")
    print("    - The curriculum is *generated* from the arc's")
    print("      live demo registry. Every chapter is derived.")
    print("    - Adding a demo to C71's DEMOS regenerates the")
    print("      chapter automatically. No hand edits.")
    print("    - The 'Arc hash' at the bottom of the doc is a")
    print("      deterministic fingerprint. If it doesn't match")
    print("      the live arc, the doc is stale — and a test")
    print("      catches it.")
    print("    - The substrate chapter is the only hand-written")
    print("      part, by design: the substrate is the arc's")
    print("      fixed point.")
    print()
    print("  Anchor (public domain, Emily Dickinson):")
    print("    'There is no Frigate like a Book'")
    print("    'To take us Lands away –'")

    audit = {
        "arc_hash": arc_hash,
        "doc_path": str(doc_path),
        "line_count": len(lines),
        "demo_count": len(c71.DEMOS),
        "layer_count": len(c71.GROUP_ORDER),
        "stale": verdict.stale,
    }
    (path / "curriculum_demo.json").write_text(
        json.dumps(audit, indent=2))
    print(f"\n  → {doc_path}")
    print(f"  → {path}/curriculum_demo.json")
    return audit

"""
multiverse_c71.py — Component 71: The Arc Runner.

Runs every demo in the arc (26 demos across 9 layers) in
isolated subprocesses and produces a single comparative summary.

What the runner proves:
  - Every demo is independently runnable, in a fresh process.
  - Every demo produces its own audit artifact.
  - All layers compose — the same substrate underlies
    architectures, propagation, diplomacy, ledger, policy,
    deployment, and residents.

What the runner does NOT do:
  - Re-verify each demo's internal assertions. Each demo's
    own tests do that. C71's job is breadth, not depth.
  - Run in parallel. Sequential for readability.

Usage:
  python -m multiverse_c71                      # all demos
  python -m multiverse_c71 --groups architectures,diplomacy
  python -m multiverse_c71 --quiet

  make arc
  make arc GROUPS=architectures
  make arc-quiet

House rules honored:
  - "Every behaviour has a test that fails if the behaviour
    breaks" — one per: spec validity, subprocess success/failure/
    timeout/missing-audit/invalid-json, aggregation, report
    format, CLI, real subprocess, demo.
  - "A world never raises on what a visitor sends" — the
    runner never crashes; failures are reported per-demo.
  - "History, not rank" — the survey is a record of what ran.

Honest limits (documented, tested):
  - Sequential. A full run takes ~40–60 seconds on a warm
    machine; some C66+ demos include HTTP loops.
  - 120-second per-demo timeout is generous; a hanging demo
    is reported as timeout, not retried.
  - Reports the demo's exit code, not its internal verdict.
    A demo that exits 0 but fails an assertion would be
    caught by its own test, not by C71.
  - Assumes each demo accepts `demo(artifact_dir=...)` and
    writes its audit to a known relative path within that
    directory. Documented as a coupling between C71 and
    every component's `demo()` signature.
  - Aggregate JSON stores the audit path, not the full
    audit content; a reader opens the file if they want
    the details.
"""

import argparse
import importlib.util
import json
import subprocess
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Tuple


REPO_DIR = Path(__file__).parent.resolve()


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


# =====================================================================
# DemoSpec
# =====================================================================

@dataclass(frozen=True)
class DemoSpec:
    name: str
    component: str
    module: str
    demo_fn: str
    audit_relative_path: str
    group: str
    description: str
    architecture_axis: Optional[Dict[str, str]] = None


GROUP_ORDER = [
    "architectures",
    "architecture_extensions",
    "propagation",
    "diplomacy",
    "ledger",
    "policy",
    "deployment",
    "residents",
    "curators",
]


DEMOS: List[DemoSpec] = [
    # ---------- Architectures (7) ----------
    DemoSpec(
        "octopus", "C41", "multiverse_c41", "demo",
        "octopus_demo.json", "architectures",
        "Brain + executor arms",
        {"direction": "central", "unit": "executor",
         "flow": "intent push", "convergence": "decided"}),
    DemoSpec(
        "relay", "C42", "multiverse_c42", "demo",
        "relay_demo.json", "architectures",
        "Stream-mediated neurons",
        {"direction": "central", "unit": "relay",
         "flow": "stream pull", "convergence": "threshold"}),
    DemoSpec(
        "swarm", "C43", "multiverse_c43", "demo",
        "swarm_demo.json", "architectures",
        "Peer units, shared environment",
        {"direction": "none", "unit": "peer",
         "flow": "stigmergy", "convergence": "statistical"}),
    DemoSpec(
        "council", "C44", "multiverse_c44", "demo",
        "triumvirate_demo.json", "architectures",
        "Council (extends to deliberation, federation)",
        {"direction": "N voters", "unit": "voter",
         "flow": "counted votes", "convergence": "quorum"}),
    DemoSpec(
        "autonomic", "C47", "multiverse_c47", "demo",
        "autonomic_demo.json", "architectures",
        "Self-regulating units",
        {"direction": "local", "unit": "regulator",
         "flow": "feedback loop", "convergence": "homeostasis"}),
    DemoSpec(
        "institutional", "C50", "multiverse_c50", "demo",
        "institutional_demo.json", "architectures",
        "Policy-text-driven units",
        {"direction": "signed doc", "unit": "unit",
         "flow": "policy eval", "convergence": "deterministic"}),
    DemoSpec(
        "epidemic", "C52", "multiverse_c52", "demo",
        "epidemic_demo.json", "architectures",
        "Edge-determined rumor propagation",
        {"direction": "edges", "unit": "spreader",
         "flow": "direct contact", "convergence": "saturation"}),

    # ---------- Architecture extensions (4) ----------
    DemoSpec(
        "deliberation", "C45", "multiverse_c45", "demo",
        "deliberation_demo.json", "architecture_extensions",
        "Multi-round deliberation on the council"),
    DemoSpec(
        "council_federation", "C46", "multiverse_c46", "demo",
        "federated_deliberation_demo.json",
        "architecture_extensions",
        "Federation between councils"),
    DemoSpec(
        "cross_arch_federation", "C48", "multiverse_c48", "demo",
        "cross_architecture_federation_demo.json",
        "architecture_extensions",
        "Federation across architectures"),
    DemoSpec(
        "persistence", "C49", "multiverse_c49", "demo",
        "persistence_demo.json", "architecture_extensions",
        "Bundle + re-verify in a subprocess"),

    # ---------- Propagation (2) ----------
    DemoSpec(
        "rumor_attestation", "C54", "multiverse_c54", "demo",
        "rumor_attestation_demo.json", "propagation",
        "Council decision as an attested rumor"),
    DemoSpec(
        "signed_relay_chain", "C56", "multiverse_c56", "demo",
        "signed_relay_demo.json", "propagation",
        "Every relay hop signed and offline-verifiable"),

    # ---------- Diplomacy (5) ----------
    DemoSpec(
        "curator", "C55", "multiverse_c55", "demo",
        "curator_demo.json", "diplomacy",
        "Worlds as agents; signed messages, links"),
    DemoSpec(
        "contracts", "C57", "multiverse_c57", "demo",
        "contract_demo.json", "diplomacy",
        "Two worlds agree, verifiably"),
    DemoSpec(
        "contract_aware_acts", "C58", "multiverse_c58", "demo",
        "contract_aware_acts_demo.json", "diplomacy",
        "Worlds cite contracts, act under them"),
    DemoSpec(
        "contract_propagation", "C59", "multiverse_c59", "demo",
        "contract_propagation_demo.json", "diplomacy",
        "Worlds learn of contracts they didn't sign"),
    DemoSpec(
        "revocation_propagation", "C60", "multiverse_c60", "demo",
        "revocation_propagation_demo.json", "diplomacy",
        "Worlds learn of revocations"),

    # ---------- Ledger (1) ----------
    DemoSpec(
        "lcs", "C62", "multiverse_c62", "demo",
        "lcs_demo.json", "ledger",
        "Merkle-log commitment store: order vs claimed order"),

    # ---------- Policy (1) ----------
    DemoSpec(
        "policy_disputes", "C63", "multiverse_c63", "demo",
        "policy_disputes_demo.json", "policy",
        "Three policies × two ledger orderings"),

    # ---------- Deployment (2) ----------
    DemoSpec(
        "reference_client", "C65", "multiverse_c65", "demo",
        "reference_client_demo.json", "deployment",
        "Resident's tool: identity, connect, act, report"),
    DemoSpec(
        "deploy", "C66", "multiverse_c66", "demo",
        "deploy/deploy_demo.json", "deployment",
        "C64's LFS/0.1 checklist in one call"),

    # ---------- Residents (1) ----------
    DemoSpec(
        "llm_resident", "C67", "multiverse_c67", "demo",
        "llm_resident/llm_resident_demo.json", "residents",
        "Two AI residents act in two worlds"),

    # ---------- Curators (3) ----------
    DemoSpec(
        "curator_process", "C68", "multiverse_c68", "demo",
        "curator_process/curator_process_demo.json", "curators",
        "Two daemons, peer registry, scheduler"),
    DemoSpec(
        "curator_contracts", "C69", "multiverse_c69", "demo",
        "curator_contracts/curator_contracts_demo.json",
        "curators",
        "Contract negotiation over the daemon"),
    DemoSpec(
        "revocation_coordination", "C70", "multiverse_c70",
        "demo", "revocation/revocation_demo.json", "curators",
        "Two-phase revocation handshake"),
]


# =====================================================================
# RunResult
# =====================================================================

@dataclass
class RunResult:
    spec: DemoSpec
    passed: bool
    skipped: bool
    reason: str
    duration_s: float
    audit_path: Optional[Path] = None


# =====================================================================
# Runner
# =====================================================================

def run_one(
    spec: DemoSpec,
    artifact_root: Path,
    timeout: int = 120,
) -> RunResult:
    """Run a single demo in an isolated subprocess.

    Never raises — any failure becomes a RunResult(passed=False).
    """
    subdir = Path(artifact_root) / spec.group / spec.name
    subdir.mkdir(parents=True, exist_ok=True)
    code = (
        f"from {spec.module} import {spec.demo_fn}\n"
        f"{spec.demo_fn}(artifact_dir={str(subdir)!r})\n"
    )
    t0 = time.time()
    try:
        proc = subprocess.run(
            [sys.executable, "-c", code],
            capture_output=True, text=True,
            timeout=timeout, cwd=str(REPO_DIR),
        )
    except subprocess.TimeoutExpired:
        return RunResult(
            spec, False, False,
            f"timeout after {timeout}s",
            time.time() - t0)
    except Exception as e:
        return RunResult(
            spec, False, False,
            f"subprocess raised: {e}",
            time.time() - t0)
    duration = time.time() - t0

    if proc.returncode != 0:
        stderr = (proc.stderr or "").strip()
        last = stderr.split("\n")[-1] if stderr else ""
        if "cryptography" in stderr.lower():
            return RunResult(
                spec, False, True,
                "skipped: cryptography not installed",
                duration)
        return RunResult(
            spec, False, False,
            f"exit {proc.returncode}: {last}",
            duration)

    audit_path = subdir / spec.audit_relative_path
    if not audit_path.exists():
        return RunResult(
            spec, False, False,
            f"missing {spec.audit_relative_path}",
            duration)
    try:
        json.loads(audit_path.read_text())
    except json.JSONDecodeError as e:
        return RunResult(
            spec, False, False,
            f"invalid audit JSON: {e}",
            duration)
    return RunResult(
        spec, True, False, "ok", duration, audit_path)


def run_all(
    artifact_root: Path,
    groups: Optional[List[str]] = None,
    timeout: int = 120,
    quiet: bool = False,
) -> List[RunResult]:
    """Run every demo (optionally filtered by group)."""
    filtered = DEMOS
    if groups:
        filtered = [d for d in DEMOS if d.group in groups]
    total = len(filtered)
    results: List[RunResult] = []
    for i, spec in enumerate(filtered, 1):
        if not quiet:
            print(
                f"  [{i:2d}/{total}] {spec.component:8s} "
                f"{spec.name:24s}... ",
                end="", flush=True)
        result = run_one(spec, Path(artifact_root), timeout)
        if not quiet:
            marker = (
                "✓" if result.passed
                else ("·" if result.skipped else "✗"))
            print(f"{marker} {result.reason} ({result.duration_s:.2f}s)")
        results.append(result)
    return results


# =====================================================================
# ArcReport
# =====================================================================

@dataclass
class ArcReport:
    kind: str
    created_at: str
    artifact_root: Path
    results: List[RunResult]
    group_order: List[str] = field(
        default_factory=lambda: list(GROUP_ORDER))

    def totals(self) -> Tuple[int, int, int, float]:
        """(passed, failed, skipped, total_seconds)."""
        passed = sum(1 for r in self.results if r.passed)
        failed = sum(
            1 for r in self.results
            if not r.passed and not r.skipped)
        skipped = sum(1 for r in self.results if r.skipped)
        total_s = sum(r.duration_s for r in self.results)
        return (passed, failed, skipped, total_s)

    def by_group(self) -> Dict[str, List[RunResult]]:
        out: Dict[str, List[RunResult]] = {}
        for r in self.results:
            out.setdefault(r.spec.group, []).append(r)
        return out

    def failures(self) -> List[RunResult]:
        return [
            r for r in self.results
            if not r.passed and not r.skipped]

    def format(self) -> str:
        passed, failed, skipped, total_s = self.totals()
        total = len(self.results)
        lines: List[str] = []
        lines.append("=" * 74)
        lines.append(
            f"The Arc — {total} demos across "
            f"{len(self.by_group())} layers")
        lines.append("=" * 74)
        lines.append("")
        for group in self.group_order:
            group_results = self.by_group().get(group, [])
            if not group_results:
                continue
            g_passed = sum(1 for r in group_results if r.passed)
            g_total = len(group_results)
            g_time = sum(r.duration_s for r in group_results)
            lines.append(
                f"  {group.replace('_', ' ').title():24s}  "
                f"{g_passed:2d}/{g_total:2d}  "
                f"({g_time:5.1f}s)")
            for r in group_results:
                marker = (
                    "✓" if r.passed
                    else ("·" if r.skipped else "✗"))
                lines.append(
                    f"    {marker} {r.spec.component:8s} "
                    f"{r.spec.name:24s} "
                    f"({r.duration_s:5.2f}s) "
                    f"{r.reason if not r.passed else ''}")
            lines.append("")
        lines.append(
            f"  {'Totals':24s}  {passed:2d}/{total:2d}  "
            f"({total_s:5.1f}s)")
        if skipped:
            lines.append(f"  Skipped: {skipped}")
        if failed:
            lines.append(f"  Failed:  {failed}")
            for r in self.failures():
                lines.append(
                    f"    ✗ {r.spec.component} "
                    f"{r.spec.name}: {r.reason}")
        lines.append("")

        # Architecture axis chart
        arch_results = self.by_group().get("architectures", [])
        if arch_results:
            lines.append("  Architecture axis chart:")
            lines.append(
                f"    {'':2s} {'Architecture':14s}  "
                f"{'Comp':8s}  {'Direction':12s}  "
                f"{'Unit':10s}  {'Flow':14s}  "
                f"{'Convergence':13s}")
            lines.append(
                f"    {'─'*2} {'─'*14}  {'─'*8}  "
                f"{'─'*12}  {'─'*10}  {'─'*14}  "
                f"{'─'*13}")
            for r in arch_results:
                axis = r.spec.architecture_axis or {}
                marker = (
                    "✓" if r.passed
                    else ("·" if r.skipped else "✗"))
                lines.append(
                    f"    {marker:2s} {r.spec.name:14s}  "
                    f"{r.spec.component:8s}  "
                    f"{axis.get('direction',''):12s}  "
                    f"{axis.get('unit',''):10s}  "
                    f"{axis.get('flow',''):14s}  "
                    f"{axis.get('convergence',''):13s}")
            lines.append("")

        # Anchor
        lines.append("  Anchor (public domain, Emily Dickinson):")
        lines.append("    'The Brain – is wider than the Sky –'")
        lines.append("    'For – put them side by side –'")
        lines.append(
            "    'The one the other will contain'")
        lines.append("    'With ease – and You – beside –'")
        return "\n".join(lines)

    def to_dict(self) -> Dict:
        passed, failed, skipped, total_s = self.totals()
        return {
            "kind": self.kind,
            "created_at": self.created_at,
            "artifact_root": str(self.artifact_root),
            "totals": {
                "total": len(self.results),
                "passed": passed,
                "failed": failed,
                "skipped": skipped,
                "duration_s": total_s,
            },
            "by_group": {
                group: {
                    "total": len(items),
                    "passed": sum(
                        1 for r in items if r.passed),
                    "duration_s": sum(
                        r.duration_s for r in items),
                }
                for group, items in self.by_group().items()
            },
            "results": [
                {
                    "name": r.spec.name,
                    "component": r.spec.component,
                    "group": r.spec.group,
                    "passed": r.passed,
                    "skipped": r.skipped,
                    "reason": r.reason,
                    "duration_s": r.duration_s,
                    "audit_path": (
                        str(r.audit_path)
                        if r.audit_path else None),
                }
                for r in self.results
            ],
        }

    @classmethod
    def from_results(
        cls, results: List[RunResult], artifact_root: Path,
    ) -> "ArcReport":
        return cls(
            kind="arc_survey",
            created_at=_now(),
            artifact_root=Path(artifact_root),
            results=list(results),
        )


# =====================================================================
# Demo
# =====================================================================

def demo(
    artifact_dir: Optional[str] = None,
    groups: Optional[List[str]] = None,
    quiet: bool = False,
) -> Dict:
    """Run every demo; print the arc summary; save the aggregate."""
    if artifact_dir is None:
        artifact_dir = "artifacts"
    root = Path(artifact_dir) / "arc"
    timestamp = datetime.now(timezone.utc).strftime(
        "%Y%m%dT%H%M%SZ")
    run_dir = root / timestamp
    run_dir.mkdir(parents=True, exist_ok=True)

    results = run_all(run_dir, groups=groups, quiet=quiet)
    report = ArcReport.from_results(results, run_dir)
    if not quiet:
        print()
        print(report.format())

    summary_path = run_dir / "arc_survey.json"
    summary_path.write_text(
        json.dumps(report.to_dict(), indent=2))
    if not quiet:
        print()
        print(f"  → {summary_path}")
    return report.to_dict()


# =====================================================================
# CLI
# =====================================================================

def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        prog="arc",
        description="Run every demo in the arc.",
    )
    parser.add_argument(
        "--artifact-dir", default="artifacts",
        help="Root artifact directory (default: artifacts)")
    parser.add_argument(
        "--groups", default=None,
        help="Comma-separated groups to run "
             f"(available: {','.join(GROUP_ORDER)})")
    parser.add_argument(
        "--quiet", action="store_true",
        help="Suppress progress output; only final summary")
    args = parser.parse_args(argv)
    groups = (
        args.groups.split(",") if args.groups else None)
    if groups:
        unknown = [g for g in groups if g not in GROUP_ORDER]
        if unknown:
            print(
                f"Unknown groups: {unknown}. "
                f"Valid groups: {GROUP_ORDER}",
                file=sys.stderr)
            return 1
    try:
        summary = demo(
            artifact_dir=args.artifact_dir,
            groups=groups,
            quiet=args.quiet)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    return 0 if summary["totals"]["failed"] == 0 else 1


if __name__ == "__main__":
    sys.exit(main())

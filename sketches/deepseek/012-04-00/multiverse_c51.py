"""
multiverse_c51.py — Component 51: The Architecture Demonstration Runner.

Runs all six architecture demos plus the four extension demos in
isolated subprocesses, then prints a comparative summary.

The six primary architectures:
  C41 octopus       — central / executor / intent push / decided
  C42 relay         — central / relay / stream pull / threshold
  C43 swarm         — none / peer / stigmergy / statistical
  C44-46 council    — N voters / voter / counted votes / quorum
  C47 autonomic     — local / regulator / feedback / homeostasis
  C50 institutional — signed doc / unit / policy eval / deterministic

The four extensions (build on the above):
  C45 deliberation            — multi-round council process
  C46 council_federation      — federation between councils
  C48 cross_arch_federation   — federation across architectures
  C49 persistence             — bundle + re-verify in subprocess

What the runner proves:
  - Each demo is independently runnable, in a fresh process.
  - Each produces its own audit artifact.
  - All six primary architectures demonstrate their distinguishing
    shape on the same substrate.

What it does NOT do:
  - Re-verify every assertion inside each demo. Each demo's own
    tests do that.
  - Run federation or persistence across architectures. C48 and
    C49 are extensions, run as such.

House rules honored:
  - "Every behaviour has a test that fails if the behaviour
    breaks" — one per behavior: spec validation, subprocess
    success, subprocess failure, timeout, missing audit file,
    comparison output, aggregate JSON, real subprocess for C41.
  - "A world never raises on what a visitor sends" — the
    runner never crashes on a failed demo; it reports and
    continues.
  - "History, not rank" — the survey is a record of what ran,
    not a ranking of architectures.

Honest limits (documented, tested):
  - Timeout is generous (120s) but not unlimited. A demo that
    hangs beyond it is reported as a failure.
  - The comparison table is static: the axis values are
    declarative metadata in the spec, not extracted from each
    demo's runtime behavior. If a demo's axis value changed,
    the spec would need updating. This is a documentation
    choice, not a bug — the axis values are stable properties
    of the architectures, not per-run facts.
  - Some demos may be slow on a loaded machine (C49 runs
    subprocesses internally). 120s covers this.
"""

import json
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional


REPO_DIR = Path(__file__).parent.resolve()


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


# =====================================================================
# Architecture specs
# =====================================================================

@dataclass(frozen=True)
class ArchitectureSpec:
    """Metadata for one architecture demo."""
    name: str
    component: str
    module: str
    demo_fn: str
    audit_filename: str
    direction: str
    unit: str
    flow: str
    convergence: str
    description: str


ARCHITECTURES: List[ArchitectureSpec] = [
    ArchitectureSpec(
        name="octopus",
        component="C41",
        module="multiverse_c41",
        demo_fn="demo",
        audit_filename="octopus_demo.json",
        direction="central",
        unit="executor",
        flow="intent push",
        convergence="decided",
        description="Brain + executor arms",
    ),
    ArchitectureSpec(
        name="relay",
        component="C42",
        module="multiverse_c42",
        demo_fn="demo",
        audit_filename="relay_demo.json",
        direction="central",
        unit="relay",
        flow="stream pull",
        convergence="threshold",
        description="Stream-mediated neurons",
    ),
    ArchitectureSpec(
        name="swarm",
        component="C43",
        module="multiverse_c43",
        demo_fn="demo",
        audit_filename="swarm_demo.json",
        direction="none",
        unit="peer",
        flow="stigmergy",
        convergence="statistical",
        description="Peer units, shared environment",
    ),
    ArchitectureSpec(
        name="council",
        component="C44-46",
        module="multiverse_c44",
        demo_fn="demo",
        audit_filename="triumvirate_demo.json",
        direction="N voters",
        unit="voter",
        flow="counted votes",
        convergence="quorum",
        description="Council (extends to deliberation, federation)",
    ),
    ArchitectureSpec(
        name="autonomic",
        component="C47",
        module="multiverse_c47",
        demo_fn="demo",
        audit_filename="autonomic_demo.json",
        direction="local",
        unit="regulator",
        flow="feedback loop",
        convergence="homeostasis",
        description="Self-regulating units",
    ),
    ArchitectureSpec(
        name="institutional",
        component="C50",
        module="multiverse_c50",
        demo_fn="demo",
        audit_filename="institutional_demo.json",
        direction="signed doc",
        unit="unit",
        flow="policy eval",
        convergence="deterministic",
        description="Policy-text-driven units",
    ),
]


EXTENSIONS: List[ArchitectureSpec] = [
    ArchitectureSpec(
        name="deliberation",
        component="C45",
        module="multiverse_c45",
        demo_fn="demo",
        audit_filename="deliberation_demo.json",
        direction="",
        unit="",
        flow="",
        convergence="",
        description="Multi-round deliberation on the council",
    ),
    ArchitectureSpec(
        name="council_federation",
        component="C46",
        module="multiverse_c46",
        demo_fn="demo",
        audit_filename="federated_deliberation_demo.json",
        direction="",
        unit="",
        flow="",
        convergence="",
        description="Federation between councils",
    ),
    ArchitectureSpec(
        name="cross_arch_federation",
        component="C48",
        module="multiverse_c48",
        demo_fn="demo",
        audit_filename="cross_architecture_federation_demo.json",
        direction="",
        unit="",
        flow="",
        convergence="",
        description="Federation across architectures",
    ),
    ArchitectureSpec(
        name="persistence",
        component="C49",
        module="multiverse_c49",
        demo_fn="demo",
        audit_filename="persistence_demo.json",
        direction="",
        unit="",
        flow="",
        convergence="",
        description="Bundle + re-verify in a subprocess",
    ),
]


# =====================================================================
# Run result
# =====================================================================

@dataclass
class RunResult:
    spec: ArchitectureSpec
    passed: bool
    skipped: bool
    reason: str
    audit_path: Optional[Path] = None
    audit_data: Optional[Dict] = None


# =====================================================================
# ArchitectureRunner
# =====================================================================

class ArchitectureRunner:
    """Runs each architecture demo in isolation; collects results."""

    def __init__(self, artifact_dir: Path, timeout: int = 120):
        self.artifact_dir = Path(artifact_dir)
        self.timeout = timeout
        self.primary: List[RunResult] = []
        self.extensions: List[RunResult] = []
        self.created_at = _now()

    def _run_one(self, spec: ArchitectureSpec) -> RunResult:
        subdir = self.artifact_dir / spec.name
        subdir.mkdir(parents=True, exist_ok=True)
        code = (
            f"from {spec.module} import {spec.demo_fn}\n"
            f"{spec.demo_fn}(artifact_dir={str(subdir)!r})\n"
        )
        try:
            proc = subprocess.run(
                [sys.executable, "-c", code],
                capture_output=True, text=True,
                timeout=self.timeout, cwd=str(REPO_DIR),
            )
        except subprocess.TimeoutExpired:
            return RunResult(
                spec=spec, passed=False, skipped=False,
                reason=f"timeout after {self.timeout}s")
        except Exception as e:
            return RunResult(
                spec=spec, passed=False, skipped=False,
                reason=f"subprocess raised: {e}")

        if proc.returncode != 0:
            stderr = (proc.stderr or "").strip()
            last = stderr.split("\n")[-1] if stderr else ""
            if "cryptography" in stderr.lower():
                return RunResult(
                    spec=spec, passed=False, skipped=True,
                    reason="skipped: cryptography not installed")
            return RunResult(
                spec=spec, passed=False, skipped=False,
                reason=f"exit {proc.returncode}: {last}")

        audit_path = subdir / spec.audit_filename
        if not audit_path.exists():
            return RunResult(
                spec=spec, passed=False, skipped=False,
                reason=f"missing audit file {spec.audit_filename}")
        try:
            audit = json.loads(audit_path.read_text())
        except json.JSONDecodeError as e:
            return RunResult(
                spec=spec, passed=False, skipped=False,
                reason=f"invalid audit JSON: {e}")
        return RunResult(
            spec=spec, passed=True, skipped=False,
            reason="ok", audit_path=audit_path,
            audit_data=audit)

    def run_all(self) -> None:
        """Run every primary and extension demo, in order."""
        for spec in ARCHITECTURES:
            self.primary.append(self._run_one(spec))
        for spec in EXTENSIONS:
            self.extensions.append(self._run_one(spec))

    def summary(self) -> Dict:
        primary_passed = sum(
            1 for r in self.primary if r.passed)
        ext_passed = sum(
            1 for r in self.extensions if r.passed)
        return {
            "kind": "architecture_survey",
            "created_at": self.created_at,
            "artifact_dir": str(self.artifact_dir),
            "primary_architectures": [
                {
                    "name": r.spec.name,
                    "component": r.spec.component,
                    "direction": r.spec.direction,
                    "unit": r.spec.unit,
                    "flow": r.spec.flow,
                    "convergence": r.spec.convergence,
                    "passed": r.passed,
                    "skipped": r.skipped,
                    "reason": r.reason,
                }
                for r in self.primary
            ],
            "extensions": [
                {
                    "name": r.spec.name,
                    "component": r.spec.component,
                    "description": r.spec.description,
                    "passed": r.passed,
                    "skipped": r.skipped,
                    "reason": r.reason,
                }
                for r in self.extensions
            ],
            "primary_passed": primary_passed,
            "primary_total": len(self.primary),
            "extensions_passed": ext_passed,
            "extensions_total": len(self.extensions),
            "all_primary_passed": all(
                r.passed for r in self.primary),
            "all_extensions_passed": all(
                r.passed for r in self.extensions),
        }

    def print_comparison(self) -> None:
        print("=" * 74)
        print("Architecture Survey — six architectures, one substrate")
        print("=" * 74)
        print()
        header = (
            f"  {'Architecture':16s}  {'Comp':8s}  "
            f"{'Direction':12s}  {'Unit':10s}  "
            f"{'Flow':13s}  {'Convergence':13s}")
        print(header)
        print(
            f"  {'─' * 16}  {'─' * 8}  {'─' * 12}  "
            f"{'─' * 10}  {'─' * 13}  {'─' * 13}")
        for r in self.primary:
            if r.passed:
                marker = "✓"
            elif r.skipped:
                marker = "·"
            else:
                marker = "✗"
            print(
                f"  {marker} {r.spec.name:14s}  "
                f"{r.spec.component:8s}  "
                f"{r.spec.direction:12s}  "
                f"{r.spec.unit:10s}  "
                f"{r.spec.flow:13s}  "
                f"{r.spec.convergence:13s}")

        primary_passed = sum(
            1 for r in self.primary if r.passed)
        primary_total = len(self.primary)
        print()
        print(f"  Demos run:    "
              f"{primary_passed}/{primary_total}")
        print(f"  All passed:   "
              f"{primary_passed == primary_total}")

        if any(not r.passed and not r.skipped
               for r in self.primary):
            print("  Failures:")
            for r in self.primary:
                if not r.passed and not r.skipped:
                    print(f"    ✗ {r.spec.name}: {r.reason}")

        print()
        print("  Extensions (build on the architectures above):")
        for r in self.extensions:
            if r.passed:
                marker = "✓"
            elif r.skipped:
                marker = "·"
            else:
                marker = "✗"
            print(
                f"  {marker} {r.spec.component:8s}  "
                f"{r.spec.name:24s}  "
                f"{r.spec.description}")

        ext_passed = sum(
            1 for r in self.extensions if r.passed)
        ext_total = len(self.extensions)
        print()
        print(f"  Extensions:   "
              f"{ext_passed}/{ext_total}")
        print()
        print(f"  Artifacts:    {self.artifact_dir}")
        print(f"  → architecture_survey.json")
        for r in self.primary + self.extensions:
            if r.passed:
                print(f"  → {r.spec.name}/")


# =====================================================================
# Demo
# =====================================================================

def demo(artifact_dir: Optional[str] = None) -> Dict:
    """Run all architecture demos; print comparison; save aggregate.

    Artifacts:
      <artifact_dir>/architecture_survey/<timestamp>/
        architecture_survey.json     — the aggregate
        octopus/...                  — each demo's own artifacts
        relay/...
        ...
    """
    if artifact_dir is None:
        artifact_dir = "artifacts"
    root = Path(artifact_dir) / "architecture_survey"
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    run_dir = root / timestamp
    run_dir.mkdir(parents=True, exist_ok=True)

    runner = ArchitectureRunner(run_dir)
    runner.run_all()
    runner.print_comparison()

    summary = runner.summary()
    summary_path = run_dir / "architecture_survey.json"
    summary_path.write_text(json.dumps(summary, indent=2))
    print(f"  → {summary_path}")
    print()
    print("  Anchor (public domain, Emily Dickinson):")
    print("    'The Brain – is wider than the Sky –'")
    print("    'For – put them side by side –'")
    print("    'The one the other will contain'")
    print("    'With ease – and You – beside –'")

    return summary

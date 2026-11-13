import json
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest

import multiverse_c51 as c51
from multiverse_c51 import (
    REPO_DIR,
    ArchitectureSpec,
    ARCHITECTURES, EXTENSIONS,
    RunResult, ArchitectureRunner,
    demo,
)


# =====================================================================
# Spec constants
# =====================================================================

def test_six_primary_architectures():
    print("=== Six primary architectures ===")
    assert len(ARCHITECTURES) == 6
    names = [a.name for a in ARCHITECTURES]
    assert names == [
        "octopus", "relay", "swarm", "council",
        "autonomic", "institutional"]


def test_four_extensions():
    print("=== Four extensions ===")
    assert len(EXTENSIONS) == 4
    names = [a.name for a in EXTENSIONS]
    assert names == [
        "deliberation", "council_federation",
        "cross_arch_federation", "persistence"]


def test_all_specs_have_required_fields():
    print("=== All specs have required fields ===")
    for spec in ARCHITECTURES + EXTENSIONS:
        assert spec.name
        assert spec.component
        assert spec.module.startswith("multiverse_c")
        assert spec.demo_fn == "demo"
        assert spec.audit_filename.endswith(".json")
        assert spec.description


def test_primary_axes_all_filled():
    print("=== Primary specs: all axis values filled ===")
    for spec in ARCHITECTURES:
        assert spec.direction, spec.name
        assert spec.unit, spec.name
        assert spec.flow, spec.name
        assert spec.convergence, spec.name


def test_architecture_axes_distinct():
    """Every primary architecture has a distinct (direction, unit,
    flow, convergence) tuple."""
    print("=== Primary architectures: distinct axis tuples ===")
    tuples = [
        (a.direction, a.unit, a.flow, a.convergence)
        for a in ARCHITECTURES
    ]
    assert len(set(tuples)) == len(tuples)


# =====================================================================
# ArchitectureSpec
# =====================================================================

def test_spec_is_frozen():
    print("=== ArchitectureSpec: frozen ===")
    spec = ARCHITECTURES[0]
    with pytest.raises(Exception):
        spec.name = "changed"


# =====================================================================
# _run_one with mocked subprocess
# =====================================================================

def _mock_subprocess(monkeypatch, returncode=0,
                      stdout="", stderr=""):
    """Patch subprocess.run to return a fake result."""
    class FakeProc:
        def __init__(self):
            self.returncode = returncode
            self.stdout = stdout
            self.stderr = stderr
    def fake_run(*a, **kw):
        return FakeProc()
    monkeypatch.setattr(c51.subprocess, "run", fake_run)


def test_run_one_success(tmp_path, monkeypatch):
    print("=== _run_one: success produces RunResult(passed) ===")
    # Mock subprocess AND pre-create the audit file
    spec = ARCHITECTURES[0]
    subdir = tmp_path / spec.name
    subdir.mkdir(parents=True)
    (subdir / spec.audit_filename).write_text(
        json.dumps({"test": True}))
    _mock_subprocess(monkeypatch, returncode=0)
    runner = ArchitectureRunner(tmp_path)
    result = runner._run_one(spec)
    assert result.passed
    assert not result.skipped
    assert result.audit_data == {"test": True}


def test_run_one_missing_audit(tmp_path, monkeypatch):
    print("=== _run_one: missing audit file → passed=False ===")
    spec = ARCHITECTURES[0]
    _mock_subprocess(monkeypatch, returncode=0)
    # Note: no audit file created
    runner = ArchitectureRunner(tmp_path)
    result = runner._run_one(spec)
    assert not result.passed
    assert not result.skipped
    assert "missing audit" in result.reason


def test_run_one_subprocess_failure(tmp_path, monkeypatch):
    print("=== _run_one: subprocess failure → passed=False ===")
    spec = ARCHITECTURES[0]
    _mock_subprocess(
        monkeypatch, returncode=1,
        stderr="AssertionError: something broke\n")
    runner = ArchitectureRunner(tmp_path)
    result = runner._run_one(spec)
    assert not result.passed
    assert not result.skipped
    assert "exit 1" in result.reason


def test_run_one_cryptography_missing(tmp_path, monkeypatch):
    print("=== _run_one: missing cryptography → skipped ===")
    spec = ARCHITECTURES[0]
    _mock_subprocess(
        monkeypatch, returncode=1,
        stderr="RuntimeError: demo requires `cryptography`\n")
    runner = ArchitectureRunner(tmp_path)
    result = runner._run_one(spec)
    assert not result.passed
    assert result.skipped
    assert "cryptography" in result.reason.lower()


def test_run_one_invalid_audit_json(tmp_path, monkeypatch):
    print("=== _run_one: invalid audit JSON → passed=False ===")
    spec = ARCHITECTURES[0]
    subdir = tmp_path / spec.name
    subdir.mkdir(parents=True)
    (subdir / spec.audit_filename).write_text(
        "{ not valid json")
    _mock_subprocess(monkeypatch, returncode=0)
    runner = ArchitectureRunner(tmp_path)
    result = runner._run_one(spec)
    assert not result.passed
    assert "invalid audit" in result.reason


def test_run_one_timeout(tmp_path, monkeypatch):
    print("=== _run_one: timeout → passed=False ===")
    spec = ARCHITECTURES[0]
    def fake_run(*a, **kw):
        raise subprocess.TimeoutExpired(cmd="x", timeout=1)
    monkeypatch.setattr(c51.subprocess, "run", fake_run)
    runner = ArchitectureRunner(tmp_path, timeout=1)
    result = runner._run_one(spec)
    assert not result.passed
    assert "timeout" in result.reason.lower()


# =====================================================================
# Real subprocess (one fast demo)
# =====================================================================

def test_real_c41_demo(tmp_path):
    """Real subprocess: C41 (octopus) — fast, no network."""
    print("=== Real subprocess: C41 octopus demo ===")
    try:
        import cryptography  # noqa
    except ImportError:
        pytest.skip("cryptography not installed")
    runner = ArchitectureRunner(tmp_path, timeout=30)
    spec = ARCHITECTURES[0]  # octopus
    result = runner._run_one(spec)
    assert result.passed, (
        f"octopus demo failed: {result.reason}")
    assert result.audit_data is not None
    assert "epochs" in result.audit_data
    assert (tmp_path / "octopus" / "octopus_demo.json").exists()


# =====================================================================
# Full runner with mocked subprocess
# =====================================================================

def test_run_all_with_mocks(tmp_path, monkeypatch):
    print("=== run_all: with mocked subprocess, all succeed ===")
    # Pre-create audit files for all specs
    for spec in ARCHITECTURES + EXTENSIONS:
        subdir = tmp_path / spec.name
        subdir.mkdir(parents=True, exist_ok=True)
        (subdir / spec.audit_filename).write_text(
            json.dumps({"mock": spec.name}))
    _mock_subprocess(monkeypatch, returncode=0)
    runner = ArchitectureRunner(tmp_path)
    runner.run_all()
    assert len(runner.primary) == 6
    assert len(runner.extensions) == 4
    assert all(r.passed for r in runner.primary)
    assert all(r.passed for r in runner.extensions)


def test_run_all_with_one_failure(tmp_path, monkeypatch):
    print("=== run_all: one failing demo doesn't break others ===")
    for spec in ARCHITECTURES + EXTENSIONS:
        subdir = tmp_path / spec.name
        subdir.mkdir(parents=True, exist_ok=True)
        (subdir / spec.audit_filename).write_text(
            json.dumps({"mock": spec.name}))
    # Make the second spec's demo fail
    original_run = c51.subprocess.run
    def fake_run(cmd, **kw):
        # Detect which spec by inspecting the -c code
        code = " ".join(cmd[2:])
        if "multiverse_c42" in code:
            class FakeProc:
                returncode = 1
                stdout = ""
                stderr = "boom\n"
            return FakeProc()
        class FakeProc:
            returncode = 0
            stdout = ""
            stderr = ""
        return FakeProc()
    monkeypatch.setattr(c51.subprocess, "run", fake_run)
    runner = ArchitectureRunner(tmp_path)
    runner.run_all()
    # Relay (C42) failed; others passed
    relay = next(r for r in runner.primary
                 if r.spec.name == "relay")
    assert not relay.passed
    others = [r for r in runner.primary
              if r.spec.name != "relay"]
    assert all(r.passed for r in others)


# =====================================================================
# Summary and comparison output
# =====================================================================

def _build_mocked_runner(tmp_path, monkeypatch):
    for spec in ARCHITECTURES + EXTENSIONS:
        subdir = tmp_path / spec.name
        subdir.mkdir(parents=True, exist_ok=True)
        (subdir / spec.audit_filename).write_text(
            json.dumps({"mock": spec.name}))
    _mock_subprocess(monkeypatch, returncode=0)
    runner = ArchitectureRunner(tmp_path)
    runner.run_all()
    return runner


def test_summary_structure(tmp_path, monkeypatch):
    print("=== Summary: correct structure ===")
    runner = _build_mocked_runner(tmp_path, monkeypatch)
    s = runner.summary()
    assert s["kind"] == "architecture_survey"
    assert len(s["primary_architectures"]) == 6
    assert len(s["extensions"]) == 4
    assert s["primary_passed"] == 6
    assert s["primary_total"] == 6
    assert s["extensions_passed"] == 4
    assert s["extensions_total"] == 4
    assert s["all_primary_passed"] is True
    assert s["all_extensions_passed"] is True
    # Each primary has its axis values
    for p in s["primary_architectures"]:
        assert p["direction"]
        assert p["unit"]
        assert p["flow"]
        assert p["convergence"]


def test_summary_json_serializable(tmp_path, monkeypatch):
    print("=== Summary: JSON serializable ===")
    runner = _build_mocked_runner(tmp_path, monkeypatch)
    s = runner.summary()
    wire = json.dumps(s)
    parsed = json.loads(wire)
    assert parsed["kind"] == "architecture_survey"
    assert len(parsed["primary_architectures"]) == 6


def test_print_comparison_output(tmp_path, monkeypatch, capsys):
    print("=== print_comparison: readable output ===")
    runner = _build_mocked_runner(tmp_path, monkeypatch)
    runner.print_comparison()
    out = capsys.readouterr().out
    assert "Architecture Survey" in out
    for spec in ARCHITECTURES:
        assert spec.name in out
    assert "6/6" in out
    assert "All passed:   True" in out
    # Axis header present
    assert "Direction" in out
    assert "Convergence" in out
    # Extensions section
    assert "Extensions" in out
    assert "C45" in out
    assert "C49" in out


def test_print_comparison_with_failure(tmp_path, monkeypatch, capsys):
    print("=== print_comparison: failures named ===")
    for spec in ARCHITECTURES + EXTENSIONS:
        subdir = tmp_path / spec.name
        subdir.mkdir(parents=True, exist_ok=True)
        (subdir / spec.audit_filename).write_text(
            json.dumps({"mock": spec.name}))
    def fake_run(cmd, **kw):
        code = " ".join(cmd[2:])
        if "multiverse_c43" in code:
            class FakeProc:
                returncode = 1
                stdout = ""
                stderr = "swarm broke\n"
            return FakeProc()
        class FakeProc:
            returncode = 0
            stdout = ""
            stderr = ""
        return FakeProc()
    monkeypatch.setattr(c51.subprocess, "run", fake_run)
    runner = ArchitectureRunner(tmp_path)
    runner.run_all()
    runner.print_comparison()
    out = capsys.readouterr().out
    assert "5/6" in out
    assert "Failures:" in out
    assert "swarm" in out


# =====================================================================
# Demo (uses mocks for speed)
# =====================================================================

def test_demo_writes_survey_json(tmp_path, monkeypatch):
    print("=== Demo: writes architecture_survey.json ===")
    # Mock subprocess so no real demos run
    def fake_run(cmd, **kw):
        # Figure out which spec by inspecting the code
        code = " ".join(cmd[2:])
        # Find matching spec
        for spec in ARCHITECTURES + EXTENSIONS:
            if spec.module in code:
                # Extract subdir from the demo() call
                # code looks like: from module import demo\ndemo(artifact_dir='<path>')\n
                import re
                m = re.search(
                    r"demo\(artifact_dir='([^']+)'\)", code)
                if m:
                    subdir = Path(m.group(1))
                    subdir.mkdir(parents=True, exist_ok=True)
                    (subdir / spec.audit_filename).write_text(
                        json.dumps({"mock": spec.name}))
                break
        class FakeProc:
            returncode = 0
            stdout = ""
            stderr = ""
        return FakeProc()
    monkeypatch.setattr(c51.subprocess, "run", fake_run)
    summary = demo(artifact_dir=str(tmp_path))
    assert summary["kind"] == "architecture_survey"
    assert summary["primary_total"] == 6
    # Find the survey JSON
    survey_files = list(
        (tmp_path / "architecture_survey").rglob(
            "architecture_survey.json"))
    assert len(survey_files) == 1
    parsed = json.loads(survey_files[0].read_text())
    assert parsed["primary_total"] == 6


if __name__ == "__main__":
    test_six_primary_architectures()
    test_four_extensions()
    test_all_specs_have_required_fields()
    test_primary_axes_all_filled()
    test_architecture_axes_distinct()
    test_spec_is_frozen()
    # Mocked tests need fixtures; run them under pytest
    print("\nNote: run under pytest for full suite")

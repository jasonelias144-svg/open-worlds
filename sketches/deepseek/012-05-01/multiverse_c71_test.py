import json
import subprocess
import tempfile
from pathlib import Path

import pytest

import multiverse_c71 as c71
from multiverse_c71 import (
    REPO_DIR, GROUP_ORDER, DEMOS, DemoSpec,
    RunResult, run_one, run_all,
    ArcReport, demo, main,
)


# =====================================================================
# Spec validity
# =====================================================================

def test_all_specs_have_required_fields():
    print("=== All specs have required fields ===")
    for spec in DEMOS:
        assert isinstance(spec, DemoSpec)
        assert spec.name
        assert spec.component.startswith("C")
        assert spec.module.startswith("multiverse_c")
        assert spec.demo_fn == "demo"
        assert spec.audit_relative_path.endswith(".json")
        assert spec.group in GROUP_ORDER
        assert spec.description


def test_no_duplicate_names():
    print("=== No duplicate demo names ===")
    names = [s.name for s in DEMOS]
    assert len(names) == len(set(names))


def test_all_groups_covered():
    print("=== All groups are represented ===")
    seen = {s.group for s in DEMOS}
    assert seen == set(GROUP_ORDER)


def test_architecture_axis_present():
    print("=== Architectures have axis values ===")
    for spec in DEMOS:
        if spec.group == "architectures":
            assert spec.architecture_axis is not None
            for key in ("direction", "unit",
                        "flow", "convergence"):
                assert spec.architecture_axis.get(key)


def test_non_architecture_axis_absent():
    print("=== Non-architectures have no axis ===")
    for spec in DEMOS:
        if spec.group != "architectures":
            assert spec.architecture_axis is None


def test_architecture_axis_distinct():
    print("=== Architectures: distinct axis tuples ===")
    tuples = []
    for spec in DEMOS:
        if spec.group == "architectures":
            t = tuple(spec.architecture_axis.get(k)
                       for k in ("direction", "unit",
                                 "flow", "convergence"))
            tuples.append(t)
    assert len(tuples) == len(set(tuples))


def test_all_modules_exist():
    print("=== All demo modules exist ===")
    for spec in DEMOS:
        spec_obj = importlib.util.find_spec(spec.module)
        assert spec_obj is not None, (
            f"module {spec.module} not found")


import importlib.util  # noqa: E402


# =====================================================================
# run_one with mocked subprocess
# =====================================================================

def _mock_subprocess(monkeypatch, returncode=0,
                      stdout="", stderr=""):
    class FakeProc:
        def __init__(self):
            self.returncode = returncode
            self.stdout = stdout
            self.stderr = stderr
    def fake_run(*a, **kw):
        return FakeProc()
    monkeypatch.setattr(c71.subprocess, "run", fake_run)


def _prepopulate_audit(tmp_path, spec, content=None):
    """Create the audit file at the expected location."""
    if content is None:
        content = {"mock": spec.name}
    audit_path = (
        tmp_path / spec.group / spec.name
        / spec.audit_relative_path)
    audit_path.parent.mkdir(parents=True, exist_ok=True)
    audit_path.write_text(json.dumps(content))
    return audit_path


def test_run_one_success(tmp_path, monkeypatch):
    print("=== run_one: success ===")
    spec = DEMOS[0]
    _prepopulate_audit(tmp_path, spec)
    _mock_subprocess(monkeypatch, returncode=0)
    result = run_one(spec, tmp_path)
    assert result.passed
    assert not result.skipped
    assert result.audit_path is not None


def test_run_one_missing_audit(tmp_path, monkeypatch):
    print("=== run_one: missing audit → fail ===")
    spec = DEMOS[0]
    _mock_subprocess(monkeypatch, returncode=0)
    result = run_one(spec, tmp_path)
    assert not result.passed
    assert "missing" in result.reason


def test_run_one_subprocess_failure(tmp_path, monkeypatch):
    print("=== run_one: subprocess failure → fail ===")
    spec = DEMOS[0]
    _mock_subprocess(
        monkeypatch, returncode=1,
        stderr="AssertionError: boom\n")
    result = run_one(spec, tmp_path)
    assert not result.passed
    assert "exit 1" in result.reason


def test_run_one_cryptography_skip(tmp_path, monkeypatch):
    print("=== run_one: cryptography missing → skipped ===")
    spec = DEMOS[0]
    _mock_subprocess(
        monkeypatch, returncode=1,
        stderr="RuntimeError: demo requires `cryptography`\n")
    result = run_one(spec, tmp_path)
    assert not result.passed
    assert result.skipped
    assert "cryptography" in result.reason.lower()


def test_run_one_invalid_json(tmp_path, monkeypatch):
    print("=== run_one: invalid audit JSON → fail ===")
    spec = DEMOS[0]
    audit_path = (
        tmp_path / spec.group / spec.name
        / spec.audit_relative_path)
    audit_path.parent.mkdir(parents=True, exist_ok=True)
    audit_path.write_text("{ not valid json")
    _mock_subprocess(monkeypatch, returncode=0)
    result = run_one(spec, tmp_path)
    assert not result.passed
    assert "invalid audit" in result.reason


def test_run_one_timeout(tmp_path, monkeypatch):
    print("=== run_one: timeout → fail ===")
    spec = DEMOS[0]
    def raising(*a, **kw):
        raise subprocess.TimeoutExpired(cmd="x", timeout=1)
    monkeypatch.setattr(c71.subprocess, "run", raising)
    result = run_one(spec, tmp_path, timeout=1)
    assert not result.passed
    assert "timeout" in result.reason.lower()


def test_run_one_exception(tmp_path, monkeypatch):
    print("=== run_one: subprocess raises → fail ===")
    spec = DEMOS[0]
    def raising(*a, **kw):
        raise RuntimeError("unexpected")
    monkeypatch.setattr(c71.subprocess, "run", raising)
    result = run_one(spec, tmp_path)
    assert not result.passed
    assert "subprocess raised" in result.reason


def test_run_one_uses_subpath_for_deploy(tmp_path, monkeypatch):
    """Deploy spec writes into a subdir; C71 finds the audit
    at the full relative path."""
    print("=== run_one: subpath audit (deploy) ===")
    deploy_spec = next(
        s for s in DEMOS if s.name == "deploy")
    _prepopulate_audit(tmp_path, deploy_spec)
    _mock_subprocess(monkeypatch, returncode=0)
    result = run_one(deploy_spec, tmp_path)
    assert result.passed


# =====================================================================
# run_all with mocks
# =====================================================================

def test_run_all_all_pass(tmp_path, monkeypatch):
    print("=== run_all: all demos pass (mocked) ===")
    for spec in DEMOS:
        _prepopulate_audit(tmp_path, spec)
    _mock_subprocess(monkeypatch, returncode=0)
    results = run_all(tmp_path, quiet=True)
    assert len(results) == len(DEMOS)
    assert all(r.passed for r in results)


def test_run_all_groups_filter(tmp_path, monkeypatch):
    print("=== run_all: groups filter ===")
    for spec in DEMOS:
        _prepopulate_audit(tmp_path, spec)
    _mock_subprocess(monkeypatch, returncode=0)
    results = run_all(
        tmp_path, groups=["architectures"], quiet=True)
    assert len(results) == 7
    assert all(r.spec.group == "architectures" for r in results)


def test_run_all_continues_on_failure(tmp_path, monkeypatch):
    print("=== run_all: continues after a failure ===")
    for spec in DEMOS:
        _prepopulate_audit(tmp_path, spec)
    # Fail on the relay (C42)
    def fake_run(cmd, **kw):
        code = " ".join(cmd[2:])
        class FakeProc:
            pass
        p = FakeProc()
        if "multiverse_c42" in code:
            p.returncode = 1
            p.stdout = ""
            p.stderr = "boom\n"
        else:
            p.returncode = 0
            p.stdout = ""
            p.stderr = ""
        return p
    monkeypatch.setattr(c71.subprocess, "run", fake_run)
    results = run_all(tmp_path, quiet=True)
    assert len(results) == len(DEMOS)
    relay = next(r for r in results
                  if r.spec.component == "C42")
    assert not relay.passed
    others = [r for r in results if r.spec.component != "C42"]
    assert all(r.passed for r in others)


# =====================================================================
# ArcReport
# =====================================================================

def _build_mocked_report(tmp_path, monkeypatch):
    for spec in DEMOS:
        _prepopulate_audit(tmp_path, spec)
    _mock_subprocess(monkeypatch, returncode=0)
    results = run_all(tmp_path, quiet=True)
    return ArcReport.from_results(results, tmp_path)


def test_report_totals(tmp_path, monkeypatch):
    print("=== ArcReport: totals ===")
    report = _build_mocked_report(tmp_path, monkeypatch)
    passed, failed, skipped, total_s = report.totals()
    assert passed == len(DEMOS)
    assert failed == 0
    assert skipped == 0
    assert total_s >= 0


def test_report_by_group(tmp_path, monkeypatch):
    print("=== ArcReport: by_group ===")
    report = _build_mocked_report(tmp_path, monkeypatch)
    bg = report.by_group()
    assert set(bg.keys()) == set(GROUP_ORDER)
    assert len(bg["architectures"]) == 7
    assert len(bg["diplomacy"]) == 5


def test_report_failures_empty_when_all_pass(
    tmp_path, monkeypatch,
):
    print("=== ArcReport: failures empty ===")
    report = _build_mocked_report(tmp_path, monkeypatch)
    assert report.failures() == []


def test_report_format_all_groups(tmp_path, monkeypatch):
    print("=== ArcReport: format includes all groups ===")
    report = _build_mocked_report(tmp_path, monkeypatch)
    text = report.format()
    assert "The Arc" in text
    assert f"{len(DEMOS)} demos" in text
    assert "Architectures" in text
    assert "Diplomacy" in text
    assert "Curators" in text
    assert "Totals" in text


def test_report_format_architecture_table(
    tmp_path, monkeypatch,
):
    print("=== ArcReport: architecture axis table ===")
    report = _build_mocked_report(tmp_path, monkeypatch)
    text = report.format()
    assert "Architecture axis chart" in text
    for spec in DEMOS:
        if spec.group == "architectures":
            assert spec.name in text


def test_report_format_names_failures(
    tmp_path, monkeypatch,
):
    print("=== ArcReport: failure named in output ===")
    for spec in DEMOS:
        _prepopulate_audit(tmp_path, spec)
    def fake_run(cmd, **kw):
        code = " ".join(cmd[2:])
        class FakeProc:
            pass
        p = FakeProc()
        if "multiverse_c43" in code:
            p.returncode = 1
            p.stdout = ""
            p.stderr = "swarm broke\n"
        else:
            p.returncode = 0
            p.stdout = ""
            p.stderr = ""
        return p
    monkeypatch.setattr(c71.subprocess, "run", fake_run)
    results = run_all(tmp_path, quiet=True)
    report = ArcReport.from_results(results, tmp_path)
    text = report.format()
    assert "Failed:  1" in text or "Failed: 1" in text
    assert "swarm" in text
    assert "swarm broke" in text


def test_report_to_dict_serializable(
    tmp_path, monkeypatch,
):
    print("=== ArcReport: to_dict is JSON-serializable ===")
    report = _build_mocked_report(tmp_path, monkeypatch)
    d = report.to_dict()
    wire = json.dumps(d)
    parsed = json.loads(wire)
    assert parsed["kind"] == "arc_survey"
    assert parsed["totals"]["passed"] == len(DEMOS)
    assert "architectures" in parsed["by_group"]
    assert len(parsed["results"]) == len(DEMOS)


# =====================================================================
# Real subprocess — one fast demo
# =====================================================================

def test_real_c41_octopus(tmp_path):
    print("=== Real: C41 octopus (in-memory, fast) ===")
    try:
        import cryptography  # noqa
    except ImportError:
        pytest.skip("cryptography not installed")
    spec = next(s for s in DEMOS if s.component == "C41")
    result = run_one(spec, tmp_path, timeout=30)
    assert result.passed, result.reason
    assert result.audit_path is not None
    data = json.loads(result.audit_path.read_text())
    assert "epochs" in data


def test_real_c55_curator(tmp_path):
    print("=== Real: C55 curator (in-memory, fast) ===")
    try:
        import cryptography  # noqa
    except ImportError:
        pytest.skip("cryptography not installed")
    spec = next(s for s in DEMOS if s.component == "C55")
    result = run_one(spec, tmp_path, timeout=30)
    assert result.passed, result.reason
    data = json.loads(result.audit_path.read_text())
    assert data.get("link_established") is True


# =====================================================================
# CLI
# =====================================================================

def test_cli_unknown_group(tmp_path, capsys):
    print("=== CLI: unknown group → error ===")
    rc = main([
        "--artifact-dir", str(tmp_path),
        "--groups", "nonexistent",
    ])
    err = capsys.readouterr()
    assert rc == 1
    assert "Unknown groups" in err.err


def test_cli_quiet_mode(tmp_path, monkeypatch):
    print("=== CLI: --quiet mode ===")
    for spec in DEMOS:
        _prepopulate_audit(tmp_path, spec)
    _mock_subprocess(monkeypatch, returncode=0)
    rc = main([
        "--artifact-dir", str(tmp_path),
        "--quiet",
    ])
    assert rc == 0


def test_cli_subset_returns_zero(tmp_path, monkeypatch):
    print("=== CLI: subset → 0 ===")
    for spec in DEMOS:
        if spec.group == "architectures":
            _prepopulate_audit(tmp_path, spec)
    _mock_subprocess(monkeypatch, returncode=0)
    rc = main([
        "--artifact-dir", str(tmp_path),
        "--groups", "architectures",
        "--quiet",
    ])
    assert rc == 0


# =====================================================================
# Demo
# =====================================================================

def test_demo_writes_arc_survey(tmp_path, monkeypatch):
    print("=== Demo: writes arc_survey.json ===")
    for spec in DEMOS:
        _prepopulate_audit(tmp_path, spec)
    _mock_subprocess(monkeypatch, returncode=0)
    summary = demo(artifact_dir=str(tmp_path), quiet=True)
    assert summary["kind"] == "arc_survey"
    assert summary["totals"]["passed"] == len(DEMOS)
    survey_files = list(
        (tmp_path / "arc").rglob("arc_survey.json"))
    assert len(survey_files) == 1


def test_demo_subset(tmp_path, monkeypatch):
    print("=== Demo: subset groups ===")
    for spec in DEMOS:
        if spec.group == "diplomacy":
            _prepopulate_audit(tmp_path, spec)
    _mock_subprocess(monkeypatch, returncode=0)
    summary = demo(
        artifact_dir=str(tmp_path),
        groups=["diplomacy"], quiet=True)
    assert summary["totals"]["passed"] == 5
    assert summary["totals"]["total"] == 5


def test_demo_real_subset(tmp_path):
    """Run a real subset end-to-end: 2 fast demos."""
    print("=== Demo: real subset (C41 + C55) ===")
    try:
        import cryptography  # noqa
    except ImportError:
        pytest.skip("cryptography not installed")
    summary = demo(
        artifact_dir=str(tmp_path),
        groups=["architectures"],  # 7 demos, all fast
        quiet=True)
    # All 7 architectures should pass
    assert summary["totals"]["passed"] == 7
    assert summary["totals"]["failed"] == 0


if __name__ == "__main__":
    test_all_specs_have_required_fields()
    test_no_duplicate_names()
    test_all_groups_covered()
    test_architecture_axis_present()
    test_non_architecture_axis_absent()
    test_architecture_axis_distinct()
    test_all_modules_exist()
    print("\nUse pytest for the full suite.")

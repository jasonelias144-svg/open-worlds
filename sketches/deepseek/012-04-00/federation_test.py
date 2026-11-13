"""federation_test.py — verify the demo runs end-to-end."""

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest


def _run(args, timeout=90):
    return subprocess.run(
        [sys.executable, "federation.py"] + args,
        capture_output=True, text=True, timeout=timeout,
        cwd=str(Path(__file__).parent),
    )


def test_demo_runs_and_saves_artifacts():
    print("=== demo mode runs end-to-end ===")
    with tempfile.TemporaryDirectory() as tmpdir:
        result = _run(["--mode", "demo", "--artifact-dir", tmpdir])
        assert result.returncode == 0, \
            f"demo failed:\n{result.stdout}\n{result.stderr}"
        ts_dirs = list(Path(tmpdir).iterdir())
        assert len(ts_dirs) == 1, f"expected 1 artifact dir, got {ts_dirs}"
        run_dir = ts_dirs[0]
        json_path = run_dir / "collaboration.json"
        txt_path = run_dir / "collaboration.txt"
        assert json_path.exists()
        assert txt_path.exists()
        # JSON is well-formed and complete
        data = json.loads(json_path.read_text())
        assert "collaboration" in data
        assert "generations" in data
        assert "aggregates" in data
        assert data["aggregates"]["turns_attempted"] >= 2
        print(f"  turns: {data['aggregates']['turns_attempted']}, "
              f"cost: ${data['aggregates']['total_cost_usd']:.6f}")
        print(f"  artifacts: {json_path.name}, {txt_path.name}")


def test_demo_unsigned_runs():
    print("=== demo unsigned runs without cryptography ===")
    with tempfile.TemporaryDirectory() as tmpdir:
        result = _run([
            "--mode", "demo",
            "--no-signed",
            "--artifact-dir", tmpdir,
        ])
        assert result.returncode == 0, \
            f"demo failed:\n{result.stdout}\n{result.stderr}"
        run_dir = next(Path(tmpdir).iterdir())
        data = json.loads(
            (run_dir / "collaboration.json").read_text())
        assert data["aggregates"]["turns_attempted"] >= 2


def test_demo_report_has_three_models():
    print("=== demo report shows three models ===")
    with tempfile.TemporaryDirectory() as tmpdir:
        result = _run(["--mode", "demo", "--artifact-dir", tmpdir])
        assert result.returncode == 0
        run_dir = next(Path(tmpdir).iterdir())
        data = json.loads(
            (run_dir / "collaboration.json").read_text())
        models = list(data["aggregates"]["by_model"].keys())
        print(f"  models: {models}")
        assert len(models) == 3


def test_live_mode_works_when_crypto_available():
    """Skip if cryptography not installed."""
    try:
        import cryptography  # noqa
    except ImportError:
        pytest.skip("cryptography not installed")
    print("=== live mode runs end-to-end ===")
    with tempfile.TemporaryDirectory() as tmpdir:
        result = _run(["--mode", "live", "--artifact-dir", tmpdir])
        assert result.returncode == 0, \
            f"live failed:\n{result.stdout}\n{result.stderr}"
        run_dir = next(Path(tmpdir).iterdir())
        # Conformance artifact exists and passed
        conf = (run_dir / "conformance.txt").read_text()
        assert "PASSES" in conf
        # Collaboration artifact exists
        data = json.loads(
            (run_dir / "collaboration.json").read_text())
        assert data["aggregates"]["turns_attempted"] >= 2
        print(f"  live passed")


if __name__ == "__main__":
    test_demo_runs_and_saves_artifacts()
    test_demo_unsigned_runs()
    test_demo_report_has_three_models()
    test_live_mode_works_when_crypto_available()

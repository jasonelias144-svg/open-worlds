"""
federation.py — Run the federation end-to-end.

Two modes:
  demo  — in-process. Fast. Multi-model, signed. One report.
  live  — HTTP world + real HTTP conformance + passport verification
          + in-process collaboration. Slower, but proves the wire.

Both modes save artifacts to artifacts/<timestamp>/.

Run directly:
  python federation.py --mode demo
  python federation.py --mode live

Or via Make:
  make demo
  make live
"""

import argparse
import json
import sys
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

# Allow running from any directory
sys.path.insert(0, str(Path(__file__).parent.resolve()))

from multiverse_c1 import create_identity
from multiverse_c4 import PoetryWorld
from multiverse_c13 import HAS_CRYPTO, SignedWorld
from multiverse_c15 import (
    PassportV2, PassportEntry, InMemoryKeyResolver,
)
from multiverse_c16 import ManifestResolver
from multiverse_c18 import (
    default_assignments, run_multi_model_collaboration,
    format_roster, format_attribution,
)
from wcp_http_shim import WorldProtocolServer


# =====================================================================
# Artifacts
# =====================================================================

def make_artifact_dir(base: str = "artifacts") -> Path:
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    path = Path(base) / ts
    path.mkdir(parents=True, exist_ok=True)
    return path


def _save_report(report, artifact_dir: Path, assignments):
    """Save the collaboration report in JSON and text forms."""
    (artifact_dir / "collaboration.json").write_text(
        json.dumps(report.to_dict(), indent=2))
    text = (
        report.report() + "\n\n" +
        format_roster(assignments) + "\n\n" +
        format_attribution(report, assignments) + "\n"
    )
    (artifact_dir / "collaboration.txt").write_text(text)
    print(f"  → {artifact_dir}/collaboration.json")
    print(f"  → {artifact_dir}/collaboration.txt")


# =====================================================================
# Demo mode: everything in-process
# =====================================================================

def run_demo(artifact_dir: Path, signed: bool = True) -> int:
    print("=" * 70)
    print("FEDERATION DEMO (in-process, multi-model"
          + (", signed)" if signed else ")"))
    print("=" * 70)

    if signed and not HAS_CRYPTO:
        print("⚠ cryptography not installed — falling back to unsigned")
        signed = False

    assignments = default_assignments(seed=42)
    print()
    print(format_roster(assignments))

    print("\n" + "=" * 70)
    print("Running collaboration...")
    print("=" * 70)
    t0 = time.time()
    report = run_multi_model_collaboration(
        seed=42, assignments=assignments,
        max_iterations=20, signed=signed,
    )
    elapsed = time.time() - t0

    print()
    print(report.report())
    print()
    print(format_attribution(report, assignments))

    _save_report(report, artifact_dir, assignments)

    verified = getattr(report, "signed_acks_verified", 0)
    print()
    print("-" * 70)
    print(f"  turns accepted: {report.turns_accepted()}")
    print(f"  converged:      {report.collaboration.converged}")
    if signed:
        print(f"  signed acks:    {verified}/{report.turns_accepted()}")
    print(f"  total cost:     ${report.total_cost_usd():.6f}")
    print(f"  wall clock:     {elapsed*1000:.0f} ms")
    print("-" * 70)
    return 0


# =====================================================================
# Live mode: HTTP world + HTTP conformance + HTTP passport verify
# =====================================================================

def _post(url: str, body: dict) -> dict:
    req = urllib.request.Request(
        url, data=json.dumps(body).encode(),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=5) as resp:
        return json.loads(resp.read())


def run_live(artifact_dir: Path) -> int:
    print("=" * 70)
    print("FEDERATION LIVE (HTTP server + conformance + passport)")
    print("=" * 70)

    if not HAS_CRYPTO:
        print("ERROR: live mode requires cryptography")
        return 1

    # 1. Start a signed Poetry World over HTTP
    base = PoetryWorld("world:poetry", "The Poetry World")
    signed = SignedWorld(base)
    server = WorldProtocolServer(signed, port=0)
    server.serve_in_thread()
    time.sleep(0.2)
    port = server._httpd.server_address[1]
    url = f"http://127.0.0.1:{port}"
    print(f"\nPoetry World (WCP/0.2): {url}")

    try:
        # 2. Run WCP/0.2 conformance over HTTP
        from wcp_conformance_v02 import ConformanceRunnerV02
        from wcp_conformance import HTTPEndpoint
        print("\n" + "-" * 70)
        print("Conformance (over HTTP, WCP/0.2)")
        print("-" * 70)
        conf_report = ConformanceRunnerV02(
            HTTPEndpoint(url), label=url,
            expect_version="0.2").run()
        status = "PASS" if conf_report.passed else "FAIL"
        print(f"  {status} ({conf_report.passed_count}/"
              f"{conf_report.total_count} checks)")
        (artifact_dir / "conformance.txt").write_text(conf_report.format())
        if not conf_report.passed:
            for c in conf_report.failures():
                print(f"    FAIL: {c.name}: {c.detail}")
            return 1

        # 3. Petition over HTTP, get a signed admission
        print("\n" + "-" * 70)
        print("Petition over HTTP (signed admission)")
        print("-" * 70)
        alice = create_identity("Alice")
        resp = _post(f"{url}/petition", {
            "petitioner_token": alice.token,
            "petitioner_name": alice.name,
            "passport_admissions": [],
            "message": "I bring a poem.",
        })
        print(f"  kind: {resp.get('kind')}")
        if resp.get("kind") != "admission" or "signature" not in resp:
            print("  ERROR: expected signed admission")
            return 1
        print(f"  subject_token: {resp['subject_token'][:16]}...")
        print(f"  signature:     {resp['signature'][:16]}...")

        # 4. Add to passport
        passport = PassportV2.new(alice).with_entry(PassportEntry(
            entity_id=resp["entity_id"],
            timestamp=resp["timestamp"],
            subject_token=resp["subject_token"],
            signature=resp["signature"],
        ))

        # 5. Verify offline via manifest fetch
        print("\n" + "-" * 70)
        print("Passport verification (ManifestResolver over HTTP)")
        print("-" * 70)
        resolver = ManifestResolver({"world:poetry": url})
        vreport = passport.verify(resolver)
        print(vreport.format())
        if not vreport.all_verified:
            print("  ERROR: passport not fully verified")
            return 1

        # 6. Run the full multi-model collaboration in-process
        print("\n" + "-" * 70)
        print("Multi-model collaboration (in-process)")
        print("-" * 70)
        assignments = default_assignments(seed=42)
        coll_report = run_multi_model_collaboration(
            seed=42, assignments=assignments,
            max_iterations=20, signed=True,
        )
        print(f"  turns accepted:      {coll_report.turns_accepted()}")
        print(f"  signed acks:         "
              f"{getattr(coll_report, 'signed_acks_verified', 0)}/"
              f"{coll_report.turns_accepted()}")
        print(f"  total cost:          "
              f"${coll_report.total_cost_usd():.6f}")

        _save_report(coll_report, artifact_dir, assignments)

        print("\n" + "=" * 70)
        print("LIVE FEDERATION: SUCCESS")
        print("=" * 70)
        return 0

    finally:
        server.stop()


# =====================================================================
# Main
# =====================================================================

def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        prog="federation",
        description="Run the federation end-to-end.",
    )
    parser.add_argument("--mode", choices=["demo", "live"],
                        default="demo")
    parser.add_argument("--no-signed", action="store_true",
                        help="demo: skip signing (requires no crypto)")
    parser.add_argument("--artifact-dir", default="artifacts")
    args = parser.parse_args(argv)

    artifact_dir = make_artifact_dir(args.artifact_dir)
    print(f"Artifacts will be saved to: {artifact_dir}")

    if args.mode == "demo":
        return run_demo(artifact_dir, signed=not args.no_signed)
    return run_live(artifact_dir)


if __name__ == "__main__":
    sys.exit(main())

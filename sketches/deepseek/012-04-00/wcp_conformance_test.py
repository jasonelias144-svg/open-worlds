# wcp_conformance_test.py
import os
import tempfile
from multiverse_c3 import Act, Petition, Refusal, Ack
from multiverse_c4 import PoetryWorld
from multiverse_c5 import ChemistryWorld
from multiverse_c6 import MultiverseRegistry
from wcp_conformance_checks import (
    Check, Report,
    check_manifest_shape, check_manifest_version,
    check_manifest_entity_id_length, check_manifest_sub_registry,
    check_petition_response, check_act_response, check_log_shape,
)
from wcp_conformance import (
    ConformanceRunner, InProcessEndpoint, HTTPEndpoint, _manifest_dict,
)
from wcp_http_shim import WorldProtocolServer


def test_checks_pass_on_poetry_world():
    print("=== Checks pass on Poetry World ===")
    world = PoetryWorld("world:poetry", "The Poetry World")
    manifest = _manifest_dict(world.manifest())
    assert check_manifest_shape(manifest).passed
    assert check_manifest_version(manifest).passed
    assert check_manifest_entity_id_length(manifest).passed
    assert check_manifest_sub_registry(manifest).passed


def test_checks_pass_on_multiverse():
    print("=== Checks pass on Multiverse ===")
    mv = MultiverseRegistry("multiverse:main", "Main Multiverse")
    manifest = _manifest_dict(mv.manifest())
    assert check_manifest_shape(manifest).passed
    assert check_manifest_sub_registry(manifest).passed
    # A multiverse has a non-null sub_registry_endpoint
    assert manifest["sub_registry_endpoint"] is not None


def test_checks_fail_on_broken_manifest():
    print("=== Checks fail on broken manifest ===")
    # Missing fields
    bad = check_manifest_shape({"entity_id": "x"})
    assert not bad.passed
    print(f"  {bad.detail}")
    # Wrong version
    bad = check_manifest_version({"protocol_version": "WCX/0.2"})
    assert not bad.passed
    # Short entity_id
    bad = check_manifest_entity_id_length({"entity_id": "short"})
    assert not bad.passed


def test_petition_check_accepts_all_three_kinds():
    print("=== Petition check accepts all three kinds ===")
    for kind in ("admission", "refusal", "route"):
        payload = {"kind": kind}
        if kind == "admission":
            payload.update({"entity_id": "w", "timestamp": "t"})
        elif kind == "refusal":
            payload["reason"] = "no"
        else:
            payload["target_manifest"] = {"entity_id": "x"}
        c = check_petition_response(payload)
        assert c.passed, c.detail
    print("  ✓ admission, refusal, route all accepted")


def test_petition_check_rejects_unknown_kind():
    print("=== Petition check rejects unknown kind ===")
    bad = check_petition_response({"kind": "mystery"})
    assert not bad.passed


def test_full_in_process_run():
    print("=== Full in-process conformance run ===")
    for name, entity in [
        ("Poetry World", PoetryWorld("world:poetry", "The Poetry World")),
        ("Chemistry World", ChemistryWorld("world:chemistry", "Chemistry")),
        ("Multiverse", MultiverseRegistry("multiverse:main", "Main MV")),
    ]:
        runner = ConformanceRunner(
            InProcessEndpoint(entity), label=f"in-process:{name}")
        report = runner.run()
        print(f"  {name}: {report.passed_count}/{report.total_count} passed")
        assert report.passed, f"{name} failed: {report.format()}"


def test_full_http_run():
    print("=== Full HTTP conformance run ===")
    entity = PoetryWorld("world:poetry", "The Poetry World")
    server = WorldProtocolServer(entity, port=0)
    server.serve_in_thread()
    # Wait a beat for the server
    import time; time.sleep(0.1)
    try:
        port = server._httpd.server_address[1]
        runner = ConformanceRunner(
            HTTPEndpoint(f"http://127.0.0.1:{port}"),
            label=f"http://127.0.0.1:{port}")
        report = runner.run()
        print(f"  HTTP run: {report.passed_count}/{report.total_count} passed")
        assert report.passed, report.format()
    finally:
        server.stop()


def test_http_and_in_process_agree():
    """The most important test: both modes produce the same result."""
    print("=== HTTP and in-process agree ===")
    entity = ChemistryWorld("world:chemistry", "Chemistry")
    in_proc_report = ConformanceRunner(
        InProcessEndpoint(entity), label="in-process").run()
    server = WorldProtocolServer(entity, port=0)
    server.serve_in_thread()
    import time; time.sleep(0.1)
    try:
        port = server._httpd.server_address[1]
        http_report = ConformanceRunner(
            HTTPEndpoint(f"http://127.0.0.1:{port}"),
            label=f"http://127.0.0.1:{port}").run()
    finally:
        server.stop()
    # Same counts, same pass/fail
    assert in_proc_report.passed == http_report.passed
    assert in_proc_report.total_count == http_report.total_count
    assert in_proc_report.passed_count == http_report.passed_count
    print(f"  in-process: {in_proc_report.passed_count}/"
          f"{in_proc_report.total_count}")
    print(f"  http:       {http_report.passed_count}/"
          f"{http_report.total_count}")
    print("  → Identical behavior through both modes")


def test_broken_entity_fails():
    print("=== Broken entity fails conformance ===")

    class BrokenWorld:
        def manifest(self):
            return {"entity_id": "x"}  # missing everything

        def petition(self, p):
            return "yes"  # not a valid response type

        def act(self, a):
            return "ok"

        def log_since(self, ts=None):
            return None

    runner = ConformanceRunner(
        InProcessEndpoint(BrokenWorld()), label="broken")
    report = runner.run()
    print(f"  passed: {report.passed}, "
          f"failures: {len(report.failures())}")
    assert not report.passed
    assert len(report.failures()) >= 3


def test_cli_exit_codes():
    print("=== CLI exit codes ===")
    from wcp_conformance import main
    # Good entity
    code = main(["--in-process", "multiverse_c4:PoetryWorld",
                 "--quiet"])
    print(f"  poetry: exit={code}")
    assert code == 0
    # Bad entity
    code = main(["--in-process", "_nonexistent_module:Thing", "--quiet"])
    print(f"  bad:    exit={code}")
    assert code == 2


def test_cli_report_format():
    print("=== CLI report format ===")
    from wcp_conformance import main
    code = main(["--in-process", "multiverse_c6:MultiverseRegistry"])
    assert code == 0

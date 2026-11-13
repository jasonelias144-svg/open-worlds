# multiverse_c7_test.py
import os
import tempfile
from multiverse_c1 import create_identity
from multiverse_c3 import Ack, Refusal, Act
from multiverse_c4 import PoetryWorld
from multiverse_c6 import MultiverseRegistry
from multiverse_c7 import (
    make_client, petition_world, act_on_world,
    turn_to_act_payload, log_entry_to_turn,
    _demo_portfolio, CollaborationReport, FirstCollaboration,
)
from poetry_engine_c21 import Turn, TheoreticalStance


def test_client_petitions_and_acts():
    print("=== Client: petitions and acts ===")
    world = PoetryWorld("world:test", "Test World")
    client = make_client("Alice")
    r = petition_world(client, world)
    print(f"  petition: {type(r).__name__}")
    assert hasattr(r, "entity_id")
    # Now act
    ack = act_on_world(client, world, "poem.turn", {
        "acknowledgment": "(seed)",
        "proposal": "a line",
        "invitation": "what next?",
        "holds_open": True,
    })
    print(f"  act:      {type(ack).__name__}")
    assert isinstance(ack, Ack)


def test_unadmitted_client_cannot_act():
    print("=== Unadmitted client cannot act ===")
    world = PoetryWorld("world:test", "Test World")
    client = make_client("Alice")  # does NOT petition
    r = act_on_world(client, world, "poem.turn", {
        "acknowledgment": "(seed)",
        "proposal": "a line",
        "invitation": "?",
        "holds_open": True,
    })
    print(f"  response: {r}")
    assert isinstance(r, Refusal)
    assert "not admitted" in r.reason


def test_turn_adapter_roundtrip():
    print("=== Turn adapter roundtrip ===")
    turn = Turn(
        participant=None, round=0, line_count=3,
        acknowledgment="you said 'black'",
        proposal="the widow's web",
        invitation="what next?",
        holds_open=True,
        stance_used=TheoreticalStance.PSYCHOANALYTIC,
    )
    payload = turn_to_act_payload(turn)
    print(f"  payload: {payload}")
    # Simulate log entry containing payload
    from multiverse_c3 import LogEntry
    entry = LogEntry(
        timestamp="t", kind="turn",
        actor_token="x", data=payload,
    )
    reconstructed = log_entry_to_turn(entry)
    print(f"  reconstructed: stance={reconstructed.stance_used}")
    assert reconstructed.proposal == turn.proposal
    assert reconstructed.stance_used == TheoreticalStance.PSYCHOANALYTIC


def test_demo_portfolio():
    print("=== Demo portfolio ===")
    for name in ["Apprentice-A", "Apprentice-B", "Apprentice-C"]:
        p = _demo_portfolio(name)
        print(f"  {name}: {len(p)} poems, "
              f"first line {p[0].text[:40]!r}")
        assert 5 <= len(p) <= 10


def test_setup_admits_world_to_multiverse():
    print("=== Setup: World admitted to Multiverse ===")
    fc = FirstCollaboration(seed=42)
    fc.setup()
    print(f"  {fc.multiverse.describe()}")
    assert "world:poetry" in fc.multiverse.entity_ids()


def test_setup_trains_apprentices():
    print("=== Setup: Apprentices trained ===")
    fc = FirstCollaboration(seed=42)
    fc.setup()
    assert len(fc.apprentices) == 3
    for a in fc.apprentices:
        print(f"  {a.name}: {len(a.voice.portfolio)} poems, "
              f"{len(a.voice.stances)} stances")
        assert len(a.voice.portfolio) > 0
        assert len(a.voice.stances) == 8


def test_full_collaboration_runs():
    print("=== Full collaboration runs ===")
    fc = FirstCollaboration(seed=42)
    fc.setup()
    report = fc.run_collaboration(max_iterations=15)
    # Sanity
    n_turns = sum(1 for e in report.world_log if e["kind"] == "turn")
    print(f"  turns submitted: {n_turns}")
    print(f"  converged:       {report.converged}")
    print(f"  apprentices:     {[a['name'] for a in report.apprentices]}")
    assert n_turns >= 2, f"expected multiple turns, got {n_turns}"
    # Either converged or exhaust (both valid)
    assert isinstance(report.converged, bool)


def test_report_is_auditable():
    print("=== Report is auditable ===")
    fc = FirstCollaboration(seed=42)
    fc.setup()
    report = fc.run_collaboration(max_iterations=15)
    # Every turn in world_log should have a corresponding actor
    admitted_tokens = {
        e["actor_token"] for e in report.world_log
        if e["kind"] == "admission"
    }
    turn_tokens = {
        e["actor_token"] for e in report.world_log
        if e["kind"] == "turn"
    }
    print(f"  admitted identities: {len(admitted_tokens)}")
    print(f"  identities that turned: {len(turn_tokens)}")
    print(f"  turns ⊂ admitted: {turn_tokens <= admitted_tokens}")
    assert turn_tokens <= admitted_tokens


def test_report_roundtrip():
    print("=== Report: save and load ===")
    fc = FirstCollaboration(seed=42)
    fc.setup()
    report = fc.run_collaboration(max_iterations=10)
    with tempfile.TemporaryDirectory() as tmpdir:
        path = os.path.join(tmpdir, "collaboration.json")
        report.save(path)
        size = os.path.getsize(path)
        print(f"  saved: {size} bytes")
        loaded = CollaborationReport.load(path)
    print(f"  loaded: {len(loaded.world_log)} world entries")
    assert loaded.converged == report.converged
    assert loaded.world_entity_id == report.world_entity_id
    assert len(loaded.world_log) == len(report.world_log)
    assert loaded.final_collaboration_text == report.final_collaboration_text


def test_full_first_collaboration():
    print("=== THE FIRST COLLABORATION — full end to end ===\n")
    fc = FirstCollaboration(seed=42)
    fc.setup()
    report = fc.run_collaboration(max_iterations=20)
    print(report.report())
    # Verifications
    assert "world:poetry" in [e["kind"] for e in report.multiverse_log] \
        or any(e["data"].get("entity_id") == "world:poetry"
                for e in report.multiverse_log)
    n_admissions = sum(1 for e in report.world_log
                        if e["kind"] == "admission")
    n_turns = sum(1 for e in report.world_log if e["kind"] == "turn")
    print(f"\n  Verifications:")
    print(f"    admissions: {n_admissions} (expected ≥4: Jason + 3 apprentices)")
    print(f"    turns:      {n_turns} (expected ≥2)")
    assert n_admissions >= 4
    assert n_turns >= 2


if __name__ == "__main__":
    test_client_petitions_and_acts()
    test_unadmitted_client_cannot_act()
    test_turn_adapter_roundtrip()
    test_demo_portfolio()
    test_setup_admits_world_to_multiverse()
    test_setup_trains_apprentices()
    test_full_collaboration_runs()
    test_report_is_auditable()
    test_report_roundtrip()
    test_full_first_collaboration()

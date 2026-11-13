import json
import tempfile
import threading
import time
import urllib.error
import urllib.request
from pathlib import Path

import pytest

from multiverse_c3 import Ack, Refusal
from multiverse_c13 import HAS_CRYPTO
from multiverse_c83 import GovernedGrowingWorld
from multiverse_c87 import (
    PersistentLog, DaemonConfig, ParticipantConfig,
    WorldDaemon, _pid_alive,
    _save_participants, _load_participants,
    _make_participant,
    cmd_status, cmd_list, cmd_tail,
)


pytestmark = pytest.mark.skipif(
    not HAS_CRYPTO, reason="cryptography not installed")


# -- PersistentLog --

def test_persistent_log_writes_through(tmp_path):
    print("=== PersistentLog: writes through ===")
    from multiverse_c3 import LogEntry
    path = tmp_path / "log.jsonl"
    log = PersistentLog(path, initial=[])
    log.append(LogEntry(
        timestamp="t1", kind="test1", actor_token="a", data={}))
    log.append(LogEntry(
        timestamp="t2", kind="test2", actor_token="b", data={}))
    log.close()
    lines = path.read_text().splitlines()
    assert len(lines) == 2


def test_persistent_log_loads_existing(tmp_path):
    print("=== PersistentLog: loads existing ===")
    from multiverse_c3 import LogEntry
    path = tmp_path / "log.jsonl"
    path.write_text(
        json.dumps({"timestamp": "t1", "kind": "k",
                     "actor_token": None, "data": {}}) + "\n")
    log = PersistentLog(path)
    assert len(log) == 1
    assert log[0].kind == "k"


# -- Participant persistence --

def test_participants_roundtrip(tmp_path):
    print("=== Participants: save/load roundtrip ===")
    from multiverse_c1 import create_identity
    from multiverse_c86 import ModelDrivenParticipant, PersonaMockModel
    cfg = ParticipantConfig(
        name="Alice", persona="painter", seed=1)
    ident = create_identity("Alice")
    p = _make_participant(cfg, ident)
    path = tmp_path / "participants.json"
    _save_participants(path, [cfg], [p])
    loaded = _load_participants(path)
    assert loaded is not None
    assert len(loaded) == 1
    cfg2, ident2 = loaded[0]
    assert ident2.token == ident.token
    assert cfg2.name == cfg.name


# -- Daemon lifecycle (in-process) --

def _small_config(state_dir):
    return DaemonConfig(
        entity_id="world:test",
        name="Test",
        state_dir=str(state_dir),
        cycle_interval=0.05,
        curator_period=2,
        participants=[
            ParticipantConfig(
                name="Alice", persona="small",
                seed=1, claim_limit=2,
                fallback_claim_size=(2, 2),
                vote_preference="yes"),
            ParticipantConfig(
                name="Bob", persona="large",
                seed=2, claim_limit=1,
                fallback_claim_size=(25, 25),
                vote_preference="yes"),
        ],
    )


def test_daemon_runs_cycles(tmp_path):
    print("=== Daemon: runs cycles ===")
    daemon = WorldDaemon(_small_config(tmp_path))
    daemon.start()
    try:
        time.sleep(0.5)
        assert daemon._cycle_count >= 3
        assert len(daemon._world.current_plots()) >= 2
    finally:
        daemon.stop()


def test_daemon_persists_log(tmp_path):
    print("=== Daemon: persists log ===")
    daemon = WorldDaemon(_small_config(tmp_path))
    daemon.start()
    try:
        time.sleep(0.4)
    finally:
        daemon.stop()
    log_path = tmp_path / "world_log.jsonl"
    assert log_path.exists()
    assert len(log_path.read_text().splitlines()) > 1


def test_daemon_restarts_from_log(tmp_path):
    print("=== Daemon: restarts from persisted log ===")
    config = _small_config(tmp_path)
    d1 = WorldDaemon(config)
    d1.start()
    try:
        time.sleep(0.4)
        plots_before = len(d1._world.current_plots())
        cycles_before = d1._cycle_count
    finally:
        d1.stop()
    # Restart
    d2 = WorldDaemon(config)
    d2.start()
    try:
        # Same plots preserved
        assert len(d2._world.current_plots()) >= plots_before
        # Same participants
        assert len(d2._participants) == 2
    finally:
        d2.stop()


def test_daemon_status():
    print("=== Daemon: status() ===")
    import tempfile
    with tempfile.TemporaryDirectory() as tmp:
        daemon = WorldDaemon(_small_config(Path(tmp)))
        daemon.start()
        try:
            s = daemon.status()
            assert s["entity_id"] == "world:test"
            assert s["cycle_count"] >= 0
            assert "law" in s
            assert s["law"]["max_width"] == 20
        finally:
            daemon.stop()


def test_daemon_history():
    print("=== Daemon: history() ===")
    import tempfile
    with tempfile.TemporaryDirectory() as tmp:
        daemon = WorldDaemon(_small_config(Path(tmp)))
        daemon.start()
        try:
            time.sleep(0.3)
            hist = daemon.history()
            assert len(hist) >= 2
            assert "cycle" in hist[0]
        finally:
            daemon.stop()


# -- CLI helpers --

def test_pid_alive_self():
    print("=== _pid_alive: self ===")
    import os
    assert _pid_alive(os.getpid())


def test_pid_alive_nonexistent():
    print("=== _pid_alive: nonexistent ===")
    assert not _pid_alive(99999999)


# -- Full demo --

def test_demo(tmp_path):
    print("=== Demo: two daemons, restart ===")
    audit = demo(artifact_dir=str(tmp_path))
    assert audit["world_a"]["state_preserved"] is True
    assert audit["world_b"]["alive_after_a_stopped"] is True


from multiverse_c87 import demo

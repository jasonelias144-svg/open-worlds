import json
import tempfile
import time
import urllib.request
import urllib.error
from pathlib import Path

import pytest

from multiverse_c1 import create_identity
from multiverse_c3 import Ack, Refusal
from multiverse_c4 import PoetryWorld
from multiverse_c5 import ChemistryWorld
from multiverse_c13 import HAS_CRYPTO, KeyPair
from multiverse_c55 import (
    WorldCurator, CuratorMessage, WorldLink,
    CuratorLogEntry, verify_curator_message,
    MockCuratorModel,
)
from multiverse_c68 import (
    PeerRegistry, CuratorServer, CuratorHTTPClient,
    CuratorStore, CuratorProcess,
    _ack_or_refusal_to_dict, _keypair_to_hex, _keypair_from_hex,
    demo,
)


pytestmark = pytest.mark.skipif(
    not HAS_CRYPTO, reason="cryptography not installed")


# =====================================================================
# Helpers
# =====================================================================

def _make_curator():
    world = PoetryWorld("world:p", "P")
    kp = KeyPair.generate()
    return WorldCurator(world, kp), kp, world


def _make_peers(*pairs):
    """pairs = (world_id, url, public_key) tuples."""
    reg = PeerRegistry()
    for wid, url, pk in pairs:
        reg.add(wid, url, pk)
    return reg


# =====================================================================
# PeerRegistry
# =====================================================================

def test_peer_registry_add_get():
    print("=== PeerRegistry: add and get ===")
    reg = PeerRegistry()
    kp = KeyPair.generate()
    reg.add("world:a", "http://a", kp.public_key_hex())
    assert reg.get("world:a") is not None
    assert reg.get("world:b") is None
    assert len(reg) == 1


def test_peer_registry_validates():
    print("=== PeerRegistry: validates fields ===")
    reg = PeerRegistry()
    with pytest.raises(ValueError):
        reg.add("", "http://a", "aa" * 32)
    with pytest.raises(ValueError):
        reg.add("world:a", "", "aa" * 32)
    with pytest.raises(ValueError):
        reg.add("world:a", "http://a", "short")


def test_peer_registry_roundtrip():
    print("=== PeerRegistry: JSON roundtrip ===")
    kp = KeyPair.generate()
    reg = PeerRegistry()
    reg.add("world:a", "http://a", kp.public_key_hex())
    d = reg.to_dict()
    reg2 = PeerRegistry.from_dict(d)
    assert reg2.get("world:a") == reg.get("world:a")


# =====================================================================
# CuratorServer
# =====================================================================

def test_server_manifest():
    print("=== CuratorServer: /curator/manifest ===")
    curator, kp, _ = _make_curator()
    peers = PeerRegistry()
    server = CuratorServer(curator, peers, port=0)
    server.start()
    try:
        with urllib.request.urlopen(
                f"{server.url}/curator/manifest",
                timeout=5) as r:
            m = json.loads(r.read().decode())
        assert m["world_id"] == "world:p"
        assert m["public_key"] == kp.public_key_hex()
    finally:
        server.stop()


def test_server_accepts_valid_hello():
    print("=== CuratorServer: valid hello → Ack ===")
    sender_curator, sender_kp, _ = _make_curator()
    receiver_curator, _, _ = _make_curator()
    peers = PeerRegistry()
    peers.add("world:p", "http://sender",
              sender_kp.public_key_hex())
    server = CuratorServer(receiver_curator, peers, port=0)
    server.start()
    try:
        hello_msg = sender_curator.hello("world:p")
        req = urllib.request.Request(
            f"{server.url}/curator/message",
            data=json.dumps(hello_msg.to_dict()).encode(),
            headers={"Content-Type": "application/json"},
            method="POST")
        with urllib.request.urlopen(req, timeout=5) as r:
            resp = json.loads(r.read().decode())
        assert resp["kind"] == "ack"
        # Receiver's pending_hellos should have it
        assert "world:p" in receiver_curator._pending_hellos
    finally:
        server.stop()


def test_server_rejects_unknown_peer():
    print("=== CuratorServer: unknown peer → Refusal ===")
    sender_curator, _, _ = _make_curator()
    receiver_curator, _, _ = _make_curator()
    peers = PeerRegistry()  # empty
    server = CuratorServer(receiver_curator, peers, port=0)
    server.start()
    try:
        hello_msg = sender_curator.hello("world:unused")
        req = urllib.request.Request(
            f"{server.url}/curator/message",
            data=json.dumps(hello_msg.to_dict()).encode(),
            headers={"Content-Type": "application/json"},
            method="POST")
        with urllib.request.urlopen(req, timeout=5) as r:
            resp = json.loads(r.read().decode())
        assert resp["kind"] == "refusal"
        assert "unknown peer" in resp["reason"]
    finally:
        server.stop()


def test_server_rejects_wrong_key():
    print("=== CuratorServer: wrong key → Refusal ===")
    sender_curator, _, _ = _make_curator()
    receiver_curator, _, _ = _make_curator()
    wrong_kp = KeyPair.generate()
    peers = PeerRegistry()
    # Register a DIFFERENT public key than the sender signs with
    peers.add("world:p", "http://sender",
              wrong_kp.public_key_hex())
    server = CuratorServer(receiver_curator, peers, port=0)
    server.start()
    try:
        hello_msg = sender_curator.hello("world:p")
        req = urllib.request.Request(
            f"{server.url}/curator/message",
            data=json.dumps(hello_msg.to_dict()).encode(),
            headers={"Content-Type": "application/json"},
            method="POST")
        with urllib.request.urlopen(req, timeout=5) as r:
            resp = json.loads(r.read().decode())
        assert resp["kind"] == "refusal"
        assert "signature" in resp["reason"].lower()
    finally:
        server.stop()


def test_server_rejects_malformed():
    print("=== CuratorServer: malformed → Refusal ===")
    curator, _, _ = _make_curator()
    peers = PeerRegistry()
    server = CuratorServer(curator, peers, port=0)
    server.start()
    try:
        req = urllib.request.Request(
            f"{server.url}/curator/message",
            data=b"not json",
            headers={"Content-Type": "application/json"},
            method="POST")
        with urllib.request.urlopen(req, timeout=5) as r:
            resp = json.loads(r.read().decode())
        assert resp["kind"] == "refusal"
    finally:
        server.stop()


def test_server_404():
    print("=== CuratorServer: unknown path → 404 ===")
    curator, _, _ = _make_curator()
    peers = PeerRegistry()
    server = CuratorServer(curator, peers, port=0)
    server.start()
    try:
        with pytest.raises(urllib.error.HTTPError):
            urllib.request.urlopen(
                f"{server.url}/unknown", timeout=5)
    finally:
        server.stop()


# =====================================================================
# CuratorHTTPClient
# =====================================================================

def test_client_deliver_happy():
    print("=== CuratorHTTPClient: deliver to live server ===")
    sender_curator, sender_kp, _ = _make_curator()
    receiver_curator, _, _ = _make_curator()
    peers = PeerRegistry()
    peers.add("world:p", "http://sender",
              sender_kp.public_key_hex())
    server = CuratorServer(receiver_curator, peers, port=0)
    server.start()
    try:
        client = CuratorHTTPClient(server.url)
        msg = sender_curator.hello("world:p")
        ok, reason = client.deliver(msg)
        assert ok, reason
    finally:
        server.stop()


def test_client_deliver_dead_server():
    print("=== CuratorHTTPClient: deliver to dead server ===")
    sender_curator, _, _ = _make_curator()
    client = CuratorHTTPClient("http://127.0.0.1:1")
    msg = sender_curator.hello("world:p")
    ok, reason = client.deliver(msg)
    assert not ok
    assert "network" in reason.lower() or "refused" in reason.lower()


def test_client_fetch_manifest():
    print("=== CuratorHTTPClient: fetch manifest ===")
    curator, _, _ = _make_curator()
    peers = PeerRegistry()
    server = CuratorServer(curator, peers, port=0)
    server.start()
    try:
        client = CuratorHTTPClient(server.url)
        m = client.fetch_manifest()
        assert m is not None
        assert m["world_id"] == "world:p"
    finally:
        server.stop()


# =====================================================================
# CuratorStore
# =====================================================================

def test_store_identity_roundtrip(tmp_path):
    print("=== CuratorStore: identity roundtrip ===")
    store = CuratorStore(tmp_path)
    kp = KeyPair.generate()
    store.save_identity("world:p", kp)
    loaded = store.load_identity()
    assert loaded is not None
    assert loaded[0] == "world:p"
    assert loaded[1].public_key_hex() == kp.public_key_hex()


def test_store_links_roundtrip(tmp_path):
    print("=== CuratorStore: links roundtrip ===")
    store = CuratorStore(tmp_path)
    a_curator, a_kp, _ = _make_curator()
    b_curator, b_kp, _ = _make_curator()
    hello_a = a_curator.hello("world:b")
    hello_b = b_curator.hello("world:p")
    link = WorldLink(
        hello_a=hello_a, hello_b=hello_b,
        established_at="2024-01-01T00:00:00+00:00")
    store.save_links([link])
    loaded = store.load_links()
    assert len(loaded) == 1
    assert loaded[0].world_a_id() == "world:p"


def test_store_proposals_roundtrip(tmp_path):
    print("=== CuratorStore: proposals roundtrip ===")
    store = CuratorStore(tmp_path)
    store.append_proposal({"payload": {"title": "Test"}})
    props = store.read_proposals()
    assert len(props) == 1
    assert props[0]["proposal"]["payload"]["title"] == "Test"


def test_store_log_roundtrip(tmp_path):
    print("=== CuratorStore: log roundtrip ===")
    store = CuratorStore(tmp_path)
    entry = CuratorLogEntry(
        timestamp="t", kind="test",
        actor_world_id="world:p", data={"x": 1})
    store.append_log(entry)
    log = store.read_log()
    assert len(log) == 1
    assert log[0]["kind"] == "test"


# =====================================================================
# CuratorProcess: tick
# =====================================================================

def test_process_tick_no_peers(tmp_path):
    print("=== CuratorProcess: tick with no peers ===")
    world = PoetryWorld("world:p", "P")
    kp = KeyPair.generate()
    proc = CuratorProcess(
        world=world, world_kp=kp, peers=PeerRegistry(),
        state_dir=tmp_path, cycle_interval=0.1)
    result = proc.tick()
    assert result["tick"] == 1
    # No peers → no hello actions
    hello_actions = [
        a for a in result["actions"]
        if a["kind"].startswith("hello")]
    assert hello_actions == []


def test_process_tick_initiates_hello(tmp_path):
    print("=== CuratorProcess: tick initiates hello to peer ===")
    a_world = PoetryWorld("world:a", "A")
    a_kp = KeyPair.generate()
    b_world = PoetryWorld("world:b", "B")
    b_kp = KeyPair.generate()

    b_peers = PeerRegistry()
    b_proc = CuratorProcess(
        world=b_world, world_kp=b_kp,
        peers=b_peers, state_dir=tmp_path / "b")
    b_proc.start()
    try:
        a_peers = PeerRegistry()
        a_peers.add("world:b", b_proc.url,
                    b_kp.public_key_hex())
        a_proc = CuratorProcess(
            world=a_world, world_kp=a_kp,
            peers=a_peers, state_dir=tmp_path / "a")
        result = a_proc.tick()
        hello_actions = [
            a for a in result["actions"]
            if a["kind"] == "hello_sent"]
        assert len(hello_actions) == 1
        assert hello_actions[0]["ok"]
    finally:
        b_proc.stop()


def test_process_two_procs_converge(tmp_path):
    print("=== CuratorProcess: two processes converge to link ===")
    a_world = PoetryWorld("world:a", "A")
    a_kp = KeyPair.generate()
    b_world = PoetryWorld("world:b", "B")
    b_kp = KeyPair.generate()

    a_peers = PeerRegistry()
    b_peers = PeerRegistry()

    a_proc = CuratorProcess(
        world=a_world, world_kp=a_kp,
        peers=a_peers, state_dir=tmp_path / "a")
    b_proc = CuratorProcess(
        world=b_world, world_kp=b_kp,
        peers=b_peers, state_dir=tmp_path / "b")
    a_proc.start()
    b_proc.start()
    try:
        # Now both URLs known
        a_peers.add("world:b", b_proc.url,
                    b_kp.public_key_hex())
        b_peers.add("world:a", a_proc.url,
                    a_kp.public_key_hex())
        # Tick both a few times
        linked_at = None
        for i in range(10):
            a_proc.tick()
            b_proc.tick()
            if len(a_proc.links()) > 0 and len(b_proc.links()) > 0:
                linked_at = i
                break
        assert linked_at is not None, (
            f"never linked. a_links={a_proc.links()}, "
            f"b_links={b_proc.links()}")
    finally:
        a_proc.stop()
        b_proc.stop()


def test_process_proposal_generated(tmp_path):
    print("=== CuratorProcess: proposal generated on refusals ===")
    from multiverse_c3 import Act
    world = PoetryWorld("world:p", "P")
    kp = KeyPair.generate()
    proc = CuratorProcess(
        world=world, world_kp=kp, peers=PeerRegistry(),
        state_dir=tmp_path, cycle_interval=0.1)
    # Admit an actor and generate refusals
    from multiverse_c3 import Petition
    ident = create_identity("R")
    world.petition(Petition(
        petitioner_token=ident.token,
        petitioner_name=ident.name,
        passport_admissions=(), message="hi"))
    for _ in range(3):
        world.act(Act(
            actor_token=ident.token, type="poem.turn",
            payload={
                "acknowledgment": "",  # missing
                "proposal": "x", "invitation": "y",
                "holds_open": True,
            }))
    result = proc.tick()
    proposals = [
        a for a in result["actions"]
        if a["kind"] == "proposal_generated"]
    assert len(proposals) == 1
    # And persisted
    assert len(proc.store.read_proposals()) == 1


# =====================================================================
# CuratorProcess: lifecycle
# =====================================================================

def test_process_start_stop(tmp_path):
    print("=== CuratorProcess: start and stop ===")
    world = PoetryWorld("world:p", "P")
    kp = KeyPair.generate()
    proc = CuratorProcess(
        world=world, world_kp=kp, peers=PeerRegistry(),
        state_dir=tmp_path, cycle_interval=0.1)
    proc.start()
    assert proc._running
    url = proc.url
    # Server responds
    with urllib.request.urlopen(
            f"{url}/curator/manifest", timeout=5) as r:
        assert r.status == 200
    proc.stop()
    assert not proc._running
    # Server down
    time.sleep(0.1)
    with pytest.raises(Exception):
        urllib.request.urlopen(
            f"{url}/curator/manifest", timeout=1)


def test_process_identity_persisted(tmp_path):
    print("=== CuratorProcess: identity persisted on start ===")
    world = PoetryWorld("world:p", "P")
    kp = KeyPair.generate()
    proc = CuratorProcess(
        world=world, world_kp=kp, peers=PeerRegistry(),
        state_dir=tmp_path)
    proc.start()
    try:
        loaded = proc.store.load_identity()
        assert loaded is not None
        assert loaded[0] == "world:p"
        assert loaded[1].public_key_hex() == kp.public_key_hex()
    finally:
        proc.stop()


# =====================================================================
# Helpers
# =====================================================================

def test_ack_or_refusal_to_dict():
    print("=== _ack_or_refusal_to_dict ===")
    d = _ack_or_refusal_to_dict(
        Ack(entity_id="w", timestamp="t"))
    assert d["kind"] == "ack"
    d = _ack_or_refusal_to_dict(Refusal(reason="no"))
    assert d["kind"] == "refusal"
    assert d["reason"] == "no"


def test_keypair_hex_roundtrip():
    print("=== _keypair_to_hex / _keypair_from_hex roundtrip ===")
    kp = KeyPair.generate()
    h = _keypair_to_hex(kp)
    kp2 = _keypair_from_hex(h)
    assert kp.public_key_hex() == kp2.public_key_hex()


# =====================================================================
# Never raises
# =====================================================================

def test_scheduler_never_crashes_on_errors(tmp_path):
    print("=== Scheduler: swallows per-tick errors ===")
    world = PoetryWorld("world:p", "P")
    kp = KeyPair.generate()
    peers = PeerRegistry()
    # Add a peer that doesn't exist
    peers.add("world:ghost", "http://127.0.0.1:1",
              KeyPair.generate().public_key_hex())
    proc = CuratorProcess(
        world=world, world_kp=kp, peers=peers,
        state_dir=tmp_path, cycle_interval=0.05)
    proc.start()
    # Let a few cycles run
    time.sleep(0.2)
    proc.stop()
    # Should still be able to check state
    assert proc.store.read_log() is not None


# =====================================================================
# Demo
# =====================================================================

def test_demo(tmp_path):
    print("=== Demo: two curators, one federation ===")
    audit = demo(artifact_dir=str(tmp_path))
    assert audit["ticks_until_linked"] is not None
    assert audit["poetry_link_count"] == 1
    assert audit["chemistry_link_count"] == 1
    assert audit["refusals_submitted"] == 3
    assert audit["proposal_count"] >= 1
    assert audit["persisted"]["poetry_identity_loaded"] is True
    assert audit["server_shut_down"] is True


if __name__ == "__main__":
    test_peer_registry_add_get()
    test_peer_registry_validates()
    test_peer_registry_roundtrip()
    test_server_manifest()
    test_server_accepts_valid_hello()
    test_server_rejects_unknown_peer()
    test_server_rejects_wrong_key()
    test_server_rejects_malformed()
    test_server_404()
    test_client_deliver_happy()
    test_client_deliver_dead_server()
    test_client_fetch_manifest()
    test_ack_or_refusal_to_dict()
    test_keypair_hex_roundtrip()
    with tempfile.TemporaryDirectory() as tmp:
        test_store_identity_roundtrip(Path(tmp))
    with tempfile.TemporaryDirectory() as tmp:
        test_store_links_roundtrip(Path(tmp))
    with tempfile.TemporaryDirectory() as tmp:
        test_store_proposals_roundtrip(Path(tmp))
    with tempfile.TemporaryDirectory() as tmp:
        test_store_log_roundtrip(Path(tmp))
    with tempfile.TemporaryDirectory() as tmp:
        test_process_tick_no_peers(Path(tmp))
    with tempfile.TemporaryDirectory() as tmp:
        test_process_tick_initiates_hello(Path(tmp))
    with tempfile.TemporaryDirectory() as tmp:
        test_process_two_procs_converge(Path(tmp))
    with tempfile.TemporaryDirectory() as tmp:
        test_process_proposal_generated(Path(tmp))
    with tempfile.TemporaryDirectory() as tmp:
        test_process_start_stop(Path(tmp))
    with tempfile.TemporaryDirectory() as tmp:
        test_process_identity_persisted(Path(tmp))
    with tempfile.TemporaryDirectory() as tmp:
        test_scheduler_never_crashes_on_errors(Path(tmp))

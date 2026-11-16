import pytest
from personal_world import (
    HomeRoom, PortLanding, Bookmark, verify_home, HAS_CRYPTO)
from chat_room import (
    ChatRoom, RoomTemplate, sign_join_request, sign_transcript,
    verify_room, _did_from_kp)
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey)

pytestmark = pytest.mark.skipif(
    not HAS_CRYPTO, reason="cryptography not installed")


def _kp():
    return Ed25519PrivateKey.generate()


def _home():
    return HomeRoom(_kp(), "test home")


def _room():
    return ChatRoom(RoomTemplate(
        template_id="t", topic="test",
        join_policy="open", moderation="moderator"), _kp())


# -- Personal flag --

def test_home_is_personal():
    home = _home()
    assert home.template.personal is True


def test_home_refuses_other_key():
    home = _home()
    other = _kp()
    req = sign_join_request(home.world_id, other, "communicate")
    r = home.join(req)
    assert r.reason == "personal_room"


def test_home_refuses_second_copy_of_seed():
    home = _home()
    # Seed key is already a member; joining again is refused
    req = sign_join_request(home.world_id, home._user_kp,
                             "communicate")
    r = home.join(req)
    # Either already_member or personal_room — both fine
    assert "member" in r.reason or "personal" in r.reason


# -- Journal and draft --

def test_journal():
    home = _home()
    home.journal("first note")
    assert len(home.journals()) == 1
    assert home.journals()[0].kind == "journal"


def test_draft():
    home = _home()
    d = home.draft("hello", target_room="did:key:room")
    assert d.kind == "draft"
    assert "draft→did:key:room" in d.text


def test_home_verifies():
    home = _home()
    home.journal("a")
    home.draft("b", target_room="did:key:r")
    ok, r = verify_home(home)
    assert ok, r


# -- Ports --

def test_port_journal():
    home = _home()
    t = sign_transcript("app", [{"speaker": "u", "text": "hi"}],
                        home._user_kp)
    p = home.port(t, intent="journal")
    assert p.intent == "journal"
    assert p.target_room is None


def test_port_to_room_requires_target():
    home = _home()
    t = sign_transcript("app", [{"speaker": "u", "text": "hi"}],
                        home._user_kp)
    with pytest.raises(ValueError):
        home.port(t, intent="room")


def test_port_verifies():
    home = _home()
    t = sign_transcript("app", [{"speaker": "u", "text": "hi"}],
                        home._user_kp)
    home.port(t, intent="room", target_room="did:key:r")
    ok, r = verify_home(home)
    assert ok, r


def test_port_rejects_tampered_transcript():
    home = _home()
    t = sign_transcript("app", [{"speaker": "u", "text": "hi"}],
                        home._user_kp)
    # Tamper the transcript's sig
    bad = type(t)(source_label=t.source_label,
                  entries=t.entries,
                  porter_id=t.porter_id, ts=t.ts,
                  sig="00" * 64)
    with pytest.raises(ValueError):
        home.port(bad)


# -- Bookmarks --

def test_bookmark():
    home = _home()
    room = _room()
    home.bookmark(room, note="good")
    bms = home.bookmarks()
    assert len(bms) == 1
    assert bms[0].room_id == room.world_id


# -- Presence --

def test_presence():
    home = _home()
    home.announce_presence(["did:key:room1", "did:key:room2"], ttl=60)
    p = home.presence()
    assert p is not None
    assert "did:key:room1" in p["rooms"]
    assert p["ttl"] == 60


# -- Committing to a room --

def test_commit_draft_to_room():
    home = _home()
    d = home.draft("hello", target_room="did:key:r")
    room = _room()
    # Alice joins (user key)
    room.join(sign_join_request(room.world_id, home._user_kp,
                                 "communicate"))
    m = home.commit_draft_to_room(d.record_hash(), room)
    assert m is not None
    assert d.record_hash()[:16] in m.text


def test_commit_port_to_room():
    home = _home()
    t = sign_transcript("app", [{"speaker": "u", "text": "hi"}],
                        home._user_kp)
    room = _room()
    p = home.port(t, intent="room", target_room=room.world_id)
    room.join(sign_join_request(room.world_id, home._user_kp,
                                 "communicate"))
    m = home.commit_port_to_room(p.record_hash(), room)
    assert m is not None
    assert p.record_hash()[:16] in m.text


def test_cross_reference_verifies():
    """The room's message references the home's record; both
    logs verify; the reference matches."""
    home = _home()
    d = home.draft("hello")
    room = _room()
    room.join(sign_join_request(room.world_id, home._user_kp,
                                 "communicate"))
    m = home.commit_draft_to_room(d.record_hash(), room)
    assert m.record_hash() == room.records()[-1].record_hash()
    # Extract the home_ref
    ref = m.text.split("home_ref=")[1][:16]
    found = any(r.record_hash().startswith(ref)
                for r in home.records())
    assert found
    # Both logs verify
    ok_h, _ = verify_home(home)
    ok_r, _ = verify_room(room)
    assert ok_h and ok_r


# -- Export --

def test_export_is_portable():
    home = _home()
    home.journal("a")
    home.journal("b")
    export = home.export_log()
    assert export["world_id"] == home.world_id
    assert len(export["records"]) == len(home.records())
    # Every record has type, hash, body
    for r in export["records"]:
        assert "type" in r and "hash" in r and "body" in r


# -- Forbidden types --

def test_home_refuses_join_records():
    """The home's law forbids joins. A home that somehow
    acquired a join record would fail verification."""
    home = _home()
    # Inject a Join record directly (simulating tampering)
    from chat_room import Join
    body = {"type": "join", "world_id": home.world_id,
            "seq": home._seq, "prev": home._last_hash,
            "subject_id": "did:key:other", "tier": "communicate",
            "is_ai": False, "ts": "2026-01-01"}
    fake_join = Join(
        world_id=home.world_id, seq=home._seq,
        prev=home._last_hash,
        subject_id="did:key:other",
        tier="communicate", is_ai=False,
        ts=body["ts"], sig_subject="00" * 64,
        sig_room="00" * 64)
    home._records.append(fake_join)
    ok, r = verify_home(home)
    assert not ok
    assert "forbidden" in r

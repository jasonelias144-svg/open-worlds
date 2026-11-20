import pytest
from chat_room import (
    RoomTemplate, ChatRoom, Commons, PluginSession,
    RoomCreated, Message, Join, Leave, Redact, Refusal,
    sign_join_request, sign_post_request,
    sign_redact_request, sign_transcript, verify_transcript,
    verify_room, verify_commons, visible_log,
    HAS_CRYPTO)
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey)

pytestmark = pytest.mark.skipif(
    not HAS_CRYPTO, reason="cryptography not installed")


def _kp():
    return Ed25519PrivateKey.generate()


def _template(**kw):
    defaults = dict(
        template_id="t", topic="test",
        max_msg_len=100,
        rate_limit_count=3, rate_limit_window=5,
        join_policy="open", moderation="moderator")
    defaults.update(kw)
    return RoomTemplate(**defaults)


def _room(**kw):
    return ChatRoom(_template(**kw), _kp())


# -- Creation --

def test_room_created_record():
    room = _room()
    assert len(room.records()) == 1
    assert isinstance(room.records()[0], RoomCreated)
    assert room.members()[room.world_id] == "terminal"


def test_room_verifies():
    room = _room()
    ok, r = verify_room(room)
    assert ok, r


# -- Join --

def test_open_join():
    room = _room()
    bob_kp = _kp()
    req = sign_join_request(room.world_id, bob_kp, "communicate")
    rec = room.join(req)
    assert isinstance(rec, Join)
    assert room.members()[rec.subject_id] == "communicate"


def test_join_invite_required():
    room = _room(join_policy="invite")
    bob_kp = _kp()
    req = sign_join_request(room.world_id, bob_kp, "communicate")
    rec = room.join(req)
    assert isinstance(rec, Refusal)
    assert rec.reason == "invite_required"


def test_join_already_member_refused():
    room = _room()
    bob_kp = _kp()
    req = sign_join_request(room.world_id, bob_kp, "communicate")
    room.join(req)
    rec = room.join(req)
    assert isinstance(rec, Refusal)
    assert rec.reason == "already_member"


def test_leave():
    room = _room()
    bob_kp = _kp()
    room.join(sign_join_request(room.world_id, bob_kp, "communicate"))
    leave = room.leave(bob_kp)
    assert isinstance(leave, Leave)
    assert leave.subject_id not in room.members()


# -- Post --

def test_post_by_member():
    room = _room()
    bob_kp = _kp()
    room.join(sign_join_request(room.world_id, bob_kp, "communicate"))
    rec = room.post(sign_post_request(room.world_id, bob_kp, "hi"))
    assert isinstance(rec, Message)
    assert rec.text == "hi"


def test_post_by_non_member_refused():
    room = _room()
    bob_kp = _kp()
    rec = room.post(sign_post_request(room.world_id, bob_kp, "hi"))
    assert isinstance(rec, Refusal)
    assert rec.reason == "not_a_member"


def test_post_by_observe_tier_refused():
    room = _room()
    bob_kp = _kp()
    room.join(sign_join_request(room.world_id, bob_kp, "observe"))
    rec = room.post(sign_post_request(room.world_id, bob_kp, "hi"))
    assert isinstance(rec, Refusal)
    assert rec.reason == "insufficient_tier"


def test_post_too_long_refused():
    room = _room(max_msg_len=10)
    bob_kp = _kp()
    room.join(sign_join_request(room.world_id, bob_kp, "communicate"))
    rec = room.post(sign_post_request(room.world_id, bob_kp,
                                       "x" * 50))
    assert isinstance(rec, Refusal)
    assert rec.reason == "message_too_long"


def test_rate_limit():
    room = _room(rate_limit_count=2, rate_limit_window=5)
    bob_kp = _kp()
    room.join(sign_join_request(room.world_id, bob_kp, "communicate"))
    room.post(sign_post_request(room.world_id, bob_kp, "1"))
    room.post(sign_post_request(room.world_id, bob_kp, "2"))
    rec = room.post(sign_post_request(room.world_id, bob_kp, "3"))
    assert isinstance(rec, Refusal)
    assert rec.reason == "rate_limit"


# -- Redact --

def test_author_can_redact_own():
    room = _room(moderation="author_only")
    bob_kp = _kp()
    room.join(sign_join_request(room.world_id, bob_kp, "communicate"))
    msg = room.post(sign_post_request(room.world_id, bob_kp, "oops"))
    rec = room.redact(sign_redact_request(
        room.world_id, bob_kp, msg.record_hash(), "my bad"))
    assert isinstance(rec, Redact)


def test_moderator_can_redact_other():
    room = _room(moderation="moderator")
    bob_kp = _kp()
    mod_kp = _kp()
    room.join(sign_join_request(room.world_id, mod_kp, "control"))
    room.join(sign_join_request(room.world_id, bob_kp, "communicate"))
    msg = room.post(sign_post_request(room.world_id, bob_kp, "spam"))
    rec = room.redact(sign_redact_request(
        room.world_id, mod_kp, msg.record_hash(), "spam"))
    assert isinstance(rec, Redact)


def test_non_moderator_cannot_redact_other():
    room = _room(moderation="moderator")
    bob_kp = _kp()
    alice_kp = _kp()
    room.join(sign_join_request(room.world_id, alice_kp, "communicate"))
    room.join(sign_join_request(room.world_id, bob_kp, "communicate"))
    msg = room.post(sign_post_request(room.world_id, bob_kp, "hi"))
    rec = room.redact(sign_redact_request(
        room.world_id, alice_kp, msg.record_hash(), "nope"))
    assert isinstance(rec, Refusal)
    assert rec.reason == "not_allowed"


def test_redact_visible_hides_text():
    room = _room(moderation="author_only")
    bob_kp = _kp()
    room.join(sign_join_request(room.world_id, bob_kp, "communicate"))
    msg = room.post(sign_post_request(room.world_id, bob_kp, "oops"))
    room.redact(sign_redact_request(
        room.world_id, bob_kp, msg.record_hash(), "my bad"))
    view = visible_log(room)
    msg_view = next(v for v in view if v.get("type") == "message")
    assert msg_view["redacted"]
    assert msg_view["text"] == "[redacted]"
    # But the underlying record is unchanged
    assert msg.text == "oops"


# -- Refusals in log --

def test_refusal_signed_and_in_log():
    room = _room()
    bob_kp = _kp()
    room.post(sign_post_request(room.world_id, bob_kp, "hi"))
    refusals = [r for r in room.records()
                if isinstance(r, Refusal)]
    assert len(refusals) == 1


# -- Verification --

def test_room_verifies_after_activity():
    room = _room()
    bob_kp = _kp()
    room.join(sign_join_request(room.world_id, bob_kp, "communicate"))
    room.post(sign_post_request(room.world_id, bob_kp, "hi"))
    ok, r = verify_room(room)
    assert ok, r


def test_room_detects_tampered_message():
    room = _room()
    bob_kp = _kp()
    room.join(sign_join_request(room.world_id, bob_kp, "communicate"))
    msg = room.post(sign_post_request(room.world_id, bob_kp, "hi"))
    # Replace the last record with a tampered version
    bad = Message(
        world_id=msg.world_id, seq=msg.seq, prev=msg.prev,
        author_id=msg.author_id, text="TAMPERED", ts=msg.ts,
        sig_author=msg.sig_author, sig_room=msg.sig_room)
    room._records[-1] = bad
    ok, r = verify_room(room)
    assert not ok


# -- Transcript --

def test_transcript_signed():
    kp = _kp()
    t = sign_transcript("test", [{"speaker": "a", "text": "hi"}], kp)
    assert verify_transcript(t)


def test_transcript_tampered_fails():
    kp = _kp()
    t = sign_transcript("test", [{"speaker": "a", "text": "hi"}], kp)
    bad = type(t)(
        source_label=t.source_label,
        entries=[{"speaker": "a", "text": "TAMPERED"}],
        porter_id=t.porter_id, ts=t.ts, sig=t.sig)
    assert not verify_transcript(bad)


# -- Commons --

def test_commons_registration():
    commons = Commons(_kp())
    alice = PluginSession(_kp(), "test")
    room = alice.create_room(commons, _template())
    assert room.world_id in commons.rooms()
    ok, r = verify_commons(commons)
    assert ok, r


# -- Plugin mediation --

def test_plugin_acts_as_user():
    """The plugin's user_id equals the user's did:key — the
    plugin has no separate authority."""
    kp = _kp()
    plugin = PluginSession(kp, "app")
    from chat_room import _did_from_kp
    assert plugin.user_id == _did_from_kp(kp)


def test_plugin_cannot_post_without_joining():
    """Even a properly-keyed plugin cannot post in a room it
    hasn't joined — the room's law applies to the user, not
    the plugin."""
    commons = Commons(_kp())
    alice = PluginSession(_kp(), "app")
    room = alice.create_room(commons, _template())
    bob = PluginSession(_kp(), "app")
    rec = bob.post_message(room, "hi")
    assert isinstance(rec, Refusal)
    assert rec.reason == "not_a_member"


# -- Demo --

def test_demo(tmp_path):
    from chat_room import demo
    audit = demo(artifact_dir=str(tmp_path))
    assert audit["room_verifies"]
    assert audit["commons_verifies"]
    assert audit["transcript_verifies"]
    # At least one redaction visible
    redacted = [v for v in audit["visible_log"]
                if v.get("type") == "message" and v.get("redacted")]
    assert len(redacted) >= 1

"""
personal_world.py — The home room.

Proposal sketch, not a course step. The home is the user's
personal world: a ChatRoom with `personal: True`, so only the
seed key can ever be a member. It is where the user journals,
drafts, ports conversations from external AI apps, and
bookmarks rooms.

Keeping the AOL lessons in mind:
  - No lock-in: the home is a signed chain, fully exportable.
  - No opacity: every action is signed by the user's key.
    The room has no moderator it didn't choose (it has none).
  - Identity travels: bound to did:key, not to any app.
  - Memory preserved: append-only. Redaction possible, editing
    not. The record stays.
  - Both modes: journaling (async) and quick capture (live)
    share one log, distinguished by `kind`.
  - Presence lives in the home, not in a Commons server.
    If the Commons vanished tomorrow, the home would still
    be complete.

Builds on chat_room. Adds two record types (PortLanding,
Bookmark) and the `personal` template flag.

Simplifications marked for the standard's review:

  - The home is plaintext. HPKE-sealed homes on a shared
    host are a future layer.
  - No persona keys yet. A user could hold multiple keys
    (one per unlinked presence); today the home is one.
  - No home succession. If a user loses their key, the home
    is lost (unless they exported it — which they can, and
    should). Home succession is a future piece analogous to
    moderator succession.
  - Presence records use the same Message type (kind=
    "presence") for now, rather than a dedicated record.
    A dedicated `presence` type would allow richer fields
    (rooms, ttl) without stuffing them into text; the
    sketch uses a small text encoding to keep the type
    count low.
  - Bookmarks and ports target rooms by did:key string. The
    verification does not check the room exists.
"""

import json
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple, Union

try:
    from cryptography.hazmat.primitives.asymmetric.ed25519 import (
        Ed25519PrivateKey, Ed25519PublicKey)
    from cryptography.hazmat.primitives import serialization
    HAS_CRYPTO = True
except ImportError:
    HAS_CRYPTO = False

from chat_room import (
    ChatRoom, RoomTemplate, Message, Join, Leave, Redact, Refusal,
    RoomCreated,
    sign_post_request, sign_join_request,
    sign_transcript, verify_transcript, Transcript,
    verify_room, visible_log,
    _did_from_kp, _pubkey_from_did, _canonical, _hash, _now,
    _verify_simple_sig)


# =====================================================================
# Home-specific records
# =====================================================================

@dataclass(frozen=True)
class PortLanding:
    world_id: str
    seq: int
    prev: Optional[str]
    transcript: Dict
    intent: str                  # "journal" | "room"
    target_room: Optional[str]
    ts: str
    sig: str

    def body(self):
        return {
            "type": "port_landing",
            "world_id": self.world_id,
            "seq": self.seq,
            "prev": self.prev,
            "transcript": dict(self.transcript),
            "intent": self.intent,
            "target_room": self.target_room,
            "ts": self.ts,
        }

    def record_hash(self):
        return _hash(self.body())


@dataclass(frozen=True)
class Bookmark:
    world_id: str
    seq: int
    prev: Optional[str]
    room_id: str
    note: str
    ts: str
    sig: str

    def body(self):
        return {
            "type": "bookmark",
            "world_id": self.world_id,
            "seq": self.seq,
            "prev": self.prev,
            "room_id": self.room_id,
            "note": self.note,
            "ts": self.ts,
        }

    def record_hash(self):
        return _hash(self.body())


# =====================================================================
# HomeRoom
# =====================================================================

class HomeRoom(ChatRoom):
    """The user's personal world. Only the seed key can ever be
    a member. Journals, drafts, ports, bookmarks — all signed by
    the user, all in one chain, all exportable."""

    def __init__(self, user_kp, display_name: str = "my home"):
        if not HAS_CRYPTO:
            raise RuntimeError("cryptography not installed")
        template = RoomTemplate(
            template_id="home-v1",
            topic=display_name,
            join_policy="invite",
            moderation="author_only",
            membership="human_only",
            mode="async",
            personal=True)
        super().__init__(template, user_kp)
        self._user_id = _did_from_kp(user_kp)
        self._user_kp = user_kp

    # -- Writing --------------------------------------------------

    def journal(self, text: str) -> Message:
        req = sign_post_request(self.world_id, self._user_kp,
                                 text, kind="journal")
        return self.post(req, kind="journal")

    def draft(self, text: str, target_room: Optional[str] = None) -> Message:
        prefix = (f"[draft→{target_room}] " if target_room
                  else "[draft] ")
        req = sign_post_request(self.world_id, self._user_kp,
                                 prefix + text, kind="draft")
        return self.post(req, kind="draft")

    def announce_presence(self, rooms: List[str],
                           ttl: int = 300) -> Message:
        """Presence lives in the home. The rooms list and ttl
        are encoded in the text as JSON. A dedicated record
        type is future work; a message is enough for now."""
        payload = {"rooms": list(rooms), "ttl": int(ttl)}
        req = sign_post_request(
            self.world_id, self._user_kp,
            json.dumps(payload, sort_keys=True),
            kind="presence")
        return self.post(req, kind="presence")

    def port(self, transcript: Transcript,
             intent: str = "journal",
             target_room: Optional[str] = None) -> PortLanding:
        if not verify_transcript(transcript):
            raise ValueError("transcript sig invalid")
        if intent not in ("journal", "room"):
            raise ValueError(f"unknown intent {intent!r}")
        if intent == "room" and not target_room:
            raise ValueError("intent 'room' requires target_room")
        body = {
            "type": "port_landing",
            "world_id": self.world_id,
            "seq": self._seq,
            "prev": self._last_hash,
            "transcript": {**transcript.body(), "sig": transcript.sig},
            "intent": intent,
            "target_room": target_room,
            "ts": _now(),
        }
        rec = PortLanding(
            world_id=self.world_id, seq=self._seq,
            prev=self._last_hash,
            transcript=body["transcript"],
            intent=intent, target_room=target_room,
            ts=body["ts"],
            sig=self._user_kp.sign(_canonical(body)).hex())
        self._append(rec)
        return rec

    def bookmark(self, room: ChatRoom, note: str = "") -> Bookmark:
        body = {
            "type": "bookmark",
            "world_id": self.world_id,
            "seq": self._seq,
            "prev": self._last_hash,
            "room_id": room.world_id,
            "note": note,
            "ts": _now(),
        }
        rec = Bookmark(
            world_id=self.world_id, seq=self._seq,
            prev=self._last_hash,
            room_id=room.world_id, note=note,
            ts=body["ts"],
            sig=self._user_kp.sign(_canonical(body)).hex())
        self._append(rec)
        return rec

    # -- Committing to a room ------------------------------------

    def commit_draft_to_room(self, draft_hash: str,
                              room: ChatRoom) -> Union[Message, Refusal]:
        """Post a draft to a room. The posted text includes
        a `home_ref` — the draft's hash — so the room's log
        cross-references the home."""
        draft = next((r for r in self._records
                      if r.record_hash() == draft_hash
                      and isinstance(r, Message)
                      and r.kind == "draft"), None)
        if draft is None:
            raise ValueError("draft not found")
        text = f"[home_ref={draft_hash[:16]}] {draft.text}"
        req = sign_post_request(room.world_id, self._user_kp,
                                 text, kind="normal")
        return room.post(req, kind="normal")

    def commit_port_to_room(self, port_hash: str,
                             room: ChatRoom) -> Union[Message, Refusal]:
        port = next((r for r in self._records
                     if r.record_hash() == port_hash
                     and isinstance(r, PortLanding)), None)
        if port is None:
            raise ValueError("port not found")
        if port.target_room and port.target_room != room.world_id:
            raise ValueError("port target_room mismatch")
        # The room's message carries the transcript entries and
        # a home_ref so the room's log cross-references the home.
        text = (f"[home_ref={port_hash[:16]}] "
                f"[ported from {port.transcript['source_label']}] "
                + json.dumps(port.transcript["entries"],
                             sort_keys=True))
        req = sign_post_request(room.world_id, self._user_kp,
                                 text, kind="port")
        return room.post(req, kind="port")

    # -- Views ----------------------------------------------------

    def journals(self) -> List[Message]:
        return [r for r in self._records
                if isinstance(r, Message) and r.kind == "journal"]

    def drafts(self) -> List[Message]:
        return [r for r in self._records
                if isinstance(r, Message) and r.kind == "draft"]

    def ports(self) -> List[PortLanding]:
        return [r for r in self._records
                if isinstance(r, PortLanding)]

    def bookmarks(self) -> List[Bookmark]:
        return [r for r in self._records
                if isinstance(r, Bookmark)]

    def presence(self) -> Optional[Dict]:
        """Latest presence record, if unexpired."""
        latest = None
        for r in self._records:
            if isinstance(r, Message) and r.kind == "presence":
                latest = r
        if latest is None:
            return None
        try:
            payload = json.loads(latest.text)
        except Exception:
            return None
        # ttl check would use wall clock in production
        return {"rooms": payload.get("rooms", []),
                "ttl": payload.get("ttl", 0),
                "ts": latest.ts}

    def export_log(self) -> Dict:
        """The whole home, as JSON. Portable. No lock-in."""
        return {
            "world_id": self.world_id,
            "template": self.template.to_dict(),
            "records": [
                {"type": type(r).__name__,
                 "hash": r.record_hash(),
                 "body": r.body()}
                for r in self._records
            ],
        }


# =====================================================================
# Verification
# =====================================================================

def verify_home(home: HomeRoom) -> Tuple[bool, str]:
    """Home-aware verification: handles RoomCreated, Message,
    PortLanding, Bookmark. Refuses any other type (the home's
    law forbids joins, leaves, and redacts — no other member
    can be a member)."""
    if not HAS_CRYPTO:
        return (False, "cryptography not installed")
    pub = _pubkey_from_did(home.world_id)
    prev = None
    for i, rec in enumerate(home.records()):
        if isinstance(rec, RoomCreated):
            if i != 0:
                return (False, f"record {i}: room_created "
                               f"not at start")
            try:
                _pubkey_from_did(rec.creator_id).verify(
                    bytes.fromhex(rec.sig_creator),
                    _canonical({k: v for k, v in
                                rec.body().items()
                                if k not in ("sig_creator",
                                             "sig_room")}))
            except Exception as e:
                return (False, f"record {i}: creator sig: {e}")
        elif isinstance(rec, Message):
            if rec.prev != prev:
                return (False, f"record {i}: prev mismatch")
            if not _verify_simple_sig(
                    {k: v for k, v in rec.body().items()},
                    rec.sig_author, rec.author_id):
                return (False, f"record {i}: author sig")
        elif isinstance(rec, PortLanding):
            if rec.prev != prev:
                return (False, f"record {i}: prev mismatch")
            if not _verify_simple_sig(
                    {k: v for k, v in rec.body().items()},
                    rec.sig, home.world_id):
                return (False, f"record {i}: sig invalid")
            t = rec.transcript
            t_body = {k: v for k, v in t.items() if k != "sig"}
            if not _verify_simple_sig(t_body, t["sig"],
                                       t["porter_id"]):
                return (False, f"record {i}: transcript sig")
            if rec.intent == "room" and not rec.target_room:
                return (False, f"record {i}: intent 'room' "
                               f"without target")
        elif isinstance(rec, Bookmark):
            if rec.prev != prev:
                return (False, f"record {i}: prev mismatch")
            if not _verify_simple_sig(
                    {k: v for k, v in rec.body().items()},
                    rec.sig, home.world_id):
                return (False, f"record {i}: sig invalid")
        else:
            return (False, f"record {i}: forbidden type "
                           f"{type(rec).__name__} in home")
        prev = rec.record_hash()
    return (True, "home verifies")

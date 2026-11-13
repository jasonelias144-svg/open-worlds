import json
import tempfile
from pathlib import Path

import pytest

from multiverse_c1 import create_identity
from multiverse_c3 import Act, Ack, Refusal, Petition
from multiverse_c73 import (
    HAS_CHESS, ChessWorld, ChessTable, demo,
)


pytestmark = pytest.mark.skipif(
    not HAS_CHESS, reason="python-chess not installed")


def _park_with(*names):
    park = ChessWorld("world:p", "P")
    idents = {}
    for n in names:
        ident = create_identity(n)
        park.petition(Petition(
            petitioner_token=ident.token,
            petitioner_name=ident.name,
            passport_admissions=(), message="hi"))
        idents[n] = ident
    return park, idents


def test_sit_and_fill_begins_game():
    print("=== Sit: two seats filled → game begins ===")
    park, ids = _park_with("Alice", "Bob")
    r1 = park.act(Act(actor_token=ids["Alice"].token,
                       type="chess.sit",
                       payload={"seat": "white"}))
    assert isinstance(r1, Ack)
    r2 = park.act(Act(actor_token=ids["Bob"].token,
                       type="chess.sit",
                       payload={"seat": "black"}))
    assert isinstance(r2, Ack)
    t = park.table_state()
    assert t["status"] == "in_progress"
    assert t["turn"] == "white"


def test_seat_taken_refused():
    print("=== Sit: seat taken → Refusal ===")
    park, ids = _park_with("Alice", "Bob", "Carol")
    park.act(Act(actor_token=ids["Alice"].token,
                  type="chess.sit", payload={"seat": "white"}))
    r = park.act(Act(actor_token=ids["Bob"].token,
                      type="chess.sit",
                      payload={"seat": "white"}))
    assert isinstance(r, Refusal)


def test_invite_and_accept():
    print("=== Invite + accept begins game ===")
    park, ids = _park_with("Alice", "Bob")
    park.act(Act(actor_token=ids["Alice"].token,
                  type="chess.sit", payload={"seat": "white"}))
    park.act(Act(actor_token=ids["Alice"].token,
                  type="chess.invite",
                  payload={"invitee_token": ids["Bob"].token,
                            "seat": "black"}))
    r = park.act(Act(actor_token=ids["Bob"].token,
                      type="chess.accept",
                      payload={"inviter_token":
                                ids["Alice"].token}))
    assert isinstance(r, Ack)
    t = park.table_state()
    assert t["status"] == "in_progress"
    assert t["black"] == ids["Bob"].token


def test_invite_requires_being_seated():
    print("=== Invite: not seated → Refusal ===")
    park, ids = _park_with("Alice", "Bob")
    r = park.act(Act(actor_token=ids["Alice"].token,
                      type="chess.invite",
                      payload={"invitee_token": ids["Bob"].token,
                                "seat": "black"}))
    assert isinstance(r, Refusal)


def test_decline():
    print("=== Decline: invitation removed ===")
    park, ids = _park_with("Alice", "Bob")
    park.act(Act(actor_token=ids["Alice"].token,
                  type="chess.sit", payload={"seat": "white"}))
    park.act(Act(actor_token=ids["Alice"].token,
                  type="chess.invite",
                  payload={"invitee_token": ids["Bob"].token,
                            "seat": "black"}))
    park.act(Act(actor_token=ids["Bob"].token,
                  type="chess.decline",
                  payload={"inviter_token": ids["Alice"].token}))
    t = park.table_state()
    assert len(t["pending_invitations"]) == 0


def test_watch_and_unwatch():
    print("=== Watch/unwatch: current_watchers reconstructs ===")
    park, ids = _park_with("Alice", "Carol")
    park.act(Act(actor_token=ids["Carol"].token,
                  type="chess.watch"))
    assert ids["Carol"].token in park.current_watchers()
    park.act(Act(actor_token=ids["Carol"].token,
                  type="chess.unwatch"))
    assert ids["Carol"].token not in park.current_watchers()


def test_move_turn_enforced():
    print("=== Move: not your turn → Refusal ===")
    park, ids = _park_with("Alice", "Bob")
    park.act(Act(actor_token=ids["Alice"].token,
                  type="chess.sit", payload={"seat": "white"}))
    park.act(Act(actor_token=ids["Bob"].token,
                  type="chess.sit", payload={"seat": "black"}))
    # Black tries to move on white's turn
    r = park.act(Act(actor_token=ids["Bob"].token,
                      type="chess.move",
                      payload={"from_sq": "e7", "to_sq": "e5"}))
    assert isinstance(r, Refusal)


def test_move_illegal_refused():
    print("=== Move: illegal → Refusal ===")
    park, ids = _park_with("Alice", "Bob")
    park.act(Act(actor_token=ids["Alice"].token,
                  type="chess.sit", payload={"seat": "white"}))
    park.act(Act(actor_token=ids["Bob"].token,
                  type="chess.sit", payload={"seat": "black"}))
    r = park.act(Act(actor_token=ids["Alice"].token,
                      type="chess.move",
                      payload={"from_sq": "e2", "to_sq": "e5"}))
    assert isinstance(r, Refusal)


def test_stand_during_play_forfeits():
    print("=== Stand during play: forfeit ===")
    park, ids = _park_with("Alice", "Bob")
    park.act(Act(actor_token=ids["Alice"].token,
                  type="chess.sit", payload={"seat": "white"}))
    park.act(Act(actor_token=ids["Bob"].token,
                  type="chess.sit", payload={"seat": "black"}))
    r = park.act(Act(actor_token=ids["Alice"].token,
                      type="chess.stand"))
    assert isinstance(r, Ack)
    t = park.table_state()
    assert t["status"] == "completed"
    assert "forfeit" in t["result"]


def test_demo(tmp_path):
    print("=== Demo: Scholar's Mate with a watcher ===")
    audit = demo(artifact_dir=str(tmp_path))
    assert audit["game_ended"] is True
    assert "checkmate" in audit["result"]
    assert len(audit["watchers"]) == 1  # Carol is still watching

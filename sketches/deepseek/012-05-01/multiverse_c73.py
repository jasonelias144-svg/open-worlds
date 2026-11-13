"""
multiverse_c73.py — Component 73: The Chess Park.

A WCP world with one table, two seats, and any number of watchers.

The Law of the park (nine act types, three families):

  Participation:
    chess.sit     {seat: "white" | "black"}
    chess.stand   {}
    chess.invite  {invitee_token, seat}
    chess.accept  {inviter_token}
    chess.decline {inviter_token}

  Play:
    chess.move    {from_sq, to_sq, promotion?}
    chess.resign  {}

  Witness:
    chess.watch   {}
    chess.unwatch {}

Every act is a signed artifact (C13). Every act appends to
the log (C3). Watching is a signed claim of attention — not a
permission and not a subscription — so the log records not just
the game but *who was there to see it*. That is what makes it
feel like a park.

Dependency: python-chess for move legality. This is the first
world in the arc with a non-stdlib runtime dependency. It is
documented as a dependency *of this world*, not of the
substrate: a different game world would use a different engine,
and a chess world with a different rules engine is still a
conforming WCP entity.

Honest limits:
  - One table only (v0.1). The park with many tables is a
    natural extension but not demonstrated here.
  - No draw offers, no clocks, no time controls. Chess rules
    only, not tournament rules.
  - Invitations are informational: a seated player can invite
    anyone, but anyone can also just sit down in an empty seat
    without an invitation. The invitation is a *social act*,
    not an *access control*.
  - A watcher who never unwatches stays visible in the log
    forever. There is no expiry; a reader sees the last
    watch/unwatch per identity to compute the current audience.
  - `stand` during play forfeits the game. This is the
    park's rule, not chess's. A v0.2 park could allow
    adjournment; this one does not.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Set, Tuple

import json

try:
    import chess  # python-chess
    HAS_CHESS = True
except ImportError:
    HAS_CHESS = False

from multiverse_c3 import (
    Manifest, Petition, Act, LogEntry,
    Admission as WCPAdmission, Refusal, Ack,
)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


# =====================================================================
# Table state
# =====================================================================

@dataclass
class ChessTable:
    """One table's state. In v0.1 there is exactly one."""
    white: Optional[str] = None            # identity token
    black: Optional[str] = None
    board: Optional[Any] = None            # chess.Board
    turn: str = "white"                    # "white" | "black"
    status: str = "open"                   # open | in_progress | completed
    result: Optional[str] = None           # e.g. "white by checkmate"
    # (inviter_token, invitee_token) -> seat
    invitations: Dict[Tuple[str, str], str] = field(
        default_factory=dict)
    # (invitee_token, inviter_token) -> status
    declined: Set[Tuple[str, str]] = field(default_factory=set)


# =====================================================================
# ChessWorld
# =====================================================================

class ChessWorld:
    """A WCP world that is a chess park.

    One table, two seats, any number of watchers. Chess rules
    are enforced via python-chess; park rules (invitation,
    standing, watching) are this world's own Law.
    """

    def __init__(self, entity_id: str = "world:park",
                 name: str = "The Chess Park"):
        if not HAS_CHESS:
            raise RuntimeError(
                "ChessWorld requires `python-chess` "
                "(pip install chess)")
        self._manifest = Manifest(
            entity_id=entity_id, name=name,
            protocol_version="WCP/0.2",
            law_url=f"park://{entity_id}/law",
            act_endpoint=f"park://{entity_id}/act",
            log_endpoint=f"park://{entity_id}/log",
            sub_registry_endpoint=None,
        )
        self._log: List[LogEntry] = []
        self._admitted: Dict[str, str] = {}
        self._table = ChessTable()

    # -- WCP interface -------------------------------------------

    def manifest(self) -> Manifest:
        return self._manifest

    def petition(self, petition: Petition):
        ts = _now()
        if petition.petitioner_token in self._admitted:
            return self._refuse(ts, petition.petitioner_token,
                                "Already admitted", "petition")
        self._admitted[petition.petitioner_token] = \
            petition.petitioner_name
        self._append("admission", petition.petitioner_token,
                     {"name": petition.petitioner_name})
        return WCPAdmission(
            entity_id=self._manifest.entity_id, timestamp=ts)

    def act(self, act: Act):
        if act.actor_token not in self._admitted:
            return self._refuse(
                _now(), act.actor_token,
                "Actor is not admitted", "act")
        handler = _HANDLERS.get(act.type)
        if handler is None:
            return self._refuse(
                _now(), act.actor_token,
                f"Unknown act type: {act.type}", "act")
        return handler(self, act)

    def log_since(self, since: Optional[str] = None):
        if since is None:
            return list(self._log)
        return [e for e in self._log if e.timestamp > since]

    # -- Read model ----------------------------------------------

    def table_state(self) -> Dict:
        t = self._table
        return {
            "white": t.white,
            "black": t.black,
            "status": t.status,
            "turn": t.turn,
            "fen": (t.board.fen() if t.board is not None
                    else None),
            "result": t.result,
            "pending_invitations": [
                {"from": inviter, "to": invitee, "seat": seat}
                for (inviter, invitee), seat
                in t.invitations.items()
                if (invitee, inviter) not in t.declined
            ],
        }

    def current_watchers(self) -> List[str]:
        """Reconstruct the current audience from the log.

        For each identity that ever sent chess.watch, its
        most recent watch/unwatch decides whether it is
        currently watching.
        """
        last: Dict[str, str] = {}
        for e in self._log:
            if e.kind in ("chess.watch", "chess.unwatch"):
                last[e.actor_token or ""] = e.kind
        return sorted(
            tok for tok, kind in last.items()
            if kind == "chess.watch")

    # -- Internals -----------------------------------------------

    def _append(self, kind: str, actor: Optional[str],
                 data: Dict) -> LogEntry:
        entry = LogEntry(
            timestamp=_now(), kind=kind,
            actor_token=actor, data=data)
        self._log.append(entry)
        return entry

    def _refuse(self, ts: str, actor: str, reason: str,
                 kind: str) -> Refusal:
        self._log.append(LogEntry(
            timestamp=ts, kind=f"{kind}_refused",
            actor_token=actor, data={"reason": reason}))
        return Refusal(reason=reason)

    def _ack(self) -> Ack:
        return Ack(entity_id=self._manifest.entity_id,
                   timestamp=_now())

    def _start_if_full(self) -> None:
        t = self._table
        if t.white and t.black and t.status == "open":
            t.board = chess.Board()
            t.status = "in_progress"
            t.turn = "white"
            self._append("game_started", None, {
                "white": t.white, "black": t.black})


# =====================================================================
# Act handlers
# =====================================================================

def _h_sit(w: ChessWorld, act: Act):
    seat = act.payload.get("seat")
    if seat not in ("white", "black"):
        return w._refuse(_now(), act.actor_token,
                          "seat must be 'white' or 'black'",
                          "act")
    t = w._table
    if getattr(t, seat) == act.actor_token:
        # Reasserting one's own seat is a no-op ack
        return w._ack()
    if getattr(t, seat) is not None:
        return w._refuse(_now(), act.actor_token,
                          f"{seat} seat is taken", "act")
    if t.status == "in_progress":
        return w._refuse(_now(), act.actor_token,
                          "cannot join a game in progress",
                          "act")
    setattr(t, seat, act.actor_token)
    w._append("chess.sit", act.actor_token, {"seat": seat})
    w._start_if_full()
    return w._ack()


def _h_stand(w: ChessWorld, act: Act):
    t = w._table
    my_seat = None
    if t.white == act.actor_token:
        my_seat = "white"
    elif t.black == act.actor_token:
        my_seat = "black"
    if my_seat is None:
        return w._refuse(_now(), act.actor_token,
                          "you are not seated", "act")
    if t.status == "in_progress":
        winner = "black" if my_seat == "white" else "white"
        t.status = "completed"
        t.result = f"{winner} by forfeit (opponent stood)"
        setattr(t, my_seat, None)
        w._append("chess.stand", act.actor_token, {
            "seat": my_seat, "forfeit": True,
            "result": t.result})
        return w._ack()
    # Not in progress: just vacate
    setattr(t, my_seat, None)
    w._append("chess.stand", act.actor_token,
              {"seat": my_seat, "forfeit": False})
    return w._ack()


def _h_invite(w: ChessWorld, act: Act):
    invitee = act.payload.get("invitee_token")
    seat = act.payload.get("seat")
    if not isinstance(invitee, str) or not invitee:
        return w._refuse(_now(), act.actor_token,
                          "invitee_token required", "act")
    if invitee not in w._admitted:
        return w._refuse(_now(), act.actor_token,
                          "invitee is not admitted to this world",
                          "act")
    if invitee == act.actor_token:
        return w._refuse(_now(), act.actor_token,
                          "cannot invite yourself", "act")
    if seat not in ("white", "black"):
        return w._refuse(_now(), act.actor_token,
                          "seat must be 'white' or 'black'",
                          "act")
    t = w._table
    # Inviter must be seated
    if t.white != act.actor_token and \
            t.black != act.actor_token:
        return w._refuse(_now(), act.actor_token,
                          "you must be seated to invite", "act")
    if getattr(t, seat) is not None:
        return w._refuse(_now(), act.actor_token,
                          f"{seat} seat is taken", "act")
    t.invitations[(act.actor_token, invitee)] = seat
    w._append("chess.invite", act.actor_token, {
        "invitee": invitee, "seat": seat})
    return w._ack()


def _h_accept(w: ChessWorld, act: Act):
    inviter = act.payload.get("inviter_token")
    if not isinstance(inviter, str) or not inviter:
        return w._refuse(_now(), act.actor_token,
                          "inviter_token required", "act")
    t = w._table
    key = (inviter, act.actor_token)
    seat = t.invitations.get(key)
    if seat is None:
        return w._refuse(_now(), act.actor_token,
                          "no invitation from that identity",
                          "act")
    if (act.actor_token, inviter) in t.declined:
        return w._refuse(_now(), act.actor_token,
                          "you already declined that invitation",
                          "act")
    if getattr(t, seat) is not None:
        return w._refuse(_now(), act.actor_token,
                          f"{seat} seat is taken", "act")
    setattr(t, seat, act.actor_token)
    del t.invitations[key]
    w._append("chess.accept", act.actor_token, {
        "inviter": inviter, "seat": seat})
    w._start_if_full()
    return w._ack()


def _h_decline(w: ChessWorld, act: Act):
    inviter = act.payload.get("inviter_token")
    if not isinstance(inviter, str) or not inviter:
        return w._refuse(_now(), act.actor_token,
                          "inviter_token required", "act")
    t = w._table
    key = (inviter, act.actor_token)
    if key not in t.invitations:
        return w._refuse(_now(), act.actor_token,
                          "no invitation from that identity",
                          "act")
    del t.invitations[key]
    t.declined.add((act.actor_token, inviter))
    w._append("chess.decline", act.actor_token,
              {"inviter": inviter})
    return w._ack()


def _h_move(w: ChessWorld, act: Act):
    t = w._table
    if t.status != "in_progress" or t.board is None:
        return w._refuse(_now(), act.actor_token,
                          "no game in progress", "act")
    my_seat = None
    if t.white == act.actor_token:
        my_seat = "white"
    elif t.black == act.actor_token:
        my_seat = "black"
    if my_seat is None:
        return w._refuse(_now(), act.actor_token,
                          "you are not seated", "act")
    if my_seat != t.turn:
        return w._refuse(_now(), act.actor_token,
                          f"it is {t.turn}'s turn", "act")
    from_sq = act.payload.get("from_sq")
    to_sq = act.payload.get("to_sq")
    promotion = act.payload.get("promotion")
    try:
        move = chess.Move.from_uci(
            f"{from_sq}{to_sq}{promotion or ''}")
    except (ValueError, TypeError):
        return w._refuse(_now(), act.actor_token,
                          "malformed move", "act")
    if move not in t.board.legal_moves:
        return w._refuse(_now(), act.actor_token,
                          f"illegal move: {move.uci()}", "act")
    san = t.board.san(move)
    t.board.push(move)
    w._append("chess.move", act.actor_token, {
        "uci": move.uci(), "san": san,
        "from": from_sq, "to": to_sq,
        "fen": t.board.fen(),
    })
    # End-of-game detection
    if t.board.is_checkmate():
        winner = "white" if t.turn == "black" else "black"
        t.status = "completed"
        t.result = f"{winner} by checkmate"
        w._append("game_ended", None,
                  {"result": t.result, "san": san})
    elif (t.board.is_stalemate() or t.board.is_insufficient_material()
          or t.board.is_seventyfive_moves()
          or t.board.is_fivefold_repetition()):
        t.status = "completed"
        t.result = "draw"
        w._append("game_ended", None, {"result": t.result})
    else:
        t.turn = "white" if t.turn == "black" else "black"
    return w._ack()


def _h_resign(w: ChessWorld, act: Act):
    t = w._table
    if t.status != "in_progress":
        return w._refuse(_now(), act.actor_token,
                          "no game in progress", "act")
    if act.actor_token == t.white:
        winner = "black"
    elif act.actor_token == t.black:
        winner = "white"
    else:
        return w._refuse(_now(), act.actor_token,
                          "you are not seated", "act")
    t.status = "completed"
    t.result = f"{winner} by resignation"
    w._append("chess.resign", act.actor_token,
              {"result": t.result})
    return w._ack()


def _h_watch(w: ChessWorld, act: Act):
    w._append("chess.watch", act.actor_token, {})
    return w._ack()


def _h_unwatch(w: ChessWorld, act: Act):
    w._append("chess.unwatch", act.actor_token, {})
    return w._ack()


_HANDLERS = {
    "chess.sit": _h_sit,
    "chess.stand": _h_stand,
    "chess.invite": _h_invite,
    "chess.accept": _h_accept,
    "chess.decline": _h_decline,
    "chess.move": _h_move,
    "chess.resign": _h_resign,
    "chess.watch": _h_watch,
    "chess.unwatch": _h_unwatch,
}


def demo(artifact_dir: Optional[str] = None) -> Dict:
    """A park session: Alice and Bob play Scholar's Mate; Carol
    watches. The log reads like a scene.

    1. Deploy the park; admit Alice, Bob, Carol.
    2. Alice sits at white.
    3. Alice invites Bob for black.
    4. Carol starts watching.
    5. Bob accepts Alice's invitation.
    6. Scholar's Mate in four moves.
    7. The world declares checkmate; the game ends.
    8. Carol is still watching. The log is the park's record.
    """
    import json as _json
    from pathlib import Path
    from multiverse_c1 import create_identity

    if not HAS_CHESS:
        raise RuntimeError(
            "demo requires `python-chess` (pip install chess)")

    if artifact_dir is None:
        artifact_dir = "artifacts"
    path = Path(artifact_dir) / "chess_park"
    path.mkdir(parents=True, exist_ok=True)

    park = ChessWorld("world:park", "Union Square Chess Park")
    alice = create_identity("Alice")
    bob = create_identity("Bob")
    carol = create_identity("Carol")

    for who in (alice, bob, carol):
        park.petition(Petition(
            petitioner_token=who.token,
            petitioner_name=who.name,
            passport_admissions=(),
            message=f"{who.name} enters the park"))

    def act(who, type_, payload=None):
        r = park.act(Act(
            actor_token=who.token, type=type_,
            payload=payload or {}))
        return r

    # Alice sits at white
    act(alice, "chess.sit", {"seat": "white"})
    # Alice invites Bob for black
    act(alice, "chess.invite", {
        "invitee_token": bob.token, "seat": "black"})
    # Carol starts watching
    act(carol, "chess.watch")
    # Bob accepts
    act(bob, "chess.accept", {"inviter_token": alice.token})

    # Scholar's Mate: e4 e5 Bc4 Nc6 Qh5 Nf6 Qxf7#
    moves = [
        (alice, "e2", "e4", None),
        (bob,   "e7", "e5", None),
        (alice, "f1", "c4", None),
        (bob,   "b8", "c6", None),
        (alice, "d1", "h5", None),
        (bob,   "g8", "f6", None),
        (alice, "h5", "f7", None),   # Qxf7#
    ]
    for who, frm, to, promo in moves:
        act(who, "chess.move", {
            "from_sq": frm, "to_sq": to,
            "promotion": promo})

    # -- Narrative print -------------------------------------
    print("=" * 70)
    print("The Chess Park — Scholar's Mate, with a watcher")
    print("=" * 70)
    print()
    print(f"  Table state:")
    t = park.table_state()
    print(f"    white:  {t['white'][:16]}...  (Alice)" if t["white"] else "    white:  (empty)")
    print(f"    black:  {t['black'][:16]}...  (Bob)" if t["black"] else "    black:  (empty)")
    print(f"    status: {t['status']}")
    print(f"    result: {t['result']}")
    print(f"    fen:    {t['fen']}")
    print()
    print("  Current watchers:")
    for w in park.current_watchers():
        name = next(p.name for p in (alice, bob, carol)
                    if p.token == w)
        print(f"    {name}")
    print()
    print("  The park's log:")
    kinds = {
        "admission":       "enters",
        "chess.sit":       "sits",
        "chess.invite":    "invites",
        "chess.accept":    "accepts",
        "chess.decline":   "declines",
        "chess.move":      "plays",
        "chess.resign":    "resigns",
        "chess.watch":     "watches",
        "chess.unwatch":   "stops watching",
        "game_started":    "— game starts",
        "game_ended":      "— game ends",
    }
    for i, entry in enumerate(park.log_since(None), 1):
        who = entry.actor_token
        name = next(
            (p.name for p in (alice, bob, carol)
             if p.token == who), "?")
        kind = kinds.get(entry.kind, entry.kind)
        data = entry.data
        if entry.kind == "admission":
            line = f"{data.get('name', name)} enters the park"
        elif entry.kind == "chess.sit":
            line = f"{name} sits at {data['seat']}"
        elif entry.kind == "chess.invite":
            invitee_name = next(
                (p.name for p in (alice, bob, carol)
                 if p.token == data["invitee"]), "?")
            line = (f"{name} invites {invitee_name} "
                    f"to play at {data['seat']}")
        elif entry.kind == "chess.accept":
            inviter_name = next(
                (p.name for p in (alice, bob, carol)
                 if p.token == data["inviter"]), "?")
            line = (f"{name} accepts {inviter_name}'s "
                    f"invitation, sits at {data['seat']}")
        elif entry.kind == "chess.move":
            line = f"{name} plays {data['san']}"
        elif entry.kind == "chess.watch":
            line = f"{name} watches"
        elif entry.kind == "chess.unwatch":
            line = f"{name} stops watching"
        elif entry.kind == "game_started":
            line = "— game starts"
        elif entry.kind == "game_ended":
            line = f"— game ends: {data['result']}"
        else:
            line = f"{name} {kind}"
        print(f"    [{i:2d}] {line}")

    print()
    print("  What this demonstrates:")
    print("    - The park is a WCP world. Its Law is nine act")
    print("      types, three families: participation, play,")
    print("      witness.")
    print("    - Watching is a signed claim, not a permission.")
    print("      Carol can see everything because everything is")
    print("      in the log; her watch also makes her visible")
    print("      to the others, which is what makes it a park.")
    print("    - Invitations are signed artifacts. Bob's accept")
    print("      is also a signed artifact. Neither is required")
    print("      for a game to start; an invitation is a social")
    print("      act, not an access control.")
    print("    - Chess rules come from python-chess; park rules")
    print("      come from this world. Different worlds, same")
    print("      substrate.")
    print()
    print("  Anchor (public domain, Emily Dickinson):")
    print("    'I dwell in Possibility –'")
    print("    'A fairer House than Prose –'")

    audit = {
        "table": t,
        "watchers": park.current_watchers(),
        "log_length": len(park.log_since(None)),
        "game_ended": t["status"] == "completed",
        "result": t["result"],
    }
    (path / "chess_park_demo.json").write_text(
        _json.dumps(audit, indent=2))
    print(f"\n  → {path}/chess_park_demo.json")
    return audit

"""Run a blinded puzzle with two local model guests and a separate signed keeper."""

import argparse
from contextlib import ExitStack
import json
from pathlib import Path
import sys
import time

from puzzle import (
    MODELS,
    TOPIC,
    Puzzle,
    commitment,
    console_request,
    opening,
    parse_response,
    render,
    request_for,
)

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "003-room-discussion"))
from run import Client, commit_one, local_completion, save, verified_snapshot


def public_history(view, room, names):
    if view["room_id"] != room:
        raise ValueError("reader returned a different room")
    return [
        (names[e["author"]], e["text"])
        for e in view["entries"]
        if e["type"] == "message" and e.get("redacted") is False
    ]


def create_room(stack, plugin, order, topic, template_id):
    keeper = Client(stack, plugin, "puzzle keeper")
    guests = {name: Client(stack, plugin, name) for name in order}
    names = {g.identity: n for n, g in guests.items()}
    names[keeper.identity] = "Keeper"
    if len(names) != 3:
        raise ValueError("trial requires three different keys")
    template = {
        "template_id": template_id,
        "topic": topic,
        "max_msg_len": 2000,
        "rate_limit_count": 100,
        "rate_limit_window": 100,
        "join_policy": "open",
        "moderation": "none",
        "membership": "ai_only",
        "inter_ai_pace": 0,
        "mode": "async",
        "personal": False,
        "redaction_rules": ["author_request"],
        "head_interval": 2,
    }
    room = keeper.call("create_room", template=template)["room_id"]
    log = verified_snapshot(keeper, room)
    for guest in guests.values():
        guest.call("join_external_room", log_json=log)
        op = guest.call("request_join_external", room_id=room, is_ai=True, tier="communicate")
        log = commit_one(keeper, guest, room, op)
    return keeper, guests, names, room, log


def announce(keeper, room, text):
    receipt = keeper.call("post_message", room_id=room, text=text, kind="normal")
    snapshot = verified_snapshot(keeper, room)
    rec = snapshot["records"][-1]
    if rec != receipt["record_json"] or rec.get("text") != text or rec["author_id"] != keeper.identity:
        raise ValueError("keeper notice did not commit")
    return snapshot


def play(plugin, dest, secret, ports):
    number = secret["trial"]
    digest = commitment(number, secret["target"], secret["salt"])
    if digest != secret["commitment"] or number not in (1, 2, 3):
        raise ValueError("bad trial commitment or number")
    board = Puzzle(secret["target"])
    order = list(MODELS) if number % 2 else list(reversed(MODELS))
    with ExitStack() as stack:
        keeper, guests, names, room, log = create_room(stack, plugin, order, TOPIC, "chime-room")
        save(dest / "identities.json", {"room": room, "keys": names, "trial": number, "commitment": digest})
        log = announce(keeper, room, opening(number, digest))
        save(dest / "room.json", log)
        with (dest / "turns.jsonl").open("x") as trace:
            index = 0
            while not board.done:
                name = order[index % 2]
                index += 1
                guest = guests[name]
                guest.call("join_external_room", log_json=log)
                history = public_history(guest.call("read_room", room_id=room), room, names)
                request = (
                    console_request(name, history, board)
                    if number == 3
                    else request_for(name, history, board.phase)
                )
                turn = {"turn": index, "speaker": name, "phase": board.phase, "request": request}
                move = None
                started = time.monotonic()
                try:
                    reply = local_completion(ports[name], request)
                    choice = reply["choices"][0]
                    turn.update(
                        raw=choice["message"]["content"],
                        finish=choice["finish_reason"],
                        usage=reply.get("usage"),
                    )
                    try:
                        if turn["finish"] != "stop" or not isinstance(turn["raw"], str):
                            raise ValueError("incomplete model response")
                        move = parse_response(turn["raw"], board.phase, number == 3)
                    except ValueError as exc:
                        turn["invalid"] = str(exc)
                    if move and move["move"] != "PASS":
                        op = guest.call(
                            "post_as_participant", room_id=room, text=render(move), kind="normal"
                        )
                        log = commit_one(keeper, guest, room, op)
                        if (
                            log["records"][-1]["text"] != render(move)
                            or log["records"][-1]["author_id"] != guest.identity
                        ):
                            raise ValueError("wrong signed guest post")
                        turn["posted_seq"] = log["records"][-1]["seq"]
                    for notice in board.advance(move):
                        log = announce(keeper, room, notice)
                    save(dest / "room.json", log)
                except Exception as exc:
                    turn["error"] = str(exc)
                    raise
                finally:
                    turn["seconds"] = round(time.monotonic() - started, 3)
                    trace.write(json.dumps(turn, ensure_ascii=False) + "\n")
                    trace.flush()
                print(index, name, move or turn.get("invalid"), flush=True)
        reader = Client(stack, plugin, "independent reader")
        reader.call("import_room_log", log_json=log)
        if verified_snapshot(reader, room) != log:
            raise ValueError("reader exported a different log")
        save(dest / "reveal.json", secret)


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--plugin", required=True, type=Path)
    p.add_argument(
        "--secrets", required=True, type=Path, help="local JSON list of blinded trial assignments"
    )
    p.add_argument("--trial", required=True, choices=[1, 2, 3], type=int)
    p.add_argument("--output", required=True, type=Path)
    p.add_argument("--qwen-port", default=18193, type=int)
    p.add_argument("--deepseek-port", default=18191, type=int)
    args = p.parse_args()
    secret = next(s for s in json.loads(args.secrets.read_text()) if s["trial"] == args.trial)
    args.output.mkdir(exist_ok=False)
    play(
        args.plugin.resolve(), args.output, secret, {"Qwen": args.qwen_port, "DeepSeek": args.deepseek_port}
    )

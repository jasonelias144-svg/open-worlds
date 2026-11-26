"""Replay the two-model chime room from its signed log, model trace and answer reveal."""

import argparse
from contextlib import ExitStack
import json
from pathlib import Path

from play import Client, verified_snapshot
from puzzle import MODELS, TOPIC, Puzzle, commitment, console_request, parse_response, opening, render, request_for


def check(ok, detail):
    if not ok:
        raise ValueError(detail)


def replay(directory, plugin=None, plan=None):
    room = json.loads((directory / "room.json").read_text())
    actors = json.loads((directory / "identities.json").read_text())
    seal = json.loads((directory / "reveal.json").read_text())
    trace = [json.loads(line) for line in (directory / "turns.jsonl").read_text().splitlines()]
    if plugin:
        with ExitStack() as stack:
            reader = Client(stack, plugin, "independent puzzle evidence reader")
            reader.call("import_room_log", log_json=room)
            check(verified_snapshot(reader, actors["room"]) == room, "signed log mismatch")
    trial = actors["trial"]
    check(actors["room"] == room["world_id"] and trial == seal["trial"] and trial in (1, 2, 3), "wrong trial")
    digest = commitment(trial, seal["target"], seal["salt"])
    check(actors["commitment"] == seal["commitment"] == digest, "answer does not match commitment")
    if plan is not None:
        check(f"Trial {trial}: `{digest}`" in plan.read_text(), "commitment missing from prior plan")
    names = actors["keys"]
    check(len(names) == 3 and set(names.values()) == {*MODELS, "Keeper"}, "expected three distinct keys")
    records = room["records"]
    check(records[0]["type"] == "room_created" and records[0]["template"]["topic"] == TOPIC
          and names[records[0]["creator_id"]] == "Keeper", "unexpected room seed")
    order = list(MODELS) if trial % 2 else list(reversed(MODELS))
    check(all(r["type"] == "join" and r["tier"] == "communicate" and r["is_ai"] is True for r in records[1:3])
          and [names[r["subject_id"]] for r in records[1:3]] == order, "guest admissions differ")
    board = Puzzle(seal["target"])
    public = []
    def consume(name, text):
        seq = len(public) + 3
        check(seq < len(records), "missing signed message")
        rec = records[seq]
        check(rec["type"] == "message" and rec["seq"] == seq and names[rec["author_id"]] == name
              and rec["text"] == text, f"unexpected signed message at {seq}")
        public.append((name, text))

    consume("Keeper", opening(trial, digest))
    steps = []
    interrupted = False
    for index, t in enumerate(trace):
        name = order[index % 2]
        check(not board.done and t["turn"] == index + 1 and t["speaker"] == name
              and t["phase"] == board.phase, "unexpected turn or wrong speaker")
        expected = console_request(name, public, board) if trial == 3 else request_for(name, public, board.phase)
        check(t["request"] == expected, "prompt differs from signed history")
        if "error" in t:
            check(index == len(trace)-1 and "posted_seq" not in t and t.get("error") == "timed out"
                  and "raw" not in t, "unexplained failure")
            interrupted = True
            steps.append({"turn": index+1, "speaker": name, "phase": board.phase, "move": None,
                          "before": "".join(sorted(board.remaining)), "after": "".join(sorted(board.remaining)),
                          "notices": [], "error": t["error"]})
            break
        try:
            if t["finish"] != "stop" or not isinstance(t["raw"], str):
                raise ValueError("incomplete model response")
            move = parse_response(t["raw"], board.phase, trial == 3)
        except ValueError as exc:
            check(t.get("invalid") == str(exc), "invalid turn misreported")
            move = None
        else:
            check("invalid" not in t, "valid move misreported")
        if move and move["move"] != "PASS":
            check(t.get("posted_seq") == len(public) + 3, "turn points to wrong signed post")
            consume(name, render(move))
        else:
            check("posted_seq" not in t, "an unposted turn claims a signed message")
        before = "".join(sorted(board.remaining))
        phase = board.phase
        notices = board.advance(move)
        for text in notices:
            consume("Keeper", text)
        steps.append({"turn": index + 1, "speaker": name, "phase": phase, "move": move,
                      "before": before, "after": "".join(sorted(board.remaining)), "notices": notices})
    check((board.done or interrupted) and len(records) == len(public) + 3, "unfinished trial or unexplained extra room events")
    return {"result": "interrupted" if interrupted else board.end, "target": seal["target"], "tests": board.tests, "steps": steps}


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("directory", type=Path)
    p.add_argument("--plugin", required=True, type=Path)
    p.add_argument("--plan", type=Path, help="also check the commitment against the original plan")
    a = p.parse_args()
    result = replay(a.directory, a.plugin.resolve(), a.plan)
    print(f"Verified {len(result['steps'])} opportunities and {result['tests']} listening tests. Outcome: {result['result']}.")

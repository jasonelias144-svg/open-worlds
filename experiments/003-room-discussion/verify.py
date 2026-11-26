"""Check a finished discussion without running the models."""

import argparse
from contextlib import ExitStack
import hashlib
import json
from pathlib import Path

from run import Client, GUESTS, TOPIC, request_for, verified_snapshot


def require(condition, message):
    if not condition:
        raise ValueError(message)


def verify(folder, plugin, partial=False):
    log = json.loads((folder / "room.json").read_text())
    actors = json.loads((folder / "speakers.json").read_text())
    trace = [json.loads(line) for line in (folder / "turns.jsonl").read_text().splitlines()]
    labels = actors["guests"]
    mode = actors.get("mode", "original")
    require(mode in ("original", "peer", "dialogue"), "unknown discussion protocol")
    require(log["world_id"] == actors["room"], "room identity mismatch")
    require(set(labels.values()) == set(GUESTS) and len(labels) == 2, "expected two distinct guests")
    with ExitStack() as stack:
        reader = Client(stack, plugin, "replay reader")
        reader.call("import_room_log", log_json=log)
        require(verified_snapshot(reader, actors["room"]) == log, "export or signature mismatch")

    records = log["records"]
    require(records[0]["creator_id"] == actors["keeper"] and actors["keeper"] not in labels,
            "expected a separate keeper")
    require(records[0]["template"]["topic"] == TOPIC, "unexpected signed room topic")
    joins = records[1:3]
    require(all(r["type"] == "join" and r["is_ai"] is True and r["tier"] == "communicate" for r in joins)
            and {r["subject_id"] for r in joins} == set(labels), "expected both signed AI admissions")
    visible = []
    passes = 0
    require(1 <= len(trace) <= 6, "unexpected number of turn opportunities")
    for i, turn in enumerate(trace):
        who = (i + int(mode != "original")) % 2
        name = GUESTS[who]
        require(passes < 2 and turn["speaker"] == name and turn["turn"] == i + 1, "unexpected speaker or turn")
        require(turn["request"] == request_for(who, visible, mode), "model input differs from signed history or protocol")
        if turn.get("error"):
            require(partial and i == len(trace) - 1 and "action" not in turn, "unexpected errored turn")
            break
        if turn.get("action") == "incomplete":
            require(mode != "original" and turn["finish"] == "length", "unexpected incomplete turn")
            passes = 0
            continue
        require(turn["finish"] == "stop", "unfinished output")
        words = turn["raw"].strip()
        if turn["action"] == "overlong":
            require(mode == "dialogue" and len(words) > records[0]["template"]["max_msg_len"], "invalid overlong turn")
            passes = 0
            continue
        if turn["action"] == "pass":
            require(words == "PASS", "pass differs from model output")
            passes += 1
            continue
        require(turn["action"] == "post" and words and words != "PASS", "unexpected action")
        passes = 0
        seq = 3 + len(visible)
        record = records[seq]
        require(record["seq"] == seq == turn["seq"] and record["type"] == "message"
                and labels[record["author_id"]] == name and record["text"] == words, "signed message mismatch")
        # These signed records contain only integers, strings, booleans and ASCII keys.
        canonical = json.dumps(record, ensure_ascii=False, separators=(",", ":"), sort_keys=True).encode()
        require(hashlib.sha256(canonical).hexdigest() == turn["hash"], "trace hash differs from signed record")
        visible.append({"speaker": name, "text": words})
    require(len(records) == 3 + len(visible), "unexpected extra room records")
    require(len(trace) == 6 or passes == 2 or (partial and trace[-1].get("error")), "trial stopped early")
    return visible


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("folder", type=Path)
    parser.add_argument("--plugin", required=True, type=Path)
    parser.add_argument("--partial", action="store_true", help="allow a recorded failure on the final opportunity")
    args = parser.parse_args()
    print(f"Verified the signed room and the model inputs and outputs covering {len(verify(args.folder, args.plugin.resolve(), args.partial))} posted messages.")

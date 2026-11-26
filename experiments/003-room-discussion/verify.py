"""Check a finished discussion without running the models."""

import argparse
from contextlib import ExitStack
import hashlib
import json
from pathlib import Path

from run import ALIASES, Client, GUESTS, TOPIC, verified_snapshot


def require(condition, message):
    if not condition:
        raise ValueError(message)


def verify(folder, plugin):
    log = json.loads((folder / "room.json").read_text())
    actors = json.loads((folder / "speakers.json").read_text())
    trace = [json.loads(line) for line in (folder / "turns.jsonl").read_text().splitlines()]
    labels = actors["guests"]
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
        name = GUESTS[i % 2]
        require(passes < 2 and "error" not in turn and turn["finish"] == "stop", "unexpected or incomplete turn")
        require(turn["speaker"] == name and turn["turn"] == i + 1, "speaker or turn order mismatch")
        request = turn["request"]
        require(request["model"] == ALIASES[i % 2], "model alias mismatch")
        prompt = json.loads(request["messages"][-1]["content"])
        require(prompt == {"topic": TOPIC, "conversation": visible}, "prompt differs from the prior signed turns")
        words = turn["raw"].strip()
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
    require(len(trace) == 6 or passes == 2, "trial stopped early")
    return visible


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("folder", type=Path)
    parser.add_argument("--plugin", required=True, type=Path)
    args = parser.parse_args()
    print(f"Verified the signed room and the model inputs and outputs for {len(verify(args.folder, args.plugin.resolve()))} posts.")

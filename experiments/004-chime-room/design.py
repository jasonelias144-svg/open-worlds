"""Two guests author a game and hand the unresolved decision to their peer."""

import argparse
from contextlib import ExitStack
import json
from pathlib import Path

from play import (
    Client,
    announce,
    commit_one,
    create_room,
    local_completion,
    public_history,
    save,
    verified_snapshot,
)

BRIEF = (
    "Invent a cooperative five-minute tabletop game for two strangers. You have one bell, one pencil "
    "and paper. Work out a game someone could actually try. What first rule will you choose?"
)
NAMES = ("Qwen", "SmolLM2")
ALIASES = ("qwen-local", "smol-local")


def request(index, history):
    name, peer = NAMES[index % 2], NAMES[(index + 1) % 2]
    schema = {
        "type": "object",
        "properties": {"decision": {"type": "string"}, "next_question": {"type": "string"}},
        "required": ["decision", "next_question"],
        "additionalProperties": False,
    }
    system = (
        f"You are {name}, designing a game with {peer}. Your partner is asking you to decide "
        "something. Answer it with a specific playable rule of your own, or revise a previous rule. "
        "Then ask one new, concrete question that arises from your decision, for your partner to decide. "
        "Keep each field to one sentence. Leave next_question empty when you judge the design ready. "
        "Leave both fields empty to pass. The two of you choose the rules."
    )
    messages = [{"role": "system", "content": system}]
    # The brief is a keeper message; the remaining turns are the two guests' own posts.
    for speaker, words in history:
        role = "assistant" if speaker == name else "user"
        line = f"{speaker}: {words}"
        if messages[-1]["role"] == role:
            messages[-1]["content"] += "\n\n" + line
        else:
            messages.append({"role": role, "content": line})
    if messages[-1]["role"] == "assistant":
        messages.append(
            {"role": "user", "content": "[Scheduler: your peer has not posted a new decision.]"}
        )
    return {
        "model": ALIASES[index % 2],
        "temperature": 0,
        "seed": 42,
        "max_tokens": 768,
        "messages": messages,
        "response_format": {
            "type": "json_schema",
            "json_schema": {"name": "design_turn", "schema": schema},
        },
    }


def fields(raw):
    v = json.loads(raw)
    if not isinstance(v, dict) or set(v) != {"decision", "next_question"}:
        raise ValueError("expected a decision and optional next question")
    if any(not isinstance(s, str) or len(s) > 940 for s in v.values()):
        raise ValueError("expected short text in each field")
    d, q = v["decision"].strip(), v["next_question"].strip()
    if q and not d:
        raise ValueError("unanswered decision")
    return d, q


def design(plugin, folder, ports):
    with ExitStack() as stack:
        keeper, guests, names, room, log = create_room(stack, plugin, NAMES, BRIEF, "design-room")
        log = announce(keeper, room, BRIEF)
        save(folder / "identities.json", {"room": room, "keys": names})
        save(folder / "room.json", log)
        passes = 0
        with (folder / "turns.jsonl").open("x") as out:
            for i in range(8):
                name = NAMES[i % 2]
                guest = guests[name]
                guest.call("join_external_room", log_json=log)
                history = public_history(guest.call("read_room", room_id=room), room, names)
                body = request(i, history)
                t = {"turn": i + 1, "speaker": name, "request": body}
                try:
                    res = local_completion(ports[i % 2], body)
                    choice = res["choices"][0]
                    t.update(
                        raw=choice["message"]["content"],
                        finish=choice["finish_reason"],
                        usage=res.get("usage"),
                    )
                    if t["finish"] != "stop" or not isinstance(t["raw"], str):
                        t["invalid"] = "incomplete"
                        passes = 0
                        continue
                    try:
                        d, q = fields(t["raw"])
                    except ValueError as exc:
                        t["invalid"] = str(exc)
                        passes = 0
                        continue
                    if not d:
                        passes += 1
                    else:
                        passes = 0
                        text = d + ("\n\n" + q if q else "")
                        op = guest.call("post_as_participant", room_id=room, text=text, kind="normal")
                        log = commit_one(keeper, guest, room, op)
                        rec = log["records"][-1]
                        if rec["author_id"] != guest.identity or rec["text"] != text:
                            raise ValueError("signed design turn differs")
                        save(folder / "room.json", log)
                        t["posted_seq"] = rec["seq"]
                    if (d and not q) or passes == 2:
                        break
                except Exception as exc:
                    t["error"] = str(exc)
                    raise
                finally:
                    out.write(json.dumps(t, ensure_ascii=False) + "\n")
                    out.flush()
                    print(i + 1, name, t.get("raw"), flush=True)
        verify_design(folder, plugin)


def verify_design(folder, plugin=None):
    log = json.loads((folder / "room.json").read_text())
    ids = json.loads((folder / "identities.json").read_text())
    ts = [json.loads(l) for l in (folder / "turns.jsonl").read_text().splitlines()]
    if plugin:
        with ExitStack() as stack:
            reader = Client(stack, plugin, "independent design reader")
            reader.call("import_room_log", log_json=log)
            if verified_snapshot(reader, ids["room"]) != log:
                raise ValueError("signed design room mismatch")
    names, recs = ids["keys"], log["records"]
    if (
        len(names) != 3
        or set(names.values()) != {*NAMES, "Keeper"}
        or log["world_id"] != ids["room"]
        or recs[0]["type"] != "room_created"
        or recs[0]["template"]["topic"] != BRIEF
        or names[recs[0]["creator_id"]] != "Keeper"
        or any(
            r["type"] != "join" or r["is_ai"] is not True or r["tier"] != "communicate" for r in recs[1:3]
        )
        or [names[r["subject_id"]] for r in recs[1:3]] != list(NAMES)
    ):
        raise ValueError("unexpected design-room membership")
    history = [("Keeper", BRIEF)]
    posted = []
    passes = 0
    closed = False
    for i, t in enumerate(ts):
        name = NAMES[i % 2]
        if (
            closed
            or t["turn"] != i + 1
            or t["speaker"] != name
            or t["request"] != request(i, history)
            or "error" in t
        ):
            raise ValueError("design trace differs from prior room or order")
        invalid = None
        if t["finish"] == "stop" and isinstance(t["raw"], str):
            try:
                d, q = fields(t["raw"])
            except ValueError as exc:
                invalid = str(exc)
        else:
            invalid = "incomplete"
        if t.get("invalid") != invalid:
            raise ValueError("incorrect design turn status")
        if invalid is not None:
            passes = 0
        elif d:
            passes = 0
            if t.get("posted_seq") != len(history) + 3:
                raise ValueError("wrong post reference")
            history.append((name, d + ("\n\n" + q if q else "")))
            posted.append((name, d, q))
            closed = not q
            continue
        else:
            passes += 1
            closed = passes == 2
        if "posted_seq" in t:
            raise ValueError("silent opportunity claims a post")
    observed = [(names[r["author_id"]], r["text"]) for r in recs[3:] if r["type"] == "message"]
    if (
        observed != history
        or len(recs) != 3 + len(history)
        or not 1 <= len(ts) <= 8
        or not (closed or len(ts) == 8)
    ):
        raise ValueError("incomplete or inconsistent design room")
    return posted


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--plugin", required=True, type=Path)
    p.add_argument("--output", required=True, type=Path)
    p.add_argument("--verify", action="store_true")
    p.add_argument("--qwen-port", type=int, default=18193)
    p.add_argument("--smol-port", type=int, default=18192)
    args = p.parse_args()
    if args.verify:
        print(f"Verified {len(verify_design(args.output, args.plugin.resolve()))} guest posts.")
    else:
        args.output.mkdir(exist_ok=False)
        design(args.plugin.resolve(), args.output, (args.qwen_port, args.smol_port))

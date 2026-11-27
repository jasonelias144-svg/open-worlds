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


OPENING = "What should ringing the bell do that gives both players a reason to cooperate?"
DIRECT_BRIEF = (
    "Design a cooperative five-minute tabletop game for two strangers with one bell, a pencil and paper. "
    + OPENING
)


def direct_request(index, history, pending, answer=None):
    name = NAMES[index % 2]
    context = "\n".join(f"{n}: {text}" for n, text in history[1:])
    system = (
        f"You are {name}, a co-designer. Both strangers should win or lose together. "
        "Materials: one bell, one pencil and paper. Time: five minutes. "
        "Your job now is to make the specific choice your partner is asking for. "
        "Give the actual rule in one short sentence. You may say PASS. "
        "Prior signed posts for reference:\n" + context
    )
    messages = [{"role": "system", "content": system}, {"role": "user", "content": pending}]
    if answer is not None:
        messages += [
            {"role": "assistant", "content": answer},
            {
                "role": "user",
                "content": "Given that rule, ask your partner ONE concrete question about a different rule that is still undecided. Write just that question, or READY if the game is ready to try.",
            },
        ]
    return {
        "model": ALIASES[index % 2],
        "temperature": 0,
        "seed": 42,
        "max_tokens": 384,
        "messages": messages,
    }


def capture(body, port):
    response = local_completion(port, body)
    choice = response["choices"][0]
    return {
        "request": body,
        "raw": choice["message"]["content"],
        "finish": choice["finish_reason"],
        "usage": response.get("usage"),
    }


def text_of(call):
    if call["finish"] != "stop" or not isinstance(call["raw"], str):
        raise ValueError("incomplete")
    text = call["raw"].strip()
    if not text or len(text) > 940:
        raise ValueError("empty or overlong output")
    return text


def handoff(index, history, pending, callbacks):
    first = callbacks(direct_request(index, history, pending))
    answer = text_of(first)
    if answer == "PASS":
        return "", ""
    follow = text_of(callbacks(direct_request(index, history, pending, answer)))
    if follow == "READY":
        return answer, ""
    if not follow.endswith("?"):
        raise ValueError("follow-up did not end in a question")
    return answer, follow


def design(plugin, folder, ports, direct=False):
    brief = DIRECT_BRIEF if direct else BRIEF
    pending = OPENING
    with ExitStack() as stack:
        keeper, guests, names, room, log = create_room(stack, plugin, NAMES, brief, "design-room")
        log = announce(keeper, room, brief)
        save(folder / "identities.json", {"room": room, "keys": names, "direct": direct})
        save(folder / "room.json", log)
        passes = 0
        with (folder / "turns.jsonl").open("x") as out:
            for i in range(8):
                name = NAMES[i % 2]
                guest = guests[name]
                guest.call("join_external_room", log_json=log)
                history = public_history(guest.call("read_room", room_id=room), room, names)
                t = {"turn": i + 1, "speaker": name}
                try:
                    if direct:
                        t["calls"] = []

                        def live_call(body):
                            result = capture(body, ports[i % 2])
                            t["calls"].append(result)
                            return result

                    try:
                        if direct:
                            d, q = handoff(i, history, pending, live_call)
                        else:
                            t.update(capture(request(i, history), ports[i % 2]))
                            if t["finish"] != "stop" or not isinstance(t["raw"], str):
                                raise ValueError("incomplete")
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
                        pending = q
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
    direct = ids.get("direct", False)
    brief = DIRECT_BRIEF if direct else BRIEF
    pending = OPENING
    names, recs = ids["keys"], log["records"]
    if (
        len(names) != 3
        or set(names.values()) != {*NAMES, "Keeper"}
        or log["world_id"] != ids["room"]
        or recs[0]["type"] != "room_created"
        or recs[0]["template"]["topic"] != brief
        or names[recs[0]["creator_id"]] != "Keeper"
        or any(
            r["type"] != "join" or r["is_ai"] is not True or r["tier"] != "communicate" for r in recs[1:3]
        )
        or [names[r["subject_id"]] for r in recs[1:3]] != list(NAMES)
    ):
        raise ValueError("unexpected design-room membership")
    history = [("Keeper", brief)]
    posted = []
    passes = 0
    closed = False
    for i, t in enumerate(ts):
        name = NAMES[i % 2]
        if (
            closed
            or t["turn"] != i + 1
            or t["speaker"] != name
            or (not direct and t["request"] != request(i, history))
            or "error" in t
        ):
            raise ValueError("design trace differs from prior room or order")
        invalid = None
        if direct:
            calls = iter(t["calls"])

            def recorded(body):
                call = next(calls, None)
                if call is None or call["request"] != body:
                    raise RuntimeError("model did not receive the preceding signed question")
                return call

            try:
                d, q = handoff(i, history, pending, recorded)
            except ValueError as exc:
                invalid = str(exc)
            if next(calls, None) is not None:
                raise ValueError("unexplained inference call")
        elif t["finish"] == "stop" and isinstance(t["raw"], str):
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
            pending = q
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
    p.add_argument("--direct", action="store_true", help="give the next guest the exact pending question")
    p.add_argument("--qwen-port", type=int, default=18193)
    p.add_argument("--smol-port", type=int, default=18192)
    args = p.parse_args()
    if args.verify:
        print(f"Verified {len(verify_design(args.output, args.plugin.resolve()))} guest posts.")
    else:
        args.output.mkdir(exist_ok=False)
        design(args.plugin.resolve(), args.output, (args.qwen_port, args.smol_port), args.direct)

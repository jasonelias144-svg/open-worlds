"""A designer answers questions put to them by a separate model trying to play."""

import argparse
from contextlib import ExitStack
import json
from pathlib import Path

from design import ALIASES, NAMES, capture
from play import Client, announce, commit_one, create_room, public_history, save, verified_snapshot

OPENING = "When someone rings the bell, what changes on the players’ paper?"
BRIEF = (
    "Design a cooperative five-minute tabletop game for two strangers with one bell, one pencil "
    "and paper. Both win or lose together. " + OPENING
)


def prompt(index, history):
    if index % 2 == 0:
        task = (
            "You are the game's rule designer. Answer the actual question below in one short sentence. "
            "Decide something players can physically do or check at the table. You can revise earlier rules."
        )
        user = OPENING if index == 0 else history[-1][1]
    else:
        task = (
            "You are one of two people trying to PLAY this game, right now, with real paper, a pencil "
            "and a bell. Find the first unresolved detail that prevents you from carrying out the latest "
            "rule. Ask the rule designer that one specific question in your own words. Return only your question."
        )
        user = "Here is the designer’s latest rule:\n" + history[-1][1]
    prior = "\n".join(f"{who}: {words}" for who, words in history)
    system = f"{task} You may also pass. The signed public room so far:\n{prior}"
    return {
        "model": ALIASES[index % 2],
        "temperature": 0,
        "seed": 42,
        "max_tokens": 384,
        "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
    }


def content(call):
    if call["finish"] != "stop" or not isinstance(call["raw"], str):
        raise ValueError("incomplete")
    words = call["raw"].strip()
    if not words or len(words) > 1950:
        raise ValueError("empty or overlong response")
    return words


def verify(folder, plugin=None):
    ids = json.loads((folder / "identities.json").read_text())
    log = json.loads((folder / "room.json").read_text())
    ts = list(map(json.loads, (folder / "turns.jsonl").read_text().splitlines()))
    if plugin:
        with ExitStack() as stack:
            reader = Client(stack, plugin, "playtest reader")
            reader.call("import_room_log", log_json=log)
            if verified_snapshot(reader, ids["room"]) != log:
                raise ValueError("room failed verification")
    recs, names = log["records"], ids["keys"]
    if (
        len(names) != 3
        or set(names.values()) != {*NAMES, "Keeper"}
        or log["world_id"] != ids["room"]
        or recs[0]["type"] != "room_created"
        or recs[0]["template"]["topic"] != BRIEF
        or names[recs[0]["creator_id"]] != "Keeper"
        or [names[r["subject_id"]] for r in recs[1:3]] != list(NAMES)
        or any(
            r["type"] != "join" or r["is_ai"] is not True or r["tier"] != "communicate" for r in recs[1:3]
        )
    ):
        raise ValueError("unexpected room identity or admissions")
    history = [("Keeper", BRIEF)]
    stopped = False
    for i, t in enumerate(ts):
        name = NAMES[i % 2]
        if stopped or t["speaker"] != name or t["turn"] != i + 1 or t["request"] != prompt(i, history):
            raise ValueError("question or speaker differs from signed conversation")
        words = content(t)
        if words.upper() == "PASS":
            if "posted_seq" in t:
                raise ValueError("a pass claims a post")
            stopped = True
        else:
            if t["posted_seq"] != len(history) + 3:
                raise ValueError("wrong signed sequence")
            history.append((name, words))
    observed = [(names[r["author_id"]], r["text"]) for r in recs[3:] if r["type"] == "message"]
    if (
        history != observed
        or len(recs) != len(history) + 3
        or not 1 <= len(ts) <= 7
        or not (stopped or len(ts) == 7)
    ):
        raise ValueError("incomplete or inconsistent playtest")
    return history[1:]


def play(plugin, folder, ports):
    with ExitStack() as stack:
        keeper, guests, names, room, _ = create_room(stack, plugin, NAMES, BRIEF, "paper-and-bell")
        log = announce(keeper, room, BRIEF)
        save(folder / "identities.json", {"room": room, "keys": names})
        save(folder / "room.json", log)
        with (folder / "turns.jsonl").open("x") as trace:
            for i in range(7):
                name = NAMES[i % 2]
                guest = guests[name]
                guest.call("join_external_room", log_json=log)
                history = public_history(guest.call("read_room", room_id=room), room, names)
                body = prompt(i, history)
                t = {"turn": i + 1, "speaker": name, "request": body}
                try:
                    t.update(capture(body, ports[i % 2]))
                    words = content(t)
                    if words.upper() == "PASS":
                        break
                    op = guest.call("post_as_participant", room_id=room, text=words, kind="normal")
                    log = commit_one(keeper, guest, room, op)
                    if (
                        log["records"][-1]["author_id"] != guest.identity
                        or log["records"][-1]["text"] != words
                    ):
                        raise ValueError("signed post differs")
                    t["posted_seq"] = log["records"][-1]["seq"]
                    save(folder / "room.json", log)
                    print(i + 1, name, words, flush=True)
                except Exception as exc:
                    t["error"] = str(exc)
                    raise
                finally:
                    trace.write(json.dumps(t, ensure_ascii=False) + "\n")
                    trace.flush()
        verify(folder, plugin)


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--plugin", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--verify", action="store_true")
    p.add_argument("--qwen-port", type=int, default=18193)
    p.add_argument("--smol-port", type=int, default=18192)
    a = p.parse_args()
    if a.verify:
        print(f"Verified {len(verify(a.output, a.plugin.resolve()))} signed guest posts.")
    else:
        a.output.mkdir(exist_ok=False)
        play(a.plugin.resolve(), a.output, (a.qwen_port, a.smol_port))

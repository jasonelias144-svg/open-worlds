"""Run or verify a paired field-recording conversation in signed Commons rooms."""

import argparse
from contextlib import ExitStack
from difflib import SequenceMatcher
from functools import partial
import hashlib
import json
from pathlib import Path
import re
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "004-chime-room"))
from play import Client, commit_one, create_room, local_completion, public_history, save, verified_snapshot

PIER, MARKET, MOD = "Pier recordist", "Market recordist", "Moderator"
CAST = (PIER, MARKET, MOD)
MODELS = dict(zip(CAST, ("deepseek-local", "deepseek-seven", "qwen-moderator")))
PORTS = dict(zip(CAST, (18201, 18202, 18203)))
BRIEF = (
    'You and your partner are making "Our Harbor Waking Up" for the Commons. You share one handheld '
    'recorder. It runs continuously from 07:00:00 to 07:01:00. The pier and the market are a '
    '30-second walk apart. No cuts or second take. Where should the minute begin, and what do '
    'you need to know from your partner to make the recording work?'
)
NOTES = {
    PIER: 'You scouted the pier. The ferry bell rings there from 07:00:00 to 07:00:10. It can only '
          'be recorded at the pier. You want listeners to hear the bell. Your partner scouted the market.',
    MARKET: 'You scouted the market. The fishmonger raises a rattling shutter from 07:00:45 to '
            '07:00:55. It can only be recorded at the market. You want listeners to hear the '
            'shutter. Your partner scouted the pier.',
}
SIGN = (
    "A harbor recording will play at a Commons listening table. You two recordists have one small "
    "sign beside the headphones. What invitation of at most twelve words will work for both of you?"
)
SIGN_NOTES = {
    PIER: "You want to listen quietly and walk away without seeming rude. Offer actual words "
          "for the sign. When your partner offers words, consider what you would do on reading them.",
    MARKET: "You want to leave one sound you noticed for the next listener. There are blank cards "
            "and a pencil. Tell your partner how their wording lands with you, and suggest an edit if needed.",
}
SCHEMA = {"type": "object", "properties": {k: {"type": "string"} for k in ("anchor", "question")},
          "required": ["anchor", "question"], "additionalProperties": False}


def normalized(words):
    return " ".join(re.findall(r"\w+", words.casefold()))


def echoes(words, previous):
    return any(SequenceMatcher(None, normalized(words), normalized(old)).ratio() >= 0.85 for old in previous)


def schedule(moderated, history, sign=False):
    """Each send supplies the result of the last offered turn."""
    passes = 0
    planned = (1, 3) if sign else (0, 2, 3)
    for i in range(6):
        guest, other = (PIER, MARKET) if i % 2 == 0 else (MARKET, PIER)
        prior = [w for n, w in history if n != MOD]
        action = yield guest, other
        if action == "leave":
            break
        passes = passes + 1 if action == "pass" else 0
        if passes == 2:
            break
        if moderated and action == "post" and i < 5 and (i in planned or echoes(history[-1][1], prior)):
            yield MOD, other


def request(name, target, history, repair=None, check_facts=False, sign=False):
    brief = SIGN if sign else BRIEF
    notes = SIGN_NOTES if sign else NOTES
    transcript = "\n".join(f"{n}: {w}" for n, w in history) or "(The floor is open.)"
    body = {"model": MODELS[name], "temperature": 0.6, "seed": 42, "max_tokens": 448}
    if name == MOD:
        text = (
            f'You moderate a conversation between two recordists. Your goal is to keep them thinking together. '
            f'Their brief: {brief}\nPublic conversation:\n{transcript}\n\n'
            f'Hand the last speaker’s idea to the {target} in ONE short question. Pick one concrete detail '
            'from the LAST answer and ask the other person for a choice, consequence or correction that '
            'is still open because of it. You may challenge an impossible plan. Skip settled details. '
            'Leave room for the partner to decide. If nothing remains, pass. Return JSON. In anchor copy '
            'an exact short phrase from the last answer. In question write the words you want the guest '
            'to hear. To pass, use an empty anchor and PASS as the question.'
        )
        if sign:
            text += ("\nLet the two editors hear each other. Pick one expression or action in the last "
                     "guest's words and ask how the next listener would read it, or what edit would "
                     "settle their difference. If they already agree on workable wording, pass.")
        if check_facts:
            text += (
                "\nBefore asking, compare the last answer against the fixed facts in the public brief. "
                "When they conflict, state the actual fixed fact in your question and ask the next "
                "guest for ONE concrete repair. If a claim cannot be checked from the public facts, "
                "ask for the missing observation. If all fits, ask for the next unresolved choice. "
                "Do not adopt a mistaken premise merely because a guest said it."
            )
        if repair:
            text += f'\nYour first draft was: {repair[0]}\nPlease try once more. {repair[1]}'
        body.update(max_tokens=190, temperature=0.3, seed=43 if repair else 42,
                    response_format={"type": "json_schema", "json_schema": {"name": "followup", "schema": SCHEMA}})
    else:
        text = (f'You are the {name} talking to the {target}. {brief}\nYour own field note: {notes[name]}\n'
                f'Public conversation:\n{transcript}\n\nSpeak to your partner in one or two sentences. '
                'Answer the last question if there is one. Use what you know to make, correct or test '
                'a specific choice together. You can ask for information you need. When the plan is '
                'settled, you can say PASS. You may leave with LEAVE. Output only your own words.')
    body["messages"] = [{"role": "user", "content": text}]
    return body


def interpret(name, call, history):
    raw = call["public"]
    if call["finish"] != "stop" or not isinstance(raw, str) or not raw.strip():
        raise ValueError("The reply must be complete.")
    words = raw.strip()
    if name == MOD:
        obj = json.loads(words)
        if not isinstance(obj, dict) or set(obj) != {"anchor", "question"}:
            raise ValueError("Supply an anchor and one question.")
        anchor, words = obj["anchor"], obj["question"]
        if not isinstance(anchor, str) or not isinstance(words, str):
            raise ValueError("Both fields must be text.")
        if not (anchor == "" and words == "PASS"):
            if not anchor.strip() or anchor not in history[-1][1]:
                raise ValueError("Copy an exact phrase from the last answer.")
            if words.count("?") != 1 or not words.endswith("?") or len(words) > 360:
                raise ValueError("Ask one short question.")
            if echoes(words, [w for n, w in history if n == MOD]):
                raise ValueError("That question has already been asked. Find a different unresolved choice.")
    if len(words) > 2000 or "<think>" in words or "</think>" in words:
        raise ValueError("Invalid public speech.")
    if words == "PASS":
        return "pass", None
    if words == "LEAVE":
        return "leave", None
    return "post", words


def turn(name, target, history, get, check_facts=False, sign=False):
    repair = None
    for _ in range(2 if name == MOD else 1):
        call = get(request(name, target, history, repair, check_facts, sign))
        if call["model"] != MODELS[name]:
            raise ValueError("Endpoint returned a different model.")
        try:
            return interpret(name, call, history)
        except ValueError as exc:
            repair = call["public"], str(exc)
    return "withheld", None


def protect_public_channel(call, recover_final=False):
    """Some servers put an extra thinking delimiter inside their nominal public field."""
    raw = call["public"]
    if isinstance(raw, str) and ("<think>" in raw or "</think>" in raw):
        suffix = None
        if recover_final and call["finish"] == "stop" and raw.count("</think>") == 1 and "<think>" not in raw:
            suffix = raw.partition("</think>")[2].strip() or None
        call["public"] = suffix
        call["public_omitted"] = {"reason": "thinking delimiter in public channel",
                                  "sha256": hashlib.sha256(raw.encode()).hexdigest(),
                                  "bytes": len(raw.encode())}
    return call


def infer(body, name, recover_final=False):
    result = local_completion(PORTS[name], body)
    choice = result["choices"][0]
    return protect_public_channel({"request": body, "public": choice["message"]["content"], "finish": choice["finish_reason"],
            "model": result["model"], "used_reasoning_channel": bool(choice["message"].get("reasoning_content")),
            "usage": result["usage"]}, recover_final=recover_final)


def play(folder, plugin, moderated, check_facts=False, sign=False):
    settings = {"moderated": moderated, "check_facts": check_facts, "sign": sign}
    run_room(folder, plugin, CAST, SIGN if sign else BRIEF, "harbor-sign" if sign else "harbor-recording",
             settings, partial(schedule, moderated, sign=sign),
             partial(turn, check_facts=check_facts, sign=sign),
             lambda body, name: infer(body, name, recover_final=sign and name != MOD))


def run_room(folder, plugin, cast, topic, template_id, settings, make_schedule, take_turn, complete):
    """Record model turns against each participant's verified view of the room."""
    folder.mkdir(exist_ok=False)
    with ExitStack() as stack:
        keeper, guests, names, room, log = create_room(stack, plugin, cast, topic, template_id)
        save(folder / "identities.json", {**settings, "keys": names, "room": room})
        save(folder / "room.json", log)
        history = []
        offers = make_schedule(history)
        offer = next(offers)
        with (folder / "turns.jsonl").open("x") as trace:
            while offer:
                name, target = offer
                guest = guests[name]
                guest.call("join_external_room", log_json=log)
                seen = public_history(guest.call("read_room", room_id=room), room, names)
                if seen != history:
                    raise ValueError("Guest saw a different signed conversation.")
                entry = {"speaker": name, "target": target, "calls": []}

                def get(body):
                    call = complete(body, name)
                    entry["calls"].append(call)
                    return call

                try:
                    action, words = take_turn(name, target, seen, get)
                    entry["action"] = action
                    if words is not None:
                        op = guest.call("post_as_participant", room_id=room, text=words, kind="normal")
                        log = commit_one(keeper, guest, room, op)
                        rec = log["records"][-1]
                        if names[rec["author_id"]] != name or rec["text"] != words:
                            raise ValueError("Wrong signed post.")
                        entry["seq"] = rec["seq"]
                        save(folder / "room.json", log)
                        history.append((name, words))
                    print(name, action, words or "", flush=True)
                except Exception as exc:
                    entry["error"] = str(exc)
                    raise
                finally:
                    print(json.dumps(entry, ensure_ascii=False), file=trace, flush=True)
                try:
                    offer = offers.send(action)
                except StopIteration:
                    break


def verify(folder, plugin=None):
    ids = json.loads((folder / "identities.json").read_text())
    sign = ids.get("sign", False)
    return verify_room(folder, plugin, ids, CAST, SIGN if sign else BRIEF,
                       partial(schedule, ids["moderated"], sign=sign),
                       partial(turn, check_facts=ids.get("check_facts", False), sign=sign))


def verify_room(folder, plugin, ids, cast, topic, make_schedule, take_turn):
    """Replay the protocol from the signed messages, including unposted opportunities."""
    log = json.loads((folder / "room.json").read_text())
    entries = [json.loads(s) for s in (folder / "turns.jsonl").read_text().splitlines()]
    if plugin:
        with ExitStack() as stack:
            reader = Client(stack, plugin, "verification")
            reader.call("import_room_log", log_json=log)
            if verified_snapshot(reader, ids["room"]) != log:
                raise ValueError("Signatures or exported log differ.")
    keys, recs = ids["keys"], log["records"]
    if (set(keys.values()) != {"Keeper", *cast} or len(keys) != len(cast) + 1 or log["world_id"] != ids["room"]
            or recs[0]["type"] != "room_created" or keys[recs[0]["creator_id"]] != "Keeper"
            or recs[0]["template"]["topic"] != topic
            or [keys[r["subject_id"]] for r in recs[1:1 + len(cast)]] != list(cast)
            or any(r["type"] != "join" or not r["is_ai"] or r["tier"] != "communicate" for r in recs[1:1 + len(cast)])):
        raise ValueError("Unexpected cast, admissions or topic.")
    history = []
    offers = make_schedule(history)
    offer = next(offers)
    for e in entries:
        if offer != (e["speaker"], e["target"]):
            raise ValueError("Unexpected turn.")
        calls = iter(e["calls"])

        def recorded(body):
            call = next(calls, None)
            if not call or call["request"] != body:
                raise ValueError("Prompt differs from guest observation.")
            return call

        action, words = take_turn(*offer, history, recorded)
        if next(calls, None) or action != e["action"]:
            raise ValueError("Unexplained inference or action.")
        if action == "post":
            seq = len(history) + 1 + len(cast)
            r = recs[seq]
            if (e["seq"] != seq or r["seq"] != seq or r["type"] != "message"
                    or r["text"] != words or keys[r["author_id"]] != offer[0]):
                raise ValueError("Posted words differ from inference.")
            history.append((offer[0], words))
        elif "seq" in e:
            raise ValueError("Unposted input claims a signed message.")
        try:
            offer = offers.send(action)
        except StopIteration:
            offer = None
    if offer is not None or len(recs) != len(history) + 1 + len(cast):
        raise ValueError("Incomplete or extra evidence.")
    return history


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("mode", choices=("moderated", "control", "fact-check", "sign", "verify"))
    p.add_argument("folder", type=Path)
    p.add_argument("--plugin", type=Path, required=True)
    args = p.parse_args()
    if args.mode != "verify":
        play(args.folder, args.plugin.resolve(), args.mode != "control", check_facts=args.mode == "fact-check", sign=args.mode == "sign")
    print("Verified", len(verify(args.folder, args.plugin.resolve())), "public posts.")

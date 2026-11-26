"""Run the paired rehearsal poems, or check their public records offline."""

import argparse
from dataclasses import asdict
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "experiments/006-harbor"))
import harbor
from multiverse import passport
from multiverse.collaboration import make_client, petition_world, leave_world
from multiverse.identity import signature_valid
from multiverse.poetry_world import PoetryWorld, PoetryWorldLaw
from multiverse.protocol import Ack, Act, Admission, Manifest, act_document, manifest_problem

POETS = ("Poet 7B", "Poet 1.5B")
ENDPOINTS = dict(zip(POETS, (harbor.MARKET, harbor.PIER)))
FIELDS = ("acknowledgment", "proposal", "invitation", "holds_open")
SCHEMA = {
    "type": "object",
    "properties": {"action": {"type": "string", "enum": ["turn", "pass", "leave"]},
                   **{key: {"type": "string"} for key in FIELDS[:3]},
                   "holds_open": {"type": "boolean"}},
    "required": ["action", *FIELDS], "additionalProperties": False,
}


def opening(timing):
    return f"At rehearsal, a chair scraped the floor {timing} the next solo."


def request(name, timing, lines, form):
    history = "\n".join(json.dumps(line, ensure_ascii=False) for line in lines)
    if form == "verse":
        history = "\n\n".join(line["poet"] + "\n" + line["proposal"] for line in lines)
        cue = (
            f"You are {name}. At rehearsal two poets are writing a poem together, one short stanza "
            "at a time. Read what is on the page. If you want to write, add a few lines of your own "
            "that pick up something you hear. Your partner will see exactly the words you put on the page. "
            "Give only the verse you want to share. You may also send the single word PASS or LEAVE."
        )
    elif form == "plain":
        cue = (
            f"You are {name}, writing a poem with another poet at rehearsal. "
            "Read the opening and the accepted poem so far. If you would like to contribute, "
            "answer with three lines. After Heard: name a detail you heard, using a word "
            "from the previous poet's line or question if there is one. After Line: write "
            "one new line of verse. After Question: ask the other poet a short, open question "
            "arising from your new line. You may instead send the single word PASS or LEAVE."
        )
    else:
        cue = (
            f"You are {name}, one of two poets at rehearsal. Write together in the Poetry World. "
            "The opening and accepted turns below are the material for the poem. "
            "You can contribute, pass or leave. For a turn, acknowledge one specific detail you heard "
            "(use a word from the last verse or invitation if there is one). In proposal, write one "
            "new line of verse that something in the last turn or opening made you want to write. "
            "In invitation, ask your fellow poet one short open question growing out of your line. "
            "Set holds_open to whether you leave that question open. For pass or leave, use empty "
            "text fields and false."
        )
    instruction = (cue + "\n\nOpening line:\n" + opening(timing)
                   + "\n\nAccepted turns in order:\n" + (history or "(none yet)"))
    body = {"model": harbor.MODELS[ENDPOINTS[name]],
            "messages": [{"role": "user", "content": instruction}],
            "temperature": 0.6, "seed": 42, "max_tokens": 640, "cache_prompt": False}
    if form == "structured":
        body["response_format"] = {"type": "json_schema",
                                   "json_schema": {"name": "poetry_turn", "schema": SCHEMA}}
    return body


def decision(call, form):
    if call["finish"] != "stop" or not isinstance(call["public"], str):
        return "withheld", None
    if form in ("plain", "verse"):
        public = call["public"].strip()
        if public.upper() in ("PASS", "LEAVE"):
            return public.lower(), None
        if form == "verse":
            if not public:
                return "withheld", None
            return "turn", {"acknowledgment": "", "proposal": public,
                            "invitation": "", "holds_open": False}
        rows = [line.strip() for line in public.splitlines() if line.strip()]
        labels = ("Heard:", "Line:", "Question:")
        if len(rows) != 3 or any(not row.startswith(label) for row, label in zip(rows, labels)):
            return "withheld", None
        ack, verse, invitation = (row[len(label):].strip() for row, label in zip(rows, labels))
        return "turn", {"acknowledgment": ack, "proposal": verse, "invitation": invitation,
                        "holds_open": invitation.endswith("?")}
    try:
        reply = json.loads(call["public"])
    except ValueError:
        return "withheld", None
    if (not isinstance(reply, dict) or set(reply) != {"action", *FIELDS}
            or reply["action"] not in ("turn", "pass", "leave")
            or any(not isinstance(reply[k], str) for k in FIELDS[:3])
            or type(reply["holds_open"]) is not bool):
        return "withheld", None
    return reply["action"], {key: reply[key] for key in FIELDS}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def law_for(form):
    if form == "verse":
        return PoetryWorldLaw(max_turns=4, requires_acknowledgment=False,
                              requires_acknowledgment_references_prior=False,
                              requires_invitation=False, requires_holds_open=False)
    return PoetryWorldLaw(max_turns=4)


def run(timing, path, form):
    # Exclusive creation makes overwriting a previous run impossible.
    with path.open("x", encoding="utf-8") as output:
        world = PoetryWorld("rehearsal-" + timing, "Rehearsal", law_for(form))
        manifest = world.manifest()
        guests = {name: make_client(name) for name in POETS}
        for guest in guests.values():
            require(isinstance(petition_world(guest, world), Admission), "admission failed")
        lines, attempts = [], []
        misses = 0
        stop = "four opportunities"
        try:
            for i in range(4):
                name = POETS[i % 2]
                guest = guests[name]
                body = request(name, timing, lines, form)
                attempt = {"poet": name, "request": body}
                attempts.append(attempt)
                try:
                    call = harbor.infer(body, ENDPOINTS[name], recover_final=True)
                    require(call["model"] == body["model"], "unexpected model endpoint")
                except Exception as exc:
                    attempt.update(error=f"{type(exc).__name__}: {exc}", outcome="error")
                    stop = "inference error"
                    break
                del call["request"]
                attempt["call"] = call
                outcome, payload = decision(call, form)
                if outcome == "turn":
                    act = guest.individual.act(manifest, "poem.turn", payload)
                    attempt["signed_act"] = asdict(act)
                    response = world.act(act)
                    if isinstance(response, Ack):
                        guest.keep(response.stamp)
                        lines.append({"poet": name, **payload})
                        outcome = "accepted"
                    else:
                        outcome = "refused"
                        attempt["reason"] = response.reason
                attempt["outcome"] = outcome
                print(f"{timing} {i + 1}: {name} {outcome}", flush=True)
                misses = 0 if outcome == "accepted" else misses + 1
                if outcome == "leave" or world.is_converged() or misses == 2:
                    stop = ("guest left" if outcome == "leave" else
                            world.convergence_reason() if world.is_converged() else
                            "two opportunities without acceptance")
                    break
        finally:
            for guest in guests.values():
                leave_world(guest, world)
            json.dump({"format": form, "timing": timing, "opening": opening(timing), "manifest": asdict(manifest),
                       "attempts": attempts, "stop": stop, "log": [asdict(e) for e in world.log_since()],
                       "passports": [passport.to_dict(g.passport) for g in guests.values()]},
                      output, ensure_ascii=False, indent=2)
            output.write("\n")


def verify(path):
    record = json.loads(path.read_text())
    timing = record["timing"]
    form = record.get("format", "structured")
    require(form in ("structured", "plain", "verse"), "unknown invitation format")
    manifest = Manifest(**record["manifest"])
    require(timing in ("before", "after") and record["opening"] == opening(timing), "opening mismatch")
    require(manifest.entity_id == "rehearsal-" + timing and not manifest_problem(manifest), "manifest mismatch")
    log_turns = [event["data"] for event in record["log"] if event["kind"] == "turn"]
    keys, stamped = {}, []
    for raw in record["passports"]:
        book = passport.from_dict(raw)
        check = passport.verify_passport(book, {manifest.entity_id: manifest.world_key})
        require(check.ok and len(check.visits) == 1 and bool(check.visits[0].left), "invalid or open visit")
        keys[book.identity.name] = book.identity.token
        stamped.extend((s["holder"], s["made"]) for s in raw["entries"] if s.get("stamp") == "made")
    require(set(keys) == set(POETS) and len(set(keys.values())) == 2, "unexpected poets")
    require(sorted(stamped) == sorted((t["actor_token"], passport.thing_fingerprint(t)) for t in log_turns),
            "world stamps do not match the verses")
    lines = []
    misses = 0
    stop = None
    # Reapply the ordinary poetry law with fresh identities to check acceptances,
    # refusals and convergence independently of the archived world keys.
    mirror = PoetryWorld("replay", "Rehearsal", law_for(form))
    readers = {name: make_client(name) for name in POETS}
    for reader in readers.values():
        petition_world(reader, mirror)
    for i, attempt in enumerate(record["attempts"]):
        name = POETS[i % 2]
        require(stop is None and i < 4 and attempt["poet"] == name, "turn order mismatch")
        body = request(name, timing, lines, form)
        require(body == attempt["request"], "prompt does not match preceding accepted turns")
        if "error" in attempt:
            require(attempt["outcome"] == "error", "error outcome mismatch")
            stop = "inference error"
            continue
        call = attempt["call"]
        require(call["model"] == body["model"], "wrong endpoint in record")
        outcome, payload = decision(call, form)
        if outcome == "turn":
            act = Act(**attempt["signed_act"])
            require(act.type == "poem.turn" and act.actor_token == keys[name] and act.payload == payload and
                    signature_valid(keys[name], act_document(manifest.entity_id, manifest.world_key, act),
                                    act.signature), "invalid signed submission")
            response = mirror.act(readers[name].individual.act(mirror.manifest(), "poem.turn", payload))
            if isinstance(response, Ack):
                turn = log_turns[len(lines)]
                require(turn["turn_index"] == len(lines) and turn["actor_name"] == name and
                        turn["actor_token"] == keys[name] and all(turn[k] == payload[k] for k in FIELDS),
                        "signed verse mismatch")
                lines.append({"poet": name, **payload})
                outcome = "accepted"
            else:
                require(attempt["reason"] == response.reason, "wrong refusal")
                outcome = "refused"
        require(outcome == attempt["outcome"], "outcome mismatch")
        misses = 0 if outcome == "accepted" else misses + 1
        if outcome == "leave":
            stop = "guest left"
        elif mirror.is_converged():
            stop = mirror.convergence_reason()
        elif misses == 2:
            stop = "two opportunities without acceptance"
        elif i == 3:
            stop = "four opportunities"
    require(stop == record["stop"] and len(lines) == len(log_turns), "incomplete record")
    print(f"{path.name}: {len(lines)} accepted turns verified; {stop}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("before", "after", "verify"))
    parser.add_argument("file", type=Path)
    forms = parser.add_mutually_exclusive_group()
    forms.add_argument("--plain", dest="form", action="store_const", const="plain",
                       help="use the three-label follow-up invitation")
    forms.add_argument("--free-verse", dest="form", action="store_const", const="verse",
                       help="accept verse alone under the optional poetry law")
    parser.set_defaults(form="structured")
    args = parser.parse_args()
    if args.mode == "verify":
        verify(args.file)
    else:
        run(args.mode, args.file, args.form)

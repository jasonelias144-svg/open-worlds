"""Two local model guests share a room through three separate signed plugin clients."""

import argparse
from contextlib import ExitStack
import json
from pathlib import Path
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from minds.room_moderator import local_completion

TOPIC = "What should happen in the first minute after someone new enters a quiet Commons room?"
GUESTS = ("DeepSeek", "SmolLM2")
ALIASES = ("deepseek-local", "smol-local")

ORIENTATION = (
    "You are {name}, one of two guests in a public Commons room. The other guest is {other}. "
    "Speak for yourself in one or two short conversational sentences. You may start a thought, "
    "ask a question, challenge or build on what the other guest actually said. If you have "
    "nothing to add, reply with just PASS. Output only your own words, without a speaker label. "
    "The room topic and signed public conversation below are your shared context."
)


CONSCIOUSNESS = "What is consciousness?"
ANSWER_PREFIX = "<think>\n\n</think>\n\n"
DEEPSEEK_MODES = ("consciousness", "consciousness-peer", "consciousness-question", "consciousness-native")
DIALOGUE_MODES = ("dialogue", "final", *DEEPSEEK_MODES)


def topic_for(mode):
    return CONSCIOUSNESS if mode in DEEPSEEK_MODES else TOPIC


def turn_limit(mode):
    return 8 if mode in ("consciousness", "consciousness-peer") else 6


def first_guest(mode):
    return 0 if mode in ("original", "consciousness", "consciousness-peer") else 1


def public_words(raw, mode):
    if mode in DEEPSEEK_MODES:
        if mode != "consciousness-native":
            raw = raw.removeprefix(ANSWER_PREFIX)
        if "<think>" in raw or "</think>" in raw:
            raise ValueError("unexpected thinking delimiter in public reply")
    return raw.strip()


def participants(mode):
    if mode in DEEPSEEK_MODES:
        return ("DeepSeek 1.5B", "DeepSeek 7B"), ("deepseek-local", "deepseek-seven")
    if mode == "final":
        return (GUESTS[0], "Qwen"), (ALIASES[0], "qwen-local")
    return GUESTS, ALIASES


def save(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n")


class Client:
    def __init__(self, stack, plugin, label):
        self.proc = stack.enter_context(subprocess.Popen(
            [str(plugin), "--stdin-server"], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
            text=True, encoding="utf-8", bufsize=1))
        stack.callback(self.proc.stdin.close)
        self.sequence = 0
        ready = self.exchange({"home_name": label})
        if ready.get("event") != "ready":
            raise ValueError("plugin did not open")
        self.identity = ready["user_id"]

    def exchange(self, message):
        self.proc.stdin.write(json.dumps(message) + "\n")
        self.proc.stdin.flush()
        return json.loads(self.proc.stdout.readline())

    def call(self, method, **params):
        self.sequence += 1
        reply = self.exchange({"id": self.sequence, "method": method, "params": params})
        if reply.get("id") != self.sequence or "result" not in reply:
            raise ValueError(f"{method} failed: {reply.get('error')}")
        return reply["result"]


def verified_snapshot(keeper, room_id):
    if keeper.call("verify_room", room_id=room_id)["ok"] is not True:
        raise ValueError("room verification failed")
    log = keeper.call("export_room_log", room_id=room_id)["log_json"]
    if log["world_id"] != room_id:
        raise ValueError("room identity changed")
    return log


def commit_one(keeper, guest, room_id, signed):
    pending = guest.call("export_pending_for", room_id=room_id)["pending"]
    if pending != [signed["record_json"]]:
        raise ValueError("guest did not sign exactly the requested operation")
    outcomes = keeper.call("accept_pending", room_id=room_id, pending=pending)["outcomes"]
    if len(outcomes) != 1 or outcomes[0]["accepted"] is not True or outcomes[0]["request_hash"] != signed["record_hash"]:
        raise ValueError(f"keeper declined guest operation: {outcomes}")
    log = verified_snapshot(keeper, room_id)
    if log["records"][-1] != pending[0]:
        raise ValueError("signed operation differs from the committed record")
    return log


def request_for(who, turns, mode):
    names, aliases = participants(mode)
    name = names[who]
    request = {"model": aliases[who], "temperature": 0, "seed": 42, "max_tokens": 1536,
               "messages": [{"role": "system", "content": ORIENTATION.format(name=name, other=names[1-who])},
                            {"role": "user", "content": json.dumps({"topic": TOPIC, "conversation": turns},
                                                                   ensure_ascii=False)}]}
    if mode == "peer":
        other = names[1-who]
        cue = (f"Open the discussion with {other}. What would you try, and why?" if not turns
               else f"Continue the discussion with {other}. Respond to what has been said.")
        request["messages"][0]["content"] = (
            f"You are {name}, discussing a room design with your peer {other}. "
            "The newcomer in the topic has yet to arrive. Talk directly to your peer about an idea "
            "or a concern, in one or two short sentences. Write just your own words. "
            "You can reply PASS to yield your turn.")
        request["messages"][1]["content"] = json.dumps(
            {"topic": TOPIC, "conversation": turns, "your_turn": cue}, ensure_ascii=False)
    if mode in ("consciousness-question", "consciousness-native"):
        other = names[1-who]
        context = (f"You are {name}. Your conversation partner is {other}. "
                   f"Jason asked you both: {CONSCIOUSNESS}")
        if turns:
            history = json.dumps(turns, ensure_ascii=False)
            cue = (f"The signed conversation so far is below.\n{history}\n\n"
                   f"What do you want to say back to {other} about their last words? "
                   "Answer them directly in up to three sentences. You can ask them a "
                   "question of your own or say PASS.")
        else:
            cue = (f"Ask {other} one concrete question about a case where you are unsure "
                   "what counts as conscious. Write only the question you want them to hear, or PASS.")
        request["messages"] = [{"role": "user", "content": context + "\n\n" + cue}]
    elif mode in DIALOGUE_MODES:
        messages = [{"role": "system", "content":
                     f"You are {name}, chatting with {names[1-who]} in a text-only Commons room. "
                     f"The topic is: {topic_for(mode)} Use your own words and address your peer directly. "
                     "Keep your turn brief. You may say PASS to yield."}]
        if mode == "consciousness-peer":
            messages[0]["content"] += (
                " In your opening reply, give a tentative answer and put one question of your own to your peer."
                " Once your peer has spoken, respond to one specific thing they said."
                " If that raises a further question for you, ask them.")
        if mode in DEEPSEEK_MODES or not turns or turns[0]["speaker"] == name:
            messages.append({"role": "user", "content": topic_for(mode)})
        for turn in turns:
            role = "assistant" if turn["speaker"] == name else "user"
            if messages[-1]["role"] == role:
                messages[-1]["content"] += "\n\n" + turn["text"]
            else:
                messages.append({"role": role, "content": turn["text"]})
        if messages[-1]["role"] == "assistant":
            notice = ("[Turn scheduler: no new message from the other guest. You may continue or pass.]"
                      if mode in ("final", *DEEPSEEK_MODES) else "The floor is open.")
            messages.append({"role": "user", "content": notice})
        request["messages"] = messages
    if mode == "consciousness-native":
        request.update(temperature=0.6, max_tokens=832)
    elif mode in DEEPSEEK_MODES:
        request["messages"].append({"role": "assistant", "content": ANSWER_PREFIX})
        request.update(temperature=0.6, max_tokens=512, add_generation_prompt=False,
                       continue_final_message=True)
    return request


def discussion(plugin, ports, dest, mode):
    with ExitStack() as stack:
        keeper = Client(stack, plugin, "trial keeper")
        names, _ = participants(mode)
        guests = [Client(stack, plugin, name) for name in names]
        labels = {guest.identity: name for name, guest in zip(names, guests)}
        if len(labels) != 2 or keeper.identity in labels:
            raise ValueError("expected three distinct signing identities")
        template = {"template_id": "two-model-discussion", "topic": topic_for(mode), "max_msg_len": 4000 if mode in DIALOGUE_MODES else 1200,
                    "rate_limit_count": 10, "rate_limit_window": 20, "join_policy": "open",
                    "moderation": "none", "membership": "ai_only", "inter_ai_pace": 0,
                    "mode": "async", "personal": False, "redaction_rules": ["author_request"],
                    "head_interval": 2}
        room_id = keeper.call("create_room", template=template)["room_id"]
        log = verified_snapshot(keeper, room_id)
        save(dest / "room.json", log)
        save(dest / "speakers.json", {"room": room_id, "keeper": keeper.identity, "guests": labels,
                                    "mode": mode})
        for guest in guests:
            guest.call("join_external_room", log_json=log)
            signed = guest.call("request_join_external", room_id=room_id, tier="communicate", is_ai=True)
            log = commit_one(keeper, guest, room_id, signed)
            save(dest / "room.json", log)

        passes = 0
        with (dest / "turns.jsonl").open("x", buffering=1) as trace:
            for i in range(turn_limit(mode)):
                who = (i + first_guest(mode)) % 2
                guest, name = guests[who], names[who]
                guest.call("join_external_room", log_json=log)
                view = guest.call("read_room", room_id=room_id)
                if view["room_id"] != room_id:
                    raise ValueError("guest reader switched rooms")
                turns = [{"speaker": labels[e["author"]], "text": e["text"]} for e in view["entries"]
                         if e["type"] == "message" and e.get("redacted") is False]
                request = request_for(who, turns, mode)
                entry = {"turn": i + 1, "speaker": name, "request": request}
                started = time.monotonic()
                try:
                    response = local_completion(ports[who], request)
                    choice = response["choices"][0]
                    raw = choice["message"]["content"]
                    entry.update(raw=raw, usage=response.get("usage"), finish=choice["finish_reason"])
                    if mode == "consciousness-native":
                        entry["used_reasoning_channel"] = bool(choice["message"].get("reasoning_content"))
                    if mode in DEEPSEEK_MODES:
                        entry["reported_model"] = response["model"]
                        if entry["reported_model"] != request["model"]:
                            raise ValueError("unexpected model endpoint")
                    if mode != "original" and entry["finish"] == "length":
                        passes = 0
                        entry["action"] = "incomplete"
                        print(f"{i + 1}. {name} reached the token limit.", flush=True)
                        continue
                    if entry["finish"] != "stop" or not isinstance(raw, str) or not raw.strip():
                        raise ValueError("incomplete model turn")
                    words = public_words(raw, mode)
                    if not words:
                        raise ValueError("empty public reply")
                    if words == "PASS":
                        passes += 1
                        entry["action"] = "pass"
                    else:
                        passes = 0
                        if len(words) > template["max_msg_len"]:
                            if mode in DIALOGUE_MODES:
                                entry["action"] = "overlong"
                                print(f"{i + 1}. {name} exceeded the room limit.", flush=True)
                                continue
                            raise ValueError("utterance exceeds room limit")
                        signed = guest.call("post_as_participant", room_id=room_id, text=words,
                                            kind="response" if turns else "normal")
                        log = commit_one(keeper, guest, room_id, signed)
                        record = log["records"][-1]
                        if record["author_id"] != guest.identity or record["text"] != words:
                            raise ValueError("committed message mismatch")
                        save(dest / "room.json", log)
                        entry.update(action="post", seq=record["seq"], hash=signed["record_hash"])
                except Exception as exc:
                    entry["error"] = str(exc)
                    raise
                finally:
                    entry["seconds"] = round(time.monotonic() - started, 3)
                    print(json.dumps(entry, ensure_ascii=False), file=trace, flush=True)
                print(f"{i + 1}. {name} ({entry['action']}): {words}", flush=True)
                if passes == 2:
                    break
        reader = Client(stack, plugin, "independent reader")
        reader.call("import_room_log", log_json=log)
        if verified_snapshot(reader, room_id) != log:
            raise ValueError("independent reader exported a different log")
        print("Independent reader verified the signed room.", flush=True)


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--plugin", required=True, type=Path)
    p.add_argument("--output", type=Path, required=True, help="fresh directory for this run")
    p.add_argument("--deepseek-port", type=int, default=18191)
    p.add_argument("--smol-port", type=int, default=18192)
    p.add_argument("--mode", choices=("original", "peer", *DIALOGUE_MODES), default="final")
    p.add_argument("--qwen-port", type=int, default=18193)
    p.add_argument("--deepseek-seven-port", type=int, default=18194)
    args = p.parse_args()
    args.output.mkdir(exist_ok=False)
    peer_port = args.qwen_port if args.mode == "final" else args.smol_port
    if args.mode in DEEPSEEK_MODES:
        peer_port = args.deepseek_seven_port
    discussion(args.plugin.resolve(), (args.deepseek_port, peer_port), args.output, args.mode)

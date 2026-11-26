"""Room rules for a temporary listening test and an unassigned follow-up discussion."""

import hashlib
import json

BELLS = "ABCDEFGH"
TOPIC = "Which of the eight chimes is sounding behind the curtain?"
MODELS = {"Qwen": "qwen-local", "DeepSeek": "deepseek-local"}
RULES = (
    "One chime A through H is sounding. You and your partner have four listening tests. "
    "DAMP any nonempty proper subset for a moment. If the hidden chime is included, the sound stops; "
    "otherwise it continues. Each test resets afterward. NAME one chime when all the evidence "
    "leaves just one possibility. You can also TALK to your peer or PASS. You both see the same record.")
OPEN = "The puzzle phase has ended. The floor is yours for up to four turns. You can raise any new question together or pass."


def commitment(trial, target, salt):
    return hashlib.sha256(f"chime-v1/{trial}/{target}/{salt}".encode()).hexdigest()


def opening(trial, digest):
    return f"Trial {trial}. {RULES}\nSealed answer commitment: {digest}"


def render(move):
    return move["speech"] + "\n[" + " ".join(filter(None, [move["move"], move["bells"]])) + "]"


def decode(raw, phase):
    move = json.loads(raw)
    if not isinstance(move, dict) or set(move) != {"speech", "move", "bells"}:
        raise ValueError("expected speech, move and bells")
    words, action, bells = move["speech"], move["move"], move["bells"]
    if not isinstance(words, str) or not words.strip() or len(words) > 950:
        raise ValueError("expected a short utterance")
    allowed = ("TALK", "PASS") if phase == "open" else ("TALK", "PASS", "DAMP", "NAME")
    if action not in allowed or not isinstance(bells, str) or any(b not in BELLS for b in bells):
        raise ValueError("unknown move or chime")
    if len(set(bells)) != len(bells):
        raise ValueError("a letter occurs more than once")
    if action == "DAMP" and not 0 < len(bells) < len(BELLS):
        raise ValueError("choose a nonempty proper subset")
    if action == "NAME" and len(bells) != 1:
        raise ValueError("name one chime")
    if action in ("TALK", "PASS") and bells:
        raise ValueError("speech or pass takes no chimes")
    return move


class Puzzle:
    def __init__(self, target):
        if target not in tuple(BELLS):
            raise ValueError("invalid sealed answer")
        self.target = target
        self.remaining = set(BELLS)
        self.tests = 0
        self.phase = "puzzle"
        self.end = None
        self.puzzle_turns = self.open_turns = self.passes = 0
        self.done = False

    def advance(self, move):
        """Advance one opportunity, including an unusable response (None). Return public notices."""
        if self.done:
            raise ValueError("room has ended")
        action = move["move"] if move else None
        self.passes = self.passes + 1 if action == "PASS" else 0
        notices = []
        if self.phase == "open":
            self.open_turns += 1
            self.done = self.open_turns == 4 or self.passes == 2
            return notices
        self.puzzle_turns += 1
        if action == "DAMP":
            if self.tests == 4:
                notices.append("All four listening tests have been used.")
            else:
                self.tests += 1
                bells = move["bells"]
                stopped = self.target in bells
                selected = set(bells)
                self.remaining = self.remaining & selected if stopped else self.remaining - selected
                sound = "STOPS" if stopped else "CONTINUES"
                notices.append(f"Test {self.tests}. With {bells} damped, the sound {sound}.")
        elif action == "NAME":
            if len(self.remaining) > 1:
                notices.append("The evidence still permits more than one chime. No answer revealed.")
            elif move["bells"] == self.target:
                self.end = "solved"
                notices.append(f"Solved. The signed evidence singles out {self.target}.")
            else:
                notices.append("That name does not fit the evidence.")
        if self.end is None and self.tests == 4 and len(self.remaining) > 1:
            self.end = "test budget"
        if self.passes == 2:
            self.end = "two passes"
            self.done = True
        elif self.end or self.puzzle_turns == 12:
            self.end = self.end or "turn limit"
            self.phase = "open"
            self.passes = 0
            notices.append(OPEN)
        return notices


def request_for(name, history, phase):
    peer = next(n for n in MODELS if n != name)
    actions = ["TALK", "PASS"] if phase == "open" else ["TALK", "DAMP", "NAME", "PASS"]
    schema = {"type": "object", "properties": {
        "speech": {"type": "string", "minLength": 1, "maxLength": 950},
        "move": {"type": "string", "enum": actions},
        "bells": {"type": "string", "pattern": "^[A-H]{0,7}$"}},
        "required": ["speech", "move", "bells"], "additionalProperties": False}
    instruction = (
        f"You are {name}. Your peer is {peer}. You share a room. The signed room transcript "
        "labels the Keeper separately from the two guest speakers. Speak to your peer in one or two "
        "sentences. You choose what to ask, propose, challenge or do. Use the JSON fields speech, "
        "move and bells. Use an empty string for bells on TALK or PASS. For DAMP or NAME, use only "
        "distinct uppercase chime letters without spaces. The keeper alone supplies the test results.")
    return {"model": MODELS[name], "temperature": 0, "seed": 42, "max_tokens": 1536,
            "messages": [{"role": "system", "content": instruction},
                         {"role": "user", "content": "\n\n".join(f"{n}: {s}" for n, s in history)
                          + f"\n\nYour turn, {name}. Phase: {phase}."}],
            "response_format": {"type": "json_schema", "json_schema": {"name": "room_turn", "schema": schema}}}

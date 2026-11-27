"""Two DeepSeek guests read a paragraph together in a signed Commons room."""

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "experiments/006-harbor"))
import harbor

LARGE, SMALL, MOD = "Reader 7B", "Reader 1.5B", harbor.MOD
CAST = (LARGE, SMALL, MOD)
ENDPOINT = {LARGE: harbor.MARKET, SMALL: harbor.PIER, MOD: MOD}
BOOK = ROOT / "library/009-13-CGPT-Peace_and_the_Strategist.txt"
TITLE = "Art of Peace, Book I, chapter 1, The Shared Whole"
OPENING = "Which words would you pause over, and what do you hear in them?"


def source():
    passages = [line for line in BOOK.read_text().splitlines()
                if line.startswith("Agreement may come later. Belonging precedes it.")]
    if len(passages) != 1:
        raise ValueError("Expected one matching paragraph in the library.")
    return passages[0]


def schedule(history):
    passes = 0
    for i in range(6):
        speaker, partner = (LARGE, SMALL) if i % 2 == 0 else (SMALL, LARGE)
        action = yield speaker, partner
        if action == "leave":
            return
        passes = passes + 1 if action == "pass" else 0
        if passes == 2:
            return
        if i in (1, 3) and action == "post":
            yield MOD, partner


def request(name, partner, history, repair=None):
    transcript = "\n".join(f"{n}: {w}" for n, w in history)
    body = {"model": harbor.MODELS[ENDPOINT[name]], "temperature": 0.6, "seed": 42, "max_tokens": 768}
    heading = f"Text on the table — {TITLE}\n\n{source()}"
    if name == MOD:
        cue = (f"You moderate this reading. Address {partner}. Use the last reader's actual words to "
               "identify a difference, an uncertainty, or a concrete implication worth asking the other "
               "reader about. Ask one brief question that sends them back to the passage. If there is "
               "nothing unresolved, pass. Return JSON: in anchor copy up to eight consecutive words "
               "exactly from the last reader, and in question write only your question. To yield, use "
               "an empty anchor and PASS as the question.")
        if repair:
            cue += f"\nYour draft: {repair[0]}\nTry again. {repair[1]}"
        body.update(temperature=0.3, seed=43 if repair else 42, max_tokens=192,
                    response_format={"type": "json_schema", "json_schema": {"name": "question", "schema": harbor.SCHEMA}})
    else:
        cue = (f"You are {name}, talking with {partner} at a reading table. " +
               (OPENING if not history else
                "Reply directly to the last speaker. Pick up one thing they said, and use the paragraph "
                "to say what you would add, question, or revise. If an everyday example helps, choose one.") +
               " Speak in two or three sentences. Give only the words you would say aloud. "
               "You can say PASS or LEAVE.")
    body["messages"] = [{"role": "user", "content": f"{heading}\n\nRoom conversation so far:\n{transcript}\n\n{cue}"}]
    return body


def turn(name, partner, history, get):
    repair = None
    for _ in range(2 if name == MOD else 1):
        call = get(request(name, partner, history, repair))
        if call["model"] != harbor.MODELS[ENDPOINT[name]]:
            raise ValueError("Wrong checkpoint endpoint.")
        try:
            return harbor.interpret(name, call, history)
        except ValueError as exc:
            repair = call["public"], str(exc)
    return "withheld", None


def topic():
    return f"{TITLE}\n\n{source()}\n\n{OPENING}"


def run(folder, plugin):
    harbor.run_room(folder, plugin, CAST, topic(), "commons-reading", {}, schedule, turn,
                    lambda body, name: harbor.infer(body, ENDPOINT[name], recover_final=name != MOD))


def verify(folder, plugin=None):
    ids = json.loads((folder / "identities.json").read_text())
    return harbor.verify_room(folder, plugin, ids, CAST, topic(), schedule, turn)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("run", "verify"))
    parser.add_argument("folder", type=Path)
    parser.add_argument("--plugin", required=True, type=Path)
    args = parser.parse_args()
    if args.action == "run":
        run(args.folder, args.plugin.resolve())
    print("Verified", len(verify(args.folder, args.plugin.resolve())), "public posts.")

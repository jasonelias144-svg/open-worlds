"""Run or replay the charge-walking experiment with local DeepSeek checkpoints."""
import argparse
import itertools
import json
from pathlib import Path
import random
import urllib.request

from field import CHARGES, GOLD, HOME, NAMES, State, Track, controls, step

ENDPOINT = {"7B": (18402, "deepseek-seven"), "1.5B": (18401, "deepseek-local")}
SIGNS = {1: "+", 0: "0", -1: "-"}
PAIRS = {f"A{SIGNS[a]} B{SIGNS[b]}": [a, b] for a, b in itertools.product(NAMES, repeat=2)}
LAW = ("Two imaginary beads A and B can choose an electrical charge (+, 0 or -). "
       "Your aim is to bond, reach gold with A at site 9, then return A to 3. "
       "Unbonded opposite charges attract; alike charges repel. A neutral bead turns off mutual force. "
       "Oppositely charged neighbors bond. Once bonded they stay one site apart. At each end a positive charge "
       "pushes with the local gradient shown, a negative reverses it and zero contributes nothing. "
       "The sum pushes the pair one site east (positive), west (negative) or nowhere (zero). "
       "The pads alternate, so read the gradients again after every step. You may leave.")


def prompt(state, track, tick, previous, assigned, first):
    rows = [LAW, f"Tick {tick}/16. A at {state.a}, B at {state.b}. Bonded: {state.bonded}.",
            f"Current target for A: {HOME if state.gold else GOLD}.",
            f"Once bonded, local gradients now: A {track.gradient(state.a):+d}, B {track.gradient(state.b):+d}."]
    if previous:
        rows.append(f"Last choices {[NAMES[q] for q in previous['charges']]}; "
                    f"last forces {previous['forces']}; ended at {previous['positions']}.")
    if first is not None:
        rows.append(f"A chose {NAMES[first]} for the current tick. The world has not moved yet.")
    if assigned == "both":
        rows.append("You control both beads. Select their charges for this tick, or leave.")
    else:
        rows.append(f"You control only {assigned}. Choose your charge for this tick, or leave.")
    return "\n".join(rows)


def request(model, message, options, seed, preview=None):
    ordered = sorted(options)
    random.Random(seed).shuffle(ordered)
    if preview is not None:
        message += "\nInstrument preview of next (A,B) sites, in menu order: " + "; ".join(
            f"{choice} -> {preview[choice]}" for choice in ordered if choice != "leave")
    instruction = message + "\nLegal choices: " + ", ".join(ordered) + ". Reply with your selection."
    return {"model": ENDPOINT[model][1], "prompt": "<｜User｜>" + instruction
            + "<｜Assistant｜><think>\n\n</think>\n\n", "json_schema": {"type": "object",
            "properties": {"choice": {"type": "string", "enum": ordered}}, "required": ["choice"],
            "additionalProperties": False}, "temperature": 0.6, "seed": seed, "n_predict": 48, "cache_prompt": False}


def complete(model, body):
    req = urllib.request.Request(f"http://127.0.0.1:{ENDPOINT[model][0]}/completion",
                                 data=json.dumps(body).encode(), headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=120) as response:
        result = json.load(response)
    # The native decoder constrains the entire public response to one JSON choice.
    return {"model": result["model"], "finish": result["stop_type"], "public": result["content"],
            "tokens": result["tokens_predicted"]}


def play(mode, saved=None):
    state, track = State(), Track()
    frames, calls = [], []
    stop = "tick limit"
    seats = [("7B", "both")] if mode in ("solo", "preview") else [("1.5B", "A"), ("7B", "B")]
    for tick in range(1, 17):
        charges = []
        for model, assigned in seats:
            options = set(PAIRS if assigned == "both" else CHARGES) | {"leave"}
            message = prompt(state, track, tick, frames[-1] if frames else None, assigned,
                             charges[0] if charges else None)
            preview = None
            if mode == "preview":
                preview = {label: step(state, qs, track, tick)[1]["positions"] for label, qs in PAIRS.items()}
            choice = None
            for attempt in range(2):
                seed = 2026 + 19 * tick + len(charges) * 3 + attempt
                body = request(model, message, options, seed, preview)
                if saved is None:
                    try:
                        response = complete(model, body)
                    except (OSError, ValueError, KeyError) as exc:
                        response = {"error": f"{type(exc).__name__}: {exc}"}
                else:
                    old = saved[len(calls)]
                    if old["request"] != body or old["model"] != model:
                        raise ValueError("prompt or checkpoint differs from replay")
                    response = old["response"]
                calls.append({"model": model, "tick": tick, "assigned": assigned, "request": body, "response": response})
                try:
                    obj = json.loads(response.get("public", ""))
                    if (response.get("model") == body["model"] and response.get("finish") == "eos"
                            and type(obj) is dict and set(obj) == {"choice"} and obj["choice"] in options):
                        choice = obj["choice"]
                        break
                except (ValueError, TypeError):
                    pass
            if choice is None or choice == "leave":
                stop = f"{model} left" if choice == "leave" else f"{model} interrupted"
                break
            if assigned == "both":
                charges = PAIRS[choice]
            else:
                charges.append(CHARGES[choice])
        if len(charges) != 2:
            break
        state, frame = step(state, charges, track, tick)
        frames.append(frame)
        if saved is None:
            print(mode, tick, frame["charges"], frame["positions"], flush=True)
        if frame["home"]:
            stop = "home"
            break
    if saved is not None and len(calls) != len(saved):
        raise ValueError("unexpected calls after world stopped")
    return {"name": mode, "powered": True, "missing_pads": [], "start": [2, 5], "frames": frames,
            "stop": stop, "calls": calls}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("controls", "solo", "pair", "preview", "verify"))
    parser.add_argument("path", type=Path)
    args = parser.parse_args()
    if args.mode == "verify":
        record = json.loads(args.path.read_text())
        if isinstance(record, list):
            expected = controls()
        else:
            if record["name"] not in ("solo", "pair", "preview"):
                raise ValueError("unknown controller")
            expected = play(record["name"], record["calls"])
        if json.dumps(record, sort_keys=True) != json.dumps(expected, sort_keys=True):
            raise ValueError("records differ")
        print("verified", args.path)
        return
    with args.path.open("x") as file:
        data = controls() if args.mode == "controls" else play(args.mode)
        json.dump(data, file, ensure_ascii=False, indent=2)
        file.write("\n")


if __name__ == "__main__":
    main()

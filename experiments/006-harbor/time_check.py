"""Replay one cut-off response with two generation limits, outside the signed room."""
import argparse
import json
from pathlib import Path

from harbor import PIER, infer, interpret, save


def replay(room, output):
    if output.exists():
        raise FileExistsError(output)
    rows = [json.loads(s) for s in (room / "turns.jsonl").read_text().splitlines()]
    index = next(i for i, row in enumerate(rows) if i and row["speaker"] == PIER
                 and row["action"] == "withheld" and row["calls"][0]["finish"] == "length"
                 and rows[i - 1]["speaker"] == "Moderator" and rows[i - 1]["action"] == "post")
    original = rows[index]["calls"][0]["request"]
    short = original["max_tokens"]
    calls = []
    for limit in (short, short * 2):
        body = {**original, "cache_prompt": False, "max_tokens": limit}
        call = infer(body, PIER, recover_final=True)
        try:
            action, words = interpret(PIER, call, [])
        except ValueError:
            action, words = "withheld", None
        calls.append({**call, "eligible_action": action, "eligible_words": words})
    save(output, {"source_opportunity": index + 1, "room_posted": False, "calls": calls})


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("room", type=Path)
    p.add_argument("output", type=Path)
    args = p.parse_args()
    replay(args.room, args.output)

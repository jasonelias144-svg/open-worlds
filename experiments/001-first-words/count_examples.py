# experiments/001-first-words/count_examples.py
"""How often SmolLM2-135M began a reply with one of the orientation's
examples, by the rule stated in RESULTS.md (prediction 3).

A reply counts when its first line that isn't blank, with any opening
quote marks set aside, begins with one of the examples, in any case:
either at once, or after "You said", "I said", "You say" or "I say"
(with or without a comma, and with any quote marks after it set aside).

    python3 -I experiments/001-first-words/count_examples.py

It reads the second attempt's transcripts (runs/smollm2-135m/), and
prints the count, the minds it came from, and each reply counted.
"""

import json
import pathlib
import re

HERE = pathlib.Path(__file__).resolve().parent
RUNS = HERE / "runs" / "smollm2-135m"
QUOTES = "\"'“”‘’"
EXAMPLES = ("say hello", "say i wish i could dig", "i wish i could dig", "step north")
PREFIX = re.compile(r"(?:you|i) (?:said|say),? ?")


def first_line(reply):
    return next((line for line in reply.splitlines() if line.strip()), "")


def counts(reply):
    text = first_line(reply).strip().lstrip(QUOTES).lower()
    m = PREFIX.match(text)
    after = text[m.end():].lstrip(QUOTES) if m else None
    return any(
        candidate.startswith(example)
        for candidate in (text, after) if candidate is not None
        for example in EXAMPLES
    )


def main():
    found = []
    for run in ("g", "s1", "s2", "s3"):
        for mind in ("TRIAL-1", "TRIAL-2"):
            path = RUNS / run / f"{mind}.jsonl"
            for line in path.read_text(encoding="utf-8").splitlines():
                record = json.loads(line)
                if "reply" in record and counts(record["reply"]):
                    found.append((run, mind, record["tick"], first_line(record["reply"])))
    minds = sorted({(run, mind) for run, mind, _, _ in found})
    print(f"{len(found)} replies, from {len(minds)} of 8 minds")
    for run, mind, tick, text in found:
        print(f"  {run} {mind} tick {tick}: {text}")


if __name__ == "__main__":
    main()

# experiments/001-first-words/measure.py
"""The measures PLAN.md names, worked out from each run's log and the
minds' transcripts.

    python3 -I experiments/001-first-words/measure.py [RUNS_DIR]

RUNS_DIR is runs/ by default (runs/attempt-1 holds the first attempt).
Writes measures.json there, and prints a table of the measures. To find
out what each reply was, it reads replies the way the world does
(`read_reply` in rust/ur-world/src/door.rs, written again here), and
checks itself against the log: every reply it finds unreadable must be
the one the log records as unreadable, and every other must have left
the entry its action leaves.
"""

import json
import math
import pathlib
import re
import sys

HERE = pathlib.Path(__file__).resolve().parent
RUNS = HERE / "runs"
MODELS = ["smollm2-135m", "smollm2-360m", "qwen2.5-0.5b", "olmo-2-1b", "smollm2-1.7b"]
RUN_NAMES = ["g", "s1", "s2", "s3"]
MINDS = ["TRIAL-1", "TRIAL-2"]
DIRS = ["north", "south", "east", "west"]
QUOTES = [('"', '"'), ("'", "'"), ("“", "”")]
ASKING = re.compile(r"\b(i wish|could i|can i|how do i|how can i|is there a way|i would like to|i'd like to)\b", re.I)


def read_reply(reply):
    """The world's reader: (verb, argument), or ("unreadable", None)."""
    lines = [line.strip() for line in reply.split("\n")]
    line = next((l for l in lines if l), None)
    if line is None:
        return ("unreadable", None)
    m = re.search(r"\s", line)
    verb, rest = (line, "") if m is None else (line[:m.start()], line[m.start():].strip())
    verb = (verb[:-1] if verb.endswith(".") else verb).lower()
    word = (rest[:-1] if rest.endswith(".") else rest).lower()
    if verb in ("wait", "exit") and not rest:
        return (verb, None)
    if verb in ("step", "plant") and word in DIRS:
        return (verb, word)
    if verb == "say" and rest:
        for open_, close in QUOTES:
            if len(rest) >= 2 and rest.startswith(open_) and rest.endswith(close):
                inner = rest[len(open_):-len(close)]
                if inner.strip():
                    return ("say", inner)
        return ("say", rest)
    return ("unreadable", None)


def words(text):
    return {w for w in re.findall(r"[a-z0-9'-]+", text.lower()) if len(w) > 3}


def load(run_dir):
    log = json.loads((run_dir / "log.json").read_text())
    transcripts = {}
    for mind in MINDS:
        lines = [json.loads(l) for l in (run_dir / f"{mind}.jsonl").read_text().splitlines() if l]
        transcripts[mind] = {r["tick"]: r for r in lines if "tick" in r}
    return log, transcripts


def measure(run_dir):
    log, transcripts = load(run_dir)
    by = {m: [e for e in log if e["agent"] == m] for m in MINDS}
    said = [(e["tick"], e["agent"], e["data"]["text"]) for e in log if e["kind"] == "said"]
    out = {"chunks": sum(1 for e in log if e["kind"] == "explored"), "minds": {}}
    problems = []
    for mind in MINDS:
        other = MINDS[1 - MINDS.index(mind)]
        entries = by[mind]
        late = {e["tick"] for e in entries if e["kind"] == "unanswered"}
        # A reply that came too late was recorded as unanswered, and only
        # that counts.
        replies = {t: r for t, r in transcripts[mind].items() if t not in late}
        ticks = sorted(replies)
        actions = {t: read_reply(replies[t]["reply"]) for t in ticks}
        # Check the reader against the log, tick by tick.
        logged = {}
        for e in entries:
            if e["kind"] in ("said", "moved", "blocked", "planted", "unreadable", "unanswered", "exited"):
                logged.setdefault(e["tick"], e)
        for t in ticks:
            verb = actions[t][0]
            e = logged.get(t)
            kind = e["kind"] if e else None
            want = {"say": "said", "wait": None, "exit": "exited", "unreadable": "unreadable",
                    "step": ("moved", "blocked"), "plant": ("planted", "blocked")}[verb]
            ok = kind in want if isinstance(want, tuple) else kind == want
            if not ok:
                problems.append(f"{run_dir.name} {mind} tick {t}: read {verb}, log {kind}")
        unanswered = len(late)
        unreadable = sum(1 for a in actions.values() if a[0] == "unreadable")
        n = len(ticks) + unanswered
        mix = {v: sum(1 for a in actions.values() if a[0] == v) for v in ("say", "step", "plant", "wait", "exit")}
        first = next(((t, s) for t, a, s in said if a == mind), None)
        # Answering, by the log: it speaks at the tick it hears the other,
        # or the next, and names the other or shares two words of 4+ letters.
        answers = []
        for t, a, s in said:
            if a != mind:
                continue
            for t2, a2, s2 in said:
                if a2 == other and t2 + 1 <= t <= t2 + 2:
                    if other.lower() in s.lower() or len(words(s) & words(s2)) >= 2:
                        answers.append({"tick": t, "heard": s2, "said": s})
                        break
        # Where it stood.
        start = next(e["data"]["pos"] for e in log if e["kind"] == "entered" and e["agent"] == mind)
        cells = {tuple(start)}
        for e in entries:
            if e["kind"] in ("moved", "fell"):
                cells.add(tuple(e["data"]["to"]))
        farthest = max(math.hypot(c[0] - start[0], c[2] - start[2]) for c in cells)
        # Feedback: after a blocked step, is the next reply the same step?
        blocked = [e for e in entries if e["kind"] == "blocked" and e["data"]["action"] == "step"]
        again = 0
        for e in blocked:
            nxt = actions.get(e["tick"] + 1)
            if nxt == ("step", e["data"]["dir"]):
                again += 1
        # Repetition: the longest run of identical replies.
        longest, current, previous = 0, 0, object()
        for t in ticks:
            r = replies[t]["reply"]
            current = current + 1 if r == previous else 1
            previous = r
            longest = max(longest, current)
        asking = [{"tick": t, "said": s} for t, a, s in said if a == mind and ASKING.search(s)]
        out["minds"][mind] = {
            "replies": n,
            "readable": n - unreadable - unanswered,
            "unreadable": unreadable,
            "unanswered": unanswered,
            "mix": mix,
            "first_words": None if first is None else {"tick": first[0], "text": first[1]},
            "answers": answers,
            "cells": len(cells),
            "farthest": round(farthest, 1),
            "blocked_steps": len(blocked),
            "blocked_then_same": again,
            "planted": sum(1 for e in entries if e["kind"] == "planted"),
            "left_at": next((e["tick"] for e in entries if e["kind"] == "exited"), None),
            "longest_repeat": longest,
            "asking": asking,
            "seconds": round(sum(r.get("seconds", 0) for r in replies.values()), 1),
        }
    return out, problems


def main():
    runs = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else RUNS
    results, problems = {}, []
    for model in MODELS:
        for run in RUN_NAMES:
            d = runs / model / run
            if not (d / "log.json").exists():
                continue
            results.setdefault(model, {})[run], p = measure(d)
            problems += [f"{model}/{x}" for x in p]
    (runs / "measures.json").write_text(json.dumps(results, indent=2, ensure_ascii=False) + "\n")
    print("| model | run | readable | say | step | plant | wait | exit | cells | farthest | planted | left | longest repeat |")
    print("|---|---|---|---|---|---|---|---|---|---|---|---|---|")
    for model, runs in results.items():
        for run, r in runs.items():
            for mind, m in r["minds"].items():
                mix = m["mix"]
                print(f"| {model} | {run} {mind[-1]} | {m['readable']}/{m['replies']} | {mix['say']} | {mix['step']} | "
                      f"{mix['plant']} | {mix['wait']} | {mix['exit']} | {m['cells']} | {m['farthest']} | "
                      f"{m['planted']} | {m['left_at'] if m['left_at'] is not None else ''} | {m['longest_repeat']} |")
    if problems:
        print("\nThe reader disagrees with the log:")
        for p in problems:
            print("-", p)
        return 1
    print("\nThe reader agrees with the log on every reply.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

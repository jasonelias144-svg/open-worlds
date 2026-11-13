# experiments/001-first-words/run.py
"""Run experiment 001 as PLAN.md sets out: each model, four runs (greedy,
and sampled with three seeds), two minds of the same model in the garden,
30 ticks each.

    python3 -I experiments/001-first-words/run.py --models DIR --python PY

DIR holds the models, one directory each, named as on the Hub with "/"
written "__" (for example DIR/Qwen__Qwen2.5-0.5B-Instruct). PY is a Python
with torch and transformers. A run whose log is already there is skipped,
so the script can be stopped and started again. `--smoke` runs only the
plumbing check: the smallest model, greedy, 2 ticks, into runs/smoke.
"""

import argparse
import pathlib
import subprocess
import sys

HERE = pathlib.Path(__file__).resolve().parent
REPO = HERE.parent.parent
MIND = REPO / "minds" / "language_model.py"

MODELS = {
    "smollm2-135m": "HuggingFaceTB/SmolLM2-135M-Instruct",
    "smollm2-360m": "HuggingFaceTB/SmolLM2-360M-Instruct",
    "qwen2.5-0.5b": "Qwen/Qwen2.5-0.5B-Instruct",
    "olmo-2-1b": "allenai/OLMo-2-0425-1B-Instruct",
    "smollm2-1.7b": "HuggingFaceTB/SmolLM2-1.7B-Instruct",
}

# The run's name, and its number for the seeds (None: greedy).
RUNS = {"g": None, "s1": 1, "s2": 2, "s3": 3}

TICKS = 30
LIMIT = 600


def mind(python, model_dir, out, index, number):
    words = [f"TRIAL-{index}={python}", "-I", str(MIND), str(model_dir),
             "--transcript", str(out / f"TRIAL-{index}.jsonl")]
    if number is None:
        words.append("--greedy")
    else:
        words += ["--seed", str(10 * number + index),
                  "--temperature", "0.7", "--top-p", "0.95"]
    return ["--mind"] + words


def run(python, model_dir, out, number, ticks):
    out.mkdir(parents=True, exist_ok=True)
    command = ["cargo", "run", "--locked", "-q", "-p", "ur-world",
               "--example", "door", "--",
               "--ticks", str(ticks), "--limit", str(LIMIT),
               "--log", str(out / "log.json")]
    for index in (1, 2):
        command += mind(python, model_dir, out, index, number)
    with open(out / "story.txt", "w") as story, open(out / "stderr.txt", "w") as err:
        done = subprocess.run(command, cwd=REPO / "rust", stdout=story, stderr=err)
    return done.returncode


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--models", required=True, type=pathlib.Path)
    p.add_argument("--python", required=True)
    p.add_argument("--smoke", action="store_true")
    args = p.parse_args()
    if args.smoke:
        name = MODELS["smollm2-135m"].replace("/", "__")
        code = run(args.python, args.models / name, HERE / "runs" / "smoke", None, 2)
        print(f"smoke: exit {code}", flush=True)
        return code
    for short, hub in MODELS.items():
        for run_name, number in RUNS.items():
            out = HERE / "runs" / short / run_name
            if (out / "log.json").exists():
                print(f"{short} {run_name}: already run", flush=True)
                continue
            code = run(args.python, args.models / hub.replace("/", "__"), out, number, TICKS)
            print(f"{short} {run_name}: exit {code}", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())

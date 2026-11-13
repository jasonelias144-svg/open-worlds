# minds/language_model.py
"""A mind whose replies come from a language model, through the Ur-world's
doorway (rust/ur-world/src/door.rs).

Each tick it builds a prompt with the model's own chat template:

- system: the orientation, as the world sent it;
- user: what it sees this tick, as the world sent it, then a blank line
  and "Your action (one line):".

It has no memory beyond that: each tick's prompt holds only the
orientation and that tick's view. It passes the model's raw text back to
the world, which reads it by the same rules as every mind's.

It keeps its own record, one JSON object a line, in the transcript file:
first the model, its settings and the orientation; then, each tick, what
it was shown, what it replied, and how long that took.

    python3 -I minds/language_model.py MODEL_DIR --transcript FILE \\
        [--greedy | --seed N --temperature T --top-p P] \\
        [--max-new-tokens N] [--threads N]

MODEL_DIR is a model downloaded from the Hugging Face Hub. It needs torch
and transformers, which aren't among the repository's requirements: they
are large, and only the experiments use them.
"""

import argparse
import json
import sys
import time

PROMPT_TAIL = "\n\nYour action (one line):"


def arguments():
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("model", help="a model directory from the Hugging Face Hub")
    p.add_argument("--transcript", required=True, help="where to keep the record")
    p.add_argument("--greedy", action="store_true", help="always the most likely token")
    p.add_argument("--seed", type=int, default=0)
    p.add_argument("--temperature", type=float, default=0.7)
    p.add_argument("--top-p", type=float, default=0.95)
    p.add_argument("--max-new-tokens", type=int, default=40)
    p.add_argument("--threads", type=int, default=4)
    return p.parse_args()


def main():
    args = arguments()
    # Imported here, so that --help works without them.
    import torch
    import transformers
    from transformers import AutoModelForCausalLM, AutoTokenizer, GenerationConfig

    torch.set_num_threads(args.threads)
    torch.manual_seed(args.seed)
    tokenizer = AutoTokenizer.from_pretrained(args.model)
    model = AutoModelForCausalLM.from_pretrained(args.model, dtype=torch.bfloat16)
    model.eval()
    # Every setting that shapes the choice of token is given a value here.
    # transformers fills a setting left as None from the model's own
    # defaults (Qwen2.5's are a top-k of 20 and a repetition penalty of
    # 1.1), then from its own (a top-k of 50). Values that switch a filter
    # off keep every model decoded alike: no top-k, no repetition penalty.
    settings = GenerationConfig(
        max_new_tokens=args.max_new_tokens,
        do_sample=not args.greedy,
        temperature=1.0 if args.greedy else args.temperature,
        top_p=1.0 if args.greedy else args.top_p,
        top_k=0,
        repetition_penalty=1.0,
        eos_token_id=model.generation_config.eos_token_id,
        pad_token_id=(
            tokenizer.pad_token_id
            if tokenizer.pad_token_id is not None
            else tokenizer.eos_token_id
        ),
    )
    # What generate will use, after it fills in what was left unset: kept
    # in the record, so that a difference from the settings above shows.
    effective = model._prepare_generation_config(settings)[0]
    used = {k: getattr(effective, k, None) for k in (
        "do_sample", "temperature", "top_p", "top_k", "repetition_penalty",
        "max_new_tokens", "no_repeat_ngram_size", "typical_p", "min_p")}
    transcript = open(args.transcript, "w", encoding="utf-8")

    def keep(record):
        transcript.write(json.dumps(record, ensure_ascii=False) + "\n")
        transcript.flush()

    keep({
        "model": args.model,
        "greedy": args.greedy,
        "seed": args.seed,
        "temperature": None if args.greedy else args.temperature,
        "top_p": None if args.greedy else args.top_p,
        "max_new_tokens": args.max_new_tokens,
        "dtype": "bfloat16",
        "threads": args.threads,
        "torch": torch.__version__,
        "transformers": transformers.__version__,
        "python": sys.version.split()[0],
        "prompt_tail": PROMPT_TAIL,
        "used": used,
    })
    orientation = ""
    first = True
    for line in sys.stdin:
        try:
            message = json.loads(line)
        except ValueError:
            continue
        if not isinstance(message, dict):
            continue
        if "orientation" in message:
            orientation = str(message["orientation"])
            keep({"name": message.get("name"), "orientation": orientation})
            continue
        tick = message.get("tick")
        if not isinstance(tick, int):
            continue
        user = str(message.get("seen", "")) + PROMPT_TAIL
        chat = [
            {"role": "system", "content": orientation},
            {"role": "user", "content": user},
        ]
        inputs = tokenizer.apply_chat_template(
            chat, add_generation_prompt=True, return_tensors="pt", return_dict=True
        )
        started = time.monotonic()
        with torch.no_grad():
            out = model.generate(**inputs, generation_config=settings)
        new = out[0, inputs["input_ids"].shape[1]:]
        reply = tokenizer.decode(new, skip_special_tokens=True)
        record = {
            "tick": tick,
            "user": user,
            "reply": reply,
            "prompt_tokens": int(inputs["input_ids"].shape[1]),
            "new_tokens": int(new.shape[0]),
            "seconds": round(time.monotonic() - started, 3),
        }
        if first:
            # The whole prompt once, as the model saw it, template and all.
            record["prompt"] = tokenizer.decode(inputs["input_ids"][0])
            first = False
        keep(record)
        sys.stdout.write(json.dumps({"tick": tick, "reply": reply}) + "\n")
        sys.stdout.flush()


if __name__ == "__main__":
    main()

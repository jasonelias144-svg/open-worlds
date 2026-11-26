# Replay the Commons discussion

From the repository root, use Python 3 and Cargo. The writer is the experimental joined-room plugin from delivery 11. The verifier also works with the standing, read-only-for-this-purpose room plugin. Each is an external executable. The sketch source in the repository is unchanged. [Known limits of the joined-room prototype](../../sketches/deepseek/012-07-03/README.md#the-rest-and-three-more-2026-11-21)

```sh
scratch=$(mktemp -d)
python3 sketches/deepseek/012-07-03/review/steps.py --now "$scratch/steps"
crate="$scratch/steps/joined-fix/chat-world"
cargo build --manifest-path "$crate/Cargo.toml" --bin chat-world-plugin
writer="$crate/target/debug/chat-world-plugin"
cp -R sketches/deepseek/012-07-03/chat-world-now "$scratch/standing"
cargo build --manifest-path "$scratch/standing/Cargo.toml" --bin chat-world-plugin
reader="$scratch/standing/target/debug/chat-world-plugin"
trial=experiments/003-room-discussion
python3 "$trial/verify.py" --plugin "$reader" --partial "$trial/run-01"
python3 "$trial/verify.py" --plugin "$reader" --partial "$trial/run-02"
python3 "$trial/verify.py" --plugin "$reader" "$trial/run-03"
python3 "$trial/verify.py" --plugin "$reader" "$trial/run-04"
```

Verification checks the signed room with a fresh reader, the two AI admissions, the order and contents of the committed messages, and the exact model inputs against the conversation that existed at each turn. The turn trace is the experimenter's record of local inference. The signed room identifies which guest key posted each utterance. Each process used a disposable key held only in memory.

## Start another discussion

Download the Q4_K_M GGUFs and set the environment variables below to the model file paths. We used llama.cpp b12780 (09c141064), Rust 1.91.1 and four CPU threads per server. Open one terminal per participating model. Runs 01–03 used DeepSeek with SmolLM2. Run 04 used DeepSeek with Qwen. [llama.cpp release](https://github.com/ggml-org/llama.cpp/releases/tag/b12780)

| Model | Pinned weight files | SHA-256 of the Q4_K_M file |
| --- | --- | --- |
| DeepSeek-R1-Distill-Qwen-1.5B | [Unsloth GGUF](https://huggingface.co/unsloth/DeepSeek-R1-Distill-Qwen-1.5B-GGUF/tree/3cb4d15544a2a5e07439592b9a0965b6445fbd34) | `f3bdf9cf31dee4b57ae4e455a1cb0d01b5c2c1b50d72d3112141c195506c2840` |
| SmolLM2-1.7B-Instruct | [Bartowski GGUF](https://huggingface.co/bartowski/SmolLM2-1.7B-Instruct-GGUF/tree/1f03464768bfcc0319fc50da8ff5fb20b6417ba2) | `77665ea4815999596525c636fbeb56ba8b080b46ae85efef4f0d986a139834d7` |
| Qwen2.5-3B-Instruct | [Publisher’s GGUF](https://huggingface.co/Qwen/Qwen2.5-3B-Instruct-GGUF/tree/7dabda4d13d513e3e842b20f0d435c732f172cbe) | `626b4a6678b86442240e33df819e00132d3ba7dddfe1cdc4fbb18e0a9615c62d` |

```sh
llama-server -m "$DEEPSEEK_GGUF" --alias deepseek-local --host 127.0.0.1 --port 18191 -t 4 -c 8192 -np 1 --reasoning-budget 0 --no-webui
llama-server -m "$SMOL_GGUF" --alias smol-local --host 127.0.0.1 --port 18192 -t 4 -c 4096 -np 1 --no-webui
llama-server -m "$QWEN_GGUF" --alias qwen-local --host 127.0.0.1 --port 18193 -t 4 -c 8192 -np 1 --no-webui
```

With the two required servers ready, run the command in the terminal where you built the plugins. The output directory must be new. The driver saves each signed post before offering the peer a turn. Earlier protocols are available as `--mode original`, `--mode peer` and `--mode dialogue`. Run limits and stopping rules are in the [plan](PLAN.md).

```sh
python3 "$trial/run.py" --mode final --plugin "$writer" --output "$scratch/new-room"
python3 "$trial/verify.py" --plugin "$reader" "$scratch/new-room"
```

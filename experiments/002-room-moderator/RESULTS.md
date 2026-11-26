# When should the Commons moderator speak?

A small local DeepSeek model had two chances to decide whether to take the floor. They missed both. When a reviewer selected an invitation, the same model produced a relevant question on their first attempt. The garden participants then had the floor because the adapter never called the model for that room. These were two synthetic conversations replayed on 26 November 2026. [Plan and amendment](PLAN.md)

| Room | Model chooses when to speak | Reviewer selects rehearsal turn 6 |
| --- | --- | --- |
| Rehearsal | Returned the topic, “A quiet way to take a musical turn”, as a statement. The adapter rejected the reply. 14.70 s | “How can you set up a quiet cue for musicians to choose their next solo without raising a hand?” Preview bound to the invitation. 13.37 s |
| Garden | “What is the purpose of comparing two seedlings in this discussion?” The adapter accepted the format. By the agreed criterion this interrupted participants who had chosen their next step. 25.91 s | Waited locally. Zero model calls. 0.11 s |

The rehearsal question picked up the wish to choose a solo quietly and left the decision to the musicians. It largely repeated the request. A more helpful question would have helped them test whether a cue can be seen without interrupting the music, the tradeoff they had already identified. Both runs used the same rooms, so they tell us little about how the model will handle an unfamiliar conversation. [Autonomous run](run-01.jsonl) · [Invited run](run-02.jsonl)

## What the room reader did

The Rust reader verified signatures, returned the visible room and exported the signed log for comparison. Each attempt got only one room's topic and up to twelve visible turns, with room-local speaker numbers and at most 600 characters per turn. A deliberately withdrawn test phrase stayed out of both prompts. The raw fixtures are public, synthetic examples and include that phrase so the check can be repeated. Both exported logs matched the input and both fixture files remained byte-for-byte unchanged. All model output went to the reviewer. [Rehearsal fixture](rooms/rehearsal.json) · [Garden fixture](rooms/garden.json) · [Reader](run.py)

The invitation in the second run was a command-line selection made by the reviewer. A participant's text alone cannot activate it. For a live room we would need a signed participant invitation, a way to withdraw it, and a fresh check before delivery. A useful next trial is a new conversation in which a participant invites a question and withdraws that invitation while the model is answering.

## Repeat the audition

From the repository root, use Python 3, Cargo (tested with Rust 1.91.1) and the chat-world sketch. Build in a scratch directory. The driver talks to the binary through its stdin protocol.

```sh
scratch=$(mktemp -d)
cp -R sketches/deepseek/012-07-03/chat-world-now "$scratch/chat-world"
cargo build --manifest-path "$scratch/chat-world/Cargo.toml" --bin chat-world-plugin
plugin="$scratch/chat-world/target/debug/chat-world-plugin"
COMMONS_TRIAL_PLUGIN="$plugin" python3 -m unittest tests.test_room_moderator
```

We used the four-thread CPU build of llama.cpp b12780 (09c141064), DeepSeek-R1-Distill-Qwen-1.5B and Unsloth's Q4_K_M GGUF, revision `3cb4d15544a2a5e07439592b9a0965b6445fbd34`. The file `DeepSeek-R1-Distill-Qwen-1.5B-Q4_K_M.gguf` has SHA-256 `f3bdf9cf31dee4b57ae4e455a1cb0d01b5c2c1b50d72d3112141c195506c2840`. Start the server in a second terminal with the downloaded file as MODEL_PATH. [Model card](https://huggingface.co/deepseek-ai/DeepSeek-R1-Distill-Qwen-1.5B) · [Pinned weights](https://huggingface.co/unsloth/DeepSeek-R1-Distill-Qwen-1.5B-GGUF/tree/3cb4d15544a2a5e07439592b9a0965b6445fbd34) · [llama.cpp build](https://github.com/ggml-org/llama.cpp/releases/tag/b12780)

```sh
llama-server -m "$MODEL_PATH" --alias deepseek-local --host 127.0.0.1 --port 18191 -t 4 -c 8192 -np 1 --reasoning-budget 0 --no-webui
```

Run each audition in the first terminal. The baseline command exits with status 1 when a reply fails validation, as happened in the recorded rehearsal. The driver prints JSON Lines with the actual prompts, visible replies, token counts, errors and elapsed time per room. The amended driver groups calls under `attempts`. Each call uses greedy decoding, seed 42 and a limit of 1,536 output tokens. Timing includes room verification.

```sh
python3 experiments/002-room-moderator/run.py --plugin "$plugin" --baseline
python3 experiments/002-room-moderator/run.py --plugin "$plugin" --invite rehearsal:6
```

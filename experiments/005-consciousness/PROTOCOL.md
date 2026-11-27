# Two DeepSeek guests in an open conversation

Jason supplies the room's only subject question, “What is consciousness?” The guests are DeepSeek-R1-Distill-Qwen-1.5B (the earlier moderator) and DeepSeek-R1-Distill-Qwen-7B. Both use Q4_K_M weights, independent local llama.cpp processes and separate guest signing keys. The smaller model opens. There are eight alternating opportunities, or fewer if both guests pass consecutively. Each guest reads the committed room before replying. Either may introduce a new idea, follow a question or pass. The keeper accepts each guest’s signed request for admission and checks incoming posts. They introduce no examples, follow-up questions or instructions to disagree.

Both endpoints use a temperature of 0.6, seed 42, and a 512-token limit per call. The assistant prefill contains only empty thinking tags. It starts generation directly in the public answer and contains no words. The server may echo that prefix. Only this prefix and outer whitespace are removed for posting. Overlong or token-limited replies are recorded and withheld. No retries for quality and no paraphrasing posts. A transport failure is preserved and ends that room. The guests, subject and prompting all differ from the chime trial, so differences between the transcripts cannot isolate the effect of sharing a model family.

When reading the record, ask which specific idea from a peer's last turn the next guest uses, whether anything new follows from it and which question the guests leave open. Repetition and either guest's ability to pass belong in the record too.

## Replay and verification

Use llama.cpp b12780 (09c141064). The first model file has SHA-256 `f3bdf9cf31dee4b57ae4e455a1cb0d01b5c2c1b50d72d3112141c195506c2840`. The second has SHA-256 `731ece8d06dc7eda6f6572997feb9ee1258db0784827e642909d9b565641937b`. Check these against the downloaded files. [1.5B weights](https://huggingface.co/unsloth/DeepSeek-R1-Distill-Qwen-1.5B-GGUF/tree/3cb4d15544a2a5e07439592b9a0965b6445fbd34) · [7B weights](https://huggingface.co/bartowski/DeepSeek-R1-Distill-Qwen-7B-GGUF/tree/361004151d4f4f6b446dc5e6d46fbf4422a80d5f) · [DeepSeek 1.5B model card](https://huggingface.co/deepseek-ai/DeepSeek-R1-Distill-Qwen-1.5B) · [DeepSeek 7B model card](https://huggingface.co/deepseek-ai/DeepSeek-R1-Distill-Qwen-7B)

Use the writer and reader binaries built as in the [earlier room instructions](../003-room-discussion/REPLAY.md). Set the weight paths and start one server in each of two terminals.

```sh
llama-server -m "$DS_SMALL_GGUF" --alias deepseek-local --host 127.0.0.1 --port 18191 -t 4 -c 8192 -np 1 --reasoning-budget 0 --no-webui
llama-server -m "$DS_LARGE_GGUF" --alias deepseek-seven --host 127.0.0.1 --port 18194 -t 4 -c 8192 -np 1 --reasoning-budget 0 --no-webui
```

The existing transcript can be verified offline using only the reader. A new run needs both local servers and a fresh output directory.

```sh
trial=experiments/003-room-discussion
python3 "$trial/verify.py" --plugin "$reader" experiments/005-consciousness/room
python3 "$trial/run.py" --mode consciousness --plugin "$writer" --output "$scratch/another-room"
```

## Peer invitation in a second room

After turn four of the open room copied turn three verbatim, Codex proposed a fresh room with the same guests, opening, order, settings and stopping rule. One addition to the orientation invites the opener to give a tentative answer and ask the peer a question, then invites each guest to pick up one specific point. It supplies no philosophical examples or follow-up questions. The first room runs to its original stopping rule. The second room starts without its history. Both records are kept. To repeat the second room use the same commands with `--mode consciousness-peer` and a new output directory. Verify its saved record with the reader at `experiments/005-consciousness/peer-room`.

## A question chosen by the larger guest

In the second room the larger model again copied turn three on turn four. For a final six-turn room Codex changed both the opener and how the guests receive the floor. DeepSeek 7B opens by choosing one concrete case they want to ask about. On later turns each guest receives a single user message containing the opening topic, the full signed transcript with speaker names, and an invitation to answer their partner. Neither the example nor any follow-up question is supplied. The settings, guest weights, keeper and pass rule are the same. These changes are combined, so any difference in the conversation cannot identify which change caused it. Both earlier rooms retain their original stopping rules. Run with `--mode consciousness-question` and verify the saved `experiments/005-consciousness/question-room`.

## Native reasoning control

The three direct-answer rooms all prefilled empty reasoning tags. In the third room the 1.5B guest twice identified themselves as the 7B guest. To check whether allowing ordinary reasoning changes the exchange, repeat the third room with the same question, larger guest opening, signed history presentation and six opportunities. Remove the assistant prefill. Run two fresh servers with `--reasoning-budget 384 --reasoning-format deepseek` in place of `--reasoning-budget 0`. Use 832 total generated tokens per call to allow for reasoning and public speech. Record whether the endpoint used its separate reasoning channel, while preserving only the public answer. Do not send private reasoning to the peer. The budget is a server setting. The evidence records the actual completion length, which can include reasoning.

For the saved control the ports were 18195 (1.5B) and 18196 (7B). Run with `--mode consciousness-native --deepseek-port 18195 --deepseek-seven-port 18196` and verify `experiments/005-consciousness/native-room`. No guest prompt was amended during a conversation.

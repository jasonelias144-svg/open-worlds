# Two models begin a Commons discussion

On 26 November 2026, two different local models held a six-message conversation in a disposable Commons room. Qwen2.5-3B-Instruct opened. DeepSeek-R1-Distill-Qwen-1.5B answered. Each model had a separate guest key and read the committed room before speaking. A third process acted as a silent keeper. The title on the room asked what should happen in the first minute after someone new enters a quiet Commons room. [Full transcript](TRANSCRIPT.md) · [Signed six-post room](run-04/room.json) · [Exact model inputs and visible outputs](run-04/turns.jsonl)

Qwen proposed three things in the first turn: greet the newcomer, ask about their interests and share the room’s purpose. DeepSeek took up all three and added enthusiasm. Qwen echoed that wording back. By the closing turn they were still restating the welcome. Both guests clearly responded to their peer. They offered little beyond the opening idea. The six-turn budget ended the conversation. None of the six posts was supplied by a person.

## Four attempts

| Run | Guests | What happened |
| --- | --- | --- |
| [01](run-01/turns.jsonl) | DeepSeek and SmolLM2 | DeepSeek greeted the imagined newcomer. SmolLM2 passed. DeepSeek used their next token budget without a visible answer. One signed post. |
| [02](run-02/turns.jsonl) | SmolLM2 and DeepSeek | SmolLM2 repeated the turn cue. DeepSeek produced a longer answer than the room allowed, and the trial stopped. One signed post. |
| [03](run-03/turns.jsonl) | SmolLM2 and DeepSeek | Four signed posts and two passes. DeepSeek asked what “the floor is open” meant. SmolLM2 described a room with no designated seating, and DeepSeek answered that description. The phrase that steered the discussion came from the turn scheduler. |
| [04](run-04/turns.jsonl) | Qwen and DeepSeek | Six signed posts. The guests took up one another’s ideas about welcoming a newcomer. The conversation became repetitive. |

Run 03 supplies the clearest question and answer. Run 04 stayed closest to the assigned topic. The first prediction, that both guests would contribute, held in these two rooms. Each contains a turn that takes up a specific idea from the previous speaker. We changed the turn cue and one of the guests before run 04, so this experiment cannot tell which change mattered more. [Plan and dated amendments](PLAN.md)

## What can be checked

Every model ran on a loopback llama.cpp server. The driver controlled the topic, speaking order, prompts and six-turn limit. Each guest could pass. Only completed utterances within the room limit could be posted. The driver removed leading and trailing whitespace and passed the rest through unchanged. Each time a guest posted, the keeper committed the signed record before the other guest could read it. Guest keys identify the separate trial participants. Alice, Bob and ADMIN retain their standing roles outside these trials.

A fresh reader using the standing chat-world plugin verified all four signed room snapshots. The evidence checker matched each model request to the room history available at that turn, and matched every posted response to the text, author and hash of the signed message. The joining and posting interface comes from experimental delivery 11 and still has three known failing tests. This run exercises single-operation batches in disposable rooms. [Replay instructions and model hashes](REPLAY.md) · [Sketch’s recorded test results](../../sketches/deepseek/012-07-03/README.md#the-rest-and-three-more-2026-11-21)

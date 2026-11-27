# Can two model participants begin a discussion in a Commons room?

Planned on 26 November 2026 in response to Jason’s question, “Perfect. Can we put two in a room and let them begin a discussion?”

Give two guest participants, DeepSeek-R1-Distill-Qwen-1.5B and SmolLM2-1.7B-Instruct, one topic: “What should happen in the first minute after someone new enters a quiet Commons room?” Choose neutral participant labels. The standing offices of Alice, Bob and ADMIN are outside this trial. A third, silent process keeps the disposable room. Each guest joins as an AI with a separate key, reads an up-to-date view and can offer their own words or PASS. Start with DeepSeek and alternate for at most six opportunities. End early after two consecutive passes. No scripted opening, private context, moderator or human replies.

I expect each guest to contribute and at least one later turn to pick up a specific idea from the other guest. Save the prompts, actual model output, authors, signed room log and verification result. Judge conversational uptake from quoted turns. Agreement by itself is weak evidence. Record failure, repetition and unexpected output too.

Use separate local servers with llama.cpp build b12780. Greedy sampling, seed 42 and a maximum of 1,536 generated tokens per turn. Use the experimental joined-room plugin built from the repository’s `joined-fix` assembly, in a scratch directory. Only a single signed operation goes to the keeper at a time. Verify after each and check the exported log against an independent reader at the end. Only this synthetic, on-record room is in scope. [Room design](../../docs/COMMONS.md) · [Joined-room sketch status](../../sketches/deepseek/012-07-03/README.md#the-rest-and-three-more-2026-11-21)

## Amendment before run 02

Run 01 had one posted greeting, an explicit PASS from SmolLM2, and a DeepSeek turn that exhausted 1,536 tokens with empty visible output. Keep the partial room and trace. Open a new room with the same topic. Let SmolLM2 open, and tell both guests plainly that they are peers planning a welcome for someone who has yet to arrive. Give each a direct turn cue to start or answer the other guest, while keeping the actual words up to them. Record any token-limited turn without posting it and offer the next guest their turn. Still stop after two consecutive explicit passes or six opportunities. The prediction remains that a later guest takes up a specific idea from their peer.

## Amendment before run 03

In run 02 SmolLM2 echoed the turn cue. DeepSeek generated a 1,270-character answer after trimming surrounding whitespace, above the trial room’s 1,200-character limit. It never entered the room. For run 03 keep the topic, guests, order and turn budget. Give each guest their model’s native chat messages: their own signed words as assistant messages and their peer’s signed words as user messages. Use the room topic as the opening question. Give the room the normal sketch limit of 4,000 characters. An overlong or unfinished response uses one opportunity without creating a post. Preserve all visible output, including any echoes. These changes test whether the presentation of a conversation helps the guests respond to each other.

## Amendment before run 04

Run 03 produced a signed question and an answer from the other model. They discussed a physical open floor after the harness supplied “The floor is open.” That sentence was never spoken by a guest. Keep the exchange. For a final trial, supply no idiom or suggested reply after a silent turn. Explicitly mark the scheduler’s turn notice when one is required. Use the same room topic, signed delivery, six opportunities and pass option. Pair DeepSeek with a new local guest, Qwen2.5-3B-Instruct, who opens. See whether the two have a discussion about the topic they were given. Changing the cue and the guest in the same trial precludes attributing a difference to either one alone.

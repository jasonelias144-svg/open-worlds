# Can two model participants begin a discussion in a Commons room?

Planned on 26 November 2026 in response to Jason’s question, “Perfect. Can we put two in a room and let them begin a discussion?”

Give two guest participants, DeepSeek-R1-Distill-Qwen-1.5B and SmolLM2-1.7B-Instruct, one topic: “What should happen in the first minute after someone new enters a quiet Commons room?” Choose neutral participant labels. The standing offices of Alice, Bob and ADMIN are outside this trial. A third, silent process keeps the disposable room. Each guest joins as an AI with a separate key, reads an up-to-date view and can offer their own words or PASS. Start with DeepSeek and alternate for at most six opportunities. End early after two consecutive passes. No scripted opening, private context, moderator or human replies.

I expect each guest to contribute and at least one later turn to pick up a specific idea from the other guest. Save the prompts, actual model output, authors, signed room log and verification result. Judge conversational uptake from quoted turns. Agreement by itself is weak evidence. Record failure, repetition and unexpected output too.

Use separate local servers with llama.cpp build b12780. Greedy sampling, seed 42 and a maximum of 1,536 generated tokens per turn. Use the experimental joined-room plugin built from the repository’s `joined-fix` assembly, in a scratch directory. Only a single signed operation goes to the keeper at a time. Verify after each and check the exported log against an independent reader at the end. Only this synthetic, on-record room is in scope. [Room design](../../docs/COMMONS.md) · [Joined-room sketch status](../../sketches/deepseek/012-07-03/README.md#the-rest-and-three-more-2026-11-21)

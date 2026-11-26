# Can a shared problem sustain a chain of decisions?

Jason asked on 26 November 2026 whether each decision could lead the guests to a new question. The rehearsal-room discussion in Experiment 003 often circled back to its opening suggestion. Here the room can answer a question experimentally, and the guests can decide what to ask next.

## Before inference

Seat Qwen2.5-3B-Instruct and DeepSeek-R1-Distill-Qwen-1.5B in two fresh signed Commons rooms. Qwen opens the first and DeepSeek opens the second. Assign each room a different random sounding chime among A through H before collecting any replies. Neither guest receives the target, a suggested first test, a list of remaining candidates, or a worked solution. Commitments are SHA-256 over the UTF-8 string `chime-v1/{trial}/{target}/{salt}`. Publish the targets and salts after the runs.

- Trial 1: `6fa24cdeeec9b663ba3d5337f3c95fb6516cc2cf6343873b9176036f3b9d7170`
- Trial 2: `3540cd6ee5230b9de112764f7d4caac2d044b37d9f53467922be823020d96e8a`

On a turn either guest can talk to the other, temporarily damp any nonempty proper subset of the chimes, name one chime, or pass. If the sounding chime was damped, the sound stops. Otherwise it continues. Each room allows four tests. A solution is accepted when the signed clues uniquely identify the named chime. A premature name yields no new clue. Guests write their own words and choose their own moves. The keeper signs the test outcomes separately from the guest messages.

Allow up to twelve puzzle opportunities per room and stop early after two consecutive passes. When solved, when four tests leave ambiguity, or at the puzzle turn limit, offer up to four open turns with no assigned next question or further puzzle feedback. In this phase the guests can discuss what they choose or pass. Partial, invalid and unproductive turns stay in the record.

**Readouts before the run**

1. Count narrowing tests and calculate the candidate set from signed evidence after each one. Did at least two successive tests narrow the field, did both guests contribute to the decision chain, and did they name a justified solution?
2. Read the guests’ language. Did either use a clue or something their peer proposed to choose the next move? A mechanical change in the candidate count alone does not answer this question.
3. Once the keeper stops supplying clues, does a guest raise a distinct new question or proposal and does the peer develop it? Record separately whether that follow-up is actually answered or merely proposed. The four-turn bound cannot establish indefinite discussion.

Use the same local model weights and loopback servers as Experiment 003, greedy decoding, seed 42, and at most 1,536 tokens per call. The response format identifies speech and an optional game move. [Previous room experiment and model hashes](../003-room-discussion/REPLAY.md)

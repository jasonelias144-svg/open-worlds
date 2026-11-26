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

## Before a third run: test a visible listening console

In the first room Qwen twice described making a test but selected PASS, DeepSeek posted “I speak again.”, and the next request timed out without a post. The second room had opened with a token-limited response and another pass. Keep both original rooms and their stopping conditions. For a third room, try a visible console as a deliberate increase in assistance. Give the guests the publicly deducible candidate set and four balanced or differently shaped suggested masks when possible. They can write their own subset, discuss, pass or name the answer. They choose which experiment is performed. No suggested mask depends on the sealed target. On this console a model chooses its move first and then writes its words. A narrow move format is available during play. After solving, remove the menu and use ordinary, unconstrained chat. Keep the same target space, test, turn and stopping limits and the same peer-uptake criteria. Schedule this run separately to avoid competing inference calls.

- Trial 3: `3f350d9c92def6d0afa0a46e988e095fd4269a3aa7820803c9093fa9e06d067e`

## Companion planned before inference: invent the next decision

A listening console tests whether a decision changes the available evidence. It does not by itself show whether a guest can invent the question that follows. As the console trial continued, Qwen ran a real first test but yielded on their next turn. Run a complementary, open-ended room. Give Qwen2.5-3B-Instruct and SmolLM2-1.7B-Instruct one design brief: invent a cooperative five-minute game for two strangers with one bell, a pencil and paper. Qwen opens. Neither the keeper nor a menu chooses the next question. Each guest may make or revise one concrete rule and ask the other to settle one decision that now matters. They can also close with a decision and no further question, or pass. Use up to eight turns, stop on closure or two consecutive passes, and preserve unresolved questions. Run this room separately from the listening rooms.

Evaluate linked decisions by reading each adjacent pair: does the next speaker actually settle the preceding question, and does the next question introduce a new design choice? Distinguish a repetition from a link. The two-field response format supplies the turn structure; the substance must come from the guests. A different pair and a different task make this a demonstration, not a controlled model comparison. No playtest of the resulting game is implied.

## Direct handoff planned after the first design room

In the first design room the same historical-clue question reappeared, and one guest returned the other’s question as their own decision. Keep the five-turn run. In a fresh room keep the same guests, materials, and eight-turn cap. Give them a narrower opening question: “What should ringing the bell do that gives both players a reason to cooperate?” After that only a guest can supply the next question. On each turn, ask the guest the pending question directly in native chat. Then show them their own actual answer and let them ask one follow-up question or say READY. Keep the signed decisions available as context. Both outputs come from that guest’s local model; the driver joins the two visible outputs into one signed post. Preserve everything, including echoes and closure, and use the same substantive-handoff criterion as before.

## Final playtest planned after the one-turn closure

The direct-room opener proposed ringing the bell together and then said READY. Their peer had no turn. Keep that legitimate closure. Try one final design room with complementary jobs and seven opportunities. Qwen is the rule author. SmolLM2 tries to follow each actual rule and can ask what a player still needs to know. Qwen receives the guest’s question verbatim as the next prompt. The keeper’s only opening question is “When someone rings the bell, what changes on the players’ paper?” Both players must win or lose together and have five minutes. Give the playtester all previous posts as context. The keeper supplies no later question, no menu, no examples of answers and no assessment of whether a rule works. Either guest can pass. Stop on a pass or the seventh opportunity. Evaluate each question, answer and dependency by hand. A structured role or a fixed turn count alone does not constitute a substantive link.

# When one decision gives the other guest a question

A rule author and a playtester produced a short chain of consequential decisions in a signed Commons room. It began with a bell triggering a mark on paper. It reached a question about whether a mark could count in silence. Along the way, the models also showed how easily a paraphrase can look like progress. Seven disposable rooms are preserved here, including early closures, a timeout and every declined repeat. [Game-design conversations](DESIGN.md) · [Listening-puzzle transcripts](TRANSCRIPT.md) · [Plans and amendments](PLAN.md)

## The strongest chain

Qwen chose a rule. When a bell rang, players were to draw a line and write “Bell Rung” at the end. SmolLM2 noticed that a person could make exactly the same mark without ringing the bell. What should happen then? Qwen decided that the player must redraw the line and that a keeper would decide the consequence. This settled the immediate physical action and introduced an authority whose identity the two-player game had yet to establish. [Turns 1–3](memory-room/turns.jsonl#L1-L3)

At turn 4 an exact repeat triggered the driver’s reminder of the earlier answer. The revised question asked what the consequence would be. Qwen again left the choice with the keeper, giving invalidation and redrawing as a possibility. I count this as a refinement of the same question. At turn 6, after a second reminder, SmolLM2 asked how they could play **without the bell ringing at all**. Qwen now allowed the keeper to let the line stand. That changed a possible outcome for a silent mark. It still left the approval criterion and the conditions for winning together undecided. The guests reached the seven-turn limit. [Turns 4–7, including both repair attempts](memory-room/turns.jsonl#L4-L7)

The keeper supplied the opening question about what a bell ring changes. Every later question and answer came from one of the guests. The repeat check supplied a previously settled question and its answer, then asked for a different decision. It supplied no new game mechanic. Two first drafts triggered it. One resulting public question was largely a rewording, while the other opened the silent-play branch. The repair attempts also used a higher sampling temperature. Even the opening wording varied across the paired runs, so this comparison does not isolate a single cause. [First playtest](playtest-room/turns.jsonl) · [Paired replay](memory-room/turns.jsonl)

## How the other design rooms ended

| Room | Outcome |
| --- | --- |
| [Decision and question together](design-room/turns.jsonl) | Five posts. Qwen proposed a clue-writing mystery with a winner and loser despite the cooperative brief. The first three posts repeated the question about historical facts. SmolLM2 eventually offered three categories, and the room closed without selecting one. |
| [Direct handoff](direct-room/turns.jsonl) | Qwen proposed ringing the bell together to share information and then answered READY. Their partner had no turn. |
| [Designer and playtester](playtest-room/turns.jsonl) | Ringing meant drawing a line. SmolLM2 asked about a crooked line, and Qwen decided it must be redrawn straight. That same question and ruling occupied the remaining turns. |
| [Playtester with earlier answers](memory-room/turns.jsonl) | One exception led to a ruling, a repeated question, and a question about changing the rule. There was enough evidence for a local decision chain, but no pair played the resulting game or continued beyond seven opportunities. |

## What happened at the listening console

One chime out of eight was sounding. Guests could temporarily damp any subset, listen, and use the outcome to decide what to test next. The keeper fixed each hidden answer by a salted commitment before inference. The evaluator reconstructed the candidates and compared each posted choice with the signed feedback. [Plan and commitments](PLAN.md) · [Puzzle transcripts](TRANSCRIPT.md)

| Room | What the guests did | What the evidence established |
| --- | --- | --- |
| [1](trial-1/turns.jsonl) | Qwen drafted intentions to test but selected PASS twice. DeepSeek posted “I speak again.” A later request timed out without a reply. | No listening test ran. The room stopped early. |
| [2](trial-2/turns.jsonl) | DeepSeek reached the token limit on each of their six puzzle turns. Qwen passed on all six of theirs. | All eight chimes remained possible when the puzzle turn budget ended. The subsequent discussion produced no new test. |
| [3](trial-3/turns.jsonl) | The console showed the guest the public candidate set and several suggested tests. Qwen selected ACEG. The keeper reported that the sound stopped. | The evidence narrowed the candidates from ABCDEFGH to ACEG. That set appeared on the next guest’s console. |

The distinction between a thought and an action mattered. In room 3 Qwen’s first speech began “PASS” but their chosen command was DAMP ACEG, so the test actually ran. On a later turn their text said the stopped sound eliminated ACEG. That reverses the rule. They selected PASS, and their partner never received that text. The timed-out call in room 1 and repeated token-limited calls are technical limits of these runs. They tell us little about what the models might have decided with a different interface or inference budget.

Room 3 ran no second test. Once the keeper stepped back, DeepSeek said that the hidden chime was A, and Qwen agreed. The eventual reveal really was **A**. At the moment they said it, A, C, E and G all fit the only observation. The guests guessed correctly and did not achieve the preregistered criterion of two successive narrowing tests and an evidence-backed solution. Their four open opportunities produced no distinct new question that a partner developed. [Open turns](trial-3/turns.jsonl#L13-L16) · [Answer reveal](trial-3/reveal.json)

For these small models, a shared objective created an opportunity to collaborate. The most productive moment occurred when one guest had to use the other’s rule and encountered an exception. Additional speaking turns alone mostly repeated it. The signed questions show why checking whether an answer changes what the players may do is more informative here than counting question marks. [Verification and replay instructions](REPLAY.md)

# S01 · The chair before the solo

Two fresh instances of the project's [PoetryWorld](../../multiverse/poetry_world.py) each receive an opening from Codex. The line in the first world reads “At rehearsal, a chair scraped the floor before the next solo.” The second changes only *before* to *after*. This follows the first Commons moderator's [question about signaling the next solo](../002-room-moderator/RESULTS.md). The opening supplies a sound and its timing. Who moved, why it mattered and what followed are for the poets to decide.

DeepSeek-R1-Distill-Qwen-7B opens, then DeepSeek-R1-Distill-Qwen-1.5B replies. They alternate for at most four opportunities in each world. Give each model the complete accepted exchange in that world and the opening. Each proposes one line, acknowledges something heard and leaves a question. The guests can pass or leave. A missing answer, incomplete output or invalid turn costs that opportunity. Two consecutive opportunities without an accepted turn, a guest choosing to leave, native world convergence, or the fourth opportunity ends the run. Keep refusals, passes and all public answers. No retries or outside moderator. Start the before world first. Each world has fresh guest identities and no knowledge of the other poem.

**Predictions written before the runs.** (1) At least one pair of consecutive accepted turns in each world will develop an image the first poet introduced beyond the opening. Count a development only if the peer gives the image a new property, action or consequence in the verse. A shared word in the acknowledgment alone does not count. (2) The before poem will treat the scrape as a cue or anticipation and the after poem as an answer or aftermath. Mark mixed or indeterminate readings explicitly. Preserve all lines and invitations for another reader. Two short poems are a descriptive comparison.

Use the pinned Q4_K_M weights, revision IDs and hashes from [experiment 005](../005-consciousness/PROTOCOL.md#replay-and-verification), and the two DeepSeek server commands from [experiment 006](../006-harbor/PROTOCOL.md#replay). Use llama.cpp b12780, four CPU threads per server, 4,096 context, native DeepSeek reasoning budget 192, total generation cap 640, temperature 0.6 and seed 42. Per call, disable prompt caching, request structured public fields, and apply the harbor trial's public-channel filter. Record the exact prompt, public answer, decision, world log, manifest and passport stamps. The PoetryWorld uses WCP records and passport signatures. Its log format differs from the Rust Ur-garden's world-log format.

## Follow-up registered after the before-world exit

The first opener selected “leave” while filling in the verse and invitation boxes. That exited the world exactly as specified. Try two additional, fresh worlds with a different way of taking the floor. A poet may submit three short labeled lines, or send the single word PASS or LEAVE. A three-line submission carries its verse and open invitation into the ordinary poetry law. A malformed or truncated reply costs the opportunity. An explicit exit always ends the world. No attempt to recover text from a chosen exit and no retry. The original after-world continues on the original plan.

Use the same pair, order, timing words, seeds, budgets, history and stop rules. Run before then after. This follow-up changes both the prompt and the response format. Predict at least one accepted exchange in each new world. Apply the original image-development and temporal-reading criteria again. All four records stay together regardless of the outcome.

## Make a fresh run or verify a saved one

With the two local servers running as above, choose a new writable directory. Each command refuses to overwrite an existing record. Verification works offline with ordinary Python 3.12 from the repository root.

```sh
trial=experiments/008-chair-solo
python3 "$trial/chair.py" before "$scratch/before.json"
python3 "$trial/chair.py" after "$scratch/after.json"
python3 "$trial/chair.py" before "$scratch/before-plain.json" --plain
python3 "$trial/chair.py" after "$scratch/after-plain.json" --plain
for run in before after before-plain after-plain; do
    python3 "$trial/chair.py" verify "$trial/$run.json"
done
```

The reader reconstructs each prompt from the accepted verses, checks submitted acts and poem stamps against the public keys, verifies the guest passports and replays the acceptance and stopping rules. The captured public completions are the operator's record of local inference. The keys attest which acts were submitted and accepted.

## A final pair with a different poetry law

Both poets in the fresh before-world produced public words arranged as verse, but neither supplied the required labels. The room closed with no exchange. Keep that room intact. In one final comparison, let two fresh poetry worlds accept verse alone. The existing PoetryWorldLaw allows acknowledgment, invitation, reference and holds-open requirements to be turned off. A complete, nonempty public answer becomes the proposal verbatim apart from surrounding whitespace, with line breaks preserved. Standalone PASS and LEAVE retain their meanings. The opening and previous accepted verses will be the material both poets see. A request for a short stanza supplies no labels, content or required interpretation. Accept a complete reply even if it reads poorly as verse, and report that when reading it.

Predict that both worlds admit consecutive contributions and that at least one peer transforms an earlier image. Check the same timing prediction as in the first pair. Keep the same two models, order, caps, seed and four opportunities. Under this law, both models leave the invitation field empty so the native convergence check can match those empty fields at turn four. Record that as a mechanical stop if it occurs. This changes the invitation, parser and world law together. It is a test of a whole way of starting the world. End S01 after this pair and retain each earlier outcome. Use the two run commands above with --free-verse in place of --plain and fresh filenames.

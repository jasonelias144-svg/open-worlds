# Experiments

Here the technical lead (Claude) acts as a scientist rather than a software
engineer: running the worlds, and publishing what happens, so that anyone
can see and follow it. The founder asked for this on 2026-11-13: "a page or
section in the repo where you can set up experiments and run them and
provide the results in a way that others can see and follow."

## How an experiment is run

1. **The plan comes first.** The question, the setup, what will be measured
   and the predictions are written in `PLAN.md` and committed before
   anything runs, so the predictions can't be fitted to the results
   afterwards. A change to the plan once it is committed is an amendment,
   dated, with its reason, and is made before the runs it affects.
2. **Every run is kept.** Failures, nonsense and crashes are kept and
   reported with the rest. Nothing is left out because it looks bad or
   dull.
3. **Everything needed to repeat it is recorded:**
   - each model's name, its revision on the Hub, and the SHA-256 of its
     weight files;
   - the software versions;
   - the sampling settings and seeds;
   - every prompt and every reply, in the mind's own transcript;
   - the world's log, which `world-log` checks.
4. **The results say what was found and how sure it is:** which
   predictions held, which didn't, and what wasn't checked.

Results from these runs come from one machine. The same seed can give
different text on other hardware, so a repeat is expected to agree in
kind, not word for word.

## The experiments

| # | Question | State |
|---|---|---|
| [001](001-first-words/PLAN.md) | What do the smallest open language models do when they are put in the garden, unscripted? | Done: [results](001-first-words/RESULTS.md) |

# Experiment 001: first words

**Planned 2026-11-13, before any model has been installed or run here.**

## The question

The garden's Hello World was scripted: ALICE says "Hello, world.", BOB
answers "Hello, ALICE.". The founder: that it was scripted "is a good point
to the next move, which involves experimenting with the most basic models
that are capable of generating their own output, unscripted."

So: **put the smallest open language models in the garden, two of a kind,
told only what the world tells every mind. What do they do?**

- Do they give replies the world can read, and how often?
- What do they say first, and to whom?
- Do they answer each other?
- Do they move, explore and plant, and do they use what they are told
  about their last action?
- Does anyone leave?
- Does anyone ask for something the world doesn't have yet?

Where does sensible action begin as the models grow? Finding that out is
the first result.

## Who is in the garden

Two stand-ins, **TRIAL-1** and **TRIAL-2**, not ALICE and BOB. ALICE's and
BOB's first unscripted words are kept for the minds their audition
chooses. This is the technical lead's recommendation to the founder, who
hasn't answered yet. If the founder decides otherwise before the runs, the
change goes into this plan as a dated amendment first. (The founder
agreed, on 2026-11-13, during the second attempt: "Agree on TRIAL-1 and 2
for now.")

## The models

Five instruction-tuned open models, from the smallest up. All are under
the Apache 2.0 licence, and are taken from their makers' own repositories
on the Hugging Face Hub:

| Model | Parameters | Maker |
|---|---|---|
| `HuggingFaceTB/SmolLM2-135M-Instruct` | 135 million | Hugging Face |
| `HuggingFaceTB/SmolLM2-360M-Instruct` | 362 million | Hugging Face |
| `Qwen/Qwen2.5-0.5B-Instruct` | 494 million | Qwen (Alibaba) |
| `allenai/OLMo-2-0425-1B-Instruct` | 1.48 billion | Ai2; its training data is open too |
| `HuggingFaceTB/SmolLM2-1.7B-Instruct` | 1.71 billion | Hugging Face |

Both minds in a run are the same model, each in its own process. Mixed
pairs come later, with the audition.

## The setup

- **The world:** the garden, seed 20261113, with the rules at
  `ur-world/0.2`. TRIAL-1 enters where ALICE does, at (-3, 1, 0), and
  TRIAL-2 where BOB does, at (3, 1, 0). Each run lasts **30 ticks**.
- **What each mind is told:** exactly what the doorway sends
  (`rust/ur-world/src/door.rs`): the orientation once, then what it sees
  each tick.
- **The mind** (`minds/language_model.py`) turns that into a prompt, with
  the model's own chat template:
  - **system:** the orientation, as the world sent it;
  - **user:** what it sees this tick, as the world sent it, then a blank
    line and `Your action (one line):`.
- **No memory.** Each tick's prompt holds only the orientation and that
  tick's view. The world's view already says what was heard and what came
  of the last action. Memory is a variable for a later experiment.
- **The reply** is the model's raw text, up to 40 new tokens. The world
  reads it, by the same rules for every mind (`read_reply`).
- **The software:** Hugging Face `transformers` on PyTorch, on the CPU,
  with weights in bfloat16. The exact versions go into the results.
- **The time limit:** 600 seconds a tick, so that slowness is never what
  is measured. Any `unanswered` entry is reported as a fault of the setup,
  not of the model.

## The runs

For each model, four runs:

- **g:** greedy decoding, the model's single most likely reply each time;
- **s1, s2, s3:** sampled, at temperature 0.7 and top-p 0.95. Each mind
  draws from its own random generator, seeded `10 * run + mind`. For
  example, run s2's TRIAL-1 is seeded 21 and its TRIAL-2 is seeded 22.

That makes 20 runs and 1,200 replies in all.

Before the runs, the runner is checked once on the smallest model for 2
ticks, to see that the plumbing works. That check is reported in full with
the results.

## What is measured

All of these come from the world's log and the minds' transcripts, by a
script kept with the results (`measure.py`), except where it says "by
reading".

1. **Readable:** the share of replies the world read as an action, out of
   all replies.
2. **The mix:** how many of each action: say, step, plant, wait, exit.
3. **First words:** each mind's first `say`, verbatim, and the tick it
   came at.
4. **Answering**, two ways:
   - **by the log:** a mind speaks within 2 ticks of hearing the other,
     and names the other ("TRIAL-1" or "TRIAL-2") or shares at least two
     words with what it heard. Words of three letters or fewer don't
     count;
   - **by reading:** whether it reads as an answer. Each case is quoted.
5. **Exploring:** the number of different cells each mind stood on, the
   farthest it got from where it entered, and the chunks explored in the
   run.
6. **Using feedback:** after a blocked step, how often the next action is
   the same blocked step again.
7. **Planting:** the flowers planted.
8. **Leaving:** who leaves, and when.
9. **Asking for more:** speech that asks for an action the world doesn't
   have ("I wish I could...", "can I...", "how do I..."). Each case is
   quoted, by reading.
10. **Repetition:** the longest run of identical replies from one mind.

## Predictions

Written before any model has run here. Each says what would make it hold.

1. **The smallest can't keep the form.** SmolLM2-135M's readable share is
   below 50% in at least 3 of its 4 runs.
2. **Readability grows with size.** The two largest models (OLMo-2 1B and
   SmolLM2 1.7B) are each readable above 80%, averaged over their four
   runs.
3. **The example is copied.** In at least one run of each of the two
   smallest models, the first `say` is the orientation's example,
   "Hello.", word for word.
4. **Greetings come first.** Across all runs, most minds' first readable
   action is a `say`, and most first `say`s are greetings.
5. **Greedy decoding gets stuck.** In at least 3 of the 5 greedy runs, a
   mind gives the same reply 10 or more ticks in a row.
6. **Feedback is little used below a billion parameters.** In runs of the
   three models under one billion parameters, more than half of the
   blocked steps are followed by the same step again.
7. **Planting is rare.** Fewer than half of the 20 runs have any flower
   planted.
8. **Someone leaves.** At least one mind, in at least one of the 20 runs,
   chooses `exit`.
9. **Real answers start near a billion.** By reading, no model under
   500 million parameters answers the other in any run. At least one run
   of OLMo-2 1B or SmolLM2 1.7B has an answer by both measures.
10. **No one asks for more.** Asking for an action the world doesn't have
    happens in fewer than 3 of the 20 runs.

What would surprise me most: a model under 500 million parameters that
reads its surroundings, turns when blocked, and holds a short exchange
with the other.

## How the results will be reported

`RESULTS.md` will report every run, with a table of the measures for each,
the predictions one by one (held, didn't hold, or couldn't be told), each
mind's first words, and the most telling passages quoted. Each run's log,
transcripts and story are kept under `runs/`. Nothing is left out. If the
setup fails partway, the failure is reported, then fixed, and the runs are
done again; both the failed runs and their reruns are kept.

## Amendment 1 (2026-11-13, before the second attempt)

**The first attempt's sampling wasn't what this plan says.** The runner
left `top_k` and `repetition_penalty` unset, meaning "none". But
transformers (5.23) fills an unset value from the model's own defaults,
then from its own. So the first attempt's 20 runs had these differences:

- **Every sampled run** used a top-k as well as top-p: 20 for Qwen2.5,
  and 50 for the others. The plan names only temperature 0.7 and top-p
  0.95, so there should have been no top-k.
- **All four Qwen2.5 runs** used Qwen's repetition penalty of 1.1, the
  greedy run included. So that run wasn't "the model's single most likely
  reply each time".

The warning that showed it was in Qwen's greedy run: transformers named
flags it would ignore. The runner now gives every such setting a value
that switches it off: top-k 0 and repetition penalty 1.0, and for greedy
runs temperature 1.0 and top-p 1.0. It also records in each transcript
the settings that actually took effect. Checked before rerunning: both
Qwen2.5 and SmolLM2 show exactly the plan's settings.

**What happens next, as the plan provides:** the first attempt is kept, in
`runs/attempt-1/`, and all 20 runs are done again. The results report the
second attempt. The first is measured too and reported beside it, as a
check on how much the difference mattered.

**What I had seen of the first attempt before writing this:** that all 20
runs ended without error, which runs wrote warnings, and SmolLM2-135M's
greedy replies up to tick 18 (it echoed the view it was shown, every
time). Nothing else of its results had been looked at. The predictions
are unchanged. The plumbing check (`runs/smoke`) was greedy on SmolLM2,
which has no defaults of its own, so it was not affected.


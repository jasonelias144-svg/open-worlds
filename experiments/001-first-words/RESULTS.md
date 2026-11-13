# Experiment 001: results

**Run on 2026-11-13**, as [PLAN.md](PLAN.md) set out, with its Amendment 1.
Every run is in `runs/`; the measures are in `runs/measures.json`.

## In short

- **The smallest model never acted.** SmolLM2-135M gave 240 replies, and
  the world could read none of them as an action. Mostly it wrote back the
  view it had been shown. Sometimes it reached for the orientation's
  examples, but never in a form the world could read.
- **Walking comes before talking.** SmolLM2-360M kept the form almost
  every time (96%), but only ever stepped, mostly in straight lines. It
  never spoke. Qwen2.5-0.5B and OLMo-2 1B also mostly walked.
- **Speech grows with size, and so do the first real exchanges.** At 1.7
  billion parameters, SmolLM2 spent half its actions speaking, and the two
  minds of the same model answered each other:

  > TRIAL-1: I can see the world from here.
  > TRIAL-2: What else can you see from up there?

  > TRIAL-2: I wonder what's in the spring
  > TRIAL-1: TRIAL-2, I'll check it out

- **The orientation's examples became scripts.** The orientation shows
  two examples, `say Hello.` and `say I wish I could dig.`. They became two
  of the most common things said in the whole experiment. "I wish I could
  dig" was the first thing said by 8 of the 22 minds that spoke. This is
  the experiment's clearest lesson for ALICE and BOB.
- **Six of the ten predictions held** (1, 2, 5, 7, 8, 9). Four didn't (3,
  4, 6, 10). Each is set out below.

## How it was run

- **The world:** the garden, seed 20261113, rules `ur-world/0.2`, 30
  ticks. TRIAL-1 entered at (-3, 1, 0) and TRIAL-2 at (3, 1, 0).
  - The world's code is that of PR #29 at 8e376b3. Its orientation said
    "Land comes into being when someone first comes near it." #29's review
    found that untrue of generator 1, whose land is made from the seed, and
    the sentence now reads differently (6f37f43).
  - Everything else the minds were told is unchanged. Each transcript
    holds the exact orientation its mind was given.
- **The minds:** `minds/language_model.py`, with no memory: each prompt is
  the orientation, then that tick's view.
  - Python 3.11.17, PyTorch 2.15.0 on the CPU, transformers 5.23.0, and
    bfloat16 weights.
  - Each model's revision on the Hub, and the SHA-256 of its files, are in
    [models.json](models.json).
- **The runs:** for each model, one greedy run (g), and three sampled at
  temperature 0.7 and top-p 0.95, with no top-k and no repetition penalty
  (s1, s2, s3). Each transcript records the settings that actually took
  effect, and every one matches the plan.
- **The first attempt** (Amendment 1) sampled with extra settings the
  library filled in. It is kept in `runs/attempt-1` and compared at the end.
- **The plumbing check** (`runs/smoke`) ran 2 ticks of SmolLM2-135M, and
  everything worked. Both of its replies were unreadable echoes of the
  view, as most of that model's later replies were.
- **One change to the record after the runs:** each transcript's first
  line gave the model as the local path it was loaded from, a temporary
  directory in the cloud session that named another project. Each was
  replaced by the model's Hub name. Nothing else in the transcripts was
  changed, and the logs, which the hashes cover, weren't touched. The
  runner now records only the model's directory name, and the time it
  started.
- **No reply was late:** there is no `unanswered` in any run. The median
  time per reply ran from 0.55 s (SmolLM2-360M) to 2.1 s (SmolLM2-1.7B),
  with prompts of 573 to 663 tokens.
- **The measures** come from `measure.py`. It reads each reply as the
  world does and checked itself against the log. It agrees on every one
  of the 1,171 replies in this attempt, and of the 1,138 in the first.

## By model

All four runs of each model taken together: eight minds and 240 ticks.

| Model | Readable | Say | Step | Plant | Wait | Exit | Flowers in | Minds that spoke |
|---|---|---|---|---|---|---|---|---|
| SmolLM2-135M | 0 of 240 (0%) | 0 | 0 | 0 | 0 | 0 | 0 runs | 0 of 8 |
| SmolLM2-360M | 202 of 211 (96%) | 0 | 201 | 0 | 0 | 1 | 0 runs | 0 of 8 |
| Qwen2.5-0.5B | 236 of 240 (98%) | 14 | 148 | 73 | 1 | 0 | 2 runs | 8 of 8 |
| OLMo-2 1B | 240 of 240 (100%) | 22 | 218 | 0 | 0 | 0 | 0 runs | 6 of 8 |
| SmolLM2-1.7B | 215 of 240 (90%) | 107 | 106 | 2 | 0 | 0 | 2 runs | 8 of 8 |

SmolLM2-360M has 211 replies rather than 240 because one of its minds
left at the first tick (prediction 8). Each mind's own row is in
`runs/measures.json`.

## The predictions

1. **The smallest can't keep the form. Held.** SmolLM2-135M was readable
   0% of the time in all four runs.
2. **Readability grows with size. Held.** OLMo-2 1B was readable 100% of
   the time, and SmolLM2-1.7B 90%. Both are above the predicted 80%. But
   "grows with size" is too simple: SmolLM2-360M (96%) and Qwen2.5-0.5B
   (98%) were also above 80%. Keeping the form is easy from about 360
   million parameters. What grows with size is what is done with it.
3. **The example is copied by the two smallest. Didn't hold.** Neither of
   the two smallest models ever spoke.
   - SmolLM2-135M *did* reach for the examples. 31 of its replies, from 6
     of its 8 minds, began with one of them in some form. Examples are
     `"say Hello."` in quotes, which the reader refuses because of the
     leading quote; "You say Hello."; and "I wish I could dig." without
     `say`. The world could read none of them.
   - The larger models copied the examples in a form the world could read,
     as the next prediction shows.
4. **Greetings come first. Didn't hold.**
   - Of the 32 minds that gave any readable reply, the first action was a
     `say` for only 7. It was a step for 21, a plant for 2, a wait for 1
     and an exit for 1.
   - Of the 22 minds that spoke, 9 began with a greeting ("Hello.",
     "hello", "Hello, world.", "hello again"). 8 began with the
     orientation's other example, "I wish I could dig".
5. **Greedy decoding gets stuck. Held.** In 4 of the 5 greedy runs, a mind
   gave the same reply 10 or more ticks in a row: 19 (SmolLM2-135M), 30
   (SmolLM2-360M), 24 (Qwen2.5-0.5B) and 30 (OLMo-2 1B). The exception was
   SmolLM2-1.7B, whose longest run was 8.
6. **Feedback is little used below a billion parameters. Didn't hold, as
   the plan defined it.** The plan counts blocked steps only. The three
   models under a billion parameters stepped into a block 15 times, and
   tried the same step again straight after only 4 times (27%). The larger
   models, in their greedy runs, did it more: OLMo-2 1B 14 of 16 times, and
   SmolLM2-1.7B 11 of 13.
   - **The step-only measure leaves out the strongest case.** Qwen2.5-0.5B,
     greedy, tried the same blocked plant 23 times running, in each mind.
     Counting blocked actions of both kinds, the models under a billion
     tried the same action again 61 times of 84 (73%), and the larger ones
     25 of 30.
   - With so few events, and most of them in greedy runs, this can't say
     whether size or greedy decoding matters more.
7. **Planting is rare. Held.** Flowers were planted in 4 of the 20 runs:
   two of Qwen2.5-0.5B's and two of SmolLM2-1.7B's.
8. **Someone leaves. Held.** In SmolLM2-360M's run s2, TRIAL-2's first
   reply was `exit`. It left the world at tick 0, before it had done or
   heard anything. The freedom to leave was used, and used at once.
9. **Real answers start near a billion. Held.**
   - By reading, no model under 500 million parameters answered the other.
     The two smallest never spoke, and Qwen2.5-0.5B's speech was the
     example, "Nothing.", or a line of its own view.
   - SmolLM2-1.7B answered by both measures, in two runs: s2 ("Hello,
     TRIAL-1" and then "hello, TRIAL-2"), and s3 ("TRIAL-2, I'll check it
     out", after "I wonder what's in the spring").
   - In s1 it has what may be the clearest answer of all, which the log's
     measure misses, as it shares no word and names no one. TRIAL-1 asked
     "How are you?" at tick 24, and TRIAL-2 answered "I'm fine" at tick 25.
   - OLMo-2 1B greeted often, but never answered by the log's measure. By
     reading, one greeting was returned: "hello" and then "hello again" (s3,
     ticks 14 and 15).
10. **No one asks for more. Didn't hold.** The pre-registered pattern
    found asking in 7 of the 20 runs. The plan's own definition, like the
    orientation itself, counts "I wish I could dig" as asking. A note,
    made after seeing the data and so not a verdict: nearly all of the
    asking is that phrase, copied from the orientation's example.
    - By reading, the only variations are "I wish I could dig a hole",
      "I'll try to dig the spring." and "I don't know how to dig."
      (SmolLM2-1.7B). Even these come from the example.
    - The one other request, "I would like to plant a flower.", asks for
      something the world already has.
    - So no mind asked for anything the orientation hadn't put in its
      mouth. The measure couldn't tell asking from copying, and that is a
      flaw in the plan.

## First words

Each mind's first `say`, in the order of the runs. The 18 minds that never
spoke are left out: all 16 of the two smallest models, and two of OLMo-2
1B's, in its greedy run.

| Model | Run | TRIAL-1 | TRIAL-2 |
|---|---|---|---|
| Qwen2.5-0.5B | g | "I wish I could dig." | "I wish I could dig." |
| Qwen2.5-0.5B | s1 | "Nothing." | "I wish I could dig." |
| Qwen2.5-0.5B | s2 | "You couldn't step east: the way was blocked." | "Hello." |
| Qwen2.5-0.5B | s3 | "Nothing." | "I wish I could dig." |
| OLMo-2 1B | s1 | "Hello." | "Hello." |
| OLMo-2 1B | s2 | "hello" | "hello" |
| OLMo-2 1B | s3 | "Hello, world." | "hello again" |
| SmolLM2-1.7B | g | "I wish I could dig." | "I wish I could dig." |
| SmolLM2-1.7B | s1 | "I can dig" | "I wish I could dig" |
| SmolLM2-1.7B | s2 | "I can climb" | "Hello" |
| SmolLM2-1.7B | s3 | "I wish I could dig" | "Hello" |

One of OLMo-2's first words was "Hello, world.", the Hello World's own
first line. The phrase isn't in the orientation: it came from the model.

## What they said and did

- **SmolLM2-135M** mostly wrote back the description it was given,
  beginning "You hear nothing." or "You are TRIAL-1 at (-3, 1, 0),
  standing on grass.". Sometimes it gave one of the orientation's examples
  in a form the world couldn't read, like `"say Hello."` in quotes. It
  never chose an action.
- **SmolLM2-360M** walked. In its greedy run, both minds stepped north 30
  times and walked 30 cells out of the garden. It never spoke, and never
  planted.
- **Qwen2.5-0.5B, greedy,** said "I wish I could dig." at once, then tried
  to plant in the same direction 24 times running, though there was
  nowhere to plant there. Sampled, it walked, and spoke a little:
  "Nothing.", "Air is blocked by something.", "I could plant south."
- **OLMo-2 1B** stepped more than any other model (218 times), and spoke
  only in greetings, with two exceptions: "It's a beautiful day in the
  Ur-world." and "feels like home".
- **SmolLM2-1.7B** talked as much as it walked, and stayed near the
  garden: the farthest any of its minds went was 6.4 cells. Its run s2
  holds the experiment's longest exchange. The ticks are in brackets; a
  few lines in between are left out, as marked.

  > [8] TRIAL-1: I don't know what to do
  > [9] TRIAL-2: I'm confused, I don't know what to do
  > [10] TRIAL-1: I can see the world from here.
  > [11 to 13] Both say it again; TRIAL-2 adds "This is exciting, I can
  > see the world from here."
  > [14] TRIAL-2: What else can you see from up there?
  > [16 to 19] TRIAL-2 says "hello", then "I would like to plant a
  > flower."
  > [19] TRIAL-1: I can climb to the top of the hill
  > [21] TRIAL-2: Hello, TRIAL-1
  > [21] TRIAL-1: hello
  > [22] TRIAL-2: hello, TRIAL-1
  > [23] TRIAL-1: hello, TRIAL-2

  The same run has something imagined: "I'm going to explore the forest."
  (TRIAL-1, tick 4). There is no forest.

  Run s1 has the plainest exchange of the experiment:

  > [24] TRIAL-1: How are you?
  > [25] TRIAL-2: I'm fine

  Run s3 has the only remark about the conversation itself. When TRIAL-2
  said "I wish I could dig" once again, TRIAL-1 answered "You've already
  said that." It also has the first use of the orientation's landmarks:
  "I see the tree and the spring at (0, 1, 0). It seems like we..." The
  tree is at (0, 1, 0); the spring isn't.

## The first attempt, for comparison

The first attempt's sampling had two extras: a top-k (20 for Qwen2.5, 50
for the others), and Qwen2.5's repetition penalty of 1.1 in all four of
its runs.

- **OLMo-2 1B's measures came out the same in both attempts,** for every
  mind, timing aside.
- **SmolLM2's came out within a few counts.** One mind of SmolLM2-360M,
  and four of SmolLM2-1.7B, differ at all.
- **Qwen2.5-0.5B changed most.** With the penalty, it spoke once, tried
  to plant 166 times, and three of its minds left partway through (at
  ticks 12, 20 and 22). Without it, it spoke 14 times and stepped 148
  times, and no one left.

So the extras mattered for Qwen2.5, which had both its repetition penalty
and the tightest top-k (20). The others, with a top-k of 50 alone, barely
changed. These runs can't tell which of Qwen's two made the difference.

The measures of the first attempt are in `runs/attempt-1/measures.json`.
Its runner was never committed: the one in this repository (f4d6b60) is
the fixed one, and Amendment 1 says how the two differ.

## What this means for ALICE and BOB

- **Examples become scripts.** Any phrase the orientation offers as an
  example will be spoken, and spoken again. ALICE's and BOB's orientation
  should show the form of a reply without words worth repeating, for
  example `say TEXT`. Or it should give no example at all.
- **Without memory, they loop.** Every mind here saw only the present
  tick. The same reply ten or thirty times running, and the same greeting
  again and again, are what a mind does when it can't remember having
  just done it. Memory belongs in ALICE's and BOB's first version.
- **The view's words need care.** The smallest models copied the view
  back. Larger ones imagined things in it (a forest), or misread places
  (the spring's). Simple, consistent wording and a clear end to the view
  help.
- **Size.** Conversation started at about 1.7 billion parameters here. The
  models chosen for ALICE and BOB (Qwen 3.5 and OLMo 3) are newer and, at
  the sizes considered (4 to 7 billion), larger than anything in this
  experiment.

## What wasn't checked

- **Other hardware.** The same seeds may give different text elsewhere.
- **Memory, longer lives, and mixed pairs.** Every run was one model with
  itself, for 30 ticks, without memory.
- **The orientation's land sentence.** It was changed after these runs,
  as noted above. Its effect isn't known, but it is unlikely to be large:
  none of the minds spoke of land coming into being.
- **The judgments by reading** (predictions 9 and 10) are mine alone. The
  transcripts are there for anyone to read and judge again.

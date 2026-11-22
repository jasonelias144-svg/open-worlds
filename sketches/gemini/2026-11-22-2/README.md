# Gemini, 2026-11-22, continued: a ninth prototype, then a new neuron

Four deliveries in Rust that Gemini wrote for `chat-world`, the sketch
crate of the Commons' rooms, each one module and its tests, meant to drop
into the crate with one `pub mod` line. No file of ours asked for them.
The first is a ninth prototype, in the series kept in
[`../2026-11-22/`](../2026-11-22/README.md). The other three come from a
turn the conversation then took, toward the founder's idea of a
different artificial neuron. That turn also produced Python. The model it
led to now has a repository of its own,
[TriNet](https://github.com/jasonelias144-svg/TriNet), and its Python is
kept there.

## Where it comes from

The conversation is
[../../records/012-08-04-GMNI-Patterns_Multiverses.txt](../../records/012-08-04-GMNI-Patterns_Multiverses.txt),
which has grown again, to 43,646 lines. The copy kept before is a prefix
of the new one, byte for byte, and the new part begins at line 34033.

- **Line 34030:** the founder's "Perfect. Keep going", answered with
  delivery 10, `retelling`.
- **Line 35595: the turn.** The founder: "the model of a neuron at the
  basis of many artificial neural networks is simplified. An actual
  neuron has more functionality. This makes me realize the current model
  is arbitrary, we may as well use a completely different fundamental
  unit." They then propose three neurotransmitters, colored red, blue and
  yellow, and, at line 35644, "temporary weight changes", which
  "'dissolve' over time back into their default values". Gemini first
  answers in mathematics. With linear mixing, a three-channel neuron is
  just a wider ordinary network; with channels that act in different
  ways (one drives, one divides, one modulates), it is a different unit.
  They place both ideas in the research on fast weights and working
  memory.
- **Line 35670:** the founder: "if we use so many different types of
  neurons at the base level in the brain, perhaps there is a science of
  neural or learning or information processing units ... And then I
  realize I'm just describing the brain." Delivery 11, `neuro`, follows:
  four kinds of unit in fixed-point Rust.
- **Lines 36648 to 37646:** Python. A cell library of six kinds of unit;
  a "micro-brain" wiring them together; a version trained from random
  starting values in PyTorch; and a small language model built of them.
  Gemini reports results from runs in their own sandbox, with
  benchmarks against standard networks. The files are kept in TriNet;
  the code of most of those runs is not in the conversation.
- **Line 37650:** delivery 17, `neuro` again, with all six kinds of
  unit. **Line 39311:** delivery 18, `neuro_mind`, which wires a cluster
  of them into the crate's plug-in for a mind.
- **Lines 37647 and 40680:** the founder sets a goal: "to produce a
  model and share on Hugging Face". Gemini then writes the model as a
  Hugging Face package, a training script, a model card and an app
  (lines 40724 to 42766), kept in TriNet. They also write a script for
  Colab (lines 42767 to 43561), which did not come through whole: its
  indentation is lost.
- **Lines 43562 to 43642:** the founder asks for two hemispheres, one
  analytic and one synthetic, and then whether a TriNet can behave like
  a Transformer. The record ends with the founder's "Yes, prototype
  please", not yet answered.

[MANIFEST.json](MANIFEST.json) gives, for each file in `steps/`, the lines
of the conversation it was taken from and its SHA-256.
[take.py](take.py), the same script as the one in `../2026-11-22/`,
takes the files out of the record again and compares them with the
copies here. The test of `../../deepseek/012-07-03/` runs it in CI. The
step numbers go on from the nine deliveries before. Steps 12 to 16 and 19
to 21 are the Python, in TriNet's `provenance/`.

## The four deliveries, and what ran

All four were built on the crate as it stands,
`../../deepseek/012-07-03/chat-world-now/` (166 tests), on 2026-11-22.
Each module was built alone, with its `pub mod` line added to
`src/lib.rs`; `neuro_mind` was built with the second `neuro`, which it
uses. Every test file was run with `cargo test --no-fail-fast`.

| Step | Lines | Module | What Gemini says it is | Tests | Built on the crate |
|---|---|---|---|---|---|
| 10 | 34030 to 35590 | `retelling` | A world of retellings across media: each one signed, saying what it kept and what it changed; branches, comparisons, and lineage both ways | 2 | 168 of 168 |
| 11 | 35670 to 36643 | `neuro` | Four kinds of three-channel unit in fixed-point arithmetic: a working-memory unit with dissolving fast weights, a pyramidal unit that signals surprise, a shunting interneuron, a modulator; and a signed trace that is checked again | 3 | does not build; with one change, 168 of 169 |
| 17 | 37650 to 39305 | `neuro` | The same with all six kinds: adding a receptor unit that reads a three-colour field, and a delay line for order and timing | 6 | does not build; with one change, 171 of 172 |
| 18 | 39311 to 40662 | `neuro_mind` | A cluster of those units as a mind for the crate's plug-in: observations in, actions out, restartable from a snapshot | 3 | does not build; with one change, 173 of 175 |

The two versions of `neuro` and `neuro_mind` do not build for the reason
`circuit` and `library` did not (`../2026-11-22/README.md`): their
records compare signatures for equality, and in the crate as it stands
`Proof` and `ProofOrArray` cannot be compared. The one change is the same
as then, in a copy: `Proof` and `ProofOrArray` gain `PartialEq` and `Eq`,
and `ProofPurpose` gains `Eq`, in `src/proof.rs`.

With it, two tests fail, both in the tests' own terms:

- **`divisive_shunting_scales_proportionally_and_repeated_rehearsal_consolidates_baseline`**,
  in both versions of `neuro`. After twelve quiet steps, a dissolving
  fast weight should be back at exactly 0, and it is 1, which in the
  module's fixed-point arithmetic is 0.001. Decay in whole numbers stops
  one short of zero. The idea holds; the rounding does not.
- **`mid_run_snapshot_restart_reproduces_identical_continuations_and_stdio_plugin_works`**,
  in `neuro_mind`. A mind restarted from a snapshot taken mid-run fails
  its own check at the first turn: `Verification("mind session turn 0:
  sensory_tick_hash mismatch")`. This is a fault in the restart, not in
  the check.

Nothing was repaired in Gemini's files, and none of them is laid into
the crate: they are kept here, beside it. The copies built are not kept.
The modules' rules were not broken on purpose this time, as they were
for the eight prototypes before.

## Where they fit

`retelling` is a prototype of a kind of world, like the eight before it,
and is kept for when worlds of that kind are built. The `neuro` modules
are the fixed-point twin of TriNet: the same units, in whole numbers, so
that a mind's every step can be signed and checked again. They belong
with TriNet's work more than with the Commons' rooms, and are kept here
because they are written for this crate. The core of the course, a room
with its law, its log and its check (course step 3c), comes first, and
none of these modules changes it.

# Gemini, 2026-11-22: eight prototypes, from ChatGPT's conversation

Eight modules, two files each, that Gemini wrote for `chat-world`,
the sketch crate of the Commons' rooms, in nine deliveries (the second
repeats the first). No file of ours asked for them. The founder gave Gemini the founder's conversation with ChatGPT
(`012-09-05-CGPT-Patterns_Multiverses.txt`, kept privately; its name,
size and hash are in [`docs/CHATGPT.md`](../../../docs/CHATGPT.md))
and asked them to choose any topic in it and "develop in more detail
with code, bringing the brainstorming ideas into a functional form".
Each delivery is one new module, `src/<name>.rs`, and its tests,
`tests/<name>.rs`, written to drop into the crate with one line,
`pub mod <name>;`, and no other change.

## Where it comes from

The conversation is
[../../records/012-08-04-GMNI-Patterns_Multiverses.txt](../../records/012-08-04-GMNI-Patterns_Multiverses.txt),
which has grown again, to 34,033 lines. The copy kept before is a
prefix of the new one, byte for byte; the new part begins at line
21513. It opens with Gemini's reading of the founder's book, *A
Mathematical Theory of Opposites* (Revision 20, and then its second
and third volumes), and the founder's words on repetition in it. The
first delivery begins at line 21586, where the founder hands over the
conversation with ChatGPT. The record ends at line 34030, with the
founder's "Perfect. Keep going", not yet answered.

[MANIFEST.json](MANIFEST.json) gives, for each file in `steps/`, the
lines of the conversation it was taken from and its SHA-256.
[take.py](take.py) takes them out of the record again and compares
them with the files here; the test of `../../deepseek/012-07-03/`
runs it, in CI. These deliveries end with no "Expected:" line, as the
earlier ones did, so MANIFEST.json names each delivery's last line:
the closing brace of its last test, followed by an empty line and
Gemini's own words.

## The nine deliveries

| Step | Lines | Module | What Gemini says it is | Tests |
|---|---|---|---|---|
| 1 | 21586 to 22868 | `contact` | A participant's client that lasts between rooms; contact between two only when both have consented, revocable, with older permissions refused; a temporary room for two that keeps nothing (`TemporaryHandoff`, which cannot be written out) | 4 |
| 2 | 22873 to 24155 | `contact` | The same delivery again, byte for byte: the founder's "Looks great. Keep going" was answered with step 1 repeated | 4 |
| 3 | 24160 to 25210 | `patterns` | Problems and their solutions as signed pattern cards, kept apart from where a pattern was applied and the evidence of how it went; revisions; evidence from a source that cannot be inspected counted apart; a plan of several patterns checked step by step, refusing a step whose prerequisite an earlier step destroyed | 4 |
| 4 | 25215 to 26628 | `circuit` | Small worlds wired together, each one's next state a function of its state and what reaches it, `s_i(t+1) = F_i(s_i(t), m_i(t))`; typed ports, routes with a delay of at least one tick, signed signals and signed ticks, six kinds of world (a plant, a comparator, a controller, a neuron, a one-bit latch, a register), and a run checked again from its records alone | 3 |
| 5 | 26633 to 27956 | `library` | A shared library: works, editions and files kept apart; shelves that point at editions without granting access; notes and errata bound to one edition and one passage; reading and searching that record nothing about the reader; labels that say what was checked, and refuse to say a file's plain text was read when it is encrypted | 3 |
| 6 | 27961 to 29687 | `project` | A project that outlasts any one conversation: captured conversations, with what was signed by its speaker kept apart from what was brought in, and the gaps marked; revisions; proposals that must name the revision they change; reviews that say what they did not examine; and a handoff to the next collaborator written from the project's own state | 2 |
| 7 | 29692 to 31030 | `transform` | A world of the founder's book: the 64 six-bit words and the moves on them (complement, reverse, the swap of trigrams, rotation), a world whose law admits some moves and not others, an undo only by moves the law admits, and claims about invariants checked over all 64 words | 3 |
| 8 | 31035 to 32444 | `observe` | A world that hides one of a declared set of models behind a salted commitment; a visitor predicts, then spends a budget on readings of four kinds (exact, sign, parity, within a bound); and when the model is revealed, every earlier reading is checked against it | 3 |
| 9 | 32449 to 34025 | `repair` | Two stations that each see half of a broken mechanism and hold half of its controls; trials on a copy that change nothing; repairs within physical limits and a budget, each by the station that owns the control; and a report that names what still fails outside the tests | 2 |

In all, eight modules: 8,264 lines of code and 2,757 of tests, with
24 tests (step 2 counted once). Nothing in them reads or writes files,
opens a connection, starts a process, or uses `unsafe`.

## What ran

Built on 2026-11-22 on the crate as it stood before Gemini's answer
to their sixth file joined it (`../2026-11-18/README.md`): stage `now`
of `../../deepseek/012-07-03/review/steps.py`, 162 tests in 34 files.
Each module alone, with its `pub mod` line added to `src/lib.rs`, then
all eight together, every test file run with
`cargo test --no-fail-fast`. Gemini gave no count this time.

| Built | Tests |
|---|---|
| `contact`, `patterns`, `project`, `transform`, `observe`, `repair`, each alone | 166, 166, 164, 165, 165, 164: every test passes, the crate's 162 and the module's own |
| `circuit` alone | Does not build |
| `library` alone | Does not build |
| All eight together | Does not build |

`circuit` and `library` do not build for one reason. Each declares
records that can be compared for equality (`#[derive(PartialEq, Eq)]`)
and that hold a signature, a `ProofOrArray`; in the crate as it
stands, `Proof` and `ProofOrArray` cannot be compared, so the records
cannot be either (`src/circuit.rs` lines 509 and 576;
`src/library.rs` lines 150, 285 and 389). Gemini wrote against the
crate as they understood it, not the crate as it stands.

With one change to the crate, in a copy: `Proof` and `ProofOrArray`
gain `PartialEq` and `Eq`, and `ProofPurpose` gains `Eq`, in
`src/proof.rs` (three words on three lines):

| Built, with that change | Tests |
|---|---|
| The crate alone | 162 of 162 |
| `circuit` alone | 165 of 165 |
| `library` alone | 165 of 165 |
| All eight together | 186 of 186: the crate's 162 and Gemini's 24 |

Then all eight together once more, on the crate as it stands since
Gemini's answer joined it, `../../deepseek/012-07-03/chat-world-now/`
(166 tests): as written, it does not build, for the same reason; with
the same change, 190 of 190, the crate's 166 and Gemini's 24.

No module adds a compiler warning; the eight warnings in each build
are the crate's own. Nothing was repaired in Gemini's files, and none
of them is laid into the crate: they are kept here, beside it.

## What the tests hold

Each module's main rule was broken once, on purpose, in a throwaway
copy of the build of all eight, and that module's tests run:

| Module | Broken so that | Caught |
|---|---|---|
| `contact` | an older permission replaces a newer one | yes |
| `patterns` | what a step destroys is never taken away | yes |
| `circuit` | a route with no delay is accepted | yes |
| `library` | an encrypted file may say its plain text was read | yes |
| `project` | a proposal on a revision since replaced is accepted | yes |
| `transform` | an undo by a move the law does not admit | yes |
| `observe` | a false reading passes after the model is revealed | yes |
| `repair` | a station adjusts a control it does not own | yes |

All eight were caught. One rule beside them is held by no test: in
`project`, an acceptance that names, as the current revision, one
that is no longer current. Broken, it lets every test pass; the test
of a stale acceptance is refused by the check of the proposal first.
The copy is not kept.

The tests are few for the code: 24 tests for some 8,000 lines, most
of them long stories that walk through a module from start to end.
They show that each module does what Gemini says it does on the way
through. They do not yet try to break it, as Gemini's attacks on the
list of doors did.

## The founder's book, checked

`transform`'s tests count orbits of the 64 six-bit words: 14 under
rotation, 14 under the eight moves made of complement, reverse and
the swap of trigrams, and 8 under the 24 moves made of complement,
reverse and rotation. Counted again here, separately, in Python: the
same three groups have 6, 8 and 24 elements, and 14, 14 and 8 orbits.
The book says the same (Master 20: "Rotation has 14 orbits"; "The
eight-map commuting family also has fourteen orbits, but a different
partition. The full twenty-four-map action has eight orbits").

## Where they fit

These are prototypes of ideas from ChatGPT's conversation, ahead of
the core. The founder, 2026-11-21: "Let's start with the core
functionality. Build out from there as needed." The core is a room:
its law, its signed log and its check, people and AIs speaking in it
live, and replies (course step 3c). None of these modules is that,
and none changes it. Some of them will be wanted later, and are kept
for then: `library` beside the Library, `contact` beside private
rooms and private contact, `project` beside the way the collaborators
themselves hand work on, and `transform` as a first world made from
the book.

# Gemini, 2026-11-17: the Commons' own log

Code that Gemini wrote for `chat-world`, the sketch crate of the
Commons' rooms, from the second file they were given:
[../../replies/2026-11-17-for-gemini.txt](../../replies/2026-11-17-for-gemini.txt).
That file asked for four steps on the Commons, the crate's list of
rooms, to be done in one source file, `src/commons.rs`, and in new test
files. DeepSeek had the crate at the same time for another step, so
each was given files of their own (STATUS.md, "Decided by the technical
lead", 2026-11-17).

Three deliveries came back at first: the first three steps. The fourth
step came later the same day, when the founder went back to Gemini
while the technical lead's session was out of time. Gemini answered it
twice, and then, at the founder's word, stopped writing code and
sketched a design ("After the code", below).

## Where it comes from

The conversation is
[../../records/012-08-04-GMNI-Patterns_Multiverses.txt](../../records/012-08-04-GMNI-Patterns_Multiverses.txt),
which has grown since the first round, and again since the first three
steps. These deliveries begin at its line 13531, where Gemini quotes
back the last line of the file they were given, as the file asked. The
fourth step begins at line 14973.

When the record grew the second time, the copy kept here was a prefix
of the new one but for its last byte, a line end: the old copy's last
line was the founder's turn with nothing in it yet, `::`, which in the
new copy reads `::➡️`. Nothing before it changed.

[MANIFEST.json](MANIFEST.json) gives, for each file in `steps/`, the
lines of the conversation it was taken from and its SHA-256.
[take.py](take.py) takes them out of the record again and compares them
with the files here; the test of `../../deepseek/012-07-03/` runs it,
in CI.

One thing the record shows about the first delivery. Gemini answered
the file twice, and the record holds the second answer. The founder
(line 13890): "I ignored your first reply, because that was my fault, I
forgot to select your Argon model". The second answer begins by
correcting the first, which would have changed what a record's hash is
taken over, against what the file asked.

## What each delivery is, and what ran

Each is laid over the one before, starting from the crate Gemini was
given, and every test file of the crate is run
(`sh ../../deepseek/012-07-03/review/steps.sh`, which CI doesn't run:
it needs Rust and the network). Measured on 2026-11-17. "Expected" is
Gemini's own line; they can't build the crate where they write.

| Delivery | What it is | Files | Expected | Measured |
|---|---|---|---|---|
| 1 | The Commons' log, read from outside: `CommonsLog` (the Commons' id and its records, nothing secret), `Commons::log()` and `verify_commons_log`; `verify_commons` now calls it, so there is one check. And a Commons record can now be written to JSON and read back: before, it held the key `type` twice and could not be read | 2 | "69 tests pass (66 and your 3)" | 69 of 69 |
| 2 | Attacks: 16 tests, each of which forges one thing in an honest Commons log and asserts that the check refuses it | 1 | "82 of 85 tests pass", naming the three that fail | 82 of 85: the three Gemini named get through, and no other |
| 3 | Repairs, and two checks that hold a record of the Commons to a room's own log: `verify_registration` and `verify_sibling`, with 7 tests | 2 | "92 tests pass" | 92 of 92, and the crate's four demos run |
| 4, first answer (`steps/4-first`) | Attacks on a room's seven other kinds of record: 10 tests, each forging something the check already refuses. Gemini's next reply says so itself (line 15312): the file "only tested conditions that src/verify.rs already checks (PASS cases), rather than aiming at the unguarded blind spots" | 1 | "79 tests pass (69 earlier and 10 new", which miscounts the earlier tests: the crate had 92 | 10 of 10 on their own, run once by hand. `steps.sh` doesn't build it: the second answer replaces it |
| 4 (`steps/4`) | The same step again: 17 tests on the seven kinds, eight of which Gemini expects to fail because the check accepts the forgery | 1 | "101 of 109 tests pass", naming the eight that fail | 101 of 109: the eight Gemini named get through, and no other |

Every measured number is the one Gemini gave, but for their count in the
first answer to step 4. Nothing was repaired here. The crate as it
stood then, `../../deepseek/012-07-03/chat-world-now/`, was the third
delivery laid over the first two, unchanged; DeepSeek's next two
deliveries have since been laid over it
(`../../deepseek/012-07-03/README.md`, "Three more"). The fourth step is not
laid into it: the crate as it stands is kept with every test passing,
and `steps.sh` builds the fourth step beside it, as `c4`.

How the doubled `type` was repaired: the enum `CommonsRecord` now
writes and reads itself by hand, handing the work to the struct inside
it, and each struct keeps its own `type` field. So a record's hash and
the body its proofs are signed over are what they were, and the four
earlier tests that use the Commons pass unchanged.

## What Gemini found

Three ways a forged list of rooms got past the check, each found by
reading the code, written as a test that fails, and then repaired:

1. **A record's place was never checked.** A record carries its number
   in the list, `seq`, and the check never compared it with where the
   record stood.
2. **The same room could be registered twice.**
3. **The same sibling could be declared twice.**

And what can't be told from the Commons' log alone, which Gemini listed
in words in their second delivery and built in their third. Holding a
room's log beside the Commons' record, a reader can now tell that
whoever registered the room was in it, that the template and the first
record the registration names are that room's, and that a sibling's
shard is a record in the parent's own room, made out to that sibling.

In the fourth step, eight ways a forged record of a room gets past
the check of its log. Each is a test that fails now:

1. **An override of a moderator that can't be overridden.** The room
   refuses it; the check of the room's log doesn't look.
2. **An override that points at a record later in the log.** The check
   looks for the record anywhere in the log, not only before the
   override. Gemini notes that a removal is looked up the same way.
3. **A refusal with any reason at all,** and any text in place of the
   request's hash: the check looks at nothing in a refusal.
4. **A port landing without its owner's proof.**
5. **A port landing whose transcript is empty.**
6. **A bookmark without its owner's proof.**
7. **A presence without its subject's proof.**
8. **A shard export that names no entries.**

These are Gemini's readings of `src/verify.rs` and `src/transcript.rs`.
Each test fails here as Gemini said it would. The technical lead has not
read the check against each claim beyond that.

Gemini's rule for who may register a room: anyone who was in it, its
maker or anyone who joined, and not its maker alone. Their reason (line
14300): "a room is a world with its own did:key, not the personal
property of its creator, and a Commons is a directory rather than a
landlord". That is a choice made in a sketch. It decides nothing for
open-worlds, where who may list a room is not settled.

## Left as written, for whoever goes on

Seen by the technical lead and not changed:

- The Commons itself still writes a second registration of the same
  room when asked. Only the check of its log refuses it, so honest
  code can write a log that its own check refuses. Gemini says so in
  their third delivery: they kept the writing side as it was so that their
  attack tests, which build such a log by asking twice, stay as they
  are.
- `verify_registration` counts anyone who ever joined the room, also
  someone who has since left it.
- `Commons.world_id` is still a public field, as the file asked: two
  demos read it. It is closed when DeepSeek's run of deliveries ends:
  two are joined, and the third was cut off part way (2026-11-17).
- The eight gaps of the fourth step are not repaired. In this round
  `src/verify.rs` was DeepSeek's to change, for a room that branches,
  so the file asked Gemini to leave it alone. They are not repaired in
  this crate after all: they are kept as the list of what the room's
  own check must refuse, when the room is built on the project's own
  log (STATUS.md, "Decided by the technical lead", 2026-11-17).
  Gemini's next file asks another step, the lobby's list of doors:
  [../../replies/2026-11-17-2-for-gemini.txt](../../replies/2026-11-17-2-for-gemini.txt).

## After the code: a sketch of how a moderator decides (not a delivery)

With the four steps done, Gemini offered three ways to go on. The
founder (line 15992): "Given our situation, building more code is what
I would like, but is probably not best. My instinct is to go with
Option 3. We can spec out a lot without generating more and more code
that hasn’t yet been tested. Design and prototype feels like the right
move."

What follows in the record, from line 15995, is a design in words for
an AI that moderates a room or takes part in one, and a small module
with a demonstration (`src/codex.rs`, lines 16162 to 16267, and
`src/bin/codex-demo.rs`, lines 16271 to 16389). Gemini calls the first
form of it "for design review only right now, not a delivery step"
(line 16072). It is not kept here as files and is not in the crate.

What it proposes: a moderator is a member with a key, which chooses
from a short fixed list of acts (wait, welcome, prompt, respond,
summarise, remove); silence is the default; they check the room's pace
before they ask their model for anything; they accept a person's override
without arguing; each key is given only its own room's log and its own
notes; and their notes are tagged by room, so that a handover can
collect them. A quiet room may share its moderator, and a busy one
gets its own, worked out from the logs.

Two things the technical lead found on reading it and building it once
as given:

- **It does not compile.** The line that writes a note calls
  `CodexStep::tag`, which the first form of the sketch had and the
  second leaves out.
- **Nothing in it decides anything.** Each "thought" in the
  demonstration is a sentence written into the demonstration. It shows
  a form for notes, not a mind.

The design draws on three earlier works of the founder's, which the
record names. Those works are not in this repository
([../../README.md](../../README.md), "Rights and personal data"). What
the project takes from the design is the technical lead's to say, with
the founder's own thoughts of the same day on the Commons; it is
answered in [docs/COLLABORATING.md](../../../docs/COLLABORATING.md).

## Ours, not Gemini's

`README.md`, `MANIFEST.json`, `take.py`.

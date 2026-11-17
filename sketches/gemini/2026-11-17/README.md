# Gemini, 2026-11-17: the Commons' own log

Code that Gemini wrote for `chat-world`, the sketch crate of the
Commons' rooms, from the second file it was given:
[../../replies/2026-11-17-for-gemini.txt](../../replies/2026-11-17-for-gemini.txt).
That file asked for four steps on the Commons, the crate's list of
rooms, to be done in one source file, `src/commons.rs`, and in new test
files. DeepSeek had the crate at the same time for another step, so
each was given files of its own (STATUS.md, "Decided by the technical
lead", 2026-11-17).

Three deliveries came back: the first three steps. The fourth step was
not begun.

## Where it comes from

The conversation is
[../../records/012-00-00-GMNI-Multiverse_Development.txt](../../records/012-00-00-GMNI-Multiverse_Development.txt),
which has grown since the first round. These deliveries begin at its
line 13531, where Gemini quotes back the last line of the file it was
given, as the file asked.

[MANIFEST.json](MANIFEST.json) gives, for each file in `steps/`, the
lines of the conversation it was taken from and its SHA-256.
[take.py](take.py) takes them out of the record again and compares them
with the files here; the test of `../../deepseek/012-09-05/` runs it,
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
(`sh ../../deepseek/012-09-05/review/steps.sh`, which CI doesn't run:
it needs Rust and the network). Measured on 2026-11-17. "Expected" is
Gemini's own line; it can't build the crate where it writes.

| Delivery | What it is | Files | Expected | Measured |
|---|---|---|---|---|
| 1 | The Commons' log, read from outside: `CommonsLog` (the Commons' id and its records, nothing secret), `Commons::log()` and `verify_commons_log`; `verify_commons` now calls it, so there is one check. And a Commons record can now be written to JSON and read back: before, it held the key `type` twice and could not be read | 2 | "69 tests pass (66 and your 3)" | 69 of 69 |
| 2 | Attacks: 16 tests, each of which forges one thing in an honest Commons log and asserts that the check refuses it | 1 | "82 of 85 tests pass", naming the three that fail | 82 of 85: the three Gemini named get through, and no other |
| 3 | Repairs, and two checks that hold a record of the Commons to a room's own log: `verify_registration` and `verify_sibling`, with 7 tests | 2 | "92 tests pass" | 92 of 92, and the crate's four demos run |

Every measured number is the one Gemini gave. Nothing was repaired
here. The crate as it stands,
`../../deepseek/012-09-05/chat-world-now/`, is the third delivery laid
over the first two, unchanged.

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
in words in its second delivery and built in its third. Holding a
room's log beside the Commons' record, a reader can now tell that
whoever registered the room was in it, that the template and the first
record the registration names are that room's, and that a sibling's
shard is a record in the parent's own room, made out to that sibling.

Gemini's rule for who may register a room: anyone who was in it, its
maker or anyone who joined, and not its maker alone. Its reason (line
14300): "a room is a world with its own did:key, not the personal
property of its creator, and a Commons is a directory rather than a
landlord". That is a choice made in a sketch. It decides nothing for
open-worlds, where who may list a room is not settled.

## Left as written, for whoever goes on

Seen by the technical lead and not changed:

- The Commons itself still writes a second registration of the same
  room when asked. Only the check of its log refuses it, so honest
  code can write a log that its own check refuses. Gemini says so in
  its third delivery: it kept the writing side as it was so that its
  attack tests, which build such a log by asking twice, stay as they
  are.
- `verify_registration` counts anyone who ever joined the room, also
  someone who has since left it.
- `Commons.world_id` is still a public field, as the file asked: two
  demos read it. It is closed when DeepSeek's work is joined.
- The file's fourth step, attacks on a room's seven other kinds of
  record, was not begun.

## Ours, not Gemini's

`README.md`, `MANIFEST.json`, `take.py`.

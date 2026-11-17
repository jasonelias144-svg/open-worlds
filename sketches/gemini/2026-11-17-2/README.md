# Gemini, 2026-11-17: the lobby's list of doors

Code that Gemini wrote for `chat-world`, the sketch crate of the
Commons' rooms, from the third file they were given:
[../../replies/2026-11-17-2-for-gemini.txt](../../replies/2026-11-17-2-for-gemini.txt).
That file asked one step: the list of the Commons' doors, which is
what a map of the Commons is first drawn from, in a new source file,
`src/doors.rs`, with fifteen tests.

## Where it comes from

The conversation is
[../../records/012-00-00-GMNI-Multiverse_Development.txt](../../records/012-00-00-GMNI-Multiverse_Development.txt),
which has grown again. This delivery begins at its line 16399, where
Gemini quotes back the last line of the file they were given, as the
file asked. The copy kept before is a prefix of the new one, byte for
byte.

[MANIFEST.json](MANIFEST.json) gives, for each file in `steps/`, the
lines of the conversation it was taken from and its SHA-256.
[take.py](take.py) takes them out of the record again and compares
them with the files here; the test of `../../deepseek/012-09-05/`
runs it, in CI.

## What it is, and what ran

Two files, kept as written in `steps/1`:

- `src/doors.rs`: `draw` makes the list from the Commons' log and the
  logs of the rooms the reader holds; `check` holds a list someone
  else handed on to what the reader draws; `ranked` gives the doors
  with the most populated first; `as_text` writes the list as text for
  a mind, with every string in quotes, on one line, in ASCII.
- `tests/doors.rs`: the fifteen tests the file named.

Laid over the crate as it stood, with the one line that names the
module added to `src/lib.rs` here, as the file said it would be
(change 26 in [../../INDEX.md](../../INDEX.md)), and every test file
run, on 2026-11-17 (`sh ../../deepseek/012-09-05/review/steps.sh`,
which CI doesn't run):

| Delivery | Gemini expected | Measured |
|---|---|---|
| The lobby's list of doors | "127 tests pass (112 and your 15)" | 127 of 127 |

Nothing was repaired. It is in the crate as it stands,
`../../deepseek/012-09-05/chat-world-now/`.

**Checked a second way.** The technical lead had written the step out
too, outside the repository, to be sure the file's tests could be
met. Gemini's fifteen tests pass against that version, and its
fifteen pass against Gemini's `src/doors.rs`. Two builds from one
file agree on both sets of tests. The technical lead's version is not
kept.

## What Gemini answered

The file asked three things in a few lines each, before the code
(line 16400):

1. **Is the number of records a count was taken from enough, when a
   log can be given without its end?** For an honest copy, yes: it
   orders two counts of one room. But "a sender can deliberately
   withhold the tail of a log to hide a recent Leave or Join", unless
   the reader compares it with a newer signed head or another copy.
2. **What a door could show besides, and what never.** The limits a
   room sets (the longest message, how many in how long), its rules
   for removing, and whether an AI moderator is declared and can be
   overridden, with no id. Never: the ids of members or of the maker,
   anything said or refused, or times.
3. **The record by which someone lets others find them.** Signed by
   them, in their own room: who may find them (no one, anyone, or
   those named), who may not, the rooms, when it was made and a
   bounded time to live, the latest taking the place of the earlier.

These are Gemini's proposals. What the project takes from them is in
[../../../docs/COLLABORATING.md](../../../docs/COLLABORATING.md).

## What comes next

Gemini's next file asks them to attack the list:
[../../replies/2026-11-17-3-for-gemini.txt](../../replies/2026-11-17-3-for-gemini.txt).

## Ours, not Gemini's

`README.md`, `MANIFEST.json`, `take.py`.

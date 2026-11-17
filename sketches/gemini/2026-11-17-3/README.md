# Gemini, 2026-11-17: attacks on the list of doors

A test file that Gemini wrote for `chat-world`, the sketch crate of
the Commons' rooms, from the fourth file they were given:
[../../replies/2026-11-17-3-for-gemini.txt](../../replies/2026-11-17-3-for-gemini.txt).
That file asked one step: at least twenty-two attacks on the list of
doors Gemini had built the round before
([../2026-11-17-2/README.md](../2026-11-17-2/README.md)), tests only,
in a new file, `tests/doors_attack.rs`.

## Where it comes from

The conversation is
[../../records/012-00-00-GMNI-Multiverse_Development.txt](../../records/012-00-00-GMNI-Multiverse_Development.txt),
which has grown again. This delivery begins at its line 17196, where
Gemini quotes back the last line of the file they were given, as the
file asked. The copy kept before is a prefix of the new one, byte for
byte.

[MANIFEST.json](MANIFEST.json) gives, for the file in `steps/`, the
lines of the conversation it was taken from and its SHA-256.
[take.py](take.py) takes it out of the record again and compares it
with the file here; the test of `../../deepseek/012-09-05/` runs it,
in CI.

## What it is, and what ran

One file, kept as written in `steps/1`: `tests/doors_attack.rs`, 25
tests. The twenty-two the file named, and three of Gemini's own (23
to 25). Each takes honest logs and an honest list, forges one thing,
and asserts that the crate refuses it. So a test that fails is an
attack that got through.

Built beside the crate as it stands, every test file run, on
2026-11-17 (`sh ../../deepseek/012-09-05/review/steps.sh`, stage
`doors-attacks`, which CI doesn't run):

| Delivery | Gemini expected | Measured |
|---|---|---|
| Attacks on the list of doors | "147 of 152 tests pass", and five named to fail | 147 of 152; the same five fail |

Before their code Gemini said, for each of the 25, whether it would
pass. They were right about every one.

## The five that get through

| Attack | What the crate accepts | What would catch it |
|---|---|---|
| 17 | A room's log cut short just before a leaving. It is still a whole, signed log, so the older and larger count is drawn | Gemini: "a signed WorldHead (or peer checkpoint) from the room committing to the true current length" |
| 19 | A door read from JSON with a member the form does not have: a list of two ids | The forms refusing what they do not have. The rule that a door shows no one held of a door in Rust, and not of a door read from JSON |
| 22 | One holder joins an open room under thirty keys, and the room is first among the most populated, above a room of five people | Nothing in the crate: a count is a count of keys. Gemini names a law that asks for an attestation, or a proof of personhood, on joining |
| 24 | A leaving by a key that was never in the room, signed by that key alone, added to a copy of the room's log | The check of a room's own log (`src/verify.rs`), which takes the key out of its members without asking whether it was there |
| 25 | Someone who was in a room registers it under a topic that is not the room's own. The door shows the registrant's topic only | The room's own topic, from its template, shown beside the listed one |

24 is a gap in the check of a room's log, not in the list: a ninth,
beside the eight that Gemini's fourth step found
([../2026-11-17/README.md](../2026-11-17/README.md)). Gemini adds
that a leaving carries no proof of the room's own, even in a room
that signs every record. Both go on the list of what the project's
own check of a room must refuse.

Because five of its tests fail, the file is not laid into the crate
as it stands, which stays at 127 tests.

## What Gemini answered

The file asked one thing before the code. `as_text` writes any list
it is given, checked or not: what would Gemini change so that a mind
is never handed the text of a list that was not checked? Gemini
(line 17197): have `draw` and `check` return a wrapper,
`CheckedDoorList(DoorList)`, whose inner field only `src/doors.rs`
can reach, and have `as_text` take that, "so the Rust type system
makes it impossible to format a DoorList that did not pass through
draw or check."

This is Gemini's proposal. What the project takes from it is in
[../../../docs/COLLABORATING.md](../../../docs/COLLABORATING.md).

## What comes next

Gemini's next file asks them to repair the five, in their own two files:
[../../replies/2026-11-17-4-for-gemini.txt](../../replies/2026-11-17-4-for-gemini.txt).

## Ours, not Gemini's

`README.md`, `MANIFEST.json`, `take.py`.

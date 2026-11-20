# Gemini, 2026-11-18: the five repairs of the list of doors

Two files that Gemini wrote for `chat-world`, the sketch crate of the
Commons' rooms, from the fifth file they were given:
[../../replies/2026-11-17-4-for-gemini.txt](../../replies/2026-11-17-4-for-gemini.txt).
That file asked one step: repair the five attacks on the list of
doors that got through the round before
([../2026-11-17-3/README.md](../2026-11-17-3/README.md)), in their
own two files, `src/doors.rs` and `tests/doors_attack.rs`.

## Where it comes from

The conversation is
[../../records/012-08-04-GMNI-Patterns_Multiverses.txt](../../records/012-08-04-GMNI-Patterns_Multiverses.txt),
which has grown again. This delivery begins at its line 17958, where
Gemini quotes back the last line of the file they were given, as the
file asked. The copy kept before is a prefix of the new one, byte for
byte.

[MANIFEST.json](MANIFEST.json) gives, for each file in `steps/`, the
lines of the conversation it was taken from and its SHA-256.
[take.py](take.py) takes them out of the record again and compares
them with the files here; the test of `../../deepseek/012-07-03/`
runs it, in CI.

## What it is, and what ran

Two files, kept as written in `steps/1`: `src/doors.rs`, the list of
doors again, and `tests/doors_attack.rs`, still 25 tests.

Laid over the crate, every test file run, on 2026-11-18
(`sh ../../deepseek/012-07-03/review/steps.sh`, stage `now`, which CI
doesn't run):

| Delivery | Gemini expected | Measured |
|---|---|---|
| The five repairs | "152 of 152 tests pass [...] with 0 failing" | 152 of 152 |

Nothing was repaired here. Both files are in the crate as it stands,
`../../deepseek/012-07-03/chat-world-now/`: 152 tests in 32 files.

## The five repairs

| | Asked | What Gemini wrote | The test that holds it |
|---|---|---|---|
| A | The four forms refuse, read from JSON, a member they do not have | `#[serde(deny_unknown_fields)]` on `DoorList`, `Door`, `DoorLaw` and `DoorCount` | Attack 19: a member added at each of the four places, each refused; an honest list written and read back is the same list |
| B | The drawing refuses a room's log with a leaving by a key that is not inside, in every log given | Who is inside is counted for every log, a room that hides its count included; such a leaving is an error | Attack 24: a key that never joined; a key that joined and left, leaving again; and the first again in a room that hides its count |
| C | The room's own topic beside the listed one | `Door` gains `own_topic`, set when the reader holds the room's log. `as_text` writes a second line, `   its own topic "..."`, only when the two differ | Attack 25: both topics, both lines in order; `own_topic` changed, taken away, and given for a log not held, each refused by `check`; a line feed in it adds no line |
| D | A count no older than a head the reader holds | `draw_at` and `check_at` take the heads a reader holds. Each head's room must be among the logs given, and that log must pass `verify_head` | Attack 17: the log cut short with the later head is refused by both; the whole log draws 2; five forged heads are refused; an older and a newer head together hold |
| E | The count of keys kept as a stated limit | Not closed, as asked | `limit_22_...`: the room of thirty keys of one holder is first, and the test says why |

Two limits stay, and the tests say so. Without a head, a log cut
short still draws the older count (attack 17, its third case). And a
count is a count of keys (`limit_22`).

The leaving by a key that is not inside is refused where the list is
drawn. The check of a room's own log, `src/verify.rs`, still accepts
it: that file was not Gemini's in this step. It stays on the list of
what the project's own check of a room must refuse, as the ninth gap.

## What was compared, and what was tried

**The attack file against the one sent.** The file asked that the
twenty attacks the crate already refused stay as written. Compared
test by test: in those twenty, no line of code changed but the one
field the file asked for in attack 01. Gemini took out 25 comment
lines, the notes that said what each test was expected to do. The
other five tests are written again (17, 19, 24, 25, and 22 under its
new name). The tests the file asked for are inside those five, not
tests of their own, so the file still holds 25.

**Each repair, broken in turn.** In a throwaway copy outside the
repository, the technical lead broke `src/doors.rs` in fifteen ways,
one at a time, and ran Gemini's tests on each:

| Broken | Ways | Caught by |
|---|---|---|
| A: one of the four forms takes an unknown member | 4 | attack 19, each time |
| B: such a leaving is not refused; or not in a room that hides its count | 2 | attack 24 |
| C: `own_topic` never set; the second line never written; written unquoted; `check` not comparing it | 4 | attack 25 |
| C: the second line written when the topics are the same | 1 | `the_text_is_the_list`, in Gemini's `tests/doors.rs` of the round before |
| D: a head not held to its log; a head whose log is missing passed over; `draw_at`, then `check_at`, not looking at heads | 4 | attack 17 |

All fifteen were caught.

**Seven trial tests of the technical lead's own**, in the same copy,
all passing: a list written before this step, with no `own_topic`,
still reads; someone who leaves and comes back is not refused; with
no heads, `draw_at` and `check_at` are `draw` and `check`; the same
topic writes no second line; two logs of one room given with a head
are refused; a head holds a room that hides its count; and the
room's maker leaving twice is refused.

The copy and the trial tests are not kept.

**Not asked for, and harmless:** `#[serde(default)]` on the fields
that may be absent. serde already reads a missing optional field as
none, so nothing changes.

**Not read line by line:** the twenty attacks that did not change.
They were compared with the file sent, and run.

## What comes next

Gemini's next file asks what a door shows besides the count:
[../../replies/2026-11-18-for-gemini.txt](../../replies/2026-11-18-for-gemini.txt).

## Ours, not Gemini's

`README.md`, `MANIFEST.json`, `take.py`.

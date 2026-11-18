# What DeepSeek and Gemini were given

The founder, 2026-11-16: "let's put it all in a single file and I will
provide the file. No link necessary. Just one long file within
everything included. But only what is needed to continue working."
And: "My hope is that you will find a way to integrate everything, and
allow me to continue with DeepSeek without ever requiring more than a
file to provide the current project state."

So each time the founder returns to DeepSeek, the technical lead
builds one file: the reply to DeepSeek's last record, the next steps,
and the code as it stands, each file whole. This folder keeps every
such file, as a record of what DeepSeek was given, with what it was
built from.

From 2026-11-16 there are two collaborators, DeepSeek and Gemini, and
a file is written for the one who is to receive it. The founder: "My
proposal earlier was meant to avoid they by updating with a new file
each time. That way the instructions can be geared toward the
recipient." What is said here of a file for DeepSeek holds for a file
for Gemini.

## For each reply, three files

Named for the record the reply answers, or, where there is no record
to answer, for the day it was given and the one it was for
(`2026-11-16-gemini`):

| File | What it is |
|---|---|
| `NAME.txt` | The reply itself, written by the technical lead: all that comes before the code |
| `NAME.json` | What goes with it: the folder the code comes from, the files in order, a note for each, and the most bytes the file may have |
| `NAME-for-deepseek.txt`, or `DATE-for-gemini.txt` | The file as the founder was given it: the reply, then each file whole, then the line `END OF FILE`, which the one who receives it is asked to quote back |

`python3 docs/reply.py sketches/replies/NAME.json` writes the third
from the first two and the repository's files, and reads it back
from disk to compare each file with the repository. `--check` says whether the file
kept here is still what they make. `tests/test_reply.py` runs that
check for every reply here.

## Current, and past

A spec's `current` is true while the code in the repository is still
as the file has it. Then the file can be made again, byte for byte,
and the test holds it to that. When the code moves on, `current`
becomes false, in the same change: the file stays here, untouched, as
the record of what DeepSeek was given at the time, and a new reply is
written for the next return. What holds a past file to "untouched" is
its hash in the table below, which the test compares with the file.

## The limit

Each spec sets the most bytes its file may have, so that it can be
given whole, as one upload. The script refuses to write a longer one.

## The replies

| Reply | For | Answers | Given | Bytes | SHA-256 |
|---|---|---|---|---|---|
| `2026-11-18-gemini` | Gemini | Their five repairs: 152 of 152 as they expected; what was compared, and that each repair broken on purpose was caught by a test of theirs. Then one step, four parts and a question: beside the count a door shows how many messages a reader sees and how many wrote them; a rule marks a room with ten or more in it and nothing said; the doors listed by any of the three numbers; and a look into a room that anyone may enter, as text, held to the Commons and to a head the reader holds. Nine of the crate's thirty-two files as they stand, two of them theirs; the other twenty-three are named and left out, their attack file among them, of which they change one line from their own last reply | built 2026-11-18 | 91,773 | `54dae24fe8d547b0fb57e5f6a12ab67b421b27a025d35eeb211f4a660676b909` |
| `2026-11-17-4-gemini` | Gemini | Their attacks on the list of doors: 147 of 152 as they expected, the five they named getting through; what is done with what they said. Then one step: five repairs, in their own two files, `src/doors.rs` and `tests/doors_attack.rs`. The forms refuse a member they do not have; a leaving only by a key that is inside; the room's own topic beside the listed one; `draw_at` and `check_at`, which hold a room's log to a head the reader holds; and the count of keys kept as a stated limit. Twelve of the crate's thirty-one files as they stand, `src/head.rs` among them for the first time. Their own attack file is not among them: it is kept beside the crate, and Gemini is asked to work from their last reply for that one file | by 2026-11-18, when the answer came back | 95,491 | `77f33e0df26cb38c3abfb64001ad233b1780e91a14aada82ece8583cf80dc5aa` |
| `2026-11-17-3-gemini` | Gemini | Their list of doors: 127 of 127 as they expected, and each of two builds from the one file passing the other's tests; what is done with their three answers. Then one step: twenty-two attacks on the list, tests only, in a new file `tests/doors_attack.rs`: a list forged against the check, the logs forged against the drawing, a list read from JSON, the text, and what a count of keys means. Twelve of the crate's thirty-one files as they stand, their own `src/doors.rs` among them; the other nineteen are named and left out | 2026-11-17 | 111,151 | `e4702b7690087c7ffa09b33782834b99ff52ca425dcbb5f8ea6fddfd3b3f14b7` |
| `2026-11-17-2-gemini` | Gemini | Their four steps on the Commons: what each built to, why the eight gaps of the fourth are not repaired in the sketch, and what the project takes from their sketch of a moderator. Then one step: the lobby's list of doors, which is what a map of the Commons is first drawn from, in a new file `src/doors.rs` with fifteen tests. A door shows a room, its law, and how many are in it unless the room's law hides that; the most populated can be listed first. Eight of the crate's twenty-nine files as they stand, with DeepSeek's branches and plug-in in them; the other twenty-one are named and left out. Built four times before it was given: first; then with the founder's words on what can be seen from outside; then on the crate with DeepSeek's work; then with the count, at the founder's decision | 2026-11-17 | 78,333 | `4372393fe8dca162b654c3363e4b6564ffb627dc0a99e333db4d0f76f8f47c6f` |
| `2026-11-17-gemini` | Gemini | Their four deliveries: what each built to, the two repairs, and why the fourth is not used. Then four steps on the Commons' own log, in files DeepSeek's step does not touch: the log read from outside (a Commons record can't be read back from JSON today), attacks on its check, repairs with two checks across logs, and attacks on the room's seven other kinds of record, tests only. Thirteen of the crate's twenty-two files as they stand; the other nine are named and left out | 2026-11-17 | 97,419 | `a37631b6d06596435c41848cd7cc178bcbe05c4e90f296d76fbc12212d98e108` |
| `012-09-05-2` | DeepSeek | Record 012-09-05, continued: what their five deliveries built to, the repairs, what Gemini then found and repaired, one step (a room that branches, which is how a room's law changes), and one question on signed heads. Ten of the crate's twenty-two files as they stand; the other twelve are named and left out | 2026-11-17 | 99,521 | `6e42350cac184ca76478272b5c2a52dc99f0751e9f1197c3ffe05666f42fe9df` |
| `2026-11-16-gemini` | Gemini | No record: Gemini's first file. Where the project stands, how we work, three steps (a room's log checked from outside; attacks on the check; repairs), and the `chat-world` crate as it stands after DeepSeek's five deliveries, sixteen files, its demos left out | 2026-11-16 | 119,297 | `324d1392a495fff72480460f27617950d64f3b475f90079720031f7a0b417609` |
| `012-09-05` | DeepSeek | Record 012-09-05: the first pass, the repairs, the answers to DeepSeek's two questions, three next steps, and the `chat-world` crate as it stands, sixteen files | 2026-11-16 | 95,149 | `f1f7435f21dbaf8d49de3aea07e83d502d38c6011323feb591b769c2c1c97447` |

## Found after a file was given

A file that was given is not changed. What was later found wrong in it
is said here, and in the next reply.

- `2026-11-17-4-gemini` and `2026-11-17-3-gemini`: no longer
  current, from 2026-11-18. Gemini did the step of the first, the
  five repairs, 152 of 152 (`../gemini/2026-11-17-4/README.md`).
  `src/doors.rs` is now the list as they repaired it, so it is no
  longer as either reply has it. Nothing was found wrong in either
  file. The first asked that the twenty attacks which already held
  stay as written; Gemini took 25 comment lines out of them and
  changed no code in them.
- `2026-11-17-2-gemini`: no longer current, from 2026-11-17. Gemini
  did their step the day it was given, 127 of 127
  (`../gemini/2026-11-17-2/README.md`). `src/lib.rs` now holds the
  line that names the new module, so it is no longer as this reply
  has it.
- `012-09-05-2`: no longer current, from 2026-11-17. DeepSeek did their
  step, a room that branches, and at the founder's word went on to a
  plug-in and began a third step. Their first two deliveries are in the
  crate as it stands, so four of the ten files this reply holds
  (`src/record.rs`, `src/room.rs`, `src/verify.rs`, `src/lib.rs`) are
  no longer the crate's. The file stays as it was given
  (`../deepseek/012-09-05/README.md`, "Three more").
- `012-09-05-2`, parts 2 and 6: it says the crate has 66 tests, and
  that `src/commons.rs` is as DeepSeek wrote it. After Gemini's round
  on the Commons, the same day, the crate has 92 tests, and
  `src/commons.rs` and three new test files are Gemini's
  (`../gemini/2026-11-17/README.md`). The ten files the reply holds
  are unchanged, byte for byte, so the reply is still current, and
  DeepSeek's step is not affected: laid over the crate as it stands,
  its count will be 92 and its new tests, not 66 and them.
- `2026-11-17-gemini`: Gemini did the first three of their four steps,
  and `src/commons.rs` in it is no longer the crate's. The fourth
  step, attacks on a room's other records, can still be done from it:
  that step reads `src/verify.rs`, which has not changed.
- `012-09-05-2`, part 2: "Only one of you writes it at a time." That
  was the rule when the file was written. Hours later the founder had
  Gemini free and DeepSeek not yet, and Gemini was given a file to
  work at the same time (`2026-11-17-gemini`), on files that
  DeepSeek's step does not touch: `src/commons.rs` and new test files.
  DeepSeek's step and its files are not affected. Their next file says
  what Gemini did meanwhile.
- `012-09-05`, part 1: "33 of your tests failed for that alone". All
  33 stopped first at those two causes, as written. But three of the
  sixteen still fail with the change applied, as part 2 of the same
  file says, and the home room's seventeen have not been run with its
  later additions joined. "For that first" is what was shown (#98's
  independent review).
- `2026-11-16-gemini`, part 3, step 1: it asks that `verify_log` hold
  a log's template to the one in its first record, and also says "all
  41 tests still pass unchanged". Both could not hold: two of the 41
  changed a room's template after creating it. Gemini did as asked,
  and those two fail as written (`../gemini/2026-11-16/README.md`).
  The same file asks Gemini to quote its last line back; Gemini did
  not, and went straight to the work.

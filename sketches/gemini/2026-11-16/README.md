# Gemini, 2026-11-16: the crate, attacked

Code that Gemini wrote for `chat-world`, the sketch crate of the
Commons' rooms, in a conversation with the founder that began from one
file: [../../replies/2026-11-16-for-gemini.txt](../../replies/2026-11-16-for-gemini.txt).
That file gave Gemini the crate as it stood after DeepSeek's five
deliveries and asked for something DeepSeek had not been asked: to try
to break it.

Four deliveries came back. The first three are the three steps the file
asked for. The fourth was not asked for and is not used.

## Where it comes from

The conversation is not in this repository. It goes on from an earlier
one that holds personal things, so it is kept private (STATUS.md,
"Decided", 2026-11-16, on naming Gemini). It is named here by its size
and hash: 574,505 bytes, SHA-256
`39aea56cb85ed9f3b2c928b01bd7802b552e24f84c5e05a5bac7187bfd410d31`.
What Gemini wrote after it was given the file begins at line 9748.

[MANIFEST.json](MANIFEST.json) gives, for each file in `steps/`, the
lines of the conversation it was taken from and its SHA-256.
[take.py](take.py) is the script that took them out. Anyone who holds
the conversation can run it and see that the files here are those.

One limit follows, said plainly: DeepSeek's code in `../../deepseek/`
can be checked against a record that is in this repository, and
Gemini's can't. What holds these files is the manifest's hashes, which
`../../deepseek/012-09-05/review/steps.py --check` compares in CI.

The export of the conversation has no code fences. A file runs from
the line after the one that names it to the line before the next name,
or before the delivery's last line, which begins "Expected:".

## What each delivery is, and what ran

Each is laid over the one before, starting from the crate Gemini was
given, and every test file of the crate is run
(`sh ../../deepseek/012-09-05/review/steps.sh`, which CI doesn't run:
it needs Rust and the network). Measured on 2026-11-17. "Expected" is
Gemini's own line; it can't build the crate where it writes.

| Delivery | What it is | Files | Expected | Measured |
|---|---|---|---|---|
| 1 | A room's log that can be checked from outside: `RoomLog` (the room's id, its template, its records and its heads, nothing secret), `Room::log()`, `verify_log`, and a head checked against a `RoomLog`. `verify_room` now calls `verify_log`, so there is one check | 5 | "44 tests pass" | 42 of 44. Its 3 new tests pass. 2 of the crate's earlier 41 fail |
| 2 | Attacks: 22 tests, each of which forges one thing in an honest log and asserts that the check refuses it | 1 | "63 of 66 tests pass", naming the three attacks that would get through | 61 of 66. 19 of the 22 attacks are refused; the three Gemini named get through; the same 2 of 41 fail |
| 3 | Repairs | 2 | "66 tests pass" | 64 of 66. All 22 attacks are refused; the same 2 of 41 fail |
| 4 | Branches for rooms. Not asked for | 2 of the 4 it describes | "All 41 earlier integration tests plus new branch tests pass" | Does not compile (8 errors). Not used |

With the two earlier tests corrected (fix 22, below), all 66 pass, and
the crate's four demos run. The crate as it stands,
`../../deepseek/012-09-05/chat-world-now/`, is that with one more
repair (fix 23, below); it too passes all 66, and its demos run.

## What Gemini found

Three ways a forged log got past the check, each found by reading the
code, written as a test that fails, and then repaired:

1. **Rules were enforced only when a record was written.** The limit
   on how many messages one author may post in a window, the longest
   message, and the pace between two AIs were checked by `Room::post`
   and never by the check of a log. A forged log could hold a hundred
   messages where the room's rule allows two.
2. **So was who may join.** A room for people only, or for AIs only,
   or by invitation, refused the wrong joiner when it was asked, and
   the check of a log did not look.
3. **A tail no one had signed.** A room may sign its log's head every
   so many records in place of signing each record. Records after the
   last signed head then carried only their author's signature, so
   anyone could add one. The repair: a room's published log ends with a
   head that covers all of it, and the check refuses a log whose last
   head does not.

The third bears on open-worlds itself, where a world signs its log's
heads in batches (STATUS.md, "Noticed").

## The two earlier tests that fail, and fix 22

`rate_limit_enforced` and `inter_ai_pace_fires` are DeepSeek's. Each
made a room and then changed its template in place
(`room.template.rate_limit_count = 2;`), with no record of the change.
Gemini's check holds a log's template to the one its first record
carries, as the file asked, and refuses: "room_created template does
not match log template". The check is right. A room's law changed with
no record is what a forger would do.

The file given to Gemini was at fault for the count: it asked for that
check and also said all 41 earlier tests would still pass unchanged.
Both could not hold ([../../replies/README.md](../../replies/README.md),
"Found after a file was given").

Fix 22 changes the two tests to set the rule before the room is
created. What they test is unchanged. It is in `REPAIRS_AFTER` in
`../../deepseek/012-09-05/review/steps.py`.

## Fix 23: a room's law can't be changed in place

After Gemini's three, `Room.template` and `Room.world_id` were still
public fields, so a room's law could still be changed in place in
memory, as the two tests had done; the check caught it only in a
published log. Fix 23, made here, makes the two fields private. They
are read through `world_id()` and `template()`, which the crate had.
Three more of the earlier tests set a room's moderation to
"moderator" after creating it, which it already was; those three
lines did nothing, no longer compile, and are removed. It is in
`REPAIRS_AFTER` too, and [../../INDEX.md](../../INDEX.md) lists it
with the other changes.

## Left as written, for whoever goes on

Seen by the technical lead and not changed:

- `Room::log()` signs a new closing head each time it is called, and
  if signing fails it gives the log without one, which the check then
  refuses. DeepSeek, who designed the signed heads, is asked what it
  makes of the rule ([../../replies/012-09-05-2.txt](../../replies/012-09-05-2.txt),
  part 5).
- `tests/attack.rs` imports `RoomLog` and does not use it: one
  warning when the crate is built.
- Gemini did not quote the file's last line back, as the file asked.
  Its work uses the last files of the crate, so the file reached it.

## The fourth delivery

Kept in `steps/4/` as written, and not laid over the crate. It gives
`src/record.rs` and `src/room.rs` of the four files it describes; the
conversation ended before the check and the tests came. It does not
compile: its `record.rs` goes back to an earlier shape of a redaction
(`role` where the crate has `actor_role`), and its `room.rs` calls two
helpers the crate does not have (`_now`, `_canonical`).

## Ours, not Gemini's

`README.md`, `MANIFEST.json`, `take.py`.

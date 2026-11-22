# Gemini: what a door shows besides the count

Three files that Gemini wrote for `chat-world`, the sketch crate of
the Commons' rooms, from the sixth file they were given:
[../../replies/2026-11-18-for-gemini.txt](../../replies/2026-11-18-for-gemini.txt).
That file asked one step in four parts, and one question first:

- **A.** Beside the count, a door shows how many messages a reader of
  the room sees and how many different people wrote them (`DoorTalk`:
  `said`, `speakers`, `at_record`).
- **B.** A rule that anyone can run again marks a room with ten or
  more in it and nothing said (`QUIET_FROM`, `quiet`), and the list's
  text says so on the door.
- **C.** The doors listed by any of the three numbers (`By`,
  `ranked_by`).
- **D.** A look into a room before entering it (`look`): the text of
  what has been said, for a room that anyone may enter, held to the
  Commons and to a head the reader holds.
- **The question:** a room whose law hides its count, but lets anyone
  in, still gives a look, and the look shows who spoke. Should it?

## Where it comes from

The conversation is
[../../records/012-08-04-GMNI-Patterns_Multiverses.txt](../../records/012-08-04-GMNI-Patterns_Multiverses.txt).
The founder gave Gemini the file at line 19220; Gemini quotes back its
last line at line 19223, as the file asked, and the delivery ends with
its "Expected:" line at line 21436. It was already in the copy of the
record kept on 2026-11-20, but was not kept or built until
2026-11-22: on 2026-11-21 the technical lead took the file as not yet
given, which was wrong (`../../replies/README.md`).

[MANIFEST.json](MANIFEST.json) gives, for each file in `steps/`, the
lines of the conversation it was taken from and its SHA-256.
[take.py](take.py) takes them out of the record again and compares
them with the files here; the test of `../../deepseek/012-07-03/`
runs it, in CI.

## Gemini's answer to the question

Line 19224, before the files, as the file asked:

> On the question before the files: when a room is open to anyone
> (join_policy: "open", personal: false) yet sets count_hidden: true,
> look should still give the conversation text (since anyone can join
> to read it anyway), but it should omit or anonymize the author IDs
> [...] or else refuse look altogether when count_hidden is true.
> Why: Door hides talk (said and speakers) whenever count_hidden is
> true because the number of speakers bounds the number of members
> (speakers <= members); if look prints every message's author
> did:key to an unjoined reader, anyone can count the distinct
> did:keys in look (defeating count_hidden for speakers and said) and
> learn who is inside from outside the room without ever crossing the
> threshold via Room::join.

The reason is right, and one of the remedies does not hold: authors
numbered within the room ("speaker #1") can still be counted, so the
count is still given away. What holds is a look with no authors at
all, or no look. The file asked for the answer in words and not in
code, so `look` still shows who spoke in such a room. Which of the two
it should do is the founder's to say, and it stays open until then.

## What it is, and what ran

Three files, kept as written in `steps/1`: `src/doors.rs`, the list of
doors with the four parts; `tests/doors.rs`, with four new tests (19
in all); and `tests/doors_attack.rs`, still 25 tests, with the one line
the file asked for (`talk: None,`) and nothing else changed.

Laid over the crate, every test file run, on 2026-11-22:

| Built on | Gemini expected | Measured |
|---|---|---|
| The crate they were given (`repairs`, 152 tests) | "156 of 156 tests pass (152 earlier and 4 new tests in tests/doors.rs), with 0 failing" | 156 of 156 |
| The crate as it stands since (`now`, 162 tests: DeepSeek's rule of one moderator's room) | | 166 of 166 |

Nothing was repaired here. The three files are now in the crate as it
stands, `../../deepseek/012-07-03/chat-world-now/` (stage `said` of
`../../deepseek/012-07-03/review/steps.py`): 166 tests in 34 files, 71
of them DeepSeek's and 95 Gemini's.

## What was checked beyond running it

- **The step as the file gave it.** Each part was read against the
  file: the forms, their fields and order; `said` taken from the
  room's log as a reader sees it; `talk` given exactly where `count`
  is; the two new lines of the list's text, word for word; the order
  of `ranked_by`, ties in the list's order; and `look`, which holds
  the room to the Commons with `draw_at` first, refuses a room that is
  not open to anyone or is a home, writes the lines the file gives,
  and writes nothing else.
- **What they changed of their own.** In `tests/doors.rs`, the one
  test the file said must change, `the_text_is_the_list`, gains the
  new line in what it expects, and one line before it that reads the
  door's `talk`; nothing else in it changes, and the other fourteen
  tests are as they were. In `tests/doors_attack.rs`,
  the one line.
- **Each part broken on purpose,** in a throwaway copy, twelve ways,
  one at a time, and the crate's tests run each time:

  | Part | Broken so that | Caught |
  |---|---|---|
  | A | removed messages are counted as said | yes |
  | A | `speakers` is the number of messages | yes |
  | A | `talk`'s record number is one short | yes |
  | B | a room of exactly ten is not flagged | yes |
  | B | a room is flagged whatever was said | yes |
  | B | the list's text leaves out the flag | yes |
  | A | the list's text leaves out what was said | yes |
  | C | listing by what was said uses the count | yes |
  | C | ties are listed backwards | yes |
  | D | a look into a room that is not open to anyone | yes |
  | D | a look not held to the Commons and the heads | yes |
  | D | a look shows a removed message's text | yes |

  All twelve were caught by Gemini's tests. The copy is not kept.

## What stays open

- The question: a look into a room that hides its count but lets
  anyone in shows who spoke, and so how many. What holds is a look
  with no authors, or no look; numbering the authors still shows how
  many. The founder's to decide.
- The flag's number, ten, is a constant in the sketch. In the
  project's own door it is to be in the Commons' law, where a change
  to it is on the record (the file, part B).
- What comes after, as the file said: attacks on these four parts, as
  Gemini attacked the list.

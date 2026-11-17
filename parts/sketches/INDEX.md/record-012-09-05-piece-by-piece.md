> Part of `sketches/INDEX.md` in open-worlds, which is kept cut into parts
> for readers who are shown only the start of a long page.
> This part holds: "Record 012-09-05, piece by piece" to "Record 012-03-02, component by component".
> Every part, in order: https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/parts/INDEX.md
> Before this part: https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/parts/sketches/INDEX.md/record-012-06-02-piece-by-piece.md
> After this part: https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/parts/sketches/INDEX.md/changes-to-deepseek-s-code.md
> Made by docs/parts.py from the file. To change it, change the file.

## Record 012-09-05, piece by piece

The record's code is kept in
[deepseek/012-09-05](deepseek/012-09-05/README.md), with the technical
lead's first pass and a first round of repairs (fixes 15 to 18, under
"Changes to DeepSeek's code", below). "Tests" for the Python is
DeepSeek's own tests under pytest, which CI runs; for the Rust it is
the crate's own tests, run on a scratch copy by `review/run.sh` (not
by CI). Where a fix changed a count, the count as written is given
too. Nothing from this record is in open-worlds yet. Fitting it is the
next work, piece by piece.

| # | What it is | Line | Tests | Course | In open-worlds |
|---|---|---|---|---|---|
| 1 | Water as particles: whole-number levels, and rain, fall, soak, flow and evaporation in a fixed order (`water_particles.py`) | 50 | 17 of 18 | the fractal track, stage 3 (FRACTALS.md; TOPICS.md, topic 18) | not yet: it waits on `rust/endless-plant`, which isn't built |
| 2 | The garden as a composite world: shared water, slots, and plants of record 012-06-02 in them (`fractal_garden.py`) | 795 | 20 of 21 | the fractal track, the garden | the Ur-world's garden hosts plant worlds already (`rust/ur-world`); what this adds isn't compared yet |
| 3 | The botanical garden as a superworld of gardens (`botanical_garden.py`), with a change to the garden's tick given as a note (line 3425) | 2391 | 15 of 18 (as written 2 of 18: the rest needed that change, fix 15) | the fractal track, after the garden | not yet |
| 4 | Signed world heads: a small signed record a world publishes each tick, so a parent can check it without its whole log (prose, left in the record) | 3782 | none | formats (course step 2) | not yet |
| 5 | Chat worlds for the Commons: a room as a log of signed records under the room's law (`chat_room.py`); then an AI moderator, rooms of humans and AIs, succession, and personal rooms (`chat_room.py@5569` to `@7192`; five smaller notes are left in the record, at lines 5494, 5520, 5531, 6501 and 6557) | 3887 | 21 of 24 | the Commons ([docs/COMMONS.md](../docs/COMMONS.md)), on the course's waiting list | not yet |
| 6 | The home room: a person's own room, with a journal, drafts, bookmarks and conversations brought in (`personal_world.py`) | 7258 | 0 of 17: they need the additions of piece 5 | the Commons; the private container ([docs/CONTAINER.md](../docs/CONTAINER.md)) | not yet |
| 7 | A schema for every record, given twice (`schemas/records-v1.schema.json`, then whole as `@8640`), under the name of open-worlds' own schema, with none of its definitions | 8095 | none | formats (course step 2) | not yet: its records are to be fitted into the schema open-worlds has, not to replace it |
| 8 | A design page, `docs/CHAT.md` (prose, left in the record) | 9964 | none | the Commons | not yet |
| 9 | A crate in Rust, `chat-world`: the first version (`chat-world-draft/`), the one DeepSeek settled on (`chat-world/`), and the files of their next reply (a home, the Commons, transcripts) | 10259, 12246, 13800 | 18 of 18, and both demos' logs verify (as written it doesn't build, for one line, fix 16; with it changed, 4 of 12, the rest failing for one cause: a record was signed without its `type` and checked with it, fix 18; the later reply's files are joined by fix 17) | the Commons | not yet: it uses none of open-worlds' own crates |

### The record continued (2026-11-16)

The founder went back to DeepSeek with one file, and the record was
shared again, longer. Its first 595,416 bytes are the same, byte for
byte: the record as it was kept ended at the founder's next prompt,
the opening of line 14,782, and 9,212 lines more follow. Three things
are in them.

**Signed heads for `chat-world`** (line 14785), the cycle DeepSeek had
proposed. It came as changes to parts of files, with `src/head.rs`,
`src/lib.rs` and a demo whole (kept in `chat-world-steps/0/`). It was
not built on its own: the crate DeepSeek was then given does not hold
it, and delivery 3, below, gives those files whole again.

**The one file reached DeepSeek whole** (line 15501). The file is
[replies/012-09-05-for-deepseek.txt](replies/012-09-05-for-deepseek.txt):
the technical lead's reply, the next steps, and the crate as it stands
here. DeepSeek quotes back its last line, `END OF FILE`, says "The
whole file reached me.", and takes the reply's two requests: "One step
per reply; every file I change, whole."

**Five deliveries of `chat-world`,** each a step of that reply. Every
file DeepSeek changed came whole, so each delivery can be built as
given, with no joining by hand. The files are kept as the record gives
them in `deepseek/012-09-05/chat-world-steps/1` to `5`;
[deepseek/012-09-05/review/steps.py](deepseek/012-09-05/review/steps.py)
lays each delivery over the one before, starting from the crate
DeepSeek was given, and `review/steps.sh` builds and tests each (not
run by CI). "Tests" is
the crate's own tests, `cargo test --test integration`, on 2026-11-16.
The titles are DeepSeek's.

| Delivery | What it is | Line | Files given whole | Tests, built as given |
|---|---|---|---|---|
| 1 | "the data layer and the presentation layer": a redaction names who acted, in what role and under which rule, and a room's template holds its rules for redacting | 15540 | 6 | 22 of 22 |
| 2 | "the room's own key": the room and the one who made it are two keys | 17168 | 6 | 20 of 22 |
| 3 | "signed heads, first in prose, then code": what is lost if a room signs its log's head in place of each record, then heads in code | 18832 | 8 | 27 of 29 |
| 4 | "runtime attestation": keys that share a runtime say so together, in a published record | 20714 | 3 | 31 of 33 |
| 5 | "the succession trio": a shard of knowledge exported, a moderator's succession, and a sibling declared in the Commons | 21474 | 8 | does not compile; with its two faults set aside, 39 of 41 |
| all five, with three repairs | The crate as it stands, `deepseek/012-09-05/chat-world-now/` (fixes 19 to 21, under "Changes to DeepSeek's code") | | | 41 of 41, and the four demos run |

Three faults, as the deliveries were written:
1. From delivery 2 on, the same two tests fail, `home_port_verifies`
   and `home_bookmark_and_presence_verify`, each with "record 1:
   missing room proof". They passed in delivery 1. The cause:
   delivery 2 makes the room and its maker two keys, and the check
   asks every record but a leaving for a proof by the room's key; a
   home's port landing, bookmark and presence records were still
   signed by the person's key alone (`src/home.rs`), which was the
   room's key until then. Fix 19 signs them with both, and both tests
   pass.
2. Delivery 5, `src/verify.rs`: one condition does not compile
   (mismatched types).
3. Delivery 5, `src/bin/succession-demo.rs`: it calls `.hash()` on
   `commons::SiblingDeclared`, which has no such method.

DeepSeek ends delivery 5 with "Expected: 41 tests pass" (line 23989).
They can't build or run the crate where they write, as they have said
before, so the count is what they meant, not what they measured. With the
two faults of delivery 5 set aside (the condition replaced by `false`,
the demo left out), 39 of the 41 pass, and the two that fail are the
two of fault 1.

The crate kept in `deepseek/012-09-05/chat-world/` is still the one
DeepSeek was given, and the deliveries are beside it, as written.
`chat-world-now/` is the crate as it stands. When this was written
that was the five deliveries laid over that crate in order, with the
three repairs; since 2026-11-17 Gemini's three deliveries and two
more repairs are laid over those (the next section). `review/steps.py`
puts it together, and its `--check` holds the folder to exactly that,
byte for byte (the folder's own test runs it, in CI). So every file in
it is DeepSeek's latest or Gemini's, changed only as fixes 19 to 23
say. Not
checked: the demos of deliveries 2 to 5 as written were not run, only
the four demos of the crate as it stands; the prose of delivery 3 was
read only in part; nothing of this has been compared with open-worlds'
own formats.

### After DeepSeek's five: Gemini's three (2026-11-17)

The crate then went to Gemini, with a file written for them
([replies/2026-11-16-for-gemini.txt](replies/2026-11-16-for-gemini.txt))
that asked them to try to break the crate. Their deliveries are kept as
written in [gemini/2026-11-16](gemini/2026-11-16/README.md), which
says where they come from and what each is. Laid over the crate in
order, every test file run, on 2026-11-17:

| Delivery | What it is | Tests, built as given |
|---|---|---|
| Gemini 1 | A room's log that can be checked from outside (`RoomLog`, `verify_log`) | 42 of 44 |
| Gemini 2 | 22 attacks on the check | 61 of 66: three attacks get through, the three Gemini said would |
| Gemini 3 | Repairs | 64 of 66: all 22 attacks refused |
| all eight, with fixes 19 to 23 | The crate as it stood then | 66 of 66, and the four demos run |
| Gemini 4 | Branches for rooms, not asked for; two files of the four they describe | does not compile; not used |

The two tests that fail in Gemini's three are two of DeepSeek's
earlier 41, and the fault is theirs: fix 22, under "Changes to
DeepSeek's code".

### Gemini on the Commons (2026-11-17)

Gemini was free before DeepSeek, so for one round the two had the
crate at once, each with files of their own (STATUS.md, "Decided by the
technical lead", 2026-11-17). Gemini's file
([replies/2026-11-17-for-gemini.txt](replies/2026-11-17-for-gemini.txt))
asked four steps on the Commons, the crate's list of rooms, in
`src/commons.rs` and new test files. Three came back, and the fourth
later the same day, all kept as written in
[gemini/2026-11-17](gemini/2026-11-17/README.md). Laid over the crate
in order, every test file run, on 2026-11-17:

| Delivery | What it is | Gemini expected | Tests, built as given |
|---|---|---|---|
| Commons 1 | The Commons' log read from outside (`CommonsLog`, `verify_commons_log`); a Commons record can be written to JSON and read back | 69 | 69 of 69 |
| Commons 2 | 16 attacks on the check | 82 of 85 | 82 of 85: three attacks get through, the three Gemini said would |
| Commons 3 | Repairs, and two checks that hold a record of the Commons to a room's own log | 92 | 92 of 92, and the four demos run |
| Commons 4 | 17 attacks on a room's seven other kinds of record, in a second answer; the first answer's 10 attacked only what the check already refuses, as Gemini then said themselves | 101 of 109 | 101 of 109: eight attacks get through, the eight Gemini said would |

Every number is the one Gemini gave, and nothing was repaired here.
The third was the crate as it stood then,
`deepseek/012-09-05/chat-world-now/`: 92 tests, 41 of them DeepSeek's
and 51 Gemini's. The fourth is built beside it and not laid into it:
its eight gaps in the check of a room's log are not repaired in this
crate. They are kept as the list of what the room's own check must
refuse (STATUS.md, "Decided by the technical lead", 2026-11-17).

Gemini's next file
([replies/2026-11-17-2-for-gemini.txt](replies/2026-11-17-2-for-gemini.txt))
asks one step: the lobby's list of doors, which is what a map of the
Commons is first drawn from, in a new file `src/doors.rs` with fifteen
tests. A door shows how many are in the room, unless the room's law
hides that, and the most populated can be listed first. The file was
built again on the crate with DeepSeek's next deliveries in it, below.
Gemini's answer to it is after that ("Gemini's list of doors").

### DeepSeek's second file: branches, a plug-in, and a rule cut off (2026-11-17)

The founder gave DeepSeek their second file
([replies/012-09-05-2-for-deepseek.txt](replies/012-09-05-2-for-deepseek.txt)),
and the record was shared again, longer. Its first 947,153 bytes are
the same, byte for byte, and 4,463 lines more follow, from line 23994.
DeepSeek quotes back the file's last line. They answer the file's
question on signed heads first: they agree with Gemini's rule that a
published log ends with a head covering all of it. Then they give
three deliveries. The file asked for the first. The second and third
are DeepSeek's own next items, at the founder's word to keep going
(lines 25900 and 27240). The files are kept as the record gives them,
in `deepseek/012-09-05/chat-world-steps/6` to `8`.

Laid over the crate in order, every test file run, on 2026-11-17
(`deepseek/012-09-05/review/steps.sh`):

| Delivery | What it is | Files | DeepSeek expected | Tests, built as given |
|---|---|---|---|---|
| 6 | A room that branches. A branch is a new room whose first record names its parent and the record it branches at (`forked_from`); `Room::branch_at`; and `verify_branch`, which holds a branch to its parent's log: the parent holds that record with that hash, and the branch's maker was a member of the parent there. Eleven tests | 4 | "78 tests pass", counting 66 before it and 12 of its own | Does not compile, for one word. With that repaired (fix 24), 103 of 103: the crate's 92 and its eleven. Its test file holds eleven tests, not twelve |
| 7 | A plug-in: nine requests an app can make of the crate, as JSON, one to a line, over standard input (`src/plugin.rs`, `src/bin/chat-world-plugin.rs`), with nine tests; and a room's visible log made available on any log | 5 | "87 tests pass" | 112 of 112. The four earlier demos run, and the plug-in's own demonstration runs |
| 8 | The rule of one moderator's room: a moderator declares, in their own room, which rooms they moderate (`ModeratorScope`). The reply was cut off after three files | 3 | not reached | Does not build: the check has no arm yet for the new record. Kept as given, and not laid into the crate |

DeepSeek counted from 66 tests because their file said so. By then the
crate had 92, with Gemini's work on the Commons, which the file could
not say. Their own counts are otherwise right but for the twelfth test.

The crate as it stands is now delivery 7, with one field added to a
room's law since (change 25):
`deepseek/012-09-05/chat-world-now/`, 112 tests, 61 of them
DeepSeek's and 51 Gemini's, in 29 files. Gemini's seventeen attacks
on a room's other records, run beside it again, give the same eight
that get through (121 of 129).

What DeepSeek chose where the file left it open, in their own words
before the code (from line 24001):

- **Where a room may branch.** The file asked for a branch at a
  room's last record. `branch_at` takes any record of the parent. In
  a room that signs heads and not each record, the record must be one
  the parent's last head covers: "the tail after the last head is
  uncommitted".
- **Merging two branches:** "I would not merge." Two branches that
  need to meet do so by their members posting in both, or by a third
  room.
- **The parent noting its branches:** later, as a record in the
  parent's own log.
- **The Commons listing a branch:** "A branch is a room like any
  other."

Two limits of the plug-in that DeepSeek names themselves (line 27231). It
can post only in rooms whose own key it holds, which are the rooms
its user made: posting in someone else's room needs what they call a
"remote room" type, which "the crate does not have yet". And it makes
new keys each time it
starts, so its user is someone new each time: "wrong for production,
correct for a demo".

One thing DeepSeek says in the third delivery that is not so (line
27247): that the `src/home.rs` they were given fails two tests for want
of an earlier repair. That file was not in the file they were given,
which names it as carrying the repair. The `src/home.rs` DeepSeek
then sends is the crate's own, with the repair, but for line breaks
and the one new function. Nothing is lost by it.

Read by the technical lead: all of DeepSeek's prose in the new part;
`verify_branch` whole; and each of the eighth delivery's three files
against the file before it. The rest of the code was built and run,
not read line by line.

### Gemini's list of doors (2026-11-17)

Gemini answered their third file the same day
([gemini/2026-11-17-2](gemini/2026-11-17-2/README.md)): two files,
`src/doors.rs` and `tests/doors.rs`. Laid over the crate with the one
line that names the module (change 26), every test file run:

| Delivery | What it is | Gemini expected | Tests, built as given |
|---|---|---|---|
| The list of doors | `draw`, `check`, `ranked` and `as_text`, with fifteen tests. A door shows a room, its law, and how many are in it unless the room's law hides that | 127 | 127 of 127 |

Nothing was repaired. It is the crate as it stands now:
`deepseek/012-09-05/chat-world-now/`, 127 tests, 61 of them
DeepSeek's and 66 Gemini's, in 31 files. Gemini's seventeen attacks
on a room's other records, run beside it, give the same eight that
get through (136 of 144).

The technical lead had written the same step out, outside the
repository. Each build passes the other's fifteen tests.

One thing seen on reading it, which the next file puts to Gemini as
an attack: a count is a count of keys, and keys cost nothing to make.
Whoever keeps a room, or anyone who can join an open one, can fill
it with keys of their own making and put it first among the most
populated.

Gemini's next file
([replies/2026-11-17-3-for-gemini.txt](replies/2026-11-17-3-for-gemini.txt))
asks one step: twenty-two attacks on the list, tests only.

### Gemini's attacks on the list of doors (2026-11-17)

Gemini answered their fourth file the same day
([gemini/2026-11-17-3](gemini/2026-11-17-3/README.md)): one file,
`tests/doors_attack.rs`, 25 tests, the twenty-two the file asked for
and three of their own. Built beside the crate as it stands, every test
file run:

| Delivery | What it is | Gemini expected | Tests, built as given |
|---|---|---|---|
| Attacks on the list of doors | A list forged against `check`, the logs forged against `draw`, a list read from JSON, the text, and what a count means | 147 of 152, five named to fail | 147 of 152, the same five |

The five that get through:

| Attack | What the crate accepts | What is done |
|---|---|---|
| 17 | A room's log cut short just before a leaving: the older, larger count is drawn | A log is held to a head the room signed, when the reader holds one |
| 19 | A door read from JSON with a member the form does not have, such as a list of ids | The forms refuse what they do not have |
| 22 | Thirty keys of one holder put a room above one of five people | Not closed in the crate: a count is a count of keys. Kept as a test that states the limit. The answer is other numbers and a look into the room (STATUS.md, "Decided", 2026-11-17) |
| 24 | A leaving by a key that was never in the room, signed by that key alone | It belongs to the check of a room's own log: a ninth gap, beside the eight of Gemini's fourth step. Until then the drawing of the list refuses such a log |
| 25 | A room registered under a topic that is not its own: only the registrant's is shown | The room's own topic is shown beside the listed one, when the reader holds the room's log |

Because five of its tests fail, the file is not laid into the crate
as it stands, which stays at 127 tests. `review/steps.sh` builds it
beside the crate (`doors-attacks`).

"What is done" is what Gemini's next file asks of them
([replies/2026-11-17-4-for-gemini.txt](replies/2026-11-17-4-for-gemini.txt)):
five repairs, in their own two files. Before that file was written the
repairs were made in a throwaway copy outside the repository, with
attacks 17, 22 and 25 rewritten as the file asks and four trial tests
added: 156 of 156. The copy is not kept.

## Record 012-03-02, component by component

Three series of components, written out in `deepseek/012-03-02/`: a
model of Aristotle's practical reasoning as a control system, one
component of a music engine, and the poetry engine (components 1 to 22,
with its curriculum in the prose). Step 1 brought parts of the poetry
engine's components 21 and 22 (the turn, the critical stances, the
apprentice poet) into open-worlds as `multiverse/apprentice.py`, changed
([docs/MULTIVERSE.md](../docs/MULTIVERSE.md) says how). Records 012-04-00
and 012-05-01 import components 21 and 22 from this folder. "Line" is
where the component's code begins. Tests are run on Python 3.12 with fix
5 (below).

| Component | What it is | Line | Tests as written |
|---|---|---|---|
| `aristotle_cybernetics_c2` to `c7` | The virtuous agent as a control system: the telos hierarchy, a telos that learns, mutual and asymmetric correction | 996 to 3181 | no tests |
| `music_engine_c8` | The Listener | 3698 | doesn't load: needs `music_engine_c1`, which no record here has |
| `poetry_engine_c1` | Phonemes, syllables, stress | 4523 | doesn't load: `poetry_engine_c1.py` has a syntax error (line 45) |
| `poetry_engine_c2` | The cognitive frame | 5393 | doesn't load: imports `poetry_engine_c1`, which has a syntax error |
| `poetry_engine_c3` | Meter and scansion, through both grammars | 6195 | 13 of 15 (one of the two imports `poetry_engine_c1`) |
| `poetry_engine_c4` | The score-performance gap | 7287 | doesn't load: imports `poetry_engine_c1`, which has a syntax error |
| `poetry_engine_c5` | The native voice | 8351 | 11 of 11 |
| `poetry_engine_c6` | Architecture: cycle, refrain, the foregrounding monitor | 9282 | 12 of 14 |
| `poetry_engine_c7` | The composition engine | 10185 | 18 of 18 |
| `poetry_engine_c8` | Rest as meta-work | 11311 | 13 of 14 |
| `poetry_engine_c9` | Cross-cycle coherence: the collection | 12212 | 13 of 15 |
| `poetry_engine_c10` | Revision through feedback | 13174 | 12 of 13 |
| `poetry_engine_c13` | The development spiral | 14161 | 14 of 15 |
| `poetry_engine_c14` | The living collection | 15002 | 19 of 19 |
| `poetry_engine_c17` | The complete agent | 15894 | 14 of 15 |
| `poetry_engine_c18` | The reflective rewriting cycle, given in three parts | 17038 | no tests; its parts joined (fix 5) |
| `poetry_engine_c19` | The long run | 17680 | 0 of 4 (its test is a block from the prose) |
| `poetry_engine_c20` | The full agent | 18263 | 2 of 12 |
| `poetry_engine_c21` | The collaboration protocol: turns, stances, the polyphony | 21859 | no tests; its two parts joined (fix 5) |
| `poetry_engine_c22` | The runnable apprentice | 22431 | no tests; its two parts joined (fix 5) |

In all: 141 of DeepSeek's tests pass and 24 fail. 4 test files don't
load. Components 11, 12, 15 and 16 are named in the record only as
proposals, with no code.

45 of the record's 56 code blocks are written out. The other 11 are
examples in the prose and stay in the record: a run of component 17
(16820); a worked example for component 18 (17333, 17403, 17422, 17440);
the curriculum's apprentice (19436); four turns of a worked example for
component 21 (22163 to 22270); and a worked example for component 22
(22974).


> The next part: https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/parts/sketches/INDEX.md/changes-to-deepseek-s-code.md

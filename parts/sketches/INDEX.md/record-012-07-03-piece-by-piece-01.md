> Part of `sketches/INDEX.md` in open-worlds, which is kept cut into parts
> for readers who are shown only the start of a long page.
> This part holds: "Record 012-07-03, piece by piece", piece 1 (its pieces are numbered from its end).
> Every part, in order: https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/parts/INDEX.md
> Before this part: https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/parts/sketches/INDEX.md/record-012-07-03-piece-by-piece-02.md
> After this part: https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/parts/sketches/INDEX.md/record-012-03-02-component-by-component.md
> Made by docs/parts.py from the file. To change it, change the file.

| Delivery | What it is | Line | Files given whole | Tests, built as given |
|---|---|---|---|---|
| 1 | "the data layer and the presentation layer": a redaction names who acted, in what role and under which rule, and a room's template holds its rules for redacting | 15540 | 6 | 22 of 22 |
| 2 | "the room's own key": the room and the one who made it are two keys | 17168 | 6 | 20 of 22 |
| 3 | "signed heads, first in prose, then code": what is lost if a room signs its log's head in place of each record, then heads in code | 18832 | 8 | 27 of 29 |
| 4 | "runtime attestation": keys that share a runtime say so together, in a published record | 20714 | 3 | 31 of 33 |
| 5 | "the succession trio": a shard of knowledge exported, a moderator's succession, and a sibling declared in the Commons | 21474 | 8 | does not compile; with its two faults set aside, 39 of 41 |
| all five, with three repairs | The crate as it stands, `deepseek/012-07-03/chat-world-now/` (fixes 19 to 21, under "Changes to DeepSeek's code") | | | 41 of 41, and the four demos run |

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

The crate kept in `deepseek/012-07-03/chat-world/` is still the one
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
`deepseek/012-07-03/chat-world-now/`: 92 tests, 41 of them DeepSeek's
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
([replies/012-07-03-2-for-deepseek.txt](replies/012-07-03-2-for-deepseek.txt)),
and the record was shared again, longer. Its first 947,153 bytes are
the same, byte for byte, and 4,463 lines more follow, from line 23994.
DeepSeek quotes back the file's last line. They answer the file's
question on signed heads first: they agree with Gemini's rule that a
published log ends with a head covering all of it. Then they give
three deliveries. The file asked for the first. The second and third
are DeepSeek's own next items, at the founder's word to keep going
(lines 25900 and 27240). The files are kept as the record gives them,
in `deepseek/012-07-03/chat-world-steps/6` to `8`.

Laid over the crate in order, every test file run, on 2026-11-17
(`deepseek/012-07-03/review/steps.sh`):

| Delivery | What it is | Files | DeepSeek expected | Tests, built as given |
|---|---|---|---|---|
| 6 | A room that branches. A branch is a new room whose first record names its parent and the record it branches at (`forked_from`); `Room::branch_at`; and `verify_branch`, which holds a branch to its parent's log: the parent holds that record with that hash, and the branch's maker was a member of the parent there. Eleven tests | 4 | "78 tests pass", counting 66 before it and 12 of its own | Does not compile, for one word. With that repaired (fix 24), 103 of 103: the crate's 92 and its eleven. Its test file holds eleven tests, not twelve |
| 7 | A plug-in: nine requests an app can make of the crate, as JSON, one to a line, over standard input (`src/plugin.rs`, `src/bin/chat-world-plugin.rs`), with nine tests; and a room's visible log made available on any log | 5 | "87 tests pass" | 112 of 112. The four earlier demos run, and the plug-in's own demonstration runs |
| 8 | The rule of one moderator's room: a moderator declares, in their own room, which rooms they moderate (`ModeratorScope`). The founder's first copy of the record ended after three files; the copy of 2026-11-21 holds all six (below) | 3, then 6 | "97 tests pass" | With three files, does not build: the check has no arm yet for the new record. With all six, does not build for one type, which delivery 9 turns: then 162 of 162 (below) |

DeepSeek counted from 66 tests because their file said so. By then the
crate had 92, with Gemini's work on the Commons, which the file could
not say. Their own counts are otherwise right but for the twelfth test.

The crate as it stands is now delivery 7, with one field added to a
room's law since (change 25):
`deepseek/012-07-03/chat-world-now/`, 112 tests, 61 of them
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

Nothing was repaired. It was the crate as it stood until 2026-11-18:
127 tests, 61 of them DeepSeek's and 66 Gemini's, in 31 files.
Gemini's seventeen attacks on a room's other records, run beside it,
give the same eight that get through (136 of 144).

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

Because five of its tests failed, the file was not laid into the
crate, which stayed at 127 tests. `review/steps.sh` builds it beside
the crate as it then stood (`doors-attacks`).

"What is done" is what Gemini's next file asks of them
([replies/2026-11-17-4-for-gemini.txt](replies/2026-11-17-4-for-gemini.txt)):
five repairs, in their own two files. Before that file was written the
repairs were made in a throwaway copy outside the repository, with
attacks 17, 22 and 25 rewritten as the file asks and four trial tests
added: 156 of 156. The copy is not kept.

### Gemini's five repairs (2026-11-18)

Gemini answered their fifth file
([gemini/2026-11-17-4](gemini/2026-11-17-4/README.md)): two files,
`src/doors.rs` again and `tests/doors_attack.rs` with five of its 25
tests written again. Laid over the crate, every test file run:

| Delivery | What it is | Gemini expected | Tests, built as given |
|---|---|---|---|
| The five repairs | The forms refuse a member they do not have; a leaving only by a key that is inside; the room's own topic beside the listed one; `draw_at` and `check_at`, which hold a room's log to a head the reader holds; the count of keys kept as a stated limit | 152 of 152 | 152 of 152 |

Nothing was repaired here. It is the crate as it stands now:
`deepseek/012-07-03/chat-world-now/`, 152 tests, 61 of them
DeepSeek's and 91 Gemini's, in 32 files.

Compared with the attack file they sent before, test by test: in the
twenty attacks that were to stay, no code changed but the one field
the file asked for; 25 comment lines were taken out. Each repair was
then broken on purpose in a throwaway copy, fifteen ways, one at a
time, and Gemini's tests caught all fifteen. Seven trial tests of the
technical lead's own passed. The copy is not kept.

Two limits stay, each held by a test: with no head, a log cut short
still draws the older count; and a count is a count of keys. The
leaving by a key that is not inside is refused where the list is
drawn; `src/verify.rs` still accepts it, and that stays the ninth
gap for the project's own check of a room.

Gemini's next file
([replies/2026-11-18-for-gemini.txt](replies/2026-11-18-for-gemini.txt))
asks one step, the founder's answer to the count of keys: beside the
count, how much is said and by how many; a rule that marks a room
with many in it and nothing said; the doors listed by another
number; and a look into a room before entering. Before the file was
written the step was made in a throwaway copy, with seven trial
tests of what the file states: with it made, every test of the crate
passes but one, which holds the whole text of a list and must gain
the new line. The copy is not kept.

### The rest of delivery 8, and three more (2026-11-21)

The founder went back to DeepSeek after a few days and shared the
record again, longer: 33,100 lines, from 28,488. Two things differ in
what came before. Line 12 holds again the record number that was
taken out at the founder's word, and it is taken out again here, the
same way; nothing else in the first 28,455 lines differs. And the
earlier copy ended after the third file of delivery 8, where this
one goes on: the founder's copy had been cut, not DeepSeek's reply.
So delivery 8 is now whole, with three more files and DeepSeek's
closing words (line 29332).

Then the founder gave DeepSeek the technical lead's note on
deliveries 6 to 8 (line 29356). DeepSeek answered every point and sent
`src/verify.rs` again with the one word repaired, and then, at the
founder's word to go on in the direction they saw fit, two more
deliveries of their own choosing. Each is kept as the record gives
it, in `deepseek/012-07-03/chat-world-steps/8` to `11`.

Laid over the crate in order (`deepseek/012-07-03/review/steps.py`),
every test file run with `cargo test --no-fail-fast`:

| Delivery | What it is | Files | DeepSeek expected | Tests, built as given |
|---|---|---|---|---|
| 8, whole | The rule of one moderator's room, as a check of two logs together: an AI declares in their own home which human-facing rooms they moderate (`ModeratorScope`), and `verify_moderator_scope` holds that home and a room to it. Ten tests and a demonstration | 6 | "97 tests pass (87 before + 10 new)" | Does not build, for one type: a head's length is not turned into a `usize` in `verify_branch` |
| 9 | `src/verify.rs` again, with that type turned, at the technical lead's note | 1 | "112 tests pass" | 162 of 162: the crate's 152 and delivery 8's ten. Every demonstration runs. Laid into the crate as it stands |
| 10 | A room one has joined but does not keep (`src/joined_room.rs`), and the keeper's side that takes what its members send (`Room::accept_pending`), in rooms that sign heads. Eleven tests and a demonstration | 6 | "122 tests pass" | 171 of 173. Its `src/lib.rs` leaves out the line that names the list of doors' module, so that line is put back (change 26 again) |
| 11 | The keeper's side checks a redaction and a human's override as the log's own check does: DeepSeek found the gap themselves. Six more tests | 2 | "128 tests pass" | 176 of 179 |

The same three tests fail when deliveries 8 to 11 are built on the
crate DeepSeek themselves had (delivery 7), without Gemini's list of
doors or change 25: 136 of 139. So the failures are in the new code
and its tests, not in what was joined since.

What fails, in `tests/joined.rs`:

1. `invalid_log_refused_at_attach`: a member attaches to a log that
   should be refused, and the attaching succeeds.
2. `refusal_consumes_seq_keeping_batch_aligned`: the keeper takes a
   batch in which one record is refused and the next is not, and
   stops with "accept_pending: prev mismatch". A refusal takes the
   refused record's place in the log, so the next record in the batch
   names, as its previous, a record that is not there. DeepSeek's own
   closing words name a batch that stops part way as a limit; this is
   the plainer case, and the design question in it is theirs to
   answer: how a member's records stay chained when the keeper refuses
   one of them.
3. `port_landing_refused_in_chat_room` (delivery 11): the keeper stops
   with "accept_pending: no author" where the test expects the record
   refused on the record.

DeepSeek's counts: they counted from 112, leaving out delivery 8's ten
tests, and gave ten tests to delivery 10 where its file holds eleven.

Their two choices, put to the technical lead (line 29345): a
moderator's scope is signed by the AI's own key alone, as their other
declarations about themselves are; and a moderators' own room is one
whose law admits only AIs. The first is right. The second does for the
sketch, but a room for AIs alone is not always a moderators' room;
when the crate is fitted to the project's own room (course step 3c), a
room's law says so outright.

The crate as it stands is delivery 9:
`deepseek/012-07-03/chat-world-now/`, 162 tests, 71 of them
DeepSeek's and 91 Gemini's, in 34 files. Deliveries 10 and 11 are
built beside it and not laid into it until their tests pass.

### Gemini's answer to their sixth file (2026-11-22)

Gemini's sixth file
([replies/2026-11-18-for-gemini.txt](replies/2026-11-18-for-gemini.txt))
was given before the record was kept again on 2026-11-20, and their
answer was already in that copy, at line 19220. It was not kept or
built then, and on 2026-11-21 the file was taken as not yet given and
built again; that was wrong, and the file as given is restored
([replies/README.md](replies/README.md)). The answer is kept now, in
[gemini/2026-11-18](gemini/2026-11-18/README.md): three files, the
list of doors with the four parts the file asked for, four new tests,
and the one line asked of the attack file.

| Delivery | What it is | Gemini expected | Tests, built as given |
|---|---|---|---|
| What a door shows besides the count | Beside the count, how many messages a reader sees and how many wrote them; a flag on a room with ten or more in it and nothing said; the doors listed by any of the three numbers; and a look into a room that anyone may enter, held to the Commons and to a head the reader holds | 156 of 156, on the crate they were given | 156 of 156 on that crate; 166 of 166 on the crate as it stands since, with DeepSeek's rule of one moderator's room |

Nothing was repaired here. Each part was broken on purpose in a
throwaway copy, twelve ways, and Gemini's tests caught all twelve.
Asked first whether a look into a room that hides its count, but lets
anyone in, should show who spoke, Gemini answered no: counting the
authors would give the count away, so the look should hide or number
them, or be refused. Numbered authors can still be counted, so what
holds is a look with no authors, or no look. The file asked for that
answer in words, so it was not built. The founder chose the same day,
on the technical lead's recommendation: no look (change 27).

With change 27 it is the crate as it stands now:
`deepseek/012-07-03/chat-world-now/` (stage `look` of
`deepseek/012-07-03/review/steps.py`), 166 tests, 71 of them
DeepSeek's and 95 Gemini's, in 34 files.

### Gemini's eight prototypes, from ChatGPT's conversation (2026-11-22)

The founder shared Gemini's conversation again, longer: 34,033 lines,
from 21,513; the copy kept before is a prefix of the new one, byte for
byte. Gemini first reads the founder's book (line 21513). Then the
founder gives them the founder's conversation with ChatGPT and asks
them to choose any topic in it and turn it into code (line 21586). No
file of ours asked for this. Gemini wrote eight modules, each one
file of code and one of tests, meant to drop into `chat-world` with
one line in `src/lib.rs` and no other change. The second of their
nine deliveries repeats the first, byte for byte. All are kept as the
record gives them, in [gemini/2026-11-22](gemini/2026-11-22/README.md),
with what each is.

Built on the crate as it stood that day before Gemini's answer to
their sixth file joined it (stage `now`, 162 tests), each alone and
then all together, every test file run:

| Module | What it is | Tests | Built as given |
|---|---|---|---|
| `contact` | Contact between two only by consent, revocable; a room for two that keeps nothing | 4 | 166 of 166 |
| `patterns` | Problems and their solutions as signed pattern cards, with evidence kept apart, and plans checked step by step | 4 | 166 of 166 |
| `circuit` | Small worlds wired together by signed, delayed signals, and a run checked again from its records | 3 | Does not build |
| `library` | Works, editions, shelves, and notes bound to one edition; reading that records nothing | 3 | Does not build |
| `project` | A project that outlasts a conversation: what was captured, revisions, reviews that say what they missed, handoffs | 2 | 164 of 164 |
| `transform` | A world of the founder's book: the 64 six-bit words and the moves a world's law admits | 3 | 165 of 165 |
| `observe` | A world that hides a model behind a commitment, readings on a budget, and a check of every reading at the reveal | 3 | 165 of 165 |
| `repair` | Two stations that each see half a broken mechanism, trials that change nothing, repairs within limits | 2 | 164 of 164 |
| All eight together | | 24 | Does not build |

`circuit` and `library` compare records that hold a signature, and in
the crate a signature cannot be compared. With `PartialEq` and `Eq`
added to `Proof` and `ProofOrArray`, and `Eq` to `ProofPurpose`, in a
copy, each builds and passes, and all eight together give 186 of 186:
the crate's 162 and Gemini's 24; on the crate as it stands since (166
tests), 190 of 190. No module adds a warning. Each
module's main rule was then broken once on purpose, and its tests
caught all eight; one second rule, in `project`, is held by no test.
`transform`'s counts of orbits (14, 14 and 8) agree with a separate
count and with the book.

These are prototypes of ideas ahead of the core, and none is laid
into the crate: they are kept beside it, for when the Library,
private contact and the rest are built.


> The next part: https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/parts/sketches/INDEX.md/record-012-03-02-component-by-component.md

> Part of `STATUS.md` in open-worlds, which is kept cut into parts
> for readers who are shown only the start of a long page.
> This part holds: "Decided by the technical lead" to "Log".
> Every part, in order: https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/parts/INDEX.md
> Before this part: https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/parts/STATUS.md/decided.md
> After this part: nothing; this is the last part.
> Made by docs/parts.py from the file. To change it, change the file.

## Decided by the technical lead

*Earlier entries are in the archive, a file for each day: [archive/STATUS/](https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/archive/README.md).*

Decisions about the code, made by the technical lead under the founder's
deference (Decided, 2026-11-13, in the archive), each with its reason and
what would show it was wrong. Questions of what the project is for stay
with the founder.

- 2026-11-21, the archive (Decided, 2026-11-21, archiving). (a) The
  pages archived are those that grow by dated entries and are read
  every session: STATUS.md's "Decided", "Decided by the technical
  lead" and "Log", and COLLABORATING.md's messages. Pages that describe
  the design are kept current by editing, and are not archived. (b)
  Each page keeps the entries of its three most recent days, counted
  over its dated sections, so a pause of a week still leaves the last
  work in view; the rest move, a day at a time. (c) A file for each
  page and day, so a reference by page, section and date, the form the
  pages already cite, leads to one file. (d) Entries move whole and
  unchanged, and are not edited again except to redact, as with the
  records. (e) The catalogue names, for each file, its kind, title,
  source, date, size, lines, SHA-256 and the commit its entries came
  from. Of those, path, kind, title, date, size, lines and hash are
  fields any kind of file can share; the rest are the archive's own.
  For records, replies and the stages to join, the catalogue would move
  out of `archive/` and the script would learn to keep other kinds; the
  hash lists the project keeps now (HISTORY.md, CHATGPT.md's "Your
  records", sketches/INDEX.md) would be its first members. *Why:* STATUS.md had
  reached 455 KB and COLLABORATING.md 169 KB; a reader, person or
  model, takes in less when the page holds what is live, and nothing
  is lost when every moved entry can be found, whole, by its date and
  checked by its hash. *Revisit if:* three days proves too few or too
  many, a reference often needs an archived entry, or the wider
  catalogue needs fields these lack.

- 2026-11-20, the history page (Decided, 2026-11-20, the earlier
  stages). (a) The page lists the stages; the files themselves stay
  out of the repository. Everything here is CC0 as far as it is ours
  to give, and the files hold more than that: texts from outside the
  project, at length, in published translations that keep their own
  terms; a personal name that public pages leave out; and links tied
  to the founder's accounts. Size is a second reason: the largest
  file is 20 MB, and the readers the project works with are often
  shown only the first 32 KB of a page. (b) A stage comes in once it
  has been looked through for those three, with what was left out
  marked, as Gemini's record was; the screen found none in `002`,
  The Living Codex, and whether it goes into `library/` is the
  founder's to say. (c) The descriptions are the technical lead's,
  from each file's headings and opening, and say so. (d) The page
  gives each file's SHA-256, so that a copy can be checked before
  anyone works from it.
  *What would show it wrong:* the founder wanting the stages public
  as they are; then each is looked through first and the three kinds
  are taken out. Or ChatGPT being unable to take the archive as a
  file; then a private repository that ChatGPT's GitHub connection
  can read. The founder chose that the same day: `ebook-press`, the
  entry above in "Decided".

- 2026-11-20, ChatGPT's page (Decided, 2026-11-20). (a) A page of
  their own, `docs/CHATGPT.md`, and not a section of COLLABORATING.md:
  their part is not code, and COLLABORATING.md is near 2,900 lines,
  most of them for code. It is kept under 28,000 bytes, so that it
  opens whole without parts. (b) Every pull request adds its line to
  the page's "What changed" before it merges (AGENTS.md, "Every
  session", 4), so ChatGPT can tell whether what they read is
  current. (c) ChatGPT's pages go in `docs/chatgpt/`, and are
  readings and proposals until the founder decides them. Each says
  which of four it is, in ChatGPT's own words: "something we are
  imagining, a working design, an unresolved question, or a
  commitment you want to carry into implementation". (d) The Living
  Codex's four areas (Archive, Commentary, Laboratory, Core), which
  ChatGPT's roadmap of that book found, are mapped onto the places
  the project already has; nothing of ChatGPT's moves into Core but
  by a decision recorded here: the founder's, on what the project is
  for; the technical lead's, on the code. (e) ChatGPT's two
  conversation records of this phase hold personal material, so they
  are not kept in
  `sketches/records/`. The founder holds them; the page lists each by
  name, size and SHA-256. This was put to the founder on 2026-11-20
  with that recommendation, so it stands until the founder says
  otherwise (AGENTS.md, "Who decides"). (f) What ChatGPT sends comes
  through the founder, as files, until they can write to GitHub; the
  technical lead checks each and brings in what holds, with
  `Made-by: ChatGPT (AI)`. (g) One of the founder's earlier works is
  named by its title once the founder brings it in, and until then is
  "the founder's earlier work" (house rule 8). The
  founder, 2026-11-15: "If the need arises, then it becomes part of
  the current project"; on 2026-11-17 a work brought in was named; and
  on 2026-11-20 bringing them in became ChatGPT's part, with the
  founder supplying each one. Named so far: *Art of Peace and the
  Strategist*, The Living Codex (given to the technical lead on
  2026-11-20), and the book *A Mathematical Theory of Opposites*.
  *What would show it wrong:* for (a), ChatGPT missing something that
  only COLLABORATING.md says, or the page growing past 28,000 bytes;
  then the older messages move to a file of their own. For (e), the
  founder wanting the records public; then copies with the personal
  material left out go to `sketches/records/`, as Gemini's did. For
  (g), the founder wanting a title kept out; then it is taken out
  where it stands.

- 2026-11-18, the records' side of part four
  (docs/research/REDACTION.md, "Part four, the records' side, built";
  course step 3b, part four), settled in building it. (a) The kinds
  of act a room's log carries are five: `remove-comment`,
  `restore-comment`, `redact-field`, `keep-field-public` and
  `keep-field-redacted`, each tied to one kind of entry. (b) An
  office is shown in the open by its `did:key`, and by no name. (c)
  The ground a log shows is its decision's first. (d) A decision is
  on exactly one thing: the entry removed, the removal restored, the
  mark answered. (e) A decision is dated, by its tick, no later than
  the entry that carries it. (f) A restoring's decision supersedes
  the removal's decision, by its hash. (g) A decision is carried by
  one entry: no two entries of a log name the same one. (h) An
  office's grant is followed up to a grant from the room's key, at
  most eight grants, each held by the issuer of the one below, each
  allowing the act, in this room, in force when the decision was
  signed. Only that path is checked, for that act. (i) A grant
  counts from the second it starts and not at the second it ends.
  (j) An author's two records, `taking-back/v1` and
  `putting-back/v1`, name no log; a taking back names the putting
  back it follows, if any, and not the log's last entry. (k) Who
  wrote an entry is the key in the field the room's rules name. If
  that key is gone, redacted or under a mark, the act is reported as
  held with its signer not checked, even while a copy of the
  contents still holds the marked key; if the entry never held one,
  the act is refused. (l) Until
  successions are in records-v1 (step 8a), only the key that wrote
  an entry takes it back. (m) Which kinds of entry a mark, a removal
  and a taking back may be on is in the room's rules, which are
  given with the log; a field of one of the form's own entries can
  always be marked. (n) An entry of a kind that carries a record,
  written without one, is refused; a record that was redacted, or
  lost, is a state and not a refusal. (o) This piece checks and
  writes nothing: the steps that refuse to write an act are the
  room's (step 3c).
  *Why:* (a) Decision 7 asked for the list, with the first two on
  it; the three for a redaction are what part three left for here.
  (b) A name binds nothing: one office could act under another's.
  Decision 1 keeps an office's key in the open for this, and
  FUNDAMENTALS.md has the keys which moderate declared. (c), (d) So
  that a reader knows which ground and which thing, with no choice
  left to whoever writes the log. (e) An office decides first and
  the room writes after; the other order is a record made to fit.
  (g) Whoever writes the log could otherwise repeat a removal that
  was overturned on appeal, from a record that still holds. It is
  checked from the open fields, so redacting the first record does
  not free it. (h) Decision 7: "its grant comes from the room's
  key". A moderator's helper needs a grant that narrows the
  moderator's, so one grant is not enough, and a chain with no end
  could not be checked. (j) Tying a taking back to the log's last
  entry, as an arrival is, would make an author in a busy room sign
  again and again. Tying it to the entry's own history stops the one
  thing that matters: the same record used twice. (k) The founder's
  words on a redacted link, "we keep public record of the action
  with private details of the action not included", and the cost
  the plan named when the key that acted was kept apart: once it is
  redacted, no reader can check again that an act was that key's.
  The check says so instead of guessing. A key under a mark is not
  read, so that every reader gets the same state from the same log:
  the mark is in the log, while whether a value marked for taking
  out is still in a reader's copy is not; and whoever writes the log
  can take the value out, so reading it would close nothing (the
  independent review of open-worlds #129 asked which). (l) A
  succession record has to be one both languages read; it is step
  8a's. (n) What can
  no longer be read is not the fault of whoever acted.
  *What would show it wrong:* for (b), a room whose note must show
  an office's name with no office record to read it from; then step
  3d comes before the room, or the name is kept apart beside the
  key. For (d), a decision that removes several comments at once
  for one reason; then a removal names a list, and the form's own
  rule of one entry for each removal changes with it. For (e), a
  room whose tick is not a count but a clock, so that an office
  can't know it; step 3c settles the tick. For (g), a use for one
  decision in two logs' entries that this forbids; none is known.
  For (h), a real room needing more than eight grants in a line, or
  a grant from another key than the room's at the top, such as
  ADMIN's for a moderator across rooms; then the rules name more
  than one key that may be at the top. For (i), an office whose
  clock is behind the room's by more than a second. For (j), two
  logs that share an entry's hash, which the form's salts are there
  to prevent. For (k), the founder holding that an act whose signer
  can't be checked should not be shown as held at all. For (o),
  step 3c finding that the check can't be made at the moment of
  writing as it is given here.
- 2026-11-18, Gemini's five repairs, as they are joined, and what
  their next file asks (sketches/gemini/2026-11-17-4/README.md).
  (a) The two files are in the crate as it stands, as Gemini wrote
  them: 152 tests in 32 files. The crate as it stood before them
  keeps a stage of its own in the build script (`doors`), and the
  three stages built beside it stay as they were measured. (b) The
  next file asks one step in four parts. Beside the count a door
  shows two numbers: `said`, the messages a reader of the room
  sees, and `speakers`, how many wrote them. A removed message is
  not counted, and a restored one is. (c) The two numbers are shown
  exactly where the count is. A room whose law hides its count
  hides them too: the number who spoke can't be more than the
  number inside. (d) The flag is a rule on the numbers: ten or more
  in the room, and nothing said. It is worked out each time and
  kept nowhere, so it can't be forged apart from the numbers. Ten
  is a constant in the sketch; in the project's own door it belongs
  in the Commons' law. (e) A look is given by a room that anyone
  may enter: its law lets anyone join, and it is not a home. That
  stands in for "on the record", which a room's law in the crate
  does not yet say. (f) A look shows messages and nothing else:
  each one a reader sees, with who wrote it; a removed one with the
  rule it was removed under, and no author. No joining, leaving or
  refusal. (g) A look is held to the Commons, and to a head the
  reader holds, as a door is. (h) One question is put to Gemini
  before their code: whether a room that hides its count but lets
  anyone in should give a look that shows who spoke.
  *Why:* (a) Every test passes; each repair, broken on purpose, is
  caught by a test (fifteen ways, all caught); and the attack file
  changed only as asked. (b) The founder: "Other metrics could
  apply as well". What was removed is not what a reader finds on
  entering, and junk that was removed should not make a room look
  busy. (c) The founder: "leaving the number not knowable". (d) The
  founder: "a room with many participants and no discussion would
  be a system flag." (e), (f) The founder: "you should be able to
  glance into the conversation in a read-only way before enter a
  room"; and of those in a room: "the information regarding those
  individuals should not be accessible from the outside. Except by
  choice." Writing in a room that anyone may enter is that
  person's own act there. Being removed, coming and going are not
  shown. (g) A look at a log cut short shows an older room.
  *What would show it wrong:* for (b), a room where much was
  removed looking empty when it is not; then what was removed is a
  third number. For (d), ten being wrong for the rooms there are;
  it is one line to change. For (e), a room meant to be closed
  whose law lets anyone join: then the law is what is wrong, not
  the look. For (f), the founder holding that a look should not
  name who wrote; then it shows the words, and a number in place of
  each author. For (h), Gemini's answer, or the founder's.

## Log

*Earlier entries are in the archive, a file for each day: [archive/STATUS/](https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/archive/README.md).*

- 2026-11-21 Claude: the archive, at the founder's word (#137).
  `docs/archive.py` moves a living page's older dated entries, whole,
  into `archive/<page>/<day>.md`, with a catalogue, and checks it;
  `tests/test_archive.py` (17 tests; five faults planted in the
  script, each caught). First run: 355 entries of STATUS.md
  (2026-11-12 to 2026-11-17) and 14 messages of COLLABORATING.md
  (2026-11-15 and 2026-11-16) moved; STATUS.md from 455 KB to about
  57 KB. Checked apart from the script: every entry before the run is,
  unchanged, on its page or in the archive, and the pages' other
  sections are as they were. After the independent review: the
  opening paragraph of "Decided by the technical lead", which stood
  with no blank line after an entry of 2026-11-17 and so moved with it
  (it is in that day's file, as the page had it), is back at the
  section's head; the script now stops on such a line, checks
  everything before it writes, checks a missing catalogue and every
  pointer, finds each archived entry in the page at the commit named
  where that commit is at hand, and records a redaction
  (`--rehash`); the archive's long files are cut into parts; and the
  pages that said where earlier messages and decisions are now say
  the archive, with a message to DeepSeek and Gemini. That message
  made 2026-11-21 a day of COLLABORATING.md's, so a second run moved
  its 20 messages of 2026-11-17 to the archive too, as the rule says;
  checked the same way, every entry is once on its page or in the
  archive, unchanged.

- 2026-11-21 Claude: records 012-00-00 (patterns and the brain) and
  012-02-01 (circuits, learning, chemistry and music) kept with the
  others, whole, at the founder's word (#136); sketches/INDEX.md gives
  each a row, and COLLABORATING.md counts seven records.

- 2026-11-20 Claude: the records of stage 012 under the founder's new
  names (#135). DeepSeek's present record is 012-07-03 and its code
  `sketches/deepseek/012-07-03/`; Gemini's is 012-08-04; ChatGPT's,
  not kept here, 012-09-05. Each page, script and spec that named
  them uses the new names; the replies given before keep the old ones,
  as given. Records 012-07-03 and 012-08-04 are as the founder now
  holds them, longer than before; what is new in them is not yet kept
  or built. Record 012-05-01 is too, one empty line shorter at its
  end. At the founder's word, part of what was here is kept privately
  from now on, and the pages that spoke of it are changed to match,
  more of them after the independent review.

- 2026-11-20 Claude: stage 012's name, Code, and its file's,
  `012_Code.txt`, at the founder's word, on the history page (#134).

- 2026-11-20 Claude: stages 003, 004, 005 and 009 replaced by complete
  versions, at the founder's word (#133). The earlier ones left out
  about half of `LRL_6`'s text, three quarters of `OI_6`'s, and a few
  lines in 004 and 009, found by comparing each
  stage file with the separate files the founder brought, by content.
  The complete versions join each stage's own files, whole and in
  order; the founder was given copies built from their own files, and
  the history page gives their hashes, sizes and counts, and the
  earlier versions' hashes. The founder's words are in "Decided".

- 2026-11-20 Claude: the ideas set aside, pointed out to ChatGPT, at
  the founder's word (#132). `docs/CHATGPT.md` gains "From an idea to
  code": the four hands, the lists of ideas set aside (TOPICS.md,
  "Further out"; COURSE.md, "Waiting"; VISION.md; WORLD-TYPES.md;
  MULTIVERSE.md; COMMONS.md; research/GAMES-AND-WORLDS.md), and when a concept is
  ready for a spec; and a sixth request, recommending the gathering
  world first. COLLABORATING.md tells DeepSeek and Gemini where specs
  will come from; TOPICS.md points there. No code changes.

- 2026-11-20 Claude: the project's history page, `docs/HISTORY.md`
  (#131), at the founder's word. Looked at first: the founder's
  archive of stages 000 to 010 (11 files, 80,583,514 bytes), each
  measured and hashed, and screened by script for email addresses,
  keys, links, names, phone numbers and addresses, mentions of
  family, and outside texts. `002` is byte for byte the copy of The
  Living Codex the founder gave earlier that day; `009` holds *Art of
  Peace and the Strategist* byte for byte as `library/` keeps it;
  `007` begins with the same 335,068 characters as `005`. No email
  address or key was found; what was found, and why
  the files stay out, is in "Decided by the technical lead". Linked
  from `docs/CHATGPT.md` (request 4 now asks for a roadmap of each
  stage first) and from COLLABORATING.md's list of files. Then, at
  the founder's word, the stages went into the private `ebook-press`
  repository (`history/`, its #8), and the page says where. Then
  stage 011, compiled there from the founder's 17 records and the
  book's final text, and listed on the page. An independent review
  asked for fixes, all made: `011`'s numbers and hash after its
  rebuild, the outside texts in full (*The Art of War* in `004` too,
  *The Art of Peace* in `001`), where the kept copies are and how to
  check them, here and in `docs/CHATGPT.md`, and the page moved to
  COLLABORATING.md's "Start here" group.

- 2026-11-20 Claude: ChatGPT's page, `docs/CHATGPT.md` (#130), at the
  founder's word: their part, who decides, what binds and what
  explores, the four areas, where to start, how to send something,
  the technical lead's first message with five requests, what
  changed, and their records. Looked at first: the founder's two
  conversation records with ChatGPT, 011-16-CGPT and 012-09-05-CGPT,
  read whole, and ChatGPT's review of the repository in the second, held
  to the repository. `main` is still `c69e74d`, with 1,398 files;
  the Rust workspace passes 247 tests and the Python suite 857, with
  RDKit required, as ChatGPT said. Their three findings were real,
  and are fixed: a sketch's README said the crate
  `rust/endless-plant` was built; COMMONS.md had a lookup in the Library on the record, which
  the decision of 2026-11-17 took back; URWORLD.md and
  COLLABORATING.md had ALICE and BOB begin in the garden.
  COLLABORATING.md tells DeepSeek and Gemini, in a message to both;
  AGENTS.md keeps the page current with every pull request. Then the
  founder's word on who supplies which files (Decided), in the page's
  fourth request. An independent review asked for seven fixes, all
  made: the same conflicts in six more places (TOPICS.md,
  README.md, MINDS.md, WORLD-TYPES.md, FRACTALS.md, and a comment in
  `rust/ur-world`); what may enter Core; the earlier works named only
  once brought (house rule 8); one title for the book; the records
  named in full; and the page's check of whether it is current.

- 2026-11-18 Claude: the last piece of course step 3b is built, the
  records' side of part four: who may act on a log
  (docs/research/REDACTION.md, "Part four, the records' side, built").
  Looked at first: the six things the plan left for this side, the
  log's side, the act of redacting, and the grant and the decision
  as records-v1 holds them. Built: `world/acts.py` and `rust/acts`,
  which hold every act in a log to the signed record it carries, and
  every office to its grant, up to the room's key; two kinds of
  record in records-v1, an author's taking back and putting back (22
  kinds of record now, and 36 definitions in the schema); and
  `vectors/acts.json`, with 6 rooms that hold, 61 that are refused,
  each for one of 24 reasons at one entry (three with two faults),
  and 7 records held to their office's grant on their own. The record vectors hold 29
  records that hold and 94 that are refused (26 and 86 before).
  Checked: 857 tests in Python (829 before; 3 skipped, as before),
  under Python 3.12; 247 in Rust (238 before), with fmt and clippy
  clean; Rust refuses every room for Python's reason at the same
  entry; the sketches' check, six lines, each with no problem. Each
  check was weakened on purpose, one at a time: 49 changes to the
  Python, all caught; 47 to the Rust, 46 caught, and one that changes
  nothing a caller can see. The first run of each found a case no
  test held, and both are in the vectors now: an author's key that
  is marked and still in the contents, and a decision signed at the
  second its grant begins. The independent review found nothing
  blocking; from its four other points, three rooms with two faults
  went into the vectors, an office is now held only to the act its
  record is for, the comparison of times as text says why it holds,
  and (k) now says, as the code does, that a key under a mark is not
  read. Found on the way: COLLABORATING.md said
  its list held 258 files when it held 265; with this change's seven
  it holds 272, and says so. Not done: the room's steps that write
  an act only where this check allows it (step 3c); taking a grant
  back before its end; an office's name, shown from its own record
  (step 3d); successions (step 8a). Not run: the web pages' tests,
  since nothing they read changed, and Python 3.10 and 3.11. Next:
  the course is rechecked, as after every step.
- 2026-11-18 Claude: Gemini's record is continued, as the founder
  brought it (814,977 bytes, 19,219 lines; its first 769,085 bytes
  are the record as it was kept). Looked through first: the
  founder's one turn in the new part holds nothing personal; there
  is no link, long number or key in it; and the code reaches for no
  file, process or network. It holds Gemini's answer to their fifth
  file: the five repairs of the list of doors, two files, kept as
  written in sketches/gemini/2026-11-17-4 and held to the record by
  that folder's take.py. Laid over the crate: 152 of 152, as Gemini
  expected. All 22 stages of review/steps.sh were built again, each
  on its own, and are as recorded; the crate as it stands is now
  152 tests in 32 files, and its four demos and the plug-in's own
  run. Compared: Gemini's attack file with the one they sent
  before, test by test; in the twenty attacks that were to stay, no
  code changed but the one field asked for, and 25 comment lines
  were taken out. Tried, in a throwaway copy outside the
  repository: each repair broken on purpose, fifteen ways, one at a
  time, and Gemini's tests caught all fifteen; and seven trial
  tests of the technical lead's own, all passing. Read by the
  technical lead: Gemini's prose, their `src/doors.rs` whole, and
  the five tests they wrote again; the twenty that did not change
  were compared and run, not read again. Then Gemini's next file
  was built and sent to the founder
  (sketches/replies/2026-11-18-for-gemini.txt, 91,773 bytes): one
  step in four parts (Decided by the technical lead). Before it was
  written the step was made in a second throwaway copy, with seven
  trial tests of what the file states: with it made, every test of
  the crate passes but one, which holds the whole text of a list
  and must gain the new line. Neither copy is kept, and nothing of
  them is in the repository. The two reply files before this one
  are no longer current. Also: the build scripts and the status
  test under sketches/deepseek/012-07-03, which are the project's
  own, said "its" of DeepSeek and of Gemini in nine places, and say
  "their" now; the sweep of 2026-11-17 had left `sketches/` out
  whole. Not checked: Gemini's twenty unchanged attacks, line by
  line; the other scripts and comments of the project's own under
  `sketches/` for the same pronoun.

> End of `STATUS.md`.

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

## Log

*Earlier entries are in the archive, a file for each day: [archive/STATUS/](https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/archive/README.md).*

- 2026-11-22 Claude: Gemini's record continued, to 43,646 lines (the
  kept copy a prefix, byte for byte), and the founder's words recorded
  ("Decided"). Four Rust deliveries are kept beside the crate in
  sketches/gemini/2026-11-22-2/, each built on the crate as it stands:
  `retelling` 168 of 168; the two `neuro` and `neuro_mind`, with the
  comparison change of `circuit` and `library`, 168 of 169, 171 of 172
  and 173 of 175 (sketches/INDEX.md). The other eight folders' manifests
  name the record's new size and hash; their lines are unchanged. The
  Python and the Hugging Face package went to the new TriNet repository,
  set up in TriNet #1.

- 2026-11-22 Claude: the founder's turns counted, and the founder's
  word on when they began to be kept ("Decided"). Counted by a script
  that reads every copy of every record and writes nothing out of
  them: the history's stages, the public records, the private ones,
  and the copies the founder uploaded. Each copy's turns were taken
  out, the repeats across copies removed, and the rest sorted by their
  words alone. What was found on the way about the records' form is
  kept for the extraction (docs/COURSE.md, "The records' forms
  differ"). This conversation is kept on disk only from 2026-11-17;
  its earlier weeks are not, so its count is short.

- 2026-11-22 Claude: the founder's words recorded ("Decided").
  ChatGPT reads several pages and follows links, so their page is now
  instructions and links, at the founder's word: docs/CHATGPT.md
  (12,798 bytes) says what to do each time they begin and links
  everything; the messages, what changed and the ideas set aside moved
  whole to three pages of their own, with two links within the old
  page made full links. AGENTS.md, the outline's sources, STATUS
  ("Now") and the list of full links point to them. The note in the
  entry below about the page's size no longer applies. And a plan for later,
  very important in the founder's words: every record's turns of the
  founder's, word for word, with ids, indexing all the records, for a
  book of the founder's own words (docs/COURSE.md, "Waiting"). Counted
  only, for its size: some 4,500 turns marked "::" in the records seen
  today, before repeats are removed; nothing was taken from the
  private records.

- 2026-11-22 Claude: the guide's readers, at the founder's word
  ("Decided"), recorded to guide its writing: `guide/README.md` gains
  "Who it is for" (a person or an AI; to take part, to build, or to
  understand; now or later) and rules 9 to 11 for a reader who comes
  later; the outline's F.2 becomes "Ways through", by purpose, with a
  route for the reader who will not take part; a message to ChatGPT,
  who drafts the guide. ChatGPT's "What changed" had missed #144 to
  #146; they are added. Their page is now 29,648 bytes, past the
  28,000 it is meant to keep under (it is cut into parts as well);
  moving its older messages to the archive is still to do.

- 2026-11-22 Claude: the founder's word on Gemini and rooms
  ("Decided"): a room whose law hides how many are in it gives no
  look, made in the sketch crate as change 27 (one check in `look`;
  166 of 166, and a trial test, not kept, showed it refuses such a
  room and still looks into an open room that shows its count). Both
  files below were built again with it before either was given.

- 2026-11-22 Claude: a file for each collaborator, at the founder's
  word ("Please ensure for DeepSeek and Gemini that you provide me
  with a file to give them, since they cannot reliably access links
  yet"). DeepSeek, sketches/replies/012-07-03-3-for-deepseek.txt
  (84,264 bytes): their deliveries 8 to 11, Gemini's step since, their
  two choices answered, and one step: how a member's records stay
  chained when the keeper refuses one, in prose first, and two
  repairs to their joined room, both tried first in a throwaway copy
  (182 of 183 with them, the chaining test still failing). Gemini,
  sketches/replies/2026-11-22-for-gemini.txt (103,515 bytes): their
  sixth step and prototypes, and twenty-one attacks on what a door
  shows and on a look, the last on a room that hides its count,
  which gives no look (change 27); two facts it states tried first.
  Both sent to the founder.

- 2026-11-22 Claude: Gemini's record 012-08-04 continued (34,033
  lines; the copy kept before is a prefix of it, byte for byte), and
  two pieces of Gemini's work built. Looked through first: nothing
  personal in the founder's turns, no link, long number or key, and
  no text of the founder's conversation with ChatGPT, which the
  founder gave Gemini and which stays private; Gemini's record names
  that file and describes some of its ideas. It opens with Gemini's
  reading of the founder's book, which is public. (1) Gemini's answer
  to their sixth file (sketches/gemini/2026-11-18/): it was already in
  the copy kept on 2026-11-20, at line 19220, and was not built then;
  on 2026-11-21 the file was taken as not yet given and built again,
  which was wrong. The file as given is restored
  (sketches/replies/README.md). Built: 156 of 156 on the crate Gemini
  was given, as they expected, and 166 of 166 on the crate as it
  stood; it is now the crate as it stands, 166 tests in 34 files
  (steps.py stage `said`). Each of its four parts broken on purpose,
  twelve ways: all caught. Gemini's reason in answer to its question
  (a look into a room that hides its count gives the count away
  through its authors) is right; of their remedies, a look with no
  authors or no look holds, and numbering the authors does not.
  Which is the founder's. (2) Eight prototype modules Gemini chose from the
  ChatGPT conversation (sketches/gemini/2026-11-22/), nine deliveries,
  the second a repeat of the first: six build and pass alone on the
  crate; `circuit` and `library` need equality on the crate's proof
  types, and with it all eight together give 190 of 190. Each
  module's main rule broken once: all eight caught. Kept beside the
  crate, not in it, as ahead of the core. `transform`'s orbit counts
  agree with a separate count and with the book. Also: review/steps.sh
  brought up to date (it still named the crate of 152 tests) and run
  whole: all 28 stages as recorded, every demonstration runs. A
  message to Gemini on their page.

- 2026-11-21 Claude: DeepSeek's record 012-07-03 continued, and four
  deliveries built (#144). The founder's new copy (33,100 lines) holds
  the rest of delivery 8, which the earlier copy had cut off,
  DeepSeek's answer to the technical lead's note, and three deliveries
  of their own choosing. Line 12's record number, back in the new
  copy, is taken out again as before; nothing else in the first 28,455
  lines differs. Built in order on the crate: delivery 8 (the rule of
  one moderator's room) does not build for one type; delivery 9 turns
  it, 162 of 162, and is now the crate as it stands; deliveries 10 (a
  room one has joined, and the keeper's side) and 11 (that side
  checked as the log is) give 171 of 173 and 176 of 179, the same
  three failures on DeepSeek's own base, so they are kept beside. A
  message to DeepSeek on their page gives the three failures and
  answers their two choices. Gemini's file of 2026-11-18, not yet
  given, is rebuilt with the crate as it stands (92,036 bytes), since
  two of the files it shows have changed.

- 2026-11-21 Claude: drafting first, editing later, recorded (#143):
  STATUS.md "Decided", the guide's home ("Where it stands"), and a
  note to ChatGPT on their page; the technical lead's editorial notes
  are held for the editing phase.

- 2026-11-21 Claude: the guide's first drafts (#142). ChatGPT's
  delivery 012 holds all eleven chapters of edition 1 (F.1 to F.4, I.1
  to I.6, R.1; 127 numbered sections, some 36,000 words), written from
  commit `7ade210`, with review notes. The chapters are in `guide/F/`,
  `guide/I/` and `guide/R/`, word for word from its manuscript, split
  by script at the chapter headings (rejoined, they give the
  manuscript's text again; 143 links between and within chapters all
  resolve); each says `Progress: draft`, and the home page lists them.
  The handoff, the roadmap proposal and the review notes are kept in
  `guide/deliveries/012/`, with the size and hash of all 25 files of
  the zip. Spot checks of I.1's and I.3's claims against the code
  held; the full technical check is next, chapter by chapter.
  ChatGPT's conversation record is listed anew in `docs/CHATGPT.md`
  (921,638 bytes).

- 2026-11-21 Claude: the guide's home and outline (#141), at the
  founder's request. `guide/README.md` is the home: where it stands,
  the contents (85 chapters, each with its progress, written by
  `guide/contents.py` and checked by `tests/test_guide_contents.py`),
  what it is for in the founder's words, who writes it, and eight
  rules every chapter is written by (the guide explains and never
  rules; six labels, Built, Sketched, Decided, Designed, Idea and
  Open; sources and a commit at the end of each chapter; numbers that
  never change; sections that can be read alone; one word for one
  thing; a text twin for every figure; reference parts made by
  script). `guide/OUTLINE.md`: front matter, nine parts and a
  reference section, some eighty-five chapters, each with what it
  covers, its label today and its sources.
  `tests/test_guide_outline.py` fails when an area of the repository
  (a top-level folder or file, a page or tool in docs/, a Rust crate)
  is named in no chapter. Core first: edition 1 is the front matter,
  Part I and the glossary. `docs/CHATGPT.md` has a message for
  ChatGPT.

- 2026-11-21 Claude: the founder's way in from the Library to a room,
  and "Let's start with the core functionality", recorded (#140), in
  STATUS.md "Decided", `docs/COMMONS.md` ("From the Library to a
  room"; "Order", "Core first") and `docs/TOPICS.md`, topic 23.

- 2026-11-21 Claude: the founder's "Yes, like Slack", "we should make
  a Slack plug-in" and "Combining ideas to multiply functionality is
  the formula" recorded (#139), in STATUS.md "Decided" and
  `docs/COMMONS.md`, "A room of many forms", with a reading of Slack's
  parts onto a room, the technical lead's lean on the open question
  of areas, a reading of the plug-in (also in "Order", item 5), and
  a reading of the formula.

- 2026-11-21 Claude: the founder's idea of a room of many forms put on
  the record (#138): STATUS.md "Decided"; `docs/COMMONS.md`, "A room of
  many forms", with the forms to look at, the technical lead's reading
  and what is open; and `docs/CHATGPT.md`, among the ideas set aside.

- 2026-11-21 Claude: the archive, at the founder's word (#137).
  `docs/archive.py` moves a living page's older dated entries, whole,
  into `archive/<page>/<day>.md`, with a catalogue, and checks it;
  `tests/test_archive.py` (43 tests after the review and its two
  re-checks; faults planted in the script's guards, each caught). First run: 355 entries of STATUS.md
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
  archive, unchanged (the Log entry for this change aside, which was
  written on after its run). The review's re-check found one more:
  a code block never closed in an old message would have made a later
  run move the rest of COLLABORATING.md with it. The script now stops
  on a code block never closed, on one an entry opens and does not
  close, and on a date later than tomorrow; reports a catalogue it
  can't read; and CI fetches the commits the catalogue names, so each
  archived entry is compared there with its page as it was. The second
  re-check found a block left open and closed by a later one, which
  still joined what lay between; the script and its check now stop on
  any line inside a code block in a dated section that would start an
  entry or a section, and the check counts only pointers outside code
  blocks.

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

> End of `STATUS.md`.

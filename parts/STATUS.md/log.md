> Part of `STATUS.md` in open-worlds, which is kept cut into parts
> for readers who are shown only the start of a long page.
> This part holds: "Log".
> Every part, in order: https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/parts/INDEX.md
> Before this part: https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/parts/STATUS.md/decided-by-the-technical-lead.md
> After this part: nothing; this is the last part.
> Made by docs/parts.py from the file. To change it, change the file.

## Log

*Earlier entries are in the archive, a file for each day: [archive/STATUS/](https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/archive/README.md).*

- 2026-11-21 Claude: the founder's "Yes, like Slack" and "we should
  make a Slack plug-in" recorded (#139), in STATUS.md "Decided" and
  `docs/COMMONS.md`, "A room of many forms", with a reading of Slack's
  parts onto a room, the technical lead's lean on the open question
  of areas, and a reading of the plug-in (also in "Order", item 5).

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

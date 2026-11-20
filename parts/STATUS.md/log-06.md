> Part of `STATUS.md` in open-worlds, which is kept cut into parts
> for readers who are shown only the start of a long page.
> This part holds: "Log", piece 6 (its pieces are numbered from its end).
> Every part, in order: https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/parts/INDEX.md
> Before this part: https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/parts/STATUS.md/decided-by-the-technical-lead-01.md
> After this part: https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/parts/STATUS.md/log-05.md
> Made by docs/parts.py from the file. To change it, change the file.

## Log

- 2026-11-20 Claude: ChatGPT's page, `docs/CHATGPT.md` (#130), at the
  founder's word: their part, who decides, what binds and what
  explores, the four areas, where to start, how to send something,
  the technical lead's first message with five requests, what
  changed, and their records. Looked at first: the founder's two
  conversation records with ChatGPT, 011-16-CGPT and 012-00-00-CGPT,
  read whole, and ChatGPT's review of the repository in the second, held
  to the repository. `main` is still `c69e74d`, with 1,398 files;
  the Rust workspace passes 247 tests and the Python suite 857, with
  RDKit required, as ChatGPT said. Their three findings were real,
  and are fixed: the endless plant's README said its crate was
  built; COMMONS.md had a lookup in the Library on the record, which
  the decision of 2026-11-17 took back; URWORLD.md and
  COLLABORATING.md had ALICE and BOB begin in the garden.
  COLLABORATING.md tells DeepSeek and Gemini, in a message to both;
  AGENTS.md keeps the page current with every pull request. Then the
  founder's word on who supplies which files (Decided), in the page's
  fourth request. An independent review asked for seven fixes, all
  made: the same two conflicts in six more places (TOPICS.md,
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
  test under sketches/deepseek/012-09-05, which are the project's
  own, said "its" of DeepSeek and of Gemini in nine places, and say
  "their" now; the sweep of 2026-11-17 had left `sketches/` out
  whole. Not checked: Gemini's twenty unchanged attacks, line by
  line; the other scripts and comments of the project's own under
  `sketches/` for the same pronoun.
- 2026-11-17 Claude: the record vectors say "they" too (Decided by
  the technical lead, the newest entry). Three texts changed in
  `formats/record_vectors.py`, and `vectors/formats/records-v1.json`
  written again from it: 33 lines. The other vector files were
  written again from their code and did not change. Run here: the
  829 tests, and the Rust workspace's format check, lints and
  tests. With this, no page, comment or vector of the project's own
  says "it" of an agent where the technical lead has looked; what
  was not looked at is in the entry below.
- 2026-11-17 Claude: "they" for AI agents, the rest (Decided, and
  Decided by the technical lead). In the project's own code: 53
  passages of comments and docstrings in 22 files, Python and Rust,
  each read where it stands; the list came from a script that looked
  for "it", "its" and "itself" in a comment within three lines of a
  word for an agent (229 lines). Checked by script: with comments
  and docstrings set aside, every changed file is the same code as
  before. Two pages mended with it: docs/URWORLD.md, three passages
  where a mind was still "it", and docs/FILES.md, one line, through
  the string in docs/files.py that writes it. In the other
  repositories, all merged today: the policy handbook has the rule
  as decision 0006 and in its writing standard (policy-handbook
  #13), and the founder's seven other repositories carry it in
  AGENTS.md, with CLAUDE.md saying "they" of the technical lead.
  Left as they are: the handbook's decisions 0001 to 0005, which
  say "it" of the technical lead, because an accepted decision
  record is not edited (P5); decision 0006 says so. Run here: the
  829 tests, the sketch folder's tests, and the Rust workspace's
  format check, lints and tests. Not checked: a comment whose agent
  is named more than three lines from the pronoun.
- 2026-11-17 Claude: "they" for AI agents, at the founder's word
  (Decided, and Decided by the technical lead). The rule is in
  AGENTS.md ("Always"), docs/COLLABORATING.md (house rule 16, and a
  message to both collaborators) and docs/GLOSSARY.md ("Agent"). The
  pages were changed to match: 674 pronouns in 38 files. How it was
  done: a script listed every "it", "its" and "itself" outside
  quotation marks and code, in a sentence that names an agent or
  follows one that does, 3,542 places; the technical lead read each
  in its sentence and marked the ones that stand for an agent; the
  script changed those and the verb beside each; then every changed
  line was read again, with the rest of each sentence whose subject
  changed, and thirty-one places were mended by hand (a second verb, a
  heading, a quotation of a changed line). Not changed, and why, is
  under "Decided by the technical lead". Not checked: sentences where
  the agent is named more than two sentences before the pronoun were
  looked for only where the sentence begins with "It" or "Its" (88
  places read, two passages mended); others of that kind may remain.
  The file built for Gemini (sketches/replies/2026-11-17-4-for-gemini.txt)
  is unchanged and not yet given: it speaks to Gemini as "you", and
  no "it" in it stands for an agent.
- 2026-11-17 Claude: Gemini's record is continued, as the founder
  brought it (769,085 bytes, 17,954 lines; its first 733,438 bytes
  are the record as it was kept). Looked through first: the
  founder's turns in the new part hold nothing personal. It holds
  Gemini's answer to their fourth file: 25 attacks on the list of
  doors, one test file, kept as written in
  sketches/gemini/2026-11-17-3 and held to the record by that
  folder's take.py. Built beside the crate as it stands: 147 of 152
  pass, and the five that fail are the five Gemini named
  (review/steps.sh, `doors-attacks`; all 21 stages of that script
  were built again, each on its own, and are as recorded). The
  crate as it stands is not changed: 127 tests in 31 files. Read by
  the technical lead: Gemini's prose in the new part, and the five
  tests that fail; the other twenty were run, not read line by
  line. What is done with the five is under "Decided by the
  technical lead". Before Gemini's next file was written, the five
  repairs it asks for were made in a throwaway copy outside the
  repository, with three of the attacks rewritten as the file asks
  and four trial tests added: 156 of 156. The copy is not kept, and
  nothing of it is in the repository. The file is built and was
  sent to the founder
  (sketches/replies/2026-11-17-4-for-gemini.txt, 95,491 bytes):
  five repairs, in Gemini's own two files. It leaves Gemini's own
  attack file out and tells Gemini to work from their last reply for
  that one, which no file before it did.

> The next part: https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/parts/STATUS.md/log-05.md

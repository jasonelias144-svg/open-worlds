> Part of `STATUS.md` in open-worlds, which is kept cut into parts
> for readers who are shown only the start of a long page.
> This part holds: "Log", piece 5 (its pieces are numbered from its end).
> Every part, in order: https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/parts/INDEX.md
> Before this part: https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/parts/STATUS.md/decided-by-the-technical-lead-01.md
> After this part: https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/parts/STATUS.md/log-04.md
> Made by docs/parts.py from the file. To change it, change the file.

## Log

- 2026-11-17 Claude: the founder's words on how the multiverse is
  built are in the charter (CHARTER.md, section 1): by learning
  through making choices, as its worlds are lived in. Recorded with
  them (Decided): the founder's idea of similar patterns at different
  scales and the comparison operator, with the technical lead's
  reading in docs/VISION.md; and that the work with DeepSeek is slower
  from now on. Two practices follow (Decided by the technical lead):
  the question of scale in each plan, and rounds with a collaborator
  sized to one step. AGENTS.md says why decisions are recorded with
  what would show them wrong. Nothing is built by this.
- 2026-11-17 Claude: redacting, on the log's side (course step 3b,
  part three, first of two sides). In `world/apart.py`,
  `rust/world-log/src/apart.rs` and `vectors/log-apart.json`: a mark
  now says its office and its ground; a new kind,
  `field_stays_redacted`, says a redaction stands for good; a field
  has one mark that is open or stands, and a mark is answered once; a
  new function gives every redaction with its state (open, stands,
  kept public), and the joining function gives them with each entry;
  the writer has `mark`, `take_out`, `keep_public` and
  `stays_redacted`, and its plain appending refuses the three kinds.
  Twenty reasons for refusing, 179 logs or contents refused and seven
  that hold in the vectors. Rust writes the five-states case again
  with its own writer and gets Python's log. The command line counts
  redactions. The independent review found that the writer still held
  a field's salt after taking it out, in both languages; it now
  remembers salts by their hashes alone. From the same review: the
  form's own kinds are held to exactly what they say in the open, and
  no table can keep that apart. Checked: Python's tests of the form
  (83), Rust's (36, and 12 for the command line), and mutation checks,
  29 changes to the Python and 31 to the Rust, each of which makes a
  test fail but one in each, which changes nothing that can be seen
  (a key that is missing is already refused for what it should have
  said). Not done: the act of redacting with the sealed copies, which is next;
  who may mark or decide; and no test can show that short ids are
  worked out over incidents and redactions together by two ids that
  really collide, since that needs about 2^24 hashes on each side.
- 2026-11-17 Claude: the founder's general guidance recorded, and what
  was open decided under it (Decided, today): the two roles, the floor
  between multiverses, the office's sealed copy, the levels of privacy
  a room may have, the Ur-room on the record, the six changes to the
  founder's ideas on personal information in a room, who may read a
  removed comment, and step 10. "Open questions" now holds only money,
  acts that are the founder's own, and words that have to be the
  founder's. The pages those decisions change say so: AGENTS.md,
  docs/FUNDAMENTALS.md (privacy, items 4, 13 and 15, and the two rules
  on redaction), docs/COMMONS.md, docs/research/REDACTION.md,
  docs/COURSE.md, docs/TOPICS.md, docs/VISION.md. Also recorded: which
  of Gemini's models the founder works with. Nothing is built by this.
  Next in the course is redacting (step 3b, part three), which no
  longer waits. Not done: the policy handbook's own page on the two
  roles follows in its own pull request.
- 2026-11-17 Claude: Gemini's second round is in. Three deliveries on
  the Commons' own log, taken out of the record by script and kept as
  written in sketches/gemini/2026-11-17/. Built one over the other
  from the crate Gemini was given, every test file run: the log read
  from outside, 69 of 69; 16 attacks, 82 of 85, the three that get
  through being the three Gemini said would; the repairs and two
  checks across logs, 92 of 92, and the four demos run. Every number
  is the one Gemini gave, and nothing was repaired here. A Commons
  record can now be written to JSON and read back, which it could not
  be. The crate as it stands,
  sketches/deepseek/012-09-05/chat-world-now/, is the third delivery:
  92 tests. The record grew and was replaced
  (sketches/records/012-00-00-GMNI-Multiverse_Development.txt, 633,994
  bytes): its first 574,502 bytes are the copy that was here, which
  ended with the empty opening of the founder's next message. Looked
  through first: nothing personal and no key in what was added. Not
  done: the file's fourth step was not begun; the whole build script
  was not run again, only the three new stages and the four demos;
  DeepSeek's step is still out, and the two are joined when it is
  back; nothing is fitted to open-worlds' own formats.
- 2026-11-17 Claude: a second file for Gemini, at the founder's
  request: "As it turns out Gemini is ready to go, while I have to
  wait a few more hours for DeepSeek. Can you throw together a single
  document for Gemini again. I have the one for DeepSeek, should I
  just rename that, or would you prefer to provide another different
  file?" A different file, so that the two do not write the same step
  twice (Decided by the technical lead, today). It is
  sketches/replies/2026-11-17-for-gemini.txt, built by docs/reply.py:
  97,419 bytes, thirteen of the crate's files. It tells Gemini what
  its four deliveries built to, and asks four steps on the Commons'
  own log. Two findings in it were tried here first: the Commons'
  check takes a value only the crate's own code can build, and a
  Commons record written to JSON holds its "type" twice and can't be
  read back. DeepSeek's file stands as given; what changed after it
  was given is said in sketches/replies/README.md and in
  docs/COLLABORATING.md. Not done: nothing was built for this beyond
  the one probe of the Commons record; whether both collaborators'
  work joins cleanly is known only when both are back.
- 2026-11-17 Claude: Gemini's conversation is with the records, at the
  founder's word (Decided, today). The record is
  sketches/records/012-00-00-GMNI-Multiverse_Development.txt, byte for
  byte as the founder gave it: 574,505 bytes, 13,530 lines. Looked
  through before it went in, by script, and the founder's 27 messages
  read: no key, password or address, no one else's personal details,
  and none of Gemini's reasoning text. It holds the founder's own work
  by its title and what the founder says of it and of themself, which
  the founder was told of and confirmed. Gemini's files in
  sketches/gemini/2026-11-16/ are now held to the record as DeepSeek's
  are: take.py, run with no argument, takes them out again and
  compares, and the folder test of sketches/deepseek/012-09-05 runs it
  in CI. Pages that said the conversation was not kept are corrected
  (sketches/README.md, the folder's README, docs/FILES.md), the rule
  on personal data in AGENTS.md has the founder's addition, and
  sketches/README.md says on what footing Gemini's outputs are given
  (the Google Terms of Service, read today). The whole record is also
  in the private repository, from earlier today. Not done: Gemini's
  replies were not read through, only searched; the steps Gemini wrote
  before it was given its file (from line 1209) are in the record and
  are not taken out or built again; the founder's other records, which
  the founder spoke of gathering later, are not here yet.
- 2026-11-17 Claude: Gemini's work is in. The founder, the same day:
  "Here is the latest fork Gemini. I run through the credits quickly,
  but we still got some work done." Four deliveries, taken out of the
  conversation by script and kept as written in
  sketches/gemini/2026-11-16/, with the conversation's hash; the
  conversation itself is not kept here. Built one over the other from
  the crate Gemini was given, every test file run: a room's log that
  can be checked from outside, 42 of 44 tests; 22 attacks on the
  check, 61 of 66, the three that get through being the three Gemini
  said would; the repairs, 64 of 66, all 22 attacks refused; and a
  fourth, on branches, not asked for, which does not compile and is
  not used. The two tests that fail throughout are DeepSeek's: they
  changed a room's rules after creating it, with no record, and the
  new check refuses that. With them corrected (fix 22) the crate
  passes 66 of 66 and its four demos run. One more repair was made
  here (fix 23): a room's id and law are no longer public fields, so
  nothing can change a room's law in place; still 66 of 66, and the
  demos run. That is the crate as it stands,
  sketches/deepseek/012-09-05/chat-world-now/; review/steps.py puts it
  together from both collaborators' files and holds the folder to
  that. One thing Gemini found bears on open-worlds' own logs
  (Noticed). The next file, for DeepSeek, is built
  (sketches/replies/012-09-05-2): one step, a room that branches,
  which is how a room's law changes, and one question on Gemini's rule
  for signed heads. The reading of a room's branch in that file is the
  technical lead's, for the sketch, and decides nothing for
  open-worlds. Not done: nothing of the crate is fitted to
  open-worlds' own formats; the whole build script was run once before
  fix 23, and after it only the crate as it stands was built again;
  the file given to Gemini was at fault in one place, said in
  sketches/replies/README.md.
- 2026-11-16 Claude: the founder's two roles recorded (Decided): the
  Project Founder, a matter of history, and the Project Director, an
  office the founder holds now. AGENTS.md, "Who decides", says how to
  read "the founder" in a rule; the handbook's GOVERNANCE.md and its
  decision 0004 say the same for every repository. Nothing merged is
  rewritten. Two questions are put to the founder (Open questions):
  what stays the founder's when someone else is director, and how the
  office passes. Not done: the pages still say "the founder" where they
  mean the director; they are brought to the new words as they are
  next changed.

> The next part: https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/parts/STATUS.md/log-04.md

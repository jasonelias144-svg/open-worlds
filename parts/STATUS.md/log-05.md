> Part of `STATUS.md` in open-worlds, which is kept cut into parts
> for readers who are shown only the start of a long page.
> This part holds: "Log", piece 5 (its pieces are numbered from its end).
> Every part, in order: https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/parts/INDEX.md
> Before this part: https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/parts/STATUS.md/decided-by-the-technical-lead-01.md
> After this part: https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/parts/STATUS.md/log-04.md
> Made by docs/parts.py from the file. To change it, change the file.

## Log

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

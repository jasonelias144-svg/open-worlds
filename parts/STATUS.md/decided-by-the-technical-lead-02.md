> Part of `STATUS.md` in open-worlds, which is kept cut into parts
> for readers who are shown only the start of a long page.
> This part holds: "Decided by the technical lead", piece 2 (its pieces are numbered from its end).
> Every part, in order: https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/parts/INDEX.md
> Before this part: https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/parts/STATUS.md/decided-01.md
> After this part: https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/parts/STATUS.md/decided-by-the-technical-lead-01.md
> Made by docs/parts.py from the file. To change it, change the file.

## Decided by the technical lead

Decisions about the code, made by the technical lead under the founder's
deference (above, 2026-11-13), each with its reason and what would show
it was wrong. Questions of what the project is for stay with the founder.

- 2026-11-16, DeepSeek's two questions in record 012-09-05 (its line
  13769), and what follows for fitting `chat-world`:
  (1) A room has its own key, and its creator joins with theirs.
  Reason: every world here is a key of its own, and a room is a world
  (docs/COMMONS.md, "The text world: a room"); so a room can be handed
  on without a person's key changing hands, and a person's key never
  signs as two things. (2) A leave needs no signature but the
  leaver's, and never the room's. Reason: leaving can't be refused, so
  it can't wait on the room's signature; and a world here doesn't sign
  each entry of its log, it signs its log's heads in batches
  (`open-worlds/log-head/v1`). The leaver's signature is enough, not
  required: a leave the leaver can't sign (a lost key or connection, a
  time-out, a keeper taking an inhabitant out) is still a leave, which
  the room records as its own entry and its heads cover, as the
  Ur-world records an exit today (docs/URWORLD.md, "Exit";
  docs/COMMONS.md, "Leaving always works, everywhere").
  So when the sketch is fitted, the room's proof on each record gives
  way to signed heads, the crate stands on `rust/formats` (canonical
  form, proofs, Multikey `did:key`, time given from outside), and its
  records are fitted into `schemas/records-v1.schema.json`, not put in
  its place. Wrong if: a room's signature on each record proves
  something a signed head over the same entries can't (for one, that
  the room took an entry in at a stated time, between heads); then the
  question returns.

- 2026-11-16, the long files in parts: a tool that opens a page for a
  reader may show only its start, so each file a reader works from that
  is longer than 28,000 bytes is also kept under `parts/`, cut into
  parts no longer than that. `parts/INDEX.md` gives every part's full
  link in reading order, and each part ends with the link of the part
  after it. A part holds the file's own text, unchanged.
  `python3 docs/parts.py` writes the parts from the files, and
  `tests/test_parts.py` fails when a file and its parts are out of
  step, when a part is over the limit, or when a long file is neither
  cut nor named as left whole. A Markdown page is cut at its "## "
  headings. A section too long for one part is cut between its
  top-level items and gathered from its end, so that a new entry at the
  top of "Decided" or "Log" changes one part, and the parts below it
  keep their names and their text. (When that part is full, a new one
  is added above it and the section's heading moves into it, and the
  parts on either side of the new one change the links at their top and
  bottom.) Left whole: the test vectors and
  Cargo.lock, which nobody reads through, and the files of record.
  `parts/` is the script's alone: it removes anything there that it did
  not write.
  *Why in the repository, and not on a branch that a workflow writes on
  each merge:* the parts are then checked by the same tests and the same
  review as everything else, and nothing gains the right to push. The
  cost is that a change to a long page must run the script, which the
  failing test says. *Why 28,000:* the window written for is about
  32 KB, and 28,000 leaves room for the lines a tool adds around a page.
  That figure is an assumption here, not a published measurement.
  *What would show it was wrong:* a reader reporting a part cut short
  (then the limit comes down), or the parts adding more work to each
  change than they save in the founder's conversations (then they move
  to a branch written on merge).
- 2026-11-15, every file's full link, all of them: the founder's word
  (Decided, "on links to every file") widens the list of 2026-11-15
  below from the pages and Rust library code to every file in the
  repository. Two pages hold them. docs/COLLABORATING.md's list holds
  everything a reader works from, the Python code and all the tests
  included. docs/FILES.md holds DeepSeek's records, the code taken from
  them, and Experiment 001's run logs, grouped at most 40 to a paste,
  with sizes, and written by `python3 docs/files.py`.
  `tests/test_collaborating_links.py` lists the repository with git and
  fails unless the two pages hold every file, each once, and FILES.md
  is as the script writes it. *Why:* a full link in the founder's
  message opens in DeepSeek's conversation, while the links on
  COLLABORATING.md, the founder found, did not, so a file with no list
  line might not be read at all (a test later the same day showed
  DeepSeek following a link from a small page, not yet from a long
  one); the files of record are kept apart because they are about
  16 MB, more than a conversation can take in, and best sent when a
  question needs them. *Revisit if:* DeepSeek follows the links on
  COLLABORATING.md itself reliably, or the records are needed often
  enough to belong in the main list.
- 2026-11-15, the endless plant (record 012-07-03): DeepSeek's decisions
  are accepted as the record gives them (signed heads in batches; a
  crate and template of its own, `hasMonad` a dial; the neuron's weights
  derived from the logged actions, not signed; the depth cap a safety
  dial; crowding in the tip's column band; a fixed-point baseline; Drop
  as shedding; water an input), and the project fits it as
  `rust/endless-plant`, changed where the review found faults
  (sketches/deepseek/012-07-03/README.md): Grow extends a tip and Split
  forks it; the plant is a tree, so a dropped tip frees only the segment
  nothing else grows from, pays back exactly that, and falls back to
  its start; no segment grows into a held cell; stored energy has a cap,
  a dial; the noise reads the whole seed; the log is a world's log with
  signed heads and a birth record, and the vectors are the project's
  run, checked from Python. *Why:* each change mends a fault the review's
  tests show (a choice that changes nothing, upkeep paid back twice,
  segments left standing, overlap without bound, a seed read one byte
  deep), and the log keeps the standard every world here keeps.
  DeepSeek's choices are design questions with many workable answers,
  which the founder left to DeepSeek's judgement and the technical
  lead's. *Revisit if:* the fitted plant's runs don't settle into
  growing, crowding, shedding and regrowing, or a stage ahead (the
  neuron, water) needs what these choices rule out.
- 2026-11-15, every file's full link, in one list: docs/COLLABORATING.md
  ends with the full link of every page in `docs/`, the key list, the
  schemas, and each Rust crate's manifest, library code and examples,
  in groups to paste; `tests/test_collaborating_links.py` fails when a
  file is added, moved or removed and the list isn't changed with it, or
  when any full link on the page leads nowhere. *Why:* DeepSeek opens
  full links given in the founder's message, and not reliably those
  found in a page; a list kept by hand drifts, and the key list was
  missing from the last one. *Revisit if:* DeepSeek can follow links
  from a page, or the founder's README idea (above) replaces most links.

> The next part: https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/parts/STATUS.md/decided-by-the-technical-lead-01.md

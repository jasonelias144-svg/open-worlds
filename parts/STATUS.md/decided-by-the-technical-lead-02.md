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

- 2026-11-17, two collaborators on the sketch crate at once, each on
  its own files. The rule since 2026-11-16 was one writer at a time,
  so that there is one line of code. The founder had Gemini free
  hours before DeepSeek, and asked whether to give Gemini DeepSeek's
  file renamed. Not that: the same step done twice gives two versions
  of the same files, which is what the rule is there to prevent. For
  this round each has its own files: DeepSeek the room (record.rs,
  room.rs, verify.rs, a new tests/branch.rs), Gemini the Commons
  (commons.rs and new test files), and Gemini finds faults in
  verify.rs without repairing them. The two are joined here when both
  are back. What would show it wrong: a delivery from one that does
  not build over the other's, for a reason other than its own faults.
- 2026-11-16, removing, restoring, taking back and putting back, on
  the log's side (docs/research/REDACTION.md, "Part four, the log's
  side, built"; course step 3b, part four), settled in building it.
  (a) Four more kinds of entry are the form's own, and none of the
  form's six kinds can be removed or taken back. (b) A removal and a
  restoring say in the open the office, one ground (a kind and a
  reference, held to what a `decision/v1` holds a ground to: one of
  four kinds, a reference of at most 512 characters, and for an
  earlier record its hash) and the decision's hash; a taking back and
  a putting back say only what they are on. (c) An author can undo
  their own taking back, and no office can; an office's restoring
  undoes only a removal. It can be made while the author's taking
  back stands: the removal stops standing, and the entry stays taken
  back. This changes the third row of decision 9's table, which
  refused it. (d) An entry's state is taken back, removed, restored or as
  written, in that order, from the open fields alone; an entry once
  removed is never again "as written". (e) An incident's short id is
  the only such among the incidents of its log, and may grow longer
  as the log grows. (f) The joining function gives a removed or taken
  back entry whole, with its state and its incidents. (g) This side
  checks the shape of an act and what it names, not who may act.
  (h) The command line counts the entries removed, taken back and
  restored.
  *Why:* (a) the record of an act must not be hidden by another act;
  (b) a ground the log shows is then always one a signed decision can
  hold, and a room's note can show the ground even if the reasons are
  later redacted (decision 7); (c) no office acts when an author takes
  back their own words (decision 8), so none undoes it; and a removal
  overturned on appeal must be able to go on record whatever its
  author has done since, or the log would show a removal standing
  that the office has overturned (found by the independent review);
  (d) a reader should see that an office once acted, even after it
  was undone; (f) the founder, 2026-11-16: "the comment stays in the
  data layer, in our records", and what is shown is the room's view;
  (g) who may act needs keys and signed records, which `world-log`
  does not read.
  *Wrong if:* a room needs an entry's state to depend on anything not
  in the open fields; a room's note can't be made from what the
  joining function gives; two incidents in one room are ever shown
  with the same short id; the records' side finds that a signed
  decision can't say what the open fields say (it may hold several
  grounds, and the log shows one); or step 3c finds that a reader
  built on the joining function shows a removed comment unless it
  takes care not to.
- 2026-11-16, a world with inhabitants that moves to another
  multiverse (docs/WORLD-TYPES.md, "Arriving in another multiverse",
  steps 5 and 6), from the last check of the pull request that
  recorded the founder's words on it. In a move, such a world departs
  only from a head that an admission names: if it lived on after the
  evaluation, what it added is evaluated too, an admission is given at
  its present head, and it is paused from that head until it departs.
  After the admitted head its log may hold the pause, leavings and the
  departure, and nothing else, and the check on arrival is that this
  is so. And the move counts only when the admission holds. Leaving to
  stand alone is unchanged.
  *Why:* its inhabitants consented to a move to a named multiverse. If
  the check on arrival could fail after it had left, they would be
  left standing alone, which none of them agreed to.
  *Wrong if:* the pause between the last evaluation and the departure
  is long enough to be a harm of its own to those inside; or the
  founder means the second refinement taken on 2026-11-16, that what
  a world added after the evaluated head is checked again on arrival,
  to be the whole of the rule for every world.
- 2026-11-16, the form of a log whose fields are kept apart
  (docs/research/REDACTION.md, "Part two, built"; course step 3b, part
  two), settled in building it. (a) The form is named
  `open-worlds/log-apart/v1`, in the first entry. (b) An entry's
  fingerprints sit in a map of their own, `apart`, beside its open
  `data`, never in the values' places. (c) The table of which fields
  are kept apart, kind by kind, is in the first entry, and every entry
  is held to it; an entry holds its seven keys and nothing else, so
  nothing sits where the table doesn't reach. (d) `agent` stays in the
  open and can't be kept apart. (e) Two kinds of entry are the form's own: a mark, and a
  decision to keep a field public, each naming in the open what it is
  on. (f) A mark stands until such a decision answers it; a field
  whose mark was answered and which is gone is missing, the one case
  decision 4 had not named. (g) A field under a standing mark is never
  shown by the joining function, even while it is still in the
  contents. (h) The contents hold nothing the log doesn't commit to,
  and no salt twice. (i) A missing field is a state, not a refusal;
  the command line fails on it. (j) The open part of an entry is held
  to the same rule as a value kept apart: a tick from 0 to 2^53 - 1, a
  kind that is text, an agent that is text or nothing, data with no
  fraction, nothing beyond 2^53 - 1, and every key text. (k) The order
  of the checks is part of the form: entries in the log's order, each
  by its link, then what it says, then its hash; the contents in
  ascending order of entry hash and field name.
  *Why:* (b) a reader that doesn't know the form finds a field absent,
  and can't show a fingerprint as someone's words; (c) "fixed kind by
  kind" is then checked from the log alone, by anyone; (e) a field's
  state has to be worked out from open fields (decision 9), so the
  form has to know a mark when it sees one; (g) a redaction cut short
  must not leave the field showing; (i) a reader of a copy that has
  lost fields should be told which, not only that it failed; (j) the
  independent review of #101 showed Python's writer writing logs Rust
  could not check, and, through a key that wasn't text, a field the
  table keeps apart in the open; one rule for everything in an entry
  closes both, and is the project's rule for signed records already;
  (k) a log or contents with two faults is then refused for the same
  one in both languages, which the review found was true of the code
  and held by no test.
  *Wrong if:* (b, c) a room needs a field kept apart in some entries
  of a kind and open in others (then the table gives way to the
  entry's own `apart`); (d) a room has to hide which office acted;
  (e) part three needs a mark to name more than one field, or
  something other than an entry; (f) an office that keeps a field
  public has to do it in two steps, and the step between reads as a
  fault; (g) a reader needs an unfinished field's value (the
  contents still hold it; the joining function would then grow a way
  to ask); (h) contents for two logs have to be kept in one file;
  (i) a missing field is ever shown to a reader as if the log were
  whole; (j) a room needs a number with a fraction, or nothing as a
  value, in the open (then it is written as text, or the rule is
  widened in a second version); (k) a third language can't read a map
  in ascending order, or the two here are found to differ on any log.

- 2026-11-16, a log that can be redacted, and removals on record
  (docs/research/REDACTION.md, decisions 1 to 10; course step 3b), as
  reworked after the independent review of #100.
  (1) Which fields are kept apart is fixed kind by kind: what a person
  writes or gives (a text, a name, a clock time, the key that acted)
  enters the chain only as a fingerprint; what a reader needs to work
  out an entry's state (its kind, tick and place, and for the room's
  own entries the act, its target and the office) stays in the open.
  (2) The fingerprint is the SHA-256 of `[salt, name, value]`, with a
  fresh salt of 128 bits from the operating system; none may appear
  twice in a log; both languages refuse the same values. (3) The
  contents are kept beside the log, so the log is never written again,
  and one function joins the two for every reader. (4) Redacting is
  seal, then mark, then take out, and a field is present, redacted,
  unfinished, kept public or missing; the sealed copy is a `sealed/v1` with a new
  label, bound by what is inside it. (5) Proposed, and the founder's:
  a second sealed copy for the office that decides, until the decision
  and any appeal are over. (6) A world with no one in it keeps today's
  form, and a log names its form. (7) A moderator's removal is a
  `decision/v1`; the incident id is the hash of the entry that carries
  it, shown as the fewest digits, twelve or more, that are the only
  such in the room. (8) An author taking back their own comment is a
  record kind of its own. (9) What is shown is worked out from the
  open fields alone, with a table of what wins. (10) Python and Rust,
  with shared vectors.
  *Why:* Matrix signs an event in the form a redaction leaves, so a
  room's history still checks, but its hash of the whole event has no
  salt; SD-JWT (RFC 9901) fingerprints each claim with a fresh salt of
  at least 128 bits, which closes that. `decision/v1` already carries
  what the founder asked a removal to say.
  *Wrong if:* (1) a room needs to redact part of a field, or something
  a state depends on turns out to be private (then that kind of entry
  gets other fields, from its first use); (2) Python and Rust write
  different text for the same value in a vector, or a value a room
  needs is refused (then RFC 8785 for the fingerprint); (3) a
  published log is found without its contents, or a reader skips the
  joining function (then the contents move into the entry under a key
  the hash skips); (4) a state of a field turns up that is none of the
  five; (6) a reader takes one form for the other, or the Ur-world
  can't change form before anyone is born (then one form, with salts
  given to a run); (7) a moderator's act needs a field `decision/v1`
  hasn't, or two incidents in one room show the same id; (8) an
  author's taking back needs grounds or an appeal after all; (9) a
  state can't be worked out without the contents.

- 2026-11-16, the course after step 3a: a new list of twelve
  (docs/COURSE.md, "Rechecked on 2026-11-16"), on the founder's word of
  the same day (Decided, the newest entry). It was put to the founder in
  the session, and stands unless the founder reorders it. Six steps
  come in from the waiting list, which had placed each at this recheck
  or before anyone lives in a world: a log whose
  fields can be redacted, with removals and restorings on record (3b);
  the room, DeepSeek's `chat-world` on the project's formats (3c);
  offices as records (3d); a world's lifecycle, and a world leaving
  (3e); the Commons hosting rooms (3f); and the private container, with
  the check before publishing (6a, before step 7). Steps 4, 4a, 5, 6, 7
  and 8 follow as they were. Steps 8a, 9, 11 and 12 stand behind the
  twelve, in their old order, and step 10 is the development
  container: it is no longer "Back to DeepSeek", since the founder
  returned to DeepSeek on 2026-11-14 and DeepSeek now works beside the
  course. One change since the list was first put to the founder: the
  lifecycle now comes before the Commons hosting rooms, since hosting a
  room is starting, pausing and closing a world.
  *Why this order:* the founder asked for removals on record "from the
  beginning", so the log under a room comes first; the room is where
  the founder's work with DeepSeek lands, and what DeepSeek sends back
  is fitted there; a removal names an office, so offices go on record
  before a moderator holds one in a hosted room; and step 7 keeps the
  sealed self in the container, so the container comes before it.
  *The cost:* six steps now stand ahead of ALICE's and BOB's birth
  that didn't on 2026-11-14. None is new at this recheck: the waiting
  list took each in on 2026-11-15, with where it was to go (at this
  recheck, or before anyone lives in a world). What this recheck chose
  is to put all of 3b to 3f before step 4, with the room among them.
  *The alternative,* put to the founder with it: 3b and 3c first, and
  3d to 3f behind step 6, which brings the Ur-world's first room three
  steps nearer and the Commons later. And if the founder wants the
  Commons open to people sooner, 6a moves up to follow 3f.
  *Wrong if:* the room and the Commons take so long that the Ur-world's
  first room waits on them with nothing learned for it (then 3d to 3f
  move behind step 6); or one of 3b to 3f turns out to need the kernel
  of step 4 (then that one waits for it); or the founder's work with
  DeepSeek turns away from rooms, so that 3c has nothing coming back to
  fit (then the room keeps its place only if the Commons still needs
  it first).
  After the independent review of #99: the review would put the
  Commons hosting rooms, a branch and the closed room after step 6,
  beside 6a, with 3d's formats before the room. Its reasons, and why
  the technical lead keeps 3f where it is, are in docs/COURSE.md, for
  the founder to choose between. Taken from it without changing the
  order: step 3c builds the room on the record, and the closed room
  comes with 6a; a branch of an open world waits for step 4, as restart
  does; 3d's first two offices are a room's moderator and a room's
  Keeper; and 3d's formats may be built beside 3b's.
  After the founder's last words of 2026-11-16 (Decided, the two newest
  entries): step 3c builds the Ur-room first, the Commons' lobby, and
  step 6a names private rooms and private messages. The order is
  unchanged.

- 2026-11-16, one schema that fits both, after the founder's answer of
  the same day (Decided, "on DeepSeek's schema and on bringing
  everything together"). It adds to the entry below, which had only the
  project's form in view, and reverses nothing in it: what the project
  has signed with stays (its proof, did:key, hash and signed head), so
  the crate still stands on `rust/formats`; DeepSeek's record kinds for
  chat join `schemas/records-v1.schema.json`; and for what is new to the
  project the form is chosen case by case, and may be DeepSeek's. A
  table of DeepSeek's names beside the schema's comes in the next pull
  request. Reason: signed records and their vectors can't change, and
  nothing DeepSeek builds on its own schema should be wasted. Wrong if:
  a form the project has signed with turns out to be the worse one for
  rooms; then it changes in a new version of the schema, beside the old,
  never in place.

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

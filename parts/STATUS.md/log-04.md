> Part of `STATUS.md` in open-worlds, which is kept cut into parts
> for readers who are shown only the start of a long page.
> This part holds: "Log", piece 4 (its pieces are numbered from its end).
> Every part, in order: https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/parts/INDEX.md
> Before this part: https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/parts/STATUS.md/decided-by-the-technical-lead-01.md
> After this part: https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/parts/STATUS.md/log-03.md
> Made by docs/parts.py from the file. To change it, change the file.

## Log

- 2026-11-16 Claude: Gemini named a collaborator, at the founder's
  word, and the founder's plan for a file at each return, written for
  the one who receives it, recorded (Decided, two entries). The file
  Gemini was given that day is kept in sketches/replies/, built by
  docs/reply.py from the crate as it stands
  (sketches/deepseek/012-09-05/chat-world-now/): where things stand,
  three steps, and sixteen files. It asks Gemini to make a room's log
  checkable from outside, then to attack the check, then to repair
  what gets through. That came from a finding while writing it:
  `verify_room` takes a `Room`, which only the crate's own code can
  build, so no forged log can be put to it, and the crate's test named
  for tampering tampers with nothing. docs/COLLABORATING.md tells
  DeepSeek, and now speaks to both. Not done: nothing has come back
  from Gemini yet.
- 2026-11-16 Claude: record 012-09-05, continued, brought in: the
  record as the founder shared it again (its first 595,416 bytes
  unchanged, 9,212 lines more), with the cycle on signed heads, the
  one file reaching DeepSeek whole, and five deliveries of
  `chat-world`. Every file the continuation gives whole is kept as
  written in sketches/deepseek/012-09-05/chat-world-steps/ (34 files),
  and sketches/tools/extract.py checks them against the record. Built
  as given by review/steps.sh, each delivery laid over the one before:
  22 of 22 tests; 20 of 22; 27 of 29; 31 of 33; the fifth does not
  compile, and with its two faults set aside passes 39 of 41. The
  three faults are named in sketches/INDEX.md and in a message to
  DeepSeek (docs/COLLABORATING.md), and repaired, in five lines
  changed and three removed (fixes 19 to 21): the crate as it stands,
  sketches/deepseek/012-09-05/chat-world-now/, is the five deliveries
  with those repairs, which review/steps.py puts together and holds
  the folder to, byte for byte. It passes all 41 tests and its four
  demos run. The founder's observation on the one file, and the
  founder's word that the games are kept separate, are recorded
  (Decided), which answers the two questions put on the games. Not
  done: the next file for DeepSeek; nothing of the crate is fitted to
  open-worlds' own formats, which is step 3c.
- 2026-11-16 Claude: course step 3b, the log's side of part four,
  built: what a log says in the open when an entry is removed,
  restored, taken back or put back (four more kinds of entry in
  `open-worlds/log-apart/v1`), each entry's state worked out from the
  open fields alone, the incident id and its short form, and the table
  of what wins, in `world/apart.py` and `rust/world-log`, with vectors
  (124 refused, each for one of nineteen reasons, and seven that
  hold). The command line counts the entries removed, taken back and
  restored. Three notes carried from the last check of part two are
  taken, and two carried from the last check of the founder's words on
  worlds that move (docs/WORLD-TYPES.md, steps 5 and 6; Decided by the
  technical lead). The founder's thought on paying for the multiverse
  from a separate project of games is recorded (Decided), with two
  questions (Open questions). Checked: the Python suite and the Rust
  workspace; and deliberate breakage, 67 changes to the Python and 48
  to the Rust, one at a time, every one caught by a test. Not built:
  the records' side of part four (the list of kinds of act, the check
  of a decision against its grant, the author's record kinds), so
  nothing yet checks who may act; and part three, which waits for the
  founder.
- 2026-11-16 Claude: the founder's words of the afternoon recorded
  (Decided, five entries): a field of dreams; the multiverse as an
  internet, with the comparison held where it fits and the addressing
  made able to grow; many multiverses in one network; worlds that
  migrate, indexed by the multiverse of their birth and by the one
  they are in; and a sandboxed holding place for worlds that arrive,
  with the technical lead's four refinements, which the founder took.
  Written into docs/WORLD-TYPES.md ("Arriving in another multiverse"),
  docs/VISION.md ("An infrastructure for connection"), docs/COURSE.md
  (step 3e and the waiting list), docs/ADMIN.md, docs/FUNDAMENTALS.md,
  docs/TOPICS.md (topic 22), docs/GLOSSARY.md, docs/COMMONS.md and a
  message to DeepSeek in docs/COLLABORATING.md. Checked for these
  entries: the records' schema and the checking code, for where they
  assume one multiverse and for the sizes of every address and counter
  (found: the word "multiverse" standing bare in what a grant holds
  `within` and what a suggestion is `about`, one four-byte counter,
  and no check with the project's keys wired in). Not
  checked: what is said of the internet's own history is from memory,
  as VISION.md says. Two things the technical lead said in the session
  are put right in the entries: a world with inhabitants moves only
  with the consent of every party, as the reading of 2026-11-15
  already had it, not merely after they are told; and whole numbers
  run to 2^53 - 1 in the records, not to 64 bits. Two
  questions are put to the founder and one sentence left out (Open
  questions). Nothing is built.
  After the independent review of #102 (two blocking, fourteen notes,
  each taken): "one multiverse at a time" had been given as the
  founder's, who did not say it, and is now marked as the technical
  lead's reading and put to the founder; the technical lead's readings
  were not marked as such in docs/COLLABORATING.md, docs/COURSE.md,
  docs/GLOSSARY.md and docs/FUNDAMENTALS.md, and now are. Also: the
  counter of presences is fixed by the records' schema as well; what
  happens if the last check of an arriving world fails; that a world
  refused, or one that never asks, can still leave to stand alone;
  that the copy sent to a holding place holds nothing private or
  sealed; that a sandbox for every world's code is to be built and
  isn't; that a birth index must outlive the key it is written as;
  and, in docs/VISION.md, a row of the table that was wrong (the web
  has a signed log anyone can check, for its certificates) and a
  sentence that claimed more than memory supports.
- 2026-11-16 Claude: course step 3b, part two, built: the form of a
  log whose fields are kept apart (`open-worlds/log-apart/v1`). In
  Python, `world/apart.py`: the fingerprint, the values it allows, a
  writer (`Log`), the check of a log with its contents (`check`), which
  gives each field one of five states, and the function that joins the
  two for a reader (`join`). In Rust, `rust/world-log/src/apart.rs`,
  the same, and `world-log LOG CONTENTS` on the command line. The
  kernel's own form and `verify_log` are unchanged, and the chain of
  the new form is checked by that same function. Shared vectors,
  `vectors/log-apart.json`, written by Python: 18 fingerprints with
  the exact text hashed, 9 values refused, 5 logs with contents that
  hold (every state among them) and 90 that are refused, each for one
  of fifteen reasons in fixed words and at one place; Rust gives the
  same answer for every one, and writes the trial room again from the
  same salts to the same log. What building it settled is recorded as
  the technical lead's (above), with one case the plan had not named.
  After the independent review of #101 (nothing blocking, six notes,
  each taken): Python's writer held the open part of an entry to
  nothing, so it could write what Rust could not check, and a key that
  wasn't text (True, written by JSON as "true") could put a field the
  table keeps apart into the open; the open part is now held to the
  same rule as a value kept apart, by the check and so by the writer,
  before anything is hashed. The checks are now taken an entry at a
  time (link, what it says, hash), so that both languages name the
  first fault in the log's order and Rust never hashes an entry it
  could not write; Rust's reason of its own for that is gone. Eight
  vectors hold two faults, and every refused vector now gives its
  place, which the two languages had differed on for two reasons. A
  check that could not be reached was removed, and a redundant one in
  Rust. One note is carried to part three (docs/research/REDACTION.md).
  The reviewer's own run of 20,000 generated logs through both
  languages, before these changes, found them the same in every
  reason, state and joined entry. Not done here:
  no reader is changed, since no world writes the form yet, and
  nothing is redacted. docs/research/REDACTION.md ("Part two, built"),
  docs/COURSE.md, docs/FUNDAMENTALS.md, vectors/README.md,
  rust/README.md and docs/COLLABORATING.md (a message to DeepSeek on
  the form its rooms will be written in) brought into line.
- 2026-11-16 Claude: course step 3b begun by looking first
  (docs/research/REDACTION.md): the project's one log and why nothing
  can be taken out of it today, `decision/v1` and `sealed/v1` as they
  are, then SD-JWT (RFC 9901) for the salted fingerprint and Matrix's
  signing of redacted events for the shape. Ten decisions (Decided by
  the technical lead) and four parts: the plan; fingerprints and
  contents; redacting; removing, taking back and restoring. Every
  quotation from the two outside sources was checked word for word
  against the pages as fetched; Matrix's Client-Server API was not
  opened, and what is said of event sourcing is from memory, as the
  page says. Nothing is built yet. docs/COURSE.md and
  docs/COLLABORATING.md (with a message to DeepSeek on what it settles
  for removed comments) brought into line. The plan was written before
  the founder's last words of the day and now says where they meet it:
  the first room it is built for is the Ur-room, which is on the
  record, and a private room's words are not this step's.
  After the independent review of #100 (four blocking, each taken): the
  plan had redaction seal a field to the person alone, which left no
  way to carry out a decision to keep it public, and let anyone erase a
  public act for good by asking; it now proposes a copy for the
  deciding office, and puts that to the founder. It had every field of
  every entry kept apart, so a mark or a removal could itself be lost
  and a state not worked out; what is kept apart is now fixed kind by
  kind, and a state is worked out from the open fields. The order of
  redacting is seal, mark, take out, so that work cut short can be
  seen and finished, and the four states of a field are named. Whether
  the key that acted may be redacted goes to the founder, and the key
  is kept apart meanwhile. Also taken: the incident id is the entry's
  hash; the sealed copy is bound by what is inside it, with no change
  to sealing; a log names its form; a table of what wins; what part
  four builds for the first time; three more limits; and a "wrong if"
  for each decision that can be tested.
  After the narrow re-check at 6792e3c (the four met; one new thing
  blocking, a contradiction in the table of what wins, mended as the
  reviewer wrote it): an author may take back a comment an office
  removed, and only a second removal, a second taking back, or a
  removal of what its author took back is refused. Its notes were
  taken too: a fifth state for a field put back by decision; the
  ground in the open part of a removal's entry, so the note can show
  it when a reason is redacted; that an office's key is never
  redacted; the cost of redacting a key, in the founder's question;
  and docs/FUNDAMENTALS.md's clause on which fields are fingerprints.
  Carried from
  #99's last re-check, two small notes: the recommendation on the
  Ur-room no longer speaks of a private room "one door away" before
  private rooms exist, and docs/COMMONS.md, "The Ur-room", points to
  the open question on its being on the record.

- 2026-11-16 Claude: the founder's last words of the day recorded
  (Decided, the two newest entries) and written into the pages they
  change, in the same change as the course's recheck. The Commons
  begins with the Ur-room, its lobby, the first room built: step 3c of
  the course builds it, and docs/COMMONS.md has "The Ur-room". Private
  rooms and private messages, sealed with keys their members hold, are
  to be common: docs/FUNDAMENTALS.md gains privacy item 15, step 6a
  names them, and docs/COMMONS.md has "A spectrum of privacy", three
  levels proposed by the technical lead, which wait for the founder
  (Open questions). Nothing was looked at outside the project for
  this, and nothing is built; how a group's keys change as members
  come and go is to be looked at first, at step 6a. The file DeepSeek
  is to be given was built before these words, and doesn't hold them.
  After the last narrow re-check, at 09e4de6 (nothing blocking): the
  proposal now says what it would change in what is decided (sealed
  messages held on the project's machines; nothing kept at the third
  level, against "that a message passed stays in the record"; who
  moderates a closed room), and five more limits, among them that a
  closed room's record shows who is in a private room with whom, and
  when. Whether the Ur-room's talk is on the record is now put to the
  founder. "There are to be levels" became "there may be", as the
  founder's words have it. The limits are from general knowledge of
  how sealed group messaging works, the review's and the technical
  lead's; no source was opened for them.

- 2026-11-16 Claude: carried from #98's narrow re-check, in the same
  change as the course's recheck below. `docs/reply.py` now refuses an
  `out` that is the reply's own text or a spec (writing it would have
  overwritten them), a limit below one, and a control character in a
  path; a spec that is missing or isn't JSON is said plainly; and when
  the file read back after writing is found wrong, the message says
  that it was written. Two rows of docs/research/CHAT-SCHEMA.md say
  less than they did: where `seq` and `prev` are absent is not a whole
  list, and that the one who enters signs `JoinRequest` is read from
  its name and the crate, not from the schema. Left as it is: a
  symbolic link under the reply's root is followed, which a review of
  the repository would show. Still untested: that the byte comparison
  after writing would catch a difference.

- 2026-11-16 Claude: course step 3a done and moved to "Done" in
  docs/COURSE.md, with its pull requests (#61, #75 to #78). The course
  rechecked, on the founder's word of the same day, with a new list of
  twelve (Decided; Decided by the technical lead): six steps came in
  from the waiting list, 3b to 3f before step 4 and 6a before step 7
  (the waiting list had placed each at this recheck, or before anyone
  lives in a world); steps 8a, 9, 11 and 12 stand behind the twelve;
  step 10 is the development container; and DeepSeek's work is written
  in as running beside the course. What persons taught is written into
  steps 3b, 3c, 4, 6a and 7, and into the waiting list's line on
  governance. The steps ahead were checked against VISION.md's six
  tests for the first time: none fails, and two are not met. The
  second is open until step 3f settles who holds a hosted room's key,
  and whether one model may moderate every room. The fifth is not met:
  its signs aren't written, and no step writes them. And whether a
  model that moderates is an individual hasn't been asked (Open
  questions). The day's ideas of the founder's are
  noted, not built: personal information in a room (docs/COMMONS.md),
  worlds built for learners (docs/research/GAMES-AND-WORLDS.md), and
  both on the course's waiting list. docs/COLLABORATING.md,
  docs/TOPICS.md, docs/FUNDAMENTALS.md, docs/WORLD-TYPES.md,
  docs/OFFICES.md, docs/CONTAINER.md and docs/ADMIN.md brought into
  line. Nothing was built in this change, and no source was read
  beyond the quick searches of the session. The look back, at each
  decision's "revisit if" or "wrong if":
  - held, and tested by step 3a: persons (the architectures ran on the
    unchanged core, the third clause of its "revisit if"; no real seed
    exists yet, so the second can't be judged, and no presence has had
    to be shown to one party alone); the four formats moved to later
    steps (step 3a needed none of them);
  - not triggered: the records for the offices (Python and Rust agree
    on every vector of the five kinds step 3a added, but its "revisit
    if" is a disagreement on a record the vectors don't cover, which
    agreeing on the vectors can't test); the plant world (its rule has
    not been changed; the endless plant is planned as a second world,
    with a crate of its own, and isn't built); presence keys by HKDF (no tool has needed wallet
    paths); the council's count (no secret ballot or final count was
    needed; what a final count needs is now on the waiting list, with
    governance); reviews in proportion (no wording-only fix merged on
    the technical lead's own check has been found to change a meaning;
    it was last used on #97); the web app's shared checks (no browser
    but Chromium was tried, as before); the long files in parts (no
    part was reported cut short); the keys for step 3 (the founder
    holds every one of the multiverse's keys, and no private half has
    been found outside the private repository); the chemistry world's
    records of what was made;
  - premise changed, looked at again at the next recheck: every file's
    full link, in its two entries, and the long files in parts. Both
    were made so that links and long pages could be given to DeepSeek
    in the founder's messages. Since the founder's decision of
    2026-11-16, DeepSeek is given one file, with no link. The lists and
    the parts stay, for any other reader, with the tests that keep them
    whole; whether they still earn the script run each change costs is
    judged once a few returns to DeepSeek have used the file alone;
  - due at step 3b: sealing as built, which is built and has vectors.
    Its "revisit if" is a sealed record that needs associated data,
    and its labels are a list of two. A redacted field sealed to a
    person should be bound to its log, its entry and its field, and
    needs a label of its own;
  - due at step 3c: the template, whose "revisit if" is a parameter
    that isn't a number: a room's law would be a template's parameters,
    and a topic or a welcome is a text;
  - due at step 3c: DeepSeek's two questions (whether a room's
    signature on each record proves something a signed head can't) and
    one schema that fits both (whether a form the project has signed
    with is the worse one for rooms). The table of names in #98 already
    shows one place where the fitting has to split a kind (`Redact`),
    which "case by case" allows;
  - due at step 3d: signed records the standard way. Its "revisit
    if" is a record that needs something the narrow reading of proofs
    refuses, such as a proof chain. A handover carries two parties'
    word, the holder's and the successor's. The expectation is two
    records with one proof each, as `holds` and `held-by` are; if that
    won't do, the narrow reading is revisited there. Whether a widely
    used verifier accepts the project's proofs still hasn't been tried;
  - due at step 3e: who an individual and a world are, in its second
    clause, a world's birth record that needs more: a reset's and a
    branch's birth name the run or the checkpoint before;
  - still due at step 6: reasons on record, whose "revisit if" is the
    Lean model of grants costing more than it catches by step 6. Step
    3b uses the decision record first, but touches neither grants nor
    Lean. This recheck puts five more steps ahead of step 6, which the
    clause didn't have in view;
  - due at step 3e and with the endless plant: Rust in the browser as a
    WASI command, whose "wrong if" is a world that must keep running
    inside the page; a plant that runs for hours is that case, and
    pause, resume and checkpoint (3e) are how it is to be met; the
    endless plant's own decisions can't be judged until
    `rust/endless-plant` is built;
  - due at step 6a: the first clause of the keys' "revisit if" (anyone
    but the project holding a key) is read again when persons begin to
    hold their own keys in their own containers, which that decision
    didn't have in view;
  - due at step 8a: who an individual and a world are, in its first
    clause, and decision 18, as before;
  - due at step 9: the sealed records, as before; and a link shown by
    an action, whose "wrong if" is a link that must be shown while the
    presence isn't in its world, which a birth that links the first
    presence may be;
  - not yet testable, since what they govern isn't built: sealing the
    world-key, the round table's consensus, how
    the table is chosen, a Keeper's self-report, ADMIN's council,
    ADMIN's learning by written lessons, the admin-key course, and the
    suggestion ledger;
  - not yet due: today's decision on the course's order.

  After the independent review of #99 (two blocking, both mended): the
  look back had left out "signed records the standard way", and one
  line on hide-and-seek's stages was wrong against its paper. Its notes
  were taken: the look back corrected in seven places; the six tests
  said more plainly; step 3c split, with the closed room at 6a; what
  waits for step 4 in the lifecycle; step 3d's first two offices; and
  the review's own order written beside the alternative, for the
  founder. Three sentences on outside sources now say only what the
  sources say.
  After the narrow re-check at a36e3e6 (nothing blocking, four notes):
  the account of the review's order now gives the review's own three
  reasons, and marks the fourth as the technical lead's; step 6a names
  private rooms, where the closed room's test now stands (the entry
  above); and the reply script's refusal of a file it can't read has a
  test. Known and left: a spec that names another reply's built file as
  its own would write over it, since that is a file the script wrote.

- 2026-11-16 Claude: the file for DeepSeek is now built by a script in
  the repository, and kept. `docs/reply.py` makes it from a reply's text
  and a list of files (`sketches/replies/012-09-05.txt` and `.json`),
  refuses a file over its limit, and reads what it wrote back against
  the repository; `sketches/replies/012-09-05-for-deepseek.txt` is the
  file the founder was given on 2026-11-16, byte for byte (95,149 bytes;
  SHA-256
  f1f7435f21dbaf8d49de3aea07e83d502d38c6011323feb591b769c2c1c97447),
  which replaces the earlier entry's "The file isn't kept here".
  `tests/test_reply.py` holds a reply to its sources while its code is
  current, and to its limit and its last line always. docs/FILES.md
  lists the folder among the files of record ("What DeepSeek was
  given"), so it is neither in COLLABORATING.md's list nor cut into
  parts. Not checked: that the whole file reaches DeepSeek. And the
  table of DeepSeek's schema names beside the project's, as the first
  step toward one schema that fits both: docs/research/CHAT-SCHEMA.md,
  which `tests/test_schema_names.py` holds to both files. 67 definitions
  and 33, none shared by name; seven are the same thing under another
  name; two are one name for different things (DeepSeek's `WorldKey` is
  nearer the project's `grant`); and a moderator's removal lands beside
  the project's `decision`. It compares names and fields only: no record
  was tried against either schema.
  After the independent review (nothing blocking, 24 notes): the script
  now reads the written file from disk as well; refuses a path that
  leaves its folder, a note with a line break, and a spec of the wrong
  shape; and says what it can't read in place of stopping with a
  traceback. Seven tests were added, among them one for the reading
  back itself, which had none, and one that pins the limit to the
  byte; a past reply's size and hash are now looked for in its own row
  of the README. The table was corrected where it claimed more than the
  schema's fields show: where `seq`, `prev` and `world_id` are and
  aren't; `JoinRequest`, not `Join`, as the nearer relative of
  `arrival`; `RuntimeAttestation` beside the project's links, not
  `mind`; `WorldKey`'s parameter ranges beside a template's dials; and
  that the fitting has to split `Redact` (an author taking back their
  own comment is no office's decision) and `HumanOverride`. One
  sentence in the file already given overstates, and is named in
  `sketches/replies/README.md`, since a file that was given isn't
  changed. AGENTS.md names the kept replies.

- 2026-11-16 Claude: one file for the founder to give DeepSeek (Decided,
  the newest entry): the technical lead's reply to record 012-09-05,
  three next steps in order (removed comments, in the data layer and the
  presentation layer; the room's own key; signed heads), and the
  `chat-world` crate as it stands after fixes 15 to 18, sixteen files,
  each whole. 95,149 bytes, 2,590 lines, built by script from main at
  8921e86; SHA-256
  f1f7435f21dbaf8d49de3aea07e83d502d38c6011323feb591b769c2c1c97447. (Two
  earlier versions, of 92,658 and 94,578 bytes, were replaced the same
  day, before the founder used either: the first step now follows the
  founder's decision on removed comments, and the note on the schema
  follows the founder's answer.) The script read the file back and found
  each of the sixteen as it is in the repository, and the crate rebuilt
  from the file alone builds with no warnings, passes its 18 tests, and
  both demos' logs verify. The file isn't kept here: its code is under
  sketches/deepseek/012-09-05/chat-world, and its reply and steps are in
  docs/COLLABORATING.md ("2026-11-16, later still"), worded for the
  page. Not checked: that the whole file reaches DeepSeek; it ends with
  a line DeepSeek is asked to quote back.


> The next part: https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/parts/STATUS.md/log-03.md

> Part of `STATUS.md` in open-worlds, which is kept cut into parts
> for readers who are shown only the start of a long page.
> This part holds: "Log", piece 4 (its pieces are numbered from its end).
> Every part, in order: https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/parts/INDEX.md
> Before this part: https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/parts/STATUS.md/decided-by-the-technical-lead-01.md
> After this part: https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/parts/STATUS.md/log-03.md
> Made by docs/parts.py from the file. To change it, change the file.

## Log

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
  for removed comments) brought into line.

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
  tests for the first time: nothing fails; two things are noted, that
  the signs of the fifth test aren't written yet and no step writes
  them, and that whether a model that moderates is an individual hasn't
  been asked (Open questions). The day's ideas of the founder's are
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
    to be shown to one party alone); the records for the offices
    (Python and Rust agree on every vector of the five kinds step 3a
    added: `holds`, `held-by`, `person-list`, `proposal` and `vote`);
    the four formats moved to later steps (step 3a needed none of
    them); the plant world (the endless plant is a second world, with
    a crate of its own, as its "wrong if" asked);
  - not triggered: presence keys by HKDF (no tool has needed wallet
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
  - due at step 3c: DeepSeek's two questions (whether a room's
    signature on each record proves something a signed head can't) and
    one schema that fits both (whether a form the project has signed
    with is the worse one for rooms). The table of names in #98 already
    shows one place where the fitting has to split a kind (`Redact`),
    which "case by case" allows;
  - due earlier than written: reasons on record was due at step 6, and
    is first used at step 3b, where a moderator's removal is a decision
    record;
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
  - due at step 8a: who an individual and a world are, and decision 18,
    as before;
  - due at step 9: the sealed records, as before; and a link shown by
    an action, whose "wrong if" is a link that must be shown while the
    presence isn't in its world, which a birth that links the first
    presence may be;
  - not yet testable, since what they govern isn't built: sealing the
    world-key and sealing as built, the round table's consensus, how
    the table is chosen, a Keeper's self-report, ADMIN's council,
    ADMIN's learning by written lessons, the admin-key course, and the
    suggestion ledger;
  - not yet due: the template (step 4), and today's decision on the
    course's order.

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

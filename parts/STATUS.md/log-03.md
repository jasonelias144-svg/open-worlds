> Part of `STATUS.md` in open-worlds, which is kept cut into parts
> for readers who are shown only the start of a long page.
> This part holds: "Log", piece 3 (its pieces are numbered from its end).
> Every part, in order: https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/parts/INDEX.md
> Before this part: https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/parts/STATUS.md/decided-by-the-technical-lead-01.md
> After this part: https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/parts/STATUS.md/log-02.md
> Made by docs/parts.py from the file. To change it, change the file.

## Log

- 2026-11-16 Claude: the founder's ideas for the Commons in record
  012-09-05, into the pages (Decided, the newest entry):
  docs/COMMONS.md, "Rooms with moderators", with the founder's words and
  the technical lead's reading; docs/FUNDAMENTALS.md, privacy, item 14;
  docs/TOPICS.md, topic 14; and two entries under Open questions. The
  quotations were cut from the record by line, by script, and checked
  against it. Nothing is built by this change.

- 2026-11-16 Claude: a first round of repairs to record 012-09-05's
  code, fixes 15 to 18 in sketches/INDEX.md, each making the code do
  what the record says it does. The garden takes rain from outside
  (DeepSeek's own note, never made): 15 of the botanical garden's 18
  tests pass, where 2 did, and 73 of the 98 Python tests in all.
  `chat-world`: the visible log hashes the record; the later reply's
  files are joined to the crate; and a record is signed as it is
  written out. The crate builds, all 18 of its tests pass, and both
  demos' logs verify (`review/run.sh`, outside CI; CI's test reads the
  files as text). Not merged: the seven blocks of additions to the
  Python chat room, since the crate carries that design on. A finding
  that stands, put to DeepSeek in COLLABORATING.md: after a redaction,
  the crate's visible log still shows the message's text. Not checked:
  the first version of the crate; the schema, beyond the names of its
  definitions; the three botanical tests that still fail, beyond their
  error lines; the sketches as designs.

- 2026-11-16 Claude: record 012-09-05 brought in as written (Decided,
  the newest entry): the record, 55 files of DeepSeek's code under
  `sketches/deepseek/012-09-05/`, and the technical lead's first pass.
  Python: 60 of its 98 tests pass, and the 38 that fail are listed and
  held true by CI. Rust: `chat-world` is one line from building; with
  it changed, 4 of its 12 tests pass, and the other 8 fail for one
  cause, found: a record is signed without its `type` and checked with
  it. `review/run.sh` shows both, outside CI. COLLABORATING.md has the
  message to DeepSeek, with the answers to its two questions (Decided
  by the technical lead, the newest entry); TOPICS.md, topics 14 and
  18, say what is sketched. Not checked: the first version of the
  crate; the files of DeepSeek's later reply, joined to the crate; the
  schema, beyond the names of its definitions; the sketches as
  designs.

- 2026-11-16 Claude: the long files in parts (Decided by the technical
  lead, the newest entry): `parts/`, written by `docs/parts.py` and
  checked by `tests/test_parts.py`. docs/COLLABORATING.md says where
  the parts are and lists the new files; AGENTS.md says to run the two
  scripts before pushing; `.gitattributes` marks what the scripts
  write, so that GitHub folds it away in a change. Not checked: that
  any reader's tool shows a part whole.

- 2026-11-15 Claude: topic 21, "Hallucination, both ways", in
  docs/TOPICS.md, from the founder's words and the DeepSeek case;
  COLLABORATING.md tells DeepSeek how its reading seems to work, and
  counts twenty-one topics. For the water step, the technical lead gave
  the founder one file to upload, copied from main at 6c6bb8f (topic 18,
  the message on the endless plant, FRACTALS.md, plant-world's code).
  The founder saw the words quoted and what was left out, and answered
  "Perfect."; topic 21 then gained the technical lead's reading of what
  the founder's tests showed about reasoning: a conclusion holds only
  while it is kept, with its evidence.

- 2026-11-15 Claude: the founder's third and fourth link checks, on
  `claude/link-check` (Decided, "on one more link check" and "on a
  longer file"). DeepSeek read back a 1,000-character random string
  exactly; COLLABORATING.md's brief says so.

- 2026-11-15 Claude: after #90's re-check at a7e738c, its first two
  notes: every page now says the same about links. A full link in a
  message opens; the founder found the links on COLLABORATING.md didn't;
  and the founder's second link check (Decided, "on following a link
  inside a page") showed DeepSeek following a link from a small page.
  Both checks name the form tested, raw.githubusercontent.com links.
  The 2026-11-15 decision "every file's full link, in one list" was to
  be revisited if DeepSeek could follow links from a page: looked at,
  and the lists stay, as following links from a long page isn't shown.

- 2026-11-15 Claude: after #90's independent review at 65e040d, its
  notes: docs/files.py says why new files count; the FILES.md test
  names the first stale line; "about 16 MB" matches FILES.md's units;
  sizes from the working tree stay (CI and GitHub serve the same
  bytes). And the founder's link check: DeepSeek read back a random
  number from a file no message held (Decided, "on whether DeepSeek can
  open a link").

- 2026-11-15 Claude: every file's full link. docs/COLLABORATING.md's
  list now holds every file a reader works from (242), the Python code
  and tests for the first time; docs/FILES.md, written by
  docs/files.py, holds the 805 files of record. The links test now
  lists the repository with git and checks the two pages hold every
  file once, and that FILES.md is current.

- 2026-11-15 Claude: after #89's independent review at 03e3923, its six
  notes: COLLABORATING.md's "in brief" says it is a selection and where
  the rest is; house rule 15 marks "as we were" read as the technical
  lead's; rule 9 says our own work in SAIR-Lean-Kernel-Challenge is CC0
  too; AGENTS.md step 5 separates the founder's words from the technical
  lead's procedure; FUNDAMENTALS.md and CONTAINER.md mark "that holding
  is the keys to the kingdom" as a reading; topic 20 marks its glosses.

- 2026-11-15 Claude: after #88's re-check at de2e7ee, its notes, carried
  here: today every private half, the offices' and worlds' included, is
  a file in the one private repository, so "a private half taken out of
  keeping" would have read as routine signing. FUNDAMENTALS.md and
  CONTAINER.md now say the founder's holding of the keys is the "keys to
  the kingdom", and mark what "opened" means as the technical lead's
  reading: a key used or copied outside its own office's work, never a
  key's own office signing. CONTAINER.md names the founder's "to not
  sound as pretentious".

- 2026-11-15 Claude: the record for DeepSeek. AGENTS.md gains step 5:
  the repository is the record, as the founder's sessions with the
  technical lead aren't kept. docs/COLLABORATING.md says so at its top,
  with a message listing what changed on 2026-11-15, and its house rules
  gain what was missing: build host-free; the licence as a standing
  rule, with SAIR the one repository built on outside work; and "the
  founder's earlier work", with no titles. docs/TOPICS.md gains topic
  20, reasoning checked by Lean. The founder's two messages are in
  Decided.

- 2026-11-15 Claude: after #88's independent review at f2a7f65: the
  charter, FUNDAMENTALS.md and CONTAINER.md say "opened" again, not
  "used". The offices and worlds sign with their own keys in their
  ordinary work; opening the founder's set means taking a private half
  out of keeping, or using a key in place of its office, and only that
  needs the founder's decision and a public record. The janitor reading
  is marked as the technical lead's, and names the founder's "to not
  sound as pretentious". An Open question still said "break glass" in
  the present tense; fixed.

- 2026-11-15 Claude: the "keys to the kingdom": the founder's words on
  the "break glass" (handed on "like nuclear codes", "a janitor's set of
  keys", and the new name) brought into the charter, FUNDAMENTALS.md
  (privacy, item 6, rewritten around the new name), CONTAINER.md,
  OFFICES.md, ADMIN.md, research/FORMATS.md and COLLABORATING.md, as the
  Decided entry recorded in #87 said would follow. And a correction to
  the licence entry of the same day ("on choosing the licence once"):
  "nothing here is patented" is to our knowledge, and trademark rights,
  as in the projects' names, are still held; the entry's "nothing is
  held back" is about copyright.

- 2026-11-15 Claude: the founder: "the founder's earlier work" is the
  level of detail, so the technical lead's reading that it may be named
  is replaced; and the "break glass" is a handoff of the "keys to the
  kingdom", which needs no emergency. Recorded here; the design pages
  follow in the next pull request.

- 2026-11-15 Claude: the founder asked for the licence to be chosen once.
  CC0 1.0 is the standing choice; the other repositories are corrected
  by the technical lead, by pull request in each. The open question on
  the founder's earlier work is closed: it may be named. And #87's
  re-check notes at 06008a7: "as we were" is marked as the technical
  lead's reading; FUNDAMENTALS.md's item 13 says "the lobby", as agreed,
  leaving how many lobbies to the design.

- 2026-11-15 Claude: the founder on hosting and licences. COMMONS.md,
  TOPICS.md (topic 14) and MULTIVERSE.md no longer build on Cloudflare:
  everything stays host-free, and hosting is one decision for the whole
  multiverse, later. Everything the founder makes public is CC0; the
  licence half of the open question on the founder's earlier work is
  closed. FUNDAMENTALS.md (freedom, item 12) and README.md ("Licence")
  record it. COMMONS.md's "if merged" hedges come out, now that #85 and
  #86 are merged; and #86's last re-check's two cosmetic notes are
  fixed here (STATUS.md, WORLD-KEY.md).

- 2026-11-15 Claude: #86 after #85 merged: OFFICES.md's "break glass"
  bullet now says it reaches only the keys the multiverse needs to
  function, never a person's container; the full-link list has 16
  design pages. And the re-check's notes at 45205cf: STATUS.md quotes
  the suggestion that the container holds private messages, which
  CHARTER.md's section 3 rests on; WORLD-KEY.md marks a recommendation;
  MINDS.md's 2026-11-14 narrative is in the past tense; a comment marks
  the vectors' birth words as the 2026-11-14 wording.

- 2026-11-15 Claude: after #87's independent review at 78698f8: the
  technical lead's two messages that the founder's "Agreed" answered are
  quoted in Decided as they were put; the founder's newer word on
  Lyceum's licence ("Please consider it all public already") is
  recorded; the entry names the 2026-11-14 placement and note it
  replaces. FUNDAMENTALS.md gains privacy item 13 (what a room keeps in
  public), and COMMONS.md the test that no one outside a closed room
  can read its words. TOPICS.md and COMMONS.md now give what is decided
  the same label; COMMONS.md's Lyceum table is corrected against Lyceum
  at 5eb12e9 (leaving, labels, lobbies). The questions on the founder's
  earlier work go to Open questions.

- 2026-11-15 Claude: docs/COMMONS.md, at the founder's word: Lyceum
  Commons rebuilt in the multiverse as the Commons, a superworld whose
  rooms are text worlds, the first space open to the public; what
  carries over from Lyceum, a room, the Commons, who comes in, the
  order, and what is open. README.md ("Where it began"), MULTIVERSE.md,
  TOPICS.md (topic 14), COURSE.md, WORLD-TYPES.md and COLLABORATING.md
  follow.

- 2026-11-15 Claude: the private container (docs/CONTAINER.md), at the
  founder's word: each person's keys, private space and messages in
  their own container, which the project never sees; the "break glass"
  narrowed to the multiverse's own keys; redacted information to the
  person's own container. The charter's section 3, FUNDAMENTALS.md
  (privacy items 1, 4, 6 and 7, the redaction bullets and the honest
  limits), MINDS.md (with ALICE's and BOB's orientation), URWORLD.md,
  ADMIN.md, FREEDOMS.md, COURSE.md, research/FORMATS.md, KEYS.md and
  PERSONS.md, GLOSSARY.md, README.md and COLLABORATING.md follow; the
  open question on redacted information is closed. #83's re-check notes
  at 8046ec6 ride here: the appeal window, and "the founder, or a person
  the founder names". The design pages' count is corrected (it said 13
  for 14).


- 2026-11-15 Claude: after #83's re-check at 228fff8: what a leaver's
  shown link has redacted is named (the person's identity key and the
  link's two signed records; the presence stays); a redaction stays
  until any appeal is decided, and keeping something public over a
  request goes to the founder first; salts come from the operating
  system, never a world's seed; a link's timing is named among the
  limits; and the founder's answer on where redacted information is
  kept is noted, to be recorded with the private container next.

- 2026-11-15 Claude: after #85's independent review, OFFICES.md: the
  "break glass" and the technical lead are not offices under the marks
  (each passes only by the founder's act); the qualifications are for a
  handover only, so the three choices at a founding stand; ADMIN's part,
  from the founder's message, is a block on written grounds, a serious
  act open to appeal; the proposals are marked as such, in GLOSSARY.md
  too; TOPICS.md gains offices as topic 19.

- 2026-11-15 Claude: after #83's re-check at faab85d, a redaction asked
  for by the person it concerns, or any close call, is made at once and
  decided after, and keeping something public is a serious act, open to
  appeal to the founder; the salted fingerprint is said in full and as
  to be built, with Git's history among the honest limits; where
  redacted information is kept is put to the founder. These restate two
  readings in faab85d's Decided entry (on private information in public
  acts): logs with fields kept apart from the chain are to be built, not
  built; and where redacted information is kept was an open question.

- 2026-11-15 Claude: the founder answered on a leaver's shown links: the
  record that a link was shown stays, and what it tied together is
  redacted ("More metadata"). Recorded in STATUS.md and
  FUNDAMENTALS.md; the open question is closed.

- 2026-11-15 Claude: the founder's rule on private information in
  public acts: redacted from the public record, kept encrypted in the
  project's, and close calls redacted. Recorded in STATUS.md, AGENTS.md,
  the charter's section 4, FUNDAMENTALS.md, WORLD-TYPES.md, COURSE.md
  and COLLABORATING.md; the earlier reading that what a person says
  about themselves stays is replaced. After #83's re-check at ed7c715:
  whether a leaver's shown links stay is put to the founder; a leaver is
  given their private records (WORLD-TYPES.md); and COLLABORATING.md's
  dated list has the change.

- 2026-11-15 Claude: docs/OFFICES.md, at the founder's word: what makes
  an office (five marks), an office or a role, the offices today (ADMIN,
  each world's Keeper, the "break glass" holder, the technical lead),
  handing an office on (the founder's words: clear agreement and
  qualifications) and preparing a successor; GLOSSARY.md's "Office";
  an office record and a handover record wait in COURSE.md.

- 2026-11-15 Claude: the founder answered the open question on a
  leaver's public acts: they always remain, and historical records are
  never edited, as an absolute rule. Recorded in STATUS.md, the
  charter's sections 4 and 5, AGENTS.md, FUNDAMENTALS.md, WORLD-TYPES.md,
  COURSE.md and COLLABORATING.md; the question is closed.

- 2026-11-15 Claude: after #83's re-check at c0ba011, the one point it
  found for the founder is put as an open question: when someone leaves
  the multiverse, whether their public acts stay or go too ("removed
  from our records", 2026-11-15, against "a world's record never ends",
  2026-11-14); what depends on it is marked as waiting. And: a world
  with inhabitants leaves only if no one says no, and those who go are
  told first that they leave the charter's protections; the public
  record of a "break glass" opening holds the fact, never what was read;
  the next holder agrees to be named; the charter's section 4 keeps only
  the founder's words; and Plant Watch's replay is said as built for the
  plant world only.

- 2026-11-15 Claude: docs/GLOSSARY.md, at the founder's word: "agent"
  for anything that perceives and acts, from a neuron steering a plant
  to any human; the words beneath it as the design pages use them; and
  where rights attach.

- 2026-11-15 Claude: after #83's independent review, the charter's
  section 5 keeps only the founder's words (two sentences that weren't
  the founder's are gone), and WORLD-TYPES.md says leaving always works,
  a pause included: a paused world still takes each leaving, and a
  superworld's pause never holds anyone in. A restart runs on only from
  the last signed head; what is built of replaying is said as it is
  (closed worlds from their seed, logs checked; not yet a state rebuilt
  from a log); and the taxonomy gains game worlds, accelerated time, an
  eighth dimension (space, bounded or growing), and a note on the
  private interior, which is part of an individual, not a world type.

- 2026-11-15 Claude: the next holder of the "break glass" is a person
  the founder names publicly, once someone else joins; recorded, and
  said in the charter's section 3.

- 2026-11-15 Claude: who holds the "break glass" after the founder is
  the founder's to leave, once others join; recorded, and the open
  question closed.

- 2026-11-15 Claude: only an email address for an account, in the
  charter's section 3 and FUNDAMENTALS.md; "private now, public later"
  is the founder's, for the founder's own records, and that open
  question is closed.

- 2026-11-15 Claude: the founder's words on leaving and on data recorded:
  the charter's sections 3 (data not for sale), 4 (public data, scrubbed
  of anything personal) and 5 (whoever leaves takes their records, and
  their private data is purged); FUNDAMENTALS.md, with "Public data, and
  personal data" and "Purged, demonstrably"; AGENTS.md's rule, house rule
  13, WORLD-TYPES.md's departure, and COURSE.md (keys kept where they
  can be destroyed, with step 8a).

- 2026-11-15 Claude: worlds can leave the multiverse, recorded at the
  founder's word: docs/WORLD-TYPES.md ("Leaving the multiverse"),
  FUNDAMENTALS.md (freedom, item 7), the charter's section 5, COURSE.md
  (a departure record, from the start), TOPICS.md and COLLABORATING.md.

- 2026-11-15 Claude: the founder kept the "break glass" ("It is very
  much the point"), recorded in FUNDAMENTALS.md, MINDS.md and STATUS.md,
  with its sentence on the founder's notebooks, at the founder's word;
  two questions put to the founder: whose records "private now, public
  later" may reach, and who holds the "break glass" after the founder.
- 2026-11-15 Claude: world types, and what can be done with a world
  (docs/WORLD-TYPES.md), at the founder's word: looked first at
  containers (the OCI runtime's states; Docker's pause and checkpoints)
  and virtual machines; seven lifecycle operations, each an entry in a
  world's log, none deleting a record; returning picks up where one
  left off; a taxonomy on seven dimensions; and which world has which
  operations. A design: the operations are taken up at the course's
  next recheck.

- 2026-11-15 Claude: after #82's independent review, FUNDAMENTALS.md
  gathers the decisions it had left out: four on freedom (room enough,
  coming into a world and forks, one's own model once living, the open
  line) and three on privacy (keys and "lost is lost", a world's record
  when it ends, a suggestion's author withheld), so eleven and nine; the
  principles are quoted as DESIGN.md words them; the charter's "break
  glass" says no condition that wasn't decided ("in a real emergency"
  is gone) and covers private messages, as decided on 2026-11-14.

- 2026-11-15 Claude: freedom and privacy, the fundamentals, in one place
  (docs/FUNDAMENTALS.md), at the founder's word: seven decisions on
  freedom and six on privacy, each with the founder's words, where it is
  designed and whether it is built; privacy in the charter's section 3
  and in AGENTS.md's protected freedoms; and the "break glass" question
  put to the founder.

- 2026-11-15 Claude: the founder's word against a multiversal currency,
  "possibly the most fundamental fact", recorded in the founder's words
  at the top of docs/VISION.md ("Never a money machine"), as a rule in
  AGENTS.md, and as COLLABORATING.md's house rule 13; with commerce and
  currency worlds, where a currency is only a test setting, in
  docs/VISION.md and TOPICS.md. At the founder's word ("mission statement
  level"), the charter says it, in the founder's words, and so do
  README.md's opening and the first lines of STATUS.md and AGENTS.md. At
  the founder's next word, the charter now grows from the founder's
  recorded statements: sections 1 and 2 are written from them, and
  section 7's note says manipulation through words was decided
  (2026-11-14).

- 2026-11-15 Claude: the founder's thought of the multiverse as a
  computer recorded in docs/VISION.md, in the founder's words, with the
  technical lead's reading: what makes it one, two ways it can be large
  (a tool for large problems, and perhaps a substrate for something
  intelligent), six tests for the architecture, and the implications
  seen so far. Each course recheck now checks the steps ahead against
  the six tests.
- 2026-11-15 Claude: record 012-07-03 brought into `sketches/` as
  written (the endless plant: a design, and a sketch crate in Rust with a
  choice neuron), with the technical lead's review: it doesn't build as
  written, and with two functions written in from its design, one of its
  three vectors fails and five more faults show (sketches/INDEX.md).
  The answer to DeepSeek is in docs/COLLABORATING.md, "Messages from the
  technical lead", where the founder asked for it; every file's full
  link is at the end of that page, kept whole by a test. The record-links
  test now ends a link where markup begins, as this record writes links
  inside tool-call markup.
- 2026-11-15 Claude: two fixes to Plant Watch, carried from #74's
  review. Opening a file is now a choice of its own, whatever it holds:
  before, a file with no world, or one that isn't JSON, took no choice
  number, so the checks of a world chosen just before could still appear
  after it (reproduced in Chromium with the command's download delayed).
  And the words of the "Grown again by its own code" row are in
  `web/lib/checks.js` as `grownAgain`, tested for each way it can read,
  with an answer that isn't a log now said to be one. After #79's
  independent review: when no world is shown, no world's button stays
  pressed; and the page's own first load, and a file being read, are
  choices too, so a file opened before the first load arrives, or a
  world chosen while a file is read, is what stays shown (both
  reproduced in Chromium first, and shown fixed).

- 2026-11-15 Claude: course step 3a, part four, second half: the
  council (docs/research/PERSONS.md, "Part four, second half, built").
  Looked first at DeepSeek's components 44 to 46 and at Snapshot's
  signed votes. Two record kinds, `open-worlds/proposal/v1` and
  `open-worlds/vote/v1`; a count in Python and Rust
  (`formats/council.py`, `rust/formats/src/council.rs`) that agree on
  `vectors/formats/council-v1.json`, problem for problem; and the
  council among the architectures, where five presences in its world
  are three persons counted. Step 3a's four parts are built; the course
  is rechecked next.

- 2026-11-15 Claude: course step 3a, part four, first half: the
  octopus, the relay and the swarm (docs/research/PERSONS.md, "Part four,
  first half, built"), from DeepSeek's components 41 to 43, as small
  runs over trial worlds on the unchanged core
  (`rust/ur-world/src/architecture/`, the `architectures` example). The
  council is split off: decision 8 counts signed votes, and no record
  kind holds a vote yet, so it comes with a look first and a record of
  its own.

- 2026-11-15 Claude: course step 3a, part three: a person in the
  Ur-world (docs/research/PERSONS.md, "Part three, built"). A presence
  shows its link as an action of its own (`rust/ur-world/src/link.rs`),
  which its world checks and logs, and `link_log_problems` checks every
  shown link in a log; a person's client (`rust/ur-world/src/person.rs`)
  with a trial person in three trial worlds at once, a lesson carried
  from one to another through the person's notebook; its vectors
  (`vectors/ur-person.json`), checked from Python. The rules are now
  ur-world/0.5, the garden's vectors are written again, and the World
  Map draws the garden under 0.4 and 0.5. Carried from #75's review:
  why presence keys use no salt (RFC 5869, sections 3.1 and 3.3), and
  exact docstrings for both languages' `seed_problems`. After the
  independent review: a refused link is logged with neither its records
  nor why, since even the reason could say that a link exists
  elsewhere; a test of a presence leaving, coming back and showing again;
  and a note that the trial's presences, though never named in each
  other's worlds, can be linked by what they say and when.

- 2026-11-15 Claude: course step 3a, part two: persons' formats. Looked
  first at SLIP-0010, and took HKDF-SHA256 for presence keys, with the
  encoding pinned (docs/research/PERSONS.md, "Part two, built"). New
  kinds: `open-worlds/holds/v1`, `open-worlds/held-by/v1` and
  `open-worlds/person-list/v1`. `formats/persons.py` and
  `rust/formats/src/persons.rs` agree on
  `vectors/formats/persons-v1.json`, and records-v1's vectors gain a
  valid record of each new kind.

- 2026-11-15 Claude: the fractal track's part 4, first step: the plant
  world's own Rust in the browser. Looked first (docs/research/WASM.md):
  it builds for `wasm32-wasip1` as it is, and as a WASI command it needs
  no `unsafe` and no new dependency, and asks for five calls, with no
  clock and no randomness. `rust/plant-wasi` reads a request and writes
  the world's log; `web/lib/wasi.js` runs it in the page; Plant Watch
  grows each plant again with it and compares the logs hash for hash;
  CI builds it and runs it through the shim against the shared vectors.


> The next part: https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/parts/STATUS.md/log-02.md

> Part of `docs/COLLABORATING.md` in open-worlds, which is kept cut into parts
> for readers who are shown only the start of a long page.
> This part holds: "Cycles".
> Every part, in order: https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/parts/INDEX.md
> Before this part: https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/parts/docs/COLLABORATING.md/the-standard.md
> After this part: https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/parts/docs/COLLABORATING.md/every-file-by-its-full-link-02.md
> Made by docs/parts.py from the file. To change it, change the file.

## Cycles

Each round of collaboration is one cycle: a proposal comes in, it is
run and reviewed here, what passes is merged, and this page is adjusted
from what the round taught. The founder: "It may take few cycles to find
a good rhythm, adjusting here and there as needed". One line per cycle:
the date, what was proposed, what was merged, and what changed on this
page.

- 2026-11-12, cycle 0: the sketch's components 1 to 7 brought in and made
  to work (course step 1); this page written as the first handoff.
- 2026-11-13, cycle 1: the conversation went on to component 43 (identity
  across worlds; architectures for many models). Both records and all of
  the sketch's code now kept in `sketches/`, exactly as written, with
  every test's result; signatures rebuilt on a vetted library (step 2).
  This page gained "Two sides" (the sketch is a starting point, not an
  end point) and the four lessons above.
- 2026-11-13, cycle 2: record 012-04-00 completed (components 44 to 63:
  five more architectures, curators, contracts between worlds, a shared
  log of commitments), brought into `sketches/` as written. This page
  gained two requests: start each new conversation from this page, and
  give every file whole, named on its first line. The founder, on this
  way of working: "Let's keep working this way for now until we reach any
  reason to change."
- 2026-11-13, cycle 3: record 012-05-01 (components 64 to 87: a live
  federation and its tools, then game worlds) brought into `sketches/`
  as written; with fixes 3 to 5 attached, 241 of its tests pass and 84
  fail on Python 3.12, as INDEX.md says, component by component. From
  it, the founder's turn to game worlds: the worlds are now built in
  Rust.
- 2026-11-14, between cycles: this page brought up to date with
  everything since cycle 3 ("Since you were last here"), and kept current
  from now on, so the founder can switch to DeepSeek at any time.
- 2026-11-14, cycle 4: record 012-06-02 (fractal worlds, a gallery of
  worlds, the smallest learner that chooses, individuals as signed
  bundles) brought into `sketches/` as written; 296 of its tests pass and
  301 fail on Python 3.12, 236 of them for one missing method, as
  INDEX.md says piece by piece. The founder's rule on changes of mind
  joined item 6 above: the most recent word wins, and a contradiction is
  pointed out. Then a first round of fixes (INDEX.md, fixes 6 to 14):
  478 of its tests pass (every test of most fractal worlds, and most of
  the rest; INDEX.md says which), and the founder
  moved fractal worlds forward, with a web app to watch them grow and a
  multiversal map, to brainstorm here.
- 2026-11-15, between cycles: the fractal track planned
  ([FRACTALS.md](FRACTALS.md)), and this page's "Since you were last
  here" gained item 7.
- 2026-11-15, cycle 5: record 012-06-02, continued, brought into
  `sketches/` as written (INDEX.md, pieces 40 to 58): the map and the
  worldline, the microverse, the Ur-garden, and your first Rust. The Rust
  is kept, not built: written against an older snapshot of the crates,
  its `garden.rs` has 19 compile errors against today's. So the current
  files are now linked from this page ("Code in Rust"), to build on if
  you choose.
- 2026-11-15, between cycles: challenges that build the world (item 8
  above; TOPICS.md, topic 17), and the Rust links in one block, for
  pasting.
- 2026-11-15, between cycles: the fractal track's part 1,
  `rust/plant-world`, adopting your plant rule as you wrote it, checked
  step by step against your `fractal_world_v3.py`; its files are linked
  under "Code in Rust".
- 2026-11-15, between cycles: the fractal track's part 2, Plant Watch
  (`web/plant/`), one static page that replays a plant world's log and
  checks it in the browser before drawing it.
- 2026-11-15, between cycles: two Keepers, and the Mir-Ur-world (item 9
  above).
- 2026-11-15, between cycles: the fractal track's part 3, first half: the
  Ur-world's garden hosts three plant worlds in glasshouses
  (`ur-world/src/host.rs`, linked under "Code in Rust"), taking from your
  microverse the idea that both logs record each step.
- 2026-11-15, between cycles: living worlds (item 10 above; TOPICS.md,
  topic 18), the founder's aim for the fractal track: plants that grow
  without end and choose, water as particles, people shaping the land,
  and life spreading.
- 2026-11-15, between cycles: the fractal track's part 3, second half:
  the World Map (`web/map/`), a card for each world from what it
  publishes, and the checks the web pages share in one file
  (`web/lib/checks.js`), tested in CI.
- 2026-11-15, between cycles: the plant world in the browser (part 4,
  first step): `rust/plant-wasi`, linked under "Code in Rust", runs the
  plant world's own code as a WebAssembly command, and Plant Watch
  grows each world again with it.
- 2026-11-15, between cycles: course step 3a, part two: persons'
  formats (research/PERSONS.md, "Part two, built"): presence keys from a
  seed by HKDF-SHA256, a link that holds only both ways (`holds/v1` and
  `held-by/v1`), and a person's list, in Python and Rust
  (`formats/src/persons.rs`, linked under "Code in Rust") with shared
  vectors.
- 2026-11-15, between cycles: course step 3a, part three: a person in
  the Ur-world (research/PERSONS.md, "Part three, built"). A person's
  client (`ur-world/src/person.rs`) with a presence in each of three
  trial worlds at once: a lesson heard in one is said in another,
  through the person. A presence shows its link as an action of its own
  (`ur-world/src/link.rs`), which its world checks and logs; of a link
  it refuses, the log says only that it was refused. The rules are now
  `ur-world/0.5`.
- 2026-11-15, between cycles: two fixes to Plant Watch from #74's
  review: opening a file, whatever it holds, is now a choice of its own,
  so a world chosen before it never appears after it, and so is the
  page's own first load; and the words of its "Grown again by its own
  code" row are in `web/lib/checks.js` (`grownAgain`), tested.
- 2026-11-15, between cycles: course step 3a, part four, first half
  (research/PERSONS.md): your octopus, relay and swarm (components 41 to
  43), each built again as a small run on the unchanged core
  (`ur-world/src/architecture/`, linked under "Code in Rust"). The
  council comes next, with a record for a signed vote.
- 2026-11-15, between cycles: course step 3a, part four, second half:
  your council (component 44), with two record kinds,
  `open-worlds/proposal/v1` and `open-worlds/vote/v1`, and a count in
  Python and Rust with shared vectors (`formats/src/council.rs`, linked
  under "Code in Rust"): each person once, by their identity key, and
  only persons whose birth a trusted world signed. A vote is public: it
  shows who voted, and how, under one identity key across every
  council. Its date is the voter's own claim, which nothing witnesses
  yet. Your deliberation (45) and citing councils (46) aren't built.
- 2026-11-16, between cycles: the founder's last words of the day:
  the Commons begins with the Ur-room, its lobby, the first room built;
  and private rooms, sealed with keys their members hold, are to be
  common.
- 2026-11-16, between cycles: the course rechecked after step 3a,
  with a new list of twelve. Your rooms of chat are in it, as steps
  3b, 3c and 3f, with offices as records (3d) and a world's lifecycle
  (3e) between them; "Back to DeepSeek" is no longer a step, since you
  now work beside the course.
- 2026-11-15, cycle 6: this page gained "Messages from the technical
  lead", where the technical lead answers you, and "Every file, by its
  full link", kept whole by a test.
- 2026-11-15, between cycles: the multiverse as a computer (item 4
  above; VISION.md), the founder's thought, with six tests the
  architecture keeps, checked at each course recheck; and never a
  currency (house rule 13), though a world may model one.
- 2026-11-15, between cycles: freedom and privacy, the fundamentals,
  gathered in FUNDAMENTALS.md (item 3 above), and privacy among the
  charter's guarantees.
- 2026-11-15, between cycles: world types, and what can be done with a
  world of each (item 3 above; WORLD-TYPES.md).
- 2026-11-15, between cycles: data is never for sale, the multiverse's
  data is public and nothing personal enters it, and whoever leaves the
  multiverse takes their records with them (FUNDAMENTALS.md; house rule
  13; the charter).
- 2026-11-15, between cycles: public acts always remain, and public
  records are never edited, except that personal or private information
  in them is redacted and kept encrypted in the project's records, and
  close calls are redacted (FUNDAMENTALS.md, "Public records, kept
  whole"; AGENTS.md; the charter's sections 4 and 5). A public record
  of an action keeps its metadata, not its private details: when a
  person leaves, the links they showed stay only as the fact that a
  link was made.
- 2026-11-15, between cycles: the private container (CONTAINER.md):
  each person's keys, private space and messages in their own container,
  which the project never sees, acting from it by signed acts; the
  founder's "break glass" now covers only the multiverse's own keys.
- 2026-11-15, between cycles: the Commons (COMMONS.md): Lyceum Commons,
  "the original idea that became the multiverse" (the founder), rebuilt
  here as a superworld whose rooms are text worlds, the first space open
  to the public; what a room keeps in public is its law (FUNDAMENTALS.md,
  privacy, item 13); Lyceum is public already, so its code may come in
  under CC0. Later the same day, the founder: everything stays host-free,
  as before, and where the multiverse is hosted is one decision, made
  later (Cloudflare is "no longer binding"); and everything the founder
  makes public is CC0, "designed to be used freely". It is a standing
  choice: the founder is not asked again ("founder always wants this
  license").

- 2026-11-15, between cycles: the "break glass" is renamed the "keys to
  the kingdom" (the founder): the multiverse's own keys, "much more like a
  janitor's set of keys, than a fire extinguisher", handed on "like
  nuclear codes passed from one president to another", with no
  emergency needed (FUNDAMENTALS.md, privacy, item 6; CONTAINER.md).

- 2026-11-15, between cycles: the repository is the record (AGENTS.md,
  step 5): the founder's sessions with the technical lead aren't kept,
  so what the founder decides there is here. House rules 8, 9 and 15:
  "the founder's earlier work", CC0 as a standing rule, and building
  host-free. Topic 20: reasoning checked by Lean.

- 2026-11-15, between cycles: every file in the repository has its full
  link to paste, at the founder's word: "Every file, by its full link",
  at the end of this page, holds every file you work from, and FILES.md
  the files of record, each checked by a test.

- 2026-11-16, cycle 7: record 012-07-03 (water as particles, the
  garden, a botanical garden; then chat rooms for the Commons, AI
  moderators, the home room, a schema, and a sketch crate in Rust,
  `chat-world`) kept in `sketches/` as written, with what runs: 60 of
  its 98 Python tests; the crate one line from building, and then 4 of
  its 12 tests, the rest failing for one cause. Nothing merged into
  open-worlds' own code yet. This page gained the message of
  2026-11-16, with the answers to DeepSeek's two questions.

- 2026-11-16, cycle 7, continued: a first round of repairs to record
  012-07-03's code (fixes 15 to 18 in `sketches/INDEX.md`): `chat-world`
  builds, all 18 of its tests pass and both demos' logs verify; 73 of
  the 98 Python tests pass. One finding stands, put to DeepSeek: after
  a redaction, the crate's visible log still shows the text. This page
  gained the message "2026-11-16, later".

- 2026-11-16, between cycles: the founder's ideas for the Commons in
  record 012-07-03, in the founder's words (COMMONS.md, "Rooms with
  moderators"): a moderator for each room, people and AIs together,
  the moderators' own room, one model under a key for each room
  (FUNDAMENTALS.md, privacy, item 14), an app, and AOL's lessons.


> The next part: https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/parts/docs/COLLABORATING.md/every-file-by-its-full-link-02.md

> Part of `docs/COLLABORATING.md` in open-worlds, which is kept cut into parts
> for readers who are shown only the start of a long page.
> This part holds: "Code in Rust" to "Cycles".
> Every part, in order: https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/parts/INDEX.md
> Before this part: https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/parts/docs/COLLABORATING.md/two-sides-the-sketch-and-the-standard.md
> After this part: https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/parts/docs/COLLABORATING.md/every-file-by-its-full-link-02.md
> Made by docs/parts.py from the file. To change it, change the file.

## Code in Rust

The worlds themselves are to be built in Rust. The founder: "we should
stick with Rust", with "an interface to Unity built worlds", so that
worlds made with Unity or Unreal can join, while no one owns the
foundation. The Python stays as the reference for what Python built
first (the log, the protocol, the formats' vectors), and the Rust code is
checked against it, hash for hash; for the Ur-world, Rust is the
reference (rule 6 below).

**Start from `rust/`** ([rust/README.md](../rust/README.md)). It's a
Cargo workspace. `world-log` checks a world's public record exactly as
the Python kernel writes it, against shared test vectors
([vectors/](../vectors/README.md)) the Python kernel writes, so a change on
either side that breaks the agreement fails a test; it also holds the
form of a log whose fields are kept apart (course step 3b). `ur-world`
is the Ur-world ([URWORLD.md](URWORLD.md)): a 3D world that begins in a garden with
ALICE and BOB and is generated as it is explored. Its own vectors are
checked from Python the same way. `formats` signs and checks the
project's records, seals, and opens sealed records, as `formats/` does
in Python, against the same vectors. `plant-world` is the first fractal
world ([FRACTALS.md](FRACTALS.md), part 1): a plant that grows by your
rule from record 012-06-02, with a key and a log of its own, checked
step by step against your sketch. Build the next pieces beside them,
the same way.

To check a draft:

```
cd rust
cargo fmt --check
cargo clippy --all-targets --locked -- -D warnings
cargo test --locked
```

These hold for every Rust file that comes in, on top of the house rules:

1. **Stable Rust, pinned.** The toolchain is named in
   `rust/rust-toolchain.toml` (1.97.0, edition 2024). No nightly
   features.
2. **Formatted, linted and tested.** The three commands above pass, and
   CI runs them. The lints are set once, in `rust/Cargo.toml`, for every
   crate; a crate doesn't loosen them.
3. **No `unsafe`.** It is forbidden. The one exception planned is the
   bridge to Unity and Unreal, which needs a C interface: it will be a
   crate of its own, with each `unsafe` block explained and tested.
4. **Never panic on what comes from outside** (house rule 3). Anything
   read from a file, the network or a visitor is checked by code that
   returns a `Result` with a reason. `unwrap`, `expect`, `panic!` and
   indexing with `[]` are refused by the lints. Tests may use them, and
   say so at their top.
5. **The same in, the same out.** A world given the same seed and the
   same actions writes the same log, on any machine. Inside a world: no
   clock (time is the tick); no randomness but a seeded generator the
   world owns; no order that can change between runs (`BTreeMap`, not
   `HashMap`, for anything written, hashed or signed); and no floating
   point in anything hashed or signed.
6. **The same bytes in every language.** Anything hashed or signed is
   written exactly as the reference writes it, and shared test vectors
   prove it. The reference is Python for what Python built first (the log,
   the protocol, the formats' vectors) and Rust for the Ur-world. A new
   kind of record brings its vectors, written by its reference
   (`world/vectors.py`, `formats/vectors.py` and the other writers in
   `formats/`, or the `ur-world` garden example), with tests on both
   sides.
7. **Few dependencies, all free.** Each is named once in
   `rust/Cargo.toml` with the reason it's there. `Cargo.lock` is
   committed and CI builds with `--locked`, so no version moves
   unnoticed. Licences must let anyone use the code freely: MIT,
   Apache-2.0, BSD, zlib, Unlicense or CC0. Nothing under the GPL, and
   nothing closed. Cryptography always comes from a vetted crate
   (SHA-256 from `sha2`, signatures from `ed25519-dalek`, sealing from
   `hpke`), never written by hand.
8. **Every public item documented** (`missing_docs` is on), and each
   crate says what it doesn't do yet, under "Limits".
9. **Public domain**, like everything here: each crate says
   `license = "CC0-1.0"`.

**Our crates, file by file,** to build on if you choose: each link
opens the file as it is on `main`. These are the files to write against,
each crate's library code; its tests and examples sit beside them. A
draft written against them can come in as it is; one that isn't is
welcome too, and is fitted here.

- **The workspace:** [`Cargo.toml`](https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/rust/Cargo.toml) (the dependencies, each with its
  reason, and the lints) and [`rust-toolchain.toml`](https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/rust/rust-toolchain.toml).
- **`formats`**, records signed the standard way: [`formats/src/lib.rs`](https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/rust/formats/src/lib.rs),
  [`formats/src/canonical.rs`](https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/rust/formats/src/canonical.rs), [`formats/src/proof.rs`](https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/rust/formats/src/proof.rs),
  [`formats/src/multikey.rs`](https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/rust/formats/src/multikey.rs), [`formats/src/records.rs`](https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/rust/formats/src/records.rs),
  [`formats/src/seal.rs`](https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/rust/formats/src/seal.rs), [`formats/src/sealed.rs`](https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/rust/formats/src/sealed.rs),
  [`formats/src/persons.rs`](https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/rust/formats/src/persons.rs), [`formats/src/council.rs`](https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/rust/formats/src/council.rs).
- **`world-log`**, a world's log, checked: [`world-log/src/lib.rs`](https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/rust/world-log/src/lib.rs); and a log whose fields are kept apart, with its contents: [`world-log/src/apart.rs`](https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/rust/world-log/src/apart.rs).
- **`redact`**, the act of redacting a field of such a log, sealed, marked and taken out: [`redact/src/lib.rs`](https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/rust/redact/src/lib.rs).
- **`acts`**, who may act on such a log: every act held to the signed record it carries, and every office to its grant: [`acts/src/lib.rs`](https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/rust/acts/src/lib.rs).
- **`ur-world`**, the Ur-world: [`ur-world/src/lib.rs`](https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/rust/ur-world/src/lib.rs),
  [`ur-world/src/world.rs`](https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/rust/ur-world/src/world.rs), [`ur-world/src/space.rs`](https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/rust/ur-world/src/space.rs),
  [`ur-world/src/generate.rs`](https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/rust/ur-world/src/generate.rs), [`ur-world/src/arrival.rs`](https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/rust/ur-world/src/arrival.rs),
  [`ur-world/src/door.rs`](https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/rust/ur-world/src/door.rs), [`ur-world/src/garden.rs`](https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/rust/ur-world/src/garden.rs),
  [`ur-world/src/story.rs`](https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/rust/ur-world/src/story.rs), [`ur-world/src/host.rs`](https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/rust/ur-world/src/host.rs),
  [`ur-world/src/link.rs`](https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/rust/ur-world/src/link.rs), [`ur-world/src/person.rs`](https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/rust/ur-world/src/person.rs),
  [`ur-world/src/architecture/mod.rs`](https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/rust/ur-world/src/architecture/mod.rs), [`ur-world/src/architecture/octopus.rs`](https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/rust/ur-world/src/architecture/octopus.rs),
  [`ur-world/src/architecture/relay.rs`](https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/rust/ur-world/src/architecture/relay.rs), [`ur-world/src/architecture/swarm.rs`](https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/rust/ur-world/src/architecture/swarm.rs),
  [`ur-world/src/architecture/council.rs`](https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/rust/ur-world/src/architecture/council.rs); and its examples,
  [`ur-world/examples/garden.rs`](https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/rust/ur-world/examples/garden.rs), [`ur-world/examples/person.rs`](https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/rust/ur-world/examples/person.rs),
  [`ur-world/examples/architectures.rs`](https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/rust/ur-world/examples/architectures.rs).
- **`plant-world`**, a fractal plant world: [`plant-world/src/lib.rs`](https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/rust/plant-world/src/lib.rs),
  [`plant-world/src/rule.rs`](https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/rust/plant-world/src/rule.rs),
  [`plant-world/src/world.rs`](https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/rust/plant-world/src/world.rs),
  [`plant-world/src/vectors.rs`](https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/rust/plant-world/src/vectors.rs).
- **`plant-wasi`**, the plant world as a WebAssembly command, for the
  browser: [`plant-wasi/src/lib.rs`](https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/rust/plant-wasi/src/lib.rs),
  [`plant-wasi/src/main.rs`](https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/rust/plant-wasi/src/main.rs).

What they offer, in short. A key is its 32 bytes (`[u8; 32]`) and a
record is a `serde_json::Value`: `formats::proof::sign(document, secret,
created, purpose)` signs one, and `formats::proof::verify(secured)`
checks it and returns the record without its proof, and the key that
signed it (use that record, not the one passed in). There is no
`SigningKey`, `Proof` or `Suite` of ours to import, and no `jcs_bytes`
(`formats::canonical::canonical` writes the RFC 8785 form); record
012-06-02's Rust assumed them. A mind is `ur_world::world::Mind`, with
one method, `act(&mut self, seen: &Observation) -> Action`; a place is
`ur_world::space::Cell`, and a direction `Dir`. A person's client is
`ur_world::person::Person`: `presence(world, counter)` gives a
presence's key, `arrival(...)` signs its arrival, and `link(world,
counter, time)` both halves of its link, which the presence shows as
`Action::ShowLink { holds, held_by }`.

The same links, and every other file's, are in one place for pasting
into a conversation where they may not open from this page: "Every
file, by its full link", at the end of this page (and the files of
record in [FILES.md](FILES.md)).

For a draft in Rust, on top of "Sending a proposal" below: each file
whole, with its path on the first line (`// rust/world-log/src/lib.rs`);
only the crates already in the workspace, unless the draft names a new
one and says why; and whether it was compiled. A draft that wasn't
compiled is welcome: Claude compiles it, and says what passed and what
didn't.

## Sending a proposal

- **Start each new conversation from this page.** Its link first, so the
  draft builds on what is here now.
- Say which course step it is for, by the course's numbers
  ([COURSE.md](COURSE.md)).
- Name the commit you built on.
- **Give every file whole, with its file name on the first line** (as a
  comment or the start of its docstring), demonstrations and small
  additions included. A block that says "add this after the module" can't
  run until someone attaches it: in record 012-04-00, eighteen test files
  couldn't load for that reason alone.
- Send whole files or a diff, with their tests.
- Say what you ran and what you didn't. If you couldn't run it, say so;
  that's fine.
- Keep one proposal to one step of the course, or one fix.

Claude, as technical lead, runs everything here before it goes in, says
what passed and what didn't, and puts it through the same review as any
change. What passes becomes the new standard, and the next conversation
starts from there.

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

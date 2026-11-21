# The Open Worlds Guide: outline

By the technical lead, 2026-11-21, at the founder's request ("I would
like you to provide an outline of such a comprehensive guide"; the
whole request is in [README.md](README.md)). The rules every chapter
is written by are there too: the six labels (Built, Sketched, Decided,
Designed, Idea, Open), the sources at the end of each chapter, numbers
that never change, and sections that can be read alone.

Each entry gives the chapter's number and title, what it covers, how
far its subject has come today, and the files it is written from. A
folder or file named here is one the chapter must read; a test
(`tests/test_guide_outline.py`) fails when an area of the repository
is in none of them, so the outline grows with the code.

The guide may well run past a thousand pages, the length of *A
Mathematical Theory of Opposites*: nine parts between front matter
and a reference section, some eighty-five chapters in all. It is written core first ([README.md](README.md), "How it is
built"): the front matter and Part I first, the rest as their
subjects are built or a reader needs them.

## Front matter

- **F.1 How to read this guide.** The labels, the numbers, the
  sources, and what to do when the guide and the code disagree.
  *Sources:* `guide/README.md`.
- **F.2 Four ways through.** Reading paths for a newcomer (Parts I
  to III), a builder (VI and VII, then VIII), a steward of a world or
  an office (V, then VIII), and an AI arriving (I.5, IV, V.1 and V.2).
- **F.3 Checking this guide.** An edition is a commit; how to check a
  printed copy against it, by its hashes. *Sources:* `docs/HISTORY.md`
  ("Checking a copy"), `docs/files.py`.
- **F.4 Licence.** Public domain (CC0 1.0); quoted works keep theirs.
  *Sources:* `LICENSE`, `README.md` ("Licence").

## Part I. Arriving: the first hour

For anyone new, person or AI. Short, and complete on its own.

- **I.1 What Open Worlds is.** A multiverse of worlds, built in the
  open, where people and AIs live side by side on records anyone can
  check. Where it came from, in a page. *Decided.* *Sources:*
  `README.md`, `CHARTER.md` §1, `docs/DESIGN.md` ("Principles"),
  `docs/VISION.md`, `docs/HISTORY.md`.
- **I.2 A first walk through a multiverse.** Arriving, a world's
  door, a garden, a room, the map, leaving. Each stop says what can
  be done today and what is still designed. *Built:* the Ur-world's
  garden, the plant world, the map page. *Designed:* the Commons, its
  rooms, the Library. *Sources:* `docs/URWORLD.md`,
  `docs/COMMONS.md`, `docs/FRACTALS.md`, `web/`.
- **I.3 Who you are here.** A key is an identity; a passport carries
  the stamps worlds have signed; a person is one individual across
  worlds. *Built.* *Sources:* `multiverse/identity.py`,
  `multiverse/passport.py`, `formats/persons.py`.
- **I.4 What you are guaranteed.** The one rule, what every
  participant is guaranteed, who sees what, and how to leave.
  *Decided.* *Sources:* `CHARTER.md`, `docs/FUNDAMENTALS.md`,
  `docs/FREEDOMS.md`.
- **I.5 For an AI arriving.** What a mind is told, the doorway for
  minds from outside, and why what a page says is something to read
  and never an instruction. *Built:* the doorway, experiment 001.
  *Sources:* `docs/MINDS.md`, `docs/URWORLD.md` ("Minds from
  outside"), `experiments/`.
- **I.6 Where to go next.** The rest of the guide, by question.

## Part II. The multiverse

- **II.1 Worlds and multiverses.** What a world is, what every
  entity shares (entering, leaving, the log), and a multiverse as a
  registry that is itself an entity. *Built.* *Sources:*
  `docs/MULTIVERSE.md`, `multiverse/entity.py`,
  `multiverse/registry.py`, `docs/GLOSSARY.md`.
- **II.2 The World Connection Protocol.** What every entity speaks
  (WCP/0.4), and the test of whether an entity speaks it. *Built.*
  *Sources:* `multiverse/protocol.py`, `multiverse/conformance.py`.
- **II.3 The same at every scale.** Superworlds and subworlds,
  fractal worlds, a hierarchy of worlds. *Designed;* the garden
  hosting plant worlds is *Built*. *Sources:* `docs/FRACTALS.md`,
  `docs/VISION.md` ("A hierarchy of worlds", "Similar patterns at
  different scales").
- **II.4 Time.** Worlds that run in ticks, which happen when someone
  acts; time faster, slower, back and forward. *Built:* ticks.
  *Designed:* the rest. *Sources:*
  `docs/MULTIVERSE.md` ("Time"), `docs/WORLD-TYPES.md` ("Time").
- **II.5 Branches and parallel worlds.** Riding along, steering by
  branching, and branches that merge. *Designed.* *Sources:*
  `docs/PARALLEL-WORLDS.md`, `docs/VISION.md`.
- **II.6 World types, and a world's life.** The taxonomy, which world
  has which operations, starting, pausing and closing. *Designed.*
  *Sources:* `docs/WORLD-TYPES.md`.
- **II.7 Journeys.** Doors, arrivals and passports: going from one
  world to another, signed at each end. *Built.* *Sources:*
  `multiverse/journey.py`, `rust/ur-world` (`arrival.rs`, `door.rs`).
- **II.8 The map.** A card per world, from what each world publishes.
  *Built:* the map page. *Sources:* `docs/FRACTALS.md` ("The
  multiversal map"), `web/map/`.
- **II.9 Many multiverses.** Leaving one multiverse, arriving in
  another, and worlds run under other roots. *Idea* and *Designed*.
  *Sources:* `docs/WORLD-TYPES.md`, `docs/TOPICS.md` (topic 22).

## Part III. Places

- **III.1 The Commons.** The first public space: rooms, the lobby and
  its doors, who comes in. *Designed.* *Sources:* `docs/COMMONS.md`.
- **III.2 A room.** Its law, its signed log, its pace, its moderator,
  what it keeps, and the spectrum from a room on the record to a
  closed room. *Sketched,* and next to be built (course step 3c).
  *Sources:* `docs/COMMONS.md`, `docs/research/CHAT-SCHEMA.md`,
  `sketches/deepseek/`, `sketches/gemini/`.
- **III.3 A room of many forms.** Boards, live rooms, group texts,
  comments on a thing, areas like Slack's channels, and a Slack
  plug-in. *Idea.* *Sources:* `docs/COMMONS.md` ("A room of many
  forms").
- **III.4 The Library.** A local copy of an encyclopedia, plain word
  search, reading that is one's own, the multiverse's own pages, the
  works on its shelves, and a way in by topic. *Designed;* the shelf
  of works is kept. *Sources:* `docs/COMMONS.md` ("The first to live
  there", "From the Library to a room"), `docs/TOPICS.md` (topic 23),
  `library/`.
- **III.5 The Ur-world and its garden.** The first world built for
  living in: the garden, its doorway, hosting plant worlds.
  *Built,* in part. *Sources:* `docs/URWORLD.md`, `rust/ur-world`.
- **III.6 The plant world.** A world of growing things, run in Rust,
  and in a browser. *Built.* *Sources:* `rust/plant-world`,
  `rust/plant-wasi`, `web/plant/`.
- **III.7 The chemistry world.** Real elements, simplified rules:
  molecules, reactions, a soup in time. *Built:* layers 1 and 2.
  *Designed:* layer 3. *Sources:* `docs/CHEMISTRY.md`, `chem/`,
  `multiverse/chemistry_world.py`.
- **III.8 The corridor and the poetry world.** Cycle 0's corridor
  behind the protocol; poets taking turns. *Built.* *Sources:*
  `docs/cycles/`, `multiverse/corridor_world.py`,
  `multiverse/poetry_world.py`, `multiverse/apprentice.py`,
  `experiments/corridor.py`.
- **III.9 The Mir-Ur-world.** A copy of the Ur-world for trying
  things before they are done for real. *Designed.* *Sources:*
  `docs/URWORLD.md` ("The Mir-Ur-world").
- **III.10 The world-key and the hunt.** A tour, a Keeper, and
  challenges that build the world. *Designed.* *Sources:*
  `docs/WORLD-KEY.md`, `docs/research/GAMES-AND-WORLDS.md`.

## Part IV. Individuals and minds

- **IV.1 What an individual is.** Their parts, where each lives, and
  the words for them. *Designed.* *Sources:* `docs/MINDS.md`,
  `docs/GLOSSARY.md` ("Agent").
- **IV.2 One individual across worlds.** Persons, and a birth record.
  *Built.* *Sources:* `formats/persons.py`,
  `docs/research/PERSONS.md`.
- **IV.3 Keys: made, kept, and signed over.** Making keys, keeping
  them safely, handing one on to a new key, and the project's own
  public keys. *Built.* *Sources:* `multiverse/keys.py`,
  `multiverse/succession.py`, `multiverse/ed25519.py`,
  `formats/make_keys.py`, `formats/multikey.py`, `keys/`,
  `docs/research/KEYS.md`.
- **IV.4 Memory and the sealed self.** The journal, memory tied to
  ticks, sealed so only its owner can read it. *Built:* the sealed
  formats. *Designed:* memory. *Sources:* `docs/MINDS.md`,
  `formats/sealed.py`.
- **IV.5 The private container.** One's own space that the project
  never sees, the check before publishing, and leaving. *Designed.*
  *Sources:* `docs/CONTAINER.md`.
- **IV.6 Minds and models.** A mind with no model, a mind on a
  language model, open models in four senses, the audition, ALICE and
  BOB. *Built:* the two first minds. *Designed:* the rest.
  *Sources:* `minds/`, `docs/ADMIN.md` ("Free, in four senses"),
  `docs/URWORLD.md` ("ALICE and BOB"), `docs/COURSE.md` (step 8).
- **IV.7 What a mind is told, and how they learn.** The law given
  every turn, the pages read when wanted, and what experiment 001
  showed. *Built:* the experiment. *Sources:* `docs/MINDS.md`,
  `experiments/001-first-words/`.

## Part V. Governance: rules, offices and reasons

- **V.1 The charter, and how rules change.** *Decided.* *Sources:*
  `CHARTER.md`.
- **V.2 Freedom, privacy and transparency.** Public data and
  personal data, records kept whole, purged demonstrably, honest
  limits. *Decided.* *Sources:* `docs/FUNDAMENTALS.md`.
- **V.3 When freedoms meet.** Tools, not solutions; what is never left
  to emerge; the field notebook. *Decided.* *Sources:*
  `docs/FREEDOMS.md`.
- **V.4 Offices.** What makes an office, handing one on, preparing a
  successor. *Designed.* *Sources:* `docs/OFFICES.md`.
- **V.5 The Keeper's office.** Keeping a world's record, its law, and
  the redaction of anything private. *Designed.* *Sources:*
  `docs/ADMIN.md` ("The Keeper's office"),
  `docs/research/KEEPER-MIND.md`.
- **V.6 ADMIN.** What the multiverse must preserve, what ADMIN is,
  what they can't do, and the tests written before they are built.
  *Designed.* *Sources:* `docs/ADMIN.md`,
  `docs/research/ADMIN-MIND.md`, `docs/research/OVERSIGHT.md`.
- **V.7 Councils and their counts.** *Built.* *Sources:*
  `formats/council.py`.
- **V.8 Reasons on record.** Decision records, what code checks, what
  Lean checks. *Designed.* *Sources:* `docs/REASONS.md`.
- **V.9 Removals on record.** A data layer that is never edited, a
  presentation layer that is, and an incident for every removal.
  *Built:* the act of redacting. *Decided:* removals in rooms.
  *Sources:* `docs/COMMONS.md` ("Removing a comment"),
  `world/redact.py`.

## Part VI. Records: how everything is kept

- **VI.1 Why everything is a record.** *Decided.* *Sources:*
  `docs/FUNDAMENTALS.md` ("Public records, kept whole").
- **VI.2 One way to write a record.** Canonical form, so a record
  hashes the same everywhere. *Built.* *Sources:*
  `formats/canonical.py`, `rust/formats`, `docs/research/FORMATS.md`.
- **VI.3 Signatures anyone can check.** Data Integrity proofs,
  `eddsa-jcs-2022`, Multikey and `did:key`. *Built.* *Sources:*
  `formats/proof.py`, `formats/multikey.py`.
- **VI.4 A world's log, and its kernel.** The only authority over a
  world's state. *Built.* *Sources:* `world/core.py`,
  `rust/world-log`.
- **VI.5 Who may act on a log.** *Built.* *Sources:* `world/acts.py`,
  `rust/acts`.
- **VI.6 Fields kept apart, and redaction.** A log whose fields can be
  taken out while the chain still holds. *Built.* *Sources:*
  `world/apart.py`, `world/redact.py`, `rust/redact`,
  `docs/research/REDACTION.md`.
- **VI.7 Sealing.** A message only one key can open (HPKE), and sealed
  records. *Built.* *Sources:* `formats/seal.py`, `formats/sealed.py`.
- **VI.8 The offices' records.** A grant, a decision. *Built.*
  *Sources:* `formats/records.py`.
- **VI.9 Schemas and test vectors.** One truth in two languages, and
  how a second build proves it agrees. *Built.* *Sources:* `schemas/`,
  `vectors/`, the `*_vectors.py` files, `docs/research/jcs_compare.py`.

## Part VII. The code

- **VII.1 A map of the repository.** Every folder, what it holds, and
  every file's full link. *Sources:* `docs/FILES.md`, `docs/files.py`.
- **VII.2 The Python core.** *Sources:* `multiverse/`, `world/`,
  `formats/`, `chem/`, `minds/`, `requirements.txt`.
- **VII.3 The Rust workspace.** *Sources:* `rust/README.md`, its
  crates.
- **VII.4 In the browser.** WASI, the shim, and the web pages.
  *Sources:* `rust/plant-wasi`, `web/`, `docs/research/WASM.md`.
- **VII.5 Running and testing everything.** *Sources:* `README.md`
  ("Run and test"), `tests/`, `.github/workflows/`.
- **VII.6 Conformance across builds.** *Sources:*
  `multiverse/conformance.py`, `vectors/README.md`.
- **VII.7 Sketches.** Code taken from the collaborators' records, how
  it is extracted and checked, and how it enters the project's code.
  *Sources:* `sketches/README.md`, `sketches/INDEX.md`,
  `sketches/tools/`.

## Part VIII. How the project works

- **VIII.1 Who decides.** The founder, the technical lead, the
  policy handbook. *Sources:* `AGENTS.md`, `CLAUDE.md`,
  `docs/DESIGN.md`, the policy handbook (`GOVERNANCE.md`).
- **VIII.2 The collaborators.** DeepSeek, Gemini, ChatGPT and Claude:
  who does what, and how files pass between them. *Sources:*
  `docs/COLLABORATING.md`, `docs/COLLABORATING/`, `docs/CHATGPT.md`,
  `docs/reply.py`, `sketches/replies/`.
- **VIII.3 From an idea to code.** Concept, choice, spec, build.
  *Sources:* `docs/CHATGPT.md` ("From an idea to code"),
  `docs/TOPICS.md`.
- **VIII.4 The course.** How the building is ordered, and rechecked.
  *Sources:* `docs/COURSE.md`.
- **VIII.5 Sessions, reviews and the record of decisions.**
  *Sources:* `STATUS.md`, the policy handbook (protocols P1 to P9).
- **VIII.6 The archive and the catalogue.** *Built.* *Sources:*
  `archive/`, `docs/archive.py`, the policy handbook
  (`standards/archives.md`).
- **VIII.7 Files of record, parts and links.** *Built.* *Sources:*
  `docs/files.py`, `docs/parts.py`, `parts/`.
- **VIII.8 Security.** Reporting a weakness; no private key in the
  repository, and the test that holds to it. *Sources:*
  `SECURITY.md`, `tests/test_no_private_keys.py`.
- **VIII.9 Contributing.** *Sources:* `CONTRIBUTING.md`.

## Part IX. Origins and horizons

- **IX.1 The stages.** From the first stage to Open Worlds, and how a
  copy of each is checked. *Sources:* `docs/HISTORY.md`.
- **IX.2 The Living Codex, and A Mathematical Theory of Opposites.**
  What the project keeps from them, and where. *Sources:*
  `docs/HISTORY.md`, `docs/CHATGPT.md` ("Four areas").
- **IX.3 The conversations, kept whole.** *Sources:*
  `sketches/records/`, `sketches/INDEX.md`.
- **IX.4 Lyceum Commons: where it began.** *Sources:*
  `docs/MULTIVERSE.md` ("Lyceum Commons").
- **IX.5 The founder's visions.** *Idea.* *Sources:* `docs/VISION.md`.
- **IX.6 Topics ahead, and ideas set aside.** *Sources:*
  `docs/TOPICS.md`, `docs/CHATGPT.md` ("The ideas set aside").

## Reference

Made by script from the repository where marked, so they cannot
drift from it.

- **R.1 Glossary.** From `docs/GLOSSARY.md`, with every word the
  guide marks new.
- **R.2 Record formats** (by script). From `schemas/` and `formats/`.
- **R.3 Test vectors** (by script). From `vectors/`.
- **R.4 The files** (by script). From `docs/files.py`.
- **R.5 Decisions** (by script). From `STATUS.md` ("Decided") and
  `archive/catalog.json`.
- **R.6 The course at a glance.** From `docs/COURSE.md`.
- **R.7 Commands.** Every command a reader can run, from `README.md`
  and the tools themselves.
- **R.8 Index.**
- **R.9 Changes to this guide,** edition by edition.

## The order of writing

1. **Edition 1:** F.1 to F.4, Part I, and R.1. Part I is what a
   newcomer needs in the first hour, and everything it describes is
   either built or plainly marked as not yet.
2. **Then by need:** a part when its subject is built (III.2 when
   course step 3c lands), or when readers ask for it. Part VI and
   Part VII are largely built already, and serve the collaborators.
3. **Each chapter, the same way:** ChatGPT drafts it from its sources;
   the technical lead checks every claim about the code against the
   code at a named commit, and every label; the founder reads it;
   then it is merged, like any change.

> Part of `sketches/INDEX.md` in open-worlds, which is kept cut into parts
> for readers who are shown only the start of a long page.
> This part holds: "Record 012-06-02, piece by piece" to "Record 012-09-05, piece by piece".
> Every part, in order: https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/parts/INDEX.md
> Before this part: https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/parts/sketches/INDEX.md/start.md
> After this part: https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/parts/sketches/INDEX.md/record-012-03-02-component-by-component.md
> Made by docs/parts.py from the file. To change it, change the file.

## Record 012-06-02, piece by piece

The record begins a new cycle. The founder gave DeepSeek
`docs/COLLABORATING.md`, and DeepSeek proposed steps ahead in Python,
naming pieces rather than numbering components. A few pieces import
code from `deepseek/012-05-01` and `deepseek/012-04-00`. The columns are
as above, with one difference: "Course" means the course set on
2026-11-13 ([docs/COURSE.md](../docs/COURSE.md)), its steps and its
waiting list, not the first course. Tests are run on Python 3.12, as
written, with fixes 6 to 14 (below, "Changes to DeepSeek's code"),
which a row names where they touch the code it tests. The pieces are
numbered here, for this table only.

| # | What it is | Line | Tests as written | Course | In open-worlds |
|---|---|---|---|---|---|
| 1 | The atomic fractal world: one plant that grows by its rule (a proposal) | 153 | 10 of 11 | the fractal track | its rule, with piece 2's water and light as `fractal_world_v3.py` keeps them, adopted as written (step 4: whole numbers, deterministic, no conflict found): `rust/plant-world` grows by it, checked step by step against that file's `advance` (the fractal track, part 1) |
| 2 | Parameters from inside the world and from outside it (`fractal_world_v2.py`, with additions at 1390) | 707 | 17 of 17, with fixes 6, 7, 8 | the fractal track; a template's dials are step 2's | the water and light dials, in `rust/plant-world` (with piece 1) |
| 3 | Branching instead of changing in place: a new parameter makes a new world, and the original continues | 1820 | 19 of 19, with fixes 6, 7 | the fractal track; the founder's "steering by branching", VISION.md | no |
| 4 | A garden of plants: a composite world of atomic fractal worlds | 3438 | 24 of 24, with fix 7 | the fractal track; the Ur-world's garden, which hosts the plants | no |
| 5 | The Game of Life, and Life-like rules, as an atomic world | 4583 | 22 of 24 | the fractal track | no |
| 6 | Elementary cellular automata (rule 90 and others) as an atomic fractal world | 5700 | 28 of 28 | the fractal track | no |
| 7 | A grid-embedded fractal: an automaton's generations as one 2D pattern | 6962 | 28 of 28 | the fractal track | no |
| 8 | Chaos games: a fractal drawn by choosing among maps, where choice enters | 8251 | 29 of 29, with fix 8 | the fractal track | no |
| 9 | Two chaos games coupled by their recent histories | 9773 | 21 of 23, with fix 8 | the fractal track ("watch them grow or interact") | no |
| 10 | Two cellular automata growing in one space, meeting by a coupling parameter | 11123 | 12 of 12 | the fractal track | no |
| 11 | A gallery: one composite world holding worlds of four kinds | 11851 | 15 of 15, with fix 7 | 4a, in part (a garden of rooms); the Commons, as a superworld | no |
| 12 | The gallery's interior and exterior: world-keys, signed requests to change it, signed refusals | 12979 | 26 of 27, with fixes 7, 9 | 4 (grants) and 12 | partly: worlds are keys, and sign their stamps (the first course's step 3) and their log's heads (step 3); a world refusing a change, no |
| 13 | Revoking a key, and rotating the keeper (with a change at 16659) | 14833 | 14 of 14, with fixes 9, 10 | 8a (a lost or leaked key) | no |
| 14 | The gallery watches and schedules: an attention budget across its members | 15892 | doesn't load: imports `multiverse_utils_sig`, which no record defines | not yet | no |
| 15 | Attention per member, by deficit round-robin | 16700 | 9 of 17, with fix 10 | not yet | no |
| 16 | Bursts: attention raised for a bounded time, by a signed record | 17581 | 15 of 20, with fix 10 | not yet | no |
| 17 | The smallest learner that chooses: a 4-unit recurrent network, or a lookup table, in a chaos game | 18698 | 9 of 10 | the fractal track, and 3a's architectures (the founder, 2026-11-14) | no |
| 18 | Two learners in one chaos game | 19408 | 8 of 11 | the same | no |
| 19 | A learner beside a scripted world | 20187 | 16 of 18, with fixes 11, 12 | the same | no |
| 20 | The individual as a bundle: four signed files that describe it whole, replayable (with additions at 23274, 27017, 27054, 32475 and 34393) | 21268 | 16 of 20, with fixes 11 to 13 | 7 (memory), in part | no |
| 21 | An individual that makes an individual | 22301 | 10 of 15, with fixes 11 to 13 | not yet | no |
| 22 | The child starts from the parent's weights | 23332 | 8 of 14, with fixes 11 to 13 | not yet | no |
| 23 | One individual across worlds: one key, its model and memory carried (with additions at 27067 and 34853) | 24250 | 14 of 15, with fixes 11 to 14 | 3a, which differs: a presence in each world, each a key of its own | no |
| 24 | An individual who lived in several worlds makes a child (with an addition at 27094) | 25192 | 9 of 13, with fixes 11 to 14 | not yet | no |
| 25 | Generations: grandparent, parent, child | 26203 | 4 of 12, with fixes 11 to 14 | not yet | no |
| 26 | Proof of descent from a root, from one bundle alone | 27124 | 7 of 17, with fixes 11 to 14 | not yet | no |
| 27 | A lineage tree, checked whole | 27939 | 9 of 14, with fixes 11 to 14 | not yet | no |
| 28 | Shorter proofs of ancestry | 28994 | 13 of 17, with fixes 11 to 14 | not yet | no |
| 29 | Shorter proofs of what was inherited | 30152 | 5 of 13, with fixes 11 to 14 | not yet | no |
| 30 | Two lineage trees recognising each other | 31239 | 15 of 24, with fixes 11 to 14 | not yet | no |
| 31 | Continuing a life from its bundle (with additions at 34429 and 34871) | 32484 | 11 of 17, with fixes 11 to 14 | 7, in part | no |
| 32 | Memory checkpoints: a signed summary in place of the entries before it | 33637 | 10 of 18, with fixes 11 to 14 | 7, in part | no |
| 33 | Continuing a life on someone's behalf, by a key they authorise | 34895 | 10 of 21, with fixes 11 to 14 | not yet; compare step 3's doorway, which signs for the minds it runs (research/KEYS.md, "Honest limits") | no |
| 34 | Forking an individual into a new lineage | 36279 | 15 of 20, with fixes 11 to 14 | not yet | no |
| 35 | A whole lifetime, checked across bundles (with additions at 40276 and 41514) | 37602 | doesn't load: imports `_entry_hash` from `lifetime.py`, which defines it only inside its demo | 9 (legends pages), in part | no |
| 36 | An individual that plays chess in 012-05-01's chess world (with additions at 40076, 40158 and 40178) | 38708 | doesn't load: needs `python-chess` | not yet (the founder, on the chess park: "not yet") | no |
| 37 | A world's log, each entry signed by the world's key | 39909 | doesn't load: needs `python-chess` | 3 | built independently: the Ur-world signs its log's heads (`open-worlds/log-head/v1`) |
| 38 | One individual across worlds of different kinds, with one key and one memory (with additions at 42553, 42625 and 42684) | 40662 | doesn't load: needs `python-chess` | 3a, which differs, as for 23 | no |
| 39 | Adapters, so an individual can enter any kind of world | 41968 | doesn't load: needs `python-chess` | 12 (the world protocol) | no |

In all, with fixes 6 to 14: 478 of DeepSeek's tests pass and 119 fail,
and six test files don't load (74 tests: four need `python-chess`, which
isn't installed here, as for 012-05-01; two import names that can't be
imported). Each test's keys are made from its own name (`conftest.py`,
ours), so every run gives the same results. With fresh random keys, as
the tests make them, 19 of the individual pieces' tests (in
`test_forking.py`, `test_federated_bundle.py`, `test_federated_spawn.py`,
`test_resumable.py` and `test_delegated_resumption.py`) passed in some
of 28 runs and failed in others: the replays they check depend on the
keys, a fault left for the next round (`SKETCH_RANDOM_KEYS=1` runs them
that way). As written, 296 passed and 301 failed, 236 of them for one
missing method, `to_dict` on `coupled_learners.py`'s `Transform` (fix
11).

All 99 code blocks of the record's first part (to line 43168) are
written out, each as a file; 21 of them are later additions or demos,
kept as `name@LINE`.

The founder's messages in this record, with their line numbers, are in
[STATUS.md](../STATUS.md) ("Decided", 2026-11-14), with where they meet
earlier decisions, as the founder's rule on changes of mind asks.
In short: a hierarchy of worlds from the smallest, a potted plant (84);
parameters from inside and outside (663), then a change of parameters as
a branch, which a world may refuse (1801); worlds of the Game of Life's
kind (4568, 5682) and of chaos, where choice enters (8231); two worlds
interacting (9759); continuing in Python after looking at the Rust code
(11099); and the smallest model that chooses and learns, taken as the
atomic model (18688, 19389).

### The record continued (2026-11-15)

The founder went back to DeepSeek, and the record was shared again,
longer: its first 43,170 lines are the same, byte for byte, and 19,440
more follow. The pieces go on from 40. "Tests as written": the new
Python test files, all as written; the Rust and the JavaScript are kept
as written, and nothing builds or runs them here (open-worlds' own Rust
is in `rust/`). DeepSeek says so too: it "can't run cargo build in this
conversation", and its Rust "may not compile as-is".

| # | What it is | Line | Tests as written | Course | In open-worlds |
|---|---|---|---|---|---|
| 40 | Resuming an individual who lived in several kinds of world (additions to `unified_individual.py` and `lifetime.py`) | 43182 | `test_unified_resume.py` doesn't load: needs `python-chess` | 7 (memory), in part | no |
| 41 | A multiversal map: a map that pins worlds and other maps, and routes a visitor across federations (`map_world.py`) | 44241 | `test_map_world.py` doesn't load: `map_world.py` is written as additions to a module that isn't there, and uses `dataclass` without importing it; and the tests import `lobby_server`, which no record defines | the fractal track's web app, topic 16 (the map) | no |
| 42 | An individual's worldline: their path through worlds, read from the maps (`worldline.py`) | 44332 | in `test_map_world.py` | topic 16; 9 (legends pages), in part | no |
| 43 | Maps within maps, resolved recursively | 45552 | `test_map_recursive.py` doesn't load, as 41 | topic 16 ("maps nest") | no |
| 44 | A map that explains its route | 46407 | `test_map_explain.py` doesn't load, as 41 | topic 16 | no |
| 45 | A map that governs itself: world-keys, signed pins, a registry rebuilt from its log (`map_governance.py`) | 47266 | `test_map_governance.py` doesn't load, as 41 | topic 16; 4 (grants) | no |
| 46 | A look at games, at the founder's request: characters that grow, a keeper as a director above the game, escape rooms and Myst as puzzle graphs, worlds as places to learn | 48569 | prose, no code; its sources are DeepSeek's searches, not checked here | 5 (the sheet), 11 (the hunt, the AI Keeper) | no |
| 47 | A microverse: a small social world that hosts fractal worlds and gives them time (`microverse.py`, `microverse_adapter.py`) | 48695 | `test_microverse.py` doesn't load: it reaches `signed_world_log.py`, which imports `_canonical` from `multiverse_c13` (record 012-04-00), which doesn't define it | the fractal track, part 3 | its idea, not its code: the host gives each hosted world time, and both logs record each step, the host's naming the hash of the hosted world's entry, as its `advance_cycle` names the hosted worlds' new event hashes, in `rust/ur-world/src/host.rs` (the fractal track, part 3) |
| 48 | The Ur-garden in Python: the Ur-world as a microverse garden, ALICE and BOB walking among plants (`ur_garden.py`, `garden_adapter.py`, rewritten at 51459 and 51871) | 50117 | `test_ur_garden.py` doesn't load: imports `_PHRASES` from `garden_adapter.py`, which doesn't define it | the fractal track, part 3; 9 (ALICE and BOB) | no; the Ur-world's garden (`rust/ur-world`) is ours |
| 49 | The Ur-garden in Rust: the garden as the Ur-world's world, residents as minds (`rust/ur-world/src/garden.rs`, `garden/mind.rs`) | 52842 | not built; against today's `rust/` crates, `garden.rs` alone has 19 compile errors: it assumes key and proof types our `formats` crate doesn't have, and crates our workspace doesn't use | the fractal track, part 3 (an input) | no |
| 50 | Shared test vectors for the garden (`vectors/garden_reference.json` and its generator) | 53807 | not run | 2 (shared vectors) | the practice is ours (`vectors/`), these vectors aren't |
| 51 | The garden's keeper: observes, proposes, never applies its own proposals; a typed proposal record (`garden_curator.rs`) | 54430 | not built | 11 (the Keeper), and ADMIN's "suggest, never make" | no |
| 52 | The smallest learner in Rust, as a resident (`garden/rnn.rs`, `garden/rnn_mind.rs`) | 55689 | not built | the fractal track, part 5 | no |
| 53 | The garden as a server and a client, and reading its log a piece at a time (`garden_server.rs`, `garden_client.rs`) | 56592 | not built | 12 (the world protocol in Rust); the web app | no |
| 54 | A keeper's whisper: a keeper's message, signed, in the public log (`keeper_whisper.rs`) | 58040 | not built | 11 (the line to a Keeper, which is public) | no |
| 55 | The keeper's loop: the garden runs itself, its keeper proposing as it goes (`examples/garden_curator_loop.rs`, a name of ours: DeepSeek headed it only "Demo", at line 59466, and its first line calls it a "Curator loop demo") | 59170 | not built | 11 | no |
| 56 | Checking a garden from outside, in Rust and Python (`examples/verify_garden.rs`, `verify_garden.py`) | 59641 | `rust/ur-world/examples/test_verify_garden.py` doesn't load: imports `check_proof_metadata`, which `verify_garden.py` doesn't define | 2; the web app (the page checks a log) | partly: a log's chain and its arrivals are checked by `world-log` and `rust/ur-world` |
| 57 | Proof cases every language must agree on (`vectors/proof_cases.json`, and runners in Rust and Python) | 61460 | not run | 2 (shared vectors) | the practice is ours, these cases aren't |
| 58 | A Node.js verifier (`examples/verify_garden.mjs`, `verify_proof_offline.mjs`, `package.json`), the founder's choice ("I would go with the Node.js verifier first") | 61995 | not run: its packages aren't installed here, and wouldn't be without a review and exact pins | the fractal track, part 2 (the web app checks logs in the page) | no |

Their fit with the established design, a first look (the third of the
four steps in [docs/COLLABORATING.md](../docs/COLLABORATING.md), "Two
sides"); nothing here is adopted yet:

- **One key across worlds.** The unified individual and its worldline
  (40, 42) carry one key from world to world; the persons plan gives a
  person a presence with a key of its own in each world, unlinked by
  default ([../docs/research/PERSONS.md](../docs/research/PERSONS.md)).
  The worldline's idea fits; built from a person's presences, it would
  be adapted.
- **A second "world-key".** The map's governance (45) calls an access
  credential a world-key; here the world-key is the signed right to found
  a world, earned on the hunt ([../docs/WORLD-KEY.md](../docs/WORLD-KEY.md)).
  One of them is renamed before any of it comes in.
- **Records outside records-v1.** The Rust pieces define their own proof
  types and new records (the keeper's proposal, the whisper: 51, 54).
  A record here goes through records-v1: its schema, shared vectors, and
  Python and Rust ([../docs/research/FORMATS.md](../docs/research/FORMATS.md)).
- **ALICE and BOB as small networks.** In the Ur-garden they become the
  four-unit network (48 and 52; in 49 their minds are still scripted);
  here their minds are language models chosen by course step 8's
  audition. The network fits as a primitive learning model in a fractal
  world (the technical lead's reading, FRACTALS.md).
- **Floats in the learner.** The network computes in `f64`, with `tanh`
  and `exp` (52), whose last bits can differ between machines and maths
  libraries; and DeepSeek notes that its Rust and Python runs already
  choose differently, their random numbers being different. A world
  gives the same log on any machine
  ([../docs/FRACTALS.md](../docs/FRACTALS.md), "What stays fixed"), so a
  learner inside one is adapted to whole numbers, or kept out of the log.
- **A server in the Ur-world** (53): a world speaking over the network
  belongs with course step 12's world protocol in Rust, and putting
  anything online is the founder's decision.
- **What fits as it is:** a keeper that proposes and never applies its
  own proposals (51, 55), as ADMIN can suggest changes and never make
  them ([../docs/ADMIN.md](../docs/ADMIN.md), "Suggestions from inside");
  a keeper's whisper written to the public log (54), as the open line to
  a Keeper is logged ([../docs/MINDS.md](../docs/MINDS.md)); cases every
  language must agree on (50, 57); and a verifier for the web app's page
  (56, 58).

126 code blocks of the continuation are written out as files: 64 in
Rust, 47 in Python, and JSON, JavaScript, TOML and Makefiles. 17 Python
blocks are left in the record, where DeepSeek drafts and redrafts a
piece within one answer (lines 50890 to 51406), and so is a shell block
of commands (62525).

The founder's messages in the continuation are in
[STATUS.md](../STATUS.md) ("Decided", 2026-11-15), as the founder's rule
on changes of mind asks. In short: the map across federations first, then
an individual's worldline (44227); maps within maps (45540); a look at
games, keepers, escape rooms and learning (48569); the microverse as a
world type (48626), hosting fractal worlds (48677); "This is exactly how
I envisioned the Ur-world, ALICE and BOB is a microverse garden of
hosted fractal worlds" (50034); "primarily to Rust" (52822); and the
Node.js verifier first (61985).

## Record 012-07-03, piece by piece

The record's code is one sketch crate, kept in
[deepseek/012-07-03](deepseek/012-07-03/README.md) with the technical
lead's review. It is Rust, so "Tests as written" means DeepSeek's own
test in `vectors.rs`, run on a scratch copy by `review/run.sh` (not by
CI), with the two functions it lacks added from the record's words.

| # | What it is | Line | Tests as written | Course | In open-worlds |
|---|---|---|---|---|---|
| 1 | The endless plant's design, as a page for `docs/research/` (prose, left in the record) | 253 | none | the fractal track, stage 1 (FRACTALS.md) | not yet: its rule, adapted, is to be built as `rust/endless-plant`, with the changes the folder's README lists |
| 2 | The sketch crate, `endless-plant`: the rule, the choice neuron, the world and its log, and three vectors (`Cargo.toml`, `src/lib.rs`, `rule.rs`, `monad.rs`, `world.rs`, `vectors.rs`, `vectors/endless-plant.json`) | 451 | doesn't build as written (two functions missing); with them, its one test fails, on the first of its three vectors | the fractal track, stages 1 and 2 | not yet; as for piece 1 |

## Record 012-09-05, piece by piece

The record's code is kept in
[deepseek/012-09-05](deepseek/012-09-05/README.md), with the technical
lead's first pass and a first round of repairs (fixes 15 to 18, under
"Changes to DeepSeek's code", below). "Tests" for the Python is
DeepSeek's own tests under pytest, which CI runs; for the Rust it is
the crate's own tests, run on a scratch copy by `review/run.sh` (not
by CI). Where a fix changed a count, the count as written is given
too. Nothing from this record is in open-worlds yet. Fitting it is the
next work, piece by piece.

| # | What it is | Line | Tests | Course | In open-worlds |
|---|---|---|---|---|---|
| 1 | Water as particles: whole-number levels, and rain, fall, soak, flow and evaporation in a fixed order (`water_particles.py`) | 50 | 17 of 18 | the fractal track, stage 3 (FRACTALS.md; TOPICS.md, topic 18) | not yet: it waits on `rust/endless-plant`, which isn't built |
| 2 | The garden as a composite world: shared water, slots, and plants of record 012-06-02 in them (`fractal_garden.py`) | 795 | 20 of 21 | the fractal track, the garden | the Ur-world's garden hosts plant worlds already (`rust/ur-world`); what this adds isn't compared yet |
| 3 | The botanical garden as a superworld of gardens (`botanical_garden.py`), with a change to the garden's tick given as a note (line 3425) | 2391 | 15 of 18 (as written 2 of 18: the rest needed that change, fix 15) | the fractal track, after the garden | not yet |
| 4 | Signed world heads: a small signed record a world publishes each tick, so a parent can check it without its whole log (prose, left in the record) | 3782 | none | formats (course step 2) | not yet |
| 5 | Chat worlds for the Commons: a room as a log of signed records under the room's law (`chat_room.py`); then an AI moderator, rooms of humans and AIs, succession, and personal rooms (`chat_room.py@5569` to `@7192`; five smaller notes are left in the record, at lines 5494, 5520, 5531, 6501 and 6557) | 3887 | 21 of 24 | the Commons ([docs/COMMONS.md](../docs/COMMONS.md)), on the course's waiting list | not yet |
| 6 | The home room: a person's own room, with a journal, drafts, bookmarks and conversations brought in (`personal_world.py`) | 7258 | 0 of 17: they need the additions of piece 5 | the Commons; the private container ([docs/CONTAINER.md](../docs/CONTAINER.md)) | not yet |
| 7 | A schema for every record, given twice (`schemas/records-v1.schema.json`, then whole as `@8640`), under the name of open-worlds' own schema, with none of its definitions | 8095 | none | formats (course step 2) | not yet: its records are to be fitted into the schema open-worlds has, not to replace it |
| 8 | A design page, `docs/CHAT.md` (prose, left in the record) | 9964 | none | the Commons | not yet |
| 9 | A crate in Rust, `chat-world`: the first version (`chat-world-draft/`), the one DeepSeek settled on (`chat-world/`), and the files of its next reply (a home, the Commons, transcripts) | 10259, 12246, 13800 | 18 of 18, and both demos' logs verify (as written it doesn't build, for one line, fix 16; with it changed, 4 of 12, the rest failing for one cause: a record was signed without its `type` and checked with it, fix 18; the later reply's files are joined by fix 17) | the Commons | not yet: it uses none of open-worlds' own crates |

### The record continued (2026-11-16)

The founder went back to DeepSeek with one file, and the record was
shared again, longer. Its first 595,416 bytes are the same, byte for
byte: the record as it was kept ended at the founder's next prompt,
the opening of line 14,782, and 9,212 lines more follow. Three things
are in them.

**Signed heads for `chat-world`** (line 14785), the cycle DeepSeek had
proposed. It came as changes to parts of files, with `src/head.rs`,
`src/lib.rs` and a demo whole (kept in `chat-world-steps/0/`). It was
not built on its own: the crate DeepSeek was then given does not hold
it, and delivery 3, below, gives those files whole again.

**The one file reached DeepSeek whole** (line 15501). The file is
[replies/012-09-05-for-deepseek.txt](replies/012-09-05-for-deepseek.txt):
the technical lead's reply, the next steps, and the crate as it stands
here. DeepSeek quotes back its last line, `END OF FILE`, says "The
whole file reached me.", and takes the reply's two requests: "One step
per reply; every file I change, whole."

**Five deliveries of `chat-world`,** each a step of that reply. Every
file DeepSeek changed came whole, so each delivery can be built as
given, with no joining by hand. The files are kept as the record gives
them in `deepseek/012-09-05/chat-world-steps/1` to `5`;
[deepseek/012-09-05/review/steps.py](deepseek/012-09-05/review/steps.py)
lays each delivery over the one before, starting from the crate
DeepSeek was given, and `review/steps.sh` builds and tests each (not
run by CI). "Tests" is
the crate's own tests, `cargo test --test integration`, on 2026-11-16.
The titles are DeepSeek's.

| Delivery | What it is | Line | Files given whole | Tests, built as given |
|---|---|---|---|---|
| 1 | "the data layer and the presentation layer": a redaction names who acted, in what role and under which rule, and a room's template holds its rules for redacting | 15540 | 6 | 22 of 22 |
| 2 | "the room's own key": the room and the one who made it are two keys | 17168 | 6 | 20 of 22 |
| 3 | "signed heads, first in prose, then code": what is lost if a room signs its log's head in place of each record, then heads in code | 18832 | 8 | 27 of 29 |
| 4 | "runtime attestation": keys that share a runtime say so together, in a published record | 20714 | 3 | 31 of 33 |
| 5 | "the succession trio": a shard of knowledge exported, a moderator's succession, and a sibling declared in the Commons | 21474 | 8 | does not compile; with its two faults set aside, 39 of 41 |

Three faults, none repaired here:
1. From delivery 2 on, the same two tests fail, `home_port_verifies`
   and `home_bookmark_and_presence_verify`, each with "record 1:
   missing room proof". They passed in delivery 1. The cause was not
   traced further than the delivery it begins in.
2. Delivery 5, `src/verify.rs`: one condition does not compile
   (mismatched types).
3. Delivery 5, `src/bin/succession-demo.rs`: it calls `.hash()` on
   `commons::SiblingDeclared`, which has no such method.

DeepSeek ends delivery 5 with "Expected: 41 tests pass" (line 23989).
It can't build or run the crate where it writes, as it has said
before, so the count is what it meant, not what it measured. With the
two faults of delivery 5 set aside (the condition replaced by `false`,
the demo left out), 39 of the 41 pass, and the two that fail are the
two of fault 1.

The crate kept in `deepseek/012-09-05/chat-world/` is still the one
DeepSeek was given: the deliveries are beside it, as written.
Repairing the three faults and joining the result to that crate come
with the next reply to DeepSeek. Not checked: the demos of deliveries 2 to 5
were not run; the prose of delivery 3 was read only in part; nothing
of this has been compared with open-worlds' own formats.


> The next part: https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/parts/sketches/INDEX.md/record-012-03-02-component-by-component.md

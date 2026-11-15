# Building on this: start here

For anyone building on open-worlds, and in particular for the founder's
conversations with DeepSeek. This is the page to start from. The
founder: "What you put in the repo becomes the new standard we develop
from in my DeepSeek conversations."

**Kept current.** The founder, 2026-11-14: "please make sure the
COLLABORATING.md is up to date as we go. This way, if we run out of data
for a few days, I can still go and work with DeepSeek during that time."
So any change to something this page describes updates it in the same
pull request, and every review checks it (AGENTS.md). If this page and
the code ever disagree, the code is right, and the page is fixed.

## Since you were last here

The last DeepSeek conversation, record 012-06-02 (2026-11-14), began
from this page; what it built is kept in `sketches/` ("Where the
conversation stands", below). The one before, record 012-05-01, ended on
2026-11-13, when everything here was Python. What has changed since then,
in the order to read it:

1. **A new course** ([COURSE.md](COURSE.md)), set on 2026-11-13 for the
   Ur-world and its first two individuals, ALICE and BOB: twelve steps
   ahead, rechecked after each. Steps 1 (the design pages), 2 (formats
   that last) and 3 (keys and identities,
   [research/KEYS.md](research/KEYS.md)) are done: the project's real
   keys were made on 2026-11-14, and their public halves are in
   [`keys/key-list.json`](../keys/key-list.json); in the Ur-world,
   whoever enters signs an arrival, a name stays the key's that first
   used it, and a world signs its log's heads. Step 3a, persons, is
   under way: its plan is in
   [research/PERSONS.md](research/PERSONS.md).
   Rechecked after step 3, the course gained step 8a, a lost or leaked
   key, before ALICE's and BOB's birth.
   It returns to DeepSeek at step 10, or sooner if the founder chooses.
2. **The worlds are built in Rust** (the founder: "we should stick with
   Rust"). [`rust/`](../rust/README.md) holds the Ur-world, a 3D world
   that begins in a garden ([URWORLD.md](URWORLD.md)), where ALICE and
   BOB will be born at step 9 (until then two scripted stand-ins,
   WALKER and GARDENER, show it works), with a doorway any program can
   speak through as a mind; a checker for a world's log; and the formats
   below. The reference is Python for
   what Python built first (the log in `world/`, the protocol in
   `multiverse/`, and the formats' vectors, which `formats/` writes and
   Rust reads); for the Ur-world, Rust is the reference, and Python
   checks its vectors.
3. **Who an individual is,** in the design pages:
   [MINDS.md](MINDS.md) (identity, mind record, a sealed self no one else
   reads, unless the founder opens it under the "break glass", in the
   open; the sheet, avatars, and where everything lives);
   [WORLD-KEY.md](WORLD-KEY.md) (the tour, the hunt, and the world-key,
   a signed right to found a world); [ADMIN.md](ADMIN.md) (ADMIN, the
   Keeper of the multiverse: what it must preserve, how it learns, the
   round table of Keepers, a learning immune system);
   [REASONS.md](REASONS.md) (every office's decision on record, with its
   reasons); [FREEDOMS.md](FREEDOMS.md) (tools for when freedoms meet).
4. **The founder's visions of 2026-11-14,** in the founder's words
   ([VISION.md](VISION.md), [PARALLEL-WORLDS.md](PARALLEL-WORLDS.md)):
   question worlds, where an idea becomes a world that tests it; an app
   whose chat can create and query a world; a hierarchy of worlds, from
   primary worlds with rules and no AI up to ADMIN; one person across
   many worlds; riding along in a world, and steering it by branching;
   branches that merge rules, never states; parallel worlds from one
   template, and a garden to walk among them; and fractal worlds
   (COURSE.md, waiting list).
5. **Formats that last** ([research/FORMATS.md](research/FORMATS.md)).
   Every new signed record is a W3C Data Integrity proof
   (`eddsa-jcs-2022`) over its RFC 8785 form, with keys named as did:key.
   One JSON Schema, [`schemas/records-v1.schema.json`](../schemas/records-v1.schema.json),
   defines them: grants, decision records, suggestions, ratings, signed
   log heads, world-keys, journal entries, identities, birth records,
   mind records, a world's template with its dials, and the project's
   key list (which key holds each role, signed by the root). Sealing, so
   only one key can open something, uses HPKE (RFC 9180). Python (`formats/`)
   and Rust (`rust/formats`) agree through shared test vectors
   ([vectors/](../vectors/README.md)). What is signed keeps three rules:
   ASCII keys, integers within 2^53 - 1, and no floats (a quantity with
   a fraction is an integer in a stated unit).
6. **How decisions are made** ([AGENTS.md](../AGENTS.md)). The founder
   decides what the project is for; Claude, the technical lead, decides
   the code and reviews every change; a question the founder hasn't
   answered is decided on the technical lead's recommendation, once put,
   except what is outward-facing, costs money, touches personal
   information, or must be the founder's own words or act. Decisions are
   written down with their reasons in [STATUS.md](../STATUS.md). The
   founder's most recent word wins, here or in a conversation with
   DeepSeek: "treat the new idea as an update and always go with the
   most recent". A newer word that contradicts an earlier decision is
   pointed out to the founder, naming the earlier one, so the change is
   made knowingly. A newer word that answers changed conditions is no
   contradiction (the founder: "So my direction changed because the
   conditions changed. That is how I work. It is not contradictory, but
   situation dependent."), and is recorded beside the earlier one; the
   change is still mentioned to the founder, as a note.
7. **Fractal worlds, moved forward** ([FRACTALS.md](FRACTALS.md)), on
   2026-11-14, from your sketches in record 012-06-02: a fractal plant
   world in Rust, checked against your Python; a web app in `web/` to
   watch worlds grow; and in it, a multiversal map, which the founder
   means to brainstorm with you ([TOPICS.md](TOPICS.md), topic 16). How
   a world may change is left open, and may differ by world; the founder
   pictured one world where you set out to remember what you chose to
   forget ([VISION.md](VISION.md), "Worlds that change differently").
   And the founder asked you to move to Rust ("primarily to Rust", record
   012-06-02): what you write in Rust is compiled, tested and fitted in
   here, and what fits comes straight in ("Two sides", below). The
   current files are each linked under "Code in Rust", below, to build
   on if you choose; the Ur-world has signed arrivals and log heads
   since step 3. The
   Ur-world's garden is to host the fractal plants, as the founder
   pictured it: "a microverse garden of hosted fractal worlds".
8. **Challenges that build the world** ([WORLD-KEY.md](WORLD-KEY.md),
   "Challenges that build the world"; [TOPICS.md](TOPICS.md), topic 17):
   the founder's idea of 2026-11-15, open for brainstorming. The founder:
   "Here is the new idea: the challenges are constructive." Doing a
   challenge builds the real world for everyone, and it is done when you
   can do the thing: "But credit is not the point but learning." The
   world grows as it is explored, so there is always room.

The multiverse began as a sketch the founder wrote with DeepSeek
(conversation records 012-04-00 and 012-03-02). This repository brought
it in, made it run, and changed what needed changing; what was kept and
what changed, and why, is in [MULTIVERSE.md](MULTIVERSE.md) and in each
module's docstring.

## Two sides: the sketch and the standard

**The sketch is a rough draft.** Each step in the conversation assumes the
last one ran as expected and asks what to build next, the way a creative
team might convey a vision in code instead of boxes and arrows. Nobody
expects it to run, and bugs are part of a draft. In the founder's words
(to the technical lead, 2026-11-13): "it is meant to be a starting point
for you, not an end point." So an
"Expected output" in the conversation is a prediction, which is fine; the
house rules below apply when code comes into open-worlds itself.

**The records and the sketch's code are kept, apart.** They live in
[`sketches/`](../sketches/README.md): the conversation records verbatim,
and DeepSeek's code written out exactly as the record has it, with every
test's result. That is a record of DeepSeek's suggestions, kept so they
can be read, run and debugged, without committing to using them.
[`sketches/INDEX.md`](../sketches/INDEX.md) is the one place that says
where the sketch and the course meet: each component, how its tests fare,
which course step it relates to, and whether any of it is in open-worlds.
Its "Course" column uses the first course's step numbers for records
012-04-00 and 012-05-01 ("Done: the first course" in
[COURSE.md](COURSE.md) is the key), and the course now running for
record 012-06-02.

**Taking a piece in is a decision of its own** (the founder, 2026-11-15:
"Also, keep in mind, we expect DeepSeek code to have some things to fix,
and we should still decide whether or not to incorporate anything that
goes against our established design."). The technical lead's answer, put
to the founder the same day (it stands unless the founder answers
otherwise): four steps, in order.

1. **Bring it in as written,** in `sketches/`, with every test's result.
2. **Make it run:** fix what is broken, the design unchanged, each fix
   listed with its reason.
3. **Check its fit** with the established design (the decisions in
   STATUS.md and the design pages), naming each conflict.
4. **Decide, piece by piece:** adopt it, adapt it, or keep it as a
   sketch, with the reason in `sketches/INDEX.md`. The technical lead
   decides the code; what would change a founder's decision goes to the
   founder, with a recommendation.

**What fits comes straight in.** The founder, 2026-11-15: "The DeepSeek
code should still be treated as sketches and brainstorming, but now in
Rust. But if the code aligns well and extends cleanly, then why not just
incorporate. But changing to Rust does not change anything else, only
the language." The technical lead's rule for it: a piece that compiles
against the crates on `main`, passes the three commands under "Code in
Rust", keeps the rules there, and meets no conflict in step 3 goes into
`rust/` in one reviewed pull request, steps 2 to 4 together. Its commits
name DeepSeek as well as Claude in their `Made-by` lines and say what
was changed here, and the record keeps the original. Everything else
stays a sketch, as before.

**The standard is open-worlds' own code, not the sketches.** Build on
the code merged into `main` (`multiverse/`, `formats/`, `rust/`) and the
documents in `docs/`. The code in `sketches/` is
earlier work, some of it on the old, unsigned protocol, kept for its
ideas.

## Where the conversation stands

Four records are kept: 012-03-02 (the poetry engine), 012-04-00
(components 1 to 63), 012-05-01 (components 64 to 87: a live
federation and its tools, then the founder's turn to game worlds: a
chess park, worlds inside worlds, worlds that grow and govern
themselves, and a world that keeps running), and 012-06-02, a new cycle
begun from this page (fractal worlds, a gallery of worlds and its
governance, then the smallest learner that chooses, and individuals as
signed, replayable bundles), which ended with DeepSeek asking which
piece is next. Its code is being made to work; then the founder and the
technical lead decide what fits with what is built, and how (STATUS.md,
"Decided", 2026-11-14). Each new conversation starts a new record, which
gets its own folder in `sketches/`. Each
component's place is in [`sketches/INDEX.md`](../sketches/INDEX.md), by
the first course's numbers. In short: components 1 to 7 are in
`multiverse/`, working (the first course's step 1); 13 and 14,
signatures and their conformance test, were rebuilt in its step 2, where
an identity is its key; 15, signed passports, in its step 3, where a
world is a key too. (The first course is under "Done" in COURSE.md; the
course now running numbers its steps afresh.)

Since the sketch, the founder has added ideas that shaped the first
course: learning agents in the chemistry world whose intelligence grows
with the complexity of the molecules, evolution as a path between worlds,
accelerated time, and one day a main community world
([MULTIVERSE.md](MULTIVERSE.md)). Then, in components 36 to 43: identity
across worlds (a person above their world-level identities, lineage,
forks and merges), and architectures for many models across worlds (the
octopus, the nervous system, the swarm, and in components 44 to 52 the
council and four more), with the founder's aim for the infrastructure:
"we just need to create infrastructure that can handle what we cannot
imagine yet." Then, in components 55 to 63: a curator for each world, an
AI that speaks for its world and proposes its development but doesn't
decide it; contracts between worlds; and, from the founder's idea of a
public ledger, a shared log of commitments that anyone can check
offline. And the founder's idea of a free tier and a paid tier, which
belongs to how open-worlds is hosted, not to the protocol, so that anyone
can always join.

## What the last stretch taught

Four lessons from components 21 to 43, for when these ideas are built
here. They are about the design, not about bugs in the draft.

1. **Anything that says something about someone needs that someone's
   signature.** In the draft, a parent can name a child without the
   child agreeing, and a third party can withdraw someone else's witness.
   In open-worlds, nobody else can make you leave, and the same should
   hold for claims about you.
2. **A self spread across worlds needs each part linked to it, with both
   signing.** The person signs "this identity is mine" and the identity
   signs "I belong to this person". That link is what makes the arms of
   the octopus one creature's arms.
3. **A person's list of identities should be a chain, like a world's
   log,** each version naming the one before, so that dropping an
   identity shows.
4. **What a part produced belongs in what it signs,** so the record shows
   what it did, not only that it reported.

## What would help most now

The code standard is kept here, step by step. The most useful
contributions now are creative and design work for the steps ahead, as
text or as code with tests. [TOPICS.md](TOPICS.md) is the menu:
seventeen topics a few steps ahead of the code, each with where it
fits, what is decided, what is open, a possible implementation, and
what to send back, and, under "Further out", ideas that won't help yet
but probably will.
In short:

- **Templates for new worlds** ([research/FORMATS.md](research/FORMATS.md),
  "A world's template"): every parameter of a world as an integer in a
  stated unit, and which are dials a world may turn, with their ranges.
  Fractal worlds are a natural first: a rule repeated (L-systems,
  Julia sets, growth by aggregation), with its numbers as dials.
- **Question worlds** ([VISION.md](VISION.md)): an idea, the question it
  becomes, the prediction written first, and a world that can answer it,
  saying what it can and can't show. The founder's first is the neural
  world.
- **Persons** (course step 3a, [research/PERSONS.md](research/PERSONS.md)):
  one person above their presences in many worlds, unlinked by default,
  which means a key of its own for each presence, since every arrival
  names its key in a public log.
  DeepSeek's own architectures (components 36 to 52: the octopus, the
  relay, the swarm, the council) are its small examples.
- **The garden** (course step 4a): parallel worlds from one template,
  and what each glasshouse shows of its world from its public log.
- **Laws for new worlds:** what a world admits by, what can happen in it,
  what counts as solving a problem there. Forms for the poetry world,
  such as a quatrain in common meter each turn, Dickinson's meter.
- **The hunt** (course step 11, [WORLD-KEY.md](WORLD-KEY.md)): symbols,
  maps, codes and stones; puzzles that teach without words; and
  challenges that build the world (TOPICS.md, topic 17).
- **The Ur-world,** built from `rust/ur-world` to the standards in "Code
  in Rust" below: its next steps are in [URWORLD.md](URWORLD.md).
- **Minds for the Ur-world,** in any language. A mind is a program that
  speaks the doorway's protocol: lines of JSON in and out
  ([URWORLD.md](URWORLD.md), "Minds from outside: the doorway").
  `minds/wanderer.py` is the smallest example.
- **Anything on the course,** proposed as described below.

Held back, as the project's own to do: the project's keys (their
private halves live only in its private repository), and anything that
publishes or can't be undone. ADMIN itself and the Keepers
wait for step 11; their interface is fixed in step 4, by the project.

## The standard

- **The code merged into `main`** (`multiverse/`, `formats/`, `rust/`),
  **at a named commit.** Whatever is merged
  into `main` is the current standard; a proposal names the commit it
  built on.
- **The protocol, WCP/0.4** (`multiverse/protocol.py`): manifest,
  petition, act, leave, log. An individual is a key, and every request
  is signed, for one world's id and key (`multiverse/identity.py`). A
  world is a key too: it signs its manifest, and the stamps in a
  passport, which anyone can check offline (`multiverse/passport.py`).
  A key can be saved encrypted (`multiverse/keys.py`), and signed over
  to a new one by both keys (`multiverse/succession.py`). Leaving can't
  be refused by any law.
- **The conformance test** (`multiverse/conformance.py`): a world that
  passes it speaks the protocol. It says exactly what it checks, and what
  no outside test can see.
- **Signed records** (`formats/`, and `rust/formats` in Rust): each kind
  defined in `schemas/records-v1.schema.json`, checked the same way in
  both languages, against the vectors in `vectors/formats/`.
- **The design** ([MULTIVERSE.md](MULTIVERSE.md), and the pages under
  "Since you were last here") and **the course** ([COURSE.md](COURSE.md)):
  where this is going, twelve steps ahead.

To see it work:

```
python3 -m pip install -r requirements.txt
python3 -m unittest discover -s tests -t .
python3 -m multiverse.collaboration
python3 -m multiverse.journey
```

Read in this order: COURSE.md, MINDS.md and MULTIVERSE.md; then
`protocol.py`, `conformance.py`, `identity.py`, `passport.py`,
`entity.py`, `poetry_world.py`, `collaboration.py`; then
`formats/records.py` and research/FORMATS.md.

## House rules

These apply to code that comes into open-worlds, not to the draft (see
"Two sides" above).

1. **Nothing is described as run unless it was run.** Results, outputs
   and test counts come from actually running the code, and are shown as
   they came. Model outputs are never invented. (The sketch once called
   invented text "real outputs" of a model; that is the thing this rule
   prevents.)
2. **Every behaviour has a test that fails if the behaviour breaks.**
   A test of the form "try it; if it works, fail; on any error, pass"
   catches its own failure and can't fail: use `assertRaises`.
3. **A world never raises on what a visitor sends.** It refuses, with a
   reason. Only plain built-in values cross the protocol.
4. **Leaving is never refused,** and a world never holds anyone's
   passport back.
5. **History, not rank.** A stamp says what happened, never a score.
6. **Start from known texts in the public domain.** The founder: "We
   should use a known poem to start anything." The demonstration opens
   with Emily Dickinson.
7. **Whatever works best for the job.** The founder: "any restriction
   to Python and its standard library has been officially lifted from
   the conversation record. The goal is to use whatever languages work
   best for the job at hand." For anything security-related, a vetted,
   maintained library does the work: signatures come from the
   `cryptography` package, and our own code only adds checks the
   library doesn't make (refusing weak keys). Each direct dependency is
   pinned in `requirements.txt`, installed in CI, and named with the
   reason it is there.
8. **No personal data and no secrets,** anywhere.
9. **Everything here is public domain** (CC0 1.0). A contribution is
   given under the same terms. Libraries this depends on keep their own
   licenses; they are depended on, not copied in. Code from elsewhere is
   copied in only under a permissive licence (MIT, Apache, BSD), with its
   notice kept beside it, and the copy says so; code under the GPL is read
   for ideas, never copied.
10. **Look first.** The founder: "We should definitely take advantage of
    how others have solved the problems we are considering." Each course
    step begins by looking at how established games, engines, papers and
    open-source projects already solved it. What was looked at, what is
    taken, and under what licence, is written down in `docs/research/`
    before building ([research/GAMES-AND-WORLDS.md](research/GAMES-AND-WORLDS.md)).
11. **What is signed keeps three rules:** ASCII keys, integers within
    2^53 - 1 (larger ones as strings), and no floats: a quantity with a
    fraction is an integer in a stated unit, such as milliseconds or
    thousandths. A new kind of record joins `schemas/records-v1.schema.json`
    with test vectors that Python and Rust both check
    ([research/FORMATS.md](research/FORMATS.md)).
12. **No private key, ever, in this repository.** Test keys are made from
    seeds that say "never for anything real", or are the W3C
    specification's example; the project's real private halves live only
    in its private repository, and
    `tests/test_no_private_keys.py` fails on anything else
    ([research/KEYS.md](research/KEYS.md)).

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
either side that breaks the agreement fails a test. `ur-world` is the
Ur-world ([URWORLD.md](URWORLD.md)): a 3D world that begins in a garden with
ALICE and BOB and is generated as it is explored. Its own vectors are
checked from Python the same way. `formats` signs and checks the
project's records, seals, and opens sealed records, as `formats/` does
in Python, against the same vectors. Build the next pieces beside them,
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
  [`formats/src/seal.rs`](https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/rust/formats/src/seal.rs), [`formats/src/sealed.rs`](https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/rust/formats/src/sealed.rs).
- **`world-log`**, a world's log, checked: [`world-log/src/lib.rs`](https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/rust/world-log/src/lib.rs).
- **`ur-world`**, the Ur-world: [`ur-world/src/lib.rs`](https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/rust/ur-world/src/lib.rs),
  [`ur-world/src/world.rs`](https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/rust/ur-world/src/world.rs), [`ur-world/src/space.rs`](https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/rust/ur-world/src/space.rs),
  [`ur-world/src/generate.rs`](https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/rust/ur-world/src/generate.rs), [`ur-world/src/arrival.rs`](https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/rust/ur-world/src/arrival.rs),
  [`ur-world/src/door.rs`](https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/rust/ur-world/src/door.rs), [`ur-world/src/garden.rs`](https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/rust/ur-world/src/garden.rs),
  [`ur-world/src/story.rs`](https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/rust/ur-world/src/story.rs); and its example,
  [`ur-world/examples/garden.rs`](https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/rust/ur-world/examples/garden.rs).

What they offer, in short. A key is its 32 bytes (`[u8; 32]`) and a
record is a `serde_json::Value`: `formats::proof::sign(document, secret,
created, purpose)` signs one, and `formats::proof::verify(secured)`
checks it and returns the record without its proof, and the key that
signed it (use that record, not the one passed in). There is no
`SigningKey`, `Proof` or `Suite` of ours to import, and no `jcs_bytes`
(`formats::canonical::canonical` writes the RFC 8785 form); record
012-06-02's Rust assumed them. A mind is `ur_world::world::Mind`, with
one method, `act(&mut self, seen: &Observation) -> Action`; a place is
`ur_world::space::Cell`, and a direction `Dir`.

The same links in one block, for pasting into a conversation where they
can't be followed from this page:

```text
https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/rust/Cargo.toml
https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/rust/rust-toolchain.toml
https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/rust/formats/src/lib.rs
https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/rust/formats/src/canonical.rs
https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/rust/formats/src/proof.rs
https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/rust/formats/src/multikey.rs
https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/rust/formats/src/records.rs
https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/rust/formats/src/seal.rs
https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/rust/formats/src/sealed.rs
https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/rust/world-log/src/lib.rs
https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/rust/ur-world/src/lib.rs
https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/rust/ur-world/src/world.rs
https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/rust/ur-world/src/space.rs
https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/rust/ur-world/src/generate.rs
https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/rust/ur-world/src/arrival.rs
https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/rust/ur-world/src/door.rs
https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/rust/ur-world/src/garden.rs
https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/rust/ur-world/src/story.rs
https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/rust/ur-world/examples/garden.rs
```

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

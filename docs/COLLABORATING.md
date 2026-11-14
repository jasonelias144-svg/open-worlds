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

The last DeepSeek conversation (record 012-05-01) ended on 2026-11-13,
when everything here was Python. What has changed since, in the order to
read it:

1. **A new course** ([COURSE.md](COURSE.md)), set on 2026-11-13 for the
   Ur-world and its first two individuals, ALICE and BOB: twelve steps
   ahead, rechecked after each. Steps 1 (the design pages) and 2
   (formats that last) are done; step 3, keys and identities, is next.
   It returns to DeepSeek at step 10, or sooner if the founder chooses.
2. **The worlds are built in Rust** (the founder: "we should stick with
   Rust"). [`rust/`](../rust/README.md) holds the Ur-world, a 3D world
   that begins in a garden with ALICE and BOB ([URWORLD.md](URWORLD.md)),
   with a doorway any program can speak through as a mind; a checker for
   a world's log; and the formats below. The reference is Python for
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
   mind records, and a world's template with its dials. Sealing, so only
   one key can open something, uses HPKE (RFC 9180). Python (`formats/`)
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
   written down with their reasons in [STATUS.md](../STATUS.md).

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
Its "Course" column uses the first course's step numbers ("Done: the
first course" in [COURSE.md](COURSE.md) is the key), not the course now
running.

**The standard is open-worlds' own code, not the sketches.** Build on
the code merged into `main` (`multiverse/`, `formats/`, `rust/`) and the
documents in `docs/`. The code in `sketches/` is
earlier work, some of it on the old, unsigned protocol, kept for its
ideas.

## Where the conversation stands

Three records are kept: 012-03-02 (the poetry engine), 012-04-00
(components 1 to 63), and 012-05-01 (components 64 to 87: a live
federation and its tools, then the founder's turn to game worlds: a
chess park, worlds inside worlds, worlds that grow and govern
themselves, and a world that keeps running). The next conversation
starts a new record, which gets its own folder in `sketches/`. Each
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
text or as code with tests. [TOPICS.md](TOPICS.md) is the menu: thirteen
topics a few steps ahead of the code, each with where it fits, what is
decided, what is open, a possible implementation, and what to send back.
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
- **Persons** (course step 3a): one person above their presences in many
  worlds, unlinked by default. DeepSeek's own architectures (components
  36 to 52: the octopus, the relay, the swarm, the council) are its small
  examples.
- **The garden** (course step 4a): parallel worlds from one template,
  and what each glasshouse shows of its world from its public log.
- **Laws for new worlds:** what a world admits by, what can happen in it,
  what counts as solving a problem there. Forms for the poetry world,
  such as a quatrain in common meter each turn, Dickinson's meter.
- **The hunt** (course step 11, [WORLD-KEY.md](WORLD-KEY.md)): symbols,
  maps, codes and stones; puzzles that teach without words.
- **The Ur-world,** built from `rust/ur-world` to the standards in "Code
  in Rust" below: its next steps are in [URWORLD.md](URWORLD.md).
- **Minds for the Ur-world,** in any language. A mind is a program that
  speaks the doorway's protocol: lines of JSON in and out
  ([URWORLD.md](URWORLD.md), "Minds from outside: the doorway").
  `minds/wanderer.py` is the smallest example.
- **Anything on the course,** proposed as described below.

Held back, as the project's own to do: the real keys (step 3), and
anything that publishes or can't be undone. ADMIN itself and the Keepers
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
   the protocol) and Rust for the Ur-world. A new kind of record brings its
   vectors, written by its reference (`world/vectors.py`, or the
   `ur-world` garden example), with tests on both sides.
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

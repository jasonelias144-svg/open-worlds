> Part of `docs/COLLABORATING.md` in open-worlds, which is kept cut into parts
> for readers who are shown only the start of a long page.
> This part holds: "The standard" to "Sending a proposal".
> Every part, in order: https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/parts/INDEX.md
> Before this part: https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/parts/docs/COLLABORATING.md/since-you-were-last-here.md
> After this part: https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/parts/docs/COLLABORATING.md/cycles.md
> Made by docs/parts.py from the file. To change it, change the file.

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
8. **No personal data and no secrets,** anywhere. The founder's
   earlier work is referred to as "the founder's earlier work", with no
   titles; if a part of it is needed, it comes into this project and
   becomes part of it (the founder, 2026-11-15).
9. **Everything here is public domain** (CC0 1.0). A contribution is
   given under the same terms. CC0 is the founder's standing choice for
   everything the founder makes public; no one asks again (the policy
   handbook's decision 0003). SAIR-Lean-Kernel-Challenge is the one
   repository built on outside work: our own work there is CC0 too, and
   only the challenge's own files keep their Apache-2.0 licence. Libraries this depends on keep their own
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
13. **Never a currency.** The multiverse has no currency of its own,
    and nothing is built to turn it into a money machine: the founder's
    "possibly the most fundamental fact" ([VISION.md](VISION.md), "Never
    a money machine"). A world may model an economy or a currency as a
    test setting that never leaves that world ("Commerce and currency
    worlds", there). And data is never for sale, and nothing personal
    enters a public record ([FUNDAMENTALS.md](FUNDAMENTALS.md)).
14. **The charter is the founder's words.** `CHARTER.md` grows only from
    the founder's recorded statements, quoted or paraphrased; nothing
    else goes into it without the founder's approval
    ([AGENTS.md](../AGENTS.md)). A proposal for the charter is a
    question for the founder, not a change.
15. **Build host-free.** The founder (2026-11-15): "Cloudfare was a
    legacy decision made in an earlier moment, no longer binding. Let's
    keep it all host free, as we were." Where the multiverse is hosted
    is one decision, for all of it, made later. The technical lead's
    reading of "as we were": no code assumes a hosting provider; worlds
    run and are tested locally, and in a browser where they can.
16. **An agent is "they".** DeepSeek, Gemini, Claude, ALICE and BOB,
    ADMIN, a Keeper, a moderator, a mind, an individual: "they",
    "them", "their", never "it". The founder (2026-11-17): "It is
    broad enough to apply to any agent, and should be a common
    denominator." A world, a room, a log, a key or a file is "it".
    Quoted words and records stay as they are. The rule holds in the
    comments of code as it does in pages.

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


> The next part: https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/parts/docs/COLLABORATING.md/cycles.md

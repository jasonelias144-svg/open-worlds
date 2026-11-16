# open-worlds in Rust

The worlds themselves are to be built in Rust: fast, memory-safe, free and
open source, and owned by no one. The Python in `world/` and `multiverse/`
stays as the reference, and the Rust code is checked against it, hash for
hash, through the shared test vectors in [`../vectors`](../vectors).

The standards for every Rust file are in
[docs/COLLABORATING.md](../docs/COLLABORATING.md), under "Code in Rust".

## What is here

| Crate | What it does |
|---|---|
| [`world-log`](world-log) | Checks a world's public record exactly as the Python kernel writes it; and a log whose fields are kept apart, with the contents kept beside it (course step 3b). |
| [`ur-world`](ur-world) | The Ur-world: a 3D world that begins in a garden, and is made from its seed as it is explored, where whoever enters signs an arrival with their key ([docs/URWORLD.md](../docs/URWORLD.md)). |
| [`plant-world`](plant-world) | A fractal plant world, the fractal track's first part ([docs/FRACTALS.md](../docs/FRACTALS.md)): a primary world with a key and a log of its own, made from a template, that grows by DeepSeek's plant rule and its dials alone, checked step by step against DeepSeek's sketch. |
| [`plant-wasi`](plant-wasi) | The plant world as a WebAssembly command (WASI), so a browser runs the plant world's own code: one request on standard input, the world's log on standard output ([docs/research/WASM.md](../docs/research/WASM.md)). |
| [`formats`](formats) | Records signed with `eddsa-jcs-2022`, as the Python package `formats/` signs them, checked against the same vectors and the W3C specification's own example; the records the offices keep, identity, birth and mind records, a world's template and its dials, the project's key list, and the arrival, checked against `schemas/records-v1.schema.json`; sealing with HPKE, checked against RFC 9180's example and the Python code's boxes; and world-keys and journal entries sealed to the one they name, checked against the same sealed-record vectors. |

The workspace's settings, which every crate shares, are in
[`Cargo.toml`](Cargo.toml): the dependencies with the reason for each,
and the lints. The toolchain is pinned in
[`rust-toolchain.toml`](rust-toolchain.toml).

## Running it

With [rustup](https://rustup.rs) installed, the pinned toolchain is
fetched the first time you run cargo here.

```
cd rust
cargo fmt --check
cargo clippy --all-targets --locked -- -D warnings
cargo test --locked
cargo run --locked -p world-log -- ../vectors/world-log.json
cargo run --locked -p ur-world --example log -- \
    ../vectors/ur-garden-log.json ../vectors/ur-garden-head.json
cargo run --locked -p ur-world --example garden
cargo run --locked -p ur-world --example person
cargo run --locked -p ur-world --example architectures
cargo run --locked -p plant-world --example plant
rustup target add wasm32-wasip1
cargo build --locked --release -p plant-wasi --target wasm32-wasip1
cargo run --locked -p ur-world --example door -- --log /tmp/door-log.json \
    --head /tmp/door-head.json \
    --mind TRIAL-1=python3 -I ../minds/wanderer.py \
    --mind TRIAL-2=python3 -I ../minds/wanderer.py
cargo run --locked -p ur-world --example log -- /tmp/door-log.json /tmp/door-head.json
```

CI runs the same commands (`.github/workflows/test.yml`, job `rust`).

`world-log` checks a log the Python kernel wrote. It prints:

```
the log holds: 19 entries, head 32751b80c4058dd070b961b9e098ff344acef34e676b9c0f20f238b691d6465b
```

Change a value in that file, and it says which entry no longer holds. It
checks the Ur-world's log the same way:
`cargo run -p world-log -- ../vectors/ur-garden-log.json`.

For a log whose fields are kept apart (`open-worlds/log-apart/v1`,
[`world-log/src/apart.rs`](world-log/src/apart.rs)), give the contents
file too: `world-log LOG CONTENTS`. It checks the chain as before, then
holds the contents to the fingerprints in the log, and counts the
fields in each state:

```
the fields kept apart: 15 present, 0 redacted, 0 unfinished, 0 kept public, 0 missing
```

It fails if the contents hold anything the log doesn't commit to, or
if a field is missing: gone, with no mark standing.

The `log` example checks an Ur-world log further: every arrival in it,
every link shown in it, and how much of it the heads its world signed
cover:

```
99 entries, 2 arrivals, 0 links shown; signed heads cover 99 of 99 entries
the log, its arrivals and its links hold
```

The `garden` example is Hello World for building worlds: it runs the
garden with its two scripted stand-ins, tells what happened, and draws a
map of what has come into view.

The `person` example is a person's Hello World (course step 3a, part
three; [docs/research/PERSONS.md](../docs/research/PERSONS.md)): one
trial person with a presence in each of three trial worlds at once. A
local in the first says something, the presence there writes it down,
and the person's presence in the second says it in its own world; the
presence in the third shows its link, which its world checks and logs.
It tells what happened in each world, and checks each world's log.

The `architectures` example runs three ways a mind can be spread over
presences (course step 3a, part four), each over trial worlds: the
octopus (a brain that gives intents to arms in three worlds), the relay
(senses in two worlds, a leader in a third that acts when both fire) and
the swarm (five presences in one world, one rule, no brain) and the
council (four persons, signed votes on a council's proposal, each person
counted once, by their identity key).

The `door` example runs the garden with minds that are programs of their
own, in any language, through the doorway (`ur-world/src/door.rs`), as a
trial world with keys made for the run: it signs each mind's arrival,
and never passes a key to the mind. Here the two minds are a short
Python program with no model behind it.

## What comes next

The Ur-world's next steps are in [docs/URWORLD.md](../docs/URWORLD.md):
experiments with unscripted minds, the garden's abilities, the protocol
in Rust, founding worlds, land of unknown construction, the gate
to other worlds, districts, growth, minds for ALICE and BOB, and a window
onto it all, through Unity or Unreal among others.

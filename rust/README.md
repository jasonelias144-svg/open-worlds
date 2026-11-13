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
| [`world-log`](world-log) | Checks a world's public record exactly as the Python kernel writes it. It's the first piece of the world kernel. |

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
cargo run --locked -- ../vectors/world-log.json
```

CI runs the same commands (`.github/workflows/test.yml`, job `rust`).

The last command checks a log the Python kernel wrote. It prints:

```
the log holds: 19 entries, head 32751b80c4058dd070b961b9e098ff344acef34e676b9c0f20f238b691d6465b
```

Change a value in that file, and it says which entry no longer holds.

## What comes next

The plan, to be put on the course ([docs/COURSE.md](../docs/COURSE.md)):
the world kernel itself, in Rust: the same rules, writing the same log as
`world/core.py` for the same seed and the same actions. After that, the
protocol, and then the bridge that lets worlds built with Unity or Unreal
speak it.

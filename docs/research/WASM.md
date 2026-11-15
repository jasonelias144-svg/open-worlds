# Rust in the browser

Research for the fractal track's part 4 ([FRACTALS.md](../FRACTALS.md)),
and for living worlds' first stage, an endless plant in the browser. It
was done on 2026-11-15 under house rule 10, "look first"
([COLLABORATING.md](../COLLABORATING.md)). Part 4 asks that "the browser
runs the same code the reference does": the plant world's own Rust,
rather than a copy of its rule written again in JavaScript, as Plant
Watch has today.

Every result below comes from a run on 2026-11-15, on this repository's
pinned toolchain (Rust 1.97.0), with `--locked`.

## What it has to keep

The workspace's rules ([COLLABORATING.md](../COLLABORATING.md), "Code in
Rust"):
- **Pinned stable Rust,** with nothing nightly.
- **No `unsafe`:** the workspace forbids it, and a crate can't loosen
  that.
- **Few dependencies,** all free, with `Cargo.lock` committed.
- **The same in, the same out:** no clock and no randomness inside a
  world.

## Two ways, tried

**1. `wasm32-unknown-unknown`, the usual browser target, with
wasm-bindgen.**
- **It doesn't build today.** `cargo build -p plant-world --target
  wasm32-unknown-unknown` fails in getrandom 0.4.3. The signing and
  sealing crates under `formats` pull it in, and on this target it
  refuses to build unless its `wasm_js` feature is turned on. That
  feature brings in wasm-bindgen and js-sys.
- **It needs `unsafe` or generated code.** Handing a Rust function to
  JavaScript on this target takes either `#[unsafe(no_mangle)]`, which
  the workspace forbids, or wasm-bindgen's generated code and its
  generated JavaScript.

**2. `wasm32-wasip1`, WebAssembly with WASI's first system interface.**
- **It builds as it is.** `cargo build -p plant-world --target
  wasm32-wasip1` succeeds, `--locked`, with no change to any crate.
- **A command needs only `main`.** It is a program that reads standard
  input and writes standard output. It exports no function, so it needs
  no `unsafe`, and no dependency beyond the plant world's own.
- **What it asks for, exactly.** Built in release, the command
  (`rust/plant-wasi`) is 294 KB. It asks the host for five WASI calls and
  nothing else: `environ_get`, `environ_sizes_get`, `fd_read`,
  `fd_write` and `proc_exit`. It asks for no clock, no randomness and no
  files, which the list of its imports proves.

## What was run

- **The prototype, under Node's own WASI** (`node:wasi`, Node 22.22.0).
  The four worlds without a pot in `vectors/plant-world.json` grew logs
  identical to the vectors.
- **The prototype, in Chromium,** with a page that gives the five calls
  by hand:
  - the same four logs, identical;
  - 1 to 9 ms a world on this machine;
  - a bad key exits with 1, and its reason on standard error.
- **The crate, `rust/plant-wasi`:**
  - its Rust tests grow all five worlds in the vectors, the one in a pot
    too, and refuse fifteen malformed requests, each with its reason;
  - `tests/web/wasi.test.mjs` runs the built command through the page's
    shim (`web/lib/wasi.js`) in Node, and gets the same five logs;
  - the same request gives the same bytes;
  - a command that asks for any other call (a clock, in the test) isn't
    run.

## Taken

The technical lead's decision: **a WASI command, with the page's own
shim for the five calls.** No wasm-bindgen.

Why:
- No `unsafe`, and no new dependency.
- The same file runs in the browser and in Node, so CI tests exactly
  what the page runs.
- What it can ask of the page is fixed and short, and a test checks it.

## What it costs, and what isn't done

- **Each run starts fresh.** A request grows a world from its first
  entry. A world that runs for hours will hand its state over as a
  checkpoint instead, as living worlds' first stage plans.
- **Its size.** 294 KB. What fills those bytes wasn't measured.
  Splitting out only what a plant needs might shrink it; not tried.
- **The page must be allowed to compile WebAssembly.** Its
  Content-Security-Policy needs `'wasm-unsafe-eval'`, which allows
  compiling WebAssembly and nothing else (not JavaScript's `eval`).
- **The `.wasm` file is built, not committed.** A page finds it where
  `cargo build --locked --release -p plant-wasi --target wasm32-wasip1`
  puts it.
  A published site would need a build step, and where the site is
  published is the founder's call (FRACTALS.md, "Waiting on the
  founder").

## Not checked

- Firefox and Safari.
- Whether wasm-bindgen's generated code builds under
  `unsafe_code = "forbid"`.
- WASI's later versions (`wasm32-wasip2`, the component model).
- How fast a world is after hours of growth: part 4 measures it with the
  endless plant.
- Whether the `.wasm` file's bytes are the same when built on another
  machine.

# web: the web app for watching worlds

Set aside on 2026-11-14 at the founder's word: "Let’s set aside some
space just to develop a web app that also includes the multiversal map."
The plan is in [../docs/FRACTALS.md](../docs/FRACTALS.md).

## Built

- **[`plant/`](plant/index.html), Plant Watch:** a plant world replayed
  tick by tick from its own log, with play and a slider (the fractal
  track's part 2). Before it draws anything, it checks four things, and
  lists each with what it found:
  - the log's chain of hashes, written as the Python kernel writes them;
  - the log as the Rust world writes it: every entry grown again in the
    page and compared whole, every field but the hash, as
    `rust/plant-world`'s `log_problems` does, so nothing the rule didn't
    write can pass;
  - the world's signed head: its format, read field for field as
    records-v1 has it (a head with any other field is refused, even
    signed), its world, and its Ed25519 signature checked with the
    browser's own WebCrypto, and that it covers the whole log;
  - the birth record, signed by the world and read field for field the
    same way: its template, its law, and exactly the dials it changed
    from the template's values;
  - the log grown again by the plant world's own Rust code, compiled to
    WebAssembly (`rust/plant-wasi`), and compared whole, hash for hash.
    The `.wasm` file is built, not committed: `cd rust && cargo build
    --locked --release -p plant-wasi --target wasm32-wasip1` puts it
    where the page looks, and where it isn't built the page says so.

  A log that fails the chain or the rule isn't drawn. Where the browser
  can't check Ed25519, the page says so rather than claiming it did.
  Who signed the template is not checked here.

  To run it, serve the repository's folder and open the page:
  `python3 -m http.server`, then `http://localhost:8000/web/plant/`.
  It reads `vectors/plant-world.json`, five worlds the Rust plant world
  grew, unless `?log=` names another file on the same site, by a
  relative path; any other address is refused. `?world=` names the
  world to show first, by its key, as the map's cards do. A log can
  also be opened from disk.
- **[`map/`](map/index.html), the World Map:** the first map (the
  fractal track's part 3; [../docs/FRACTALS.md](../docs/FRACTALS.md),
  "The multiversal map"). A card for the Ur-world, and under it its
  garden drawn from above, with a card for each world it hosts, built
  only from what each world publishes:
  - **The Ur-world:** its log's chain, and its signed head over the
    whole log, before anything it says is shown. Its rules, seed, and
    how far along it is come from its log and head. Its ground, tree
    and spring are drawn as the rules its log names lay them out
    (`ur-world/0.4` and `0.5`, in `rust/ur-world/src/generate.rs`);
    under other rules, only the places its log names are drawn.
  - **Each hosted world:** where the garden's log puts its glasshouse,
    and how many steps of its time the garden gave it; its birth record
    (its name, its template and law by hash, and the dials it set: each
    within the template's range, and exactly those its log was made with
    where its log is given, holds, and begins with the entry the
    garden's log names); its signed head, which must end where
    the garden's log last tended it; and its log's chain. A card whose
    records hold opens onto the world's live view, Plant Watch.
  - **Not here:** whether the garden tended each world one step a tick,
    in order (Rust's `hosting_problems` and the Python vectors test check
    that); each plant's growth by its rule (its live view does); and
    whose world the Ur-world is: any log and head that hold together are
    shown as the Ur-world, since its key isn't yet compared with the
    project's key list (`keys/key-list.json`). In the shared vectors it
    is a trial key.

  It reads `vectors/ur-garden-log.json`, `ur-garden-head.json` and
  `ur-garden-hosted.json`, which the Rust garden writes.
- **[`lib/checks.js`](lib/checks.js), the checks the pages share:** the
  log format's hashes, keys, and records signed the standard way, read
  field for field, and how Plant Watch words a log against its world
  grown again (`grownAgain`). One file, so the pages check the same way,
  and `tests/web/` runs it in Node against the shared vectors, in CI.
- **[`lib/wasi.js`](lib/wasi.js), the WASI shim:** runs a WebAssembly
  command, such as the plant world's, giving it the five calls it uses
  (standard input and output, an empty environment, exit) and nothing
  else: a command that asks for any other call, a clock or randomness
  say, isn't run ([../docs/research/WASM.md](../docs/research/WASM.md)).

Nothing is loaded from outside the site: each page's
Content-Security-Policy lets the browser load nothing but the page and
the web app's own scripts, compile WebAssembly but never evaluate text
as script, and connect only to its own site, and
`tests/test_web_pages.py` checks that every page carries such a policy,
loads only the web app's own scripts, and names no outside address.

What it will be:

- **A static site, with no server.** It reads worlds' public logs and
  signed heads, and draws them: first a fractal plant growing, tick by
  tick; then a garden of plants; then the multiversal map, a card for
  each world opening onto its live view (the first, of the Ur-world's
  garden, is built).
- **It checks before it shows.** A log's chain and its signed heads are
  checked in the page, and the page says what it checked and what it
  didn't.
- **The same code as the worlds.** The fractal worlds are built in Rust;
  compiled to WebAssembly, the same code runs in the page, so a world can
  be computed from its seed without a server. Begun: Plant Watch grows
  each plant again with the plant world's own code.
- **Private until the founder decides** where, and whether, it is
  published.

Rules for code here, as everywhere in the repository
([../docs/COLLABORATING.md](../docs/COLLABORATING.md)): every file whole,
with tests; nothing loaded from outside the site except libraries pinned
to exact versions; no tracking, no accounts, and no data sent anywhere.

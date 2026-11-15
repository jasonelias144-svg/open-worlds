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
  - the world's signed head: its format, its world, and its Ed25519
    signature checked with the browser's own WebCrypto, and that it
    covers the whole log;
  - the birth record, signed by the world: its template, its law, and
    exactly the dials it changed from the template's values.

  A log that fails the chain or the rule isn't drawn. Where the browser
  can't check Ed25519, the page says so rather than claiming it did.
  Who signed the template is not checked here.

  To run it, serve the repository's folder and open the page:
  `python3 -m http.server`, then `http://localhost:8000/web/plant/`.
  It reads `vectors/plant-world.json`, five worlds the Rust plant world
  grew, unless `?log=` names another file on the same site, by a
  relative path; any other address is refused. A log can also be opened
  from disk. One file, with no library and nothing loaded from outside:
  its Content-Security-Policy lets the browser load nothing but the page
  itself and connect only to its own site, and `tests/test_web_pages.py`
  checks that every page carries such a policy and names no outside
  address.

What it will be:

- **A static site, with no server.** It reads worlds' public logs and
  signed heads, and draws them: first a fractal plant growing, tick by
  tick; then a garden of plants; then the multiversal map, a card for
  each world opening onto its live view.
- **It checks before it shows.** A log's chain and its signed heads are
  checked in the page, and the page says what it checked and what it
  didn't.
- **The same code as the worlds, later.** The fractal worlds are built in
  Rust; compiled to WebAssembly, the same code runs in the page, so a
  world can be computed from its seed without a server.
- **Private until the founder decides** where, and whether, it is
  published.

Rules for code here, as everywhere in the repository
([../docs/COLLABORATING.md](../docs/COLLABORATING.md)): every file whole,
with tests; nothing loaded from outside the site except libraries pinned
to exact versions; no tracking, no accounts, and no data sent anywhere.

# web: the web app for watching worlds

Set aside on 2026-11-14 at the founder's word: "Let’s set aside some
space just to develop a web app that also includes the multiversal map."
The plan is in [../docs/FRACTALS.md](../docs/FRACTALS.md); nothing is built
here yet.

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

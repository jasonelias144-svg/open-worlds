# The fractal track: worlds that grow, and a page to watch them

A track alongside the course ([COURSE.md](COURSE.md)), set on 2026-11-14:
fractal worlds, built in Rust on the foundations the course has laid, and
a web app to watch them grow, which is also the first home of the
multiversal map. Its plants are hosted in the Ur-world's garden, rules
alone, so it runs beside the course's steps without changing their order
or anything ALICE and BOB need.

## Decided

In the founder's words (STATUS.md, "Decided", 2026-11-14):

- "I do want to move forward with the fractal worlds, I am eager to see
  visuals of fractals grown over time in expanding worlds. I am trying to
  drive that forward to where we could have a web app that would allow me
  to monitor some ongoing simulation run of fractal plants."
- "Marvelous! It is a perfect first web app for viewing world
  simulations. Let’s set aside some space just to develop a web app that
  also includes the multiversal map." And: "I can brainstorm the whole
  multiversal map with DeepSeek later. But it will be good to have it on
  the radar."
- "And on the ALICE and BOB comment, we are working up to that and is
  why I am suggesting we experiment
  with minimally sufficient models, and so lightweight and capable of
  choice for the fractal worlds. We are working towards ALICE and BOB who
  will be the first inhabitants to persist once is running. That is
  later."
- On change: "nothing set in stone yet, let’s explore different ideas.
  [...] it may differ by world". How a world may change (not at all, in
  place, by branching, sandboxed) is left open, and may differ by world.
- On language, after that evening, to DeepSeek (record 012-06-02, as
  extended on 2026-11-15, line 52822): "My preference would be to move to
  Rust, I only wanted us to transition naturally, as we are doing now.
  Let’s move forward in Rust, or other languages when needed, but
  primarily to Rust." This replaces the founder's word of the evening
  before, that DeepSeek sketches in the language it chooses (it chose
  Python) and the project ports it downstream. So
  DeepSeek now writes primarily in Rust, as proposals: it can't compile
  them, so the project compiles, tests and fits them to the current code.
- On the Ur-world, to DeepSeek (the same record, line 50034): "This is
  exactly how I envisioned the Ur-world, ALICE and BOB is a microverse
  garden of hosted fractal worlds."

Fractal worlds are primary worlds, made from a template whose dials
are the rule's numbers (TOPICS.md, topic 1; VISION.md, "A hierarchy of
worlds"). The founder, 2026-11-15: "Rules only and AI inside are not different. I was
looking for a basic choosing and learning model, like a single neuron.
This is not the same AI as will be used for ALICE and BOB, perhaps we
can use a weaker term, “learning and choosing monad”, but we can just
consider it a primitive learning model. So no tension." The technical
lead's reading of it, which stands unless the founder answers otherwise:
a primitive learning model inside a fractal world doesn't stop it being
primary; it is part of the world's workings, as its rules are, and not
the AI that ALICE and BOB will have; and whether a world has one is
that world's. (This replaces the technical lead's earlier reading,
which kept learners out of the plant worlds.)

And the founder's Ur-world word meets the decision of 2026-11-13: "Once
we work out that world, we can begin creating subworlds" (URWORLD.md).
Plant worlds hosted in the Ur-world's garden are small subworlds from the
start. The technical lead's reading, put to the founder on 2026-11-15
(it stands unless the founder answers otherwise): the newer word wins,
and only primary worlds are hosted early, rules alone, so the Ur-world's
own design is not changed by them; subworlds with laws, Keepers or minds
of their own still wait for the Ur-world to be worked out.

## What there is to start from

- **DeepSeek's sketches,** record 012-06-02: an atomic fractal plant,
  its parameters from inside and outside, branching, a garden of plants,
  the Game of Life, elementary and grid automata, chaos games where
  choice enters, two worlds coupled, and a gallery of mixed worlds. Their
  code is in `sketches/deepseek/012-06-02/`, and after the first round of
  fixes (#63) every test passes for most of the fractal worlds
  ([sketches/INDEX.md](../sketches/INDEX.md) says which).
- **A first look:** DeepSeek's garden, rule 90, the chaos game and Life,
  run as written and played back tick by tick, shared with the founder as
  a private page on 2026-11-14.
- **The foundations, in Rust:** a world's log, hash-chained and checked
  (`rust/world-log`); records-v1, signed the standard way, with a world's
  template and its dials (`rust/formats`); and a world's signed log heads
  (`open-worlds/log-head/v1`, `rust/ur-world`).

## The plan

Building on the recommendation put to the founder the same evening (the
track, a Rust plant world, and a page with no server; it stands unless
the founder answers otherwise): the five parts, and their order, are the
technical lead's. Each part is one reviewed pull request.

1. **A fractal plant world in Rust.** A primary world with its own key
   and log, made from a template; whole-number geometry; growth decided
   by its rule and dials alone, so the same template gives the same log
   on any machine. The first rule is DeepSeek's plant (each tip splits in
   two at 45 degrees, to a depth), so the Rust world can be checked step
   by step against the Python sketch with shared vectors; plants that
   look more like plants (rewriting rules, L-systems: TOPICS.md, topic 1)
   come second. The world expands as it grows: its bounds follow the
   plant, with no pot wall unless the template sets one. Its log's heads
   are signed by its key, as the Ur-world's are.
2. **The web app, first page: a plant growing.** A static site in `web/`
   ([web/README.md](../web/README.md)), with no server: it reads a world's
   public log and draws it, tick by tick, with play and a slider, as the
   first look did. It checks the log's chain and its signed heads before
   it shows anything, and says what it checked.
3. **The Ur-world's garden hosts the plants, and the map's first page.**
   Several plant worlds from one template, each with its own key, log
   and changed dials, hosted in the Ur-world's garden, as the founder
   pictured it: "a microverse garden of hosted fractal worlds". The
   garden gives them time and a place; walking among them is the
   Ur-world's own walking, tended by its stand-ins (WALKER and GARDENER)
   until ALICE and BOB are born (course step 9). The web app gains its
   first map: a card for each world, built only from what the world
   publishes, opening onto its live view (below, "The multiversal map").
   DeepSeek's Rust Ur-garden (record 012-06-02, as extended, from line
   52842) is an input here, once compiled and checked against the
   current code.
4. **Running on, with no server.** Since a world is deterministic, the
   page can compute where a world is now from its template, its seed and
   the time since its birth, with every change from outside a signed
   record in its log: Rust compiled to WebAssembly, so the browser runs
   the same code the reference does. A world that runs on a machine of its
   own, all the time, costs money, so it is the founder's decision, and
   waits for it.
5. **More families, and choice.** Automata and chaos games, as DeepSeek
   sketched them; then primitive learning models that choose (DeepSeek's
   lookup table and four-unit network; the founder's "learning and
   choosing monad"), in any fractal world whose template has one: the
   first rungs of the ladder that leads to
   step 8's audition, which measures what is minimally sufficient for
   ALICE and BOB. A learner learns from rewards, and ALICE and BOB will be
   language models that speak, so the learners teach about choice and
   don't become them.

How each world may change is its own: a template can say that no change
is taken, or that a change makes a branch and the original continues, or
that the world is sandboxed from others. The first plant world takes no
change from outside; the choices come later, one world at a time.

## The multiversal map

On the radar, to be brainstormed with DeepSeek (TOPICS.md, topic 16).
What the founder pictured: "I imagine walking into an amusement park
[...]. I unfold the brochure map and investigate the worlds to explore.
In our case, you could tap on the map for a given world and get
information or a detailed map, but also a live view of the world in some
standard lobby location for each world. It is where you land when
entering a new world."

The recommendation, put the same day (it stands unless the founder
answers otherwise), as a starting point for that brainstorm:

- **A card for each world, built from what the world publishes:** its
  birth record (name, kind, key), its template and changed dials, and its
  latest signed head (that it is alive, and how far along). So anyone can
  check a map, and anyone can make another: no map is the authority, as
  no registry is (MULTIVERSE.md).
- **Each world names its lobby,** where an arrival lands, and the card's
  live view shows the lobby, read from the world's public log. A world's
  law says what its lobby shows.
- **Maps nest:** a superworld's card opens its own map, a garden's its
  plants, as the hierarchy of worlds has it (VISION.md).
- **A web page first,** in the web app; inside the Ur-world later, a
  brochure picked up at the entrance of the "multiverse lobby or travel
  hub" the founder decided the Ur-world is (URWORLD.md).

## What stays fixed

What every world shares, and what lets worlds meet: the floor (one rule,
transparency, leaving at any time); records-v1's three rules (ASCII keys,
whole numbers within 2^53 - 1, no floats); signed logs and heads; and
determinism, with randomness only from a seed the world names. The rest
is open, and may differ by world.

## Waiting on the founder

- **Where the web app is published,** if anywhere: it is private until
  the founder decides. GitHub Pages serves a public repository's site at
  no cost; recommended when there is something worth showing, and not
  before.
- **A machine that keeps a world running,** if the no-server page isn't
  enough: it costs money.

## Not checked

- Whether a browser computing a long-lived world from its seed stays fast
  enough as a world grows: part 4 measures it before relying on it.
- Which Rust-to-WebAssembly toolchain fits the workspace's pins: looked at
  in part 4.

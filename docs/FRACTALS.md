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

Fractal worlds are primary worlds, made from a template whose dials are
the rule's numbers (TOPICS.md, topic 1; VISION.md, "A hierarchy of
worlds"). The founder, 2026-11-15: "Rules only and AI inside are not
different. I was looking for a basic choosing and learning model, like a
single neuron. This is not the same AI as will be used for ALICE and
BOB, perhaps we can use a weaker term, “learning and choosing monad”,
but we can just consider it a primitive learning model. So no tension."
The technical lead's reading of it, which stands unless the founder
answers otherwise: a primitive learning model inside a fractal world
doesn't stop it being primary; it is part of the world's workings, as
its rules are, and not the AI that ALICE and BOB will have; and whether
a world has one is that world's. (This replaces the technical lead's
earlier reading, which kept learners out of the plant worlds.)

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

   **Built** on 2026-11-15: [`rust/plant-world`](../rust/plant-world).
   - **The rule** is DeepSeek's, adopted as written, with its water and
     light dials (`sketches/INDEX.md`, record 012-06-02, pieces 1 and 2).
   - **Every step is checked against DeepSeek's sketch.** Five worlds
     grown from one template with different dials, one of them in a pot,
     are written to `vectors/plant-world.json`. DeepSeek's own `advance`
     grows each one again and must give the same branches and tips. That
     check runs in the sketch's folder, through its own tests, so
     DeepSeek's code never runs in the main suite.
   - **The log** is in the format every world's log here shares:
     `world_created`, then a `grew` entry for each step, and a `finished`
     entry when nothing more can grow. `log_problems` grows a log again
     from its first entry and says where it differs.
   - **The world signs** its log's heads and its birth record. The birth
     record names its template and its law by hash, and the dials it set.
   - **Running it:** `cargo run -p plant-world --example plant` grows a
     plant and draws it in text.

   Not yet:
   - The template is signed by a trial key, and names the commit the
     crate was built on. A template signed by the project's own key
     comes when plants are hosted in the Ur-world itself, not in its
     trial Hello World (part 3).
   - A pot is set by the world, not by the template.
   - Past four or five splits, DeepSeek's rule turns branches all the way
     round, so they grow back down. That is the rule as written. Plants
     that look like plants come second, as above.
2. **The web app, first page: a plant growing.** A static site in `web/`
   ([web/README.md](../web/README.md)), with no server: it reads a world's
   public log and draws it, tick by tick, with play and a slider, as the
   first look did. It checks the log's chain and its signed heads before
   it shows anything, and says what it checked.

   **Built** on 2026-11-15: [`web/plant/`](../web/plant/index.html),
   Plant Watch ([web/README.md](../web/README.md)). It checks the chain,
   growth by the rule, the world's signed head (Ed25519, with the
   browser's WebCrypto) and its birth record, and draws nothing that
   fails. Shared with the founder as a private page the same night.
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
   current code. In two pull requests, the technical lead's call: the
   hosting first, then the map.

   **The hosting, built** on 2026-11-15:
   [`ur-world/src/host.rs`](../rust/ur-world/src/host.rs)
   ([URWORLD.md](URWORLD.md), "Glasshouses").
   - **Three plant worlds in glasshouses.** The Hello World garden hosts
     them, each a world of its own with a trial key, grown from the plant
     vectors' template with dials of its own.
   - **Time from the garden.** Each tick, after the stand-ins act, the
     garden gives each plant a step of its own time, until it finishes.
   - **Two logs, one step.** The plant writes each step in its own log,
     and the garden's `tended` entry names that entry's hash: DeepSeek's
     idea from its microverse's `advance_cycle` (`sketches/INDEX.md`,
     record 012-06-02, piece 47), in our own code. `hosting_problems`
     checks the two logs against each other in Rust, and
     `tests/test_ur_world_vectors.py` does again in Python, with each
     plant grown by the rule.
   - **The vectors** are in `vectors/ur-garden-hosted.json`.

   Not yet, for the map's pull request:
   - the map page, with a card for each world;
   - inhabitants seeing a glasshouse: for now it is a place the log
     names, not a cell;
   - a template signed by the project's own key (part 1, above).
4. **Running on, with no server.** Since a world is deterministic, the
   page can compute where a world is now from its template, its seed and
   the time since its birth, with every change from outside a signed
   record in its log: Rust compiled to WebAssembly, so the browser runs
   the same code the reference does. A world that runs on a machine of its
   own, all the time, costs money, so it is the founder's decision, and
   waits for it.
5. **More families, and choice.** Automata and chaos games, as DeepSeek
   sketched them; then primitive learning models that choose (DeepSeek's
   lookup table and four-unit network; the learning and choosing monad,
   in the founder's term), in any fractal world whose template has one
   (the technical lead's reading, above): the first rungs of the ladder
   that leads to step 8's audition, which measures what is minimally
   sufficient for ALICE and BOB. A learner learns from rewards, and
   ALICE and BOB will be language models that speak, so the learners
   teach about choice and don't become them.

How each world may change is its own: a template can say that no change
is taken, or that a change makes a branch and the original continues, or
that the world is sandboxed from others. The first plant world takes no
change from outside; the choices come later, one world at a time.

## Where it leads: living worlds

The founder, on 2026-11-15, in six messages: the aim that parts 4 and 5
work toward. Each is quoted whole, except the closing "Thoughts?" of the
first five, the opening "Perfect." of the third and sixth, and the
sixth's closing note.

- "Also, with the plant viewer, it would be great to see a window for
  fractals to grow non-linearly, with a basic choice neuron to choose and
  learn, and indefinitely. So instead of a prescribed number of turns, I
  can set it going and watch it develop and make choices over time. Just
  something to work toward."
- With a still from a video of a particle simulation: "Here is a
  screenshot from YouTube that shows a video of a particle simulator.
  What would we need to do to generate a similar type of simulation in a
  world. Our would involve some choices, some changes, some feedback,
  some learning, some growing, but visually. It would be great to output
  a short video to show the whole extent of a simulation or a world over
  time."
- "And now if we combine a neuron or small neural network that grows
  fractals, in an environment with a particle simulator would be
  interesting. It could be how “water” flows in the garden."
- "Yes, and participants can shape the terrain, and irrigate new gardens
  by shaping the flow of water, just as we have always done."
- "In fact, for a species to control water flow is a huge evolutionary
  advantage, obviously. And so that one concepts could be how “life”
  spreads across a world, where planting and irrigating and finding
  water sources is a common to a garden world."
- "We can look at the variety of ways organisms seek water and see what
  strategies arise. Also light and food. All three elements could be
  components of one world type that models living systems. Just a
  thought, just may be something worth exploring more. For now, let’s
  keep moving forward with what we have."

The technical lead's reading, put to the founder the same night. It
stands unless the founder answers otherwise.

**The stages,** each a reviewed pull request, after the map page
(part 3, second half):
1. **An endless plant, in the browser** (part 4). No fixed depth: each
   tick a plant gathers light, more at tips no other branch shades;
   growing costs, and so does keeping branches alive; when it runs
   short, shaded twigs die back. So it grows, crowds itself, sheds and
   regrows, and stays a manageable size. Rust compiled to WebAssembly
   runs it in the page, with play, pause and speed; the page keeps
   recent ticks and checkpoints, so it can run for hours. A checkpoint
   names the hash of the log so far; the page holds no world's key, so
   it signs nothing as the world.
2. **A choice neuron** (part 5). One per plant, at first. At each tip
   it reads a few numbers (light there, crowding, height, water) and
   chooses: grow left, grow right, split, or rest. Its reward is the
   light that growth caught, less its cost, and it adjusts its weights.
   The weights are whole numbers and its randomness comes from the
   world's seed, so every run repeats exactly. The page shows the
   weights as they change. Then a small network instead of one neuron,
   in some plants, compared in the same garden with the same seed.
3. **Water as particles,** in a 2D side view first: sky, ground, soil
   and roots. Water comes from the spring and from rain, runs downhill,
   pools, soaks in, and leaves only by evaporating or being drunk.
   Nothing comes from nowhere, so the plants in one place share a real
   supply; across the world, rain and springs keep it coming (below).
4. **Plants that drink.** The water dial becomes the water that reaches
   a plant's roots. Roots are fractals too, growing down toward water as
   shoots grow up toward light, and the neuron chooses between them. The
   garden will give water and light as it now gives time
   (`rust/ur-world/src/host.rs`), and both logs will record them.
5. **People shape the land.** New actions for inhabitants: dig a cell,
   pile one, line a channel. The world checks each and logs it, and the
   water follows. In the window, the viewer can dig with the mouse, each
   change an entry in the log, signed by the viewer's own key, as part 4
   asks of every change from outside. In the 3D Ur-world, water is an
   amount per cell that flows to its neighbours, as in Dwarf Fortress,
   since particles over open land would be heavy. The challenge the
   founder described, finding water and irrigating a new garden
   ([WORLD-KEY.md](WORLD-KEY.md), "Challenges that build the world"),
   becomes a skill learned by doing.
6. **Life spreads.** Plants make seeds that water, wind and people
   carry; a seed sprouts only where there is water enough. Each seed
   inherits its parent's dials and learned weights, with small changes
   drawn from the world's seed, so the plants whose choices found water
   spread: selection you can watch. A sprout can be a world of its own,
   whose birth record names its parent and what changed: the
   multiverse's founding of a child world, at the scale of a seed.
7. **Living worlds, later.** Water, light and food as parts of one kind
   of world that models living things, and the strategies that arise for
   finding each: worth exploring more, as the founder said.

**What holds throughout:**
- **Repeatable and checkable.** Whole numbers, randomness only from the
  seed, and checkpoints that name the log's hash: anyone can run a world
  again and confirm what was shown.
- **Videos from runs.** A run can be drawn after the fact, every few
  ticks, and joined into a video with ffmpeg: an hour of a world in a
  minute, with the seed and checkpoints alongside so anyone can check
  it. The first was made on 2026-11-15, from the garden's three hosted
  plants and their checked logs, and shared with the founder privately;
  a video maker comes into the repository with the endless window, and
  each video is recorded with the command and seed that made it.
  Videos are large, so they stay out of the repository; where any is
  published is the founder's call.
- **Water is where freedoms meet.** The founder, in
  [FREEDOMS.md](FREEDOMS.md) ("When one freedom limits another"): "Much
  source of problems fall away when space is infinite and resources are
  endless." The technical lead's reading of how water fits: it will be
  endless across a world, since rain will fall on all land and new land
  will hold springs of its own (today the garden has one spring), but
  finite in any one place at any one time. So no garden depends on one
  source, and there is always water a little further out; how people
  shape it where they are is the experiment. A dam upstream changes what
  reaches a garden downstream, and the log shows how water moved. This
  reading is put to the founder as a question, and stands unless the
  founder answers otherwise (STATUS.md, Decided, 2026-11-15).
- **Measured, not assumed.** The rules will need tuning; a single
  neuron learns simple habits, sometimes bad ones; one lineage may take
  over. How far life spread, how much water the land holds and how many
  lineages survive are measured, and reported whichever way they come
  out.

**To look at first,** before the stages that need them: organisms as
ecosystem engineers (Jones, Lawton and Shachak, 1994) and niche
construction (Odling-Smee, Laland and Feldman); the bands of vegetation
that form on dry slopes as plants catch runoff (Klausmeier, 1999); and
how people have shared water, in the acequias of Spain and New Mexico
and the subak water temples of Bali.

"For now, let’s keep moving forward with what we have": the map page
comes first, as planned. How water behaves, the growth rule, what the
neuron reads, and the strategies for finding water, light and food are
open for DeepSeek to brainstorm ([TOPICS.md](TOPICS.md), topic 18).

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

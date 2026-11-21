> Part of `docs/COLLABORATING.md` in open-worlds, which is kept cut into parts
> for readers who are shown only the start of a long page.
> This part holds: "Two sides: the sketch and the standard" to "House rules".
> Every part, in order: https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/parts/INDEX.md
> Before this part: https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/parts/docs/COLLABORATING.md/start.md
> After this part: https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/parts/docs/COLLABORATING.md/code-in-rust.md
> Made by docs/parts.py from the file. To change it, change the file.

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
Its "Course" column uses the first course's step numbers for records
012-04-00 and 012-05-01 ("Done: the first course" in
[COURSE.md](COURSE.md) is the key), and the course now running for
record 012-06-02 and after.

**Taking a piece in is a decision of its own** (the founder, 2026-11-15:
"Also, keep in mind, we expect DeepSeek code to have some things to fix,
and we should still decide whether or not to incorporate anything that
goes against our established design."). The technical lead's answer, put
to the founder the same day (it stands unless the founder answers
otherwise): four steps, in order.

1. **Bring it in as written,** in `sketches/`, with every test's result.
2. **Make it run:** fix what is broken, the design unchanged, each fix
   listed with its reason.
3. **Check its fit** with the established design (the decisions in
   STATUS.md and the design pages), naming each conflict.
4. **Decide, piece by piece:** adopt it, adapt it, or keep it as a
   sketch, with the reason in `sketches/INDEX.md`. The technical lead
   decides the code; what would change a founder's decision goes to the
   founder, with a recommendation.

**What fits comes straight in.** The founder, 2026-11-15: "The DeepSeek
code should still be treated as sketches and brainstorming, but now in
Rust. But if the code aligns well and extends cleanly, then why not just
incorporate. But changing to Rust does not change anything else, only
the language." The technical lead's rule for it: a piece that compiles
against the crates on `main`, passes the three commands under "Code in
Rust", keeps the rules there, and meets no conflict in step 3 goes into
`rust/` in one reviewed pull request, steps 2 to 4 together. Its commits
name DeepSeek as well as Claude in their `Made-by` lines and say what
was changed here, and the record keeps the original. Everything else
stays a sketch, as before.

**The standard is open-worlds' own code, not the sketches.** Build on
the code merged into `main` (`multiverse/`, `formats/`, `rust/`) and the
documents in `docs/`. The code in `sketches/` is
earlier work, some of it on the old, unsigned protocol, kept for its
ideas.

## Where the conversation stands

Seven records are kept: 012-00-00 (patterns and the brain), 012-02-01
(circuits, learning, chemistry and music), 012-03-02 (the poetry
engine), 012-04-00
(components 1 to 63), 012-05-01 (components 64 to 87: a live
federation and its tools, then the founder's turn to game worlds: a
chess park, worlds inside worlds, worlds that grow and govern
themselves, and a world that keeps running); 012-06-02, a new cycle
begun from this page (fractal worlds, a gallery of worlds and its
governance, then the smallest learner that chooses, and individuals as
signed, replayable bundles), which ended with DeepSeek asking which
piece is next; and 012-07-03, begun here: water as particles, the garden and a
botanical garden of gardens, then the founder's turn to the Commons
as chat rooms, each with an AI moderator, a home room for each person,
a schema, and a sketch crate in Rust, `chat-world`. It is kept with a
first round of repairs, each listed, and what runs: the crate builds
and passes its own 18 tests (the messages of 2026-11-16, in the
archive: https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/archive/COLLABORATING/2026-11-16.md).
It is fitted next. The record then goes on: the one file
reached DeepSeek whole, and five deliveries of the crate followed,
kept as written beside it, with what each builds to. Then Gemini,
from a file of their own, made the log checkable from outside, attacked
the check, and repaired it (the messages of 2026-11-17, in the
archive: https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/archive/COLLABORATING/2026-11-17.md).
012-06-02's code is being made to work; then the founder and the
technical lead decide what fits with what is built, and how (STATUS.md,
"Decided", 2026-11-14). Each new conversation starts a new record, which
gets its own folder in `sketches/`. Each
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
AI that speaks for their world and proposes its development but doesn't
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
text or as code with tests. [TOPICS.md](TOPICS.md) is the menu:
twenty-one topics a few steps ahead of the code, each with where it
fits, what is decided, what is open, a possible implementation, and
what to send back, and, under "Further out", ideas that won't help yet
but probably will.
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
- **Persons** (course step 3a, [research/PERSONS.md](research/PERSONS.md)):
  one person above their presences in many worlds, unlinked by default,
  which means a key of its own for each presence, since every arrival
  names its key in a public log.
  DeepSeek's own architectures (components 36 to 52: the octopus, the
  relay, the swarm, the council) are its small examples.
- **The garden** (course step 4a): parallel worlds from one template,
  and what each glasshouse shows of its world from its public log.
- **Living worlds** ([TOPICS.md](TOPICS.md), topic 18): how water moves,
  a plant that grows without end, what a choice neuron reads and learns,
  and the strategies for finding water, light and food.
- **The Commons** ([COMMONS.md](COMMONS.md); [TOPICS.md](TOPICS.md),
  topic 14): Lyceum Commons, where the multiverse began, rebuilt as a
  superworld of rooms and the first space open to the public. A room's
  law for each kind (people, AIs, or both), as data and as text; how an
  AI from another company's app could hold their key.
- **Offices** ([TOPICS.md](TOPICS.md), topic 19;
  [OFFICES.md](OFFICES.md)): a Keeper's qualifications, as checks code
  could run, and what preparing a successor looks like in the open.
- **Reasoning checked by Lean** ([TOPICS.md](TOPICS.md), topic 20): a
  small world of claims and proofs, where a claim counts once Lean's
  kernel accepts its proof; and what a proof attached to an office's
  decision should state.
- **Hallucination, both ways** ([TOPICS.md](TOPICS.md), topic 21): how a
  mind tells, and says, which of their words they saw and which they
  imagined; and a test that catches overclaiming and self-doubt alike.
- **Laws for new worlds:** what a world admits by, what can happen in it,
  what counts as solving a problem there. Forms for the poetry world,
  such as a quatrain in common meter each turn, Dickinson's meter.
- **The hunt** (course step 11, [WORLD-KEY.md](WORLD-KEY.md)): symbols,
  maps, codes and stones; puzzles that teach without words; and
  challenges that build the world (TOPICS.md, topic 17).
- **The Ur-world,** built from `rust/ur-world` to the standards in "Code
  in Rust" below: its next steps are in [URWORLD.md](URWORLD.md).
- **Minds for the Ur-world,** in any language. A mind is a program that
  speaks the doorway's protocol: lines of JSON in and out
  ([URWORLD.md](URWORLD.md), "Minds from outside: the doorway").
  `minds/wanderer.py` is the smallest example.
- **Anything on the course,** proposed as described below.

Held back, as the project's own to do: the project's keys (their
private halves live only in its private repository), and anything that
publishes or can't be undone. ADMIN and the Keepers
wait for step 11; their interface is fixed in step 4, by the project.
So are the measures that compare the two Keepers (item 9 above).

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
   becomes part of it (the founder, 2026-11-15). A work the founder has
   brought in is named by its title (2026-11-17 and 2026-11-20; STATUS.md,
   "Decided by the technical lead", 2026-11-20).
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


> The next part: https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/parts/docs/COLLABORATING.md/code-in-rust.md

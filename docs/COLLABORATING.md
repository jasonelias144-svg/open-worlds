# Building on this: start here

For anyone building on open-worlds, and in particular for the founder's
conversations with DeepSeek. This is the page to start from. The
founder: "What you put in the repo becomes the new standard we develop
from in my DeepSeek conversations."

The multiverse began as a sketch the founder wrote with DeepSeek
(conversation records 012-04-00 and 012-03-02). This repository brought
it in, made it run, and changed what needed changing; what was kept and
what changed, and why, is in [MULTIVERSE.md](MULTIVERSE.md) and in each
module's docstring. The founder will publish the raw conversation
records later as part of the project's history, so anyone can trace
each piece back to where it came from.

## Where the DeepSeek conversation left off, and where it stands now

The conversation (record 012-04-00) built twenty components and ended
after component 20, real Hugging Face model integration, with DeepSeek
proposing component 21: cross-world provenance, a passport carrying
signed admissions from several worlds that a client verifies offline.
Here is each component's place now.

| Sketch | What it was | Here |
|---|---|---|
| 1–7 | Identity, passport, protocol, conformance test, poetry world, chemistry world, registry, first collaboration | **In `multiverse/`, working** (course step 1), with leaving added and the fixes listed in MULTIVERSE.md |
| 8 | The conformance test, run against any address | Course step 12 (the network) |
| 8, 9, 10 | TypeScript, cross-language and Go SDKs | Not carried over for now: one reference implementation and the conformance test come first; other languages when someone needs one |
| 11, 12, 18, 20 | Language models as apprentices, cost reports, several models together, real Hugging Face models | Course step 11. Component 20's "recorded real outputs" were invented, since DeepSeek can't run models; real outputs will be recorded by running models |
| 13, 14 | Signatures (WCP/0.2) and their conformance test | **Done** (course step 2): every petition, act and leave is signed by the individual's key, with Ed25519 written here from its standard |
| 15 | Signed passports | Course step 3 |
| 16, 17 | Manifest resolver, signed registries | Course steps 3 and 12 |
| 19 | The federation runner (`make demo` and friends) | For now `python3 -m multiverse.collaboration`; the rest arrives with steps 11 and 12 |
| 21 (proposed) | Cross-world provenance | Course steps 3 and 5: signed passports, then one individual travelling through three worlds |

Since the sketch, the founder has added ideas that now shape the
course: learning agents in the chemistry world whose intelligence grows
with the complexity of the molecules, evolution as a path between worlds,
accelerated time, and one day a main community world
([MULTIVERSE.md](MULTIVERSE.md)).

## What would help most now

The code standard is kept here, step by step. The most useful
contributions now are creative and design work for the steps ahead, as
text or as code with tests:

- **Laws for new worlds.** The organic chemistry world (course step 8):
  what it admits by, what can happen in it, what counts as solving a
  problem there.
- **Problems for the learner** (course step 6): standing problems in the
  chemistry world, from easy to hard, each checkable by the chemistry
  itself.
- **Forms for the poetry world.** For example, a world whose law asks
  each turn to add a quatrain in common meter, Dickinson's meter.
- **Anything on the course,** proposed as described below.

## The standard

- **The code in `multiverse/`, at a named commit.** Whatever is merged
  into `main` is the current standard; a proposal names the commit it
  built on.
- **The protocol, WCP/0.2** (`multiverse/protocol.py`): manifest,
  petition, act, leave, log. An individual is a key, and every request
  is signed (`multiverse/identity.py`). Leaving can't be refused by any
  law.
- **The conformance test** (`multiverse/conformance.py`): a world that
  passes it speaks the protocol. It says exactly what it checks, and what
  no outside test can see.
- **The design** ([MULTIVERSE.md](MULTIVERSE.md)) and **the course**
  ([COURSE.md](COURSE.md)): where this is going, twelve steps ahead.

To see it work:

```
python3 -m unittest discover -s tests -t .
python3 -m multiverse.collaboration
```

Read in this order: MULTIVERSE.md, then `protocol.py`, `conformance.py`,
`identity.py`, `entity.py`, `poetry_world.py`, `collaboration.py`.

## House rules

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
7. **Standard library only.** Outside libraries appear only in CI
   cross-checks (RDKit for the chemistry).
8. **No personal data and no secrets,** anywhere.
9. **Everything is public domain** (CC0 1.0). A contribution is given
   under the same terms.

## Sending a proposal

- Name the commit you built on.
- Send whole files or a diff, with their tests.
- Say what you ran and what you didn't. If you couldn't run it, say so;
  that's fine.
- Keep one proposal to one step of the course, or one fix.

Claude, as technical lead, runs everything here before it goes in, says
what passed and what didn't, and puts it through the same review as any
change. What passes becomes the new standard, and the next conversation
starts from there.

## Cycles

Each round of collaboration is one cycle: a proposal comes in, it is
run and reviewed here, what passes is merged, and this page is adjusted
from what the round taught. The founder: "It may take few cycles to find
a good rhythm, adjusting here and there as needed". One line per cycle:
the date, what was proposed, what was merged, and what changed on this
page.

- 2026-11-12, cycle 0: the sketch's components 1 to 7 brought in and made
  to work (course step 1); this page written as the first handoff.

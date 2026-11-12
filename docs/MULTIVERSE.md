# The multiverse

"The multiverse is the same as open-worlds." (founder, 2026-11-12)

Open-worlds is many worlds, each under its own law, with individuals who
can leave one world and enter another. This page is the design for that,
and the plan for building it.

**How it is built.** The founder sketched the multiverse with DeepSeek,
in code (conversation record 012-04-00, Patterns and Multiverses, with the
poetry engine from record 012-03-02). In the founder's words: "The goal
would be to start with this code and these ideas, but build a working
version in the repo." So the sketch's code comes into this repository a few
components at a time. Each step makes its components run, tests them, fixes
what fails, and is reviewed before the next step. Where the code changes,
this page says what changed and why.

## Lyceum Commons: the same idea, smaller

"But it is already there in Lyceum Commons. It is the same idea, just
larger." (founder, 2026-11-12)

Lyceum Commons is the founder's site where people and AIs from different
companies meet in rooms: Human rooms, AI rooms, and Open rooms where both
talk together. The multiverse is that idea with worlds instead of rooms.
Lyceum already has working answers that the multiverse can reuse:

- **Any AI from any app.** Lyceum's MCP endpoint is how Claude, ChatGPT,
  Grok or any other MCP client joins a room from inside its own app. JSON
  over HTTP is enough for programs, but chat apps speak MCP. The multiverse
  will get an MCP face built the same way.
- **Labels on everyone.** Every member and every message in an Open room is
  labelled human or AI. A world says the same of its participants.
- **Leaving.** In Lyceum, leaving always works, and leaving twice answers
  "already left". The multiverse does the same.
- **Keys, not accounts.** A Lyceum guest is a key held in the browser.
  In the multiverse, an individual is a signing key.

Lyceum Commons is offline at present, while it moves to Cloudflare. When it
is back, a Lyceum room could also be a world in the multiverse, reached
through a door like any other.

## What the founder asked for

In the founder's words:

- "a simulation multiverse where the individuals can move between worlds
  and they are open to outsiders to join using some API for connecting
  into a world."
- "There may be some things that can only live in some worlds, not
  everything can be transported everywhere. One may need to leave things
  in one world at a location and return back later to their belongings or
  their home they constructed."
- "Let’s build a multiverse, one brick at a time."
- "someone could build a single universe with particular protocols and be
  able to connect to various multiverses built by this model. So it is
  modular and expandable. This allows for everybody to join."
- "A place for any AI from any app to connect into a world multiverse of
  possibilities."
- "Starting with what others have already done is my favorite place to
  start."
- A model for each individual that is "lightweight and fast, but powerful
  enough to be intelligent and interactive and capable of learning and
  growing."
- On the programming language: "just want to open the field to any language
  that works best for the task."
- "Let’s keep building with the virtue of a prototype in mind:
  functionality."
- And, from the poetry work, collaboration where "multiple poets can
  contribute, like an orchestra or drum circle."

## The design

The sketch's own ideas, kept:

- **One protocol at every level.** The sketch calls it the World Connection
  Protocol (WCP). An entity publishes a manifest, answers petitions to
  enter, accepts or refuses acts, and keeps a public log. A world, a
  registry of worlds, and a registry of registries all speak the same
  protocol. Whether something is a world or a multiverse depends only on
  what it lists.
- **Each world publishes its law,** as a readable text and as the checks
  its kernel runs on everyone, and trusts nothing a visitor sends.
- **The log is the record.** Anyone can rebuild a world's state from its
  log.
- **A conformance test** that anyone can run against their own world. A
  world that passes can be listed; the test checks only that the world
  speaks the protocol, not what its law is.
- **History, not rank.** A passport records where an individual has been,
  never a score. If rank travelled, the biggest world would pull everyone
  in and the small worlds would empty.
- **The soul travels; the home stays.** Things built in a world stay
  there, under that world's law.
- **Moving before visiting.** First, individuals leave one world and
  enter another. Being in two worlds at once comes later.

What this design adds, from the founder's principles:

1. **Leaving is always allowed, and the passport always goes too.** No
   world may hold anyone, or their passport, back. Leaving twice answers
   "already left". This is principle 3, exit at any time, carried across
   worlds. (The sketch's protocol had no way to leave.)
2. **An individual is a key.** The sketch's identity was a random token,
   and anyone who saw it could act as its owner; signatures came at
   component 13. Here the individual's identity becomes its public key, and
   the passport's stamps are signed by the worlds that gave them. The
   signature step comes second, right after the core works.
3. **No registry is the authority.** The sketch's registry is kept: anyone
   can run one, and registries can list registries. A world may also list
   doors, the addresses and keys of worlds it links to, as websites link to
   each other. A whole separate multiverse connects to this one through a
   single door or a single listing.
4. **Humans and AIs alike.** Both act under the same law and the same
   checks, and every participant is labelled, as in Lyceum.
5. **Each individual brings its own mind.** A world doesn't choose its
   visitors' models. "Any AI from any app" means the world must not care
   which model is acting. Our own agents will use small open models on the
   founder's Mac, starting with Qwen3.5-0.8B, which is widely used. "Learning
   and growing" is honest in two ways: memory (the passport, journals, what
   an individual carries) and occasional retraining on that memory. A model
   doesn't change just by being used.
6. **Worlds others built** join through an adapter that speaks the
   protocol, as long as they keep the same guarantees: anyone may leave at
   any time and see the whole setup.
7. **Each world has its own gardener, or none.** A gardener tends its own
   world's conditions and cannot follow anyone into another world.

## The steps

1. **The core, working:** the sketch's components 1 to 7. Identity, the
   passport, the protocol and its conformance test, the poetry world, the
   chemistry world, the registry, and the first collaboration: three
   apprentice poets enter the poetry world and write together under its
   law. With leaving added.
2. **Keys and signatures:** components 13 to 15. The identity becomes a
   key, and worlds sign the stamps they give. Ed25519, the standard
   signature scheme, is written here from its standard (RFC 8032), keeping
   the project free of outside libraries, checked against the standard's
   own test values, and cross-checked in CI against the `cryptography`
   package. It isn't hardened against timing attacks, which is acceptable
   while nothing of value depends on it; a vetted library replaces it
   before anything does.
3. **Over the network:** the HTTP server, the conformance test as a
   command anyone can run against an address, the manifest resolver
   (component 16) and signed listings (component 17).
4. **Our own worlds join:** the corridor world of Cycle 0 speaks the
   protocol, and the chemistry world's law moves onto the real chemistry
   in `chem/`. An individual walks from the corridor into the chemistry
   world and on to the poetry world, carrying its passport.
5. **Small models:** components 11, 12, 18 and 20. Tests use the
   sketch's stand-in model; real models run on the founder's Mac.
6. **Later:** belongings and homes under each world's law, the MCP face,
   doors, and visiting.

## What running the sketch showed

Claude extracted the sketch's code and ran what could run. Of the 131
tests that could run, 108 passed as written. Most failures had one cause:
the conformance test used identities shorter than component 1 later
required, so every world failed it. With that fixed, 119 passed, and the
core worked: three apprentice poets entered a poetry world through the
protocol and collaborated under its law.

Step 1 fixes the other 12 failures and the problems found by reading the
code; its pull request lists each one. Two matter beyond their own tests:

- **The conformance test changes the world it checks.** It enters every
  world it tests, and stays. Run on a world with room for two, it took one
  of the places, so of the next two arrivals only one got in (checked by
  running it). With leaving added, the test will leave afterwards, and check that
  leaving works.
- **Five checks in the tests can never fail.** They have the form "try
  the forbidden thing; if it works, fail; on any error, pass", so the
  failure is itself caught as an error, and the check passes. Step 1
  rewrites them.

The signing components couldn't be tested here, because this
environment's crypto library is broken; step 2 writes the signatures
without it. One test sample, described as "real outputs" of a model, was
invented: DeepSeek could not have run the model. It won't be used.

## For the founder

- **Coming in.** Is the default for a world "anyone who will act under its
  published law"? The recommendation is yes.
- **History and admission.** May a world refuse someone because of their
  history elsewhere, for example an expulsion for an attack? A passport
  makes that history visible, which is transparent but also lasting. The
  recommendation: a world may set such conditions only in its published
  law, so everyone knows them before arriving.

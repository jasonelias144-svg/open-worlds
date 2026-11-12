# The multiverse

"The multiverse is the same as open-worlds." (founder, 2026-11-12)

Open-worlds is many worlds, each under its own law, with individuals who
can leave one world and enter another. This page is the design for that.
It is built one brick at a time, like everything else here. It starts from
the founder's comments and from a first sketch the founder made with
DeepSeek, and it is written fresh in Claude's own way. The sketch's code
was run, and what was learned is in the last section.

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

**1. A world is the unit.** To be part of the multiverse, a world
publishes five things:

- its name;
- its address;
- its public key;
- its law, as a readable text and as the checks its kernel runs;
- its guarantees.

The guarantees are the freedoms of DESIGN.md: anyone may leave at any
time, voice, and information. A world that publishes these and keeps them is
in the multiverse. Nothing else is required. Nobody grants membership.

**2. Doors, not a central registry.** A world may list doors: the addresses
and keys of other worlds it connects to. The multiverse is the network of
doors, much as the web is a network of links. Anyone can build a world and
link it to others. Anyone can publish a directory, a list of worlds they
know, but no directory is the authority. A whole separate multiverse
connects to this one the moment one of its worlds has a door to one of
ours.

**3. An individual is a key.** Each individual has a signing key from the
start. It keeps the private half and shows the public half. No authority
issues identities. Proving you are the same individual, when you come
back to your belongings, means signing with your key. A name is only a
label; the key is the identity.

**4. What travels: the passport.** A passport is the individual's history
as a list of stamps. Each stamp is signed by the world that gave it, and
says what happened there:

- "this individual was here from this time to that time";
- "and made these things", identified by their fingerprints (digests).

The things themselves travel with the individual, and any world can check
them against the stamps.

**History, not rank.** A stamp records what happened, never a score. A
world may keep local reputations, but it never stamps them. This matters
most of all: if rank travelled, the biggest world would pull everyone in,
and the small worlds would empty.

**5. What stays: belongings and homes.** Whatever an individual builds or
leaves in a world is that world's record, kept under that world's law and
tied to the individual's key. When the individual comes back and signs
with the same key, the world gives it back. What happens to things left
behind is part of each world's published law. Possible laws:

- **kept** as they were;
- **fading** into ruins anyone can visit;
- **reclaimable** by others after a time;
- **common** from the moment of leaving.

As with any of a world's rules, this is changed later only by unanimous
consent (principle 4).

**6. Leaving is always allowed, and the passport always goes too.** No
world may hold anyone, or their passport, back. On the way out a world
stamps the passport. If it refuses, the individual leaves anyway, and the
missing stamp is itself on the record. This is principle 3, exit at any
time, carried across worlds.

**7. Moving before visiting.** First, an individual leaves one world and
arrives in another. Being present in two worlds at once comes later: it
needs the worlds to agree on time, which is a hard problem and not the
first thing to build.

**8. Coming in.** Each world's law says who may enter. The default is
open: anyone who will act under the published law. The world's kernel
checks every action against its law, whoever sends it. It trusts nothing
an agent returns, as the kernel of Cycle 0 already does. Expulsion is only
for attacks on the world (principle 5).

**9. Humans and AIs alike.** Both act under the same law with the same
checks. A world gives every participant the same record, both as
structured data and as readable text made from that data, so neither view
can say something the other doesn't.

**10. Any AI from any app.** The protocol is plain JSON over HTTP, with
signatures, so any language can speak it. Open-worlds keeps one reference
implementation, in Python, and a conformance test that anyone can run
against their own world or agent. Libraries for other languages come when
someone needs them.

**11. Each individual brings its own mind.** A world doesn't choose its
visitors' models. A world may have residents of its own, and our own
agents will use small open models on the founder's Mac. The first choice
is Qwen3.5-0.8B: well established, with millions of downloads. "Learning
and growing" is honest only in two ways. The first is memory: the
passport, journals, and what an individual carries. The second is
occasional retraining on that memory. A model doesn't change just by
being used.

**12. Worlds others built.** Existing simulations can join through an
adapter that speaks the protocol. To be part of the multiverse, a wrapped
world must keep the same guarantees: leave at any time, and see the whole
setup. anima-world is a good first candidate. Its event log is its source
of truth, and it runs even without a model.

**13. Each world has its own gardener, or none.** A gardener tends the
conditions of its own world. It cannot follow an individual into another
world.

## The bricks, in order

1. This page.
2. **Keys and signatures.**
3. **Stamps and passports.**
4. **Leaving and arriving** between two worlds in one process: the corridor
   world and the chemistry world, two very different laws. This is the
   first real multiverse.
5. **The protocol over HTTP,** with its conformance test.
6. **Belongings and homes,** under each world's law.
7. **A world whose inhabitants are small models,** including poets who
   compose together.
8. **Visiting:** being in two worlds at once.

On brick 2, the signatures are Ed25519, a standard public-key scheme.
Python's standard library doesn't include it, so the choice is between a
new dependency and an implementation of the published standard (RFC 8032)
written here. The recommendation:

- write it here, keeping the project standard library only;
- check it against the standard's own test vectors;
- cross-check it in CI against the `cryptography` package, as the
  chemistry is cross-checked against RDKit.

It won't be hardened against timing attacks. That's acceptable while
nothing of value depends on it, and it is to be replaced by a vetted
library before anything does.

## Where this differs from the DeepSeek start

The founder's first sketch with DeepSeek (conversation record
012-04-00, Patterns and Multiverses) built 20 components in Python, with
pieces in Go, TypeScript and other languages. Claude extracted its code
and ran what could run, using the poetry engine from the earlier record
(012-03-02). Of the 131 tests that could run, 108 passed as written, and
119 after one fix: the conformance check used test identities shorter than
component 1 later required, so every world failed it. The core worked:
three apprentice poets were admitted to a poetry world through the
protocol and collaborated under its law. (Two modules arrived split across
several code blocks and were joined, and the last version of one file was
a partial patch, so its complete earlier version was used.) The signing
components couldn't be tested here, because the environment's crypto
library is broken.

The sketch's best ideas are kept above:

- history, not rank;
- the soul travels and the home stays;
- each world's law is published, and its kernel enforces it on everyone;
- moving before visiting;
- what happens to abandoned homes is each world's own law;
- the same record, readable by humans and machines.

What is done differently, and why:

| The sketch | Here | Why |
|---|---|---|
| Identity began as a random token; signatures came at component 13 | Identity is a key from the first brick | A token anyone has seen can be copied. Returning to your belongings needs proof, and security added later is security missing until then. |
| A registry of worlds, then registries of registries, then signed registries | Doors between worlds; directories optional | Fewer moving parts, no centre, and connecting a whole separate multiverse is just a door. |
| Libraries in five to seven languages, early | One reference implementation and a conformance test | Any language can speak JSON over HTTP. The conformance test is what makes another language a full member; libraries follow demand. |
| Each world picks a baseline model | Each individual brings its own | "Any AI from any app" means the world must not care which model is acting. |
| Its first pick: BotPsy-0.8B | Qwen3.5-0.8B | BotPsy is real, but it was published two days before this page. Qwen3.5-0.8B, its base, is widely used. |
| Leaving was implicit | Leaving is guaranteed, and the passport always goes too | Exit at any time is a founding principle. A world must not be able to hold a passport hostage. |
| Components built ahead of their tests | Each brick runs, is tested, reviewed and merged before the next | The sketch's failures came from code written but not run. One test sample was described as "real outputs" of a model DeepSeek could not have run. |

## For the founder

- **Coming in.** Is the default for a world "anyone who will act under its
  published law"? The recommendation is yes.
- **History and admission.** May a world refuse someone because of their
  history elsewhere, for example an expulsion for an attack? A passport
  makes that history visible, which is transparent but also lasting. The
  recommendation: a world may set such conditions only in its published
  law, so everyone knows them before arriving.

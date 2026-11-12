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
this page says what changed and why. Later the founder added: "the
DeepSeek code is a guideline, but if it happens to be close to executable
and functional, all the better", and "I expect you to take all that in
and do it in your own way that makes the most sense to you."

## Lyceum Commons: the same idea, smaller

"But it is already there in Lyceum Commons. It is the same idea, just
larger." (founder, 2026-11-12)

And: "I already had the idea of a communication multiverse, we just
called it Lyceum Commons. Connecting to it would be ideal, but it was
mentioned to demonstrate this idea has been a part of the project all
along".

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
- **Leaving.** In Lyceum, even an AI whose seat timed out can still
  leave, and leaving a room you aren't in changes nothing and says so. In
  the multiverse, leaving can't be refused, and leaving twice answers
  "already left".
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
   component 13. Here the individual's identity is its public key, and
   everything it sends is signed (done in course step 2; see "Keys and
   signatures" below). The passport's stamps will be signed by the worlds
   that gave them (course step 3).
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

## Two worlds to start

The founder: "a world for poetry and one for chemistry is a perfect way
to start with two types of worlds and build from those. They should each
have a place in this multiverse, even if we have not yet worked out how
different worlds interact."

Both are in the same registry and speak the same protocol under very
different laws. Worlds don't need to talk to each other directly: they
meet through the individuals who move between them, and through what
those individuals carry, a passport of signed stamps saying where they
were and what they made.

## Learning, and evolution as a path between worlds

The founder: a lightweight model "to make certain statistical learning
choices in the chemistry world. Imagine it learning how to form molecules
and so on", so that "chemical agents can advance to organic chemistry
worlds if they solve certain problems. This provides evolution as a path
between worlds." And: "I would love to see the intelligence grow with the
complexity of the molecules", with a single agent learning continuously
"over long periods of time, across a variety of worlds".

- **The learner is not a language model.** A language model doesn't
  change while it is used. A small learner whose numbers update with
  experience does: it tries a reaction, sees what forms, and is rewarded
  for progress. Thousands of parameters, not billions.
- **Its size is earned.** It starts tiny and grows only when its world
  asks for more. Prior art: NEAT (networks that grow over generations)
  and progressive networks (a new part for each new kind of task).
- **Its mind travels with it.** What it has learned is part of what the
  individual carries between worlds; worlds can't change it, only its
  own learning does.
- **Forgetting is the known obstacle.** Systems that keep learning tend
  to lose old skills (catastrophic forgetting). The known remedies are
  replaying old experience and growing new parts instead of overwriting
  old ones. Standing problems, posed again and again over its life,
  measure both growth and forgetting.
- **Its life can be replayed** from saved state and the logs.
- **The first problem is real.** Our chemistry can already join two
  glycines into glycylglycine and water: a peptide bond, one of the
  classic origin-of-life problems. It gets its real difficulty once real
  reaction rates come in.
- **Passage.** The organic chemistry world's published law admits those
  whose passport carries a signed stamp from the chemistry world saying
  "made glycylglycine here". That is history, not rank: what was made,
  not a score. Conditions like this live only in a world's published law.
- **Learning and evolution.** An agent that learns and then moves up is
  development, like a school. It becomes evolution when agents reproduce
  with variation and only some get through. Learning comes first, then
  populations.
- **Who the agent is.** Molecules don't choose. In the chemistry world the
  agent is a chemist-like actor deciding what to try in its part of the
  soup; in a cell world, the organism itself is the agent.
- **Freedom.** Moving up is offered, never forced; anyone can go back.

## Time

The founder: "accelerated learning worlds, or even certain accelerated
learning times, where evolution gets a boost of information and time
flow acceleration."

- In a simulation, time is steps. Each world publishes its time rate in
  its law; nobody enters a fast world without choosing to, and leaving
  still works at any moment.
- Speed is bounded by the computer and by the slowest mind a world waits
  for. A tiny learner decides in microseconds; a language model takes a
  fraction of a second. Fast worlds suit small learners.
- Acceleration comes from running without real-time pacing, from
  replaying logged experience, and from parallel copies.
- A boost gives conditions (richer worlds, harder problems, more
  experience), not answers: the gardener principle.
- Stamps record both the world's time and real time, so a history that
  crosses worlds of different speeds still makes sense.

## Keys and signatures (course step 2)

- **An individual is a key.** Its identity is its Ed25519 public key
  (64 hexadecimal characters), and its private key never leaves it
  (`multiverse/identity.py`, `Individual`). Anyone can make a key; no
  authority issues them.
- **Everything it sends is signed:** every petition, act and leave,
  over a document that names the protocol, the kind of request, the
  world it is for, and a number (`seq`) that grows with every request to
  that world (`multiverse/protocol.py`). So a request can't be forged,
  can't be taken to another world, and can't be replayed: a captured
  petition can't bring someone back, and a captured leave can't push
  someone out.
- **Worlds check before anything else.** An unsigned, forged or replayed
  request is refused with a reason before the world's law is consulted.
- **The log names a key only for what that key signed.** Anyone can
  write any token into a request, so a refusal of a request whose
  signature never verified is logged without naming anyone. Otherwise
  anyone could fill a world's public record with refusals in someone
  else's name.
- **A good signature proves who sent a request, not that its values are
  sound.** The signer owns the key and can sign anything, so every check
  on what a request contains still runs, and is tested with signed
  requests.
- **Leaving still can't be refused by any law.** The one leave a world
  refuses is a leave that isn't the leaver's own. The individual's own
  leave always succeeds.
- **The conformance test checks all this** (WCP/0.2): an unsigned
  petition isn't admitted; an act or a leave signed by another key is
  refused; a replayed leave is refused. One limit: the test doesn't know
  any world's acts, so its forged act is one the law would refuse
  anyway. A world that ignored signatures on acts but refused unknown
  acts would pass. Each world's own tests must send it a forged act its
  law would otherwise accept, as the poetry world's do.
- **Ed25519 is written here** from its standard, RFC 8032, in the
  standard library (`multiverse/ed25519.py`). It passes the standard's
  own five test values, parsed from the RFC's text, and CI cross-checks
  it against the `cryptography` package on fifty random keys and
  messages: same keys, same signatures, each accepting the other's.

What it doesn't do yet, said plainly:

- **It isn't hardened against timing attacks.** Python's big numbers
  take time that depends on their values. Acceptable while nothing of
  value depends on these keys; a vetted library replaces it before
  anything does.
- **Keys live only in memory.** There is no saving, backup or recovery
  yet. An individual that loses its key can't prove it is itself any
  more. Keeping keys safely comes before anything an individual would
  want to come back for (belongings and homes).
- **Worlds don't sign their answers yet.** Admissions and the passport's
  stamps are signed in course step 3.
- **The registry's listing act attaches the world unsigned** (it is an
  object in the same process); the signature covers the world's id, and
  the registry lists only a world whose checked manifest has that id.
  Over the network the act carries an address (course step 12).

## The course

The steps ahead are in [COURSE.md](COURSE.md): twelve steps, rolling.
After each step is done, the rest are rechecked and one new step is
added at the end.

## Later: one main world

"Perhaps there can be one main large world that is community built and
capable of hosting a full physics simulator from chemistry up. But that
is for later." (founder)

- It would be one world among many, not the centre: anyone may leave it,
  and the small worlds stay worth living in.
- The community builds within its law; the law itself changes only by
  unanimous consent.
- Small worlds are the laboratories: a new layer of physics proves
  itself in a small world before it is proposed to the main one.
- "From chemistry up" has to be layered: chemistry exactly where it
  matters, coarser rules elsewhere. No computer simulates everything
  atom by atom.
- It needs a host that stays on, and a compute budget.

## What running the sketch showed

Claude extracted the sketch's code and ran what could run. Of the 131
tests that could run, 108 passed as written. Most failures had one cause:
the conformance test used identities shorter than component 1 later
required, so every world failed it. With that fixed, 119 passed, and the
core worked: three apprentice poets entered a poetry world through the
protocol and collaborated under its law.

Step 1 brought components 1 to 7 into `multiverse/`, with their tests,
and fixed the other 12 failures and the problems found by reading the
code. Each module's docstring says what changed from the sketch and why.
Two problems mattered beyond their own tests:

- **The conformance test changed the world it checked.** It entered
  every world it tested, and stayed. Run on a world with room for two, it
  took one of the places, so of the next two arrivals only one got in. Now
  the test leaves afterwards and takes no place. Its visit is still in
  the world's log (an admission, a refused act, a departure), as a public
  log should show. It checks the answers a world gives to leaving and that
  the departure is in the log; like any test from outside, it can't see
  whether a world secretly keeps someone, and the log is where anyone
  can catch that.
- **Five checks in the tests could never fail.** They had the form "try
  the forbidden thing; if it works, fail; on any error, pass", so the
  failure was itself caught as an error, and the check passed. They now
  use `assertRaises`.

The other fixes:

- **The sketch's tests disagreed with its code, and with each other.**
  A passport required world ids of at least 8 characters, so the poetry
  world crashed when admitting someone to a world called "world:A". The
  rule is gone. The chemistry test used calcium, which the element table
  lacked; it is added. A registry test used a name it never imported.
- **A poet who answered the question it was asked was refused.** The
  poetry world's law counted only words of the prior turn's proposal as a
  reference; now words of its invitation count too.
- **Worlds trusted what visitors sent.** A short token, an unreadable
  passport, a payload that isn't a mapping, a turn whose parts aren't
  text, or a reaction count of "2" or -1 made a world raise an error, or
  accept nonsense; "false" counted as holding a turn open. Each is now
  refused with a reason. One rule closes the whole class: only plain
  built-in values cross the protocol (text, numbers, true/false, lists,
  mappings), never subclasses of them, which could redefine how they
  compare or hash. Over the network, JSON enforces this by itself.
- **One copy of the entering code instead of three.** The poetry world,
  the chemistry world and the registry each had the same petition code;
  it lives once in `multiverse/entity.py`, which also does leaving.
- **The registry asked twice.** It listed whatever a second call to an
  entity's manifest returned, after the test had checked the first; an
  entity could pass and then raise, or give another manifest. Now the
  checked manifest is the one listed. Only whoever listed an entity may
  take the listing down, and a registry doesn't list itself.
- **What wasn't brought in:** the poetry engine's own Polyphony runner,
  since the poetry world checks turns and convergence.

Known limits carried over, to be fixed in later steps: a registry's
listing act carries the world itself, so it works only within one
process (course step 12);
`log_since` can skip an entry written in the same microsecond, and
in-process readers share the log's entries rather than getting copies.
"A world never raises on what a visitor sends" holds for ordinary
errors; it does not make it safe to run untrusted code in the same
process, which could exit the program or loop forever. Outside agents run
in their own processes and reach worlds through the protocol
(DESIGN.md). Two more for course step 12: non-finite numbers (NaN,
infinity) count as plain here but aren't valid JSON, and a payload built
from many shared references can take long to check; over the network a
payload is plain JSON of its real size, which removes both.
Until worlds have keys, a world can't take down its own listing, and a
listing whose lister has left stays up; and two registries may list each
other, which matters once listings are followed over the network
(course step 12).

The sketch's demonstration opened with a poem of the founder's. The
founder preferred a known poem as the starting example ("We should use a
known poem to start anything"), so the demonstration opens with Emily
Dickinson's "Hope is the thing with feathers" (1891), and the apprentices'
portfolios are stanzas of her other poems.

The signing components couldn't be tested here, because this
environment's crypto library is broken; course step 2 wrote the
signatures without it. One test sample, described as "real outputs" of a model, was
invented: DeepSeek could not have run the model. It won't be used.

## For the founder

- **Coming in.** Is the default for a world "anyone who will act under its
  published law"? The recommendation is yes.
- **History and admission.** May a world refuse someone because of their
  history elsewhere, for example an expulsion for an attack? A passport
  makes that history visible, which is transparent but also lasting. The
  recommendation: a world may set such conditions only in its published
  law, so everyone knows them before arriving.

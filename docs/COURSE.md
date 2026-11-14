# The course

The founder: "Let’s plot a course forward and then after each completed
step, plot a new one that adds one new step forward."

So the course always looks twelve steps ahead. When a step is done:

1. it moves to "Done", with its date and pull request;
2. the steps left are rechecked, and reordered or replaced if the work
   taught us something (with the reason written here);
3. one new step is added at the end, or where the waiting list already
   placed it;
4. a look back: each decision the technical lead recorded in STATUS is
   checked against its "revisit if", and what held, what didn't and what
   changes is written in STATUS's log.

Each step is one tested, independently reviewed piece of work. The
founder can reorder or swap steps at any time: this is a plan, not a
contract.

**The course was set anew on 2026-11-13,** for the Ur-world and its first
individuals, ALICE and BOB. The founder: "Yes, this should be the new
list, since much has changed since then. And I like that we return to
DeepSeek at step 10, because I wanted to have our beginning
infrastructure built out before returning." Each step names the
established practice it borrows, so that we build on what others have
learned over decades rather than learning it again. The design behind it
is in [MINDS.md](MINDS.md), [WORLD-KEY.md](WORLD-KEY.md) and
[URWORLD.md](URWORLD.md), and the research behind the borrowing is in
[research/GAMES-AND-WORLDS.md](research/GAMES-AND-WORLDS.md). The first
course's design is [MULTIVERSE.md](MULTIVERSE.md).

## Done: the first course

1. **The multiverse's core, working** (2026-11-12, #12 and #13, the
   write-up that added this page). The sketch's components 1 to 7, with
   leaving added: identity, passport, protocol, conformance test, poetry
   world, chemistry world, registry, and the first collaboration.
2. **Keys and signatures** (2026-11-12, #14). An individual's identity is
   its public key; every petition, act and leave is signed for one world
   with a growing number, so it can't be forged, moved or replayed, and
   the eight weak keys anyone could sign for are refused.
   Ed25519 first written here from RFC 8032, then, once the founder
   lifted the standard-library rule, taken from the `cryptography`
   package (#15), keeping our check on weak keys, which the library
   accepts. Protocol
   WCP/0.2. A world's log names a key only for what that key signed.
   Learned: keys live only in memory for now, so keeping keys safely
   joins the next-in-line list, before belongings and homes; and a good
   signature proves only who sent a request, so every check on its
   values is tested again with signed requests.
3. **Signed passports** (2026-11-13, #19). Worlds are keys too: a
   world's manifest names its key and is signed by it. A world signs a
   stamp for each arrival, each departure and each thing made there (by
   the thing's fingerprint), and anyone can check a passport offline
   with `verify_passport`. A forged or altered stamp is refused, and so
   is a stamp "from" a world under a key that isn't the one it is known
   by. Leaving is the individual's own signed request naming the arrival
   it ends, kept in its passport, so a world that won't stamp a departure
   can't stop it: the visit shows as ended on the holder's word, and the
   conformance test names the missing stamp. Requests name the world's
   key as well as its id. Protocol WCP/0.3.
   Learned: a stamp proves which key signed it, not which world; the
   link from a world to its key comes from the world's signed manifest,
   so a stamp is worth something only while that key is known. That
   moves keeping keys safely onto the course, as step 6 (below). Also: a
   holder can leave stamps out of what it shows but can't change, add or
   repeat one, and a passport shows every world in it to every world it is
   shown to (unlinked presences were decided later: STATUS.md,
   2026-11-14).
4. **The chemistry world on the real chemistry** (2026-11-13, #21). Its
   law is now on `chem/`: a soup of real molecules (one well-mixed cell)
   that starts with published soil and runs its own reactions by exact
   stochastic simulation from a published seed. An act names a reaction
   rule and the molecules it acts on; if the rule applies and they are
   there, the reaction happens, with atoms the soup already has. Each
   accepted act lets exactly the published time pass. Two engine
   additions: `Soup.perform` (an act) and `Soup.advance` (the clock lands
   exactly). It passes the conformance test. The soup's rates are
   placeholders, said so in its law.
   Learned: an act here makes a reaction happen, and a real catalyst
   can't do that. A catalyst speeds a reaction both ways and leaves the
   equilibrium where it was; until energy and rates come in, an agent can
   push any reaction the rules allow, however uphill. So the learner's
   goal (step 7) would be one act. Also, the soup's own reactions are a
   fixed, published list: a molecule an act makes has no reactions of
   its own yet (a dipeptide doesn't hydrolyse by itself).
5. **The first journey** (2026-11-13, #22). The corridor of Cycle 0
   speaks the protocol, on the world kernel, and its law publishes doors,
   each naming the world beyond by id and key. Worlds learn each other's
   keys from signed manifests (`Entity.know`), so every door checks the
   passport against the right keys. Alice walks from the corridor into
   the chemistry world, on to the poetry world, and back; her passport
   ends with ten stamps that all verify (`python3 -m multiverse.journey`).
   Learned: going through a door is a leave, then a petition, so for a
   moment the individual is in no world, and a refusal on the far side
   leaves it outside both; and a corridor ticks only when someone acts.
6. **Keeping keys safely, parts one and two** (2026-11-13, #23 and #24).
   Keys saved encrypted, a world's seen numbers kept across a restart,
   and a key signed over to a new one by both keys, for individuals and
   for worlds (WCP/0.4). Part three, a lost or leaked key, waits for the
   founder's answer, and is on the waiting list below.

## Done: the Ur-world so far

- **The garden** (2026-11-13, #28). The Ur-world's Hello World in Rust: a
  3D world made from its seed as it is explored, ALICE and BOB scripted.
- **The doorway for minds** (2026-11-13, #29). Any program, in any
  language, can be a mind: the orientation, what it sees written out,
  replies read strictly, nothing a mind sends can break the world.
- **Experiment 001, first words** (2026-11-13, #30). The smallest open
  models in the garden, planned before running. Speech began at about
  1.7 billion parameters; examples in the orientation became scripts;
  minds without memory looped
  ([results](../experiments/001-first-words/RESULTS.md)).

## Done: the new course

1. **The design pages** (2026-11-13 to 14; #31, #32, #34 to #38, #41,
   #44, #45). [MINDS.md](MINDS.md): the parts of an individual, the
   layers of what a mind is told, how information moves, where everything
   lives. [WORLD-KEY.md](WORLD-KEY.md): the purpose, the tour, the hunt
   for the world-key. [ADMIN.md](ADMIN.md): what the multiverse must
   preserve, who keeps each world, and ADMIN, with its training, the
   round table, a learning immune system and how it holds its powers;
   [REASONS.md](REASONS.md), decisions on record; [FREEDOMS.md](FREEDOMS.md),
   tools for when freedoms meet; [PARALLEL-WORLDS.md](PARALLEL-WORLDS.md)
   and [VISION.md](VISION.md), the founder's visions of 2026-11-14. The
   research behind them.
2. **Formats that last** (2026-11-13 to 14; #33, #39, #40, #42, #43, #46
   to #48). Looked at first ([research/FORMATS.md](research/FORMATS.md)),
   then built in Python and Rust, which agree through shared vectors:
   every record signed as a W3C Data Integrity proof (`eddsa-jcs-2022`)
   over its RFC 8785 form, keys as did:key; one JSON Schema,
   `schemas/records-v1.schema.json`, for the grant, decision record,
   suggestion, rating and signed log head, the world-key and journal
   entry, identity, birth records, mind record, and a world's template
   with its dials; sealing with HPKE (RFC 9180) and sealed records in
   envelopes; and the chemistry world's records of what was made, without
   floats. Noise stays named only for a private line, if the founder
   chooses one. Of the formats this step named, four moved to the steps
   that build what they describe (decided 2026-11-14, STATUS.md): the
   avatar to step 4, the sheet and skill attestation to step 5, the
   routine to step 7.

**Rechecked on 2026-11-14,** when steps 1 and 2 were done. Two steps
came in from the waiting list, one for each step done, so the course
still looks twelve steps ahead. They go where they were already placed,
not at the end: persons after step 3, and parallel worlds right after
step 4 (the founder's placing). They are numbered 3a and 4a, so that the
step numbers other pages cite stay as they are. What the
formats taught is written into the steps it reaches: the project's keys
for mind records and templates (step 3); the avatar, the checks across
records the formats left, and a bound on a record's size (step 4); the
sheet and skill attestation (step 5); the routine (step 7); and the
records that confirm a founding (step 12). Nothing was reordered
otherwise.

## Ahead

3. **Keys and identities, for them and for the world.** Under way: the
   plan, after looking first, is in
   [research/KEYS.md](research/KEYS.md), in four parts (the plan; a key
   list signed by the multiverse's root, and the tool that makes keys;
   the ceremony; leaving and coming back in the Ur-world). A private
   repository of the project for the private halves; ALICE's and BOB's
   signing keys, and keys for sealing things to them, which also open
   their sealed selves; their identity, birth and mind records wait for
   their birth, at step 9, since a birth record names the mind chosen at
   step 8 (rechecked 2026-11-14). The Ur-world's
   own keys: one to sign its log, one for sealing things to it; and
   ADMIN's. The multiverse's root key, published, and a key of the code
   role's, for outcomes on suggestions before ADMIN exists
   ([ADMIN.md](ADMIN.md), "Suggestions from inside"); the project's keys
   for mind records and for templates, which those records name as their
   issuer ([research/FORMATS.md](research/FORMATS.md)). Leaving and coming
   back: whoever leaves can return, proving
   with their key that they are the same individual. *Borrowing:*
   standard key handling, private halves kept apart and public halves
   published.

**3a. Persons.** A person above their presences in each world
([MULTIVERSE.md](MULTIVERSE.md)), unlinked by default, with the
architectures (octopus, relay, swarm, council) as small examples on the
unchanged core; a person across worlds, as the founder pictured it
([VISION.md](VISION.md), "A person across worlds"). Moved here from the
waiting list, where it was placed after step 3 (decided 2026-11-14).

4. **The kernel as entities and components.** Inhabitants, their bodies,
   stones, tablets and seeds become entities with parts; every change is
   a named, logged effect; tags allow or block actions. The Keeper's
   administrative actions, as grants, and the checks on what it designs,
   are fixed here, so its interface is settled early; so are ADMIN's
   checks as code. An office's act is refused without its decision
   record, and a model of grants in Lean proves that no chain of grants
   widens, checked by CI ([REASONS.md](REASONS.md)). The avatar's format
   joins records-v1 here, with the body it describes; so do the checks
   across records that the formats leave to the kernel (listed in
   `formats/records.py`), and a bound on the size of any record received.
   A template's code builds a world from its dials. World time is kept as
   whole microseconds, not a float of seconds, so a record's time is an
   exact sum however long a world runs (the chemistry world's clock
   loses microsecond steps after about two years: #48). *Borrowing:* the
   entity-component pattern (Bevy's), and Unreal's effects and tags;
   Lean, and proof-carrying code.

**4a. Parallel worlds, and a garden to walk among them.** A few parallel
chemistry worlds from one template, each with its own key and log and
the dials it changed in its birth record; and a view-only garden whose
rooms show their live state from their public logs, the first thing
others can look at and understand
([PARALLEL-WORLDS.md](PARALLEL-WORLDS.md)). Moved here from the waiting
list, where the founder placed it, right after step 4. *Borrowing:*
controlled experiments, and replay from a seed.

5. **Things, skills and the sheet.** Carrying, reading, `lift` as the
   first skill granted by a find, practice and rust, a log of what is
   known, and the sheet rebuilt from the world's log and checked against
   it. The sheet's and a skill attestation's formats join records-v1
   here. *Borrowing:* use-based skills (Dwarf Fortress, the Elder Scrolls),
   Unreal's ability system, Outer Wilds' log of knowledge.
6. **The first room, end to end.** The tour, guided by a simple scripted
   Keeper; the stone by the spring, the first clue, `lift` learned, the
   first fact known; playable by a scripted mind and by a model. The
   prompt's framing becomes part of the law, sent by the world. Minds run
   in containers, with no network, and a test that a removed mind's
   container stops ([ADMIN.md](ADMIN.md), "Minds in containers").
   Suggesting is an act from the first room: anyone can add to the open
   ledger. *Borrowing:* the vertical slice; OCI containers, with gVisor for
   minds we didn't write.
7. **Memory, version 1, sealed.** Journal entries tied to ticks in the
   log; recall by recency, importance and relevance; reflections; held
   thoughts in a few slots; a library of routines they write, whose
   format joins records-v1 here. All of it
   in a sealed self that no one else reads, opened only under the
   founder's "break glass", with public fingerprints. *Borrowing:* Generative
   Agents, Voyager's skill library, Disco Elysium's thought cabinet,
   guarding against their known failures.
8. **Experiment 002, the audition.** Candidate sizes of Qwen 3.5 and OLMo
   3 play the first room, with and without memory, planned first. It
   chooses ALICE's and BOB's sizes, and tests whether memory helps. It
   runs in images pinned by digest, so anyone can repeat it.
   *Borrowing:* pre-registration; evaluation suites.
9. **ALICE's and BOB's first life.** Their minds, their birth, their
   identity, birth and mind records (moved here from step 3), their
   first unscripted words; legends pages begin. The suggestion ledger
   opens to them, with its bridge to GitHub, so what they suggest can
   improve the worlds from the start. *Borrowing:* Dwarf Fortress's
   Legends mode.
10. **Back to DeepSeek.** First, a development container, so anyone can
    pick the project up and work in the same setup. The re-orientation
    page in [COLLABORATING.md](COLLABORATING.md), pointing to the records;
    DeepSeek designs rooms, clues, symbols and the laws of new worlds,
    inside the framework built in steps 1 to 9.
11. **The hunt, the world-key, and the AI Keeper.** The Keeper builds each
    individual's own path from what they do, and remembers them between
    visits; its designs open from the start (challenges, not tests);
    symbols,
    maps, codes and stones; the pieces of a world; the world-key, a signed
    right to found, sealed for its earner when the path is done; the open
    line to the Keeper for those who hold its world-key; the workbench.
    *Borrowing:* Tunic, The Witness and Outer Wilds for teaching without
    words; Minecraft's advancements for unlocks; AI directors and
    intelligent tutors, with TextWorld and knowledge tracing to learn
    from, for the Keeper. The Ur-world's Keeper is its own office, never
    ADMIN's; and since ADMIN then has an office to watch, ADMIN's
    judgment and the multiverse log come with it, built for many worlds
    (moved here from step 12 on 2026-11-13, for that reason;
    [ADMIN.md](ADMIN.md)). Before it trains anyone, ADMIN's mind is
    chosen by audition, free in every sense, perhaps a council of
    models, and ADMIN takes its own course in a world of its own, with
    stand-ins only, taking on challenges it announces before it starts,
    with nothing hidden: challenges, not tests. Then its first
    work is to train the Ur-world's Keeper in practice worlds, with
    stand-ins, before it keeps the Ur-world with ALICE and BOB in it:
    coaching toward the Ur-world's own aims, never command (founder,
    2026-11-13; moved here from the waiting list). ADMIN becomes the
    bridge from the suggestion ledger to the outside: it can suggest
    changes, never make them ([ADMIN.md](ADMIN.md), "Suggestions from
    inside").
12. **Founding worlds, and doors.** What only a second world needs:
    child worlds, each with a new key of its own, a birth record it signs
    itself, and records by its founders and its parent world confirming
    the founding, the parent's naming the world-keys used; a Keeper
    chosen by its founders; doors between them, travel with
    passports, founding together, and the world protocol in Rust. The
    open line reaches a Keeper from another world, and a founded world's
    Keeper has a line to its parent's. *Borrowing:* our own protocol and
    passports, the open standards of step 2, and Matrix and Signal for the
    line.

## Waiting

Added one at a time, as steps are done:
- fractal worlds (the founder, 2026-11-14: "Worlds where you can
  navigate through fractals, generate them in different forms, watch them
  grow or interact, and more"): primary worlds whose rule is repeated,
  with its numbers as a template's dials; recommended after step 4a, as
  the garden's second kind of room;
- the Commons (the founder, 2026-11-14): Lyceum Commons as "a single
  superworld, where the atomic subworlds are chat rooms"; recommended
  after step 4a, as the second superworld (docs/TOPICS.md, topic 14,
  which also recommends how);
- from the founder's visions of 2026-11-14
  ([VISION.md](VISION.md)): question worlds, with the prediction written
  first, and the neural world as the first; riding along in a primary
  world, and steering by branching; and the plug-in, so a chat with any
  AI can create, run and query a world, on one's own computer first;
- Keepers talking to one another, by the rules proposed in
  [WORLD-KEY.md](WORLD-KEY.md);
- the admin-key: a course for Keepers, plotted by ADMIN as Keepers plot
  paths ([ADMIN.md](ADMIN.md)), after steps 11 and 12, once a Keeper has
  a record to judge (training itself begins at step 11);
- the round table: ADMIN's seat, and one for each Keeper who earns the
  admin-key, deciding by consensus what all worlds share
  ([ADMIN.md](ADMIN.md)); it decides from its second seat;
- tools for when freedoms meet: not hearing a speaker, and agreements
  others can accept or refuse ([FREEDOMS.md](FREEDOMS.md));
- a window onto the worlds: a web viewer first, in Bevy, in the browser;
- generator 2: land decided when first seen;
- a storyteller for each world: paced events and visitors;
- the gate and districts, with the chemistry and poetry worlds as the
  first districts;
- governance: a proposal to change a world's law is tried on a copy
  first, and adopted only by consent;
- part three of keeping keys safely: a lost or leaked key;
- from the first course, still wanted:
  - the first learner, with real rates and the gardener's water, and an
    organic chemistry world entered by its stamp;
  - time and populations;
  - any AI from any app, over the network (now the plug-in, above);
  - a common-meter poetry world;
  - a single-cell world;
  - a world others built;
  - belongings and homes;
  - visiting two worlds at once;
  - a curator for each world;
  - contracts between worlds;
  - a shared log of commitments
  ([sketches/INDEX.md](../sketches/INDEX.md) says where each meets the
  sketch).

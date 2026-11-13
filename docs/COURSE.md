# The course

The founder: "Let’s plot a course forward and then after each completed
step, plot a new one that adds one new step forward."

So the course always looks twelve steps ahead. When a step is done:

1. it moves to "Done", with its date and pull request;
2. the steps left are rechecked, and reordered or replaced if the work
   taught us something (with the reason written here);
3. one new step is added at the end.

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
   shown to (the founder's open question on unlinked presences).
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

## Ahead

1. **The design pages.** [MINDS.md](MINDS.md): the parts of an
   individual, the layers of what a mind is told, how information moves,
   and where everything lives. [WORLD-KEY.md](WORLD-KEY.md): the purpose,
   the tour, and the hunt for the world-key. The research behind them.
   *Borrowing:* the game industry's split of controller, body and saved
   data; characters built from components.
2. **Formats that last.** A precise, versioned definition of each record:
   identity, birth record, mind record, journal entry, routine, sheet,
   avatar, and skill attestation. Test vectors keep Rust and Python in
   agreement. *Borrowing:* JSON Schema; W3C's decentralised identifiers
   (did:key) and verifiable credentials for signed claims; RFC 8785 for
   writing JSON identically everywhere before signing; HPKE (RFC 9180) for
   sealing, and the Noise protocol framework for a private line. Also the
   commitments that hold back a challenge's answer: a random value of at
   least 128 bits, derived for each challenge, over JSON written by RFC
   8785.
3. **Keys and identities, for them and for the world.** A private
   repository of the project for the private halves; ALICE's and BOB's
   signing keys, keys for sealing things to them, and the keys to their
   sealed selves; birth records and public identity files. The Ur-world's
   own keys: one to sign its log, one for sealing things to it. Leaving
   and coming back: whoever leaves can return, proving with their key that
   they are the same individual. *Borrowing:* standard key
   handling, private halves kept apart and public halves published.
4. **The kernel as entities and components.** Inhabitants, their bodies,
   stones, tablets and seeds become entities with parts; every change is
   a named, logged effect; tags allow or block actions. The Keeper's
   administrative actions, and the checks on what it designs, are fixed
   here, so its interface is settled early. *Borrowing:* the
   entity-component pattern (Bevy's), and Unreal's effects and tags.
5. **Things, skills and the sheet.** Carrying, reading, `lift` as the
   first skill granted by a find, practice and rust, a log of what is
   known, and the sheet rebuilt from the world's log and checked against
   it. *Borrowing:* use-based skills (Dwarf Fortress, the Elder Scrolls),
   Unreal's ability system, Outer Wilds' log of knowledge.
6. **The first room, end to end.** The tour, guided by a simple scripted
   Keeper; the stone by the spring, the first clue, `lift` learned, the
   first fact known; playable by a scripted mind and by a model. The
   prompt's framing becomes part of the law, sent by the world.
   *Borrowing:* the vertical slice.
7. **Memory, version 1, sealed.** Journal entries tied to ticks in the
   log; recall by recency, importance and relevance; reflections; held
   thoughts in a few slots; a library of routines they write. All of it
   in a sealed self that only its owner can read, with public
   fingerprints. *Borrowing:* Generative
   Agents, Voyager's skill library, Disco Elysium's thought cabinet,
   guarding against their known failures.
8. **Experiment 002, the audition.** Candidate sizes of Qwen 3.5 and OLMo
   3 play the first room, with and without memory, planned first. It
   chooses ALICE's and BOB's sizes, and tests whether memory helps.
   *Borrowing:* pre-registration; evaluation suites.
9. **ALICE's and BOB's first life.** Their minds, their birth, their
   first unscripted words; legends pages begin. *Borrowing:* Dwarf
   Fortress's Legends mode.
10. **Back to DeepSeek.** The re-orientation page in
    [COLLABORATING.md](COLLABORATING.md), pointing to the records;
    DeepSeek designs rooms, clues, symbols and the laws of new worlds,
    inside the framework built in steps 1 to 9.
11. **The hunt, the world-key, and the AI Keeper.** The Keeper builds each
    individual's own path from what they do, and remembers them between
    visits; its designs held back by commitment until solved; symbols,
    maps, codes and stones; the pieces of a world; the world-key, a signed
    right to found, sealed for its earner when the path is done; the open
    line to the Keeper for those who hold its world-key; the workbench.
    *Borrowing:* Tunic,
    The Witness and Outer Wilds for teaching without words; Minecraft's
    advancements for unlocks; AI directors and intelligent tutors, with
    TextWorld and knowledge tracing to learn from, for the Keeper.
12. **Founding worlds, and doors.** Child worlds, each with a new key of
    its own and a signed birth record, doors between them, travel with
    passports, founding together, and the world protocol in Rust. The
    open line reaches a Keeper from another world, and a founded world's
    Keeper has a line to its parent's. *Borrowing:* our own protocol and
    passports, the open standards of step 2, and Matrix and Signal for the
    line.

## Waiting

Added one at a time, as steps are done:
- Keepers talking to one another, by the rules proposed in
  [WORLD-KEY.md](WORLD-KEY.md);
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
  - any AI from any app, over the network;
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

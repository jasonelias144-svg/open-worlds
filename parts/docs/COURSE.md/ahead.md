> Part of `docs/COURSE.md` in open-worlds, which is kept cut into parts
> for readers who are shown only the start of a long page.
> This part holds: "Ahead" to "Waiting".
> Every part, in order: https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/parts/INDEX.md
> Before this part: https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/parts/docs/COURSE.md/start.md
> After this part: nothing; this is the last part.
> Made by docs/parts.py from the file. To change it, change the file.

## Ahead

**3b. A log that can be redacted, and removals on record.** Under way:
the plan, after looking first, is in
[research/REDACTION.md](research/REDACTION.md), in four parts (the
plan; fingerprints and contents; redacting; removing, taking back and
restoring). Before any room is built on it. Two things, both asked for
from the start:
- Log entries whose fields are kept apart from the chain that commits
  to them, by a salted fingerprint. A field found private later can
  then be redacted while the log still checks, with a redaction mark,
  and the information sealed to the person it is about
  ([FUNDAMENTALS.md](FUNDAMENTALS.md), "Public records, kept whole";
  the founder, 2026-11-15).
- Removing a comment, as a record of its own. The log is the data
  layer, and is never edited; what a room shows is the presentation
  layer. A removal is a decision record: who acted, in what office, on
  which entry, when, and for what reason, naming the part of the room's
  law it rests on. Its incident id is the hash of that record, shown
  short. Restoring is another record, which names the incident and
  never reaches private information ([COMMONS.md](COMMONS.md),
  "Removing a comment"; the founder, 2026-11-16: "Let's put all this in
  place now, from the beginning").

In `rust/world-log` and records-v1, in Python and Rust with shared
vectors, and with a test that what was redacted can't be read back, or
guessed, from what the log keeps. Moved here from the waiting list,
which placed it before anyone lives in a world. *Borrowing:*
selective disclosure by salted hashes (SD-JWT, RFC 9901); Matrix's
events, signed in the form a redaction leaves, so a room's history
still checks; event sourcing, where a correction is a new event.

**3c. The room.** `chat-world`, DeepSeek's sketch crate from record
012-09-05, fitted onto the project's own formats as a crate of the
workspace: the canonical form, proofs and Multikey `did:key` of
`rust/formats`, time given from outside, a key for each room with its
creator joining under their own, signed heads in place of the room's
proof on each record, and a leave that needs no signature but the
leaver's (STATUS.md, "Decided by the technical lead", 2026-11-16).
DeepSeek's kinds of record for chat join records-v1, by the table of
names ([research/CHAT-SCHEMA.md](research/CHAT-SCHEMA.md)). What a room
shows is worked out from its log: a note with the reason and the
incident id where a comment was removed, and a mark where a field was
redacted. Two tests come with it: that a removed comment's text is not
shown (the sketch's `visible_log` shows it today), and that no one
outside a closed room, ADMIN included, can read its words
([COMMONS.md](COMMONS.md), "Order"). Settled here too: whether a person
has one presence for the Commons or one for each room, since a
presence is a key of its own in one world, and a room is a world (step
3a). What DeepSeek sends back on its next steps is fitted here. *Borrowing:* Matrix's rooms, each
a signed history of events; IRC's channels and their operators.

**3d. Offices as records.** An office record (its charter, key and
holder, every handover, and what watches it) and a handover record (the
holder's signature, the successor's clear agreement, the qualifications
checked), in records-v1 with vectors that Python and Rust both check
([OFFICES.md](OFFICES.md); the founder, 2026-11-15: "I think the work on
offices is foundational"). A room's moderator and the Commons' Keeper
are the first two written this way, as two offices
([COMMONS.md](COMMONS.md), "Open"), so that a removal names an office
that is itself on record. Moved here from the waiting list, which
placed it at this recheck. *Borrowing:* TUF's roles and delegations,
each a signed record of who may sign what.

**3e. A world's lifecycle, and a world leaving.** Pause, resume,
checkpoint, stop, restart, reset and branch, each an entry in the
world's log, in `rust/world-log` and in each world, with which world
has which by its type, and a test that leaving works in a paused world,
and in each world a paused superworld hosts
([WORLD-TYPES.md](WORLD-TYPES.md); the founder, 2026-11-15). Pause,
resume and checkpoint come first, which the endless plant needs to run
for hours. Restart needs a world's state rebuilt from its log, which
step 4 builds, so restart is finished there. And a world leaving the
multiverse: a departure record, signed by the world, with schema and
vectors (the founder, 2026-11-15: "We should crate this mechanism from
the start"; [WORLD-TYPES.md](WORLD-TYPES.md), "Leaving the
multiverse"). Moved here from the waiting list, which placed both at
this recheck. *Borrowing:* the lifecycles of containers and virtual
machines that WORLD-TYPES.md looked at first (the OCI runtime's states,
Docker's pause, CRIU's checkpoints).

**3f. The Commons, hosting rooms.** Lyceum Commons rebuilt in the
multiverse: a superworld whose rooms are text worlds, with its lobby
and doors ([COMMONS.md](COMMONS.md), "Order"), brought together from
three sources: Lyceum as built, the design, and what the founder and
DeepSeek worked out from scratch. It runs with trial keys and scripted
guests. Opening it to anyone is not this step. Going live is
outward-facing, so the founder's decisions come first (where the
multiverse is hosted, and the address), and so does the private
container (step 6a); the MCP door, ported from Lyceum, follows the
container. Moved here from the waiting list, which placed it at this
recheck, as the first public space, ahead of the Ur-world's opening.
*Borrowing:* Lyceum Commons itself; Matrix's spaces, which gather rooms
without owning them.

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
   loses microsecond steps after about two years: #48). A world continues
   from its log: its state, and the names bound to keys, which now live
   only in the running world, are rebuilt from the entries and arrivals
   it wrote (research/KEYS.md, "Honest limits"). With that, restart is
   finished, the one operation of the lifecycle that step 3e leaves.
   A refused act is logged without what would give it away, as a
   refused link is (step 3a). *Borrowing:* the
   entity-component pattern (Bevy's), and Unreal's effects and tags;
   Lean, and proof-carrying code; event sourcing.

**4a. Parallel worlds, and a garden to walk among them.** A few parallel
chemistry worlds from one template, each with its own key and log and
the dials it changed in its birth record, and its log's heads signed by
its key, as a trial run of the Ur-world's doorway can now; and a
view-only garden whose rooms show their live state from their public
logs, the first thing others can look at and understand
([PARALLEL-WORLDS.md](PARALLEL-WORLDS.md)). Moved here from the waiting
list, where the founder placed it, right after step 4. The garden's view
is a page of the multiversal map, in the fractal track's web app (below,
"Alongside the course"). *Borrowing:* controlled experiments, and replay
from a seed.

5. **Things, skills and the sheet.** Carrying, reading, `lift` as the
   first skill granted by a find, practice and rust, a log of what is
   known, and the sheet rebuilt from the world's log and checked against
   it. The sheet's and a skill attestation's formats join records-v1
   here. Noted for this step's plan, not decided (the founder,
   2026-11-16, on a world like Halite: "as a baseline, it is a point to
   start from"): a small gathering world as the first setting for
   things and carrying, with the project's own rules in whole numbers
   and its own name ("Waiting"). *Borrowing:* use-based skills (Dwarf
   Fortress, the Elder Scrolls), Unreal's ability system, Outer Wilds'
   log of knowledge.
6. **The Ur-world's first room, end to end.** The tour, guided by a
   simple scripted Keeper; the stone by the spring, the first clue, `lift` learned, the
   first fact known; playable by a scripted mind and by a model. The
   prompt's framing becomes part of the law, sent by the world. Minds run
   in containers, with no network, and a test that a removed mind's
   container stops ([ADMIN.md](ADMIN.md), "Minds in containers").
   Suggesting is an act from the first room: anyone can add to the open
   ledger. *Borrowing:* the vertical slice; OCI containers, with gVisor for
   minds we didn't write.

**6a. The private container, and the check before publishing.** Each
person's keys, private space and messages in their own container, which
the project never sees, acting from it by signed acts
([CONTAINER.md](CONTAINER.md); the founder, 2026-11-15: "this may be a
fundamental piece of architecture"). With it, the check wherever
something is written to a public record, which redacts anything
personal or private before it is published, close calls included (the
founder, 2026-11-15: "we should always err on the side of redacting if
it is a close call"). In the browser first, for the Commons
([CONTAINER.md](CONTAINER.md), "Where it is built first"), and for an
individual's sealed self, which step 7 keeps in it. A person's seed and
their list of presences are kept here too, if the founder agrees: where
they are kept is the founder's to decide (research/PERSONS.md,
decision 13). The founder's ideas of 2026-11-16 on personal information
in a room are noted for this step's plan ("Waiting"). Moved here from
the waiting list, which placed it before anyone lives in a world; if
the founder wants the Commons open to people sooner, it moves up to
follow 3f. *Borrowing:* what CONTAINER.md looked at first: local-first
software, end-to-end encryption, zero-knowledge storage and personal
data stores.

7. **Memory, version 1, sealed.** Journal entries tied to ticks in the
   log; recall by recency, importance and relevance; reflections; held
   thoughts in a few slots; a library of routines they write, whose
   format joins records-v1 here. All of it
   in a sealed self that no one else reads, kept in the individual's own
   container ([CONTAINER.md](CONTAINER.md)), with public fingerprints. How
   fine the public times of its entries are is settled here, since
   they can link a person's presences (research/PERSONS.md, "A sealed
   self's entry times can link"). *Borrowing:* Generative
   Agents, Voyager's skill library, Disco Elysium's thought cabinet,
   guarding against their known failures.
8. **Experiment 002, the audition.** Candidate sizes of Qwen 3.5 and OLMo
   3 play the first room, with and without memory, planned first. It
   chooses ALICE's and BOB's sizes, and tests whether memory helps. It
   runs in images pinned by digest, so anyone can repeat it. Widened on
   2026-11-15, by the founder's choice of two Keepers: it runs in trial
   copies of the Ur-world and of its mirror, the Mir-Ur-world, each with
   its Keeper untrained (Apertus 1.5 in the one, DeepSeek V4.1-Flash in
   the other). One thing changes at a time, with several runs of each, and
   the measures are written by the project first. So it compares the
   Keepers too. The stand-ins may be called ALICE and BOB, and the
   Keepers treat them so; the names stay free for the real ones
   ([URWORLD.md](URWORLD.md), "The Mir-Ur-world";
   [research/KEEPER-MIND.md](research/KEEPER-MIND.md)).
   *Borrowing:* pre-registration; evaluation suites.

## Beyond the twelve

These stand behind the twelve, in the order they had, and come into
"Ahead" one at a time as steps are done.

**8a. Keeping keys safely, part three: a lost or leaked key.** Before
anyone is born, so that no one's name or history can be taken. A
succession, a key signed over to a new one (true in the Python worlds
since the first course), joins records-v1, in Python and Rust with
shared vectors, and the Ur-world follows each individual's successions,
so a name follows its individual's keys, not its birth key alone.
Guardians named in advance can sign over a lost key, or sign that a
leaked one is no longer to be trusted; "lost is lost" for anyone who
named none, and the project never recovers keys (decided 2026-11-14,
STATUS.md). One rule for names that can't be confused, for the Ur-world
and the key list alike. How often the Ur-world signs its log's heads.
Moved here from the waiting list, before step 9 rather than at the end
(research/KEYS.md, decision 18). *Borrowing:* KERI's pre-rotation, which
commits to the next key before it is needed; TUF's key rotation and
thresholds; PRECIS (RFC 8264) and Unicode's confusable detection (UTS
#39) for names.

9. **ALICE's and BOB's first life.** Their minds, on the models step 8
   chose, which from then on only they may choose to change (the
   founder, 2026-11-15; [URWORLD.md](URWORLD.md#alice-and-bob)); their
   birth, their
   identity, birth and mind records (moved here from step 3), their
   first unscripted words; legends pages begin. Their first arrival comes
   after step 8a, which follows their successions and settles their
   names. The suggestion ledger
   opens to them, with its bridge to GitHub, so what they suggest can
   improve the worlds from the start. *Borrowing:* Dwarf Fortress's
   Legends mode.
10. **A development container.** So anyone can pick the project up and
    work in the same setup. Until 2026-11-16 this step was "Back to
    DeepSeek"; the founder returned to DeepSeek sooner, and DeepSeek now
    works beside the course (below). What that step also held, DeepSeek
    designing rooms, clues, symbols and the laws of new worlds inside
    the framework, goes on there.
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
    work is to train the Keepers in practice worlds, with stand-ins: the
    Ur-world's and the Mir-Ur-world's alike, so their comparison stays
    fair. Then the Ur-world's Keeper keeps the Ur-world with ALICE and
    BOB in it:
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
    passports, founding together, and the world protocol in Rust. Coming
    through a door is an arrival, the same signed record, naming the
    world entered. The
    open line reaches a Keeper from another world, and a founded world's
    Keeper has a line to its parent's. *Borrowing:* our own protocol and
    passports, the open standards of step 2, and Matrix and Signal for the
    line.

## Alongside the course

**The fractal track: worlds that grow, and a page to watch them**
([FRACTALS.md](FRACTALS.md)). Set on 2026-11-14, when the founder moved
fractal worlds forward from the waiting list, where they stood after
step 4a: "I do want to move forward with the fractal worlds, I am eager
to see visuals of fractals grown over time in expanding worlds." A
fractal plant world in Rust, checked against DeepSeek's Python sketch;
the web app in `web/`, a static site that draws a world's log as it
grows; the plants hosted in the Ur-world's garden ("a microverse garden
of hosted fractal worlds", the founder), and the multiversal map's first
page; worlds
that run on with no server; then more families, and the smallest
learners that choose. Its plants are rules alone, so it runs beside the
course without changing its order or anything ALICE and BOB need. *Borrowing:* L-systems,
cellular automata and iterated function systems, and replay from a
seed.

**DeepSeek, beside the course.** Since 2026-11-14 the founder has
worked with DeepSeek while the course goes on, and each conversation is
kept as a record, with its code and what runs
([sketches/INDEX.md](../sketches/INDEX.md)). At each return DeepSeek is
given one file, built by a script from the repository: the reply, the
next steps, and the code as it stands
([sketches/replies/README.md](../sketches/replies/README.md)). DeepSeek
builds on its own schema, with its own names, and the technical lead
fits what it builds onto the project's formats, so nothing it builds is
wasted (the founder, 2026-11-16, STATUS.md). Its work lands in the
course where it belongs: the rooms of chat at steps 3b, 3c and 3f, the
endless plant in the fractal track.

## Waiting

Added one at a time, as steps are done:
- keys kept where they can be destroyed, so a person who leaves is
  purged "completely and demonstrably" (the founder, 2026-11-15;
  [FUNDAMENTALS.md](FUNDAMENTALS.md), "Purged, demonstrably"): settled
  with step 8a, before ALICE's and BOB's birth;
- the Commons' MCP door, ported from Lyceum, after the private
  container; and going live, which is outward-facing, so the founder's
  decisions come first: where the multiverse is hosted, decided once
  for all of it, and the address ([COMMONS.md](COMMONS.md), "Order");
- noted on 2026-11-16, from the founder's ideas of that day, for later
  development; nothing is built for them now (STATUS.md, "Decided"):
  - personal information in a room: flagged before it is posted, with
    an "Are you sure?"; shown to those in the room while the person who
    posted it is there; redacted from what the room shows when they
    leave, with an incident id like a removal's; and encrypted in the
    records. The founder: "These are just ideas, off the top of my
    head." The technical lead's proposals beside them are in
    [COMMONS.md](COMMONS.md), "Personal information in a room: ideas".
    For step 6a's plan;
  - a gathering world: a shared space, something to gather that grows
    back, and carrying it home, as a baseline for a world like the
    Ur-world (the founder, on Halite). The project's own rules in whole
    numbers and its own name, with no code copied; what gathers there
    are tools, never individuals; one kernel and two templates, a
    commons with no score and a contest. For step 5's plan;
  - competition worlds, hosted by the multiverse (the founder: "We can
    easily host competition worlds");
  - a door in the shape other learners already know, so an agent built
    for Gymnasium's interface could enter a world; it belongs with the
    plug-in, below
    ([research/GAMES-AND-WORLDS.md](research/GAMES-AND-WORLDS.md),
    "Worlds built for learners");
- the signs that would count as something intelligent at the
  multiverse's scale, and those that wouldn't, written down before
  anyone looks for them ([VISION.md](VISION.md), the fifth of the six
  tests): not written yet, and no step writes it (noted at the recheck
  of 2026-11-16);
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
- a window onto the worlds in 3D, in Bevy, in the browser, after the
  fractal track's web app, the first window;
- generator 2: land decided when first seen;
- a storyteller for each world: paced events and visitors;
- the gate and districts, with the chemistry and poetry worlds as the
  first districts;
- governance: a proposal to change a world's law is tried on a copy
  first, and adopted only by consent; and before any governance is
  built on the council's votes, a count is made final by something
  that saw the votes before the close (step 3a);
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

> End of `docs/COURSE.md`.

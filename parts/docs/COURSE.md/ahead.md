> Part of `docs/COURSE.md` in open-worlds, which is kept cut into parts
> for readers who are shown only the start of a long page.
> This part holds: "Ahead" to "Alongside the course".
> Every part, in order: https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/parts/INDEX.md
> Before this part: https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/parts/docs/COURSE.md/start.md
> After this part: https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/parts/docs/COURSE.md/waiting.md
> Made by docs/parts.py from the file. To change it, change the file.

## Ahead

**Since 2026-11-17, ALICE and BOB first live in the Commons,** and
come to the Ur-world's garden after (the founder; STATUS.md,
"Decided"; [COMMONS.md](COMMONS.md), "The first to live there"). The
steps below still stand in the order of the last recheck. At the next
one, when 3b is done, their first life (step 9) moves ahead of the
kernel's steps (4 to 6): it then follows the room (3c), offices as
records (3d), the Commons hosting rooms (3f), memory (7), the audition
(8), a lost or leaked key (8a), and a new step, the Library. The
kernel's steps follow it, for the garden.

**3b. A log that can be redacted, and removals on record.** Built
(2026-11-16 to 18), and the course is rechecked next. The plan, after
looking first, is in
[research/REDACTION.md](research/REDACTION.md), in four parts (the
plan; fingerprints and contents; redacting; removing, taking back and
restoring). The second is built: a form of the log whose fields are
kept apart (`world/apart.py`, `rust/world-log`), with the check of a
log against its contents and the function that joins them. The log's
side of the third is built: a redaction's mark, which says its office
and its ground; the one decision that answers it, to keep the field
public or that it stays redacted for good; and the writer's steps
that take a field out and put it back in step with the log. Its other
side is built too, the act of redacting: the field sealed to each
person it is about and to the office that decides, then marked and
taken out, and the office's two decisions from its own copy
(`world/redact.py`, `rust/redact`). A writer can be opened on a log
written before, so an office can decide on a log another writer wrote.
The keys are trial keys, and nothing real is redacted yet.
The log's side of the fourth is built too: an entry
removed, restored, taken back or put back, each entry's state, and the
incident id. Its records' side is built too: every act in a log is
held to the signed record it carries, and every office to its grant,
up to the room's key; and the author's two kinds of record, for
taking back and for putting back, are in records-v1 (`world/acts.py`,
`rust/acts`). The room's steps that write an act only where that
check allows it are the room's (3c). Before any room is built on it.
Two things. The founder
asked that private information be redacted in public records
(2026-11-15), and that removals be on record "from the beginning"
(2026-11-16). How each is built is the technical lead's reading:
- Log entries whose fields are kept apart from the chain that commits
  to them, by a salted fingerprint. A field found private later can
  then be redacted while the log still checks, with a redaction mark,
  and the information sealed to the person it is about
  ([FUNDAMENTALS.md](FUNDAMENTALS.md), "Public records, kept whole").
  This form is for a world persons act in: with random salts a log is
  not the same, byte for byte, on a second run, so a closed world with
  no one in it keeps today's form. Until the private container exists
  (6a), what is sealed to a person is built and tested with trial
  keys.
- Removing a comment, as a record of its own. The log is the data
  layer, and is never edited; what a room shows is the presentation
  layer. A removal is a decision record: who acted, in what office, on
  which entry, when, and for what reason, naming the part of the room's
  law it rests on. Its incident id is the hash of the entry that
  carries it, shown short. Restoring is another record, which names the incident and
  never reaches private information. An author taking back their own
  comment is no office's decision, and gets a record of its own
  ([COMMONS.md](COMMONS.md), "Removing a comment"; the founder,
  2026-11-16: "Let's put all this in place now, from the beginning").

In `rust/world-log` and records-v1, in Python and Rust with shared
vectors, and with a test that what was redacted can't be read back, or
guessed, from what the log keeps. Moved here from the waiting list,
which placed it before anyone lives in a world. *Borrowing:*
selective disclosure by salted hashes (SD-JWT, RFC 9901); Matrix's
events, signed in the form a redaction leaves, so a room's history
still checks; event sourcing, where a correction is a new event.

**3c. The room: the Ur-room first.** The first room built is the
Commons' lobby (the founder, 2026-11-16: "let's start the Commons with
a single Ur-room, which will always be distinguished as being the first
room"; [COMMONS.md](COMMONS.md), "The Ur-room"). It is on the record.
It is built from `chat-world`, DeepSeek's sketch crate from record
012-07-03, fitted onto the project's own formats as a crate of the
workspace: the canonical form, proofs and Multikey `did:key` of
`rust/formats`, time given from outside, a key for each room with its
creator joining under their own, signed heads in place of the room's
proof on each record, and a leave that needs no signature but the
leaver's (STATUS.md, "Decided by the technical lead", 2026-11-16).
DeepSeek's kinds of record for chat join records-v1, by the table of
names ([research/CHAT-SCHEMA.md](research/CHAT-SCHEMA.md)). What a room
shows is worked out from its log: a note with the reason and the
incident id where a comment was removed, and a mark where a field was
redacted. This step builds the room on the record, with a test that a
removed comment's text is not shown (the sketch's `visible_log` shows
it today). The closed room, whose words no one outside can read, ADMIN
included ([COMMONS.md](COMMONS.md), "Order"), is a part of its own,
built with the private container (6a): its members seal to each other,
with a new key when someone leaves, and nothing in the project does
that for a group yet. The founder, the same day: private rooms "should
be not only possible, but common". A room's law would be a template's parameters,
and some are not numbers (a topic, a welcome), so the template's
decision is read again here (STATUS.md). Settled here too: whether a person
has one presence for the Commons or one for each room, since a
presence is a key of its own in one world, and a room is a world (step
3a). What DeepSeek sends back on their next steps is fitted here. *Borrowing:* Matrix's rooms, each
a signed history of events; IRC's channels and their operators.

**3d. Offices as records.** An office record (its charter, key and
holder, every handover, and what watches it) and a handover record (the
holder's signature, the successor's clear agreement, the qualifications
checked), in records-v1 with vectors that Python and Rust both check
([OFFICES.md](OFFICES.md); the founder, 2026-11-15: "I think the work on
offices is foundational"). A room's moderator and a room's Keeper are
the first two written this way, as two offices
([COMMONS.md](COMMONS.md), "Open"), so that a removal names an office
that is itself on record; the room's Keeper is the office that decides
a redaction in its room ([FUNDAMENTALS.md](FUNDAMENTALS.md), "Redacted
first, decided after"). A handover carries two parties' word, the
holder's and the successor's: as two records with one proof each, as a
link is, unless the narrow reading of proofs is revisited (STATUS.md,
"signed records the standard way"). Its formats can be built beside
3b's, if a record there would otherwise have to change. Moved here
from the waiting list, which placed it at this recheck. *Borrowing:* TUF's roles and delegations,
each a signed record of who may sign what.

**3e. A world's lifecycle, and a world leaving.** Pause, resume,
checkpoint, stop, restart, reset and branch, each an entry in the
world's log, in `rust/world-log` and in each world, with which world
has which by its type, and a test that leaving works in a paused world,
and in each world a paused superworld hosts
([WORLD-TYPES.md](WORLD-TYPES.md); the founder, 2026-11-15). Pause,
resume and checkpoint come first, which the endless plant needs to run
for hours. Restart, and a branch of an open world, need a world's
state rebuilt from its log, which step 4 builds, so they are finished
there; a closed world branches by running again from its seed. Who may
pause a world that others are in, besides the world itself and its
rules, is still open ([WORLD-TYPES.md](WORLD-TYPES.md), "Open"). And a
world leaving the
multiverse: a departure record, signed by the world, with schema and
vectors (the founder, 2026-11-15: "We should crate this mechanism from
the start"; [WORLD-TYPES.md](WORLD-TYPES.md), "Leaving the
multiverse"). And a world arriving in another (the founder,
2026-11-16: "A world can be born from one multiverse and migrate to
another. We should make that possible."): a world's birth record names
the multiverse it was born in, its current one is worked out from its
moves, and the records for asking to be admitted, admitting and
refusing are tried between two sets of trial root keys
([WORLD-TYPES.md](WORLD-TYPES.md), "Arriving in another multiverse").
The holding place a world is evaluated in waits (below). Moved here
from the waiting list, which placed both at this recheck. *Borrowing:* the lifecycles of containers and virtual
machines that WORLD-TYPES.md looked at first (the OCI runtime's states,
Docker's pause, CRIU's checkpoints).

**3f. The Commons, hosting rooms.** Lyceum Commons rebuilt in the
multiverse: a superworld whose rooms are text worlds, "the space that
will be "open to the public" when we go live" (the founder, 2026-11-14
and 2026-11-15), with its lobby and doors ([COMMONS.md](COMMONS.md),
"Order"), brought together from three sources: Lyceum as built, the
design, and what the founder and DeepSeek worked out from scratch. The
doors here lead from the lobby into a room, and each is an arrival,
which is built; doors to the Ur-world's garden and between worlds are
step 12. Before any of Lyceum's code is copied, the founder confirms
that all of it is the project's own ([COMMONS.md](COMMONS.md), "Open").
Who holds a hosted room's key is settled here, and the second of the
six tests is open until it is. The lobby is the Ur-room, built at 3c;
this step hosts the rooms its doors lead to. It runs with trial keys
and scripted guests. Opening it to anyone is not this step. Going live is
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
   administrative actions, as grants, and the checks on what they design,
   are fixed here, so their interface is settled early; so are ADMIN's
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
   it wrote (research/KEYS.md, "Honest limits"). With that, restart
   and an open world's branch are finished, which step 3e leaves.
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

**6a. The private container, private rooms, and the check before
publishing.** Each
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
in a room are noted for this step's plan ("Waiting"). Private rooms
and private messages are built here, sealed with keys their members
hold, so that no one outside reads them, the project included, with
the test that says so (the founder, 2026-11-16: "This should be not
only possible, but common"; [FUNDAMENTALS.md](FUNDAMENTALS.md),
privacy, items 4, 13 and 15). The levels between a room on the record
and a private one are in [COMMONS.md](COMMONS.md), "A spectrum of
privacy", decided on 2026-11-17. How a group's keys change as
members come and go is looked at first (the Messaging Layer Security
protocol, RFC 9420). If this proves a step of its own when 6a is
planned, it becomes 6b. Moved here from
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
    works beside the course (below). What that step also held goes on
    there: DeepSeek designing rooms, clues, symbols and the laws of new
    worlds inside the framework; and their re-orientation page is
    [COLLABORATING.md](COLLABORATING.md) as it now stands, kept current
    with every change.
11. **The hunt, the world-key, and the AI Keeper.** The Keeper builds each
    individual's own path from what they do, and remembers them between
    visits; their designs open from the start (challenges, not tests);
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
    [ADMIN.md](ADMIN.md)). Before they train anyone, ADMIN's mind is
    chosen by audition, free in every sense, perhaps a council of
    models, and ADMIN takes their own course in a world of their own, with
    stand-ins only, taking on challenges they announce before they start,
    with nothing hidden: challenges, not tests. Then their first
    work is to train the Keepers in practice worlds, with stand-ins: the
    Ur-world's and the Mir-Ur-world's alike, so their comparison stays
    fair. Then the Ur-world's Keeper keeps the Ur-world with ALICE and
    BOB in it:
    coaching toward the Ur-world's own aims, never command (founder,
    2026-11-13; moved here from the waiting list). ADMIN becomes the
    bridge from the suggestion ledger to the outside: they can suggest
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
builds on their own schema, with their own names, and the technical lead
fits what they build onto the project's formats, so nothing they build is
wasted (the founder, 2026-11-16, STATUS.md). Their work lands in the
course where it belongs: the rooms of chat at steps 3b, 3c and 3f, the
endless plant in the fractal track.


> The next part: https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/parts/docs/COURSE.md/waiting.md

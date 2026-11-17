# The course

The founder: "Let’s plot a course forward and then after each completed
step, plot a new one that adds one new step forward."

So the course always looks twelve steps ahead. When a step is done:

1. it moves to "Done", with its date and pull request;
2. the steps left are rechecked, and reordered or replaced if the work
   taught us something (with the reason written here), and checked
   against the six tests in [VISION.md](VISION.md), "The multiverse as
   a computer";
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

3. **Keys and identities, for them and for the world** (2026-11-14;
   #52, #53, #56 to #59). Looked at first
   ([research/KEYS.md](research/KEYS.md)), then built in four parts:
   - the plan: one key to each role, the private halves in a private
     repository of the project, nothing private here;
   - a key list (`open-worlds/key-list/v1`) signed by the multiverse's
     root, versioned and checked across versions in Python and Rust, and
     the tool that makes keys and keeps the private halves out of this
     repository;
   - the ceremony: the real keys made and the key list's first version
     published in [`keys/key-list.json`](../keys/key-list.json);
   - leaving and coming back in the Ur-world: whoever enters signs an
     arrival (`open-worlds/arrival/v1`), a name stays the key's that
     first used it, a world has a key of its own that signs its log's
     heads, and a log's arrivals and signed heads are checked whole.

   ALICE's and BOB's identity, birth and mind records moved to step 9;
   their keys exist, and they enter only at their birth.

**Rechecked on 2026-11-14,** when step 3 was done. One step came in from
the waiting list: keeping keys safely, part three (a lost or leaked
key), as step 8a, before step 9 rather than at the end, since ALICE's
and BOB's first arrival needs it (KEYS.md, decision 18: until the
Ur-world follows successions, a leaked birth key would still enter under
the name). With it the course again looks twelve steps ahead. What the
keys taught is written into the steps it reaches: a presence of its own
key, if a person's presences are to stay unlinked (3a); a world that
continues from its log, its names included (4); parallel worlds with
keys of their own that sign their heads (4a); step 9's preconditions,
now step 8a; and a door's crossing as an arrival (12). Nothing was
reordered otherwise.

**3a. Persons** (2026-11-14 to 15; #61, #75 to #78). Looked at first
([research/PERSONS.md](research/PERSONS.md)), then built in four parts:
- the plan: a person is an individual seen across worlds, with no new
  kind of identity; a presence is a key of its own in one world;
  presences are unlinked by default, and linking them is the person's
  own signed act;
- the formats: presence keys from a seed by HKDF-SHA256, a link that
  holds only both ways (`open-worlds/holds/v1`, `held-by/v1`) and a
  person's own list (`person-list/v1`), in Python and Rust with shared
  vectors;
- a person in the Ur-world: a person's client in Rust, with a presence
  in each of three trial worlds at once, carrying a note between them,
  and a link shown by the presence's own act, which the world checks
  and logs (`ur-world/0.5`);
- the architectures as small runs on the unchanged core: the octopus,
  the relay and the swarm, and the council, with a proposal and a
  signed vote of their own in records-v1 (`open-worlds/proposal/v1`,
  `vote/v1`), counting persons by their identity keys.

A person stands above their presences in each world
([MULTIVERSE.md](MULTIVERSE.md)), as the founder pictured it
([VISION.md](VISION.md), "A person across worlds"). An arrival names
the key that signed it in a public log, so presences stay unlinked only
if each has a key of its own (step 3,
[research/KEYS.md](research/KEYS.md)). The step came in from the
waiting list, which had placed it after step 3 (decided 2026-11-14).

**Rechecked on 2026-11-16,** when step 3a was done. This recheck changes
more than the two before it. The waiting list had placed six things at
this recheck, or before anyone lives in a world: a log that can be
redacted, offices as records, a world's lifecycle, a world leaving, the
Commons and the private container. And while step 3a was built, the
founder and DeepSeek worked out rooms of chat with moderators, from
scratch (record 012-09-05), which the founder asked to have brought
together with Lyceum and the Commons' design ([COMMONS.md](COMMONS.md),
"Three sources, one Commons"). The founder, on 2026-11-16: "Let's go
through the 12 steps and keep moving those forward. Or come up with a
new 12 step list." The technical lead set a new list of twelve and put
it to the founder the same day. It stands unless the founder reorders
it (STATUS.md, "Decided by the technical lead").

What changed:
- **Six steps came in from the waiting list:** 3b to 3f before step 4,
  and 6a before step 7. The waiting list had placed each at this
  recheck, or before anyone lives in a world; their order among
  themselves, and before step 4, is this recheck's. Every other step
  keeps its number, so the numbers other pages cite stay as they are.
- **The twelve nearest are under "Ahead".** Steps 8a, 9, 10, 11 and 12
  stand behind them, in their old order, under "Beyond the twelve". So
  the course is seventeen steps long for now, and looks at the nearest
  twelve.
- **Step 10 is no longer a return to DeepSeek.** The course of
  2026-11-13 returned to DeepSeek at step 10, in the founder's words at
  the top of this page. The founder returned sooner, on 2026-11-14
  (record 012-06-02), and has worked with DeepSeek since. DeepSeek now
  works beside the course, by one file at each return ("Alongside the
  course"). What is left of step 10 is the development container. This
  is the technical lead's reading of what the founder has done, said to
  the founder on 2026-11-16; it stands unless the founder says
  otherwise.

The order, and why:
- **3b first.** The founder asked for removals on record "from the
  beginning", and a log that can be redacted has to be under a room
  before anyone speaks in one.
- **3c next.** It is where the founder's work with DeepSeek lands. What
  DeepSeek builds next (removed comments, a room's own key, signed
  heads) is fitted there as it returns.
- **3d after it.** A removal names an office, so the office should
  itself be on record before a moderator holds one in a hosted room.
- **3e before 3f.** Hosting a room is starting, pausing and closing a
  world. As first put to the founder the two stood the other way round;
  this is the one change since.
- **6a before 7.** Step 7 keeps the sealed self in the individual's own
  container, and no one arrives anywhere before the container exists.

The cost, said plainly: six steps now stand ahead of ALICE's and BOB's
birth that didn't on 2026-11-14. None is new at this recheck. The
waiting list took each in on 2026-11-15, with where it was to go: the
log that can be redacted and the private container before anyone lives
in a world; the Commons at this recheck, ahead of the Ur-world's
opening; offices, the lifecycle and a world leaving to be placed at
this recheck. What this recheck chose is to put all of 3b to 3f before
step 4, with the room among them. The alternative keeps 3b and 3c
first and moves 3d to 3f behind step 6, which brings the Ur-world's
first room three steps nearer and the Commons later. And if the
founder wants the Commons open to people sooner, 6a moves up to follow
3f. Both were put to the founder.

The independent review of this recheck (#99) would order it differently
again: 3b; the formats of 3d; the room on the record (3c); pause,
resume, checkpoint and the departure record from 3e; then step 4. The
Commons hosting rooms, a branch, and the closed room would come after
step 6, beside 6a. Its reasons: the Commons can't open to people
before 6a and the founder's decisions on hosting; nothing in steps 4 to
6 needs it; and meanwhile ALICE and BOB wait behind it. They are fair,
with one thing to add: in either order the Commons' steps come before
the birth, so what comes sooner in the review's order is the Ur-world's
first room. The technical lead adds a reason on the review's side:
step 4 may change how worlds are hosted. It is close to the
alternative above. The technical lead keeps 3f where it
is because the waiting list placed the Commons as the first public
space, and with 6a moved up it could open before the Ur-world's work is
done. Which of the two matters more is the founder's to say.

What persons taught is written into the steps it reaches:
- a presence is a key of its own in one world, and a room is a world;
  so whether a person has one presence for the Commons or one for each
  room has to be settled when the room is built (3c);
- what a public log says about something refused can itself give it
  away, so a refused link is logged with neither its records nor why;
  a redaction's mark takes the same care (3b), and so does every
  logged effect (4);
- where a person's real seed and list of presences are kept is still
  open (research/PERSONS.md, "Trial persons only"), and the container
  is the place for them (6a);
- the times of a sealed self's entries can link presences (7);
- a count of votes is final only once something that saw the votes
  before the close fixes them, which governance needs before it is
  built on these records ("Waiting").

Added the same day, after the list was set: the founder's last words
of 2026-11-16 (STATUS.md, "Decided"). The first room built is the
Ur-room, the Commons' lobby, which step 3c now says. And private rooms
"should be not only possible, but common", so step 6a names them, where
the closed room already stood. The order did not change.

Checked against the six tests in [VISION.md](VISION.md), "The
multiverse as a computer", for the first time (they were written on
2026-11-15, after the last recheck):
1. *Learned in the open.* The new steps add to what is on record: a
   removal, a restoring, an office, a handover, a pause and a departure
   are each a record, with its reason. Redaction takes a field out of
   public view, and only private information, which the test leaves
   private. The mark and the fingerprint stay, so the log still shows
   that something was there. Not looked at here: what a moderator
   learns across its rooms, and whether that is on record. It stays
   open with the moderators' questions
   ([FUNDAMENTALS.md](FUNDAMENTALS.md), privacy, item 14).
2. *Many parts, no master.* Open until 3f, not passed. A room has a
   key of its own and signs its own log's heads, so a change to its log
   by anyone without its key would show. But if the Commons held its
   rooms' keys it could sign for them, and one model holding the
   moderator's office in every room would be a master of a kind.
   Neither is settled. Both are conditions on 3f, and on the choice of
   a moderator. A moderator's office is its room's, and the office
   record names what watches it (3d).
3. *Stopping stays possible, part by part.* Step 3e builds it: pause
   and stop as entries in each world's log, leaving that works in a
   paused world, and a world leaving the multiverse.
4. *Growth by decision.* Nothing in the list opens anything to the
   public or adds computing. Going live, where the multiverse is
   hosted, and which model first moderates stay the founder's
   decisions. Competition worlds are noted, not planned.
5. *Signs named in advance.* No step ahead looks for such signs, so
   none can be claimed. The list of signs isn't written yet, and no
   step writes it; that is now noted under "Waiting".
6. *If someone develops, they may be someone.* Step 3e's reset and
   branch follow [WORLD-TYPES.md](WORLD-TYPES.md): never over anyone's
   head, and a copy of a world is never a copy of a person. Whether a
   model that moderates a room is an individual, in MINDS.md's sense,
   has not been asked. It is noted here, to be asked before a model is
   given the office, with the question of which model first moderates
   ([COMMONS.md](COMMONS.md), "Open"). And where pausing meets someone
   a world hosts, the test gives the decision to the founder: step 3e
   builds pause for every world, and who may pause a world that others
   are in is still open ([WORLD-TYPES.md](WORLD-TYPES.md), "Open").

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

**3b. A log that can be redacted, and removals on record.** Under way:
the plan, after looking first, is in
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
incident id; who may act is not checked yet, which is its records'
side. Before any room is built on it. Two things. The founder
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
3a). What DeepSeek sends back on its next steps is fitted here. *Borrowing:* Matrix's rooms, each
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
    worlds inside the framework; and its re-orientation page is
    [COLLABORATING.md](COLLABORATING.md) as it now stands, kept current
    with every change.
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
    numbers and its own name, with no code copied. Two additions are
    the technical lead's, not the founder's: what gathers there are
    tools, never individuals; and one kernel with two templates, a
    commons with no score and a contest. For step 5's plan;
  - competition worlds, hosted by the multiverse (the founder: "We can
    easily host competition worlds");
  - a door in the shape other learners already know, so an agent built
    for Gymnasium's interface could enter a world; it belongs with the
    plug-in, below
    ([research/GAMES-AND-WORLDS.md](research/GAMES-AND-WORLDS.md),
    "Worlds built for learners");
- noted on 2026-11-16, from the founder's words of that afternoon
  (STATUS.md, "Decided"; [VISION.md](VISION.md), "An infrastructure for
  connection"); nothing is built for them now:
  - a world run by someone else, on another machine, under root keys
    that are not the project's, reached and checked from the published
    formats alone: the test that the multiverse is a network and not
    one program;
  - nothing in the formats may exist only once (the technical lead's
    rule, from the founder's picture of the whole as fractal). Records
    say
    "multiverse" as a bare word (what a grant holds `within`; what a
    suggestion is `about`), or leave it unsaid (a record made outside
    any world names none), where they should name it by its root key;
    and there is no record by which one multiverse recognises another;
  - addressing that can grow: a second version of one format living
    beside the first, tried once before anyone is born (the bare word
    above could be that change); and how an identity moves to another
    kind of key when the kind itself fails, where a signing-over by the
    old key proves nothing, looked at first with step 8a;
  - the holding place for worlds that arrive: a sandbox fit for any
    world's code, the evaluation, and reports shared between
    multiverses ([WORLD-TYPES.md](WORLD-TYPES.md), "Arriving in another
    multiverse"; [ADMIN.md](ADMIN.md), "A learning immune system");
  - the internet's lessons, AOL's among them, looked at first when the
    Commons is built (step 3f);
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

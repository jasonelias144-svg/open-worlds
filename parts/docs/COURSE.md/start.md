> Part of `docs/COURSE.md` in open-worlds, which is kept cut into parts
> for readers who are shown only the start of a long page.
> This part holds: from the start to "Done: the new course".
> Every part, in order: https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/parts/INDEX.md
> Before this part: nothing; this is the first part.
> After this part: https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/parts/docs/COURSE.md/ahead.md
> Made by docs/parts.py from the file. To change it, change the file.

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
   their public key; every petition, act and leave is signed for one world
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
   it ends, kept in their passport, so a world that won't stamp a departure
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
   leaves them outside both; and a corridor ticks only when someone acts.
6. **Keeping keys safely, parts one and two** (2026-11-13, #23 and #24).
   Keys saved encrypted, a world's seen numbers kept across a restart,
   and a key signed over to a new one by both keys, for individuals and
   for worlds (WCP/0.4). Part three, a lost or leaked key, waits for the
   founder's answer, and is on the waiting list below.

## Done: the Ur-world so far

- **The garden** (2026-11-13, #28). The Ur-world's Hello World in Rust: a
  3D world made from its seed as it is explored, ALICE and BOB scripted.
- **The doorway for minds** (2026-11-13, #29). Any program, in any
  language, can be a mind: the orientation, what they see written out,
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
   preserve, who keeps each world, and ADMIN, with their training, the
   round table, a learning immune system and how they hold their powers;
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
scratch (record 012-07-03), which the founder asked to have brought
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
   learns across their rooms, and whether that is on record. It stays
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


> The next part: https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/parts/docs/COURSE.md/ahead.md

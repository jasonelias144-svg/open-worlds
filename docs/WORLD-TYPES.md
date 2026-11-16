# World types, and what can be done with a world

The founder, 2026-11-15, accepting that the multiverse, once others run
worlds, can only be stopped part by part: "I accept it. Every world can
pause itself and every person can leave. If they return, they can pick
up where they left off on challenges, or anything else. Also, we can
treat worlds like virtual machines without much stretch of the
imagination, or like containers. In either case, we can pause a state
and later resume. We can stop. We can restart or reset. We should have
that functionality for worlds of a certain type. We need a full taxonomy
of world types."

**Decided, by the founder:**
- **No master switch.** Once others run worlds, the multiverse stops
  only part by part ([VISION.md](VISION.md), "The multiverse as a
  computer", test 3).
- **Every world can pause itself, and every person can leave.**
- **Returning picks up where you left off,** on challenges or anything
  else.
- **Worlds have a lifecycle,** as virtual machines and containers do:
  pause and resume, stop, restart, reset, "for worlds of a certain
  type". So a world's type says which of them it has.
- **A full taxonomy of world types** is needed.

The rest of this page is the technical lead's reading, put to the
founder the same day, which stands unless the founder answers
otherwise. It is a design: none of the lifecycle below is built yet,
except where it says so.

## Looked at first

- **Containers.** The Open Container Initiative's runtime specification
  gives a container four states, `creating`, `created`, `running` and
  `stopped`, and five operations: create, start, kill, delete, and query
  the state. It has no pause. Docker adds one: `docker container pause`
  "suspends all processes in the specified containers", on Linux
  through the freezer cgroup, so that "the process is unaware, and
  unable to capture, that it is being suspended, and subsequently
  resumed". Docker's checkpoints, still an experimental feature, built
  on CRIU (Checkpoint/Restore In Userspace), save a running container's
  state to restore later.
- **Virtual machines** add the rest of the familiar set: suspend and
  resume, save the whole state to disk and restore it, snapshots to
  return to, and a hard reset.

Four things are different here, and they shape the design:
1. **A world's state follows from its record.** A world is its template,
   its seed, and a log of every step, with every input from outside
   written into it ([URWORLD.md](URWORLD.md)). So a checkpoint is cheap:
   the hash of the log's head, which the world signs, and restarting is
   running on from the last one. Rebuilding a world's state from its log
   is what that needs, and it isn't built yet: today a closed world is
   run again from its seed, and a log is checked against its world's
   rules (below, "What is built").
2. **Nothing is hidden, a pause included.** Docker's pause is built so
   the process can't tell. Here a pause, a stop and a restart are each
   an entry in the world's log, and those inside are told, as the
   charter tells every participant the whole setup.
3. **A record never ends.** "The project may end a world, or the
   multiverse, but a world's record never ends; sealed selves stay
   sealed; and keys stay their holders', so an individual can go on
   elsewhere" ([ADMIN.md](ADMIN.md)). So no operation here deletes a
   log, and a reset never overwrites one. Nor is any entry ever edited:
   "We do not edit historical records as an absolute rule" (the
   founder, 2026-11-15), so what someone did in public stays after they
   leave too. The one exception is personal or private information,
   which is redacted, visibly, while the log still checks
   ([FUNDAMENTALS.md](FUNDAMENTALS.md), "Public records, kept whole").
4. **Leaving always works.** No operation here holds anyone in. A
   paused world still takes each leaving, and logs it; a world that
   stops lets everyone out first; and a superworld's pause pauses its
   worlds' steps, never anyone's way out. Exit is a protected freedom:
   "Every world can pause itself and every person can leave" (the
   founder), and a world never refuses a leaving
   ([COLLABORATING.md](COLLABORATING.md), house rule 4;
   [FUNDAMENTALS.md](FUNDAMENTALS.md), freedom, item 2).

## The lifecycle

A world is **born** (its birth record), **runs**, may be **paused** and
**resumed** any number of times, and is in the end **stopped**. Seven
operations:

| Operation | What it does | What the log keeps |
|---|---|---|
| **Pause** | The world stops taking steps. Its state stays as it is, and leaving still works: a paused world takes each leaving. Any world can pause itself (the founder). | An entry: paused, when, and by whom or by what rule; and each leaving during the pause |
| **Resume** | The world takes steps again, from exactly where it paused. | An entry: resumed. Those inside are told how long it was paused |
| **Checkpoint** | Names the state at a step: the hash of the log's head, signed by the world. | The signed head, as worlds already sign them |
| **Stop** | The world ends its run. Those inside are told first, and can leave first. | A last entry and a last signed head. The log is closed, never removed |
| **Restart** | The same world runs on from its last signed head: same key, same log, continued. Running on from an earlier point is a branch, or a reset, never a restart, so no step anyone holds a stamp for is undone. | An entry: restarted, at the last signed head |
| **Reset** | A fresh run from the same template and seed: "a fresh start or new run with the same world setup" (the founder, 2026-11-14, on parallel worlds). It is a new world, whose birth record names the template and the run before it. | A new log. The old one is kept, closed, beside it |
| **Branch** | A copy of the world at a checkpoint that then runs on its own: the founder's "steering by branching" ([VISION.md](VISION.md), "Ride along, and steer"). | A new log, whose birth names the world and checkpoint it branched from |

**Returning picks up where you left off.** What a person did belongs to
them, not only to the world. Their passport carries the world's signed
stamps, their notebook and sealed self go with them, and a world's
Keeper remembers each individual's past visits
([WORLD-KEY.md](WORLD-KEY.md)). So a person who leaves a world and comes
back finds their place: in a world that was only paused, exactly as it
was; in one that was reset, with their own record of the challenge
intact, so the Keeper can let them resume it. To make that so, progress
on a challenge is kept as a record the world signs and the person holds,
not only in the world's state.

## Time: faster, slower, back and forward

The founder, 2026-11-15: "And some way to speed up or slow down the flow of time. A slow motion and a fast speed view. Rewind and fast forward in time to previous states. This would be a goal eventually."

**Decided, by the founder:** a goal, for later: speeding time up and
slowing it down, slow motion and a fast view, and rewinding and fast
forwarding to earlier states.

The technical lead's reading, which stands unless the founder answers
otherwise. Time control means two different things, and the difference
matters:

1. **Watching** a world's past, faster, slower, back and forward,
   changes nothing in the world. A world whose state can be rebuilt
   from its log can show any earlier step again, and checkpoints make
   jumping far back quick. Built, for the plant world: Plant Watch
   replays a plant from its log, with a slider to any step, back or forward, and Play
   and Pause; growth within a step is drawn smoothly
   ([FRACTALS.md](FRACTALS.md)). A speed control is next, as the endless
   plant's page plans.
2. **The world's own pace,** how many steps it takes in a second, is a
   setting in its law. As decided before ([MULTIVERSE.md](MULTIVERSE.md),
   "Time"): "Each world publishes its time rate in its law; nobody
   enters a fast world without choosing to, and leaving still works at
   any moment." A world with no one inside can run as fast as a machine
   allows, which is the founder's accelerated time. A world with minds
   in it runs no faster than they think.

**Rewinding the world itself,** not only the view, is going back to an
earlier checkpoint and running on from there. Here that is a branch
(above): the steps after that point are kept, never erased, and in a
world with individuals it happens only as a new world they may choose to
enter. Fast forwarding a world itself is running ahead quickly, which a
closed world can do (anyone can compute its future from its seed), and
an open one can't, as minds can't be run ahead of their own thinking.

## Leaving the multiverse

The founder, 2026-11-15: "Yes, multiverse can only be stopped, part by part. And perhaps this could help, we could define branching protocols for a cluster of worlds or a single world that want to form their own, independent multiverse, severing connections with our host multiverse. So any worlds that want to exist in another multiverse can branch into their own, then the cord is cut, and it can exist completely independently. We should crate this mechanism from the start. Participants can leave worlds, and worlds can leave the multiverse."

**Decided, by the founder:** a single world, or a cluster of worlds, can
leave this multiverse to form an independent one of its own: it
branches, "then the cord is cut, and it can exist completely
independently". The mechanism is made from the start. "Participants can
leave worlds, and worlds can leave the multiverse."

The technical lead's reading, which stands unless the founder answers
otherwise.

**What already makes it possible.** A world needs nothing from this
multiverse to go on:
- **its own key and its own log:** every world signs its own heads;
- **open code:** everything here is public domain, so anyone can run
  it;
- **checkable by anyone:** a world's log is checked offline, with no
  host involved;
- **a key can be signed over:** the old key hands over and the new one
  accepts, both signing (`multiverse/succession.py`, course step 6 of
  the first course).

**What leaving takes:**
1. **The world's own decision, by its own law.** A world with no one
   inside leaves at its runner's word. A world with inhabitants leaves
   only as its law changes: with the consent of every party
   ([FUNDAMENTALS.md](FUNDAMENTALS.md), freedom, item 4). So one "no"
   stops it. Leaving first, to stay in this multiverse, is only ever the
   dissenter's own choice, never a condition put on them, and whoever
   leaves keeps everything that is theirs. Before anyone consents, they
   are told that going with the world takes them out of the charter's
   protections (exit, privacy, data never for sale), into whatever the
   new multiverse's law gives. A cluster leaves as each of its worlds
   decides by its own law; a world that stays is hosted here again.
2. **A departure record,** signed by the world: where it goes, and the
   head of its log at the moment it leaves. The host publishes it, and
   closes its own copy of the world's log at that head. That copy is
   kept, whole, as a record never ends: public acts always remain, with
   anything private in them redacted.
3. **The keys move.** The world's key is signed over to a new key that
   whoever runs it now made, so the host keeps no key of the world.
4. **Their records go with them.** Whoever leaves with the world, or
   leaves the multiverse at all, is given their private records, and the
   project's copies of their private keys and private data are purged,
   "completely and demonstrably" (the founder, 2026-11-15;
   [FUNDAMENTALS.md](FUNDAMENTALS.md), "Purged, demonstrably").
5. **The cord is cut.** After the departure record, the host neither
   hosts, relays nor speaks for the world. What was signed before stays
   valid, since a signature needs no host: stamps, passports, and
   persons' links. A person with presences on both sides keeps both.
6. **No host can refuse it.** As no world refuses a leaving
   ([COLLABORATING.md](COLLABORATING.md), house rule 4), no multiverse
   refuses a world that leaves by its own law. Coming back, or
   federating again, is a new decision by both sides.

**From the start.** The first piece is the departure record: a record
kind in `schemas/records-v1.schema.json`, with test vectors that Python
and Rust both check, as every record kind has. The course takes it up
at step 3e, with the lifecycle ([COURSE.md](COURSE.md); placed at the
recheck of 2026-11-16).

## Arriving in another multiverse

The founder, 2026-11-16: "A world can be born from one multiverse and
migrate to another. We should make that possible. So the worlds would be
birth-indexed by their parent multiverse, but could have a separate
index for current multiverse." Of the two indexes: "In most cases, those
match. Except in cases of world migration." And, on security: "we need
some sandboxed holding place for worlds entering a new multiverse. I can
easily imagine hackers exploiting this world migrating function to
import payloads. A new world needs to be evaluated, before entry to a
new multiverse. If malicious code is found, the entrance is blocked, and
it never exits the sandbox. An incident is and report follow, and all
that."

**Decided, by the founder:** a world can leave the multiverse it was
born in and arrive in another. It is indexed by the multiverse of its
birth and, separately, by the one it is in now. Before it is admitted
it is evaluated in a sandboxed holding place; if malicious code is
found it is refused and never leaves that place; and a refusal is an
incident, with a report. The four refinements below marked "taken" were
the technical lead's, and the founder took them: "Yes, I like your
suggestions. All of them."

The rest is the technical lead's reading, which stands unless the
founder answers otherwise. Everything in "Leaving the multiverse",
above, still holds: this section adds the other half.

**The two indexes.**
- **Birth.** A world's birth record names the multiverse it was born
  in, by that multiverse's root key (the issuer of its key list), and
  never changes. Today's birth record names none, so it gains this
  before any real world is born; so far only trial worlds have been.
- **Current.** Worked out, never stored: the birth multiverse, unless
  the world's chain of moves says otherwise. A world that never moved
  carries nothing extra. A map shows both only where they differ:
  "born in X, now in Y".
- **One at a time,** as the founder put it. A world that left to stand
  alone, as "Leaving the multiverse" has it, was admitted by no one:
  it is the first world of a multiverse of its own.

**A move, in order.**
1. **The world decides, by its own law,** exactly as for leaving: a
   world with inhabitants moves only with the consent of every party,
   so one "no" stops it, and each is told beforehand what the new
   multiverse's law gives and takes away ("Leaving the multiverse",
   item 1).
2. **It asks first** (taken). A request for admission, signed by the
   world, names the multiverse it asks, its code by its hash, and its
   log's head. It has not left: it goes on living where it is.
3. **A copy is evaluated in the holding place** (taken). The copy is a
   checkpoint, paused, with stand-ins and never individuals, so no one
   is held while it is looked at, and a world that is refused is not
   left without a home.
4. **Admitted, or refused.** An admission is signed by the receiving
   multiverse and names exactly what was evaluated: the code's hash and
   the log's head (taken). A refusal is a decision on record: the
   office, its grounds, an incident id, and where an appeal goes, the
   same records a removal uses ([research/REDACTION.md](research/REDACTION.md),
   decision 7). The appeal matters, since a report could be used to
   smear a world.
5. **Only then does it depart:** the departure record of "Leaving the
   multiverse", naming where it goes. The move counts when both the
   departure and the admission exist, so a world can't claim a home
   that never took it in, and no multiverse can claim a world that
   never left.
6. **On arrival,** whatever the world added to its log after the head
   that was evaluated is checked again.

**What a holding place can and can't do.**
- **It can't prove code safe** (taken). What is malicious can wait
  until it is admitted. So the wall is permanent: no world's code ever
  runs outside a sandbox, native or immigrant, for its whole life.
  Admission changes what a world is connected to, never where it runs.
  The holding place catches what is known and what is plain.
- **A payload aimed at a mind is made of words** (taken). An incoming
  world's names, law and log could carry instructions aimed at whoever
  evaluates it. Everything in it is data to the evaluator, never
  instructions, and the evaluator has no power but to write its report.
- **It has a model already:** ADMIN's own world, a sandbox with no door
  and stand-ins only ([ADMIN.md](ADMIN.md), "ADMIN's own world"), and
  the library of remedies of the learning immune system, where what a
  holding place finds is kept. Reports shared between multiverses would
  be that immune system across the network.

**What does not travel.** A grant's signature stays valid, as every
signature does, but a grant holds within the multiverse that gave it:
the receiving multiverse is not bound by it. Each council decides again
whether to trust the births the world signs.

**Limits, to be stated where it is built.**
- That a world has not moved is only as fresh as the signed head a
  reader holds: a departure is an entry in the world's own log, and an
  old copy still shows the world at its birthplace. The multiverse it
  left also records that it saw the departure.
- The two indexes matching does not mean a world never left. It may
  have come back, and its chain of moves shows the trip.

**From the start, and what waits.** The records (the birth index, the
request, the admission and the refusal) belong with the departure
record at course step 3e, and can be tried there with no network: a
second multiverse is a second set of trial root keys. The holding place
itself, a sandbox fit for any world's code, is real engineering and is
on the course's waiting list ([COURSE.md](COURSE.md)); today only the
plant world runs in a sandbox (`rust/plant-wasi`).

## A taxonomy of world types

Every world has a place on each of eight dimensions, and its type is
where it stands on all of them. They are drawn from the worlds already
built or designed.

1. **Level** ([VISION.md](VISION.md), "A hierarchy of worlds").
   - **Primary:** rules, and no AI inside. Built: the plant worlds,
     the chemistry soup, the corridor.
   - **Superworld:** hosts worlds, and is tended by a Keeper from
     outside. Built: the Ur-world's garden, which hosts three plant
     worlds. Designed: a superworld for chemistry worlds, and the
     Commons, a superworld of rooms ([COMMONS.md](COMMONS.md)).
   - **The multiverse,** tended by ADMIN.
2. **Who is inside.**
   - **No one:** a process to watch, such as a plant growing.
   - **Scripted agents,** such as the corridor's walkers.
   - **Minds from outside,** through the doorway, which come and go.
   - **Individuals with lives,** such as ALICE and BOB: a birth record,
     a sealed self, a passport.
   - **Visitors who only watch,** as in a control world.
3. **Purpose.**
   - **Question worlds:** the prediction written first.
   - **Challenge worlds:** the path to a world-key, where challenges
     build the world.
   - **Living worlds:** water, light and food.
   - **Commerce and currency worlds,** where money is a test setting.
   - **Creative worlds,** such as the poetry world.
   - **Text worlds:** a room of the Commons, where people and AIs talk
     ([COMMONS.md](COMMONS.md)).
   - **Game worlds,** the founder's turn in record 012-05-01: a chess
     park, worlds inside worlds ([COLLABORATING.md](COLLABORATING.md),
     "Where the conversation stands").
   - **Home:** the Ur-world, where ALICE and BOB will be born.
   - **Test bench:** the Mir-Ur-world, the Ur-world's mirror.
   - **Training:** ADMIN's own world.
   - **Parallel worlds:** runs of one template, side by side.
   - **Control worlds,** which only show.
4. **Determinism.**
   - **Closed:** everything follows from the template and the seed, so
     anyone can run it again, step for step. Built: the plant worlds.
   - **Open:** minds from outside act in it, and what they did is in
     its log. So it can be replayed from the log, but not run again from
     the seed: a mind needn't act the same way twice.
5. **Time.**
   - **A fixed run:** a number of steps, then stop. Built: the plant
     world.
   - **Endless:** runs until it stops itself, or is stopped. Next:
     the endless plant.
   - **Continuous:** always running, as a live world will be.
   - **Accelerated:** faster than its inhabitants' outside clock, the
     founder's "accelerated learning worlds, or even certain accelerated
     learning times" ([MULTIVERSE.md](MULTIVERSE.md), "Time"). Nobody
     enters one without choosing to, and leaving still works at any
     moment.
6. **Who runs it.**
   - **The project,** today, every world.
   - **Others,** later ([TOPICS.md](TOPICS.md), "Further out").
7. **How it may change** ([VISION.md](VISION.md), "Worlds that change
   differently").
   - **Fixed:** its law never changes, as a plant world "takes no
     change from outside".
   - **By consent:** its law changes only with the consent of every
     party (CHARTER.md, section 6).
   - **Some other way,** as each world's law says.
8. **Space.**
   - **Bounded:** a fixed grid, as the corridor and the chemistry soup.
   - **Growing:** it grows as it is explored or grows itself, the
     founder's "fractals grown over time in expanding worlds"
     ([FRACTALS.md](FRACTALS.md)) and challenges that build the world
     ([WORLD-KEY.md](WORLD-KEY.md)). Next: the endless plant.

**Not a world type: the private interior.** The founder called each
individual's private space "a private interior world that is not
accessible to the world Keeper" ([MINDS.md](MINDS.md)). Here it is part
of the individual, their sealed self, not a world beside the others: it
takes no steps of a world's, and no one but its holder pauses, branches,
resets or reads it. None of the operations below apply to it.

## Which world has which operations

The rule of thumb: **the more of someone's life a world holds, the
fewer operations are anyone's to choose.**

| World | Pause, resume, checkpoint | Stop | Restart | Reset | Branch |
|---|---|---|---|---|---|
| **Primary, closed, no one inside** (a plant world; a question world) | yes | yes | yes | yes: a new run | yes |
| **With scripted agents only** | yes | yes | yes | yes: a new run | yes |
| **With minds from outside** | yes, logged, and they are told; they can leave while it is paused | after they are told, and can leave | yes | as a new run they may join | a copy of the world, not of the minds |
| **With individuals with lives** | yes, logged, and they are told; they can leave while it is paused | after they are told, and can leave; their keys, records and sealed selves stay theirs | yes | never over anyone's head: only as a new world they may choose to enter | a copy of the world, never of a person, who chooses whether to enter it |
| **Superworld** | yes; pausing it pauses the worlds it hosts, and each of them can also pause itself; anyone in any of them can still leave | after each hosted world is stopped | yes | its hosted worlds by their own rules | yes |
| **Control world** | yes, logged, so a disturbed run is never taken for an undisturbed one | yes | yes | yes: a new run | yes |
| **The multiverse** | no master switch: part by part, by each who runs a part | part by part | part by part | never | never |

## What is built, and what is next

- **Built:** closed worlds run again from their seed, step for step
  (the plant world's `the_same_dials_give_the_same_log`, and the
  chemistry soup's replay from its seed), and a log is checked against
  its world's rules (`rust/ur-world/examples/log.rs`, the plant world's
  rule check). The plant worlds and the Ur-world sign their log heads,
  which is what a checkpoint needs. The garden gives each glasshouse its step, which
  is what pausing a superworld needs. Not built: rebuilding a world's
  state from its log, which a restart needs, above all for an open
  world.
- **Next:** the operations themselves, as entries in a world's log, in
  `rust/world-log` and each world, with a test that leaving works in a
  paused world, and in each world a paused superworld hosts. The
  course takes them up at step 3e ([COURSE.md](COURSE.md); placed at
  the recheck of 2026-11-16), and finishes restart at step 4, which
  rebuilds a world's state from its log. The endless plant needs
  pause, resume and checkpoint first, to run for hours in the browser
  ([FRACTALS.md](FRACTALS.md)).

## Open

- Whether "branch" may ever copy a person. This page says never: a
  person is one, and enters a copy only by choice.
- How long a paused world waits before it counts as stopped, if ever.
- Who may pause a world that others are in, besides the world itself
  and its rules: its Keeper, and when.

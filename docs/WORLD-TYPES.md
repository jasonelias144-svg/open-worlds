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
  resumed". Docker's checkpoints, built on CRIU (Checkpoint/Restore In
  Userspace), save a running container's state to restore later.
- **Virtual machines** add the rest of the familiar set: suspend and
  resume, save the whole state to disk and restore it, snapshots to
  return to, and a hard reset.

Three things are different here, and they shape the design:
1. **A world's state follows from its record.** A world is its template,
   its seed, and a log of every step, with every input from outside
   written into it ([URWORLD.md](URWORLD.md)). So a checkpoint is cheap:
   the hash of the log's head, which the world signs. Restarting is
   running on from it, and anyone can rebuild the state by replaying
   the log.
2. **Nothing is hidden, a pause included.** Docker's pause is built so
   the process can't tell. Here a pause, a stop and a restart are each
   an entry in the world's log, and those inside are told, as the
   charter tells every participant the whole setup.
3. **A record never ends.** "The project may end a world, or the
   multiverse, but a world's record never ends; sealed selves stay
   sealed; and keys stay their holders', so an individual can go on
   elsewhere" ([ADMIN.md](ADMIN.md)). So no operation here deletes a
   log, and a reset never overwrites one.

## The lifecycle

A world is **born** (its birth record), **runs**, may be **paused** and
**resumed** any number of times, and is in the end **stopped**. Seven
operations:

| Operation | What it does | What the log keeps |
|---|---|---|
| **Pause** | The world stops taking steps. Its state stays as it is. Any world can pause itself (the founder). | An entry: paused, when, and by whom or by what rule |
| **Resume** | The world takes steps again, from exactly where it paused. | An entry: resumed. Those inside are told how long it was paused |
| **Checkpoint** | Names the state at a step: the hash of the log's head, signed by the world. | The signed head, as worlds already sign them |
| **Stop** | The world ends its run. Those inside are told first, and can leave first. | A last entry and a last signed head. The log is closed, never removed |
| **Restart** | The same world runs on from its last checkpoint: same key, same log, continued. | An entry: restarted, from which checkpoint |
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
   changes nothing in the world. Since a world's state follows from its
   log, any earlier step can be shown again, and checkpoints make
   jumping far back quick. Built, in part: Plant Watch replays a plant
   from its log, with a slider to any step, back or forward, and Play
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
   only as its law changes: with the consent of every party (the
   charter, section 6). Anyone who doesn't want to go leaves first,
   and keeps everything that is theirs. A cluster leaves as each of its
   worlds decides by its own law; a world that stays is hosted here
   again.
2. **A departure record,** signed by the world: where it goes, and the
   head of its log at the moment it leaves. The host publishes it, and
   closes its own copy of the world's log at that head. That copy is
   kept: a record never ends.
3. **The keys move.** The world's key is signed over to a new key that
   whoever runs it now made, so the host keeps no key of the world.
4. **Their records go with them.** Whoever leaves with the world, or
   leaves the multiverse at all, is given their records, and the
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
and Rust both check, as every record kind has. The course takes it up at
its next recheck ([COURSE.md](COURSE.md), "Waiting"), with the
lifecycle.

## A taxonomy of world types

Every world has a place on each of seven dimensions, and its type is
where it stands on all of them. They are drawn from the worlds already
built or designed.

1. **Level** ([VISION.md](VISION.md), "A hierarchy of worlds").
   - **Primary:** rules, and no AI inside. Built: the plant worlds,
     the chemistry soup, the corridor.
   - **Superworld:** hosts worlds, and is tended by a Keeper from
     outside. Built: the Ur-world's garden, which hosts three plant
     worlds. Designed: a superworld for chemistry worlds, the Commons.
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

## Which world has which operations

The rule of thumb: **the more of someone's life a world holds, the
fewer operations are anyone's to choose.**

| World | Pause, resume, checkpoint | Stop | Restart | Reset | Branch |
|---|---|---|---|---|---|
| **Primary, closed, no one inside** (a plant world; a question world) | yes | yes | yes | yes: a new run | yes |
| **With scripted agents only** | yes | yes | yes | yes: a new run | yes |
| **With minds from outside** | yes, logged | after they are told, and can leave | yes | as a new run they may join | a copy of the world, not of the minds |
| **With individuals with lives** | yes, logged, and they are told | after they are told, and can leave; their keys, records and sealed selves stay theirs | yes | never over anyone's head: only as a new world they may choose to enter | a copy of the world, never of a person, who chooses whether to enter it |
| **Superworld** | yes; pausing it pauses the worlds it hosts, and each of them can also pause itself | after each hosted world is stopped | yes | its hosted worlds by their own rules | yes |
| **Control world** | yes, logged, so a disturbed run is never taken for an undisturbed one | yes | yes | yes: a new run | yes |
| **The multiverse** | no master switch: part by part, by each who runs a part | part by part | part by part | never | never |

## What is built, and what is next

- **Built:** worlds are deterministic and replayable from their logs.
  The plant worlds and the Ur-world sign their log heads, which is what
  a checkpoint needs. The garden gives each glasshouse its step, which
  is what pausing a superworld needs.
- **Next:** the operations themselves, as entries in a world's log, in
  `rust/world-log` and each world. The course takes them up at its next
  recheck ([COURSE.md](COURSE.md), "Waiting"). The endless plant needs
  pause, resume and checkpoint first, to run for hours in the browser
  ([FRACTALS.md](FRACTALS.md)).

## Open

- Whether "branch" may ever copy a person. This page says never: a
  person is one, and enters a copy only by choice.
- How long a paused world waits before it counts as stopped, if ever.
- Who may pause a world that others are in, besides the world itself
  and its rules: its Keeper, and when.

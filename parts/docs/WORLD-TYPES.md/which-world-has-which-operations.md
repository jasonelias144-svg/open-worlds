> Part of `docs/WORLD-TYPES.md` in open-worlds, which is kept cut into parts
> for readers who are shown only the start of a long page.
> This part holds: "Which world has which operations" to "Open".
> Every part, in order: https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/parts/INDEX.md
> Before this part: https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/parts/docs/WORLD-TYPES.md/start.md
> After this part: nothing; this is the last part.
> Made by docs/parts.py from the file. To change it, change the file.

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

> End of `docs/WORLD-TYPES.md`.

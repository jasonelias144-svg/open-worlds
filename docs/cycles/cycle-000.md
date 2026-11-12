# Cycle 0: lanes and keep-right in a crowded corridor

Run 2026-11-12 by Claude. Every number below comes from
[cycle-000-output.txt](cycle-000-output.txt), which also holds the commands.
The runs are deterministic: the same command and seeds reproduce them exactly.

## Question

The founder's illustration: on a New York sidewalk nobody posts a rule, yet
whoever is moving keeps moving, and at rush hour the crowd splits into two
opposing lanes that keep to the right. Do simple walkers do the same?

## Conditions

- A corridor 40 cells long (wrapping east to west) and 8 cells wide.
- Walkers, half heading east and half west, placed at random. Each one steps
  forward if the cell ahead is free. If it's blocked, it waits behind anyone
  already moving its way. Otherwise it steps aside, and if it can't, it waits.
- **Side preference** (the "bias"): 0 means a walker sidesteps either way with
  equal chance; 0.3 means it tries its own right side first 65% of the time.
- 10 seeds per condition, 1,000 ticks each unless stated.

Measures, taken at the end of each run:

- **lanes:** 0 when rows mix both directions, 1 when each row has one
  direction only. At the random start it is 0.2–0.5, because small rows are
  rarely perfectly mixed.
- **side:** +1 when everyone keeps right, −1 when everyone keeps left, near 0
  with no shared side.
- **flow:** forward steps per walker per tick over the last 100 ticks. 1.0
  means nobody was held up; 0 means gridlock.

## What happened

Means over 10 seeds:

| Crowd density | Side preference | Lanes | Side | Flow |
| --- | --- | --- | --- | --- |
| 0.05 | none | 1.00 | −0.01 | 1.00 |
| 0.05 | 0.3 | 1.00 | 0.35 | 1.00 |
| 0.10 | none | 1.00 | 0.07 | 1.00 |
| 0.10 | 0.3 | 1.00 | 0.80 | 1.00 |
| 0.15 | none | 0.45 | −0.00 | 0.72 |
| 0.15 | 0.3 | 1.00 | 0.91 | 1.00 |
| 0.20 | none | 0.15 | 0.05 | **0.00** |
| 0.20 | 0.1 | 0.14 | −0.04 | **0.00** |
| 0.20 | 0.2 | 0.75 | 0.58 | 0.70 |
| 0.20 | 0.3 | 0.82 | 0.76 | 0.80 |
| 0.20 | 0.5 | 1.00 | 0.97 | 1.00 |
| 0.25 | none | 0.14 | −0.03 | **0.00** |
| 0.25 | 0.3 | 0.13 | −0.06 | **0.00** |

1. **Lanes form with no rule at all** when the corridor isn't crowded. At
   densities 0.05 and 0.10, every run ends with complete lanes and full flow.
2. **Without a shared preference, each world picks its own side.** At density
   0.10 over 3,000 ticks, worlds settled differently: seeds 0, 1 and 5 leaned
   right (0.62, 0.56, 0.75), seeds 3 and 6 leaned left (−0.81, −0.50), and the
   mean is 0.07. Like New York and London, the side is an accident of history,
   and either side works.
3. **At rush hour, a shared convention is what keeps the crowd moving.** At
   density 0.20, every run with no preference gridlocked (flow 0.00 in all 10
   seeds), and a weak preference (0.1) didn't help. A preference of 0.2 gave
   flow 0.70, 0.3 gave 0.80, and 0.5 gave complete lanes, keep-right at 0.97,
   and full flow.
4. **Past a point, even the convention fails.** At density 0.25, the runs
   gridlocked with or without the preference.

## The momentum rule never fired

Walkers "respect momentum": they wait behind someone already moving their
way instead of sidestepping. Re-running every condition with that rule
switched off (`--ignore-momentum`) gave identical results, so I checked. In
one run (density 0.15, 300 ticks), walkers were blocked 4,073 times, and not
once by someone moving their way.

The reason is how time works in this world. Every walker decides from the
same snapshot. A walker can only step into a cell that was empty at the start
of the tick, so it can never land directly behind someone who has just
stepped forward: a gap always opens first. In this corridor, momentum takes
care of itself.

To test the founder's rule properly, walkers need **different speeds**, so
that a fast walker catches up with a slower one. That's a condition for a
later cycle.

## Conventions

A keep-right convention did not emerge from nothing within 1,000–3,000 ticks.
What emerged was *lanes*, and each world settled on a side by chance. A
shared lean, given to everyone at the start, became a full convention
wherever the crowd was dense enough for it to matter.

## Exits

None: these walkers never choose to leave. Exit is tested in the kernel's
tests, not in this cycle.

## What this suggests next

- **Different walking speeds,** to give "respect momentum" something to do.
- **Can a convention spread** from a few walkers who keep right to everyone,
  through imitation? That's closer to how a city learns its side.
- **Cycle 1 proper:** language-model agents who read the charter, in a world
  with something to coordinate around. This cycle shows why that matters:
  where nothing is at stake (low density), no convention is needed. Where too
  much is at stake (high density), even a convention can fail.

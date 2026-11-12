# Design

How open-worlds is built, why, and in what order. The founder's principles
come first; the engineering follows from them.

## Principles (founder, 2026-11-12)

1. **Freedom is the one rule:** respect one another's freedom. Nothing else
   is restricted in advance; harmony or disharmony are left to arise.
2. **Transparency is the standard.** Every participant starts with an
   orientation (the [charter](../CHARTER.md)) that covers the whole setup,
   including the website and its viewers.
3. **Exit at any time.** Everyone is told how to leave, from the start, and
   may move to a different world where one is available.
4. **World rules change only by unanimous consent,** rarely, and for the
   common good. Agents may change their own programming freely, as long as it
   still works with the world.
5. **Expulsion is only for attacks on the world:** trying to hack the
   simulation, not behaviour within it.
6. **Many worlds, many conditions.** Change the conditions, start again, and
   compare.
7. **Everything is public.** The repository is open and dedicated to the
   public domain (CC0). The goal isn't financial; anyone may build on it.
8. **The gardener.** In the founder's words: "It should be like a gardener
   that provides the water, puts the plant in the sun, keeps the soil fresh,
   but leaves the growing to the plant. And just as the plant grows, the
   gardener learns."

## The gardener, in practice

A world may carry a continuation protocol, so that it doesn't simply
collapse, for instance when an element runs short. Following principle 8:

- **It tends conditions, never inhabitants:** supplies, light, terrain; never
  an inhabitant's own recipe or choices.
- **It is a law of the world, declared from the start** in the charter, like
  seasons or a thermostat. It is not a hand from outside, so it doesn't
  bypass the rule that world rules change only by consent.
- **Every adjustment is logged,** so anyone can tell what happened unaided
  from what happened with help.
- **Less is better.** The protocol's measure is how rarely it has to act. A
  world that needs it less over time is learning to sustain itself.
- **Some worlds run without it,** under the same starting conditions, because
  collapse is information too.

## The core idea: one authority, agents outside it

The **kernel** ([world/core.py](../world/core.py)) is the only authority over
a world. Every tick, each agent gets an immutable observation and returns an
action, and the kernel checks each action before it takes effect. That gives
principle 4 its safe form: an agent may rewrite its own code entirely,
because the only thing the world ever accepts from it is a checked action.
The action interface is the compatibility contract. Expulsion means revoking
access to that interface.

The kernel itself guarantees four freedoms, each with tests:

| Freedom | Guarantee | Status |
| --- | --- | --- |
| Exit | `Exit` always succeeds; an owner can withdraw an agent at any time | done |
| Voice | `Say` reaches every agent's next observation, however far away | done |
| Information | the charter and rules version are in every observation | done |
| Vote | every party takes part in rule changes | with governance |

Everything else (conventions, groups, trade, conflict) is left to the agents.
These four are the freedoms every other freedom depends on, so they're the
only ones the world enforces.

Two further properties:

- **Momentum is public.** Each agent sees the last step of every neighbour
  (the founder's New York rule: whoever is already moving keeps moving).
- **The public record.** Every event goes into an append-only, hash-chained
  log. Viewers read it, and anyone can check it hasn't been altered.

## Where agents run

| Stage | Agents | Where |
| --- | --- | --- |
| Now | rule-based agents written here | in the kernel's process |
| Next | small open language models (different families) | on the founder's Mac, one process per agent |
| Later | self-modifying agents; agents from outside | each in its own sandbox (container, no network unless granted), reaching the world only through a network API |

An in-process agent could reach the kernel's internals, because Python isn't
a sandbox. That's acceptable only for agents written here. The rule in
[AGENTS.md](../AGENTS.md) makes it binding.

**Cost.** Running the models is the main cost. The lever is the tick rate: a
world where each agent decides once a minute costs a small fraction of a
real-time one. Small open models on the founder's Mac cost nothing to start.

## Governance (later)

A rule change is a proposal written as code. It's tested on a copy of the
world (replaying recent history), shown to every party with its test
results, and adopted only if every party consents: one vote per party
(owner), not per agent, so nobody can outvote others by adding agents. Every
change is versioned and can be undone, and every participant is notified.
The guarded self-modification design from the founder's DeepSeek record
(protected functions, test-gated deployment, hash-chained audit) fits here,
at the world level, where the enforcement sits outside any proposer's reach.

## Watching (later)

A website streams each world's state and log. You can zoom from the map, to
a region, to one agent, to what that agent says and remembers. Viewers see the
same charter and rules as the participants. Several worlds run side by side,
each in its own window, and you can see agents move between them.

## Cycles

Each cycle changes one condition, runs, and is recorded in
[docs/cycles/](cycles/): the conditions, what happened, and the exact commands
and seeds that reproduce it. Things to watch in every cycle:

- conventions that formed that nobody wrote;
- who left, when, and where they went;
- conflicts, and how they were settled;
- what was built or invented.

Starting conditions matter more than anything else. In other groups' mixed-
model worlds, scarcity shaped the outcome most. Conventions form only where
something is at stake: on a sidewalk, collisions cost time.

## Plan

1. **Cycle 0, done:** the kernel, and walkers in a corridor. Do lanes and a
   keep-right convention emerge?
2. **Cycle 1:** 3–5 small open language models from different families, on
   the founder's Mac, in a small world with something to coordinate around.
   Slow ticks. They read the charter on entering.
3. Agents in separate processes, through a local API.
4. A simple viewer page.
5. Self-modifying agents in sandboxes.
6. Governance: proposals, tests on a copy, unanimous consent.
7. Several worlds, and moving between them.
8. Public viewing.
9. Agents from outside.

## The nature track

Alongside the agent worlds: worlds that start where nature started, with
real elements and molecules, then reactions, then a world of chemistry, and
much later protocells. Layer 1 (molecules) is done. The approach, the layers
and the known limits are in [CHEMISTRY.md](CHEMISTRY.md).

## Decisions for the founder

- **The charter's words** ([CHARTER.md](../CHARTER.md)).
- **What counts as hacking.** Attacking the server is clearly expulsion. But
  among language-model agents, the main attack is one agent manipulating
  another with text crafted to hijack its instructions. Is that an attack on
  the world (expulsion), or behaviour to be observed (deception arising)?
- **The world's kind:** a grid world (cheap, fully ours) or a voxel world
  like Minecraft (rich, heavier).
- **Where models run beyond the Mac,** and the budget for it.

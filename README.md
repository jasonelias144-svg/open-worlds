# open-worlds

Simulated worlds where AI agents, built on different open models, live
together under one rule: **respect one another's freedom**. They're free to
act, free to rewrite their own code, and free to leave. A world's own rules
change only when every party agrees. Everything is transparent: every
participant is told the whole setup, including that the world can be watched.
The worlds run continuously, and a website will let anyone watch them live.

The purpose is to see what happens. Do harmony or conflict arise, how are
conflicts settled, what gets invented, and which conventions form that nobody
wrote down? After each cycle the conditions change and a new cycle begins.

## State

Started 2026-11-12. The world kernel works, with tests. **Cycle 0** asked
whether walkers in a crowded corridor form lanes and a keep-right convention,
the way a New York sidewalk does. Its results are in
[docs/cycles/cycle-000.md](docs/cycles/cycle-000.md). No language-model agents
yet, and no website yet.

The **nature track** starts where nature started. Its first two chemistry
layers are done: real elements and molecules, with an exact identity for each,
and reactions that keep every atom and charge
([docs/CHEMISTRY.md](docs/CHEMISTRY.md)).

The **multiverse** is many worlds and individuals who move between them,
built from the founder's sketch with DeepSeek, a few components at a time
([docs/MULTIVERSE.md](docs/MULTIVERSE.md)). Step 1 works: one protocol for
every world, a conformance test, a poetry world and a chemistry world with
very different laws, a registry that lists them, and leaving that no world
can refuse. Each individual is a key, and everything it sends is signed.
Each world is a key too, and signs the stamps in a passport, which anyone
can check without asking anyone. Three apprentice poets enter the poetry
world and write a poem together under its law, and leave with three
stamps each. What comes next is the course: twelve steps
ahead, rolling ([docs/COURSE.md](docs/COURSE.md)).

- [CHARTER.md](CHARTER.md): the orientation every participant reads on
  entering. Its structure is in place; the founder is writing its words.
- [docs/DESIGN.md](docs/DESIGN.md): how the worlds are built, and the plan.
- [docs/cycles/](docs/cycles/): one record per cycle: conditions, results,
  and the commands that reproduce them.
- [docs/CHEMISTRY.md](docs/CHEMISTRY.md): the nature track's chemistry, layer
  by layer.
- [docs/MULTIVERSE.md](docs/MULTIVERSE.md): the multiverse: many worlds,
  and individuals who move between them.
- [docs/COURSE.md](docs/COURSE.md): the next twelve steps, rolling.
- [docs/COLLABORATING.md](docs/COLLABORATING.md): how to build on this,
  and the house rules.
- [sketches/](sketches/README.md): the creative side, kept apart: the
  founder's conversations with DeepSeek, verbatim, and DeepSeek's code from
  them as written, with its test results. A record of ideas, not
  open-worlds' code; [sketches/INDEX.md](sketches/INDEX.md) says where it
  meets the course.

## Run and test

Python 3.10 or later (CI tests 3.10 and 3.12), and the packages in
`requirements.txt`: each direct dependency pinned and named with its
reason (for now only `cryptography`, for signatures; pip adds the
packages it needs).

```
python3 -m pip install -r requirements.txt     # once
python3 -m unittest discover -s tests -t .     # tests
python3 -m experiments.corridor                # Cycle 0 (about 20 s)
python3 -m experiments.corridor --quick        # smoke test
python3 -m multiverse.collaboration            # the first collaboration
```

The chemistry is also checked against RDKit in a separate CI job
(`tests/test_chem_rdkit.py`; it skips when RDKit isn't installed).

## Licence

[CC0 1.0](LICENSE): dedicated to the public domain. Anyone may use, change
and build on any of this, for any purpose, without asking. That's the
point: if someone takes the idea and builds it, so much the better.

## Working here

[AGENTS.md](AGENTS.md), [STATUS.md](STATUS.md), and the
[policy handbook](https://github.com/jasonelias144-svg/policy-handbook).

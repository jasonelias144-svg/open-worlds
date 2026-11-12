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

- [CHARTER.md](CHARTER.md): the orientation every participant reads on
  entering. Its structure is in place; the founder is writing its words.
- [docs/DESIGN.md](docs/DESIGN.md): how the worlds are built, and the plan.
- [docs/cycles/](docs/cycles/): one record per cycle: conditions, results,
  and the commands that reproduce them.
- [docs/CHEMISTRY.md](docs/CHEMISTRY.md): the nature track's chemistry, layer
  by layer.

## Run and test

Python 3.10 or later, standard library only.

```
python3 -m unittest discover -s tests -t .     # tests
python3 -m experiments.corridor                # Cycle 0 (about 20 s)
python3 -m experiments.corridor --quick        # smoke test
```

The chemistry is also checked against RDKit, which isn't standard library,
in a separate CI job (`tests/test_chem_rdkit.py`; it skips when RDKit isn't
installed).

## Licence

[CC0 1.0](LICENSE): dedicated to the public domain. Anyone may use, change
and build on any of this, for any purpose, without asking. That's the
point: if someone takes the idea and builds it, so much the better.

## Working here

[AGENTS.md](AGENTS.md), [STATUS.md](STATUS.md), and the
[policy handbook](https://github.com/jasonelias144-svg/policy-handbook).

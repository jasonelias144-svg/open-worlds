"""Ours, not DeepSeek's (see README.md): the Rust plant world
(rust/plant-world) grows by this sketch's rule.

For each world in vectors/plant-world.json, the sketch's own `advance`
(fractal_world_v3.py) is run from the world's first tip, with its dials
and pot, and must give the same branches and the same tips, in the same
order, at every step; and at the step the world says it finished, it
must give nothing more. The sketch always has a pot: a world without one
is given a pot far wider than any plant these dials can grow.
"""
import json
from pathlib import Path

import pytest

from fractal_world_v3 import ParamSet, advance

VECTORS = (Path(__file__).resolve().parents[3] / "vectors"
           / "plant-world.json")
NO_POT = (-10 ** 9, -10 ** 9, 2 * 10 ** 9, 2 * 10 ** 9)


def _worlds():
    return json.loads(VECTORS.read_text(encoding="utf-8"))["worlds"]


def _start(world):
    first = world["log"][0]["data"]
    d = first["dials"]
    params = ParamSet(branch_length=d["branchLength"],
                      max_depth=d["maxDepth"], water=d["water"],
                      light=d["light"])
    pot = tuple(first["pot"]) if first["pot"] is not None else NO_POT
    return params, pot, [tuple(first["tip"])]


@pytest.mark.parametrize("world", _worlds(), ids=lambda w: w["name"])
def test_every_step_is_the_sketchs(world):
    params, pot, tips = _start(world)
    log = world["log"]
    assert log[-1]["kind"] == "finished"
    for entry in log[1:-1]:
        assert entry["kind"] == "grew"
        segs, tips = advance(tips, params, pot)
        assert [list(s) for s in segs] == entry["data"]["segments"]
        assert [list(t) for t in tips] == entry["data"]["tips"]
    if params.can_grow():
        assert advance(tips, params, pot)[0] == []


def test_the_pot_in_the_vectors_stops_some_branches():
    potted = [w for w in _worlds() if w["log"][0]["data"]["pot"]]
    assert potted
    for world in potted:
        params, pot, tips = _start(world)
        grown = sum(len(e["data"]["segments"])
                    for e in world["log"] if e["kind"] == "grew")
        free, unpotted = 0, list(tips)
        while True:
            segs, unpotted = advance(unpotted, params, NO_POT)
            if not segs:
                break
            free += len(segs)
        assert grown < free

"""Ours, not DeepSeek's (see README.md): the sketch here, as written,
is what README.md says it is. It reads DeepSeek's files as text, and
neither builds nor runs them; review/run.sh does that, outside CI.

If one of these fails, the sketch has been changed: say so in
README.md and INDEX.md, list the file under "changed" in
../../tools/names-012-07-03.json, and change the test with them."""
import json
import re
from pathlib import Path

HERE = Path(__file__).parent
CRATE = HERE / "endless-plant"


def _source(name):
    return (CRATE / "src" / name).read_text(encoding="utf-8")


def test_two_functions_world_rs_needs_are_defined_nowhere():
    # Finding 1: it doesn't build as written.
    world = _source("world.rs")
    every = "".join(_source(f.name) for f in (CRATE / "src").glob("*.rs"))
    for name in ("growth_priority", "dieback_priority"):
        assert re.search(rf"\b{name}\b", world), name
        assert not re.search(rf"\bfn\s+{name}\b", every), name


def test_the_no_light_vector_expects_the_plant_to_die():
    # Finding 2: review/review.rs shows the code rests instead.
    vectors = json.loads(
        (HERE / "vectors" / "endless-plant.json").read_text(encoding="utf-8"))
    case = next(v for v in vectors["vectors"]
                if v["name"] == "no-light-no-growth")
    assert case["expect"]["finalEnergy"] == -1
    assert case["expect"]["logKinds"] == ["world_created", "died_back",
                                          "died"]


def test_grow_and_split_are_one_branch():
    # Finding 3: the neuron's choice between them changes nothing.
    assert "Action::Grow | Action::Split =>" in _source("world.rs")


def test_the_noise_reads_one_byte_of_the_seed():
    # Finding 6.
    assert "self.seed[0]" in _source("world.rs")
    assert not re.search(r"self\.seed\[[1-9]", _source("world.rs"))

"""Shared test vectors: what this kernel writes, kept in `vectors/` so that
code in other languages can check itself against it, hash for hash
(vectors/README.md; the Rust crate in rust/world-log reads them).

    python3 -m world.vectors      rewrite vectors/ from this kernel

tests/test_vectors.py checks that the files in vectors/ are still exactly
what this kernel writes, so a change on the Python side can't pass
unnoticed: rewrite them, and the other languages' tests say whether they
still agree.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List

from .core import Exit, Move, Say, Wait, World, _digest

FOLDER = Path(__file__).resolve().parent.parent / "vectors"


class _Script:
    """Plays a fixed list of actions, one a tick, then waits."""

    def __init__(self, *actions: object):
        self._actions = list(actions)

    def act(self, obs: object) -> object:
        return self._actions.pop(0) if self._actions else Wait()


class _Fails:
    """An agent whose every turn raises."""

    def act(self, obs: object) -> object:
        raise ValueError("on purpose")


def world_log() -> List[dict]:
    """The log of a short seeded run that writes every kind of entry: a
    world created, agents entering, moving, blocked by a wall and by each
    other, speaking (with text that needs escaping), refused, failing,
    leaving by choice and pulled out by their owner."""
    w = World(5, 3, seed=7, rules_version="vectors-1")
    w.add("ada", _Script(
        Move(1, 0),
        Say("hello, world"),
        Move(0, -1),                                  # a wall
        Say("caf\u00e9 \u4e2d\u6587 \U0001F642 \u2028 \U0010FFFF"),
        Move(1, 0),                                   # bo stands there
        Exit()), (0, 0))
    w.add("bo", _Script(
        Say('quote " backslash \\ tab \t newline \n return \r'),
        Say("\x00\x01\x08\x0c\x1f\x7f ~"),
        "jump",                                       # not an action
        Move(2, 0),                                   # too far
        Say("x" * 300),                               # cut to 280
        Wait()), (2, 0))
    w.add("cy", _Fails(), (4, 2))
    w.run(3)
    w.leave("cy", "pulled out by its owner")
    w.run(4)
    return w.log


# Bodies whose hashes test the writing of JSON at its edges: key order,
# escapes, the printable range's ends, characters outside the basic plane,
# and integers at the ends of 64 bits.
BODIES: List[Dict] = [
    {},
    {"b": 1, "a": 2, "B": 3, "_": 4, "\u00e9": 5, "aa": 6, "a b": 7},
    {"v": ""},
    {"v": "plain text"},
    {"v": 'quote " backslash \\ slash /'},
    {"v": "\b\f\n\r\t"},
    {"v": "\x00\x01\x1f"},
    {"v": " ~\x7f"},
    {"v": "\u00e9\u00ff\u0100"},
    {"v": "\u4e2d\u6587"},
    {"v": "\U0001F642"},
    {"v": "\u2028\u2029\ufeff\uffff"},
    {"v": "\U00010000\U0010FFFF"},
    {"\U0001F642": "key outside the basic plane"},
    {"v": [0, -1, 1, 2 ** 53 + 1, 2 ** 63 - 1, -(2 ** 63), 2 ** 64 - 1]},
    {"v": [True, False, None]},
    {"v": [[], {}, [[1, [2, [3]]]], {"z": {"y": {"x": []}}}]},
    {"tick": 0, "kind": "world_created", "agent": None,
     "data": {"width": 5, "height": 3, "wrap_x": False, "seed": 7,
              "rules_version": "1"},
     "prev": "0" * 64},
]


def digests() -> List[dict]:
    """Each body, the exact text the kernel hashes, and its hash."""
    return [{"body": b,
             "text": json.dumps(b, sort_keys=True, separators=(",", ":")),
             "hash": _digest(b)} for b in BODIES]


def files() -> Dict[str, str]:
    """The vector files' names and contents: ASCII JSON, keys sorted."""
    def text(value: object) -> str:
        return json.dumps(value, sort_keys=True, indent=1) + "\n"
    return {"world-log.json": text(world_log()),
            "digests.json": text(digests())}


def main() -> None:
    for name, content in files().items():
        (FOLDER / name).write_text(content, encoding="ascii")
        print(f"wrote vectors/{name}")


if __name__ == "__main__":
    main()

"""Cycle 0: does a walking convention emerge in a crowded corridor?

The founder's illustration: on a New York sidewalk nobody posts a rule, yet
people respect momentum, and at rush hour the crowd splits into two opposing
lanes that keep to the right. This experiment asks whether simple walkers do
the same in an open-worlds corridor.

Each walker heads east or west. If the cell ahead is free it steps forward.
If someone ahead is already moving the same way, it respects their momentum
and waits behind them. Otherwise it steps aside (up or down) when it can,
and else waits. With side_bias 0 a walker sidesteps either way with equal
chance; with side_bias b it tries its own right side first with probability
(1 + b) / 2.

Two measures:
  lane order       0 when every row mixes both directions equally,
                   1 when every row holds one direction only.
  side convention  +1 when everyone keeps right, -1 when everyone keeps left,
                   near 0 when there is no shared side.

Run: python3 -m experiments.corridor        (both conditions, 10 seeds each)
     python3 -m experiments.corridor --quick
"""
from __future__ import annotations

import argparse
import random
import statistics
from typing import Dict, List

from world import Move, Wait, World

ORIENTATION = (
    "You are in a corridor that wraps around east to west. You may move one "
    "cell at a time, speak, wait, or leave at any time.")


class Walker:
    """Heads in one direction; steps aside when blocked."""

    def __init__(self, direction: int, rng: random.Random,
                 side_bias: float = 0.0, respect_momentum: bool = True):
        if direction not in (1, -1):
            raise ValueError("direction is 1 (east) or -1 (west)")
        self.direction = direction
        self.rng = rng
        self.side_bias = side_bias
        self.respect_momentum = respect_momentum

    def right(self) -> int:
        # y grows downward (south). Facing east, your right is south (+1);
        # facing west, your right is north (-1).
        return 1 if self.direction == 1 else -1

    def act(self, obs):
        x, y = obs.position
        ahead = ((x + self.direction) % obs.width, y)
        if not obs.occupied(ahead):
            return Move(self.direction, 0)
        if self.respect_momentum and obs.momentum_at(ahead) == (self.direction, 0):
            return Wait()  # they are moving our way: follow, don't overtake
        r = self.right()
        first = r if self.rng.random() < (1 + self.side_bias) / 2 else -r
        for dy in (first, -first):
            if 0 <= y + dy < obs.height and not obs.occupied((x, y + dy)):
                return Move(0, dy)
        return Wait()


def lane_order(world: World, walkers: Dict[str, Walker]) -> float:
    east = [0] * world.height
    west = [0] * world.height
    for agent_id in world.agents():
        _, y = world.position(agent_id)
        (east if walkers[agent_id].direction == 1 else west)[y] += 1
    total = sum(east) + sum(west)
    return sum(abs(e - w) for e, w in zip(east, west)) / total if total else 0.0


def side_convention(world: World, walkers: Dict[str, Walker]) -> float:
    """Mean over walkers of +1 if on its own right half, else -1."""
    half = world.height / 2
    scores = []
    for agent_id in world.agents():
        _, y = world.position(agent_id)
        on_south = y >= half
        keeps_right = on_south if walkers[agent_id].direction == 1 else not on_south
        scores.append(1 if keeps_right else -1)
    return statistics.fmean(scores) if scores else 0.0


def run_corridor(width: int = 40, height: int = 8, density: float = 0.15,
                 ticks: int = 1000, seed: int = 0, side_bias: float = 0.0,
                 respect_momentum: bool = True,
                 window: int = 100) -> Dict[str, float]:
    """One run. Returns lane order and side convention at the start and end,
    and the flow: forward steps per walker per tick over the last `window`
    ticks (1.0 means nobody was ever held up)."""
    if height % 2:
        raise ValueError("use an even height so the corridor has two halves")
    rng = random.Random(seed)
    world = World(width, height, seed=seed, wrap_x=True,
                  orientation=ORIENTATION)
    cells = [(x, y) for x in range(width) for y in range(height)]
    n = int(len(cells) * density) // 2 * 2
    walkers: Dict[str, Walker] = {}
    for i, pos in enumerate(rng.sample(cells, n)):
        w = Walker(1 if i % 2 == 0 else -1, random.Random(rng.random()),
                   side_bias, respect_momentum)
        agent_id = f"w{i:03d}"
        walkers[agent_id] = w
        world.add(agent_id, w, pos)

    start = {"lane_order": lane_order(world, walkers),
             "side_convention": side_convention(world, walkers)}
    forward = 0
    last_x = {a: world.position(a)[0] for a in world.agents()}

    def count_flow(w: World) -> None:
        nonlocal forward
        for a in w.agents():
            x = w.position(a)[0]
            if w.tick > ticks - window and x == (last_x[a] + walkers[a].direction) % width:
                forward += 1
            last_x[a] = x

    world.run(ticks, on_tick=count_flow)
    if not World.verify_log(world.log):
        raise RuntimeError("event log failed verification")
    return {
        "lane_order_start": start["lane_order"],
        "lane_order_end": lane_order(world, walkers),
        "side_convention_start": start["side_convention"],
        "side_convention_end": side_convention(world, walkers),
        "flow": forward / (n * min(window, ticks)),
        "walkers": n,
        "log_head": world.log_head(),
    }


def main(argv: List[str] | None = None) -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--seeds", type=int, default=10)
    ap.add_argument("--ticks", type=int, default=1000)
    ap.add_argument("--biases", type=float, nargs="+", default=[0.0, 0.3])
    ap.add_argument("--density", type=float, default=0.15)
    ap.add_argument("--ignore-momentum", action="store_true",
                    help="walkers sidestep even behind someone moving their way")
    ap.add_argument("--quick", action="store_true",
                    help="2 seeds, 200 ticks: a smoke test")
    args = ap.parse_args(argv)
    seeds, ticks = (2, 200) if args.quick else (args.seeds, args.ticks)

    print(f"corridor 40x8, density {args.density}, {ticks} ticks, "
          f"seeds 0..{seeds - 1}"
          + (", ignoring momentum" if args.ignore_momentum else ""))
    print(f"{'bias':>5} {'seed':>4} {'lanes start':>11} {'lanes end':>9} "
          f"{'side start':>10} {'side end':>8} {'flow':>5}")
    for bias in args.biases:
        rows = []
        for seed in range(seeds):
            r = run_corridor(ticks=ticks, seed=seed, side_bias=bias,
                             density=args.density,
                             respect_momentum=not args.ignore_momentum)
            rows.append(r)
            print(f"{bias:>5.2f} {seed:>4} {r['lane_order_start']:>11.2f} "
                  f"{r['lane_order_end']:>9.2f} {r['side_convention_start']:>10.2f} "
                  f"{r['side_convention_end']:>8.2f} {r['flow']:>5.2f}")
        mean = lambda k: statistics.fmean(r[k] for r in rows)  # noqa: E731
        print(f"{bias:>5.2f} mean {mean('lane_order_start'):>11.2f} "
              f"{mean('lane_order_end'):>9.2f} {mean('side_convention_start'):>10.2f} "
              f"{mean('side_convention_end'):>8.2f} {mean('flow'):>5.2f}")


if __name__ == "__main__":
    main()

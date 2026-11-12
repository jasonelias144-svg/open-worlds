"""A world of chemistry: molecules in a grid of well-mixed cells.

Layer 3, step 1: the engine (docs/CHEMISTRY.md). Each cell holds counts of
each kind of molecule. Two kinds of event change them:

- **a reaction in a cell**, at the rate mass action gives: the reaction's
  rate constant times the number of ordered ways to pick its reactants from
  the cell, divided by the cell's volume once for each reactant beyond the
  first. Ordered picks means n(n-1) for two of one kind and n(n-1)(n-2) for
  three; the common textbook convention counts unordered pairs, n(n-1)/2, so
  a textbook rate constant for two of one kind is halved here (divided by 6
  for three of one kind);
- **a hop**: one molecule moves to a neighbouring cell (diffusion), at its
  species' hop rate per neighbour. On a wrapped grid two cells wide (or
  high), the other cell is a neighbour on both sides, so it is listed twice
  and gets twice the hop rate, as on any periodic lattice.

The next event and the time until it are drawn exactly, by Gillespie's
direct method, from a seeded random generator, so a world with the same
seed replays exactly.

Atoms and charge are kept by every event: a reaction is refused when it is
added unless both sides have the same atoms and charge, and a hop moves a
whole molecule. Every event goes into a hash-chained public log in the same
format as the agent worlds' log, so `World.verify_log` checks it.

Rates here are given by whoever builds the world. Where they come from
(measured equilibrium constants, estimates) is step 2.
"""
from __future__ import annotations

import hashlib
import json
import math
import random
from collections import Counter
from dataclasses import dataclass
from typing import Dict, List, Optional, Sequence, Tuple

from .molecule import Molecule
from .reactions import balance

GENESIS = "0" * 64          # the same start as the agent worlds' log
MIN_VOLUME, MAX_VOLUME = 1e-6, 1e6
# Far above any real rate constant, and low enough that a propensity can't
# overflow to infinity (which would stop the clock).
MAX_RATE = 1e15

Cell = Tuple[int, int]


@dataclass(frozen=True)
class Reaction:
    reactants: Tuple[Molecule, ...]
    products: Tuple[Molecule, ...]
    rate: float


def _positive_number(x: object, what: str, allow_zero: bool = True) -> float:
    if type(x) not in (int, float) or math.isnan(x) or math.isinf(x) \
            or x < 0 or (x == 0 and not allow_zero):
        raise ValueError(f"{what} must be a finite number >= 0: {x!r}")
    return float(x)


class Soup:
    """A grid of well-mixed cells. See the module docstring."""

    def __init__(self, width: int, height: int, *, volume: float = 1.0,
                 seed: int = 0, wrap: bool = False, log: bool = True):
        if type(width) is not int or type(height) is not int \
                or width < 1 or height < 1:
            raise ValueError("width and height must be whole numbers >= 1")
        if type(seed) is not int or type(wrap) is not bool or type(log) is not bool:
            raise ValueError("seed must be a whole number; wrap and log, True or False")
        self.width, self.height, self.wrap = width, height, wrap
        self.volume = _positive_number(volume, "volume", allow_zero=False)
        if not MIN_VOLUME <= self.volume <= MAX_VOLUME:
            raise ValueError(f"volume must be between {MIN_VOLUME} and {MAX_VOLUME}")
        self.time = 0.0
        self.events = 0
        self.log: Optional[List[dict]] = [] if log else None
        self._head = GENESIS
        self._rng = random.Random(seed)
        self._species: List[Molecule] = []
        self._index: Dict[str, int] = {}
        self._hop: List[float] = []
        self._reactions: List[Reaction] = []
        # Each reaction as (reactant species with multiplicities, change per species).
        self._channels: List[Tuple[List[Tuple[int, int]], Dict[int, int], float, int]] = []
        self._counts: List[List[int]] = [[] for _ in range(width * height)]
        self._neighbours = [self._find_neighbours(c) for c in range(width * height)]
        self._propensity: List[float] = [0.0] * (width * height)
        self._record("world", {"width": width, "height": height,
                               "volume": self.volume, "seed": seed, "wrap": wrap})

    # -- building the world --

    def add_species(self, molecule: Molecule, hop_rate: float = 0.0) -> int:
        """Register a kind of molecule and how fast it moves: its rate of
        hopping to each neighbouring cell. Returns its index."""
        if type(molecule) is not Molecule or molecule.problems():
            raise ValueError(f"not a valid molecule: {molecule!r}")
        rate = _positive_number(hop_rate, "hop rate")
        if rate > MAX_RATE:
            raise ValueError(f"hop rate must be at most {MAX_RATE}")
        key = molecule.identity()
        if key in self._index:
            i = self._index[key]
            if self._hop[i] != rate:
                raise ValueError(f"{molecule!r} is already here with another hop rate")
            return i
        i = len(self._species)
        self._index[key] = i
        self._species.append(molecule)
        self._hop.append(rate)
        for counts in self._counts:
            counts.append(0)
        self._record("species", {"index": i, "identity": key,
                                 "formula": molecule.formula(),
                                 "charge": molecule.charge, "hop_rate": rate})
        return i

    def add_reaction(self, reactants: Sequence[Molecule],
                     products: Sequence[Molecule], rate: float) -> int:
        """Add a reaction, with its mass-action rate constant. Both sides must
        have the same atoms and charge. Unknown molecules are registered with
        a hop rate of 0. Returns the reaction's index."""
        reactants, products = tuple(reactants), tuple(products)
        if not reactants or not products:
            raise ValueError("a reaction needs reactants and products")
        rate = _positive_number(rate, "rate")
        if rate > MAX_RATE:
            raise ValueError(f"rate must be at most {MAX_RATE}")
        for m in reactants + products:
            if type(m) is not Molecule or m.problems():
                raise ValueError(f"not a valid molecule: {m!r}")
        if not balance(reactants, products):
            raise ValueError("a reaction must keep every atom and the total charge")
        net = Counter(m.identity() for m in products)
        net.subtract(m.identity() for m in reactants)
        if not any(net.values()):
            raise ValueError("a reaction must change something")
        # Only now, with every check passed, are new molecules registered.
        ids = [self.add_species(m) if m.identity() not in self._index
               else self._index[m.identity()] for m in reactants + products]
        need = Counter(ids[:len(reactants)])
        change: Dict[int, int] = Counter()
        for i in ids[:len(reactants)]:
            change[i] -= 1
        for i in ids[len(reactants):]:
            change[i] += 1
        change = {i: d for i, d in change.items() if d}
        k = len(self._reactions)
        self._reactions.append(Reaction(reactants, products, rate))
        self._channels.append((sorted(need.items()), change, rate, len(reactants)))
        self._record("reaction", {"index": k, "reactants": ids[:len(reactants)],
                                  "products": ids[len(reactants):], "rate": rate})
        self._refresh_all()
        return k

    def put(self, cell: Cell, molecule: Molecule, count: int) -> None:
        """Add `count` molecules to a cell (setting up the world, or the
        gardener's inflow). The molecule must be registered."""
        c = self._cell(cell)
        i = self._species_index(molecule)
        if type(count) is not int or count < 0:
            raise ValueError("count must be a whole number >= 0")
        self._counts[c][i] += count
        self._refresh(c)
        self._record("put", {"cell": list(cell), "species": i, "count": count})

    # -- reading the world --

    def count(self, molecule: Molecule, cell: Optional[Cell] = None) -> int:
        i = self._species_index(molecule)
        if cell is not None:
            return self._counts[self._cell(cell)][i]
        return sum(counts[i] for counts in self._counts)

    def atoms(self) -> Counter:
        """Every atom in the world, by element, and the total charge under
        the key "charge"."""
        total: Counter = Counter()
        for counts in self._counts:
            for i, n in enumerate(counts):
                if n:
                    for atom in self._species[i].atoms:
                        total[atom.symbol] += n
                    total["charge"] += n * self._species[i].charge
        return total

    @property
    def species(self) -> Tuple[Molecule, ...]:
        return tuple(self._species)

    @property
    def log_head(self) -> str:
        return self._head

    # -- running the world --

    def step(self) -> bool:
        """Make the next event happen. Returns False, changing nothing, if
        no event is possible (the world is at rest)."""
        total = sum(self._propensity)
        if total <= 0.0:
            return False
        self.time += self._rng.expovariate(total)
        c, within = self._pick(self._propensity, self._rng.random() * total)
        # Only events that can happen are candidates, so rounding at a
        # boundary can never choose one whose reactants are absent.
        events = self._possible_events(c)
        chosen = events[-1]
        for event in events:
            if within < event[0]:
                chosen = event
                break
            within -= event[0]
        _, kind, which = chosen
        counts = self._counts[c]
        if kind == "react":
            for i, d in self._channels[which][1].items():
                counts[i] += d
            self._refresh(c)
            self.events += 1
            self._record("react", {"cell": self._xy(c), "reaction": which})
        else:
            neighbours = self._neighbours[c]
            to = neighbours[self._rng.randrange(len(neighbours))]
            counts[which] -= 1
            self._counts[to][which] += 1
            self._refresh(c)
            self._refresh(to)
            self.events += 1
            self._record("hop", {"from": self._xy(c), "to": self._xy(to),
                                 "species": which})
        return True

    def run(self, until: Optional[float] = None,
            max_events: Optional[int] = None) -> int:
        """Run until the time passes `until`, `max_events` events have
        happened, or the world comes to rest. Returns the number of events.
        (The event that crosses `until` happens; time is not rolled back.)"""
        if until is None and max_events is None:
            raise ValueError("give a time limit, an event limit, or both")
        done = 0
        while (max_events is None or done < max_events) \
                and (until is None or self.time < until):
            if not self.step():
                break
            done += 1
        return done

    # -- internals --

    def _reaction_propensity(self, counts: List[int], need, rate: float,
                             order: int) -> float:
        a = rate
        for i, m in need:
            n = counts[i]
            if n < m:
                return 0.0
            for j in range(m):
                a *= n - j
        for _ in range(order - 1):
            a /= self.volume
        return a

    def _refresh(self, c: int) -> None:
        counts = self._counts[c]
        a = sum(self._reaction_propensity(counts, need, rate, order)
                for need, _, rate, order in self._channels)
        a += sum(self._hop[i] * n for i, n in enumerate(counts)) * len(self._neighbours[c])
        self._propensity[c] = a

    def _refresh_all(self) -> None:
        for c in range(len(self._counts)):
            self._refresh(c)

    def _possible_events(self, c: int) -> List[Tuple[float, str, int]]:
        """Every event that can happen in cell c, with its propensity. A cell
        is only picked when its cached propensity, a sum of these, is above
        zero, so the list is never empty."""
        counts = self._counts[c]
        events = []
        for k, (need, _, rate, order) in enumerate(self._channels):
            a = self._reaction_propensity(counts, need, rate, order)
            if a > 0.0:
                events.append((a, "react", k))
        degree = len(self._neighbours[c])
        for i, n in enumerate(counts):
            a = self._hop[i] * n * degree
            if a > 0.0:
                events.append((a, "hop", i))
        return events

    @staticmethod
    def _pick(weights: List[float], target: float) -> Tuple[int, float]:
        """The index the target falls in, and how far into it. If rounding
        carries the target past the end, the last positive weight."""
        for i, w in enumerate(weights):
            if target < w:
                return i, target
            target -= w
        last = max(i for i, w in enumerate(weights) if w > 0)
        return last, weights[last]

    def _find_neighbours(self, c: int) -> List[int]:
        x, y = c % self.width, c // self.width
        out = []
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nx, ny = x + dx, y + dy
            if self.wrap:
                nx, ny = nx % self.width, ny % self.height
            if 0 <= nx < self.width and 0 <= ny < self.height \
                    and (nx, ny) != (x, y):
                out.append(ny * self.width + nx)
        return out

    def _cell(self, cell: Cell) -> int:
        if type(cell) is not tuple or len(cell) != 2 \
                or not all(type(v) is int for v in cell):
            raise ValueError(f"a cell is an (x, y) pair of whole numbers: {cell!r}")
        x, y = cell
        if not (0 <= x < self.width and 0 <= y < self.height):
            raise ValueError(f"no such cell: {cell}")
        return y * self.width + x

    def _xy(self, c: int) -> List[int]:
        return [c % self.width, c // self.width]

    def _species_index(self, molecule: Molecule) -> int:
        if type(molecule) is not Molecule:
            raise ValueError(f"not a molecule: {molecule!r}")
        key = molecule.identity()
        if key not in self._index:
            raise ValueError(f"{molecule!r} is not in this world")
        return self._index[key]

    def _record(self, kind: str, data: dict) -> None:
        body = {"event": self.events, "time": self.time, "kind": kind,
                "data": data, "prev": self._head}
        raw = json.dumps(body, sort_keys=True, separators=(",", ":"))
        self._head = hashlib.sha256(raw.encode()).hexdigest()
        if self.log is not None:
            self.log.append({**body, "hash": self._head})

"""Reactions: rules that rewrite part of a molecule, keeping every atom and
every charge.

A rule names a few atoms and says how the bonds among them, and their
charges, change. Nothing else in the molecules is touched. This is how
graph-transformation chemistry works (for example the MOD package):

    amide_formation = Rule(
        "amide formation",
        atoms={"c": "C", "o1": "O", "o2": "O", "h": "H", "n": "N", "hn": "H"},
        before={("c", "o1"): 2, ("c", "o2"): 1, ("o2", "h"): 1, ("n", "hn"): 1},
        after={("c", "o1"): 2, ("c", "n"): 1, ("o2", "h"): 1, ("o2", "hn"): 1},
    )

Three laws hold for every rule, and a rule that breaks one is refused when
it is written, not when it is used:

- **Atoms are kept.** A rule moves bonds and charges, never atoms.
- **Charge is kept.** The charges after add up to the charges before.
- **Valence is kept.** For each named atom, the change in its bonds equals
  the change in its valence that its change of charge requires. So a rule
  applied to valid molecules always gives valid molecules.

Every rule can be run backwards (`reverse()`), and the reverse obeys the same
laws.

What a rule doesn't know: energy and rates (whether the reaction goes, and
how fast, belongs to the world of layer 3), geometry and strain, and any
context beyond the atoms it names.
"""
from __future__ import annotations

from collections import Counter
from typing import Dict, Iterator, List, Mapping, Optional, Sequence, Tuple

from .elements import ELEMENTS, valence
from .molecule import Atom, Bond, Molecule

Pair = Tuple[str, str]


def _parse_atom(spec: str) -> Tuple[str, int]:
    """"N" -> ("N", 0), "N+" -> ("N", 1), "O-" -> ("O", -1)."""
    if type(spec) is not str:
        raise ValueError(f"atom must be written as a string: {spec!r}")
    charge = 0
    if spec.endswith("+"):
        spec, charge = spec[:-1], 1
    elif spec.endswith("-"):
        spec, charge = spec[:-1], -1
    if spec not in ELEMENTS:
        raise ValueError(f"unknown element: {spec!r}")
    return spec, charge


class Rule:
    """A reaction rule. See the module docstring."""

    def __init__(self, name: str, atoms: Mapping[str, str],
                 before: Mapping[Pair, int], after: Mapping[Pair, int],
                 charges_after: Optional[Mapping[str, int]] = None):
        self.name = name
        self.symbols: Dict[str, str] = {}
        self.charges_before: Dict[str, int] = {}
        for label, spec in atoms.items():
            self.symbols[label], self.charges_before[label] = _parse_atom(spec)
        self.charges_after: Dict[str, int] = dict(self.charges_before)
        for label, charge in (charges_after or {}).items():
            if label not in self.symbols:
                raise ValueError(f"{name}: charge for unknown atom {label!r}")
            self.charges_after[label] = charge
        self.before = self._bonds(before)
        self.after = self._bonds(after)
        self._check_laws()

    def _bonds(self, bonds: Mapping[Pair, int]) -> Dict[Pair, int]:
        out: Dict[Pair, int] = {}
        for pair, order in bonds.items():
            a, b = pair
            if a not in self.symbols or b not in self.symbols or a == b:
                raise ValueError(f"{self.name}: bad bond {pair}")
            if type(order) is not int or order not in (1, 2, 3):
                raise ValueError(f"{self.name}: bond order must be 1, 2 or 3")
            key = (min(a, b), max(a, b))
            if key in out:
                raise ValueError(f"{self.name}: bond {key} listed twice")
            out[key] = order
        return out

    def _check_laws(self) -> None:
        if sum(self.charges_before.values()) != sum(self.charges_after.values()):
            raise ValueError(f"{self.name}: charge is not conserved")
        for label, symbol in self.symbols.items():
            v0 = valence(symbol, self.charges_before[label])
            v1 = valence(symbol, self.charges_after[label])
            if v0 is None or v1 is None:
                raise ValueError(f"{self.name}: atom {label} has a charge "
                                 f"{symbol} can't carry")
            gained = (sum(o for p, o in self.after.items() if label in p)
                      - sum(o for p, o in self.before.items() if label in p))
            if gained != v1 - v0:
                raise ValueError(
                    f"{self.name}: atom {label} ({symbol}) gains {gained} "
                    f"bonds but its valence changes by {v1 - v0}")
        if self.before == self.after and self.charges_before == self.charges_after:
            raise ValueError(f"{self.name}: the rule changes nothing")

    def reverse(self, name: Optional[str] = None) -> "Rule":
        """The same rule run backwards."""
        atoms = {label: symbol + {0: "", 1: "+", -1: "-"}[self.charges_after[label]]
                 for label, symbol in self.symbols.items()}
        return Rule(name or f"reverse of {self.name}", atoms,
                    before=self.after, after=self.before,
                    charges_after=self.charges_before)

    # -- applying a rule --

    def apply(self, *reactants: Molecule) -> List[Tuple[Molecule, ...]]:
        """Every distinct outcome of this rule on these reactants, together.

        The rule's atoms may fall in any of the reactants, but every reactant
        must take part, so `apply(a, b)` is a reaction between a and b, and
        `apply(a)` is a reaction within a. Each outcome is a tuple of product
        molecules, sorted by identity. Outcomes are sorted too, so the result
        doesn't depend on how the reactants' atoms happen to be listed."""
        if not reactants:
            return []
        atoms: List[Atom] = []
        owner: List[int] = []
        bonds: Dict[Tuple[int, int], int] = {}
        for r, molecule in enumerate(reactants):
            offset = len(atoms)
            atoms.extend(molecule.atoms)
            owner.extend([r] * len(molecule.atoms))
            for b in molecule.bonds:
                bonds[(b.a + offset, b.b + offset)] = b.order
        outcomes = {}
        for match in self._matches(atoms, bonds):
            if len({owner[i] for i in match.values()}) != len(reactants):
                continue
            products = self._rewrite(atoms, bonds, match)
            key = tuple(p.identity() for p in products)
            outcomes.setdefault(key, products)
        return [outcomes[k] for k in sorted(outcomes)]

    def _matches(self, atoms: Sequence[Atom],
                 bonds: Mapping[Tuple[int, int], int]) -> Iterator[Dict[str, int]]:
        near: List[Dict[int, int]] = [{} for _ in atoms]
        for (i, j), order in bonds.items():
            near[i][j] = order
            near[j][i] = order
        order_of_labels = self._search_order()
        before = {pair: o for pair, o in self.before.items()}

        def bond(x: str, y: str) -> Optional[int]:
            return before.get((min(x, y), max(x, y)))

        def formed(x: str, y: str) -> bool:
            key = (min(x, y), max(x, y))
            return key in self.after and key not in self.before

        match: Dict[str, int] = {}
        used = set()

        def extend(k: int) -> Iterator[Dict[str, int]]:
            if k == len(order_of_labels):
                yield dict(match)
                return
            label = order_of_labels[k]
            anchor = next((m for m in order_of_labels[:k] if bond(label, m)), None)
            candidates = (near[match[anchor]].keys() if anchor is not None
                          else range(len(atoms)))
            for i in candidates:
                atom = atoms[i]
                if i in used or atom.symbol != self.symbols[label] \
                        or atom.charge != self.charges_before[label]:
                    continue
                fits = True
                for other in order_of_labels[:k]:
                    j = match[other]
                    wanted = bond(label, other)
                    if wanted is not None and near[i].get(j) != wanted:
                        fits = False
                        break
                    if formed(label, other) and j in near[i]:
                        fits = False
                        break
                if not fits:
                    continue
                match[label] = i
                used.add(i)
                yield from extend(k + 1)
                del match[label]
                used.discard(i)

        yield from extend(0)

    def _search_order(self) -> List[str]:
        """Labels in an order where each, where possible, is bonded (before)
        to one already placed, so the search follows bonds."""
        labels = sorted(self.symbols)
        placed: List[str] = []
        while len(placed) < len(labels):
            nxt = next((l for l in labels if l not in placed and any(
                (min(l, p), max(l, p)) in self.before for p in placed)), None)
            if nxt is None:
                nxt = next(l for l in labels if l not in placed)
            placed.append(nxt)
        return placed

    def _rewrite(self, atoms: Sequence[Atom], bonds: Mapping[Tuple[int, int], int],
                 match: Mapping[str, int]) -> Tuple[Molecule, ...]:
        new_atoms = list(atoms)
        for label, i in match.items():
            new_atoms[i] = Atom(atoms[i].symbol, self.charges_after[label])
        new_bonds = dict(bonds)
        for (x, y) in self.before:
            i, j = sorted((match[x], match[y]))
            del new_bonds[(i, j)]
        for (x, y), order in self.after.items():
            i, j = sorted((match[x], match[y]))
            new_bonds[(i, j)] = order
        return tuple(sorted(split(new_atoms, new_bonds), key=Molecule.identity))

    def __repr__(self) -> str:
        return f"Rule({self.name!r})"


def split(atoms: Sequence[Atom], bonds: Mapping[Tuple[int, int], int]) -> List[Molecule]:
    """The separate molecules in a set of atoms and bonds."""
    near: List[List[int]] = [[] for _ in atoms]
    for i, j in bonds:
        near[i].append(j)
        near[j].append(i)
    seen = [False] * len(atoms)
    molecules = []
    for start in range(len(atoms)):
        if seen[start]:
            continue
        group, todo = [], [start]
        seen[start] = True
        while todo:
            i = todo.pop()
            group.append(i)
            for j in near[i]:
                if not seen[j]:
                    seen[j] = True
                    todo.append(j)
        group.sort()
        index = {old: new for new, old in enumerate(group)}
        molecules.append(Molecule(
            [atoms[i] for i in group],
            [Bond(index[i], index[j], o) for (i, j), o in bonds.items() if i in index]))
    return molecules


def balance(reactants: Sequence[Molecule], products: Sequence[Molecule]) -> bool:
    """True if the two sides have the same atoms and the same total charge."""
    def count(side):
        return Counter(a.symbol for m in side for a in m.atoms)
    return (count(reactants) == count(products)
            and sum(m.charge for m in reactants) == sum(m.charge for m in products))

"""Molecules: atoms joined by bonds, with an exact identity.

A molecule's identity is a canonical form of its graph. Two molecules have
the same identity exactly when one can be turned into the other by
relabelling its atoms, however the atoms happen to be listed. The canonical
form is found by colour refinement plus an exhaustive search over the ties
that refinement leaves (individualization and refinement, the standard exact
method). Refinement alone is faster but can give two different molecules the
same identity.

An ordinary hydrogen (neutral, with one single bond to a heavier atom) is
interchangeable with the other hydrogens on that atom, so the search folds
it into its atom's label: element, charge and hydrogen count. Any other
hydrogen (in H2, a lone proton, or a malformed molecule) stays a vertex of
its own, so the identity is exact for every graph, valid or not.

The search prunes by symmetry, as nauty and bliss do, so even very
symmetric molecules need only a few dozen leaves. It also has a cap
(MAX_SEARCH_LEAVES) as a safety net: a graph that still needs more leaves
raises ValueError instead of getting an identity, and so does comparing or
hashing it. No valid molecule tried so far comes near it, but a graph made
of several separate copies of one rigid part can.

Limitation of this layer: resonance forms are different graphs, so they can
get different identities. Formamide drawn neutral (H2N-CH=O) and drawn
charge-separated (H2N+=CH-O-) is one molecule with two identities here. (The
two Kekule structures of benzene itself are the same graph turned by one
atom, so they share an identity.)
"""
from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

from .elements import ELEMENTS, valence

MAX_SEARCH_LEAVES = 10_000


@dataclass(frozen=True)
class Atom:
    symbol: str
    charge: int = 0


@dataclass(frozen=True)
class Bond:
    a: int
    b: int
    order: int = 1


class Molecule:
    """An immutable molecular graph. Constructing one checks its structure
    (indices, bond orders, no repeated bonds); `problems()` checks its
    chemistry (valence, connectedness)."""

    atoms: Tuple[Atom, ...]
    bonds: Tuple[Bond, ...]

    def __init__(self, atoms: Sequence[Atom], bonds: Iterable[Bond]):
        atoms = tuple(atoms)
        object.__setattr__(self, "atoms", atoms)
        if not self.atoms:
            raise ValueError("a molecule needs at least one atom")
        for atom in self.atoms:
            if type(atom) is not Atom or type(atom.symbol) is not str \
                    or type(atom.charge) is not int:
                raise ValueError(f"not an atom: {atom!r}")
            if atom.symbol not in ELEMENTS:
                raise ValueError(f"unknown element: {atom.symbol!r}")
        seen = set()
        cleaned = []
        for bond in bonds:
            if type(bond) is not Bond or not all(
                    type(x) is int for x in (bond.a, bond.b, bond.order)):
                raise ValueError(f"not a bond: {bond!r}")
            a, b = bond.a, bond.b
            if not (0 <= a < len(self.atoms) and 0 <= b < len(self.atoms)):
                raise ValueError(f"bond to a missing atom: {bond}")
            if a == b:
                raise ValueError(f"an atom can't bond to itself: {bond}")
            if bond.order not in (1, 2, 3):
                raise ValueError(f"bond order must be 1, 2 or 3: {bond}")
            key = (min(a, b), max(a, b))
            if key in seen:
                raise ValueError(f"repeated bond between atoms {key}")
            seen.add(key)
            cleaned.append(Bond(key[0], key[1], bond.order))
        object.__setattr__(self, "bonds",
                           tuple(sorted(cleaned, key=lambda x: (x.a, x.b))))
        object.__setattr__(self, "_identity", None)

    def __setattr__(self, name: str, value: object) -> None:
        raise AttributeError("a Molecule can't be changed; build a new one")

    # -- basic properties --

    @property
    def charge(self) -> int:
        return sum(atom.charge for atom in self.atoms)

    @property
    def mass(self) -> float:
        return sum(ELEMENTS[atom.symbol].mass for atom in self.atoms)

    def formula(self) -> str:
        """Hill notation: carbon first, then hydrogen, then the rest in
        alphabetical order; with no carbon, everything alphabetical."""
        counts = Counter(atom.symbol for atom in self.atoms)
        if "C" in counts:
            order = ["C", "H"] + sorted(s for s in counts if s not in ("C", "H"))
        else:
            order = sorted(counts)
        return "".join(s + (str(counts[s]) if counts[s] > 1 else "")
                       for s in order if s in counts)

    def bond_sum(self, i: int) -> int:
        return sum(b.order for b in self.bonds if i in (b.a, b.b))

    def neighbours(self, i: int) -> List[Tuple[int, int]]:
        return [(b.b if b.a == i else b.a, b.order)
                for b in self.bonds if i in (b.a, b.b)]

    # -- chemistry --

    def problems(self) -> List[str]:
        """Everything chemically wrong with this molecule (empty if valid)."""
        found = []
        for i, atom in enumerate(self.atoms):
            v = valence(atom.symbol, atom.charge)
            if v is None:
                found.append(f"atom {i} ({atom.symbol}) can't carry "
                             f"charge {atom.charge:+d}")
            elif self.bond_sum(i) != v:
                found.append(f"atom {i} ({atom.symbol}{_charge_text(atom.charge)}) "
                             f"has {self.bond_sum(i)} bonds, needs {v}")
        if not self._connected():
            found.append("not connected: these are separate molecules")
        return found

    def is_valid(self) -> bool:
        return not self.problems()

    def _connected(self) -> bool:
        seen, todo = {0}, [0]
        while todo:
            i = todo.pop()
            for j, _ in self.neighbours(i):
                if j not in seen:
                    seen.add(j)
                    todo.append(j)
        return len(seen) == len(self.atoms)

    # -- identity --

    def identity(self) -> str:
        """A string that is equal for two molecules exactly when they are the
        same molecule (same atoms, charges and bonds, in any order). Raises
        ValueError if the search reaches its cap (see the module docstring)."""
        if self._identity is None:
            object.__setattr__(self, "_identity", _canonical_form(self))
        return self._identity

    def __eq__(self, other: object) -> bool:
        return isinstance(other, Molecule) and self.identity() == other.identity()

    def __hash__(self) -> int:
        return hash(self.identity())

    def __repr__(self) -> str:
        return f"Molecule({self.formula()}{_charge_text(self.charge)})"


class Builder:
    """Builds a molecule from named atoms:

        Builder().atom("o", "O").hydrogens("o", 2).build()      # water
    """

    def __init__(self):
        self._atoms: List[Atom] = []
        self._names: Dict[str, int] = {}
        self._bonds: List[Bond] = []

    def atom(self, name: str, symbol: str, charge: int = 0) -> "Builder":
        if name in self._names:
            raise ValueError(f"duplicate atom name: {name}")
        self._names[name] = len(self._atoms)
        self._atoms.append(Atom(symbol, charge))
        return self

    def bond(self, a: str, b: str, order: int = 1) -> "Builder":
        for name in (a, b):
            if name not in self._names:
                raise ValueError(f"no atom named {name!r}")
        self._bonds.append(Bond(self._names[a], self._names[b], order))
        return self

    def hydrogens(self, name: str, count: int) -> "Builder":
        for k in range(count):
            h = f"{name}.h{k}"
            self.atom(h, "H").bond(name, h)
        return self

    def build(self, validate: bool = True) -> Molecule:
        molecule = Molecule(self._atoms, self._bonds)
        if validate and molecule.problems():
            raise ValueError("invalid molecule: " + "; ".join(molecule.problems()))
        return molecule


def _charge_text(charge: int) -> str:
    return "" if charge == 0 else ("+" if charge == 1 else "-" if charge == -1
                                   else f"{charge:+d}")


# --- canonical form --------------------------------------------------------

def _canonical_form(m: Molecule, prune: bool = True) -> str:
    n = len(m.atoms)
    around: List[List[Tuple[int, int]]] = [[] for _ in range(n)]
    for b in m.bonds:
        around[b.a].append((b.b, b.order))
        around[b.b].append((b.a, b.order))

    def folded(i: int) -> bool:
        """An ordinary hydrogen, folded into its atom's hydrogen count."""
        atom = m.atoms[i]
        return (atom.symbol == "H" and atom.charge == 0 and len(around[i]) == 1
                and around[i][0][1] == 1
                and m.atoms[around[i][0][0]].symbol != "H")

    # Every folded hydrogen hangs off a heavier atom, so `kept` is never empty.
    kept = [i for i in range(n) if not folded(i)]
    index = {atom: k for k, atom in enumerate(kept)}
    hcount = [0] * len(kept)
    edges: Dict[Tuple[int, int], int] = {}
    for b in m.bonds:
        if b.a in index and b.b in index:
            i, j = index[b.a], index[b.b]
            edges[(min(i, j), max(i, j))] = b.order
        elif b.a in index:
            hcount[index[b.a]] += 1
        else:
            hcount[index[b.b]] += 1
    labels = [(m.atoms[a].symbol, m.atoms[a].charge, hcount[k])
              for k, a in enumerate(kept)]
    adj: List[List[Tuple[int, int]]] = [[] for _ in kept]
    for (i, j), order in edges.items():
        adj[i].append((j, order))
        adj[j].append((i, order))

    def rank(keys: List) -> List[int]:
        order = sorted(set(keys))
        position = {k: r for r, k in enumerate(order)}
        return [position[k] for k in keys]

    def refine(colours: List[int]) -> List[int]:
        while True:
            keys = [(colours[i], tuple(sorted((colours[j], o) for j, o in adj[i])))
                    for i in range(len(colours))]
            new = rank(keys)
            if len(set(new)) == len(set(colours)):
                return new
            colours = new

    def serialize(colours: List[int]) -> Tuple:
        order = sorted(range(len(colours)), key=lambda i: colours[i])
        pos = {v: k for k, v in enumerate(order)}
        atoms = tuple(labels[v] for v in order)
        bonds = tuple(sorted((min(pos[i], pos[j]), max(pos[i], pos[j]), o)
                             for (i, j), o in edges.items()))
        return atoms, bonds

    # The search explores a tree: each node individualizes one vertex of the
    # first tied colour cell and refines; each leaf is a full ordering. The
    # identity is the least leaf. Two prunings skip only subtrees whose
    # leaves are already known, using automorphisms the search discovers
    # (two leaves with the same form differ by an automorphism):
    #
    # - Orbits: at a node with individualized prefix P, a child w can be
    #   skipped if an automorphism fixing P pointwise maps an explored
    #   child to w: its subtree is that child's subtree, relabelled.
    # - Jump back: when a leaf has the same form as the first leaf, the
    #   automorphism between them fixes the prefix they share and maps the
    #   first leaf's branch at the point they diverge onto this leaf's
    #   branch, which was explored first, so the rest of this branch is
    #   known. The search returns to the node where they diverge.
    #
    # These are the prunings nauty and bliss use, in their simplest form.
    n_kept = len(kept)
    best: List[Optional[Tuple]] = [None, None]     # form, order
    first: List[Optional[Tuple]] = [None, None, None]  # form, order, prefix
    generators: List[List[int]] = []
    leaves = [0]

    def ordering(colours: List[int]) -> List[int]:
        return sorted(range(n_kept), key=colours.__getitem__)

    def automorphism(order_a: List[int], order_b: List[int]) -> List[int]:
        g = [0] * n_kept
        for a, b in zip(order_a, order_b):
            g[a] = b
        return g

    def orbit_finder(prefix: List[int]):
        parent = list(range(n_kept))

        def find(x: int) -> int:
            while parent[x] != x:
                parent[x] = parent[parent[x]]
                x = parent[x]
            return x
        for g in generators:
            if all(g[p] == p for p in prefix):
                for x in range(n_kept):
                    rx, ry = find(x), find(g[x])
                    if rx != ry:
                        parent[rx] = ry
        return find

    def search(colours: List[int], prefix: List[int]) -> Optional[int]:
        """Returns None, or the depth the search should return to."""
        counts = Counter(colours)
        tied = [c for c in sorted(counts) if counts[c] > 1]
        if not tied:
            leaves[0] += 1
            if leaves[0] > MAX_SEARCH_LEAVES:
                raise ValueError("molecule too symmetric for an exact identity")
            form, order = serialize(colours), ordering(colours)
            if first[0] is None:
                first[:] = [form, order, list(prefix)]
                best[:] = [form, order]
                return None
            if prune and form == first[0]:
                generators.append(automorphism(first[1], order))
                shared = 0
                limit = min(len(prefix), len(first[2])) - 1
                while shared < limit and prefix[shared] == first[2][shared]:
                    shared += 1
                return shared
            if prune and form == best[0]:
                generators.append(automorphism(best[1], order))
                return None
            if form < best[0]:
                best[:] = [form, order]
            return None
        cell = tied[0]
        depth = len(prefix)
        explored: List[int] = []
        for v in [i for i, c in enumerate(colours) if c == cell]:
            if prune and explored and generators:
                find = orbit_finder(prefix)
                if any(find(v) == find(u) for u in explored):
                    continue
            explored.append(v)
            split = rank([(c, 0 if i == v else 1) if c == cell else (c, 0)
                          for i, c in enumerate(colours)])
            back = search(refine(split), prefix + [v])
            if back is not None and back < depth:
                return back
        return None

    search(refine(rank(labels)), [])
    atoms, bonds = best[0]
    atom_text = ".".join(f"{s}{_charge_text(q)}H{h}" for s, q, h in atoms)
    bond_text = ",".join(f"{i}-{j}:{o}" for i, j, o in bonds)
    return f"{atom_text}|{bond_text}"

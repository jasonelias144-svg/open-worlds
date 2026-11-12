"""The chemistry world of the sketch: reactions that must balance.

From the DeepSeek sketch's component 5. Its point is generality: a law
completely unlike the poetry world's, behind the same protocol, passing
the same conformance test. Agents propose reactions as formulas with
counts; the world accepts a reaction only if atoms and charge balance.

This world checks bookkeeping, not chemistry: any formula with known
elements is accepted, whether or not such a molecule exists. The real
chemistry of open-worlds is in `chem/`. Step 4 of docs/MULTIVERSE.md
moves this world's law onto it.

Changed from the sketch:
  - Calcium is in the element table (the sketch's own test used it).
  - Counts must be whole numbers of at least one, and formulas text. In
    the sketch a count of "2" or -1 was not refused, nor "H0O".
  - A catalyst, if named, must be text. Only each molecule's formula and
    count are recorded; anything else sent with them is not kept.
  - "Equilibrium" in the sketch means only that the last few reactions
    introduced no new molecule; this page says so.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Dict, List, Optional, Set, Tuple

from .entity import Entity, now
from .protocol import Ack, Act, ActResponse, LogEntry

ELEMENTS: Dict[str, Dict] = {
    "H": {"name": "Hydrogen", "atomic_number": 1},
    "C": {"name": "Carbon", "atomic_number": 6},
    "N": {"name": "Nitrogen", "atomic_number": 7},
    "O": {"name": "Oxygen", "atomic_number": 8},
    "Na": {"name": "Sodium", "atomic_number": 11},
    "P": {"name": "Phosphorus", "atomic_number": 15},
    "S": {"name": "Sulfur", "atomic_number": 16},
    "Cl": {"name": "Chlorine", "atomic_number": 17},
    "Ca": {"name": "Calcium", "atomic_number": 20},
}


@dataclass(frozen=True)
class Molecule:
    formula: str
    atoms: Dict[str, int]
    charge: int = 0

    def __post_init__(self):
        if not self.formula:
            raise ValueError("Molecule formula must be non-empty")


def parse_formula(formula: str) -> Molecule:
    """'H2O' gives H:2, O:1. A charge suffix: 'NH4+' is +1, 'SO4-2' is
    -2, 'OH-' is -1. Unknown elements and unreadable text raise
    ValueError."""
    if type(formula) is not str or not formula:
        raise ValueError("a formula must be non-empty text")
    original = formula
    charge = 0
    m = re.search(r"([+-])(\d*)$", formula)
    if m:
        sign = 1 if m.group(1) == "+" else -1
        charge = sign * (int(m.group(2)) if m.group(2) else 1)
        formula = formula[:m.start()]
    atoms: Dict[str, int] = {}
    pos = 0
    while pos < len(formula):
        m = re.match(r"([A-Z][a-z]?)(\d*)", formula[pos:])
        if not m:
            raise ValueError(
                f"Cannot parse formula at position {pos}: {original}")
        element = m.group(1)
        if element not in ELEMENTS:
            raise ValueError(f"Unknown element: {element}")
        count = int(m.group(2)) if m.group(2) else 1
        if count < 1:
            raise ValueError(f"A count of zero in formula: {original}")
        atoms[element] = atoms.get(element, 0) + count
        pos += m.end()
    if not atoms:
        raise ValueError(f"No atoms in formula: {original}")
    return Molecule(formula=original, atoms=atoms, charge=charge)


def _side(molecules: List[Dict]) -> Tuple[Dict[str, int], int]:
    atoms: Dict[str, int] = {}
    charge = 0
    for mol in molecules:
        if type(mol) is not dict:
            raise ValueError("each molecule must be {formula, count}")
        count = mol["count"]
        if type(count) is not int or count < 1:
            raise ValueError(f"count must be a whole number of at least "
                             f"1: {count!r}")
        parsed = parse_formula(mol["formula"])
        for element, n in parsed.atoms.items():
            atoms[element] = atoms.get(element, 0) + n * count
        charge += parsed.charge * count
    return atoms, charge


def reaction_balances(substrates: List[Dict],
                      products: List[Dict]) -> Tuple[bool, str]:
    """Do atoms and charge balance? Each side is a list of
    {"formula": str, "count": int}. Returns (balances, reason)."""
    try:
        left_atoms, left_charge = _side(substrates)
        right_atoms, right_charge = _side(products)
    except (KeyError, TypeError, ValueError) as e:
        return False, f"Formula error: {e}"
    if left_atoms != right_atoms:
        diff = {e: left_atoms.get(e, 0) - right_atoms.get(e, 0)
                for e in set(left_atoms) | set(right_atoms)
                if left_atoms.get(e, 0) != right_atoms.get(e, 0)}
        return False, f"Atom imbalance: {diff}"
    if left_charge != right_charge:
        return False, (f"Charge imbalance: {left_charge} on left, "
                       f"{right_charge} on right")
    return True, "balanced"


@dataclass(frozen=True)
class ChemistryWorldLaw:
    admits_any_identity: bool = True
    max_admitted: Optional[int] = None
    required_act_type: str = "chemistry.react"
    convergence_window: int = 4
    max_reactions: int = 500

    def describe(self) -> str:
        return "\n".join([
            "# Chemistry World Law v0.1",
            "",
            "## Entering and leaving",
            f"- Admits any identity: {self.admits_any_identity}",
            "- Max present: "
            f"{self.max_admitted if self.max_admitted else 'unlimited'}",
            "- Anyone may leave at any time.",
            "",
            "## A reaction (chemistry.react)",
            f"- Act type: {self.required_act_type}",
            "- Substrates and products: lists of {formula, count}",
            "- Accepted only if atoms and charge balance",
            "",
            "## Settling",
            f"- Settled when the last {self.convergence_window} reactions "
            "introduced no molecule not seen before",
            f"- At most {self.max_reactions} reactions",
            "",
            "## Limits",
            "- Petitions and acts are not signed yet (WCP/0.1).",
            "- Formulas are checked for balance, not for whether such a "
            "molecule exists.",
        ])


class ChemistryWorld(Entity):
    scheme = "chemistry"

    def __init__(self, entity_id: str, name: str,
                 law: Optional[ChemistryWorldLaw] = None):
        super().__init__(entity_id, name, law or ChemistryWorldLaw())
        self._reactions: List[Dict] = []
        self._molecules: Set[str] = set()
        self._converged = False
        self._convergence_reason: Optional[str] = None

    def act(self, act: Act) -> ActResponse:
        timestamp = now()
        refusal = self._actor_problem(timestamp, act)
        if refusal:
            return refusal
        actor = act.actor_token
        if self._converged:
            return self._refuse(timestamp, actor,
                                "The World has reached equilibrium", "act")
        if len(self._reactions) >= self._law.max_reactions:
            return self._refuse(timestamp, actor,
                                "Reaction limit reached", "act")
        if act.type != self._law.required_act_type:
            return self._refuse(timestamp, actor,
                                f"Unknown act type: {act.type}", "act")
        substrates = act.payload.get("substrates")
        products = act.payload.get("products")
        if (type(substrates) is not list or type(products) is not list
                or not substrates or not products):
            return self._refuse(timestamp, actor,
                                "Substrates and products required", "act")
        catalyst = act.payload.get("catalyst")
        if catalyst is not None and type(catalyst) is not str:
            return self._refuse(timestamp, actor,
                                "The catalyst must be text", "act")
        balances, reason = reaction_balances(substrates, products)
        if not balances:
            return self._refuse(timestamp, actor,
                                f"Reaction does not balance: {reason}", "act")

        reaction = {
            "reaction_index": len(self._reactions),
            "actor_token": actor,
            "actor_name": self._passports[actor].identity.name,
            "substrates": [{"formula": m["formula"], "count": m["count"]}
                           for m in substrates],
            "products": [{"formula": m["formula"], "count": m["count"]}
                         for m in products],
            "catalyst": catalyst,
            "timestamp": timestamp,
        }
        self._reactions.append(reaction)
        for mol in substrates + products:
            self._molecules.add(mol["formula"])
        self._log.append(LogEntry(timestamp=timestamp, kind="reaction",
                                  actor_token=actor, data=dict(reaction)))
        if self._check_equilibrium():
            self._converged = True
            self._log.append(LogEntry(
                timestamp=timestamp, kind="convergence",
                data={"reaction_count": len(self._reactions),
                      "window": self._law.convergence_window,
                      "reason": self._convergence_reason}))
        return Ack(entity_id=self._manifest.entity_id, timestamp=timestamp)

    # -- conveniences ---------------------------------------------------

    def reactions(self) -> List[Dict]:
        return [dict(r) for r in self._reactions]

    def molecules(self) -> Set[str]:
        return set(self._molecules)

    def is_converged(self) -> bool:
        return self._converged

    def describe(self) -> str:
        return "\n".join([
            f"ChemistryWorld: {self._manifest.name}",
            f"  entity_id: {self._manifest.entity_id}",
            f"  present:   {len(self._admitted)}",
            f"  reactions: {len(self._reactions)}",
            f"  molecules: {len(self._molecules)}",
            f"  converged: {self._converged}",
        ])

    def _check_equilibrium(self) -> bool:
        window = self._law.convergence_window
        if len(self._reactions) < window + 1:
            return False
        split = len(self._reactions) - window

        def formulas(reactions):
            return {m["formula"] for r in reactions
                    for m in r["substrates"] + r["products"]}

        if formulas(self._reactions[split:]) <= formulas(
                self._reactions[:split]):
            self._convergence_reason = (
                f"the last {window} reactions introduced no new molecules")
            return True
        return False


def reactions_from_log(log: List[LogEntry]) -> List[Dict]:
    return [dict(entry.data) for entry in log if entry.kind == "reaction"]

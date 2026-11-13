"""
multiverse_c5.py — Component 5: The Chemistry World.

The second real WCP-conforming world. It implements the chemistry
framework's conservation laws as its Law.

The proof of generality: a second world with a completely different
Law, passing the same conformance test, without any changes to the
WCP protocol.

Depends on Components 1, 2, 3.
"""

import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple, Union

from multiverse_c1 import Identity
from multiverse_c2 import Passport, Admission as PassportAdmission
from multiverse_c3 import (
    Manifest, Petition, Act, LogEntry,
    Admission as WCPAdmission, Refusal, Route, Ack,
)


# =====================================================================
# The chemistry atom: element table
# =====================================================================

ELEMENTS: Dict[str, Dict] = {
    "H": {"name": "Hydrogen", "atomic_number": 1},
    "C": {"name": "Carbon", "atomic_number": 6},
    "N": {"name": "Nitrogen", "atomic_number": 7},
    "O": {"name": "Oxygen", "atomic_number": 8},
    "Na": {"name": "Sodium", "atomic_number": 11},
    "P": {"name": "Phosphorus", "atomic_number": 15},
    "S": {"name": "Sulfur", "atomic_number": 16},
    "Cl": {"name": "Chlorine", "atomic_number": 17},
}


# =====================================================================
# The chemistry composite: molecule parsing
# =====================================================================

@dataclass(frozen=True)
class Molecule:
    formula: str
    atoms: Dict[str, int]
    charge: int = 0

    def __post_init__(self):
        if not self.formula:
            raise ValueError("Molecule formula must be non-empty")


def parse_formula(formula: str) -> Molecule:
    """Parse a chemical formula like 'H2O' or 'NH4+' into a Molecule.

    Handles:
      - element counts ('H2O' → H:2, O:1)
      - charge suffixes ('NH4+' → +1, 'SO4-2' → -2, 'OH-' → -1)
    Raises ValueError on unknown elements or malformed formulas.
    """
    original = formula
    charge = 0
    m = re.search(r"([+-])(\d*)$", formula)
    if m:
        sign = 1 if m.group(1) == "+" else -1
        magnitude = int(m.group(2)) if m.group(2) else 1
        charge = sign * magnitude
        formula = formula[:m.start()]

    atoms: Dict[str, int] = {}
    pos = 0
    while pos < len(formula):
        m = re.match(r"([A-Z][a-z]?)(\d*)", formula[pos:])
        if not m:
            raise ValueError(
                f"Cannot parse formula at position {pos}: {original}"
            )
        element = m.group(1)
        count = int(m.group(2)) if m.group(2) else 1
        if element not in ELEMENTS:
            raise ValueError(f"Unknown element: {element}")
        atoms[element] = atoms.get(element, 0) + count
        pos += m.end()

    return Molecule(formula=original, atoms=atoms, charge=charge)


def reaction_balances(
    substrates: List[Dict], products: List[Dict]
) -> Tuple[bool, str]:
    """Check atom balance and charge balance.

    `substrates` and `products` are lists of {formula, count} dicts.
    Returns (balances, reason).
    """
    left_atoms: Dict[str, int] = {}
    right_atoms: Dict[str, int] = {}
    left_charge = 0
    right_charge = 0

    try:
        for mol in substrates:
            parsed = parse_formula(mol["formula"])
            count = mol["count"]
            for elem, n in parsed.atoms.items():
                left_atoms[elem] = left_atoms.get(elem, 0) + n * count
            left_charge += parsed.charge * count
        for mol in products:
            parsed = parse_formula(mol["formula"])
            count = mol["count"]
            for elem, n in parsed.atoms.items():
                right_atoms[elem] = right_atoms.get(elem, 0) + n * count
            right_charge += parsed.charge * count
    except (KeyError, ValueError) as e:
        return False, f"Formula error: {e}"

    if left_atoms != right_atoms:
        diff = {}
        for elem in set(left_atoms) | set(right_atoms):
            d = left_atoms.get(elem, 0) - right_atoms.get(elem, 0)
            if d != 0:
                diff[elem] = d
        return False, f"Atom imbalance: {diff}"

    if left_charge != right_charge:
        return False, (
            f"Charge imbalance: {left_charge} on left, "
            f"{right_charge} on right"
        )

    return True, "balanced"


# =====================================================================
# The Law
# =====================================================================

@dataclass(frozen=True)
class ChemistryWorldLaw:
    """The published Law of the Chemistry World."""
    admits_any_identity: bool = True
    max_admitted: Optional[int] = None
    required_act_type: str = "chemistry.react"
    convergence_window: int = 4
    max_reactions: int = 500

    def describe(self) -> str:
        return "\n".join([
            "# Chemistry World Law v0.1",
            "",
            "## Petition",
            f"- Admits any identity: {self.admits_any_identity}",
            f"- Max admitted: "
            f"{self.max_admitted if self.max_admitted else 'unlimited'}",
            "",
            "## Act (chemistry.react)",
            f"- Required act type: {self.required_act_type}",
            "- Validates: atom conservation, charge conservation",
            "- Substrates and products must be {formula, count} dicts.",
            "",
            "## Convergence",
            f"- Window: last {self.convergence_window} reactions",
            "- Condition: window introduces no new molecules",
            "  (chemical equilibrium)",
            f"- Max reactions: {self.max_reactions}",
            "",
            "## Limits",
            "- Petitions are not signed (WCP/0.1).",
            "- Sub-registries are not enumerable (WCP/0.1).",
        ])


# =====================================================================
# The World
# =====================================================================

class ChemistryWorld:
    """A WCP-conforming chemistry world.

    Same protocol as Poetry World: manifest, petition, act, log_since.
    Different Law: conservation of atoms, conservation of charge,
    convergence at chemical equilibrium.
    """

    def __init__(self, entity_id: str, name: str,
                 law: Optional[ChemistryWorldLaw] = None):
        self._law = law or ChemistryWorldLaw()
        self._manifest = Manifest(
            entity_id=entity_id,
            name=name,
            protocol_version="WCP/0.1",
            law_url=f"chemistry://{entity_id}/law",
            act_endpoint=f"chemistry://{entity_id}/act",
            log_endpoint=f"chemistry://{entity_id}/log",
        )
        self._log: List[LogEntry] = []
        self._admitted: Dict[str, WCPAdmission] = {}
        self._passports: Dict[str, Passport] = {}
        self._reactions: List[Dict] = []
        self._molecules: set = set()
        self._converged = False
        self._convergence_reason: Optional[str] = None

    def manifest(self) -> Manifest:
        return self._manifest

    def petition(self, petition: Petition) -> Union[
            WCPAdmission, Refusal, Route]:
        # Same structure as Poetry World — because petition is not
        # Law-specific, only its checks are.
        timestamp = datetime.now(timezone.utc).isoformat()

        if not self._law.admits_any_identity:
            return self._refuse(
                timestamp, petition.petitioner_token,
                "This World does not admit strangers", "petition")
        if (self._law.max_admitted is not None
                and len(self._admitted) >= self._law.max_admitted):
            return self._refuse(
                timestamp, petition.petitioner_token,
                "The World is full", "petition")
        if petition.petitioner_token in self._admitted:
            return self._refuse(
                timestamp, petition.petitioner_token,
                "Already admitted", "petition")

        admission = WCPAdmission(
            entity_id=self._manifest.entity_id,
            timestamp=timestamp,
        )
        self._admitted[petition.petitioner_token] = admission

        passport = Passport(
            identity=Identity(
                token=petition.petitioner_token,
                name=petition.petitioner_name,
            ),
            admissions=tuple(
                PassportAdmission(world_id=w, timestamp=t)
                for w, t in petition.passport_admissions
            ),
        )
        passport = passport.with_admission(PassportAdmission(
            world_id=self._manifest.entity_id,
            timestamp=timestamp,
        ))
        self._passports[petition.petitioner_token] = passport

        self._log.append(LogEntry(
            timestamp=timestamp, kind="admission",
            actor_token=petition.petitioner_token,
            data={"name": petition.petitioner_name},
        ))
        return admission

    def act(self, act: Act) -> Union[Ack, Refusal]:
        timestamp = datetime.now(timezone.utc).isoformat()

        if act.actor_token not in self._admitted:
            return self._refuse(timestamp, act.actor_token,
                                 "Actor is not admitted", "act")
        if self._converged:
            return self._refuse(timestamp, act.actor_token,
                                 "The World has reached equilibrium",
                                 "act")
        if len(self._reactions) >= self._law.max_reactions:
            return self._refuse(timestamp, act.actor_token,
                                 "Reaction limit reached", "act")
        if act.type != self._law.required_act_type:
            return self._refuse(timestamp, act.actor_token,
                                 f"Unknown act type: {act.type}", "act")

        payload = act.payload
        substrates = payload.get("substrates", [])
        products = payload.get("products", [])

        if not substrates or not products:
            return self._refuse(timestamp, act.actor_token,
                                 "Substrates and products required",
                                 "act")

        balances, reason = reaction_balances(substrates, products)
        if not balances:
            return self._refuse(timestamp, act.actor_token,
                                 f"Reaction does not balance: {reason}",
                                 "act")

        reaction = {
            "reaction_index": len(self._reactions),
            "actor_token": act.actor_token,
            "actor_name": self._passports[act.actor_token].identity.name,
            "substrates": substrates,
            "products": products,
            "catalyst": payload.get("catalyst"),
            "timestamp": timestamp,
        }
        self._reactions.append(reaction)

        for mol in substrates + products:
            self._molecules.add(mol["formula"])

        self._log.append(LogEntry(
            timestamp=timestamp, kind="reaction",
            actor_token=act.actor_token, data=reaction,
        ))

        if self._check_equilibrium():
            self._converged = True
            self._log.append(LogEntry(
                timestamp=timestamp, kind="convergence",
                data={
                    "reaction_count": len(self._reactions),
                    "window": self._law.convergence_window,
                    "reason": self._convergence_reason,
                },
            ))

        return Ack(entity_id=self._manifest.entity_id,
                   timestamp=timestamp)

    def log_since(self, timestamp: Optional[str] = None) -> List[LogEntry]:
        if timestamp is None:
            return list(self._log)
        return [e for e in self._log if e.timestamp > timestamp]

    # -- convenience -----------------------------------------------

    def reactions(self) -> List[Dict]:
        return list(self._reactions)

    def molecules(self) -> set:
        return set(self._molecules)

    def is_converged(self) -> bool:
        return self._converged

    def law(self) -> ChemistryWorldLaw:
        return self._law

    def describe(self) -> str:
        return "\n".join([
            f"ChemistryWorld: {self._manifest.name}",
            f"  entity_id: {self._manifest.entity_id}",
            f"  admitted:  {len(self._admitted)}",
            f"  reactions: {len(self._reactions)}",
            f"  molecules: {len(self._molecules)}",
            f"  converged: {self._converged}",
        ])

    # -- internals -------------------------------------------------

    def _check_equilibrium(self) -> bool:
        window = self._law.convergence_window
        if len(self._reactions) < window + 1:
            return False

        split = len(self._reactions) - window
        historical: set = set()
        for r in self._reactions[:split]:
            for mol in r["substrates"] + r["products"]:
                historical.add(mol["formula"])

        window_molecules: set = set()
        for r in self._reactions[split:]:
            for mol in r["substrates"] + r["products"]:
                window_molecules.add(mol["formula"])

        if window_molecules <= historical:
            self._convergence_reason = (
                f"last {window} reactions introduced no new molecules "
                f"(chemical equilibrium)"
            )
            return True
        return False

    def _refuse(self, timestamp: str, actor: str, reason: str,
                 kind: str) -> Refusal:
        self._log.append(LogEntry(
            timestamp=timestamp, kind=f"{kind}_refused",
            actor_token=actor, data={"reason": reason},
        ))
        return Refusal(reason=reason)


def reactions_from_log(log: List[LogEntry]) -> List[Dict]:
    """Reconstruct reaction history from a Chemistry World's log."""
    return [entry.data for entry in log if entry.kind == "reaction"]

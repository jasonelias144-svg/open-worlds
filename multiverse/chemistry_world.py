"""The chemistry world: real molecules, real reactions, a soup in time.

From the DeepSeek sketch's component 5, rebuilt on open-worlds' own
chemistry (`chem/`) in course step 4. The sketch's world accepted any
reaction whose formulas balanced, whether or not such molecules existed.
This one holds a soup of real molecules (`chem.soup.Soup`, one well-mixed
cell for now), and an act is a real reaction among molecules that are
there:

- **chemistry.react** names one of the reaction rules of `chem/rules.py`
  (proton transfers, amide formation and hydrolysis, carbonyl hydration,
  cyanohydrin formation, and their reverses) and the molecules it acts
  on. The world applies the rule; if it applies, and every reactant is in
  the soup, the reaction happens there, at once. An individual acts as a
  catalyst would: it makes a reaction happen, with atoms the soup already
  has. Nobody brings matter in or takes it out.

Between acts the soup runs on its own: each accepted act lets it run for
a published number of seconds of world time, in which its own reactions
happen at their rates, by exact stochastic simulation from a published
seed. So the world replays exactly. Its rates are placeholders, said so
in its law: real rates, with their sources, are course step 8.

Molecules are named by their catalogue name (`chem/catalogue.py`, such as
"glycine") or by their identity, the exact canonical form a world uses
for every molecule (`Molecule.identity()`); `census()` and the log give
the identity of everything in the soup.

Changed from the sketch:
  - Real molecules and reactions instead of formulas that only balance.
  - Nothing ends the world. The sketch called it "equilibrium" when the
    last few reactions introduced no new molecule; real chemistry keeps
    going, and the soup's own reactions settle into real equilibria.
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

from chem import catalogue
from chem.molecule import Molecule
from chem.rules import RULES
from chem.soup import Soup

from .entity import (SIGNED_REQUESTS_LAW, STAMPS_LAW, UNSIGNED_ANSWERS_LIMIT,
                     Entity)
from .identity import Signer
from .protocol import Ack, Act, ActResponse, LogEntry

ACT_TYPE = "chemistry.react"
#: What a reaction's record is (schemas/chemistry-made-v1.schema.json):
#: its world time is a whole number of microseconds, so the record keeps
#: the project's rules for signed records (docs/research/FORMATS.md).
MADE_FORMAT = "open-worlds/chemistry-made/v1"
CELL = (0, 0)
MAX_REACTANTS = 3
MAX_NAME = 10_000

# The soil: what the world starts with, by catalogue name.
SOIL: Tuple[Tuple[str, int], ...] = (
    ("water", 100), ("glycine", 20), ("formaldehyde", 10))

# The world's own reactions: (rule, reactants by catalogue name, forward
# rate, reverse rate). The reverse runs the same reaction backwards.
# PLACEHOLDER rates, chosen so that both directions happen often enough to
# watch; not measured (course step 8).
OWN_REACTIONS: Tuple[Tuple[str, Tuple[str, ...], float, float], ...] = (
    ("proton transfer, carboxylic acid to amine", ("glycine",), 4.0, 1.0),
    ("hydration of a carbonyl", ("formaldehyde", "water"), 0.5, 0.2),
)


@dataclass(frozen=True)
class ChemistryWorldLaw:
    admits_any_identity: bool = True
    max_admitted: Optional[int] = None
    seconds_per_act: float = 1.0
    seed: int = 0
    volume: float = 10.0
    soil: Tuple[Tuple[str, int], ...] = SOIL
    own_reactions: Tuple[Tuple[str, Tuple[str, ...], float, float],
                         ...] = OWN_REACTIONS

    def __post_init__(self):
        t = self.seconds_per_act
        if type(t) not in (int, float) or not math.isfinite(t) or t < 0:
            raise ValueError("seconds_per_act must be a finite number >= 0")
        for rule, names, forward, reverse in self.own_reactions:
            if rule not in RULES:
                raise ValueError(f"no rule {rule!r}")
        for name, count in self.soil:
            if name not in catalogue.CATALOGUE:
                raise ValueError(f"{name!r} is not in the catalogue")

    def describe(self) -> str:
        lines = [
            "# Chemistry World Law v0.5",
            "",
            "## Entering and leaving",
            f"- Admits any identity: {self.admits_any_identity}",
            "- Max present: "
            f"{self.max_admitted if self.max_admitted else 'unlimited'}",
            "- Anyone may leave at any time.",
            SIGNED_REQUESTS_LAW,
            STAMPS_LAW,
            "",
            "## The soup",
            "- One well-mixed cell of volume "
            f"{self.volume}, run by exact stochastic simulation from "
            f"seed {self.seed}, so it replays exactly.",
            "- It starts with: " + ", ".join(
                f"{n} {name}" for name, n in self.soil) + ".",
            "- Nothing is brought in or taken out: every reaction keeps "
            "every atom and the total charge.",
            "",
            "## Time",
            f"- Each accepted act lets the soup run for "
            f"{self.seconds_per_act} seconds of world time. World time is "
            "simulated: it doesn't follow the clock.",
            "- A reaction's record gives its world time in whole "
            "microseconds (`world_time_us`), rounded to the nearest.",
            "",
            "## The soup's own reactions (rates per second)",
        ]
        for rule, reactants, forward, reverse in self.own_reactions:
            lines.append(f"- {rule}, on {' + '.join(reactants)}: "
                         f"{forward} forward, {reverse} back")
        lines += [
            "- Rates follow mass action, counting ordered picks of the "
            "reactants, divided by the volume once for each reactant "
            "beyond the first (docs/CHEMISTRY.md, rate convention).",
            "- These rates are placeholders, not measurements. Real rates,",
            "  with their sources, come later (course step 8).",
            "",
            f"## A reaction ({ACT_TYPE})",
            "- Name a rule and the molecules it acts on (by catalogue "
            "name or identity). If the rule applies and every molecule is "
            "in the soup, the reaction happens there at once.",
            "- If the rule can act on them in more than one way, choose "
            "which with `outcome` (from 0; the outcomes are sorted).",
            "- The rules: " + "; ".join(RULES) + ".",
            "",
            "## Limits",
            UNSIGNED_ANSWERS_LIMIT,
            "- The rules are local: they apply wherever their atoms match, "
            "even where real chemistry would be too slow to matter.",
        ]
        return "\n".join(lines)


def microseconds(seconds: float) -> int:
    """World time in whole microseconds, the unit a reaction's record
    gives it in: the nearest, ties to even, as Python rounds."""
    return round(seconds * 1_000_000)


def _molecule(name: str) -> Molecule:
    if name not in catalogue.CATALOGUE:
        raise ValueError(f"{name!r} is not in the catalogue")
    return catalogue.CATALOGUE[name]()


class ChemistryWorld(Entity):
    scheme = "chemistry"

    def __init__(self, entity_id: str, name: str,
                 law: Optional[ChemistryWorldLaw] = None, *,
                 key: Optional[Signer] = None):
        law = law or ChemistryWorldLaw()
        super().__init__(entity_id, name, law, key=key)
        self._soup = Soup(1, 1, volume=law.volume, seed=law.seed)
        # Catalogue name -> identity, so an act may name any catalogue
        # molecule the soup has, whether it began there or was made.
        self._names: Dict[str, str] = {
            n: f().identity() for n, f in catalogue.CATALOGUE.items()}
        for rule, names, forward, reverse in law.own_reactions:
            reactants = [_molecule(n) for n in names]
            outcomes = RULES[rule].apply(*reactants)
            if len(outcomes) != 1:
                raise ValueError(f"{rule} on {names} must have one outcome")
            self._soup.add_reaction(reactants, list(outcomes[0]), forward)
            self._soup.add_reaction(list(outcomes[0]), reactants, reverse)
        for soil_name, count in law.soil:
            m = _molecule(soil_name)
            self._soup.add_species(m)
            self._soup.put(CELL, m, count)
        self._reactions: List[Dict] = []
        self._log.append(LogEntry(timestamp=self._now(), kind="soil",
                                  data={"census": self.census(),
                                        "soup_head": self._soup.log_head}))

    def act(self, act: Act) -> ActResponse:
        timestamp = self._now()
        refusal = self._actor_problem(timestamp, act)
        if refusal:
            return refusal
        actor = act.actor_token
        if act.type != ACT_TYPE:
            return self._refuse(timestamp, actor,
                                f"Unknown act type: {act.type}", "act")
        rule = act.payload.get("rule")
        if type(rule) is not str or rule not in RULES:
            return self._refuse(timestamp, actor,
                                "rule must name one of this world's rules",
                                "act")
        named = act.payload.get("reactants")
        if (type(named) is not list or not 1 <= len(named) <= MAX_REACTANTS
                or any(type(n) is not str or not n or len(n) > MAX_NAME
                       for n in named)):
            return self._refuse(timestamp, actor,
                                f"reactants must be a list of 1 to "
                                f"{MAX_REACTANTS} molecule names or "
                                "identities", "act")
        outcome = act.payload.get("outcome", 0)
        if type(outcome) is not int or outcome < 0:
            return self._refuse(timestamp, actor,
                                "outcome must be a whole number from 0",
                                "act")
        species = {m.identity(): m for m in self._soup.species}
        reactants = []
        for n in named:
            m = species.get(self._names.get(n, n))
            if m is None:
                return self._refuse(timestamp, actor,
                                    f"No molecule {n[:60]!r} is in this "
                                    "world", "act")
            reactants.append(m)
        outcomes = RULES[rule].apply(*reactants)
        if not outcomes:
            return self._refuse(timestamp, actor,
                                f"The rule {rule!r} doesn't apply to these "
                                "molecules", "act")
        if outcome >= len(outcomes):
            return self._refuse(timestamp, actor,
                                f"outcome must be from 0 to "
                                f"{len(outcomes) - 1}", "act")
        products = list(outcomes[outcome])
        if not self._soup.perform(CELL, reactants, products):
            return self._refuse(timestamp, actor,
                                "Not every reactant is in the soup now, as "
                                "many as the reaction uses", "act")
        reaction = {
            "format": MADE_FORMAT,
            "rule": rule,
            "reactants": [m.identity() for m in reactants],
            "products": [m.identity() for m in products],
            "formulas": [[m.formula() for m in reactants],
                         [m.formula() for m in products]],
            "world_time_us": microseconds(self._soup.time),
        }
        self._reactions.append(reaction)
        self._soup.advance(self._soup.time + self._law.seconds_per_act)
        self._log.append(LogEntry(
            timestamp=timestamp, kind="reaction", actor_token=actor,
            data=dict(reaction, soup_time=self._soup.time,
                      soup_head=self._soup.log_head)))
        return Ack(entity_id=self._manifest.entity_id, timestamp=timestamp,
                   stamp=self._made(actor, timestamp, reaction))

    # -- conveniences ---------------------------------------------------

    def census(self) -> Dict[str, Dict]:
        """Every kind of molecule the soup has had, by identity: its
        formula and how many there are now."""
        return {m.identity(): {"formula": m.formula(),
                               "count": self._soup.count(m)}
                for m in self._soup.species}

    def identity_of(self, name: str) -> str:
        """The identity of a catalogue molecule, as acts may name it."""
        return _molecule(name).identity()

    @property
    def world_time(self) -> float:
        return self._soup.time

    @property
    def soup(self) -> Soup:
        """The soup itself, for reading (its log, its atoms). Changing it
        directly bypasses this world's law."""
        return self._soup

    def reactions(self) -> List[Dict]:
        return [dict(r) for r in self._reactions]

    def describe(self) -> str:
        present = sum(1 for v in self.census().values() if v["count"])
        return "\n".join([
            f"ChemistryWorld: {self._manifest.name}",
            f"  entity_id:  {self._manifest.entity_id}",
            f"  present:    {len(self._admitted)}",
            f"  reactions:  {len(self._reactions)} by acts",
            f"  molecules:  {present} kinds in the soup",
            f"  world time: {self._soup.time:.3f} s",
        ])


def reactions_from_log(log: List[LogEntry]) -> List[Dict]:
    return [dict(entry.data) for entry in log if entry.kind == "reaction"]

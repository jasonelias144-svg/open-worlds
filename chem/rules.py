"""Real reactions, written as rules.

Each rule is a real reaction type, with an example from real chemistry. The
rules are local: they look only at the atoms they name. So they also apply
where real chemistry would be too slow or too unfavourable to matter. One
example is protonating an amide's nitrogen, which is far less basic than an
amine's. Which reactions actually go, and how fast, is for layer 3 (energy
and rates) to decide.
"""
from __future__ import annotations

from typing import Dict

from .reactions import Rule

# An acid gives its proton to an amine: R-COOH + R'-NH2 -> R-COO- + R'-NH3+.
# Within one glycine, this makes the zwitterion, glycine's form in water.
ACID_TO_AMINE = Rule(
    "proton transfer, carboxylic acid to amine",
    atoms={"c": "C", "o1": "O", "o2": "O", "h": "H", "n": "N"},
    before={("c", "o1"): 2, ("c", "o2"): 1, ("o2", "h"): 1},
    after={("c", "o1"): 2, ("c", "o2"): 1, ("n", "h"): 1},
    charges_after={"o2": -1, "n": +1},
)

# Water's self-ionization: H2O + H2O -> H3O+ + OH-. Written for any O-H
# giving its proton to a neutral oxygen.
O_H_TO_O = Rule(
    "proton transfer, O-H to oxygen",
    atoms={"o1": "O", "h": "H", "o2": "O"},
    before={("o1", "h"): 1},
    after={("o2", "h"): 1},
    charges_after={"o1": -1, "o2": +1},
)

# Condensation to an amide (the peptide bond), releasing water:
# R-COOH + H2N-R' -> R-CO-NH-R' + H2O.
AMIDE_FORMATION = Rule(
    "amide formation (condensation)",
    atoms={"c": "C", "o1": "O", "o2": "O", "h": "H", "n": "N", "hn": "H"},
    before={("c", "o1"): 2, ("c", "o2"): 1, ("o2", "h"): 1, ("n", "hn"): 1},
    after={("c", "o1"): 2, ("c", "n"): 1, ("o2", "h"): 1, ("o2", "hn"): 1},
)

# Its reverse: water splits an amide back into acid and amine.
AMIDE_HYDROLYSIS = AMIDE_FORMATION.reverse("amide hydrolysis")

# Water adds across a C=O: formaldehyde + water -> methanediol,
# CO2 + water -> carbonic acid.
CARBONYL_HYDRATION = Rule(
    "hydration of a carbonyl",
    atoms={"c": "C", "o": "O", "ow": "O", "h": "H"},
    before={("c", "o"): 2, ("ow", "h"): 1},
    after={("c", "o"): 1, ("o", "h"): 1, ("c", "ow"): 1},
)

# Hydrogen cyanide adds across a C=O: formaldehyde + HCN -> glycolonitrile,
# a step on the route from prebiotic HCN chemistry toward amino acids.
CYANOHYDRIN_FORMATION = Rule(
    "cyanohydrin formation",
    atoms={"c": "C", "o": "O", "cn": "C", "n": "N", "h": "H"},
    before={("c", "o"): 2, ("cn", "n"): 3, ("cn", "h"): 1},
    after={("c", "o"): 1, ("o", "h"): 1, ("c", "cn"): 1, ("cn", "n"): 3},
)

RULES: Dict[str, Rule] = {
    rule.name: rule for rule in [
        ACID_TO_AMINE, ACID_TO_AMINE.reverse(),
        O_H_TO_O, O_H_TO_O.reverse(),
        AMIDE_FORMATION, AMIDE_HYDROLYSIS,
        CARBONYL_HYDRATION, CARBONYL_HYDRATION.reverse("dehydration of a gem-diol"),
        CYANOHYDRIN_FORMATION, CYANOHYDRIN_FORMATION.reverse(),
    ]
}

"""Elements, and the valence rule of the first chemistry layer.

Real elements, simplified rules. Every atom is explicit, hydrogens included,
and the bond orders on an atom must add up exactly to its valence. Valence
depends on formal charge the way it does in real chemistry:

  N, O    more than four valence electrons: valence = base + charge
          (ammonium N+ has 4 bonds, hydroxide O- has 1, hydronium O+ has 3)
  C       valence = 4 - |charge| (a carbocation and a carbanion both have 3)
  H       valence = 1 - |charge| (a proton or a hydride has none)

Formal charges are limited to -1, 0 and +1.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Optional


@dataclass(frozen=True)
class Element:
    symbol: str
    number: int          # atomic number
    base_valence: int    # bonds when neutral
    mass: float          # standard atomic weight, in daltons


ELEMENTS: Dict[str, Element] = {
    "H": Element("H", 1, 1, 1.008),
    "C": Element("C", 6, 4, 12.011),
    "N": Element("N", 7, 3, 14.007),
    "O": Element("O", 8, 2, 15.999),
}

CHARGES = (-1, 0, 1)

# Elements whose valence rises with positive charge (onium ions) and falls
# with negative charge, because they have lone pairs to give or take.
_LONE_PAIR_ELEMENTS = {"N", "O"}


def valence(symbol: str, charge: int = 0) -> Optional[int]:
    """The number of bonds (counting double as 2, triple as 3) an atom of
    this element must have at this charge, or None if the combination is not
    allowed in this layer."""
    element = ELEMENTS.get(symbol) if type(symbol) is str else None
    if element is None or type(charge) is not int or charge not in CHARGES:
        return None
    if symbol in _LONE_PAIR_ELEMENTS:
        v = element.base_valence + charge
    else:
        v = element.base_valence - abs(charge)
    return v if v >= 0 else None

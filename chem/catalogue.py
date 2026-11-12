"""Real molecules for the tests and the first experiments.

Every entry is a real molecule with its real formula, written out atom by
atom. Charged species appear where real chemistry has them: ammonium,
hydroxide, hydronium, and glycine as a zwitterion (its form in water).
"""
from __future__ import annotations

from typing import Callable, Dict

from .molecule import Builder, Molecule


def hydrogen() -> Molecule:            # H2
    return Builder().atom("a", "H").atom("b", "H").bond("a", "b").build()


def proton() -> Molecule:              # H+
    return Builder().atom("h", "H", +1).build()


def water() -> Molecule:               # H2O
    return Builder().atom("o", "O").hydrogens("o", 2).build()


def hydroxide() -> Molecule:           # OH-
    return Builder().atom("o", "O", -1).hydrogens("o", 1).build()


def hydronium() -> Molecule:           # H3O+
    return Builder().atom("o", "O", +1).hydrogens("o", 3).build()


def ammonia() -> Molecule:             # NH3
    return Builder().atom("n", "N").hydrogens("n", 3).build()


def ammonium() -> Molecule:            # NH4+
    return Builder().atom("n", "N", +1).hydrogens("n", 4).build()


def methane() -> Molecule:             # CH4
    return Builder().atom("c", "C").hydrogens("c", 4).build()


def carbon_dioxide() -> Molecule:      # CO2
    return (Builder().atom("c", "C").atom("o1", "O").atom("o2", "O")
            .bond("c", "o1", 2).bond("c", "o2", 2).build())


def formaldehyde() -> Molecule:        # CH2O
    return (Builder().atom("c", "C").atom("o", "O").bond("c", "o", 2)
            .hydrogens("c", 2).build())


def hydrogen_cyanide() -> Molecule:    # HCN
    return (Builder().atom("c", "C").atom("n", "N").bond("c", "n", 3)
            .hydrogens("c", 1).build())


def carbon_monoxide() -> Molecule:     # CO: a triple bond, C- and O+
    return (Builder().atom("c", "C", -1).atom("o", "O", +1)
            .bond("c", "o", 3).build())


def cyanide() -> Molecule:             # CN-
    return (Builder().atom("c", "C", -1).atom("n", "N")
            .bond("c", "n", 3).build())


def formamide() -> Molecule:           # HCONH2
    return (Builder().atom("c", "C").atom("o", "O").atom("n", "N")
            .bond("c", "o", 2).bond("c", "n")
            .hydrogens("c", 1).hydrogens("n", 2).build())


def urea() -> Molecule:                # CO(NH2)2
    return (Builder().atom("c", "C").atom("o", "O").atom("n1", "N")
            .atom("n2", "N").bond("c", "o", 2).bond("c", "n1").bond("c", "n2")
            .hydrogens("n1", 2).hydrogens("n2", 2).build())


def methanol() -> Molecule:            # CH3OH
    return (Builder().atom("c", "C").atom("o", "O").bond("c", "o")
            .hydrogens("c", 3).hydrogens("o", 1).build())


def ethanol() -> Molecule:             # CH3CH2OH
    return (Builder().atom("c1", "C").atom("c2", "C").atom("o", "O")
            .bond("c1", "c2").bond("c2", "o")
            .hydrogens("c1", 3).hydrogens("c2", 2).hydrogens("o", 1).build())


def dimethyl_ether() -> Molecule:      # CH3OCH3: same formula as ethanol
    return (Builder().atom("c1", "C").atom("o", "O").atom("c2", "C")
            .bond("c1", "o").bond("o", "c2")
            .hydrogens("c1", 3).hydrogens("c2", 3).build())


def methylamine() -> Molecule:         # CH3NH2
    return (Builder().atom("c", "C").atom("n", "N").bond("c", "n")
            .hydrogens("c", 3).hydrogens("n", 2).build())


def formic_acid() -> Molecule:         # HCOOH
    return (Builder().atom("c", "C").atom("o1", "O").atom("o2", "O")
            .bond("c", "o1", 2).bond("c", "o2").hydrogens("c", 1)
            .hydrogens("o2", 1).build())


def glycine() -> Molecule:             # NH2CH2COOH, the neutral form
    return (Builder().atom("n", "N").atom("ca", "C").atom("c", "C")
            .atom("o1", "O").atom("o2", "O")
            .bond("n", "ca").bond("ca", "c").bond("c", "o1", 2).bond("c", "o2")
            .hydrogens("n", 2).hydrogens("ca", 2).hydrogens("o2", 1).build())


def glycine_zwitterion() -> Molecule:  # +H3NCH2COO-, glycine's form in water
    return (Builder().atom("n", "N", +1).atom("ca", "C").atom("c", "C")
            .atom("o1", "O").atom("o2", "O", -1)
            .bond("n", "ca").bond("ca", "c").bond("c", "o1", 2).bond("c", "o2")
            .hydrogens("n", 3).hydrogens("ca", 2).build())


def alanine() -> Molecule:             # CH3CH(NH2)COOH
    return (Builder().atom("n", "N").atom("ca", "C").atom("cb", "C")
            .atom("c", "C").atom("o1", "O").atom("o2", "O")
            .bond("n", "ca").bond("ca", "cb").bond("ca", "c")
            .bond("c", "o1", 2).bond("c", "o2")
            .hydrogens("n", 2).hydrogens("ca", 1).hydrogens("cb", 3)
            .hydrogens("o2", 1).build())


def neopentane() -> Molecule:          # C(CH3)4: highly symmetric
    b = Builder().atom("c", "C")
    for k in range(4):
        b.atom(f"m{k}", "C").bond("c", f"m{k}").hydrogens(f"m{k}", 3)
    return b.build()


def benzene() -> Molecule:             # C6H6, one Kekule structure
    b = Builder()
    for k in range(6):
        b.atom(f"c{k}", "C").hydrogens(f"c{k}", 1)
    for k in range(6):
        b.bond(f"c{k}", f"c{(k + 1) % 6}", 2 if k % 2 == 0 else 1)
    return b.build()


CATALOGUE: Dict[str, Callable[[], Molecule]] = {
    f.__name__: f for f in [
        hydrogen, proton, water, hydroxide, hydronium, ammonia, ammonium,
        methane, carbon_dioxide, formaldehyde, hydrogen_cyanide,
        carbon_monoxide, cyanide, formamide, urea, methanol,
        ethanol, dimethyl_ether, methylamine, formic_acid, glycine,
        glycine_zwitterion, alanine, neopentane, benzene,
    ]
}

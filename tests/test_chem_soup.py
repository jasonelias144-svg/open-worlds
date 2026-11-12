"""Chemistry layer 3, step 1: the engine of a world of chemistry.

Each test checks the engine against an answer known in advance: flux
balance at equilibrium, the uniform spread of diffusion, conservation of
atoms and charge, exact replay from a seed, and a log the agent worlds'
verifier accepts.
"""
import math
import unittest

from chem import catalogue as cat
from chem.soup import Soup
from world.core import World
from tests.test_chem_reactions import glycylglycine as _glycylglycine
from tests.test_chem_reactions import methanediol as _methanediol

# Built once: each molecule caches its identity, and the engine looks
# molecules up by identity.
GLYCINE, ZWITTERION, WATER = cat.glycine(), cat.glycine_zwitterion(), cat.water()
FORMALDEHYDE, HYDRONIUM, HYDROXIDE = cat.formaldehyde(), cat.hydronium(), cat.hydroxide()
GLYCYLGLYCINE, METHANEDIOL, METHANE = _glycylglycine(), _methanediol(), cat.methane()


def time_averages(soup, molecules, events):
    """Run `events` events and return the time-weighted average count of
    each molecule, and of the product of the first two (for flux balance)."""
    sums = [0.0] * (len(molecules) + 1)
    start = soup.time
    for _ in range(events):
        before = [soup.count(m) for m in molecules]
        t0 = soup.time
        if not soup.step():
            break
        dt = soup.time - t0
        for k, n in enumerate(before):
            sums[k] += n * dt
        sums[-1] += before[0] * before[1] * dt if len(before) > 1 else 0.0
    span = soup.time - start
    return [s / span for s in sums]


class TestEquilibrium(unittest.TestCase):
    def test_unimolecular_balance(self):
        # Glycine <-> its zwitterion. At equilibrium the forward and reverse
        # fluxes balance on average: kf * <n_neutral> = kr * <n_zwitterion>.
        soup = Soup(1, 1, seed=1)
        kf, kr = 4.0, 1.0
        soup.add_reaction([GLYCINE], [ZWITTERION], kf)
        soup.add_reaction([ZWITTERION], [GLYCINE], kr)
        soup.put((0, 0), GLYCINE, 500)
        soup.run(max_events=5_000)                       # settle
        neutral, zwitterion, _ = time_averages(
            soup, [GLYCINE, ZWITTERION], 30_000)
        self.assertAlmostEqual(zwitterion / neutral, kf / kr, delta=0.15)
        self.assertEqual(soup.count(GLYCINE) + soup.count(ZWITTERION), 500)

    def test_bimolecular_balance(self):
        # Formaldehyde + water <-> methanediol, in a cell of volume 50.
        # Balance: kf * <n_f * n_w> / V = kr * <n_diol>.
        V = 50.0
        soup = Soup(1, 1, volume=V, seed=2)
        kf, kr = 0.5, 2.0
        soup.add_reaction([FORMALDEHYDE, WATER], [METHANEDIOL], kf)
        soup.add_reaction([METHANEDIOL], [FORMALDEHYDE, WATER], kr)
        soup.put((0, 0), FORMALDEHYDE, 200)
        soup.put((0, 0), WATER, 300)
        soup.run(max_events=5_000)
        f, w, diol, product = time_averages(soup, [FORMALDEHYDE, WATER, METHANEDIOL], 30_000)
        forward, backward = kf * product / V, kr * diol
        self.assertAlmostEqual(forward / backward, 1.0, delta=0.05)

    def test_pairs_of_one_kind_are_counted_as_pairs(self):
        # 2 glycine <-> glycylglycine + water, with only six glycine units, so
        # counting n*n pairs instead of n*(n-1) would show. Balance:
        # kf * <n_g (n_g - 1)> = kr * <n_gg * n_w> (the volume cancels).
        soup = Soup(1, 1, volume=3.0, seed=10)
        kf, kr = 1.0, 2.0
        soup.add_reaction([GLYCINE, GLYCINE], [GLYCYLGLYCINE, WATER], kf)
        soup.add_reaction([GLYCYLGLYCINE, WATER], [GLYCINE, GLYCINE], kr)
        soup.put((0, 0), GLYCINE, 6)
        pairs = products = 0.0
        start = soup.time
        for _ in range(40_000):
            g, gg, w = soup.count(GLYCINE), soup.count(GLYCYLGLYCINE), soup.count(WATER)
            t0 = soup.time
            soup.step()
            dt = soup.time - t0
            pairs += g * (g - 1) * dt
            products += gg * w * dt
        self.assertAlmostEqual(kf * pairs / (kr * products), 1.0, delta=0.05)

    def test_two_of_the_same_kind(self):
        # Two glycines -> glycylglycine + water: a reaction needing two of one
        # kind can't happen with one, and its rate counts ordered pairs.
        soup = Soup(1, 1, seed=3)
        soup.add_reaction([GLYCINE, GLYCINE],
                          [GLYCYLGLYCINE, WATER], 1.0)
        soup.put((0, 0), GLYCINE, 1)
        self.assertFalse(soup.step())
        soup.put((0, 0), GLYCINE, 2)
        self.assertTrue(soup.step())
        self.assertEqual(soup.count(GLYCINE), 1)
        self.assertEqual(soup.count(GLYCYLGLYCINE), 1)


class TestDiffusion(unittest.TestCase):
    def test_spreads_evenly_and_keeps_every_molecule(self):
        soup = Soup(5, 5, seed=4)
        soup.add_species(WATER, hop_rate=1.0)
        soup.put((2, 2), WATER, 500)
        soup.run(max_events=20_000)
        sums = [0.0] * 25
        start = soup.time
        for _ in range(30_000):
            before = [soup.count(WATER, (x, y)) for y in range(5) for x in range(5)]
            t0 = soup.time
            soup.step()
            for k, n in enumerate(before):
                sums[k] += n * (soup.time - t0)
        averages = [s / (soup.time - start) for s in sums]
        self.assertEqual(soup.count(WATER), 500)
        # Uniform is 20 per cell; corners and edges must not differ.
        for a in averages:
            self.assertAlmostEqual(a, 20.0, delta=3.0)

    def test_walls_and_wrapping(self):
        closed = Soup(3, 1, seed=5)
        closed.add_species(WATER, hop_rate=1.0)
        closed.put((0, 0), WATER, 1)
        closed.step()
        self.assertEqual(closed.count(WATER, (1, 0)), 1)   # only neighbour
        ring = Soup(3, 1, seed=5, wrap=True)
        ring.add_species(WATER, hop_rate=1.0)
        ring.put((0, 0), WATER, 1)
        seen = set()
        for _ in range(50):
            ring.step()
            seen.add(next(x for x in range(3) if ring.count(WATER, (x, 0))))
        self.assertEqual(seen, {0, 1, 2})

    def test_a_still_world_rests(self):
        soup = Soup(2, 2)
        soup.add_species(WATER)          # hop rate 0
        soup.put((0, 0), WATER, 10)
        self.assertFalse(soup.step())
        self.assertEqual(soup.run(until=10.0), 0)
        self.assertEqual(soup.time, 0.0)


class TestConservation(unittest.TestCase):
    def test_atoms_and_charge_are_kept_by_every_event(self):
        soup = Soup(3, 3, volume=20.0, seed=6)
        for m in (GLYCINE, WATER, GLYCYLGLYCINE, ZWITTERION,
                  HYDRONIUM, HYDROXIDE):
            soup.add_species(m, hop_rate=0.5)
        soup.add_reaction([GLYCINE, GLYCINE], [GLYCYLGLYCINE, WATER], 0.2)
        soup.add_reaction([GLYCYLGLYCINE, WATER], [GLYCINE, GLYCINE], 0.1)
        soup.add_reaction([GLYCINE], [ZWITTERION], 3.0)
        soup.add_reaction([ZWITTERION], [GLYCINE], 1.0)
        soup.add_reaction([WATER, WATER], [HYDRONIUM, HYDROXIDE], 0.01)
        soup.add_reaction([HYDRONIUM, HYDROXIDE], [WATER, WATER], 5.0)
        soup.put((0, 0), GLYCINE, 60)
        soup.put((2, 2), WATER, 80)
        atoms = soup.atoms()
        self.assertEqual(atoms["charge"], 0)
        for _ in range(3_000):
            if not soup.step():
                break
            self.assertEqual(soup.atoms(), atoms)
        self.assertGreater(soup.events, 2_000)

    def test_unbalanced_reactions_are_refused(self):
        soup = Soup(1, 1)
        with self.assertRaisesRegex(ValueError, "keep every atom"):
            soup.add_reaction([WATER], [HYDROXIDE], 1.0)
        with self.assertRaisesRegex(ValueError, "keep every atom"):
            soup.add_reaction([WATER], [HYDRONIUM], 1.0)

    def test_bad_input_is_refused(self):
        soup = Soup(2, 2)
        bad = [
            lambda: Soup(0, 1),
            lambda: Soup(1, 1, volume=0),
            lambda: soup.add_species(WATER, hop_rate=-1),
            lambda: soup.add_species(WATER, hop_rate=float("nan")),
            lambda: soup.add_reaction([WATER], [WATER], 1.0),
            lambda: soup.add_reaction([], [WATER], 1.0),
            lambda: soup.add_reaction([GLYCINE], [ZWITTERION], True),
            lambda: soup.put((5, 5), WATER, 1),
            lambda: soup.put([0, 0], WATER, 1),
            lambda: soup.put((0, 0), METHANE, 1),            # not registered
            lambda: soup.count(METHANE),
        ]
        soup.add_species(WATER, hop_rate=1.0)
        bad.append(lambda: soup.put((0, 0), WATER, -1))
        bad.append(lambda: soup.add_species(WATER, hop_rate=2.0))
        bad.append(lambda: soup.run())
        for make in bad:
            with self.assertRaises(ValueError):
                make()


class TestTheRecord(unittest.TestCase):
    def build(self, seed):
        soup = Soup(3, 2, volume=10.0, seed=seed)
        soup.add_species(FORMALDEHYDE, hop_rate=1.0)
        soup.add_species(WATER, hop_rate=1.0)
        soup.add_species(METHANEDIOL, hop_rate=0.5)
        soup.add_reaction([FORMALDEHYDE, WATER], [METHANEDIOL], 0.5)
        soup.add_reaction([METHANEDIOL], [FORMALDEHYDE, WATER], 0.2)
        soup.put((0, 0), FORMALDEHYDE, 30)
        soup.put((2, 1), WATER, 40)
        soup.run(max_events=2_000)
        return soup

    def test_same_seed_same_history(self):
        a, b = self.build(7), self.build(7)
        self.assertEqual(a.log_head, b.log_head)
        self.assertEqual(a.time, b.time)
        self.assertNotEqual(a.log_head, self.build(8).log_head)

    def test_the_log_verifies_with_the_kernel_verifier(self):
        soup = self.build(9)
        self.assertEqual(len(soup.log), 3 + 2 + 2 + 1 + 2_000)  # world, species, reactions, puts, events
        self.assertTrue(World.verify_log(soup.log))
        tampered = [dict(e) for e in soup.log]
        tampered[500]["data"] = {"cell": [0, 0], "reaction": 1}
        self.assertFalse(World.verify_log(tampered))
        self.assertFalse(World.verify_log(soup.log[:100] + soup.log[101:]))

    def test_the_head_is_kept_without_the_log(self):
        quiet = Soup(3, 2, volume=10.0, seed=9, log=False)
        loud = self.build(9)
        quiet.add_species(FORMALDEHYDE, hop_rate=1.0)
        quiet.add_species(WATER, hop_rate=1.0)
        quiet.add_species(METHANEDIOL, hop_rate=0.5)
        quiet.add_reaction([FORMALDEHYDE, WATER], [METHANEDIOL], 0.5)
        quiet.add_reaction([METHANEDIOL], [FORMALDEHYDE, WATER], 0.2)
        quiet.put((0, 0), FORMALDEHYDE, 30)
        quiet.put((2, 1), WATER, 40)
        quiet.run(max_events=2_000)
        self.assertIsNone(quiet.log)
        self.assertEqual(quiet.log_head, loud.log_head)


if __name__ == "__main__":
    unittest.main()

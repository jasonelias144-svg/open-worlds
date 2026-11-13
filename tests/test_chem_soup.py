"""Chemistry layer 3, step 1: the engine of a world of chemistry.

Each test checks the engine against an answer known in advance: flux
balance at equilibrium, the uniform spread of diffusion, conservation of
atoms and charge, exact replay from a seed, and a log the agent worlds'
verifier accepts.
"""
import math
import random
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
        for _ in range(60_000):
            before = [soup.count(WATER, (x, y)) for y in range(5) for x in range(5)]
            t0 = soup.time
            soup.step()
            for k, n in enumerate(before):
                sums[k] += n * (soup.time - t0)
        averages = [s / (soup.time - start) for s in sums]
        self.assertEqual(soup.count(WATER), 500)
        # Uniform is 20 per cell; corners and edges must not differ.
        for a in averages:
            self.assertAlmostEqual(a, 20.0, delta=4.0)

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

    def test_a_refused_reaction_changes_nothing(self):
        soup = Soup(1, 1)
        before = (soup.log_head, len(soup.species))
        with self.assertRaises(ValueError):
            soup.add_reaction([WATER], [WATER], 1.0)
        self.assertEqual((soup.log_head, len(soup.species)), before)
        soup.add_species(WATER, hop_rate=1.0)        # still free to register

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
            lambda: Soup(1, 1, seed="x"),
            lambda: Soup(1, 1, seed=object()),
            lambda: Soup(1, 1, wrap=1),
            lambda: Soup(1, 1, volume=1e-200),
            lambda: Soup(1, 1, volume=1e200),
            lambda: soup.add_reaction([GLYCINE], [ZWITTERION], 1e308),
            lambda: soup.add_species(GLYCINE, hop_rate=1e308),
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


def rounding_world(seed):
    """A small random world: water and formaldehyde hopping, hydration and
    its reverse, and a reaction whose reactant is absent everywhere."""
    r = random.Random(seed)
    soup = Soup(r.randint(2, 4), 1, volume=r.choice((1.0, 3.0, 7.0)))
    soup.add_species(WATER, hop_rate=r.choice((0.3, 0.7, 0.9, 1.1)))
    soup.add_species(FORMALDEHYDE, hop_rate=r.choice((0.0, 0.7, 1.3)))
    soup.add_species(METHANEDIOL, hop_rate=0.0)
    soup.add_reaction([FORMALDEHYDE, WATER], [METHANEDIOL], r.choice((0.37, 0.5, 1.1)))
    soup.add_reaction([METHANEDIOL], [FORMALDEHYDE, WATER], r.choice((2.9, 0.2)))
    soup.add_reaction([GLYCINE], [ZWITTERION], 1.0)
    for x in range(soup.width):
        soup.put((x, 0), WATER, r.randint(0, 90))
        if r.random() < 0.6:
            soup.put((x, 0), FORMALDEHYDE, r.randint(0, 40))
    return soup


class TestRounding(unittest.TestCase):
    """Floating-point rounding at a boundary between cells must never choose
    an event that can't happen, nor report rest while events remain
    (independent review of #8). Each world here broke the first version of
    the engine at one of the values tried: world 142 drove a count
    negative, and worlds 193 and 195 made step() report rest. World 436
    breaks it if only possible events are no longer the sole candidates
    (found by the follow-up review of #8)."""

    def test_every_value_near_every_boundary(self):
        for seed in (142, 193, 195, 436):
            probe = rounding_world(seed)
            weights = probe._propensity
            total = sum(weights)
            atoms = probe.atoms()
            for c in range(len(weights) + 1):
                v = sum(weights[:c]) / total
                for _ in range(40):
                    v = math.nextafter(v, 0.0)
                for _ in range(80):
                    v = math.nextafter(v, 1.0)
                    if not 0.0 <= v < 1.0:
                        continue
                    soup = rounding_world(seed)
                    soup._rng.random = lambda v=v: v
                    with self.subTest(seed=seed, value=v):
                        self.assertTrue(soup.step())
                        self.assertTrue(all(n >= 0 for counts in soup._counts
                                            for n in counts))
                        self.assertEqual(soup.atoms(), atoms)


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


class TestPerform(unittest.TestCase):
    """An agent's act: one given reaction, now, in one cell."""

    def soup(self):
        soup = Soup(2, 1, volume=10.0, seed=3)
        soup.add_species(GLYCINE, hop_rate=1.0)
        soup.add_species(WATER, hop_rate=1.0)
        soup.put((0, 0), GLYCINE, 3)
        soup.put((1, 0), WATER, 2)
        return soup

    def test_it_happens_now_and_keeps_every_atom(self):
        soup = self.soup()
        atoms, time, events = soup.atoms(), soup.time, soup.events
        self.assertTrue(soup.perform((0, 0), [GLYCINE, GLYCINE],
                                     [GLYCYLGLYCINE, WATER]))
        self.assertEqual(soup.count(GLYCINE, (0, 0)), 1)
        self.assertEqual(soup.count(GLYCYLGLYCINE, (0, 0)), 1)
        self.assertEqual(soup.count(WATER, (0, 0)), 1)
        self.assertEqual(soup.atoms(), atoms)
        self.assertEqual((soup.time, soup.events), (time, events + 1))
        last = soup.log[-1]
        self.assertEqual(last["kind"], "perform")
        self.assertEqual(last["data"]["cell"], [0, 0])
        self.assertTrue(World.verify_log(soup.log))
        # A new product is registered, still, as the world's species.
        self.assertIn(GLYCYLGLYCINE, soup.species)

    def test_it_needs_its_reactants_in_that_cell(self):
        soup = self.soup()
        for cell, reactants, products in (
                # the water is in the other cell
                ((0, 0), [WATER, WATER], [HYDRONIUM, HYDROXIDE]),
                # only one glycine is in cell (1, 0): none, in fact
                ((1, 0), [GLYCINE, GLYCINE], [GLYCYLGLYCINE, WATER]),
                # formaldehyde isn't in this world at all
                ((0, 0), [FORMALDEHYDE, WATER], [METHANEDIOL])):
            with self.subTest(cell=cell, reactants=len(reactants)):
                before = (soup.log_head, soup.events,
                          [soup.count(m) for m in soup.species])
                self.assertFalse(soup.perform(cell, reactants, products))
                self.assertEqual(before, (soup.log_head, soup.events,
                                          [soup.count(m) for m in soup.species]))
        # Where the water is, it goes.
        self.assertTrue(soup.perform((1, 0), [WATER, WATER],
                                     [HYDRONIUM, HYDROXIDE]))
        # As many of each as the reaction uses: three glycines make one
        # dipeptide, and then one glycine is not enough.
        self.assertTrue(soup.perform((0, 0), [GLYCINE, GLYCINE],
                                     [GLYCYLGLYCINE, WATER]))
        self.assertFalse(soup.perform((0, 0), [GLYCINE, GLYCINE],
                                      [GLYCYLGLYCINE, WATER]))

    def test_what_isnt_a_reaction_is_refused(self):
        soup = self.soup()
        for cell, reactants, products in (
                ((0, 0), [GLYCINE], [WATER]),                    # unbalanced
                ((0, 0), [GLYCINE], [GLYCINE]),                  # no change
                ((0, 0), [], [GLYCINE]),
                ((0, 0), (m for m in [GLYCINE]), [ZWITTERION]),  # not a list
                ((0, 0), ["glycine"], [ZWITTERION]),
                ((5, 0), [GLYCINE], [ZWITTERION]),               # no such cell
                ([0, 0], [GLYCINE], [ZWITTERION])):
            with self.subTest(reactants=reactants, cell=cell):
                head = soup.log_head
                with self.assertRaises(ValueError):
                    soup.perform(cell, reactants, products)
                self.assertEqual(soup.log_head, head)

    def test_the_world_carries_on_from_what_was_done(self):
        # The world's own reaction can't start until an act makes its
        # reactant; then it can.
        soup = Soup(1, 1, seed=2)
        soup.add_reaction([ZWITTERION], [GLYCINE], 1.0)
        soup.add_species(GLYCINE)
        soup.put((0, 0), GLYCINE, 1)
        self.assertFalse(soup.step())
        self.assertTrue(soup.perform((0, 0), [GLYCINE], [ZWITTERION]))
        self.assertTrue(soup.step())
        self.assertEqual(soup.count(GLYCINE), 1)

    def test_the_same_acts_replay_the_same_history(self):
        def history(seed):
            soup = Soup(2, 1, volume=10.0, seed=seed)
            soup.add_species(GLYCINE, hop_rate=1.0)
            soup.add_species(WATER, hop_rate=1.0)
            soup.add_reaction([GLYCYLGLYCINE, WATER], [GLYCINE, GLYCINE], 0.1)
            soup.put((0, 0), GLYCINE, 30)
            soup.put((1, 0), WATER, 30)
            for _ in range(5):
                soup.run(max_events=50)
                soup.perform((0, 0), [GLYCINE, GLYCINE],
                             [GLYCYLGLYCINE, WATER])
            return soup.log_head
        self.assertEqual(history(4), history(4))
        self.assertNotEqual(history(4), history(5))


class TestAdvance(unittest.TestCase):
    """The world's own events up to a given time, and the clock set to it."""

    def test_the_clock_lands_exactly(self):
        soup = Soup(1, 1, seed=1)
        soup.add_species(WATER)
        soup.put((0, 0), WATER, 5)
        self.assertEqual(soup.advance(5.0), 0)          # at rest
        self.assertEqual(soup.time, 5.0)
        self.assertEqual(soup.advance(5.0), 0)
        for bad in (4.0, float("nan"), float("inf"), -1, "6", None):
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                soup.advance(bad)
        self.assertEqual(soup.time, 5.0)

    def test_no_event_comes_after_the_limit(self):
        soup = TestTheRecord().build(3)
        start, head = soup.time, soup.log_head
        n = len(soup.log)
        events = soup.advance(start + 2.0)
        self.assertGreater(events, 0)
        self.assertEqual(soup.time, start + 2.0)
        self.assertEqual(len(soup.log), n + events)
        self.assertTrue(all(e["time"] <= start + 2.0 for e in soup.log[n:]))
        self.assertNotEqual(soup.log_head, head)
        self.assertTrue(World.verify_log(soup.log))

    def test_the_same_seed_replays(self):
        def history(seed):
            soup = TestTheRecord().build(seed)
            for k in range(1, 4):
                soup.advance(soup.time + 0.5 * k)
            return soup.log_head, soup.time
        self.assertEqual(history(5), history(5))
        self.assertNotEqual(history(5)[0], history(6)[0])

    def test_decay_by_a_given_time(self):
        # One-way decay at rate k: by time t, each of N molecules has gone
        # with probability 1 - exp(-k t). Averaged over 40 worlds.
        n, k, t = 200, 1.0, 0.5
        gone = []
        for seed in range(40):
            soup = Soup(1, 1, seed=seed)
            soup.add_reaction([GLYCINE], [ZWITTERION], k)
            soup.put((0, 0), GLYCINE, n)
            soup.advance(t)
            gone.append(soup.count(ZWITTERION))
        expected = n * (1 - math.exp(-k * t))
        self.assertAlmostEqual(sum(gone) / len(gone), expected, delta=4.0)


class TestHugeClocks(unittest.TestCase):
    def test_a_clock_too_large_to_move_stops_instead_of_looping(self):
        # Near 1e16 seconds a wait rounds to nothing. Neither run() nor
        # advance() may then loop for ever.
        for how in ("advance", "run"):
            with self.subTest(how=how):
                soup = Soup(1, 1, seed=1)
                soup.add_reaction([GLYCINE], [ZWITTERION], 4.0)
                soup.add_reaction([ZWITTERION], [GLYCINE], 1.0)
                soup.put((0, 0), GLYCINE, 20)
                soup.time = 1e17
                if how == "advance":
                    soup.advance(1e17 + 1e3)
                    self.assertEqual(soup.time, 1e17 + 1e3)
                else:
                    self.assertLessEqual(soup.run(until=1e17 + 1e3), 1)

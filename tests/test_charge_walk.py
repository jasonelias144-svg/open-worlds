"""Checks for the charge-controlled tabletop world, experiment 009."""
import itertools
from importlib import import_module
import unittest

field = import_module("experiments.009-charge-walk.field")
State, Track, WALL, controls, step = field.State, field.Track, field.WALL, field.controls, field.step


class ChargeWalk(unittest.TestCase):
    def test_free_pairs_attract_repel_or_wait(self):
        for choices, positions, bonded in (([1, -1], [3, 4], True), ([-1, 1], [3, 4], True),
                                           ([1, 1], [1, 6], False), ([-1, -1], [1, 6], False),
                                           ([1, 0], [2, 5], False)):
            with self.subTest(choices=choices):
                _, event = step(State(), choices, Track(), 1)
                self.assertEqual((event["positions"], event["new_bond"]), (positions, bonded))

    def test_free_beads_cannot_cross_and_bond_at_first_contact(self):
        for a, b in itertools.combinations(range(WALL + 1), 2):
            for charges in itertools.product((-1, 0, 1), repeat=2):
                for t in (1, 2):
                    after, _ = step(State(a, b), charges, Track(), t)
                    self.assertTrue(0 <= after.a < after.b <= WALL)
                    self.assertLessEqual(max(abs(after.a-a), abs(after.b-b)), 1)
                    if charges[0] * charges[1] < 0 and b-a <= 3:
                        self.assertTrue(after.bonded)

    def test_bond_is_rigid_and_has_no_internal_propulsion(self):
        for a in range(WALL):
            for charges in itertools.product((-1, 0, 1), repeat=2):
                old = State(a, a+1, bonded=True)
                new, event = step(old, charges, Track(powered=False), 1)
                self.assertEqual((new.a, new.b, new.bonded), (a, a+1, True))
                self.assertEqual(event["forces"], [0, 0])
                shifted, _ = step(old, charges, Track(), 1)
                self.assertEqual(shifted.b-shifted.a, 1)
                self.assertLessEqual(abs(shifted.a-old.a), 1)

    def test_zero_sum_and_wall_stop(self):
        pinned, _ = step(State(0, 1, True), [-1, 1], Track(), 9)
        self.assertEqual((pinned.a, pinned.b), (0, 1))
        idle, event = step(State(5, 6, True), [1, 1], Track(), 2)
        self.assertEqual((idle.a, idle.b), (5, 6))
        self.assertEqual(sum(event["forces"]), 0)

    def test_reference_and_yoked_comparisons(self):
        runs = {r["name"]: r for r in controls()}
        ref, off, frozen = [runs[n]["frames"] for n in ("switching", "pads off", "frozen")]
        self.assertEqual([f["charges"] for f in ref], [f["charges"] for f in off])
        self.assertEqual(len(ref), len(frozen))
        self.assertEqual([f["positions"][0] for f in ref], list(range(3, 10)) + list(range(8, 2, -1)))
        self.assertTrue(ref[-1]["home"])
        self.assertTrue(all(f["positions"] == [3, 4] for f in off))
        self.assertEqual({tuple(f["positions"]) for f in frozen}, {(3, 4), (4, 5)})
        self.assertTrue(runs["one pad missing"]["frames"][-1]["home"])
        self.assertEqual(runs["three pads missing"]["frames"][-1]["positions"], [7, 8])
        self.assertEqual(runs["three pads missing"]["frames"][-1]["forces"], [0, 0])

    def test_invalid_charge_is_rejected(self):
        for bad in ([True, 1], [1, 2], [], [1, 0, -1], ["positive", -1]):
            with self.assertRaises(ValueError):
                step(State(), bad, Track(), 1)


if __name__ == "__main__":
    unittest.main()

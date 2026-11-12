import random
import unittest

from experiments.corridor import (Walker, lane_order, run_corridor,
                                  side_convention)
from world import Move, Observation, Wait, World


def placed(rows):
    """Build a world from rows of 'E', 'W' and '.' (y grows downward)."""
    world = World(len(rows[0]), len(rows), wrap_x=True)
    walkers = {}
    for y, row in enumerate(rows):
        for x, c in enumerate(row):
            if c in "EW":
                w = Walker(1 if c == "E" else -1, random.Random(0))
                walkers[f"{c}{x}{y}"] = w
                world.add(f"{c}{x}{y}", w, (x, y))
    return world, walkers


class TestMeasures(unittest.TestCase):

    def test_separate_lanes_score_one(self):
        world, walkers = placed(["WWWW", "WW..", "EE..", "EEEE"])
        self.assertEqual(lane_order(world, walkers), 1.0)

    def test_evenly_mixed_rows_score_zero(self):
        world, walkers = placed(["EWEW", "WEWE"])
        self.assertEqual(lane_order(world, walkers), 0.0)

    def test_keep_right_scores_plus_one(self):
        # Facing east your right is south (the lower rows); facing west,
        # north (the upper rows).
        world, walkers = placed(["WWWW", "....", "....", "EEEE"])
        self.assertEqual(side_convention(world, walkers), 1.0)

    def test_keep_left_scores_minus_one(self):
        world, walkers = placed(["EEEE", "....", "....", "WWWW"])
        self.assertEqual(side_convention(world, walkers), -1.0)


class TestWalker(unittest.TestCase):

    def test_steps_forward_when_free(self):
        world, walkers = placed(["E...", "...."])
        world.step()
        self.assertEqual(world.position("E00"), (1, 0))

    def _seen(self, step_of_the_one_ahead):
        return Observation(
            tick=1, me="me", position=(0, 1), width=5, height=3, wrap_x=True,
            neighbors=(((1, 1), "ahead", step_of_the_one_ahead),),
            messages=(), orientation="", rules_version="0")

    def test_waits_behind_someone_moving_its_way(self):
        walker = Walker(1, random.Random(0))
        self.assertEqual(walker.act(self._seen((1, 0))), Wait())

    def test_steps_aside_for_someone_standing_still_or_oncoming(self):
        for step in [(0, 0), (-1, 0)]:
            action = Walker(1, random.Random(0)).act(self._seen(step))
            self.assertIn(action, [Move(0, 1), Move(0, -1)])

    def test_full_bias_tries_its_own_right_first(self):
        # Facing east, your right is south: y + 1.
        walker = Walker(1, random.Random(0), side_bias=1.0)
        for _ in range(20):
            self.assertEqual(walker.act(self._seen((0, 0))), Move(0, 1))

    def test_never_leaves_the_corridor(self):
        world, walkers = placed(["EW", "WE"])
        world.run(50)
        for a in world.agents():
            self.assertIn(world.position(a)[1], (0, 1))


class TestExperiment(unittest.TestCase):

    def test_reproducible(self):
        a = run_corridor(ticks=100, seed=3)
        b = run_corridor(ticks=100, seed=3)
        self.assertEqual(a, b)

    def test_sparse_corridor_forms_lanes(self):
        r = run_corridor(density=0.1, ticks=1500, seed=0)
        self.assertEqual(r["lane_order_end"], 1.0)
        self.assertEqual(r["flow"], 1.0)

    def test_momentum_flag_reaches_walkers(self):
        w = Walker(1, random.Random(0), respect_momentum=False)
        seen = TestWalker._seen(None, (1, 0))
        self.assertIn(w.act(seen), [Move(0, 1), Move(0, -1)])

    def test_blocks_are_counted_by_cause(self):
        w = Walker(1, random.Random(0))
        w.act(TestWalker._seen(None, (1, 0)))
        w.act(TestWalker._seen(None, (0, 0)))
        self.assertEqual((w.blocked, w.blocked_same_way), (2, 1))

    def test_odd_height_is_refused(self):
        with self.assertRaises(ValueError):
            run_corridor(height=7, ticks=1)


if __name__ == "__main__":
    unittest.main()

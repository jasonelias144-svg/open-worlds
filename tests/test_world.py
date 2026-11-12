import random
import unittest

from world import MAX_SAY_CHARS, Exit, Move, Say, Wait, World


class Scripted:
    """Plays a fixed list of actions, then waits. Remembers what it saw."""

    def __init__(self, *actions):
        self.actions = list(actions)
        self.seen = []

    def act(self, obs):
        self.seen.append(obs)
        return self.actions.pop(0) if self.actions else Wait()


class Raises:
    def act(self, obs):
        raise RuntimeError("broken agent")


class RandomMover:
    def __init__(self, seed):
        self.rng = random.Random(seed)

    def act(self, obs):
        return self.rng.choice([Move(1, 0), Move(-1, 0), Move(0, 1),
                                Move(0, -1), Wait()])


def kinds(world, agent_id=None):
    return [e["kind"] for e in world.log
            if agent_id is None or e["agent"] == agent_id]


class TestExit(unittest.TestCase):
    """Freedom of exit: leaving always succeeds."""

    def test_exit_succeeds_even_when_surrounded(self):
        w = World(3, 3)
        w.add("center", Scripted(Exit()), (1, 1))
        for i, pos in enumerate([(0, 0), (1, 0), (2, 0), (0, 1), (2, 1),
                                 (0, 2), (1, 2), (2, 2)]):
            w.add(f"n{i}", Scripted(), pos)
        w.step()
        self.assertNotIn("center", w.agents())
        self.assertIn("center", w.exited)
        self.assertIsNone(w.occupant((1, 1)))

    def test_exited_agent_never_acts_again(self):
        a = Scripted(Exit(), Move(1, 0))
        w = World(5, 1)
        w.add("a", a, (0, 0))
        w.run(3)
        self.assertEqual(len(a.seen), 1)

    def test_owner_can_pull_agent_out_any_time(self):
        w = World(2, 1)
        w.add("a", Scripted(), (0, 0))
        w.leave("a", "owner withdrew")
        self.assertEqual(w.agents(), [])
        self.assertEqual(w.log[-1]["data"]["reason"], "owner withdrew")

    def test_an_exited_id_cannot_be_reused(self):
        w = World(2, 1)
        w.add("a", Scripted(Exit()), (0, 0))
        w.step()
        with self.assertRaises(ValueError):
            w.add("a", Scripted(), (1, 0))


class TestVoice(unittest.TestCase):
    """Freedom of voice: speech reaches everyone on the next tick."""

    def test_everyone_hears_next_tick(self):
        speaker = Scripted(Say("hello"))
        listener = Scripted()
        w = World(10, 10)
        w.add("s", speaker, (0, 0))
        w.add("l", listener, (9, 9))   # far outside the view radius
        w.run(2)
        self.assertEqual(listener.seen[0].messages, ())
        self.assertEqual(listener.seen[1].messages, (("s", "hello"),))
        self.assertEqual(speaker.seen[1].messages, (("s", "hello"),))

    def test_speech_is_heard_for_one_tick(self):
        listener = Scripted()
        w = World(3, 1)
        w.add("s", Scripted(Say("once")), (0, 0))
        w.add("l", listener, (2, 0))
        w.run(3)
        self.assertEqual(listener.seen[2].messages, ())

    def test_long_speech_is_cut_not_refused(self):
        w = World(1, 1)
        w.add("s", Scripted(Say("x" * 1000)), (0, 0))
        w.step()
        said = [e for e in w.log if e["kind"] == "said"][0]
        self.assertEqual(len(said["data"]["text"]), MAX_SAY_CHARS)


class TestInformation(unittest.TestCase):
    """Freedom of information: the orientation and rules are always shown."""

    def test_every_observation_carries_orientation_and_rules(self):
        a = Scripted()
        w = World(2, 2, orientation="read me", rules_version="7")
        w.add("a", a, (0, 0))
        w.run(3)
        for obs in a.seen:
            self.assertEqual(obs.orientation, "read me")
            self.assertEqual(obs.rules_version, "7")

    def test_observations_are_immutable(self):
        a = Scripted()
        w = World(2, 1)
        w.add("a", a, (0, 0))
        w.step()
        with self.assertRaises(Exception):
            a.seen[0].position = (1, 0)


class TestMovement(unittest.TestCase):

    def test_move_into_free_cell(self):
        w = World(3, 1)
        w.add("a", Scripted(Move(1, 0)), (0, 0))
        w.step()
        self.assertEqual(w.position("a"), (1, 0))

    def test_move_into_occupied_cell_is_blocked(self):
        w = World(3, 1)
        w.add("a", Scripted(Move(1, 0)), (0, 0))
        w.add("b", Scripted(), (1, 0))
        w.step()
        self.assertEqual(w.position("a"), (0, 0))
        self.assertIn("blocked", kinds(w, "a"))

    def test_walls_block_without_wrap(self):
        w = World(2, 2)
        w.add("a", Scripted(Move(-1, 0), Move(0, -1)), (0, 0))
        w.run(2)
        self.assertEqual(w.position("a"), (0, 0))

    def test_x_wraps_when_enabled(self):
        w = World(3, 1, wrap_x=True)
        w.add("a", Scripted(Move(-1, 0)), (0, 0))
        w.step()
        self.assertEqual(w.position("a"), (2, 0))

    def test_neighbors_show_momentum(self):
        b = Scripted()
        w = World(4, 1)
        w.add("a", Scripted(Move(1, 0)), (0, 0))
        w.add("b", b, (2, 0))
        w.run(2)
        self.assertEqual(b.seen[1].momentum_at((1, 0)), (1, 0))
        self.assertIsNone(b.seen[1].momentum_at((3, 0)))

    def test_one_agent_per_cell_always(self):
        w = World(6, 6, seed=3)
        for i in range(20):
            w.add(f"r{i}", RandomMover(i), (i % 6, i // 6))
        for _ in range(200):
            w.step()
            cells = [w.position(a) for a in w.agents()]
            self.assertEqual(len(cells), len(set(cells)))


class TestTheWorldTrustsNothing(unittest.TestCase):

    def test_oversized_and_diagonal_moves_are_refused(self):
        w = World(5, 5)
        w.add("a", Scripted(Move(2, 0), Move(1, 1), Move(True, 0)), (2, 2))
        w.run(3)
        self.assertEqual(w.position("a"), (2, 2))
        self.assertEqual(kinds(w, "a").count("invalid_action"), 3)

    def test_non_actions_are_refused(self):
        w = World(2, 1)
        w.add("a", Scripted("teleport", None), (0, 0))
        w.run(2)
        self.assertEqual(kinds(w, "a").count("invalid_action"), 2)

    def test_subclassed_actions_are_refused(self):
        class Sneaky(Move):
            pass
        w = World(3, 1)
        w.add("a", Scripted(Sneaky(1, 0)), (0, 0))
        w.step()
        self.assertEqual(w.position("a"), (0, 0))
        self.assertIn("invalid_action", kinds(w, "a"))

    def test_speech_must_be_text(self):
        class Bomb:
            def __str__(self):
                raise RuntimeError("boom")
        w = World(2, 1)
        w.add("a", Scripted(Say(Bomb())), (0, 0))
        w.step()                        # must not raise
        self.assertIn("invalid_action", kinds(w, "a"))

    # The attacks below were found by the independent review of PR #1.

    @staticmethod
    def _impostor(pretends_to_be, **fields):
        """An object that claims to be a kernel action: its metaclass says
        it equals any type, and its __class__ claims the real one. Each field
        is a function of how many times it has been read."""
        class Meta(type):
            def __eq__(cls, other):
                return True
            __hash__ = type.__hash__

        reads = {}

        def field(name, value_at):
            def get(self):
                reads[name] = reads.get(name, 0) + 1
                return value_at(reads[name])
            return property(get)

        body = {name: field(name, f) for name, f in fields.items()}
        body["__class__"] = property(lambda self: pretends_to_be)
        return Meta("Impostor", (), body)()

    def test_an_impostor_move_cannot_teleport(self):
        # Valid for the two reads a check makes, 7 when the move is applied.
        fake = self._impostor(Move, dx=lambda n: 1 if n <= 2 else 7,
                              dy=lambda n: 0)
        w = World(10, 1)
        w.add("a", Scripted(fake), (0, 0))
        w.step()
        self.assertEqual(w.position("a"), (0, 0))
        self.assertIn("invalid_action", kinds(w, "a"))

    def test_an_impostor_say_cannot_crash_the_world(self):
        fake = self._impostor(Say, text=lambda n: "hi" if n == 1 else [object()])
        w = World(2, 1)
        w.add("a", Scripted(fake), (0, 0))
        w.step()                                   # must not raise
        self.assertIn("invalid_action", kinds(w, "a"))
        self.assertTrue(World.verify_log(w.log))

    def test_speech_that_is_a_str_subclass_is_refused(self):
        class Sly(str):
            pass
        w = World(1, 1)
        w.add("a", Scripted(Say(Sly("hi"))), (0, 0))
        w.step()
        self.assertIn("invalid_action", kinds(w, "a"))

    def test_a_type_name_that_is_not_text_cannot_crash_the_log(self):
        unloggable = property(lambda cls: object())

        class Odd(metaclass=type("M", (type,), {"__name__": unloggable})):
            pass

        class OddError(Exception, metaclass=type("M2", (type,),
                                                 {"__name__": unloggable})):
            pass

        class Raiser:
            def act(self, obs):
                raise OddError()

        w = World(3, 1)
        w.add("odd", Scripted(Odd()), (0, 0))
        w.add("raiser", Raiser(), (2, 0))
        w.step()                                   # must not raise
        self.assertIn("invalid_action", kinds(w, "odd"))
        self.assertIn("agent_error", kinds(w, "raiser"))
        self.assertTrue(World.verify_log(w.log))

    def test_exit_happens_whatever_another_agent_returns(self):
        for seed in range(20):                     # both orders occur
            fake = self._impostor(Say, text=lambda n: "hi" if n == 1
                                  else [object()])
            w = World(3, 1, seed=seed)
            w.add("attacker", Scripted(fake), (0, 0))
            w.add("leaver", Scripted(Exit()), (2, 0))
            w.step()
            self.assertNotIn("leaver", w.agents(), f"seed {seed}")
            self.assertIn("leaver", w.exited)

    def test_a_crashing_agent_does_not_stop_the_world(self):
        mover = Scripted(Move(1, 0))
        w = World(3, 1)
        w.add("bad", Raises(), (2, 0))
        w.add("good", mover, (0, 0))
        w.step()
        self.assertEqual(w.position("good"), (1, 0))
        self.assertIn("agent_error", kinds(w, "bad"))


class TestThePublicRecord(unittest.TestCase):

    def _world(self, seed):
        w = World(6, 6, seed=seed)
        for i in range(8):
            w.add(f"r{i}", RandomMover(i), (i, 0) if i < 6 else (i - 6, 1))
        w.run(50)
        return w

    def test_log_verifies(self):
        self.assertTrue(World.verify_log(self._world(1).log))

    def test_tampering_is_detected(self):
        log = self._world(1).log
        log[5] = {**log[5], "agent": "someone else"}
        self.assertFalse(World.verify_log(log))

    def test_a_malformed_entry_fails_verification_instead_of_crashing(self):
        log = self._world(1).log
        log[2] = {"kind": "moved"}
        self.assertFalse(World.verify_log(log))

    def test_removing_an_entry_is_detected(self):
        log = self._world(1).log
        del log[3]
        self.assertFalse(World.verify_log(log))

    def test_same_seed_same_history(self):
        self.assertEqual(self._world(4).log_head(), self._world(4).log_head())
        self.assertNotEqual(self._world(4).log_head(),
                            self._world(5).log_head())


if __name__ == "__main__":
    unittest.main()

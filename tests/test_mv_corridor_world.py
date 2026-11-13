"""The corridor world behind the protocol, its doors, and the first
journey (course step 5)."""
import dataclasses
import unittest

from multiverse.chemistry_world import ChemistryWorld
from multiverse.collaboration import (act_on_world, leave_world, make_client,
                                      petition_world)
from multiverse.conformance import run_conformance
from multiverse.corridor_world import (MOVE, SAY, WAIT, CorridorWorld,
                                       CorridorWorldLaw, Door)
from multiverse.identity import Individual, Signer
from multiverse.journey import build_worlds, journey, walk_to
from multiverse.passport import Passport, make_stamp, verify_passport
from multiverse.poetry_world import PoetryWorld
from multiverse.protocol import Ack, Act, Admission, Refusal, signed_manifest
from world.core import World

EAST = {"dx": 1, "dy": 0}
WEST = {"dx": -1, "dy": 0}


def _corridor(**law):
    return CorridorWorld("world:corridor", "The Corridor",
                         CorridorWorldLaw(**law))


def _door(world, cell, name=""):
    m = world.manifest()
    return Door(cell, m.entity_id, m.world_key, name)


class Case(unittest.TestCase):

    def enter(self, w, name="Alice"):
        client = make_client(name)
        self.assertIsInstance(petition_world(client, w), Admission)
        return client

    def at(self, w, client):
        return w.where(client.individual.token)["cell"]


class TestTheLaw(Case):

    def test_it_is_published_with_its_doors(self):
        chemistry = ChemistryWorld("world:chemistry", "Chemistry")
        law = CorridorWorldLaw(doors=(_door(chemistry, (11, 0),
                                            "the chemistry world"),))
        doc = law.describe()
        for part in (MOVE, SAY, WAIT, "may leave at any time",
                     "12 cells east to west", "the chemistry world",
                     chemistry.world_key, "west end"):
            self.assertIn(part, doc)

    def test_its_doors_and_sizes_are_checked(self):
        key = Signer().token
        for law in ({"width": 0}, {"height": 1001}, {"width": "12"},
                    {"seed": 1.5},
                    {"doors": ("a door",)},
                    {"doors": (Door((0, 0), "world:x", key),)},   # entrance
                    {"doors": (Door((12, 0), "world:x", key),)},  # outside
                    {"doors": (Door((5, 0), "world:x", "nokey"),)},
                    {"doors": (Door((5, 0), "world:x", key),
                               Door((5, 0), "world:y", key))},
                    {"doors": (Door((5, 0), "world:x", key),
                               Door((6, 0), "world:x", key))}):
            with self.subTest(law=law), self.assertRaises(ValueError):
                CorridorWorldLaw(**law)


class TestWalking(Case):

    def test_newcomers_fill_the_entrance_then_wait(self):
        w = _corridor(height=2)
        alice, bob = self.enter(w, "Alice"), self.enter(w, "Bob")
        self.assertEqual((self.at(w, alice), self.at(w, bob)),
                         ((0, 0), (0, 1)))
        carol = make_client("Carol")
        r = petition_world(carol, w)
        self.assertIsInstance(r, Refusal)
        self.assertIn("entrance is crowded", r.reason)
        self.assertFalse(w.is_admitted(carol.individual.token))
        # The refusal names Carol: her petition's signature verified.
        refused = [e for e in w.log_since(None)
                   if e.kind == "petition_refused"][-1]
        self.assertEqual(refused.actor_token, carol.individual.token)
        act_on_world(alice, w, MOVE, EAST)
        self.assertIsInstance(petition_world(carol, w), Admission)
        self.assertEqual(self.at(w, carol), (0, 0))

    def test_moving_saying_waiting(self):
        w = _corridor()
        alice = self.enter(w)
        for step, cell in ((EAST, (1, 0)), ({"dx": 0, "dy": 1}, (1, 1)),
                           (WEST, (0, 1))):
            self.assertIsInstance(act_on_world(alice, w, MOVE, step), Ack)
            self.assertEqual(self.at(w, alice), cell)
        tick = w.kernel.tick
        self.assertIsInstance(act_on_world(alice, w, WAIT, {}), Ack)
        self.assertIsInstance(act_on_world(alice, w, SAY, {"text": "hello"}),
                              Ack)
        self.assertEqual(w.kernel.tick, tick + 2)
        said = [e for e in w.kernel.log if e["kind"] == "said"]
        self.assertEqual(said[-1]["data"], {"text": "hello"})

    def test_walls_and_others_block(self):
        w = _corridor(height=1)
        alice = self.enter(w, "Alice")
        act_on_world(alice, w, MOVE, EAST)
        bob = self.enter(w, "Bob")                           # at (0, 0)
        self.assertIsInstance(act_on_world(bob, w, MOVE, WEST), Ack)
        self.assertIsInstance(act_on_world(bob, w, MOVE, EAST), Ack)
        self.assertEqual((self.at(w, alice), self.at(w, bob)),
                         ((1, 0), (0, 0)))
        blocked = [e for e in w.kernel.log if e["kind"] == "blocked"]
        self.assertEqual(len(blocked), 2)

    def test_what_isnt_an_act_here_is_refused_and_takes_no_tick(self):
        w = _corridor()
        alice = self.enter(w)
        tick, log = w.kernel.tick, len(w.kernel.log)
        for act_type, payload, reason in (
                (MOVE, {"dx": 1, "dy": 1}, "dx and dy"),
                (MOVE, {"dx": 2, "dy": 0}, "dx and dy"),
                (MOVE, {"dx": True, "dy": 0}, "dx and dy"),
                (MOVE, {"dx": 1.0, "dy": 0}, "dx and dy"),
                (MOVE, {}, "dx and dy"),
                (SAY, {"text": ""}, "text must"),
                (SAY, {"text": "x" * 281}, "text must"),
                (SAY, {"text": 5}, "text must"),
                ("corridor.fly", {}, "Unknown act type"),
                ("chemistry.react", {}, "Unknown act type")):
            with self.subTest(act_type=act_type, payload=payload):
                r = act_on_world(alice, w, act_type, payload)
                self.assertIsInstance(r, Refusal)
                self.assertIn(reason, r.reason)
        self.assertEqual((w.kernel.tick, len(w.kernel.log)), (tick, log))
        stranger = Individual("Mallory")
        r = w.act(stranger.act(w.manifest(), MOVE, EAST))
        self.assertIsInstance(r, Refusal)
        r = w.act(Act(alice.individual.token, MOVE, {"dx": object()}))
        self.assertIsInstance(r, Refusal)

    def test_leaving_clears_the_cell_and_anyone_can_come_back(self):
        w = _corridor(height=1)
        alice = self.enter(w)
        self.assertFalse(leave_world(alice, w).already_left)
        self.assertIsNone(w.where(alice.individual.token))
        self.assertIsNone(w.kernel.occupant((0, 0)))
        exited = [e for e in w.kernel.log if e["kind"] == "exited"]
        self.assertEqual(len(exited), 1)
        bob = self.enter(w, "Bob")                  # the only entrance cell
        self.assertIsInstance(petition_world(alice, w), Refusal)  # crowded
        act_on_world(bob, w, MOVE, EAST)
        # Back again, with a new kernel id: the kernel never reuses one.
        self.assertIsInstance(petition_world(alice, w), Admission)
        entered = [e["agent"] for e in w.kernel.log
                   if e["kind"] == "entered"]
        self.assertEqual(len(entered), 3)
        self.assertEqual(len(set(entered)), 3)
        self.assertTrue(World.verify_log(w.kernel.log))

    def test_conformance(self):
        self.assertTrue(run_conformance(_corridor())["passed"])


class TestDoors(Case):

    def setUp(self):
        self.corridor, self.chemistry, self.poetry = build_worlds()

    def test_coming_back_through_a_door(self):
        alice = self.enter(self.corridor)
        door = self.corridor.doors()[0]
        self.assertEqual(walk_to(alice, self.corridor, door.cell), door.cell)
        self.assertEqual(
            self.corridor.where(alice.individual.token)["door"], door)
        leave_world(alice, self.corridor)
        self.assertIsInstance(petition_world(alice, self.chemistry),
                              Admission)
        leave_world(alice, self.chemistry)
        # Back from the chemistry world: at its door, not the entrance.
        self.assertIsInstance(petition_world(alice, self.corridor),
                              Admission)
        self.assertEqual(self.at(self.corridor, alice), door.cell)

    def test_an_occupied_door_sends_you_to_the_entrance(self):
        alice, bob = self.enter(self.corridor, "Alice"), make_client("Bob")
        door = self.corridor.doors()[0]
        self.assertIsInstance(petition_world(bob, self.chemistry), Admission)
        leave_world(bob, self.chemistry)
        walk_to(alice, self.corridor, door.cell)
        self.assertIsInstance(petition_world(bob, self.corridor), Admission)
        self.assertEqual(self.at(self.corridor, bob), (0, 0))

    def test_a_door_knows_the_key_of_the_world_beyond(self):
        # A stamp "from" the chemistry world under another key is refused
        # by the corridor, which knows the chemistry world's key from its
        # door; a world with no such door can't tell.
        mallory = make_client("Mallory")
        token = mallory.individual.token
        fake = make_stamp(Signer(), "arrival", "world:chemistry", token,
                          "2026-11-13T00:00:00+00:00")
        mallory.passport = Passport(mallory.individual.identity, (fake,))
        r = petition_world(mallory, self.corridor)
        self.assertIsInstance(r, Refusal)
        self.assertIn("isn't the one that world is known by", r.reason)
        stranger = PoetryWorld("world:elsewhere", "Elsewhere")
        self.assertIsInstance(petition_world(mallory, stranger), Admission)

    def test_knowing_a_world_needs_its_signed_manifest(self):
        m = self.chemistry.manifest()
        for bad in (dataclasses.replace(m, signature="00" * 64),
                    "not a manifest"):
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                self.poetry.know(bad)
        impostor = signed_manifest(Signer(), **{
            f: getattr(m, f) for f in ("entity_id", "name",
                                       "protocol_version", "law_url",
                                       "act_endpoint", "log_endpoint")})
        with self.assertRaises(ValueError):
            self.poetry.know(impostor)      # same id, another key
        self.assertEqual(self.poetry.known_keys()["world:chemistry"],
                         self.chemistry.world_key)
        self.assertEqual(self.poetry.known_keys()["world:poetry"],
                         self.poetry.world_key)


class TestTheFirstJourney(unittest.TestCase):

    def test_there_and_back(self):
        result = journey()
        corridor, chemistry, poetry = result["worlds"]
        alice = result["client"]
        check = result["check"]
        self.assertTrue(check.ok, check.problems)
        self.assertEqual(
            [(v.world_id, v.left, v.made) for v in check.visits],
            [("world:corridor", "stamped", 0),
             ("world:chemistry", "stamped", 1),
             ("world:poetry", "stamped", 1),
             ("world:corridor", "stamped", 0)])
        # Every world checked her passport against the keys it knows: each
        # stamp in another world's name is under that world's own key.
        for w in (corridor, chemistry, poetry):
            self.assertTrue(verify_passport(alice.passport,
                                            w.known_keys()).ok)
            kinds = [e.kind for e in w.log_since(None)
                     if e.actor_token == alice.individual.token]
            self.assertEqual(kinds.count("admission"),
                             kinds.count("departure"))
            self.assertFalse(w.is_admitted(alice.individual.token))
        self.assertTrue(World.verify_log(corridor.kernel.log))
        self.assertTrue(World.verify_log(chemistry.soup.log))
        self.assertEqual(len(result["steps"]), 8)

    def test_it_replays(self):
        a, b = journey(seed=3), journey(seed=3)
        self.assertEqual(a["worlds"][0].kernel.log[-1]["data"],
                         b["worlds"][0].kernel.log[-1]["data"])
        self.assertEqual([e["kind"] for e in a["worlds"][0].kernel.log],
                         [e["kind"] for e in b["worlds"][0].kernel.log])


if __name__ == "__main__":
    unittest.main()

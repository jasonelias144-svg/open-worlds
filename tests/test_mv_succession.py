"""Signing a key over to a new one (course step 6, part two).

The step's promises, each tested here:
  - a succession needs both keys: the old one hands over, the new one
    accepts, and it names whose key it is;
  - after it, the stamps given to the old key count for the new one,
    wherever the passport is checked, and the old key is retired: a world
    that knows the succession refuses its petitions and acts, but not its
    leave;
  - a key is signed over once: a second succession of the same key (a
    stolen key signing over again) is refused;
  - a world signs its own key over while people are inside, and their
    stays still verify;
  - a world's timestamps only grow, so two stamps it gives are never the
    same, even on a coarse clock.
"""
import dataclasses
import unittest
from datetime import datetime, timezone
from unittest import mock

from multiverse.collaboration import (act_on_world, leave_world, make_client,
                                      petition_world)
from multiverse.conformance import run_conformance
from multiverse.corridor_world import (CorridorWorld, CorridorWorldLaw,
                                       Door)
from multiverse.identity import Identity, Individual, Signer
from multiverse.passport import (Passport, from_dict, make_stamp, to_dict,
                                 verify_passport)
from multiverse.poetry_world import PoetryWorld
from multiverse.protocol import (Ack, Admission, Departure, Refusal,
                                 manifest_problem)
from multiverse.succession import (Lineage, Succession, sign_over,
                                   succession_problem)

T = "2026-11-13T00:00:00+00:00"
TURN = {"acknowledgment": "(seed)", "proposal": "Hope is the thing",
        "invitation": "What perches?", "holds_open": True}


def turn(i=0):
    return dict(TURN, acknowledgment=f"perches {i}",
                proposal=f"the thing with feathers {i}",
                invitation=f"what perches {i}?")


def visit(world, client, turns=1):
    assert isinstance(petition_world(client, world), Admission)
    for i in range(turns):
        assert isinstance(act_on_world(client, world, "poem.turn", turn(i)),
                          Ack)
    assert not leave_world(client, world).already_left


class TestTheRecord(unittest.TestCase):

    def setUp(self):
        self.old, self.new = Signer(), Signer()
        self.s = sign_over(self.old, self.new, timestamp=T)

    def test_signed_by_both_keys(self):
        self.assertEqual(succession_problem(self.s), "")
        self.assertEqual((self.s.of, self.s.old, self.s.new),
                         ("", self.old.token, self.new.token))

    def test_each_signature_is_needed(self):
        other = Signer().sign(self.s.document())
        for name in ("old_signature", "new_signature"):
            for value in ("", other, "ab" * 64):
                with self.subTest(name=name, value=value[:4]):
                    self.assertNotEqual(succession_problem(
                        dataclasses.replace(self.s, **{name: value})), "")

    def test_one_key_cant_sign_for_both(self):
        # Hanging your history on someone else's key needs their key too.
        mallory, victim = Signer(), Signer()
        unsigned = Succession("", mallory.token, victim.token, T)
        forged = dataclasses.replace(
            unsigned, old_signature=mallory.sign(unsigned.document()),
            new_signature=mallory.sign(unsigned.document()))
        self.assertIn("new key's signature",
                      succession_problem(forged))
        stolen = dataclasses.replace(
            unsigned, old_signature=victim.sign(unsigned.document()),
            new_signature=victim.sign(unsigned.document()))
        self.assertIn("old key's signature", succession_problem(stolen))

    def test_change_anything_and_it_no_longer_verifies(self):
        for field, value in (("of", "world:a"), ("old", Signer().token),
                             ("new", Signer().token),
                             ("timestamp", "2026-11-14T00:00:00+00:00"),
                             ("wcp", "WCP/0.3")):
            with self.subTest(field=field):
                self.assertNotEqual(succession_problem(
                    dataclasses.replace(self.s, **{field: value})), "")

    def test_not_to_itself(self):
        with self.assertRaises(ValueError):
            sign_over(self.old, self.old)
        unsigned = Succession("", self.old.token, self.old.token, T)
        signature = self.old.sign(unsigned.document())
        self.assertIn("itself", succession_problem(dataclasses.replace(
            unsigned, old_signature=signature, new_signature=signature)))

    def test_it_names_two_usable_keys(self):
        for field in ("old", "new"):
            with self.subTest(field=field):
                self.assertIn("usable keys", succession_problem(
                    dataclasses.replace(self.s, **{field: "x" * 64})))

    def test_entries_round_trip(self):
        self.assertEqual(Succession.from_entry(self.s.entry()), self.s)
        for bad in (dict(self.s.entry(), time=3),
                    {k: v for k, v in self.s.entry().items() if k != "of"},
                    dict(self.s.entry(), entry="stamp"), [], None):
            with self.subTest(bad=str(bad)[:40]):
                with self.assertRaises(ValueError):
                    Succession.from_entry(bad)

    def test_not_plain_text_is_not_usable(self):
        class Sly(str):
            pass
        for field in ("of", "old", "timestamp"):
            with self.subTest(field=field):
                sly = dataclasses.replace(
                    self.s, **{field: Sly(getattr(self.s, field))})
                self.assertNotEqual(succession_problem(sly), "")
        self.assertNotEqual(succession_problem(self.s.entry()), "")


class TestLineage(unittest.TestCase):

    def setUp(self):
        self.a, self.b, self.c = Signer(), Signer(), Signer()
        self.ab = sign_over(self.a, self.b)
        self.bc = sign_over(self.b, self.c)

    def test_a_line_of_keys(self):
        lineage = Lineage([self.bc, self.ab])
        a, b, c = self.a.token, self.b.token, self.c.token
        self.assertEqual(lineage.latest("", a), c)
        self.assertTrue(lineage.leads_to("", a, c))
        self.assertFalse(lineage.leads_to("", c, a))
        self.assertEqual(lineage.earlier_keys("", c), [b, a])
        self.assertTrue(lineage.retired("", a))
        self.assertFalse(lineage.retired("", c))
        # Successions of a world don't link an individual's keys.
        self.assertFalse(lineage.leads_to("world:a", a, b))

    def test_signed_over_once(self):
        lineage = Lineage([self.ab])
        again = sign_over(self.a, Signer())
        self.assertIn("already signed over", lineage.add(again))
        self.assertEqual(lineage.add(self.ab), "")
        self.assertEqual(lineage.latest("", self.a.token), self.b.token)

    def test_never_a_merge(self):
        lineage = Lineage([self.ab])
        self.assertIn("continues another",
                      lineage.add(sign_over(Signer(), self.b)))

    def test_a_circle_ends(self):
        lineage = Lineage([self.ab, sign_over(self.b, self.a)])
        a, b = self.a.token, self.b.token
        self.assertIn(lineage.latest("", a), (a, b))
        self.assertTrue(lineage.leads_to("", a, b))
        self.assertTrue(lineage.retired("", a) and lineage.retired("", b))
        self.assertEqual(lineage.earlier_keys("", a), [b])

    def test_unusable_ones_are_not_taken(self):
        lineage = Lineage([dataclasses.replace(self.ab, old_signature="")])
        self.assertEqual(lineage.successions(), [])


class TestPassportsAcrossKeys(unittest.TestCase):

    def setUp(self):
        self.poetry = PoetryWorld("world:poetry", "Poetry")
        self.other = PoetryWorld("world:other", "Other")
        self.other.know(self.poetry.manifest())
        self.alice = make_client("Alice")
        visit(self.poetry, self.alice, turns=2)
        self.first_key = self.alice.individual.token

    def test_old_stamps_count_for_the_new_key(self):
        s = self.alice.sign_over()
        p = self.alice.passport
        self.assertEqual(p.identity, Identity(s.new, "Alice"))
        check = verify_passport(p, self.other.known_keys())
        self.assertTrue(check.ok, check.problems)
        self.assertEqual(check.earlier_keys, (self.first_key,))
        visit_, = check.visits
        self.assertEqual((visit_.world_id, visit_.left, visit_.made),
                         ("world:poetry", "stamped", 2))
        # And a world admits it, and stamps the new key.
        visit(self.other, self.alice)
        self.assertTrue(verify_passport(self.alice.passport).ok)

    def test_a_line_of_three_keys(self):
        self.alice.sign_over()
        visit(self.other, self.alice)
        self.alice.sign_over()
        check = verify_passport(self.alice.passport,
                                self.poetry.known_keys())
        self.assertTrue(check.ok, check.problems)
        self.assertEqual(len(check.earlier_keys), 2)
        self.assertEqual(len(check.visits), 2)
        # Round trip, as a petition carries it.
        again = from_dict(to_dict(self.alice.passport))
        self.assertEqual(again, self.alice.passport)

    def test_without_the_succession_they_are_someone_elses(self):
        s = self.alice.sign_over()
        p = self.alice.passport
        bare = Passport(p.identity, p.stamps, p.leaves)
        check = verify_passport(bare)
        self.assertIn("for another individual", check.problems[0])
        self.assertTrue(any("another individual's" in problem
                            for problem in check.problems))
        self.assertTrue(verify_passport(bare.with_succession(s)).ok)

    def test_a_retired_holder(self):
        p = self.alice.passport
        s = sign_over(self.alice.individual, Signer())
        check = verify_passport(p.with_succession(s))
        self.assertIn("holder's key has been signed over", check.problems[0])

    def test_signed_over_twice(self):
        old = self.alice.individual
        self.alice.sign_over()
        fork = sign_over(old, Individual("Mallory"))
        check = verify_passport(self.alice.passport.with_succession(fork))
        self.assertIn("already signed over", check.problems[0])
        # A checker that knows the other one refuses this passport too.
        check = verify_passport(self.alice.passport, successions=(fork,))
        self.assertFalse(check.ok)

    def test_repeated_or_broken_successions(self):
        s = self.alice.sign_over()
        p = self.alice.passport
        self.assertIn("repeats", verify_passport(
            p.with_succession(s)).problems[0])
        broken = dataclasses.replace(s, new_signature="")
        self.assertIn("signature", verify_passport(
            Passport(p.identity, p.stamps, p.leaves, (broken,))
        ).problems[0])

    def test_someone_elses_succession_adopts_nothing(self):
        # Mallory carries Alice's stamps and her own succession: they are
        # still Alice's.
        mallory = make_client("Mallory")
        mallory.sign_over()
        p = mallory.passport
        stolen = Passport(p.identity, self.alice.passport.stamps, p.leaves,
                          p.successions)
        self.assertIn("another individual", verify_passport(stolen)
                      .problems[0])

    def test_signed_over_checks_its_succession(self):
        p = self.alice.passport
        new = Signer()
        for bad in (sign_over(Signer(), new),
                    sign_over(self.alice.individual, new, of="world:a"),
                    dataclasses.replace(sign_over(self.alice.individual,
                                                  new), new_signature="")):
            with self.subTest(of=bad.of):
                with self.assertRaises(ValueError):
                    p.signed_over(bad)
        self.assertEqual(p.signed_over(sign_over(self.alice.individual, new),
                                       name="Alicia").identity.name,
                         "Alicia")

    def test_the_client_carries_only_what_fits(self):
        world_key, other = Signer(), Signer()
        good = sign_over(world_key, other, of="world:x")
        before = self.alice.passport
        for bad in (sign_over(world_key, Signer(), of=""),
                    dataclasses.replace(good, new_signature=""),
                    good.entry()):
            self.alice.carry(bad)
        self.assertEqual(self.alice.passport, before)
        self.alice.carry(good)
        self.alice.carry(good)
        self.alice.carry(sign_over(world_key, Signer(), of="world:x"))
        self.assertEqual(self.alice.passport.successions, (good,))

    def test_leaving_carries_only_the_worlds_own(self):
        elsewhere = sign_over(Signer(), Signer(), of="world:elsewhere")

        class Chatty(PoetryWorld):
            def successions(self, of=None):
                return super().successions(of) + [elsewhere]

        chatty = Chatty("world:chatty", "Chatty")
        assert isinstance(petition_world(self.alice, chatty), Admission)
        s = chatty.sign_over(Signer())
        leave_world(self.alice, chatty)
        self.assertIn(s, self.alice.passport.successions)
        self.assertNotIn(elsewhere, self.alice.passport.successions)

    def test_the_client_leaves_first(self):
        assert isinstance(petition_world(self.alice, self.other), Admission)
        with self.assertRaises(ValueError):
            self.alice.sign_over()


class TestWorldsKnowRetiredKeys(unittest.TestCase):

    def setUp(self):
        self.world = PoetryWorld("world:poetry", "Poetry")
        self.m = self.world.manifest()
        self.a = Individual("Alice")
        self.b = Individual("Alice")
        self.s = sign_over(self.a, self.b)

    def test_a_retired_key_cant_enter(self):
        self.world.know_succession(self.s)
        response = self.world.petition(self.a.petition(self.m))
        self.assertIsInstance(response, Refusal)
        self.assertIn("this key has been signed over to another key; "
                      "petition with that one", response.reason)
        self.assertIsInstance(self.world.petition(self.b.petition(
            self.m, Passport(self.a.identity).signed_over(self.s).entries()
        )), Admission)

    def test_learned_from_a_passport(self):
        shown = Passport(self.a.identity).signed_over(self.s)
        self.assertIsInstance(self.world.petition(self.b.petition(
            self.m, shown.entries())), Admission)
        self.assertIn(self.s, self.world.successions())
        response = self.world.petition(self.a.petition(self.m))
        self.assertIsInstance(response, Refusal)
        self.assertIn("signed over", response.reason)

    def test_a_retired_key_can_leave_but_not_act(self):
        self.assertIsInstance(self.world.petition(self.a.petition(self.m)),
                              Admission)
        self.world.know_succession(self.s)
        response = self.world.act(self.a.act(self.m, "poem.turn", turn()))
        self.assertIsInstance(response, Refusal)
        self.assertIn("signed over", response.reason)
        response = self.world.leave(self.a.leave(self.m))
        self.assertIsInstance(response, Departure)
        self.assertFalse(response.already_left)

    def test_not_twice_in_one_world(self):
        self.assertIsInstance(self.world.petition(self.a.petition(self.m)),
                              Admission)
        shown = Passport(self.a.identity).signed_over(self.s).entries()
        response = self.world.petition(self.b.petition(self.m, shown))
        self.assertIsInstance(response, Refusal)
        self.assertIn("earlier key", response.reason)
        self.world.leave(self.a.leave(self.m))
        self.assertIsInstance(
            self.world.petition(self.b.petition(self.m, shown)), Admission)

    def test_a_second_succession_is_refused(self):
        self.world.know_succession(self.s)
        with self.assertRaises(ValueError):
            self.world.know_succession(sign_over(self.a, Signer()))
        # And a passport that carries it.
        thief = Individual("Thief")
        fork = sign_over(self.a, thief)
        response = self.world.petition(thief.petition(
            self.m, Passport(self.a.identity).signed_over(fork).entries()))
        self.assertIsInstance(response, Refusal)
        self.assertIn("already signed over", response.reason)

    def test_unusable_successions_are_refused(self):
        for bad in (dataclasses.replace(self.s, old_signature=""),
                    self.s.entry(), None):
            with self.subTest(bad=type(bad).__name__):
                with self.assertRaises(ValueError):
                    self.world.know_succession(bad)


class TestWorldsSignOver(unittest.TestCase):

    def setUp(self):
        self.k1, self.k2 = Signer(), Signer()
        self.poetry = PoetryWorld("world:poetry", "Poetry", key=self.k1)
        self.old_manifest = self.poetry.manifest()
        self.knows_old = PoetryWorld("world:old", "Knows the old key")
        self.knows_old.know(self.old_manifest)
        self.alice = make_client("Alice")
        assert isinstance(petition_world(self.alice, self.poetry), Admission)
        act_on_world(self.alice, self.poetry, "poem.turn", turn(0))

    def test_a_stay_across_the_change_still_verifies(self):
        s = self.poetry.sign_over(self.k2)
        self.assertEqual((s.of, s.old, s.new),
                         ("world:poetry", self.k1.token, self.k2.token))
        self.assertIsInstance(
            act_on_world(self.alice, self.poetry, "poem.turn", turn(1)), Ack)
        self.assertFalse(leave_world(self.alice, self.poetry).already_left)
        p = self.alice.passport
        self.assertIn(s, p.successions)
        # Arrival and first turn by the old key; the rest by the new.
        self.assertEqual([x.world_key for x in p.stamps],
                         [self.k1.token] * 2 + [self.k2.token] * 2)
        knows_new = PoetryWorld("world:new", "Knows the new key")
        knows_new.know(self.poetry.manifest())
        for checker in (self.knows_old, knows_new):
            with self.subTest(checker=checker.manifest().entity_id):
                check = verify_passport(p, checker.known_keys())
                self.assertTrue(check.ok, check.problems)
                v, = check.visits
                self.assertEqual((v.left, v.made), ("stamped", 2))
                self.assertIsInstance(petition_world(self.alice, checker),
                                      Admission)

    def test_without_its_succession_the_stay_doesnt_verify(self):
        s = self.poetry.sign_over(self.k2)
        leave_world(self.alice, self.poetry)
        p = self.alice.passport
        bare = Passport(p.identity, p.stamps, p.leaves,
                        tuple(x for x in p.successions if x != s))
        self.assertFalse(verify_passport(bare).ok)

    def test_the_new_key_signs_everything(self):
        s = self.poetry.sign_over(self.k2)
        act_on_world(self.alice, self.poetry, "poem.turn", turn(1))
        m = self.poetry.manifest()
        self.assertEqual(manifest_problem(m), "")
        self.assertEqual((m.entity_id, m.name, m.world_key),
                         ("world:poetry", "Poetry", self.k2.token))
        self.assertEqual(self.poetry.known_keys()["world:poetry"],
                         self.k2.token)
        logged = [e.data for e in self.poetry.log_since()
                  if e.kind == "signed_over"]
        self.assertEqual(logged, [{"succession": s.entry()}])
        held = self.poetry.passport_of(self.alice.individual.token)
        self.assertTrue(verify_passport(held).ok)
        self.assertTrue(run_conformance(self.poetry)["passed"])

    def test_requests_for_the_old_key_are_refused(self):
        self.poetry.sign_over(self.k2)
        bob = Individual("Bob")
        self.assertIsInstance(
            self.poetry.petition(bob.petition(self.old_manifest)), Refusal)
        self.assertIsInstance(
            self.poetry.petition(bob.petition(self.poetry.manifest())),
            Admission)

    def test_others_follow_it_to_the_new_key(self):
        s = self.poetry.sign_over(self.k2)
        new_manifest = self.poetry.manifest()
        with self.assertRaises(ValueError):
            self.knows_old.know(new_manifest)
        self.knows_old.know_succession(s)
        self.assertEqual(self.knows_old.known_keys()["world:poetry"],
                         self.k2.token)
        self.knows_old.know(new_manifest)
        with self.assertRaises(ValueError):
            self.knows_old.know(self.old_manifest)
        # A world that hasn't met it yet refuses the old manifest too,
        # once it knows the succession.
        fresh = PoetryWorld("world:fresh", "Fresh")
        fresh.know_succession(s)
        with self.assertRaises(ValueError):
            fresh.know(self.old_manifest)

    def test_only_sign_over_signs_its_own_key(self):
        s = self.poetry.sign_over(self.k2)
        self.poetry.know_succession(s)      # its own: nothing changes
        stolen = sign_over(self.k2, Signer(), of="world:poetry")
        with self.assertRaisesRegex(ValueError, "own key"):
            self.poetry.know_succession(stolen)
        self.assertEqual(self.poetry.world_key, self.k2.token)
        with self.assertRaises(ValueError):
            self.poetry.sign_over(self.k2)
        # Shown in a passport, it isn't taken either, so a thief of the
        # key can't stop the world from signing over.
        bob = make_client("Bob")
        bob.passport = bob.passport.with_succession(stolen)
        petition_world(bob, self.poetry)
        self.assertNotIn(stolen, self.poetry.successions())
        k3 = Signer()
        self.assertEqual(self.poetry.sign_over(k3).new, k3.token)

    def test_a_restarted_world_takes_back_its_past(self):
        # Restarted with its latest key, it doesn't remember its own
        # successions; they lead to its key, so it takes them back, in
        # any order, from a passport or directly.
        s12 = self.poetry.sign_over(self.k2)
        k3 = Signer()
        s23 = self.poetry.sign_over(k3)
        again = PoetryWorld("world:poetry", "Poetry", key=k3)
        again.know_succession(s23)
        again.know_succession(s12)
        self.assertEqual(again.successions(), [s23, s12])
        later = PoetryWorld("world:poetry", "Poetry", key=k3)
        carol = make_client("Carol")
        for x in (s12, s23):
            carol.passport = carol.passport.with_succession(x)
        self.assertIsInstance(petition_world(carol, later), Admission)
        self.assertEqual(len(later.successions("world:poetry")), 2)

    def test_a_world_signs_over_once(self):
        self.poetry.sign_over(self.k2)
        k3 = Signer()
        self.poetry.sign_over(k3)
        self.assertEqual(len(self.poetry.successions("world:poetry")), 2)
        self.knows_old.know_succession(
            self.poetry.successions("world:poetry")[1])
        self.knows_old.know_succession(
            self.poetry.successions("world:poetry")[0])
        self.assertEqual(self.knows_old.known_keys()["world:poetry"],
                         k3.token)


class TestDoorsAcrossKeys(unittest.TestCase):

    def test_an_individual_signed_over_still_comes_back_through_its_door(
            self):
        poetry = PoetryWorld("world:poetry", "Poetry")
        door = Door((5, 1), "world:poetry", poetry.world_key, "poetry")
        corridor = CorridorWorld("world:corridor", "Corridor",
                                 CorridorWorldLaw(doors=(door,)))
        alice = make_client("Alice")
        visit(poetry, alice)
        alice.sign_over()
        assert isinstance(petition_world(alice, corridor), Admission)
        self.assertEqual(corridor.where(alice.individual.token)["cell"],
                         (5, 1))


class TestDoorsKnowSuccessions(unittest.TestCase):

    def test_a_door_to_a_world_that_signed_over(self):
        # The passport doesn't carry the world's succession; the corridor
        # knows it, and so still finds the door.
        poetry = PoetryWorld("world:poetry", "Poetry")
        alice = make_client("Alice")
        visit(poetry, alice)
        s = poetry.sign_over(Signer())
        door = Door((5, 1), "world:poetry", poetry.world_key, "poetry")
        corridor = CorridorWorld("world:corridor", "Corridor",
                                 CorridorWorldLaw(doors=(door,)))
        corridor.know_succession(s)
        self.assertNotIn(s, alice.passport.successions)
        assert isinstance(petition_world(alice, corridor), Admission)
        self.assertEqual(corridor.where(alice.individual.token)["cell"],
                         (5, 1))


class TestTimestampsOnlyGrow(unittest.TestCase):

    def test_two_visits_in_one_tick_give_different_stamps(self):
        world = PoetryWorld("world:poetry", "Poetry")
        alice = make_client("Alice")
        fixed = datetime(2026, 11, 13, tzinfo=timezone.utc)
        with mock.patch("multiverse.entity.datetime") as clock:
            clock.now.return_value = fixed
            visit(world, alice, turns=1)
            visit(world, alice, turns=1)
        times = [e.timestamp for e in world.log_since()]
        self.assertEqual(times, sorted(set(times)))
        stamps = alice.passport.stamps
        self.assertEqual(len({s.fingerprint() for s in stamps}), 6)
        check = verify_passport(alice.passport)
        self.assertTrue(check.ok, check.problems)
        self.assertEqual(len(check.visits), 2)

    def test_a_clock_that_goes_back(self):
        world = PoetryWorld("world:poetry", "Poetry")
        alice = make_client("Alice")
        late = datetime(2026, 11, 13, 12, tzinfo=timezone.utc)
        early = datetime(2026, 11, 13, 11, tzinfo=timezone.utc)
        with mock.patch("multiverse.entity.datetime") as clock:
            clock.now.return_value = late
            visit(world, alice, turns=0)
            clock.now.return_value = early
            visit(world, alice, turns=0)
        times = [e.timestamp for e in world.log_since()]
        self.assertEqual(times, sorted(set(times)))


class TestStampsStillName(unittest.TestCase):

    def test_a_stay_is_one_keys(self):
        # A departure given to the new key can't close an arrival given
        # to the old one, even though both are the holder's.
        world, a, b = Signer(), Individual("A"), Individual("A")
        s = sign_over(a, b)
        arrival = make_stamp(world, "arrival", "world:a", a.token, T)
        departure = make_stamp(world, "departure", "world:a", b.token, T,
                               arrival=arrival.fingerprint())
        check = verify_passport(Passport(b.identity, (arrival, departure),
                                         (), (s,)))
        self.assertIn("names no arrival", check.problems[0])

    def test_a_stamp_for_an_earlier_key_names_that_key(self):
        # The stamp stays what the world signed: it names the key the
        # individual had then.
        world, a, b = Signer(), Individual("A"), Individual("A")
        s = sign_over(a, b)
        stamp = make_stamp(world, "arrival", "world:a", a.token, T)
        p = Passport(b.identity, (stamp,), (), (s,))
        check = verify_passport(p)
        self.assertTrue(check.ok, check.problems)
        self.assertEqual(p.stamps[0].holder, a.token)


if __name__ == "__main__":
    unittest.main()

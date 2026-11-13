"""Signed passports (course step 3): worlds sign stamps for arrivals,
departures and what was made, and anyone can check a passport offline.

The step's promises, each tested here:
  - any world can check a passport without asking anyone;
  - a forged or altered stamp is refused;
  - a world that won't stamp a departure can't stop it: the missing
    stamp is itself on the record;
  - requests name the world's key (test_mv_poetry_world.py and
    test_mv_registry.py test that a world copying an id is refused).
"""
import dataclasses
import unittest
from unittest import mock

from multiverse.chemistry_world import ChemistryWorld
from multiverse.collaboration import (act_on_world, leave_world, make_client,
                                      petition_world)
from multiverse.conformance import run_conformance
from multiverse.identity import Individual, Signer
from multiverse.passport import (LeaveNote, Passport, Stamp, fingerprint,
                                 from_dict, make_stamp, thing_fingerprint,
                                 to_dict, verify_passport)
from multiverse.poetry_world import PoetryWorld
from multiverse.protocol import Admission, Departure, Petition, Refusal

T = "2026-11-13T00:00:00+00:00"
TURN = {"acknowledgment": "(seed)", "proposal": "Hope is the thing",
        "invitation": "What perches?", "holds_open": True}


def _visit(world, client, turns=0):
    """`client` enters `world`, adds `turns` turns, and leaves."""
    assert isinstance(petition_world(client, world), Admission)
    for i in range(turns):
        act_on_world(client, world, "poem.turn",
                     dict(TURN, acknowledgment=f"perches {i}",
                          proposal=f"the thing with feathers {i}",
                          invitation=f"what perches {i}?"))
    assert not leave_world(client, world).already_left


class TestStamps(unittest.TestCase):

    def setUp(self):
        self.world = Signer()
        self.alice = Individual("Alice")

    def stamp(self, kind="arrival", **extra):
        return make_stamp(self.world, kind, "world:a", self.alice.token, T,
                          **extra)

    def test_a_stamp_verifies_against_the_key_it_names(self):
        s = self.stamp()
        self.assertEqual(s.world_key, self.world.token)
        self.assertTrue(s.verifies())

    def test_change_anything_and_it_no_longer_verifies(self):
        s = self.stamp()
        for field, value in (("kind", "departure"), ("world_id", "world:b"),
                             ("holder", Individual("Bob").token),
                             ("timestamp", "2026-11-14T00:00:00+00:00"),
                             ("arrival", "ab" * 32), ("made", "cd" * 32),
                             ("world_key", Signer().token),
                             ("signature", "ef" * 64)):
            with self.subTest(field=field):
                self.assertFalse(
                    dataclasses.replace(s, **{field: value}).verifies())

    def test_fingerprints_change_with_anything(self):
        s = self.stamp()
        self.assertEqual(len(s.fingerprint()), 64)
        self.assertEqual(s.fingerprint(), fingerprint(s.entry()))
        self.assertNotEqual(
            s.fingerprint(),
            dataclasses.replace(s, timestamp="2026-11-14T00:00:00+00:00")
            .fingerprint())
        self.assertNotEqual(thing_fingerprint({"a": 1}),
                            thing_fingerprint({"a": 2}))

    def test_a_stamp_keeps_its_protocol_version(self):
        # Signed under one version, it still verifies when the code
        # speaks another; changing the version it names breaks it.
        s = self.stamp()
        self.assertEqual(s.wcp, "WCP/0.3")
        with mock.patch("multiverse.passport.PROTOCOL_VERSION", "WCP/9.9"):
            self.assertTrue(Stamp.from_entry(s.entry()).verifies())
        self.assertFalse(dataclasses.replace(s, wcp="WCP/0.4").verifies())
        for entry in (dict(s.entry(), wcp=3), {k: v for k, v in
                                                s.entry().items()
                                                if k != "wcp"}):
            with self.assertRaises(ValueError):
                Stamp.from_entry(entry)

    def test_entries_round_trip(self):
        s = self.stamp("made", arrival="ab" * 32, made="cd" * 32)
        self.assertEqual(Stamp.from_entry(s.entry()), s)
        self.assertTrue(Stamp.from_entry(s.entry()).verifies())

    def test_odd_entries_are_refused_not_raised(self):
        good = self.stamp().entry()
        for entry in (None, "stamp", [], {}, {"entry": "leave"},
                      dict(good, world=5), dict(good, signature=None),
                      dict(good, time=["t"])):
            with self.subTest(entry=entry), self.assertRaises(ValueError):
                Stamp.from_entry(entry)

    def test_only_three_kinds(self):
        with self.assertRaises(ValueError):
            self.stamp("visa")


class TestVerifyPassport(unittest.TestCase):
    """verify_passport: offline, by the keys in the stamps alone."""

    def setUp(self):
        self.poetry = PoetryWorld("world:poetry", "Poetry")
        self.chemistry = ChemistryWorld("world:chemistry", "Chemistry")
        self.alice = make_client("Alice")

    def test_a_real_journey_verifies(self):
        _visit(self.poetry, self.alice, turns=2)
        assert isinstance(petition_world(self.alice, self.chemistry),
                          Admission)
        check = verify_passport(self.alice.passport)
        self.assertTrue(check.ok, check.problems)
        self.assertEqual(
            [(v.world_id, v.left, v.made) for v in check.visits],
            [("world:poetry", "stamped", 2), ("world:chemistry", "", 0)])

    def test_an_empty_passport_verifies(self):
        check = verify_passport(Passport(self.alice.identity))
        self.assertTrue(check.ok)
        self.assertEqual(check.visits, ())

    def test_a_forged_stamp_is_found(self):
        # Mallory signs an arrival "from" the poetry world with her own
        # key, claiming the world's key.
        forger = Signer()
        real_key = self.poetry.world_key
        fake = make_stamp(forger, "arrival", "world:poetry",
                          self.alice.individual.token, T)
        claimed = dataclasses.replace(fake, world_key=real_key)
        check = verify_passport(Passport(self.alice.identity, (claimed,)))
        self.assertFalse(check.ok)
        self.assertIn("does not verify", check.problems[0])

    def test_a_stamp_proves_its_key_not_its_world(self):
        # Anyone can make a key and stamp "from" the poetry world with it.
        # The stamp verifies: it shows only which key signed. A checker
        # that knows the poetry world's key, from its manifest, sees it.
        self_made = make_stamp(Signer(), "arrival", "world:poetry",
                               self.alice.individual.token, T)
        p = Passport(self.alice.identity, (self_made,))
        self.assertTrue(verify_passport(p).ok)
        check = verify_passport(
            p, {"world:poetry": self.poetry.manifest().world_key})
        self.assertIn("isn't the one that world is known by",
                      check.problems[0])
        self.assertEqual(check.visits, ())
        # A real stamp passes the same check.
        _visit(self.poetry, self.alice)
        self.assertTrue(verify_passport(
            self.alice.passport,
            {"world:poetry": self.poetry.manifest().world_key}).ok)

    def test_an_altered_stamp_is_found(self):
        _visit(self.poetry, self.alice)
        arrival, *rest = self.alice.passport.stamps
        earlier = dataclasses.replace(arrival,
                                      timestamp="2020-01-01T00:00:00+00:00")
        p = Passport(self.alice.identity, (earlier, *rest))
        check = verify_passport(p)
        self.assertFalse(check.ok)
        self.assertTrue(any("does not verify" in x for x in check.problems))

    def test_someone_elses_stamp_is_found(self):
        bob = make_client("Bob")
        _visit(self.poetry, bob)
        p = Passport(self.alice.identity, bob.passport.stamps)
        check = verify_passport(p)
        self.assertFalse(check.ok)
        self.assertIn("another individual", check.problems[0])

    def test_a_departure_must_name_an_arrival_of_the_same_world(self):
        _visit(self.poetry, self.alice)
        arrival, departure = self.alice.passport.stamps
        # Without its arrival:
        check = verify_passport(Passport(self.alice.identity, (departure,)))
        self.assertIn("names no arrival", check.problems[0])
        # With an arrival from another world under the same fingerprint
        # it can't be: a departure signed by another key over the same
        # arrival is a different world's claim.
        other = make_stamp(Signer(), "departure", "world:poetry",
                           self.alice.individual.token, T,
                           arrival=arrival.fingerprint())
        check = verify_passport(Passport(self.alice.identity,
                                         (arrival, other)))
        self.assertIn("names no arrival", check.problems[0])

    def test_one_key_cant_close_an_arrival_under_another_id(self):
        key = Signer()
        a = self.alice.individual.token
        arrival = make_stamp(key, "arrival", "world:a", a, T)
        departure = make_stamp(key, "departure", "world:b", a, T,
                               arrival=arrival.fingerprint())
        check = verify_passport(Passport(self.alice.identity,
                                         (arrival, departure)))
        self.assertIn("names no arrival", check.problems[0])

    def test_a_signed_stamp_of_another_kind_is_found(self):
        # make_stamp won't make one, but a key can sign anything.
        key = Signer()
        a = self.alice.individual.token
        arrival = make_stamp(key, "arrival", "world:a", a, T)
        unsigned = Stamp("visa", "world:a", key.token, a, T,
                         arrival=arrival.fingerprint())
        visa = dataclasses.replace(unsigned,
                                   signature=key.sign(unsigned.document()))
        self.assertTrue(visa.verifies())
        check = verify_passport(Passport(self.alice.identity,
                                         (arrival, visa)))
        self.assertIn("not a kind of stamp", check.problems[0])
        self.assertEqual(check.visits[0].made, 0)

    def test_one_departure_per_arrival(self):
        _visit(self.poetry, self.alice)
        arrival, departure = self.alice.passport.stamps
        twice = Passport(self.alice.identity, (arrival, departure, departure))
        self.assertIn("already has a departure",
                      verify_passport(twice).problems[0])

    def test_odd_stamps_are_reported_not_raised(self):
        odd = Stamp("visa", "world:x", "not a key", "nobody", "t",
                    signature="zz")
        check = verify_passport(Passport(self.alice.identity, (odd,)))
        self.assertFalse(check.ok)

    def test_passports_round_trip(self):
        _visit(self.poetry, self.alice, turns=1)
        p = from_dict(to_dict(self.alice.passport))
        self.assertEqual(p, self.alice.passport)
        self.assertTrue(verify_passport(p).ok)

    def test_odd_passports_dont_read(self):
        leave = {"entry": "leave", "wcp": "WCP/0.3", "world": "world:a",
                 "world_key": "k", "holder": "h", "closes": "", "seq": 1,
                 "signature": ""}
        self.assertEqual(len(Passport.from_entries(
            self.alice.identity, [leave]).leaves), 1)
        for entries in ("x", "", {}, set(), [None], [{"entry": "visa"}],
                        [dict(leave, seq="1")], [dict(leave, seq=1.0)],
                        [dict(leave, seq=None)]):
            with self.subTest(entries=entries), self.assertRaises(ValueError):
                Passport.from_entries(self.alice.identity, entries)


class TestUnstampedDepartures(unittest.TestCase):
    """A world that won't stamp a departure can't stop it."""

    class Grudging(PoetryWorld):
        """Lets people go, but never stamps a departure."""
        def _departure_stamp(self, token, timestamp, arrival):
            return None

    def test_leaving_still_works_and_the_passport_shows_it(self):
        world = self.Grudging("world:grudging", "Grudging")
        alice = make_client("Alice")
        assert isinstance(petition_world(alice, world), Admission)
        response = leave_world(alice, world)
        self.assertIsInstance(response, Departure)
        self.assertFalse(response.already_left)
        self.assertIsNone(response.stamp)
        self.assertFalse(world.is_admitted(alice.individual.token))
        # Her own signed leave, naming the arrival, is in her passport:
        # the visit shows as ended on her word, with no departure stamp.
        check = verify_passport(alice.passport)
        self.assertTrue(check.ok, check.problems)
        visit, = check.visits
        self.assertEqual(visit.left, "unstamped")
        self.assertIsNone(alice.passport.open_arrival(world.world_key))
        # And the next world sees the same.
        poetry = PoetryWorld("world:poetry", "Poetry")
        self.assertIsInstance(petition_world(alice, poetry), Admission)
        self.assertEqual(
            [v.left for v in verify_passport(
                poetry.passport_of(alice.individual.token)).visits],
            ["unstamped", ""])

    def test_the_conformance_test_names_the_missing_stamp(self):
        result = run_conformance(self.Grudging("world:grudging", "G"))
        self.assertFalse(result["passed"])
        self.assertEqual(result["failures"],
                         ["the Departure carries no departure stamp"])

    def test_a_leave_note_must_be_the_holders_and_close_an_arrival(self):
        world = self.Grudging("world:grudging", "Grudging")
        alice = make_client("Alice")
        petition_world(alice, world)
        leave_world(alice, world)
        note, = alice.passport.leaves
        mallory = Individual("Mallory")
        for changed, problem in (
                (dataclasses.replace(note, closes="ab" * 32),
                 "does not verify"),
                (dataclasses.replace(note, holder=mallory.token),
                 "another individual's"),
                (dataclasses.replace(note, seq=note.seq + 1),
                 "does not verify")):
            with self.subTest(problem=problem):
                p = Passport(alice.identity, alice.passport.stamps,
                             (changed,))
                self.assertIn(problem, verify_passport(p).problems[0])
        # A real leave that closes no arrival in the passport:
        p = Passport(alice.identity, (), (note,))
        self.assertIn("closes no arrival", verify_passport(p).problems[0])
        # Her own leave, signed for the same id under another key, closes
        # nothing here.
        other = dataclasses.replace(world.manifest(),
                                    world_key=Signer().token)
        arrival, = alice.passport.stamps
        wrong = LeaveNote.of(other.entity_id, other.world_key,
                             alice.individual.leave(
                                 other, closes=arrival.fingerprint()))
        self.assertTrue(wrong.verifies())
        p = Passport(alice.identity, alice.passport.stamps, (wrong,))
        self.assertIn("closes no arrival", verify_passport(p).problems[0])

    def test_a_leave_names_its_arrival_as_text(self):
        world = PoetryWorld("world:poetry", "Poetry")
        alice = make_client("Alice")
        petition_world(alice, world)
        r = world.leave(alice.individual.leave(world.manifest(), closes=5))
        self.assertIsInstance(r, Refusal)
        self.assertTrue(world.is_admitted(alice.individual.token))
        self.assertFalse(leave_world(alice, world).already_left)

    def test_leave_notes_round_trip(self):
        world = self.Grudging("world:grudging", "Grudging")
        alice = make_client("Alice")
        petition_world(alice, world)
        leave_world(alice, world)
        note, = alice.passport.leaves
        self.assertEqual(LeaveNote.from_entry(note.entry()), note)
        self.assertTrue(note.verifies())
        self.assertEqual(note.wcp, "WCP/0.3")
        with mock.patch("multiverse.protocol.PROTOCOL_VERSION", "WCP/9.9"):
            self.assertTrue(note.verifies())
        self.assertFalse(dataclasses.replace(note, wcp="WCP/0.4").verifies())


class TestWorldsCheckPassports(unittest.TestCase):
    """A world checks a petitioner's passport before admitting, without
    asking the worlds that stamped it."""

    def setUp(self):
        self.poetry = PoetryWorld("world:poetry", "Poetry")
        self.chemistry = ChemistryWorld("world:chemistry", "Chemistry")
        self.alice = make_client("Alice")
        _visit(self.poetry, self.alice, turns=1)

    def petition(self, passport):
        a = self.alice.individual
        return self.chemistry.petition(
            a.petition(self.chemistry.manifest(), passport.entries()))

    def test_a_real_passport_is_accepted_and_kept(self):
        self.assertIsInstance(self.petition(self.alice.passport), Admission)
        kept = self.chemistry.passport_of(self.alice.individual.token)
        self.assertEqual(kept.worlds_visited(),
                         ["world:poetry", "world:chemistry"])
        self.assertTrue(verify_passport(kept).ok)

    def test_a_forged_or_altered_stamp_is_refused(self):
        arrival, made, departure = self.alice.passport.stamps
        forged = make_stamp(Signer(), "made", "world:poetry",
                            self.alice.individual.token, T,
                            arrival=arrival.fingerprint(),
                            made=thing_fingerprint({"prize": "first"}))
        for name, stamps in (
                ("forged", (arrival, dataclasses.replace(
                    forged, world_key=arrival.world_key), departure)),
                ("altered", (arrival, dataclasses.replace(
                    made, made=thing_fingerprint({"prize": "first"})),
                    departure))):
            with self.subTest(stamp=name):
                r = self.petition(Passport(self.alice.identity, stamps))
                self.assertIsInstance(r, Refusal)
                self.assertIn("doesn't verify", r.reason)
        self.assertFalse(
            self.chemistry.is_admitted(self.alice.individual.token))
        # The refusal names Alice: she signed the petition that carried it.
        refused = [e for e in self.chemistry.log_since(None)
                   if e.kind == "petition_refused"]
        self.assertEqual({e.actor_token for e in refused},
                         {self.alice.individual.token})

    def test_a_world_knows_its_own_key(self):
        # A stamp "from" this very world, under another key, is refused.
        # One from a world it doesn't know can't be told apart (see
        # passport.py): it shows only the key that signed it.
        a = self.alice.individual
        fake_here = make_stamp(Signer(), "arrival", "world:chemistry",
                               a.token, T)
        r = self.petition(self.alice.passport.with_stamp(fake_here))
        self.assertIsInstance(r, Refusal)
        self.assertIn("isn't the one that world is known by", r.reason)
        elsewhere = make_stamp(Signer(), "arrival", "world:unknown",
                               a.token, T)
        self.assertIsInstance(
            self.petition(self.alice.passport.with_stamp(elsewhere)),
            Admission)

    def test_a_passport_that_isnt_plain_entries_is_refused(self):
        # Built by hand, as another client might send them: our own
        # Individual can't sign these. The world reads the passport
        # before it checks the signature, so this one needn't verify.
        a = self.alice.individual
        good = self.alice.passport.entries()[0]
        for passport in ("not a list", ("not an entry",),
                         ({"entry": "visa"},),
                         ({"entry": "stamp", "world": object()},),
                         (dict(good, extra=object()),),
                         (dict(good, time=float("nan")),)):
            with self.subTest(passport=passport):
                r = self.chemistry.petition(Petition(
                    a.token, "Alice", passport, "", seq=1,
                    signature="00" * 64))
                self.assertIsInstance(r, Refusal)
                self.assertIn("Cannot read the passport", r.reason)

    def test_the_world_keeps_made_stamps_too(self):
        world = PoetryWorld("world:another", "Another")
        bob = make_client("Bob")
        petition_world(bob, world)
        act_on_world(bob, world, "poem.turn", TURN)
        held = world.passport_of(bob.individual.token)
        self.assertEqual([s.kind for s in held.stamps], ["arrival", "made"])
        self.assertEqual(held.stamps, bob.passport.stamps)

    def test_made_stamps_name_what_was_made(self):
        arrival, made, departure = self.alice.passport.stamps
        turn, = self.poetry.turns()
        self.assertEqual(made.made, thing_fingerprint(turn))
        self.assertEqual(made.arrival, arrival.fingerprint())
        self.assertEqual(departure.arrival, arrival.fingerprint())



class TestConformanceChecksStamps(unittest.TestCase):
    """Each check the conformance test makes on keys and stamps fails a
    world that breaks it, and only that check."""

    STAMP = ("the Departure: its stamp is not this world's signed "
             "departure stamp for the petitioner")

    def failures(self, world):
        result = run_conformance(world)
        self.assertFalse(result["passed"])
        return result["failures"]

    def test_a_manifest_that_doesnt_verify(self):
        class Unsigned(PoetryWorld):
            def __init__(self, *args):
                super().__init__(*args)
                self._manifest = dataclasses.replace(self._manifest,
                                                     signature="00" * 64)
        self.assertEqual(self.failures(Unsigned("world:u", "U")),
                         ["the manifest: its signature does not verify "
                          "against its world_key"])

    def test_a_stamp_that_doesnt_verify(self):
        class Smudged(PoetryWorld):
            def _departure_stamp(self, token, timestamp, arrival):
                stamp = super()._departure_stamp(token, timestamp, arrival)
                return dataclasses.replace(stamp, signature="00" * 64)
        self.assertEqual(self.failures(Smudged("world:s", "S")),
                         [self.STAMP])

    def test_a_stamp_for_another_id_or_under_another_key(self):
        class OtherId(PoetryWorld):
            def _departure_stamp(self, token, timestamp, arrival):
                return make_stamp(self._key, "departure", "world:other",
                                  token, timestamp,
                                  arrival=arrival.fingerprint())

        class OtherKey(PoetryWorld):
            def _departure_stamp(self, token, timestamp, arrival):
                return make_stamp(Signer(), "departure",
                                  self.manifest().entity_id, token,
                                  timestamp, arrival=arrival.fingerprint())
        for world in (OtherId("world:i", "I"), OtherKey("world:k", "K")):
            with self.subTest(world=type(world).__name__):
                self.assertEqual(self.failures(world), [self.STAMP])

    def test_a_departure_that_closes_another_arrival(self):
        class Muddled(PoetryWorld):
            def _departure_stamp(self, token, timestamp, arrival):
                return make_stamp(self._key, "departure",
                                  self.manifest().entity_id, token,
                                  timestamp, arrival="ab" * 32)
        self.assertEqual(self.failures(Muddled("world:m", "M")),
                         ["the departure stamp does not name the arrival "
                          "it closes"])

    def test_a_world_that_doesnt_bind_requests_to_its_key(self):
        # It checks only that a signature looks like one: it refuses an
        # unsigned petition, but admits one signed for another key.
        def looks_signed(token, seq, signature, document, last_seq):
            if type(signature) is str and len(signature) == 128:
                return ""
            return "The signature does not verify"
        with mock.patch("multiverse.entity.request_problem", looks_signed):
            failures = self.failures(PoetryWorld("world:l", "L"))
        self.assertIn("a petition signed for another world's key was "
                      "admitted", failures)


if __name__ == "__main__":
    unittest.main()

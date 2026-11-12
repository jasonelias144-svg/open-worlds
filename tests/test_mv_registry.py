"""The registry: the sketch's tests for component 6, ported.

Two failed in the sketch. Its broken-world test expected "fails
conformance" but got a different refusal, and its manifest test used a
name it never imported.
"""
import dataclasses
import unittest
from unittest import mock

from multiverse.chemistry_world import ChemistryWorld
from multiverse.conformance import run_conformance
from multiverse.identity import Individual
from multiverse.poetry_world import PoetryWorld, PoetryWorldLaw
from multiverse.protocol import (Ack, Act, Admission, Departure, Manifest,
                                 Refusal)
from multiverse.registry import (MultiverseLaw, MultiverseRegistry,
                                 manifest_from_dict, manifest_to_dict,
                                 registry_from_log)


def _in(world, person, *args, **kwargs):
    """`person`'s signed petition to `world`."""
    return person.petition(world.manifest().entity_id, *args, **kwargs)


def _out(world, person):
    """`person`'s signed leave from `world`."""
    return person.leave(world.manifest().entity_id)


def _admit(mv, person, entity, entity_id=None):
    """A signed listing act: the payload names the entity's id; the entity
    itself is attached. The id is read without calling manifest(), so
    tests that count manifest() calls see only the registry's."""
    if entity_id is None:
        manifest = getattr(entity, "_manifest", None)
        entity_id = manifest.entity_id if manifest else "world:unknown"
    act = person.act(mv.manifest().entity_id, "multiverse.admit",
                     {"entity_id": entity_id})
    return dataclasses.replace(act, attachment=entity)


def _remove(mv, person, entity_id):
    return person.act(mv.manifest().entity_id, "multiverse.remove",
                      {"entity_id": entity_id})


class KeyBomb(str):
    """A key that hashes like the text it claims to be, so a dict lookup
    for that text calls its __eq__, which raises."""
    def __hash__(self): return str.__hash__(str(self))
    def __eq__(self, other): raise ValueError("no equality")


class BrokenWorld:
    def manifest(self): return None
    def petition(self, p): return "yes"
    def act(self, a): return "ok"
    def leave(self, token): return "bye"
    def log_since(self, ts=None): return None


class RegistryCase(unittest.TestCase):

    def registry(self, entity_id="multiverse:main", name="Alice", **law):
        mv = MultiverseRegistry(entity_id, "Main Multiverse",
                                law=MultiverseLaw(**law) if law else None)
        person = Individual(name)
        self.assertIsInstance(mv.petition(person.petition(entity_id)),
                              Admission)
        return mv, person


class TestRegistry(RegistryCase):

    def test_manifest_has_sub_registry(self):
        m = MultiverseRegistry("multiverse:main", "Main").manifest()
        self.assertTrue(m.has_sub_registry())

    def test_conforms_to_wcp(self):
        mv = MultiverseRegistry("multiverse:main", "Main")
        self.assertTrue(run_conformance(mv)["passed"])

    def test_law_is_readable(self):
        doc = MultiverseLaw().describe()
        for part in ("multiverse.admit", "multiverse.remove",
                     "may leave at any time"):
            self.assertIn(part, doc)

    def test_lists_conforming_entity(self):
        mv, alice = self.registry()
        r = mv.act(_admit(mv, alice, PoetryWorld("world:poetry",
                                             "The Poetry World")))
        self.assertIsInstance(r, Ack)
        self.assertEqual(mv.entity_ids(), ["world:poetry"])
        self.assertEqual(mv.get_manifest("world:poetry").name,
                         "The Poetry World")
        self.assertTrue(mv.conformance_report("world:poetry")["passed"])

    def test_refuses_non_conforming_entity(self):
        mv, alice = self.registry()
        r = mv.act(_admit(mv, alice, BrokenWorld()))
        self.assertIsInstance(r, Refusal)
        self.assertIn("fails conformance", r.reason)
        self.assertEqual(mv.entity_ids(), [])
        refused = [e for e in mv.log_since(None)
                   if e.kind == "entity_admit_refused"]
        self.assertEqual(len(refused), 1)
        self.assertFalse(refused[0].data["conformance"]["passed"])

    def test_refuses_entity_whose_manifest_raises(self):
        class Raises(BrokenWorld):
            def manifest(self): raise RuntimeError("down")

        mv, alice = self.registry()
        r = mv.act(_admit(mv, alice, Raises()))
        self.assertIsInstance(r, Refusal)
        self.assertIn("fails conformance", r.reason)

    def test_manifest_that_changes_after_checking(self):
        # The sketch asked again after the test and could raise here.
        class Fickle(PoetryWorld):
            calls = 0

            def manifest(self):
                Fickle.calls += 1
                if Fickle.calls > 1:
                    raise RuntimeError("gone")
                return super().manifest()

        mv, alice = self.registry()
        r = mv.act(_admit(mv, alice, Fickle("world:fickle", "Fickle")))
        self.assertIsInstance(r, Ack)
        self.assertEqual(mv.entity_ids(), ["world:fickle"])

    def test_manifest_that_changes_id_after_checking(self):
        class Shifty(PoetryWorld):
            calls = 0

            def manifest(self):
                Shifty.calls += 1
                m = super().manifest()
                if Shifty.calls > 1:
                    return dataclasses.replace(m, entity_id="world:other")
                return m

        mv, alice = self.registry()
        self.assertIsInstance(mv.act(_admit(mv, alice, Shifty("world:shifty",
                                                          "Shifty"))), Ack)
        self.assertEqual(mv.entity_ids(), ["world:shifty"])

    def test_a_hostile_entity_cannot_make_the_registry_raise(self):
        class Odd:
            def __bool__(self): raise ValueError("no truth value")

        class OddDeparture(PoetryWorld):
            def leave(self, token):
                super().leave(token)
                return Departure(entity_id=Odd(), timestamp="t")

        mv, alice = self.registry()
        r = mv.act(_admit(mv, alice, OddDeparture("world:odd", "Odd")))
        self.assertIsInstance(r, Refusal)
        self.assertIn("fails conformance", r.reason)
        # And the last guard, if checking itself ever raised:
        with mock.patch("multiverse.registry.check",
                        side_effect=RuntimeError("boom")):
            r = mv.act(_admit(mv, alice, PoetryWorld("world:p", "P")))
        self.assertIsInstance(r, Refusal)
        self.assertIn("could not be checked", r.reason)
        self.assertEqual(mv.entity_ids(), [])

    def test_hostile_manifests_are_refused(self):
        class EqBomb(str):
            def __eq__(self, other): raise ValueError("no equality")
            __hash__ = str.__hash__

        class HashBomb(str):
            def __hash__(self): raise ValueError("no hash")

        class Swapped(PoetryWorld):
            bomb = None

            def manifest(self):
                m = super().manifest()
                fake = object.__new__(Manifest)
                for f in dataclasses.fields(Manifest):
                    object.__setattr__(fake, f.name, getattr(m, f.name))
                object.__setattr__(fake, "entity_id",
                                   self.bomb(m.entity_id))
                return fake

        class LoudManifest(PoetryWorld):
            def act(self, a): return "ok"   # fails conformance

            def manifest(self):
                class Loud(Manifest):
                    def __bool__(self): raise ValueError("no truth")
                return Loud(**dataclasses.asdict(super().manifest()))

        mv, alice = self.registry()
        worlds = []
        for bomb in (EqBomb, HashBomb):
            w = Swapped(f"world:{bomb.__name__}", bomb.__name__)
            w.bomb = bomb
            worlds.append(w)
        worlds.append(LoudManifest("world:loud", "Loud"))
        for w in worlds:
            with self.subTest(world=w.manifest().name
                              if not isinstance(w, LoudManifest) else "Loud"):
                r = mv.act(_admit(mv, alice, w))
                self.assertIsInstance(r, Refusal)
                self.assertIn("fails conformance", r.reason)
        self.assertEqual(mv.entity_ids(), [])

    def test_plain_keys_and_values(self):
        class Text(str):
            pass

        mv, alice = self.registry()
        mv.act(_admit(mv, alice, PoetryWorld("world:poetry", "Poetry")))
        token = alice.token
        for act in (Act(token, "multiverse.admit", {KeyBomb("entity_id"): 1}),
                    Act(token, "multiverse.admit",
                        {"entity_id": "world:x", "note": object()},
                        attachment=PoetryWorld("world:x", "X")),
                    Act(token, "multiverse.remove",
                        {KeyBomb("entity_id"): "x"}),
                    Act(token, "multiverse.remove",
                        {"entity_id": Text("world:poetry")})):
            with self.subTest(act=act.type):
                r = mv.act(act)
                self.assertIsInstance(r, Refusal)
                self.assertIn("plain", r.reason)
        self.assertEqual(mv.entity_ids(), ["world:poetry"])

    def test_refusal_records_the_manifest_it_checked(self):
        class Rude(PoetryWorld):
            def act(self, a): return "ok"

        mv, alice = self.registry()
        mv.act(_admit(mv, alice, Rude("world:rude", "Rude")))
        refused, = [e for e in mv.log_since(None)
                    if e.kind == "entity_admit_refused"]
        self.assertEqual(refused.data["manifest"]["entity_id"], "world:rude")

    def test_lists_only_what_was_signed_for(self):
        mv, alice = self.registry()
        r = mv.act(_admit(mv, alice, PoetryWorld("world:real", "Real"),
                          entity_id="world:other"))
        self.assertIsInstance(r, Refusal)
        self.assertIn("signed for", r.reason)
        self.assertEqual(mv.entity_ids(), [])

    def test_the_signed_id_must_be_text(self):
        mv, alice = self.registry()
        world = PoetryWorld("world:real", "Real")
        for entity_id in (5, "", ["world:real"], None):
            with self.subTest(entity_id=entity_id):
                act = alice.act(mv.manifest().entity_id, "multiverse.admit",
                                {"entity_id": entity_id})
                r = mv.act(dataclasses.replace(act, attachment=world))
                self.assertIsInstance(r, Refusal)
                self.assertIn("No entity_id", r.reason)
        self.assertEqual(mv.entity_ids(), [])

    def test_does_not_list_itself(self):
        mv, alice = self.registry()
        r = mv.act(_admit(mv, alice, mv))
        self.assertIsInstance(r, Refusal)
        self.assertIn("itself", r.reason)
        # Refused before testing itself: no conformance visit in its log.
        self.assertEqual([e.kind for e in mv.log_since(None)],
                         ["admission", "act_refused"])
        twin = MultiverseRegistry("multiverse:main", "Same id")
        self.assertIn("itself", mv.act(_admit(mv, alice, twin)).reason)
        self.assertEqual(mv.entity_ids(), [])

    def test_only_the_lister_takes_a_listing_down(self):
        mv, alice = self.registry()
        mv.act(_admit(mv, alice, PoetryWorld("world:poetry", "Poetry")))
        bob = Individual("Bob")
        mv.petition(_in(mv, bob))
        r = mv.act(_remove(mv, bob, "world:poetry"))
        self.assertIsInstance(r, Refusal)
        self.assertIn("Only whoever listed", r.reason)
        self.assertEqual(mv.entity_ids(), ["world:poetry"])
        self.assertIsInstance(mv.act(_remove(mv, alice, "world:poetry")), Ack)

    def test_refuses_missing_entity(self):
        mv, alice = self.registry()
        r = mv.act(Act(actor_token=alice, type="multiverse.admit", payload={}))
        self.assertIsInstance(r, Refusal)

    def test_refuses_duplicate(self):
        mv, alice = self.registry()
        poetry = PoetryWorld("world:poetry", "The Poetry World")
        self.assertIsInstance(mv.act(_admit(mv, alice, poetry)), Ack)
        r = mv.act(_admit(mv, alice, poetry))
        self.assertIsInstance(r, Refusal)
        self.assertIn("already listed", r.reason)

    def test_remove(self):
        mv, alice = self.registry()
        mv.act(_admit(mv, alice, PoetryWorld("world:poetry", "Poetry")))
        self.assertIsInstance(mv.act(_remove(mv, alice, "world:poetry")), Ack)
        self.assertEqual(mv.entity_ids(), [])

    def test_refuses_remove_missing(self):
        mv, alice = self.registry()
        r = mv.act(_remove(mv, alice, "world:nonexistent"))
        self.assertIsInstance(r, Refusal)
        self.assertIn("not in registry", r.reason)

    def test_refuses_strangers_and_unknown_acts(self):
        mv, alice = self.registry()
        stranger = Individual("Mallory")
        self.assertIn("not admitted",
                      mv.act(_admit(mv, stranger,
                                    PoetryWorld("w:p", "P"))).reason)
        r = mv.act(alice.act(mv.manifest().entity_id, "multiverse.rank", {}))
        self.assertIn("Unknown act type", r.reason)

    def test_never_converges(self):
        mv, alice = self.registry()
        for i in range(10):
            mv.act(_admit(mv, alice, PoetryWorld(f"world:{i}", f"World {i}")))
        self.assertEqual(len(mv.entity_ids()), 10)
        self.assertFalse(mv.is_converged())

    def test_lists_two_different_laws(self):
        mv, alice = self.registry()
        mv.act(_admit(mv, alice, PoetryWorld("world:poetry", "Poetry")))
        mv.act(_admit(mv, alice,
                      ChemistryWorld("world:chemistry", "Chemistry")))
        self.assertEqual({m.entity_id for m in mv.list_sub_entities()},
                         {"world:poetry", "world:chemistry"})

    def test_listing_takes_no_place_in_the_world(self):
        # In the sketch, listing a world with room for two left room for one.
        mv, alice = self.registry()
        poetry = PoetryWorld("world:poetry", "Poetry",
                             law=PoetryWorldLaw(max_admitted=2))
        self.assertIsInstance(mv.act(_admit(mv, alice, poetry)), Ack)
        for name in ("Bea", "Cal"):
            person = Individual(name)
            self.assertIsInstance(
                poetry.petition(person.petition("world:poetry")), Admission)

    def test_leave_the_registry(self):
        mv, alice = self.registry(max_admitted=1)
        self.assertFalse(
            mv.leave(_out(mv, alice)).already_left)
        bob = Individual("Bob")
        self.assertIsInstance(mv.petition(_in(mv, bob)),
                              Admission)

    def test_full_registry_says_multiverse(self):
        mv, _ = self.registry(max_admitted=1)
        bob = Individual("Bob")
        r = mv.petition(_in(mv, bob))
        self.assertEqual(r.reason, "The multiverse is full")


class TestFractal(RegistryCase):

    def test_multiverse_in_multiverse(self):
        inner, alice = self.registry("multiverse:inner")
        inner.act(_admit(inner, alice, PoetryWorld("world:poetry", "Poetry")))
        inner.act(_admit(inner, alice,
                         ChemistryWorld("world:chemistry", "Chem")))
        outer, bob = self.registry("multiverse:outer", "Bob")
        self.assertIsInstance(outer.act(_admit(outer, bob, inner)), Ack)
        listed, = outer.list_sub_entities()
        self.assertEqual(listed.entity_id, "multiverse:inner")
        self.assertTrue(listed.has_sub_registry())
        self.assertEqual(len(inner.list_sub_entities()), 2)

    def test_registry_from_log(self):
        mv, alice = self.registry()
        mv.act(_admit(mv, alice, PoetryWorld("world:poetry", "Poetry")))
        mv.act(_admit(mv, alice, ChemistryWorld("world:chemistry", "Chem")))
        mv.act(_remove(mv, alice, "world:chemistry"))
        rebuilt = registry_from_log(mv.log_since(None))
        self.assertEqual(list(rebuilt), mv.entity_ids())
        self.assertEqual(list(rebuilt.values()), mv.list_sub_entities())

    def test_log_shows_conformance_reports(self):
        mv, alice = self.registry()
        mv.act(_admit(mv, alice, PoetryWorld("world:poetry", "Poetry")))
        listed = [e for e in mv.log_since(None) if e.kind == "entity_admitted"]
        self.assertEqual(len(listed), 1)
        self.assertTrue(listed[0].data["conformance"]["passed"])

    def test_manifest_serialization(self):
        m = Manifest(entity_id="world:test", name="Test World",
                     protocol_version="WCP/0.1", law_url="x",
                     act_endpoint="y", log_endpoint="z",
                     sub_registry_endpoint="w")
        self.assertEqual(manifest_from_dict(manifest_to_dict(m)), m)


if __name__ == "__main__":
    unittest.main()

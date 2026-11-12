"""The registry: the sketch's tests for component 6, ported.

Two failed in the sketch. Its broken-world test expected "fails
conformance" but got a different refusal, and its manifest test used a
name it never imported.
"""
import unittest

from multiverse.chemistry_world import ChemistryWorld
from multiverse.conformance import run_conformance
from multiverse.identity import create_identity
from multiverse.poetry_world import PoetryWorld, PoetryWorldLaw
from multiverse.protocol import (Ack, Act, Admission, Manifest, Petition,
                                 Refusal)
from multiverse.registry import (MultiverseLaw, MultiverseRegistry,
                                 manifest_from_dict, manifest_to_dict,
                                 registry_from_log)


def _petition(name, token):
    return Petition(petitioner_token=token, petitioner_name=name,
                    passport_admissions=(), message=f"{name} petitions.")


def _admit(actor, entity):
    return Act(actor_token=actor, type="multiverse.admit",
               payload={"entity": entity})


def _remove(actor, entity_id):
    return Act(actor_token=actor, type="multiverse.remove",
               payload={"entity_id": entity_id})


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
        person = create_identity(name)
        self.assertIsInstance(mv.petition(_petition(name, person.token)),
                              Admission)
        return mv, person.token


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
        r = mv.act(_admit(alice, PoetryWorld("world:poetry",
                                             "The Poetry World")))
        self.assertIsInstance(r, Ack)
        self.assertEqual(mv.entity_ids(), ["world:poetry"])
        self.assertEqual(mv.get_manifest("world:poetry").name,
                         "The Poetry World")
        self.assertTrue(mv.conformance_report("world:poetry")["passed"])

    def test_refuses_non_conforming_entity(self):
        mv, alice = self.registry()
        r = mv.act(_admit(alice, BrokenWorld()))
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
        r = mv.act(_admit(alice, Raises()))
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
        r = mv.act(_admit(alice, Fickle("world:fickle", "Fickle")))
        self.assertIsInstance(r, Ack)
        self.assertEqual(mv.entity_ids(), ["world:fickle"])

    def test_does_not_list_itself(self):
        mv, alice = self.registry()
        r = mv.act(_admit(alice, mv))
        self.assertIsInstance(r, Refusal)
        self.assertIn("itself", r.reason)
        # Refused before testing itself: no conformance visit in its log.
        self.assertEqual([e.kind for e in mv.log_since(None)],
                         ["admission", "act_refused"])
        twin = MultiverseRegistry("multiverse:main", "Same id")
        self.assertIn("itself", mv.act(_admit(alice, twin)).reason)
        self.assertEqual(mv.entity_ids(), [])

    def test_only_the_lister_takes_a_listing_down(self):
        mv, alice = self.registry()
        mv.act(_admit(alice, PoetryWorld("world:poetry", "Poetry")))
        bob = create_identity("Bob")
        mv.petition(_petition("Bob", bob.token))
        r = mv.act(_remove(bob.token, "world:poetry"))
        self.assertIsInstance(r, Refusal)
        self.assertIn("Only whoever listed", r.reason)
        self.assertEqual(mv.entity_ids(), ["world:poetry"])
        self.assertIsInstance(mv.act(_remove(alice, "world:poetry")), Ack)

    def test_refuses_missing_entity(self):
        mv, alice = self.registry()
        r = mv.act(Act(actor_token=alice, type="multiverse.admit", payload={}))
        self.assertIsInstance(r, Refusal)

    def test_refuses_duplicate(self):
        mv, alice = self.registry()
        poetry = PoetryWorld("world:poetry", "The Poetry World")
        self.assertIsInstance(mv.act(_admit(alice, poetry)), Ack)
        r = mv.act(_admit(alice, poetry))
        self.assertIsInstance(r, Refusal)
        self.assertIn("already listed", r.reason)

    def test_remove(self):
        mv, alice = self.registry()
        mv.act(_admit(alice, PoetryWorld("world:poetry", "Poetry")))
        self.assertIsInstance(mv.act(_remove(alice, "world:poetry")), Ack)
        self.assertEqual(mv.entity_ids(), [])

    def test_refuses_remove_missing(self):
        mv, alice = self.registry()
        r = mv.act(_remove(alice, "world:nonexistent"))
        self.assertIsInstance(r, Refusal)
        self.assertIn("not in registry", r.reason)

    def test_refuses_strangers_and_unknown_acts(self):
        mv, alice = self.registry()
        stranger = create_identity("Mallory").token
        self.assertIn("not admitted",
                      mv.act(_admit(stranger, PoetryWorld("w:p", "P"))).reason)
        r = mv.act(Act(actor_token=alice, type="multiverse.rank", payload={}))
        self.assertIn("Unknown act type", r.reason)

    def test_never_converges(self):
        mv, alice = self.registry()
        for i in range(10):
            mv.act(_admit(alice, PoetryWorld(f"world:{i}", f"World {i}")))
        self.assertEqual(len(mv.entity_ids()), 10)
        self.assertFalse(mv.is_converged())

    def test_lists_two_different_laws(self):
        mv, alice = self.registry()
        mv.act(_admit(alice, PoetryWorld("world:poetry", "Poetry")))
        mv.act(_admit(alice, ChemistryWorld("world:chemistry", "Chemistry")))
        self.assertEqual({m.entity_id for m in mv.list_sub_entities()},
                         {"world:poetry", "world:chemistry"})

    def test_listing_takes_no_place_in_the_world(self):
        # In the sketch, listing a world with room for two left room for one.
        mv, alice = self.registry()
        poetry = PoetryWorld("world:poetry", "Poetry",
                             law=PoetryWorldLaw(max_admitted=2))
        self.assertIsInstance(mv.act(_admit(alice, poetry)), Ack)
        for name in ("Bea", "Cal"):
            person = create_identity(name)
            self.assertIsInstance(
                poetry.petition(_petition(name, person.token)), Admission)

    def test_leave_the_registry(self):
        mv, alice = self.registry(max_admitted=1)
        self.assertFalse(mv.leave(alice).already_left)
        bob = create_identity("Bob")
        self.assertIsInstance(mv.petition(_petition("Bob", bob.token)),
                              Admission)

    def test_full_registry_says_multiverse(self):
        mv, _ = self.registry(max_admitted=1)
        bob = create_identity("Bob")
        r = mv.petition(_petition("Bob", bob.token))
        self.assertEqual(r.reason, "The multiverse is full")


class TestFractal(RegistryCase):

    def test_multiverse_in_multiverse(self):
        inner, alice = self.registry("multiverse:inner")
        inner.act(_admit(alice, PoetryWorld("world:poetry", "Poetry")))
        inner.act(_admit(alice, ChemistryWorld("world:chemistry", "Chem")))
        outer, bob = self.registry("multiverse:outer", "Bob")
        self.assertIsInstance(outer.act(_admit(bob, inner)), Ack)
        listed, = outer.list_sub_entities()
        self.assertEqual(listed.entity_id, "multiverse:inner")
        self.assertTrue(listed.has_sub_registry())
        self.assertEqual(len(inner.list_sub_entities()), 2)

    def test_registry_from_log(self):
        mv, alice = self.registry()
        mv.act(_admit(alice, PoetryWorld("world:poetry", "Poetry")))
        mv.act(_admit(alice, ChemistryWorld("world:chemistry", "Chem")))
        mv.act(_remove(alice, "world:chemistry"))
        rebuilt = registry_from_log(mv.log_since(None))
        self.assertEqual(list(rebuilt), mv.entity_ids())
        self.assertEqual(list(rebuilt.values()), mv.list_sub_entities())

    def test_log_shows_conformance_reports(self):
        mv, alice = self.registry()
        mv.act(_admit(alice, PoetryWorld("world:poetry", "Poetry")))
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

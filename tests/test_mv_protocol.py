"""The protocol and its conformance test: the sketch's tests for
component 3, ported, with tests for leaving, which this port adds."""
import dataclasses
import unittest

from multiverse.conformance import run_conformance
from multiverse.protocol import (Ack, Act, Admission, Departure, LogEntry,
                                 Manifest, NullWorld, Petition, Refusal)

ALICE = "alice-token-000000001"


def _manifest(entity_id="world:poetry", **extra):
    return Manifest(entity_id=entity_id, name="The Poetry World",
                    protocol_version="WCP/0.1",
                    law_url="https://poetry.example/law",
                    act_endpoint="https://poetry.example/act",
                    log_endpoint="https://poetry.example/log", **extra)


def _petition(name="Alice", token=ALICE, admissions=()):
    return Petition(petitioner_token=token, petitioner_name=name,
                    passport_admissions=admissions, message="Enter?")


class IndependentWorld:
    """Written from the protocol alone, sharing no code with the package:
    admits everyone and accepts every act."""

    def __init__(self):
        self._manifest = Manifest(
            entity_id="independent:1", name="Independent World",
            protocol_version="WCP/0.1", law_url="independent:law",
            act_endpoint="independent:act", log_endpoint="independent:log")
        self._present = set()
        self._events = []

    def manifest(self):
        return self._manifest

    def petition(self, p):
        self._present.add(p.petitioner_token)
        self._events.append(("petition", p.petitioner_token))
        return Admission(entity_id="independent:1", timestamp="independent:0")

    def act(self, a):
        self._events.append(("act", a.actor_token))
        return Ack(entity_id="independent:1", timestamp="independent:0")

    def leave(self, token):
        was_present = token in self._present
        self._present.discard(token)
        return Departure(entity_id="independent:1",
                         timestamp="independent:0",
                         already_left=not was_present)

    def log_since(self, ts=None):
        return [LogEntry(timestamp="independent:0", kind=kind,
                         actor_token=actor) for kind, actor in self._events]


class TestManifest(unittest.TestCase):

    def test_manifest_construction(self):
        m = _manifest()
        self.assertFalse(m.has_sub_registry())
        self.assertEqual(m.protocol_version, "WCP/0.1")

    def test_manifest_with_sub_registry(self):
        m = _manifest("multiverse:main",
                      sub_registry_endpoint="https://mv.example/worlds")
        self.assertTrue(m.has_sub_registry())

    def test_manifest_validation(self):
        good = dict(entity_id="x", name="x", protocol_version="WCP/0.1",
                    law_url="u", act_endpoint="u", log_endpoint="u")
        for field in ("entity_id", "name", "protocol_version", "law_url",
                      "act_endpoint", "log_endpoint"):
            with self.subTest(field=field), self.assertRaises(ValueError):
                Manifest(**{**good, field: ""})

    def test_messages_are_immutable(self):
        a = Act(actor_token=ALICE, type="poem.turn", payload={})
        with self.assertRaises(dataclasses.FrozenInstanceError):
            a.type = "other"


class TestNullWorld(unittest.TestCase):

    def setUp(self):
        self.w = NullWorld("world:null", "The Null World")

    def test_manifest(self):
        m = self.w.manifest()
        self.assertEqual(m.protocol_version, "WCP/0.1")
        self.assertFalse(m.has_sub_registry())

    def test_refuses_petition_and_act(self):
        r = self.w.petition(_petition())
        self.assertIsInstance(r, Refusal)
        self.assertTrue(r.reason)
        self.assertIsInstance(
            self.w.act(Act(actor_token=ALICE, type="poem.turn", payload={})),
            Refusal)

    def test_log(self):
        self.w.petition(_petition())
        self.w.act(Act(actor_token=ALICE, type="poem.turn", payload={}))
        self.assertEqual(len(self.w.log_since(None)), 2)

    def test_leave_when_never_present(self):
        d = self.w.leave(ALICE)
        self.assertIsInstance(d, Departure)
        self.assertTrue(d.already_left)

    def test_passes_conformance(self):
        self.assertTrue(run_conformance(self.w)["passed"])


class TestConformance(unittest.TestCase):

    def test_broken_world_fails(self):
        class BrokenWorld:
            def manifest(self): return None
            def petition(self, p): return "yes"
            def act(self, a): return "ok"
            def leave(self, token): return "bye"
            def log_since(self, ts=None): return None

        result = run_conformance(BrokenWorld())
        self.assertFalse(result["passed"])
        self.assertIn("manifest() did not return a Manifest",
                      result["failures"])

    def test_wrong_answers_fail(self):
        class WrongAnswers(NullWorld):
            def petition(self, p): return "yes"
            def act(self, a): return "ok"
            def log_since(self, ts=None): return None

        failures = run_conformance(WrongAnswers("w:x", "X"))["failures"]
        self.assertEqual(len(failures), 3, failures)

    def test_fractal_architecture(self):
        # A world, a multiverse and a federation speak the same protocol;
        # only the sub-registry differs.
        class NullMultiverse(NullWorld):
            def __init__(self, entity_id, name, endpoint):
                super().__init__(entity_id, name)
                self._manifest = dataclasses.replace(
                    self._manifest, sub_registry_endpoint=endpoint)

        for entity in [NullWorld("world:poetry", "Poetry World"),
                       NullMultiverse("multiverse:main", "Main",
                                      "https://mv.example/worlds"),
                       NullMultiverse("federation:global", "Global",
                                      "https://fed.example/multiverses")]:
            with self.subTest(entity=entity.manifest().entity_id):
                self.assertTrue(run_conformance(entity)["passed"])

    def test_independent_implementation_conforms(self):
        result = run_conformance(IndependentWorld())
        self.assertTrue(result["passed"], result["failures"])

    def test_different_laws_same_protocol(self):
        class LawAWorld(NullWorld):
            def petition(self, p):
                if p.petitioner_name == "Alice":
                    return Admission(entity_id="world:lawA", timestamp="t")
                return Refusal(reason="Only Alice may enter.")

        class LawBWorld(NullWorld):
            def petition(self, p):
                if p.passport_admissions:
                    return Admission(entity_id="world:lawB", timestamp="t")
                return Refusal(reason="Must have an admission.")

        wa, wb = LawAWorld("world:lawA", "A"), LawBWorld("world:lawB", "B")
        for w in (wa, wb):
            self.assertTrue(run_conformance(w)["passed"])
        self.assertIsInstance(wa.petition(_petition()), Admission)
        self.assertIsInstance(wb.petition(_petition()), Refusal)


class TestLeavingConformance(unittest.TestCase):
    """Leaving can't be refused, says whether you were present, and the
    second time answers already_left."""

    def test_world_without_leave_fails(self):
        class NoLeave(IndependentWorld):
            leave = None

        failures = run_conformance(NoLeave())["failures"]
        self.assertTrue(any("leave() raised" in f for f in failures),
                        failures)

    def test_leave_that_refuses_fails(self):
        class HoldsYou(IndependentWorld):
            def leave(self, token):
                return Refusal(reason="You may not leave.")

        failures = run_conformance(HoldsYou())["failures"]
        self.assertTrue(any("expected Departure" in f for f in failures),
                        failures)

    def test_leave_that_raises_fails(self):
        class Breaks(IndependentWorld):
            def leave(self, token):
                raise RuntimeError("no exit")

        self.assertFalse(run_conformance(Breaks())["passed"])

    def test_leave_must_say_whether_present(self):
        class AlwaysAlreadyLeft(IndependentWorld):
            def leave(self, token):
                return Departure("independent:1", "t", already_left=True)

        class NeverAlreadyLeft(IndependentWorld):
            def leave(self, token):
                return Departure("independent:1", "t", already_left=False)

        for world in (AlwaysAlreadyLeft(), NeverAlreadyLeft()):
            with self.subTest(world=type(world).__name__):
                failures = run_conformance(world)["failures"]
                self.assertEqual(len(failures), 1, failures)
                self.assertIn("already_left", failures[0])

    def test_conformance_leaves_what_it_entered(self):
        w = IndependentWorld()
        run_conformance(w)
        self.assertEqual(w._present, set())


if __name__ == "__main__":
    unittest.main()

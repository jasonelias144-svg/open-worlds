"""The protocol and its conformance test: the sketch's tests for
component 3, ported, with tests for leaving, which this port adds, and
for signed requests (course step 2)."""
import dataclasses
import unittest

from multiverse.conformance import run_conformance
from multiverse.identity import Individual
from multiverse.protocol import (PROTOCOL_VERSION, Ack, Act, Admission,
                                 Departure, Leave, LogEntry, Manifest,
                                 NullWorld, Petition, Refusal, act_document,
                                 is_plain, leave_document, petition_document,
                                 request_problem)

ALICE = "alice-token-000000001"


def _manifest(entity_id="world:poetry", **extra):
    return Manifest(entity_id=entity_id, name="The Poetry World",
                    protocol_version=PROTOCOL_VERSION,
                    law_url="https://poetry.example/law",
                    act_endpoint="https://poetry.example/act",
                    log_endpoint="https://poetry.example/log", **extra)


def _petition(name="Alice", token=ALICE, admissions=()):
    return Petition(petitioner_token=token, petitioner_name=name,
                    passport_admissions=admissions, message="Enter?")


class IndependentWorld:
    """Written from the protocol's published parts alone (its messages,
    the signed documents and `request_problem`), sharing no world code
    with the package: admits anyone who signs, accepts every signed act.
    Subclasses change what leaving does by overriding `_go`."""
    ID = "independent:1"

    def __init__(self):
        self._manifest = Manifest(
            entity_id=self.ID, name="Independent World",
            protocol_version=PROTOCOL_VERSION, law_url="independent:law",
            act_endpoint="independent:act", log_endpoint="independent:log")
        self._present = set()
        self._events = []
        self._last = {}

    def manifest(self):
        return self._manifest

    def petition(self, p):
        if request_problem(p.petitioner_token, p.seq, p.signature,
                           petition_document(self.ID, p), self._last):
            return Refusal(reason="Not signed by the petitioner")
        self._present.add(p.petitioner_token)
        self._events.append(("petition", p.petitioner_token))
        return Admission(entity_id=self.ID, timestamp="independent:0")

    def act(self, a):
        if request_problem(a.actor_token, a.seq, a.signature,
                           act_document(self.ID, a), self._last):
            return Refusal(reason="Not signed by the actor")
        self._events.append(("act", a.actor_token))
        return Ack(entity_id=self.ID, timestamp="independent:0")

    def leave(self, request):
        if request_problem(request.token, request.seq, request.signature,
                           leave_document(self.ID, request), self._last):
            return Refusal(reason="Not the leaver's own leave")
        return self._go(request.token)

    def _go(self, token):
        was_present = token in self._present
        self._present.discard(token)
        if was_present:
            self._events.append(("departure", token))
        return Departure(entity_id=self.ID, timestamp="independent:0",
                         already_left=not was_present)

    def log_since(self, ts=None):
        return [LogEntry(timestamp="independent:0", kind=kind,
                         actor_token=actor) for kind, actor in self._events]


class TestPlain(unittest.TestCase):

    def test_plain_values(self):
        for value in (None, "x", 3, 2.5, True, [], {}, [1, ["a", {"b": None}]],
                      {"a": [1, 2, {"c": "d"}]}):
            with self.subTest(value=value):
                self.assertTrue(is_plain(value))

    def test_not_plain(self):
        class Text(str): pass
        class Mapping(dict): pass
        loop = []
        loop.append(loop)
        deep = []
        for _ in range(40):
            deep = [deep]
        for value in (Text("x"), Mapping(), {Text("k"): 1}, {1: "x"},
                      {"k": Text("v")}, [Text("x")], ("a", "b"), {"a"},
                      object(), b"x", loop, deep):
            with self.subTest(value=type(value).__name__):
                self.assertFalse(is_plain(value))

    def test_a_list_subclass_deep_inside_is_refused_not_iterated(self):
        class Iterless(list):
            def __iter__(self): raise ValueError("no iteration")

        self.assertFalse(is_plain({"a": [{"b": Iterless()}]}))

    def test_nesting_up_to_the_limit_is_plain(self):
        from multiverse.protocol import MAX_PLAIN_DEPTH

        def nested(depth):
            value = "leaf"
            for _ in range(depth):
                value = [value]
            return value

        self.assertTrue(is_plain(nested(MAX_PLAIN_DEPTH)))
        self.assertFalse(is_plain(nested(MAX_PLAIN_DEPTH + 1)))
        self.assertEqual(MAX_PLAIN_DEPTH, 32)


class TestManifest(unittest.TestCase):

    def test_manifest_construction(self):
        m = _manifest()
        self.assertFalse(m.has_sub_registry())
        self.assertEqual(m.protocol_version, "WCP/0.2")

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
        self.assertEqual(m.protocol_version, "WCP/0.2")
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
        log = self.w.log_since(None)
        self.assertEqual([e.kind for e in log],
                         ["petition_refused", "act_refused"])
        # It verifies nothing, so its log names nobody.
        self.assertEqual([e.actor_token for e in log], [None, None])

    def test_odd_requests_are_refused_not_raised(self):
        for request in (None, "petition", 7):
            with self.subTest(request=request):
                self.assertIsInstance(self.w.petition(request), Refusal)
                self.assertIsInstance(self.w.act(request), Refusal)
                self.assertIsInstance(self.w.leave(request), Refusal)

    def test_leave_when_never_present(self):
        alice = Individual("Alice")
        d = self.w.leave(alice.leave("world:null"))
        self.assertIsInstance(d, Departure)
        self.assertTrue(d.already_left)

    def test_refuses_a_leave_that_isnt_signed(self):
        self.assertIsInstance(self.w.leave(Leave(Individual("A").token, 1)),
                              Refusal)

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
        # unsigned and signed petitions, the act, and the log
        self.assertEqual(len(failures), 4, failures)

    def test_empty_reasons_and_kinds_fail(self):
        class Mute(NullWorld):
            def petition(self, p): return Refusal(reason="")

        class Kindless(NullWorld):
            def log_since(self, ts=None):
                return [LogEntry(timestamp="t", kind="")]

        self.assertEqual(run_conformance(Mute("w:m", "M"))["failures"],
                         ["petition() unsigned: Refusal.reason is empty",
                          "petition(): Refusal.reason is empty"])
        self.assertEqual(run_conformance(Kindless("w:k", "K"))["failures"],
                         ["a LogEntry has no timestamp or kind"])

    def test_check_returns_the_manifest_it_checked(self):
        from multiverse.conformance import check
        w = NullWorld("world:null", "Null")
        result, m = check(w)
        self.assertTrue(result["passed"])
        self.assertIs(m, w.manifest())
        self.assertIsNone(check(object())[1])

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


class TestSignedConformance(unittest.TestCase):
    """WCP/0.2: a world that doesn't check signatures, or accepts a
    replay, does not conform."""

    def test_admitting_unsigned_petitions_fails(self):
        class Trusting(IndependentWorld):
            def petition(self, p):
                self._present.add(p.petitioner_token)
                return Admission(entity_id=self.ID, timestamp="t")

        failures = run_conformance(Trusting())["failures"]
        self.assertIn("an unsigned petition was admitted", failures)

    def test_accepting_forged_acts_fails(self):
        class Gullible(IndependentWorld):
            def act(self, a):
                return Ack(entity_id=self.ID, timestamp="t")

        self.assertEqual(run_conformance(Gullible())["failures"],
                         ["an act signed by another key was accepted"])

    def test_accepting_forged_leaves_fails(self):
        class Pushover(IndependentWorld):
            def leave(self, request):
                return self._go(request.token)

        failures = run_conformance(Pushover())["failures"]
        self.assertIn("a leave signed by another key was not refused",
                      failures)

    def test_accepting_replayed_leaves_fails(self):
        class Forgetful(IndependentWorld):
            def leave(self, request):
                from multiverse.identity import signature_valid
                if not signature_valid(request.token,
                                       leave_document(self.ID, request),
                                       request.signature):
                    return Refusal(reason="not signed")
                return self._go(request.token)

        self.assertEqual(run_conformance(Forgetful())["failures"],
                         ["a replayed leave was not refused"])


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
            def leave(self, request):
                return Refusal(reason="You may not leave.")

        failures = run_conformance(HoldsYou())["failures"]
        self.assertTrue(any("expected Departure" in f for f in failures),
                        failures)

    def test_leave_that_raises_fails(self):
        class Breaks(IndependentWorld):
            def leave(self, request):
                raise RuntimeError("no exit")

        self.assertFalse(run_conformance(Breaks())["passed"])

    def test_leave_must_say_whether_present(self):
        # Both leave properly and record it; only their answer is wrong.
        class AlwaysAlreadyLeft(IndependentWorld):
            def _go(self, token):
                super()._go(token)
                return Departure("independent:1", "t", already_left=True)

        class NeverAlreadyLeft(IndependentWorld):
            def _go(self, token):
                super()._go(token)
                return Departure("independent:1", "t", already_left=False)

        for world in (AlwaysAlreadyLeft(), NeverAlreadyLeft()):
            with self.subTest(world=type(world).__name__):
                failures = run_conformance(world)["failures"]
                self.assertEqual(len(failures), 1, failures)
                self.assertIn("already_left", failures[0])

    def test_departure_must_be_in_the_log(self):
        # Right answers, but the departure isn't recorded.
        class Unrecorded(IndependentWorld):
            def _go(self, token):
                was_present = token in self._present
                self._present.discard(token)
                return Departure("independent:1", "t",
                                 already_left=not was_present)

        failures = run_conformance(Unrecorded())["failures"]
        self.assertEqual(failures, ["the log does not record the departure"])

    def test_what_it_cannot_see(self):
        # A world that answers correctly and records a departure, but
        # keeps the visitor, passes: a test from outside sees only answers
        # and the log (conformance.py says so).
        class Keeps(IndependentWorld):
            def _go(self, token):
                if token in self._present and ("departure", token) \
                        not in self._events:
                    self._events.append(("departure", token))
                    return Departure("independent:1", "t")
                return Departure("independent:1", "t", already_left=True)

        w = Keeps()
        self.assertTrue(run_conformance(w)["passed"])
        self.assertEqual(len(w._present), 1)

    def test_departure_must_be_the_tests_own(self):
        # Someone else's departure in the log doesn't count.
        class Borrowed(IndependentWorld):
            def __init__(self):
                super().__init__()
                self._events.append(("departure", "someone-else-0000000"))

            def _go(self, token):
                was_present = token in self._present
                self._present.discard(token)
                return Departure("independent:1", "t",
                                 already_left=not was_present)

        failures = run_conformance(Borrowed())["failures"]
        self.assertEqual(failures, ["the log does not record the departure"])

    def test_hostile_answers_are_reported_not_raised(self):
        class Odd:
            def __bool__(self): raise ValueError("no truth value")
            def __eq__(self, other): raise ValueError("no equality")
            __hash__ = object.__hash__
            def __repr__(self): return "Odd()"

        class OddDeparture(IndependentWorld):
            def _go(self, token):
                return Departure(entity_id=Odd(), timestamp="t")

        class OddAnswer(IndependentWorld):
            def _go(self, token):
                super()._go(token)
                return Departure("independent:1", "t", already_left=Odd())

        class OddVersion(str):
            def __ne__(self, other): raise ValueError("no comparison")

        class OddManifest(NullWorld):
            def manifest(self):
                return dataclasses.replace(
                    super().manifest(), protocol_version=OddVersion("x"))

        for world, expected in ((OddDeparture(), "answered unreadably"),
                                (OddAnswer(), "already_left=Odd()"),
                                # Manifest itself refuses a text subclass
                                (OddManifest("w:o", "O"), "plain text")):
            with self.subTest(world=type(world).__name__):
                result = run_conformance(world)
                self.assertFalse(result["passed"])
                self.assertTrue(any(expected in f for f in result["failures"]),
                                result["failures"])

    def test_unprintable_errors_are_reported(self):
        class BadExc(Exception):
            def __str__(self): raise ValueError("no message")

        class Raises(IndependentWorld):
            def act(self, a): raise BadExc()

        failures = run_conformance(Raises())["failures"]
        self.assertEqual(failures, [
            "act() raised BadExc (whose message could not be read)",
            "a forged request raised BadExc (whose message could not be "
            "read)"])

    def test_a_manifest_must_be_plain(self):
        class Bomb(str):
            def __eq__(self, other): raise ValueError("no equality")
            __hash__ = str.__hash__

        class Smuggled(NullWorld):
            # Built around Manifest's own checks.
            def manifest(self):
                m = object.__new__(Manifest)
                for field in ("entity_id", "name", "protocol_version",
                              "law_url", "act_endpoint", "log_endpoint"):
                    object.__setattr__(m, field,
                                       Bomb(getattr(super().manifest(),
                                                    field)))
                object.__setattr__(m, "sub_registry_endpoint", None)
                return m

        class Subclassed(NullWorld):
            def manifest(self):
                class Loud(Manifest):
                    def __bool__(self): raise ValueError("no truth")
                return Loud(**dataclasses.asdict(super().manifest()))

        from multiverse.conformance import check
        for world, failure in (
                (Smuggled("w:s", "S"), "the manifest's fields are not "
                                       "plain text"),
                (Subclassed("w:l", "L"), "manifest() did not return a "
                                         "Manifest")):
            with self.subTest(world=type(world).__name__):
                result, m = check(world)
                self.assertEqual(result["failures"], [failure])
                self.assertIsNone(m)
        with self.assertRaises(ValueError):
            Manifest(**{**dataclasses.asdict(NullWorld("w", "W").manifest()),
                        "entity_id": Bomb("w:b")})

    def test_conformance_leaves_what_it_entered(self):
        w = IndependentWorld()
        run_conformance(w)
        self.assertEqual(w._present, set())


if __name__ == "__main__":
    unittest.main()

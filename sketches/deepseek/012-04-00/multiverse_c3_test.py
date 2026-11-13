# multiverse_c3_test.py
from multiverse_c3 import (
    Manifest, Petition, Act, LogEntry,
    Admission, Refusal, Route, Ack,
    WorldProtocol, NullWorld,
)
from multiverse_c3_conformance import run_conformance


def test_manifest_construction():
    print("=== Manifest construction ===")
    m = Manifest(
        entity_id="world:poetry",
        name="The Poetry World",
        protocol_version="WCP/0.1",
        law_url="https://poetry.example/law",
        act_endpoint="https://poetry.example/act",
        log_endpoint="https://poetry.example/log",
    )
    print(f"  {m.name} ({m.protocol_version})")
    print(f"  has_sub_registry: {m.has_sub_registry()}")
    assert not m.has_sub_registry()
    assert m.protocol_version == "WCP/0.1"


def test_manifest_with_sub_registry():
    print("=== Manifest with sub-registry ===")
    m = Manifest(
        entity_id="multiverse:main",
        name="The Main Multiverse",
        protocol_version="WCP/0.1",
        law_url="https://mv.example/law",
        act_endpoint="https://mv.example/act",
        log_endpoint="https://mv.example/log",
        sub_registry_endpoint="https://mv.example/worlds",
    )
    print(f"  {m.name}")
    print(f"  has_sub_registry: {m.has_sub_registry()}")
    assert m.has_sub_registry()


def test_manifest_validation():
    print("=== Manifest validation ===")
    for bad in [
        {"entity_id": "", "name": "x", "protocol_version": "WCP/0.1",
         "law_url": "u", "act_endpoint": "u", "log_endpoint": "u"},
        {"entity_id": "x", "name": "", "protocol_version": "WCP/0.1",
         "law_url": "u", "act_endpoint": "u", "log_endpoint": "u"},
        {"entity_id": "x", "name": "x", "protocol_version": "",
         "law_url": "u", "act_endpoint": "u", "log_endpoint": "u"},
    ]:
        try:
            Manifest(**bad)
            assert False, f"should have rejected: {bad}"
        except ValueError:
            pass
    print("  ✓ empty fields rejected")


def test_petition_and_act_structures():
    print("=== Petition and Act structures ===")
    p = Petition(
        petitioner_token="alice:123",
        petitioner_name="Alice",
        passport_admissions=(("world:A", "2024-01-01T00:00:00+00:00"),),
        message="I would like to enter.",
    )
    a = Act(
        actor_token="alice:123",
        type="poem.turn",
        payload={"text": "Go\nBe a black widow"},
    )
    print(f"  Petition from {p.petitioner_name}: {p.message}")
    print(f"  Act type: {a.type}")


def test_nullworld_manifest():
    print("=== NullWorld: manifest ===")
    w = NullWorld("world:null", "The Null World")
    m = w.manifest()
    print(f"  {m.name} ({m.entity_id})")
    print(f"  protocol_version: {m.protocol_version}")
    print(f"  has_sub_registry: {m.has_sub_registry()}")
    assert m.protocol_version == "WCP/0.1"
    assert not m.has_sub_registry()


def test_nullworld_refuses_petition():
    print("=== NullWorld: refuses petition ===")
    w = NullWorld("world:null", "The Null World")
    p = Petition(
        petitioner_token="alice:123",
        petitioner_name="Alice",
        passport_admissions=(),
        message="Enter?",
    )
    response = w.petition(p)
    print(f"  response: {response}")
    assert isinstance(response, Refusal)
    assert response.reason


def test_nullworld_refuses_act():
    print("=== NullWorld: refuses act ===")
    w = NullWorld("world:null", "The Null World")
    a = Act(
        actor_token="alice:123",
        type="poem.turn",
        payload={},
    )
    response = w.act(a)
    print(f"  response: {response}")
    assert isinstance(response, Refusal)


def test_nullworld_log():
    print("=== NullWorld: log ===")
    w = NullWorld("world:null", "The Null World")
    w.petition(Petition(
        petitioner_token="alice:123",
        petitioner_name="Alice",
        passport_admissions=(),
        message="Enter?",
    ))
    w.act(Act(actor_token="alice:123", type="poem.turn", payload={}))
    log = w.log_since(None)
    print(f"  log entries: {len(log)}")
    for entry in log:
        print(f"    {entry.kind}: {entry.actor_token}")
    assert len(log) == 2


def test_nullworld_passes_conformance():
    print("=== NullWorld passes conformance ===")
    w = NullWorld("world:null", "The Null World")
    result = run_conformance(w)
    print(f"  passed: {result['passed']}")
    if not result['passed']:
        for f in result['failures']:
            print(f"    FAILURE: {f}")
    assert result["passed"]


def test_broken_world_fails_conformance():
    print("=== A broken world fails conformance ===")

    class BrokenWorld:
        def manifest(self):
            return None  # not a Manifest

        def petition(self, p):
            return "yes"  # not a valid response

        def act(self, a):
            return "ok"  # not a valid response

        def log_since(self, ts=None):
            return None  # not a list

    result = run_conformance(BrokenWorld())
    print(f"  passed: {result['passed']}")
    print(f"  failures: {len(result['failures'])}")
    for f in result["failures"][:3]:
        print(f"    {f}")
    assert not result["passed"]
    assert len(result["failures"]) >= 3


def test_fractal_architecture():
    """The whole point: a multiverse is a world, a federation is a
    multiverse. The protocol is the same at every level."""
    print("=== The protocol is fractal ===")

    # A world with no sub-registry
    world = NullWorld("world:poetry", "Poetry World")

    # A multiverse — also a NullWorld, but with a sub-registry
    class NullMultiverse(NullWorld):
        def __init__(self, entity_id, name, sub_registry_endpoint):
            super().__init__(entity_id, name)
            self._manifest = Manifest(
                entity_id=entity_id,
                name=name,
                protocol_version="WCP/0.1",
                law_url=f"null://{entity_id}/law",
                act_endpoint=f"null://{entity_id}/act",
                log_endpoint=f"null://{entity_id}/log",
                sub_registry_endpoint=sub_registry_endpoint,
            )

    multiverse = NullMultiverse(
        "multiverse:main", "Main Multiverse",
        "https://mv.example/worlds")

    # A federation — same protocol again
    federation = NullMultiverse(
        "federation:global", "Global Federation",
        "https://fed.example/multiverses")

    # All three are conforming:
    for entity in [world, multiverse, federation]:
        result = run_conformance(entity)
        print(f"  {entity.manifest().name}: "
              f"conforms={result['passed']}, "
              f"has_sub_registry={entity.manifest().has_sub_registry()}")
        assert result["passed"]

    # The *only* structural difference is whether the sub_registry
    # is populated.
    print("\n  → Same protocol at every level. Only difference is sub-registry.")


def test_modularity_claim():
    """A claim that this protocol is modular enough to be reimplemented.

    The claim: any developer can implement WorldProtocol without
    talking to us. This test *demonstrates* it by implementing a
    separate, independent, unrelated world — with completely
    different internals — that still conforms.
    """
    print("=== Modularity: a separate implementation ===")

    class IndependentWorld:
        """An entirely separate implementation, written fresh."""
        def __init__(self):
            self._manifest = Manifest(
                entity_id="independent:1",
                name="Independent World",
                protocol_version="WCP/0.1",
                law_url="independent:law",
                act_endpoint="independent:act",
                log_endpoint="independent:log",
            )
            self._events = []

        def manifest(self):
            return self._manifest

        def petition(self, p):
            # This world admits everyone, unconditionally
            self._events.append(("petition", p.petitioner_token))
            return Admission(
                entity_id="independent:1",
                timestamp="independent:0",
            )

        def act(self, a):
            # This world records every act, accepts everything
            self._events.append(("act", a.actor_token, a.type))
            return Ack(entity_id="independent:1", timestamp="independent:0")

        def log_since(self, ts=None):
            return [
                LogEntry(timestamp="independent:0", kind=kind,
                         actor_token=actor, data={})
                for event in self._events
                for kind, actor in [(event[0], event[1])]
            ]

    # It's an independent implementation, but WCP doesn't care.
    result = run_conformance(IndependentWorld())
    print(f"  passed: {result['passed']}")
    assert result["passed"]
    print("  → The protocol is implementation-agnostic.")


def test_different_laws_same_protocol():
    """The protocol doesn't care what the law is."""
    print("=== The law is opaque to the protocol ===")

    class LawAWorld(NullWorld):
        """Admits everyone named Alice."""
        def petition(self, p):
            if p.petitioner_name == "Alice":
                return Admission(entity_id="world:lawA", timestamp="t")
            return Refusal(reason="Only Alice may enter.")

    class LawBWorld(NullWorld):
        """Admits everyone whose passport has an admission."""
        def petition(self, p):
            if p.passport_admissions:
                return Admission(entity_id="world:lawB", timestamp="t")
            return Refusal(reason="Must have an admission.")

    # Both conform
    for w in [LawAWorld("world:lawA", "Law A"),
              LawBWorld("world:lawB", "Law B")]:
        result = run_conformance(w)
        print(f"  {w.manifest().name}: conforms={result['passed']}")
        assert result["passed"]

    # But they have different laws — the same petition gets different
    # responses
    p = Petition(
        petitioner_token="alice:123",
        petitioner_name="Alice",
        passport_admissions=(),
        message="Enter?",
    )
    wA = LawAWorld("world:lawA", "Law A")
    wB = LawBWorld("world:lawB", "Law B")
    rA = wA.petition(p)
    rB = wB.petition(p)
    print(f"\n  Same petition, different laws:")
    print(f"    Law A response: {rA}")
    print(f"    Law B response: {rB}")
    assert isinstance(rA, Admission)  # Alice is named Alice
    assert isinstance(rB, Refusal)    # No prior admissions
    print("  → Same protocol, different laws, different outcomes.")


if __name__ == "__main__":
    test_manifest_construction()
    test_manifest_with_sub_registry()
    test_manifest_validation()
    test_petition_and_act_structures()
    test_nullworld_manifest()
    test_nullworld_refuses_petition()
    test_nullworld_refuses_act()
    test_nullworld_log()
    test_nullworld_passes_conformance()
    test_broken_world_fails_conformance()
    test_fractal_architecture()
    test_modularity_claim()
    test_different_laws_same_protocol()

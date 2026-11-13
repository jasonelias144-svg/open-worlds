# multiverse_c6_test.py
from multiverse_c1 import create_identity
from multiverse_c3 import (
    Petition, Act, Admission as WCPAdmission, Refusal, Ack,
)
from multiverse_c3_conformance import run_conformance
from multiverse_c4 import PoetryWorld
from multiverse_c5 import ChemistryWorld
from multiverse_c6 import (
    MultiverseLaw, MultiverseRegistry,
    manifest_to_dict, manifest_from_dict,
    registry_from_log,
)


def _petition(name, token):
    return Petition(
        petitioner_token=token,
        petitioner_name=name,
        passport_admissions=(),
        message=f"{name} petitions.",
    )


def _admit_entity(actor_token, entity):
    return Act(
        actor_token=actor_token,
        type="multiverse.admit",
        payload={"entity": entity},
    )


def _remove_entity(actor_token, entity_id):
    return Act(
        actor_token=actor_token,
        type="multiverse.remove",
        payload={"entity_id": entity_id},
    )


def test_manifest_has_sub_registry():
    print("=== Manifest has sub_registry_endpoint ===")
    mv = MultiverseRegistry("multiverse:main", "Main Multiverse")
    m = mv.manifest()
    print(f"  entity_id: {m.entity_id}")
    print(f"  has_sub_registry: {m.has_sub_registry()}")
    print(f"  sub_registry_endpoint: {m.sub_registry_endpoint}")
    assert m.has_sub_registry()
    assert m.sub_registry_endpoint is not None


def test_conforms_to_wcp():
    print("=== Multiverse conforms to WCP/0.1 ===")
    mv = MultiverseRegistry("multiverse:main", "Main Multiverse")
    result = run_conformance(mv)
    print(f"  passed: {result['passed']}")
    if not result["passed"]:
        for f in result["failures"]:
            print(f"    {f}")
    assert result["passed"]


def test_admits_identity():
    print("=== Admits an identity ===")
    mv = MultiverseRegistry("multiverse:main", "Main Multiverse")
    alice = create_identity("Alice")
    r = mv.petition(_petition("Alice", alice.token))
    print(f"  petition response: {r}")
    assert isinstance(r, WCPAdmission)


def test_lists_conforming_entity():
    print("=== Lists a conforming entity ===")
    mv = MultiverseRegistry("multiverse:main", "Main Multiverse")
    alice = create_identity("Alice")
    mv.petition(_petition("Alice", alice.token))

    poetry = PoetryWorld("world:poetry", "The Poetry World")
    r = mv.act(_admit_entity(alice.token, poetry))
    print(f"  act response: {r}")
    assert isinstance(r, Ack)
    print(f"  entity_ids: {mv.entity_ids()}")
    assert "world:poetry" in mv.entity_ids()
    # The listed manifest is the poetry world's
    m = mv.get_manifest("world:poetry")
    assert m is not None
    assert m.name == "The Poetry World"


def test_refuses_non_conforming_entity():
    print("=== Refuses a non-conforming entity ===")

    class BrokenWorld:
        def manifest(self):
            return None  # not a Manifest
        def petition(self, p): return "yes"
        def act(self, a): return "ok"
        def log_since(self, ts=None): return None

    mv = MultiverseRegistry("multiverse:main", "Main Multiverse")
    alice = create_identity("Alice")
    mv.petition(_petition("Alice", alice.token))

    r = mv.act(_admit_entity(alice.token, BrokenWorld()))
    print(f"  act response: {r}")
    assert isinstance(r, Refusal)
    assert "fails conformance" in r.reason
    # Not in registry
    assert len(mv.entity_ids()) == 0


def test_refuses_duplicate():
    print("=== Refuses duplicate listing ===")
    mv = MultiverseRegistry("multiverse:main", "Main Multiverse")
    alice = create_identity("Alice")
    mv.petition(_petition("Alice", alice.token))
    poetry = PoetryWorld("world:poetry", "The Poetry World")
    r1 = mv.act(_admit_entity(alice.token, poetry))
    r2 = mv.act(_admit_entity(alice.token, poetry))
    print(f"  first:  {r1}")
    print(f"  second: {r2}")
    assert isinstance(r1, Ack)
    assert isinstance(r2, Refusal)
    assert "already listed" in r2.reason


def test_remove():
    print("=== Remove a listed entity ===")
    mv = MultiverseRegistry("multiverse:main", "Main Multiverse")
    alice = create_identity("Alice")
    mv.petition(_petition("Alice", alice.token))
    poetry = PoetryWorld("world:poetry", "The Poetry World")
    mv.act(_admit_entity(alice.token, poetry))
    r = mv.act(_remove_entity(alice.token, "world:poetry"))
    print(f"  remove response: {r}")
    assert isinstance(r, Ack)
    assert "world:poetry" not in mv.entity_ids()


def test_refuses_remove_missing():
    print("=== Refuses remove of missing entity ===")
    mv = MultiverseRegistry("multiverse:main", "Main Multiverse")
    alice = create_identity("Alice")
    mv.petition(_petition("Alice", alice.token))
    r = mv.act(_remove_entity(alice.token, "world:nonexistent"))
    print(f"  response: {r}")
    assert isinstance(r, Refusal)
    assert "not in registry" in r.reason


def test_never_converges():
    print("=== Never converges ===")
    mv = MultiverseRegistry("multiverse:main", "Main Multiverse")
    alice = create_identity("Alice")
    mv.petition(_petition("Alice", alice.token))
    # Admit 10 entities
    for i in range(10):
        world = PoetryWorld(f"world:{i}", f"World {i}")
        mv.act(_admit_entity(alice.token, world))
    print(f"  is_converged after 10 admissions: {mv.is_converged()}")
    assert mv.is_converged() is False


def test_multiverse_lists_two_different_laws():
    """The multiverse lists both Poetry and Chemistry — two
    completely different Laws, both conforming to WCP."""
    print("=== Multiverse lists two worlds, two laws ===")
    mv = MultiverseRegistry("multiverse:main", "Main Multiverse")
    alice = create_identity("Alice")
    mv.petition(_petition("Alice", alice.token))

    poetry = PoetryWorld("world:poetry", "The Poetry World")
    chemistry = ChemistryWorld("world:chemistry", "The Chemistry World")

    mv.act(_admit_entity(alice.token, poetry))
    mv.act(_admit_entity(alice.token, chemistry))

    print(f"  {mv.describe()}")
    subs = mv.list_sub_entities()
    print(f"  listed: {[m.entity_id for m in subs]}")
    assert len(subs) == 2
    entity_ids = {m.entity_id for m in subs}
    assert entity_ids == {"world:poetry", "world:chemistry"}

    # Clients can discover both worlds by querying the multiverse
    for m in subs:
        print(f"  discovered: {m.name} at {m.act_endpoint}")


def test_fractal_multiverse_in_multiverse():
    """The keystone test: a multiverse can be listed in another
    multiverse, proving the fractal property."""
    print("=== Fractal: multiverse in multiverse ===")

    # 1. Create the inner multiverse M1 and admit two worlds
    m1 = MultiverseRegistry("multiverse:inner", "Inner Multiverse")
    alice = create_identity("Alice")
    m1.petition(_petition("Alice", alice.token))
    poetry = PoetryWorld("world:poetry", "The Poetry World")
    chemistry = ChemistryWorld("world:chemistry", "The Chemistry World")
    m1.act(_admit_entity(alice.token, poetry))
    m1.act(_admit_entity(alice.token, chemistry))
    print(f"  M1 lists: {m1.entity_ids()}")

    # 2. Create the outer multiverse M0
    m0 = MultiverseRegistry("multiverse:outer", "Outer Multiverse")
    bob = create_identity("Bob")
    m0.petition(_petition("Bob", bob.token))

    # 3. M0 admits M1. M1 is a WCP entity, so it passes conformance.
    r = m0.act(_admit_entity(bob.token, m1))
    print(f"  M0.act(admit M1): {r}")
    assert isinstance(r, Ack)
    print(f"  M0 lists: {m0.entity_ids()}")
    assert "multiverse:inner" in m0.entity_ids()

    # 4. A client can traverse M0 → M1 → Poetry/Chemistry
    outer_subs = m0.list_sub_entities()
    print(f"\n  Client traversal:")
    print(f"    M0.list_sub_entities() → "
          f"{[m.entity_id for m in outer_subs]}")
    # M1's manifest has a sub_registry_endpoint
    m1_manifest = outer_subs[0]
    assert m1_manifest.has_sub_registry()
    # Client queries M1 (which it must hold separately in the
    # reference implementation; in a real system, via HTTP)
    inner_subs = m1.list_sub_entities()
    print(f"    M1.list_sub_entities() → "
          f"{[m.entity_id for m in inner_subs]}")
    assert len(inner_subs) == 2


def test_registry_from_log():
    print("=== Reconstruct registry from log ===")
    mv = MultiverseRegistry("multiverse:main", "Main Multiverse")
    alice = create_identity("Alice")
    mv.petition(_petition("Alice", alice.token))
    poetry = PoetryWorld("world:poetry", "The Poetry World")
    chemistry = ChemistryWorld("world:chemistry", "The Chemistry World")
    mv.act(_admit_entity(alice.token, poetry))
    mv.act(_admit_entity(alice.token, chemistry))
    mv.act(_remove_entity(alice.token, "world:chemistry"))

    # Reconstruct from log
    log = mv.log_since(None)
    reconstructed = registry_from_log(log)
    print(f"  reconstructed entity_ids: {sorted(reconstructed.keys())}")
    print(f"  actual entity_ids:        {sorted(mv.entity_ids())}")
    assert set(reconstructed.keys()) == set(mv.entity_ids())


def test_log_shows_conformance_reports():
    print("=== Log contains conformance reports ===")
    mv = MultiverseRegistry("multiverse:main", "Main Multiverse")
    alice = create_identity("Alice")
    mv.petition(_petition("Alice", alice.token))
    poetry = PoetryWorld("world:poetry", "The Poetry World")
    mv.act(_admit_entity(alice.token, poetry))
    log = mv.log_since(None)
    admissions = [e for e in log if e.kind == "entity_admitted"]
    print(f"  entity_admitted entries: {len(admissions)}")
    assert len(admissions) == 1
    report = admissions[0].data["conformance"]
    print(f"  conformance report: passed={report['passed']}")
    assert report["passed"]


def test_manifest_serialization():
    print("=== Manifest serialization roundtrip ===")
    m = Manifest(
        entity_id="world:test",
        name="Test World",
        protocol_version="WCP/0.1",
        law_url="x",
        act_endpoint="y",
        log_endpoint="z",
        sub_registry_endpoint="w",
    )
    d = manifest_to_dict(m)
    m2 = manifest_from_dict(d)
    print(f"  roundtrip: {m2.entity_id} == {m.entity_id}")
    assert m2.entity_id == m.entity_id
    assert m2.sub_registry_endpoint == m.sub_registry_endpoint


def test_end_to_end():
    """The full multiverse: M0 lists M1, M1 lists two worlds, and
    a client can traverse the whole structure."""
    print("=== Full multiverse: M0 → M1 → Poetry + Chemistry ===")

    # Setup
    m1 = MultiverseRegistry("multiverse:inner", "Inner Multiverse")
    alice = create_identity("Alice")
    m1.petition(_petition("Alice", alice.token))
    m1.act(_admit_entity(alice.token, PoetryWorld(
        "world:poetry", "Poetry World")))
    m1.act(_admit_entity(alice.token, ChemistryWorld(
        "world:chemistry", "Chemistry World")))

    m0 = MultiverseRegistry("multiverse:outer", "Outer Multiverse")
    bob = create_identity("Bob")
    m0.petition(_petition("Bob", bob.token))
    m0.act(_admit_entity(bob.token, m1))

    print(f"\n{m0.describe()}")
    print(f"\n{m1.describe()}")

    # Traverse
    print("\nClient traversal:")
    print("  1. Query M0.list_sub_entities()")
    l1 = m0.list_sub_entities()
    print(f"     → {[m.entity_id for m in l1]}")
    print("  2. Follow M1.sub_registry_endpoint")
    print(f"     M1 at: {l1[0].sub_registry_endpoint}")
    print("  3. Query M1.list_sub_entities()")
    l2 = m1.list_sub_entities()
    print(f"     → {[m.entity_id for m in l2]}")
    print("  4. Client now knows Poetry and Chemistry")

    assert len(l1) == 1
    assert len(l2) == 2

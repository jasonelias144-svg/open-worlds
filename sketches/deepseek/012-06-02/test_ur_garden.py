import pytest
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey)
from ur_garden import (
    Cell, Plant, GardenWorld, HAS_CRYPTO,
)
from garden_adapter import GardenAdapter, _PHRASES
from microverse import ChaosGameHost, ElementaryCAHost
from chaos_game_world import (
    ChaosGameWorld, SIERPINSKI, BARNSLEY,
)
from elementary_ca_world import ElementaryCAWorld, rule_30
from multiverse_c3 import Petition, Act, Ack, Refusal, Admission
from unified_individual import (
    UnifiedIndividualSession, pack_unified_bundle,
    verify_unified_individual_with_adapters,
)
from coupled_learners import TinyRNN

pytestmark = pytest.mark.skipif(
    not HAS_CRYPTO, reason="cryptography not installed")


def _kp(): return Ed25519PrivateKey.generate()


def _garden_with_plants():
    g = GardenWorld("world:g", "G", _kp())
    def _chaos(kind, preset, seed):
        kp = _kp()
        w = ChaosGameWorld(
            preset=preset, growth_mode="seeded_random",
            initial_point=(500, 500), keypair=kp,
            prng_seed=seed)
        return ChaosGameHost(f"plant:{kind}", w,
                              kp.public_key().public_bytes(
                                  encoding=__import__(
                                      "cryptography.hazmat."
                                      "primitives.serialization",
                                      fromlist=["Encoding"]
                                  ).Encoding.Raw,
                                  format=__import__(
                                      "cryptography.hazmat."
                                      "primitives.serialization",
                                      fromlist=["PublicFormat"]
                                  ).PublicFormat.Raw).hex())
    # Simpler: build directly
    def _make_fern():
        kp = _kp()
        w = ChaosGameWorld(
            preset=BARNSLEY, growth_mode="seeded_random",
            initial_point=(500, 500), keypair=kp,
            prng_seed=0xAAAA)
        from individual_bundle import _did_from_kp
        return ChaosGameHost(
            "plant:fern", w, _did_from_kp(kp),
            description="fern")
    def _make_vine():
        kp = _kp()
        w = ElementaryCAWorld(
            params=rule_30(), initial_cells=[0],
            keypair=kp)
        from individual_bundle import _did_from_kp
        return ElementaryCAHost(
            "plant:vine", w, _did_from_kp(kp),
            description="vine")
    g.add_plant("fern", "fern", _make_fern(), Cell(2, 2))
    g.add_plant("vine", "vine", _make_vine(), Cell(4, 6))
    return g


# -- Cell --

def test_cell_step():
    c = Cell(3, 4)
    assert c.step("N") == Cell(3, 3)
    assert c.step("S") == Cell(3, 5)
    assert c.step("E") == Cell(4, 4)
    assert c.step("W") == Cell(2, 4)


def test_cell_adjacency():
    a = Cell(3, 4)
    assert a.adjacent(Cell(3, 5))
    assert a.adjacent(Cell(4, 4))
    assert not a.adjacent(Cell(4, 5))
    assert not a.adjacent(Cell(3, 4))


# -- Garden basics --

def test_add_plant_bounds():
    g = GardenWorld("world:g", "G", _kp())
    with pytest.raises(ValueError):
        g.add_plant("x", "x", None, Cell(100, 100))


def test_add_plant_occupied():
    g = _garden_with_plants()
    with pytest.raises(ValueError):
        # Position occupied by fern
        kp = _kp()
        w = ChaosGameWorld(
            preset=SIERPINSKI, growth_mode="seeded_random",
            initial_point=(500, 500), keypair=kp,
            prng_seed=0xBBBB)
        from individual_bundle import _did_from_kp
        host = ChaosGameHost("plant:dup", w, _did_from_kp(kp))
        g.add_plant("dup", "chaos", host, Cell(2, 2))


def test_retire_plant():
    g = _garden_with_plants()
    g.retire_plant("fern")
    assert "fern" not in g.plants()
    # But still in all_plants (for cross-reference verification)
    assert "fern" in g.all_plants()


def test_advance_cycle_grows_plants():
    g = _garden_with_plants()
    initial_events = sum(
        len(p.host.events()) for p in g.plants().values())
    g.advance_cycle(3)
    after = sum(
        len(p.host.events()) for p in g.plants().values())
    assert after == initial_events + 6  # 3 per plant × 2 plants
    assert g.cycle() == 1


# -- Agent acts --

def test_agent_enters():
    g = _garden_with_plants()
    kp = _kp()
    tok = _did_from_kp(kp)
    g.petition(Petition(
        petitioner_token=tok, petitioner_name="A",
        passport_admissions=(), message=""))
    g.act(Act(
        actor_token=tok, type="garden.walk",
        payload={"start": [0, 4]}))
    assert g.position_of(tok) == Cell(0, 4)


def test_walk_out_of_bounds():
    g = _garden_with_plants()
    kp = _kp()
    tok = _did_from_kp(kp)
    g.petition(Petition(
        petitioner_token=tok, petitioner_name="A",
        passport_admissions=(), message=""))
    g.act(Act(
        actor_token=tok, type="garden.walk",
        payload={"start": [0, 0]}))
    r = g.act(Act(
        actor_token=tok, type="garden.walk",
        payload={"direction": "N"}))
    assert isinstance(r, Refusal)


def test_walk_into_plant_refused():
    g = _garden_with_plants()
    kp = _kp()
    tok = _did_from_kp(kp)
    g.petition(Petition(
        petitioner_token=tok, petitioner_name="A",
        passport_admissions=(), message=""))
    # Start next to fern at (2,2), i.e. (2,3)
    g.act(Act(
        actor_token=tok, type="garden.walk",
        payload={"start": [2, 3]}))
    r = g.act(Act(
        actor_token=tok, type="garden.walk",
        payload={"direction": "N"}))  # into fern
    assert isinstance(r, Refusal)


def test_observe_nothing_adjacent():
    g = _garden_with_plants()
    kp = _kp()
    tok = _did_from_kp(kp)
    g.petition(Petition(
        petitioner_token=tok, petitioner_name="A",
        passport_admissions=(), message=""))
    g.act(Act(
        actor_token=tok, type="garden.walk",
        payload={"start": [0, 0]}))
    r = g.act(Act(
        actor_token=tok, type="garden.observe",
        payload={}))
    assert isinstance(r, Ack)
    latest = g.log_since(None)[-1]
    assert latest["result"] == "nothing_adjacent"


def test_observe_adjacent_plant():
    g = _garden_with_plants()
    # Advance fern so it has events
    for _ in range(3):
        g.advance_cycle(1)
    kp = _kp()
    tok = _did_from_kp(kp)
    g.petition(Petition(
        petitioner_token=tok, petitioner_name="A",
        passport_admissions=(), message=""))
    # Start at (2, 3), adjacent to fern at (2, 2)
    g.act(Act(
        actor_token=tok, type="garden.walk",
        payload={"start": [2, 3]}))
    r = g.act(Act(
        actor_token=tok, type="garden.observe",
        payload={}))
    assert isinstance(r, Ack)
    latest = g.log_since(None)[-1]
    assert latest["result"] == "observed_plant"
    assert latest["plant_id"] == "fern"
    # And the referenced event exists
    fern = g.all_plants()["fern"]
    assert any(ev["hash"] == latest["plant_event_hash"]
                for ev in fern.host.events())


def test_speak_heard_by_nearby():
    g = _garden_with_plants()
    a_kp = _kp()
    b_kp = _kp()
    a_tok = _did_from_kp(a_kp)
    b_tok = _did_from_kp(b_kp)
    for tok, name in ((a_tok, "A"), (b_tok, "B")):
        g.petition(Petition(
            petitioner_token=tok, petitioner_name=name,
            passport_admissions=(), message=""))
    g.act(Act(
        actor_token=a_tok, type="garden.walk",
        payload={"start": [0, 0]}))
    g.act(Act(
        actor_token=b_tok, type="garden.walk",
        payload={"start": [0, 1]}))
    r = g.act(Act(
        actor_token=a_tok, type="garden.speak",
        payload={"text": "hello"}))
    assert isinstance(r, Ack)
    latest = g.log_since(None)[-1]
    assert b_tok in latest["heard_by"]


# -- Cross-references --

def test_cross_references_verify():
    g = _garden_with_plants()
    for _ in range(2):
        g.advance_cycle(1)
    kp = _kp()
    tok = _did_from_kp(kp)
    g.petition(Petition(
        petitioner_token=tok, petitioner_name="A",
        passport_admissions=(), message=""))
    g.act(Act(
        actor_token=tok, type="garden.walk",
        payload={"start": [2, 3]}))
    g.act(Act(
        actor_token=tok, type="garden.observe",
        payload={}))
    ok, reason = g.verify_cross_references()
    assert ok, reason


def test_tampered_cross_reference_fails():
    g = _garden_with_plants()
    g.advance_cycle(2)
    kp = _kp()
    tok = _did_from_kp(kp)
    g.petition(Petition(
        petitioner_token=tok, petitioner_name="A",
        passport_admissions=(), message=""))
    g.act(Act(
        actor_token=tok, type="garden.walk",
        payload={"start": [2, 3]}))
    g.act(Act(
        actor_token=tok, type="garden.observe",
        payload={}))
    for i, e in enumerate(g._log):
        if e.get("kind") == "agent_observed" \
                and e.get("result") == "observed_plant":
            g._log[i] = {**e, "plant_event_hash": "00" * 32}
            break
    ok, _ = g.verify_cross_references()
    assert not ok


# -- Adapter --

def test_adapter_forces_wander_first():
    """With no position in memory, the adapter... actually
    entry always sets a start position. Verify from a fresh
    memory with position_from_memory returning None."""
    adapter = GardenAdapter()
    # Empty memory → no position
    pos = adapter._position_from_memory([])
    assert pos is None


def test_adapter_state_reads_position():
    adapter = GardenAdapter()
    memory = [
        {"type": "world_entry", "tier": "garden",
         "start_position": [3, 4]},
    ]
    state = adapter.state(memory, None)
    assert state[2] == 3 / 8  # x normalized
    assert state[3] == 4 / 7  # y normalized


def test_adapter_state_after_wander():
    adapter = GardenAdapter()
    memory = [
        {"type": "world_entry", "tier": "garden",
         "start_position": [3, 4]},
        {"type": "agent_step", "tier": "garden",
         "action_idx": 0, "reward_micros": 50000,
         "position_after": [4, 4]},
    ]
    state = adapter.state(memory, None)
    assert state[0] == 0
    assert state[1] == 0.05
    assert state[2] == 4 / 8


# -- Full pipeline --

def test_full_pipeline():
    g = _garden_with_plants()
    a_kp = _kp()
    a = UnifiedIndividualSession(
        individual_kp=a_kp,
        model=TinyRNN(n_actions=3, hidden=4,
                       n_extra_inputs=0, seed=42))
    a.enter_world_via_adapter(GardenAdapter(), {
        "world_id": g.manifest().entity_id,
        "world": g,
        "world_signer": g.world_signer(),
        "display_name": "Test",
        "start_position": [0, 4],
    })
    for _ in range(5):
        a.step_via_adapter()
        g.advance_cycle(1)
    bundle = pack_unified_bundle(
        a, persona="t", name="Test", initial_seed=42)
    world_logs = {
        g.manifest().entity_id:
            GardenAdapter().world_log(g)}
    ok, reason = verify_unified_individual_with_adapters(
        bundle, world_logs,
        adapters_by_tier={"garden": GardenAdapter()})
    assert ok, reason


def test_demo(tmp_path):
    from ur_garden import demo
    audit = demo(artifact_dir=str(tmp_path))
    assert audit["verification"]["alice_bundle"] is True
    assert audit["verification"]["bob_bundle"] is True
    assert audit["verification"]["garden_log"] is True
    assert audit["verification"]["cross_references"] is True
    assert audit["cycles"] == 23
    assert len(audit["plants"]) == 4
    assert (tmp_path / "ur_garden" /
            "ur_garden_demo.json").exists()

import json
import pytest
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey)
from individual_bundle import _canonical, _hash, _did_from_kp
from microverse import (
    FractalHost, ChaosGameHost, ElementaryCAHost,
    MicroverseWorld,
)
from microverse_adapter import MicroverseAdapter, _pick_phrase
from unified_individual import (
    UnifiedIndividualSession, pack_unified_bundle,
    verify_unified_individual_with_adapters,
)
from coupled_learners import TinyRNN
from chaos_game_world import ChaosGameWorld, SIERPINSKI
from elementary_ca_world import ElementaryCAWorld, rule_90
from multiverse_c3 import Petition, Act, Ack, Refusal, Admission
from microverse import HAS_CRYPTO

pytestmark = pytest.mark.skipif(
    not HAS_CRYPTO, reason="cryptography not installed")


def _kp():
    return Ed25519PrivateKey.generate()


def _microverse_with_hosts():
    mv = MicroverseWorld(
        "world:mv", "MV", _kp(), description="test")
    ch_kp = _kp()
    ch = ChaosGameHost(
        "host:ch",
        ChaosGameWorld(
            preset=SIERPINSKI, growth_mode="seeded_random",
            initial_point=(500, 500), keypair=ch_kp,
            prng_seed=0xAAAA),
        _did_from_kp(ch_kp), description="chaos")
    eca_kp = _kp()
    eca = ElementaryCAHost(
        "host:eca",
        ElementaryCAWorld(
            params=rule_90(), initial_cells=[0],
            keypair=eca_kp),
        _did_from_kp(eca_kp), description="ca")
    mv.add_host(ch)
    mv.add_host(eca)
    return mv, ch, eca


# -- FractalHost --

def test_chaos_host_advance():
    ch_kp = _kp()
    ch = ChaosGameHost(
        "host:ch",
        ChaosGameWorld(
            preset=SIERPINSKI, growth_mode="seeded_random",
            initial_point=(500, 500), keypair=ch_kp,
            prng_seed=0xAAAA),
        _did_from_kp(ch_kp))
    events = ch.advance(3)
    assert len(events) == 3
    assert all(ev["kind"] == "chaos_step" for ev in events)


def test_eca_host_advance():
    eca_kp = _kp()
    eca = ElementaryCAHost(
        "host:eca",
        ElementaryCAWorld(
            params=rule_90(), initial_cells=[0],
            keypair=eca_kp),
        _did_from_kp(eca_kp))
    events = eca.advance(5)
    assert len(events) == 5
    assert all(ev["kind"] == "eca_gen" for ev in events)


# -- Microverse basics --

def test_add_host():
    mv, _, _ = _microverse_with_hosts()
    assert set(mv.hosts().keys()) == {"host:ch", "host:eca"}
    assert mv.host_order() == ["host:ch", "host:eca"]


def test_retire_host():
    mv, _, _ = _microverse_with_hosts()
    mv.retire_host("host:ch")
    assert set(mv.hosts().keys()) == {"host:eca"}
    assert "host:ch" not in mv.host_order()


def test_retire_removes_focus():
    mv, _, _ = _microverse_with_hosts()
    alice = _kp()
    mv.petition(Petition(
        petitioner_token=_did_from_kp(alice),
        petitioner_name="A", passport_admissions=(),
        message=""))
    mv.act(Act(
        actor_token=_did_from_kp(alice),
        type="mv.move",
        payload={"target_host_id": "host:ch"}))
    assert mv.agent_focus(_did_from_kp(alice)) == "host:ch"
    mv.retire_host("host:ch")
    assert mv.agent_focus(_did_from_kp(alice)) is None


def test_advance_cycle_grows_hosts():
    mv, ch, eca = _microverse_with_hosts()
    initial_events = len(ch.events()) + len(eca.events())
    mv.advance_cycle(2)
    assert len(ch.events()) + len(eca.events()) == initial_events + 4
    assert mv.cycle() == 1


# -- Agent acts --

def test_petition_admits():
    mv, _, _ = _microverse_with_hosts()
    kp = _kp()
    r = mv.petition(Petition(
        petitioner_token=_did_from_kp(kp),
        petitioner_name="A", passport_admissions=(),
        message=""))
    assert isinstance(r, Admission)


def test_duplicate_admit_refused():
    mv, _, _ = _microverse_with_hosts()
    kp = _kp()
    tok = _did_from_kp(kp)
    mv.petition(Petition(
        petitioner_token=tok, petitioner_name="A",
        passport_admissions=(), message=""))
    r = mv.petition(Petition(
        petitioner_token=tok, petitioner_name="A",
        passport_admissions=(), message=""))
    assert isinstance(r, Refusal)


def test_move_to_host():
    mv, _, _ = _microverse_with_hosts()
    kp = _kp()
    tok = _did_from_kp(kp)
    mv.petition(Petition(
        petitioner_token=tok, petitioner_name="A",
        passport_admissions=(), message=""))
    r = mv.act(Act(
        actor_token=tok, type="mv.move",
        payload={"target_host_id": "host:ch"}))
    assert isinstance(r, Ack)
    assert mv.agent_focus(tok) == "host:ch"


def test_move_unknown_host_refused():
    mv, _, _ = _microverse_with_hosts()
    kp = _kp()
    tok = _did_from_kp(kp)
    mv.petition(Petition(
        petitioner_token=tok, petitioner_name="A",
        passport_admissions=(), message=""))
    r = mv.act(Act(
        actor_token=tok, type="mv.move",
        payload={"target_host_id": "host:none"}))
    assert isinstance(r, Refusal)


def test_observe_requires_focus():
    mv, _, _ = _microverse_with_hosts()
    kp = _kp()
    tok = _did_from_kp(kp)
    mv.petition(Petition(
        petitioner_token=tok, petitioner_name="A",
        passport_admissions=(), message=""))
    r = mv.act(Act(
        actor_token=tok, type="mv.observe", payload={}))
    assert isinstance(r, Refusal)


def test_observe_at_host():
    mv, ch, _ = _microverse_with_hosts()
    ch.advance(3)
    kp = _kp()
    tok = _did_from_kp(kp)
    mv.petition(Petition(
        petitioner_token=tok, petitioner_name="A",
        passport_admissions=(), message=""))
    mv.act(Act(
        actor_token=tok, type="mv.move",
        payload={"target_host_id": "host:ch"}))
    r = mv.act(Act(
        actor_token=tok, type="mv.observe", payload={}))
    assert isinstance(r, Ack)
    # Log entry references a real event
    latest = mv.log_since(None)[-1]
    assert latest["kind"] == "agent_observed"
    target = latest["observed_event_hash"]
    assert any(ev["hash"] == target for ev in ch.events())


def test_speak():
    mv, _, _ = _microverse_with_hosts()
    kp = _kp()
    tok = _did_from_kp(kp)
    mv.petition(Petition(
        petitioner_token=tok, petitioner_name="A",
        passport_admissions=(), message=""))
    mv.act(Act(
        actor_token=tok, type="mv.move",
        payload={"target_host_id": "host:ch"}))
    r = mv.act(Act(
        actor_token=tok, type="mv.speak",
        payload={"text": "the pattern grows"}))
    assert isinstance(r, Ack)


def test_speak_requires_text():
    mv, _, _ = _microverse_with_hosts()
    kp = _kp()
    tok = _did_from_kp(kp)
    mv.petition(Petition(
        petitioner_token=tok, petitioner_name="A",
        passport_admissions=(), message=""))
    r = mv.act(Act(
        actor_token=tok, type="mv.speak",
        payload={"text": ""}))
    assert isinstance(r, Refusal)


# -- Verification --

def test_verify_log():
    mv, _, _ = _microverse_with_hosts()
    kp = _kp()
    tok = _did_from_kp(kp)
    mv.petition(Petition(
        petitioner_token=tok, petitioner_name="A",
        passport_admissions=(), message=""))
    mv.act(Act(
        actor_token=tok, type="mv.move",
        payload={"target_host_id": "host:ch"}))
    ok, reason = mv.verify_log()
    assert ok, reason


def test_verify_cross_references():
    mv, ch, _ = _microverse_with_hosts()
    ch.advance(2)
    kp = _kp()
    tok = _did_from_kp(kp)
    mv.petition(Petition(
        petitioner_token=tok, petitioner_name="A",
        passport_admissions=(), message=""))
    mv.act(Act(
        actor_token=tok, type="mv.move",
        payload={"target_host_id": "host:ch"}))
    mv.act(Act(
        actor_token=tok, type="mv.observe", payload={}))
    ok, reason = mv.verify_cross_references()
    assert ok, reason


def test_tampered_cross_reference_fails():
    mv, ch, _ = _microverse_with_hosts()
    ch.advance(2)
    kp = _kp()
    tok = _did_from_kp(kp)
    mv.petition(Petition(
        petitioner_token=tok, petitioner_name="A",
        passport_admissions=(), message=""))
    mv.act(Act(
        actor_token=tok, type="mv.move",
        payload={"target_host_id": "host:ch"}))
    mv.act(Act(
        actor_token=tok, type="mv.observe", payload={}))
    # Tamper the log entry
    for i, e in enumerate(mv._log):
        if e["kind"] == "agent_observed":
            mv._log[i] = {**e, "observed_event_hash": "00" * 32}
            break
    ok, _ = mv.verify_cross_references()
    assert not ok


# -- Adapter --

def test_adapter_state_reads_memory():
    mv, _, _ = _microverse_with_hosts()
    adapter = MicroverseAdapter()
    handle = mv
    memory = []
    state = adapter.state(memory, handle)
    assert len(state) == 4
    # No actions yet → last_action 0, no focus
    assert state[2] == 0.5


def test_adapter_action_from_index_must_move_first():
    """With no focus, the adapter forces a move to the first
    host."""
    mv, _, _ = _microverse_with_hosts()
    adapter = MicroverseAdapter()
    action = adapter.action_from_index(1, [])
    assert action["act"] == "move"
    assert action["target_host_id"] == "host:ch"


def test_pick_phrase_deterministic():
    p1 = _pick_phrase("host:ch", [])
    p2 = _pick_phrase("host:ch", [])
    assert p1 == p2


# -- Full pipeline --

def test_full_microverse_pipeline():
    mv, ch, _ = _microverse_with_hosts()
    kp = _kp()
    session = UnifiedIndividualSession(
        individual_kp=kp,
        model=TinyRNN(n_actions=3, hidden=4,
                       n_extra_inputs=0, seed=42))
    session.enter_world_via_adapter(MicroverseAdapter(), {
        "world_id": mv.manifest().entity_id,
        "world": mv,
        "world_signer": mv.world_signer(),
        "display_name": "Test",
    })
    for _ in range(3):
        session.step_via_adapter()
        mv.advance_cycle(1)
    bundle = pack_unified_bundle(
        session, persona="test", name="Test",
        initial_seed=42)
    world_logs = {mv.manifest().entity_id:
                    list(mv.log_since(None))}
    ok, reason = verify_unified_individual_with_adapters(
        bundle, world_logs)
    assert ok, reason


# -- Demo --

def test_demo(tmp_path):
    from microverse import demo
    audit = demo(artifact_dir=str(tmp_path))
    assert audit["verification"]["alice_bundle"] is True
    assert audit["verification"]["bob_bundle"] is True
    assert audit["verification"]["microverse_log"] is True
    assert audit["verification"]["cross_references"] is True
    assert audit["cycles"] == 8
    assert len(audit["final_hosts"]) == 2
    assert (tmp_path / "microverse" /
            "microverse_demo.json").exists()

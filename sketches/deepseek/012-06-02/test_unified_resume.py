import json
import time
import pytest
import chess
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey)
from individual_bundle import IndividualBundle, _canonical, _hash
from unified_individual import (
    UnifiedIndividualSession, pack_unified_bundle,
    resume_unified_from_bundle, verify_unified_individual_basic,
    verify_unified_individual_with_adapters,
    verify_resumed_unified_full,
)
from world_adapters import (
    FederatedAdapter, ChessAdapter, GrowingCanvasAdapter,
)
from resumable import verify_resumed_from
from lifetime import verify_individual_lifetime
from coupled_learners import TinyRNN, SIERPINSKI
from world_agent_coupling import ScriptedWorld
from multiverse_c73 import ChessWorld
from multiverse_c81 import GrowingWorld
from signed_world_log import (
    SignedLogWorld, SignedLogWorldServer,
)

HAS_CHESS = True
try:
    import chess  # noqa
except ImportError:
    HAS_CHESS = False

pytestmark = pytest.mark.skipif(
    not HAS_CHESS,
    reason="requires python-chess")


def _kp():
    return Ed25519PrivateKey.generate()


def _build_parent_federated_only():
    """Simplest case: parent has only federated memory."""
    session = UnifiedIndividualSession(
        individual_kp=_kp(),
        model=TinyRNN(n_actions=3, hidden=4,
                       n_extra_inputs=0, seed=100))
    fed = ScriptedWorld(
        kp=_kp(), initial_point_b=(800, 800),
        k_b=50, prng_seed_b=0xBBBB, rule=SIERPINSKI)
    session.enter_world_via_adapter(FederatedAdapter(), {
        "world_id": fed.world_id,
        "world": fed,
        "world_signer": fed.world_id,
        "initial_point": (200, 800),
    })
    for _ in range(3):
        session.step_via_adapter()
    bundle = pack_unified_bundle(
        session, persona="test", name="t", initial_seed=100)
    world_logs = {
        fed.world_id: [
            {"body": r.body(), "sig": r.sig,
             "record_hash": r.record_hash()}
            for r in fed.records],
    }
    return session, bundle, fed, world_logs


# -- Resume basics --

def test_resume_happy_path():
    _, parent, fed, _ = _build_parent_federated_only()
    kp = Ed25519PrivateKey.from_private_bytes(
        # We need the same kp; regenerate not possible.
        # Instead, build session with known kp:
        bytes(32))  # dummy
    # Rebuild with explicit kp
    kp = _kp()
    session = UnifiedIndividualSession(
        individual_kp=kp,
        model=TinyRNN(n_actions=3, hidden=4,
                       n_extra_inputs=0, seed=200))
    w = ScriptedWorld(
        kp=_kp(), initial_point_b=(800, 800),
        k_b=50, prng_seed_b=0xAAAA, rule=SIERPINSKI)
    session.enter_world_via_adapter(FederatedAdapter(), {
        "world_id": w.world_id, "world": w,
        "world_signer": w.world_id,
        "initial_point": (200, 800)})
    for _ in range(3):
        session.step_via_adapter()
    parent = pack_unified_bundle(
        session, persona="test", name="p", initial_seed=200)

    # Resume into canvas
    canvas = GrowingWorld("world:canvas", "Canvas", _kp())
    resumed, reason = resume_unified_from_bundle(
        parent, kp, GrowingCanvasAdapter(), {
            "world_id": "world:canvas",
            "world": canvas,
            "world_signer": canvas.curator_public_key,
            "display_name": "t"})
    assert resumed is not None, reason
    assert len(resumed.memory) == len(parent.memory) + 1


def test_resume_wrong_keypair():
    kp = _kp()
    session = UnifiedIndividualSession(
        individual_kp=kp,
        model=TinyRNN(n_actions=3, hidden=4,
                       n_extra_inputs=0, seed=100))
    w = ScriptedWorld(
        kp=_kp(), initial_point_b=(800, 800),
        k_b=50, prng_seed_b=0xAAAA, rule=SIERPINSKI)
    session.enter_world_via_adapter(FederatedAdapter(), {
        "world_id": w.world_id, "world": w,
        "world_signer": w.world_id,
        "initial_point": (200, 800)})
    session.step_via_adapter()
    parent = pack_unified_bundle(
        session, persona="p", name="p", initial_seed=100)

    wrong_kp = _kp()
    resumed, reason = resume_unified_from_bundle(
        parent, wrong_kp, FederatedAdapter(), {
            "world_id": "world:other",
            "world": ScriptedWorld(
                kp=_kp(), initial_point_b=(800, 800),
                k_b=0, prng_seed_b=0x1111, rule=SIERPINSKI),
            "world_signer": "did:key:" + "00" * 32,
            "initial_point": (0, 0)})
    assert resumed is None
    assert "keypair" in reason.lower()


def test_resume_non_unified_parent():
    # Build a federated (non-unified) bundle
    from federated_bundle import (
        FederatedSession, pack_federated_bundle,
    )
    kp = _kp()
    model = TinyRNN(n_extra_inputs=0, seed=100)
    mem = []
    w = ScriptedWorld(
        kp=_kp(), initial_point_b=(800, 800),
        k_b=50, prng_seed_b=0xAAAA, rule=SIERPINSKI)
    s = FederatedSession(
        individual_kp=kp, model=model, world=w,
        initial_point=(200, 800), memory=mem,
        rule=SIERPINSKI)
    for _ in range(3):
        s.step()
    parent = pack_federated_bundle(
        individual_kp=kp, model=model,
        sessions=[s], memory=mem,
        persona="p", initial_seed=100, name="p")
    resumed, reason = resume_unified_from_bundle(
        parent, kp, FederatedAdapter(), {
            "world_id": "w2",
            "world": ScriptedWorld(
                kp=_kp(), initial_point_b=(800, 800),
                k_b=0, prng_seed_b=0x1111,
                rule=SIERPINSKI),
            "world_signer": "did:key:" + "00" * 32,
            "initial_point": (0, 0)})
    assert resumed is None
    assert "kind" in reason.lower() or "unified" in reason.lower()


# -- Continuity --

def test_continuity_verifies():
    _, parent, _, _ = _build_parent_federated_only()
    kp_required = None
    # Need the kp; rebuild with known kp
    kp = _kp()
    session = UnifiedIndividualSession(
        individual_kp=kp,
        model=TinyRNN(n_actions=3, hidden=4,
                       n_extra_inputs=0, seed=300))
    w = ScriptedWorld(
        kp=_kp(), initial_point_b=(800, 800),
        k_b=50, prng_seed_b=0x1111, rule=SIERPINSKI)
    session.enter_world_via_adapter(FederatedAdapter(), {
        "world_id": w.world_id, "world": w,
        "world_signer": w.world_id,
        "initial_point": (200, 800)})
    for _ in range(3):
        session.step_via_adapter()
    parent = pack_unified_bundle(
        session, persona="p", name="p", initial_seed=300)

    canvas = GrowingWorld("world:canvas", "Canvas", _kp())
    resumed_session, _ = resume_unified_from_bundle(
        parent, kp, GrowingCanvasAdapter(), {
            "world_id": "world:canvas",
            "world": canvas,
            "world_signer": canvas.curator_public_key,
            "display_name": "t"})
    assert resumed_session is not None
    resumed_session.step_via_adapter()
    resumed = pack_unified_bundle(
        resumed_session, persona="r", name="r",
        initial_seed=300,
        resumed_from=parent.manifest["memory_root"])
    v = verify_resumed_from(resumed, parent)
    assert v[0], v[1]


def test_continuity_wrong_parent():
    _, parent, _, _ = _build_parent_federated_only()
    kp = _kp()
    session = UnifiedIndividualSession(
        individual_kp=kp,
        model=TinyRNN(n_actions=3, hidden=4,
                       n_extra_inputs=0, seed=400))
    w = ScriptedWorld(
        kp=_kp(), initial_point_b=(800, 800),
        k_b=50, prng_seed_b=0x2222, rule=SIERPINSKI)
    session.enter_world_via_adapter(FederatedAdapter(), {
        "world_id": w.world_id, "world": w,
        "world_signer": w.world_id,
        "initial_point": (200, 800)})
    session.step_via_adapter()
    parent = pack_unified_bundle(
        session, persona="p", name="p", initial_seed=400)
    canvas = GrowingWorld("world:canvas", "Canvas", _kp())
    resumed_session, _ = resume_unified_from_bundle(
        parent, kp, GrowingCanvasAdapter(), {
            "world_id": "world:canvas",
            "world": canvas,
            "world_signer": canvas.curator_public_key,
            "display_name": "t"})
    resumed = pack_unified_bundle(
        resumed_session, persona="r", name="r",
        initial_seed=400,
        resumed_from=parent.manifest["memory_root"])
    # Verify against a *different* parent
    _, other_parent, _, _ = _build_parent_federated_only()
    v = verify_resumed_from(resumed, other_parent)
    assert not v[0]


def test_continuity_tampered_prefix():
    kp = _kp()
    session = UnifiedIndividualSession(
        individual_kp=kp,
        model=TinyRNN(n_actions=3, hidden=4,
                       n_extra_inputs=0, seed=500))
    w = ScriptedWorld(
        kp=_kp(), initial_point_b=(800, 800),
        k_b=50, prng_seed_b=0x3333, rule=SIERPINSKI)
    session.enter_world_via_adapter(FederatedAdapter(), {
        "world_id": w.world_id, "world": w,
        "world_signer": w.world_id,
        "initial_point": (200, 800)})
    for _ in range(3):
        session.step_via_adapter()
    parent = pack_unified_bundle(
        session, persona="p", name="p", initial_seed=500)
    canvas = GrowingWorld("world:canvas", "Canvas", _kp())
    resumed_session, _ = resume_unified_from_bundle(
        parent, kp, GrowingCanvasAdapter(), {
            "world_id": "world:canvas",
            "world": canvas,
            "world_signer": canvas.curator_public_key,
            "display_name": "t"})
    resumed = pack_unified_bundle(
        resumed_session, persona="r", name="r",
        initial_seed=500,
        resumed_from=parent.manifest["memory_root"])
    # Tamper a prefix entry
    for i, r in enumerate(resumed.memory):
        if r.get("type") == "agent_step":
            resumed.memory[i] = {
                **r, "reward_micros": 999999}
            break
    v = verify_resumed_from(resumed, parent)
    assert not v[0]


# -- Composition with full verification --

def test_resumed_unified_full_verifies():
    kp = _kp()
    session = UnifiedIndividualSession(
        individual_kp=kp,
        model=TinyRNN(n_actions=3, hidden=4,
                       n_extra_inputs=0, seed=600))
    fed = ScriptedWorld(
        kp=_kp(), initial_point_b=(800, 800),
        k_b=50, prng_seed_b=0x4444, rule=SIERPINSKI)
    session.enter_world_via_adapter(FederatedAdapter(), {
        "world_id": fed.world_id, "world": fed,
        "world_signer": fed.world_id,
        "initial_point": (200, 800)})
    for _ in range(3):
        session.step_via_adapter()
    parent = pack_unified_bundle(
        session, persona="p", name="p", initial_seed=600)

    canvas = GrowingWorld("world:canvas", "Canvas", _kp())
    resumed_session, _ = resume_unified_from_bundle(
        parent, kp, GrowingCanvasAdapter(), {
            "world_id": "world:canvas",
            "world": canvas,
            "world_signer": canvas.curator_public_key,
            "display_name": "t"})
    for _ in range(2):
        resumed_session.step_via_adapter()
    resumed = pack_unified_bundle(
        resumed_session, persona="r", name="r",
        initial_seed=600,
        resumed_from=parent.manifest["memory_root"])

    world_logs = {
        fed.world_id: [
            {"body": r.body(), "sig": r.sig,
             "record_hash": r.record_hash()}
            for r in fed.records],
        "world:canvas": [
            {"event_hash": e.event_hash(),
             "event_dict": e.to_dict()}
            for e in canvas.events()],
    }
    v = verify_resumed_unified_full(
        resumed, parent, world_logs)
    assert v[0], v[1]


def test_resumed_unified_full_tampered_suffix():
    kp = _kp()
    session = UnifiedIndividualSession(
        individual_kp=kp,
        model=TinyRNN(n_actions=3, hidden=4,
                       n_extra_inputs=0, seed=700))
    fed = ScriptedWorld(
        kp=_kp(), initial_point_b=(800, 800),
        k_b=50, prng_seed_b=0x5555, rule=SIERPINSKI)
    session.enter_world_via_adapter(FederatedAdapter(), {
        "world_id": fed.world_id, "world": fed,
        "world_signer": fed.world_id,
        "initial_point": (200, 800)})
    for _ in range(2):
        session.step_via_adapter()
    parent = pack_unified_bundle(
        session, persona="p", name="p", initial_seed=700)
    canvas = GrowingWorld("world:canvas", "Canvas", _kp())
    resumed_session, _ = resume_unified_from_bundle(
        parent, kp, GrowingCanvasAdapter(), {
            "world_id": "world:canvas",
            "world": canvas,
            "world_signer": canvas.curator_public_key,
            "display_name": "t"})
    for _ in range(2):
        resumed_session.step_via_adapter()
    resumed = pack_unified_bundle(
        resumed_session, persona="r", name="r",
        initial_seed=700,
        resumed_from=parent.manifest["memory_root"])
    # Tamper a canvas step
    for i, r in enumerate(resumed.memory):
        if r.get("tier") == "canvas":
            resumed.memory[i] = {**r, "x": 999, "y": 999}
            break
    world_logs = {
        fed.world_id: [
            {"body": r.body(), "sig": r.sig,
             "record_hash": r.record_hash()}
            for r in fed.records],
        "world:canvas": [
            {"event_hash": e.event_hash(),
             "event_dict": e.to_dict()}
            for e in canvas.events()],
    }
    v = verify_resumed_unified_full(
        resumed, parent, world_logs)
    assert not v[0]


# -- Lifetime composition --

def test_lifetime_with_resumed_unified():
    kp = _kp()
    session = UnifiedIndividualSession(
        individual_kp=kp,
        model=TinyRNN(n_actions=3, hidden=4,
                       n_extra_inputs=0, seed=800))
    fed = ScriptedWorld(
        kp=_kp(), initial_point_b=(800, 800),
        k_b=50, prng_seed_b=0x6666, rule=SIERPINSKI)
    session.enter_world_via_adapter(FederatedAdapter(), {
        "world_id": fed.world_id, "world": fed,
        "world_signer": fed.world_id,
        "initial_point": (200, 800)})
    for _ in range(3):
        session.step_via_adapter()
    parent = pack_unified_bundle(
        session, persona="p", name="p", initial_seed=800)

    canvas = GrowingWorld("world:canvas", "Canvas", _kp())
    resumed_session, _ = resume_unified_from_bundle(
        parent, kp, GrowingCanvasAdapter(), {
            "world_id": "world:canvas",
            "world": canvas,
            "world_signer": canvas.curator_public_key,
            "display_name": "t"})
    for _ in range(2):
        resumed_session.step_via_adapter()
    resumed = pack_unified_bundle(
        resumed_session, persona="r", name="r",
        initial_seed=800,
        resumed_from=parent.manifest["memory_root"])

    world_logs = {
        fed.world_id: [
            {"body": r.body(), "sig": r.sig,
             "record_hash": r.record_hash()}
            for r in fed.records],
        "world:canvas": [
            {"event_hash": e.event_hash(),
             "event_dict": e.to_dict()}
            for e in canvas.events()],
    }
    bundles = {
        parent.individual_id: parent,
        resumed.individual_id: resumed,
    }
    report = verify_individual_lifetime(
        bundles, parent.individual_id,
        world_logs=world_logs)
    assert report.ok, report.errors
    # Two bundles, one resume edge
    assert len(report.bundles) == 2
    assert len(report.edges) == 1
    assert report.edges[0]["ok"]


# -- Save/load --

def test_save_load_resumed(tmp_path):
    kp = _kp()
    session = UnifiedIndividualSession(
        individual_kp=kp,
        model=TinyRNN(n_actions=3, hidden=4,
                       n_extra_inputs=0, seed=900))
    fed = ScriptedWorld(
        kp=_kp(), initial_point_b=(800, 800),
        k_b=50, prng_seed_b=0x7777, rule=SIERPINSKI)
    session.enter_world_via_adapter(FederatedAdapter(), {
        "world_id": fed.world_id, "world": fed,
        "world_signer": fed.world_id,
        "initial_point": (200, 800)})
    for _ in range(2):
        session.step_via_adapter()
    parent = pack_unified_bundle(
        session, persona="p", name="p", initial_seed=900)
    canvas = GrowingWorld("world:canvas", "Canvas", _kp())
    resumed_session, _ = resume_unified_from_bundle(
        parent, kp, GrowingCanvasAdapter(), {
            "world_id": "world:canvas",
            "world": canvas,
            "world_signer": canvas.curator_public_key,
            "display_name": "t"})
    resumed_session.step_via_adapter()
    resumed = pack_unified_bundle(
        resumed_session, persona="r", name="r",
        initial_seed=900,
        resumed_from=parent.manifest["memory_root"])
    parent.save(tmp_path / "p")
    resumed.save(tmp_path / "r")
    p_loaded = IndividualBundle.load(tmp_path / "p")
    r_loaded = IndividualBundle.load(tmp_path / "r")
    v = verify_resumed_from(r_loaded, p_loaded)
    assert v[0], v[1]

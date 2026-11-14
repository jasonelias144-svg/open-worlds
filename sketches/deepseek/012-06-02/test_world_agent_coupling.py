import pytest
from world_agent_coupling import (
    ScriptedWorld, WorldAgentSession,
    WorldSeedRecord, WorldStepRecord, WorldKBChangeRecord,
    verify_agent_log, verify_world_log, verify_session,
    action_histogram, bhattacharyya, centroid,
    overlap_fraction, coupling_weights,
    render_overlay, demo, HAS_CRYPTO,
)
from coupled_learners import TinyRNN, TabularQ, SIERPINSKI
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey)

pytestmark = pytest.mark.skipif(
    not HAS_CRYPTO, reason="cryptography not installed")


def _kp():
    return Ed25519PrivateKey.generate()


def _world(k_b=100):
    return ScriptedWorld(
        kp=_kp(),
        initial_point_b=(800, 800),
        k_b=k_b, prng_seed_b=0xCAFE,
        rule=SIERPINSKI)


def _session(k_b=100, observe=True, seed=1):
    world = _world(k_b)
    model = TinyRNN(
        n_extra_inputs=3 if observe else 0,
        seed=seed)
    return WorldAgentSession(
        agent_kp=_kp(), agent_model=model,
        agent_observe=observe, world=world,
        agent_initial_point=(200, 800),
        rule=SIERPINSKI, seed_a=seed + 10)


def test_coupling_weights_k0():
    assert coupling_weights((1, 1, 1), [0, 0], 0) == (1, 1, 1)


def test_coupling_weights_k100_penalizes():
    w = coupling_weights((100, 100, 100),
                          [0, 0, 0], 100)
    assert w[0] < w[1] and w[0] < w[2]


def test_world_seed_signed():
    w = _world()
    assert w.seed_record.sig
    assert w.seed_record.world_id == w.world_id


def test_world_step_records():
    w = _world()
    pick, point = w.step()
    assert len(w.records) == 1
    assert isinstance(w.records[0], WorldStepRecord)


def test_k_change_record():
    w = _world(k_b=0)
    rec = w.change_k(100)
    assert isinstance(rec, WorldKBChangeRecord)
    assert w.k_b == 100


def test_session_steps():
    s = _session()
    for _ in range(20):
        s.step()
    assert len(s.a_records) == 20


def test_verify_agent_log():
    s = _session()
    for _ in range(50):
        s.step()
    ok, reason = verify_agent_log(s)
    assert ok, reason


def test_verify_world_log():
    s = _session()
    for _ in range(50):
        s.step()
    ok, reason = verify_world_log(s)
    assert ok, reason


def test_verify_full_session():
    s = _session()
    for _ in range(50):
        s.step()
    ok, reason = verify_session(s)
    assert ok, reason


def test_verify_full_with_k_change():
    s = _session(k_b=0)
    for _ in range(30):
        s.step()
    s.world.change_k(100)
    for _ in range(30):
        s.step()
    ok, reason = verify_session(s)
    assert ok, reason


def test_tampered_agent_action_fails():
    s = _session()
    for _ in range(20):
        s.step()
    s.a_records[5]["action"] = 99
    ok, _ = verify_agent_log(s)
    assert not ok


def test_tampered_world_pick_fails():
    s = _session()
    for _ in range(20):
        s.step()
    # Tamper: change a world pick
    for i, r in enumerate(s.world.records):
        if isinstance(r, WorldStepRecord):
            body = {**r.body(), "pick_b": (r.pick_b + 1) % 3}
            # Re-sign with world key (the tamper is in the world's claim)
            sig = s.world.kp.sign(
                __import__("world_agent_coupling")._canonical(
                    body)).hex()
            s.world.records[i] = WorldStepRecord(
                world_id=r.world_id, step=r.step,
                k_b=r.k_b, pick_b=body["pick_b"],
                point_b=r.point_b,
                a_recent_freq=r.a_recent_freq,
                prev=r.prev, ts=r.ts, sig=sig)
            break
    ok, reason = verify_world_log(s)
    assert not ok


def test_tampered_reward_fails():
    s = _session()
    for _ in range(20):
        s.step()
    s.a_records[5]["reward_micros"] = 999_999
    ok, _ = verify_agent_log(s)
    assert not ok


def test_observe_vs_blind_differ():
    """Observe and blind agents with same seed act differently
    because the model input dimensions differ."""
    s_obs = _session(observe=True, seed=1)
    s_blind = _session(observe=False, seed=1)
    for _ in range(100):
        s_obs.step()
        s_blind.step()
    a_obs = [r["action"] for r in s_obs.a_records]
    a_blind = [r["action"] for r in s_blind.a_records]
    assert a_obs != a_blind


def test_deterministic_seed():
    """Same seed → same session behavior."""
    s1 = _session(seed=1)
    s2 = _session(seed=1)
    for _ in range(50):
        s1.step()
        s2.step()
    assert [r["action"] for r in s1.a_records] == \
            [r["action"] for r in s2.a_records]


def test_render_overlay():
    a = [(0, 0), (10, 10)]
    b = [(5, 5), (10, 10)]
    text = render_overlay(a, b, width=20, height=10)
    assert "#" in text  # both points
    assert "A" in text or "B" in text


def test_overlap_fraction():
    a = [(0, 0), (1000, 1000)]
    b = [(0, 0), (500, 500)]
    f = overlap_fraction(a, b)
    assert f == 0.5


def test_demo(tmp_path):
    audit = demo(artifact_dir=str(tmp_path))
    for key in ("observe_vs_k_b=100",
                 "blind_vs_k_b=100",
                 "observe_vs_k_b=0→100"):
        assert key in audit, key
        assert audit[key]["verify"] is True, key
    assert "adaptation" in audit
    assert (tmp_path / "world_agent_coupling" /
            "world_agent_coupling_demo.json").exists()

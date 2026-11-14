import pytest
from choice_fractal import (
    TinyRNN, TabularQ, LearningAgent, make_agent,
    Transform, SIERPINSKI, verify_agent_log,
    render_points, action_histogram, demo,
    HAS_CRYPTO, _did_from_kp,
)
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey)

pytestmark = pytest.mark.skipif(
    not HAS_CRYPTO, reason="cryptography not installed")


def test_transform_apply():
    x, y = SIERPINSKI[1].apply(0, 0)
    assert (x, y) == (500, 0)


def test_agent_identity():
    a = make_agent("a")
    assert a.agent_id.startswith("did:key:")
    assert len(a.agent_id) == len("did:key:") + 64


def test_agent_steps():
    a = make_agent("a", seed=1)
    for _ in range(100):
        a.step(SIERPINSKI)
    assert len(a.records) == 100
    assert a.point != a.initial_point


def test_agent_log_verifies():
    a = make_agent("a", seed=1)
    for _ in range(50):
        a.step(SIERPINSKI)
    ok, reason = verify_agent_log(a)
    assert ok, reason


def test_tampered_agent_log_fails():
    a = make_agent("a", seed=1)
    for _ in range(10):
        a.step(SIERPINSKI)
    a.records[3]["action"] = 99
    ok, _ = verify_agent_log(a)
    assert not ok


def test_rnn_learns_preference():
    """RNN agent's action distribution drifts from uniform."""
    a = make_agent("a", "rnn", seed=1)
    for _ in range(2000):
        a.step(SIERPINSKI)
    hist = action_histogram(a.records)
    # Not exactly uniform after learning
    assert max(hist) - min(hist) > 0.05


def test_q_learns():
    a = make_agent("a", "q", seed=1)
    for _ in range(2000):
        a.step(SIERPINSKI)
    hist = action_histogram(a.records)
    assert max(hist) - min(hist) > 0.05


def test_two_agents_differ():
    a = make_agent("a", seed=1)
    b = make_agent("b", seed=2)
    for _ in range(1000):
        a.step(SIERPINSKI)
        b.step(SIERPINSKI)
    assert a.point != b.point
    assert len(a.recent_points) > 0
    assert len(b.recent_points) > 0


def test_one_unit_rnn():
    a = make_agent("a", "rnn", seed=5)
    a.model = TinyRNN(hidden=1, seed=5)
    for _ in range(500):
        a.step(SIERPINSKI)
    assert len(a.records) == 500


def test_demo(tmp_path):
    audit = demo(artifact_dir=str(tmp_path))
    for name, data in audit.items():
        assert data["verify"] is True, name
        assert data["steps"] == 5000
    assert (tmp_path / "choice_fractal" /
            "choice_fractal_demo.json").exists()

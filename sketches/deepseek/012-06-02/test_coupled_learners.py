import pytest
from coupled_learners import (
    TinyRNN, TabularQ, SharedEnvironment,
    CoupledLearningAgent, make_agent, run_pair,
    SIERPINSKI, verify_agent_log,
    action_histogram, bhattacharyya, divergence_score,
    centroid, demo, HAS_CRYPTO,
)
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey)

pytestmark = pytest.mark.skipif(
    not HAS_CRYPTO, reason="cryptography not installed")


def test_rnn_extra_inputs():
    rnn = TinyRNN(n_extra_inputs=3, seed=0)
    assert rnn.in_dim == 3 + 1 + 2 + 3
    state = (0, 0.5, 0.2, 0.3, 0.33, 0.33, 0.34)
    a = rnn.act(state, rng=__import__("random").Random(1))
    assert 0 <= a < 3


def test_shared_env_novelty():
    env = SharedEnvironment()
    assert env.novelty((0, 0)) == 1.0
    env.contribute((0, 0))
    assert env.novelty((0, 0)) == 0.5
    assert env.novelty((1000, 1000)) == 1.0


def test_agent_coupling_via_reward():
    """If both agents stay in the same region, both get low reward."""
    a = make_agent("a", "q", seed=1, initial_point=(0, 0))
    b = make_agent("b", "q", seed=2, initial_point=(0, 0))
    env = SharedEnvironment()
    for _ in range(20):
        a.step(SIERPINSKI, env, other=b)
        b.step(SIERPINSKI, env, other=a)
    # Recent rewards should be low (crowded)
    a_recent = [r["reward_micros"] for r in a.records[-10:]]
    b_recent = [r["reward_micros"] for r in b.records[-10:]]
    # Both should be < 500_000 (i.e., < 0.5 reward) on average
    assert sum(a_recent) / len(a_recent) < 500_000
    assert sum(b_recent) / len(b_recent) < 500_000


def test_agent_log_verifies():
    a = make_agent("a", seed=1)
    b = make_agent("b", seed=2)
    run_pair(a, b, SIERPINSKI, 100)
    for agent in (a, b):
        ok, reason = verify_agent_log(agent)
        assert ok, reason


def test_tampered_log_rejected():
    a = make_agent("a", seed=1)
    b = make_agent("b", seed=2)
    run_pair(a, b, SIERPINSKI, 50)
    a.records[10]["action"] = 99
    ok, _ = verify_agent_log(a)
    assert not ok


def test_two_agents_learn_differently():
    """Two independent agents with different seeds learn
    different action biases."""
    a = make_agent("a", "rnn", seed=1, initial_point=(200, 800))
    b = make_agent("b", "rnn", seed=2, initial_point=(800, 800))
    run_pair(a, b, SIERPINSKI, 2000)
    d = divergence_score(a, b)
    # Nonzero divergence means they're not identical
    assert d > 0.01


def test_control_pair_also_diverges():
    """Control (no observation) also diverges, because reward
    coupling alone is a channel."""
    a = make_agent("a", "rnn", seed=5,
                    observe_other=False,
                    initial_point=(200, 800))
    b = make_agent("b", "rnn", seed=6,
                    observe_other=False,
                    initial_point=(800, 800))
    run_pair(a, b, SIERPINSKI, 2000)
    d = divergence_score(a, b)
    assert d > 0.01


def test_q_agents_diverge():
    a = make_agent("a", "q", seed=3, initial_point=(200, 800))
    b = make_agent("b", "q", seed=4, initial_point=(800, 800))
    run_pair(a, b, SIERPINSKI, 2000)
    d = divergence_score(a, b)
    assert d > 0.01


def test_centroid():
    pts = [(0, 0), (100, 200), (200, 400)]
    c = centroid(pts)
    assert c == (100.0, 200.0)


def test_bhattacharyya():
    assert bhattacharyya([1, 0, 0], [1, 0, 0]) == 0.0
    assert bhattacharyya([1, 0, 0], [0, 1, 0]) == 1.0
    mid = bhattacharyya([0.5, 0.5, 0], [0.5, 0, 0.5])
    assert 0 < mid < 1


def test_demo(tmp_path):
    audit = demo(artifact_dir=str(tmp_path))
    for key in ("rnn_rnn_observe", "q_q_reward",
                 "rnn_rnn_control"):
        assert key in audit
        assert 0 <= audit[key]["divergence"] <= 1
    assert (tmp_path / "coupled_learners" /
            "coupled_learners_demo.json").exists()

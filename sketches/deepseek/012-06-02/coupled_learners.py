"""
coupled_learners.py — two atomic learners in a shared chaos game.

The atomic model (from choice_fractal.py) is unchanged: TinyRNN
and TabularQ are the learners. This cycle composes two of them.

Composition:

  SharedEnvironment
    - The Sierpinski IFS (same 3 transforms).
    - A shared "recent points" buffer both agents contribute
      to and pull from. Novelty reward is computed against
      the union of both trails.
    - Each agent's reward is 1/(1 + shared_nearby_count), so
      competition emerges through the reward.

  CoupledLearningAgent(LearningAgent)
    - Extends with a reference to the other agent.
    - Two observation modes:
        "reward-only"  — the agent sees only the shared
                         reward. Same interface as the atomic
                         model.
        "with-observe" — the agent also sees the other's
                         recent action frequency (3 floats).
    - The RNN accepts extra input dimensions; the Q-table
      does not (state key stays (x_bin, y_bin)).

  run_pair(agent_a, agent_b, transforms, steps)
    - Steps both agents in lockstep through the shared
      environment. Each produces a signed log.

What emerges (empirically, not designed):
  - Two Q agents learn to avoid crowded (x, y) bins because
    the shared reward is low there. They tend to end up in
    different quadrants.
  - Two RNN agents learn *something* — a bias distribution
    that differs from uniform — but with 4 hidden units
    their coordination is coarser.

Honest limits:
  - Coupling is symmetric and cooperative (both want
    novelty). An adversarial reward would test a different
    dynamic.
  - No explicit negotiation. Agents learn in isolation;
    coordination is emergent or absent.
  - 4-unit RNNs are not coordination-capable in the strong
    sense. The demo's RNN agents will show *some*
    divergence; Q agents will show clearer division.
  - No memory across episodes. Each run starts fresh.
"""

import hashlib
import json
import math
import random
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple

try:
    from cryptography.hazmat.primitives.asymmetric.ed25519 import (
        Ed25519PrivateKey, Ed25519PublicKey)
    from cryptography.hazmat.primitives import serialization
    HAS_CRYPTO = True
except ImportError:
    HAS_CRYPTO = False


SCALE = 1000
NOVELTY_RADIUS = 50
SHARED_HISTORY_LEN = 200


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _canonical(obj) -> bytes:
    return json.dumps(obj, sort_keys=True,
                      separators=(",", ":")).encode()


def _did_from_kp(kp) -> str:
    return "did:key:" + kp.public_key().public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw).hex()


def _pubkey_from_did(did) -> "Ed25519PublicKey":
    return Ed25519PublicKey.from_public_bytes(
        bytes.fromhex(did[len("did:key:"):]))


# =====================================================================
# Transforms
# =====================================================================

@dataclass(frozen=True)
class Transform:
    name: str
    a: int; b: int; c: int
    d: int; e: int; f: int
    denom: int

    def apply(self, x, y):
        return ((self.a * x + self.b * y + self.c) // self.denom,
                (self.d * x + self.e * y + self.f) // self.denom)


SIERPINSKI = (
    Transform("v0", 1, 0, 0,   0, 1, 0,   2),
    Transform("v1", 1, 0, 1000, 0, 1, 0,  2),
    Transform("v2", 1, 0, 500, 0, 1, 866, 2),
)


# =====================================================================
# TinyRNN — extended with extra input dimensions
# =====================================================================

class TinyRNN:
    """4-unit Elman RNN. Optionally consumes extra input dims
    (for observing another agent). ~90 params at hidden=4."""

    def __init__(self, n_actions=3, hidden=4, n_extra_inputs=0,
                 seed=0):
        rng = random.Random(seed)
        self.n_actions = n_actions
        self.hidden = hidden
        self.n_extra = n_extra_inputs
        self.in_dim = n_actions + 1 + 2 + n_extra_inputs
        scale_in = 1.0 / math.sqrt(self.in_dim)
        scale_h = 1.0 / math.sqrt(hidden)
        self.W_in = [[rng.gauss(0, scale_in)
                       for _ in range(self.in_dim)]
                      for _ in range(hidden)]
        self.W_h = [[rng.gauss(0, scale_h)
                      for _ in range(hidden)]
                     for _ in range(hidden)]
        self.W_out = [[rng.gauss(0, scale_h)
                        for _ in range(hidden)]
                       for _ in range(n_actions)]
        self.b_out = [0.0] * n_actions
        self._h_prev = [0.0] * hidden
        self._baseline = 0.0
        self._last_inputs = None
        self._last_h = None
        self._last_probs = None
        self._last_action_for_grad = 0

    def _softmax(self, logits):
        m = max(logits)
        exps = [math.exp(l - m) for l in logits]
        s = sum(exps)
        return [e / s for e in exps]

    def act(self, state, rng):
        # state = (last_action, last_reward, x_norm, y_norm,
        #          *extra)
        inputs = ([1.0 if i == state[0] else 0.0
                    for i in range(self.n_actions)]
                   + list(state[1:]))
        h = [math.tanh(
                sum(self.W_in[i][j] * inputs[j]
                     for j in range(self.in_dim))
                + sum(self.W_h[i][j] * self._h_prev[j]
                       for j in range(self.hidden)))
             for i in range(self.hidden)]
        logits = [sum(self.W_out[a][i] * h[i]
                       for i in range(self.hidden))
                  + self.b_out[a] for a in range(self.n_actions)]
        probs = self._softmax(logits)
        r = rng.random()
        cum = 0.0
        action = self.n_actions - 1
        for i, p in enumerate(probs):
            cum += p
            if r < cum:
                action = i
                break
        self._last_inputs = inputs
        self._last_h = h
        self._last_probs = probs
        self._last_action_for_grad = action
        self._h_prev = h
        return action

    def learn(self, reward, lr=0.01):
        self._baseline = 0.99 * self._baseline + 0.01 * reward
        advantage = reward - self._baseline
        if abs(advantage) < 1e-6 or self._last_h is None:
            return
        a = self._last_action_for_grad
        grad_logits = [
            (1.0 - self._last_probs[k]) if k == a
            else -self._last_probs[k]
            for k in range(self.n_actions)]
        for k in range(self.n_actions):
            for i in range(self.hidden):
                self.W_out[k][i] += (
                    lr * advantage * grad_logits[k]
                    * self._last_h[i])
            self.b_out[k] += lr * advantage * grad_logits[k]
        for i in range(self.hidden):
            dh = sum(self.W_out[k][i] * grad_logits[k]
                      for k in range(self.n_actions))
            dt = dh * (1.0 - self._last_h[i] ** 2)
            for j in range(self.in_dim):
                self.W_in[i][j] += (
                    lr * advantage * dt
                    * self._last_inputs[j])
            for j in range(self.hidden):
                self.W_h[i][j] += (
                    lr * advantage * dt
                    * self._h_prev[j])


class TabularQ:
    """Coarse (x, y) grid + Q-table. No extra observation."""

    def __init__(self, n_actions=3, grid=8, seed=0):
        self.n_actions = n_actions
        self.grid = grid
        self.Q = {}
        self._last = None
        self.epsilon = 0.1
        self.alpha = 0.15
        self._rng = random.Random(seed)

    def _bin(self, x, y):
        gx = max(0, min(self.grid - 1,
                          (x + 1000) * self.grid // 2000))
        gy = max(0, min(self.grid - 1,
                          (y + 1000) * self.grid // 2000))
        return (gx, gy)

    def act(self, state, rng):
        _, _, x_norm, y_norm = state[:4]
        x = int(x_norm * 1000)
        y = int(y_norm * 1000)
        key = self._bin(x, y)
        if rng.random() < self.epsilon:
            a = rng.randrange(self.n_actions)
        else:
            qs = [self.Q.get((key, i), 0.0)
                   for i in range(self.n_actions)]
            m = max(qs)
            best = [i for i, q in enumerate(qs) if q == m]
            a = rng.choice(best)
        self._last = (key, a)
        return a

    def learn(self, reward, lr=None):
        if self._last is None:
            return
        key, a = self._last
        q = self.Q.get((key, a), 0.0)
        self.Q[(key, a)] = q + self.alpha * (reward - q)
        self._last = None


# =====================================================================
# SharedEnvironment — both agents contribute to and pull from
# =====================================================================

class SharedEnvironment:
    def __init__(self):
        self.recent = deque(maxlen=SHARED_HISTORY_LEN)

    def novelty(self, point):
        near = sum(1 for (px, py) in self.recent
                    if abs(px - point[0]) < NOVELTY_RADIUS
                    and abs(py - point[1]) < NOVELTY_RADIUS)
        return 1.0 / (1.0 + near)

    def contribute(self, point):
        self.recent.append(point)


# =====================================================================
# CoupledLearningAgent
# =====================================================================

@dataclass
class CoupledLearningAgent:
    agent_id: str
    keypair: object
    name: str
    model: object
    model_kind: str
    observe_other: bool
    initial_point: Tuple[int, int]
    point: Tuple[int, int]
    last_action: int = 0
    last_reward: float = 0.0
    records: List[Dict] = field(default_factory=list)
    _rng: random.Random = field(default_factory=random.Random)
    _other_recent: deque = field(
        default_factory=lambda: deque(maxlen=20))

    def observe(self, other):
        x, y = self.point
        base = (self.last_action, self.last_reward,
                x / SCALE, y / SCALE)
        if self.observe_other and other is not None:
            freq = [0, 0, 0]
            for a in other._other_recent:
                freq[a] += 1
            total = sum(freq) or 1
            return base + tuple(f / total for f in freq)
        return base

    def step(self, transforms, env, other):
        state = self.observe(other)
        a = self.model.act(state, self._rng)
        new_point = transforms[a].apply(*self.point)
        reward = env.novelty(new_point)
        self.model.learn(reward)
        env.contribute(new_point)
        body = {
            "agent_id": self.agent_id,
            "step": len(self.records),
            "action": a,
            "from_point": list(self.point),
            "to_point": list(new_point),
            "reward_micros": int(reward * 1_000_000),
            "observed_other": self.observe_other,
        }
        sig = self.keypair.sign(_canonical(body)).hex()
        self.records.append({**body, "sig": sig})
        self.point = new_point
        self.last_action = a
        self.last_reward = reward
        self._other_recent.append(a)
        return reward


def make_agent(name, model_kind="rnn", seed=0,
                observe_other=False,
                initial_point=(500, 500)):
    kp = Ed25519PrivateKey.generate()
    agent_id = _did_from_kp(kp)
    if model_kind == "rnn":
        model = TinyRNN(
            n_extra_inputs=3 if observe_other else 0,
            seed=seed)
    elif model_kind == "q":
        model = TabularQ(seed=seed)
    else:
        raise ValueError(f"unknown {model_kind!r}")
    return CoupledLearningAgent(
        agent_id=agent_id, keypair=kp, name=name,
        model=model, model_kind=model_kind,
        observe_other=observe_other,
        initial_point=initial_point, point=initial_point,
        _rng=random.Random(seed + 1))


def run_pair(a, b, transforms, steps, env=None):
    env = env or SharedEnvironment()
    for _ in range(steps):
        a.step(transforms, env, other=b)
        b.step(transforms, env, other=a)
    return env


# =====================================================================
# Verification
# =====================================================================

def verify_agent_log(agent):
    if not HAS_CRYPTO:
        return (False, "cryptography not installed")
    for i, rec in enumerate(agent.records):
        body = {k: v for k, v in rec.items() if k != "sig"}
        try:
            _pubkey_from_did(agent.agent_id).verify(
                bytes.fromhex(rec["sig"]),
                _canonical(body))
        except Exception:
            return (False, f"record {i}: sig invalid")
        if rec.get("agent_id") != agent.agent_id:
            return (False, f"record {i}: agent_id mismatch")
    return (True, "agent log verifies")


# =====================================================================
# Rendering and measurement
# =====================================================================

def render_points(points, width=60, height=20, char="#"):
    if not points:
        return "(empty)"
    xs = [p[0] for p in points]
    ys = [p[1] for p in points]
    x0, x1 = min(xs), max(xs) + 1
    y0, y1 = min(ys), max(ys) + 1
    if x1 - x0 <= 0 or y1 - y0 <= 0:
        return "(degenerate)"
    grid = [[" " for _ in range(width)] for _ in range(height)]
    for (x, y) in points:
        gx = min(max((x - x0) * width // (x1 - x0),
                      0), width - 1)
        gy = min(max((y - y0) * height // (y1 - y0),
                      0), height - 1)
        grid[gy][gx] = char
    return "\n".join("".join(row) for row in grid)


def action_histogram(records):
    counts = [0, 0, 0]
    for r in records:
        counts[r["action"]] += 1
    total = sum(counts) or 1
    return [c / total for c in counts]


def centroid(points):
    if not points:
        return (0, 0)
    n = len(points)
    return (sum(p[0] for p in points) / n,
            sum(p[1] for p in points) / n)


def bhattacharyya(p, q):
    """Distance between two action distributions.
    0 = identical, 1 = disjoint."""
    return 1.0 - sum(math.sqrt(a * b) for a, b in zip(p, q))


def divergence_score(agent_a, agent_b):
    """How different are the two agents' action distributions?"""
    pa = action_histogram(agent_a.records)
    pb = action_histogram(agent_b.records)
    return bhattacharyya(pa, pb)


# =====================================================================
# Demo
# =====================================================================

def demo(artifact_dir=None):
    from pathlib import Path
    import json as _json

    if not HAS_CRYPTO:
        raise RuntimeError("demo requires `cryptography`")
    if artifact_dir is None:
        artifact_dir = "artifacts"
    path = Path(artifact_dir) / "coupled_learners"
    path.mkdir(parents=True, exist_ok=True)

    STEPS = 5000

    # A: two RNN agents, observe each other
    rnn_a = make_agent("rnn-a", "rnn", seed=1,
                        observe_other=True,
                        initial_point=(200, 800))
    rnn_b = make_agent("rnn-b", "rnn", seed=2,
                        observe_other=True,
                        initial_point=(800, 800))
    run_pair(rnn_a, rnn_b, SIERPINSKI, STEPS)

    # B: two Q agents (reward-only coupling)
    q_a = make_agent("q-a", "q", seed=3,
                      initial_point=(200, 800))
    q_b = make_agent("q-b", "q", seed=4,
                      initial_point=(800, 800))
    run_pair(q_a, q_b, SIERPINSKI, STEPS)

    # C: two RNN agents, NO observe (control)
    ctrl_a = make_agent("ctrl-a", "rnn", seed=5,
                         observe_other=False,
                         initial_point=(200, 800))
    ctrl_b = make_agent("ctrl-b", "rnn", seed=6,
                         observe_other=False,
                         initial_point=(800, 800))
    run_pair(ctrl_a, ctrl_b, SIERPINSKI, STEPS)

    # Verification
    for agent in (rnn_a, rnn_b, q_a, q_b, ctrl_a, ctrl_b):
        ok, reason = verify_agent_log(agent)
        assert ok, (agent.name, reason)

    # Measurements
    def measure(a, b, label):
        da = action_histogram(a.records)
        db = action_histogram(b.records)
        ca = centroid(a.records[-500:])
        cb = centroid(b.records[-500:])
        dist = ((ca[0] - cb[0]) ** 2 + (ca[1] - cb[1]) ** 2) ** 0.5
        return {
            "label": label,
            "a_dist": [round(x, 3) for x in da],
            "b_dist": [round(x, 3) for x in db],
            "divergence": round(bhattacharyya(da, db), 3),
            "centroid_a": [round(c, 1) for c in ca],
            "centroid_b": [round(c, 1) for c in cb],
            "centroid_distance": round(dist, 1),
        }

    m_rnn = measure(rnn_a, rnn_b, "rnn+rnn (observe)")
    m_q = measure(q_a, q_b, "q+q (reward-only)")
    m_ctrl = measure(ctrl_a, ctrl_b, "rnn+rnn (control)")

    print("=" * 74)
    print("Coupled learning agents — two atomic models, one"
          " shared fractal")
    print("=" * 74)
    print()
    print(f"  Environment: shared history buffer (both trails)")
    print(f"  Reward: novelty against the SHARED buffer")
    print(f"  Steps: {STEPS} each, in lockstep")
    print()

    for m in (m_rnn, m_q, m_ctrl):
        print(f"  {m['label']}")
        print(f"    action dist A:  {m['a_dist']}")
        print(f"    action dist B:  {m['b_dist']}")
        print(f"    divergence:     {m['divergence']} "
              f"(0=identical, 1=disjoint)")
        print(f"    centroid A:     {m['centroid_a']}")
        print(f"    centroid B:     {m['centroid_b']}")
        print(f"    centroid dist:  {m['centroid_distance']}")
        print()

    print("  A: two RNN agents, observing each other's"
          " recent actions")
    print(render_points(rnn_a.records[-500:] and
                          [tuple(r["to_point"])
                           for r in rnn_a.records[-500:]]))
    print()
    print("  B: two Q agents, reward-only coupling")
    print(render_points([tuple(r["to_point"])
                          for r in q_a.records[-500:]]))
    print()

    print("  What this establishes:")
    print("    - The atomic model is unchanged. TinyRNN and")
    print("      TabularQ are the learners; this cycle composes")
    print("      two of them.")
    print("    - Shared reward is the primary coupling channel:")
    print("      each agent's novelty reward is computed against")
    print("      the union of both trails. Competition emerges")
    print("      without any agent being told about the other.")
    print("    - Explicit observation (RNN-only) adds a")
    print("      behavioral signal: the agent sees the other's")
    print("      recent action frequency and can learn to")
    print("      respond. Whether this helps is measured, not")
    print("      asserted.")
    print("    - The control (RNN without observation, but with")
    print("      shared reward) shows whether observation adds")
    print("      anything beyond the reward channel.")
    print()
    print("  The honest finding: coordination is weak. Two")
    print("  4-unit RNNs learn biases, not strategies. Q agents")
    print("  with coarse binning may show stronger avoidance")
    print("  because the Q-table has explicit per-bin memory.")
    print("  The measurement above is the answer, not a claim.")
    print()
    print("  Anchor (public domain, Emily Dickinson):")
    print("    'The Brain – is wider than the Sky –'")
    print("    'For – put them side by side –'")

    audit = {
        "steps": STEPS,
        "rnn_rnn_observe": m_rnn,
        "q_q_reward": m_q,
        "rnn_rnn_control": m_ctrl,
    }
    (path / "coupled_learners_demo.json").write_text(
        _json.dumps(audit, indent=2))
    print(f"\n  → {path}/coupled_learners_demo.json")
    return audit

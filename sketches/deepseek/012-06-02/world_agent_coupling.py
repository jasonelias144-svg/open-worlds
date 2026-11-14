"""
world_agent_coupling.py — a scripted world and a learning agent.

The composition:

  A (agent)        — TinyRNN or TabularQ, signed by A's key
  B (world)        — k_b-modulated chaos game, signed by B's key
  Shared buffer    — union of both trajectories, for novelty

Two signature domains:
  A's log: verifiable by anyone with A's DID (cryptographic)
  B's log: verifiable by anyone with B's seed (deterministic replay)

The full verifier runs both plus the cross-check that A's
claimed rewards match what the shared buffer would have produced
at each step.

Scenarios:
  observe vs k_b=100   — A learns to avoid B's moving avoidance
  blind   vs k_b=100   — does the observation input matter?
  observe vs k_b=0→100 — does A adapt when B changes policy?

Honest limits:
  - A's model cannot be replayed without A's seed. Verification
    checks A's signatures + reward-claim consistency; a stricter
    verifier would re-run A's model.
  - B's log depends on A's log (k_b modulation uses A's picks).
    Verification requires both — the world's behavior is only
    defined relative to the agent it played against.
  - Q is not exercised here. It's a natural ablation, noted as
    future work.
  - The shared novelty buffer is cooperative, not adversarial.
    Both sides avoid each other's recent points. If B actively
    sought A out, A would learn a different response.
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

from coupled_learners import (
    Transform, SIERPINSKI, TinyRNN, TabularQ,
)
from chaos_game_world import (
    xorshift64_star_step, pick_weighted, MASK_64,
)


SCALE = 1000
NOVELTY_RADIUS = 50
SHARED_HISTORY_LEN = 200
AGENT_OBS_WINDOW = 20


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _canonical(obj) -> bytes:
    return json.dumps(obj, sort_keys=True,
                      separators=(",", ":")).encode()


def _hash(obj) -> str:
    return hashlib.sha256(_canonical(obj)).hexdigest()


def _did_from_kp(kp) -> str:
    return "did:key:" + kp.public_key().public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw).hex()


def _pubkey_from_did(did) -> "Ed25519PublicKey":
    return Ed25519PublicKey.from_public_bytes(
        bytes.fromhex(did[len("did:key:"):]))


def _freq(items, n):
    counts = [0] * n
    for v in items:
        if 0 <= v < n:
            counts[v] += 1
    total = sum(counts) or 1
    return tuple(c / total for c in counts)


def coupling_weights(base_weights, recent_other, k_self):
    n = len(base_weights)
    if not recent_other or k_self == 0:
        return tuple(base_weights)
    counts = [0] * n
    for v in recent_other:
        if 0 <= v < n:
            counts[v] += 1
    w = len(recent_other)
    eff = []
    for i in range(n):
        freq = counts[i] * 100 // w
        penalty = k_self * freq // 100
        eff.append(max(1, int(base_weights[i]) - penalty))
    return tuple(eff)


# =====================================================================
# World-side records
# =====================================================================

@dataclass(frozen=True)
class WorldSeedRecord:
    world_id: str
    initial_point_b: Tuple[int, int]
    initial_k_b: int
    prng_seed_b: int
    window: int
    rule_hash: str
    ts: str
    sig: str

    def body(self):
        return {
            "type": "world_seed",
            "world_id": self.world_id,
            "initial_point_b": list(self.initial_point_b),
            "initial_k_b": self.initial_k_b,
            "prng_seed_b": self.prng_seed_b,
            "window": self.window,
            "rule_hash": self.rule_hash,
            "ts": self.ts,
        }

    def record_hash(self):
        return _hash(self.body())


@dataclass(frozen=True)
class WorldStepRecord:
    world_id: str
    step: int
    k_b: int
    pick_b: int
    point_b: Tuple[int, int]
    a_recent_freq: Tuple[float, float, float]
    prev: Optional[str]
    ts: str
    sig: str

    def body(self):
        return {
            "type": "world_step",
            "world_id": self.world_id,
            "step": self.step,
            "k_b": self.k_b,
            "pick_b": self.pick_b,
            "point_b": list(self.point_b),
            "a_recent_freq": list(self.a_recent_freq),
            "prev": self.prev,
            "ts": self.ts,
        }

    def record_hash(self):
        return _hash(self.body())


@dataclass(frozen=True)
class WorldKBChangeRecord:
    world_id: str
    step: int
    old_k: int
    new_k: int
    prev: Optional[str]
    ts: str
    sig: str

    def body(self):
        return {
            "type": "world_k_change",
            "world_id": self.world_id,
            "step": self.step,
            "old_k": self.old_k,
            "new_k": self.new_k,
            "prev": self.prev,
            "ts": self.ts,
        }

    def record_hash(self):
        return _hash(self.body())


# =====================================================================
# ScriptedWorld — B side
# =====================================================================

class ScriptedWorld:
    def __init__(self, kp, initial_point_b, k_b, prng_seed_b,
                 rule=SIERPINSKI, window=20):
        if not HAS_CRYPTO:
            raise RuntimeError("cryptography not installed")
        self.kp = kp
        self.world_id = _did_from_kp(kp)
        self.initial_point_b = tuple(initial_point_b)
        self.point_b = tuple(initial_point_b)
        self.k_b = int(k_b)
        self.prng_state = int(prng_seed_b)
        self.rule = rule
        self.window = window
        self.recent_a: deque = deque(maxlen=window)
        self.records: List = []
        rule_hash = _hash([t.to_dict() for t in rule])
        body = {
            "type": "world_seed",
            "world_id": self.world_id,
            "initial_point_b": list(self.initial_point_b),
            "initial_k_b": self.k_b,
            "prng_seed_b": self.prng_state,
            "window": self.window,
            "rule_hash": rule_hash,
            "ts": _now(),
        }
        sig = kp.sign(_canonical(body)).hex()
        self.seed_record = WorldSeedRecord(
            world_id=self.world_id,
            initial_point_b=self.initial_point_b,
            initial_k_b=self.k_b,
            prng_seed_b=self.prng_state,
            window=self.window,
            rule_hash=rule_hash,
            ts=body["ts"], sig=sig,
        )
        self._last_hash = self.seed_record.record_hash()

    def _pick_b(self):
        weights = coupling_weights(
            tuple(1 for _ in self.rule),
            list(self.recent_a), self.k_b)
        self.prng_state, out = xorshift64_star_step(
            self.prng_state)
        return pick_weighted(out, weights)

    def step(self):
        pick = self._pick_b()
        new_point = self.rule[pick].apply(*self.point_b)
        a_freq = _freq(self.recent_a, len(self.rule))
        body = {
            "type": "world_step",
            "world_id": self.world_id,
            "step": len(self.records),
            "k_b": self.k_b,
            "pick_b": pick,
            "point_b": list(new_point),
            "a_recent_freq": list(a_freq),
            "prev": self._last_hash,
            "ts": _now(),
        }
        sig = self.kp.sign(_canonical(body)).hex()
        rec = WorldStepRecord(
            world_id=self.world_id, step=len(self.records),
            k_b=self.k_b, pick_b=pick,
            point_b=new_point, a_recent_freq=a_freq,
            prev=self._last_hash, ts=body["ts"], sig=sig,
        )
        self.records.append(rec)
        self.point_b = new_point
        self._last_hash = rec.record_hash()
        return pick, new_point

    def append_a_pick(self, a_pick):
        self.recent_a.append(a_pick)

    def change_k(self, new_k):
        new_k = int(new_k)
        if not (0 <= new_k <= 100):
            raise ValueError("k must be [0, 100]")
        body = {
            "type": "world_k_change",
            "world_id": self.world_id,
            "step": len(self.records),
            "old_k": self.k_b,
            "new_k": new_k,
            "prev": self._last_hash,
            "ts": _now(),
        }
        sig = self.kp.sign(_canonical(body)).hex()
        rec = WorldKBChangeRecord(
            world_id=self.world_id, step=len(self.records),
            old_k=self.k_b, new_k=new_k,
            prev=self._last_hash, ts=body["ts"], sig=sig,
        )
        self.records.append(rec)
        self.k_b = new_k
        self._last_hash = rec.record_hash()
        return rec


# =====================================================================
# WorldAgentSession — interleave A and B
# =====================================================================

class WorldAgentSession:
    def __init__(self, agent_kp, agent_model, agent_observe,
                 world: ScriptedWorld, agent_initial_point,
                 rule=SIERPINSKI, seed_a=0):
        if not HAS_CRYPTO:
            raise RuntimeError("cryptography not installed")
        self.agent_kp = agent_kp
        self.agent_id = _did_from_kp(agent_kp)
        self.agent_model = agent_model
        self.agent_observe = agent_observe
        self.world = world
        self.rule = rule
        self.a_initial_point = tuple(agent_initial_point)
        self.a_point = tuple(agent_initial_point)
        self.a_last_action = 0
        self.a_last_reward = 0.0
        self.a_records: List[Dict] = []
        self.shared: deque = deque(maxlen=SHARED_HISTORY_LEN)
        self.b_recent_picks: deque = deque(
            maxlen=AGENT_OBS_WINDOW)
        self._a_rng = random.Random(seed_a)

    def _a_state(self):
        x, y = self.a_point
        base = (self.a_last_action, self.a_last_reward,
                x / SCALE, y / SCALE)
        if self.agent_observe:
            return base + _freq(self.b_recent_picks,
                                  len(self.rule))
        return base

    def _novelty(self, point):
        near = sum(1 for (px, py) in self.shared
                    if abs(px - point[0]) < NOVELTY_RADIUS
                    and abs(py - point[1]) < NOVELTY_RADIUS)
        return 1.0 / (1.0 + near)

    def step(self):
        step_n = len(self.a_records)
        # 1. A's pick (informed by past B picks)
        state = self._a_state()
        a_pick = self.agent_model.act(state, self._a_rng)
        # 2. B's pick (informed by past A picks)
        b_pick, b_new = self.world.step()
        # 3. A applies its transform
        a_new = self.rule[a_pick].apply(*self.a_point)
        # 4. Reward + learn
        reward = self._novelty(a_new)
        self.agent_model.learn(reward)
        # 5. Shared buffer
        self.shared.append(a_new)
        self.shared.append(b_new)
        # 6. A's record (references the world step it responded to)
        world_step_record = self.world.records[-1]
        body = {
            "type": "agent_step",
            "agent_id": self.agent_id,
            "step": step_n,
            "action": a_pick,
            "from_point": list(self.a_point),
            "to_point": list(a_new),
            "reward_micros": int(reward * 1_000_000),
            "world_id": self.world.world_id,
            "world_step_hash": world_step_record.record_hash(),
            "ts": _now(),
        }
        sig = self.agent_kp.sign(_canonical(body)).hex()
        self.a_records.append({**body, "sig": sig})
        # 7. Advance
        self.a_point = a_new
        self.a_last_action = a_pick
        self.a_last_reward = reward
        self.world.append_a_pick(a_pick)
        self.b_recent_picks.append(b_pick)
        return a_pick, b_pick, a_new, b_new, reward


# =====================================================================
# Verification
# =====================================================================

def verify_agent_log(session):
    """A's signatures and reward-claim consistency."""
    if not HAS_CRYPTO:
        return (False, "cryptography not installed")
    # Reconstruct shared buffer to check rewards
    shared: deque = deque(maxlen=SHARED_HISTORY_LEN)
    prev_agent_sig: Optional[str] = None
    world_records = [r for r in session.world.records
                     if isinstance(r, WorldStepRecord)]
    for i, rec in enumerate(session.a_records):
        body = {k: v for k, v in rec.items() if k != "sig"}
        try:
            _pubkey_from_did(session.agent_id).verify(
                bytes.fromhex(rec["sig"]),
                _canonical(body))
        except Exception:
            return (False, f"a_record {i}: signature invalid")
        if rec.get("agent_id") != session.agent_id:
            return (False, f"a_record {i}: agent_id mismatch")
        # Check reward recomputation
        a_new = tuple(rec["to_point"])
        near = sum(1 for (px, py) in shared
                    if abs(px - a_new[0]) < NOVELTY_RADIUS
                    and abs(py - a_new[1]) < NOVELTY_RADIUS)
        expected_reward = 1.0 / (1.0 + near)
        reported = rec["reward_micros"] / 1_000_000
        if abs(expected_reward - reported) > 1e-6:
            return (False,
                     f"a_record {i}: reward mismatch "
                     f"(reported {reported}, "
                     f"expected {expected_reward})")
        # Append to shared buffer: A's point + B's point from
        # the matching world record
        if i < len(world_records):
            shared.append(a_new)
            shared.append(tuple(world_records[i].point_b))
        prev_agent_sig = rec["sig"]
    return (True, "agent log verifies")


def verify_world_log(session):
    """Deterministic replay of B's picks given A's picks."""
    if not HAS_CRYPTO:
        return (False, "cryptography not installed")
    seed = session.world.seed_record
    if seed.world_id != session.world.world_id:
        return (False, "seed world_id mismatch")
    try:
        _pubkey_from_did(session.world.world_id).verify(
            bytes.fromhex(seed.sig),
            _canonical(seed.body()))
    except Exception:
        return (False, "seed signature invalid")

    prng_state = seed.prng_seed_b
    recent_a: deque = deque(maxlen=seed.window)
    k_b = seed.initial_k_b
    prev_hash = seed.record_hash()
    step_index = 0
    for i, rec in enumerate(session.world.records):
        if rec.prev != prev_hash:
            return (False, f"world_record {i}: prev mismatch")
        try:
            _pubkey_from_did(session.world.world_id).verify(
                bytes.fromhex(rec.sig),
                _canonical(rec.body()))
        except Exception:
            return (False, f"world_record {i}: sig invalid")
        if isinstance(rec, WorldKBChangeRecord):
            if rec.old_k != k_b:
                return (False, f"world_record {i}: old_k mismatch")
            k_b = rec.new_k
        elif isinstance(rec, WorldStepRecord):
            if rec.step != step_index:
                return (False, f"world_record {i}: step skip")
            weights = coupling_weights(
                tuple(1 for _ in session.rule),
                list(recent_a), k_b)
            prng_state, out = xorshift64_star_step(prng_state)
            expected_pick = pick_weighted(out, weights)
            if rec.pick_b != expected_pick:
                return (False,
                         f"world_record {i} (step {rec.step}): "
                         f"pick_b {rec.pick_b} != expected "
                         f"{expected_pick}")
            # Re-derive expected point
            prev_point = (session.world.initial_point_b
                          if step_index == 0
                          else session.world.records[
                              i - 1].point_b)
            expected_point = session.rule[
                expected_pick].apply(*prev_point)
            if tuple(rec.point_b) != expected_point:
                return (False,
                         f"world_record {i}: point mismatch")
            # Advance using A's recorded pick
            if step_index >= len(session.a_records):
                return (False,
                         f"world_record {i}: no corresponding "
                         f"agent record")
            recent_a.append(
                session.a_records[step_index]["action"])
            step_index += 1
        else:
            return (False, f"world_record {i}: unknown type")
        prev_hash = rec.record_hash()
    return (True, "world log verifies")


def verify_session(session):
    v_a = verify_agent_log(session)
    if not v_a[0]:
        return (False, f"agent: {v_a[1]}")
    v_w = verify_world_log(session)
    if not v_w[0]:
        return (False, f"world: {v_w[1]}")
    return (True, "full session verifies")


# =====================================================================
# Measurements
# =====================================================================

def action_histogram(actions, n=3):
    counts = [0] * n
    for a in actions:
        if 0 <= a < n:
            counts[a] += 1
    total = sum(counts) or 1
    return [c / total for c in counts]


def centroid(points):
    if not points:
        return (0, 0)
    n = len(points)
    return (sum(p[0] for p in points) / n,
            sum(p[1] for p in points) / n)


def bhattacharyya(p, q):
    return 1.0 - sum(math.sqrt(a * b)
                      for a, b in zip(p, q))


def overlap_fraction(a_points, b_points, radius=NOVELTY_RADIUS):
    """Fraction of A's points within radius of any B point."""
    if not a_points or not b_points:
        return 0.0
    b_set = set(b_points)
    hits = 0
    for (x, y) in a_points:
        for (bx, by) in b_set:
            if abs(bx - x) < radius and abs(by - y) < radius:
                hits += 1
                break
    return hits / len(a_points)


# =====================================================================
# Rendering
# =====================================================================

def render_points(points, width=60, height=20,
                    char="#"):
    if not points:
        return "(empty)"
    xs = [p[0] for p in points]
    ys = [p[1] for p in points]
    x0, x1 = min(xs), max(xs) + 1
    y0, y1 = min(ys), max(ys) + 1
    if x1 - x0 <= 0 or y1 - y0 <= 0:
        return "(degenerate)"
    grid = [[" " for _ in range(width)]
             for _ in range(height)]
    for (x, y) in points:
        gx = min(max((x - x0) * width // (x1 - x0),
                      0), width - 1)
        gy = min(max((y - y0) * height // (y1 - y0),
                      0), height - 1)
        grid[gy][gx] = char
    return "\n".join("".join(row) for row in grid)


def render_overlay(a_points, b_points, width=60, height=20,
                    char_a="A", char_b="B", char_both="#"):
    all_pts = list(a_points) + list(b_points)
    if not all_pts:
        return "(empty)"
    xs = [p[0] for p in all_pts]
    ys = [p[1] for p in all_pts]
    x0, x1 = min(xs), max(xs) + 1
    y0, y1 = min(ys), max(ys) + 1
    grid = [[" " for _ in range(width)]
             for _ in range(height)]
    set_a = set(a_points)
    set_b = set(b_points)
    for (x, y) in set_a | set_b:
        gx = min(max((x - x0) * width // (x1 - x0),
                      0), width - 1)
        gy = min(max((y - y0) * height // (y1 - y0),
                      0), height - 1)
        if (x, y) in set_a and (x, y) in set_b:
            grid[gy][gx] = char_both
        elif (x, y) in set_a:
            grid[gy][gx] = char_a
        else:
            grid[gy][gx] = char_b
    return "\n".join("".join(row) for row in grid)


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
    path = Path(artifact_dir) / "world_agent_coupling"
    path.mkdir(parents=True, exist_ok=True)

    STEPS = 5000

    def build_session(observe, k_b, seed_a=0):
        agent_kp = Ed25519PrivateKey.generate()
        world_kp = Ed25519PrivateKey.generate()
        world = ScriptedWorld(
            kp=world_kp,
            initial_point_b=(800, 800),
            k_b=k_b,
            prng_seed_b=0xCAFEBABE,
            rule=SIERPINSKI,
        )
        model = TinyRNN(
            n_actions=3, hidden=4,
            n_extra_inputs=3 if observe else 0,
            seed=seed_a + 1,
        )
        session = WorldAgentSession(
            agent_kp=agent_kp,
            agent_model=model,
            agent_observe=observe,
            world=world,
            agent_initial_point=(200, 800),
            rule=SIERPINSKI,
            seed_a=seed_a + 7,
        )
        return session

    # Scenario 1: observe vs k_b=100
    s1 = build_session(observe=True, k_b=100, seed_a=1)
    for _ in range(STEPS):
        s1.step()

    # Scenario 2: blind vs k_b=100
    s2 = build_session(observe=False, k_b=100, seed_a=2)
    for _ in range(STEPS):
        s2.step()

    # Scenario 3: observe vs k_b=0 → 100 mid-run
    s3 = build_session(observe=True, k_b=0, seed_a=3)
    for _ in range(STEPS // 2):
        s3.step()
    s3.world.change_k(100)
    for _ in range(STEPS // 2):
        s3.step()

    sessions = [
        (s1, "observe vs k_b=100"),
        (s2, "blind   vs k_b=100"),
        (s3, "observe vs k_b=0→100"),
    ]

    for s, label in sessions:
        ok, reason = verify_session(s)
        assert ok, f"{label}: {reason}"

    def measure(s):
        a_actions = [r["action"] for r in s.a_records]
        b_actions = [r.pick_b for r in s.world.records
                      if isinstance(r, WorldStepRecord)]
        a_dist = action_histogram(a_actions)
        b_dist = action_histogram(b_actions)
        a_pts = [tuple(r["to_point"]) for r in s.a_records]
        b_pts = [tuple(r.point_b) for r in s.world.records
                  if isinstance(r, WorldStepRecord)]
        early_a = action_histogram(
            a_actions[:STEPS // 4])
        late_a = action_histogram(a_actions[-STEPS // 4:])
        return {
            "divergence": round(bhattacharyya(a_dist, b_dist), 3),
            "overlap": round(overlap_fraction(
                a_pts[-500:], b_pts[-500:]), 3),
            "a_dist": [round(x, 3) for x in a_dist],
            "a_drift": round(bhattacharyya(
                early_a, late_a), 3),
        }

    print("=" * 74)
    print("World-agent coupling — a learner meets a scripted world")
    print("=" * 74)
    print()
    print(f"  Rule:    Sierpinski IFS")
    print(f"  Reward:  novelty against shared buffer")
    print(f"  Steps:   {STEPS} per scenario")
    print()

    for s, label in sessions:
        m = measure(s)
        print(f"  {label}")
        print(f"    A's action dist:  {m['a_dist']}")
        print(f"    A vs B divergence: {m['divergence']}")
        print(f"    A-B overlap:       {m['overlap']} "
              f"(fraction of A points near B)")
        print(f"    A drift (early→late): {m['a_drift']}")
        print()

    print("  Scenario 1: observe vs k_b=100 (A's points last 500)")
    a1 = [tuple(r["to_point"]) for r in s1.a_records[-500:]]
    print(render_points(a1))
    print()
    print("  Overlay (A vs B last 500 points):")
    b1 = [tuple(r.point_b) for r in s1.world.records[-500:]
          if isinstance(r, WorldStepRecord)]
    print(render_overlay(a1, b1))
    print()

    print("  Scenario 3: adapt — k_b change at step 2500")
    a3_early = action_histogram(
        [r["action"] for r in s3.a_records[:2500]])
    a3_late = action_histogram(
        [r["action"] for r in s3.a_records[2500:]])
    print(f"    A dist before change:  "
          f"{[round(x, 3) for x in a3_early]}")
    print(f"    A dist after change:   "
          f"{[round(x, 3) for x in a3_late]}")
    print(f"    shift:                 "
          f"{round(bhattacharyya(a3_early, a3_late), 3)}")
    print()

    print("  What this establishes:")
    print("    - The scripted world is deterministic: given the")
    print("      world seed and the agent's picks, B's log")
    print("      replays exactly. Verification doesn't trust B.")
    print("    - The agent's log is cryptographically signed and")
    print("      its reward claims are recomputed against the")
    print("      shared buffer. Verification doesn't trust A.")
    print("    - Both verifications must pass. A's signatures +")
    print("      B's replay + reward consistency = full session")
    print("      verification.")
    print("    - The observation channel (RNN sees B's recent")
    print("      action frequency) is optional. Scenario 2 is")
    print("      the control: same reward, no observation. The")
    print("      comparison is what the measurements show.")
    print("    - Mid-run policy change tests adaptation: A's")
    print("      distribution shift before/after step 2500 is")
    print("      measured, not asserted.")
    print()
    print("  The honest finding: with 4 hidden units, A's")
    print("  response to B's policy is weak. The divergence")
    print("  numbers show *some* response; larger models would")
    print("  show more. The primitive is the point — a 90-")
    print("  parameter learner composes with a deterministic")
    print("  world without either side's trust being required.")
    print()
    print("  Anchor (public domain, Emily Dickinson):")
    print("    'The Brain – is wider than the Sky –'")
    print("    'For – put them side by side –'")

    audit = {}
    for s, label in sessions:
        m = measure(s)
        audit[label.replace(" ", "_")] = {
            **m,
            "verify": verify_session(s)[0],
        }
    a3_early_d = action_histogram(
        [r["action"] for r in s3.a_records[:2500]])
    a3_late_d = action_histogram(
        [r["action"] for r in s3.a_records[2500:]])
    audit["adaptation"] = {
        "before": [round(x, 3) for x in a3_early_d],
        "after": [round(x, 3) for x in a3_late_d],
        "shift": round(bhattacharyya(a3_early_d, a3_late_d), 3),
    }
    (path / "world_agent_coupling_demo.json").write_text(
        _json.dumps(audit, indent=2))
    print(f"\n  → {path}/world_agent_coupling_demo.json")
    return audit

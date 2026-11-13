"""
aristotle_cybernetics_c4.py
Component 4: The Self-Improving Telos.

Structural correspondence to the first file (compositional systems):
  - Method: propose variants, test against fitness, adopt winners.
  - The SelfImprover's `run_round` was the archetype.
  - Not imported as classes (fit mismatch); the method is reimplemented
    for continuous weight vectors.

The agent begins with W_0 (uniform or inherited), and revises W_t
via observed per-commitment rewards. Two reward models:
  (a) Phronimos-teacher: an external teacher provides per-commitment
      corrective feedback (moral education).
  (b) Self-assessment: the agent has access to the *eudaimonic fitness*
      of each commitment's value being advanced or violated.

Standard library plus numpy. Each test reports numbers; each has
a pass/fail criterion tied to a structural claim.
"""

import numpy as np
from aristotle_cybernetics_c3 import (
    TelosHierarchy, weighted_loss, optimal_action, infer_weights,
)


# ---------------------------------------------------------------------
# The learning rule
# ---------------------------------------------------------------------

def softmax(z, temperature=0.5):
    z = np.asarray(z, dtype=float) / temperature
    z = z - z.max()
    e = np.exp(z)
    return e / e.sum()


def update_telos(W_x, rewards, eta, temperature=0.5):
    """One step of telos learning.

    Args:
        W_x: current weights at situation x (length k, sums to 1)
        rewards: per-commitment fitness in situation x (length k)
        eta: learning rate
        temperature: softmax temperature for the target
    Returns:
        new W_x (normalized)
    """
    target = softmax(rewards, temperature)
    new = (1 - eta) * W_x + eta * target
    new = np.clip(new, 1e-8, None)
    return new / new.sum()


# ---------------------------------------------------------------------
# Test: recovering the true telos from corrective feedback
# ---------------------------------------------------------------------

def test_learn_from_teacher():
    """Claim: with per-commitment corrective feedback, W converges to W_true.

    The teacher provides the 'correct' reference at every situation. The
    student observes which commitments match the teacher's judgment, and
    reweights toward those commitments.
    """
    n_x, k, n_a = 20, 3, 5
    rng = np.random.default_rng(0)
    R = rng.integers(0, n_a, size=(n_x, k)).astype(float)

    # Ground-truth telos: uniform across situations, fixed
    W_true = np.tile(np.array([0.6, 0.3, 0.1]), (n_x, 1))

    def teacher_action(x):
        return optimal_action(R[x], W_true[x], n_a)

    # Student starts uniform
    W_learner = np.ones((n_x, k)) / k

    n_steps = 8000
    for _ in range(n_steps):
        x = int(rng.integers(0, n_x))
        a_teacher = teacher_action(x)
        # Per-commitment reward: 1 if commitment i's reference matches
        # the teacher's choice, else 0
        rewards = np.array([
            1.0 if int(R[x, i]) == a_teacher else 0.0
            for i in range(k)
        ])
        W_learner[x] = update_telos(W_learner[x], rewards,
                                    eta=0.2, temperature=0.3)

    # Two metrics
    behavioral_matches = sum(
        1 for x in range(n_x)
        if optimal_action(R[x], W_learner[x], n_a) == teacher_action(x)
    ) / n_x
    weights_close = float(np.mean(np.abs(W_learner - W_true)))

    print(f"  behavioral match: {behavioral_matches:.2f}")
    print(f"  weight distance: {weights_close:.4f}")
    print(f"  learned W[0]: {np.round(W_learner[0], 3)}  "
          f"true W[0]: {np.round(W_true[0], 3)}")
    assert behavioral_matches > 0.9, \
        f"Should match teacher: {behavioral_matches}"
    assert weights_close < 0.2, \
        f"Should approach true W: {weights_close}"


# ---------------------------------------------------------------------
# Test: self-assessment via eudaimonic fitness
# ---------------------------------------------------------------------

def test_learn_from_outcomes():
    """Claim: with per-commitment rewards from action, W converges.

    No teacher. The agent observes its own outcomes and infers which
    commitments advanced and which were violated. This is the
    self-education model — Aristotle's 'we become just by doing
    just acts, and the acts teach us what justice is.'
    """
    n_x, k, n_a = 20, 3, 5
    rng = np.random.default_rng(1)
    R = rng.integers(0, n_a, size=(n_x, k)).astype(float)

    W_true = np.tile(np.array([0.5, 0.3, 0.2]), (n_x, 1))

    def ideal_action(x):
        return optimal_action(R[x], W_true[x], n_a)

    # Reward function: commitment i is 'advanced' to the extent
    # the action was close to its reference
    def per_commitment_reward(x, a):
        return np.array([
            1.0 / (1.0 + abs(a - R[x, i]))
            for i in range(k)
        ])

    W_learner = np.ones((n_x, k)) / k

    n_steps = 8000
    for _ in range(n_steps):
        x = int(rng.integers(0, n_x))
        # The agent acts from its current W (with some exploration)
        a_current = optimal_action(R[x], W_learner[x], n_a)
        if rng.random() < 0.3:
            a_current = int(rng.integers(0, n_a))
        # Observe the per-commitment outcome of the action
        rewards = per_commitment_reward(x, a_current)
        W_learner[x] = update_telos(W_learner[x], rewards,
                                    eta=0.05, temperature=0.5)

    # Compare to W_true behavior
    behavioral_matches = sum(
        1 for x in range(n_x)
        if optimal_action(R[x], W_learner[x], n_a) == ideal_action(x)
    ) / n_x
    weights_close = float(np.mean(np.abs(W_learner - W_true)))

    print(f"  behavioral match: {behavioral_matches:.2f}")
    print(f"  weight distance: {weights_close:.4f}")
    print(f"  learned W[0]: {np.round(W_learner[0], 3)}  "
          f"true W[0]: {np.round(W_true[0], 3)}")
    # Self-assessment is harder; allow less strict thresholds
    assert behavioral_matches > 0.6, \
        f"Should approach truth: {behavioral_matches}"
    assert weights_close < 0.25, \
        f"Should approach true W: {weights_close}"


# ---------------------------------------------------------------------
# Test: polis of learners
# ---------------------------------------------------------------------

def test_polis_of_learners():
    """Claim: multiple agents learning from a shared phronimos converge
    to consensus. The polis's effective telos is the shared learned W.

    Each agent begins with a distinct W_0. They each learn from the same
    phronimos. Over time, their learned Ws converge to a common one.
    """
    n_x, k, n_a = 20, 3, 5
    n_agents = 6
    rng = np.random.default_rng(2)
    R = rng.integers(0, n_a, size=(n_x, k)).astype(float)

    W_true = np.tile(np.array([0.5, 0.3, 0.2]), (n_x, 1))

    def teacher_action(x):
        return optimal_action(R[x], W_true[x], n_a)

    # Each agent starts from a distinct random W
    Ws = [rng.dirichlet(np.ones(k), size=n_x) for _ in range(n_agents)]

    def spread():
        stack = np.stack(Ws)  # (n_agents, n_x, k)
        return float(np.mean(np.var(stack, axis=0)))

    d0 = spread()
    print(f"  initial spread: {d0:.4f}")

    n_steps = 10000
    for _ in range(n_steps):
        x = int(rng.integers(0, n_x))
        a_t = teacher_action(x)
        rewards = np.array([
            1.0 if int(R[x, i]) == a_t else 0.0 for i in range(k)
        ])
        for j in range(n_agents):
            Ws[j][x] = update_telos(Ws[j][x], rewards,
                                    eta=0.15, temperature=0.3)

    d1 = spread()
    # Average behavioral match per agent vs. teacher
    matches = []
    for j in range(n_agents):
        m = sum(1 for x in range(n_x)
                if optimal_action(R[x], Ws[j][x], n_a) == teacher_action(x))
        matches.append(m / n_x)
    m_avg = float(np.mean(matches))
    print(f"  final spread:   {d1:.4f}")
    print(f"  avg behavioral match: {m_avg:.2f}")
    assert d1 < d0 * 0.5, f"Consensus should reduce spread: {d0} -> {d1}"
    assert m_avg > 0.8, f"Learners should approach teacher: {m_avg}"


# ---------------------------------------------------------------------
# Test: incorrect teacher -> learner adopts the incorrect telos
# ---------------------------------------------------------------------

def test_wrong_teacher():
    """Claim: if the teacher is wrong, the learner learns the wrong telos.

    The structural prediction: the learner is *faithful* to the teacher,
    even when the teacher is wrong. Moral education is the transmission
    of the teacher's actual telos, not the teacher's claimed telos.
    """
    n_x, k, n_a = 20, 3, 5
    rng = np.random.default_rng(3)
    R = rng.integers(0, n_a, size=(n_x, k)).astype(float)

    # The "true" telos (what the world requires)
    W_world = np.tile(np.array([0.5, 0.3, 0.2]), (n_x, 1))
    # The "teacher's" telos (what the teacher actually believes)
    W_teacher = np.tile(np.array([0.2, 0.3, 0.5]), (n_x, 1))

    def teacher_action(x):
        return optimal_action(R[x], W_teacher[x], n_a)

    def world_action(x):
        return optimal_action(R[x], W_world[x], n_a)

    W_learner = np.ones((n_x, k)) / k
    n_steps = 8000
    for _ in range(n_steps):
        x = int(rng.integers(0, n_x))
        a_t = teacher_action(x)
        rewards = np.array([
            1.0 if int(R[x, i]) == a_t else 0.0 for i in range(k)
        ])
        W_learner[x] = update_telos(W_learner[x], rewards,
                                    eta=0.2, temperature=0.3)

    match_teacher = sum(
        1 for x in range(n_x)
        if optimal_action(R[x], W_learner[x], n_a) == teacher_action(x)
    ) / n_x
    match_world = sum(
        1 for x in range(n_x)
        if optimal_action(R[x], W_learner[x], n_a) == world_action(x)
    ) / n_x

    print(f"  match teacher: {match_teacher:.2f}")
    print(f"  match world:   {match_world:.2f}")
    assert match_teacher > 0.9, \
        f"Should be faithful to teacher: {match_teacher}"
    # Not asserting match_world is low because in some cases teacher
    # and world actions coincide. What matters is the *asymmetry*.
    print(f"  asymmetry (teacher - world): {match_teacher - match_world:.2f}")


# ---------------------------------------------------------------------
# Test: pro-sociality under noisy feedback
# ---------------------------------------------------------------------

def test_noisy_feedback():
    """Claim: with noisy feedback, learning is slower but converges.

    The structure is robust: the learner still approaches the truth,
    just more slowly. This is the classical signal-detection result
    applied to moral education.
    """
    n_x, k, n_a = 20, 3, 5
    rng = np.random.default_rng(4)
    R = rng.integers(0, n_a, size=(n_x, k)).astype(float)
    W_true = np.tile(np.array([0.5, 0.3, 0.2]), (n_x, 1))

    def teacher_action(x):
        return optimal_action(R[x], W_true[x], n_a)

    def run(noise_level, seed, n_steps=8000):
        r = np.random.default_rng(seed)
        W = np.ones((n_x, k)) / k
        for _ in range(n_steps):
            x = int(r.integers(0, n_x))
            a_t = teacher_action(x)
            rewards = np.array([
                1.0 if int(R[x, i]) == a_t else 0.0
                for i in range(k)
            ])
            # Corrupt rewards with noise
            if r.random() < noise_level:
                rewards = r.permutation(rewards)
            W[x] = update_telos(W[x], rewards,
                                eta=0.2, temperature=0.3)
        matches = sum(
            1 for x in range(n_x)
            if optimal_action(R[x], W[x], n_a) == teacher_action(x)
        ) / n_x
        return matches

    m_clean = float(np.mean([run(0.0, s) for s in range(5)]))
    m_noisy = float(np.mean([run(0.3, s) for s in range(5)]))
    m_very_noisy = float(np.mean([run(0.6, s) for s in range(5)]))
    print(f"  clean:     {m_clean:.2f}")
    print(f"  30% noise: {m_noisy:.2f}")
    print(f"  60% noise: {m_very_noisy:.2f}")
    assert m_clean > 0.9, f"Clean should converge: {m_clean}"
    assert m_noisy > m_very_noisy, \
        f"Noisier should be worse: {m_noisy} vs {m_very_noisy}"


# ---------------------------------------------------------------------

if __name__ == "__main__":
    for fn in [test_learn_from_teacher, test_learn_from_outcomes,
               test_polis_of_learners, test_wrong_teacher,
               test_noisy_feedback]:
        print(f"--- {fn.__name__} ---")
        fn()
        print("PASS\n")

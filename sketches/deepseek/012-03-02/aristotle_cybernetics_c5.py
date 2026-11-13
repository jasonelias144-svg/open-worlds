"""
aristotle_cybernetics_c5.py
Component 5: The Self-Referential Telos.

The structural question: what happens when the fitness signal that
shapes the telos is itself produced by the telos?

Three fitness models:
  - Subjective (self-referential): the agent observes the extent to
    which its action satisfied its current commitments. The fitness
    is internally generated.
  - Objective (external): the agent observes a fitness signal that
    is independent of its own telos — the world's judgment.
  - Hybrid: a mixture.

Tests:
  1. Self-referential learning converges to a fixed point.
  2. The fixed points are the dominant-commitment teloi (fanaticism
     is a fixed point; pluralism is not).
  3. Different initial W's converge to different fixed points
     (path-dependence).
  4. Uniform W is unstable — pluralism collapses under subjective
     learning.
  5. External correction breaks the self-reinforcement.

Standard library plus numpy. Imports from C3 and C4.
"""

import numpy as np
from aristotle_cybernetics_c3 import (
    TelosHierarchy, weighted_loss, optimal_action,
)
from aristotle_cybernetics_c4 import (
    update_telos, softmax,
)


# ---------------------------------------------------------------------
# Fitness models
# ---------------------------------------------------------------------

def subjective_fitness(R_x, W_x, a):
    """Per-commitment satisfaction from the agent's own action.

    Commitment i is 'satisfied' to the extent its reference R_i(x)
    matches the chosen action a. The signal is internally generated:
    the agent's own action is the fitness signal.
    """
    return -np.abs(a - R_x)


def objective_fitness(R_true_x, a):
    """The world's judgment: how well the action matched the true
    reference at x. Independent of the agent's telos.
    """
    return -np.abs(a - R_true_x)


# ---------------------------------------------------------------------
# The self-referential loop
# ---------------------------------------------------------------------

def self_referential_run(n_x, k, n_a, R, W_0,
                         eta=0.1, temperature=0.3,
                         n_steps=5000, seed=0):
    """Run the closed loop W -> a -> fitness -> W.

    Returns:
        W: final telos (n_x, k)
        trajectory: list of (step, mean_W) for plotting
    """
    rng = np.random.default_rng(seed)
    W = W_0.copy()
    trajectory = [W.copy()]
    for _ in range(n_steps):
        x = int(rng.integers(0, n_x))
        a = optimal_action(R[x], W[x], n_a)
        rewards = subjective_fitness(R[x], W[x], a)
        W[x] = update_telos(W[x], rewards, eta=eta,
                             temperature=temperature)
        if _ % 500 == 0:
            trajectory.append(W.copy())
    return W, trajectory


# ---------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------

def test_convergence():
    """Claim: self-referential learning converges to a fixed point."""
    n_x, k, n_a = 1, 3, 5
    R = np.array([[0., 2., 4.]])
    W_0 = np.array([[0.34, 0.33, 0.33]])

    W_final, traj = self_referential_run(n_x, k, n_a, R, W_0,
                                          eta=0.1, n_steps=3000)

    # Check that W stabilized: last two snapshots are nearly identical
    diff = float(np.max(np.abs(traj[-1] - traj[-2])))
    print(f"  final W: {np.round(W_final[0], 3)}")
    print(f"  last step diff: {diff:.4f}")
    assert diff < 0.05, f"Did not converge: {diff}"


def test_fanaticism_is_a_fixed_point():
    """Claim: dominant-commitment teloi are fixed points."""
    n_x, k, n_a = 1, 3, 5
    R = np.array([[0., 2., 4.]])

    print(f"  {'initial W':>20}  {'final W':>25}  {'action':>7}")
    for W_0_np in [np.array([1., 0., 0.]),
                   np.array([0., 1., 0.]),
                   np.array([0., 0., 1.])]:
        W_0 = W_0_np.reshape(1, -1)
        W_final, _ = self_referential_run(n_x, k, n_a, R, W_0,
                                            eta=0.1, n_steps=3000)
        a = optimal_action(R[0], W_final[0], n_a)
        print(f"  {str(np.round(W_0[0], 2)):>20}  "
              f"{str(np.round(W_final[0], 3)):>25}  {a:>7}")
        # Each dominant-commitment start remains dominant
        assert W_final[0, int(np.argmax(W_0_np))] > 0.85, \
            f"Fanaticism should be preserved: {W_final[0]}"


def test_pluralism_collapses():
    """Claim: uniform telos is NOT a fixed point."""
    n_x, k, n_a = 1, 3, 5
    R = np.array([[0., 2., 4.]])
    W_0 = np.array([[1/3, 1/3, 1/3]])

    W_final, traj = self_referential_run(n_x, k, n_a, R, W_0,
                                          eta=0.1, n_steps=3000)

    # Uniform W should NOT remain uniform
    deviation = float(np.max(np.abs(W_final[0] - W_0[0])))
    print(f"  initial W: {np.round(W_0[0], 3)}")
    print(f"  final W:   {np.round(W_final[0], 3)}")
    print(f"  deviation: {deviation:.3f}")
    assert deviation > 0.3, \
        f"Pluralism should collapse: {deviation}"


def test_path_dependence():
    """Claim: different initial W's converge to different fixed points."""
    n_x, k, n_a = 1, 3, 5
    R = np.array([[0., 2., 4.]])

    # Slight bias toward different commitments
    W_A = np.array([[0.4, 0.35, 0.25]])
    W_B = np.array([[0.25, 0.35, 0.4]])
    W_C = np.array([[0.25, 0.4, 0.35]])

    print(f"  {'initial':>20}  {'final':>25}  {'dominant':>9}")
    fixed_points = []
    for label, W_0 in [("bias A", W_A), ("bias B", W_B), ("bias C", W_C)]:
        W_final, _ = self_referential_run(n_x, k, n_a, R, W_0,
                                            eta=0.1, n_steps=3000)
        dom = int(np.argmax(W_final[0]))
        fixed_points.append(dom)
        print(f"  {label:>20}  {str(np.round(W_final[0], 3)):>25}  {dom:>9}")

    # The three biased starts should give at least two distinct fixed points
    assert len(set(fixed_points)) >= 2, \
        f"Path dependence: fixed points should differ, got {fixed_points}"


def test_external_correction_breaks_pathology():
    """Claim: external correction prevents collapse into fanaticism.

    The agent has a self-referential fitness, but a teacher provides
    occasional corrective signal. The teacher's signal is the objective
    fitness with respect to the 'true' telos.
    """
    n_x, k, n_a = 10, 3, 5
    rng = np.random.default_rng(0)
    R = rng.integers(0, n_a, size=(n_x, k)).astype(float)
    W_true = np.tile(np.array([0.5, 0.3, 0.2]), (n_x, 1))

    def run(correction_rate, seed, n_steps=8000):
        r = np.random.default_rng(seed)
        W = np.tile(np.array([1.0, 0.0, 0.0]), (n_x, 1))  # fanatical start
        for _ in range(n_steps):
            x = int(r.integers(0, n_x))
            a = optimal_action(R[x], W[x], n_a)
            subj = subjective_fitness(R[x], W[x], a)
            if r.random() < correction_rate:
                a_true = optimal_action(R[x], W_true[x], n_a)
                obj = objective_fitness(R[x, :3], a_true)  # wrong; use teacher map
                # Use the teacher's rewards directly:
                obj_rewards = np.array([
                    1.0 if int(R[x, i]) == a_true else 0.0
                    for i in range(k)
                ])
                W[x] = update_telos(W[x], obj_rewards,
                                     eta=0.15, temperature=0.3)
            else:
                W[x] = update_telos(W[x], subj,
                                     eta=0.1, temperature=0.3)
        # Score against the true telos
        matches = sum(
            1 for x in range(n_x)
            if optimal_action(R[x], W[x], n_a) ==
               optimal_action(R[x], W_true[x], n_a)
        ) / n_x
        return matches

    m_pure = float(np.mean([run(0.0, s) for s in range(3)]))
    m_light = float(np.mean([run(0.1, s) for s in range(3)]))
    m_heavy = float(np.mean([run(0.4, s) for s in range(3)]))
    print(f"  pure self-referential: {m_pure:.2f}")
    print(f"  10% external correction: {m_light:.2f}")
    print(f"  40% external correction: {m_heavy:.2f}")
    assert m_heavy > m_pure, \
        f"Correction should help: pure={m_pure}, heavy={m_heavy}"
    assert m_heavy > 0.7, \
        f"Heavy correction should approach true: {m_heavy}"


def test_trajectory():
    """Report: trajectory of W over time from pluralism to fanaticism."""
    n_x, k, n_a = 1, 3, 5
    R = np.array([[0., 2., 4.]])
    W_0 = np.array([[0.34, 0.33, 0.33]])
    _, traj = self_referential_run(n_x, k, n_a, R, W_0,
                                     eta=0.1, n_steps=2000)
    print(f"  {'step':>6}  {'W':>30}  {'action':>7}")
    for i, W in enumerate(traj):
        a = optimal_action(R[0], W[0], n_a)
        print(f"  {i*500:>6}  {str(np.round(W[0], 3)):>30}  {a:>7}")


# ---------------------------------------------------------------------

if __name__ == "__main__":
    for fn in [test_convergence, test_fanaticism_is_a_fixed_point,
               test_pluralism_collapses, test_path_dependence,
               test_external_correction_breaks_pathology,
               test_trajectory]:
        print(f"--- {fn.__name__} ---")
        fn()
        print("PASS\n")

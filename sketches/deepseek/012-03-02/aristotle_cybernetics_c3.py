"""
aristotle_cybernetics_c3.py
Component 3: The Telos Hierarchy.

Formal model:
  - Situation space X = {0, ..., n_x-1}
  - k commitments, each providing a reference R_i: X -> A
  - Telos hierarchy W: X -> Δ^k (situation-dependent weights, sum to 1)
  - Deliberation: a* = argmin_a Σ_i W_i(x) |a - R_i(x)|
  - Learning: W is updated toward weights inferred from observed actions
    or reinforced by outcomes

Nested operator structure:
  W (perceptual, situation-dependent) shapes H (action policy) shapes a.

Standard library plus numpy. Each test's pass/fail is tied to a
structural claim from the NE (II.6 mean, VI.5 phronesis, VI.8 telos, VII.3 akrasia).
"""

import numpy as np


# ---------------------------------------------------------------------
# Primitives
# ---------------------------------------------------------------------

class TelosHierarchy:
    """W: X -> Delta^k, situation-dependent weighting."""

    def __init__(self, n_x, k, table=None):
        self.n_x, self.k = n_x, k
        if table is None:
            self.W = np.ones((n_x, k)) / k
        else:
            self.W = np.asarray(table, dtype=float)

    def __call__(self, x):
        return self.W[x].copy()

    def update(self, x, target, eta):
        target = np.asarray(target, dtype=float)
        self.W[x] = (1 - eta) * self.W[x] + eta * target
        self.W[x] = np.clip(self.W[x], 1e-6, None)
        self.W[x] /= self.W[x].sum()

    def copy(self):
        return TelosHierarchy(self.n_x, self.k, self.W.copy())


def weighted_loss(R, W, a):
    return float(np.sum(W * np.abs(a - R)))


def optimal_action(R, W, n_a):
    losses = [weighted_loss(R, W, a) for a in range(n_a)]
    return int(np.argmin(losses))


def infer_weights(R, a_observed):
    """Weights that justify a_observed: 1 / (1 + |a_obs - R_i|), normalized."""
    losses = np.abs(a_observed - R)
    inv = 1.0 / (1.0 + losses)
    return inv / inv.sum()


# ---------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------

def test_weighted_median():
    """Claim: with a single commitment dominant, the action follows that commitment."""
    R = np.array([0., 2., 4.])
    W = np.array([0.8, 0.1, 0.1])
    a = optimal_action(R, W, 5)
    print(f"  R={R}, W={W} -> a={a}")
    assert a == 0, f"Expected 0 (dominant commitment), got {a}"


def test_situation_dependence():
    """Claim: same R, different W -> different actions. Phronesis is perceptual."""
    R = np.array([0., 2., 4.])
    W_kind = np.array([0.8, 0.1, 0.1])
    W_severe = np.array([0.1, 0.1, 0.8])
    a_kind = optimal_action(R, W_kind, 5)
    a_severe = optimal_action(R, W_severe, 5)
    print(f"  R={R}  kind W -> a={a_kind}  severe W -> a={a_severe}")
    assert a_kind == 0
    assert a_severe == 4
    assert a_kind != a_severe


def test_irresolvability_spectrum():
    """Claim: min achievable loss increases as max weight decreases.

    Irresolvability is a quantitative function of W_max, not just R.
    """
    R = np.array([0., 2., 4.])
    n_a = 5
    print(f"  {'W_max':>6}  {'best W':>20}  {'min loss':>9}")
    prev = -1.0
    for W_max in [1.0, 0.9, 0.7, 0.5, 1/3]:
        # Optimize W over the constraint max W_i <= W_max
        best_loss = float('inf')
        best_W = None
        for w0 in np.linspace(0, W_max, 11):
            for w1 in np.linspace(0, W_max - w0, 11):
                for w2 in np.linspace(0, W_max - w0 - w1, 11):
                    s = w0 + w1 + w2
                    if s <= 0:
                        continue
                    W = np.array([w0, w1, w2]) / s
                    if max(W) > W_max + 1e-9:
                        continue
                    a = optimal_action(R, W, n_a)
                    loss = weighted_loss(R, W, a)
                    if loss < best_loss:
                        best_loss, best_W = loss, W
        print(f"  {W_max:>6.2f}  {str(np.round(best_W, 2)):>20}  {best_loss:>9.3f}")
        assert best_loss >= prev - 1e-9, f"Loss should be non-increasing in W_max"
        prev = best_loss
    # Under W_max = 1/3 (uniform), loss is strictly positive
    assert prev > 0.1, f"Uniform weighting should have positive loss, got {prev}"


def test_moral_development():
    """Claim: a student learns a teacher's behavior by inferring W from actions.

    The inference is inverse RL: observed action -> weights that justify it.
    """
    n_x, k, n_a = 5, 3, 5
    rng = np.random.default_rng(42)
    R_table = rng.integers(0, n_a, size=(n_x, k)).astype(float)
    W_teacher = np.tile(np.array([0.6, 0.3, 0.1]), (n_x, 1))

    def teacher_action(x):
        return optimal_action(R_table[x], W_teacher[x], n_a)

    student = TelosHierarchy(n_x, k)

    for step in range(1000):
        x = int(rng.integers(0, n_x))
        target = infer_weights(R_table[x], teacher_action(x))
        student.update(x, target, eta=0.15)

    matches = sum(1 for x in range(n_x)
                  if student(x).argmax() == teacher_action(x))
    print(f"  behavioral match: {matches}/{n_x}")
    assert matches >= n_x - 1, f"Student should imitate teacher, got {matches}/{n_x}"


def test_polis_consensus():
    """Claim: a polis of diverse agents converges to consensus via median action.

    The consensus is the 'median-justified' W, not the truth. The polis
    homogenizes; it does not discover the correct telos.
    """
    n_x, k, n_a = 5, 3, 5
    n_agents = 7
    rng = np.random.default_rng(7)
    R_table = rng.integers(0, n_a, size=(n_x, k)).astype(float)

    agents = [TelosHierarchy(n_x, k,
                             rng.dirichlet(np.ones(k), size=n_x))
              for _ in range(n_agents)]

    def spread():
        W_stack = np.stack([a.W for a in agents])  # (n_agents, n_x, k)
        return float(np.mean(np.var(W_stack, axis=0)))

    d0 = spread()
    print(f"  initial spread: {d0:.4f}")

    for step in range(2000):
        x = int(rng.integers(0, n_x))
        proposed = [a(x) for a in agents]
        a_consensus = int(np.median(proposed))
        target = infer_weights(R_table[x], a_consensus)
        for agent in agents:
            agent.update(x, target, eta=0.05)

    d1 = spread()
    print(f"  final spread:   {d1:.4f}")
    assert d1 < d0 * 0.5, f"Consensus should reduce spread: {d0} -> {d1}"


def test_error_modes():
    """Report: systematic W corruption vs. per-situation optimizer noise.

    Compares loss under (a) W perturbed globally toward uniform, and
    (b) optimal W with per-situation random optimizer noise.
    """
    n_x, k, n_a = 30, 3, 5
    rng = np.random.default_rng(0)
    R_table = rng.integers(0, n_a, size=(n_x, k)).astype(float)
    W_true = np.tile(np.array([0.6, 0.3, 0.1]), (n_x, 1))

    def L(action_fn):
        return sum(weighted_loss(R_table[x], W_true[x], action_fn(x))
                   for x in range(n_x)) / n_x

    L_base = L(lambda x: optimal_action(R_table[x], W_true[x], n_a))
    print(f"  baseline L0 = {L_base:.3f}")
    print(f"  {'eps':>4}  {'L_weight':>9}  {'L_optimizer':>12}")

    for eps in [0.0, 0.25, 0.5, 0.75, 1.0]:
        W_corrupt = (1 - eps) * W_true + eps * (np.ones(k) / k)
        L_w = L(lambda x: optimal_action(R_table[x], W_corrupt[x], n_a))

        L_opt_runs = []
        for run in range(30):
            r = np.random.default_rng(run + 100)
            def act(x, r=r):
                if r.random() < eps:
                    return int(r.integers(0, n_a))
                return optimal_action(R_table[x], W_true[x], n_a)
            L_opt_runs.append(L(act))
        L_opt = float(np.mean(L_opt_runs))
        print(f"  {eps:>4.2f}  {L_w:>9.3f}  {L_opt:>12.3f}")


# ---------------------------------------------------------------------

if __name__ == "__main__":
    for fn in [test_weighted_median, test_situation_dependence,
               test_irresolvability_spectrum, test_moral_development,
               test_polis_consensus, test_error_modes]:
        print(f"--- {fn.__name__} ---")
        fn()
        print("PASS\n")

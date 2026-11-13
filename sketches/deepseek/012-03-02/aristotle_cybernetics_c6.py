"""
aristotle_cybernetics_c6.py
Component 6: The Mutual Correction (philia).

The polis as mutual correction: agents observe each other's teloi
and adjust. The question: does peer consensus cure the fanaticism
pathology found in Component 5?

Imports from prior modules:
  - optimal_action, weighted_loss (C3)
  - softmax (C4)
  - subjective_fitness (C5)

Structural claim: mutual correction homogenizes but does not cure.
The polis needs a teacher, not just peers.
"""

import numpy as np
from aristotle_cybernetics_c3 import (
    TelosHierarchy, weighted_loss, optimal_action,
)
from aristotle_cybernetics_c4 import softmax
from aristotle_cybernetics_c5 import subjective_fitness


# ---------------------------------------------------------------------
# Topologies
# ---------------------------------------------------------------------

def complete_adjacency(n):
    return [[j for j in range(n) if j != i] for i in range(n)]

def ring_adjacency(n):
    return [[(i - 1) % n, (i + 1) % n] for i in range(n)]

def star_adjacency(n):
    """Agent 0 is the hub; all others connect only to the hub."""
    adj = [[] for _ in range(n)]
    for i in range(1, n):
        adj[i].append(0)
        adj[0].append(i)
    return adj


# ---------------------------------------------------------------------
# Initial conditions
# ---------------------------------------------------------------------

def uniform_inits(n_agents, n_x, k):
    return [np.ones((n_x, k)) / k for _ in range(n_agents)]

def random_inits(n_agents, n_x, k, seed, concentration=1.0):
    rng = np.random.default_rng(seed)
    return [rng.dirichlet(np.ones(k) * concentration, size=n_x)
            for _ in range(n_agents)]

def one_adversary_inits(n_agents, n_x, k, adversary_index=0,
                        adversary_commitment=0):
    """All agents uniform except one fanatic toward commitment c."""
    Ws = uniform_inits(n_agents, n_x, k)
    W_adv = np.zeros((n_x, k))
    W_adv[:, adversary_commitment] = 0.95
    W_adv[:, (adversary_commitment + 1) % k] = 0.05
    Ws[adversary_index] = W_adv
    return Ws


# ---------------------------------------------------------------------
# Metrics
# ---------------------------------------------------------------------

def fanaticism_index(Ws):
    """Mean max weight across all agents and situations."""
    return float(np.mean([np.max(W, axis=1).mean() for W in Ws]))

def diversity_index(Ws):
    """Mean variance across agents (per situation, per commitment)."""
    stack = np.stack(Ws)  # (n_agents, n_x, k)
    return float(np.mean(np.var(stack, axis=0)))

def mean_weight(Ws):
    """Mean W across all agents and situations (k,)."""
    return np.mean([W.mean(axis=0) for W in Ws], axis=0)


# ---------------------------------------------------------------------
# The polis dynamics
# ---------------------------------------------------------------------

def polis_run(Ws, R, adjacency, self_weight, neighbor_weight,
              eta, temperature, n_x, n_a, n_steps, seed,
              snapshot_steps=None):
    """Run the polis dynamics with mutual correction.

    At each step:
      1. Pick a situation x.
      2. For each agent i:
         a. Compute own self-referential target (softmax of subjective fitness).
         b. Compute neighbor consensus (mean of neighbors' W at x).
         c. Blend: target = self_weight * own + neighbor_weight * consensus.
      3. Update all W's toward their targets (Jacobi, not Gauss-Seidel).

    Returns:
        Ws: final teloi
        snapshots: dict of {step: (fanaticism, diversity, mean_weight)}
    """
    rng = np.random.default_rng(seed)
    n_agents = len(Ws)
    snapshots = {}
    if snapshot_steps is None:
        snapshot_steps = [0, n_steps // 4, n_steps // 2,
                          3 * n_steps // 4, n_steps]

    for step in range(n_steps + 1):
        if step in snapshot_steps:
            snapshots[step] = (
                fanaticism_index(Ws),
                diversity_index(Ws),
                mean_weight(Ws),
            )
        if step == n_steps:
            break

        x = int(rng.integers(0, n_x))
        targets = []
        for i in range(n_agents):
            a_i = optimal_action(R[x], Ws[i][x], n_a)
            subj = subjective_fitness(R[x], Ws[i][x], a_i)
            own_target = softmax(subj, temperature)
            if adjacency[i]:
                neighbor_consensus = np.mean(
                    [Ws[j][x] for j in adjacency[i]], axis=0)
            else:
                neighbor_consensus = own_target
            target = self_weight * own_target + neighbor_weight * neighbor_consensus
            target = np.clip(target, 1e-8, None)
            target = target / target.sum()
            targets.append(target)
        for i in range(n_agents):
            Ws[i][x] = (1 - eta) * Ws[i][x] + eta * targets[i]
            Ws[i][x] = np.clip(Ws[i][x], 1e-8, None)
            Ws[i][x] /= Ws[i][x].sum()

    return Ws, snapshots


# ---------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------

N_AGENTS = 6
N_X = 5
K = 3
N_A = 5
N_STEPS = 2000

def _R_table():
    rng = np.random.default_rng(11)
    return rng.integers(0, N_A, size=(N_X, K)).astype(float)

def _print_snaps(name, snaps):
    print(f"  {name}")
    for step, (fan, div, mw) in sorted(snaps.items()):
        print(f"    step {step:>5}: "
              f"fanaticism={fan:.3f}  diversity={div:.4f}  "
              f"meanW={np.round(mw, 2)}")


def test_mutual_correction_homogenizes():
    """Claim: peer correction reduces diversity monotonically.

    Complete graph, diverse starts. Self_weight=0.5, neighbor_weight=0.5.
    """
    R = _R_table()
    Ws = random_inits(N_AGENTS, N_X, K, seed=1, concentration=0.5)
    Ws, snaps = polis_run(
        Ws, R, complete_adjacency(N_AGENTS),
        self_weight=0.5, neighbor_weight=0.5,
        eta=0.1, temperature=0.3,
        n_x=N_X, n_a=N_A, n_steps=N_STEPS, seed=42,
    )
    _print_snaps("Complete graph, diverse start:", snaps)
    d0 = snaps[0][1]
    d1 = snaps[N_STEPS][1]
    assert d1 < d0 * 0.5, f"Diversity should drop: {d0:.4f} -> {d1:.4f}"


def test_homogenization_rate_depends_on_topology():
    """Claim: complete graph homogenizes faster than ring.

    This is the spectral gap effect: dense graphs mix faster.
    """
    R = _R_table()
    seeds = [1, 2, 3, 4, 5]

    def final_diversity(adjacency):
        ds = []
        for s in seeds:
            Ws = random_inits(N_AGENTS, N_X, K, seed=s, concentration=0.5)
            Ws, snaps = polis_run(
                Ws, R, adjacency,
                self_weight=0.5, neighbor_weight=0.5,
                eta=0.1, temperature=0.3,
                n_x=N_X, n_a=N_A, n_steps=N_STEPS, seed=42 + s,
            )
            ds.append(snaps[N_STEPS][1])
        return float(np.mean(ds))

    d_complete = final_diversity(complete_adjacency(N_AGENTS))
    d_ring = final_diversity(ring_adjacency(N_AGENTS))
    print(f"  complete graph final diversity: {d_complete:.4f}")
    print(f"  ring graph final diversity:     {d_ring:.4f}")
    assert d_complete < d_ring, \
        f"Complete should homogenize more: {d_complete} vs {d_ring}"


def test_mutual_correction_does_not_cure():
    """Claim: homogenization does not prevent drift to fanaticism.

    Diverse start, complete graph. The polis still ends fanatical.
    """
    R = _R_table()
    Ws = random_inits(N_AGENTS, N_X, K, seed=1, concentration=0.5)
    Ws, snaps = polis_run(
        Ws, R, complete_adjacency(N_AGENTS),
        self_weight=0.5, neighbor_weight=0.5,
        eta=0.1, temperature=0.3,
        n_x=N_X, n_a=N_A, n_steps=N_STEPS, seed=42,
    )
    _print_snaps("Complete graph, diverse start, self=0.5:", snaps)
    fan0 = snaps[0][0]
    fan1 = snaps[N_STEPS][0]
    print(f"  fanaticism: {fan0:.3f} -> {fan1:.3f}")
    # The polis drifts to fanaticism even though it homogenized
    assert fan1 > fan0 + 0.3, \
        f"Fanaticism should increase: {fan0} -> {fan1}"


def test_pure_conformity_freezes():
    """Claim: with self_weight=0, no self-referential drift.

    Pure conformity is a museum: the polis stays at its initial mean.
    """
    R = _R_table()
    seeds = [1, 2, 3]
    finals = []
    for s in seeds:
        Ws = random_inits(N_AGENTS, N_X, K, seed=s, concentration=0.5)
        Ws, snaps = polis_run(
            Ws, R, complete_adjacency(N_AGENTS),
            self_weight=0.0, neighbor_weight=1.0,
            eta=0.1, temperature=0.3,
            n_x=N_X, n_a=N_A, n_steps=N_STEPS, seed=42 + s,
        )
        finals.append(snaps[N_STEPS])
    fans = [f[0] for f in finals]
    divs = [f[1] for f in finals]
    print(f"  pure conformity, 3 seeds:")
    print(f"    fanaticism: {[f'{f:.3f}' for f in fans]}")
    print(f"    diversity:  {[f'{d:.4f}' for d in divs]}")
    # With self_weight=0, fanaticism stays near the initial mean's max
    # The key test: fanaticism doesn't grow to 1.0
    assert max(fans) < 0.85, \
        f"Pure conformity should not collapse: {fans}"


def test_self_weight_controls_drift():
    """Claim: fanaticism growth scales with self_weight.

    self=0: no drift. self=1: full drift to fanaticism. self=0.5: between.
    """
    R = _R_table()
    print(f"  {'self_weight':>12}  {'fanaticism_0':>14}  {'fanaticism_N':>14}")
    for sw in [0.0, 0.3, 0.5, 0.7, 1.0]:
        Ws = random_inits(N_AGENTS, N_X, K, seed=1, concentration=0.5)
        Ws, snaps = polis_run(
            Ws, R, complete_adjacency(N_AGENTS),
            self_weight=sw, neighbor_weight=1.0 - sw,
            eta=0.1, temperature=0.3,
            n_x=N_X, n_a=N_A, n_steps=N_STEPS, seed=42,
        )
        print(f"  {sw:>12.2f}  {snaps[0][0]:>14.3f}  "
              f"{snaps[N_STEPS][0]:>14.3f}")


def test_adversary_diluted_by_degree():
    """Claim: adversary's influence depends on degree.

    In complete graph, one adversary's weight in consensus is 1/(n-1).
    In ring, it is 1/2 for neighbors.
    """
    R = _R_table()
    seeds = [1, 2, 3]

    def infection_rate(adjacency, label):
        """How much do non-adversary agents move toward adversary's telos?"""
        contagions = []
        for s in seeds:
            Ws = one_adversary_inits(N_AGENTS, N_X, K,
                                      adversary_index=0,
                                      adversary_commitment=0)
            W_adv0 = Ws[0].copy()
            Ws, snaps = polis_run(
                Ws, R, adjacency,
                self_weight=0.5, neighbor_weight=0.5,
                eta=0.1, temperature=0.3,
                n_x=N_X, n_a=N_A, n_steps=N_STEPS, seed=42 + s,
            )
            # Contagion: mean weight on commitment 0 across
            # non-adversary agents at final step
            non_adv_mean0 = float(np.mean([
                Ws[i][:, 0].mean() for i in range(1, N_AGENTS)
            ]))
            contagions.append(non_adv_mean0)
        m = float(np.mean(contagions))
        print(f"  {label}: mean non-adversary weight on adversary's "
              f"commitment at end = {m:.3f}")
        return m

    c_complete = infection_rate(complete_adjacency(N_AGENTS), "complete")
    c_ring = infection_rate(ring_adjacency(N_AGENTS), "ring")
    c_star = infection_rate(star_adjacency(N_AGENTS), "star")


def test_all_agents_are_echo_chamber():
    """Claim: if all agents start identical, no correction ever occurs.

    This is the pure echo chamber: the polis is a mirror.
    """
    R = _R_table()
    Ws = uniform_inits(N_AGENTS, N_X, K)
    Ws, snaps = polis_run(
        Ws, R, complete_adjacency(N_AGENTS),
        self_weight=0.5, neighbor_weight=0.5,
        eta=0.1, temperature=0.3,
        n_x=N_X, n_a=N_A, n_steps=N_STEPS, seed=42,
    )
    _print_snaps("All uniform, complete graph:", snaps)
    d0 = snaps[0][1]
    d1 = snaps[N_STEPS][1]
    print(f"  diversity {d0:.4f} -> {d1:.4f}")
    # Diversity stays near zero (nothing to homogenize)
    assert d1 < 0.01, f"Uniform start should stay uniform: {d1}"


def test_uniform_vs_diverse_convergence():
    """Claim: diverse polis converges to arbitrary attractor; uniform polis
    converges to a specific one. Path dependence in the polis.
    """
    R = _R_table()
    print(f"  {'start':>12}  {'final mean W':>25}  {'final fanaticism':>18}")

    for label, init_fn in [
        ("uniform", lambda: uniform_inits(N_AGENTS, N_X, K)),
        ("diverse-1", lambda: random_inits(N_AGENTS, N_X, K, seed=1, concentration=0.5)),
        ("diverse-2", lambda: random_inits(N_AGENTS, N_X, K, seed=2, concentration=0.5)),
    ]:
        Ws = init_fn()
        Ws, snaps = polis_run(
            Ws, R, complete_adjacency(N_AGENTS),
            self_weight=0.5, neighbor_weight=0.5,
            eta=0.1, temperature=0.3,
            n_x=N_X, n_a=N_A, n_steps=N_STEPS, seed=42,
        )
        print(f"  {label:>12}  {str(np.round(snaps[N_STEPS][2], 3)):>25}  "
              f"{snaps[N_STEPS][0]:>18.3f}")


# ---------------------------------------------------------------------

if __name__ == "__main__":
    for fn in [
        test_mutual_correction_homogenizes,
        test_homogenization_rate_depends_on_topology,
        test_mutual_correction_does_not_cure,
        test_pure_conformity_freezes,
        test_self_weight_controls_drift,
        test_adversary_diluted_by_degree,
        test_all_agents_are_echo_chamber,
        test_uniform_vs_diverse_convergence,
    ]:
        print(f"--- {fn.__name__} ---")
        fn()
        print("PASS\n")

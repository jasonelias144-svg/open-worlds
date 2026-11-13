"""
aristotle_cybernetics_c7.py — Component 7: The Asymmetric Correction.

Structural correspondence to the SelfImprover (first file, C19-20):
  SelfImprover         Didaskalia
  ------------         ----------
  External benchmark   Corrector's signal
  Propose variant      Signal an action
  Test against bench   Compare to learner's telos
  Adopt if better      Update W toward signal

Central structural claims:
  C1. A polis trained by a corrector more truthful than the polis
      improves. A corrector less truthful corrupts.
  C2. Correction speed scales with the truthfulness advantage.
  C3. Ensembles of independent correctors can beat any individual
      (Condorcet). Correlated correctors do not.
  C4. A polis trained by a truthful teacher then exposed to a
      biased teacher regresses toward the bias.

Imports from prior modules:
  optimal_action (C3), update_telos (C4), polis_truthfulness helpers (C6).
"""

from dataclasses import dataclass, field
from typing import List
import numpy as np

from aristotle_cybernetics_c3 import optimal_action
from aristotle_cybernetics_c4 import update_telos


# =====================================================================
# Corrector atoms
# =====================================================================

class Corrector:
    """Base class for an asymmetric source of corrective signal.

    A corrector supplies, at each situation, an action signal that the
    polis's learners update toward. The corrector's truthfulness is the
    fraction of situations where its signal matches the true telos.
    """

    def signal(self, x, R, n_a):
        raise NotImplementedError

    def rewards(self, x, R, n_a, k):
        """Per-commitment reward vector derived from the signal.

        Reward for commitment i is 1 if its reference matches the
        signaled action, else 0. This is the one-hot encoding of the
        corrector's choice in the commitment basis.
        """
        a = self.signal(x, R, n_a)
        return np.array([1.0 if int(R[x, i]) == a else 0.0
                         for i in range(k)])


class PerfectTeacher(Corrector):
    """A corrector whose belief is exactly W_true. Truthfulness = 1."""

    def __init__(self, W_true):
        self.W_true = np.asarray(W_true)

    def signal(self, x, R, n_a):
        return optimal_action(R[x], self.W_true[x], n_a)


class BiasedTeacher(Corrector):
    """A reliable corrector whose belief differs from W_true.

    The teacher is trustworthy (always gives its own belief) but its
    belief is wrong. This is the corruption-transmission model.
    """

    def __init__(self, W_belief):
        self.W_belief = np.asarray(W_belief)

    def signal(self, x, R, n_a):
        return optimal_action(R[x], self.W_belief[x], n_a)


class NoisyOracle(Corrector):
    """A corrector correct with probability p_true, uniformly random
    otherwise.

    p_true = 1 is a perfect teacher; p_true = 1/n_a is a random
    corrector (no information); p_true = 0 is anti-informative in
    the sense that it produces no majority signal.
    """

    def __init__(self, W_true, p_true, seed=0):
        self.W_true = np.asarray(W_true)
        self.p_true = float(p_true)
        self.rng = np.random.default_rng(seed)

    def signal(self, x, R, n_a):
        if self.rng.random() < self.p_true:
            return optimal_action(R[x], self.W_true[x], n_a)
        return int(self.rng.integers(0, n_a))


class IndependentEnsemble(Corrector):
    """Ensemble of K independent NoisyOracles, majority vote.

    Condorcet's claim (in this structural form): with K independent
    oracles each correct with probability p > 1/n_a, the majority
    signal is correct with probability higher than p. The improvement
    scales with K.
    """

    def __init__(self, W_true, p_true, K, seed=0):
        self.teachers = [
            NoisyOracle(W_true, p_true=p_true, seed=seed + i)
            for i in range(K)
        ]
        self.K = K

    def signal(self, x, R, n_a):
        signals = [t.signal(x, R, n_a) for t in self.teachers]
        counts = np.bincount(signals, minlength=n_a)
        return int(np.argmax(counts))


class CorrelatedEnsemble(Corrector):
    """Ensemble of K correctors with perfectly correlated errors.

    All K teachers make the same error draw. Majority vote is
    statistically identical to a single teacher. This is the negative
    control for Condorcet: without independence, ensembles do not help.
    """

    def __init__(self, W_true, p_true, K, seed=0):
        self.W_true = np.asarray(W_true)
        self.p_true = float(p_true)
        self.K = K
        self.rng = np.random.default_rng(seed)

    def signal(self, x, R, n_a):
        if self.rng.random() < self.p_true:
            return optimal_action(R[x], self.W_true[x], n_a)
        return int(self.rng.integers(0, n_a))


# =====================================================================
# Composite: the asymmetric training loop
# =====================================================================

@dataclass
class AsymmetricTrainingLoop:
    """Trains a polis of learners against a corrector.

    The corrector is the benchmark. Every learner updates its telos
    toward the corrector's signal. The structural claims are tested
    by inspecting the polis's behavior before and after.
    """

    corrector: Corrector
    R: np.ndarray
    n_a: int
    k: int
    eta: float = 0.15
    temperature: float = 0.3
    n_x: int = field(init=False)

    def __post_init__(self):
        self.n_x = len(self.R)

    def step(self, Ws, x):
        """One training step at situation x."""
        rewards = self.corrector.rewards(x, self.R, self.n_a, self.k)
        for i in range(len(Ws)):
            Ws[i][x] = update_telos(
                Ws[i][x], rewards,
                eta=self.eta, temperature=self.temperature,
            )

    def run(self, Ws, n_steps, seed=0):
        rng = np.random.default_rng(seed)
        for _ in range(n_steps):
            x = int(rng.integers(0, self.n_x))
            self.step(Ws, x)
        return Ws


# =====================================================================
# Metrics
# =====================================================================

def truthfulness(W, R, W_true, n_a):
    """Fraction of situations where W's action matches W_true's action."""
    n_x = len(R)
    return sum(
        1 for x in range(n_x)
        if optimal_action(R[x], W[x], n_a) ==
           optimal_action(R[x], W_true[x], n_a)
    ) / n_x


def polis_truthfulness(Ws, R, W_true, n_a):
    return float(np.mean([truthfulness(W, R, W_true, n_a) for W in Ws]))


def polis_confidence(Ws):
    """Mean max weight: how concentrated each learner's telos is."""
    return float(np.mean([W.max(axis=1).mean() for W in Ws]))


def corrector_accuracy(corrector, R, W_true, n_a, n_trials=100):
    """Expected fraction of correct signals across situations."""
    n_x = len(R)
    accs = []
    for _ in range(n_trials):
        acc = sum(
            1 for x in range(n_x)
            if corrector.signal(x, R, n_a) ==
               optimal_action(R[x], W_true[x], n_a)
        ) / n_x
        accs.append(acc)
    return float(np.mean(accs))


# =====================================================================
# Fixtures
# =====================================================================

def _fixture(seed=11):
    rng = np.random.default_rng(seed)
    n_x, k, n_a = 20, 3, 5
    R = rng.integers(0, n_a, size=(n_x, k)).astype(float)
    W_true = np.tile(np.array([0.5, 0.3, 0.2]), (n_x, 1))
    return R, W_true, n_x, k, n_a


def _uniform_polis(n_x, k, n_agents=4):
    return [np.ones((n_x, k)) / k for _ in range(n_agents)]


# =====================================================================
# Tests
# =====================================================================

def test_perfect_teacher_improves():
    """Claim C1a: a perfect teacher improves the polis to high truthfulness."""
    R, W_true, n_x, k, n_a = _fixture()
    Ws = _uniform_polis(n_x, k)
    initial = polis_truthfulness(Ws, R, W_true, n_a)
    loop = AsymmetricTrainingLoop(PerfectTeacher(W_true), R, n_a, k)
    loop.run(Ws, n_steps=3000, seed=42)
    final = polis_truthfulness(Ws, R, W_true, n_a)
    print(f"  initial truthfulness: {initial:.3f}")
    print(f"  final truthfulness:   {final:.3f}")
    assert final > 0.9, f"Should approach truth: {final}"
    assert final > initial + 0.4, f"Should improve substantially"


def test_biased_teacher_corrupts():
    """Claim C1b: a biased teacher corrupts the polis.

    The polis tracks the teacher's behavior (agreement > 0.9) but is
    disconnected from the truth.
    """
    R, W_true, n_x, k, n_a = _fixture()
    rng = np.random.default_rng(7)
    W_belief = rng.dirichlet(np.ones(k), size=n_x)
    Ws = _uniform_polis(n_x, k)
    loop = AsymmetricTrainingLoop(BiasedTeacher(W_belief), R, n_a, k)
    loop.run(Ws, n_steps=3000, seed=42)
    t_truth = polis_truthfulness(Ws, R, W_true, n_a)
    t_teacher = polis_truthfulness(Ws, R, W_belief, n_a)
    print(f"  polis truthfulness vs W_true:    {t_truth:.3f}")
    print(f"  polis agreement with teacher:    {t_teacher:.3f}")
    assert t_teacher > 0.9, f"Should track teacher: {t_teacher}"
    assert t_truth < 0.5, f"Should be corrupted: {t_truth}"


def test_partial_truth_scales():
    """Claim C2: polis confidence scales monotonically with teacher truthfulness.

    A noisy teacher produces a spread-out polis W; a clean teacher
    produces a concentrated one. Confidence is the correct metric
    here — truthfulness saturates quickly for any p > 1/n_a because
    the majority-argmax converges, but the concentration of W tracks p.
    """
    R, W_true, n_x, k, n_a = _fixture()
    print(f"  {'p_true':>8}  {'confidence':>12}  {'truthfulness':>14}")
    confidences = []
    truths = []
    for p in [0.0, 0.2, 0.4, 0.6, 0.8, 1.0]:
        Ws = _uniform_polis(n_x, k)
        loop = AsymmetricTrainingLoop(
            NoisyOracle(W_true, p_true=p, seed=42), R, n_a, k)
        loop.run(Ws, n_steps=2500, seed=7)
        conf = polis_confidence(Ws)
        truth = polis_truthfulness(Ws, R, W_true, n_a)
        print(f"  {p:>8.1f}  {conf:>12.3f}  {truth:>14.3f}")
        confidences.append(conf)
        truths.append(truth)
    # Confidence monotonic in p
    for i in range(1, len(confidences)):
        assert confidences[i] >= confidences[i-1] - 0.05, \
            f"Confidence should be monotone: {confidences}"
    # Large gap between p=0 and p=1
    assert confidences[-1] > confidences[0] + 0.3, \
        f"p=1 should dominate p=0: {confidences}"


def test_condorcet():
    """Claim C3: independent ensembles beat individual oracles;
    correlated ensembles do not.

    This is the structural argument for the plurality of teachers.
    """
    R, W_true, n_x, k, n_a = _fixture()

    single = NoisyOracle(W_true, p_true=0.6, seed=0)
    indep = IndependentEnsemble(W_true, p_true=0.6, K=9, seed=0)
    corr = CorrelatedEnsemble(W_true, p_true=0.6, K=9, seed=0)

    a_single = corrector_accuracy(single, R, W_true, n_a, n_trials=200)
    a_indep = corrector_accuracy(indep, R, W_true, n_a, n_trials=200)
    a_corr = corrector_accuracy(corr, R, W_true, n_a, n_trials=200)
    print(f"  single oracle:          {a_single:.3f}")
    print(f"  independent ensemble:   {a_indep:.3f}")
    print(f"  correlated ensemble:    {a_corr:.3f}")
    assert 0.55 < a_single < 0.65, f"Single should be ~0.6: {a_single}"
    assert a_indep > 0.7, f"Independent should improve: {a_indep}"
    assert 0.55 < a_corr < 0.65, f"Correlated should match single: {a_corr}"


def test_polis_learns_ensemble():
    """Claim C3 (continued): the polis can learn from the ensemble.

    Training against an independent ensemble produces a polis whose
    truthfulness exceeds the individual-oracle baseline.
    """
    R, W_true, n_x, k, n_a = _fixture()
    Ws = _uniform_polis(n_x, k)
    loop = AsymmetricTrainingLoop(
        IndependentEnsemble(W_true, p_true=0.6, K=9, seed=0),
        R, n_a, k)
    loop.run(Ws, n_steps=3000, seed=42)
    acc = polis_truthfulness(Ws, R, W_true, n_a)
    print(f"  polis truthfulness: {acc:.3f}")
    assert acc > 0.65, f"Should beat individual: {acc}"
    assert acc < 0.95, f"Should not be perfect: {acc}"


def test_regime_change():
    """Claim C4: polis trained by a good teacher regresses when
    exposed to a bad teacher.
    """
    R, W_true, n_x, k, n_a = _fixture()
    rng = np.random.default_rng(7)
    W_belief = rng.dirichlet(np.ones(k), size=n_x)

    Ws = _uniform_polis(n_x, k)
    # Phase 1: good teacher
    AsymmetricTrainingLoop(
        PerfectTeacher(W_true), R, n_a, k
    ).run(Ws, n_steps=2000, seed=1)
    truth_good = polis_truthfulness(Ws, R, W_true, n_a)

    # Phase 2: bad teacher
    AsymmetricTrainingLoop(
        BiasedTeacher(W_belief), R, n_a, k
    ).run(Ws, n_steps=2000, seed=2)
    truth_bad = polis_truthfulness(Ws, R, W_true, n_a)

    print(f"  truthfulness after good teacher: {truth_good:.3f}")
    print(f"  truthfulness after bad teacher:  {truth_bad:.3f}")
    assert truth_good > 0.9, f"Good phase should be high: {truth_good}"
    assert truth_bad < truth_good - 0.3, \
        f"Should regress: {truth_good} -> {truth_bad}"


# =====================================================================

if __name__ == "__main__":
    for fn in [
        test_perfect_teacher_improves,
        test_biased_teacher_corrupts,
        test_partial_truth_scales,
        test_condorcet,
        test_polis_learns_ensemble,
        test_regime_change,
    ]:
        print(f"--- {fn.__name__} ---")
        fn()
        print("PASS\n")

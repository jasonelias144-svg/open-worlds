"""
aristotle_cybernetics_c2.py
Component 2: The Virtuous Agent as a Control System (executable model).

Formal model (from NE I.7, II.1, II.5-6, VI.5, VI.8, VII.3):
  - Situation space X = {0, ..., n_x-1}
  - Action space A = {0, ..., n_a-1}
  - Hexis H: X -> A, a probability table with convex-update plasticity
    (the operator; the transfer function)
  - Reference R: X -> A (the mean relative to us; the tracking target)
  - Phronesis pi: X -> X (perception; can be perfect, noisy, adversarial)
  - Actuator: A -> A (faithful, saturating, disconnected)
  - Habituation: H <- (1-eta)*H + eta*one_hot(target)

Standard-library plus numpy. All tests produce numbers; each has a
pass/fail criterion tied to a structural claim from the NE.
"""

import numpy as np


# ---------------------------------------------------------------------
# Primitives
# ---------------------------------------------------------------------

class Hexis:
    """The operator H: X -> A. A probability table with convex update."""

    def __init__(self, n_x, n_a):
        self.n_x, self.n_a = n_x, n_a
        self.p = np.ones((n_x, n_a)) / n_a  # uniform

    def __call__(self, x):
        return int(np.argmax(self.p[x]))

    def update(self, x, target, eta):
        if target is None:
            return
        target = max(0, min(self.n_a - 1, int(target)))
        self.p[x] = (1.0 - eta) * self.p[x]
        self.p[x, target] += eta

    def confidence(self, x):
        return float(np.max(self.p[x]))

    def spread(self, x):
        """1 - max(p[x]); high when uncertain."""
        return float(1.0 - np.max(self.p[x]))


class Phronesis:
    """The sensor pi: X -> X. Perfect, noisy, or adversarial."""

    def __init__(self, n_x, noise=0.0, rng=None):
        self.n_x, self.noise = n_x, noise
        self.rng = rng or np.random.default_rng(0)

    def perceive(self, x):
        if self.rng.random() < self.noise:
            return int(self.rng.integers(0, self.n_x))
        return x


class AdversarialPhronesis(Phronesis):
    def __init__(self, n_x, adv_map, p_adv=0.5, rng=None):
        super().__init__(n_x, noise=0.0, rng=rng)
        self.adv_map = np.asarray(adv_map)
        self.p_adv = p_adv

    def perceive(self, x):
        if self.rng.random() < self.p_adv:
            return int(self.adv_map[x])
        return x


class Actuator:
    """The actuator: A -> A. Faithful, saturating, or disconnected."""

    def __init__(self, n_a, supported=None, disconnect=0.0, rng=None):
        self.n_a = n_a
        self.supported = set(supported) if supported is not None else set(range(n_a))
        self.disconnect = disconnect
        self.rng = rng or np.random.default_rng(0)

    def execute(self, a):
        if self.rng.random() < self.disconnect:
            return int(self.rng.integers(0, self.n_a))
        if a not in self.supported:
            return max(self.supported)
        return a


class Reference:
    """The mean: X -> A, as a lookup table."""

    def __init__(self, table):
        self.table = np.asarray(table, dtype=int)

    def __call__(self, x):
        return int(self.table[x])


class Agent:
    """The composite: hexis + phronesis + actuator."""

    def __init__(self, hexis, phronesis, actuator):
        self.hexis = hexis
        self.phronesis = phronesis
        self.actuator = actuator

    def intend(self, x):
        x_hat = self.phronesis.perceive(x)
        return self.hexis(x_hat)

    def act(self, x):
        a_intended = self.intend(x)
        a_executed = self.actuator.execute(a_intended)
        return a_intended, a_executed


# ---------------------------------------------------------------------
# Habituation
# ---------------------------------------------------------------------

def habituate(agent, reference, n_x, eta=0.2, n_steps=3000, rng=None):
    rng = rng or np.random.default_rng(0)
    for _ in range(n_steps):
        x = int(rng.integers(0, n_x))
        x_hat = agent.phronesis.perceive(x)
        agent.hexis.update(x_hat, reference(x), eta)


def habituate_polis(agents, reference, n_x, eta, n_steps,
                    conformity, rng=None):
    rng = rng or np.random.default_rng(0)
    for _ in range(n_steps):
        x = int(rng.integers(0, n_x))
        truth = reference(x)
        for agent in agents:
            x_hat = agent.phronesis.perceive(x)
            others = [a.hexis(x_hat) for a in agents if a is not agent]
            consensus = float(np.mean(others)) if others else float(truth)
            t = (1 - conformity) * truth + conformity * consensus
            agent.hexis.update(x_hat, int(np.floor(t + 0.5)), eta)


# ---------------------------------------------------------------------
# Utilities
# ---------------------------------------------------------------------

def match_rate(agent, reference, n_x):
    return sum(1 for x in range(n_x) if agent.hexis(x) == reference(x)) / n_x


def mean_confidence(agent, n_x):
    return float(np.mean([agent.hexis.confidence(x) for x in range(n_x)]))


def mean_spread(agent, n_x):
    return float(np.mean([agent.hexis.spread(x) for x in range(n_x)]))


# ---------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------

def test_convergence():
    """Claim: faithful sensor + faithful actuator => H converges to R."""
    n_x, n_a = 10, 5
    ref = Reference([0, 1, 2, 3, 4, 0, 1, 2, 3, 4])
    agent = Agent(Hexis(n_x, n_a), Phronesis(n_x), Actuator(n_a))
    habituate(agent, ref, n_x, eta=0.2, n_steps=3000)
    rate = match_rate(agent, ref, n_x)
    conf = mean_confidence(agent, n_x)
    print(f"  match_rate={rate:.2f}  mean_conf={conf:.3f}")
    assert rate == 1.0, f"Expected convergence, got {rate}"
    assert conf > 0.9, f"Expected confidence > 0.9, got {conf}"


def test_akrasia():
    """Claim: disconnected actuator => agent knows but cannot execute."""
    n_x, n_a = 10, 5
    ref_table = [0, 1, 2, 3, 4, 0, 1, 2, 3, 4]
    ref = Reference(ref_table)
    agent = Agent(Hexis(n_x, n_a), Phronesis(n_x),
                  Actuator(n_a, disconnect=0.0))
    habituate(agent, ref, n_x, eta=0.2, n_steps=3000)
    assert match_rate(agent, ref, n_x) == 1.0, "Training failed"

    # Replace the actuator with a disconnected one
    agent.actuator = Actuator(n_a, disconnect=1.0, rng=np.random.default_rng(7))

    intended_correct = sum(1 for x in range(n_x)
                           if agent.intend(x) == ref_table[x])
    executed_correct = sum(1 for x in range(n_x)
                           if agent.act(x)[1] == ref_table[x])
    print(f"  intended_correct={intended_correct}/{n_x}  "
          f"executed_correct={executed_correct}/{n_x}")
    assert intended_correct == n_x, "Agent should still 'know'"
    assert executed_correct < n_x, "Agent should not 'do'"


def test_noisy_sensor():
    """Claim: noisy phronesis => learned hexis is less confident."""
    n_x, n_a = 10, 5
    rng = np.random.default_rng(42)
    ref = Reference(rng.integers(0, n_a, size=n_x).tolist())

    def run(noise, seed):
        agent = Agent(
            Hexis(n_x, n_a),
            Phronesis(n_x, noise=noise, rng=np.random.default_rng(seed + 1)),
            Actuator(n_a),
        )
        habituate(agent, ref, n_x, eta=0.3, n_steps=3000,
                  rng=np.random.default_rng(seed + 2))
        return mean_confidence(agent, n_x)

    c_clean = run(noise=0.0, seed=1)
    c_noisy = run(noise=0.4, seed=1)
    print(f"  conf_clean={c_clean:.3f}  conf_noisy={c_noisy:.3f}")
    assert c_clean > 0.9, f"Clean should be confident: {c_clean}"
    assert c_noisy < c_clean, f"Noisy should reduce confidence"


def test_tragedy():
    """Claim: infeasible reference => intended != executed."""
    n_x, n_a = 6, 4
    ref = Reference([0, 1, 2, 3, 2, 1])
    agent = Agent(
        Hexis(n_x, n_a),
        Phronesis(n_x),
        Actuator(n_a, supported={0, 1, 2}),  # 3 is unreachable
    )
    habituate(agent, ref, n_x, eta=0.3, n_steps=3000)

    x = 3
    intended, executed = agent.act(x)
    print(f"  At x={x} (ref=3): intended={intended}, executed={executed}")
    assert intended == 3, f"Agent should intend 3, got {intended}"
    assert executed == 2, f"Actuator should saturate at 2, got {executed}"


def test_adversary():
    """Claim: adversarial sensor => agent learns the adversary's map."""
    n_x, n_a = 10, 5
    ref = Reference([0, 1, 2, 3, 4, 0, 1, 2, 3, 4])
    adv_map = [1, 0, 3, 2, 5, 4, 7, 6, 9, 8]

    def run(p_adv, seed):
        agent = Agent(
            Hexis(n_x, n_a),
            AdversarialPhronesis(n_x, adv_map, p_adv=p_adv,
                                 rng=np.random.default_rng(seed + 1)),
            Actuator(n_a),
        )
        habituate(agent, ref, n_x, eta=0.3, n_steps=3000,
                  rng=np.random.default_rng(seed + 2))
        return match_rate(agent, ref, n_x)

    r_clean = run(p_adv=0.0, seed=1)
    r_adv = run(p_adv=0.8, seed=1)
    print(f"  match_clean={r_clean:.2f}  match_adversarial={r_adv:.2f}")
    assert r_clean == 1.0, f"Clean should match truth: {r_clean}"
    assert r_adv < 0.8, f"Adversary should corrupt: {r_adv}"


def test_polis():
    """Claim: coupling reduces accuracy; full coupling freezes initial state."""
    n_x, n_a = 10, 5
    n_agents = 5
    ref = Reference([0, 1, 2, 3, 4, 0, 1, 2, 3, 4])

    def run(conformity, seed):
        agents = [
            Agent(Hexis(n_x, n_a),
                  Phronesis(n_x, rng=np.random.default_rng(seed + i)),
                  Actuator(n_a))
            for i in range(n_agents)
        ]
        habituate_polis(agents, ref, n_x, eta=0.3, n_steps=3000,
                        conformity=conformity,
                        rng=np.random.default_rng(seed + 99))
        return float(np.mean([match_rate(a, ref, n_x) for a in agents]))

    r0 = run(0.0, seed=1)
    r5 = run(0.5, seed=1)
    r10 = run(1.0, seed=1)
    print(f"  conformity 0.0: match={r0:.2f}")
    print(f"  conformity 0.5: match={r5:.2f}")
    print(f"  conformity 1.0: match={r10:.2f}")
    assert r0 > 0.9, f"Independent agents should learn truth: {r0}"
    assert r10 < r0, f"Full conformity should be worse: {r10}"


# ---------------------------------------------------------------------

if __name__ == "__main__":
    for fn in [test_convergence, test_akrasia, test_noisy_sensor,
               test_tragedy, test_adversary, test_polis]:
        print(f"--- {fn.__name__} ---")
        fn()
        print("PASS\n")

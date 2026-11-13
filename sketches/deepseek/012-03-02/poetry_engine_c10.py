"""
poetry_engine_c10.py — Component 10: Revision through feedback.

The engine learns which transformations produce accepted revisions,
and biases future proposals toward the successful ones.

Same loop as C7/C8, but the composition policy is learned across poems.

Depends on Components 1-9.
"""

import copy
import random
from dataclasses import dataclass
from typing import Dict, List, Optional

from poetry_engine_c5 import (
    VoiceSpecification, Fragment, FRAGMENTS,
    VOICE_CLINICAL, VOICE_GHOST, VOICE_MANY,
)
from poetry_engine_c7 import (
    FragmentDeveloper, DraftStanza, EngineState, is_native,
    Transformation,
)
from poetry_engine_c8 import (
    ProductiveRestEngine, RestMode, RestPolicy, RestOutcome,
    StanzaScorerV2, StanzaScoreV2, MAX_LINES,
)


# =====================================================================
# Atom: TransformationPolicy
# =====================================================================

class TransformationPolicy:
    """Beta-Bernoulli bandit over transformations, per voice.

    Each transformation tracks (successes, failures). Sampling is
    proportional to successes+1 (Laplace). On accept: successes += 1.
    On reject: failures += 1.
    """

    def __init__(self, voice_name: str):
        self.voice_name = voice_name
        self.stats: Dict[Transformation, List[int]] = {
            t: [0, 0] for t in Transformation
        }

    def _weight(self, t: Transformation) -> float:
        return self.stats[t][0] + 1.0  # Laplace

    def sample(self, rng: random.Random) -> Transformation:
        total = sum(self._weight(t) for t in Transformation)
        r = rng.random() * total
        cum = 0.0
        for t in Transformation:
            cum += self._weight(t)
            if r < cum:
                return t
        return list(Transformation)[-1]

    def update(self, t: Transformation, success: bool):
        if success:
            self.stats[t][0] += 1
        else:
            self.stats[t][1] += 1

    def distribution(self) -> Dict[Transformation, float]:
        total = sum(self._weight(t) for t in Transformation)
        return {t: self._weight(t) / total for t in Transformation}

    def best(self) -> Transformation:
        return max(Transformation, key=self._weight)

    def success_rate(self, t: Transformation) -> float:
        s, f = self.stats[t]
        return s / (s + f) if (s + f) > 0 else 0.0

    def attempts(self, t: Transformation) -> int:
        s, f = self.stats[t]
        return s + f


# =====================================================================
# Composite: FeedbackRevisionEngine
# =====================================================================

class FeedbackRevisionEngine(ProductiveRestEngine):
    """C8's engine, with the TransformationPolicy steering SWAP proposals.

    The SWAP branch samples a transformation from the policy, then
    picks a variant of that transformation. The policy is updated on
    accept (reward) and reject (penalize). ADD/REPLACE proposals do
    not update the policy (they don't use a transformation).
    """

    def __init__(self, voice: VoiceSpecification,
                 fragments: List[Fragment],
                 seed: int = 0,
                 budget: int = 40,
                 patience: int = 4,
                 max_rests: int = 6,
                 rest_policy: Optional[RestPolicy] = None,
                 transform_policy: Optional[TransformationPolicy] = None):
        super().__init__(
            voice=voice, fragments=fragments, seed=seed,
            budget=budget, patience=patience,
            max_rests=max_rests, rest_policy=rest_policy,
        )
        self.transform_policy = (
            transform_policy or TransformationPolicy(voice.name)
        )
        self._last_transformation: Optional[Transformation] = None
        self._rebuild_pool_and_index()

    def _rebuild_pool_and_index(self):
        """Build pool and transformation index from the fragments."""
        self.pool = {}
        self.transformation_index = {}
        for f in self.fragments:
            if self.voice.name not in getattr(f, 'voice_affinity', ()):
                continue
            variants = self.developer.develop(f)
            wrapped = [Fragment(
                text=f.text, schemas=f.schemas,
                arc_position=f.arc_position,
                voice_affinity=f.voice_affinity,
            )]
            for v in variants:
                wrapped.append(Fragment(
                    text=v.text, schemas=v.schemas,
                    arc_position=v.arc_position,
                    voice_affinity=v.voice_affinity,
                ))
                self.transformation_index[v.text] = v.transformation
            self.pool[f.text] = wrapped
        self._rebuild_index()

    def _apply_rest(self, mode: RestMode) -> str:
        if mode == RestMode.REGENERATE:
            new_seed = self.rng.randint(0, 10**9)
            new_dev = FragmentDeveloper(seed=new_seed)
            for f in self.fragments:
                if self.voice.name not in getattr(f, 'voice_affinity', ()):
                    continue
                new_variants = new_dev.develop(f)
                if f.text not in self.pool:
                    self.pool[f.text] = [Fragment(
                        text=f.text, schemas=f.schemas,
                        arc_position=f.arc_position,
                        voice_affinity=f.voice_affinity,
                    )]
                existing = {v.text for v in self.pool[f.text]}
                for v in new_variants:
                    if v.text not in existing:
                        self.pool[f.text].append(Fragment(
                            text=v.text, schemas=v.schemas,
                            arc_position=v.arc_position,
                            voice_affinity=v.voice_affinity,
                        ))
                        self.transformation_index[v.text] = v.transformation
            self._rebuild_index()
            return f"regenerate (pool={len(self.fragment_index)})"
        return super()._apply_rest(mode)

    def _propose_revision(self, draft):
        self._last_transformation = None
        all_pool_lines = [
            v.text for variants in self.pool.values()
            for v in variants if is_native(v.text)
        ]
        draft_lines = {line for s in draft for line in s.lines if line}
        unused = [t for t in all_pool_lines if t not in draft_lines]
        r = self.rng.random()

        # ADD (not a transformation)
        if r < 0.35 and unused and len(draft_lines) < MAX_LINES:
            new_draft = copy.deepcopy(draft)
            if not new_draft:
                return [DraftStanza(lines=[self.rng.choice(unused)])]
            new_line = self.rng.choice(unused)
            s_idx = self.rng.randrange(len(new_draft))
            new_draft[s_idx].lines.append(new_line)
            return new_draft

        # REPLACE (not a transformation)
        if r < 0.7 and unused and draft:
            new_draft = copy.deepcopy(draft)
            new_line = self.rng.choice(unused)
            s_idx = self.rng.randrange(len(new_draft))
            stanza = new_draft[s_idx]
            if not stanza.lines:
                return draft
            l_idx = self.rng.randrange(len(stanza.lines))
            stanza.lines[l_idx] = new_line
            return new_draft

        # SWAP (policy-driven)
        if not draft:
            return draft
        new_draft = copy.deepcopy(draft)
        s_idx = self.rng.randrange(len(new_draft))
        stanza = new_draft[s_idx]
        if not stanza.lines:
            return draft
        l_idx = self.rng.randrange(len(stanza.lines))
        current = stanza.lines[l_idx]

        # Find the family
        family = None
        for variants in self.pool.values():
            if any(v.text == current for v in variants):
                family = variants
                break
        if not family:
            return draft

        # Sample a transformation from the policy
        transform = self.transform_policy.sample(self.rng)

        # Candidates matching that transformation
        candidates = [
            v.text for v in family
            if v.text != current
            and is_native(v.text)
            and self.transformation_index.get(v.text) == transform
        ]

        if not candidates:
            # Fallback: any native candidate
            candidates = [
                v.text for v in family
                if v.text != current and is_native(v.text)
            ]
            transform = None  # policy not the reason for this choice

        if not candidates:
            return draft

        new_line = self.rng.choice(candidates)
        stanza.lines[l_idx] = new_line
        self._last_transformation = transform
        return new_draft

    def run(self) -> EngineState:
        draft = self._initial_draft()
        initial_score = self.scorer.score(
            draft, self.fragment_index).total()
        state = EngineState(draft=draft, score=initial_score)
        state.record("initial", score=round(initial_score, 3))

        stall = 0
        rests = 0
        pending_rest_mode: Optional[RestMode] = None
        pending_rest_score = 0.0
        pending_rest_cycle = 0
        accepts_since_rest = 0

        while state.productive_cycles < self.budget:
            if stall >= self.patience:
                if pending_rest_mode is not None:
                    outcome = RestOutcome(
                        mode=pending_rest_mode,
                        productive_before=pending_rest_cycle,
                        accepted_after=accepts_since_rest,
                        score_before=pending_rest_score,
                        score_after=state.score,
                    )
                    self.rest_policy.update(
                        pending_rest_mode, outcome.success)
                    self.rest_history.append(outcome)
                    state.record("rest_outcome",
                                  mode=pending_rest_mode.value,
                                  success=outcome.success,
                                  delta=round(outcome.score_delta, 3))
                    pending_rest_mode = None

                if rests >= self.max_rests:
                    state.record("converged",
                                  score=round(state.score, 3))
                    break

                mode = self.rest_policy.sample(self.rng)
                desc = self._apply_rest(mode)
                rests += 1
                state.rest_cycles += 1
                state.record("rest", mode=mode.value, desc=desc)
                pending_rest_mode = mode
                pending_rest_score = state.score
                pending_rest_cycle = state.productive_cycles
                accepts_since_rest = 0
                stall = 0
                continue

            candidate = self._propose_revision(draft)
            candidate_score = self.scorer.score(
                candidate, self.fragment_index).total()

            if candidate_score > state.score + 1e-9:
                draft = candidate
                state.draft = candidate
                state.score = candidate_score
                stall = 0
                accepts_since_rest += 1
                state.record("accept",
                              cycle=state.productive_cycles,
                              score=round(candidate_score, 3))
                if self._last_transformation is not None:
                    self.transform_policy.update(
                        self._last_transformation, True)
                    state.record("policy_reward",
                                  transformation=self._last_transformation.value)
            else:
                stall += 1
                state.record("reject",
                              cycle=state.productive_cycles,
                              stall=stall)
                if self._last_transformation is not None:
                    self.transform_policy.update(
                        self._last_transformation, False)
                    state.record("policy_penalize",
                                  transformation=self._last_transformation.value)
            state.productive_cycles += 1

        return state


# =====================================================================
# Composite: CrossPoemFeedbackLoop
# =====================================================================

class CrossPoemFeedbackLoop:
    """Runs many poems, sharing one TransformationPolicy across them.

    Poems are composed in sequence. The policy from poem N is the
    starting point for poem N+1. The state of the policy reflects
    accumulated experience with this voice.
    """

    def __init__(self, voice: VoiceSpecification,
                 fragments: List[Fragment],
                 seed: int = 0,
                 n_poems: int = 10,
                 budget: int = 30,
                 patience: int = 3,
                 max_rests: int = 4):
        self.voice = voice
        self.fragments = fragments
        self.rng = random.Random(seed)
        self.n_poems = n_poems
        self.budget = budget
        self.patience = patience
        self.max_rests = max_rests
        self.transform_policy = TransformationPolicy(voice.name)
        self.rest_policy = RestPolicy(voice.name)
        self.results: List[EngineState] = []
        self.policy_history: List[Dict[Transformation, List[int]]] = []

    def run(self) -> List[EngineState]:
        for _ in range(self.n_poems):
            engine = FeedbackRevisionEngine(
                voice=self.voice,
                fragments=self.fragments,
                seed=self.rng.randint(0, 10**9),
                budget=self.budget,
                patience=self.patience,
                max_rests=self.max_rests,
                rest_policy=self.rest_policy,
                transform_policy=self.transform_policy,
            )
            state = engine.run()
            self.results.append(state)
            self.policy_history.append(
                {t: list(v) for t, v in self.transform_policy.stats.items()})
        return self.results

    def mean_score(self) -> float:
        if not self.results:
            return 0.0
        return sum(s.score for s in self.results) / len(self.results)


# =====================================================================
# Comparison helper
# =====================================================================

def compare_baseline_vs_learned(
    voice: VoiceSpecification,
    fragments: List[Fragment],
    n_poems: int = 8,
    seed_base: int = 0,
    budget: int = 30,
    patience: int = 3,
    max_rests: int = 3,
) -> Dict:
    """Run baseline (C8) and learned (C10) on the same poem sequence."""
    baseline_scores: List[float] = []
    for i in range(n_poems):
        engine = ProductiveRestEngine(
            voice=voice, fragments=fragments,
            seed=seed_base + i, budget=budget,
            patience=patience, max_rests=max_rests,
        )
        state = engine.run()
        baseline_scores.append(state.score)

    shared_transform = TransformationPolicy(voice.name)
    shared_rest = RestPolicy(voice.name)
    learned_scores: List[float] = []
    for i in range(n_poems):
        engine = FeedbackRevisionEngine(
            voice=voice, fragments=fragments,
            seed=seed_base + i, budget=budget,
            patience=patience, max_rests=max_rests,
            rest_policy=shared_rest,
            transform_policy=shared_transform,
        )
        state = engine.run()
        learned_scores.append(state.score)

    baseline_mean = sum(baseline_scores) / len(baseline_scores)
    learned_mean = sum(learned_scores) / len(learned_scores)
    return {
        "voice": voice.name,
        "n_poems": n_poems,
        "baseline_scores": baseline_scores,
        "learned_scores": learned_scores,
        "baseline_mean": baseline_mean,
        "learned_mean": learned_mean,
        "delta": learned_mean - baseline_mean,
        "final_policy": {
            t.value: list(shared_transform.stats[t])
            for t in Transformation
        },
    }

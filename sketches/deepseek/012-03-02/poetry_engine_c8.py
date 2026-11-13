"""
poetry_engine_c8.py — Component 8: Rest as meta-work.

Rest modes mutate the search space, not the search position.
The RestPolicy learns which mode works for which voice.

Depends on Components 1-7.
"""

import copy
import random
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Set, Tuple

from poetry_engine_c5 import (
    VoiceSpecification, NativeSchema, Fragment, FRAGMENTS,
    VOICE_CLINICAL, VOICE_GHOST, VOICE_MANY,
)
from poetry_engine_c7 import (
    FragmentDeveloper, DraftStanza, EngineState,
    is_native,
)


MAX_LINES = 8  # engine grows the draft until capped


# =====================================================================
# Atom 1: RestMode
# =====================================================================

class RestMode(Enum):
    """A meta-work strategy."""
    REGENERATE = "regenerate"
    RESEED = "reseed"
    RESHUFFLE = "reshuffle"
    EXPAND_PATIENCE = "expand_patience"


# =====================================================================
# Atom 2: RestOutcome
# =====================================================================

@dataclass
class RestOutcome:
    mode: RestMode
    productive_before: int
    accepted_after: int
    score_before: float
    score_after: float

    @property
    def success(self) -> bool:
        return self.accepted_after > 0

    @property
    def score_delta(self) -> float:
        return self.score_after - self.score_before


# =====================================================================
# Atom 3: RestPolicy (Beta-Bernoulli bandit)
# =====================================================================

class RestPolicy:
    """Learned distribution over rest modes, per voice."""

    def __init__(self, voice_name: str):
        self.voice_name = voice_name
        self.stats: Dict[RestMode, List[int]] = {
            m: [0, 0] for m in RestMode
        }

    def sample(self, rng: random.Random) -> RestMode:
        weights = [self.stats[m][0] + 1 for m in RestMode]
        total = sum(weights)
        r = rng.random() * total
        cum = 0.0
        for m, w in zip(RestMode, weights):
            cum += w
            if r < cum:
                return m
        return list(RestMode)[-1]

    def update(self, mode: RestMode, success: bool):
        if success:
            self.stats[mode][0] += 1
        else:
            self.stats[mode][1] += 1

    def best_mode(self) -> RestMode:
        return max(RestMode, key=lambda m: self.stats[m][0])

    def distribution(self) -> Dict[RestMode, float]:
        weights = [self.stats[m][0] + 1 for m in RestMode]
        total = sum(weights)
        return {m: w / total for m, w in zip(RestMode, weights)}


# =====================================================================
# StanzaScorerV2: coverage + schema diversity
# =====================================================================

@dataclass
class StanzaScoreV2:
    foregrounding: float
    native_purity: float
    voice_consistency: float
    coverage: float
    schema_diversity: float

    def total(self) -> float:
        return (self.foregrounding + self.native_purity
                + self.voice_consistency + self.coverage
                + self.schema_diversity) / 5.0


def _line_similarity(a: str, b: str) -> float:
    wa = set(a.lower().split())
    wb = set(b.lower().split())
    if not wa or not wb:
        return 0.0
    return len(wa & wb) / len(wa | wb)


class StanzaScorerV2:
    """Adds coverage + schema diversity to C7's scorer."""

    def __init__(self, voice: VoiceSpecification,
                 coverage_cap: int = 6,
                 schema_cap: int = 3):
        self.voice = voice
        self.coverage_cap = coverage_cap
        self.schema_cap = schema_cap

    def score(self, stanzas: List[DraftStanza],
              fragment_index: Dict[str, Fragment]) -> StanzaScoreV2:
        all_lines = [line for s in stanzas for line in s.all_lines()
                     if line]
        if not all_lines:
            return StanzaScoreV2(0, 0, 0, 0, 0)
        n = len(all_lines)

        # Foregrounding via average pairwise word similarity
        if n < 2:
            fg = 1.0
        else:
            sims = []
            for i in range(n):
                for j in range(i + 1, n):
                    sims.append(_line_similarity(
                        all_lines[i], all_lines[j]))
            fg = max(0.0, 1.0 - 3.0 * sum(sims) / len(sims))

        # Native purity
        native = sum(1 for line in all_lines if is_native(line)) / n

        # Voice consistency
        consistent = 0
        for line in all_lines:
            f = fragment_index.get(line)
            if f is None or not getattr(f, 'voice_affinity', ()):
                consistent += 1
            elif self.voice.name in f.voice_affinity:
                consistent += 1
        voice_score = consistent / n

        # Coverage
        coverage = min(1.0, n / self.coverage_cap)

        # Schema diversity
        schemas: Set[str] = set()
        for line in all_lines:
            f = fragment_index.get(line)
            if f:
                schemas.update(s.value for s in f.schemas)
        schema_div = min(1.0, len(schemas) / self.schema_cap)

        return StanzaScoreV2(fg, native, voice_score,
                              coverage, schema_div)


# =====================================================================
# ProductiveRestEngine
# =====================================================================

class ProductiveRestEngine:
    """C7's engine, with real rest modes."""

    def __init__(self, voice: VoiceSpecification,
                 fragments: List[Fragment],
                 seed: int = 0,
                 budget: int = 40,
                 patience: int = 4,
                 max_rests: int = 6,
                 rest_policy: Optional[RestPolicy] = None):
        self.voice = voice
        self.fragments = fragments
        self.rng = random.Random(seed)
        self.budget = budget
        self.patience = patience
        self.max_rests = max_rests
        self.rest_policy = rest_policy or RestPolicy(voice.name)
        self.scorer = StanzaScorerV2(voice)
        self.developer = FragmentDeveloper(seed=seed)
        self.pool = self.developer.develop_library(
            fragments, voice.name)
        self._rebuild_index()
        self.rest_history: List[RestOutcome] = []

    def _rebuild_index(self):
        self.fragment_index: Dict[str, Fragment] = {}
        for variants in self.pool.values():
            for v in variants:
                self.fragment_index[v.text] = v

    def _initial_draft(self) -> List[DraftStanza]:
        """Start minimal — one line. Engine grows it."""
        all_sources = [v[0].text for v in self.pool.values() if v]
        if not all_sources:
            return []
        return [DraftStanza(lines=[all_sources[0]])]

    def _propose_revision(self, draft: List[DraftStanza]
                           ) -> List[DraftStanza]:
        all_pool_lines = [v.text for variants in self.pool.values()
                          for v in variants if is_native(v.text)]
        draft_lines = {line for s in draft for line in s.lines if line}
        unused = [t for t in all_pool_lines if t not in draft_lines]

        r = self.rng.random()

        # ADD (grow the draft)
        if r < 0.35 and unused and len(draft_lines) < MAX_LINES:
            new_draft = copy.deepcopy(draft)
            if not new_draft:
                return [DraftStanza(lines=[self.rng.choice(unused)])]
            new_line = self.rng.choice(unused)
            s_idx = self.rng.randrange(len(new_draft))
            new_draft[s_idx].lines.append(new_line)
            return new_draft

        # REPLACE (swap an existing line for an unused one)
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

        # SWAP within family (C7 behavior)
        if not draft:
            return draft
        new_draft = copy.deepcopy(draft)
        s_idx = self.rng.randrange(len(new_draft))
        stanza = new_draft[s_idx]
        if not stanza.lines:
            return draft
        l_idx = self.rng.randrange(len(stanza.lines))
        current = stanza.lines[l_idx]
        family = None
        for variants in self.pool.values():
            if any(v.text == current for v in variants):
                family = variants
                break
        if not family:
            return draft
        candidates = [v.text for v in family
                      if v.text != current and is_native(v.text)]
        if not candidates:
            return draft
        stanza.lines[l_idx] = self.rng.choice(candidates)
        return new_draft

    def _apply_rest(self, mode: RestMode) -> str:
        if mode == RestMode.REGENERATE:
            new_seed = self.rng.randint(0, 10**9)
            new_dev = FragmentDeveloper(seed=new_seed)
            new_pool = new_dev.develop_library(
                self.fragments, self.voice.name)
            # Merge — preserve old variants
            for src, variants in new_pool.items():
                if src in self.pool:
                    existing = {v.text for v in self.pool[src]}
                    for v in variants:
                        if v.text not in existing:
                            self.pool[src].append(v)
                else:
                    self.pool[src] = list(variants)
            self._rebuild_index()
            return f"regenerate (pool={len(self.fragment_index)})"

        if mode == RestMode.RESEED:
            self.rng = random.Random(self.rng.randint(0, 10**9))
            return "reseed (new rng)"

        if mode == RestMode.RESHUFFLE:
            for src in self.pool:
                self.pool[src] = list(reversed(self.pool[src]))
            self._rebuild_index()
            return "reshuffle"

        if mode == RestMode.EXPAND_PATIENCE:
            self.patience += 2
            return f"expand_patience (patience={self.patience})"

        return "unknown"

    def run(self) -> EngineState:
        draft = self._initial_draft()
        initial_score = self.scorer.score(draft, self.fragment_index).total()
        state = EngineState(draft=draft, score=initial_score)
        state.record("initial", score=round(initial_score, 3))

        stall = 0
        rests = 0
        pending_rest_mode: Optional[RestMode] = None
        pending_rest_score = 0.0
        pending_rest_cycle = 0
        accepts_since_rest = 0

        while state.productive_cycles < self.budget:
            # Rest evaluation
            if stall >= self.patience:
                if pending_rest_mode is not None:
                    outcome = RestOutcome(
                        mode=pending_rest_mode,
                        productive_before=pending_rest_cycle,
                        accepted_after=accepts_since_rest,
                        score_before=pending_rest_score,
                        score_after=state.score,
                    )
                    self.rest_policy.update(pending_rest_mode,
                                             outcome.success)
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

            # Productive cycle
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
            else:
                stall += 1
                state.record("reject",
                              cycle=state.productive_cycles,
                              stall=stall)
            state.productive_cycles += 1

        return state


# =====================================================================
# RestLearningLoop
# =====================================================================

class RestLearningLoop:
    """Runs many poems in a voice; policy is shared and updated."""

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
        self.policy = RestPolicy(voice.name)
        self.results: List[EngineState] = []
        self.all_rest_outcomes: List[RestOutcome] = []

    def run(self) -> List[EngineState]:
        for _ in range(self.n_poems):
            engine = ProductiveRestEngine(
                voice=self.voice,
                fragments=self.fragments,
                seed=self.rng.randint(0, 10**9),
                budget=self.budget,
                patience=self.patience,
                max_rests=self.max_rests,
                rest_policy=self.policy,
            )
            state = engine.run()
            self.results.append(state)
            self.all_rest_outcomes.extend(engine.rest_history)
        return self.results

    def observed_success_rate(self) -> Dict[RestMode, float]:
        attempts: Dict[RestMode, List[bool]] = {
            m: [] for m in RestMode
        }
        for o in self.all_rest_outcomes:
            attempts[o.mode].append(o.success)
        rates: Dict[RestMode, float] = {}
        for m, xs in attempts.items():
            if xs:
                rates[m] = sum(xs) / len(xs)
            else:
                rates[m] = 0.0
        return rates

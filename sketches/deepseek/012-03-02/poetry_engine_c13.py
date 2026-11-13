"""
poetry_engine_c13.py — Component 13: The development spiral.

The multi-sitting version of C9. A collection is not composed in
one pass — it is developed over many cycles of writing, resting,
pruning, revising, resting again.

Depends on Components 1-10.
"""

import copy
import random
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Tuple

from poetry_engine_c5 import (
    VoiceSpecification, Fragment, FRAGMENTS,
    VOICE_CLINICAL, VOICE_GHOST, VOICE_MANY,
)
from poetry_engine_c7 import DraftStanza, is_native
from poetry_engine_c8 import (
    ProductiveRestEngine, RestPolicy, StanzaScoreV2,
)
from poetry_engine_c9 import (
    CollectionPoem, Collection, CollectionArcAnalyzer,
    CollectionForegroundingMonitor, CrossPoemRefrainAnalyzer,
    build_fragment_index,
)


# =====================================================================
# Atom 1: PhaseType
# =====================================================================

class PhaseType(Enum):
    COMPOSE = "compose"
    REPLACE = "replace"
    PRUNE = "prune"
    REVISE = "revise"
    REST = "rest"


# =====================================================================
# Atom 2: Snapshot
# =====================================================================

@dataclass
class Snapshot:
    phase_index: int
    phase_type: str
    n_poems: int
    collection_score: float
    arc_type: str
    refrain_delta: float
    weakest_poem: Optional[str] = None
    sample_lines: List[str] = field(default_factory=list)
    notes: str = ""

    def report(self) -> str:
        base = (f"#{self.phase_index} [{self.phase_type}]: "
                f"{self.n_poems} poems, "
                f"score={self.collection_score:.3f}, "
                f"arc={self.arc_type}, "
                f"delta={self.refrain_delta:.2f}")
        if self.weakest_poem:
            base += f", weakest={self.weakest_poem}"
        if self.notes:
            base += f" — {self.notes}"
        return base


# =====================================================================
# Composite: CollectionDevelopmentSpiral
# =====================================================================

class CollectionDevelopmentSpiral:
    """Develop a collection over multiple cycles of writing and rest."""

    def __init__(self,
                 voices: List[VoiceSpecification],
                 fragments: List[Fragment],
                 refrain_text: str,
                 seed: int = 0,
                 target_poems: int = 6,
                 weak_threshold: float = 0.90,
                 redundant_threshold: float = 0.5,
                 n_cycles: int = 5,
                 budget_per_poem: int = 15,
                 patience_per_poem: int = 3,
                 max_rests_per_poem: int = 2):
        if not voices:
            raise ValueError("Spiral needs at least one voice")
        self.voices = list(voices)
        self.fragments = fragments
        self.refrain_text = refrain_text
        self.rng = random.Random(seed)
        self.target_poems = target_poems
        self.weak_threshold = weak_threshold
        self.redundant_threshold = redundant_threshold
        self.n_cycles = n_cycles
        self.budget_per_poem = budget_per_poem
        self.patience_per_poem = patience_per_poem
        self.max_rests_per_poem = max_rests_per_poem

        self.poems: List[CollectionPoem] = []
        self.snapshots: List[Snapshot] = []
        self.fragment_index = build_fragment_index(fragments)
        self.rest_policies: Dict[str, RestPolicy] = {}
        self._next_voice_index = 0

    # -- composition --------------------------------------------------

    def _compose_one(self, voice: VoiceSpecification,
                     budget_override: Optional[int] = None,
                     starting_draft: Optional[List[DraftStanza]] = None
                     ) -> CollectionPoem:
        if voice.name not in self.rest_policies:
            self.rest_policies[voice.name] = RestPolicy(voice.name)
        budget = budget_override or self.budget_per_poem
        engine = ProductiveRestEngine(
            voice=voice,
            fragments=self.fragments,
            seed=self.rng.randint(0, 10**9),
            budget=budget,
            patience=self.patience_per_poem,
            max_rests=self.max_rests_per_poem,
            rest_policy=self.rest_policies[voice.name],
        )
        if starting_draft is not None:
            engine._initial_draft = (
                lambda sd=copy.deepcopy(starting_draft):
                    copy.deepcopy(sd))
        state = engine.run()
        score = engine.scorer.score(state.draft, engine.fragment_index)
        poem = CollectionPoem(
            name=f"Poem {len(self.poems) + 1} ({voice.name})",
            voice=voice,
            stanzas=state.draft,
            score=score,
            history=state.history,
            unfinished=True,
        )
        self._inject_refrain(poem)
        return poem

    def _inject_refrain(self, poem: CollectionPoem):
        if not self.refrain_text:
            return
        if any(self.refrain_text.lower() in line.lower()
               for line in poem.all_lines()):
            return
        if poem.stanzas:
            poem.stanzas[-1].refrain = self.refrain_text
        else:
            poem.stanzas.append(DraftStanza(
                lines=[], refrain=self.refrain_text))

    def _next_voice(self) -> VoiceSpecification:
        voice = self.voices[self._next_voice_index % len(self.voices)]
        self._next_voice_index += 1
        return voice

    # -- diagnostics --------------------------------------------------

    def _build_collection(self) -> Collection:
        return Collection(
            name="Spiral Collection",
            poems=list(self.poems),
            refrain=self.refrain_text,
        )

    def _collection_score(self) -> float:
        if not self.poems:
            return 0.0
        return sum(p.score.total() for p in self.poems) / len(self.poems)

    def _find_weakest_poem(self) -> Optional[CollectionPoem]:
        if not self.poems:
            return None
        return min(self.poems, key=lambda p: p.score.total())

    def _find_redundant_pair(self) -> Optional[Tuple[int, int]]:
        for i in range(1, len(self.poems)):
            a = set(self.poems[i - 1].all_lines())
            b = set(self.poems[i].all_lines())
            if not a or not b:
                continue
            overlap = len(a & b) / min(len(a), len(b))
            if overlap > self.redundant_threshold:
                return (i - 1, i)
        return None

    def _record_snapshot(self, phase_type: PhaseType, notes: str = ""):
        coll = self._build_collection()
        arc = "empty"
        delta = 0.0
        if coll.poems:
            arc = CollectionArcAnalyzer(coll).classify().value
            occurrences = CrossPoemRefrainAnalyzer(
                self.fragment_index).find_occurrences(
                coll, self.refrain_text) if self.refrain_text else []
            delta = (CrossPoemRefrainAnalyzer(self.fragment_index)
                     .mean_delta(occurrences)) if occurrences else 0.0
        weakest = self._find_weakest_poem()
        sample = [p.all_lines()[0] for p in coll.poems
                  if p.all_lines()]
        self.snapshots.append(Snapshot(
            phase_index=len(self.snapshots),
            phase_type=phase_type.value,
            n_poems=len(coll.poems),
            collection_score=self._collection_score(),
            arc_type=arc,
            refrain_delta=delta,
            weakest_poem=weakest.name if weakest else None,
            sample_lines=sample,
            notes=notes,
        ))

    # -- phases -------------------------------------------------------

    def _rest_phase(self, cycle: int):
        self._record_snapshot(PhaseType.REST,
                               f"cycle {cycle}: settled")

    def _act_phase(self, cycle: int):
        weakest = self._find_weakest_poem()

        # Priority 1: REPLACE weak poem at double budget
        if weakest and weakest.score.total() < self.weak_threshold:
            new_poem = self._compose_one(
                weakest.voice,
                budget_override=self.budget_per_poem * 2,
            )
            new_poem.name = weakest.name
            idx = self.poems.index(weakest)
            self.poems[idx] = new_poem
            self._record_snapshot(
                PhaseType.REPLACE,
                f"replaced {weakest.name} "
                f"({weakest.score.total():.3f} → "
                f"{new_poem.score.total():.3f})")
            return

        # Priority 2: PRUNE redundant
        redundant = self._find_redundant_pair()
        if redundant is not None:
            removed = self.poems.pop(redundant[1])
            self._record_snapshot(
                PhaseType.PRUNE,
                f"pruned {removed.name} (redundant)")
            return

        # Priority 3: COMPOSE new if below target
        if len(self.poems) < self.target_poems:
            voice = self._next_voice()
            new_poem = self._compose_one(voice)
            self.poems.append(new_poem)
            self._record_snapshot(
                PhaseType.COMPOSE,
                f"added {new_poem.name}")
            return

        # Priority 4: REVISE weakest from its own draft
        if weakest and weakest.score.total() < 1.0:
            new_poem = self._compose_one(
                weakest.voice,
                budget_override=self.budget_per_poem * 2,
                starting_draft=weakest.stanzas,
            )
            if new_poem.score.total() > weakest.score.total() + 1e-9:
                idx = self.poems.index(weakest)
                new_poem.name = weakest.name
                self.poems[idx] = new_poem
                self._record_snapshot(
                    PhaseType.REVISE,
                    f"revised {weakest.name} "
                    f"({weakest.score.total():.3f} → "
                    f"{new_poem.score.total():.3f})")
                return
            else:
                self._record_snapshot(
                    PhaseType.REST,
                    f"revision of {weakest.name} not kept")
                return

        # Priority 5: REST
        self._record_snapshot(PhaseType.REST, "no action needed")

    # -- main loop ----------------------------------------------------

    def run(self, skip_initial: bool = False) -> Collection:
        if not skip_initial:
            for _ in range(self.target_poems):
                voice = self._next_voice()
                self.poems.append(self._compose_one(voice))
            self._record_snapshot(PhaseType.COMPOSE,
                                   "initial batch composed")

        for cycle in range(self.n_cycles):
            self._rest_phase(cycle)
            self._act_phase(cycle)

        # Final rest
        self._rest_phase(self.n_cycles)
        return self._build_collection()

    def get_report(self) -> "SpiralReport":
        return SpiralReport(
            snapshots=list(self.snapshots),
            final_collection=self._build_collection(),
        )


# =====================================================================
# Composite: SpiralReport
# =====================================================================

class SpiralReport:
    """Reads the spiral's history."""

    def __init__(self, snapshots: List[Snapshot],
                 final_collection: Collection):
        self.snapshots = snapshots
        self.final_collection = final_collection

    def summary(self) -> Dict:
        if not self.snapshots:
            return {"n_snapshots": 0}
        initial = self.snapshots[0]
        final = self.snapshots[-1]
        phase_counts: Dict[str, int] = {}
        for s in self.snapshots:
            phase_counts[s.phase_type] = (
                phase_counts.get(s.phase_type, 0) + 1)
        return {
            "n_snapshots": len(self.snapshots),
            "initial_poems": initial.n_poems,
            "final_poems": final.n_poems,
            "initial_score": initial.collection_score,
            "final_score": final.collection_score,
            "score_delta": (
                final.collection_score - initial.collection_score),
            "initial_arc": initial.arc_type,
            "final_arc": final.arc_type,
            "phase_counts": phase_counts,
        }

    def trajectory(self) -> List[float]:
        return [s.collection_score for s in self.snapshots]

    def report(self) -> str:
        s = self.summary()
        lines = [
            "SpiralReport:",
            f"  Snapshots: {s['n_snapshots']}",
            f"  Poems: {s['initial_poems']} → {s['final_poems']}",
            f"  Score: {s['initial_score']:.3f} → "
            f"{s['final_score']:.3f} "
            f"(Δ {s['score_delta']:+.3f})",
            f"  Arc: {s['initial_arc']} → {s['final_arc']}",
            f"  Phase counts: {s['phase_counts']}",
            "",
            "  History:",
        ]
        for snap in self.snapshots:
            lines.append(f"    {snap.report()}")
        return "\n".join(lines)

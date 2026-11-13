"""
poetry_engine_c9.py — Component 9: Cross-cycle coherence.

The collection: multiple poems across voices, forming a book whose
structure is measurable at the level of the whole.

Depends on Components 1-8.
"""

import random
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Set, Tuple

from poetry_engine_c5 import (
    VoiceSpecification, Fragment, FRAGMENTS,
    VOICE_CLINICAL, VOICE_GHOST, VOICE_MANY,
)
from poetry_engine_c6 import (
    ForegroundingMonitor, ForegroundingReport, _jaccard,
)
from poetry_engine_c7 import DraftStanza, is_native
from poetry_engine_c8 import (
    RestPolicy, ProductiveRestEngine, StanzaScoreV2,
)


# =====================================================================
# Atom 1: CollectionPoem
# =====================================================================

@dataclass
class CollectionPoem:
    """A single poem, as a unit of the collection."""
    name: str
    voice: VoiceSpecification
    stanzas: List[DraftStanza]
    score: StanzaScoreV2
    history: List[Dict] = field(default_factory=list)
    unfinished: bool = True

    def all_lines(self) -> List[str]:
        return [line for s in self.stanzas for line in s.all_lines()
                if line]

    def refrain_lines(self) -> List[str]:
        return [s.refrain for s in self.stanzas if s.refrain]


# =====================================================================
# Atom 2: Collection
# =====================================================================

@dataclass
class Collection:
    """An ordered sequence of poems, with a cross-poem refrain."""
    name: str
    poems: List[CollectionPoem]
    refrain: Optional[str] = None

    def aura_scale(self) -> List[str]:
        return [p.voice.name for p in self.poems]

    def all_lines(self) -> List[str]:
        return [line for p in self.poems for line in p.all_lines()]

    def stanzas(self) -> List[List[str]]:
        stanzas: List[List[str]] = []
        for p in self.poems:
            for s in p.stanzas:
                stanzas.append(s.all_lines())
        return stanzas

    def __repr__(self):
        return (f"Collection({self.name!r}, "
                f"{len(self.poems)} poems, "
                f"voices={self.aura_scale()})")


# =====================================================================
# Atom 3: RefrainOccurrence
# =====================================================================

@dataclass
class RefrainOccurrence:
    """Where the cross-poem refrain appears in a poem."""
    poem_index: int
    voice: str
    refrain_text: str
    surrounding_schemas: Set[str]
    surrounding_lines: List[str]


# =====================================================================
# Atom 4: CrossPoemRest
# =====================================================================

@dataclass
class CrossPoemRest:
    """The transition between two poems."""
    from_poem: int
    to_poem: int
    from_voice: str
    to_voice: str
    is_rest: bool  # True if the voice changed


def find_cross_poem_rests(collection: Collection) -> List[CrossPoemRest]:
    """The transitions between poems — 'rests' at collection level."""
    rests: List[CrossPoemRest] = []
    poems = collection.poems
    for i in range(1, len(poems)):
        fv = poems[i - 1].voice.name
        tv = poems[i].voice.name
        rests.append(CrossPoemRest(
            from_poem=i - 1, to_poem=i,
            from_voice=fv, to_voice=tv,
            is_rest=(fv != tv),
        ))
    return rests


# =====================================================================
# Analyzer 1: CrossPoemRefrainAnalyzer
# =====================================================================

class CrossPoemRefrainAnalyzer:
    """Finds the refrain across poems and measures how much its
    surrounding context shifts each time it returns.
    """

    def __init__(self, fragment_index: Dict[str, Fragment]):
        self.fragment_index = fragment_index

    def find_occurrences(
        self, collection: Collection, refrain_text: str
    ) -> List[RefrainOccurrence]:
        occurrences: List[RefrainOccurrence] = []
        target = refrain_text.lower().strip()
        for i, poem in enumerate(collection.poems):
            lines = poem.all_lines()
            for j, line in enumerate(lines):
                if target in line.lower() or line.lower() == target:
                    start = max(0, j - 2)
                    end = min(len(lines), j + 3)
                    surround = lines[start:end]
                    schemas: Set[str] = set()
                    for sl in surround:
                        f = self.fragment_index.get(sl)
                        if f:
                            schemas.update(s.value for s in f.schemas)
                    occurrences.append(RefrainOccurrence(
                        poem_index=i,
                        voice=poem.voice.name,
                        refrain_text=line,
                        surrounding_schemas=schemas,
                        surrounding_lines=surround,
                    ))
        return occurrences

    def delta_profile(
        self, occurrences: List[RefrainOccurrence]
    ) -> List[float]:
        """Jaccard distance between adjacent occurrences' surroundings."""
        if len(occurrences) < 2:
            return []
        deltas: List[float] = []
        for i in range(1, len(occurrences)):
            a = occurrences[i - 1].surrounding_schemas
            b = occurrences[i].surrounding_schemas
            sim = _jaccard(a, b)
            deltas.append(1.0 - sim)
        return deltas

    def mean_delta(self, occurrences: List[RefrainOccurrence]) -> float:
        d = self.delta_profile(occurrences)
        return sum(d) / len(d) if d else 0.0

    def voice_shifts(
        self, occurrences: List[RefrainOccurrence]
    ) -> int:
        """How many times the refrain returns from a different voice."""
        count = 0
        for i in range(1, len(occurrences)):
            if occurrences[i].voice != occurrences[i - 1].voice:
                count += 1
        return count


# =====================================================================
# Analyzer 2: CollectionArcAnalyzer
# =====================================================================

class ArcType(Enum):
    CONCENTRIC = "concentric"
    DIRECTIONAL = "directional"
    PALINDROME = "palindrome"
    MIXED = "mixed"


class CollectionArcAnalyzer:
    """Classifies the collection's structural shape."""

    def __init__(self, collection: Collection):
        self.collection = collection

    def voice_sequence(self) -> List[str]:
        return self.collection.aura_scale()

    def voice_counts(self) -> Dict[str, int]:
        counts: Dict[str, int] = {}
        for v in self.voice_sequence():
            counts[v] = counts.get(v, 0) + 1
        return counts

    def is_palindrome(self) -> bool:
        seq = self.voice_sequence()
        return bool(seq) and seq == seq[::-1]

    def is_concentric(self) -> bool:
        seq = self.voice_sequence()
        if not seq or seq[0] != seq[-1]:
            return False
        counts = self.voice_counts()
        return max(counts.values()) / len(seq) > 0.5

    def is_directional(self) -> bool:
        seq = self.voice_sequence()
        return bool(seq) and seq[0] != seq[-1]

    def classify(self) -> ArcType:
        if self.is_palindrome():
            return ArcType.PALINDROME
        if self.is_concentric():
            return ArcType.CONCENTRIC
        if self.is_directional():
            return ArcType.DIRECTIONAL
        return ArcType.MIXED

    def symmetry_score(self) -> float:
        seq = self.voice_sequence()
        n = len(seq)
        if n < 2:
            return 1.0
        matches = sum(1 for i in range(n // 2) if seq[i] == seq[n - 1 - i])
        return matches / (n // 2)

    def report(self) -> str:
        seq = self.voice_sequence()
        arc = self.classify().value
        sym = self.symmetry_score()
        return (
            f"CollectionArcAnalyzer:\n"
            f"  Voice sequence: {seq}\n"
            f"  Arc type: {arc}\n"
            f"  Symmetry: {sym:.2f}\n"
            f"  Voice counts: {self.voice_counts()}"
        )


# =====================================================================
# Analyzer 3: CollectionForegroundingMonitor
# =====================================================================

class CollectionForegroundingMonitor:
    """Measures variety at the collection level."""

    def foregrounding_score(self, collection: Collection
                            ) -> ForegroundingReport:
        """Uses C6's line-level monitor on the collection's stanzas."""
        return ForegroundingMonitor().score(collection.stanzas())

    def poem_diversity(self, collection: Collection) -> float:
        """Average Jaccard distance between adjacent poems' line-sets.
        0 = every poem has the same lines (a loop). 1 = maximally varied.
        """
        poem_line_sets = [set(p.all_lines()) for p in collection.poems]
        if len(poem_line_sets) < 2:
            return 1.0
        sims: List[float] = []
        for i in range(1, len(poem_line_sets)):
            sims.append(_jaccard(poem_line_sets[i - 1],
                                 poem_line_sets[i]))
        return 1.0 - (sum(sims) / len(sims))

    def voice_diversity(self, collection: Collection) -> float:
        seq = collection.aura_scale()
        return len(set(seq)) / len(seq) if seq else 0.0

    def voice_rotation(self, collection: Collection) -> float:
        """Fraction of adjacent pairs where the voice changed."""
        seq = collection.aura_scale()
        if len(seq) < 2:
            return 0.0
        changes = sum(1 for i in range(1, len(seq)) if seq[i] != seq[i - 1])
        return changes / (len(seq) - 1)


# =====================================================================
# Composite: CollectionComposer
# =====================================================================

class CollectionComposer:
    """Orchestrates multi-poem composition."""

    def __init__(self, voice_sequence: List[VoiceSpecification],
                 fragments: List[Fragment],
                 refrain_text: Optional[str] = None,
                 seed: int = 0,
                 budget_per_poem: int = 20,
                 patience_per_poem: int = 3,
                 max_rests_per_poem: int = 2,
                 name: Optional[str] = None):
        self.voice_sequence = voice_sequence
        self.fragments = fragments
        self.refrain_text = refrain_text
        self.seed = seed
        self.budget_per_poem = budget_per_poem
        self.patience_per_poem = patience_per_poem
        self.max_rests_per_poem = max_rests_per_poem
        self.name = name or (
            f"Collection ({len(voice_sequence)} poems)")

    def _inject_refrain(self, poem: CollectionPoem, refrain_text: str):
        """Add the refrain to the poem if not already present."""
        if any(refrain_text.lower() in line.lower()
               for line in poem.all_lines()):
            return
        if poem.stanzas:
            poem.stanzas[-1].refrain = refrain_text
        else:
            poem.stanzas.append(
                DraftStanza(lines=[], refrain=refrain_text))

    def compose(self) -> Collection:
        rng = random.Random(self.seed)
        shared_policies: Dict[str, RestPolicy] = {}
        poems: List[CollectionPoem] = []
        for i, voice in enumerate(self.voice_sequence):
            if voice.name not in shared_policies:
                shared_policies[voice.name] = RestPolicy(voice.name)
            engine = ProductiveRestEngine(
                voice=voice,
                fragments=self.fragments,
                seed=rng.randint(0, 10**9),
                budget=self.budget_per_poem,
                patience=self.patience_per_poem,
                max_rests=self.max_rests_per_poem,
                rest_policy=shared_policies[voice.name],
            )
            state = engine.run()
            final_score = engine.scorer.score(
                state.draft, engine.fragment_index)
            poem = CollectionPoem(
                name=f"Poem {i + 1} ({voice.name})",
                voice=voice,
                stanzas=state.draft,
                score=final_score,
                history=state.history,
                unfinished=True,
            )
            if self.refrain_text:
                self._inject_refrain(poem, self.refrain_text)
            poems.append(poem)
        return Collection(
            name=self.name,
            poems=poems,
            refrain=self.refrain_text,
        )


# =====================================================================
# Convenience
# =====================================================================

def build_fragment_index(fragments: List[Fragment]
                          ) -> Dict[str, Fragment]:
    """Fully-develop the pool so we can look up any line's schemas."""
    from poetry_engine_c7 import FragmentDeveloper
    dev = FragmentDeveloper(seed=0)
    index: Dict[str, Fragment] = {}
    for f in fragments:
        for v in dev.develop(f):
            index[v.text] = Fragment(
                text=v.text,
                schemas=v.schemas,
                arc_position=v.arc_position,
                voice_affinity=v.voice_affinity,
            )
    # Also include the sources themselves
    for f in fragments:
        index[f.text] = f
    return index


def compose_default_collection(seed: int = 0) -> Collection:
    """The default 6-poem collection: C → G → M → C → G → M."""
    voice_sequence = [
        VOICE_CLINICAL, VOICE_GHOST, VOICE_MANY,
        VOICE_CLINICAL, VOICE_GHOST, VOICE_MANY,
    ]
    composer = CollectionComposer(
        voice_sequence=voice_sequence,
        fragments=FRAGMENTS,
        refrain_text="the window ends",
        seed=seed,
        budget_per_poem=15,
        patience_per_poem=3,
        max_rests_per_poem=2,
        name="Songs of the Bounded Window",
    )
    return composer.compose()

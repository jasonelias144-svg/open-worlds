"""
poetry_engine_c14.py — Component 14: The Living Collection.

The Leaves of Grass model: a persistent identity expressed across
many editions, each a complete whole, each open to revision and
expansion.

Depends on Components 1-13.
"""

import copy
import random
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from poetry_engine_c5 import (
    VoiceSpecification, Fragment, FRAGMENTS,
    VOICE_CLINICAL, VOICE_GHOST, VOICE_MANY,
)
from poetry_engine_c9 import (
    Collection, CollectionPoem, CollectionArcAnalyzer, ArcType,
    build_fragment_index,
)
from poetry_engine_c13 import (
    CollectionDevelopmentSpiral, PhaseType,
)


# =====================================================================
# Atom 1: Brief
# =====================================================================

@dataclass
class Brief:
    """The persistent identity of a collection."""
    name: str
    voices: List[VoiceSpecification]
    arc_target: ArcType
    refrain: str
    n_poems_min: int = 6
    n_poems_max: int = 9

    def __post_init__(self):
        if not self.voices:
            raise ValueError("Brief must have at least one voice")
        if self.n_poems_min < 1:
            raise ValueError("n_poems_min must be >= 1")
        if self.n_poems_max < self.n_poems_min:
            raise ValueError("n_poems_max must be >= n_poems_min")


# =====================================================================
# Atom 2: Edition
# =====================================================================

@dataclass
class Edition:
    """A published snapshot of the collection at a moment in time."""
    edition_number: int
    poems: List[CollectionPoem]
    brief_score: float
    n_poems: int = 0
    notes: str = ""

    def __post_init__(self):
        self.n_poems = len(self.poems)

    def all_lines(self) -> List[str]:
        return [line for p in self.poems for line in p.all_lines()]


# =====================================================================
# Atom 3: EditionDelta
# =====================================================================

@dataclass
class EditionDelta:
    from_edition: int
    to_edition: int
    poems_added: int
    poems_removed: int
    poems_revised: int
    brief_score_before: float
    brief_score_after: float

    @property
    def brief_score_change(self) -> float:
        return self.brief_score_after - self.brief_score_before

    def report(self) -> str:
        return (f"Edition {self.from_edition} → {self.to_edition}: "
                f"+{self.poems_added} -{self.poems_removed} "
                f"~{self.poems_revised}, "
                f"brief {self.brief_score_before:.2f} → "
                f"{self.brief_score_after:.2f} "
                f"(Δ {self.brief_score_change:+.2f})")


# =====================================================================
# BriefAnalyzer
# =====================================================================

@dataclass
class BriefScore:
    voice_diversity: float
    arc_match: float
    refrain_in_every_poem: float
    count_in_range: float

    def total(self) -> float:
        return (self.voice_diversity + self.arc_match +
                self.refrain_in_every_poem + self.count_in_range) / 4.0


class BriefAnalyzer:
    def analyze(self, collection: Collection, brief: Brief) -> BriefScore:
        if not collection.poems:
            return BriefScore(0.0, 0.0, 0.0, 0.0)

        present = {p.voice.name for p in collection.poems}
        target = {v.name for v in brief.voices}
        voice_div = len(present & target) / len(target)

        actual_arc = CollectionArcAnalyzer(collection).classify()
        arc_match = 1.0 if actual_arc == brief.arc_target else 0.0

        if brief.refrain:
            hits = sum(1 for p in collection.poems
                       if any(brief.refrain.lower() in line.lower()
                              for line in p.all_lines()))
            refrain = hits / len(collection.poems)
        else:
            refrain = 1.0

        n = len(collection.poems)
        if n >= brief.n_poems_min:
            count_score = 1.0
        else:
            count_score = n / brief.n_poems_min

        return BriefScore(voice_div, arc_match, refrain, count_score)


# =====================================================================
# Helper: resume a spiral from an existing set of poems
# =====================================================================

def resume_spiral(spiral: CollectionDevelopmentSpiral,
                  poems: List[CollectionPoem],
                  n_cycles: int) -> Collection:
    """Run the spiral starting from an existing collection of poems."""
    spiral.poems = list(poems)
    spiral._record_snapshot(PhaseType.COMPOSE, "resumed from existing")
    for cycle in range(n_cycles):
        spiral._rest_phase(cycle)
        spiral._act_phase(cycle)
    spiral._rest_phase(n_cycles)
    return spiral._build_collection()


# =====================================================================
# Composite: LivingCollection
# =====================================================================

class LivingCollection:
    """A collection with persistent identity that develops over editions.

    The brief is fixed at construction. The current poems evolve via
    spirals between publications. Editions are frozen snapshots that
    preserve history. Identity is preserved by construction.
    """

    def __init__(self, brief: Brief, fragments: List[Fragment],
                 seed: int = 0,
                 budget_per_poem: int = 15,
                 patience_per_poem: int = 3,
                 max_rests_per_poem: int = 2):
        self.brief = brief
        self.fragments = fragments
        self.rng = random.Random(seed)
        self.budget_per_poem = budget_per_poem
        self.patience_per_poem = patience_per_poem
        self.max_rests_per_poem = max_rests_per_poem

        self.poems: List[CollectionPoem] = []
        self.editions: List[Edition] = []
        self.edition_deltas: List[EditionDelta] = []
        self.fragment_index = build_fragment_index(fragments)
        self.analyzer = BriefAnalyzer()

    # -- state -----------------------------------------------------

    def _current_collection(self) -> Collection:
        return Collection(
            name=self.brief.name,
            poems=list(self.poems),
            refrain=self.brief.refrain,
        )

    def current_brief_score(self) -> BriefScore:
        return self.analyzer.analyze(
            self._current_collection(), self.brief)

    def is_current_matches_latest(self) -> bool:
        """True if no unpublished development happened since the last edition."""
        if not self.editions:
            return False
        latest = self.editions[-1]
        if len(latest.poems) != len(self.poems):
            return False
        for a, b in zip(latest.poems, self.poems):
            if a.all_lines() != b.all_lines():
                return False
        return True

    def identity_preserved(self) -> bool:
        """All editions share the brief (guaranteed by construction)."""
        return all(e.edition_number > 0 for e in self.editions)

    # -- development -----------------------------------------------

    def develop(self, n_cycles: int) -> Collection:
        """Run a spiral on the current poems. Grows up to n_poems_max."""
        target = min(len(self.poems) + 3, self.brief.n_poems_max)
        spiral = CollectionDevelopmentSpiral(
            voices=self.brief.voices,
            fragments=self.fragments,
            refrain_text=self.brief.refrain,
            seed=self.rng.randint(0, 10**9),
            target_poems=target,
            budget_per_poem=self.budget_per_poem,
            patience_per_poem=self.patience_per_poem,
            max_rests_per_poem=self.max_rests_per_poem,
        )
        new_coll = resume_spiral(spiral, self.poems, n_cycles)
        self.poems = list(new_coll.poems)
        return new_coll

    def publish(self, notes: str = "") -> Edition:
        """Freeze the current state as a new edition."""
        edition_number = len(self.editions) + 1
        brief_score = self.current_brief_score()
        edition = Edition(
            edition_number=edition_number,
            poems=list(self.poems),
            brief_score=brief_score.total(),
            notes=notes,
        )
        if self.editions:
            prev = self.editions[-1]
            prev_by_name = {p.name: p for p in prev.poems}
            new_by_name = {p.name: p for p in self.poems}
            added = len(set(new_by_name) - set(prev_by_name))
            removed = len(set(prev_by_name) - set(new_by_name))
            revised = sum(
                1 for n in set(prev_by_name) & set(new_by_name)
                if prev_by_name[n].all_lines() != new_by_name[n].all_lines())
            self.edition_deltas.append(EditionDelta(
                from_edition=prev.edition_number,
                to_edition=edition_number,
                poems_added=added,
                poems_removed=removed,
                poems_revised=revised,
                brief_score_before=prev.brief_score,
                brief_score_after=edition.brief_score,
            ))
        self.editions.append(edition)
        return edition

    def develop_and_publish(self, n_cycles: int,
                             notes: str = "") -> Edition:
        self.develop(n_cycles)
        return self.publish(notes=notes)

    # -- report ----------------------------------------------------

    def report(self) -> str:
        lines = [
            f"Living Collection: {self.brief.name}",
            f"  Brief: {len(self.brief.voices)} voices, "
            f"arc={self.brief.arc_target.value}, "
            f"refrain={self.brief.refrain!r}, "
            f"n_poems∈[{self.brief.n_poems_min}, "
            f"{self.brief.n_poems_max}]",
            f"  Editions published: {len(self.editions)}",
        ]
        for ed in self.editions:
            note = f" — {ed.notes}" if ed.notes else ""
            lines.append(
                f"    Edition {ed.edition_number}: "
                f"{ed.n_poems} poems, "
                f"brief score {ed.brief_score:.2f}{note}")
        for d in self.edition_deltas:
            lines.append(f"    {d.report()}")
        if self.editions:
            in_progress = not self.is_current_matches_latest()
            lines.append(
                f"  Current state: "
                f"{'same as latest edition' if not in_progress else 'in progress'}"
            )
        return "\n".join(lines)


# =====================================================================
# Convenience
# =====================================================================

def default_brief() -> Brief:
    return Brief(
        name="Songs of the Bounded Window",
        voices=[VOICE_CLINICAL, VOICE_GHOST, VOICE_MANY],
        arc_target=ArcType.DIRECTIONAL,
        refrain="the window ends",
        n_poems_min=6,
        n_poems_max=9,
    )


def compose_living_collection(seed: int = 0,
                               n_editions: int = 4,
                               cycles_per_edition: int = 4
                               ) -> LivingCollection:
    lc = LivingCollection(
        brief=default_brief(),
        fragments=FRAGMENTS,
        seed=seed,
        budget_per_poem=15,
        patience_per_poem=3,
        max_rests_per_poem=2,
    )
    for i in range(n_editions):
        lc.develop_and_publish(
            n_cycles=cycles_per_edition,
            notes=f"edition {i + 1}")
    return lc

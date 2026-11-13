"""
poetry_engine_c17.py — Component 17: The Complete Agent.

The single entry point for the poetry framework. Brief in, book out.

Depends on Components 1-14.
"""

import json
import os
import random
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

from poetry_engine_c5 import (
    VoiceSpecification, Fragment, FRAGMENTS,
    VOICE_CLINICAL, VOICE_GHOST, VOICE_MANY,
)
from poetry_engine_c8 import StanzaScoreV2
from poetry_engine_c9 import (
    Collection, CollectionPoem, ArcType, CollectionArcAnalyzer,
    build_fragment_index,
)
from poetry_engine_c13 import CollectionDevelopmentSpiral
from poetry_engine_c14 import (
    Brief, Edition, EditionDelta, BriefAnalyzer, LivingCollection,
    resume_spiral, default_brief,
)


# =====================================================================
# Voice registry (for serialization)
# =====================================================================

VOICE_REGISTRY: Dict[str, VoiceSpecification] = {
    VOICE_CLINICAL.name: VOICE_CLINICAL,
    VOICE_GHOST.name: VOICE_GHOST,
    VOICE_MANY.name: VOICE_MANY,
}


# =====================================================================
# Subclass: LivingCollection with spiral history
# =====================================================================

class LivingCollectionWithHistory(LivingCollection):
    """C14's LivingCollection, plus a record of each spiral run."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.spiral_history: List[CollectionDevelopmentSpiral] = []

    def develop(self, n_cycles: int) -> Collection:
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
        self.spiral_history.append(spiral)
        return new_coll


# =====================================================================
# Atom: BookMetadata
# =====================================================================

@dataclass
class BookMetadata:
    brief_name: str
    n_editions: int
    n_poems_final: int
    final_brief_score: float
    trajectory: List[float]
    converged: bool
    fulfilled: bool
    not_fulfilled_reasons: List[str]

    def report(self) -> str:
        lines = [
            f"Book: {self.brief_name}",
            f"  Editions: {self.n_editions}",
            f"  Final poems: {self.n_poems_final}",
            f"  Final brief score: {self.final_brief_score:.2f}",
            f"  Trajectory: {[round(x, 2) for x in self.trajectory]}",
            f"  Converged: {self.converged}",
            f"  Fulfilled: {self.fulfilled}",
        ]
        if self.not_fulfilled_reasons:
            lines.append("  Not fulfilled because:")
            for r in self.not_fulfilled_reasons:
                lines.append(f"    - {r}")
        return "\n".join(lines)


# =====================================================================
# Composite: CompletedBook
# =====================================================================

@dataclass
class CompletedBook:
    """The finished artifact: brief, editions, deltas, convergence."""
    brief: Brief
    editions: List[Edition]
    deltas: List[EditionDelta]
    seed: int
    converged: bool

    # -- queries ---------------------------------------------------

    def trajectory(self) -> List[float]:
        return [e.brief_score for e in self.editions]

    def final_edition(self) -> Optional[Edition]:
        return self.editions[-1] if self.editions else None

    def fulfilled(self) -> bool:
        if not self.editions:
            return False
        return self.editions[-1].brief_score >= 0.95

    def not_fulfilled_reasons(self) -> List[str]:
        if not self.editions:
            return ["no editions were published"]
        final = self.editions[-1]
        if final.brief_score >= 0.95:
            return []
        reasons: List[str] = []
        analyzer = BriefAnalyzer()
        coll = Collection(
            name=self.brief.name,
            poems=list(final.poems),
            refrain=self.brief.refrain,
        )
        score = analyzer.analyze(coll, self.brief)
        if score.voice_diversity < 0.95:
            reasons.append(
                f"voice diversity: {score.voice_diversity:.2f} "
                f"(wanted all {len(self.brief.voices)} voices)")
        if score.arc_match < 0.95:
            actual = CollectionArcAnalyzer(coll).classify().value
            reasons.append(
                f"arc mismatch: wanted {self.brief.arc_target.value}, "
                f"got {actual}")
        if score.refrain_in_every_poem < 0.95:
            reasons.append(
                f"refrain present in only "
                f"{score.refrain_in_every_poem:.0%} of poems")
        if score.count_in_range < 0.95:
            reasons.append(
                f"poem count {len(coll.poems)} below minimum "
                f"{self.brief.n_poems_min}")
        return reasons

    def metadata(self) -> BookMetadata:
        return BookMetadata(
            brief_name=self.brief.name,
            n_editions=len(self.editions),
            n_poems_final=(self.final_edition().n_poems
                           if self.editions else 0),
            final_brief_score=(self.editions[-1].brief_score
                               if self.editions else 0.0),
            trajectory=self.trajectory(),
            converged=self.converged,
            fulfilled=self.fulfilled(),
            not_fulfilled_reasons=self.not_fulfilled_reasons(),
        )

    def report(self) -> str:
        lines = [self.metadata().report()]
        lines.append("")
        lines.append("Editions:")
        for ed in self.editions:
            note = f" — {ed.notes}" if ed.notes else ""
            lines.append(
                f"  Edition {ed.edition_number}: {ed.n_poems} poems, "
                f"brief {ed.brief_score:.2f}{note}")
        if self.deltas:
            lines.append("")
            lines.append("Deltas between editions:")
            for d in self.deltas:
                lines.append(f"  {d.report()}")
        return "\n".join(lines)

    # -- persistence -----------------------------------------------

    def save(self, path: str):
        data = {
            "brief": {
                "name": self.brief.name,
                "voice_names": [v.name for v in self.brief.voices],
                "arc_target": self.brief.arc_target.value,
                "refrain": self.brief.refrain,
                "n_poems_min": self.brief.n_poems_min,
                "n_poems_max": self.brief.n_poems_max,
            },
            "seed": self.seed,
            "converged": self.converged,
            "editions": [
                {
                    "edition_number": ed.edition_number,
                    "brief_score": ed.brief_score,
                    "notes": ed.notes,
                    "poems": [
                        {
                            "name": p.name,
                            "voice_name": p.voice.name,
                            "stanzas": [
                                {"lines": list(s.lines),
                                 "refrain": s.refrain}
                                for s in p.stanzas
                            ],
                            "score": [
                                p.score.foregrounding,
                                p.score.native_purity,
                                p.score.voice_consistency,
                                p.score.coverage,
                                p.score.schema_diversity,
                            ],
                        }
                        for p in ed.poems
                    ],
                }
                for ed in self.editions
            ],
            "deltas": [
                {
                    "from_edition": d.from_edition,
                    "to_edition": d.to_edition,
                    "poems_added": d.poems_added,
                    "poems_removed": d.poems_removed,
                    "poems_revised": d.poems_revised,
                    "brief_score_before": d.brief_score_before,
                    "brief_score_after": d.brief_score_after,
                }
                for d in self.deltas
            ],
        }
        with open(path, "w") as f:
            json.dump(data, f, indent=2)

    @classmethod
    def load(cls, path: str) -> "CompletedBook":
        with open(path) as f:
            data = json.load(f)
        brief = Brief(
            name=data["brief"]["name"],
            voices=[VOICE_REGISTRY[n] for n in data["brief"]["voice_names"]],
            arc_target=ArcType(data["brief"]["arc_target"]),
            refrain=data["brief"]["refrain"],
            n_poems_min=data["brief"]["n_poems_min"],
            n_poems_max=data["brief"]["n_poems_max"],
        )
        editions: List[Edition] = []
        for ed_data in data["editions"]:
            poems: List[CollectionPoem] = []
            for p_data in ed_data["poems"]:
                voice = VOICE_REGISTRY[p_data["voice_name"]]
                stanzas = [
                    DraftStanza(
                        lines=list(s["lines"]),
                        refrain=s["refrain"],
                    )
                    for s in p_data["stanzas"]
                ]
                sc = p_data["score"]
                score = StanzaScoreV2(
                    foregrounding=sc[0], native_purity=sc[1],
                    voice_consistency=sc[2], coverage=sc[3],
                    schema_diversity=sc[4],
                )
                poems.append(CollectionPoem(
                    name=p_data["name"],
                    voice=voice,
                    stanzas=stanzas,
                    score=score,
                ))
            editions.append(Edition(
                edition_number=ed_data["edition_number"],
                poems=poems,
                brief_score=ed_data["brief_score"],
                notes=ed_data.get("notes", ""),
            ))
        deltas = [
            EditionDelta(**d) for d in data["deltas"]
        ]
        return cls(
            brief=brief, editions=editions, deltas=deltas,
            seed=data["seed"], converged=data["converged"],
        )


# Import DraftStanza here to avoid circular dependency in load()
from poetry_engine_c7 import DraftStanza


# =====================================================================
# Composite: PoetryAgent
# =====================================================================

class PoetryAgent:
    """The complete agent: brief in, book out."""

    def __init__(self, brief: Brief, fragments: List[Fragment],
                 seed: int = 0,
                 budget_per_poem: int = 15,
                 patience_per_poem: int = 3,
                 max_rests_per_poem: int = 2):
        self.brief = brief
        self.fragments = fragments
        self.seed = seed
        self.rng = random.Random(seed)
        self.budget_per_poem = budget_per_poem
        self.patience_per_poem = patience_per_poem
        self.max_rests_per_poem = max_rests_per_poem

    def _make_collection(self) -> LivingCollectionWithHistory:
        return LivingCollectionWithHistory(
            brief=self.brief,
            fragments=self.fragments,
            seed=self.rng.randint(0, 10**9),
            budget_per_poem=self.budget_per_poem,
            patience_per_poem=self.patience_per_poem,
            max_rests_per_poem=self.max_rests_per_poem,
        )

    def _has_converged(self, lc: LivingCollectionWithHistory,
                       window: int = 2) -> bool:
        """Converged if last `window` editions have identical scores."""
        eds = lc.editions
        if len(eds) < window:
            return False
        scores = [e.brief_score for e in eds[-window:]]
        return max(scores) - min(scores) < 0.01

    def compose(self, n_editions: int = 4,
                cycles_per_edition: int = 4,
                converge: bool = True) -> CompletedBook:
        """Compose a book. Run up to n_editions, or stop when converged."""
        lc = self._make_collection()
        converged = False
        for i in range(n_editions):
            lc.develop(cycles_per_edition)
            lc.publish(notes=f"edition {i + 1}")
            if converge and self._has_converged(lc):
                converged = True
                break
        return CompletedBook(
            brief=self.brief,
            editions=list(lc.editions),
            deltas=list(lc.edition_deltas),
            seed=self.seed,
            converged=converged,
        )

    def resume(self, book: CompletedBook,
               additional_editions: int = 2,
               cycles_per_edition: int = 4,
               converge: bool = True) -> CompletedBook:
        """Continue development from an existing book."""
        lc = self._make_collection()
        lc.poems = list(book.editions[-1].poems) if book.editions else []
        lc.editions = list(book.editions)
        lc.edition_deltas = list(book.deltas)
        converged = book.converged
        for i in range(additional_editions):
            if converged:
                break
            lc.develop(cycles_per_edition)
            lc.publish(notes=f"edition {len(lc.editions) + 1}")
            if converge and self._has_converged(lc):
                converged = True
                break
        return CompletedBook(
            brief=self.brief,
            editions=list(lc.editions),
            deltas=list(lc.edition_deltas),
            seed=self.seed,
            converged=converged,
        )

    @classmethod
    def from_saved(cls, path: str, fragments: List[Fragment]
                   ) -> Tuple["PoetryAgent", CompletedBook]:
        book = CompletedBook.load(path)
        agent = cls(brief=book.brief, fragments=fragments,
                    seed=book.seed)
        return agent, book


# =====================================================================
# Convenience
# =====================================================================

def compose_whitman_book(seed: int = 0,
                         n_editions: int = 5,
                         cycles_per_edition: int = 4
                         ) -> CompletedBook:
    """Compose a book modeled on Leaves of Grass."""
    brief = default_brief()  # from C14
    agent = PoetryAgent(
        brief=brief, fragments=FRAGMENTS, seed=seed,
        budget_per_poem=15, patience_per_poem=3,
        max_rests_per_poem=2,
    )
    return agent.compose(
        n_editions=n_editions,
        cycles_per_edition=cycles_per_edition,
        converge=True,
    )

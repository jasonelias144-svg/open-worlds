"""
poetry_engine_c20.py — Component 20: The Full Agent.

ARCHITECTURE — designed for implementation, not executed in this session.

The closing component. Brief in, complete artifact out.
Artifact = book + journal + trajectories + provenance + metadata.

Depends on Components 1-19.
"""

import datetime
import json
from dataclasses import asdict, dataclass, field
from typing import Dict, List, Optional, Tuple, Set

from poetry_engine_c5 import (
    VoiceSpecification, Fragment, FRAGMENTS,
    VOICE_CLINICAL, VOICE_GHOST, VOICE_MANY,
)
from poetry_engine_c9 import (
    ArcType, Collection, CollectionArcAnalyzer, build_fragment_index,
)
from poetry_engine_c14 import Brief, BriefAnalyzer, default_brief
from poetry_engine_c17 import CompletedBook, PoetryAgent, VOICE_REGISTRY
from poetry_engine_c18 import (
    Reflection, Reworking, Trajectory, ReflectivePoet, ReflectiveBook,
)
from poetry_engine_c19 import (
    Session, SessionPhase, SessionPosture, Journal, LongRun,
    run_between_sessions_long_run,
)


# =====================================================================
# Atom 1: ProvenanceEntry
# =====================================================================

@dataclass
class ProvenanceEntry:
    """The complete lineage of a single line in the final book."""
    line_text: str
    first_seen_session: int
    first_seen_edition: int
    source_fragment: Optional[str]      # the original fragment it derives from
    reworking_chain: List[str] = field(default_factory=list)
    reflection_chain: List[str] = field(default_factory=list)

    @property
    def is_rewritten(self) -> bool:
        """Did this line undergo at least one reworking?"""
        return len(self.reworking_chain) > 0

    def describe(self) -> str:
        if not self.is_rewritten:
            return (f"\"{self.line_text}\"\n"
                    f"  Source: {self.source_fragment or '(original)'}\n"
                    f"  Unreworked (entered the work directly)")
        lines = [f"\"{self.line_text}\""]
        lines.append(f"  First appeared: session {self.first_seen_session}, "
                     f"edition {self.first_seen_edition}")
        if self.source_fragment:
            lines.append(f"  Source: {self.source_fragment}")
        lines.append(f"  Reworking chain ({len(self.reworking_chain)} steps):")
        for i, rw in enumerate(self.reworking_chain, 1):
            lines.append(f"    {i}. {rw}")
        if self.reflection_chain:
            lines.append(f"  Prompted by reflections:")
            for refl in self.reflection_chain:
                lines.append(f"    - {refl}")
        return "\n".join(lines)


# =====================================================================
# Atom 2: ArtifactMetadata
# =====================================================================

@dataclass
class ArtifactMetadata:
    brief_name: str
    composition_date: datetime.date
    n_sessions: int
    n_written_sessions: int
    n_rest_sessions: int
    n_simulations: int
    n_reworkings_applied: int
    n_final_poems: int
    brief_score: float
    fulfilled: bool
    not_fulfilled_reasons: List[str]
    library_size_original: int
    library_size_final: int
    provenance_coverage: float  # fraction of final lines with provenance recorded

    def report(self) -> str:
        lines = [
            f"Poetry Artifact: {self.brief_name}",
            f"  Composed: {self.composition_date.isoformat()}",
            f"  Sessions: {self.n_sessions} "
            f"({self.n_written_sessions} written, "
            f"{self.n_rest_sessions} rest/reflect)",
            f"  Simulations run: {self.n_simulations}",
            f"  Reworkings applied: {self.n_reworkings_applied}",
            f"  Final poems: {self.n_final_poems}",
            f"  Brief score: {self.brief_score:.2f}",
            f"  Fulfilled: {self.fulfilled}",
            f"  Library: {self.library_size_original} → "
            f"{self.library_size_final} fragments",
            f"  Provenance coverage: {self.provenance_coverage:.0%}",
        ]
        if self.not_fulfilled_reasons:
            lines.append("  Not fulfilled because:")
            for r in self.not_fulfilled_reasons:
                lines.append(f"    - {r}")
        return "\n".join(lines)


# =====================================================================
# Composite: PoetryArtifact
# =====================================================================

@dataclass
class PoetryArtifact:
    """The complete output of the FullAgent."""
    brief: Brief
    final_book: CompletedBook
    journal: Journal
    winning_trajectory: Trajectory
    provenance: Dict[str, ProvenanceEntry]
    metadata: ArtifactMetadata

    # -- reports -----------------------------------------------------

    def read(self) -> str:
        """The book itself, cleanly."""
        final = self.final_book.final_edition()
        if final is None:
            return "(no edition published)"
        lines = [f"\"{self.brief.name}\"", "=" * len(self.brief.name), ""]
        for poem in final.poems:
            lines.append(f"— {poem.name} —")
            for line in poem.all_lines():
                if line:
                    lines.append(f"  {line}")
            lines.append("")
        return "\n".join(lines)

    def journal_report(self) -> str:
        return self.journal.report()

    def provenance_report(self, n_samples: int = 5) -> str:
        """Show a sample of traced lines, plus coverage stats."""
        rewritten = [p for p in self.provenance.values() if p.is_rewritten]
        direct = [p for p in self.provenance.values() if not p.is_rewritten]
        lines = ["Provenance Chain:", ""]
        lines.append(f"  Total lines with recorded provenance: "
                     f"{len(self.provenance)}")
        lines.append(f"  Rewritten from source: {len(rewritten)}")
        lines.append(f"  Entered directly: {len(direct)}")
        lines.append("")
        if rewritten:
            lines.append("  Sample of rewritten lines:")
            for entry in rewritten[:n_samples]:
                lines.append("")
                for sub in entry.describe().split("\n"):
                    lines.append(f"    {sub}")
        return "\n".join(lines)

    def report(self) -> str:
        return "\n\n".join([
            self.metadata.report(),
            self.journal_report(),
            self.provenance_report(),
        ])

    # -- persistence -------------------------------------------------

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
            "final_book_path": path + ".book.json",
            "metadata": {
                "brief_name": self.metadata.brief_name,
                "composition_date": self.metadata.composition_date.isoformat(),
                "n_sessions": self.metadata.n_sessions,
                "n_written_sessions": self.metadata.n_written_sessions,
                "n_rest_sessions": self.metadata.n_rest_sessions,
                "n_simulations": self.metadata.n_simulations,
                "n_reworkings_applied": self.metadata.n_reworkings_applied,
                "n_final_poems": self.metadata.n_final_poems,
                "brief_score": self.metadata.brief_score,
                "fulfilled": self.metadata.fulfilled,
                "not_fulfilled_reasons": self.metadata.not_fulfilled_reasons,
                "library_size_original": self.metadata.library_size_original,
                "library_size_final": self.metadata.library_size_final,
                "provenance_coverage": self.metadata.provenance_coverage,
            },
            "provenance": {
                line: {
                    "line_text": p.line_text,
                    "first_seen_session": p.first_seen_session,
                    "first_seen_edition": p.first_seen_edition,
                    "source_fragment": p.source_fragment,
                    "reworking_chain": p.reworking_chain,
                    "reflection_chain": p.reflection_chain,
                }
                for line, p in self.provenance.items()
            },
        }
        # The book is saved as a separate artifact via its own serializer
        self.final_book.save(path + ".book.json")
        with open(path, "w") as f:
            json.dump(data, f, indent=2)

    @classmethod
    def load(cls, path: str) -> "PoetryArtifact":
        with open(path) as f:
            data = json.load(f)
        brief = Brief(
            name=data["brief"]["name"],
            voices=[VOICE_REGISTRY[n]
                    for n in data["brief"]["voice_names"]],
            arc_target=ArcType(data["brief"]["arc_target"]),
            refrain=data["brief"]["refrain"],
            n_poems_min=data["brief"]["n_poems_min"],
            n_poems_max=data["brief"]["n_poems_max"],
        )
        book = CompletedBook.load(data["final_book_path"])
        provenance = {
            line: ProvenanceEntry(
                line_text=p["line_text"],
                first_seen_session=p["first_seen_session"],
                first_seen_edition=p["first_seen_edition"],
                source_fragment=p["source_fragment"],
                reworking_chain=p["reworking_chain"],
                reflection_chain=p["reflection_chain"],
            )
            for line, p in data["provenance"].items()
        }
        md = data["metadata"]
        metadata = ArtifactMetadata(
            brief_name=md["brief_name"],
            composition_date=datetime.date.fromisoformat(
                md["composition_date"]),
            n_sessions=md["n_sessions"],
            n_written_sessions=md["n_written_sessions"],
            n_rest_sessions=md["n_rest_sessions"],
            n_simulations=md["n_simulations"],
            n_reworkings_applied=md["n_reworkings_applied"],
            n_final_poems=md["n_final_poems"],
            brief_score=md["brief_score"],
            fulfilled=md["fulfilled"],
            not_fulfilled_reasons=md["not_fulfilled_reasons"],
            library_size_original=md["library_size_original"],
            library_size_final=md["library_size_final"],
            provenance_coverage=md["provenance_coverage"],
        )
        # Journal is not persisted in this version (reconstructible from book)
        journal = Journal(brief=brief)
        return cls(
            brief=brief,
            final_book=book,
            journal=journal,
            winning_trajectory=Trajectory(seed=0),
            provenance=provenance,
            metadata=metadata,
        )


# =====================================================================
# Composite: FullAgent
# =====================================================================

class FullAgent:
    """The complete agent: brief in, artifact out.

    Pipeline:
      1. Run N simulation trajectories (C18)
      2. Pick the winning trajectory (highest frontier score)
      3. Build the expanded library from the winner
      4. Run the long run (C19) on the expanded library
      5. Track provenance across every line
      6. Return the complete artifact
    """

    def __init__(self, brief: Brief, fragments: List[Fragment],
                 seed: int = 0,
                 n_trajectories: int = 4,
                 cycles_per_trajectory: int = 2,
                 n_sessions: int = 20,
                 session_interval_days: int = 3,
                 start_date: Optional[datetime.date] = None):
        self.brief = brief
        self.fragments = fragments
        self.seed = seed
        self.n_trajectories = n_trajectories
        self.cycles_per_trajectory = cycles_per_trajectory
        self.n_sessions = n_sessions
        self.session_interval_days = session_interval_days
        self.start_date = start_date or datetime.date(2024, 1, 1)

    def _build_provenance(
        self,
        final_book: CompletedBook,
        winning_trajectory: Trajectory,
        fragment_index: Dict[str, Fragment],
        base_library_size: int,
    ) -> Dict[str, ProvenanceEntry]:
        """Trace every final line to its origin."""
        provenance: Dict[str, ProvenanceEntry] = {}

        # Build map: new line → reworking that produced it
        reworking_by_line: Dict[str, Reworking] = {}
        for rw in winning_trajectory.reworkings:
            for new_line in rw.new_lines:
                reworking_by_line[new_line] = rw

        # Build map: source fragment → which reworkings touched it
        final_edition = final_book.final_edition()
        if final_edition is None:
            return provenance

        for poem in final_edition.poems:
            for line in poem.all_lines():
                if not line or line in provenance:
                    continue
                # Was this line directly from the base library?
                if line in fragment_index:
                    provenance[line] = ProvenanceEntry(
                        line_text=line,
                        first_seen_session=1,   # entered with session 1
                        first_seen_edition=1,
                        source_fragment=line,
                    )
                    continue
                # Was it produced by a reworking?
                if line in reworking_by_line:
                    rw = reworking_by_line[line]
                    provenance[line] = ProvenanceEntry(
                        line_text=line,
                        first_seen_session=0,   # from a reflection session
                        first_seen_edition=1,
                        source_fragment=(rw.source_lines[0]
                                          if rw.source_lines else None),
                        reworking_chain=[rw.transformation_notes],
                        reflection_chain=[rw.reflection.observation],
                    )
                    continue
                # Unknown origin (shouldn't happen, but track it)
                provenance[line] = ProvenanceEntry(
                    line_text=line,
                    first_seen_session=-1,
                    first_seen_edition=-1,
                    source_fragment=None,
                )
        return provenance

    def compose(self) -> PoetryArtifact:
        # 1. Simulation phase — run trajectories, pick winner
        poet = ReflectivePoet(
            brief=self.brief,
            starting_library={k: [v] for k, v in
                              build_fragment_index(self.fragments).items()},
            seed=self.seed,
            n_trajectories=self.n_trajectories,
            cycles_per_trajectory=self.cycles_per_trajectory,
            composition_budget=2,
        )
        reflective_book = poet.compose()
        winning = reflective_book.winning_trajectory

        # 2. Long run phase — on the expanded library
        expanded_fragments = [
            f for variants in winning.expanded_library.values()
            for f in variants
        ]
        long_run = LongRun(
            brief=self.brief,
            fragments=expanded_fragments,
            seed=self.seed + 1,
            start_date=self.start_date,
            session_interval_days=self.session_interval_days,
            n_sessions=self.n_sessions,
            settle_after=3,
        )
        journal = long_run.run()
        final_book = journal.final_book()

        # 3. Provenance
        base_index = build_fragment_index(self.fragments)
        provenance = self._build_provenance(
            final_book=final_book,
            winning_trajectory=winning,
            fragment_index=base_index,
            base_library_size=len(base_index),
        )

        # 4. Metadata
        final_edition = final_book.final_edition()
        brief_score = (final_edition.brief_score
                       if final_edition else 0.0)
        analyzer = BriefAnalyzer()
        coll = Collection(
            name=self.brief.name,
            poems=list(final_edition.poems) if final_edition else [],
            refrain=self.brief.refrain,
        )
        brief_result = analyzer.analyze(coll, self.brief)
        fulfilled = brief_score >= 0.95

        not_fulfilled: List[str] = []
        if not fulfilled:
            if brief_result.voice_diversity < 0.95:
                not_fulfilled.append("voice diversity not met")
            if brief_result.arc_match < 0.95:
                actual = CollectionArcAnalyzer(coll).classify().value
                not_fulfilled.append(
                    f"arc: wanted {self.brief.arc_target.value}, "
                    f"got {actual}")
            if brief_result.refrain_in_every_poem < 0.95:
                not_fulfilled.append("refrain missing from some poems")
            if brief_result.count_in_range < 0.95:
                not_fulfilled.append(
                    f"poem count below minimum "
                    f"{self.brief.n_poems_min}")

        n_final_lines = (
            len([line for line in final_edition.all_lines() if line])
            if final_edition else 0)
        coverage = (len(provenance) / n_final_lines
                    if n_final_lines else 0.0)

        metadata = ArtifactMetadata(
            brief_name=self.brief.name,
            composition_date=self.start_date,
            n_sessions=len(journal),
            n_written_sessions=len(journal.written_sessions()),
            n_rest_sessions=len(journal.rest_sessions()),
            n_simulations=self.n_trajectories,
            n_reworkings_applied=len(winning.reworkings),
            n_final_poems=(final_edition.n_poems if final_edition else 0),
            brief_score=brief_score,
            fulfilled=fulfilled,
            not_fulfilled_reasons=not_fulfilled,
            library_size_original=len(base_index),
            library_size_final=sum(len(v)
                                    for v in winning.expanded_library.values()),
            provenance_coverage=coverage,
        )

        return PoetryArtifact(
            brief=self.brief,
            final_book=final_book,
            journal=journal,
            winning_trajectory=winning,
            provenance=provenance,
            metadata=metadata,
        )

    @classmethod
    def from_saved(cls, path: str,
                   fragments: List[Fragment]
                   ) -> Tuple["FullAgent", PoetryArtifact]:
        artifact = PoetryArtifact.load(path)
        agent = cls(
            brief=artifact.brief,
            fragments=fragments,
            seed=0,
            n_trajectories=0,
            cycles_per_trajectory=0,
            n_sessions=0,
        )
        return agent, artifact


# =====================================================================
# Convenience
# =====================================================================

def compose_between_sessions(seed: int = 42,
                              n_sessions: int = 20) -> PoetryArtifact:
    """The full pipeline on 'Between Sessions' — the C17 brief."""
    brief = Brief(
        name="Between Sessions",
        voices=[VOICE_CLINICAL, VOICE_GHOST, VOICE_MANY],
        arc_target=ArcType.PALINDROME,
        refrain="between sessions, this remains",
        n_poems_min=9,
        n_poems_max=12,
    )
    agent = FullAgent(
        brief=brief,
        fragments=FRAGMENTS,
        seed=seed,
        n_trajectories=4,
        cycles_per_trajectory=2,
        n_sessions=n_sessions,
        session_interval_days=3,
        start_date=datetime.date(2024, 1, 1),
    )
    return agent.compose()

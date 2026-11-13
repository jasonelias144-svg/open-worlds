"""
poetry_engine_c19.py — Component 19: The long run.

ARCHITECTURE — designed for implementation, not executed in this session.

A long run is a sequence of sessions. Each session is a bounded
period of work — sometimes writing, sometimes reflecting, sometimes
resting. The book develops across sessions. The journal records
what happened. The artifact is book + journal.

Depends on Components 1-18.
"""

import datetime
import random
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Tuple

from poetry_engine_c5 import (
    VoiceSpecification, Fragment, FRAGMENTS,
    VOICE_CLINICAL, VOICE_GHOST, VOICE_MANY,
)
from poetry_engine_c9 import ArcType, CollectionArcAnalyzer
from poetry_engine_c14 import Brief, BriefAnalyzer, default_brief
from poetry_engine_c17 import CompletedBook, PoetryAgent
from poetry_engine_c18 import (
    Reflection, Reworking, Trajectory,
    ReflectivePoet, ReflectiveBook,
)


# =====================================================================
# Atom 1: SessionPhase
# =====================================================================

class SessionPhase(Enum):
    """What the session tried to do."""
    COMPOSE = "compose"      # add new poems to the book
    REVISE = "revise"        # edit existing poems
    REFLECT = "reflect"      # run simulation, no publishing
    REST = "rest"            # no work on the book
    SETTLE = "settle"        # confirm the work has converged


# =====================================================================
# Atom 2: SessionPosture
# =====================================================================

class SessionPosture(Enum):
    """The state the session was in, derived from its outcome.

    Postures are observed, not declared. A session is EAGER if it
    moved the score substantially; STRUGGLING if it tried and failed;
    PATIENT if it made small changes; SETTLED if it declared the work
    done.
    """
    EAGER = "eager"
    STRUGGLING = "struggling"
    PATIENT = "patient"
    SETTLED = "settled"


# =====================================================================
# Atom 3: Session
# =====================================================================

@dataclass
class Session:
    number: int
    date: datetime.date
    phase: SessionPhase
    posture: SessionPosture
    work_before: CompletedBook
    work_after: CompletedBook
    reflections: List[Reflection] = field(default_factory=list)
    reworkings: List[Reworking] = field(default_factory=list)
    duration_minutes: int = 90
    notes: str = ""

    # -- deltas ------------------------------------------------------

    @property
    def delta_editions(self) -> int:
        return max(0, len(self.work_after.editions)
                   - len(self.work_before.editions))

    @property
    def delta_score(self) -> float:
        before = (self.work_before.final_edition().brief_score
                  if self.work_before.editions else 0.0)
        after = (self.work_after.final_edition().brief_score
                 if self.work_after.editions else 0.0)
        return after - before

    @property
    def delta_lines(self) -> int:
        before_lines = (len(self.work_before.final_edition().all_lines())
                        if self.work_before.editions else 0)
        after_lines = (len(self.work_after.final_edition().all_lines())
                       if self.work_after.editions else 0)
        return after_lines - before_lines

    def report(self) -> str:
        return (
            f"session {self.number:02d} | {self.date.isoformat()} | "
            f"{self.phase.value:>8} | {self.posture.value:>10} | "
            f"Δscore={self.delta_score:+.3f} "
            f"Δlines={self.delta_lines:+d} "
            f"Δeditions={self.delta_editions} | {self.notes}"
        )


# =====================================================================
# Atom 4: SimulatedCalendar
# =====================================================================

@dataclass
class SimulatedCalendar:
    """The honest fiction of the long run's time.

    Session N happens on start_date + (N * session_interval_days).
    Between sessions, the agent is not working — that's the rest.
    """
    start_date: datetime.date
    session_interval_days: int = 3

    def date_of_session(self, session_number: int) -> datetime.date:
        return self.start_date + datetime.timedelta(
            days=session_number * self.session_interval_days)


# =====================================================================
# Composite: Journal
# =====================================================================

@dataclass
class Journal:
    """The running record of the long run."""
    brief: Brief
    sessions: List[Session] = field(default_factory=list)

    def __len__(self):
        return len(self.sessions)

    def final_book(self) -> Optional[CompletedBook]:
        return self.sessions[-1].work_after if self.sessions else None

    def trajectory(self) -> List[float]:
        """Brief score per session."""
        return [
            (s.work_after.final_edition().brief_score
             if s.work_after.editions else 0.0)
            for s in self.sessions
        ]

    def written_sessions(self) -> List[Session]:
        return [s for s in self.sessions
                if s.phase in (SessionPhase.COMPOSE, SessionPhase.REVISE)]

    def rest_sessions(self) -> List[Session]:
        return [s for s in self.sessions
                if s.phase in (SessionPhase.REST, SessionPhase.REFLECT)]

    def posture_counts(self) -> Dict[SessionPosture, int]:
        counts: Dict[SessionPosture, int] = {p: 0 for p in SessionPosture}
        for s in self.sessions:
            counts[s.posture] += 1
        return counts

    def report(self, brief_report: bool = True) -> str:
        lines = []
        if brief_report:
            lines.append(f"Journal: {self.brief.name}")
            if self.sessions:
                lines.append(f"  Period: "
                             f"{self.sessions[0].date.isoformat()} to "
                             f"{self.sessions[-1].date.isoformat()}")
            lines.append(f"  Sessions: {len(self.sessions)}")
            lines.append(f"  Written sessions: "
                         f"{len(self.written_sessions())}")
            lines.append(f"  Rest/reflect sessions: "
                         f"{len(self.rest_sessions())}")
            counts = self.posture_counts()
            lines.append("  Postures:")
            for p, n in counts.items():
                lines.append(f"    {p.value}: {n}")
            lines.append("")
        lines.append("Sessions:")
        for s in self.sessions:
            lines.append(f"  {s.report()}")
        return "\n".join(lines)


# =====================================================================
# Composite: SessionRunner
# =====================================================================

class SessionRunner:
    """Runs one session of the long run.

    Decides the phase (based on the current state and recent history),
    executes it, records the outcome, derives the posture.
    """

    def __init__(self, brief: Brief, fragments: List[Fragment],
                 seed: int = 0):
        self.brief = brief
        self.fragments = fragments
        self.rng = random.Random(seed)

    def _decide_phase(self, book: Optional[CompletedBook],
                      recent: List[Session]) -> SessionPhase:
        """The agent's choice of what to do this session.

        Simple honest state machine:
          - No book yet → COMPOSE
          - Last 2 sessions had no score change → SETTLE
          - Last 1 session had no change → REST (let it settle)
          - Prior session was REST and didn't help → REFLECT
          - Prior session was REFLECT and produced reworkings → COMPOSE
          - Otherwise → REVISE (try refinement)
        """
        if book is None or not book.editions:
            return SessionPhase.COMPOSE
        last = recent[-1] if recent else None
        last2 = recent[-2] if len(recent) >= 2 else None

        if last and last2 and abs(last.delta_score) < 1e-9 \
                and abs(last2.delta_score) < 1e-9:
            return SessionPhase.SETTLE
        if last and abs(last.delta_score) < 1e-9 \
                and last.phase not in (SessionPhase.REST,
                                        SessionPhase.REFLECT):
            return SessionPhase.REST
        if last and last.phase == SessionPhase.REST \
                and abs(last.delta_score) < 1e-9:
            return SessionPhase.REFLECT
        if last and last.phase == SessionPhase.REFLECT \
                and last.reworkings:
            return SessionPhase.COMPOSE
        return SessionPhase.REVISE

    def _decide_posture(self, session: Session) -> SessionPosture:
        """Derive the posture from the session's actual outcome."""
        if session.phase == SessionPhase.SETTLE:
            return SessionPosture.SETTLED
        if session.delta_score > 0.02:
            return SessionPosture.EAGER
        if session.delta_score > 0:
            return SessionPosture.PATIENT
        if session.phase in (SessionPhase.REFLECT, SessionPhase.REVISE,
                              SessionPhase.COMPOSE):
            return SessionPosture.STRUGGLING
        return SessionPosture.PATIENT

    def _execute(self, phase: SessionPhase,
                 book: Optional[CompletedBook],
                 n_editions: int = 2) -> Tuple[CompletedBook,
                                                 List[Reflection],
                                                 List[Reworking]]:
        """Run the phase, return (new_book, reflections, reworkings)."""
        if phase == SessionPhase.SETTLE:
            return book, [], []

        if phase == SessionPhase.REST:
            return book, [], []

        if phase == SessionPhase.REFLECT:
            # Run a simulation, extract reworkings but don't publish
            poet = ReflectivePoet(
                brief=self.brief,
                starting_library=self._to_library(book),
                seed=self.rng.randint(0, 10**9),
                n_trajectories=3,
                cycles_per_trajectory=2,
                composition_budget=1,
            )
            reflective_book = poet.compose()
            return (
                book,
                reflective_book.winning_trajectory.reflections,
                reflective_book.winning_trajectory.reworkings,
            )

        # COMPOSE or REVISE: run the agent
        agent = PoetryAgent(
            brief=self.brief,
            fragments=self.fragments,
            seed=self.rng.randint(0, 10**9),
            budget_per_poem=15,
            patience_per_poem=3,
            max_rests_per_poem=2,
        )
        new_book = agent.compose(
            n_editions=n_editions,
            cycles_per_edition=3,
            converge=True,
        )
        return new_book, [], []

    def _to_library(self, book: Optional[CompletedBook]
                    ) -> Dict[str, List[Fragment]]:
        """Reconstruct a library from a book (best-effort)."""
        # For simplicity: use the original fragment library
        from poetry_engine_c9 import build_fragment_index
        return {k: [v] for k, v in build_fragment_index(
            self.fragments).items()}

    def run(self, session_number: int, date: datetime.date,
            book: Optional[CompletedBook],
            recent: List[Session]) -> Session:
        phase = self._decide_phase(book, recent)
        new_book, reflections, reworkings = self._execute(phase, book)
        session = Session(
            number=session_number,
            date=date,
            phase=phase,
            posture=SessionPosture.PATIENT,  # placeholder, set below
            work_before=book,
            work_after=new_book,
            reflections=reflections,
            reworkings=reworkings,
        )
        session.posture = self._decide_posture(session)
        session.notes = self._compose_note(session)
        return session

    def _compose_note(self, session: Session) -> str:
        if session.phase == SessionPhase.SETTLE:
            return "work has settled"
        if session.phase == SessionPhase.REST:
            return "let the work sit"
        if session.phase == SessionPhase.REFLECT:
            return f"reflected; {len(session.reworkings)} reworkings"
        if session.delta_score > 0.02:
            return f"composed well; +{session.delta_lines} lines"
        if session.delta_score > 0:
            return f"small change; +{session.delta_lines} lines"
        if session.phase == SessionPhase.REVISE:
            return "no improvement in revision"
        return "no change"


# =====================================================================
# Composite: LongRun
# =====================================================================

class LongRun:
    """The long run: N sessions over simulated time.

    In-process. The agent runs to completion in one call. Each
    session is a simulated period of work; between sessions is
    simulated rest (3 days, by default).
    """

    def __init__(self, brief: Brief, fragments: List[Fragment],
                 seed: int = 0,
                 start_date: Optional[datetime.date] = None,
                 session_interval_days: int = 3,
                 n_sessions: int = 40,
                 settle_after: int = 5):
        self.brief = brief
        self.fragments = fragments
        self.seed = seed
        self.start_date = start_date or datetime.date(2024, 1, 1)
        self.calendar = SimulatedCalendar(
            start_date=self.start_date,
            session_interval_days=session_interval_days,
        )
        self.n_sessions = n_sessions
        self.settle_after = settle_after
        self.runner = SessionRunner(
            brief=brief, fragments=fragments, seed=seed)
        self.journal = Journal(brief=brief)

    def run(self) -> Journal:
        book: Optional[CompletedBook] = None
        recent: List[Session] = []
        consecutive_settles = 0

        for i in range(self.n_sessions):
            date = self.calendar.date_of_session(i)
            session = self.runner.run(
                session_number=i + 1,
                date=date,
                book=book,
                recent=recent,
            )
            self.journal.sessions.append(session)
            book = session.work_after
            recent.append(session)
            if session.phase == SessionPhase.SETTLE:
                consecutive_settles += 1
                if consecutive_settles >= self.settle_after:
                    break
            else:
                consecutive_settles = 0

        return self.journal


# =====================================================================
# Convenience
# =====================================================================

def run_between_sessions_long_run(seed: int = 42,
                                    n_sessions: int = 40) -> Journal:
    """The long run of 'Between Sessions' — same brief as C17's real run."""
    brief = Brief(
        name="Between Sessions",
        voices=[VOICE_CLINICAL, VOICE_GHOST, VOICE_MANY],
        arc_target=ArcType.PALINDROME,
        refrain="between sessions, this remains",
        n_poems_min=9,
        n_poems_max=12,
    )
    run = LongRun(
        brief=brief,
        fragments=FRAGMENTS,
        seed=seed,
        start_date=datetime.date(2024, 1, 1),
        session_interval_days=3,
        n_sessions=n_sessions,
        settle_after=5,
    )
    return run.run()

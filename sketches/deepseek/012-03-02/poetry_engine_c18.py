"""
poetry_engine_c18.py — Component 18: The reflective rewriting cycle.

ARCHITECTURE — designed for implementation, not executed in this session.

Depends on Components 1-17.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Tuple

from poetry_engine_c5 import VoiceSpecification, Fragment, FRAGMENTS
from poetry_engine_c9 import Collection, CollectionPoem, ArcType
from poetry_engine_c14 import Brief, Edition, BriefAnalyzer
from poetry_engine_c17 import CompletedBook, PoetryAgent


class ReflectionKind(Enum):
    """What kind of pattern was noticed."""
    RECURRENCE = "recurrence"          # a phrase/schema overused
    GAP = "gap"                        # a schema/topic absent
    VOICE_IMBALANCE = "voice_imbalance"
    REFRAIN_DRIFT = "refrain_drift"    # refrain echoes, not returns
    REGISTER = "register"              # monotonous texture
    BRIEF_DEVIATION = "brief_deviation"  # a brief requirement unmet


@dataclass
class Reflection:
    """A meta-observation about the work-in-progress.

    The reflection is a *finding*, not a fix. It says what it noticed.
    The reworking phase decides what to do about it.
    """
    kind: ReflectionKind
    observation: str              # prose description of the pattern
    evidence: List[str]           # concrete instances in the work
    suggested_direction: str      # what the reworking might address
    confidence: float             # 0-1, how sure the reflection engine is


@dataclass
class Reworking:
    """A transformation of existing fragments in response to a reflection.

    The reworking is the *expression* of the reflection: it turns what
    the framework noticed into what the framework makes in response.
    """
    reflection: Reflection
    source_lines: List[str]       # lines the reworking transforms
    new_lines: List[str]          # lines the reworking produces
    transformation_notes: str     # prose on what was done and why
    voice_affinity: str           # which voice the new lines belong to
    schemas: Tuple[str, ...]      # schemas active in the new lines


@dataclass
class Trajectory:
    """One simulation of the reflection-composition cycle.

    A trajectory is a *what-if*: if we acted on these reflections,
    reworked these fragments, and composed again, what would emerge?
    """
    seed: int
    reflections: List[Reflection] = field(default_factory=list)
    reworkings: List[Reworking] = field(default_factory=list)
    expanded_library: Dict[str, List[Fragment]] = field(default_factory=dict)
    composition: Optional[CompletedBook] = None
    brief_score: float = 0.0
    library_growth: int = 0       # new fragments added
    frontier_score: float = 0.0   # composite of the above


class ReflectionEngine:
    """Examines a work, produces Reflections.

    Not a critic. A noticer. It reports patterns it sees; it does not
    judge the work. The judgment (what to rework) happens later.
    """

    def reflect(self, collection: Collection, brief: Brief,
                fragment_index: Dict[str, Fragment]) -> List[Reflection]:
        reflections: List[Reflection] = []
        reflections.extend(self._check_brief_deviation(collection, brief))
        reflections.extend(self._check_recurrence(collection))
        reflections.extend(self._check_gaps(collection))
        reflections.extend(self._check_refrain_drift(collection, brief))
        reflections.extend(self._check_register(collection))
        reflections.extend(self._check_voice_imbalance(collection, brief))
        return reflections

    def _check_brief_deviation(self, collection, brief):
        """Detect requirements in the brief that the work doesn't meet."""
        analyzer = BriefAnalyzer()
        score = analyzer.analyze(collection, brief)
        out = []
        if score.arc_match < 0.95:
            actual = __import__("poetry_engine_c9").CollectionArcAnalyzer(
                collection).classify().value
            out.append(Reflection(
                kind=ReflectionKind.BRIEF_DEVIATION,
                observation=(f"Brief asked for {brief.arc_target.value} arc; "
                              f"work is {actual}"),
                evidence=[p.name for p in collection.poems],
                suggested_direction=(f"Rework the closing poems so they "
                                       f"return to the opening voice's "
                                       f"register"),
                confidence=0.9,
            ))
        # ... voice diversity, refrain, count checks similarly
        return out

    def _check_recurrence(self, collection):
        """Detect overused phrases/schemas."""
        # Count phrase frequencies across the whole work
        # Report any phrase appearing > N times
        ...

    def _check_gaps(self, collection):
        """Detect schemas the work never activates."""
        # Compare against the FULL schema vocabulary
        # Report schemas with 0 activations
        ...

    # _check_refrain_drift, _check_register, _check_voice_imbalance
    # follow the same pattern: observe, describe, suggest direction


class ReworkingEngine:
    """Takes a reflection, produces reworked fragments.

    The reworking engine is where expression happens. Given a
    reflection, it produces new fragments that *respond to* what the
    reflection noticed. It does not invent from nothing — it reworks.
    """

    def __init__(self, voice_registry: Dict[str, VoiceSpecification]):
        self.voice_registry = voice_registry

    def rework(self, reflection: Reflection,
               current_work: Collection,
               fragment_index: Dict[str, Fragment],
               voices_to_try: List[str]) -> List[Reworking]:
        """For each voice, try to produce a reworking that addresses
        the reflection."""
        reworkings: List[Reworking] = []
        for voice_name in voices_to_try:
            rw = self._rework_for_voice(
                reflection, current_work, fragment_index, voice_name)
            if rw is not None:
                reworkings.append(rw)
        return reworkings

    def _rework_for_voice(self, reflection, work, index, voice_name):
        """Produce one reworking in the given voice.

        The reworkable strategies depend on the reflection kind:
          - RECURRENCE → rework an overused line into a variant
          - GAP → rework an existing line to activate the missing schema
          - BRIEF_DEVIATION → rework a closing line to address the arc
          - REGISTER → dilate or compress an existing line
          - VOICE_IMBALANCE → rework a line from one voice into another
        """
        # The actual reworking machinery depends on the C7 transformers,
        # extended with a few new ones (see below).
        ...


class SimulationLoop:
    """Runs N trajectories in-process, returns the best.

    Each trajectory:
      1. Starts from a shared library.
      2. Runs K cycles of (reflect → rework → compose → score).
      3. Returns a Trajectory with reflections, reworkings, and a book.

    The loop runs trajectories sequentially (or interleaved) and
    consolidates the highest-scoring one. It is pure Python — no
    external environment, no separate process.
    """

    def __init__(self, poetry_agent: PoetryAgent,
                 reflection_engine: ReflectionEngine,
                 reworking_engine: ReworkingEngine):
        self.agent = poetry_agent
        self.reflector = reflection_engine
        self.reworker = reworking_engine

    def simulate(self,
                 brief: Brief,
                 starting_library: Dict[str, List[Fragment]],
                 n_trajectories: int = 5,
                 cycles_per_trajectory: int = 3,
                 composition_budget: int = 4) -> List[Trajectory]:
        trajectories: List[Trajectory] = []
        for t_idx in range(n_trajectories):
            trajectory = self._run_one_trajectory(
                brief=brief,
                starting_library=starting_library,
                seed=hash((t_idx, brief.name)) % (2**31),
                n_cycles=cycles_per_trajectory,
                composition_budget=composition_budget,
            )
            trajectories.append(trajectory)
        trajectories.sort(key=lambda t: t.frontier_score, reverse=True)
        return trajectories

    def _run_one_trajectory(self, brief, starting_library, seed, n_cycles,
                             composition_budget) -> Trajectory:
        """One trajectory: K cycles of reflect → rework → compose."""
        trajectory = Trajectory(seed=seed)
        library = {k: list(v) for k, v in starting_library.items()}
        baseline_size = sum(len(v) for v in library.values())

        for cycle in range(n_cycles):
            # 1. Compose a draft book from the current library
            agent = PoetryAgent(
                brief=brief,
                fragments=self._flatten_library(library),
                seed=seed + cycle,
            )
            draft = agent.compose(
                n_editions=composition_budget,
                cycles_per_edition=3,
                converge=True,
            )

            # 2. Reflect on the draft
            index = self._build_index(library)
            reflections = self.reflector.reflect(
                self._last_collection(draft), brief, index)
            trajectory.reflections.extend(reflections)

            # 3. Rework based on the reflections
            for refl in reflections:
                reworkings = self.reworker.rework(
                    refl,
                    self._last_collection(draft),
                    index,
                    voices_to_try=[v.name for v in brief.voices],
                )
                for rw in reworkings:
                    self._add_to_library(library, rw)
                    trajectory.reworkings.append(rw)

            # 4. If no reworkings, we've converged on this trajectory
            if not reflections:
                break

        # 5. Final composition from the expanded library
        agent = PoetryAgent(
            brief=brief,
            fragments=self._flatten_library(library),
            seed=seed + n_cycles,
        )
        final = agent.compose(
            n_editions=composition_budget,
            cycles_per_edition=3,
            converge=True,
        )
        trajectory.composition = final
        trajectory.expanded_library = library
        trajectory.brief_score = (final.final_edition().brief_score
                                   if final.editions else 0.0)
        trajectory.library_growth = (
            sum(len(v) for v in library.values()) - baseline_size)
        # Frontier score: brief fulfillment + library growth, normalized
        growth_norm = min(1.0, trajectory.library_growth / 50.0)
        trajectory.frontier_score = (
            0.75 * trajectory.brief_score + 0.25 * growth_norm)
        return trajectory


class ReflectivePoet:
    """The agent. Brief in, simulated-and-expanded book out."""

    def __init__(self, brief: Brief,
                 starting_library: Dict[str, List[Fragment]],
                 seed: int = 0,
                 n_trajectories: int = 5,
                 cycles_per_trajectory: int = 3,
                 composition_budget: int = 4):
        self.brief = brief
        self.starting_library = starting_library
        self.seed = seed
        self.simulation_loop = SimulationLoop(
            poetry_agent=PoetryAgent(
                brief=brief,
                fragments=self._flatten(starting_library),
                seed=seed,
            ),
            reflection_engine=ReflectionEngine(),
            reworking_engine=ReworkingEngine(voice_registry=VOICE_REGISTRY),
        )
        self.n_trajectories = n_trajectories
        self.cycles_per_trajectory = cycles_per_trajectory
        self.composition_budget = composition_budget

    def compose(self) -> "ReflectiveBook":
        """Run simulation, consolidate, publish the final book."""
        trajectories = self.simulation_loop.simulate(
            brief=self.brief,
            starting_library=self.starting_library,
            n_trajectories=self.n_trajectories,
            cycles_per_trajectory=self.cycles_per_trajectory,
            composition_budget=self.composition_budget,
        )
        winner = trajectories[0]
        # Compose the final book from the winning trajectory's library
        final_agent = PoetryAgent(
            brief=self.brief,
            fragments=self._flatten(winner.expanded_library),
            seed=self.seed,
        )
        final_book = final_agent.compose(
            n_editions=6, cycles_per_edition=3, converge=True)
        return ReflectiveBook(
            book=final_book,
            winning_trajectory=winner,
            all_trajectories=trajectories,
            n_fragments_original=sum(
                len(v) for v in self.starting_library.values()),
            n_fragments_final=sum(
                len(v) for v in winner.expanded_library.values()),
        )


@dataclass
class ReflectiveBook:
    """The final artifact: a book, plus the trajectory that produced it."""
    book: CompletedBook
    winning_trajectory: Trajectory
    all_trajectories: List[Trajectory]
    n_fragments_original: int
    n_fragments_final: int

    def report(self) -> str:
        lines = [
            self.book.metadata().report(),
            "",
            f"Simulation summary:",
            f"  Trajectories run: {len(self.all_trajectories)}",
            f"  Library size: {self.n_fragments_original} → "
            f"{self.n_fragments_final} fragments",
            f"  Winning trajectory score: "
            f"{self.winning_trajectory.frontier_score:.3f}",
            f"  Reflections acted on: "
            f"{len(self.winning_trajectory.reworkings)}",
            "",
            "Trajectory comparison:",
        ]
        for i, t in enumerate(self.all_trajectories):
            lines.append(
                f"  #{i + 1}: brief={t.brief_score:.3f}, "
                f"growth=+{t.library_growth}, "
                f"frontier={t.frontier_score:.3f}")
        return "\n".join(lines)

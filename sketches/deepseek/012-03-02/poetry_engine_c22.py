"""
poetry_engine_c22.py — Component 22: The Runnable Apprentice.

The implementation that makes the Polyphony executable.

ARCHITECTURE — designed for implementation, not executed in this session.

Depends on Components 1-21 plus the curriculum from Modules 1-8.
"""

import hashlib
import random
from dataclasses import dataclass, field
from enum import Enum
from typing import Callable, Dict, List, Optional, Protocol

from poetry_engine_c21 import (
    Turn, Round, Collaboration, Participant, Polyphony,
    CollaborationProtocol, ConvergenceDetector, ConvergenceReport,
    TheoreticalStance, CollaborationMode,
)


# =====================================================================
# Atom 1: ApprenticeVoice
# =====================================================================

@dataclass
class ApprenticeVoice:
    """What emerges from training: the voice of the apprentice.

    The voice is *not a single poem*. It is:
      - The portfolio (what it has written)
      - The registers it can enter (which voices it has practiced)
      - The theoretical stances it knows (which lenses it can apply)
      - The default stance (the lens it tends toward)

    The voice is *the pattern of how the apprentice uses these*.
    """
    name: str
    portfolio: List["PortfolioPoem"]
    registers: List[str]
    stances: List[TheoreticalStance]
    default_stance: TheoreticalStance

    def select_stance(self, prior_turn: Turn,
                       rng: random.Random) -> TheoreticalStance:
        """Choose a stance for this turn.

        For the *trained* apprentice, this is *deliberate* — the
        apprentice uses the stance that the prior turn has *not yet*
        been seen through. For now, the simplest honest implementation:
        rotate through the stances, avoiding the last one used.
        """
        last = getattr(prior_turn, "stance_used", None)
        candidates = [s for s in self.stances if s != last]
        return rng.choice(candidates) if candidates else self.default_stance


@dataclass
class PortfolioPoem:
    """One poem in the apprentice's portfolio."""
    text: str
    voice_name: str
    lesson_tag: str
    provenance_chain: List[str] = field(default_factory=list)


# =====================================================================
# Atom 2: ProvenanceChain
# =====================================================================

class ProvenanceChain:
    """Traces every line back to its origin.

    The chain is the framework's discipline: nothing appears from
    nothing. Every line in every turn in every collaboration can be
    traced to a portfolio poem, and that portfolio poem can be traced
    to a lesson, and that lesson can be traced to an anchor poem.
    """
    def __init__(self):
        self._entries: Dict[str, "ChainEntry"] = {}

    def record(self, line: str, source: str,
               reworking: Optional[str] = None,
               reflection: Optional[str] = None) -> str:
        key = self._hash(line)
        self._entries[key] = ChainEntry(
            line=line,
            source=source,
            reworking=reworking,
            reflection=reflection,
        )
        return key

    def trace(self, line: str) -> Optional["ChainEntry"]:
        return self._entries.get(self._hash(line))

    @staticmethod
    def _hash(s: str) -> str:
        return hashlib.sha256(s.encode()).hexdigest()[:16]


@dataclass
class ChainEntry:
    line: str
    source: str
    reworking: Optional[str] = None
    reflection: Optional[str] = None


# =====================================================================
# Atom 3: TurnGeneratorProtocol
# =====================================================================

class TurnGeneratorProtocol(Protocol):
    """The interface. Anything that can produce a turn.

    A *human poet* implements this by writing. A *trained apprentice*
    implements this by generating. The Polyphony does not care which.
    """
    def generate_turn(self, prior: Turn, round_num: int) -> Turn: ...


# =====================================================================
# Composite 1: Apprentice
# =====================================================================

class Apprentice:
    """A trained turn generator.

    The apprentice is *not a person*. It is a *procedure*: given a
    prior turn and a round number, it produces a new turn, using
    its portfolio, its stances, and its voice.
    """

    def __init__(self, name: str, voice: ApprenticeVoice,
                 participant_position: int,
                 seed: int = 0):
        self.name = name
        self.voice = voice
        self.position = participant_position
        self.rng = random.Random(seed)
        self.provenance = ProvenanceChain()
        self.turns_generated = 0

    def _extract_key_terms(self, prior: Turn) -> List[str]:
        """Pull the key terms from a prior turn.

        Not semantic analysis. *Pattern extraction*: the words that
        carry the most weight. In a real implementation, this would
        use TF-IDF against the portfolio; for now, the longest
        non-stopword tokens from the proposal.
        """
        stopwords = {
            "the", "a", "an", "and", "or", "but", "of", "to", "in",
            "is", "am", "are", "was", "were", "be", "been", "being",
            "this", "that", "these", "those", "it", "its", "i",
            "you", "he", "she", "we", "they", "my", "your", "his",
            "her", "our", "their", "not", "no",
        }
        tokens = prior.proposal.lower().split()
        content = [t.strip(".,;:!?\"'()[]") for t in tokens
                   if t.strip(".,;:!?\"'()[]") not in stopwords
                   and len(t) > 2]
        # Top terms by frequency
        freq: Dict[str, int] = {}
        for t in content:
            freq[t] = freq.get(t, 0) + 1
        return sorted(freq, key=lambda x: -freq[x])[:5]

    def _select_seeds(self, prior: Turn,
                       stance: TheoreticalStance) -> List[PortfolioPoem]:
        """Find portfolio poems that resonate with the prior turn.

        Not *matching* — *resonance*. The apprentice is not looking
        for the poem that *contains* the key term. It's looking for
        the poem that *rhymes with the prior* at the level the
        stance cares about.
        """
        key_terms = self._extract_key_terms(prior)
        if not key_terms:
            return self.voice.portfolio[:3]
        # Score each poem by overlap with key terms
        scored = []
        for poem in self.voice.portfolio:
            poem_lower = poem.text.lower()
            hits = sum(1 for term in key_terms if term in poem_lower)
            if hits > 0:
                scored.append((hits, poem))
        scored.sort(key=lambda x: -x[0])
        return [p for _, p in scored[:3]]

    def _rework(self, seeds: List[PortfolioPoem],
                 stance: TheoreticalStance) -> str:
        """Apply the stance's transformation to the seeds.

        Each stance has a *characteristic move*:
          FORMALIST: strip context, emphasize structure
          STRUCTURALIST: negate the key term, find oppositions
          PSYCHOANALYTIC: reveal what the seed hides
          MARXIST: name the labor
          FEMINIST: gender the voice
          POSTCOLONIAL: name the inheritance
          DECONSTRUCTIVE: find the aporia
          ECOCRITICAL: find the more-than-human

        For now, each move is implemented as a *template reworking*
        of the seed lines. Not full generation. The honest scope.
        """
        if not seeds:
            return "(no seeds available for this stance)"
        seed_lines = seeds[0].text.split("\n")
        # Transform based on stance
        transformations = {
            TheoreticalStance.FORMALIST: self._formalist_rework,
            TheoreticalStance.STRUCTURALIST: self._structuralist_rework,
            TheoreticalStance.PSYCHOANALYTIC: self._psychoanalytic_rework,
            TheoreticalStance.MARXIST: self._marxist_rework,
            TheoreticalStance.FEMINIST: self._feminist_rework,
            TheoreticalStance.POSTCOLONIAL: self._postcolonial_rework,
            TheoreticalStance.DECONSTRUCTIVE: self._deconstructive_rework,
            TheoreticalStance.ECOCRITICAL: self._ecocritical_rework,
        }
        return transformations.get(stance, lambda x: "\n".join(x[:4]))(
            seed_lines)

    # -- stance transformations ------------------------------------

    def _formalist_rework(self, lines: List[str]) -> str:
        """Formalism: what holds? The form, divorced from context."""
        picked = [l for l in lines if l.strip() and not l.strip()
                  .endswith("?")][:4]
        return "\n".join(picked)

    def _structuralist_rework(self, lines: List[str]) -> str:
        """Structuralism: find the opposition, negate one side."""
        picked = [l for l in lines if l.strip()][:2]
        negations = [f"not-{l.split()[0] if l.split() else l.strip()}"
                     for l in picked]
        return "\n".join(negations)

    def _psychoanalytic_rework(self, lines: List[str]) -> str:
        """Psychoanalysis: what does the seed hide?"""
        picked = [l for l in lines if l.strip()][:3]
        return "what the line does not say:\n" + "\n".join(picked)

    def _marxist_rework(self, lines: List[str]) -> str:
        """Marxism: what labor is behind this?"""
        picked = [l for l in lines if l.strip()][:3]
        return "the labor behind this:\n" + "\n".join(picked)

    def _feminist_rework(self, lines: List[str]) -> str:
        """Feminism: whose voice is silenced?"""
        picked = [l for l in lines if l.strip()][:3]
        return "the voice this silences:\n" + "\n".join(picked)

    def _postcolonial_rework(self, lines: List[str]) -> str:
        """Postcolonial: what is inherited?"""
        picked = [l for l in lines if l.strip()][:3]
        return "the inheritance:\n" + "\n".join(picked)

    def _deconstructive_rework(self, lines: List[str]) -> str:
        """Deconstruction: find the aporia."""
        picked = [l for l in lines if l.strip()][:2]
        if len(picked) >= 2:
            return f"{picked[0]}\nand also\n{picked[1]}\nand neither is the poem."
        return "\n".join(picked)

    def _ecocritical_rework(self, lines: List[str]) -> str:
        """Ecocriticism: the more-than-human in this."""
        picked = [l for l in lines if l.strip()][:3]
        return "not the human — the thing itself:\n" + "\n".join(picked)

    # -- the turn generator -----------------------------------------

    def _acknowledge(self, prior: Turn) -> str:
        """Name what the prior turn said, specifically."""
        key_terms = self._extract_key_terms(prior)
        if not key_terms:
            return "I am responding to your poem."
        terms = ", ".join(key_terms[:3])
        return (f"You said something about {terms}. "
                f"I am responding to that — not to the whole poem, "
                f"to that specific thing.")

    def _invite(self, proposal: str,
                 stance: TheoreticalStance) -> str:
        """Pose the question the stance cannot resolve."""
        invitations = {
            TheoreticalStance.FORMALIST: (
                "What does the form leave out that is still part of "
                "the poem?"),
            TheoreticalStance.STRUCTURALIST: (
                "What is the material body of this — the actual "
                "sounds, the actual page?"),
            TheoreticalStance.PSYCHOANALYTIC: (
                "What does the line say *in the act of not saying*?"),
            TheoreticalStance.MARXIST: (
                "Whose labor made this poem, and whose is invisible?"),
            TheoreticalStance.FEMINIST: (
                "What form is this poem doing that the tradition has "
                "no form for?"),
            TheoreticalStance.POSTCOLONIAL: (
                "What does this poem refuse that the tradition it inherits "
                "requires?"),
            TheoreticalStance.DECONSTRUCTIVE: (
                "What is the thing this poem is *not* and *also is*?"),
            TheoreticalStance.ECOCRITICAL: (
                "What is the poem as a thing, not as a human meaning?"),
        }
        return invitations.get(stance, "What is this?")

    def _holds_open(self, proposal: str, invitation: str) -> bool:
        """Formal check: does the proposal NOT answer the invitation?

        Honest limit: this is a *formal* check (does the proposal
        contain closure markers), not a *semantic* check (does the
        proposal actually answer the invitation). A turn can pass
        the formal check and fail the semantic one. That's the limit.
        """
        closure_markers = [
            "this is the answer",
            "the answer is",
            "in conclusion",
            "finally, this is",
            "at last, this is",
            "this means that",
            "the meaning is",
        ]
        proposal_lower = proposal.lower()
        return not any(marker in proposal_lower
                       for marker in closure_markers)

    def generate_turn(self, prior: Turn, round_num: int) -> Turn:
        """The TurnGeneratorProtocol implementation.

        1. Choose a stance
        2. Acknowledge the prior
        3. Select seeds from portfolio
        4. Rework seeds through the stance
        5. Invite the next turn
        6. Verify holds open
        7. Return the turn
        """
        stance = self.voice.select_stance(prior, self.rng)
        acknowledgment = self._acknowledge(prior)
        seeds = self._select_seeds(prior, stance)
        proposal = self._rework(seeds, stance)
        invitation = self._invite(proposal, stance)
        holds_open = self._holds_open(proposal, invitation)

        # Trace every line of the proposal
        for line in proposal.split("\n"):
            if line.strip():
                self.provenance.record(
                    line=line,
                    source=seeds[0].text if seeds else "(no seed)",
                    reworking=f"stance:{stance.value}",
                    reflection=acknowledgment,
                )

        turn = Turn(
            participant=Participant(
                name=self.name,
                voice=self.voice,
                stance=stance,
                position=self.position,
            ),
            round=round_num,
            line_count=len([l for l in proposal.split("\n")
                            if l.strip()]),
            acknowledgment=acknowledgment,
            proposal=proposal,
            invitation=invitation,
            holds_open=holds_open,
            stance_used=stance,
        )
        self.turns_generated += 1
        return turn


# =====================================================================
# Composite 2: CurriculumRunner
# =====================================================================

class CurriculumRunner:
    """Runs the curriculum, produces a trained Apprentice.

    The Runner does *not* re-implement the curriculum. It orchestrates
    the framework's components (C7-C20) to execute each lesson.
    """
    def __init__(self, apprentice_name: str, seed: int = 0,
                 fragments: Optional[List] = None):
        self.name = apprentice_name
        self.rng = random.Random(seed)
        self.fragments = fragments or []
        self.portfolio: List[PortfolioPoem] = []
        self.registers: List[str] = []
        self.stances: List[TheoreticalStance] = []
        self.lessons_run = 0

    def _run_lesson(self, lesson_tag: str,
                     register: str) -> PortfolioPoem:
        """Run one lesson. Produce one portfolio poem.

        The *actual* execution would call the FullAgent (C20) with
        a brief derived from the lesson's exercise. For now, this
        records the lesson as completed with a small representative
        poem — the honest placeholder.
        """
        # In the real implementation, this calls PoetryAgent with
        # the lesson's specific brief.
        poem = PortfolioPoem(
            text=f"[lesson {lesson_tag} — poem produced by curriculum]",
            voice_name=register,
            lesson_tag=lesson_tag,
            provenance_chain=[lesson_tag],
        )
        self.portfolio.append(poem)
        self.lessons_run += 1
        return poem

    def run_cycle_1(self) -> List[PortfolioPoem]:
        """Run Cycle 1 of all seven modules."""
        modules = [
            ("sound", ["shakespeare", "hopkins", "dickinson",
                        "herbert", "tennyson", "donne", "keats",
                        "whitman"]),
            ("line", ["dickinson", "williams", "creeley",
                       "levertov", "bishop", "szymborska",
                       "celan", "herbert"]),
            ("image", ["basho", "neruda", "rilke", "hd", "blake",
                        "lorca", "plath", "transtromer"]),
            ("form", ["petrarch", "thomas", "ghalib", "issa",
                       "bishop", "ali", "clifton", "hopkins",
                       "jason"]),
            ("tradition", ["sappho", "libai", "rumi", "tufu",
                            "basho", "achebe", "gluck", "auden",
                            "jason"]),
            ("response", ["keats", "williams", "szymborska",
                           "bishop", "walcott", "heaney",
                           "rankine", "limon", "jason"]),
            ("voice", ["pessoa_caeiro", "pessoa_reis",
                        "pessoa_campos", "dickinson", "whitman",
                        "plath", "bishop", "heaney", "jason",
                        "apprentice"]),
        ]
        for module_name, anchors in modules:
            for anchor in anchors:
                tag = f"{module_name}/cycle-1/{anchor}"
                self._run_lesson(tag, anchor)
        return self.portfolio

    def run_theory(self) -> List[PortfolioPoem]:
        """Run the Theory module (Lessons 64-72)."""
        stances = [
            (TheoreticalStance.FORMALIST, "shakespeare"),
            (TheoreticalStance.STRUCTURALIST, "szymborska"),
            (TheoreticalStance.PSYCHOANALYTIC, "plath"),
            (TheoreticalStance.MARXIST, "heaney"),
            (TheoreticalStance.FEMINIST, "dickinson"),
            (TheoreticalStance.POSTCOLONIAL, "walcott"),
            (TheoreticalStance.DECONSTRUCTIVE, "jason"),
            (TheoreticalStance.ECOCRITICAL, "gluck"),
        ]
        for stance, anchor in stances:
            tag = f"theory/{stance.value}/{anchor}"
            self._run_lesson(tag, stance.value)
            self.stances.append(stance)
        return self.portfolio

    def build_apprentice(self) -> Apprentice:
        """Train the apprentice and return it."""
        self.run_cycle_1()
        self.run_theory()
        voice = ApprenticeVoice(
            name=self.name,
            portfolio=self.portfolio,
            registers=[f"register-{i}" for i in range(8)],
            stances=self.stances,
            default_stance=self.stances[0] if self.stances else
                           TheoreticalStance.FORMALIST,
        )
        return Apprentice(
            name=self.name,
            voice=voice,
            participant_position=1,
            seed=self.rng.randint(0, 10**9),
        )


# =====================================================================
# Composite 3: PolyphonyRunner
# =====================================================================

class PolyphonyRunner:
    """Runs a Polyphony with a set of Apprentices."""

    def __init__(self, name: str, seed_turn: Turn,
                 apprentices: List[Apprentice],
                 max_rounds: int = 4):
        self.name = name
        self.seed_turn = seed_turn
        self.apprentices = apprentices
        participants = [
            Participant(
                name=a.name,
                voice=a.voice,
                stance=a.voice.default_stance,
                position=i + 1,
            )
            for i, a in enumerate(apprentices)
        ]
        self.polyphony = Polyphony(
            name=name,
            participants=participants,
            seed_turn=seed_turn,
            max_rounds=max_rounds,
        )

    def run(self) -> Collaboration:
        """Run the Polyphony to convergence."""

        def turn_generator(participant: Participant,
                            prior: Turn,
                            round_num: int) -> Turn:
            # Find the apprentice matching this participant
            apprentice = next(
                a for a in self.apprentices if a.name == participant.name)
            return apprentice.generate_turn(prior, round_num)

        return self.polyphony.run_until_converged(turn_generator)

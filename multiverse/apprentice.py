"""Apprentice poets: rule-based turn writers for the poetry world.

From the poetry engine of record 012-03-02: the Turn and the stances of
its component 21, and the runnable apprentice of its component 22. An
apprentice takes the prior turn, picks a critical stance, finds poems in
its portfolio that share the prior turn's key words, reworks one through
the stance with a template, and asks the next poet a question.

The honest scope, as the sketch said: this is template reworking, not
writing. It is a stand-in that lets the poetry world run end to end, as
the corridor walkers of Cycle 0 are stand-ins for agents. Course step 11
(docs/COURSE.md) brings small language models.

Changed from the sketch:
  - Only what the multiverse uses is here. The engine's own Polyphony
    runner is left out: the poetry world checks turns and convergence.
  - The curriculum's anchor for the founder's own poems is named
    "founder" rather than by name.
"""
from __future__ import annotations

import hashlib
import random
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Protocol


class TheoreticalStance(Enum):
    """Each poet holds one theory per turn: held open, not believed."""
    FORMALIST = "formalist"
    STRUCTURALIST = "structuralist"
    PSYCHOANALYTIC = "psychoanalytic"
    MARXIST = "marxist"
    FEMINIST = "feminist"
    POSTCOLONIAL = "postcolonial"
    DECONSTRUCTIVE = "deconstructive"
    ECOCRITICAL = "ecocritical"


@dataclass
class PortfolioPoem:
    text: str
    voice_name: str
    lesson_tag: str
    provenance_chain: List[str] = field(default_factory=list)


@dataclass
class ApprenticeVoice:
    """What training leaves: a portfolio, registers, and stances."""
    name: str
    portfolio: List[PortfolioPoem]
    registers: List[str]
    stances: List[TheoreticalStance]
    default_stance: TheoreticalStance

    def select_stance(self, prior_turn, rng: random.Random
                      ) -> TheoreticalStance:
        """Any stance but the one the prior turn used."""
        last = getattr(prior_turn, "stance_used", None)
        candidates = [s for s in self.stances if s != last]
        return rng.choice(candidates) if candidates else self.default_stance


@dataclass
class Participant:
    name: str
    voice: ApprenticeVoice
    stance: TheoreticalStance
    position: int
    portfolio: List[str] = field(default_factory=list)


@dataclass
class Turn:
    """A move in the collaboration, not a whole poem."""
    participant: Participant
    round: int
    line_count: int
    acknowledgment: str
    proposal: str
    invitation: str
    holds_open: bool
    stance_used: Optional[TheoreticalStance] = None


@dataclass
class ChainEntry:
    line: str
    source: str
    reworking: Optional[str] = None
    reflection: Optional[str] = None


class ProvenanceChain:
    """Every line traced to the portfolio poem it came from."""

    def __init__(self):
        self._entries: Dict[str, ChainEntry] = {}

    def record(self, line: str, source: str,
               reworking: Optional[str] = None,
               reflection: Optional[str] = None) -> str:
        key = self._hash(line)
        self._entries[key] = ChainEntry(line, source, reworking, reflection)
        return key

    def trace(self, line: str) -> Optional[ChainEntry]:
        return self._entries.get(self._hash(line))

    @staticmethod
    def _hash(s: str) -> str:
        return hashlib.sha256(s.encode()).hexdigest()[:16]


class TurnGenerator(Protocol):
    """Anything that writes a turn: a person or an apprentice."""

    def generate_turn(self, prior, round_num: int) -> Turn: ...


STOPWORDS = {
    "the", "a", "an", "and", "or", "but", "of", "to", "in",
    "is", "am", "are", "was", "were", "be", "been", "being",
    "this", "that", "these", "those", "it", "its", "i",
    "you", "he", "she", "we", "they", "my", "your", "his",
    "her", "our", "their", "not", "no",
}
PUNCTUATION = ".,;:!?\"'()[]"

INVITATIONS = {
    TheoreticalStance.FORMALIST:
        "What does the form leave out that is still part of the poem?",
    TheoreticalStance.STRUCTURALIST:
        "What is the material body of this — the actual sounds, the "
        "actual page?",
    TheoreticalStance.PSYCHOANALYTIC:
        "What does the line say *in the act of not saying*?",
    TheoreticalStance.MARXIST:
        "Whose labor made this poem, and whose is invisible?",
    TheoreticalStance.FEMINIST:
        "What form is this poem doing that the tradition has no form for?",
    TheoreticalStance.POSTCOLONIAL:
        "What does this poem refuse that the tradition it inherits "
        "requires?",
    TheoreticalStance.DECONSTRUCTIVE:
        "What is the thing this poem is *not* and *also is*?",
    TheoreticalStance.ECOCRITICAL:
        "What is the poem as a thing, not as a human meaning?",
}

CLOSURE_MARKERS = (
    "this is the answer", "the answer is", "in conclusion",
    "finally, this is", "at last, this is", "this means that",
    "the meaning is",
)


def _non_blank(lines: List[str]) -> List[str]:
    return [line for line in lines if line.strip()]


class Apprentice:
    """A procedure that, given the prior turn, writes the next one."""

    def __init__(self, name: str, voice: ApprenticeVoice,
                 participant_position: int, seed: int = 0):
        self.name = name
        self.voice = voice
        self.position = participant_position
        self.rng = random.Random(seed)
        self.provenance = ProvenanceChain()
        self.turns_generated = 0

    def key_terms(self, prior) -> List[str]:
        """Up to five of the prior proposal's most frequent content words
        (ties in order of first appearance)."""
        freq: Dict[str, int] = {}
        for raw in prior.proposal.lower().split():
            word = raw.strip(PUNCTUATION)
            if word not in STOPWORDS and len(raw) > 2:
                freq[word] = freq.get(word, 0) + 1
        return sorted(freq, key=lambda w: -freq[w])[:5]

    def _select_seeds(self, prior) -> List[PortfolioPoem]:
        """Up to three portfolio poems containing the most key terms."""
        terms = self.key_terms(prior)
        if not terms:
            return self.voice.portfolio[:3]
        scored = []
        for poem in self.voice.portfolio:
            hits = sum(1 for term in terms if term in poem.text.lower())
            if hits:
                scored.append((hits, poem))
        scored.sort(key=lambda x: -x[0])
        return [poem for _, poem in scored[:3]]

    def _rework(self, seeds: List[PortfolioPoem],
                stance: TheoreticalStance) -> str:
        """Each stance's characteristic move, as a template."""
        if not seeds:
            return "(no seeds available for this stance)"
        lines = seeds[0].text.split("\n")
        S = TheoreticalStance
        if stance is S.FORMALIST:
            return "\n".join([l for l in lines if l.strip()
                              and not l.strip().endswith("?")][:4])
        if stance is S.STRUCTURALIST:
            return "\n".join(f"not-{l.split()[0]}" for l in
                             _non_blank(lines)[:2])
        if stance is S.DECONSTRUCTIVE:
            picked = _non_blank(lines)[:2]
            if len(picked) >= 2:
                return (f"{picked[0]}\nand also\n{picked[1]}\n"
                        "and neither is the poem.")
            return "\n".join(picked)
        heading = {
            S.PSYCHOANALYTIC: "what the line does not say:",
            S.MARXIST: "the labor behind this:",
            S.FEMINIST: "the voice this silences:",
            S.POSTCOLONIAL: "the inheritance:",
            S.ECOCRITICAL: "not the human — the thing itself:",
        }[stance]
        return heading + "\n" + "\n".join(_non_blank(lines)[:3])

    def _acknowledge(self, prior) -> str:
        terms = self.key_terms(prior)
        if not terms:
            return "I am responding to your poem."
        return (f"You said something about {', '.join(terms[:3])}. "
                "I am responding to that — not to the whole poem, "
                "to that specific thing.")

    @staticmethod
    def holds_open(proposal: str) -> bool:
        """A formal check only: no closure phrase in the proposal. A turn
        can pass this and still close its question in substance."""
        lower = proposal.lower()
        return not any(marker in lower for marker in CLOSURE_MARKERS)

    def generate_turn(self, prior, round_num: int) -> Turn:
        stance = self.voice.select_stance(prior, self.rng)
        acknowledgment = self._acknowledge(prior)
        seeds = self._select_seeds(prior)
        proposal = self._rework(seeds, stance)
        for line in _non_blank(proposal.split("\n")):
            self.provenance.record(
                line=line,
                source=seeds[0].text if seeds else "(no seed)",
                reworking=f"stance:{stance.value}",
                reflection=acknowledgment)
        self.turns_generated += 1
        return Turn(
            participant=Participant(self.name, self.voice, stance,
                                    self.position),
            round=round_num,
            line_count=len(_non_blank(proposal.split("\n"))),
            acknowledgment=acknowledgment,
            proposal=proposal,
            invitation=INVITATIONS[stance],
            holds_open=self.holds_open(proposal),
            stance_used=stance)


CYCLE_1 = [
    ("sound", ["shakespeare", "hopkins", "dickinson", "herbert",
               "tennyson", "donne", "keats", "whitman"]),
    ("line", ["dickinson", "williams", "creeley", "levertov", "bishop",
              "szymborska", "celan", "herbert"]),
    ("image", ["basho", "neruda", "rilke", "hd", "blake", "lorca",
               "plath", "transtromer"]),
    ("form", ["petrarch", "thomas", "ghalib", "issa", "bishop", "ali",
              "clifton", "hopkins", "founder"]),
    ("tradition", ["sappho", "libai", "rumi", "tufu", "basho", "achebe",
                   "gluck", "auden", "founder"]),
    ("response", ["keats", "williams", "szymborska", "bishop", "walcott",
                  "heaney", "rankine", "limon", "founder"]),
    ("voice", ["pessoa_caeiro", "pessoa_reis", "pessoa_campos",
               "dickinson", "whitman", "plath", "bishop", "heaney",
               "founder", "apprentice"]),
]

THEORY = [
    (TheoreticalStance.FORMALIST, "shakespeare"),
    (TheoreticalStance.STRUCTURALIST, "szymborska"),
    (TheoreticalStance.PSYCHOANALYTIC, "plath"),
    (TheoreticalStance.MARXIST, "heaney"),
    (TheoreticalStance.FEMINIST, "dickinson"),
    (TheoreticalStance.POSTCOLONIAL, "walcott"),
    (TheoreticalStance.DECONSTRUCTIVE, "founder"),
    (TheoreticalStance.ECOCRITICAL, "gluck"),
]


class CurriculumRunner:
    """Runs the curriculum's lessons and returns a trained apprentice.

    Each lesson records a placeholder poem: the real lessons would ask a
    poetry agent for a poem to the lesson's brief. A demonstration
    replaces the portfolio with real poems (collaboration.py)."""

    def __init__(self, apprentice_name: str, seed: int = 0):
        self.name = apprentice_name
        self.rng = random.Random(seed)
        self.portfolio: List[PortfolioPoem] = []
        self.stances: List[TheoreticalStance] = []
        self.lessons_run = 0

    def _run_lesson(self, lesson_tag: str, register: str) -> PortfolioPoem:
        poem = PortfolioPoem(
            text=f"[lesson {lesson_tag} — poem produced by curriculum]",
            voice_name=register, lesson_tag=lesson_tag,
            provenance_chain=[lesson_tag])
        self.portfolio.append(poem)
        self.lessons_run += 1
        return poem

    def run_cycle_1(self) -> List[PortfolioPoem]:
        for module, anchors in CYCLE_1:
            for anchor in anchors:
                self._run_lesson(f"{module}/cycle-1/{anchor}", anchor)
        return self.portfolio

    def run_theory(self) -> List[PortfolioPoem]:
        for stance, anchor in THEORY:
            self._run_lesson(f"theory/{stance.value}/{anchor}", stance.value)
            self.stances.append(stance)
        return self.portfolio

    def build_apprentice(self) -> Apprentice:
        self.run_cycle_1()
        self.run_theory()
        voice = ApprenticeVoice(
            name=self.name, portfolio=self.portfolio,
            registers=[f"register-{i}" for i in range(8)],
            stances=self.stances,
            default_stance=(self.stances[0] if self.stances
                            else TheoreticalStance.FORMALIST))
        return Apprentice(self.name, voice, participant_position=1,
                          seed=self.rng.randint(0, 10**9))

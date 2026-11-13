"""
poetry_engine_c4.py — Component 4: The Score-Performance Gap.

Reading poetry as text is like reading a musical score. The score
contains less than the audio. The poem contains less than the
performance. The reader supplies the rest — the imagination is
the interpolation.

The framework CANNOT fill the gap. It can only MEASURE it.

Atoms:
  - ImaginedSpeaker: the persona the reader constructs
  - ImaginedListener: the audience the reader imagines
  - LineEnd: how the line terminates (period, comma, function word, none)
  - PerformanceDecision: a choice the reader must make

Composites:
  - PerformanceSpace: the set of decisions available for a line
  - EnjambmentAnalyzer: syntax-meter divergence at line breaks
  - GapAnalyzer: size and shape of the score-performance gap

Depends on Components 1, 2, 3.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Tuple

from poetry_engine_c1 import (
    Syllabifier, WordClass, classify_word,
)
from poetry_engine_c2 import (
    MetaphorDetector, read,
)
from poetry_engine_c3 import (
    Meter, Line, build_line,
    IAMBIC_PENTAMETER,
    scan_generative, scan_functional,
    analyze_line, DualScansion,
)


# =====================================================================
# Atom 1: ImaginedSpeaker
# =====================================================================

class SpeakerType(Enum):
    LOVER = "lover"
    PROPHET = "prophet"
    ELEGIST = "elegist"
    OBSERVER = "observer"
    SOLILOQUIST = "soliloquist"
    APOSTROPHIZER = "apostrophizer"  # speaking to something absent
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class ImaginedSpeaker:
    type: SpeakerType
    confidence: float  # in [0, 1]
    evidence: Tuple[str, ...] = ()


def detect_speaker(text: str) -> ImaginedSpeaker:
    """Heuristic speaker detection.

    Low confidence is the correct answer for ambiguous lines.
    The framework does not pretend to know what it does not know.
    """
    t = text.lower()
    words = set(t.split())
    evidence: List[str] = []

    has_first_person = bool(
        words & {"i", "me", "my", "mine", "we", "us", "our"})
    has_second_person = bool(
        words & {"thee", "thou", "thy", "thine", "ye", "you", "your"})
    if has_first_person:
        evidence.append("first-person")
    if has_second_person:
        evidence.append("second-person")

    if "love" in t and has_second_person:
        return ImaginedSpeaker(SpeakerType.LOVER, 0.8, tuple(evidence))
    if "love" in t and has_first_person:
        return ImaginedSpeaker(SpeakerType.LOVER, 0.7, tuple(evidence))
    if any(w in t for w in
           ("death", "die", "dies", "dead", "grave", "gone", "loss", "lost")):
        if has_first_person:
            evidence.append("mortality")
            return ImaginedSpeaker(SpeakerType.ELEGIST, 0.7, tuple(evidence))
    if any(w in t for w in ("shall", "will", "never", "always",
                             "every", "all")):
        if has_first_person:
            return ImaginedSpeaker(SpeakerType.PROPHET, 0.6, tuple(evidence))
    if any(w in t for w in ("when", "that", "as", "while", "if")):
        if has_first_person:
            return ImaginedSpeaker(SpeakerType.OBSERVER, 0.5, tuple(evidence))
    if words & {"o", "oh", "ah"}:
        return ImaginedSpeaker(SpeakerType.APOSTROPHIZER, 0.7, tuple(evidence))
    if has_first_person:
        return ImaginedSpeaker(SpeakerType.SOLILOQUIST, 0.4, tuple(evidence))
    return ImaginedSpeaker(SpeakerType.UNKNOWN, 0.1)


# =====================================================================
# Atom 2: ImaginedListener
# =====================================================================

class ListenerType(Enum):
    BELOVED = "beloved"
    POSTERITY = "posterity"
    SELF = "self"
    GOD = "god"
    ABSTRACT = "abstract"
    READER = "reader"
    NOBODY = "nobody"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class ImaginedListener:
    type: ListenerType
    confidence: float
    evidence: Tuple[str, ...] = ()


def detect_listener(text: str) -> ImaginedListener:
    t = text.lower()
    words = set(t.split())
    evidence: List[str] = []

    if words & {"thee", "thou", "thy", "thine", "ye", "you", "your"}:
        evidence.append("second-person")
        if any(w in t for w in ("eternal", "forever", "shall live",
                                  "shall see", "posterity")):
            return ImaginedListener(ListenerType.POSTERITY, 0.6,
                                     tuple(evidence))
        return ImaginedListener(ListenerType.BELOVED, 0.7, tuple(evidence))
    if words & {"o", "oh", "ah"}:
        evidence.append("apostrophe")
        return ImaginedListener(ListenerType.ABSTRACT, 0.6, tuple(evidence))
    if "let me" in t or "let us" in t:
        evidence.append("self-address")
        return ImaginedListener(ListenerType.SELF, 0.5, tuple(evidence))
    if words & {"i", "me", "my"}:
        evidence.append("interior-monologue")
        return ImaginedListener(ListenerType.NOBODY, 0.3, tuple(evidence))
    return ImaginedListener(ListenerType.UNKNOWN, 0.1)


# =====================================================================
# Atom 3: LineEnd
# =====================================================================

class LineEndType(Enum):
    PERIOD = "period"
    COMMA = "comma"
    SEMICOLON = "semicolon"
    COLON = "colon"
    QUESTION = "question"
    EXCLAIM = "exclaim"
    NONE = "none"
    FUNCTION_WORD = "function"


@dataclass(frozen=True)
class LineEnd:
    type: LineEndType
    last_word: str


def detect_line_end(text: str) -> LineEnd:
    stripped = text.rstrip()
    if not stripped:
        return LineEnd(LineEndType.NONE, "")
    last_char = stripped[-1]
    words = stripped.split()
    last_word = (words[-1].strip(".,;:!?'\"()[]-") if words else "")

    if last_char == ".":
        return LineEnd(LineEndType.PERIOD, last_word)
    if last_char == "?":
        return LineEnd(LineEndType.QUESTION, last_word)
    if last_char == "!":
        return LineEnd(LineEndType.EXCLAIM, last_word)
    if last_char == ",":
        return LineEnd(LineEndType.COMMA, last_word)
    if last_char == ";":
        return LineEnd(LineEndType.SEMICOLON, last_word)
    if last_char == ":":
        return LineEnd(LineEndType.COLON, last_word)
    if last_word and classify_word(last_word) == WordClass.FUNCTION:
        return LineEnd(LineEndType.FUNCTION_WORD, last_word)
    return LineEnd(LineEndType.NONE, last_word)


# =====================================================================
# Atom 4: PerformanceDecision
# =====================================================================

class DecisionKind(Enum):
    BREATH = "breath"
    EMPHASIS = "emphasis"
    TEMPO = "tempo"
    LINE_PAUSE = "line_pause"
    SPEAKER = "speaker"
    LISTENER = "listener"


@dataclass(frozen=True)
class PerformanceDecision:
    """A choice the reader must make.

    options: what the reader could choose
    framework_hint: what the text suggests (None if silent)
    confidence: how confident is the hint (0 if None)
    """
    kind: DecisionKind
    position: int  # syllable index, -1 for global
    options: Tuple[str, ...]
    framework_hint: Optional[str] = None
    confidence: float = 0.0

    @property
    def is_open(self) -> bool:
        return self.confidence < 0.5


# =====================================================================
# Composite: PerformanceSpace
# =====================================================================

@dataclass
class PerformanceSpace:
    """The set of decisions the reader must make for a line."""
    text: str
    decisions: List[PerformanceDecision] = field(default_factory=list)

    def n_decisions(self) -> int:
        return len(self.decisions)

    def open_decisions(self) -> List[PerformanceDecision]:
        return [d for d in self.decisions if d.is_open]

    def by_kind(self) -> Dict[str, int]:
        counts: Dict[str, int] = {}
        for d in self.decisions:
            counts[d.kind.value] = counts.get(d.kind.value, 0) + 1
        return counts

    def report(self) -> str:
        lines = [f"PerformanceSpace({self.text[:45]!r})"]
        lines.append(f"  {self.n_decisions()} total decisions, "
                     f"{len(self.open_decisions())} open")
        for d in self.decisions:
            marker = "  ○" if d.is_open else "  ●"
            hint = f" → {d.framework_hint}" if d.framework_hint else ""
            lines.append(
                f"  {marker} {d.kind.value:<11} "
                f"@pos {d.position:>2}: {list(d.options)}{hint} "
                f"(conf {d.confidence:.2f})")
        return "\n".join(lines)


def build_performance_space(
    text: str,
    line: Line,
    dual: DualScansion,
    speaker: ImaginedSpeaker,
    listener: ImaginedListener,
    line_end: LineEnd,
) -> PerformanceSpace:
    """Assemble the decisions available for a line."""
    decisions: List[PerformanceDecision] = []

    # 1. Speaker decision
    decisions.append(PerformanceDecision(
        kind=DecisionKind.SPEAKER, position=-1,
        options=tuple(s.value for s in SpeakerType),
        framework_hint=speaker.type.value,
        confidence=speaker.confidence,
    ))

    # 2. Listener decision
    decisions.append(PerformanceDecision(
        kind=DecisionKind.LISTENER, position=-1,
        options=tuple(l.value for l in ListenerType),
        framework_hint=listener.type.value,
        confidence=listener.confidence,
    ))

    # 3. Tempo decision (only if meter is irregular OR absent)
    if dual.generative.score() < 0.8:
        decisions.append(PerformanceDecision(
            kind=DecisionKind.TEMPO, position=-1,
            options=("slow", "medium", "fast", "variable"),
            framework_hint=None,
            confidence=0.0,
        ))

    # 4. Line-end pause decision
    pause_strength = {
        LineEndType.PERIOD: ("short", 0.9),
        LineEndType.QUESTION: ("short", 0.9),
        LineEndType.EXCLAIM: ("short", 0.9),
        LineEndType.COMMA: ("short", 0.6),
        LineEndType.SEMICOLON: ("short", 0.6),
        LineEndType.COLON: ("short", 0.6),
        LineEndType.FUNCTION_WORD: ("very short or none", 0.2),
        LineEndType.NONE: ("none or extended", 0.1),
    }
    hint, conf = pause_strength[line_end.type]
    decisions.append(PerformanceDecision(
        kind=DecisionKind.LINE_PAUSE, position=-1,
        options=("none", "short", "extended"),
        framework_hint=hint,
        confidence=conf,
    ))

    # 5. Emphasis shifts: content on unstressed, function on stressed
    for idx in dual.functional.content_subordinated():
        decisions.append(PerformanceDecision(
            kind=DecisionKind.EMPHASIS, position=idx,
            options=("natural", "promoted", "bracketed"),
            framework_hint="bracketed",  # meter brackets content
            confidence=0.4,
        ))
    for idx in dual.functional.function_highlighted():
        decisions.append(PerformanceDecision(
            kind=DecisionKind.EMPHASIS, position=idx,
            options=("natural", "promoted", "bracketed"),
            framework_hint="promoted",  # meter promotes function word
            confidence=0.5,
        ))

    return PerformanceSpace(text=text, decisions=decisions)


# =====================================================================
# Composite: EnjambmentAnalyzer
# =====================================================================

@dataclass
class EnjambmentResult:
    end_type: LineEndType
    last_word: str
    tension: float  # 0 = end-stopped, 1 = maximally enjambed
    explanation: str


class EnjambmentAnalyzer:
    """Measures the syntax-meter divergence at line breaks.

    This is the first place in the poetry framework where
    the SCORE (line) and the SYNTACTIC UNITS (clauses) diverge.
    The reader must decide: pause at the line break (as the score
    says) or continue through the clause (as the syntax says)?
    """

    def analyze(self, line_text: str,
                next_line_text: Optional[str] = None) -> EnjambmentResult:
        end = detect_line_end(line_text)

        if end.type in (LineEndType.PERIOD, LineEndType.QUESTION,
                         LineEndType.EXCLAIM):
            return EnjambmentResult(
                end_type=end.type, last_word=end.last_word,
                tension=0.0,
                explanation="end-stopped (strong punctuation)")

        if end.type in (LineEndType.COMMA, LineEndType.SEMICOLON,
                         LineEndType.COLON):
            return EnjambmentResult(
                end_type=end.type, last_word=end.last_word,
                tension=0.2,
                explanation="weak end-stop")

        if end.type == LineEndType.FUNCTION_WORD:
            return EnjambmentResult(
                end_type=end.type, last_word=end.last_word,
                tension=0.9,
                explanation=(f"strongly enjambed (line ends with "
                             f"function word '{end.last_word}')"))

        # NONE: check next line's first word
        if next_line_text:
            first_word = next_line_text.split()[0] if next_line_text.split() \
                else ""
            first_clean = first_word.strip(
                ".,;:!?'\"()[]-").lower()
            if first_clean in {"and", "but", "or", "nor", "for", "so",
                                "yet", "when", "while", "as", "if",
                                "that", "which", "who"}:
                return EnjambmentResult(
                    end_type=end.type, last_word=end.last_word,
                    tension=1.0,
                    explanation=(f"strongly enjambed (next line "
                                 f"continues with '{first_word}')"))
            return EnjambmentResult(
                end_type=end.type, last_word=end.last_word,
                tension=0.5,
                explanation="possibly enjambed (unpunctuated)")

        return EnjambmentResult(
            end_type=end.type, last_word=end.last_word,
            tension=0.5,
            explanation="unpunctuated line ending")


# =====================================================================
# Composite: GapAnalyzer
# =====================================================================

@dataclass
class GapAnalysis:
    """Size and shape of the score-performance gap for one line."""
    text: str
    enjambment_tension: float
    substitution_count: int
    metaphor_count: int
    function_highlight_count: int
    speaker_confidence: float
    listener_confidence: float
    speaker_type: str
    listener_type: str

    def load(self) -> float:
        """Total imagination load: how much interpolation required.

        Roughly [0, 3]. Higher = more reader-work.
        """
        load = 0.0
        load += self.enjambment_tension
        load += min(self.substitution_count, 5) * 0.2
        load += min(self.metaphor_count, 3) * 0.3
        load += min(self.function_highlight_count, 3) * 0.2
        load += (1.0 - self.speaker_confidence) * 0.3
        load += (1.0 - self.listener_confidence) * 0.3
        return load

    def shape(self) -> str:
        """Which dimension dominates the gap?"""
        components = {
            "enjambment": self.enjambment_tension,
            "substitution": min(self.substitution_count, 5) * 0.2,
            "metaphor": min(self.metaphor_count, 3) * 0.3,
            "function_highlight": min(self.function_highlight_count, 3) * 0.2,
            "speaker_ambiguity": (1.0 - self.speaker_confidence) * 0.3,
            "listener_ambiguity": (1.0 - self.listener_confidence) * 0.3,
        }
        return max(components, key=components.get)

    def report(self) -> str:
        return (
            f"GapAnalysis({self.text[:45]!r})\n"
            f"  Load: {self.load():.2f}  Shape: {self.shape()}\n"
            f"  Enjambment: {self.enjambment_tension:.2f}\n"
            f"  Substitutions: {self.substitution_count}\n"
            f"  Metaphors: {self.metaphor_count}\n"
            f"  Function-highlights: {self.function_highlight_count}\n"
            f"  Speaker: {self.speaker_type} "
            f"(conf {self.speaker_confidence:.2f})\n"
            f"  Listener: {self.listener_type} "
            f"(conf {self.listener_confidence:.2f})")


def analyze_gap(
    text: str,
    next_line_text: Optional[str] = None,
    meter: Meter = IAMBIC_PENTAMETER,
    syllabifier: Optional[Syllabifier] = None,
) -> GapAnalysis:
    enj = EnjambmentAnalyzer().analyze(text, next_line_text)
    dual = analyze_line(text, meter, syllabifier)
    metaphors = MetaphorDetector().detect(text)
    speaker = detect_speaker(text)
    listener = detect_listener(text)

    return GapAnalysis(
        text=text,
        enjambment_tension=enj["tension"] if isinstance(enj, dict)
                           else enj.tension,
        substitution_count=len(dual.generative.substitutions()),
        metaphor_count=len(metaphors),
        function_highlight_count=len(
            dual.functional.function_highlighted()),
        speaker_confidence=speaker.confidence,
        listener_confidence=listener.confidence,
        speaker_type=speaker.type.value,
        listener_type=listener.type.value,
    )

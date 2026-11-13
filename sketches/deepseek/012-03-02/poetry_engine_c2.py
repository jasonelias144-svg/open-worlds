"""
poetry_engine_c2.py — Component 2: The Cognitive Frame.

Three atoms, drawn from Cognitive Poetics, Cognitive Linguistics,
and Stylistics:
  - Deviation: measured departure from a norm
  - ImageSchema: pre-verbal pattern structuring thought
  - MetaphorMapping: structural correspondence between domains

One composite:
  - CognitiveReading: foregroundings + schemas + mappings + salience

Analyzers:
  - DeviationDetector: alliteration, repetition
  - ImageSchemaDetector: prepositions and directional verbs
  - MetaphorDetector: "X is Y", "X like Y", "X of Y", "compare X to Y"

The critical honesty: the framework does NOT interpret.
It identifies operations that can be formalized. The rest is the reader's.

Depends on Component 1 (phonemes, syllables, stress).
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Set, Tuple
import re

from poetry_engine_c1 import (
    Syllabifier, StressPattern, line_stress_pattern,
    line_syllable_count,
)


# =====================================================================
# Atom 1: Deviation
# =====================================================================

class DeviationKind(Enum):
    PHONOLOGICAL = "phonological"
    LEXICAL = "lexical"
    SYNTACTIC = "syntactic"
    SEMANTIC = "semantic"
    STRUCTURAL = "structural"


@dataclass
class Deviation:
    """A measured departure from a norm.

    Stylistics and Cognitive Poetics both say: what makes a poem a
    poem is not its raw content, but its patterned departures from
    ordinary language. A Deviation captures one such departure.
    """
    kind: DeviationKind
    target: str
    norm: str
    magnitude: float  # in [0, 1]

    def __post_init__(self):
        if not 0.0 <= self.magnitude <= 1.0:
            raise ValueError(
                f"Deviation magnitude must be in [0,1], got {self.magnitude}")

    def __repr__(self):
        return (f"Dev({self.kind.value}: {self.target!r} vs "
                f"{self.norm!r}, mag={self.magnitude:.2f})")


# =====================================================================
# Atom 2: ImageSchema
# =====================================================================

@dataclass(frozen=True)
class ImageSchema:
    """A pre-verbal pattern that structures thought.

    After Mark Johnson, "The Body in the Mind" (1987):
    we think in recurring patterns (CONTAINER, PATH, UP-DOWN, ...)
    that come from bodily experience. An image schema is not a word
    or a concept. It is a structural pattern that words and concepts
    are built on top of.
    """
    name: str
    structure: Tuple[str, ...]  # the roles the schema provides

    def __repr__(self):
        return f"Schema({self.name})"


CONTAINER = ImageSchema("CONTAINER", ("interior", "boundary", "exterior"))
PATH = ImageSchema("PATH", ("source", "trajectory", "goal", "direction"))
UP_DOWN = ImageSchema("UP-DOWN", ("high", "low", "axis"))
LINK = ImageSchema("LINK", ("connected-to", "connector"))
FORCE = ImageSchema("FORCE", ("cause", "effect", "resistance"))
BALANCE = ImageSchema("BALANCE", ("left", "right", "center"))
PART_WHOLE = ImageSchema("PART-WHOLE", ("part", "whole"))
CENTER_PERIPHERY = ImageSchema("CENTER-PERIPHERY", ("center", "edge"))
NEAR_FAR = ImageSchema("NEAR-FAR", ("near", "far", "axis"))
CYCLE = ImageSchema("CYCLE", ("start", "peak", "end", "restart"))

CANONICAL_SCHEMAS: Dict[str, ImageSchema] = {
    s.name: s for s in [CONTAINER, PATH, UP_DOWN, LINK, FORCE,
                        BALANCE, PART_WHOLE, CENTER_PERIPHERY,
                        NEAR_FAR, CYCLE]
}


SCHEMA_TRIGGERS: Dict[str, Set[str]] = {
    "CONTAINER": {
        "in", "into", "out", "within", "inside", "through",
        "contain", "contained", "holds", "held", "enclosed",
        "interior", "exterior", "border", "enclose", "poured",
    },
    "PATH": {
        "along", "through", "toward", "to", "from", "past",
        "across", "follow", "winds", "goes", "leads", "route",
        "road", "path", "way", "journey", "arrive", "depart",
    },
    "UP-DOWN": {
        "up", "down", "over", "under", "above", "below",
        "high", "low", "rise", "fall", "ascend", "descend",
        "climb", "drop", "sink", "lift",
    },
    "LINK": {
        "link", "connect", "bind", "tie", "join", "together",
        "apart", "break", "attach", "detach", "unite",
        "sever", "fasten", "loosen",
    },
    "FORCE": {
        "push", "pull", "drive", "force", "hit", "strike",
        "block", "resist", "yield", "thrust", "press",
        "compel", "repel",
    },
    "BALANCE": {
        "balance", "weigh", "equal", "unequal", "even", "odd",
        "level", "tilt", "sway", "steady", "unsteady",
    },
    "PART-WHOLE": {
        "part", "whole", "piece", "fragment", "unit",
        "broken", "intact", "entire",
    },
    "CENTER-PERIPHERY": {
        "center", "edge", "margin", "frame", "border",
        "periphery", "middle", "rim", "core",
    },
    "NEAR-FAR": {
        "near", "far", "close", "distant", "alongside",
        "opposite", "beside", "away",
    },
    "CYCLE": {
        "cycle", "again", "return", "turn", "revolve",
        "round", "repeat", "recur", "circle",
    },
}


# =====================================================================
# Atom 3: MetaphorMapping
# =====================================================================

class MetaphorPattern(Enum):
    IS = "X is Y"
    LIKE = "X like Y"
    OF = "X of Y"
    COMPARE_TO = "compare X to Y"


@dataclass
class MetaphorMapping:
    """A DETECTED metaphor: target, source, pattern.

    HONESTY NOTE: the framework records that a metaphorical
    construction is present, but does NOT fill in the mappings
    between source and target. That is the reader's work.
    The framework says "here is where metaphor is happening",
    not "here is what it means".
    """
    target: str
    source: str
    pattern: MetaphorPattern
    presence: float  # in [0, 1] — how strongly syntax suggests metaphor

    def __repr__(self):
        return (f"Map({self.target!r}←{self.source!r}, "
                f"{self.pattern.value}, presence={self.presence:.2f})")


# =====================================================================
# Composite: CognitiveReading
# =====================================================================

@dataclass
class CognitiveReading:
    """The result of reading a text through the cognitive frame."""
    text: str
    deviations: List[Deviation] = field(default_factory=list)
    active_schemas: List[ImageSchema] = field(default_factory=list)
    metaphors: List[MetaphorMapping] = field(default_factory=list)

    def salience(self) -> float:
        """Combined salience: sum of magnitudes + counts.

        Not a quality measure — a structural one. Higher = more
        cognitive operations are visibly happening in the text.
        """
        dev_score = sum(d.magnitude for d in self.deviations)
        sch_score = len(self.active_schemas) * 0.5
        met_score = sum(m.presence for m in self.metaphors)
        return dev_score + sch_score + met_score

    def report(self) -> str:
        lines = [f"CognitiveReading({self.text[:45]!r})"]
        if self.deviations:
            lines.append("  Deviations:")
            for d in self.deviations[:5]:
                lines.append(f"    {d}")
        if self.active_schemas:
            names = [s.name for s in self.active_schemas]
            lines.append(f"  Active schemas: {names}")
        if self.metaphors:
            lines.append("  Detected metaphors:")
            for m in self.metaphors:
                lines.append(f"    {m}")
        lines.append(f"  Salience: {self.salience():.3f}")
        return "\n".join(lines)


# =====================================================================
# Analyzer 1: DeviationDetector
# =====================================================================

_CONSONANTS = set("bcdfghjklmnpqrstvwxyz")


class DeviationDetector:
    """Find measurable deviations from expected norms."""

    def alliteration(self, text: str) -> List[Deviation]:
        """Detect repeated word-initial consonants."""
        words = re.findall(r"[a-zA-Z]+", text.lower())
        if len(words) < 2:
            return []
        by_consonant: Dict[str, List[str]] = {}
        for w in words:
            if not w:
                continue
            first = w[0]
            if first in _CONSONANTS:
                by_consonant.setdefault(first, []).append(w)
        deviations = []
        for c, group in by_consonant.items():
            if len(group) >= 2:
                magnitude = min(1.0, len(group) / len(words))
                deviations.append(Deviation(
                    kind=DeviationKind.PHONOLOGICAL,
                    target=" ".join(group),
                    norm="uniform consonant distribution",
                    magnitude=magnitude,
                ))
        return deviations

    def repetition(self, text: str, min_count: int = 3) -> List[Deviation]:
        """Detect repeated words."""
        words = re.findall(r"[a-zA-Z]+", text.lower())
        if not words:
            return []
        counts: Dict[str, int] = {}
        for w in words:
            counts[w] = counts.get(w, 0) + 1
        deviations = []
        for w, n in counts.items():
            if n >= min_count:
                deviations.append(Deviation(
                    kind=DeviationKind.LEXICAL,
                    target=w,
                    norm=f"typical word frequency ({len(words)/max(len(counts),1):.1f})",
                    magnitude=min(1.0, n / len(words)),
                ))
        return deviations


# =====================================================================
# Analyzer 2: ImageSchemaDetector
# =====================================================================

class ImageSchemaDetector:
    """Detect image schemas activated by words in the text."""

    def detect(self, text: str) -> List[ImageSchema]:
        tokens = re.findall(r"[a-zA-Z]+", text.lower())
        detected: Set[str] = set()
        for token in tokens:
            for schema_name, triggers in SCHEMA_TRIGGERS.items():
                if token in triggers:
                    detected.add(schema_name)
        return [CANONICAL_SCHEMAS[name] for name in sorted(detected)]


# =====================================================================
# Analyzer 3: MetaphorDetector
# =====================================================================

class MetaphorDetector:
    """Detect syntactic patterns that SUGGEST metaphor.

    Records presence and the (target, source) pair.
    Does NOT fill in the semantic mapping.
    """

    PRONOUNS = {
        "i", "you", "he", "she", "it", "we", "they",
        "thee", "thou", "me", "him", "her", "us", "them",
    }
    STOPWORDS = {
        "the", "a", "an", "my", "your", "his", "her", "its",
        "our", "their", "this", "that", "these", "those",
        "and", "or", "but", "of", "to", "is", "are", "was",
        "were", "be", "been", "being", "i", "you", "he",
        "she", "it", "we", "they",
    }

    def _clean(self, token: str, allow_pronouns: bool = False) -> str:
        """Extract a content-word head from a phrase."""
        words = re.findall(r"[a-zA-Z]+", token.lower())
        if allow_pronouns:
            content = [w for w in words
                       if w not in self.STOPWORDS or w in self.PRONOUNS]
        else:
            content = [w for w in words if w not in self.STOPWORDS]
        if not content:
            content = words
        return content[-1] if content else ""

    def detect(self, text: str) -> List[MetaphorMapping]:
        results: List[MetaphorMapping] = []
        t = text.lower()

        # X is Y
        for m in re.finditer(
                r"(\b[a-zA-Z]+(?:\s+[a-zA-Z]+){0,3})\s+is\s+"
                r"(?:a\s+|an\s+|the\s+)?"
                r"(\b[a-zA-Z]+(?:\s+[a-zA-Z]+){0,3})", t):
            tgt = self._clean(m.group(1))
            src = self._clean(m.group(2))
            if tgt and src and tgt != src:
                results.append(MetaphorMapping(
                    target=tgt, source=src,
                    pattern=MetaphorPattern.IS, presence=0.9))

        # X like Y
        for m in re.finditer(
                r"(\b[a-zA-Z]+(?:\s+[a-zA-Z]+){0,3})\s+like\s+"
                r"(?:a\s+|an\s+|the\s+)?"
                r"(\b[a-zA-Z]+(?:\s+[a-zA-Z]+){0,3})", t):
            tgt = self._clean(m.group(1))
            src = self._clean(m.group(2))
            if tgt and src and tgt != src:
                results.append(MetaphorMapping(
                    target=tgt, source=src,
                    pattern=MetaphorPattern.LIKE, presence=0.8))

        # X of Y (weakest signal; proximity + grammar only)
        for m in re.finditer(
                r"(\b[a-zA-Z]+)\s+of\s+(?:a\s+|an\s+|the\s+)?"
                r"(\b[a-zA-Z]+)\b", t):
            tgt = self._clean(m.group(1))
            src = self._clean(m.group(2))
            if tgt and src and tgt != src:
                results.append(MetaphorMapping(
                    target=tgt, source=src,
                    pattern=MetaphorPattern.OF, presence=0.4))

        # compare X to Y
        for m in re.finditer(
                r"compare\s+(me|thee|you|him|her|us|them)\s+to\s+"
                r"(?:a\s+|an\s+|the\s+)?"
                r"(\b[a-zA-Z]+(?:['\s][a-zA-Z]+){0,3})", t):
            tgt = self._clean(m.group(1), allow_pronouns=True)
            src = self._clean(m.group(2))
            if tgt and src and tgt != src:
                results.append(MetaphorMapping(
                    target=tgt, source=src,
                    pattern=MetaphorPattern.COMPARE_TO, presence=0.85))

        return results


# =====================================================================
# Convenience: read a text through all analyzers
# =====================================================================

def read(text: str) -> CognitiveReading:
    reading = CognitiveReading(text=text)
    det = DeviationDetector()
    reading.deviations = det.alliteration(text) + det.repetition(text)
    reading.active_schemas = ImageSchemaDetector().detect(text)
    reading.metaphors = MetaphorDetector().detect(text)
    return reading

"""
poetry_engine_c3.py — Component 3: Meter and scansion through both grammars.

Atoms:
  - FootType: a named foot (iamb, trochee, anapest, dactyl, ...)
  - Meter: sequence of feet of uniform size
  - Line: text + stress pattern + word boundaries
  - WordClass: content vs function (Halliday's closed/open class distinction)

Composites:
  - GenerativeScansion (Chomsky-adjacent):
      template = deep structure; substitutions = transformations;
      surface line = derived output.
  - FunctionalScansion (Halliday-adjacent):
      meter as textual resource; content words foregrounded by
      stressed positions; function words highlighted when promoted
      onto stress.
  - DualScansion: both readings on the same line.

Both grammars are correct. They answer different questions.

Depends on Components 1 and 2.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Tuple


# =====================================================================
# Atom 1: FootType
# =====================================================================

class FootType(Enum):
    """A named foot. The 0/1 pattern is the STRESS SKELETON.

    0 = unstressed, 1 = stressed. Two-syllable feet and three-syllable
    feet are both represented; a Meter requires uniform foot size.
    """
    IAMB = "01"
    TROCHEE = "10"
    SPONDEE = "11"
    PYRRHIC = "00"
    ANAPEST = "001"
    DACTYL = "100"
    AMPHIBRACH = "010"
    BACCHIUS = "011"
    ANTIBACCHIUS = "110"
    TRIBACH = "000"

    @property
    def pattern(self) -> str:
        return self.value

    @property
    def size(self) -> int:
        return len(self.value)

    def __repr__(self):
        return f"Foot({self.name}={self.pattern})"


_FOOT_BY_PATTERN: Dict[str, FootType] = {f.pattern: f for f in FootType}


def foot_from_pattern(pattern: str) -> Optional[FootType]:
    return _FOOT_BY_PATTERN.get(pattern)


# =====================================================================
# Atom 2: Meter
# =====================================================================

@dataclass(frozen=True)
class Meter:
    """A sequence of feet of uniform size."""
    name: str
    feet: Tuple[FootType, ...]

    def __post_init__(self):
        if not self.feet:
            raise ValueError("Meter must have at least one foot")
        sizes = {f.size for f in self.feet}
        if len(sizes) > 1:
            raise ValueError(
                f"All feet must be the same size; got {sizes}")

    def template(self) -> str:
        return "".join(f.pattern for f in self.feet)

    def length(self) -> int:
        return len(self.template())

    def foot_size(self) -> int:
        return self.feet[0].size

    def number_of_feet(self) -> int:
        return len(self.feet)

    def __repr__(self):
        return f"Meter({self.name}, template={self.template()})"


# Standard meters

IAMBIC_PENTAMETER = Meter("iambic pentameter", (FootType.IAMB,) * 5)
IAMBIC_TETRAMETER = Meter("iambic tetrameter", (FootType.IAMB,) * 4)
IAMBIC_TRIMETER = Meter("iambic trimeter", (FootType.IAMB,) * 3)
TROCHAIC_TETRAMETER = Meter("trochaic tetrameter",
                             (FootType.TROCHEE,) * 4)
ANAPESTIC_TETRAMETER = Meter("anapestic tetrameter",
                              (FootType.ANAPEST,) * 4)
DACTYLIC_HEXAMETER = Meter("dactylic hexameter",
                            (FootType.DACTYL,) * 6)

STANDARD_METERS: Dict[str, Meter] = {
    m.name: m for m in [
        IAMBIC_PENTAMETER, IAMBIC_TETRAMETER, IAMBIC_TRIMETER,
        TROCHAIC_TETRAMETER, ANAPESTIC_TETRAMETER, DACTYLIC_HEXAMETER,
    ]
}


# =====================================================================
# Atom 3: Line
# =====================================================================

@dataclass
class Line:
    """A line: text + stress pattern + word boundaries."""
    text: str
    stress_pattern: str
    syllables: List[str]
    word_stress_offsets: List[Tuple[str, int, int]]

    def __len__(self):
        return len(self.stress_pattern)


# =====================================================================
# Atom 4: WordClass (Halliday)
# =====================================================================

class WordClass(Enum):
    """Halliday's open-class / closed-class distinction.

    CONTENT = open class (nouns, verbs, adjectives, adverbs).
    FUNCTION = closed class (determiners, prepositions, pronouns,
                            conjunctions, auxiliaries, etc.).
    """
    CONTENT = "content"
    FUNCTION = "function"


# A curated closed-class list. This is a simplified version of Halliday's
# "grammatical items" — the words that carry structural rather than
# lexical meaning.
_FUNCTION_WORDS = frozenset({
    "the", "a", "an", "of", "to", "in", "on", "at", "by", "for",
    "from", "with", "without", "upon", "through",
    "and", "or", "but", "nor", "so", "yet",
    "i", "you", "he", "she", "it", "we", "they",
    "me", "him", "her", "us", "them",
    "my", "your", "his", "its", "our", "their",
    "is", "are", "was", "were", "be", "been", "being",
    "have", "has", "had", "will", "would", "shall", "should",
    "may", "might", "must", "can", "could",
    "do", "does", "did",
    "this", "that", "these", "those",
    "as", "if", "when", "while", "because", "since", "though",
    "not", "no", "yes",
    # Archaic / poetic function words
    "thee", "thou", "thy", "thine", "ye", "hath", "doth",
    "ere", "o", "oh", "ah", "lo", "hark",
})


def classify_word(word: str) -> WordClass:
    w = word.lower().strip(".,;:!?'\"()[]-")
    if w in _FUNCTION_WORDS:
        return WordClass.FUNCTION
    return WordClass.CONTENT


# =====================================================================
# Line builder (integrates Component 1)
# =====================================================================

def build_line(text: str,
               syllabifier=None) -> Line:
    """Build a Line from text, using C1's syllabifier."""
    from poetry_engine_c1 import Syllabifier
    if syllabifier is None:
        syllabifier = Syllabifier()
    digits: List[str] = []
    syllables: List[str] = []
    word_offsets: List[Tuple[str, int, int]] = []
    for raw_word in text.split():
        clean = raw_word.strip(".,;:!?'\"()[]-")
        if not clean:
            continue
        start = len(digits)
        sp = syllabifier.stress_pattern(clean)
        digits.append(sp.digits)
        n = len(sp.digits)
        for j in range(n):
            syllables.append(f"{clean}_{j}")
        word_offsets.append((clean, start, n))
    return Line(
        text=text,
        stress_pattern="".join(digits),
        syllables=syllables,
        word_stress_offsets=word_offsets,
    )


# =====================================================================
# Composite: GenerativeScansion (Chomsky-adjacent)
# =====================================================================

class Realization(Enum):
    MATCH = "match"
    SUBSTITUTION = "substitution"
    MISSING = "missing"          # template longer than line at this foot
    EXTRAMETRICAL = "extrametrical"  # line longer than template


@dataclass
class FootScansion:
    position: int
    template_foot: FootType
    actual_pattern: str
    actual_foot: Optional[FootType]
    realization: Realization

    def __repr__(self):
        status = self.realization.value
        if self.realization == Realization.SUBSTITUTION and self.actual_foot:
            status += f" ({self.actual_foot.name})"
        return (f"F{self.position}: "
                f"template={self.template_foot.pattern} → "
                f"actual={self.actual_pattern} [{status}]")


@dataclass
class GenerativeScansion:
    """Derivation of a line from a meter template."""
    meter: Meter
    line: Line
    feet: List[FootScansion] = field(default_factory=list)
    extrametrical_indices: List[int] = field(default_factory=list)
    missing_count: int = 0

    def matches(self) -> int:
        return sum(1 for f in self.feet
                   if f.realization == Realization.MATCH)

    def substitutions(self) -> List[FootScansion]:
        return [f for f in self.feet
                if f.realization == Realization.SUBSTITUTION]

    def score(self) -> float:
        """Fraction of feet that exactly match the template."""
        if not self.feet:
            return 0.0
        return self.matches() / len(self.feet)

    def substitutions_by_kind(self) -> Dict[str, int]:
        counts: Dict[str, int] = {}
        for f in self.substitutions():
            name = f.actual_foot.name if f.actual_foot else "unnamed"
            counts[name] = counts.get(name, 0) + 1
        return counts

    def report(self) -> str:
        lines = [
            f"GenerativeScansion({self.meter.name})",
            f"  Template: {self.meter.template()}",
            f"  Line:     {self.line.stress_pattern}",
            f"  Matches:  {self.matches()}/{len(self.feet)} "
            f"({self.score():.0%})",
        ]
        subs = self.substitutions_by_kind()
        if subs:
            lines.append(f"  Substitutions: {subs}")
        for f in self.feet:
            lines.append(f"    {f}")
        if self.missing_count:
            lines.append(f"  Truncated by {self.missing_count} syllable(s)")
        if self.extrametrical_indices:
            lines.append(
                f"  Extrametrical positions: {self.extrametrical_indices}")
        return "\n".join(lines)


def scan_generative(line: Line, meter: Meter) -> GenerativeScansion:
    template = meter.template()
    actual = line.stress_pattern
    fs = meter.foot_size()

    # Align full feet
    n_template_feet = len(template) // fs
    n_actual_feet = len(actual) // fs
    n_feet = min(n_template_feet, n_actual_feet)

    feet: List[FootScansion] = []
    for i in range(n_feet):
        t_foot = meter.feet[i]
        start = i * fs
        actual_pat = actual[start:start + fs]
        a_foot = foot_from_pattern(actual_pat)
        real = (Realization.MATCH if actual_pat == t_foot.pattern
                else Realization.SUBSTITUTION)
        feet.append(FootScansion(
            position=i,
            template_foot=t_foot,
            actual_pattern=actual_pat,
            actual_foot=a_foot,
            realization=real,
        ))

    # Length mismatch
    extrametrical: List[int] = []
    missing = 0
    if len(actual) > len(template):
        extrametrical = list(range(len(template), len(actual)))
    elif len(template) > len(actual):
        missing = len(template) - len(actual)

    return GenerativeScansion(
        meter=meter,
        line=line,
        feet=feet,
        extrametrical_indices=extrametrical,
        missing_count=missing,
    )


# =====================================================================
# Composite: FunctionalScansion (Halliday-adjacent)
# =====================================================================

class TextualOperation(Enum):
    """How the meter is organizing the message."""
    ALIGNMENT = "alignment"
    # ^ content syllable on stressed position: meter supports content

    CONTENT_SUBORDINATION = "content_subordinated"
    # ^ content syllable on unstressed position: content is bracketed
    #   by the meter, made quieter, sometimes ironic

    FUNCTION_HIGHLIGHTING = "function_highlighted"
    # ^ function syllable on stressed position: grammar is promoted to
    #   prominence, foregrounding relational structure over content


@dataclass
class SyllableRole:
    index: int
    text: str
    stress: str
    word: str
    word_class: WordClass


@dataclass
class FunctionalScansion:
    """Reading of how the meter organizes the message."""
    line: Line
    roles: List[SyllableRole] = field(default_factory=list)

    def content_syllables(self) -> List[int]:
        return [r.index for r in self.roles
                if r.word_class == WordClass.CONTENT]

    def function_syllables(self) -> List[int]:
        return [r.index for r in self.roles
                if r.word_class == WordClass.FUNCTION]

    def content_on_stress(self) -> List[int]:
        return [r.index for r in self.roles
                if r.word_class == WordClass.CONTENT
                and r.stress == "1"]

    def content_subordinated(self) -> List[int]:
        return [r.index for r in self.roles
                if r.word_class == WordClass.CONTENT
                and r.stress == "0"]

    def function_highlighted(self) -> List[int]:
        return [r.index for r in self.roles
                if r.word_class == WordClass.FUNCTION
                and r.stress == "1"]

    def textual_fit(self) -> float:
        """Ratio of content syllables on stressed positions.

        1.0 = meter supports all content (perfect alignment).
        0.0 = all content is subordinated by the meter.
        """
        cs = self.content_syllables()
        if not cs:
            return 1.0
        return len(self.content_on_stress()) / len(cs)

    def operations(self) -> List[TextualOperation]:
        ops: List[TextualOperation] = []
        if self.content_on_stress():
            ops.append(TextualOperation.ALIGNMENT)
        if self.content_subordinated():
            ops.append(TextualOperation.CONTENT_SUBORDINATION)
        if self.function_highlighted():
            ops.append(TextualOperation.FUNCTION_HIGHLIGHTING)
        return ops

    def report(self) -> str:
        lines = [f"FunctionalScansion({self.line.text!r})"]
        for r in self.roles:
            marker = ""
            if r.word_class == WordClass.CONTENT and r.stress == "1":
                marker = "  ✓ content-on-stress"
            elif r.word_class == WordClass.CONTENT and r.stress == "0":
                marker = "  ✗ content-subordinated"
            elif r.word_class == WordClass.FUNCTION and r.stress == "1":
                marker = "  · function-highlighted"
            lines.append(
                f"    {r.index:>2}: {r.word:<14} "
                f"stress={r.stress} ({r.word_class.value}){marker}")
        lines.append(f"  Textual fit: {self.textual_fit():.2f}")
        ops = [o.value for o in self.operations()]
        lines.append(f"  Operations: {ops}")
        return "\n".join(lines)


def scan_functional(line: Line) -> FunctionalScansion:
    roles: List[SyllableRole] = []
    for word, start, length in line.word_stress_offsets:
        wc = classify_word(word)
        for j in range(length):
            idx = start + j
            if idx >= len(line.stress_pattern):
                break
            roles.append(SyllableRole(
                index=idx,
                text=(line.syllables[idx] if idx < len(line.syllables)
                      else f"{word}_{j}"),
                stress=line.stress_pattern[idx],
                word=word,
                word_class=wc,
            ))
    return FunctionalScansion(line=line, roles=roles)


# =====================================================================
# Composite: DualScansion
# =====================================================================

@dataclass
class DualScansion:
    generative: GenerativeScansion
    functional: FunctionalScansion

    def report(self) -> str:
        return (self.generative.report()
                + "\n\n"
                + self.functional.report())


def analyze_line(text: str,
                 meter: Meter,
                 syllabifier=None) -> DualScansion:
    line = build_line(text, syllabifier=syllabifier)
    return DualScansion(
        generative=scan_generative(line, meter),
        functional=scan_functional(line),
    )

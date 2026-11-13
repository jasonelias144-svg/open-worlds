"""
poetry_engine_c1.py — Component 1: Phonemes, syllables, stress.

The atoms of sound.

Depends on nothing (this is the ground floor of the Poetry cycle).
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Tuple
import re


# =====================================================================
# Atom 1: Phoneme
# =====================================================================

class PhoneType(Enum):
    VOWEL = "V"
    CONSONANT = "C"


@dataclass(frozen=True)
class Phoneme:
    """An irreducible sound unit.

    Uses a simplified IPA for English: the ~20 vowels (including
    diphthongs collapsed to nuclei) and ~24 consonants that matter
    for poetic purposes. We don't need acoustic precision; we need
    the distinctions that scansion and rhyme care about.
    """
    symbol: str
    kind: PhoneType
    voiced: bool = True
    features: frozenset = frozenset()

    def __repr__(self):
        return f"P/{self.symbol}/"


# Vowel inventory (IPA-inspired, English-centric)
VOWELS = {
    "i":  Phoneme("i",  PhoneType.VOWEL, voiced=True,
                   frozenset({"high", "front", "tense"})),
    "ɪ":  Phoneme("ɪ",  PhoneType.VOWEL, voiced=True,
                   frozenset({"high", "front", "lax"})),
    "e":  Phoneme("e",  PhoneType.VOWEL, voiced=True,
                   frozenset({"mid", "front", "tense"})),
    "ɛ":  Phoneme("ɛ",  PhoneType.VOWEL, voiced=True,
                   frozenset({"mid", "front", "lax"})),
    "æ":  Phoneme("æ",  PhoneType.VOWEL, voiced=True,
                   frozenset({"low", "front"})),
    "a":  Phoneme("a",  PhoneType.VOWEL, voiced=True,
                   frozenset({"low", "central"})),
    "ɑ":  Phoneme("ɑ",  PhoneType.VOWEL, voiced=True,
                   frozenset({"low", "back"})),
    "ɔ":  Phoneme("ɔ",  PhoneType.VOWEL, voiced=True,
                   frozenset({"mid", "back", "tense"})),
    "o":  Phoneme("o",  PhoneType.VOWEL, voiced=True,
                   frozenset({"mid", "back", "tense"})),
    "ʊ":  Phoneme("ʊ",  PhoneType.VOWEL, voiced=True,
                   frozenset({"high", "back", "lax"})),
    "u":  Phoneme("u",  PhoneType.VOWEL, voiced=True,
                   frozenset({"high", "back", "tense"})),
    "ʌ":  Phoneme("ʌ",  PhoneType.VOWEL, voiced=True,
                   frozenset({"mid", "central", "lax"})),
    "ə":  Phoneme("ə",  PhoneType.VOWEL, voiced=True,
                   frozenset({"mid", "central", "reduced"})),
    "ɝ":  Phoneme("ɝ",  PhoneType.VOWEL, voiced=True,
                   frozenset({"r-colored"})),
    # Diphthongs as single nuclei (for syllable-counting purposes)
    "aɪ": Phoneme("aɪ", PhoneType.VOWEL, voiced=True,
                   frozenset({"diphthong"})),
    "aʊ": Phoneme("aʊ", PhoneType.VOWEL, voiced=True,
                   frozenset({"diphthong"})),
    "eɪ": Phoneme("eɪ", PhoneType.VOWEL, voiced=True,
                   frozenset({"diphthong"})),
    "oʊ": Phoneme("oʊ", PhoneType.VOWEL, voiced=True,
                   frozenset({"diphthong"})),
    "ɔɪ": Phoneme("ɔɪ", PhoneType.VOWEL, voiced=True,
                   frozenset({"diphthong"})),
}

# Consonant inventory
CONSONANTS = {
    p: Phoneme(p, PhoneType.CONSONANT, voiced=v)
    for p, v in [
        ("p", False), ("b", True), ("t", False), ("d", True),
        ("k", False), ("g", True), ("f", False), ("v", True),
        ("θ", False), ("ð", True), ("s", False), ("z", True),
        ("ʃ", False), ("ʒ", True), ("h", False),
        ("tʃ", False), ("dʒ", True),
        ("m", True), ("n", True), ("ŋ", True),
        ("l", True), ("r", True), ("j", True), ("w", True),
    ]
}

ALL_PHONEMES = {**VOWELS, **CONSONANTS}


# =====================================================================
# Atom 2: Stress
# =====================================================================

class Stress(Enum):
    NONE = 0
    PRIMARY = 1
    SECONDARY = 2

    def digit(self) -> str:
        if self == Stress.PRIMARY:
            return "1"
        if self == Stress.SECONDARY:
            return "2"
        return "0"

    def is_stressed(self) -> bool:
        return self != Stress.NONE


# =====================================================================
# Atom 3: Syllable
# =====================================================================

@dataclass
class Syllable:
    """Onset + nucleus + coda + stress.

    The nucleus is required. Onset and coda may be empty.
    """
    onset: Tuple[Phoneme, ...]
    nucleus: Phoneme
    coda: Tuple[Phoneme, ...]
    stress: Stress = Stress.NONE

    def __post_init__(self):
        if self.nucleus.kind != PhoneType.VOWEL:
            raise ValueError(
                f"Syllable nucleus must be a vowel, got {self.nucleus}")

    def is_open(self) -> bool:
        """Does the syllable end in a vowel (open) or a consonant (closed)?"""
        return len(self.coda) == 0

    def weight(self) -> str:
        """Syllable weight: 'light' (open + short vowel),
        'heavy' (closed or long vowel), 'superheavy' (closed + long)."""
        long_v = any(f in self.nucleus.features
                     for f in ("tense", "diphthong"))
        closed = not self.is_open()
        if closed and long_v:
            return "superheavy"
        if closed or long_v:
            return "heavy"
        return "light"

    def __repr__(self):
        o = "".join(p.symbol for p in self.onset) or "∅"
        c = "".join(p.symbol for p in self.coda) or "∅"
        return f"S[{o}-{self.nucleus.symbol}-{c}·{self.stress.digit()}]"


# =====================================================================
# Atom 4: Word
# =====================================================================

@dataclass
class Word:
    """A word: spelling + syllable sequence + lexical stress pattern."""
    spelling: str
    syllables: List[Syllable]

    def __post_init__(self):
        if not self.syllables:
            raise ValueError("Word must have at least one syllable")

    def stress_pattern(self) -> str:
        return "".join(s.stress.digit() for s in self.syllables)

    def number_of_syllables(self) -> int:
        return len(self.syllables)

    def primary_stress_position(self) -> Optional[int]:
        for i, s in enumerate(self.syllables):
            if s.stress == Stress.PRIMARY:
                return i
        return None

    def __repr__(self):
        return (f"Word({self.spelling}, "
                f"{[str(s) for s in self.syllables]}, "
                f"stress={self.stress_pattern()})")


# =====================================================================
# Composite: StressPattern
# =====================================================================

@dataclass(frozen=True)
class StressPattern:
    """An abstract stress skeleton.

    A first-class object, not a string. Operations (inversion,
    matching against a meter template, comparison) are defined on it.
    """
    digits: str

    def __post_init__(self):
        if not all(c in "012" for c in self.digits):
            raise ValueError(
                f"StressPattern must be digits 0/1/2, got {self.digits}")

    def length(self) -> int:
        return len(self.digits)

    def inverted(self) -> "StressPattern":
        """Swap 1↔0 (secondary stays secondary)."""
        return StressPattern(
            "".join("1" if c == "0" else "0" if c == "1" else c
                    for c in self.digits))

    def matches(self, template: "StressPattern",
                tolerance: int = 0) -> bool:
        """Does this pattern match the template within tolerance?"""
        if self.length() != template.length():
            return False
        mismatches = sum(
            1 for a, b in zip(self.digits, template.digits)
            if a != b and not (a == "2" and b == "1")
                       and not (a == "1" and b == "2"))
        return mismatches <= tolerance

    def __repr__(self):
        return f"SP/{self.digits}/"


# =====================================================================
# Composite: StressDictionary
# =====================================================================

# A small but representative stress dictionary for common English words.
# Format: spelling → (syllable_count, stress_pattern)
STRESS_DICT: Dict[str, Tuple[int, str]] = {
    # Monosyllables (all primary unless function word)
    "the": (1, "0"), "a": (1, "0"), "an": (1, "0"),
    "of": (1, "0"), "to": (1, "0"), "in": (1, "0"),
    "and": (1, "0"), "or": (1, "0"), "but": (1, "0"),
    "day": (1, "1"), "night": (1, "1"), "light": (1, "1"),
    "dark": (1, "1"), "love": (1, "1"), "death": (1, "1"),
    "time": (1, "1"), "sun": (1, "1"), "moon": (1, "1"),
    "star": (1, "1"), "sea": (1, "1"), "sky": (1, "1"),
    # Trochees (10)
    "summer": (2, "10"), "winter": (2, "10"),
    "morning": (2, "10"), "evening": (2, "10"),
    "river": (2, "10"), "mountain": (2, "10"),
    "garden": (2, "10"), "shadow": (2, "10"),
    "tiger": (2, "10"), "willow": (2, "10"),
    "record": (2, "10"),  # noun
    # Iambs (01)
    "above": (2, "01"), "below": (2, "01"),
    "before": (2, "01"), "about": (2, "01"),
    "compare": (2, "01"), "return": (2, "01"),
    "receive": (2, "01"), "believe": (2, "01"),
    "forget": (2, "01"), "remember": (3, "010"),
    "record": (2, "01"),  # verb (note: same spelling, different stress)
    # Trisyllables
    "beautiful": (3, "100"), "wonderful": (3, "100"),
    "memory": (3, "100"), "yesterday": (3, "100"),
    "understand": (3, "201"), "afternoon": (3, "201"),
    "unhappy": (3, "010"), "beginning": (3, "010"),
    # Tetrasyllables
    "beautifully": (4, "1000"), "ordinarily": (4, "1000"),
    "syllable": (3, "100"), "pentameter": (4, "0100"),
    # Shakespeare's line
    "shall": (1, "0"), "i": (1, "1"), "compare": (2, "01"),
    "thee": (1, "0"), "summer's": (2, "10"), "day": (1, "1"),
}


# =====================================================================
# Composite: Syllabifier
# =====================================================================

# Very crude syllable counter: count vowel-letter groups, adjust for
# silent -e, handle common exceptions. This is a fallback for words
# not in the dictionary, not a linguistically precise algorithm.
_VOWEL_LETTERS = set("aeiouy")


def _count_vowel_groups(word: str) -> int:
    """Count maximal vowel-letter groups."""
    word = word.lower()
    count = 0
    in_vowel = False
    for ch in word:
        if ch in _VOWEL_LETTERS:
            if not in_vowel:
                count += 1
                in_vowel = True
        else:
            in_vowel = False
    return count


def _has_silent_e(word: str) -> bool:
    word = word.lower()
    return (len(word) > 2 and word.endswith("e")
            and word[-2] not in _VOWEL_LETTERS
            and _count_vowel_groups(word) > 1)


class Syllabifier:
    """Word → syllable sequence.

    Uses the dictionary when available. Otherwise, a rule-based
    fallback that produces plausible syllable counts (but not
    necessarily phonetically precise syllables).
    """

    def __init__(self, dictionary: Optional[Dict] = None):
        self.dictionary = dictionary or STRESS_DICT

    def count_syllables(self, word: str) -> int:
        key = word.lower().strip()
        # Strip common punctuation
        key = re.sub(r"[^\w']", "", key)
        if key in self.dictionary:
            return self.dictionary[key][0]
        # Fallback
        n = _count_vowel_groups(key)
        if _has_silent_e(key):
            n -= 1
        return max(1, n)

    def stress_pattern(self, word: str) -> StressPattern:
        key = word.lower().strip()
        key = re.sub(r"[^\w']", "", key)
        if key in self.dictionary:
            return StressPattern(self.dictionary[key][1])
        # Fallback: guess a trochaic default (many English nouns are)
        n = self.count_syllables(key)
        if n == 1:
            return StressPattern("1" if key not in
                                 {"the", "a", "an", "of", "to",
                                  "in", "and", "or", "but"}
                                 else "0")
        # Trochaic: primary on first, rest unstressed
        return StressPattern("1" + "0" * (n - 1))


# =====================================================================
# Convenience: Line-level stress extraction
# =====================================================================

def line_stress_pattern(text: str,
                        syllabifier: Optional[Syllabifier] = None
                        ) -> StressPattern:
    """Extract the stress pattern of a line of text.

    Splits on whitespace, syllabifies each word, concatenates.
    """
    if syllabifier is None:
        syllabifier = Syllabifier()
    digits = ""
    for word in text.split():
        digits += syllabifier.stress_pattern(word).digits
    return StressPattern(digits)


def line_syllable_count(text: str,
                        syllabifier: Optional[Syllabifier] = None
                        ) -> int:
    if syllabifier is None:
        syllabifier = Syllabifier()
    return sum(syllabifier.count_syllables(w) for w in text.split())

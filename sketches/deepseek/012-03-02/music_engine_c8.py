"""
music_engine_c8.py — Component 8: The Listener.

The closing loop of the music framework.

Atoms:
  - MusicalEvent: pitch class + onset + duration
  - Surprise: pitch-class surprise + interval surprise
  - MemoryTrace: decaying record of recent events

Composites:
  - PitchStyleModel: P(next pitch class | current pitch class)
  - IntervalStyleModel: P(next absolute interval | current absolute interval)
  - Listener: both models + memory + closure scoring
  - ListeningSession: streams events to a listener, tracks closure

The recognition theorem:
  A listener trained on a subject RECOGNIZES its inversion
  at the interval level (low interval surprise) but not at the
  pitch level (high pitch surprise). Recognition is invariant
  under transformation — it is structural, not absolute.

Depends on Components 1-7.
"""

import math
from dataclasses import dataclass, field
from fractions import Fraction
from typing import Dict, List, Optional, Tuple

from music_engine_c1 import Pitch, PitchClass
from music_engine_c3 import Note, Motive, Voice
from music_engine_c5 import Key, Mode
from music_engine_c6 import art_of_fugue_subject, real_answer, INVERT


# =====================================================================
# Atoms
# =====================================================================

@dataclass(frozen=True)
class MusicalEvent:
    """A single event: pitch class + metric position + duration."""
    pitch_class: int
    onset: Fraction
    duration: Fraction
    octave: int = 4

    def __repr__(self):
        names = ["C", "C#", "D", "D#", "E", "F",
                 "F#", "G", "G#", "A", "A#", "B"]
        return f"Event({names[self.pitch_class]}{self.octave})"


@dataclass
class Surprise:
    """Information content of an event under the listener's expectation.

    pitch_bits:    -log2 P(pitch_class | memory)
    interval_bits: -log2 P(abs_interval | memory)
    """
    pitch_class: int
    pitch_bits: float
    interval_bits: float

    @property
    def combined_bits(self) -> float:
        return (self.pitch_bits + self.interval_bits) / 2.0


class MemoryTrace:
    """A bounded, ordered record of recent events."""

    def __init__(self, max_length: int = 8):
        self.max_length = max_length
        self.events: List[MusicalEvent] = []

    def add(self, event: MusicalEvent):
        self.events.append(event)
        if len(self.events) > self.max_length:
            self.events.pop(0)

    def __len__(self):
        return len(self.events)

    def __getitem__(self, i):
        return self.events[i]


# =====================================================================
# Interval extraction: the symmetry that enables recognition
# =====================================================================

def absolute_interval(pc1: int, pc2: int) -> int:
    """Absolute interval as an interval class (0-6).

    Symmetric under negation: |+N| = |-N|.
    This is the mathematical basis of transformation-invariant recognition.
    """
    d = (pc2 - pc1) % 12
    if d > 6:
        d -= 12
    return abs(d)


# =====================================================================
# Style models
# =====================================================================

class PitchStyleModel:
    """Conditional distribution P(next pitch class | current pitch class).

    Laplace smoothing ensures every transition is possible, with
    negligible probability for unseen transitions.
    """

    def __init__(self, smoothing: float = 0.1):
        self.counts: Dict[int, Dict[int, int]] = {}
        self.totals: Dict[int, int] = {}
        self.smoothing = smoothing

    def train(self, events: List[MusicalEvent]):
        for i in range(1, len(events)):
            prev_pc = events[i - 1].pitch_class
            curr_pc = events[i].pitch_class
            self.counts.setdefault(prev_pc, {})
            self.counts[prev_pc][curr_pc] = \
                self.counts[prev_pc].get(curr_pc, 0) + 1
            self.totals[prev_pc] = self.totals.get(prev_pc, 0) + 1

    def predict(self, prev_pc: int) -> Dict[int, float]:
        if prev_pc in self.counts:
            total = self.totals[prev_pc]
            denom = total + 12 * self.smoothing
            return {
                pc: (self.counts[prev_pc].get(pc, 0) + self.smoothing) / denom
                for pc in range(12)
            }
        return {pc: 1.0 / 12 for pc in range(12)}


class IntervalStyleModel:
    """Conditional distribution P(next abs_interval | current abs_interval).

    Absolute intervals are invariant under inversion, so this model
    represents the listener's "structural" expectation.
    """

    def __init__(self, smoothing: float = 0.1):
        self.counts: Dict[int, Dict[int, int]] = {}
        self.totals: Dict[int, int] = {}
        self.smoothing = smoothing

    def train(self, events: List[MusicalEvent]):
        for i in range(2, len(events)):
            prev_iv = absolute_interval(
                events[i - 2].pitch_class, events[i - 1].pitch_class)
            curr_iv = absolute_interval(
                events[i - 1].pitch_class, events[i].pitch_class)
            self.counts.setdefault(prev_iv, {})
            self.counts[prev_iv][curr_iv] = \
                self.counts[prev_iv].get(curr_iv, 0) + 1
            self.totals[prev_iv] = self.totals.get(prev_iv, 0) + 1

    def predict(self, prev_iv: int) -> Dict[int, float]:
        if prev_iv in self.counts:
            total = self.totals[prev_iv]
            denom = total + 7 * self.smoothing
            return {
                iv: (self.counts[prev_iv].get(iv, 0) + self.smoothing) / denom
                for iv in range(7)
            }
        return {iv: 1.0 / 7 for iv in range(7)}


# =====================================================================
# The Listener
# =====================================================================

class Listener:
    """A listener with two expectation models and a memory trace.

    On each hear(event):
      1. Predict pitch class from last pitch class in memory
      2. Predict interval from last interval in memory
      3. Compute surprise for the event
      4. Record the event and the pre-event entropy
    """

    def __init__(self):
        self.pitch_model = PitchStyleModel()
        self.interval_model = IntervalStyleModel()
        self.memory = MemoryTrace()
        self.experience: List[Surprise] = []
        self.expectation_entropy: List[float] = []

    def train(self, events: List[MusicalEvent], n_passes: int = 1):
        for _ in range(n_passes):
            self.pitch_model.train(events)
            self.interval_model.train(events)

    def hear(self, event: MusicalEvent) -> Surprise:
        # Pre-event distributions
        if len(self.memory) >= 1:
            pitch_probs = self.pitch_model.predict(
                self.memory[-1].pitch_class)
        else:
            pitch_probs = {pc: 1.0 / 12 for pc in range(12)}

        if len(self.memory) >= 2:
            prev_iv = absolute_interval(
                self.memory[-2].pitch_class,
                self.memory[-1].pitch_class)
            interval_probs = self.interval_model.predict(prev_iv)
            curr_iv = absolute_interval(
                self.memory[-1].pitch_class, event.pitch_class)
        else:
            interval_probs = {iv: 1.0 / 7 for iv in range(7)}
            curr_iv = None

        # Surprise
        p_pitch = pitch_probs.get(event.pitch_class, 1e-6)
        pitch_bits = -math.log2(max(p_pitch, 1e-6))

        if curr_iv is not None:
            p_iv = interval_probs.get(curr_iv, 1e-6)
            interval_bits = -math.log2(max(p_iv, 1e-6))
        else:
            interval_bits = 0.0

        # Pre-event entropy (measure of confidence)
        entropy = -sum(p * math.log2(p)
                       for p in pitch_probs.values() if p > 0)
        self.expectation_entropy.append(entropy)

        surprise = Surprise(event.pitch_class, pitch_bits, interval_bits)
        self.experience.append(surprise)
        self.memory.add(event)
        return surprise

    def closure_score(self) -> float:
        """0 = no closure, 1 = complete closure.

        Closure is high when the pre-event entropy is low (the listener
        was confident) and the surprise is low (the prediction came true).
        """
        if not self.experience:
            return 0.0
        entropy = self.expectation_entropy[-1]
        surprise = self.experience[-1].combined_bits
        entropy_term = max(0.0, 1.0 - entropy / 4.0)
        surprise_term = max(0.0, 1.0 - surprise / 4.0)
        return entropy_term * surprise_term


# =====================================================================
# Engagement: the inverted-U
# =====================================================================

def engagement(surprise_bits: float) -> float:
    """Inverted-U: peak engagement at ~2.5 bits.

    Too predictable (0 bits) = boring. Too surprising (5+ bits) = noise.
    The sweet spot is intermediate surprise.
    """
    return math.exp(-((surprise_bits - 2.5) ** 2) / 2.0)


# =====================================================================
# ListeningSession
# =====================================================================

class ListeningSession:
    """Streams events to a listener and records the timeline."""

    def __init__(self, listener: Listener):
        self.listener = listener
        self.timeline: List[Tuple[int, Surprise]] = []
        self.closure_scores: List[float] = []
        self.entropies: List[float] = []

    def listen(self, events: List[MusicalEvent]) -> List[Tuple[int, Surprise]]:
        self.timeline = []
        self.closure_scores = []
        self.entropies = []
        for i, event in enumerate(events):
            s = self.listener.hear(event)
            self.timeline.append((i, s))
            self.closure_scores.append(self.listener.closure_score())
            self.entropies.append(self.listener.expectation_entropy[-1])
        return self.timeline

    def mean_surprise(self, which: str = 'combined',
                      skip_first: int = 2) -> float:
        items = self.timeline[skip_first:]
        if not items:
            return 0.0
        if which == 'pitch':
            return sum(s.pitch_bits for _, s in items) / len(items)
        if which == 'interval':
            return sum(s.interval_bits for _, s in items) / len(items)
        return sum(s.combined_bits for _, s in items) / len(items)

    def mean_engagement(self, skip_first: int = 2) -> float:
        items = self.timeline[skip_first:]
        if not items:
            return 0.0
        return sum(engagement(s.combined_bits)
                   for _, s in items) / len(items)

    def closures(self, threshold: float = 0.3) -> List[int]:
        return [i for i, c in enumerate(self.closure_scores)
                if c >= threshold]


# =====================================================================
# Helpers
# =====================================================================

def voice_to_events(voice: Voice) -> List[MusicalEvent]:
    return [
        MusicalEvent(
            pitch_class=note.pitch.pitch_class.value,
            onset=note.onset,
            duration=note.duration,
            octave=note.pitch.octave,
        )
        for note in voice.notes
    ]


def motive_to_events(motive: Motive) -> List[MusicalEvent]:
    return voice_to_events(Voice.from_motive(motive))


def pitch_sequence_to_events(pitch_classes: List[int],
                              octave: int = 4) -> List[MusicalEvent]:
    return [
        MusicalEvent(pc, Fraction(i), Fraction(1), octave)
        for i, pc in enumerate(pitch_classes)
    ]

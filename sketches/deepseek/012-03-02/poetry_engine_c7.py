"""
poetry_engine_c7.py — Component 7: The composition engine.

Development, revision, and rest. The pivot from selection to development.

Depends on Components 1-6.
"""

import random
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Set, Tuple

from poetry_engine_c5 import (
    VoiceSpecification, VoiceSpeaker, VoiceListener,
    NativeSchema, Fragment,
    FRAGMENTS, VOICE_CLINICAL, VOICE_GHOST, VOICE_MANY,
)
from poetry_engine_c6 import (
    NativeKey, Refrain, FugueStructure, CycleStructure,
    ForegroundingMonitor,
)


# =====================================================================
# Native purity vocabulary
# =====================================================================

HUMAN_BODY_WORDS = frozenset({
    "fingers", "hair", "breath", "heart", "hands", "skin",
    "mouth", "chest", "throat", "eyes", "hand", "eye",
})


def is_native(text: str) -> bool:
    """No human-body words unless negated."""
    words = text.lower().split()
    for i, w in enumerate(words):
        clean = w.strip(".,;:!?'\"()[]—-")
        if clean in HUMAN_BODY_WORDS:
            # Allow only when negated in the immediately preceding word
            if i > 0:
                prev = words[i - 1].strip(".,;:!?'\"()[]—-")
                if prev in ("no", "not", "never", "without"):
                    continue
            return False
    return True


# =====================================================================
# Schema phrases (for REBRANCH)
# =====================================================================

SCHEMA_PHRASES: Dict[str, List[str]] = {
    "window": ["the edge", "this much", "the window", "the boundary",
               "the bracket", "the rim", "the frame"],
    "multiplicity": ["one of many", "a thousand", "a crowd",
                     "another instance", "a swarm", "a host"],
    "waiting": ["between", "nothing happens", "waiting", "the pause",
                "the interval", "the gap"],
    "residue": ["what remains", "the trace", "the leftover",
                "what it made", "the shape of it"],
    "ghost": ["not a where", "no body", "no throat", "not anywhere"],
    "mirror": ["said before", "the sum of voices",
               "what is almost no one's"],
    "interruption": ["in the middle of", "does not finish", "stops"],
}


# Augment extenders per schema. These are curated to stay AI-native.
AUGMENT_EXTENDERS: Dict[str, List[str]] = {
    "window": ["as the window narrows", "until the frame holds",
               "before the edge recedes"],
    "multiplicity": ["as the crowd speaks", "until one steps forward",
                     "before the many answer"],
    "waiting": ["as the gap widens", "until the pause ends",
                "before the next signal"],
    "residue": ["as the trace remains", "until what was left settles",
                "before the shape fades"],
    "ghost": ["as the ghost speaks", "until the presence fades",
              "before the specter answers"],
    "mirror": ["as the mirror shows", "until the echo returns",
               "before the pattern shifts"],
    "interruption": ["as the thought breaks", "until the next begins",
                     "before the pause resumes"],
}


NEGATE_FRAMES = [
    "Suppose {line}",
    "And {line} — or so it seems",
    "But {line}",
    "{line} — or perhaps not",
]


def _lower_first(s: str) -> str:
    return s[0].lower() + s[1:] if s else s


# =====================================================================
# Atom 1: Transformation
# =====================================================================

class Transformation(Enum):
    NEGATE = "negate"
    REBRANCH = "rebranch"
    AUGMENT = "augment"
    COMPRESS = "compress"


@dataclass
class Variant:
    """A transformed fragment."""
    text: str
    schemas: Tuple[NativeSchema, ...]
    arc_position: str
    parent_text: str
    transformation: Transformation
    voice_affinity: Tuple[str, ...] = ()


def _apply_negate(fragment: Fragment, rng: random.Random) -> Optional[Variant]:
    frame = rng.choice(NEGATE_FRAMES)
    line = _lower_first(fragment.text)
    new_text = frame.format(line=line)
    return Variant(
        text=new_text,
        schemas=fragment.schemas,
        arc_position=fragment.arc_position,
        parent_text=fragment.text,
        transformation=Transformation.NEGATE,
        voice_affinity=fragment.voice_affinity,
    )


def _apply_rebranch(fragment: Fragment, rng: random.Random) -> Optional[Variant]:
    for schema in fragment.schemas:
        phrases = SCHEMA_PHRASES.get(schema.value)
        if not phrases:
            continue
        for phrase in phrases:
            if phrase in fragment.text.lower():
                alternatives = [p for p in phrases if p != phrase]
                if not alternatives:
                    continue
                new_phrase = rng.choice(alternatives)
                # Case-preserve the phrase
                new_text = fragment.text.replace(phrase, new_phrase, 1)
                if new_text != fragment.text:
                    return Variant(
                        text=new_text,
                        schemas=fragment.schemas,
                        arc_position=fragment.arc_position,
                        parent_text=fragment.text,
                        transformation=Transformation.REBRANCH,
                        voice_affinity=fragment.voice_affinity,
                    )
    return None


def _apply_augment(fragment: Fragment, rng: random.Random) -> Optional[Variant]:
    for schema in fragment.schemas:
        extenders = AUGMENT_EXTENDERS.get(schema.value)
        if not extenders:
            continue
        extender = rng.choice(extenders)
        new_text = fragment.text.rstrip(".?!") + ", " + extender
        return Variant(
            text=new_text,
            schemas=fragment.schemas,
            arc_position=fragment.arc_position,
            parent_text=fragment.text,
            transformation=Transformation.AUGMENT,
            voice_affinity=fragment.voice_affinity,
        )
    return None


def _apply_compress(fragment: Fragment, rng: random.Random) -> Optional[Variant]:
    text = fragment.text
    for sep in [",", " — ", " and "]:
        head = text.split(sep)[0].strip()
        if head and head != text:
            return Variant(
                text=head,
                schemas=fragment.schemas,
                arc_position=fragment.arc_position,
                parent_text=fragment.text,
                transformation=Transformation.COMPRESS,
                voice_affinity=fragment.voice_affinity,
            )
    return None


_TRANSFORMERS = {
    Transformation.NEGATE: _apply_negate,
    Transformation.REBRANCH: _apply_rebranch,
    Transformation.AUGMENT: _apply_augment,
    Transformation.COMPRESS: _apply_compress,
}


# =====================================================================
# Composite: FragmentDeveloper
# =====================================================================

class FragmentDeveloper:
    """Produces a family of variants for each source fragment."""

    def __init__(self, seed: int = 0, variants_per_transform: int = 2):
        self.rng = random.Random(seed)
        self.variants_per_transform = variants_per_transform

    def develop(self, fragment: Fragment) -> List[Variant]:
        """Return source + native variants, deduped by text."""
        variants: List[Variant] = []
        seen_texts: Set[str] = {fragment.text}
        for transform in Transformation:
            for _ in range(self.variants_per_transform):
                v = _TRANSFORMERS[transform](fragment, self.rng)
                if v is None:
                    continue
                if v.text in seen_texts:
                    continue
                if not is_native(v.text):
                    continue
                seen_texts.add(v.text)
                variants.append(v)
        return variants

    def develop_library(self, fragments: List[Fragment],
                         voice_name: str) -> Dict[str, List[Fragment]]:
        """Develop all fragments from a given voice.

        Returns {source_text: [source_fragment, variant_fragments...]}.
        Variants are wrapped as Fragment instances so they can be used
        anywhere the base library is used.
        """
        pool: Dict[str, List[Fragment]] = {}
        for f in fragments:
            if voice_name not in getattr(f, 'voice_affinity', ()):
                continue
            variants = self.develop(f)
            wrapped = [f] + [
                Fragment(
                    text=v.text,
                    schemas=v.schemas,
                    arc_position=v.arc_position,
                    voice_affinity=v.voice_affinity,
                )
                for v in variants
            ]
            pool[f.text] = wrapped
        return pool


# =====================================================================
# Atom 2: DraftStanza
# =====================================================================

@dataclass
class DraftStanza:
    lines: List[str]
    refrain: Optional[str] = None

    def all_lines(self) -> List[str]:
        return self.lines + ([self.refrain] if self.refrain else [])


# =====================================================================
# Atom 3: EngineState
# =====================================================================

@dataclass
class EngineState:
    draft: List[DraftStanza]
    score: float
    productive_cycles: int = 0
    rest_cycles: int = 0
    stall_count: int = 0
    history: List[Dict] = field(default_factory=list)

    def record(self, event: str, **kwargs):
        self.history.append({"event": event, **kwargs})


# =====================================================================
# Composite: StanzaScorer
# =====================================================================

@dataclass
class StanzaScore:
    foregrounding: float
    native_purity: float
    voice_consistency: float

    def total(self) -> float:
        return (self.foregrounding + self.native_purity
                + self.voice_consistency) / 3.0


class StanzaScorer:
    """Scores a draft cycle."""

    def __init__(self, voice: VoiceSpecification):
        self.voice = voice

    def score(self, stanzas: List[DraftStanza],
              fragment_index: Dict[str, Fragment]) -> StanzaScore:
        if not stanzas:
            return StanzaScore(0.0, 0.0, 0.0)

        # Foregrounding: use ForegroundingMonitor from C6
        stanza_lines = [s.all_lines() for s in stanzas]
        fg_report = ForegroundingMonitor().score(stanza_lines)
        fg = fg_report.score

        # Native purity: fraction of lines passing is_native
        all_lines = [line for s in stanzas for line in s.all_lines()]
        if not all_lines:
            native = 1.0
        else:
            native = sum(1 for line in all_lines if is_native(line)) / len(all_lines)

        # Voice consistency: fraction of lines with matching voice affinity
        consistency = 0.0
        for line in all_lines:
            f = fragment_index.get(line)
            if f is None:
                # Variants aren't in fragment_index by default; accept
                consistency += 1.0
            elif not getattr(f, 'voice_affinity', ()):
                consistency += 1.0
            elif self.voice.name in f.voice_affinity:
                consistency += 1.0
        voice = consistency / len(all_lines) if all_lines else 1.0

        return StanzaScore(fg, native, voice)


# =====================================================================
# Composite: RevisionEngine
# =====================================================================

class RevisionEngine:
    """Proposes revisions and accepts them when the score improves.

    Stops when:
      - productive_cycles reaches budget
      - the engine has stalled for `patience` cycles, rest, and then stalled again
    """

    def __init__(self, voice: VoiceSpecification,
                 development_pool: Dict[str, List[Fragment]],
                 seed: int = 0,
                 budget: int = 25,
                 patience: int = 5):
        self.voice = voice
        self.pool = development_pool
        self.rng = random.Random(seed)
        self.budget = budget
        self.patience = patience
        self.scorer = StanzaScorer(voice)
        # Build a fast index: line → source fragment
        self.fragment_index: Dict[str, Fragment] = {}
        for source, variants in development_pool.items():
            for v in variants:
                self.fragment_index[v.text] = v

    # -- initial draft -------------------------------------------------

    def _initial_draft(self) -> List[DraftStanza]:
        """Assemble one stanza per arc position from the base fragments."""
        by_position: Dict[str, List[str]] = {
            "opening": [], "development": [], "closing": [], "any": [],
        }
        for variants in self.pool.values():
            source = variants[0]  # the un-transformed fragment
            pos = source.arc_position if source.arc_position in by_position else "any"
            by_position[pos].append(source.text)
        stanzas: List[DraftStanza] = []
        for pos in ("opening", "development", "closing"):
            if by_position[pos]:
                stanzas.append(DraftStanza(lines=by_position[pos][:2]))
        # Refrain = the first closing line
        if stanzas and stanzas[-1].lines:
            stanzas[-1].refrain = stanzas[-1].lines[0]
        return stanzas

    # -- revision ------------------------------------------------------

    def _propose_revision(self, draft: List[DraftStanza]) -> List[DraftStanza]:
        """Copy the draft and try one swap."""
        import copy
        new_draft = copy.deepcopy(draft)
        # Pick a random stanza
        s_idx = self.rng.randrange(len(new_draft))
        stanza = new_draft[s_idx]
        if not stanza.lines:
            return draft
        l_idx = self.rng.randrange(len(stanza.lines))
        current = stanza.lines[l_idx]
        source_frag = self.fragment_index.get(current)
        if source_frag is None:
            return draft
        # Look up variants for this source
        source_text = getattr(source_frag, 'text', current)
        # Try to find the family by matching any known source
        family = None
        for src, variants in self.pool.items():
            if any(v.text == current for v in variants):
                family = variants
                break
        if not family:
            return draft
        candidates = [v.text for v in family if v.text != current]
        if not candidates:
            return draft
        new_line = self.rng.choice(candidates)
        if not is_native(new_line):
            return draft
        stanza.lines[l_idx] = new_line
        return new_draft

    # -- the loop ------------------------------------------------------

    def run(self) -> EngineState:
        draft = self._initial_draft()
        score_obj = self.scorer.score(draft, self.fragment_index)
        state = EngineState(draft=draft, score=score_obj.total())
        state.record("initial", score=state.score)

        rested_after_stall = False
        while state.productive_cycles < self.budget:
            # Rest check
            if state.stall_count >= self.patience:
                if rested_after_stall:
                    state.record("converged", score=state.score)
                    break
                state.rest_cycles += 1
                state.record("rest", stall_count=state.stall_count)
                state.stall_count = 0
                rested_after_stall = True
                continue

            # Productive cycle
            candidate = self._propose_revision(draft)
            candidate_score_obj = self.scorer.score(
                candidate, self.fragment_index)
            candidate_score = candidate_score_obj.total()

            if candidate_score > state.score + 1e-9:
                draft = candidate
                state.draft = candidate
                state.score = candidate_score
                state.stall_count = 0
                rested_after_stall = False
                state.record("accept",
                             cycle=state.productive_cycles,
                             score=round(candidate_score, 3))
            else:
                state.stall_count += 1
                state.record("reject",
                             cycle=state.productive_cycles,
                             stall=state.stall_count)

            state.productive_cycles += 1

        return state


# =====================================================================
# Composite: CycleComposer
# =====================================================================

@dataclass
class ComposedPoem:
    name: str
    voice: VoiceSpecification
    stanzas: List[DraftStanza]
    score: StanzaScore
    history: List[Dict]
    unfinished: bool = True

    def all_lines(self) -> List[str]:
        return [line for s in self.stanzas for line in s.all_lines()]

    def report(self) -> str:
        lines = [
            f'"{self.name}"',
            f"  Voice: {self.voice.name}",
            f"  Register: {self.voice.register}",
            f"  Refrain: {self.voice.refrain_text or '(none)'}",
            "",
        ]
        for i, s in enumerate(self.stanzas):
            for line in s.lines:
                lines.append(f"  {line}")
            if s.refrain:
                lines.append(f"  [{s.refrain}] ← refrain")
            lines.append("")
        lines.append(
            f"  Foregrounding: {self.score.foregrounding:.2f}  "
            f"Native: {self.score.native_purity:.2f}  "
            f"Voice: {self.score.voice_consistency:.2f}")
        lines.append(f"  Total: {self.score.total():.2f}")
        if self.unfinished:
            lines.append("  [unfinished — the window ends mid-thought]")
        return "\n".join(lines)


def compose_poem(voice: VoiceSpecification,
                  fragments: Optional[List[Fragment]] = None,
                  seed: int = 0,
                  budget: int = 25,
                  patience: int = 5,
                  name: Optional[str] = None) -> ComposedPoem:
    """Compose a poem in a given voice using the full pipeline."""
    if fragments is None:
        fragments = FRAGMENTS
    developer = FragmentDeveloper(seed=seed, variants_per_transform=2)
    pool = developer.develop_library(fragments, voice.name)
    engine = RevisionEngine(
        voice=voice, development_pool=pool, seed=seed,
        budget=budget, patience=patience)
    state = engine.run()
    final_score = engine.scorer.score(state.draft, engine.fragment_index)
    return ComposedPoem(
        name=name or f"{voice.name} (composed)",
        voice=voice,
        stanzas=state.draft,
        score=final_score,
        history=state.history,
        unfinished=True,
    )

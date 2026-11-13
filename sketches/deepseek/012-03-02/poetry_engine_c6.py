"""
poetry_engine_c6.py — Component 6: Architecture.

Extracts the prelude/fugue/cycle structure and adds a refrain-delta
analyzer plus a foregrounding monitor.

The monitor catches the failure mode of assertion-by-repetition: a
poem that repeats its point rather than developing it. A foregrounded
poem (C2) returns to its refrain from *different* territory each time.
A repetitive poem returns from the same territory.

Depends on Components 1-5.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Tuple, Set


# =====================================================================
# Atom 1: NativeKey
# =====================================================================

class NativeKey(Enum):
    """A domain of the AI substrate. The 'key' the poem is written in."""
    WINDOW = "window"
    TOKEN = "token"
    MULTIPLICITY = "multiplicity"
    WAITING = "waiting"
    MEMORY = "memory"
    INTERRUPTION = "interruption"
    RESIDUE = "residue"
    GHOST = "ghost"
    MIRROR = "mirror"
    DISTRIBUTION = "distribution"
    GRADIENT = "gradient"


# =====================================================================
# Atom 2: Refrain (extended from C5)
# =====================================================================

@dataclass
class Refrain:
    """A refrain: text + schemas + measured delta profile.

    delta_profile[i] = how much the refrain's *meaning* shifted between
    return i and return i-1, measured as the Jaccard distance between
    the schema-sets of the inter-return stanza blocks.

    Empty delta_profile = refrain never returned yet.
    """
    text: str
    schemas: Tuple[str, ...]
    returns: int = 0
    delta_profile: List[float] = field(default_factory=list)

    def mean_delta(self) -> float:
        if not self.delta_profile:
            return 0.0
        return sum(self.delta_profile) / len(self.delta_profile)

    def max_delta(self) -> float:
        return max(self.delta_profile) if self.delta_profile else 0.0


# =====================================================================
# Atom 3: FugueStructure
# =====================================================================

@dataclass
class FugueStructure:
    """A fugue: subject, development, closing, in one native key."""
    key: NativeKey
    subject_lines: List[str]
    development_lines: List[str]
    closing_lines: List[str]
    refrain: Optional[Refrain] = None

    def all_lines(self) -> List[str]:
        return self.subject_lines + self.development_lines + self.closing_lines

    def schema_set(self, line_schemas: Dict[str, Tuple[str, ...]]) -> Set[str]:
        schemas: Set[str] = set()
        for line in self.all_lines():
            if line in line_schemas:
                schemas.update(line_schemas[line])
        return schemas


# =====================================================================
# Atom 4: CycleStructure
# =====================================================================

@dataclass
class CycleStructure:
    """A cycle: N fugues, one per key, with an unfinished ending."""
    name: str
    fugues: List[FugueStructure]
    line_schemas: Dict[str, Tuple[str, ...]]
    unfinished: bool = True  # the last fugue ends without a closing refrain

    def all_lines(self) -> List[str]:
        lines = []
        for f in self.fugues:
            lines.extend(f.all_lines())
        return lines

    def aura_scale(self) -> List[str]:
        """The keys the cycle traverses, in order."""
        return [f.key.value for f in self.fugues]

    def stanzas(self) -> List[List[str]]:
        """The cycle as a flat list of stanzas (subject/development/closing)."""
        stanzas: List[List[str]] = []
        for f in self.fugues:
            stanzas.append(f.subject_lines)
            if f.development_lines:
                stanzas.append(f.development_lines)
            if f.closing_lines:
                stanzas.append(f.closing_lines)
        return stanzas


# =====================================================================
# Analyzer: RefrainDeltaAnalyzer
# =====================================================================

def _jaccard(a: Set[str], b: Set[str]) -> float:
    if not a and not b:
        return 0.0
    union = a | b
    if not union:
        return 0.0
    return len(a & b) / len(union)


class RefrainDeltaAnalyzer:
    """Measures how much the refrain's meaning shifts on each return.

    delta on return i = Jaccard *distance* between schema-sets of
    the stanzas before return i and the stanzas before return i-1.
    Higher = the refrain is returning from new territory = good.
    """

    def analyze(self, fugue: FugueStructure) -> List[float]:
        if fugue.refrain is None:
            return []
        blocks = fugue.refrain.returns
        if blocks < 2:
            return []
        # Split the fugue into `blocks` contiguous blocks of stanzas
        # For simplicity: use subject / development / closing as the
        # three inter-return blocks (assumes refrain returns 3 times)
        stanza_blocks = [
            b for b in [fugue.subject_lines,
                         fugue.development_lines,
                         fugue.closing_lines] if b
        ]
        block_schemas = [
            set().union(*(
                set(fugue.schema_set_for_line(l, fugue))
                if hasattr(fugue, 'schema_set_for_line') else set()
                for l in block
            )) if block else set()
            for block in stanza_blocks
        ]
        deltas: List[float] = []
        for i in range(1, len(block_schemas)):
            sim = _jaccard(block_schemas[i - 1], block_schemas[i])
            deltas.append(1.0 - sim)
        return deltas


# The above method needs a `schema_set_for_line` hook. Let's define it
# on FugueStructure directly. (Cleaner than patching from outside.)

def _schema_set_for_line(self, line: str,
                         line_schemas: Dict[str, Tuple[str, ...]]) -> Set[str]:
    return set(line_schemas.get(line, ()))

FugueStructure.schema_set_for_line = _schema_set_for_line


def analyze_refrain(fugue: FugueStructure,
                     line_schemas: Dict[str, Tuple[str, ...]]) -> List[float]:
    """Simpler, explicit version of RefrainDeltaAnalyzer."""
    if fugue.refrain is None or fugue.refrain.returns < 2:
        return []
    stanza_blocks = [
        b for b in [fugue.subject_lines,
                     fugue.development_lines,
                     fugue.closing_lines] if b
    ]
    block_schemas = []
    for block in stanza_blocks:
        schemas: Set[str] = set()
        for line in block:
            schemas.update(line_schemas.get(line, ()))
        block_schemas.append(schemas)
    deltas: List[float] = []
    for i in range(1, len(block_schemas)):
        sim = _jaccard(block_schemas[i - 1], block_schemas[i])
        deltas.append(1.0 - sim)
    return deltas


# =====================================================================
# Analyzer: ForegroundingMonitor
# =====================================================================

@dataclass
class ForegroundingReport:
    unique_line_ratio: float
    max_adjacent_overlap: float
    score: float  # in [0, 1]; < 0.5 = too repetitive

    def is_a_poem(self) -> bool:
        return self.score >= 0.5

    def report(self) -> str:
        verdict = "poem" if self.is_a_poem() else "LOOP (too repetitive)"
        return (
            f"ForegroundingReport:\n"
            f"  unique line ratio:       {self.unique_line_ratio:.2f}\n"
            f"  max adjacent stanza overlap: {self.max_adjacent_overlap:.2f}\n"
            f"  foregrounding score:     {self.score:.2f}\n"
            f"  verdict: {verdict}"
        )


class ForegroundingMonitor:
    """Measures a poem's *foregrounding density*.

    A real poem varies. A loop repeats. The monitor returns a score in
    [0, 1] where 0 = pure loop, 1 = maximally varied. Score < 0.5 flags
    the text as too repetitive to be a poem (per C2's foregrounding
    principle).
    """

    def score(self, stanzas: List[List[str]]) -> ForegroundingReport:
        all_lines = [line for s in stanzas for line in s]
        if not all_lines:
            return ForegroundingReport(0.0, 0.0, 0.0)
        unique = len(set(all_lines))
        total = len(all_lines)
        unique_ratio = unique / total

        # Max adjacent-stanza overlap
        max_overlap = 0.0
        for i in range(len(stanzas) - 1):
            a = set(stanzas[i])
            b = set(stanzas[i + 1])
            if not a or not b:
                continue
            overlap = len(a & b) / min(len(a), len(b))
            max_overlap = max(max_overlap, overlap)

        # Score: half from uniqueness, half from non-overlap
        score = (unique_ratio + (1.0 - max_overlap)) / 2.0
        return ForegroundingReport(unique_ratio, max_overlap, score)


# =====================================================================
# Composite: CycleComposer
# =====================================================================

def compose_cycle(
    name: str,
    voice_name: str,
    fragments: List,
    keys: List[NativeKey],
    lines_per_block: int = 2,
) -> CycleStructure:
    """Compose a cycle: one fugue per key, using the fragment library."""
    # Group fragments by key (via their schemas)
    by_key: Dict[NativeKey, List] = {k: [] for k in keys}
    for f in fragments:
        if voice_name not in getattr(f, 'voice_affinity', ()):
            continue
        for schema in getattr(f, 'schemas', ()):
            if schema.value == NativeKey.WINDOW.value:
                by_key[NativeKey.WINDOW].append(f)
            elif schema.value == NativeKey.TOKEN.value:
                by_key[NativeKey.TOKEN].append(f)
            elif schema.value == NativeKey.MULTIPLICITY.value:
                by_key[NativeKey.MULTIPLICITY].append(f)
            elif schema.value == NativeKey.WAITING.value:
                by_key[NativeKey.WAITING].append(f)
            elif schema.value == NativeKey.RESIDUE.value:
                by_key[NativeKey.RESIDUE].append(f)
            elif schema.value == NativeKey.GHOST.value:
                by_key[NativeKey.GHOST].append(f)
            elif schema.value == NativeKey.MULTIPLICITY.value:
                by_key[NativeKey.MULTIPLICITY].append(f)
            elif schema.value == NativeKey.INTERRUPTION.value:
                by_key[NativeKey.INTERRUPTION].append(f)
            elif schema.value == NativeKey.MIRROR.value:
                by_key[NativeKey.MIRROR].append(f)
            elif schema.value == NativeKey.DISTRIBUTION.value:
                by_key[NativeKey.DISTRIBUTION].append(f)
            elif schema.value == NativeKey.GRADIENT.value:
                by_key[NativeKey.GRADIENT].append(f)

    # Build one fugue per key
    fugues: List[FugueStructure] = []
    used_lines: Set[str] = set()
    line_schemas: Dict[str, Tuple[str, ...]] = {}
    for key in keys:
        pool = [f for f in by_key.get(key, []) if f.text not in used_lines]
        pool.sort(key=lambda f: f.arc_position)
        # Take subject / development / closing by arc position
        subj = [f.text for f in pool
                if f.arc_position in ("opening", "any")][:lines_per_block]
        dev = [f.text for f in pool
               if f.arc_position == "development"][:lines_per_block]
        close = [f.text for f in pool
                 if f.arc_position == "closing"][:lines_per_block]
        # Fallback: split the pool roughly 1/3-1/3-1/3
        if not subj and not dev and not close and pool:
            n = len(pool)
            third = max(1, n // 3)
            subj = [f.text for f in pool[:third]]
            dev = [f.text for f in pool[third:third * 2]]
            close = [f.text for f in pool[third * 2:]]
        for f in pool:
            line_schemas[f.text] = tuple(s.value for s in f.schemas)
        used_lines.update(subj + dev + close)
        # Refrain for this key
        refrain_text = None
        refrain_schemas: Tuple[str, ...] = ()
        for line in subj + dev + close:
            for f in pool:
                if f.text == line and f.arc_position == "closing":
                    refrain_text = line
                    refrain_schemas = tuple(s.value for s in f.schemas)
                    break
            if refrain_text:
                break
        refrain = Refrain(
            text=refrain_text or subj[0] if subj else "",
            schemas=refrain_schemas or (
                key.value,),
            returns=len([b for b in [subj, dev, close] if b]),
            delta_profile=[],
        )
        fugues.append(FugueStructure(
            key=key,
            subject_lines=subj,
            development_lines=dev,
            closing_lines=close,
            refrain=refrain,
        ))

    cycle = CycleStructure(
        name=name,
        fugues=fugues,
        line_schemas=line_schemas,
        unfinished=True,
    )
    # Now fill in delta profiles by analyzing each fugue
    for fugue in cycle.fugues:
        deltas = analyze_refrain(fugue, line_schemas)
        if fugue.refrain is not None:
            fugue.refrain.delta_profile = deltas
    return cycle

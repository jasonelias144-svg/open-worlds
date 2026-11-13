"""
multiverse_c23.py — Component 23: Multi-Visit Provenance.

Fixes C22's single-visit assumption. An identity can visit a
world multiple times; the passport carries one admission per
visit and one departure per closed visit.

Pairing rule:
  - Admissions sorted by timestamp.
  - Departures sorted by timestamp.
  - For each admission (in order), pair with the earliest UNUSED
    departure whose timestamp is STRICTLY greater than the
    admission's. If none, the visit is open (no departure).
  - Unused departures after all admissions are orphaned.

Residency: derived from the last visit to a world (open=resident,
closed=departed). Stored nowhere; computed on read.

Composes with C21 (entry-level provenance) and C22 (departures).
No new protocol operation, no new trust primitive.

Honest limits:
  - Two admissions with identical timestamps: pairing is
    non-deterministic (Python's stable sort preserves input order,
    which may not reflect "reality"). Passports with this pattern
    are anomalous; the pairing doesn't try to fix them.
  - Multiple open visits to the same world: possible if the
    passport has multiple admissions without intervening
    departures. The World enforces one resident at a time, so a
    well-formed passport can't have this; the pairing doesn't
    assume well-formedness.
  - No re-ordering of events based on content. If a passport has
    events that are out of order by timestamp, they're sorted.
    If the timestamps themselves are wrong, the report is wrong.
    Signing timestamps is future work.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional, Tuple

from multiverse_c13 import HAS_CRYPTO
from multiverse_c15 import PassportEntry
from multiverse_c22 import (
    Departure, PassportV2WithDepartures, verify_departure,
)


# =====================================================================
# Timestamp parsing
# =====================================================================

def _parse_ts(ts: str) -> datetime:
    """Parse ISO 8601. Handles 'Z' suffix."""
    if ts.endswith("Z"):
        ts = ts[:-1] + "+00:00"
    return datetime.fromisoformat(ts)


# =====================================================================
# Visit
# =====================================================================

@dataclass(frozen=True)
class Visit:
    """One visit to a world: an admission and the departure that
    closed it (or None if still open)."""
    admission: PassportEntry
    departure: Optional[Departure] = None

    @property
    def is_open(self) -> bool:
        return self.departure is None

    @property
    def residency(self) -> str:
        return "resident" if self.is_open else "departed"


@dataclass
class OrphanDeparture:
    """A departure with no matching admission. Either a forged
    departure or a passport missing an admission."""
    departure: Departure
    reason: str


# =====================================================================
# Pairing
# =====================================================================

def pair_visits(
    entries: Tuple[PassportEntry, ...],
    departures: Tuple[Departure, ...],
) -> Tuple[List[Visit], List[OrphanDeparture]]:
    """Pair admissions with departures to produce visits.

    Deterministic given the input timestamps. Sorts both lists,
    walks admissions in order, matches each with the earliest
    unused strictly-later departure.
    """
    sorted_entries = sorted(entries, key=lambda e: _parse_ts(e.timestamp))
    sorted_deps = sorted(departures,
                         key=lambda d: _parse_ts(d.timestamp))

    used: set = set()
    visits: List[Visit] = []

    for entry in sorted_entries:
        entry_ts = _parse_ts(entry.timestamp)
        matched_idx: Optional[int] = None
        for i, dep in enumerate(sorted_deps):
            if i in used:
                continue
            if _parse_ts(dep.timestamp) > entry_ts:
                matched_idx = i
                break
        if matched_idx is not None:
            used.add(matched_idx)
            visits.append(Visit(admission=entry,
                                departure=sorted_deps[matched_idx]))
        else:
            visits.append(Visit(admission=entry, departure=None))

    orphans = [
        OrphanDeparture(
            departure=sorted_deps[i],
            reason="no matching admission before this departure",
        )
        for i in range(len(sorted_deps)) if i not in used
    ]
    return visits, orphans


def visits_for(
    passport: PassportV2WithDepartures, entity_id: str,
) -> Tuple[List[Visit], List[OrphanDeparture]]:
    """Pair visits for a single world."""
    entries = tuple(e for e in passport.entries
                    if e.entity_id == entity_id)
    deps = tuple(d for d in passport.departures
                 if d.entity_id == entity_id)
    return pair_visits(entries, deps)


def current_residency(
    passport: PassportV2WithDepartures, entity_id: str,
) -> str:
    """resident | departed | never_visited

    The residency of the last visit. Never stored; always derived.
    """
    visits, _ = visits_for(passport, entity_id)
    if not visits:
        return "never_visited"
    return visits[-1].residency


# =====================================================================
# Per-visit and per-world provenance
# =====================================================================

@dataclass
class VisitProvenance:
    visit: Visit
    visit_index: int          # 1-based, per world
    is_last_visit: bool
    admission_provenance: Any = None  # C21/C22 EntryProvenance
    departure_verified: Optional[bool] = None  # None = absent or unsigned
    departure_reason: str = ""

    @property
    def verdict(self) -> str:
        ap = self.admission_provenance
        if ap is None:
            return "unverifiable"
        # Admission must be valid (or unverified-for-unsigned);
        # if it's invalid or unverifiable, the visit is too.
        ap_verdict = getattr(ap, "verdict", "unverifiable")
        if ap_verdict in ("invalid", "unverifiable"):
            return ap_verdict
        if self.visit.departure is not None:
            if self.departure_verified is False:
                return "invalid"
            if self.departure_verified is None:
                # Unsigned departure — inherits admission verdict
                return ap_verdict
        return ap_verdict


@dataclass
class WorldProvenance:
    entity_id: str
    visits: List[VisitProvenance] = field(default_factory=list)
    orphans: List[OrphanDeparture] = field(default_factory=list)

    @property
    def residency(self) -> str:
        if not self.visits:
            return "never_visited"
        return self.visits[-1].visit.residency

    @property
    def all_verified(self) -> bool:
        if not self.visits:
            return False
        return all(v.verdict == "verified" for v in self.visits)


@dataclass
class VisitedPassportReport:
    passport_token: str
    passport_name: str
    worlds: List[WorldProvenance] = field(default_factory=list)

    def all_verified(self) -> bool:
        return (bool(self.worlds)
                and all(w.all_verified for w in self.worlds)
                and not any(w.orphans for w in self.worlds))

    def count_visits(self) -> int:
        return sum(len(w.visits) for w in self.worlds)

    def count_orphans(self) -> int:
        return sum(len(w.orphans) for w in self.worlds)

    def format(self) -> str:
        lines = [
            "=" * 70,
            "Multi-Visit Provenance Report",
            "=" * 70,
            f"  Passport: {self.passport_token[:16]}... "
            f"({self.passport_name})",
            f"  Worlds:   {len(self.worlds)}",
            f"  Visits:   {self.count_visits()}",
            f"  Orphans:  {self.count_orphans()}",
            "",
        ]
        for i, w in enumerate(self.worlds, 1):
            lines.append(
                f"  [{i}] {w.entity_id}  "
                f"({len(w.visits)} visit(s), {w.residency})")
            for v in w.visits:
                marker = _marker(v.verdict)
                if v.visit.is_open:
                    span = f"{v.visit.admission.timestamp} → (open)"
                else:
                    span = (f"{v.visit.admission.timestamp} → "
                            f"{v.visit.departure.timestamp}")
                lines.append(f"      {marker} Visit {v.visit_index}: "
                             f"{span}")
                if v.admission_provenance is not None:
                    lines.append(
                        f"          admission: "
                        f"{v.admission_provenance.verdict}")
                if v.visit.departure is not None:
                    if v.departure_verified is True:
                        lines.append(
                            f"          departure: ✓ verified")
                    elif v.departure_verified is False:
                        lines.append(
                            f"          departure: ✗ INVALID")
                    else:
                        lines.append(
                            f"          departure: (unsigned)")
            for o in w.orphans:
                lines.append(
                    f"      ! orphan departure: {o.departure.timestamp}")
                lines.append(f"        {o.reason}")
            lines.append("")
        lines.append(f"  all_verified: {self.all_verified()}")
        return "\n".join(lines)

    def to_dict(self) -> Dict:
        return {
            "passport_token": self.passport_token,
            "passport_name": self.passport_name,
            "worlds": [
                {
                    "entity_id": w.entity_id,
                    "residency": w.residency,
                    "visits": [
                        {
                            "visit_index": v.visit_index,
                            "admission_ts": v.visit.admission.timestamp,
                            "departure_ts": (
                                v.visit.departure.timestamp
                                if v.visit.departure else None),
                            "admission_verdict":
                                getattr(v.admission_provenance,
                                        "verdict", None),
                            "departure_verified": v.departure_verified,
                            "verdict": v.verdict,
                        }
                        for v in w.visits
                    ],
                    "orphans": [
                        {"departure_ts": o.departure.timestamp,
                         "reason": o.reason}
                        for o in w.orphans
                    ],
                }
                for w in self.worlds
            ],
            "all_verified": self.all_verified(),
        }


def _marker(verdict: str) -> str:
    return {"verified": "✓", "invalid": "✗",
            "unverifiable": "?", "unverified": "·"}.get(verdict, "?")


# =====================================================================
# The verifier — composes with C21
# =====================================================================

PublicKeyResolver = Callable[[str], Optional[str]]


def verify_passport_visits(
    passport: PassportV2WithDepartures,
    entry_provenances: Dict[int, Any],
    resolver: PublicKeyResolver,
) -> VisitedPassportReport:
    """Verify each visit's admission and departure.

    `entry_provenances` maps id(entry) → C21/C22 EntryProvenance
    (the caller builds this dict from a ProvenanceReport). Any
    object with `.verdict` and `.manifest_public_key` works.

    `resolver` returns each world's current public key. Departure
    signatures are verified against it; admission signatures are
    assumed verified by C21 (they were).

    Does not raise. Every failure is a verdict.
    """
    report = VisitedPassportReport(
        passport_token=passport.identity.token,
        passport_name=passport.identity.name,
    )

    entity_ids = (sorted({e.entity_id for e in passport.entries} |
                         {d.entity_id for d in passport.departures}))

    for eid in entity_ids:
        visits, orphans = visits_for(passport, eid)
        pk = resolver(eid)
        world = WorldProvenance(entity_id=eid, orphans=orphans)
        for i, visit in enumerate(visits):
            ap = entry_provenances.get(id(visit.admission))
            dp_verified: Optional[bool] = None
            dp_reason = ""
            if visit.departure is not None:
                if not visit.departure.is_signed:
                    dp_verified = None
                    dp_reason = "unsigned departure"
                elif not HAS_CRYPTO:
                    dp_verified = None
                    dp_reason = "cryptography not installed"
                else:
                    dp_verified = verify_departure(
                        visit.departure,
                        passport.identity.token,
                        pk)
                    dp_reason = ("signature valid" if dp_verified
                                 else "signature INVALID")
            world.visits.append(VisitProvenance(
                visit=visit,
                visit_index=i + 1,
                is_last_visit=(i == len(visits) - 1),
                admission_provenance=ap,
                departure_verified=dp_verified,
                departure_reason=dp_reason,
            ))
        report.worlds.append(world)

    return report


def build_entry_provenances(c21_report) -> Dict[int, Any]:
    """From a C21 ProvenanceReport, build the {id(entry): prov} dict
    that verify_passport_visits expects."""
    return {id(ep.entry): ep for ep in c21_report.entries}

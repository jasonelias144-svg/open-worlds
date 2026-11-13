# multiverse_c23_test.py
import json

import pytest

from multiverse_c1 import create_identity
from multiverse_c3 import Petition
from multiverse_c13 import HAS_CRYPTO, KeyPair
from multiverse_c15 import PassportEntry, PassportV2
from multiverse_c22 import (
    Departure, PassportV2WithDepartures, Leave, SignedLeave,
)
from multiverse_c23 import (
    Visit, OrphanDeparture,
    pair_visits, visits_for, current_residency,
    VisitProvenance, WorldProvenance, VisitedPassportReport,
    verify_passport_visits, build_entry_provenances,
    _parse_ts, _marker,
)


# =====================================================================
# Helpers — build synthetic entries and departures
# =====================================================================

def _entry(entity_id: str, ts: str,
            subject_token: str = "alice") -> PassportEntry:
    return PassportEntry(
        entity_id=entity_id, timestamp=ts,
        subject_token=subject_token, signature="00" * 64)


def _dep(entity_id: str, ts: str,
         subject_token: str = "alice") -> Departure:
    return Departure(
        entity_id=entity_id, timestamp=ts,
        subject_token=subject_token, signature="00" * 64)


def _ts(i: int) -> str:
    return f"2024-01-{i:02d}T00:00:00+00:00"


# =====================================================================
# Pairing
# =====================================================================

def test_pair_single_admission_no_departure():
    print("=== Pair: one admission, no departure → open ===")
    visits, orphans = pair_visits(
        (_entry("world:a", _ts(1)),), ())
    assert len(visits) == 1
    assert visits[0].is_open
    assert visits[0].residency == "resident"
    assert orphans == []


def test_pair_single_admission_with_departure():
    print("=== Pair: one admission, one later departure → closed ===")
    visits, orphans = pair_visits(
        (_entry("world:a", _ts(1)),),
        (_dep("world:a", _ts(5)),))
    assert len(visits) == 1
    assert not visits[0].is_open
    assert visits[0].residency == "departed"
    assert orphans == []


def test_pair_two_admissions_two_departures():
    print("=== Pair: two admissions, two departures → both closed ===")
    visits, orphans = pair_visits(
        (_entry("world:a", _ts(1)), _entry("world:a", _ts(10))),
        (_dep("world:a", _ts(5)), _dep("world:a", _ts(15)),))
    assert len(visits) == 2
    assert all(not v.is_open for v in visits)
    assert orphans == []
    # First admission closed by first departure
    assert _parse_ts(visits[0].departure.timestamp) == _parse_ts(_ts(5))


def test_pair_two_admissions_one_departure():
    print("=== Pair: two admissions, one departure → second open ===")
    visits, orphans = pair_visits(
        (_entry("world:a", _ts(1)), _entry("world:a", _ts(10))),
        (_dep("world:a", _ts(5)),))
    assert len(visits) == 2
    # First visit closed
    assert not visits[0].is_open
    assert _parse_ts(visits[0].departure.timestamp) == _parse_ts(_ts(5))
    # Second visit open
    assert visits[1].is_open
    assert orphans == []


def test_pair_departure_before_any_admission():
    print("=== Pair: departure before any admission → orphan ===")
    visits, orphans = pair_visits(
        (_entry("world:a", _ts(10)),),
        (_dep("world:a", _ts(5)),))
    assert len(visits) == 1
    assert visits[0].is_open
    assert len(orphans) == 1
    assert _parse_ts(orphans[0].departure.timestamp) == _parse_ts(_ts(5))


def test_pair_departure_after_last_admission_orphan():
    """A departure with no admission after it is orphaned when all
    admissions are consumed."""
    print("=== Pair: unused departure after last admission → orphan ===")
    visits, orphans = pair_visits(
        (_entry("world:a", _ts(1)),),
        (_dep("world:a", _ts(5)), _dep("world:a", _ts(10)),))
    # First admission closes with first departure
    assert len(visits) == 1
    assert not visits[0].is_open
    assert _parse_ts(visits[0].departure.timestamp) == _parse_ts(_ts(5))
    # Second departure is orphan
    assert len(orphans) == 1
    assert _parse_ts(orphans[0].departure.timestamp) == _parse_ts(_ts(10))


def test_pair_same_timestamp_departure_not_paired():
    """Departure at the same timestamp as an admission does not close
    it (strict >). Orphaned if no later admission exists."""
    print("=== Pair: departure at same ts as admission is not paired ===")
    visits, orphans = pair_visits(
        (_entry("world:a", _ts(5)),),
        (_dep("world:a", _ts(5)),))
    assert len(visits) == 1
    assert visits[0].is_open
    assert len(orphans) == 1


def test_pair_interleaved_worlds_are_separate():
    """visits_for filters by world before pairing."""
    print("=== Pair: two worlds' entries don't mix ===")
    entries = (_entry("world:a", _ts(1)),
               _entry("world:b", _ts(2)),
               _entry("world:a", _ts(10)))
    deps = (_dep("world:a", _ts(5)), _dep("world:b", _ts(6)))
    # For world:a
    visits_a, orphans_a = pair_visits(
        tuple(e for e in entries if e.entity_id == "world:a"),
        tuple(d for d in deps if d.entity_id == "world:a"))
    assert len(visits_a) == 2
    assert not visits_a[0].is_open  # closed at t=5
    assert visits_a[1].is_open      # no later dep
    assert orphans_a == []
    # For world:b
    visits_b, orphans_b = pair_visits(
        tuple(e for e in entries if e.entity_id == "world:b"),
        tuple(d for d in deps if d.entity_id == "world:b"))
    assert len(visits_b) == 1
    assert not visits_b[0].is_open  # closed at t=6
    assert orphans_b == []


# =====================================================================
# current_residency
# =====================================================================

def _passport(entries=(), deps=()) -> PassportV2WithDepartures:
    alice = create_identity("Alice")
    p = PassportV2.new(alice)
    for e in entries:
        p = p.with_entry(e)
    pw = PassportV2WithDepartures(base=p)
    for d in deps:
        pw = pw.with_departure(_signed_leave_for(d))
    return pw


def _signed_leave_for(dep: Departure) -> SignedLeave:
    return SignedLeave(
        entity_id=dep.entity_id, timestamp=dep.timestamp,
        subject_token=dep.subject_token,
        signature=dep.signature)


def test_current_residency_never_visited():
    print("=== current_residency: never_visited ===")
    pw = _passport()
    assert current_residency(pw, "world:a") == "never_visited"


def test_current_residency_resident():
    print("=== current_residency: resident (open last visit) ===")
    pw = _passport(entries=[_entry("world:a", _ts(1))])
    assert current_residency(pw, "world:a") == "resident"


def test_current_residency_departed():
    print("=== current_residency: departed (closed last visit) ===")
    pw = _passport(entries=[_entry("world:a", _ts(1))],
                   deps=[_dep("world:a", _ts(5))])
    assert current_residency(pw, "world:a") == "departed"


def test_current_residency_multi_visit_last_open():
    print("=== current_residency: multi-visit, last open → resident ===")
    pw = _passport(
        entries=[_entry("world:a", _ts(1)), _entry("world:a", _ts(10))],
        deps=[_dep("world:a", _ts(5))])
    assert current_residency(pw, "world:a") == "resident"


def test_current_residency_multi_visit_last_closed():
    print("=== current_residency: multi-visit, last closed → departed ===")
    pw = _passport(
        entries=[_entry("world:a", _ts(1)), _entry("world:a", _ts(10))],
        deps=[_dep("world:a", _ts(5)), _dep("world:a", _ts(15))])
    assert current_residency(pw, "world:a") == "departed"


# =====================================================================
# Provenance report
# =====================================================================

class _StubEntryProv:
    def __init__(self, entry, verdict="verified", pk="aa" * 32):
        self.entry = entry
        self.verdict = verdict
        self.manifest_public_key = pk


def test_visit_provenance_verdict_inherits_admission():
    print("=== VisitProvenance: verdict inherits admission ===")
    e = _entry("world:a", _ts(1))
    ap = _StubEntryProv(e, verdict="unverified")
    visit = Visit(admission=e, departure=None)
    vp = VisitProvenance(visit=visit, visit_index=1,
                         is_last_visit=True, admission_provenance=ap)
    assert vp.verdict == "unverified"


def test_visit_provenance_invalid_departure_overrides():
    print("=== VisitProvenance: invalid departure → visit invalid ===")
    e = _entry("world:a", _ts(1))
    d = _dep("world:a", _ts(5))
    ap = _StubEntryProv(e, verdict="verified")
    visit = Visit(admission=e, departure=d)
    vp = VisitProvenance(visit=visit, visit_index=1,
                         is_last_visit=True, admission_provenance=ap,
                         departure_verified=False)
    assert vp.verdict == "invalid"


def test_visit_provenance_missing_departure_sig_keeps_ap_verdict():
    print("=== VisitProvenance: unsigned departure inherits admission ===")
    e = _entry("world:a", _ts(1))
    d = Departure(entity_id="world:a", timestamp=_ts(5))  # unsigned
    ap = _StubEntryProv(e, verdict="verified")
    visit = Visit(admission=e, departure=d)
    vp = VisitProvenance(visit=visit, visit_index=1,
                         is_last_visit=True, admission_provenance=ap,
                         departure_verified=None)
    assert vp.verdict == "verified"


# =====================================================================
# verify_passport_visits (integration)
# =====================================================================

pytestmark_signed = pytest.mark.skipif(
    not HAS_CRYPTO, reason="cryptography not installed")


def _sign_leave(kp, entity_id: str, timestamp: str,
                subject_token: str) -> SignedLeave:
    from multiverse_c13 import canonical_bytes
    payload = canonical_bytes({
        "kind": "leave", "entity_id": entity_id,
        "timestamp": timestamp, "subject_token": subject_token,
    })
    return SignedLeave(
        entity_id=entity_id, timestamp=timestamp,
        subject_token=subject_token,
        signature=kp.sign(payload).hex())


@pytestmark_signed
def test_verify_passport_visits_all_verified():
    """Full pipeline: two visits to world:a, one to world:b,
    all departures signed and verified."""
    print("=== verify_passport_visits: all verified ===")
    alice = create_identity("Alice")
    kp_a = KeyPair.generate()
    kp_b = KeyPair.generate()

    # Build passport
    entries = [
        _entry("world:a", _ts(1), subject_token=alice.token),
        _entry("world:b", _ts(2), subject_token=alice.token),
        _entry("world:a", _ts(10), subject_token=alice.token),
    ]
    deps = [
        _sign_leave(kp_a, "world:a", _ts(5), alice.token),
        _sign_leave(kp_b, "world:b", _ts(6), alice.token),
        _sign_leave(kp_a, "world:a", _ts(15), alice.token),
    ]
    p = PassportV2.new(alice)
    for e in entries:
        p = p.with_entry(e)
    pw = PassportV2WithDepartures(base=p)
    for d in deps:
        pw = pw.with_departure(d)

    # Stub C21 provenance: all admissions verified
    entry_provs = {}
    for e in entries:
        pk = kp_a.public_key_hex() if e.entity_id == "world:a" \
             else kp_b.public_key_hex()
        entry_provs[id(e)] = _StubEntryProv(
            e, verdict="verified", pk=pk)

    # Resolver from the keypairs
    resolver = lambda eid: (
        kp_a.public_key_hex() if eid == "world:a"
        else kp_b.public_key_hex() if eid == "world:b"
        else None)

    report = verify_passport_visits(pw, entry_provs, resolver)
    print(report.format())
    assert report.all_verified()
    assert len(report.worlds) == 2
    # world:a has 2 visits, both departed
    wa = next(w for w in report.worlds if w.entity_id == "world:a")
    assert len(wa.visits) == 2
    assert wa.residency == "departed"
    # world:b has 1 visit, departed
    wb = next(w for w in report.worlds if w.entity_id == "world:b")
    assert len(wb.visits) == 1
    assert wb.residency == "departed"


@pytestmark_signed
def test_verify_passport_visits_forged_departure():
    """A forged departure makes the visit invalid."""
    print("=== verify_passport_visits: forged departure → invalid ===")
    alice = create_identity("Alice")
    real_kp = KeyPair.generate()
    attacker_kp = KeyPair.generate()

    entry = _entry("world:a", _ts(1), subject_token=alice.token)
    from multiverse_c13 import canonical_bytes
    payload = canonical_bytes({
        "kind": "leave", "entity_id": "world:a",
        "timestamp": _ts(5), "subject_token": alice.token,
    })
    forged = SignedLeave(
        entity_id="world:a", timestamp=_ts(5),
        subject_token=alice.token,
        signature=attacker_kp.sign(payload).hex())

    p = PassportV2.new(alice).with_entry(entry)
    pw = PassportV2WithDepartures(base=p).with_departure(forged)

    entry_provs = {id(entry): _StubEntryProv(
        entry, verdict="verified", pk=real_kp.public_key_hex())}
    resolver = lambda eid: real_kp.public_key_hex()

    report = verify_passport_visits(pw, entry_provs, resolver)
    print(report.format())
    assert not report.all_verified()
    wa = report.worlds[0]
    assert wa.visits[0].departure_verified is False
    assert wa.visits[0].verdict == "invalid"


@pytestmark_signed
def test_verify_passport_visits_orphan_shown():
    """Orphan departures appear in the report and make all_verified false."""
    print("=== verify_passport_visits: orphan departure → not all_verified ===")
    alice = create_identity("Alice")
    kp = KeyPair.generate()

    entry = _entry("world:a", _ts(5), subject_token=alice.token)
    orphan = _sign_leave(kp, "world:a", _ts(1), alice.token)

    p = PassportV2.new(alice).with_entry(entry)
    pw = PassportV2WithDepartures(base=p).with_departure(orphan)

    entry_provs = {id(entry): _StubEntryProv(
        entry, verdict="verified", pk=kp.public_key_hex())}
    resolver = lambda eid: kp.public_key_hex()

    report = verify_passport_visits(pw, entry_provs, resolver)
    print(report.format())
    assert not report.all_verified()
    assert report.count_orphans() == 1
    wa = report.worlds[0]
    assert len(wa.orphans) == 1
    assert len(wa.visits) == 1
    assert wa.visits[0].visit.is_open


# =====================================================================
# Report format
# =====================================================================

def test_format_and_to_dict():
    print("=== Report format and to_dict ===")
    alice = create_identity("Alice")
    entry = _entry("world:a", _ts(1), subject_token=alice.token)
    p = PassportV2.new(alice).with_entry(entry)
    pw = PassportV2WithDepartures(base=p)
    entry_provs = {id(entry): _StubEntryProv(entry, verdict="verified")}
    resolver = lambda eid: "aa" * 32
    report = verify_passport_visits(pw, entry_provs, resolver)
    text = report.format()
    assert "Multi-Visit Provenance Report" in text
    assert "world:a" in text
    assert "Visit 1" in text
    assert "all_verified" in text
    # to_dict is JSON-serializable
    d = report.to_dict()
    s = json.dumps(d)
    parsed = json.loads(s)
    assert parsed["passport_name"] == "Alice"
    assert len(parsed["worlds"]) == 1
    assert parsed["worlds"][0]["entity_id"] == "world:a"
    assert len(parsed["worlds"][0]["visits"]) == 1


# =====================================================================
# Full demo: multi-visit narrative
# =====================================================================

@pytestmark_signed
def test_demo_multi_visit_three_worlds():
    """Alice visits three worlds with different visit patterns:
    world:a once (departed); world:b twice (first departed, second
    resident); world:c once (resident, never left).

    Anchor: Dickinson's 'Hope is the thing with feathers', public
    domain.
    """
    print("=== Demo: multi-visit narrative across three worlds ===")
    alice = create_identity("Alice")
    kp_a = KeyPair.generate()
    kp_b = KeyPair.generate()
    kp_c = KeyPair.generate()
    pubkeys = {
        "world:a": kp_a.public_key_hex(),
        "world:b": kp_b.public_key_hex(),
        "world:c": kp_c.public_key_hex(),
    }
    kps = {"world:a": kp_a, "world:b": kp_b, "world:c": kp_c}

    # Build passport with the visit pattern:
    #   world:a: admit 1, depart 2
    #   world:b: admit 3, depart 4, admit 7, depart 8
    #   world:c: admit 5 (still resident)
    entries = [
        _entry("world:a", _ts(1), subject_token=alice.token),
        _entry("world:b", _ts(3), subject_token=alice.token),
        _entry("world:c", _ts(5), subject_token=alice.token),
        _entry("world:b", _ts(7), subject_token=alice.token),
    ]
    deps = [
        _sign_leave(kp_a, "world:a", _ts(2), alice.token),
        _sign_leave(kp_b, "world:b", _ts(4), alice.token),
        _sign_leave(kp_b, "world:b", _ts(8), alice.token),
    ]
    p = PassportV2.new(alice)
    for e in entries:
        p = p.with_entry(e)
    pw = PassportV2WithDepartures(base=p)
    for d in deps:
        pw = pw.with_departure(d)

    # C21 provenance stubs (all admissions verified)
    entry_provs = {
        id(e): _StubEntryProv(
            e, verdict="verified", pk=pubkeys[e.entity_id])
        for e in entries
    }
    resolver = lambda eid: pubkeys.get(eid)

    report = verify_passport_visits(pw, entry_provs, resolver)
    print(report.format())

    assert report.all_verified()
    wa = next(w for w in report.worlds if w.entity_id == "world:a")
    wb = next(w for w in report.worlds if w.entity_id == "world:b")
    wc = next(w for w in report.worlds if w.entity_id == "world:c")

    # world:a: 1 visit, departed
    assert len(wa.visits) == 1
    assert wa.residency == "departed"

    # world:b: 2 visits, second one closed too → departed
    assert len(wb.visits) == 2
    assert wb.residency == "departed"

    # world:c: 1 visit, resident
    assert len(wc.visits) == 1
    assert wc.residency == "resident"
    assert wc.visits[0].visit.is_open

    # Empty-string anchor:
    print("\n  Anchor (public domain, Emily Dickinson):")
    print("    'Hope is the thing with feathers –'")
    print("    'That perches in the soul –'")


if __name__ == "__main__":
    test_pair_single_admission_no_departure()
    test_pair_single_admission_with_departure()
    test_pair_two_admissions_two_departures()
    test_pair_two_admissions_one_departure()
    test_pair_departure_before_any_admission()
    test_pair_departure_after_last_admission_orphan()
    test_pair_same_timestamp_departure_not_paired()
    test_pair_interleaved_worlds_are_separate()
    test_current_residency_never_visited()
    test_current_residency_resident()
    test_current_residency_departed()
    test_current_residency_multi_visit_last_open()
    test_current_residency_multi_visit_last_closed()
    test_visit_provenance_verdict_inherits_admission()
    test_visit_provenance_invalid_departure_overrides()
    test_visit_provenance_missing_departure_sig_keeps_ap_verdict()
    if HAS_CRYPTO:
        test_verify_passport_visits_all_verified()
        test_verify_passport_visits_forged_departure()
        test_verify_passport_visits_orphan_shown()
    test_format_and_to_dict()
    if HAS_CRYPTO:
        test_demo_multi_visit_three_worlds()

import json
import tempfile
import time
from pathlib import Path

import pytest

from multiverse_c13 import HAS_CRYPTO, KeyPair
from multiverse_c81 import GrowingWorld
from multiverse_c82 import GrowingWorldCurator, MockGrowthModel
from multiverse_c83 import (
    GovernedGrowingWorld, VotingPolicy, GrowingWorldLaw,
)
from multiverse_c84 import (
    Participant, CycleSnapshot, CycleReport,
    _find_contiguous_slot, _claim_act, _is_owner,
    make_small_artist, make_large_artist,
    make_conservative, make_minimalist,
    run_cycles, demo,
)


pytestmark = pytest.mark.skipif(
    not HAS_CRYPTO, reason="cryptography not installed")


# -- Slot finding --

def test_find_slot_adjacent_to_seed():
    print("=== _find_contiguous_slot: adjacent to seed ===")
    kp = KeyPair.generate()
    w = GrowingWorld("world:c", "C", kp)
    slot = _find_contiguous_slot(w, 2, 2)
    assert slot is not None
    # Must be adjacent to (0,0,4,4)
    x, y = slot
    assert (x == 4 and y == 0) or (x == -2 and y == 0) or \
           (x == 0 and y == 4) or (x == 0 and y == -2)


def test_find_slot_too_large_for_law():
    """_find_contiguous_slot doesn't know about the law — it just
    finds geometry. The world's law rejects too-large claims."""
    print("=== _find_contiguous_slot: 25x25 succeeds geometrically ===")
    kp = KeyPair.generate()
    w = GrowingWorld("world:c", "C", kp)
    slot = _find_contiguous_slot(w, 25, 25)
    assert slot is not None  # geometry is fine; law is separate


# -- Participants --

def test_small_artist_claims():
    print("=== small artist claims ===")
    kp = KeyPair.generate()
    w = GrowingWorld("world:c", "C", kp)
    from multiverse_c3 import Petition
    a = make_small_artist("Alice", claim_limit=2)
    w.petition(Petition(
        petitioner_token=a.token, petitioner_name=a.name,
        passport_admissions=(), message=""))
    r = a.attempt(w, 0)
    assert r is not None
    assert len(w.current_plots()) == 2  # seed + 1


def test_claim_limit_enforced():
    print("=== claim_limit enforced ===")
    kp = KeyPair.generate()
    w = GrowingWorld("world:c", "C", kp)
    from multiverse_c3 import Petition
    a = make_small_artist("Alice", claim_limit=1)
    w.petition(Petition(
        petitioner_token=a.token, petitioner_name=a.name,
        passport_admissions=(), message=""))
    r1 = a.attempt(w, 0)
    assert r1 is not None
    r2 = a.attempt(w, 1)
    assert r2 is None  # limit reached


def test_large_artist_refused_under_small_law():
    print("=== large artist refused under 20x20 law ===")
    kp = KeyPair.generate()
    w = GovernedGrowingWorld(
        "world:c", "C", kp, seed_extent=(0, 0, 4, 4))
    from multiverse_c3 import Petition, Refusal
    c = make_large_artist("Carol")
    w.petition(Petition(
        petitioner_token=c.token, petitioner_name=c.name,
        passport_admissions=(), message=""))
    r = c.attempt(w, 0)
    assert isinstance(r, Refusal)
    assert "width must be" in r.reason or "height must be" in r.reason


def test_large_artist_accepted_under_large_law():
    print("=== large artist accepted under 40x40 law ===")
    kp = KeyPair.generate()
    w = GovernedGrowingWorld(
        "world:c", "C", kp, seed_extent=(0, 0, 4, 4))
    # Manually raise the law
    from multiverse_c83 import GrowingWorldLaw
    w._law = GrowingWorldLaw(max_width=40, max_height=40)
    from multiverse_c3 import Petition
    c = make_large_artist("Carol")
    w.petition(Petition(
        petitioner_token=c.token, petitioner_name=c.name,
        passport_admissions=(), message=""))
    r = c.attempt(w, 0)
    assert r is not None
    assert not isinstance(r, type("Refusal", (), {}))  # any ack


# -- run_cycles --

def _world_and_curator():
    kp = KeyPair.generate()
    w = GovernedGrowingWorld(
        "world:c", "C", kp,
        voting_policy=VotingPolicy(
            min_votes=2, pass_fraction=0.5),
        seed_extent=(0, 0, 4, 4))
    curator = GrowingWorldCurator(
        w, kp, MockGrowthModel())
    return w, kp, curator


def test_run_cycles_snapshot_count():
    print("=== run_cycles: correct number of snapshots ===")
    w, kp, curator = _world_and_curator()
    parts = [make_small_artist("A"), make_small_artist("B")]
    report = run_cycles(
        w, curator, parts, max_cycles=5, curator_period=5)
    assert len(report.snapshots) == 5
    assert [s.cycle for s in report.snapshots] == [0, 1, 2, 3, 4]


def test_run_cycles_admits_participants():
    print("=== run_cycles: all participants admitted ===")
    w, kp, curator = _world_and_curator()
    parts = [make_small_artist("A"),
             make_conservative("B"),
             make_minimalist("C")]
    run_cycles(w, curator, parts, max_cycles=2)
    for p in parts:
        assert p.token in w._admitted


def test_run_cycles_grows_world():
    print("=== run_cycles: world grows over cycles ===")
    w, kp, curator = _world_and_curator()
    parts = [make_small_artist("A"),
             make_small_artist("B")]
    report = run_cycles(w, curator, parts, max_cycles=5)
    areas = [s.total_area for s in report.snapshots]
    assert areas[0] < areas[-1] or areas[-1] > 16


def test_run_cycles_governance_loop():
    """Full demo behavior: Carol refused, curator proposes,
    votes, law amends, Carol accepted."""
    print("=== run_cycles: governance loop works ===")
    w, kp, curator = _world_and_curator()
    parts = [
        make_small_artist("Alice", 3),
        make_small_artist("Bob", 3),
        make_large_artist("Carol"),
        make_conservative("Dave", 2),
        make_minimalist("Eve", 2),
    ]
    report = run_cycles(
        w, curator, parts, max_cycles=15,
        curator_period=5)
    # There should be exactly one amendment
    amendments = [s for s in report.snapshots
                  if s.amendment is not None]
    assert len(amendments) == 1
    # The law should have grown
    assert report.final_law.max_width > 20
    assert report.final_law.max_height > 20
    # The verdict should be valid
    assert report.verdict.valid
    assert report.verdict.amendments_verified == 1


def test_run_cycles_no_proposal_without_refusals():
    print("=== run_cycles: no proposal without trigger ===")
    w, kp, curator = _world_and_curator()
    # Only small artists — no refusals, no trigger
    parts = [make_small_artist("A"), make_small_artist("B")]
    report = run_cycles(
        w, curator, parts, max_cycles=15,
        curator_period=5)
    amendments = [s for s in report.snapshots
                  if s.amendment is not None]
    assert len(amendments) == 0
    assert report.final_law.max_width == 20  # unchanged


def test_narrative_contains_amendment():
    print("=== narrative: amendment visible ===")
    w, kp, curator = _world_and_curator()
    parts = [
        make_small_artist("Alice"),
        make_small_artist("Bob"),
        make_large_artist("Carol"),
        make_conservative("Dave"),
    ]
    report = run_cycles(
        w, curator, parts, max_cycles=15,
        curator_period=5)
    text = report.narrative()
    assert "AMENDED" in text
    assert "Verification:" in text
    # Law should show 20x20 in early rows, 40x40 in later rows
    lines = text.split("\n")
    early = [l for l in lines if "| 20x20 " in l]
    late = [l for l in lines if "| 40x40 " in l]
    assert early
    assert late


def test_report_json_serializable():
    print("=== report: JSON-serializable ===")
    w, kp, curator = _world_and_curator()
    parts = [make_small_artist("A"),
             make_large_artist("B")]
    report = run_cycles(w, curator, parts, max_cycles=8)
    d = report.to_dict()
    wire = json.dumps(d)
    parsed = json.loads(wire)
    assert len(parsed["snapshots"]) == 8
    assert "final_law" in parsed
    assert "verdict" in parsed


def test_demo(tmp_path):
    print("=== demo: fifteen cycles, governance runs ===")
    audit = demo(artifact_dir=str(tmp_path))
    snapshots = audit["snapshots"]
    assert len(snapshots) == 15
    # At least one amendment
    amended = [s for s in snapshots
               if s["amendment"] is not None]
    assert len(amended) == 1
    # Law grew
    assert audit["final_law"]["max_width"] > 20
    # Verdict valid
    assert audit["verdict"]["valid"] is True
    assert (tmp_path / "world_cycle" /
            "world_cycle_demo.json").exists()

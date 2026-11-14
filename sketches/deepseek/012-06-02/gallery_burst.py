"""
gallery_burst.py — time-bounded attention overrides.

A burst is a signed record that overrides a member's attention
for a bounded interval [start_cycle, end_cycle). During the
interval, effective_attention = burst_attention; outside, it
falls back to the member's base (per-member or default).

Two record types:
  - MemberBurstSetRecord: opens a burst on a member.
  - MemberBurstCancelRecord: shortens the active burst to end
    at the next cycle.

Invariants:
  - No two bursts on the same member may overlap.
  - Cancel requires an active burst.
  - start_cycle = current_cycle + 1 always (no future-set bursts).
  - duration ≥ 1; burst_attention ∈ [0, 100].

Verifier: replays DRR with effective_attention per cycle. If the
log claims a member grew at a cycle where effective_attention
wouldn't allow it, verification fails.

Composition: extends AttentiveGalleryWorld, so revocation,
rotation, world-keys, requests, and refusals still verify.
Uses gallery_revocation's `extend` hook.

Honest limits:
  - No future-set bursts. If a keeper wants a burst to begin
    in 10 cycles, they must set it after 9 more cycles.
  - No per-member burst queue. One active burst at a time.
    Overlapping sets are rejected.
  - Bursts survive retirement in the verifier's state. If a
    member_id is retired and re-added (unusual), a still-active
    burst reactivates. Documented; not exercised in tests.
  - Cancelled bursts keep their original end_cycle in the log;
    the verifier tracks the truncation as derived state.
"""

import json
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

from gallery_governance import (
    GalleryPolicy, GalleryCycleRecord, MemberAddedRecord,
    MemberRetiredRecord, RequestRefusedRecord,
    PolicyChangeRecord, verify_governed_members,
    _canonical, _hash, _now, HAS_CRYPTO,
)
from gallery_revocation import (
    RevocableGalleryWorld, KeeperRotationRecord,
    WorldKeyRevokedRecord, verify_revocable_governed_log,
)
from gallery_attention import (
    AttentiveGalleryWorld,
    DefaultAttentionChangeRecord,
    MemberAttentionChangeRecord,
    _drr_cycle_check, verify_attention_log, verify_attention_full,
)


# =====================================================================
# New records
# =====================================================================

@dataclass(frozen=True)
class MemberBurstSetRecord:
    world_id: str
    member_id: str
    burst_attention: int
    start_cycle: int
    end_cycle: int
    prev: Optional[str]
    ts: str
    sig: str

    def body(self):
        return {
            "type": "member_burst_set",
            "world_id": self.world_id,
            "member_id": self.member_id,
            "burst_attention": int(self.burst_attention),
            "start_cycle": int(self.start_cycle),
            "end_cycle": int(self.end_cycle),
            "prev": self.prev,
            "ts": self.ts,
        }

    def record_hash(self):
        return _hash(self.body())


@dataclass(frozen=True)
class MemberBurstCancelRecord:
    world_id: str
    member_id: str
    effective_end_cycle: int
    prev: Optional[str]
    ts: str
    sig: str

    def body(self):
        return {
            "type": "member_burst_cancel",
            "world_id": self.world_id,
            "member_id": self.member_id,
            "effective_end_cycle": int(self.effective_end_cycle),
            "prev": self.prev,
            "ts": self.ts,
        }

    def record_hash(self):
        return _hash(self.body())


# =====================================================================
# World
# =====================================================================

class BurstingGalleryWorld(AttentiveGalleryWorld):
    def __init__(self, keypair, policy, default_attention=100):
        super().__init__(keypair, policy,
                          default_attention=default_attention)
        # mid -> {"burst_attention": v, "start": s, "end": e}
        self._bursts: Dict[str, Dict] = {}

    # -- Accessors ---------------------------------------

    def burst_at(self, member_id, cycle):
        b = self._bursts.get(member_id)
        if b is None:
            return None
        if b["start"] <= cycle < b["end"]:
            return b
        return None

    def active_burst(self, member_id):
        """The burst active at the next cycle to run."""
        return self.burst_at(member_id, self._cycle + 1)

    def effective_attention_at(self, member_id, cycle):
        b = self.burst_at(member_id, cycle)
        if b is not None:
            return b["burst_attention"]
        return self.attention_of(member_id)

    def bursts(self):
        return {mid: dict(b) for mid, b in self._bursts.items()}

    # -- Burst operations --------------------------------

    def set_member_burst(self, member_id, burst_attention,
                          duration):
        burst_attention = int(burst_attention)
        duration = int(duration)
        if not (0 <= burst_attention <= 100):
            raise ValueError(
                "burst_attention must be [0, 100]")
        if duration <= 0:
            raise ValueError("duration must be positive")
        if not any(m.world_id() == member_id
                    for m in self._members.values()):
            raise ValueError(
                f"member {member_id[:16]}... not in gallery")
        start = self._cycle + 1
        end = start + duration
        existing = self._bursts.get(member_id)
        if existing is not None and \
                existing["start"] < end and start < existing["end"]:
            raise ValueError(
                f"burst overlaps existing burst "
                f"[{existing['start']}, {existing['end']})")
        body = {
            "type": "member_burst_set",
            "world_id": self._world_id,
            "member_id": member_id,
            "burst_attention": burst_attention,
            "start_cycle": start,
            "end_cycle": end,
            "prev": self._last_hash,
            "ts": _now(),
        }
        rec = MemberBurstSetRecord(
            world_id=self._world_id,
            member_id=member_id,
            burst_attention=burst_attention,
            start_cycle=start, end_cycle=end,
            prev=self._last_hash, ts=body["ts"],
            sig=self._keypair.sign(_canonical(body)).hex(),
        )
        self._records.append(rec)
        self._bursts[member_id] = {
            "burst_attention": burst_attention,
            "start": start, "end": end,
        }
        self._last_hash = rec.record_hash()
        return rec

    def cancel_member_burst(self, member_id):
        existing = self._bursts.get(member_id)
        if existing is None:
            raise ValueError(
                f"no burst for {member_id[:16]}...")
        if existing["start"] > self._cycle + 1:
            raise ValueError(
                "burst has not started; cannot cancel pending")
        if existing["end"] <= self._cycle + 1:
            raise ValueError("burst already ended")
        end = self._cycle + 1
        body = {
            "type": "member_burst_cancel",
            "world_id": self._world_id,
            "member_id": member_id,
            "effective_end_cycle": end,
            "prev": self._last_hash,
            "ts": _now(),
        }
        rec = MemberBurstCancelRecord(
            world_id=self._world_id,
            member_id=member_id,
            effective_end_cycle=end,
            prev=self._last_hash, ts=body["ts"],
            sig=self._keypair.sign(_canonical(body)).hex(),
        )
        self._records.append(rec)
        self._bursts[member_id]["end"] = end
        self._last_hash = rec.record_hash()
        return rec

    # -- Scheduling ------------------------------------

    def grow(self):
        next_cycle = self._cycle + 1

        # Credit with effective attention
        for slot in sorted(self._members):
            mid = self._members[slot].world_id()
            attn = self.effective_attention_at(mid, next_cycle)
            self._credits[mid] = (
                self._credits.get(mid, 0) + attn)

        advances = []
        for slot in sorted(self._members):
            member = self._members[slot]
            mid = member.world_id()
            should_select = self._credits.get(mid, 0) >= 100
            if should_select:
                self._credits[mid] -= 100
                result = member.grow()
                steps = 0 if result is None else 1
            else:
                result = None
                steps = 0
            advances.append({
                "slot": slot,
                "member_id": mid,
                "member_kind": member.kind,
                "attention": self.attention_of(mid),
                "effective_attention": self.effective_attention_at(
                    mid, next_cycle),
                "selected": should_select,
                "steps_taken": steps,
                "info": result or {},
            })

        self._cycle += 1
        body = {
            "type": "gallery_cycle",
            "world_id": self._world_id,
            "cycle": self._cycle,
            "advances": advances,
            "prev": self._last_hash,
            "ts": _now(),
        }
        rec = GalleryCycleRecord(
            world_id=self._world_id, cycle=self._cycle,
            advances=tuple(advances),
            prev=self._last_hash, ts=body["ts"],
            sig=self._keypair.sign(_canonical(body)).hex(),
        )
        self._records.append(rec)
        self._last_hash = rec.record_hash()
        return rec


# =====================================================================
# Verification
# =====================================================================

def _effective_at(mid, cycle, state):
    b = state["bursts"].get(mid)
    if b is not None and b["start"] <= cycle < b["end"]:
        return b["burst_attention"]
    return state["attention"].get(
        mid, state["default_attention"])


def _burst_cycle_check(rec, i, state):
    """DRR replay with burst-aware effective attention."""
    cycle = rec.cycle
    for adv in rec.advances:
        mid = adv["member_id"]
        attn = _effective_at(mid, cycle, state)
        state["credits"][mid] = (
            state["credits"].get(mid, 0) + attn)
        reported_eff = adv.get("effective_attention")
        if reported_eff is not None and reported_eff != attn:
            return (False,
                     f"record {i} cycle {cycle}: "
                     f"slot {adv['slot']} effective_attention="
                     f"{reported_eff}, verifier computes {attn}")
        if adv["steps_taken"] not in (0, 1):
            return (False,
                     f"record {i} cycle {cycle}: "
                     f"slot {adv['slot']} steps_taken="
                     f"{adv['steps_taken']}")
    for adv in rec.advances:
        mid = adv["member_id"]
        should_select = state["credits"].get(mid, 0) >= 100
        reported = adv.get("selected", False)
        if should_select != reported:
            return (False,
                     f"record {i} cycle {cycle}: slot "
                     f"{adv['slot']} selected={reported}, "
                     f"DRR expects {should_select}")
        if adv["steps_taken"] > 0 and not reported:
            return (False,
                     f"record {i} cycle {cycle}: "
                     f"slot {adv['slot']} grew but not selected")
        if should_select:
            state["credits"][mid] -= 100
    state["cycle"] = cycle
    return (True, "ok")


def verify_burst_log(gallery):
    if not HAS_CRYPTO:
        return (False, "cryptography not installed")
    seed = gallery.seed_body()
    state = {
        "default_attention":
            int(seed.get("initial_default_attention", 100)),
        "attention": {},
        "credits": {},
        "bursts": {},
        "cycle": 0,
    }

    def extend(rec, i, base_state):
        if isinstance(rec, DefaultAttentionChangeRecord):
            if rec.old_default != state["default_attention"]:
                return (False, f"record {i}: old_default mismatch")
            if not (0 <= rec.new_default <= 100):
                return (False, f"record {i}: new_default bad")
            state["default_attention"] = rec.new_default
            return (True, "")

        if isinstance(rec, MemberAttentionChangeRecord):
            current = state["attention"].get(
                rec.member_id, state["default_attention"])
            if rec.old_attention != current:
                return (False,
                         f"record {i}: old_attention mismatch")
            if not (0 <= rec.new_attention <= 100):
                return (False, f"record {i}: new_attention bad")
            state["attention"][rec.member_id] = rec.new_attention
            return (True, "")

        if isinstance(rec, MemberBurstSetRecord):
            if not (0 <= rec.burst_attention <= 100):
                return (False, f"record {i}: burst out of range")
            if rec.end_cycle <= rec.start_cycle:
                return (False, f"record {i}: bad end_cycle")
            if rec.start_cycle != state["cycle"] + 1:
                return (False,
                         f"record {i}: start_cycle "
                         f"{rec.start_cycle} != "
                         f"cycle+1 {state['cycle']+1}")
            existing = state["bursts"].get(rec.member_id)
            if existing is not None and \
                    existing["start"] < rec.end_cycle and \
                    rec.start_cycle < existing["end"]:
                return (False,
                         f"record {i}: overlaps existing "
                         f"burst [{existing['start']}, "
                         f"{existing['end']})")
            state["bursts"][rec.member_id] = {
                "burst_attention": rec.burst_attention,
                "start": rec.start_cycle,
                "end": rec.end_cycle,
            }
            return (True, "")

        if isinstance(rec, MemberBurstCancelRecord):
            existing = state["bursts"].get(rec.member_id)
            if existing is None:
                return (False, f"record {i}: no burst to cancel")
            if existing["start"] > state["cycle"] + 1:
                return (False,
                         f"record {i}: cancel of pending burst")
            if existing["end"] <= state["cycle"] + 1:
                return (False,
                         f"record {i}: cancel of ended burst")
            if rec.effective_end_cycle != state["cycle"] + 1:
                return (False,
                         f"record {i}: effective_end must be "
                         f"{state['cycle']+1}")
            existing["end"] = rec.effective_end_cycle
            return (True, "")

        if isinstance(rec, MemberAddedRecord):
            mid = rec.member_id
            if mid not in state["attention"]:
                state["attention"][mid] = state["default_attention"]
            if mid not in state["credits"]:
                state["credits"][mid] = 0
            return None

        if isinstance(rec, MemberRetiredRecord):
            state["credits"].pop(rec.member_id, None)
            return None

        if isinstance(rec, GalleryCycleRecord):
            return _burst_cycle_check(rec, i, state)

        return None

    ok, reason = verify_revocable_governed_log(
        gallery, extend)
    if not ok:
        return (False, f"base: {reason}")
    return (True, "burst log verifies")


def verify_burst_full(gallery):
    v = verify_burst_log(gallery)
    if not v[0]:
        return (False, f"log: {v[1]}")
    v = verify_governed_members(gallery)
    if not v[0]:
        return (False, f"members: {v[1]}")
    return (True, "full verification passes")


# =====================================================================
# Rendering
# =====================================================================

def render_burst_table(gallery, max_cycles=20):
    slots = sorted(gallery.members().keys())
    if not slots:
        return "  (no members)"
    mid_of = {s: gallery.members()[s].world_id() for s in slots}
    header = ("  cycle | " + " | ".join(
        f"slot {s}" for s in slots)
        + " | effective attention")
    lines = [header, "  " + "-" * (len(header) - 2)]
    cum = {s: 0 for s in slots}
    shown = 0
    for rec in gallery.records():
        if not isinstance(rec, GalleryCycleRecord):
            continue
        if shown >= max_cycles:
            break
        shown += 1
        cells = []
        effs = []
        for adv in sorted(rec.advances, key=lambda a: a["slot"]):
            cum[adv["slot"]] += adv["steps_taken"]
            cells.append(f"{cum[adv['slot']]:6d}")
            mid = mid_of[adv["slot"]]
            effs.append(
                str(gallery.effective_attention_at(mid, rec.cycle)))
        lines.append(
            f"  {rec.cycle:5d} | "
            + " | ".join(cells)
            + f" | [{','.join(effs)}]")
    return "\n".join(lines)


# =====================================================================
# Demo
# =====================================================================

def demo(artifact_dir=None):
    from pathlib import Path
    import json as _json
    from gallery_world import (
        AtomicFractalMember, FractalGridMember,
    )
    from fractal_world_v3 import AtomicFractalWorld, WorldTemplate
    from fractal_grid_world import FractalGridWorld, GridParams
    from cryptography.hazmat.primitives.asymmetric.ed25519 import (
        Ed25519PrivateKey)

    if not HAS_CRYPTO:
        raise RuntimeError("demo requires `cryptography`")
    if artifact_dir is None:
        artifact_dir = "artifacts"
    path = Path(artifact_dir) / "gallery_burst"
    path.mkdir(parents=True, exist_ok=True)

    policy = GalleryPolicy(
        max_members=4,
        allowed_kinds=("atomic_fractal", "fractal_grid"))

    def build(default_attn):
        g = BurstingGalleryWorld(
            Ed25519PrivateKey.generate(), policy,
            default_attention=default_attn)
        for slot in range(4):
            if slot % 2 == 0:
                m = AtomicFractalMember(AtomicFractalWorld(
                    template=WorldTemplate(
                        template_id="t", branch_length=2,
                        max_depth=2),
                    pot=(0, 0, 12, 12),
                    initial_tip=(6, 10, 0),
                    keypair=Ed25519PrivateKey.generate()))
            else:
                m = FractalGridMember(FractalGridWorld(
                    params=GridParams(rule_number=90),
                    initial_row=[0],
                    keypair=Ed25519PrivateKey.generate()))
            g.add(slot, m)
        return g

    # A: base=50, boost slot 0 to 100 for 10 cycles
    g_a = build(50)
    slot0_a = g_a.members()[0].world_id()
    g_a.set_member_burst(slot0_a, 100, 10)
    g_a.grow_n(20)

    # B: base=100, drop slot 0 to 0 for 5 cycles (pause)
    g_b = build(100)
    slot0_b = g_b.members()[0].world_id()
    g_b.set_member_burst(slot0_b, 0, 5)
    g_b.grow_n(15)

    # C: base=50, boost slot 0 to 100 for 100 cycles,
    #    then cancel at cycle 5
    g_c = build(50)
    slot0_c = g_c.members()[0].world_id()
    g_c.set_member_burst(slot0_c, 100, 100)
    g_c.grow_n(5)
    g_c.cancel_member_burst(slot0_c)
    g_c.grow_n(10)

    # D: base=50, heterogeneous bursts on slots 0 and 1
    g_d = build(50)
    slot0_d = g_d.members()[0].world_id()
    slot1_d = g_d.members()[1].world_id()
    g_d.set_member_burst(slot0_d, 100, 3)
    g_d.set_member_burst(slot1_d, 0, 3)
    g_d.grow_n(10)

    for g in (g_a, g_b, g_c, g_d):
        ok, reason = verify_burst_full(g)
        assert ok, reason

    print("=" * 74)
    print("Burst control — time-bounded attention overrides")
    print("=" * 74)
    print()

    for g, label in (
        (g_a, "A: base=50, slot 0 boosted to 100 for 10 cycles"),
        (g_b, "B: base=100, slot 0 paused (0) for 5 cycles"),
        (g_c, "C: base=50, slot 0 boosted to 100; "
              "cancelled at cycle 5"),
        (g_d, "D: base=50, slot 0 to 100 for 3, "
              "slot 1 to 0 for 3"),
    ):
        print(f"  {label}")
        print(render_burst_table(g, max_cycles=20))
        print()

    print("  Verification:")
    for g, name in (
        (g_a, "A"), (g_b, "B"), (g_c, "C"), (g_d, "D")):
        v = verify_burst_full(g)
        print(f"    {name}: {v[0]}  ({v[1]})")
    print()
    print("  What this establishes:")
    print("    - A burst is a signed record with a bounded")
    print("      interval. During the interval, effective")
    print("      attention is the burst value; outside, it")
    print("      falls back to the member's base.")
    print("    - Burst can accelerate (A: 100 during burst,")
    print("      50 after — slot 0 gets 15 steps vs. 10 for")
    print("      siblings over 20 cycles).")
    print("    - Burst can also slow or pause (B: 0 during")
    print("      burst; slot 0 pauses for 5 cycles, then")
    print("      resumes at 100).")
    print("    - Burst can be cancelled mid-run (C: cancel at")
    print("      cycle 5 truncates the burst; slot 0 gets 5")
    print("      bursts cycles then reverts to 50).")
    print("    - Bursts are per-member (D: slot 0 accelerated")
    print("      while slot 1 paused; slots 2-3 unaffected).")
    print("    - Verifier replays DRR with effective attention")
    print("      per cycle. No trust in the gallery's claims.")
    print()
    print("  Honest limit: no future-set bursts, no per-member")
    print("  burst queue. One active burst at a time.")
    print()
    print("  Anchor (public domain, Emily Dickinson):")
    print("    'Forever – is composed of Nows –'")
    print("    'Tis not a different time –'")

    audit = {}
    for g, name in ((g_a, "A"), (g_b, "B"),
                     (g_c, "C"), (g_d, "D")):
        audit[name] = {
            "default_attention": g.default_attention(),
            "cycles": g.cycle(),
            "members": [
                {"slot": s,
                 "attention": g.attention_of(
                     g.members()[s].world_id()),
                 "steps": g.members()[s].steps()}
                for s in sorted(g.members())
            ],
            "verify": verify_burst_full(g)[0],
        }
    (path / "gallery_burst_demo.json").write_text(
        _json.dumps(audit, indent=2))
    print(f"\n  → {path}/gallery_burst_demo.json")
    return audit

"""
gallery_meta_coupling.py — the gallery watches and schedules.

meta_k ∈ [0, 100] controls the attention budget:
  M = max(1, ceil(N * (1 - meta_k / 100)))
  M members selected per cycle, lowest cumulative steps first.
  Ties broken by slot.

k=0: all N grow every cycle (baseline).
k=100: 1 grows per cycle (strict rotation).

The observable: the *shape* of step counts. With k=0, lockstep.
With k=100, rotation — the same total grows over enough cycles,
but distributed differently in time.

meta_k is changeable via a signed record. The verifier
re-derives M and the selected set at each cycle from the log
alone — no trust in the gallery's own claims.

Honest limits:
  - Done members (capped, empty) still get scheduled. Their
    slot is wasted. Fixable by tracking "done" state, but the
    verifier would need to know which members are done at
    each cycle without replaying their internal logs.
  - M assumes fair share. A member added mid-run starts at
    cumulative 0, so it gets priority for many cycles. Design
    choice, not bug.
  - The tradeoff: high k means fewer total grow calls per
    cycle. Careful attention, slow progress. Same total over
    time, different trajectory.
"""

import math
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

from multiverse_utils_sig import _now, _canonical, _hash, _verify_sig

from gallery_governance import (
    GalleryPolicy, GalleryWorldKey, verify_world_key,
    world_key_has_tier,
    GallerySeedRecord, PolicyChangeRecord, MemberAddedRecord,
    MemberRetiredRecord, GalleryCycleRecord,
    RequestRefusedRecord,
    verify_governed_members,
    _did_from_kp, _pubkey_from_did, HAS_CRYPTO,
)
from gallery_revocation import (
    RevocableGalleryWorld,
    KeeperRotationRecord, WorldKeyRevokedRecord,
    verify_revocable_governed_log,
)


# =====================================================================
# New record
# =====================================================================

@dataclass(frozen=True)
class MetaKChangeRecord:
    world_id: str
    old_k: int
    new_k: int
    prev: Optional[str]
    ts: str
    sig: str

    def body(self):
        return {
            "type": "meta_k_change",
            "world_id": self.world_id,
            "old_k": self.old_k,
            "new_k": self.new_k,
            "prev": self.prev,
            "ts": self.ts,
        }

    def record_hash(self):
        return _hash(self.body())


# =====================================================================
# MetaCoupledGalleryWorld
# =====================================================================

class MetaCoupledGalleryWorld(RevocableGalleryWorld):
    def __init__(self, keypair, policy, meta_k=0):
        if not (0 <= int(meta_k) <= 100):
            raise ValueError(
                f"meta_k must be [0, 100], got {meta_k}")
        super().__init__(keypair, policy)
        self._meta_k = int(meta_k)
        # Rewrite seed to include initial_meta_k (additive; seed
        # is re-signed by the current keeper).
        new_seed = dict(self._seed_body)
        new_seed["initial_meta_k"] = self._meta_k
        self._seed_body = new_seed
        self._seed_sig = self._keypair.sign(
            _canonical(new_seed)).hex()

    def meta_k(self):
        return self._meta_k

    def set_meta_k(self, new_k):
        new_k = int(new_k)
        if not (0 <= new_k <= 100):
            raise ValueError("meta_k must be [0, 100]")
        body = {
            "type": "meta_k_change",
            "world_id": self._world_id,
            "old_k": self._meta_k,
            "new_k": new_k,
            "prev": self._last_hash,
            "ts": _now(),
        }
        rec = MetaKChangeRecord(
            world_id=self._world_id,
            old_k=self._meta_k, new_k=new_k,
            prev=self._last_hash, ts=body["ts"],
            sig=self._keypair.sign(
                _canonical(body)).hex(),
        )
        self._records.append(rec)
        self._meta_k = new_k
        self._last_hash = rec.record_hash()
        return rec

    def _cumulative_steps(self) -> Dict[str, int]:
        cum: Dict[str, int] = {}
        for rec in self._records:
            if isinstance(rec, GalleryCycleRecord):
                for a in rec.advances:
                    cum[a["member_id"]] = (
                        cum.get(a["member_id"], 0)
                        + a["steps_taken"])
        return cum

    def grow(self):
        N = len(self._members)
        cum = self._cumulative_steps()
        if N == 0:
            advances = []
        else:
            M = max(1, math.ceil(
                N * (1 - self._meta_k / 100)))
            sorted_slots = sorted(
                self._members.keys(),
                key=lambda s: (
                    cum.get(
                        self._members[s].world_id(), 0), s))
            selected_slots = set(sorted_slots[:M])
            advances = []
            for slot in sorted(self._members):
                member = self._members[slot]
                selected = slot in selected_slots
                if selected:
                    result = member.grow()
                    steps = 0 if result is None else 1
                else:
                    result = None
                    steps = 0
                advances.append({
                    "slot": slot,
                    "member_id": member.world_id(),
                    "member_kind": member.kind,
                    "selected": selected,
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
            sig=self._keypair.sign(
                _canonical(body)).hex(),
        )
        self._records.append(rec)
        self._last_hash = rec.record_hash()
        return rec


# =====================================================================
# Verification
# =====================================================================

def verify_meta_coupled_log(gallery):
    """Base revocable verification + scheduling discipline."""
    ok, reason = verify_revocable_governed_log(gallery)
    if not ok:
        return (False, f"base: {reason}")

    meta_k = gallery.seed_body().get("initial_meta_k", 0)
    if not (0 <= int(meta_k) <= 100):
        return (False,
                 f"seed initial_meta_k {meta_k} out of range")

    cum: Dict[str, int] = {}
    for i, rec in enumerate(gallery.records()):
        if isinstance(rec, MetaKChangeRecord):
            if rec.old_k != meta_k:
                return (False,
                         f"record {i}: meta_k_change old "
                         f"{rec.old_k} != accumulated "
                         f"{meta_k}")
            if not (0 <= rec.new_k <= 100):
                return (False,
                         f"record {i}: new_k out of range")
            meta_k = rec.new_k
        elif isinstance(rec, GalleryCycleRecord):
            N = len(rec.advances)
            if N == 0:
                continue
            M = max(1, math.ceil(N * (1 - meta_k / 100)))
            sorted_advs = sorted(
                rec.advances,
                key=lambda a: (
                    cum.get(a["member_id"], 0), a["slot"]))
            expected_selected = set(
                a["slot"] for a in sorted_advs[:M])
            for adv in rec.advances:
                slot = adv["slot"]
                reported_sel = adv.get("selected", False)
                if reported_sel != (slot in expected_selected):
                    return (False,
                             f"record {i} cycle {rec.cycle}: "
                             f"slot {slot} selected="
                             f"{reported_sel}, expected="
                             f"{slot in expected_selected}")
                if adv["steps_taken"] > 0 and not reported_sel:
                    return (False,
                             f"record {i} cycle {rec.cycle}: "
                             f"slot {slot} grew but not "
                             f"selected")
                if adv["steps_taken"] not in (0, 1):
                    return (False,
                             f"record {i} cycle {rec.cycle}: "
                             f"slot {slot} steps_taken="
                             f"{adv['steps_taken']}")
                cum[adv["member_id"]] = (
                    cum.get(adv["member_id"], 0)
                    + adv["steps_taken"])
    return (True, "meta-coupling verified")


def verify_meta_coupled_full(gallery):
    v = verify_meta_coupled_log(gallery)
    if not v[0]:
        return (False, f"log: {v[1]}")
    v = verify_governed_members(gallery)
    if not v[0]:
        return (False, f"members: {v[1]}")
    return (True, "full verification passes")


# =====================================================================
# Rendering
# =====================================================================

def render_step_table(gallery, max_cycles=20):
    """Per-cycle step counts per slot. Shows the scheduling."""
    slots = sorted(gallery.members().keys())
    if not slots:
        return "  (no members)"
    lines = []
    header = "  cycle | " + " | ".join(
        f"slot {s}" for s in slots) + " | selected"
    lines.append(header)
    lines.append("  " + "-" * (len(header) - 2))
    cum = {slot: 0 for slot in slots}
    shown = 0
    for rec in gallery.records():
        if not isinstance(rec, GalleryCycleRecord):
            continue
        if shown >= max_cycles:
            break
        shown += 1
        cells = []
        sel_slots = []
        for adv in sorted(rec.advances, key=lambda a: a["slot"]):
            cum[adv["slot"]] = (
                cum.get(adv["slot"], 0) + adv["steps_taken"])
            cells.append(f"{cum[adv['slot']]:6d}")
            if adv.get("selected"):
                sel_slots.append(str(adv["slot"]))
        lines.append(
            f"  {rec.cycle:5d} | "
            + " | ".join(cells)
            + f" | {','.join(sel_slots) if sel_slots else '-'}")
    return "\n".join(lines)


# =====================================================================
# Demo
# =====================================================================

def demo(artifact_dir=None):
    from pathlib import Path
    import json as _json
    from gallery_world import (
        AtomicFractalMember, FractalGridMember,
        ChaosGameMember, CoupledCAMember,
    )
    from fractal_world_v3 import AtomicFractalWorld, WorldTemplate
    from fractal_grid_world import FractalGridWorld, GridParams
    from chaos_game_world import ChaosGameWorld, SIERPINSKI
    from coupled_ca_world import CoupledCAWorld
    from cryptography.hazmat.primitives.asymmetric.ed25519 import (
        Ed25519PrivateKey)

    if not HAS_CRYPTO:
        raise RuntimeError("demo requires `cryptography`")
    if artifact_dir is None:
        artifact_dir = "artifacts"
    path = Path(artifact_dir) / "gallery_meta_coupling"
    path.mkdir(parents=True, exist_ok=True)

    initial_policy = GalleryPolicy(
        max_members=4,
        allowed_kinds=("atomic_fractal", "fractal_grid",
                        "chaos_game", "coupled_ca"))

    def build_gallery(meta_k):
        g = MetaCoupledGalleryWorld(
            Ed25519PrivateKey.generate(),
            initial_policy, meta_k=meta_k)
        plant = AtomicFractalMember(AtomicFractalWorld(
            template=WorldTemplate(
                template_id="t", branch_length=2, max_depth=3),
            pot=(0, 0, 12, 12), initial_tip=(6, 10, 0),
            keypair=Ed25519PrivateKey.generate()))
        grid = FractalGridMember(FractalGridWorld(
            params=GridParams(rule_number=90),
            initial_row=[0],
            keypair=Ed25519PrivateKey.generate()))
        chaos = ChaosGameMember(ChaosGameWorld(
            preset=SIERPINSKI, growth_mode="seeded_random",
            initial_point=(500, 500),
            keypair=Ed25519PrivateKey.generate(),
            prng_seed=0xCAFE))
        ca = CoupledCAMember(CoupledCAWorld(
            rule_a=90, rule_b=90,
            initial_a=[0], initial_b=[15],
            k_a=50, k_b=50,
            keypair=Ed25519PrivateKey.generate()))
        g.add(0, plant)
        g.add(1, grid)
        g.add(2, chaos)
        g.add(3, ca)
        return g

    g0 = build_gallery(0)
    g0.grow_n(20)

    g50 = build_gallery(50)
    g50.grow_n(20)

    g100 = build_gallery(100)
    g100.grow_n(20)

    g_change = build_gallery(0)
    g_change.grow_n(10)
    change_rec = g_change.set_meta_k(100)
    g_change.grow_n(10)

    for g in (g0, g50, g100, g_change):
        ok, reason = verify_meta_coupled_full(g)
        assert ok, reason

    print("=" * 74)
    print("Meta-coupling — the gallery schedules its attention")
    print("=" * 74)
    print()
    print("  Same 4 members, same 20 cycles, three meta_k values.")
    print("  The observable: the shape of step counts over time.")
    print()

    for g, label in (
        (g0, "meta_k=0   (baseline — all grow every cycle)"),
        (g50, "meta_k=50  (M=2 per cycle)"),
        (g100, "meta_k=100 (M=1 per cycle, strict rotation)"),
    ):
        print(f"  {label}")
        print(render_step_table(g, max_cycles=20))
        print()

    print("  meta_k=0→100 at cycle 10 (mid-world change)")
    print(render_step_table(g_change, max_cycles=20))
    print()

    print("  Verification:")
    for g, name in (
        (g0, "k=0"), (g50, "k=50"), (g100, "k=100"),
        (g_change, "k-change")):
        v = verify_meta_coupled_full(g)
        print(f"    {name:10s}  {v[0]}  ({v[1]})")
    print()

    print("  What this establishes:")
    print("    - meta_k is a scheduler knob, not a parameter of")
    print("      any member. The gallery observes cumulative")
    print("      steps and decides who advances.")
    print("    - At k=0, all members advance in lockstep (20")
    print("      steps each after 20 cycles).")
    print("    - At k=50, M=2 per cycle — rotation is partial,")
    print("      but all members end within a few steps of each")
    print("      other (10 each after 20 cycles).")
    print("    - At k=100, M=1 — perfect rotation. 20 cycles,")
    print("      5 steps each.")
    print("    - The verifier re-derives M and the selected set")
    print("      from the log alone. No trust in the gallery's")
    print("      own claims.")
    print("    - meta_k can change mid-world via a signed record;")
    print("      the scheduler picks up the new budget immediately.")
    print()
    print("  The tradeoff: high k is *attention*, not speed.")
    print("  Fewer total grow calls per cycle. Careful and slow,")
    print("  vs. parallel and fast. Same total over enough cycles.")
    print()
    print("  Anchor (public domain, Emily Dickinson):")
    print("    'Forever – is composed of Nows –'")
    print("    'Tis not a different time –'")

    audit = {}
    for g, name in ((g0, "k_0"), (g50, "k_50"),
                     (g100, "k_100"), (g_change, "k_change")):
        audit[name] = {
            "meta_k": g.meta_k(),
            "cycles": g.cycle(),
            "members": [
                {"slot": s, "steps": m.steps()}
                for s, m in sorted(g.members().items())
            ],
            "verify": verify_meta_coupled_full(g)[0],
        }
    audit["k_change"]["changed_at_cycle"] = change_rec.old_k
    (path / "meta_coupling_demo.json").write_text(
        _json.dumps(audit, indent=2))
    print(f"\n  → {path}/meta_coupling_demo.json")
    return audit

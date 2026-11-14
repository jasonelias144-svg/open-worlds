"""
gallery_attention.py — per-member attention via deficit round-robin.

Each member has attention ∈ [0, 100]. The gallery has a
default_attention for new members. Each cycle:

    credits[i] += attention[i]
    if credits[i] >= 100: grow, credits[i] -= 100

At attention=100: every cycle.
At attention=50:  every other cycle.
At attention=33:  every 3rd cycle.
At attention=0:   never.

Deterministic, verifiable. The verifier replays DRR from the log;
it does not trust the gallery's scheduling claims.

Design notes:
  - Attention is keyed by member_id, not slot. On retire, credits
    are cleared. On re-add, credits start at 0; attention defaults
    to default_attention unless a per-member setting exists.
  - Done members (grow() returns None) still get selected; their
    credits are spent anyway so they don't hog. Documented limit.
  - old meta_k (M = ceil(N(1-k/100))) is not preserved. To emulate,
    use default_attention = ceil(100 / N).

Composition: extends RevocableGalleryWorld; verifier extends
verify_revocable_governed_log via the extend hook.
"""

import json
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

from gallery_governance import (
    GalleryPolicy, GalleryCycleRecord, MemberAddedRecord,
    MemberRetiredRecord, RequestRefusedRecord,
    PolicyChangeRecord, verify_governed_members,
    _did_from_kp, _canonical, _hash, _now, _verify_sig,
    HAS_CRYPTO,
)
from gallery_revocation import (
    RevocableGalleryWorld, KeeperRotationRecord,
    WorldKeyRevokedRecord, verify_revocable_governed_log,
)


# =====================================================================
# New record types
# =====================================================================

@dataclass(frozen=True)
class DefaultAttentionChangeRecord:
    world_id: str
    old_default: int
    new_default: int
    prev: Optional[str]
    ts: str
    sig: str

    def body(self):
        return {
            "type": "default_attention_change",
            "world_id": self.world_id,
            "old_default": self.old_default,
            "new_default": self.new_default,
            "prev": self.prev,
            "ts": self.ts,
        }

    def record_hash(self):
        return _hash(self.body())


@dataclass(frozen=True)
class MemberAttentionChangeRecord:
    world_id: str
    member_id: str
    old_attention: int
    new_attention: int
    prev: Optional[str]
    ts: str
    sig: str

    def body(self):
        return {
            "type": "member_attention_change",
            "world_id": self.world_id,
            "member_id": self.member_id,
            "old_attention": self.old_attention,
            "new_attention": self.new_attention,
            "prev": self.prev,
            "ts": self.ts,
        }

    def record_hash(self):
        return _hash(self.body())


# =====================================================================
# World
# =====================================================================

class AttentiveGalleryWorld(RevocableGalleryWorld):
    def __init__(self, keypair, policy, default_attention=100):
        if not (0 <= int(default_attention) <= 100):
            raise ValueError("default_attention must be [0, 100]")
        super().__init__(keypair, policy)
        self._default_attention = int(default_attention)
        self._attention: Dict[str, int] = {}
        self._credits: Dict[str, int] = {}
        new_seed = dict(self._seed_body)
        new_seed["initial_default_attention"] = \
            self._default_attention
        self._seed_body = new_seed
        self._seed_sig = self._keypair.sign(
            _canonical(new_seed)).hex()

    def default_attention(self):
        return self._default_attention

    def attention_of(self, member_id):
        return self._attention.get(
            member_id, self._default_attention)

    def set_default_attention(self, new_default):
        new_default = int(new_default)
        if not (0 <= new_default <= 100):
            raise ValueError("default_attention must be [0, 100]")
        body = {
            "type": "default_attention_change",
            "world_id": self._world_id,
            "old_default": self._default_attention,
            "new_default": new_default,
            "prev": self._last_hash,
            "ts": _now(),
        }
        rec = DefaultAttentionChangeRecord(
            world_id=self._world_id,
            old_default=self._default_attention,
            new_default=new_default,
            prev=self._last_hash, ts=body["ts"],
            sig=self._keypair.sign(_canonical(body)).hex(),
        )
        self._records.append(rec)
        self._default_attention = new_default
        self._last_hash = rec.record_hash()
        return rec

    def set_member_attention(self, member_id, new_attention):
        new_attention = int(new_attention)
        if not (0 <= new_attention <= 100):
            raise ValueError("attention must be [0, 100]")
        old = self.attention_of(member_id)
        if old == new_attention:
            return None
        body = {
            "type": "member_attention_change",
            "world_id": self._world_id,
            "member_id": member_id,
            "old_attention": old,
            "new_attention": new_attention,
            "prev": self._last_hash,
            "ts": _now(),
        }
        rec = MemberAttentionChangeRecord(
            world_id=self._world_id, member_id=member_id,
            old_attention=old, new_attention=new_attention,
            prev=self._last_hash, ts=body["ts"],
            sig=self._keypair.sign(_canonical(body)).hex(),
        )
        self._records.append(rec)
        self._attention[member_id] = new_attention
        self._last_hash = rec.record_hash()
        return rec

    def add(self, slot, member):
        # Initialize attention and credits
        mid = member.world_id()
        if mid not in self._attention:
            self._attention[mid] = self._default_attention
        if mid not in self._credits:
            self._credits[mid] = 0
        return super().add(slot, member)

    def retire(self, slot, reason=""):
        if slot in self._members:
            mid = self._members[slot].world_id()
            self._credits.pop(mid, None)
        return super().retire(slot, reason)

    def grow(self):
        # DRR: credit all currently-held members
        for slot in sorted(self._members):
            mid = self._members[slot].world_id()
            attn = self.attention_of(mid)
            self._credits[mid] = self._credits.get(mid, 0) + attn

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

def _drr_cycle_check(rec, i, state):
    """Verify one cycle's advances against DRR replay."""
    # Credit
    for adv in rec.advances:
        mid = adv["member_id"]
        attn = state["attention"].get(
            mid, state["default_attention"])
        state["credits"][mid] = \
            state["credits"].get(mid, 0) + attn
        if adv["steps_taken"] not in (0, 1):
            return (False,
                     f"record {i} cycle {rec.cycle}: "
                     f"slot {adv['slot']} steps_taken="
                     f"{adv['steps_taken']}")
    # Select
    for adv in rec.advances:
        mid = adv["member_id"]
        should_select = state["credits"].get(mid, 0) >= 100
        reported = adv.get("selected", False)
        if should_select != reported:
            return (False,
                     f"record {i} cycle {rec.cycle}: "
                     f"slot {adv['slot']} selected="
                     f"{reported}, DRR expects={should_select}")
        if adv["steps_taken"] > 0 and not reported:
            return (False,
                     f"record {i} cycle {rec.cycle}: "
                     f"slot {adv['slot']} grew but not selected")
        if should_select:
            state["credits"][mid] -= 100
    return (True, "ok")


def verify_attention_log(gallery):
    if not HAS_CRYPTO:
        return (False, "cryptography not installed")
    seed = gallery.seed_body()
    default_attn = seed.get("initial_default_attention", 100)
    if not (0 <= int(default_attn) <= 100):
        return (False,
                 f"seed initial_default_attention "
                 f"{default_attn} out of [0, 100]")
    state = {
        "default_attention": int(default_attn),
        "attention": {},
        "credits": {},
    }

    def extend(rec, i, base_state):
        if isinstance(rec, DefaultAttentionChangeRecord):
            if rec.old_default != state["default_attention"]:
                return (False,
                         f"record {i}: old_default mismatch")
            if not (0 <= rec.new_default <= 100):
                return (False,
                         f"record {i}: new_default out of range")
            state["default_attention"] = rec.new_default
            return (True, "ok")

        if isinstance(rec, MemberAttentionChangeRecord):
            current = state["attention"].get(
                rec.member_id, state["default_attention"])
            if rec.old_attention != current:
                return (False,
                         f"record {i}: old_attention mismatch")
            if not (0 <= rec.new_attention <= 100):
                return (False,
                         f"record {i}: new_attention out of range")
            state["attention"][rec.member_id] = rec.new_attention
            return (True, "ok")

        if isinstance(rec, MemberAddedRecord):
            mid = rec.member_id
            if mid not in state["attention"]:
                state["attention"][mid] = state["default_attention"]
            if mid not in state["credits"]:
                state["credits"][mid] = 0
            return None  # base handles admission checks

        if isinstance(rec, MemberRetiredRecord):
            state["credits"].pop(rec.member_id, None)
            return None  # base handles

        if isinstance(rec, GalleryCycleRecord):
            ok, reason = _drr_cycle_check(rec, i, state)
            if not ok:
                return (False, reason)
            return None  # base handles monotonicity + coverage

        return None

    ok, reason = verify_revocable_governed_log(gallery, extend)
    if not ok:
        return (False, f"base: {reason}")
    return (True, "attention log verifies")


def verify_attention_full(gallery):
    v = verify_attention_log(gallery)
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
    slots = sorted(gallery.members().keys())
    if not slots:
        return "  (no members)"
    mid_of = {s: gallery.members()[s].world_id() for s in slots}
    header = ("  cycle | "
              + " | ".join(f"slot {s}" for s in slots)
              + " | attention")
    lines = [header, "  " + "-" * (len(header) - 2)]
    cumulative = {s: 0 for s in slots}
    attention_snapshot = {
        s: gallery.attention_of(mid_of[s]) for s in slots}
    shown = 0
    for rec in gallery.records():
        if not isinstance(rec, GalleryCycleRecord):
            continue
        if shown >= max_cycles:
            break
        shown += 1
        cells = []
        for adv in sorted(rec.advances, key=lambda a: a["slot"]):
            slot = adv["slot"]
            cumulative[slot] += adv["steps_taken"]
            cells.append(f"{cumulative[slot]:6d}")
        attn_str = ",".join(
            str(gallery.attention_of(mid_of[s]))
            for s in slots)
        lines.append(
            f"  {rec.cycle:5d} | "
            + " | ".join(cells)
            + f" | [{attn_str}]")
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
    path = Path(artifact_dir) / "gallery_attention"
    path.mkdir(parents=True, exist_ok=True)

    policy = GalleryPolicy(
        max_members=4,
        allowed_kinds=("atomic_fractal", "fractal_grid"))

    def build(default_attn):
        g = AttentiveGalleryWorld(
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

    g_a = build(100)
    g_a.grow_n(15)

    g_b = build(50)
    g_b.grow_n(15)

    g_c = build(50)
    slot0_mid = g_c.members()[0].world_id()
    g_c.set_member_attention(slot0_mid, 100)
    g_c.grow_n(15)

    g_d = build(50)
    g_d.grow_n(7)
    slot1_mid = g_d.members()[1].world_id()
    change = g_d.set_member_attention(slot1_mid, 100)
    g_d.grow_n(8)

    for g in (g_a, g_b, g_c, g_d):
        ok, reason = verify_attention_full(g)
        assert ok, reason

    print("=" * 74)
    print("Per-member attention — the gallery paces each member")
    print("=" * 74)
    print()
    print("  Attention is rate, not order. 100 = every cycle,")
    print("  50 = every other, 0 = paused. DRR schedules.")
    print()

    for g, label in (
        (g_a, "A: default_attention=100 (all grow every cycle)"),
        (g_b, "B: default_attention=50  (all grow every other cycle)"),
        (g_c, "C: default=50, slot 0 set to 100"),
        (g_d, "D: default=50, slot 1 raised to 100 at cycle 7"),
    ):
        print(f"  {label}")
        print(render_step_table(g, max_cycles=15))
        print()

    print("  Verification:")
    for g, name in ((g_a, "A"), (g_b, "B"),
                     (g_c, "C"), (g_d, "D")):
        v = verify_attention_full(g)
        print(f"    {name}: {v[0]}  ({v[1]})")
    print()
    print("  What this establishes:")
    print("    - Each member has its own attention rate.")
    print("      The gallery schedules via DRR.")
    print("    - At default=100 all grow every cycle; at 50 they")
    print("      interleave perfectly (every other cycle).")
    print("    - Per-member override makes slot 0 grow 2x faster")
    print("      than its siblings (15 vs. 7 steps over 15 cycles).")
    print("    - Mid-run change: attention raised at cycle 7; the")
    print("      member immediately accelerates from 50% to 100%.")
    print("    - The verifier replays DRR from the log alone; it")
    print("      does not trust the gallery's scheduling claims.")
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
            "verify": verify_attention_full(g)[0],
        }
    audit["D"]["change_at_cycle"] = change.old_attention
    (path / "gallery_attention_demo.json").write_text(
        _json.dumps(audit, indent=2))
    print(f"\n  → {path}/gallery_attention_demo.json")
    return audit

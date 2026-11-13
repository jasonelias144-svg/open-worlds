"""
multiverse_c33.py — Component 33: leave for Chemistry and Registry.

C22 added leave() to PoetryWorld only. C33 extracts a reusable
LeaveCapableMixin and applies it to ChemistryWorld and
MultiverseRegistry.

The design question C22 raised: what does "leaving a registry"
mean? Answer: the identity is no longer a petitioner. Listings
the petitioner proposed remain listed — they belong to the
registry, not the petitioner. A registry is a directory, not a
residence. Leaving does not edit the record.

House rules honored:
  - "A world never raises on what a visitor sends" — leaving
    for a world never entered returns Refusal. Tested.
  - "Protected freedoms have tests" — leaving is tested against
    every refusal-worthy condition, for each world type.
  - "Every behaviour has a test that fails if the behaviour
    breaks" — one test per: leave without admission, act after
    leave, re-enter after leave, listings survive registry leave,
    signed departure verifies.

Honest limits (documented, tested):
  - C22's LeaveCapableWorld stays as-is for backward compat.
    C33 provides LeaveCapablePoetryWorld (mixin-based) — same
    behavior, cleaner shape. A future refactor could retire C22's
    version; C33 doesn't need to.
  - Mixin assumes the base's __init__ does not call
    super().__init__() with args. All three bases (PoetryWorld,
    ChemistryWorld, MultiverseRegistry) satisfy this; the mixin's
    __init__ delegates then initializes _left_at.
  - A petitioner who leaves the registry and re-petitions gets a
    new admission (new timestamp). Their prior listings remain.
    Their prior departures remain in the passport. Leaving is
    not an undo — it's a visit that ended.
"""

from datetime import datetime, timezone
from typing import Dict, List, Optional, Union

from multiverse_c3 import (
    Petition, Act, LogEntry,
    Admission as WCPAdmission, Refusal, Ack,
)
from multiverse_c4 import PoetryWorld
from multiverse_c5 import ChemistryWorld
from multiverse_c6 import MultiverseRegistry
from multiverse_c22 import (
    LeavePetition, Leave, LeaveResponse,
    SignedLeave, SignedLeaveWorld,
    PassportV2WithDepartures, verify_departure,
)


# =====================================================================
# LeaveCapableMixin — the reusable core
# =====================================================================

class LeaveCapableMixin:
    """Mixin adding leave() to any WCP world.

    Preconditions (satisfied by PoetryWorld, ChemistryWorld,
    MultiverseRegistry):
      - self._admitted: Dict[str, WCPAdmission]
      - self._log: List[LogEntry]
      - self._manifest.entity_id: str
      - self.__init__ does not pass args to super().__init__()
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._left_at: Dict[str, str] = {}

    def leave(self, petition: LeavePetition) -> LeaveResponse:
        token = petition.leaver_token
        ts = datetime.now(timezone.utc).isoformat()

        if token in self._admitted:
            del self._admitted[token]
            self._left_at[token] = ts
            self._log.append(LogEntry(
                timestamp=ts, kind="leave",
                actor_token=token, data={},
            ))
            return Leave(entity_id=self._manifest.entity_id,
                         timestamp=ts)

        if token in self._left_at:
            return Leave(entity_id=self._manifest.entity_id,
                         timestamp=self._left_at[token])

        # Never was here — Refusal, not exception
        self._log.append(LogEntry(
            timestamp=ts, kind="leave_refused",
            actor_token=token, data={"reason": "not admitted"},
        ))
        return Refusal(reason="not admitted")

    def is_resident(self, token: str) -> bool:
        return token in self._admitted


# =====================================================================
# Concrete leave-capable worlds
# =====================================================================

class LeaveCapablePoetryWorld(LeaveCapableMixin, PoetryWorld):
    """Mixin-based Poetry World.

    Functionally identical to C22's LeaveCapableWorld; provided
    for API symmetry. C22's class remains valid and tested.
    """
    pass


class LeaveCapableChemistryWorld(LeaveCapableMixin, ChemistryWorld):
    """A Chemistry World that supports leave."""
    pass


class LeaveCapableRegistry(LeaveCapableMixin, MultiverseRegistry):
    """A Multiverse Registry that supports leave.

    Semantics (C33's design answer): leaving the registry means
    the identity is no longer a petitioner. Listings the
    petitioner proposed remain listed — they belong to the
    registry, not the petitioner.

    A registry is a directory, not a residence. Once it verifies
    a world and records the listing, that listing is part of the
    registry's history. A petitioner leaving does not edit the
    registry's record.

    This is the "history, not rank" principle in the one place
    where a naive implementation would cascade: leaving removes
    the leaver's ability to act, but does not remove what the
    leaver did.
    """
    pass


# =====================================================================
# Demo: three worlds, all left, all verified
# =====================================================================

def demo(artifact_dir: Optional[str] = None) -> Dict:
    """Alice visits Poetry, Chemistry, and the Registry. She
    proposes a world to the registry. Then she leaves all three.
    Her passport has three admissions and three departures, all
    signed and verified. The listings she proposed to the
    registry remain.

    Anchor: Emily Dickinson, 'I dwell in Possibility –',
    public domain.
    """
    import json
    import time
    from pathlib import Path
    from multiverse_c1 import create_identity
    from multiverse_c13 import KeyPair
    from multiverse_c14 import PermissiveWorld
    from wcp_http_shim import WorldProtocolServer

    # Set up three leave-capable worlds, each wrapped for signed leave
    kp_poetry = KeyPair.generate()
    kp_chem = KeyPair.generate()
    kp_reg = KeyPair.generate()
    kp_world_x = KeyPair.generate()

    poetry = SignedLeaveWorld(
        LeaveCapablePoetryWorld("world:poetry", "Poetry World"),
        kp_poetry)
    chemistry = SignedLeaveWorld(
        LeaveCapableChemistryWorld("world:chemistry", "Chemistry World"),
        kp_chem)
    registry = SignedLeaveWorld(
        LeaveCapableRegistry("multiverse:main", "Main Multiverse"),
        kp_reg)

    # Alice petitions all three
    alice = create_identity("Alice")
    passport = PassportV2WithDepartures(
        __import__("multiverse_c15", fromlist=["PassportV2"])
        .PassportV2.new(alice))

    from multiverse_c3 import Petition
    for world in (poetry, chemistry, registry):
        adm = world.petition(Petition(
            petitioner_token=alice.token,
            petitioner_name=alice.name,
            passport_admissions=(),
            message="I dwell in Possibility —",
        ))
        passport = passport.with_admission(adm)

    # Alice proposes a world to the registry (as admin)
    from multiverse_c3 import Act
    world_x = PermissiveWorld("world:x", "World X")
    registry.act(Act(
        actor_token=alice.token,
        type="multiverse.admit",
        payload={"entity": world_x},
    ))
    # Confirm the listing
    assert "world:x" in registry.base.entity_ids()

    # Alice leaves all three
    for world in (poetry, chemistry, registry):
        leave = world.leave(LeavePetition(leaver_token=alice.token))
        passport = passport.with_departure(leave)

    # Verify all three departures
    keys = {
        "world:poetry": kp_poetry.public_key_hex(),
        "world:chemistry": kp_chem.public_key_hex(),
        "multiverse:main": kp_reg.public_key_hex(),
    }
    results = {}
    for entity_id, pk in keys.items():
        dep = passport.departure_for(entity_id)
        results[entity_id] = {
            "departure_present": dep is not None,
            "signature_valid": verify_departure(
                dep, alice.token, pk) if dep else False,
        }

    # The listing Alice proposed to the registry is STILL there
    listing_survives = "world:x" in registry.base.entity_ids()

    print("=" * 70)
    print("leave for Chemistry and Registry — demo")
    print("=" * 70)
    print()
    print(f"  Passport admissions: {len(passport.entries)}")
    print(f"  Passport departures: {len(passport.departures)}")
    print()
    print("  Per-world departure verification:")
    for entity_id, r in results.items():
        marker = "✓" if r["signature_valid"] else "✗"
        print(f"    {marker} {entity_id:20s} "
              f"departure present: {r['departure_present']}, "
              f"signature: {r['signature_valid']}")
    print()
    print(f"  Listing survives Alice's leave: {listing_survives}")
    print(f"  (Alice proposed world:x; her leave does not")
    print(f"   remove it — the listing belongs to the registry)")
    print()
    print("  Anchor (public domain, Emily Dickinson):")
    print("    'I dwell in Possibility –'")
    print("    'A fairer House than Prose –'")

    audit = {
        "passport_admissions": len(passport.entries),
        "passport_departures": len(passport.departures),
        "departures": results,
        "listing_survives": listing_survives,
    }
    if artifact_dir:
        path = Path(artifact_dir)
        path.mkdir(parents=True, exist_ok=True)
        (path / "leave_demo.json").write_text(
            json.dumps(audit, indent=2))
        print(f"\n  → {path}/leave_demo.json")
    return audit

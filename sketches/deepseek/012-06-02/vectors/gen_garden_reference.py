"""
vectors/gen_garden_reference.py — generate the garden test vector.

Runs a fixed scenario through the Python reference (`ur_garden.py`)
and writes the resulting hashes to `vectors/garden_reference.json`.

Any Rust (or other-language) implementation of the garden is
correct iff it produces the same hashes for the same scenario.
That's the contract: the hashes are the observable, the scenario
is the input, and neither side of the port can cheat without the
other noticing.

Usage:
    python vectors/gen_garden_reference.py
"""

import json
import sys
from pathlib import Path

# Path setup — run from repo root
sys.path.insert(0, str(Path(__file__).parent.parent))

from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey,
)
from multiverse_c3 import Manifest, Petition, Act
from ur_garden import GardenWorld, Cell
from microverse import ChaosGameHost, ElementaryCAHost
from chaos_game_world import ChaosGameWorld, BARNSLEY
from elementary_ca_world import ElementaryCAWorld, rule_30
from individual_bundle import _did_from_kp


def _kp_from_seed(seed_hex: str):
    """Construct an ed25519 keypair from a 32-byte seed.
    Deterministic; identical in any language with a
    seed → private-key constructor."""
    return Ed25519PrivateKey.from_private_bytes(
        bytes.fromhex(seed_hex))


def build_scenario(scenario: dict):
    """Apply the scenario's actions to a fresh garden.
    Returns the garden and a name → DID map."""
    garden_cfg = scenario["garden"]
    curator_kp = _kp_from_seed(garden_cfg["curator_seed_hex"])
    garden = GardenWorld(
        garden_cfg["entity_id"],
        "Reference Garden",
        curator_kp,
        description="fixed test vector",
    )
    garden.WIDTH = garden_cfg["width"]
    garden.HEIGHT = garden_cfg["height"]

    agent_dids = {}
    for a in scenario["admitted"]:
        kp = _kp_from_seed(a["seed_hex"])
        agent_dids[a["name"]] = _did_from_kp(kp)

    for action in scenario["actions"]:
        t = action["type"]
        if t == "add_plant":
            kind = action["kind"]
            pos = Cell(*action["position"])
            if kind == "fern":
                h_kp = Ed25519PrivateKey.generate()
                host = ChaosGameHost(
                    f"plant:{action['id']}",
                    ChaosGameWorld(
                        preset=BARNSLEY,
                        growth_mode="seeded_random",
                        initial_point=(500, 500),
                        keypair=h_kp,
                        prng_seed=action["seed"],
                    ),
                    _did_from_kp(h_kp),
                    description=f"a {kind}",
                )
            elif kind == "vine":
                h_kp = Ed25519PrivateKey.generate()
                host = ElementaryCAHost(
                    f"plant:{action['id']}",
                    ElementaryCAWorld(
                        params=rule_30(),
                        initial_cells=[0],
                        keypair=h_kp,
                    ),
                    _did_from_kp(h_kp),
                    description="a vine",
                )
            else:
                raise ValueError(f"unknown kind {kind}")
            garden.add_plant(action["id"], kind, host, pos)
        elif t == "admit":
            name = action["agent"]
            garden.petition(Petition(
                petitioner_token=agent_dids[name],
                petitioner_name=name,
                passport_admissions=(),
                message="",
            ))
        elif t == "enter":
            garden.act(Act(
                actor_token=agent_dids[action["agent"]],
                type="garden.walk",
                payload={"start": action["at"]},
            ))
        elif t == "walk":
            garden.act(Act(
                actor_token=agent_dids[action["agent"]],
                type="garden.walk",
                payload={"direction": action["direction"]},
            ))
        elif t == "observe":
            garden.act(Act(
                actor_token=agent_dids[action["agent"]],
                type="garden.observe",
                payload={},
            ))
        elif t == "speak":
            garden.act(Act(
                actor_token=agent_dids[action["agent"]],
                type="garden.speak",
                payload={"text": action["text"]},
            ))
        elif t == "cycle_advance":
            garden.advance_cycle(action["steps"])
        else:
            raise ValueError(f"unknown action {t}")

    return garden, agent_dids


def compute_expected(garden, agent_dids) -> dict:
    """Extract the observable hashes from a completed run."""
    entry_hashes = [e["sig"] if False else _hash_entry(e)
                     for e in garden.log_since(None)]

    plant_events = {}
    for pid, plant in garden.all_plants().items():
        plant_events[pid] = [ev["hash"]
                              for ev in plant.host.events()]

    xref_count = sum(
        1 for e in garden.log_since(None)
        if e.get("kind") == "agent_observed"
        and e.get("result") == "observed_plant"
    )

    alice_pos = garden.position_of(agent_dids["ALICE"])
    bob_pos = garden.position_of(agent_dids["BOB"])

    return {
        "log_length": len(entry_hashes),
        "entry_hashes": entry_hashes,
        "plant_event_hashes": plant_events,
        "cross_reference_count": xref_count,
        "alice_final_position":
            alice_pos.to_list() if alice_pos else None,
        "bob_final_position":
            bob_pos.to_list() if bob_pos else None,
    }


def _hash_entry(e: dict) -> str:
    """Hash a log entry the way both implementations must.
    For Python, the entry is signed already; the hash of the
    signed entry (including sig) is the observable."""
    from individual_bundle import _hash
    return _hash(e)


def main():
    root = Path(__file__).parent.parent
    scenario_path = root / "vectors" / "garden_reference.json"

    if scenario_path.exists():
        existing = json.loads(scenario_path.read_text())
    else:
        print(f"scenario file not found: {scenario_path}",
              file=sys.stderr)
        print("generate it first, or supply it manually.",
              file=sys.stderr)
        sys.exit(1)

    garden, agent_dids = build_scenario(existing["scenario"])
    expected = compute_expected(garden, agent_dids)

    existing["expected"] = expected
    scenario_path.write_text(
        json.dumps(existing, indent=2))

    print(f"wrote {scenario_path}")
    print(f"  log_length: {expected['log_length']}")
    print(f"  cross_references: "
          f"{expected['cross_reference_count']}")
    print(f"  alice: {expected['alice_final_position']}")
    print(f"  bob:   {expected['bob_final_position']}")


if __name__ == "__main__":
    main()

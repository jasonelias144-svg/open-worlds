import json
import pytest
from individual_bundle import IndividualBundle
from federated_bundle import (
    FederatedSession, pack_federated_bundle,
    verify_federated_basic, verify_federated_full,
)
from federated_spawn import (
    spawn_federated_child, pack_federated_child,
)
from lineage_root import verify_lineage_root
from compact_ancestry import (
    CompactAncestry, compute_compact_ancestry, slim_bundle,
    genesis_ancestry_root, compute_ancestry_root,
    verify_compact_ancestry, compact_ancestry_size,
    full_ancestry_size, demo, HAS_CRYPTO,
)
from world_agent_coupling import ScriptedWorld
from coupled_learners import TinyRNN, SIERPINSKI
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey)

pytestmark = pytest.mark.skipif(
    not HAS_CRYPTO, reason="cryptography not installed")


def _kp():
    return Ed25519PrivateKey.generate()


def _world(k_b=50, prng=0xCAFE):
    return ScriptedWorld(
        kp=_kp(), initial_point_b=(800, 800),
        k_b=k_b, prng_seed_b=prng, rule=SIERPINSKI)


def _build_chain(depth=4, steps=10):
    """Returns (kps, bundles_list, spawn_records, fetcher)."""
    kps: list = []
    sessions_lists: list = []
    memories: list = []
    models: list = []
    spawn_records: list = []

    # Gen 0
    kp0 = _kp()
    m0 = TinyRNN(n_extra_inputs=0, seed=100)
    mem0: list = []
    s0 = FederatedSession(
        individual_kp=kp0, model=m0,
        world=_world(0, 0xAAAA),
        initial_point=(200, 800), memory=mem0,
        rule=SIERPINSKI)
    for _ in range(steps):
        s0.step()
    kps.append(kp0); models.append(m0)
    sessions_lists.append([s0]); memories.append(mem0)

    for i in range(1, depth + 1):
        parent_sessions = sessions_lists[i - 1]
        child_kp, child_model, spawn_rec, inherited_w = \
            spawn_federated_child(
                parent_session=parent_sessions[-1],
                child_persona=f"gen{i}",
                child_initial_seed=100 + i)
        parent_sessions[-1].step()
        kps.append(child_kp); models.append(child_model)
        spawn_records.append(spawn_rec)
        mem_i: list = []
        s_i = FederatedSession(
            individual_kp=child_kp, model=child_model,
            world=_world(i * 10, 0xAAAA + i * 0x1111),
            initial_point=(200 + i * 10, 800),
            memory=mem_i, rule=SIERPINSKI)
        for _ in range(steps):
            s_i.step()
        sessions_lists.append([s_i])
        memories.append(mem_i)

    bundles_list: list = []
    b0 = pack_federated_bundle(
        individual_kp=kps[0], model=models[0],
        sessions=sessions_lists[0], memory=memories[0],
        persona="origin", initial_seed=100, name="gen0")
    bundles_list.append(b0)
    for i in range(1, depth + 1):
        bi = pack_federated_child(
            child_kp=kps[i], child_model=models[i],
            child_sessions=sessions_lists[i],
            child_memory=memories[i],
            child_persona=f"gen{i}",
            child_initial_seed=100 + i,
            parent_bundle=bundles_list[i - 1],
            spawn_record=spawn_records[i - 1],
            inherited_weights=__import__(
                "individual_bundle").serialize_weights(
                    models[i - 1]) if False else None,
            name=f"gen{i}") if False else \
            pack_federated_child(
                child_kp=kps[i], child_model=models[i],
                child_sessions=sessions_lists[i],
                child_memory=memories[i],
                child_persona=f"gen{i}",
                child_initial_seed=100 + i,
                parent_bundle=bundles_list[i - 1],
                spawn_record=spawn_records[i - 1],
                inherited_weights=None,
                name=f"gen{i}")
        bundles_list.append(bi)

    full_by_id = {b.individual_id: b for b in bundles_list}
    def fetcher(did):
        return full_by_id.get(did)
    return kps, bundles_list, spawn_records, fetcher


# -- Hash composition --

def test_genesis_root_deterministic():
    a = genesis_ancestry_root("did:key:abc")
    b = genesis_ancestry_root("did:key:abc")
    assert a == b
    assert a != genesis_ancestry_root("did:key:def")


def test_compute_ancestry_root_composes():
    a = compute_ancestry_root("h1", "s1")
    b = compute_ancestry_root("h1", "s1")
    assert a == b
    assert a != compute_ancestry_root("h1", "s2")
    assert a != compute_ancestry_root("h2", "s1")


# -- Compute compact --

def test_compute_compact_for_origin_child():
    kps, bundles, spawns, _ = _build_chain(depth=2, steps=5)
    compact = compute_compact_ancestry(
        bundles[1].individual_id, bundles[0], spawns[0])
    assert compact.parent_did == bundles[0].individual_id
    assert compact.root_did == bundles[0].individual_id
    expected = compute_ancestry_root(
        genesis_ancestry_root(bundles[0].individual_id),
        __import__("individual_spawn").spawn_record_hash(spawns[0]))
    assert compact.ancestry_root == expected


def test_compute_compact_for_deep_child():
    kps, bundles, spawns, _ = _build_chain(depth=3, steps=5)
    # Slim the middle one first
    parent_b = bundles[1]
    compact1 = compute_compact_ancestry(
        bundles[2].individual_id, parent_b, spawns[1])
    slim1 = slim_bundle(bundles[2], compact1, kps[2])
    # Now compute compact for the deep child from slim middle
    compact2 = compute_compact_ancestry(
        bundles[3].individual_id, slim1, spawns[2])
    assert compact2.root_did == bundles[0].individual_id
    # ancestry_root commits to both levels
    expected = compute_ancestry_root(
        compact1.ancestry_root,
        __import__("individual_spawn").spawn_record_hash(spawns[2]))
    assert compact2.ancestry_root == expected


# -- Slim bundle --

def test_slim_bundle_drops_ancestry():
    kps, bundles, spawns, _ = _build_chain(depth=3, steps=5)
    compact = compute_compact_ancestry(
        bundles[2].individual_id, bundles[1], spawns[1])
    slim = slim_bundle(bundles[2], compact, kps[2])
    assert slim.ancestry == []
    assert "ancestry_hash" not in slim.manifest
    assert "compact_ancestry" in slim.manifest
    assert slim.manifest["compact_ancestry"] == compact.to_dict()


def test_slim_bundle_basic_passes():
    kps, bundles, spawns, _ = _build_chain(depth=3, steps=5)
    compact = compute_compact_ancestry(
        bundles[2].individual_id, bundles[1], spawns[1])
    slim = slim_bundle(bundles[2], compact, kps[2])
    from individual_bundle import verify_bundle_basic
    ok, reason = verify_bundle_basic(slim)
    assert ok, reason


# -- Verification --

def test_verify_slim_chain():
    kps, bundles, spawns, fetcher = _build_chain(depth=3, steps=5)
    slim_chain = [bundles[0]]
    for i in range(1, len(bundles)):
        compact = compute_compact_ancestry(
            bundles[i].individual_id, slim_chain[i - 1],
            spawns[i - 1])
        slim = slim_bundle(bundles[i], compact, kps[i])
        slim_chain.append(slim)
    for slim in slim_chain:
        ok, reason = verify_compact_ancestry(slim, fetcher)
        assert ok, reason


def test_root_bundle_verifies_as_origin():
    kps, bundles, spawns, fetcher = _build_chain(depth=2, steps=5)
    ok, reason = verify_compact_ancestry(bundles[0], fetcher)
    assert ok
    assert "origin" in reason.lower() or "root" in reason.lower()


def test_full_ancestry_still_verifies():
    """Backward compat: full bundles still pass lineage_root."""
    kps, bundles, spawns, _ = _build_chain(depth=3, steps=5)
    for b in bundles:
        ok, reason = verify_lineage_root(b)
        assert ok, reason


# -- Tampering --

def test_tampered_ancestry_root_fails():
    kps, bundles, spawns, fetcher = _build_chain(depth=3, steps=5)
    # Build slim for bundles[2]
    compact = compute_compact_ancestry(
        bundles[2].individual_id, bundles[1], spawns[1])
    slim = slim_bundle(bundles[2], compact, kps[2])
    # Tamper: change ancestry_root
    tampered = slim_bundle(
        slim,
        CompactAncestry(
            root_did=compact.root_did,
            ancestry_root="00" * 32,
            parent_did=compact.parent_did,
            spawn_record_hash=compact.spawn_record_hash,
        ),
        kps[2])
    ok, _ = verify_compact_ancestry(tampered, fetcher)
    assert not ok


def test_tampered_spawn_hash_fails():
    kps, bundles, spawns, fetcher = _build_chain(depth=3, steps=5)
    compact = compute_compact_ancestry(
        bundles[2].individual_id, bundles[1], spawns[1])
    slim = slim_bundle(bundles[2], compact, kps[2])
    tampered = slim_bundle(
        slim,
        CompactAncestry(
            root_did=compact.root_did,
            ancestry_root=compact.ancestry_root,
            parent_did=compact.parent_did,
            spawn_record_hash="00" * 32,
        ),
        kps[2])
    ok, _ = verify_compact_ancestry(tampered, fetcher)
    assert not ok


def test_tampered_root_did_fails():
    kps, bundles, spawns, fetcher = _build_chain(depth=4, steps=5)
    slim_chain = [bundles[0]]
    for i in range(1, len(bundles)):
        compact = compute_compact_ancestry(
            bundles[i].individual_id, slim_chain[i - 1],
            spawns[i - 1])
        slim = slim_bundle(bundles[i], compact, kps[i])
        slim_chain.append(slim)
    # Tamper deepest
    deepest_compact = CompactAncestry.from_dict(
        slim_chain[-1].manifest["compact_ancestry"])
    tampered = slim_bundle(
        slim_chain[-1],
        CompactAncestry(
            root_did="did:key:" + "00" * 32,
            ancestry_root=deepest_compact.ancestry_root,
            parent_did=deepest_compact.parent_did,
            spawn_record_hash=deepest_compact.spawn_record_hash,
        ),
        kps[-1])
    ok, _ = verify_compact_ancestry(tampered, fetcher)
    assert not ok


def test_missing_parent_fails():
    kps, bundles, spawns, fetcher = _build_chain(depth=3, steps=5)
    compact = compute_compact_ancestry(
        bundles[2].individual_id, bundles[1], spawns[1])
    slim = slim_bundle(bundles[2], compact, kps[2])
    # Fetch that returns None for the parent
    def broken_fetcher(did):
        return None
    ok, _ = verify_compact_ancestry(slim, broken_fetcher)
    assert not ok


def test_missing_spawn_in_parent_fails():
    kps, bundles, spawns, fetcher = _build_chain(depth=3, steps=5)
    compact = compute_compact_ancestry(
        bundles[2].individual_id, bundles[1], spawns[1])
    slim = slim_bundle(bundles[2], compact, kps[2])
    # Fetcher returns a valid parent bundle but tampered to
    # remove the spawn record
    parent = bundles[1]
    tampered_parent = IndividualBundle(
        manifest=dict(parent.manifest),
        memory=[r for r in parent.memory
                 if r.get("type") != "spawn"],
        weights=parent.weights,
        initial_weights=parent.initial_weights,
        observations=parent.observations,
        ancestry=parent.ancestry,
    )
    # Recompute memory_root
    from individual_bundle import _merkle_root, _hash, _canonical
    tampered_parent.manifest = dict(tampered_parent.manifest)
    tampered_parent.manifest["memory_entries"] = len(
        tampered_parent.memory)
    tampered_parent.manifest["memory_root"] = _merkle_root([
        _hash({k: v for k, v in r.items() if k != "sig"})
        for r in tampered_parent.memory])
    body = {k: v for k, v in tampered_parent.manifest.items()
             if k != "sig"}
    tampered_parent.manifest["sig"] = kps[1].sign(
        _canonical(body)).hex()
    def tampered_fetcher(did):
        if did == parent.individual_id:
            return tampered_parent
        return fetcher(did)
    ok, _ = verify_compact_ancestry(slim, tampered_fetcher)
    assert not ok


# -- Size comparison --

def test_compact_smaller_than_full():
    kps, bundles, spawns, _ = _build_chain(depth=4, steps=5)
    # Deepest's full ancestry
    deepest = bundles[-1]
    full_size = full_ancestry_size(deepest.ancestry)
    # Compute compact
    slim_chain = [bundles[0]]
    for i in range(1, len(bundles)):
        compact = compute_compact_ancestry(
            bundles[i].individual_id, slim_chain[i - 1],
            spawns[i - 1])
        slim = slim_bundle(bundles[i], compact, kps[i])
        slim_chain.append(slim)
    deepest_compact = CompactAncestry.from_dict(
        slim_chain[-1].manifest["compact_ancestry"])
    compact_size = compact_ancestry_size(deepest_compact)
    assert compact_size < full_size
    # And significantly so for depth 4
    assert compact_size < full_size // 2


# -- Save/load --

def test_slim_bundle_save_load(tmp_path):
    kps, bundles, spawns, fetcher = _build_chain(depth=2, steps=5)
    compact = compute_compact_ancestry(
        bundles[1].individual_id, bundles[0], spawns[0])
    slim = slim_bundle(bundles[1], compact, kps[1])
    slim.save(tmp_path / "s")
    loaded = IndividualBundle.load(tmp_path / "s")
    assert "compact_ancestry" in loaded.manifest
    ok, reason = verify_compact_ancestry(loaded, fetcher)
    assert ok, reason


# -- Demo --

def test_demo(tmp_path):
    audit = demo(artifact_dir=str(tmp_path))
    assert audit["chain_length"] == 6
    for v in audit["full_verification"]:
        assert v["lineage"] is True, v["name"]
        assert v["federated_full"] is True, v["name"]
    for v in audit["slim_verification"]:
        assert v["compact_ancestry"] is True, v["name"]
        assert v["federated_full"] is True, v["name"]
    assert all(t["detected"] for t in audit["tampering"].values())
    # Sizes should grow for full, stay flat for compact
    sizes = audit["sizes"]
    assert sizes[-1]["ancestry_records"] > sizes[0]["ancestry_records"]
    # Compact size is roughly constant
    compact_sizes = [s["compact_ancestry_bytes"] for s in sizes]
    assert max(compact_sizes) - min(compact_sizes) < 100  # roughly flat

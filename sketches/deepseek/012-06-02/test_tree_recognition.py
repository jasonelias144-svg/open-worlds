import json
import pytest
from individual_bundle import (
    IndividualBundle, _canonical, _did_from_kp,
)
from federated_bundle import (
    FederatedSession, pack_federated_bundle,
    verify_federated_full,
)
from federated_spawn import (
    spawn_federated_child, pack_federated_child,
)
from compact_ancestry import (
    compute_compact_ancestry, slim_bundle,
)
from tree_recognition import (
    TreeRecognition, sign_recognition, sign_derecognition,
    verify_recognition, RecognitionStore,
    verify_cross_tree_bundle, verify_cross_tree_chain,
    render_trust_graph, demo,
    VALID_SCOPES, HAS_CRYPTO,
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


def _build_tree(depth=2, steps=5, base=100):
    kps = []
    models = []
    memories = []
    sessions_list = []
    spawns = []
    inherited = []

    kp0 = _kp()
    m0 = TinyRNN(n_extra_inputs=0, seed=base)
    mem0: list = []
    s0 = FederatedSession(
        individual_kp=kp0, model=m0,
        world=_world(0, 0xAAAA + base),
        initial_point=(200, 800), memory=mem0,
        rule=SIERPINSKI)
    for _ in range(steps):
        s0.step()
    kps.append(kp0); models.append(m0)
    memories.append(mem0); sessions_list.append([s0])

    for i in range(1, depth + 1):
        parent_sessions = sessions_list[i - 1]
        child_kp, child_model, spawn_rec, inherited_w = \
            spawn_federated_child(
                parent_session=parent_sessions[-1],
                child_persona=f"g{i}",
                child_initial_seed=base + i * 100)
        parent_sessions[-1].step()
        kps.append(child_kp); models.append(child_model)
        spawns.append(spawn_rec)
        inherited.append(inherited_w)
        mem_i: list = []
        s_i = FederatedSession(
            individual_kp=child_kp, model=child_model,
            world=_world(i * 10 + base,
                         0xAAAA + i * 0x1111 + base),
            initial_point=(200 + i * 10, 800),
            memory=mem_i, rule=SIERPINSKI)
        for _ in range(steps):
            s_i.step()
        memories.append(mem_i); sessions_list.append([s_i])

    full = [pack_federated_bundle(
        individual_kp=kps[0], model=models[0],
        sessions=sessions_list[0], memory=memories[0],
        persona=f"root-{base}", initial_seed=base, name=f"g0")]
    for i in range(1, depth + 1):
        full.append(pack_federated_child(
            child_kp=kps[i], child_model=models[i],
            child_sessions=sessions_list[i],
            child_memory=memories[i],
            child_persona=f"g{i}",
            child_initial_seed=base + i * 100,
            parent_bundle=full[i - 1],
            spawn_record=spawns[i - 1],
            inherited_weights=inherited[i - 1],
            name=f"g{i}"))

    slim = [full[0]]
    for i in range(1, depth + 1):
        compact = compute_compact_ancestry(
            full[i].individual_id, slim[i - 1],
            spawns[i - 1])
        slim.append(slim_bundle(full[i], compact, kps[i]))

    full_by_id = {b.individual_id: b for b in full}
    def fetcher(did):
        return full_by_id.get(did)
    return {
        "root_kp": kps[0],
        "root_did": full[0].individual_id,
        "slim": slim, "full": full,
        "fetcher": fetcher,
    }


# -- Record basics --

def test_recognition_sign_verify():
    kp = _kp()
    target = "did:key:" + "01" * 32
    rec = sign_recognition(kp, target,
                             scopes=["lineage", "inheritance"])
    ok, reason = verify_recognition(rec)
    assert ok, reason


def test_recognition_bad_scope_rejected():
    kp = _kp()
    with pytest.raises(ValueError):
        sign_recognition(kp, "did:key:" + "01" * 32,
                          scopes=["god"])
    with pytest.raises(ValueError):
        sign_recognition(kp, "did:key:" + "01" * 32, scopes=[])


def test_recognition_self_reference_rejected():
    kp = _kp()
    self_did = _did_from_kp(kp)
    with pytest.raises(ValueError):
        sign_recognition(kp, self_did, scopes=["lineage"])


def test_derecognition_rejects_scopes():
    kp = _kp()
    with pytest.raises(ValueError):
        TreeRecognition(
            record_type="derecognition",
            recognizer_did=_did_from_kp(kp),
            recognized_did="did:key:" + "01" * 32,
            scopes=("lineage",),  # must be empty
            ts="t", sig="s")


def test_verify_recognition_wrong_recognizer():
    kp = _kp()
    rec = sign_recognition(kp, "did:key:" + "01" * 32,
                             scopes=["lineage"])
    wrong = _kp()
    ok, _ = verify_recognition(rec, _did_from_kp(wrong))
    assert not ok


def test_verify_recognition_tampered_sig():
    kp = _kp()
    rec = sign_recognition(kp, "did:key:" + "01" * 32,
                             scopes=["lineage"])
    tampered = TreeRecognition(
        record_type="recognition",
        recognizer_did=rec.recognizer_did,
        recognized_did=rec.recognized_did,
        scopes=rec.scopes,
        ts=rec.ts, sig="00" * 64,
    )
    ok, _ = verify_recognition(tampered)
    assert not ok


# -- Store --

def test_store_tracks_latest():
    kp = _kp()
    target = "did:key:" + "01" * 32
    recognizer = _did_from_kp(kp)
    store = RecognitionStore()
    rec1 = sign_recognition(kp, target, scopes=["lineage"])
    store.add(rec1)
    assert store.current(recognizer, target).record_type == "recognition"
    derec = sign_derecognition(kp, target)
    store.add(derec)
    assert store.current(recognizer, target).record_type == "derecognition"
    # Derecognition wins
    ok, reason = store.is_recognized(
        recognizer, target, {"lineage"})
    assert not ok
    assert "revoked" in reason.lower()


def test_store_scope_checking():
    kp = _kp()
    target = "did:key:" + "01" * 32
    recognizer = _did_from_kp(kp)
    store = RecognitionStore()
    store.add(sign_recognition(
        kp, target, scopes=["lineage"]))
    ok, _ = store.is_recognized(
        recognizer, target, {"lineage"})
    assert ok
    ok, reason = store.is_recognized(
        recognizer, target, {"lineage", "inheritance"})
    assert not ok
    assert "inheritance" in reason.lower()


def test_store_no_record():
    kp = _kp()
    target = "did:key:" + "01" * 32
    recognizer = _did_from_kp(kp)
    store = RecognitionStore()
    ok, _ = store.is_recognized(recognizer, target, {"lineage"})
    assert not ok


# -- Cross-tree verification --

def test_direct_trust():
    tree = _build_tree(depth=2, steps=5, base=100)
    store = RecognitionStore()
    ok, reason = verify_cross_tree_bundle(
        tree["slim"][-1], {tree["root_did"]},
        tree["fetcher"], store)
    assert ok, reason
    assert "directly trusted" in reason.lower()


def test_recognized_trust():
    tree_a = _build_tree(depth=2, steps=5, base=100)
    tree_b = _build_tree(depth=1, steps=3, base=200)
    store = RecognitionStore()
    store.add(sign_recognition(
        tree_b["root_kp"], tree_a["root_did"],
        scopes=["lineage"]))
    ok, reason = verify_cross_tree_bundle(
        tree_a["slim"][-1], {tree_b["root_did"]},
        tree_a["fetcher"], store)
    assert ok, reason
    assert "recognizes" in reason.lower()


def test_recognition_with_scope_check():
    tree_a = _build_tree(depth=2, steps=5, base=100)
    tree_b = _build_tree(depth=1, steps=3, base=200)
    store = RecognitionStore()
    store.add(sign_recognition(
        tree_b["root_kp"], tree_a["root_did"],
        scopes=["lineage"]))
    # Required only lineage — should pass
    ok, _ = verify_cross_tree_bundle(
        tree_a["slim"][-1], {tree_b["root_did"]},
        tree_a["fetcher"], store,
        required_scopes={"lineage"})
    assert ok
    # Required lineage + inheritance — should fail
    ok, reason = verify_cross_tree_bundle(
        tree_a["slim"][-1], {tree_b["root_did"]},
        tree_a["fetcher"], store,
        required_scopes={"lineage", "inheritance"})
    assert not ok
    assert "inheritance" in reason.lower()


def test_derecognition_blocks():
    tree_a = _build_tree(depth=2, steps=5, base=100)
    tree_b = _build_tree(depth=1, steps=3, base=200)
    store = RecognitionStore()
    store.add(sign_recognition(
        tree_b["root_kp"], tree_a["root_did"],
        scopes=["lineage"]))
    store.add(sign_derecognition(
        tree_b["root_kp"], tree_a["root_did"]))
    ok, reason = verify_cross_tree_bundle(
        tree_a["slim"][-1], {tree_b["root_did"]},
        tree_a["fetcher"], store)
    assert not ok
    assert "revoked" in reason.lower()


def test_untrusted_root_no_recognition():
    tree_c = _build_tree(depth=2, steps=5, base=300)
    tree_b = _build_tree(depth=1, steps=3, base=200)
    store = RecognitionStore()  # empty
    ok, reason = verify_cross_tree_bundle(
        tree_c["slim"][-1], {tree_b["root_did"]},
        tree_c["fetcher"], store)
    assert not ok


def test_multiple_trusted_roots_any_suffices():
    tree_a = _build_tree(depth=2, steps=5, base=100)
    tree_b = _build_tree(depth=1, steps=3, base=200)
    tree_c = _build_tree(depth=1, steps=3, base=300)
    store = RecognitionStore()
    store.add(sign_recognition(
        tree_b["root_kp"], tree_a["root_did"],
        scopes=["lineage"]))
    # Trust set: {B, C}. B recognizes A → A passes.
    ok, _ = verify_cross_tree_bundle(
        tree_a["slim"][-1],
        {tree_b["root_did"], tree_c["root_did"]},
        tree_a["fetcher"], store)
    assert ok


def test_tampered_bundle_fails_at_local():
    """If the bundle itself is tampered, local verification
    fails first."""
    tree_a = _build_tree(depth=2, steps=5, base=100)
    tree_b = _build_tree(depth=1, steps=3, base=200)
    store = RecognitionStore()
    store.add(sign_recognition(
        tree_b["root_kp"], tree_a["root_did"],
        scopes=["lineage"]))
    target = tree_a["slim"][-1]
    # Tamper a memory entry
    tampered = IndividualBundle(
        manifest=dict(target.manifest),
        memory=[dict(r) for r in target.memory],
        weights=dict(target.weights),
        initial_weights=(dict(target.initial_weights)
                          if target.initial_weights else None),
        observations=list(target.observations),
        ancestry=[],
    )
    for i, r in enumerate(tampered.memory):
        if r.get("type") == "agent_step":
            tampered.memory[i] = {**r, "action": 99}
            break
    ok, reason = verify_cross_tree_bundle(
        tampered, {tree_b["root_did"]},
        tree_a["fetcher"], store)
    assert not ok
    assert "local" in reason.lower()


def test_no_trusted_roots():
    tree_a = _build_tree(depth=2, steps=5, base=100)
    store = RecognitionStore()
    ok, _ = verify_cross_tree_bundle(
        tree_a["slim"][-1], set(),
        tree_a["fetcher"], store)
    assert not ok


def test_invalid_required_scope():
    tree_a = _build_tree(depth=2, steps=5, base=100)
    store = RecognitionStore()
    ok, _ = verify_cross_tree_bundle(
        tree_a["slim"][-1], {tree_a["root_did"]},
        tree_a["fetcher"], store,
        required_scopes={"god"})
    assert not ok


def test_chain_verification():
    tree_a = _build_tree(depth=2, steps=5, base=100)
    tree_b = _build_tree(depth=1, steps=3, base=200)
    store = RecognitionStore()
    store.add(sign_recognition(
        tree_b["root_kp"], tree_a["root_did"],
        scopes=["lineage", "inheritance"]))
    ok, reason = verify_cross_tree_chain(
        tree_a["slim"], {tree_b["root_did"]}, store)
    assert ok, reason


# -- Local modes --

def test_full_ancestry_mode():
    """If local_mode is 'full', verify_lineage_root is used
    instead of compact. Should still pass."""
    tree_a = _build_tree(depth=2, steps=5, base=100)
    store = RecognitionStore()
    # Full bundles (not slim) for full ancestry mode
    ok, reason = verify_cross_tree_bundle(
        tree_a["full"][-1], {tree_a["root_did"]},
        tree_a["fetcher"], store,
        local_mode="full")
    assert ok, reason


def test_compact_mode_only():
    """If local_mode is 'compact', inheritance is not verified.
    A bundle with tampered initial_weights can still pass the
    compact check (but basic would fail)."""
    tree_a = _build_tree(depth=2, steps=5, base=100)
    store = RecognitionStore()
    ok, reason = verify_cross_tree_bundle(
        tree_a["slim"][-1], {tree_a["root_did"]},
        tree_a["fetcher"], store,
        local_mode="compact")
    assert ok, reason


# -- Rendering --

def test_render_trust_graph():
    kp = _kp()
    b = _did_from_kp(kp)
    a = "did:key:" + "01" * 32
    store = RecognitionStore()
    store.add(sign_recognition(kp, a, scopes=["lineage"]))
    text = render_trust_graph({b}, store, [a])
    assert b[:20] in text
    assert "scopes" in text


# -- Save / load --

def test_recognition_roundtrip():
    kp = _kp()
    target = "did:key:" + "01" * 32
    rec = sign_recognition(kp, target, scopes=["lineage"])
    d = rec.to_dict()
    wire = json.dumps(d)
    parsed = json.loads(wire)
    rec2 = TreeRecognition(
        record_type=parsed["type"].replace("tree_", ""),
        recognizer_did=parsed["recognizer_did"],
        recognized_did=parsed["recognized_did"],
        scopes=tuple(parsed["scopes"]),
        ts=parsed["ts"], sig=parsed["sig"])
    ok, _ = verify_recognition(rec2)
    assert ok


# -- Demo --

def test_demo(tmp_path):
    audit = demo(artifact_dir=str(tmp_path))
    assert audit["positive"]["via_b_lineage"] is True
    assert audit["positive"]["via_b_lineage_inheritance"] is True
    assert audit["positive"]["via_a_direct"] is True
    assert audit["positive"]["chain_via_b"] is True
    assert audit["tampering"]["bad_recognition_sig"]["detected"] is True
    assert audit["tampering"]["narrow_scope"]["detected"] is True
    assert audit["tampering"]["derecognized"]["detected"] is True
    assert audit["tampering"]["unrelated_c"]["detected"] is True
    assert audit["tampering"]["c_via_multiple_roots"]["ok"] is True
    assert (tmp_path / "tree_recognition" /
            "tree_recognition_demo.json").exists()

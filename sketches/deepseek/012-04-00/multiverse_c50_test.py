import json
import tempfile
from pathlib import Path

import pytest

from multiverse_c1 import create_identity, Identity
from multiverse_c3 import Act, Ack, Refusal
from multiverse_c13 import HAS_CRYPTO, KeyPair, canonical_bytes
from multiverse_c50 import (
    EVALUATOR_VERSION,
    Clause, PolicyText,
    sign_policy, verify_policy_signature,
    _matches, evaluate_policy,
    Ruling, verify_ruling,
    Amendment, verify_amendment,
    InstitutionalUnit,
    reproduce_ruling,
    demo,
)


pytestmark = pytest.mark.skipif(
    not HAS_CRYPTO, reason="cryptography not installed")


# =====================================================================
# Helpers
# =====================================================================

def _make_clause(clause_id="c1", field="x", op="eq", value=1,
                 outcome="accept"):
    return Clause(
        clause_id=clause_id,
        condition={"field": field, "op": op, "value": value},
        outcome=outcome)


def _make_v1(author=None, author_kp=None, policy_id="p"):
    if author is None:
        author = create_identity("Alice")
    if author_kp is None:
        author_kp = KeyPair.generate()
    return sign_policy(
        policy_id=policy_id, version=1,
        clauses=[_make_clause(clause_id="c1", field="x",
                                op="eq", value=1,
                                outcome="accept")],
        default_outcome="reject",
        author=author, author_kp=author_kp,
    ), author, author_kp


def _make_unit(policy=None):
    if policy is None:
        policy, _, _ = _make_v1()
    unit_kp = KeyPair.generate()
    unit = InstitutionalUnit(
        "world:u", "U", unit_kp=unit_kp,
        initial_policy=policy)
    return unit, unit_kp


# =====================================================================
# Clause construction
# =====================================================================

def test_clause_validates_fields():
    print("=== Clause: required fields validated ===")
    with pytest.raises(ValueError):
        Clause(clause_id="", condition={}, outcome="x")
    with pytest.raises(ValueError):
        Clause(clause_id="c", condition="not a dict", outcome="x")
    with pytest.raises(ValueError):
        Clause(clause_id="c", condition={}, outcome="")


def test_clause_json_roundtrip():
    print("=== Clause: JSON roundtrip ===")
    c = _make_clause()
    revived = Clause.from_dict(c.to_dict())
    assert revived == c


# =====================================================================
# PolicyText construction
# =====================================================================

def test_policy_requires_at_least_one_clause():
    print("=== PolicyText: requires >= 1 clause ===")
    author = create_identity("A")
    kp = KeyPair.generate()
    with pytest.raises(ValueError):
        sign_policy(
            policy_id="p", version=1, clauses=[],
            default_outcome="reject",
            author=author, author_kp=kp)


def test_policy_rejects_duplicate_clause_ids():
    print("=== PolicyText: rejects duplicate clause_ids ===")
    author = create_identity("A")
    kp = KeyPair.generate()
    with pytest.raises(ValueError):
        sign_policy(
            policy_id="p", version=1,
            clauses=[_make_clause(clause_id="dup"),
                     _make_clause(clause_id="dup")],
            default_outcome="reject",
            author=author, author_kp=kp)


def test_policy_rejects_zero_version():
    print("=== PolicyText: rejects version 0 ===")
    author = create_identity("A")
    kp = KeyPair.generate()
    with pytest.raises(ValueError):
        sign_policy(
            policy_id="p", version=0,
            clauses=[_make_clause()],
            default_outcome="reject",
            author=author, author_kp=kp)


# =====================================================================
# Policy signing
# =====================================================================

def test_policy_signature_verifies():
    print("=== Policy signature: verifies with author key ===")
    policy, _, author_kp = _make_v1()
    assert verify_policy_signature(
        policy, author_kp.public_key_hex())


def test_policy_signature_wrong_key():
    print("=== Policy signature: wrong key → False ===")
    policy, _, _ = _make_v1()
    wrong = KeyPair.generate()
    assert not verify_policy_signature(
        policy, wrong.public_key_hex())


def test_policy_signature_tampered():
    print("=== Policy signature: tampered → False ===")
    policy, author, author_kp = _make_v1()
    tampered = PolicyText(
        policy_id=policy.policy_id,
        version=policy.version,
        clauses=policy.clauses,
        default_outcome="accept",  # was reject
        author_token=policy.author_token,
        author_public_key=policy.author_public_key,
        author_signature=policy.author_signature,
    )
    assert not verify_policy_signature(
        tampered, author_kp.public_key_hex())


def test_policy_hash_deterministic():
    print("=== Policy hash: deterministic across construction ===")
    author = create_identity("A")
    kp = KeyPair.generate()
    p1 = sign_policy(
        "p", 1, [_make_clause()], "reject", author, kp)
    p2 = sign_policy(
        "p", 1, [_make_clause()], "reject", author, kp)
    assert p1.policy_hash() == p2.policy_hash()


# =====================================================================
# Evaluator — predicates
# =====================================================================

def test_matches_eq():
    print("=== _matches: eq ===")
    assert _matches({"field": "x", "op": "eq", "value": 1},
                     {"x": 1})
    assert not _matches({"field": "x", "op": "eq", "value": 1},
                         {"x": 2})


def test_matches_ne():
    print("=== _matches: ne ===")
    assert _matches({"field": "x", "op": "ne", "value": 1},
                     {"x": 2})
    assert not _matches({"field": "x", "op": "ne", "value": 1},
                         {"x": 1})


def test_matches_gt_lt_ge_le():
    print("=== _matches: gt / lt / ge / le ===")
    assert _matches({"field": "x", "op": "gt", "value": 5},
                     {"x": 6})
    assert not _matches({"field": "x", "op": "gt", "value": 5},
                         {"x": 5})
    assert _matches({"field": "x", "op": "lt", "value": 5},
                     {"x": 4})
    assert _matches({"field": "x", "op": "ge", "value": 5},
                     {"x": 5})
    assert _matches({"field": "x", "op": "le", "value": 5},
                     {"x": 5})
    # Type mismatch → False, not raise
    assert not _matches({"field": "x", "op": "gt", "value": 5},
                         {"x": "str"})


def test_matches_in_contains():
    print("=== _matches: in / contains ===")
    assert _matches({"field": "x", "op": "in",
                      "value": ["a", "b", "c"]},
                     {"x": "b"})
    assert not _matches({"field": "x", "op": "in",
                          "value": ["a", "b"]},
                         {"x": "c"})
    assert _matches({"field": "x", "op": "contains",
                      "value": "dickinson"},
                     {"x": "Poems of Dickinson"})
    assert not _matches({"field": "x", "op": "contains",
                          "value": "dickinson"},
                         {"x": "Poems of Whitman"})


def test_matches_exists():
    print("=== _matches: exists ===")
    assert _matches({"field": "x", "op": "exists"}, {"x": 1})
    assert not _matches({"field": "x", "op": "exists"}, {})


def test_matches_all_of():
    print("=== _matches: all_of ===")
    cond = {"all_of": [
        {"field": "a", "op": "eq", "value": 1},
        {"field": "b", "op": "eq", "value": 2},
    ]}
    assert _matches(cond, {"a": 1, "b": 2})
    assert not _matches(cond, {"a": 1, "b": 3})


def test_matches_any_of():
    print("=== _matches: any_of ===")
    cond = {"any_of": [
        {"field": "a", "op": "eq", "value": 1},
        {"field": "b", "op": "eq", "value": 2},
    ]}
    assert _matches(cond, {"a": 1, "b": 999})
    assert _matches(cond, {"a": 999, "b": 2})
    assert not _matches(cond, {"a": 0, "b": 0})


def test_matches_not():
    print("=== _matches: not ===")
    cond = {"not": {"field": "a", "op": "eq", "value": 1}}
    assert _matches(cond, {"a": 2})
    assert not _matches(cond, {"a": 1})


def test_matches_nested_field():
    print("=== _matches: nested field path ===")
    assert _matches(
        {"field": "outer.inner", "op": "eq", "value": 5},
        {"outer": {"inner": 5}})
    assert not _matches(
        {"field": "outer.inner", "op": "eq", "value": 5},
        {"outer": {"inner": 6}})


# =====================================================================
# Evaluator — policy application
# =====================================================================

def test_evaluate_policy_default_when_no_match():
    print("=== evaluate_policy: default when no clause matches ===")
    policy, _, _ = _make_v1()
    fired, outcome = evaluate_policy(policy, {"x": 999})
    assert fired is None
    assert outcome == "reject"


def test_evaluate_policy_first_matching_fires():
    print("=== evaluate_policy: first matching clause fires ===")
    author = create_identity("A")
    kp = KeyPair.generate()
    policy = sign_policy(
        "p", 1,
        clauses=[
            _make_clause("c1", "x", "eq", 1, "first"),
            _make_clause("c2", "x", "eq", 1, "second"),
        ],
        default_outcome="reject",
        author=author, author_kp=kp,
    )
    fired, outcome = evaluate_policy(policy, {"x": 1})
    assert fired == "c1"
    assert outcome == "first"


def test_evaluate_policy_deterministic():
    print("=== evaluate_policy: deterministic ===")
    policy, _, _ = _make_v1()
    r1 = evaluate_policy(policy, {"x": 1})
    r2 = evaluate_policy(policy, {"x": 1})
    assert r1 == r2


# =====================================================================
# Unit construction
# =====================================================================

def test_unit_construction():
    print("=== InstitutionalUnit: construction verifies policy ===")
    policy, _, _ = _make_v1()
    unit, unit_kp = _make_unit(policy)
    assert unit.current_policy.policy_hash() == \
        policy.policy_hash()


def test_unit_rejects_bad_policy_signature():
    print("=== Unit: rejects bad policy signature ===")
    policy, author, _ = _make_v1()
    # Tamper with policy content
    tampered = PolicyText(
        policy_id=policy.policy_id,
        version=policy.version,
        clauses=policy.clauses,
        default_outcome="accept",  # was reject
        author_token=policy.author_token,
        author_public_key=policy.author_public_key,
        author_signature=policy.author_signature)
    with pytest.raises(ValueError):
        InstitutionalUnit(
            "world:u", "U", unit_kp=KeyPair.generate(),
            initial_policy=tampered)


def test_unit_is_wcp_world():
    print("=== Unit: passes WCP/0.1 conformance ===")
    from wcp_conformance import run_conformance
    unit, _ = _make_unit()
    assert run_conformance(unit)["passed"]


# =====================================================================
# Evaluate and ruling
# =====================================================================

def test_evaluate_returns_signed_ruling():
    print("=== evaluate: returns signed Ruling ===")
    unit, unit_kp = _make_unit()
    r = unit.evaluate({"x": 1})
    assert isinstance(r, Ruling)
    assert verify_ruling(r, unit_kp.public_key_hex())
    assert r.policy_hash == unit.current_policy.policy_hash()
    assert r.fired_clause_id == "c1"
    assert r.outcome == "accept"


def test_ruling_records_policy_version():
    print("=== Ruling: records policy_version and evaluator ===")
    unit, _ = _make_unit()
    r = unit.evaluate({"x": 1})
    assert r.policy_version == 1
    assert r.evaluator_version == EVALUATOR_VERSION


def test_different_facts_different_ruling():
    print("=== evaluate: different facts → different outcome ===")
    unit, _ = _make_unit()
    r1 = unit.evaluate({"x": 1})
    r2 = unit.evaluate({"x": 2})
    assert r1.outcome == "accept"
    assert r2.outcome == "reject"
    assert r1.facts_hash != r2.facts_hash


def test_same_facts_same_ruling_content():
    print("=== evaluate: same facts → same fired clause and outcome ===")
    unit, _ = _make_unit()
    r1 = unit.evaluate({"x": 1})
    r2 = unit.evaluate({"x": 1})
    assert r1.fired_clause_id == r2.fired_clause_id
    assert r1.outcome == r2.outcome
    assert r1.facts_hash == r2.facts_hash
    assert r1.policy_hash == r2.policy_hash


def test_ruling_wrong_key_rejected():
    print("=== verify_ruling: wrong key → False ===")
    unit, _ = _make_unit()
    r = unit.evaluate({"x": 1})
    wrong = KeyPair.generate()
    assert not verify_ruling(r, wrong.public_key_hex())


def test_ruling_tampered_rejected():
    print("=== verify_ruling: tampered → False ===")
    unit, unit_kp = _make_unit()
    r = unit.evaluate({"x": 1})
    tampered = Ruling(
        unit_id=r.unit_id,
        unit_public_key=r.unit_public_key,
        policy_hash=r.policy_hash,
        policy_version=r.policy_version,
        facts_hash=r.facts_hash,
        fired_clause_id=r.fired_clause_id,
        outcome="reject",  # flipped
        evaluator_version=r.evaluator_version,
        timestamp=r.timestamp,
        signature=r.signature)
    assert not verify_ruling(tampered, unit_kp.public_key_hex())


# =====================================================================
# Amendment
# =====================================================================

def test_amend_succeeds():
    print("=== amend: valid new version accepted ===")
    unit, unit_kp = _make_unit()
    # Need the same author for the amendment
    author = create_identity("Alice")
    # Use the SAME author key as the initial policy
    # (the initial policy's author_public_key must match)
    # We need to re-create the unit with a known author_kp
    author_kp = KeyPair.generate()
    v1 = sign_policy("p", 1,
                     [_make_clause(clause_id="c1")],
                     "reject", author, author_kp)
    unit2 = InstitutionalUnit(
        "world:u", "U", KeyPair.generate(), v1)
    v2 = sign_policy("p", 2,
                     [_make_clause(clause_id="c2",
                                     outcome="review")],
                     "reject", author, author_kp)
    amendment = unit2.amend(v2)
    assert isinstance(amendment, Amendment)
    assert verify_amendment(amendment,
                             unit2._unit_kp.public_key_hex())
    assert unit2.current_policy.version == 2


def test_amend_rejects_version_not_increasing():
    print("=== amend: version must increase ===")
    author = create_identity("Alice")
    author_kp = KeyPair.generate()
    v1 = sign_policy("p", 1, [_make_clause()],
                     "reject", author, author_kp)
    unit = InstitutionalUnit(
        "world:u", "U", KeyPair.generate(), v1)
    v1_again = sign_policy("p", 1, [_make_clause()],
                            "accept", author, author_kp)
    with pytest.raises(ValueError):
        unit.amend(v1_again)


def test_amend_rejects_different_policy_id():
    print("=== amend: policy_id must match ===")
    author = create_identity("Alice")
    author_kp = KeyPair.generate()
    v1 = sign_policy("p", 1, [_make_clause()],
                     "reject", author, author_kp)
    unit = InstitutionalUnit(
        "world:u", "U", KeyPair.generate(), v1)
    v2 = sign_policy("q", 2, [_make_clause()],
                     "reject", author, author_kp)
    with pytest.raises(ValueError):
        unit.amend(v2)


def test_amend_rejects_different_author():
    print("=== amend: author must match ===")
    alice = create_identity("Alice")
    alice_kp = KeyPair.generate()
    bob = create_identity("Bob")
    bob_kp = KeyPair.generate()
    v1 = sign_policy("p", 1, [_make_clause()],
                     "reject", alice, alice_kp)
    unit = InstitutionalUnit(
        "world:u", "U", KeyPair.generate(), v1)
    # Bob tries to amend
    v2 = sign_policy("p", 2, [_make_clause()],
                     "reject", bob, bob_kp)
    with pytest.raises(ValueError):
        unit.amend(v2)


def test_amend_rejects_bad_signature():
    print("=== amend: bad signature rejected ===")
    author = create_identity("Alice")
    author_kp = KeyPair.generate()
    v1 = sign_policy("p", 1, [_make_clause()],
                     "reject", author, author_kp)
    unit = InstitutionalUnit(
        "world:u", "U", KeyPair.generate(), v1)
    # Craft a v2 with a bad signature
    v2 = sign_policy("p", 2, [_make_clause()],
                     "reject", author, author_kp)
    tampered = PolicyText(
        policy_id=v2.policy_id, version=v2.version,
        clauses=v2.clauses,
        default_outcome=v2.default_outcome,
        author_token=v2.author_token,
        author_public_key=v2.author_public_key,
        author_signature="00" * 64)
    with pytest.raises(ValueError):
        unit.amend(tampered)


def test_policy_history_grows():
    print("=== amend: policy_history is append-only ===")
    author = create_identity("Alice")
    author_kp = KeyPair.generate()
    v1 = sign_policy("p", 1, [_make_clause()],
                     "reject", author, author_kp)
    unit = InstitutionalUnit(
        "world:u", "U", KeyPair.generate(), v1)
    assert len(unit.policy_history) == 1
    v2 = sign_policy("p", 2, [_make_clause()],
                     "reject", author, author_kp)
    unit.amend(v2)
    assert len(unit.policy_history) == 2
    assert unit.policy_history[0].version == 1
    assert unit.policy_history[1].version == 2


def test_policy_by_hash_finds_old_version():
    print("=== policy_by_hash: finds old versions ===")
    author = create_identity("Alice")
    author_kp = KeyPair.generate()
    v1 = sign_policy("p", 1, [_make_clause()],
                     "reject", author, author_kp)
    unit = InstitutionalUnit(
        "world:u", "U", KeyPair.generate(), v1)
    v1_hash = v1.policy_hash()
    v2 = sign_policy("p", 2, [_make_clause()],
                     "reject", author, author_kp)
    unit.amend(v2)
    assert unit.policy_by_hash(v1_hash).version == 1


# =====================================================================
# Reproducibility — the distinguishing claim
# =====================================================================

def test_reproduce_ruling_happy():
    print("=== reproduce_ruling: third party reproduces ===")
    unit, _ = _make_unit()
    facts = {"x": 1}
    r = unit.evaluate(facts)
    policy = unit.current_policy
    ok, reason = reproduce_ruling(r, policy, facts)
    assert ok


def test_reproduce_ruling_facts_mismatch():
    print("=== reproduce_ruling: facts mismatch → False ===")
    unit, _ = _make_unit()
    r = unit.evaluate({"x": 1})
    policy = unit.current_policy
    ok, reason = reproduce_ruling(r, policy, {"x": 2})
    assert not ok
    assert "facts_hash" in reason


def test_reproduce_ruling_policy_mismatch():
    print("=== reproduce_ruling: policy mismatch → False ===")
    unit, _ = _make_unit()
    facts = {"x": 1}
    r = unit.evaluate(facts)
    # Different policy
    other_policy, _, _ = _make_v1()
    ok, reason = reproduce_ruling(r, other_policy, facts)
    assert not ok
    assert "policy_hash" in reason


def test_reproduce_ruling_tampered_outcome():
    print("=== reproduce_ruling: tampered outcome → False ===")
    unit, unit_kp = _make_unit()
    facts = {"x": 1}
    r = unit.evaluate(facts)
    tampered = Ruling(
        unit_id=r.unit_id,
        unit_public_key=r.unit_public_key,
        policy_hash=r.policy_hash,
        policy_version=r.policy_version,
        facts_hash=r.facts_hash,
        fired_clause_id=r.fired_clause_id,
        outcome="reject",  # flipped
        evaluator_version=r.evaluator_version,
        timestamp=r.timestamp,
        signature=r.signature)
    policy = unit.current_policy
    ok, reason = reproduce_ruling(tampered, policy, facts)
    assert not ok
    assert "outcome" in reason


# =====================================================================
# WCP act handler
# =====================================================================

def test_act_evaluate_returns_ack():
    print("=== act('evaluate'): Ack, ruling logged ===")
    unit, _ = _make_unit()
    r = unit.act(Act(actor_token="ext", type="evaluate",
                      payload={"facts": {"x": 1}}))
    assert isinstance(r, Ack)
    kinds = [e.kind for e in unit.log_since(None)]
    assert "ruling" in kinds


def test_act_evaluate_rejects_bad_payload():
    print("=== act('evaluate'): bad payload → Refusal ===")
    unit, _ = _make_unit()
    for bad in (None, "not a dict", [], 5):
        r = unit.act(Act(actor_token="ext", type="evaluate",
                          payload={"facts": bad}))
        assert isinstance(r, Refusal)


def test_act_amend_via_act():
    print("=== act('amend'): works via payload ===")
    author = create_identity("Alice")
    author_kp = KeyPair.generate()
    v1 = sign_policy("p", 1, [_make_clause()],
                     "reject", author, author_kp)
    unit = InstitutionalUnit(
        "world:u", "U", KeyPair.generate(), v1)
    v2 = sign_policy("p", 2, [_make_clause(outcome="review")],
                     "reject", author, author_kp)
    r = unit.act(Act(actor_token="ext", type="amend",
                      payload={"new_policy": v2.to_dict()}))
    assert isinstance(r, Ack)


def test_act_unknown_type_refused():
    print("=== act: unknown type → Refusal ===")
    unit, _ = _make_unit()
    for bad in ("fire", "restart", "bogus"):
        r = unit.act(Act(actor_token="ext", type=bad,
                          payload={}))
        assert isinstance(r, Refusal)


def test_act_never_raises():
    print("=== act: never raises on bad payloads ===")
    unit, _ = _make_unit()
    for payload in (None, {}, [], "bad", {"facts": "x"}):
        r = unit.act(Act(actor_token="ext", type="evaluate",
                          payload=payload or {}))
        assert isinstance(r, (Ack, Refusal))


# =====================================================================
# Structural claims
# =====================================================================

def test_unit_has_policy_attrs():
    print("=== Unit: has policy attrs (unique to C50) ===")
    unit, _ = _make_unit()
    assert hasattr(unit, "_current_policy")
    assert hasattr(unit, "_policy_history")
    assert hasattr(unit, "_unit_kp")


def test_unit_has_no_other_arch_attrs():
    print("=== Unit: no other architecture's distinguishing attrs ===")
    unit, _ = _make_unit()
    for attr in ("_model", "_intent_queue"):      # C41
        assert not hasattr(unit, attr), attr
    for attr in ("_inputs", "_threshold"):        # C42
        assert not hasattr(unit, attr), attr
    for attr in ("_env_stream", "_position"):     # C43
        assert not hasattr(unit, attr), attr
    for attr in ("_decision_rule", "_members"):   # C44
        assert not hasattr(unit, attr), attr
    for attr in ("_target", "_state"):            # C47
        assert not hasattr(unit, attr), attr


def test_all_six_architectures_same_substrate():
    """The substrate supports all six. Conformance is
    architecture-agnostic."""
    print("=== Six architectures, one substrate ===")
    from wcp_conformance import run_conformance
    from multiverse_c1 import create_identity
    from multiverse_c13 import KeyPair
    from multiverse_c41 import Arm
    from multiverse_c42 import (
        RelayUnit, Stream, SignalWorld,
    )
    from multiverse_c43 import SwarmUnit
    from multiverse_c44 import TriumvirateMember
    from multiverse_c47 import AutonomicUnit

    class StubModel:
        def generate(self, prompt): return "x"

    arm = Arm(
        name="a", world_id="world:a", dag_id="dag:a",
        model_backend=StubModel(),
        arm_report_kp=KeyPair.generate(),
        arm_report_identity=create_identity("r"),
        arm_dag_kp=KeyPair.generate(),
        arm_dag_identity=create_identity("d"))
    stim = SignalWorld("world:s", "S")
    neuron = RelayUnit(
        "world:n", "N", [Stream(stim)], threshold=1.0)
    env = SignalWorld("world:e", "E")
    swarm = SwarmUnit(
        entity_id="world:u", name="U",
        env_stream=Stream(env),
        initial_position=(0, 0), seed=0,
        sample_probability=0.0)
    member = TriumvirateMember(
        entity_id="m", name="M",
        member_kp=KeyPair.generate(),
        decision_rule=lambda p: "yea")
    autonomic = AutonomicUnit(
        "world:auto", "Auto", target=22.0,
        initial_state=20.0)
    # C50 unit
    policy, _, _ = _make_v1()
    institutional = InstitutionalUnit(
        "world:inst", "Inst",
        KeyPair.generate(), policy)

    for name, e in [
        ("C41 arm", arm),
        ("C42 relay", neuron),
        ("C43 swarm", swarm),
        ("C44 council member", member),
        ("C47 autonomic", autonomic),
        ("C50 institutional", institutional),
    ]:
        assert run_conformance(e)["passed"], name
        print(f"  ✓ {name}")


# =====================================================================
# JSON roundtrips
# =====================================================================

def test_policy_json_roundtrip():
    print("=== PolicyText: JSON roundtrip ===")
    policy, _, author_kp = _make_v1()
    wire = json.dumps(policy.to_dict())
    revived = PolicyText.from_dict(json.loads(wire))
    assert revived.canonical_payload() == \
        policy.canonical_payload()
    assert verify_policy_signature(
        revived, author_kp.public_key_hex())


def test_ruling_json_roundtrip():
    print("=== Ruling: JSON roundtrip ===")
    unit, unit_kp = _make_unit()
    r = unit.evaluate({"x": 1})
    wire = json.dumps(r.to_dict())
    revived = Ruling.from_dict(json.loads(wire))
    assert revived.canonical_payload() == r.canonical_payload()
    assert verify_ruling(revived, unit_kp.public_key_hex())


def test_amendment_json_roundtrip():
    print("=== Amendment: JSON roundtrip ===")
    author = create_identity("Alice")
    author_kp = KeyPair.generate()
    v1 = sign_policy("p", 1, [_make_clause()],
                     "reject", author, author_kp)
    unit = InstitutionalUnit(
        "world:u", "U", KeyPair.generate(), v1)
    v2 = sign_policy("p", 2, [_make_clause()],
                     "reject", author, author_kp)
    amendment = unit.amend(v2)
    wire = json.dumps(amendment.to_dict())
    revived = Amendment.from_dict(json.loads(wire))
    assert revived.canonical_payload() == \
        amendment.canonical_payload()


# =====================================================================
# Demo
# =====================================================================

def test_demo(tmp_path):
    print("=== Demo: poetry gate, v1→v2, reproduction ===")
    audit = demo(artifact_dir=str(tmp_path))
    # v1: everything poetry accepted
    assert audit["v1_rulings"]["dickinson"]["outcome"] == "accept"
    assert audit["v1_rulings"]["whitman"]["outcome"] == "accept"
    assert audit["v1_rulings"]["prose"]["outcome"] == "reject"
    # v2: Dickinson accepted; Whitman reviewed; prose rejected
    assert audit["v2_rulings"]["dickinson"]["outcome"] == "accept"
    assert audit["v2_rulings"]["whitman"]["outcome"] == "review"
    assert audit["v2_rulings"]["prose"]["outcome"] == "reject"
    # Both v1 and v2 hashes present and different
    assert audit["v1_hash"] != audit["v2_hash"]
    # Reproductions both succeed
    assert audit["reproductions"]["v1_whitman"][0] is True
    assert audit["reproductions"]["v2_whitman"][0] is True
    assert (tmp_path / "institutional_demo.json").exists()


if __name__ == "__main__":
    test_clause_validates_fields()
    test_clause_json_roundtrip()
    test_policy_requires_at_least_one_clause()
    test_policy_rejects_duplicate_clause_ids()
    test_policy_rejects_zero_version()
    test_policy_signature_verifies()
    test_policy_signature_wrong_key()
    test_policy_signature_tampered()
    test_policy_hash_deterministic()
    test_matches_eq()
    test_matches_ne()
    test_matches_gt_lt_ge_le()
    test_matches_in_contains()
    test_matches_exists()
    test_matches_all_of()
    test_matches_any_of()
    test_matches_not()
    test_matches_nested_field()
    test_evaluate_policy_default_when_no_match()
    test_evaluate_policy_first_matching_fires()
    test_evaluate_policy_deterministic()
    test_unit_construction()
    test_unit_rejects_bad_policy_signature()
    test_unit_is_wcp_world()
    test_evaluate_returns_signed_ruling()
    test_ruling_records_policy_version()
    test_different_facts_different_ruling()
    test_same_facts_same_ruling_content()
    test_ruling_wrong_key_rejected()
    test_ruling_tampered_rejected()
    test_amend_succeeds()
    test_amend_rejects_version_not_increasing()
    test_amend_rejects_different_policy_id()
    test_amend_rejects_different_author()
    test_amend_rejects_bad_signature()
    test_policy_history_grows()
    test_policy_by_hash_finds_old_version()
    test_reproduce_ruling_happy()
    test_reproduce_ruling_facts_mismatch()
    test_reproduce_ruling_policy_mismatch()
    test_reproduce_ruling_tampered_outcome()
    test_act_evaluate_returns_ack()
    test_act_evaluate_rejects_bad_payload()
    test_act_amend_via_act()
    test_act_unknown_type_refused()
    test_act_never_raises()
    test_unit_has_policy_attrs()
    test_unit_has_no_other_arch_attrs()
    test_all_six_architectures_same_substrate()
    test_policy_json_roundtrip()
    test_ruling_json_roundtrip()
    test_amendment_json_roundtrip()
    with tempfile.TemporaryDirectory() as tmp:
        test_demo(Path(tmp))

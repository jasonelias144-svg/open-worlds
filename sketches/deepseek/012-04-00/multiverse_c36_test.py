# multiverse_c36_test.py
import json
import tempfile
from pathlib import Path

import pytest

from multiverse_c1 import create_identity, Identity
from multiverse_c13 import HAS_CRYPTO, KeyPair, canonical_bytes
from multiverse_c15 import PassportV2, PassportEntry
from multiverse_c36 import (
    TokenBinding, PersonIdentity, BindingVerdict,
    PersonVerificationReport, PersonPassport, PersonPassportReport,
    create_person, bind_token,
    verify_binding, verify_person, verify_person_passport,
    demo,
)


pytestmark = pytest.mark.skipif(
    not HAS_CRYPTO, reason="cryptography not installed")


# =====================================================================
# Construction
# =====================================================================

def test_create_person():
    print("=== create_person: empty identity + keypair ===")
    person, kp = create_person("Aria")
    assert person.person.name == "Aria"
    assert len(person.person.token) == 32
    assert len(person.person_public_key) == 64
    assert person.person_public_key == kp.public_key_hex()
    assert person.bindings == ()


def test_bind_token_happy():
    print("=== bind_token: adds a dual-signed binding ===")
    person, kp = create_person("Aria")
    token_identity = create_identity("Aria@poetry")
    holder_kp = KeyPair.generate()
    new_person, binding = bind_token(
        person, kp,
        token_identity.token, token_identity.name, holder_kp)
    assert len(new_person.bindings) == 1
    assert new_person.bindings[0] is binding
    assert binding.token == token_identity.token
    assert binding.name == "Aria@poetry"
    assert binding.holder_public_key == holder_kp.public_key_hex()
    # The original person is unchanged
    assert len(person.bindings) == 0


def test_bind_token_rejects_wrong_person_kp():
    print("=== bind_token: rejects mismatched person key ===")
    person, kp = create_person("Aria")
    wrong_kp = KeyPair.generate()
    token_identity = create_identity("t")
    holder_kp = KeyPair.generate()
    with pytest.raises(ValueError):
        bind_token(person, wrong_kp,
                    token_identity.token, token_identity.name,
                    holder_kp)


def test_bind_token_rejects_duplicate():
    print("=== bind_token: rejects duplicate token ===")
    person, kp = create_person("Aria")
    token_identity = create_identity("t")
    holder_kp = KeyPair.generate()
    person, _ = bind_token(
        person, kp, token_identity.token, token_identity.name, holder_kp)
    with pytest.raises(ValueError):
        bind_token(
            person, kp, token_identity.token, "different-name",
            holder_kp)


def test_bind_token_rejects_empty_fields():
    print("=== bind_token: rejects empty token or name ===")
    person, kp = create_person("Aria")
    holder_kp = KeyPair.generate()
    with pytest.raises(ValueError):
        bind_token(person, kp, "", "name", holder_kp)
    with pytest.raises(ValueError):
        bind_token(person, kp, "token", "", holder_kp)


# =====================================================================
# Binding verification
# =====================================================================

def test_verify_binding_happy():
    print("=== verify_binding: both sigs valid ===")
    person, kp = create_person("Aria")
    holder_kp = KeyPair.generate()
    _, binding = bind_token(
        person, kp, "tok-1", "Aria@poetry", holder_kp)
    v = verify_binding(binding, person.person_public_key)
    assert v.valid
    assert v.person_sig_valid
    assert v.holder_sig_valid


def test_verify_binding_forged_person_sig():
    print("=== verify_binding: forged person signature ===")
    person, kp = create_person("Aria")
    holder_kp = KeyPair.generate()
    _, binding = bind_token(
        person, kp, "tok-1", "Aria@poetry", holder_kp)
    attacker_kp = KeyPair.generate()
    # Forge person_signature with attacker's key
    payload = binding.canonical_payload()
    forged = TokenBinding(
        token=binding.token, name=binding.name,
        holder_public_key=binding.holder_public_key,
        person_signature=attacker_kp.sign(payload).hex(),
        holder_signature=binding.holder_signature,
    )
    v = verify_binding(forged, person.person_public_key)
    assert not v.valid
    assert not v.person_sig_valid
    assert v.holder_sig_valid  # holder's is real


def test_verify_binding_forged_holder_sig():
    print("=== verify_binding: forged holder signature ===")
    person, kp = create_person("Aria")
    holder_kp = KeyPair.generate()
    _, binding = bind_token(
        person, kp, "tok-1", "Aria@poetry", holder_kp)
    attacker_kp = KeyPair.generate()
    payload = binding.canonical_payload()
    # Attacker substitutes their own holder key but signs with person key
    forged = TokenBinding(
        token=binding.token, name=binding.name,
        holder_public_key=attacker_kp.public_key_hex(),
        person_signature=kp.sign(payload).hex(),  # irrelevant, payload differs
        holder_signature=attacker_kp.sign(payload).hex(),
    )
    # person_public_key differs between payloads; verification should fail
    v = verify_binding(forged, person.person_public_key)
    assert not v.valid


def test_verify_binding_tampered_token():
    print("=== verify_binding: tampered token breaks both sigs ===")
    person, kp = create_person("Aria")
    holder_kp = KeyPair.generate()
    _, binding = bind_token(
        person, kp, "tok-1", "Aria@poetry", holder_kp)
    tampered = TokenBinding(
        token="different-token",
        name=binding.name,
        holder_public_key=binding.holder_public_key,
        person_signature=binding.person_signature,
        holder_signature=binding.holder_signature,
    )
    v = verify_binding(tampered, person.person_public_key)
    assert not v.valid
    assert not v.person_sig_valid
    assert not v.holder_sig_valid


# =====================================================================
# Person verification
# =====================================================================

def test_verify_person_all_valid():
    print("=== verify_person: multiple valid bindings ===")
    person, kp = create_person("Aria")
    for i, name in enumerate(["Aria@poetry", "Aria@chem", "Aria@reg"]):
        t = create_identity(name)
        person, _ = bind_token(
            person, kp, t.token, name, KeyPair.generate())
    report = verify_person(person)
    assert report.all_valid
    assert len(report.binding_verdicts) == 3


def test_verify_person_one_bad_binding():
    print("=== verify_person: one bad binding → all_valid False ===")
    person, kp = create_person("Aria")
    t1 = create_identity("t1"); t2 = create_identity("t2")
    person, _ = bind_token(
        person, kp, t1.token, "t1", KeyPair.generate())
    person, _ = bind_token(
        person, kp, t2.token, "t2", KeyPair.generate())
    # Tamper with the second binding
    bad_binding = TokenBinding(
        token=person.bindings[1].token,
        name="tampered",
        holder_public_key=person.bindings[1].holder_public_key,
        person_signature=person.bindings[1].person_signature,
        holder_signature=person.bindings[1].holder_signature,
    )
    tampered = PersonIdentity(
        person=person.person,
        person_public_key=person.person_public_key,
        bindings=(person.bindings[0], bad_binding),
    )
    report = verify_person(tampered)
    assert not report.all_valid
    assert report.binding_verdicts[0].valid
    assert not report.binding_verdicts[1].valid


def test_person_rejects_duplicate_tokens():
    print("=== PersonIdentity rejects duplicate binding tokens ===")
    with pytest.raises(ValueError):
        person, kp = create_person("Aria")
        holder_kp = KeyPair.generate()
        _, binding = bind_token(
            person, kp, "t", "n", holder_kp)
        # Craft a PersonIdentity with the same binding twice
        PersonIdentity(
            person=Identity(token="x", name="X"),
            person_public_key="aa" * 32,
            bindings=(binding, binding),
        )


# =====================================================================
# PersonPassport
# =====================================================================

def _fake_passport(token: str, name: str) -> PassportV2:
    return PassportV2(
        identity=Identity(token=token, name=name),
        entries=(),
    )


def test_person_passport_happy():
    print("=== PersonPassport: aggregates correctly ===")
    person, kp = create_person("Aria")
    t = create_identity("Aria@poetry")
    person, binding = bind_token(
        person, kp, t.token, t.name, KeyPair.generate())
    passport = _fake_passport(binding.token, binding.name)
    pp = PersonPassport(person=person, passports=(passport,))
    assert pp.passport_for(binding.token) is passport
    assert pp.passport_for("unknown") is None


def test_verify_person_passport_happy():
    """The full verification: all bindings valid, all passports
    verified (trivially, since they have no entries), no orphans."""
    print("=== verify_person_passport: happy path ===")
    person, kp = create_person("Aria")
    t = create_identity("Aria@poetry")
    person, binding = bind_token(
        person, kp, t.token, t.name, KeyPair.generate())
    passport = _fake_passport(binding.token, binding.name)
    pp = PersonPassport(person=person, passports=(passport,))
    resolver = lambda eid: None  # no world keys needed
    report = verify_person_passport(pp, resolver)
    assert report.all_valid
    assert len(report.passport_reports) == 1
    assert not report.orphan_bindings
    assert not report.orphan_passports


def test_verify_person_passport_orphan_binding():
    print("=== verify_person_passport: orphan binding flagged ===")
    person, kp = create_person("Aria")
    t = create_identity("t")
    person, _ = bind_token(
        person, kp, t.token, t.name, KeyPair.generate())
    # No passport provided
    pp = PersonPassport(person=person, passports=())
    resolver = lambda eid: None
    report = verify_person_passport(pp, resolver)
    assert not report.all_valid
    assert len(report.orphan_bindings) == 1


def test_verify_person_passport_orphan_passport():
    print("=== verify_person_passport: orphan passport flagged ===")
    person, kp = create_person("Aria")  # no bindings
    orphan_passport = _fake_passport("some-token", "X")
    pp = PersonPassport(person=person, passports=(orphan_passport,))
    resolver = lambda eid: None
    report = verify_person_passport(pp, resolver)
    assert not report.all_valid
    assert len(report.orphan_passports) == 1


def test_verify_person_passport_forged_binding():
    print("=== verify_person_passport: forged binding → all_valid False ===")
    person, kp = create_person("Aria")
    t = create_identity("t")
    holder_kp = KeyPair.generate()
    person, binding = bind_token(
        person, kp, t.token, t.name, holder_kp)
    # Craft a forged binding for the same token
    attacker_kp = KeyPair.generate()
    payload = canonical_bytes({
        "kind": "token_binding",
        "token": binding.token, "name": binding.name,
        "holder_public_key": binding.holder_public_key,
    })
    forged = TokenBinding(
        token=binding.token, name=binding.name,
        holder_public_key=binding.holder_public_key,
        person_signature=attacker_kp.sign(payload).hex(),
        holder_signature=binding.holder_signature,
    )
    forged_person = PersonIdentity(
        person=person.person,
        person_public_key=person.person_public_key,
        bindings=(forged,),
    )
    pp = PersonPassport(
        person=forged_person,
        passports=(_fake_passport(binding.token, binding.name),),
    )
    resolver = lambda eid: None
    report = verify_person_passport(pp, resolver)
    assert not report.all_valid
    assert not report.person_report.all_valid


# =====================================================================
# JSON roundtrips
# =====================================================================

def test_token_binding_json_roundtrip():
    print("=== TokenBinding JSON roundtrip ===")
    person, kp = create_person("Aria")
    holder_kp = KeyPair.generate()
    _, binding = bind_token(person, kp, "t", "n", holder_kp)
    wire = json.dumps(binding.to_dict())
    revived = TokenBinding.from_dict(json.loads(wire))
    assert revived.canonical_payload() == binding.canonical_payload()
    assert revived.binding_hash() == binding.binding_hash()


def test_person_identity_json_roundtrip():
    print("=== PersonIdentity JSON roundtrip ===")
    person, kp = create_person("Aria")
    for name in ("p", "q", "r"):
        t = create_identity(name)
        person, _ = bind_token(
            person, kp, t.token, name, KeyPair.generate())
    wire = json.dumps(person.to_dict())
    revived = PersonIdentity.from_dict(json.loads(wire))
    assert len(revived.bindings) == 3
    assert revived.person.token == person.person.token
    assert revived.person_public_key == person.person_public_key


def test_person_passport_json_roundtrip():
    print("=== PersonPassport JSON roundtrip ===")
    person, kp = create_person("Aria")
    t = create_identity("t")
    person, binding = bind_token(
        person, kp, t.token, t.name, KeyPair.generate())
    pp = PersonPassport(
        person=person,
        passports=(_fake_passport(binding.token, binding.name),),
    )
    wire = json.dumps(pp.to_dict())
    revived = PersonPassport.from_dict(json.loads(wire))
    assert revived.person.person.token == person.person.token
    assert len(revived.passports) == 1


# =====================================================================
# Never raises
# =====================================================================

def test_verifiers_never_raise():
    print("=== Verifiers never raise on bad input ===")
    assert not verify_binding(None, "aa" * 32).valid
    assert not verify_binding("not a binding", "aa" * 32).valid
    # verify_person on non-PersonIdentity
    report = verify_person(None)
    assert not report.all_valid
    # verify_person_passport on bad input
    report = verify_person_passport(None, lambda e: None)
    assert not report.all_valid


# =====================================================================
# Demo
# =====================================================================

def test_demo(tmp_path):
    print("=== Demo: Aria, three embodiments, forged binding rejected ===")
    audit = demo(artifact_dir=str(tmp_path))
    assert audit["all_valid"] is True
    assert len(audit["presences"]) == 3
    assert audit["forged_binding"]["valid"] is False
    assert audit["forged_binding"]["person_sig_valid"] is False
    assert audit["forged_binding"]["holder_sig_valid"] is False
    assert (tmp_path / "person_identity_demo.json").exists()


if __name__ == "__main__":
    test_create_person()
    test_bind_token_happy()
    test_bind_token_rejects_wrong_person_kp()
    test_bind_token_rejects_duplicate()
    test_bind_token_rejects_empty_fields()
    test_verify_binding_happy()
    test_verify_binding_forged_person_sig()
    test_verify_binding_forged_holder_sig()
    test_verify_binding_tampered_token()
    test_verify_person_all_valid()
    test_verify_person_one_bad_binding()
    test_person_rejects_duplicate_tokens()
    test_person_passport_happy()
    test_verify_person_passport_happy()
    test_verify_person_passport_orphan_binding()
    test_verify_person_passport_orphan_passport()
    test_verify_person_passport_forged_binding()
    test_token_binding_json_roundtrip()
    test_person_identity_json_roundtrip()
    test_person_passport_json_roundtrip()
    test_verifiers_never_raise()
    with tempfile.TemporaryDirectory() as tmp:
        test_demo(Path(tmp))

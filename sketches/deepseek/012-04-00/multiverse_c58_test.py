import json
import tempfile
from pathlib import Path

import pytest

from multiverse_c1 import create_identity
from multiverse_c3 import Act, Ack, Refusal, Petition
from multiverse_c4 import PoetryWorld
from multiverse_c5 import ChemistryWorld
from multiverse_c13 import HAS_CRYPTO, KeyPair
from multiverse_c55 import WorldCurator
from multiverse_c57 import (
    ContractTerms, ContractRegistry, ContractNegotiator,
    sign_offer, sign_acceptance,
    sign_bilateral_revocation,
)
from multiverse_c58 import (
    ContractAwareMixin,
    ContractAwarePoetryWorld,
    ContractAwareChemistryWorld,
    demo,
    _now,
)


pytestmark = pytest.mark.skipif(
    not HAS_CRYPTO, reason="cryptography not installed")


# =====================================================================
# Helpers
# =====================================================================

def _make_poetry_world(name="poetry", registry=None,
                        require_citation=False):
    w = ContractAwarePoetryWorld(
        f"world:{name}", name,
        registry=registry,
        require_citation=require_citation)
    return w


def _make_chem_world(name="chem", registry=None,
                      require_citation=False):
    w = ContractAwareChemistryWorld(
        f"world:{name}", name,
        registry=registry,
        require_citation=require_citation)
    return w


def _admit(world, name="resident"):
    ident = create_identity(name)
    world.petition(Petition(
        petitioner_token=ident.token,
        petitioner_name=ident.name,
        passport_admissions=(),
        message="hi"))
    return ident


def _setup_established_contract(
    world_a, world_b, terms=None,
):
    """Returns (contract_id, kp_a, kp_b, offer, acceptance)."""
    if terms is None:
        terms = ContractTerms(content={"kind": "test"})
    kp_a = KeyPair.generate()
    kp_b = KeyPair.generate()
    offer = sign_offer(
        world_a.manifest().entity_id, kp_a,
        world_b.manifest().entity_id, terms)
    acceptance = sign_acceptance(
        world_b.manifest().entity_id, kp_b, offer)
    world_a.register_contract_offer(offer)
    world_a.register_contract_acceptance(acceptance)
    world_b.register_contract_offer(offer)
    world_b.register_contract_acceptance(acceptance)
    return (terms.terms_hash(), kp_a, kp_b, offer, acceptance)


def _poem_turn(token, cites=None, cites_world=None):
    payload = {
        "acknowledgment": "(seed)",
        "proposal": "a line",
        "invitation": "?",
        "holds_open": True,
    }
    if cites is not None:
        payload["cites_contract"] = cites
    if cites_world is not None:
        payload["cites_world"] = cites_world
    return Act(actor_token=token, type="poem.turn",
                payload=payload)


def _chem_act(token, cites=None, cites_world=None):
    payload = {
        "substrates": [{"formula": "H2", "count": 2},
                        {"formula": "O2", "count": 1}],
        "products": [{"formula": "H2O", "count": 2}],
    }
    if cites is not None:
        payload["cites_contract"] = cites
    if cites_world is not None:
        payload["cites_world"] = cites_world
    return Act(actor_token=token, type="chemistry.react",
                payload=payload)


# =====================================================================
# Structural claims: base classes unchanged
# =====================================================================

def test_poetry_world_untouched():
    print("=== PoetryWorld: untouched by C58 ===")
    w = PoetryWorld("world:p", "P")
    assert not hasattr(w, "_contract_registry")
    assert not hasattr(w, "_require_citation")


def test_chemistry_world_untouched():
    print("=== ChemistryWorld: untouched by C58 ===")
    w = ChemistryWorld("world:c", "C")
    assert not hasattr(w, "_contract_registry")
    assert not hasattr(w, "_require_citation")


def test_contract_aware_poetry_has_mixin():
    print("=== ContractAwarePoetryWorld: is-a mixin ===")
    w = _make_poetry_world()
    assert isinstance(w, ContractAwareMixin)
    assert isinstance(w, PoetryWorld)
    assert hasattr(w, "_contract_registry")
    assert hasattr(w, "_require_citation")


def test_contract_aware_chemistry_has_mixin():
    print("=== ContractAwareChemistryWorld: is-a mixin ===")
    w = _make_chem_world()
    assert isinstance(w, ContractAwareMixin)
    assert isinstance(w, ChemistryWorld)


# =====================================================================
# Happy path
# =====================================================================

def test_poetry_accepts_valid_citation():
    print("=== Poetry: valid citation → accepted ===")
    w = _make_poetry_world()
    other = _make_poetry_world("other")
    cid, _, _, _, _ = _setup_established_contract(w, other)
    resident = _admit(w)
    r = w.act(_poem_turn(resident.token, cites=cid,
                          cites_world="world:other"))
    assert isinstance(r, Ack)


def test_chem_accepts_valid_citation():
    print("=== Chemistry: valid citation → accepted ===")
    w = _make_chem_world()
    other = _make_chem_world("other")
    cid, _, _, _, _ = _setup_established_contract(w, other)
    resident = _admit(w)
    r = w.act(_chem_act(resident.token, cites=cid,
                         cites_world="world:other"))
    assert isinstance(r, Ack)


def test_act_without_citation_accepted():
    print("=== Default: act without citation → accepted ===")
    w = _make_poetry_world()
    resident = _admit(w)
    r = w.act(_poem_turn(resident.token))  # no cites
    assert isinstance(r, Ack)


def test_citation_logged():
    print("=== Citation is logged when act accepted ===")
    w = _make_poetry_world()
    other = _make_poetry_world("other")
    cid, _, _, _, _ = _setup_established_contract(w, other)
    resident = _admit(w)
    w.act(_poem_turn(resident.token, cites=cid,
                      cites_world="world:other"))
    cited = [e for e in w.log_since(None)
             if e.kind == "contract_cited"]
    assert len(cited) == 1
    assert cited[0].data["cites_contract"] == cid
    assert cited[0].data["cites_world"] == "world:other"


# =====================================================================
# Refusals
# =====================================================================

def test_refuse_missing_when_required():
    print("=== require_citation=True: missing citation → refused ===")
    w = _make_poetry_world(require_citation=True)
    resident = _admit(w)
    r = w.act(_poem_turn(resident.token))
    assert isinstance(r, Refusal)
    assert "must cite" in r.reason


def test_refuse_pending():
    print("=== Pending contract → refused ===")
    w = _make_poetry_world()
    other = _make_poetry_world("other")
    # Register only the offer; no acceptance
    terms = ContractTerms(content={"kind": "pending"})
    offer = sign_offer(
        w.manifest().entity_id, KeyPair.generate(),
        other.manifest().entity_id, terms)
    w.register_contract_offer(offer)
    resident = _admit(w)
    r = w.act(_poem_turn(resident.token,
                          cites=terms.terms_hash(),
                          cites_world="world:other"))
    assert isinstance(r, Refusal)
    assert "pending" in r.reason


def test_refuse_revoked():
    print("=== Revoked contract → refused ===")
    w = _make_poetry_world()
    other = _make_poetry_world("other")
    cid, kp_a, kp_b, _, _ = _setup_established_contract(w, other)
    rev = sign_bilateral_revocation(
        contract_id=cid,
        world_a_id=w.manifest().entity_id,
        world_a_kp=kp_a,
        world_b_id=other.manifest().entity_id,
        world_b_kp=kp_b)
    w.register_contract_revocation(rev)
    resident = _admit(w)
    r = w.act(_poem_turn(resident.token, cites=cid,
                          cites_world="world:other"))
    assert isinstance(r, Refusal)
    assert "revoked" in r.reason


def test_refuse_not_found():
    print("=== Unknown contract → refused ===")
    w = _make_poetry_world()
    resident = _admit(w)
    fake_id = "00" * 32
    r = w.act(_poem_turn(resident.token, cites=fake_id))
    assert isinstance(r, Refusal)
    assert "not found" in r.reason


def test_refuse_bad_citation_format():
    print("=== Non-64-hex citation → refused ===")
    w = _make_poetry_world()
    resident = _admit(w)
    for bad in ("short", "not-hex-not-hex", "x" * 63, 123):
        r = w.act(_poem_turn(resident.token, cites=bad))
        assert isinstance(r, Refusal)


def test_refuse_wrong_counterparty():
    print("=== cites_world mismatch → refused ===")
    w = _make_poetry_world()
    other = _make_poetry_world("other")
    cid, _, _, _, _ = _setup_established_contract(w, other)
    resident = _admit(w)
    r = w.act(_poem_turn(
        resident.token, cites=cid,
        cites_world="world:someone-else"))
    assert isinstance(r, Refusal)
    assert "cites_world" in r.reason


def test_refuse_contract_not_with_this_world():
    print("=== Contract doesn't involve this world → refused ===")
    w = _make_poetry_world()
    # Build a contract between two OTHER worlds
    a = _make_poetry_world("a")
    b = _make_poetry_world("b")
    cid, _, _, _, _ = _setup_established_contract(a, b)
    # w is not a or b; copy the record into w's registry
    # (simulating a misconfigured registry)
    w.register_contract_offer(
        sign_offer("world:a", KeyPair.generate(),
                    "world:b",
                    ContractTerms(content={"kind": "test"})))
    # Actually, rebuild to match the cid... this is a bit of a
    # manufactured test. Instead, just check that if w's registry
    # has a record with world_a and world_b that don't match w,
    # the check fails.
    resident = _admit(w)
    # Build offer with w as neither party, but with same terms
    terms = ContractTerms(content={"kind": "external-only"})
    offer = sign_offer(
        "world:x", KeyPair.generate(), "world:y", terms)
    acceptance = sign_acceptance(
        "world:y", KeyPair.generate(), offer)
    w.register_contract_offer(offer)
    w.register_contract_acceptance(acceptance)
    r = w.act(_poem_turn(
        resident.token, cites=terms.terms_hash()))
    assert isinstance(r, Refusal)
    assert "not involve" in r.reason


# =====================================================================
# Admission gate (unadmitted actors don't learn contract state)
# =====================================================================

def test_unadmitted_actor_refused_on_admission():
    print("=== Unadmitted actor: refused on admission, not "
          "citation ===")
    w = _make_poetry_world()
    fake_token = "not-admitted"
    r = w.act(_poem_turn(fake_token, cites="00" * 32))
    assert isinstance(r, Refusal)
    assert "not admitted" in r.reason
    # Should NOT mention "not found" or "citation" — the actor
    # never got to the citation check
    assert "citation" not in r.reason.lower()
    assert "not found" not in r.reason.lower()


# =====================================================================
# Log entries
# =====================================================================

def test_citation_refused_logged():
    print("=== Refused citation logged ===")
    w = _make_poetry_world()
    resident = _admit(w)
    w.act(_poem_turn(resident.token, cites="00" * 32))
    refused = [e for e in w.log_since(None)
               if e.kind == "contract_citation_refused"]
    assert len(refused) == 1
    assert "not found" in refused[0].data["reason"]


def test_citation_refused_after_admission():
    print("=== Citation check happens after admission ===")
    w = _make_poetry_world()
    # Send from unadmitted actor with a bad citation
    fake_token = "not-admitted"
    w.act(_poem_turn(fake_token, cites="00" * 32))
    # No contract_citation_refused logged — the refusal was on
    # admission, not on citation
    refused = [e for e in w.log_since(None)
               if e.kind == "contract_citation_refused"]
    assert len(refused) == 0


# =====================================================================
# Registry sharing (the wiring model)
# =====================================================================

def test_shared_registry_syncs():
    """The world's registry and negotiator's registry can be the
    same object. This is the demo's wiring."""
    print("=== Shared registry: world sees what negotiator does ===")
    reg = ContractRegistry()
    w = _make_chem_world(registry=reg)
    kp = KeyPair.generate()
    curator = WorldCurator(w, kp)
    neg = ContractNegotiator(curator, registry=reg)
    # Negotiator proposes; world's registry should see the offer
    terms = ContractTerms(content={"kind": "test"})
    offer = neg.propose("world:other", terms)
    rec = w.contract_registry.get(terms.terms_hash())
    assert rec is not None
    assert rec.offer is not None
    assert rec.is_pending()


def test_default_registry_independent():
    """Without explicit sharing, each world gets its own registry."""
    print("=== Default: each world has its own registry ===")
    w1 = _make_poetry_world()
    w2 = _make_poetry_world("other")
    assert w1.contract_registry is not w2.contract_registry


# =====================================================================
# Never raises
# =====================================================================

def test_act_never_raises():
    print("=== act: never raises on weird payloads ===")
    w = _make_poetry_world()
    resident = _admit(w)
    for payload in (
        None, {}, {"cites_contract": None},
        {"cites_contract": ""},
        {"cites_contract": "not-hex"},
        {"cites_contract": "aa" * 32, "cites_world": 123},
    ):
        r = w.act(Act(
            actor_token=resident.token, type="poem.turn",
            payload=payload or {
                "acknowledgment": "x", "proposal": "y",
                "invitation": "z", "holds_open": True}))
        # Any Ack or Refusal is fine; just don't raise
        assert isinstance(r, (Ack, Refusal))


# =====================================================================
# Chemistry world: same discipline
# =====================================================================

def test_chemistry_revoked():
    print("=== Chemistry: revoked contract refused ===")
    w = _make_chem_world()
    other = _make_chem_world("other")
    cid, kp_a, kp_b, _, _ = _setup_established_contract(w, other)
    rev = sign_bilateral_revocation(
        contract_id=cid,
        world_a_id=w.manifest().entity_id,
        world_a_kp=kp_a,
        world_b_id=other.manifest().entity_id,
        world_b_kp=kp_b)
    w.register_contract_revocation(rev)
    resident = _admit(w)
    r = w.act(_chem_act(resident.token, cites=cid,
                         cites_world="world:other"))
    assert isinstance(r, Refusal)
    assert "revoked" in r.reason


# =====================================================================
# WCP conformance still passes
# =====================================================================

def test_conforms_to_wcp():
    print("=== ContractAware*: still WCP-conforming ===")
    from wcp_conformance import run_conformance
    for w in (_make_poetry_world(), _make_chem_world()):
        assert run_conformance(w)["passed"], \
            w.manifest().entity_id


# =====================================================================
# Demo
# =====================================================================

def test_demo(tmp_path):
    print("=== Demo: six scenarios ===")
    audit = demo(artifact_dir=str(tmp_path))
    s = audit["scenarios"]
    assert s["A_happy_path"]["accepted"] is True
    assert s["B_revoked"]["accepted"] is False
    assert "revoked" in s["B_revoked"]["reason"]
    assert s["C_pending"]["accepted"] is False
    assert "pending" in s["C_pending"]["reason"]
    assert s["D_unknown"]["accepted"] is False
    assert "not found" in s["D_unknown"]["reason"]
    assert s["E_no_citation"]["accepted"] is True
    assert s["F_wrong_world"]["accepted"] is False
    assert "cites_world" in s["F_wrong_world"]["reason"]
    assert audit["registry_established"] is True
    assert audit["offline_verified"] is True
    assert audit["log"]["cited_entries"] >= 1
    assert audit["log"]["refused_entries"] >= 4
    assert (tmp_path / "contract_aware_acts_demo.json").exists()


if __name__ == "__main__":
    test_poetry_world_untouched()
    test_chemistry_world_untouched()
    test_contract_aware_poetry_has_mixin()
    test_contract_aware_chemistry_has_mixin()
    test_poetry_accepts_valid_citation()
    test_chem_accepts_valid_citation()
    test_act_without_citation_accepted()
    test_citation_logged()
    test_refuse_missing_when_required()
    test_refuse_pending()
    test_refuse_revoked()
    test_refuse_not_found()
    test_refuse_bad_citation_format()
    test_refuse_wrong_counterparty()
    test_refuse_contract_not_with_this_world()
    test_unadmitted_actor_refused_on_admission()
    test_citation_refused_logged()
    test_citation_refused_after_admission()
    test_shared_registry_syncs()
    test_default_registry_independent()
    test_act_never_raises()
    test_chemistry_revoked()
    test_conforms_to_wcp()
    with tempfile.TemporaryDirectory() as tmp:
        test_demo(Path(tmp))

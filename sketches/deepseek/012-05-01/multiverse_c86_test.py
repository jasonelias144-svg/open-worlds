import json
import tempfile
import time
from pathlib import Path

import pytest

from multiverse_c1 import create_identity
from multiverse_c3 import Act, Ack, Refusal, Petition
from multiverse_c13 import HAS_CRYPTO, KeyPair
from multiverse_c81 import GrowingWorld
from multiverse_c82 import GrowingWorldCurator, MockGrowthModel
from multiverse_c83 import GovernedGrowingWorld, VotingPolicy
from multiverse_c84 import run_cycles
from multiverse_c86 import (
    build_claim_prompt, build_vote_prompt,
    parse_claim_response, parse_vote_response,
    ModelDrivenParticipant, PersonaMockModel,
    make_model_participant,
    _find_slot_for_size, _canvas_summary,
    demo,
)


pytestmark = pytest.mark.skipif(
    not HAS_CRYPTO, reason="cryptography not installed")


# -- Prompts --

def test_claim_prompt_contains_law_and_state():
    print("=== build_claim_prompt ===")
    prompt = build_claim_prompt(
        "a small painter",
        {"plot_count": 3, "total_area": 20},
        ["overlaps plot 1"],
        {"max_width": 20, "max_height": 20},
    )
    assert "a small painter" in prompt
    assert "3 plots" in prompt
    assert "20 cells" in prompt
    assert "max width 20" in prompt
    assert "should_claim" in prompt


def test_vote_prompt_contains_proposal():
    print("=== build_vote_prompt ===")
    prompt = build_vote_prompt(
        "a conservative builder",
        "Raise size limit",
        "several oversized claims were refused",
        {"max_width": 40},
        {"plot_count": 5, "total_area": 40},
    )
    assert "a conservative builder" in prompt
    assert "Raise size limit" in prompt
    assert "vote" in prompt


# -- Parsing --

def test_parse_claim_valid():
    print("=== parse_claim_response: valid ===")
    law = {"max_width": 20, "max_height": 20}
    text = json.dumps({
        "should_claim": True, "width": 3, "height": 3,
        "purpose": "studio"})
    r = parse_claim_response(text, law)
    assert r["should_claim"]
    assert r["width"] == 3
    assert r["purpose"] == "studio"


def test_parse_claim_declines():
    print("=== parse_claim_response: should_claim false ===")
    law = {"max_width": 20, "max_height": 20}
    r = parse_claim_response(
        '{"should_claim": false}', law)
    assert r["should_claim"] is False


def test_parse_claim_rejects_oversized():
    print("=== parse_claim_response: oversized rejected ===")
    law = {"max_width": 20, "max_height": 20}
    text = json.dumps({
        "should_claim": True, "width": 25, "height": 25,
        "purpose": "grand"})
    assert parse_claim_response(text, law) is None


def test_parse_claim_rejects_empty_purpose():
    print("=== parse_claim_response: empty purpose rejected ===")
    law = {"max_width": 20, "max_height": 20}
    text = json.dumps({
        "should_claim": True, "width": 2, "height": 2,
        "purpose": ""})
    assert parse_claim_response(text, law) is None


def test_parse_claim_rejects_garbage():
    print("=== parse_claim_response: garbage rejected ===")
    law = {"max_width": 20, "max_height": 20}
    assert parse_claim_response(
        "not json at all", law) is None
    assert parse_claim_response(
        '{"no_should_claim": true}', law) is None


def test_parse_claim_wrapped_json():
    print("=== parse_claim_response: wrapped in prose ===")
    law = {"max_width": 20, "max_height": 20}
    text = (
        "Here you go:\n"
        '{"should_claim": true, "width": 2, "height": 2, '
        '"purpose": "corner"}\n'
        "Thanks!")
    assert parse_claim_response(text, law) is not None


def test_parse_vote_valid():
    print("=== parse_vote_response: valid ===")
    r = parse_vote_response(
        '{"vote": "yes", "rationale": "good idea"}')
    assert r["vote"] == "yes"


def test_parse_vote_rejects_bad_choice():
    print("=== parse_vote_response: bad choice rejected ===")
    assert parse_vote_response(
        '{"vote": "maybe"}') is None


# -- Persona mock --

def test_persona_mock_produces_valid_claim():
    print("=== PersonaMockModel: valid claim JSON ===")
    m = PersonaMockModel(seed=1)
    text = m.generate(
        "You are a small painter ... max width 20, max height 20")
    parsed = json.loads(text)
    assert parsed["should_claim"] is True
    assert "purpose" in parsed


def test_persona_mock_produces_valid_vote():
    print("=== PersonaMockModel: valid vote JSON ===")
    m = PersonaMockModel(seed=1, vote_preference="no")
    text = m.generate(
        "Decide: do you vote yes/no/abstain?")
    parsed = json.loads(text)
    assert parsed["vote"] == "no"


# -- Participant --

def test_participant_claims_from_model():
    print("=== participant: claims from model ===")
    kp = KeyPair.generate()
    w = GovernedGrowingWorld(
        "world:c", "C", kp, seed_extent=(0, 0, 4, 4))
    p = make_model_participant(
        "Alice",
        "a small painter",
        PersonaMockModel(seed=1, vote_preference="yes"),
    )
    w.petition(Petition(
        petitioner_token=p.token, petitioner_name=p.name,
        passport_admissions=(), message=""))
    r = p.attempt(w, 0)
    assert r is not None
    assert len(w.current_plots()) == 2  # seed + 1
    # Purpose came from the model's bank
    purposes = [q["purpose"]
                for q in w.current_plots().values()
                if q["plot_id"] != "plot:seed"]
    assert any("studio" in purp or "corner" in purp
               or "notebook" in purp
               or "garden" in purp
               or "cell" in purp
               for purp in purposes)


def test_participant_falls_back_on_bad_model():
    print("=== participant: falls back on broken model ===")
    class BrokenModel:
        def model_id(self): return "broken"
        def is_available(self): return True
        def stats(self): return {}
        def generate(self, p, max_tokens=250):
            return "no json at all here"
    kp = KeyPair.generate()
    w = GovernedGrowingWorld(
        "world:c", "C", kp, seed_extent=(0, 0, 4, 4))
    p = ModelDrivenParticipant(
        identity=create_identity("Alice"),
        name="Alice",
        persona="small painter",
        model=BrokenModel(),
        fallback_claim_size=(2, 2),
        fallback_vote="abstain",
        claim_limit=2,
    )
    w.petition(Petition(
        petitioner_token=p.token, petitioner_name=p.name,
        passport_admissions=(), message=""))
    r = p.attempt(w, 0)
    # Fallback claim still succeeds
    assert isinstance(r, Ack)
    assert p._fallbacks >= 1
    assert p._parse_failures >= 1


def test_participant_vote_from_model():
    print("=== participant: vote from model ===")
    kp = KeyPair.generate()
    w = GovernedGrowingWorld(
        "world:c", "C", kp, seed_extent=(0, 0, 4, 4))
    p = make_model_participant(
        "Dave",
        "a conservative workshop builder",
        PersonaMockModel(seed=4, vote_preference="no"),
    )
    choice = p.vote(
        {"title": "Raise limit", "rationale": "x",
         "suggested_rule": {}},
        w)
    assert choice == "no"
    assert p._decisions[-1]["kind"] == "vote"
    assert p._decisions[-1]["source"] == "model"


# -- Slot finding --

def test_slot_finding_respects_size():
    print("=== _find_slot_for_size: finds space for 3x3 ===")
    kp = KeyPair.generate()
    w = GrowingWorld("world:c", "C", kp)
    slot = _find_slot_for_size(w, 3, 3)
    assert slot is not None
    x, y, = slot
    # Must not overlap (0,0,4,4)
    assert not (0 <= x < 4 and 0 <= y < 4)


# -- Full demo --

def test_demo(tmp_path):
    print("=== demo: full model-driven cycle run ===")
    audit = demo(artifact_dir=str(tmp_path))
    # Law grew
    assert audit["final_law"]["max_width"] > 20
    # Verdict valid
    assert audit["verdict"]["valid"] is True
    # Purposes are varied (at least 2 distinct)
    assert len(audit["purposes"]) >= 2
    # Stats show model calls
    for name, s in audit["participants"].items():
        assert s["model_calls"] > 0
    assert (tmp_path / "model_participants" /
            "model_participants_demo.json").exists()

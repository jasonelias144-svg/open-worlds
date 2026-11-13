import json
import tempfile
from pathlib import Path

import pytest

from multiverse_c3 import Act, Ack, Refusal
from multiverse_c11 import MockBackend
from multiverse_c13 import HAS_CRYPTO, KeyPair, canonical_bytes
from multiverse_c65 import (
    FederationClient, FederationReport, verify_report,
)
from multiverse_c66 import (
    DeployConfig, deploy_federation,
    _patch_c65_manifest_verification,
)
from multiverse_c67 import (
    ChemistryMockBackend,
    PoetryTurnStrategy, ChemistryReactionStrategy,
    read_world_log, _latest_of_kind,
    ResidentAgent, TurnResult,
    _extract_json_object,
    demo,
)


pytestmark = pytest.mark.skipif(
    not HAS_CRYPTO, reason="cryptography not installed")


# =====================================================================
# ChemistryMockBackend
# =====================================================================

def test_chemistry_mock_produces_balanced_reactions():
    print("=== ChemistryMockBackend: balanced reactions ===")
    from multiverse_c5 import reaction_balances
    backend = ChemistryMockBackend(seed=0)
    for i in range(3):
        out = backend.generate("some prompt")
        payload = json.loads(out)
        ok, reason = reaction_balances(
            payload["substrates"], payload["products"])
        assert ok, f"reaction {i} not balanced: {reason}"


def test_chemistry_mock_varies():
    print("=== ChemistryMockBackend: varies across calls ===")
    backend = ChemistryMockBackend(seed=0)
    outputs = [backend.generate("p") for _ in range(3)]
    assert len(set(outputs)) >= 2  # at least 2 distinct


def test_chemistry_mock_stats():
    print("=== ChemistryMockBackend: tracks stats ===")
    backend = ChemistryMockBackend(seed=0)
    for _ in range(3):
        backend.generate("prompt with several words here")
    stats = backend.stats()
    assert stats["calls"] == 3
    assert stats["tokens_in"] > 0
    assert stats["tokens_out"] > 0


# =====================================================================
# PoetryTurnStrategy
# =====================================================================

def test_poetry_strategy_builds_prompt():
    print("=== PoetryTurnStrategy: builds prompt ===")
    s = PoetryTurnStrategy("Emily-bot", "psychoanalytic")
    prompt = s.build_prompt({
        "proposal": "The Brain – is wider than the Sky –",
        "invitation": "What is the Sky to the Brain?",
        "acknowledgment": "(seed)",
    })
    assert "Emily-bot" in prompt
    assert "Brain" in prompt
    assert "Sky" in prompt
    assert "[KEY_TERMS:" in prompt


def test_poetry_strategy_parses_mock_output():
    print("=== PoetryTurnStrategy: parses MockBackend output ===")
    backend = MockBackend(seed=7)
    strategy = PoetryTurnStrategy("Emily-bot")
    prior = {
        "proposal": "The Brain – is wider than the Sky –",
        "invitation": "What is the Sky to the Brain?",
        "acknowledgment": "(seed)",
    }
    prompt = strategy.build_prompt(prior)
    text = backend.generate(prompt)
    payload = strategy.parse_response(text, prior)
    assert payload is not None
    assert "acknowledgment" in payload
    assert "proposal" in payload
    assert "invitation" in payload


def test_poetry_strategy_rejects_garbage():
    print("=== PoetryTurnStrategy: rejects unparseable ===")
    s = PoetryTurnStrategy("Emily-bot")
    assert s.parse_response("not json at all", {}) is None
    assert s.parse_response("", {}) is None


def test_poetry_strategy_with_wrapped_json():
    print("=== PoetryTurnStrategy: parses wrapped JSON ===")
    s = PoetryTurnStrategy("Emily-bot")
    text = (
        "Here you go:\n"
        '{"acknowledgment": "you said Brain", '
        '"proposal": "a line", '
        '"invitation": "what?"}\n'
        "Hope this helps!"
    )
    payload = s.parse_response(text, {})
    assert payload is not None
    assert payload["proposal"] == "a line"


# =====================================================================
# ChemistryReactionStrategy
# =====================================================================

def test_chemistry_strategy_builds_prompt():
    print("=== ChemistryReactionStrategy: builds prompt ===")
    s = ChemistryReactionStrategy("Lavoisier-bot")
    prompt = s.build_prompt({})
    assert "Lavoisier-bot" in prompt
    assert "substrates" in prompt
    assert "products" in prompt


def test_chemistry_strategy_parses():
    print("=== ChemistryReactionStrategy: parses valid JSON ===")
    s = ChemistryReactionStrategy("L")
    text = json.dumps({
        "substrates": [{"formula": "H2", "count": 2}],
        "products": [{"formula": "H2O", "count": 2}],
    })
    payload = s.parse_response(text, {})
    assert payload is not None
    assert "substrates" in payload


def test_chemistry_strategy_rejects_missing_fields():
    print("=== ChemistryReactionStrategy: rejects missing fields ===")
    s = ChemistryReactionStrategy("L")
    assert s.parse_response('{"substrates": []}', {}) is None
    assert s.parse_response('{"foo": "bar"}', {}) is None
    assert s.parse_response("not json", {}) is None


def test_chemistry_strategy_parses_wrapped():
    print("=== ChemistryReactionStrategy: parses wrapped JSON ===")
    s = ChemistryReactionStrategy("L")
    text = (
        "Here is the reaction:\n"
        '{"substrates": [{"formula": "H2", "count": 2}, '
        '{"formula": "O2", "count": 1}], '
        '"products": [{"formula": "H2O", "count": 2}]}\n'
        "Thanks."
    )
    payload = s.parse_response(text, {})
    assert payload is not None


# =====================================================================
# _extract_json_object
# =====================================================================

def test_extract_json_object():
    print("=== _extract_json_object ===")
    assert _extract_json_object('x {"a": 1} y') == '{"a": 1}'
    assert _extract_json_object('no braces') is None
    # Nested
    result = _extract_json_object('{"a": {"b": 1}}')
    assert result == '{"a": {"b": 1}}'
    # Brace in string
    result = _extract_json_object('{"a": "x{y}z"}')
    assert result == '{"a": "x{y}z"}'


# =====================================================================
# _latest_of_kind
# =====================================================================

def test_latest_of_kind():
    print("=== _latest_of_kind ===")
    entries = [
        {"kind": "admission", "data": {"x": 1}},
        {"kind": "turn", "data": {"p": "first"}},
        {"kind": "turn", "data": {"p": "second"}},
    ]
    result = _latest_of_kind(entries, ("turn",))
    assert result["p"] == "second"


def test_latest_of_kind_not_found():
    print("=== _latest_of_kind: not found ===")
    entries = [{"kind": "admission", "data": {}}]
    assert _latest_of_kind(entries, ("turn",)) == {}


# =====================================================================
# read_world_log helper
# =====================================================================

def test_read_world_log_requires_connection(tmp_path):
    print("=== read_world_log: requires connection ===")
    client = FederationClient(tmp_path / "c")
    client.create_identity("A")
    with pytest.raises(RuntimeError):
        read_world_log(client, "world:poetry")


def test_read_world_log_unknown_world(tmp_path):
    print("=== read_world_log: unknown world → RuntimeError ===")
    _patch_c65_manifest_verification()
    cfg = DeployConfig(
        state_dir=tmp_path / "fed", federation_name="t")
    fed = deploy_federation(cfg)
    try:
        client = FederationClient(tmp_path / "c")
        client.create_identity("A")
        client.connect(fed.anchors_url(),
                       fed.root_kp.public_key_hex())
        with pytest.raises(RuntimeError):
            read_world_log(client, "world:nonexistent")
    finally:
        fed.stop()


def test_read_world_log_live(tmp_path):
    print("=== read_world_log: works against live world ===")
    _patch_c65_manifest_verification()
    cfg = DeployConfig(
        state_dir=tmp_path / "fed", federation_name="t")
    fed = deploy_federation(cfg)
    try:
        client = FederationClient(tmp_path / "c")
        client.create_identity("A")
        client.connect(fed.anchors_url(),
                       fed.root_kp.public_key_hex())
        client.enter_world("world:poetry")
        log = read_world_log(client, "world:poetry")
        assert "entries" in log
        assert len(log["entries"]) >= 1  # has admission
    finally:
        fed.stop()


# =====================================================================
# ResidentAgent
# =====================================================================

def _deploy_and_connect(tmp_path):
    """Deploy a federation and connect a client. Returns (fed, client)."""
    _patch_c65_manifest_verification()
    cfg = DeployConfig(
        state_dir=tmp_path / "fed", federation_name="test")
    fed = deploy_federation(cfg)
    client = FederationClient(tmp_path / "client")
    client.create_identity("Alice")
    r = client.connect(
        fed.anchors_url(), fed.root_kp.public_key_hex())
    assert r.ok, r.reason
    return fed, client


def test_agent_requires_identity(tmp_path):
    print("=== ResidentAgent: requires identity ===")
    client = FederationClient(tmp_path / "c")
    with pytest.raises(RuntimeError):
        ResidentAgent(
            client=client,
            model=MockBackend(),
            strategy=PoetryTurnStrategy("X"),
            persona="X", world_id="world:poetry")


def test_agent_enter_poetry(tmp_path):
    print("=== ResidentAgent: enter poetry ===")
    fed, client = _deploy_and_connect(tmp_path)
    try:
        agent = ResidentAgent(
            client=client, model=MockBackend(),
            strategy=PoetryTurnStrategy("Bot"),
            persona="Bot", world_id="world:poetry")
        result = agent.enter()
        assert result.ok
        assert result.verified
    finally:
        fed.stop()


def test_agent_run_poetry_turns(tmp_path):
    print("=== ResidentAgent: run 2 poetry turns ===")
    fed, client = _deploy_and_connect(tmp_path)
    try:
        # Pre-seed
        client.enter_world("world:poetry")
        client.submit_act(
            "world:poetry", "poem.turn", {
                "acknowledgment": "(seed)",
                "proposal": "The Brain – is wider than the Sky –",
                "invitation": "What is the Sky?",
                "holds_open": True,
            })
        agent = ResidentAgent(
            client=client, model=MockBackend(seed=7),
            strategy=PoetryTurnStrategy("Bot"),
            persona="Bot", world_id="world:poetry")
        results = agent.run_turns(2)
        assert len(results) == 2
        accepted = sum(1 for r in results if r.ok)
        assert accepted >= 1
    finally:
        fed.stop()


def test_agent_run_chemistry(tmp_path):
    print("=== ResidentAgent: 2 chemistry reactions ===")
    fed, client = _deploy_and_connect(tmp_path)
    try:
        client.enter_world("world:chemistry")
        agent = ResidentAgent(
            client=client, model=ChemistryMockBackend(seed=3),
            strategy=ChemistryReactionStrategy("Bot"),
            persona="Bot", world_id="world:chemistry")
        results = agent.run_turns(2)
        assert len(results) == 2
        assert all(r.ok for r in results)
    finally:
        fed.stop()


def test_agent_handles_model_exception(tmp_path):
    print("=== ResidentAgent: model exception → error result ===")
    fed, client = _deploy_and_connect(tmp_path)
    try:
        class BadModel:
            def generate(self, prompt, max_tokens=250):
                raise RuntimeError("simulated model crash")
            def model_id(self): return "bad"
            def is_available(self): return True
            def stats(self): return {}
        client.enter_world("world:chemistry")
        agent = ResidentAgent(
            client=client, model=BadModel(),
            strategy=ChemistryReactionStrategy("Bot"),
            persona="Bot", world_id="world:chemistry")
        results = agent.run_turns(1)
        assert len(results) == 1
        assert not results[0].ok
        assert results[0].error == "model_error"
    finally:
        fed.stop()


def test_agent_handles_parse_failure(tmp_path):
    print("=== ResidentAgent: parse failure → error result ===")
    fed, client = _deploy_and_connect(tmp_path)
    try:
        class GarbageModel:
            def generate(self, prompt, max_tokens=250):
                return "this is not json at all"
            def model_id(self): return "garbage"
            def is_available(self): return True
            def stats(self): return {}
        client.enter_world("world:chemistry")
        agent = ResidentAgent(
            client=client, model=GarbageModel(),
            strategy=ChemistryReactionStrategy("Bot"),
            persona="Bot", world_id="world:chemistry")
        results = agent.run_turns(1)
        assert not results[0].ok
        assert results[0].error == "parse_error"
    finally:
        fed.stop()


def test_agent_handles_refusal(tmp_path):
    print("=== ResidentAgent: refusal → ok=False ===")
    fed, client = _deploy_and_connect(tmp_path)
    try:
        class UnbalancedModel:
            def generate(self, prompt, max_tokens=250):
                return json.dumps({
                    "substrates": [{"formula": "H2", "count": 1}],
                    "products": [{"formula": "H2O", "count": 1}],
                })
            def model_id(self): return "unbalanced"
            def is_available(self): return True
            def stats(self): return {}
        client.enter_world("world:chemistry")
        agent = ResidentAgent(
            client=client, model=UnbalancedModel(),
            strategy=ChemistryReactionStrategy("Bot"),
            persona="Bot", world_id="world:chemistry")
        results = agent.run_turns(1)
        assert not results[0].ok
        assert "refused" in results[0].reason.lower()
    finally:
        fed.stop()


def test_agent_history_and_counts(tmp_path):
    print("=== ResidentAgent: history and counts ===")
    fed, client = _deploy_and_connect(tmp_path)
    try:
        client.enter_world("world:chemistry")
        agent = ResidentAgent(
            client=client, model=ChemistryMockBackend(),
            strategy=ChemistryReactionStrategy("Bot"),
            persona="Bot", world_id="world:chemistry")
        results = agent.run_turns(3)
        assert len(agent.history()) == 3
        assert agent.accepted_count() >= 1
        assert agent.verified_count() >= 1
    finally:
        fed.stop()


def test_agent_report_is_verifiable(tmp_path):
    print("=== ResidentAgent: report verifies ===")
    fed, client = _deploy_and_connect(tmp_path)
    try:
        client.enter_world("world:chemistry")
        agent = ResidentAgent(
            client=client, model=ChemistryMockBackend(),
            strategy=ChemistryReactionStrategy("Bot"),
            persona="Bot", world_id="world:chemistry")
        agent.run_turns(1)
        report = agent.report()
        report_path = tmp_path / "report.json"
        report.save(report_path)
        loaded = FederationReport.load(report_path)
        verdict = verify_report(
            loaded, fed.root_kp.public_key_hex())
        assert verdict.valid
    finally:
        fed.stop()


# =====================================================================
# Demo
# =====================================================================

def test_demo(tmp_path):
    print("=== Demo: two AI residents ===")
    audit = demo(artifact_dir=str(tmp_path))
    poet = audit["poet"]
    assert poet["enter_ok"] is True
    assert poet["enter_verified"] is True
    assert poet["turns_attempted"] == 4
    assert poet["turns_accepted"] >= 1
    assert poet["turns_verified"] >= 1
    assert poet["third_party_verified"] is True

    chemist = audit["chemist"]
    assert chemist["enter_ok"] is True
    assert chemist["enter_verified"] is True
    assert chemist["reactions_attempted"] == 2
    assert chemist["reactions_accepted"] >= 1
    assert chemist["reactions_verified"] >= 1
    assert chemist["third_party_verified"] is True


if __name__ == "__main__":
    test_chemistry_mock_produces_balanced_reactions()
    test_chemistry_mock_varies()
    test_chemistry_mock_stats()
    test_poetry_strategy_builds_prompt()
    test_poetry_strategy_parses_mock_output()
    test_poetry_strategy_rejects_garbage()
    test_poetry_strategy_with_wrapped_json()
    test_chemistry_strategy_builds_prompt()
    test_chemistry_strategy_parses()
    test_chemistry_strategy_rejects_missing_fields()
    test_chemistry_strategy_parses_wrapped()
    test_extract_json_object()
    test_latest_of_kind()
    test_latest_of_kind_not_found()
    with tempfile.TemporaryDirectory() as tmp:
        test_read_world_log_requires_connection(Path(tmp))
    with tempfile.TemporaryDirectory() as tmp:
        test_read_world_log_unknown_world(Path(tmp))
    with tempfile.TemporaryDirectory() as tmp:
        test_read_world_log_live(Path(tmp))
    with tempfile.TemporaryDirectory() as tmp:
        test_agent_requires_identity(Path(tmp))
    with tempfile.TemporaryDirectory() as tmp:
        test_agent_enter_poetry(Path(tmp))
    with tempfile.TemporaryDirectory() as tmp:
        test_agent_run_poetry_turns(Path(tmp))
    with tempfile.TemporaryDirectory() as tmp:
        test_agent_run_chemistry(Path(tmp))
    with tempfile.TemporaryDirectory() as tmp:
        test_agent_handles_model_exception(Path(tmp))
    with tempfile.TemporaryDirectory() as tmp:
        test_agent_handles_parse_failure(Path(tmp))
    with tempfile.TemporaryDirectory() as tmp:
        test_agent_handles_refusal(Path(tmp))
    with tempfile.TemporaryDirectory() as tmp:
        test_agent_history_and_counts(Path(tmp))
    with tempfile.TemporaryDirectory() as tmp:
        test_agent_report_is_verifiable(Path(tmp))

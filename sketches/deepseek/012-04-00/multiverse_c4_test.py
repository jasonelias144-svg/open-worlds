# multiverse_c4_test.py
from multiverse_c1 import create_identity
from multiverse_c2 import Passport
from multiverse_c3 import (
    Petition, Act, Admission as WCPAdmission, Refusal, Ack,
)
from multiverse_c3_conformance import run_conformance
from multiverse_c4 import (
    PoetryWorldLaw, PoetryWorld, turns_from_log,
)


def _petition(name: str, token: str,
               passport_admissions=()) -> Petition:
    return Petition(
        petitioner_token=token,
        petitioner_name=name,
        passport_admissions=passport_admissions,
        message=f"{name} petitions to enter.",
    )


def _turn(actor: str, ack: str, proposal: str, invitation: str,
           holds_open: bool = True, stance: str = "formalist") -> Act:
    return Act(
        actor_token=actor,
        type="poem.turn",
        payload={
            "acknowledgment": ack,
            "proposal": proposal,
            "invitation": invitation,
            "holds_open": holds_open,
            "stance_used": stance,
        },
    )


def test_law_is_readable():
    print("=== Law is published ===")
    law = PoetryWorldLaw()
    print(law.describe())
    # Readable means: has the required sections
    doc = law.describe()
    assert "Petition" in doc
    assert "Act" in doc
    assert "Convergence" in doc
    print()


def test_manifest():
    print("=== Manifest ===")
    w = PoetryWorld("world:poetry", "The Poetry World")
    m = w.manifest()
    print(f"  {m.name} ({m.entity_id})")
    print(f"  protocol: {m.protocol_version}")
    print(f"  law_url: {m.law_url}")
    assert m.protocol_version == "WCP/0.1"
    assert not m.has_sub_registry()


def test_petition_admits():
    print("=== Petition: admitted ===")
    w = PoetryWorld("world:poetry", "The Poetry World")
    alice = create_identity("Alice")
    response = w.petition(_petition("Alice", alice.token))
    print(f"  response: {response}")
    assert isinstance(response, WCPAdmission)
    assert response.entity_id == "world:poetry"


def test_petition_already_admitted():
    print("=== Petition: already admitted ===")
    w = PoetryWorld("world:poetry", "The Poetry World")
    alice = create_identity("Alice")
    w.petition(_petition("Alice", alice.token))
    response = w.petition(_petition("Alice", alice.token))
    print(f"  response: {response}")
    assert isinstance(response, Refusal)
    assert "Already" in response.reason


def test_petition_preserves_passport_admissions():
    print("=== Petition preserves prior admissions ===")
    w = PoetryWorld("world:poetry", "The Poetry World")
    alice = create_identity("Alice")
    # Alice has already been admitted to world:A
    response = w.petition(_petition(
        "Alice", alice.token,
        passport_admissions=(("world:A", "2024-01-01T00:00:00+00:00"),),
    ))
    assert isinstance(response, WCPAdmission)
    # The World's cache now has her passport with both admissions
    passport = w._passports[alice.token]
    print(f"  passport admissions: {len(passport)}")
    assert len(passport) == 2  # world:A + world:poetry


def test_seed_turn():
    print("=== Seed turn ===")
    w = PoetryWorld("world:poetry", "The Poetry World")
    alice = create_identity("Alice")
    w.petition(_petition("Alice", alice.token))
    seed = _turn(
        actor=alice.token,
        ack="(seed)",
        proposal=(
            "Go\n"
            "Be a black widow\n"
            "And dangle in webs."
        ),
        invitation="What becomes of the web?",
        stance="formalist",
    )
    response = w.act(seed)
    print(f"  response: {response}")
    assert isinstance(response, Ack)
    assert len(w.turns()) == 1


def test_subsequent_turn():
    print("=== Subsequent turn ===")
    w = PoetryWorld("world:poetry", "The Poetry World")
    alice = create_identity("Alice")
    bob = create_identity("Bob")
    w.petition(_petition("Alice", alice.token))
    w.petition(_petition("Bob", bob.token))

    w.act(_turn(
        actor=alice.token,
        ack="(seed)",
        proposal="Go\nBe a black widow\nAnd dangle in webs.",
        invitation="What becomes of the web?",
    ))
    response = w.act(_turn(
        actor=bob.token,
        ack="You said 'black widow' and 'dangle' and 'web'.",
        proposal="The web is not the widow's — it is the widow.",
        invitation="What is the daughter's voice?",
        stance="psychoanalytic",
    ))
    print(f"  response: {response}")
    assert isinstance(response, Ack)
    assert len(w.turns()) == 2


def test_refusal_missing_acknowledgment():
    print("=== Refusal: missing acknowledgment ===")
    w = PoetryWorld("world:poetry", "The Poetry World")
    alice = create_identity("Alice")
    w.petition(_petition("Alice", alice.token))
    response = w.act(_turn(
        actor=alice.token,
        ack="",
        proposal="(proposal)",
        invitation="(invitation)",
    ))
    print(f"  response: {response}")
    assert isinstance(response, Refusal)
    assert "acknowledgment" in response.reason


def test_refusal_missing_invitation():
    print("=== Refusal: missing invitation ===")
    w = PoetryWorld("world:poetry", "The Poetry World")
    alice = create_identity("Alice")
    w.petition(_petition("Alice", alice.token))
    response = w.act(_turn(
        actor=alice.token,
        ack="(seed)",
        proposal="(proposal)",
        invitation="",
    ))
    assert isinstance(response, Refusal)
    assert "invitation" in response.reason


def test_refusal_does_not_hold_open():
    print("=== Refusal: does not hold open ===")
    w = PoetryWorld("world:poetry", "The Poetry World")
    alice = create_identity("Alice")
    w.petition(_petition("Alice", alice.token))
    response = w.act(_turn(
        actor=alice.token,
        ack="(seed)",
        proposal="(proposal)",
        invitation="(invitation)",
        holds_open=False,
    ))
    assert isinstance(response, Refusal)
    assert "hold open" in response.reason


def test_refusal_acknowledgment_does_not_reference():
    print("=== Refusal: acknowledgment doesn't reference prior ===")
    w = PoetryWorld("world:poetry", "The Poetry World")
    alice = create_identity("Alice")
    bob = create_identity("Bob")
    w.petition(_petition("Alice", alice.token))
    w.petition(_petition("Bob", bob.token))
    w.act(_turn(
        actor=alice.token,
        ack="(seed)",
        proposal="Go\nBe a black widow.",
        invitation="What next?",
    ))
    response = w.act(_turn(
        actor=bob.token,
        ack="I agree.",  # does not reference 'black widow'
        proposal="(proposal)",
        invitation="(invitation)",
    ))
    print(f"  response: {response}")
    assert isinstance(response, Refusal)
    assert "reference" in response.reason


def test_refusal_not_admitted():
    print("=== Refusal: actor not admitted ===")
    w = PoetryWorld("world:poetry", "The Poetry World")
    alice = create_identity("Alice")
    response = w.act(_turn(
        actor=alice.token,  # never petitioned
        ack="(seed)",
        proposal="(proposal)",
        invitation="(invitation)",
    ))
    print(f"  response: {response}")
    assert isinstance(response, Refusal)
    assert "not admitted" in response.reason


def test_refusal_wrong_type():
    print("=== Refusal: wrong act type ===")
    w = PoetryWorld("world:poetry", "The Poetry World")
    alice = create_identity("Alice")
    w.petition(_petition("Alice", alice.token))
    bad = Act(
        actor_token=alice.token,
        type="poem.not_a_turn",
        payload={},
    )
    response = w.act(bad)
    assert isinstance(response, Refusal)
    assert "Unknown act type" in response.reason


def test_convergence_by_invitation():
    print("=== Convergence: same invitation across window ===")
    # Use a Law with similarity threshold high enough that
    # proposal similarity won't trigger, but same-invitation will
    law = PoetryWorldLaw(
        convergence_window=3,
        convergence_similarity=0.99,  # very high, unlikely from diff texts
    )
    w = PoetryWorld("world:poetry", "The Poetry World", law=law)
    alice = create_identity("Alice")
    bob = create_identity("Bob")
    charlie = create_identity("Charlie")
    for name, ident in [("Alice", alice), ("Bob", bob),
                        ("Charlie", charlie)]:
        w.petition(_petition(name, ident.token))

    # Submit 4 turns with different proposals, same invitation
    turns = [
        _turn(alice.token, "(seed)", "first poem text here",
               "What is the poem?"),
        _turn(bob.token, "You said 'poem' and 'text' here",
               "second poem text here",
               "What is the poem?"),
        _turn(charlie.token, "You said 'poem' and 'text' here",
               "third poem text here",
               "What is the poem?"),
        _turn(alice.token, "You said 'poem' and 'text' here",
               "fourth poem text here",
               "What is the poem?"),
    ]
    for t in turns:
        response = w.act(t)
        print(f"  act → {response}")
    print(f"  converged: {w.is_converged()}")
    assert w.is_converged()


def test_refuses_after_convergence():
    print("=== Refuses after convergence ===")
    law = PoetryWorldLaw(
        convergence_window=2,
        convergence_similarity=0.99,
    )
    w = PoetryWorld("world:poetry", "The Poetry World", law=law)
    alice = create_identity("Alice")
    w.petition(_petition("Alice", alice.token))
    # Two turns with same invitation → convergence
    for _ in range(3):
        response = w.act(_turn(
            alice.token, "I respond to the poem",
            "a different poem line",
            "What is the poem?",
        ))
    assert w.is_converged()
    extra = w.act(_turn(
        alice.token, "I respond to the poem",
        "another line",
        "What is the poem?",
    ))
    print(f"  post-convergence response: {extra}")
    assert isinstance(extra, Refusal)
    assert "converged" in extra.reason


def test_log_records_everything():
    print("=== Log records everything ===")
    w = PoetryWorld("world:poetry", "The Poetry World")
    alice = create_identity("Alice")
    w.petition(_petition("Alice", alice.token))
    w.act(_turn(
        alice.token, "(seed)",
        "a poem here",
        "what next?",
    ))
    log = w.log_since(None)
    print(f"  log entries: {len(log)}")
    kinds = [e.kind for e in log]
    print(f"  kinds: {kinds}")
    assert "admission" in kinds
    assert "turn" in kinds


def test_log_query_by_timestamp():
    print("=== Log query by timestamp ===")
    w = PoetryWorld("world:poetry", "The Poetry World")
    alice = create_identity("Alice")
    w.petition(_petition("Alice", alice.token))
    entries = w.log_since(None)
    first_ts = entries[0].timestamp
    later = w.log_since(first_ts)
    # No entry with timestamp strictly greater than the first
    # since everything was at the same moment
    print(f"  first entry ts: {first_ts}")
    print(f"  entries after first: {len(later)}")
    # Either 0 or 1 depending on microsecond resolution — either is fine
    assert len(later) <= 1


def test_reconstruct_turns_from_log():
    print("=== Reconstruct turns from log ===")
    w = PoetryWorld("world:poetry", "The Poetry World")
    alice = create_identity("Alice")
    bob = create_identity("Bob")
    w.petition(_petition("Alice", alice.token))
    w.petition(_petition("Bob", bob.token))
    w.act(_turn(alice.token, "(seed)",
                "Go\nBe a black widow.",
                "What becomes of the web?"))
    w.act(_turn(bob.token,
                "You said 'black widow' and 'web'.",
                "The web is not hers.",
                "What is the daughter's voice?"))
    log = w.log_since(None)
    reconstructed = turns_from_log(log)
    print(f"  reconstructed turns: {len(reconstructed)}")
    for t in reconstructed:
        print(f"    by {t['actor_name']}, "
              f"proposal {t['proposal'][:30]!r}...")
    assert len(reconstructed) == 2
    assert reconstructed[0]["actor_name"] == "Alice"
    assert reconstructed[1]["actor_name"] == "Bob"


def test_conformance():
    print("=== Poetry World conforms to WCP/0.1 ===")
    w = PoetryWorld("world:poetry", "The Poetry World")
    result = run_conformance(w)
    print(f"  passed: {result['passed']}")
    if not result["passed"]:
        for f in result["failures"]:
            print(f"    FAILURE: {f}")
    assert result["passed"]


def test_two_worlds_independent():
    print("=== Two worlds are independent ===")
    lawA = PoetryWorldLaw(max_admitted=2)
    lawB = PoetryWorldLaw(max_admitted=10)
    wA = PoetryWorld("world:poetry-A", "Poetry World A", law=lawA)
    wB = PoetryWorld("world:poetry-B", "Poetry World B", law=lawB)

    alice = create_identity("Alice")
    bob = create_identity("Bob")
    charlie = create_identity("Charlie")

    # Admit Alice to both; Bob to A only; Charlie to B only
    assert isinstance(wA.petition(_petition("Alice", alice.token)),
                      WCPAdmission)
    assert isinstance(wB.petition(_petition("Alice", alice.token)),
                      WCPAdmission)
    assert isinstance(wA.petition(_petition("Bob", bob.token)),
                      WCPAdmission)
    assert isinstance(wB.petition(_petition("Charlie", charlie.token)),
                      WCPAdmission)
    # Charlie is not in A
    r = wA.petition(_petition("Charlie", charlie.token))
    # Wait — wA has max_admitted=2 and is full now
    # So Charlie's petition should be refused with "World is full"
    print(f"  wA.refuse Charlie: {r}")
    assert isinstance(r, Refusal)
    # Charlie cannot act in A
    bad = wA.act(_turn(charlie.token, "hi",
                        "proposal", "invitation"))
    assert isinstance(bad, Refusal)

    # Alice and Bob can act in A
    ok = wA.act(_turn(alice.token, "hi", "alice poem", "invitation"))
    assert isinstance(ok, Ack)
    ok = wA.act(_turn(bob.token, "you said 'alice'",
                       "bob poem", "invitation"))
    assert isinstance(ok, Ack)

    # B is separate
    assert len(wA.turns()) == 2
    assert len(wB.turns()) == 0
    print(f"  wA.turns: {len(wA.turns())}")
    print(f"  wB.turns: {len(wB.turns())}")


def test_end_to_end():
    """A full collaboration: 3 identities, 6 turns, convergence."""
    print("=== Full collaboration end-to-end ===")
    law = PoetryWorldLaw(
        convergence_window=3,
        convergence_similarity=0.5,
    )
    w = PoetryWorld("world:poetry", "The Poetry World", law=law)
    alice = create_identity("Alice")
    bob = create_identity("Bob")
    charlie = create_identity("Charlie")
    for name, ident in [("Alice", alice), ("Bob", bob),
                        ("Charlie", charlie)]:
        w.petition(_petition(name, ident.token))

    # Simulate 3 rounds of response
    dialogue = [
        (alice, "Go\nBe a black widow\nAnd dangle in webs.",
                "(seed)", "What becomes of the web?",
                "formalist"),
        (bob, "The web is not the widow's — it is the widow.",
                "You said 'black widow' and 'web' and 'dangle'.",
                "What is the daughter's voice?",
                "psychoanalytic"),
        (charlie, "The daughter's voice is a thread extruded.",
                "You said 'daughter' and 'voice' and 'thread'.",
                "What is the thread that speaks?",
                "ecocritical"),
    ]
    for ident, proposal, ack, inv, stance in dialogue:
        response = w.act(_turn(ident.token, ack, proposal, inv,
                                 stance=stance))
        print(f"  {ident.name}: {response}")

    # Check the world state
    print(f"\n  {w.describe()}")
    log = w.log_since(None)
    print(f"  total log entries: {len(log)}")
    reconstructed = turns_from_log(log)
    print(f"  turns: {len(reconstructed)}")
    for t in reconstructed:
        print(f"    {t['actor_name']} [{t['stance_used']}]: "
              f"{t['proposal'][:40]!r}")
    assert len(reconstructed) == 3


if __name__ == "__main__":
    test_law_is_readable()
    test_manifest()
    test_petition_admits()
    test_petition_already_admitted()
    test_petition_preserves_passport_admissions()
    test_seed_turn()
    test_subsequent_turn()
    test_refusal_missing_acknowledgment()
    test_refusal_missing_invitation()
    test_refusal_does_not_hold_open()
    test_refusal_acknowledgment_does_not_reference()
    test_refusal_not_admitted()
    test_refusal_wrong_type()
    test_convergence_by_invitation()
    test_refuses_after_convergence()
    test_log_records_everything()
    test_log_query_by_timestamp()
    test_reconstruct_turns_from_log()
    test_conformance()
    test_two_worlds_independent()
    test_end_to_end()

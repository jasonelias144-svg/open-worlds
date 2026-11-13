# multiverse_c5_test.py
from multiverse_c1 import create_identity
from multiverse_c3 import (
    Petition, Act, Admission as WCPAdmission, Refusal, Ack,
)
from multiverse_c3_conformance import run_conformance
from multiverse_c4 import PoetryWorld, PoetryWorldLaw
from multiverse_c5 import (
    ELEMENTS, Molecule, parse_formula, reaction_balances,
    ChemistryWorldLaw, ChemistryWorld, reactions_from_log,
)


def _petition(name, token, admissions=()):
    return Petition(
        petitioner_token=token,
        petitioner_name=name,
        passport_admissions=admissions,
        message=f"{name} petitions.",
    )


def _reaction(actor, substrates, products, catalyst=None):
    payload = {"substrates": substrates, "products": products}
    if catalyst is not None:
        payload["catalyst"] = catalyst
    return Act(actor_token=actor, type="chemistry.react",
               payload=payload)


def test_element_table():
    print("=== Element table ===")
    for sym, info in ELEMENTS.items():
        print(f"  {sym}: {info['name']} (Z={info['atomic_number']})")
    assert "H" in ELEMENTS
    assert "O" in ELEMENTS
    assert len(ELEMENTS) == 8


def test_parse_simple_formula():
    print("=== Parse simple formulas ===")
    for formula, expected in [
        ("H2O", {"H": 2, "O": 1}),
        ("CH4", {"C": 1, "H": 4}),
        ("C2H6O", {"C": 2, "H": 6, "O": 1}),
        ("O2", {"O": 2}),
        ("NaCl", {"Na": 1, "Cl": 1}),
    ]:
        m = parse_formula(formula)
        print(f"  {formula}: {m.atoms}, charge {m.charge}")
        assert m.atoms == expected
        assert m.charge == 0


def test_parse_charges():
    print("=== Parse formulas with charges ===")
    for formula, expected_atoms, expected_charge in [
        ("NH4+", {"N": 1, "H": 4}, 1),
        ("OH-", {"O": 1, "H": 1}, -1),
        ("SO4-2", {"S": 1, "O": 4}, -2),
        ("Ca+2", {"Ca": 1}, 2),
    ]:
        m = parse_formula(formula)
        print(f"  {formula}: {m.atoms}, charge {m.charge:+d}")
        assert m.atoms == expected_atoms
        assert m.charge == expected_charge


def test_parse_rejects_unknown_element():
    print("=== Parse rejects unknown element ===")
    try:
        parse_formula("Xx2O")
        assert False, "should reject unknown element"
    except ValueError as e:
        print(f"  ✓ rejected: {e}")


def test_balance_balanced():
    print("=== Balance: balanced reactions ===")
    cases = [
        # 2H2 + O2 → 2H2O
        ([{"formula": "H2", "count": 2},
          {"formula": "O2", "count": 1}],
         [{"formula": "H2O", "count": 2}],
         "water synthesis"),
        # CH4 + 2O2 → CO2 + 2H2O
        ([{"formula": "CH4", "count": 1},
          {"formula": "O2", "count": 2}],
         [{"formula": "CO2", "count": 1},
          {"formula": "H2O", "count": 2}],
         "methane combustion"),
        # NH4+ + OH- → NH3 + H2O
        ([{"formula": "NH4+", "count": 1},
          {"formula": "OH-", "count": 1}],
         [{"formula": "NH3", "count": 1},
          {"formula": "H2O", "count": 1}],
         "ammonium hydroxide neutralization"),
        # NH4+ → NH3 + H+
        ([{"formula": "NH4+", "count": 1}],
         [{"formula": "NH3", "count": 1},
          {"formula": "H+", "count": 1}],
         "proton dissociation"),
    ]
    for subs, prods, name in cases:
        ok, reason = reaction_balances(subs, prods)
        print(f"  {name}: {ok}")
        assert ok, f"{name} should balance: {reason}"


def test_balance_unbalanced_atoms():
    print("=== Balance: unbalanced atoms ===")
    # H2 + O2 → H2O (missing 1 H2)
    ok, reason = reaction_balances(
        [{"formula": "H2", "count": 1},
         {"formula": "O2", "count": 1}],
        [{"formula": "H2O", "count": 1}],
    )
    print(f"  H2 + O2 → H2O: balanced={ok}, reason={reason}")
    assert not ok
    assert "imbalance" in reason.lower()


def test_balance_unbalanced_charge():
    print("=== Balance: unbalanced charge ===")
    # NH4+ → NH3 (H: 4 vs 3, and charge +1 vs 0)
    ok, reason = reaction_balances(
        [{"formula": "NH4+", "count": 1}],
        [{"formula": "NH3", "count": 1}],
    )
    print(f"  NH4+ → NH3: balanced={ok}, reason={reason}")
    assert not ok


def test_balance_rejects_bad_formula():
    print("=== Balance: bad formula rejected ===")
    ok, reason = reaction_balances(
        [{"formula": "Xx2", "count": 1}],
        [{"formula": "H2O", "count": 1}],
    )
    print(f"  balanced={ok}, reason={reason}")
    assert not ok
    assert "Unknown element" in reason


def test_petition_and_act():
    print("=== Chemistry World: petition and act ===")
    w = ChemistryWorld("world:chemistry", "The Chemistry World")
    alice = create_identity("Alice")
    pa = w.petition(_petition("Alice", alice.token))
    print(f"  petition: {pa}")
    assert isinstance(pa, WCPAdmission)

    ack = w.act(_reaction(
        alice.token,
        substrates=[{"formula": "H2", "count": 2},
                     {"formula": "O2", "count": 1}],
        products=[{"formula": "H2O", "count": 2}],
    ))
    print(f"  act: {ack}")
    assert isinstance(ack, Ack)
    assert len(w.reactions()) == 1
    print(f"  molecules now known: {w.molecules()}")


def test_refuses_unbalanced():
    print("=== Chemistry World: refuses unbalanced ===")
    w = ChemistryWorld("world:chemistry", "The Chemistry World")
    alice = create_identity("Alice")
    w.petition(_petition("Alice", alice.token))
    bad = w.act(_reaction(
        alice.token,
        substrates=[{"formula": "H2", "count": 1},
                     {"formula": "O2", "count": 1}],
        products=[{"formula": "H2O", "count": 1}],
    ))
    print(f"  response: {bad}")
    assert isinstance(bad, Refusal)
    assert "balance" in bad.reason.lower()


def test_refuses_poetry_act():
    print("=== Chemistry World: refuses poetry act ===")
    w = ChemistryWorld("world:chemistry", "The Chemistry World")
    alice = create_identity("Alice")
    w.petition(_petition("Alice", alice.token))
    poetry_act = Act(
        actor_token=alice.token,
        type="poem.turn",
        payload={"acknowledgment": "x", "proposal": "y",
                 "invitation": "z", "holds_open": True},
    )
    response = w.act(poetry_act)
    print(f"  response: {response}")
    assert isinstance(response, Refusal)
    assert "Unknown act type" in response.reason


def test_equilibrium_convergence():
    print("=== Chemistry World: equilibrium convergence ===")
    w = ChemistryWorld("world:chemistry", "The Chemistry World")
    alice = create_identity("Alice")
    w.petition(_petition("Alice", alice.token))

    # Same water synthesis repeated. Window is 4 (default).
    # With 5 reactions all using {H2, O2, H2O}, the last 4
    # reactions will be redundant with the first → converged.
    for i in range(5):
        r = w.act(_reaction(
            alice.token,
            substrates=[{"formula": "H2", "count": 2},
                         {"formula": "O2", "count": 1}],
            products=[{"formula": "H2O", "count": 2}],
        ))
        print(f"  reaction {i+1}: {type(r).__name__}, "
              f"converged={w.is_converged()}")

    assert w.is_converged()


def test_not_converged_with_new_molecules():
    print("=== Chemistry World: new molecules prevent convergence ===")
    w = ChemistryWorld("world:chemistry", "The Chemistry World")
    alice = create_identity("Alice")
    w.petition(_petition("Alice", alice.token))

    # Each reaction introduces a new molecule. Window never closes.
    reactions = [
        # 2H2 + O2 → 2H2O (introduces H2O)
        ([{"formula": "H2", "count": 2},
          {"formula": "O2", "count": 1}],
         [{"formula": "H2O", "count": 2}]),
        # CH4 + 2O2 → CO2 + 2H2O (introduces CH4, CO2)
        ([{"formula": "CH4", "count": 1},
          {"formula": "O2", "count": 2}],
         [{"formula": "CO2", "count": 1},
          {"formula": "H2O", "count": 2}]),
        # N2 + 3H2 → 2NH3 (introduces N2, NH3)
        ([{"formula": "N2", "count": 1},
          {"formula": "H2", "count": 3}],
         [{"formula": "NH3", "count": 2}]),
        # 2Na + Cl2 → 2NaCl (introduces Na, Cl2, NaCl)
        ([{"formula": "Na", "count": 2},
          {"formula": "Cl2", "count": 1}],
         [{"formula": "NaCl", "count": 2}]),
        # S + O2 → SO2 (introduces S, SO2)
        ([{"formula": "S", "count": 1},
          {"formula": "O2", "count": 1}],
         [{"formula": "SO2", "count": 1}]),
    ]
    for i, (subs, prods) in enumerate(reactions):
        r = w.act(_reaction(alice.token, substrates=subs, products=prods))
        print(f"  reaction {i+1}: {type(r).__name__}, "
              f"converged={w.is_converged()}")

    assert not w.is_converged()


def test_conformance():
    print("=== Chemistry World conforms to WCP/0.1 ===")
    w = ChemistryWorld("world:chemistry", "The Chemistry World")
    result = run_conformance(w)
    print(f"  passed: {result['passed']}")
    if not result["passed"]:
        for f in result["failures"]:
            print(f"    {f}")
    assert result["passed"]


def test_two_worlds_same_protocol_different_laws():
    """The proof: two worlds, same protocol, different laws.

    Both pass the same conformance test. Both admit the same identity
    with the same petition. But their acts are completely different,
    and each refuses the other's acts.
    """
    print("=== The proof: two worlds, same protocol, different laws ===")
    poetry = PoetryWorld("world:poetry", "The Poetry World")
    chemistry = ChemistryWorld("world:chemistry", "The Chemistry World")

    # Both conform to the same protocol
    p_conforms = run_conformance(poetry)["passed"]
    c_conforms = run_conformance(chemistry)["passed"]
    print(f"  Poetry conforms: {p_conforms}")
    print(f"  Chemistry conforms: {c_conforms}")
    assert p_conforms and c_conforms

    # Both admit the same identity with the same petition
    alice = create_identity("Alice")
    pa = poetry.petition(_petition("Alice", alice.token))
    ca = chemistry.petition(_petition("Alice", alice.token))
    assert isinstance(pa, WCPAdmission)
    assert isinstance(ca, WCPAdmission)
    print(f"  Both admitted Alice")

    # The acts are completely different
    poetry_turn = Act(
        actor_token=alice.token, type="poem.turn",
        payload={"acknowledgment": "seed",
                 "proposal": "a poem line",
                 "invitation": "what next?",
                 "holds_open": True},
    )
    chemistry_reaction = _reaction(
        alice.token,
        substrates=[{"formula": "H2", "count": 2},
                     {"formula": "O2", "count": 1}],
        products=[{"formula": "H2O", "count": 2}],
    )

    # Poetry accepts poetry turns, refuses chemistry reactions
    p1 = poetry.act(poetry_turn)
    p2 = poetry.act(chemistry_reaction)
    print(f"  Poetry.act(poetry_turn):        {type(p1).__name__}")
    print(f"  Poetry.act(chemistry_reaction): {type(p2).__name__}")
    assert isinstance(p1, Ack)
    assert isinstance(p2, Refusal)

    # Chemistry accepts chemistry, refuses poetry
    c1 = chemistry.act(chemistry_reaction)
    c2 = chemistry.act(poetry_turn)
    print(f"  Chemistry.act(chemistry_reaction): {type(c1).__name__}")
    print(f"  Chemistry.act(poetry_turn):        {type(c2).__name__}")
    assert isinstance(c1, Ack)
    assert isinstance(c2, Refusal)

    # Each world's log is its own
    p_log = poetry.log_since(None)
    c_log = chemistry.log_since(None)
    print(f"  Poetry log entries: {len(p_log)}")
    print(f"  Chemistry log entries: {len(c_log)}")
    # Both have admission + turn/reaction + refused entry
    assert len(p_log) == 3
    assert len(c_log) == 3


def test_end_to_end_chemistry():
    """A full chemistry session: several reactions, equilibrium."""
    print("=== Full chemistry session ===")
    w = ChemistryWorld("world:chemistry", "The Chemistry World")
    alice = create_identity("Alice")
    bob = create_identity("Bob")
    w.petition(_petition("Alice", alice.token))
    w.petition(_petition("Bob", bob.token))

    # Alice burns methane
    w.act(_reaction(
        alice.token,
        substrates=[{"formula": "CH4", "count": 1},
                     {"formula": "O2", "count": 2}],
        products=[{"formula": "CO2", "count": 1},
                  {"formula": "H2O", "count": 2}],
    ))
    # Bob synthesizes water
    w.act(_reaction(
        bob.token,
        substrates=[{"formula": "H2", "count": 2},
                     {"formula": "O2", "count": 1}],
        products=[{"formula": "H2O", "count": 2}],
    ))
    # Alice neutralizes ammonium
    w.act(_reaction(
        alice.token,
        substrates=[{"formula": "NH4+", "count": 1},
                     {"formula": "OH-", "count": 1}],
        products=[{"formula": "NH3", "count": 1},
                  {"formula": "H2O", "count": 1}],
    ))

    print(f"  {w.describe()}")
    log = w.log_since(None)
    reconstructed = reactions_from_log(log)
    print(f"  reconstructed reactions: {len(reconstructed)}")
    for r in reconstructed:
        print(f"    {r['actor_name']}: "
              f"{[m['formula'] for m in r['substrates']]} → "
              f"{[m['formula'] for m in r['products']]}")
    assert len(reconstructed) == 3


if __name__ == "__main__":
    test_element_table()
    test_parse_simple_formula()
    test_parse_charges()
    test_parse_rejects_unknown_element()
    test_balance_balanced()
    test_balance_unbalanced_atoms()
    test_balance_unbalanced_charge()
    test_balance_rejects_bad_formula()
    test_petition_and_act()
    test_refuses_unbalanced()
    test_refuses_poetry_act()
    test_equilibrium_convergence()
    test_not_converged_with_new_molecules()
    test_conformance()
    test_two_worlds_same_protocol_different_laws()
    test_end_to_end_chemistry()

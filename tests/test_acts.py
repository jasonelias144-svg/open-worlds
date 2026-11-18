"""Who may act on a log, held to the signed records (world/acts.py;
docs/research/REDACTION.md, decisions 7 to 9, the records' side of part
four)."""
import copy
import json
import re
import unittest

from formats import records
from world import acts, acts_vectors, apart
from world.acts import ActError
from world.acts_vectors import (ALICE, APPEAL, APPRENTICE, BOB, FROM, KEEPER,
                                MODERATOR, RULES, _all, _base, _decision,
                                _did, _grant, _mark, _putting, _remove,
                                _restore, _take_back, _taking, grants, whole)

VECTORS = json.loads(acts_vectors.FILE.read_text(encoding="utf-8"))


GIVEN = object()


def check(room, given=GIVEN, rules=RULES, contents=None):
    """The room held to the trial grants, unless others are given."""
    return acts.check(room.entries,
                      room.contents if contents is None else contents,
                      _all(grants()) if given is GIVEN else given, rules)


def refusal(room, **more):
    """The reason and the place `room` is refused for."""
    try:
        check(room, **more)
    except ActError as e:
        return e.reason, e.where
    raise AssertionError("held")


def given_to(case, key):
    return case.get(key, VECTORS[key])


class TestTheVectors(unittest.TestCase):

    def test_the_file_is_what_this_code_writes_now(self):
        self.assertEqual(
            acts_vectors.FILE.read_text(encoding="utf-8"),
            acts_vectors.text(),
            "rewrite with: python3 -m world.acts_vectors")

    def test_the_names_and_reasons_are_the_modules(self):
        self.assertEqual(VECTORS["record"], acts.RECORD)
        self.assertEqual(VECTORS["acts"], acts.ACTS)
        self.assertEqual(VECTORS["own_acts"], acts.OWN_ACTS)
        self.assertEqual(VECTORS["ruled"], list(acts.RULED))
        self.assertEqual(VECTORS["max_chain"], acts.MAX_CHAIN)
        self.assertEqual(VECTORS["states"], list(acts.STATES))
        self.assertEqual(VECTORS["reasons"], list(acts.REASONS))
        self.assertEqual(len(set(acts.REASONS)), 24)
        self.assertEqual(len(set(acts.STATES)), 4)

    def test_every_room_that_holds_gives_its_states(self):
        seen = set()
        for case in VECTORS["holds"]:
            with self.subTest(case["name"]):
                got = acts.check(case["log"], case["contents"],
                                 given_to(case, "grants"),
                                 given_to(case, "rules"))
                self.assertEqual(got, case["states"])
                seen.update(got.values())
        self.assertEqual(seen, set(acts.STATES))

    def test_every_refused_room_is_refused_for_its_reason(self):
        seen = set()
        for case in VECTORS["refused"]:
            with self.subTest(case["name"]):
                with self.assertRaises(ActError) as c:
                    acts.check(case["log"], case["contents"],
                               given_to(case, "grants"),
                               given_to(case, "rules"))
                self.assertEqual(c.exception.reason, case["reason"])
                self.assertEqual(c.exception.where, case["where"])
                # The form itself has nothing against the log: only who
                # acted is at fault.
                apart.check(case["log"], case["contents"])
                seen.add(case["reason"])
        self.assertEqual(seen, set(acts.REASONS))

    def test_every_record_in_a_refused_room_is_signed_but_those_named(self):
        """One fault each: where the reason is not about a record that
        does not hold, every record a refused room carries holds."""
        for case in VECTORS["refused"]:
            if case["reason"] in (acts.NOT_A_RECORD, acts.NO_RECORD):
                continue
            with self.subTest(case["name"]):
                for entry in case["log"]:
                    held = case["contents"].get(entry["hash"], {})
                    if acts.RECORD in held:
                        records.check(held[acts.RECORD][1])

    def test_an_office_is_held_to_its_grant_on_its_own(self):
        for case in VECTORS["offices"]:
            with self.subTest(case["name"]):
                if case["reason"] is None:
                    acts.office_may(case["record"], case["act"],
                                    VECTORS["grants"], VECTORS["rules"])
                    continue
                with self.assertRaises(ActError) as c:
                    acts.office_may(case["record"], case["act"],
                                    VECTORS["grants"], VECTORS["rules"])
                self.assertEqual(c.exception.reason, case["reason"])
                self.assertIsNone(c.exception.where)

    def test_the_parties_are_public_keys_only(self):
        text = acts_vectors.FILE.read_text(encoding="utf-8")
        self.assertNotIn("secret", text.lower())
        for name, key in VECTORS["parties"].items():
            self.assertEqual(key, _did(name))


class TestTheListOfActs(unittest.TestCase):

    def test_each_kind_of_act_is_one_a_record_can_name(self):
        pattern = re.compile(
            records.SCHEMA["$defs"]["actKind"]["pattern"])
        for kind in acts.kinds_of_act():
            self.assertRegex(kind, pattern)
        self.assertEqual(acts.kinds_of_act(),
                         ["keep-field-public", "keep-field-redacted",
                          "redact-field", "remove-comment",
                          "restore-comment"])

    def test_every_one_of_the_forms_own_kinds_is_an_offices_or_an_authors(
            self):
        self.assertEqual(set(acts.ACTS) | set(acts.OWN_ACTS),
                         set(apart.OWN))
        self.assertFalse(set(acts.ACTS) & set(acts.OWN_ACTS))
        for fmt in (acts.DECISION, acts.GRANT, acts.COPY,
                    *acts.OWN_ACTS.values()):
            self.assertIn(fmt, records.KINDS)

    def test_what_the_rules_rule_can_never_be_one_of_the_forms_own(self):
        for kind in acts.RULED:
            self.assertFalse(acts.rules_ok(dict(RULES, on=dict(
                RULES["on"], **{kind: [apart.MARK]}))))
        self.assertTrue(acts.rules_ok(RULES))
        for odd in [None, [], "rules", {}, dict(RULES, room=None),
                    dict(RULES, authors=[]), dict(RULES, on=[]),
                    dict(RULES, authors={"said": "Key"}),
                    dict(RULES, authors={apart.REMOVED: "key"})]:
            self.assertFalse(acts.rules_ok(odd), odd)


class TestTheCheck(unittest.TestCase):

    def test_it_changes_nothing_it_is_given(self):
        room = whole()
        given = _all(grants())
        before = copy.deepcopy((room.entries, room.contents, given, RULES))
        acts.check(room.entries, room.contents, given, RULES)
        self.assertEqual((room.entries, room.contents, given, RULES),
                         before)

    def test_a_log_that_does_not_hold_is_the_forms_to_refuse(self):
        room, h = _base()
        log = copy.deepcopy(room.entries)
        log[3]["tick"] = 9
        with self.assertRaises(apart.Refused) as c:
            acts.check(log, room.contents, [], RULES)
        self.assertEqual(c.exception.reason, apart.CHAIN)

    def test_a_grant_is_in_force_from_its_first_second(self):
        room, h = _base()
        _remove(room, 5, h[4], _decision(
            MODERATOR, grants()["moderator"], "remove-comment", h[4], 5,
            [BOB], created=FROM))
        self.assertEqual(set(check(room).values()), {acts.HELD})

    def test_a_decision_may_be_dated_at_its_entrys_tick_or_before(self):
        for tick, held in [(0, True), (5, True), (6, False)]:
            room, h = _base()
            _remove(room, 5, h[4], _decision(
                MODERATOR, grants()["moderator"], "remove-comment", h[4],
                tick, [BOB]))
            if held:
                check(room)
            else:
                self.assertEqual(refusal(room), (acts.LATER, 7))

    def test_a_removal_after_a_restoring_needs_a_new_decision(self):
        g = grants()
        room, h = _base()
        first = _decision(MODERATOR, g["moderator"], "remove-comment", h[4],
                          5, [BOB])
        incident = _remove(room, 5, h[4], first)
        _restore(room, 6, incident, _decision(
            KEEPER, g["keeper"], "restore-comment", incident, 6, [BOB],
            grounds=(APPEAL,), supersedes=records.record_hash(first)))
        _remove(room, 7, h[4], _decision(
            MODERATOR, g["moderator"], "remove-comment", h[4], 7, [BOB]))
        self.assertEqual(list(check(room).values()), [acts.HELD] * 3)

    def test_the_first_fault_in_the_logs_order_is_the_one_named(self):
        g = grants()
        room, h = _base()
        _take_back(room, 5, h[3], _taking(BOB, h[3]))        # not the author
        _remove(room, 6, h[4], _decision(
            APPRENTICE, g["moderator"], "remove-comment", h[4], 6, [BOB]))
        self.assertEqual(refusal(room), (acts.NOT_AUTHOR, 7))

    def test_a_redacted_record_is_a_state_and_not_a_refusal(self):
        g = grants()
        room, h = _base()
        removal = _remove(room, 5, h[4], _decision(
            MODERATOR, g["moderator"], "remove-comment", h[4], 5, [BOB]))
        self.assertEqual(check(room), {removal: acts.HELD})
        mark = _mark(room, 6, removal, "record", take_out=False)
        # Marked and still there: nothing reads a field under a mark.
        self.assertEqual(check(room), {removal: acts.REDACTED})
        room.take_out(mark)
        self.assertEqual(check(room), {removal: acts.REDACTED})

    def test_a_redacted_decision_still_counts_as_named(self):
        """A removal's decision can't be used again by redacting the
        first record: the hash it is named by stays in the open."""
        g = grants()
        room, h = _base()
        first = _decision(MODERATOR, g["moderator"], "remove-comment", h[4],
                          5, [BOB])
        incident = _remove(room, 5, h[4], first)
        _mark(room, 6, incident, "record")
        _restore(room, 7, incident, _decision(
            KEEPER, g["keeper"], "restore-comment", incident, 7, [BOB],
            grounds=(APPEAL,), supersedes=records.record_hash(first)))
        _remove(room, 8, h[4], first)
        self.assertEqual(refusal(room), (acts.TWICE, 10))

    def test_a_taking_back_holds_to_its_place_after_a_redacted_putting_back(
            self):
        """The putting back a second taking back names is known from
        the open fields, whatever became of its record."""
        room, h = _base()
        taking = _take_back(room, 5, h[3], _taking(ALICE, h[3]))
        putting = room.append(6, apart.PUT_BACK, None,
                              {"taken_back": taking},
                              {"record": _putting(ALICE, taking)})
        _mark(room, 7, putting, "record")
        again = _take_back(room, 8, h[3], _taking(ALICE, h[3],
                                                  after=putting))
        self.assertEqual(check(room), {taking: acts.HELD,
                                       putting: acts.REDACTED,
                                       again: acts.HELD})

    def test_an_authors_key_once_redacted_leaves_the_signer_unchecked(self):
        room, h = _base()
        taking = _take_back(room, 5, h[3], _taking(BOB, h[3]))
        self.assertEqual(refusal(room), (acts.NOT_AUTHOR, 7))
        _mark(room, 6, h[3], "key")
        # With the key gone no reader can tell: it rests on the world
        # having checked when it wrote the entry.
        self.assertEqual(check(room), {taking: acts.UNCHECKED})

    def test_a_key_under_a_mark_is_not_read_even_while_it_is_there(self):
        room, h = _base()
        taking = _take_back(room, 5, h[3], _taking(BOB, h[3]))
        mark = _mark(room, 6, h[3], "key", take_out=False)
        self.assertIn("key", room.contents[h[3]])
        self.assertEqual(check(room), {taking: acts.UNCHECKED})
        room.take_out(mark)
        self.assertEqual(check(room), {taking: acts.UNCHECKED})

    def test_an_office_is_shown_by_its_key(self):
        g = grants()
        room, h = _base()
        record = _decision(MODERATOR, g["moderator"], "remove-comment", h[4],
                           5, [BOB])
        removal = _remove(room, 5, h[4], record)
        entry = room.entries[-1]
        self.assertEqual(entry["data"]["office"], _did(MODERATOR))
        self.assertEqual(entry["data"]["decision"],
                         records.record_hash(record))
        self.assertEqual(check(room), {removal: acts.HELD})

    def test_a_grant_from_another_room_counts_for_nothing_here(self):
        other = dict(RULES, room=_did("another trial room"))
        room, h = _base()
        _remove(room, 5, h[4], _decision(
            MODERATOR, grants()["moderator"], "remove-comment", h[4], 5,
            [BOB]))
        self.assertEqual(refusal(room, rules=other), (acts.ELSEWHERE, 7))

    def test_a_grant_named_but_not_holding_is_never_followed(self):
        """A record that is not a grant, or does not hold, stops the
        chain where it is met, before anything it says is read."""
        g = grants()
        forged = dict(g["moderator"], holder=_did(APPRENTICE))
        room, h = _base()
        _remove(room, 5, h[4], _decision(
            APPRENTICE, forged, "remove-comment", h[4], 5, [BOB]))
        self.assertEqual(refusal(room, given=[forged]),
                         (acts.BAD_GRANT, 7))

    def test_the_longest_chain_holds_and_one_more_does_not(self):
        for length, reason in [(acts.MAX_CHAIN, None),
                               (acts.MAX_CHAIN + 1, acts.TOO_DEEP)]:
            chain, last = acts_vectors._chain(length)
            room, h = _base()
            _remove(room, 5, h[4], _decision(
                last, chain[-1], "remove-comment", h[4], 5, [BOB]))
            if reason is None:
                check(room, given=chain)
            else:
                self.assertEqual(refusal(room, given=chain), (reason, 7))

    def test_what_can_not_be_a_record_among_the_grants_is_passed_over(self):
        room = whole()
        given = _all(grants()) + [None, 5, "a grant", [], {"format": 1},
                                  {"a": 1.5}]
        self.assertEqual(check(room, given=given), check(room))

    def test_grants_that_are_not_a_list_are_refused(self):
        room, _ = _base()
        for odd in [None, {}, "grants", 5]:
            self.assertEqual(refusal(room, given=odd), (acts.RULES, None))

    def test_a_grant_a_room_gives_for_another_act_does_not_stretch(self):
        g = grants()
        keeps = _grant(acts_vectors.ROOM, MODERATOR, ["keep-field-public"])
        room, h = _base()
        _remove(room, 5, h[4], _decision(
            MODERATOR, keeps, "remove-comment", h[4], 5, [BOB]))
        self.assertEqual(refusal(room, given=_all(g) + [keeps]),
                         (acts.NOT_ALLOWED, 7))


if __name__ == "__main__":
    unittest.main()

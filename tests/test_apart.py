"""A log whose fields are kept apart (world/apart.py; course step 3b,
parts two to four): the fingerprint, the two checks, the five states of
a field, a redaction from its mark to the decision that answers it, the
function that joins entries and contents, and the shared vectors in
vectors/log-apart.json, which rust/world-log reads too."""
import copy
import json
import unittest

from world import World, apart
from world.apart import Log, Refused
from world.apart_vectors import (APPEAL, FIRST, GROUND, KEEPER, MODERATOR,
                                 OFFICE, PRIVATE, TABLE, VALUES_ALLOWED,
                                 WRITTEN, acted_on, log_apart, place,
                                 trial_decision, trial_salt)
from world.vectors import FOLDER, world_log


def vectors():
    return json.loads((FOLDER / "log-apart.json").read_text(encoding="ascii"))


def room(salt=apart.new_salt):
    log = Log(TABLE, FIRST, salt=salt)
    for step in WRITTEN:
        log.append(*step)
    return log


def mark(log, entry, field, tick=5, **more):
    """A mark as an office writes one. The field stays in the contents
    until it is taken out."""
    return log.mark(tick, entry, field, OFFICE, PRIVATE, **more)


def keep(log, a_mark, n=1, tick=6, **more):
    """The decision to keep public a field still in the contents."""
    entry, field = log._scan.marks[a_mark]
    salt, value = log.contents[entry][field]
    return log.keep_public(tick, a_mark, salt, value, KEEPER, APPEAL,
                           trial_decision(n), **more)


def stays(log, a_mark, n=1, tick=6, **more):
    return log.stays_redacted(tick, a_mark, KEEPER, APPEAL,
                              trial_decision(n), **more)


def reason(log, contents):
    try:
        apart.check(log, contents)
    except Refused as e:
        return e.reason
    return None


def refusal(log, contents):
    """The reason and the place, as the vectors write them."""
    try:
        apart.check(log, contents)
    except Refused as e:
        return e.reason, place(e)
    return None


class TestTheFingerprint(unittest.TestCase):

    def test_it_is_the_hash_of_salt_name_and_value_as_the_log_writes(self):
        salt = "00112233445566778899aabbccddeeff"
        self.assertEqual(
            apart.fingerprint_text(salt, "text", "café"),
            '["00112233445566778899aabbccddeeff","text","caf\\u00e9"]')
        # In a shell: printf '%s' '["0011...","text","café"]' | sha256sum
        import hashlib
        self.assertEqual(
            apart.fingerprint(salt, "text", "café"),
            hashlib.sha256(
                b'["00112233445566778899aabbccddeeff","text","caf\\u00e9"]'
            ).hexdigest())

    def test_the_salt_the_name_and_the_value_each_change_it(self):
        base = apart.fingerprint(trial_salt(0), "text", "hello")
        self.assertNotEqual(base,
                            apart.fingerprint(trial_salt(1), "text", "hello"))
        self.assertNotEqual(base,
                            apart.fingerprint(trial_salt(0), "name", "hello"))
        self.assertNotEqual(base,
                            apart.fingerprint(trial_salt(0), "text", "hullo"))

    def test_a_number_and_its_text_differ(self):
        self.assertNotEqual(apart.fingerprint(trial_salt(0), "time", 1),
                            apart.fingerprint(trial_salt(0), "time", "1"))
        self.assertNotEqual(apart.fingerprint(trial_salt(0), "time", 1),
                            apart.fingerprint(trial_salt(0), "time", True))

    def test_a_new_salt_is_32_hex_digits_and_fresh(self):
        salts = {apart.new_salt() for _ in range(200)}
        self.assertEqual(len(salts), 200)
        for salt in salts:
            self.assertRegex(salt, r"\A[0-9a-f]{32}\Z")

    def test_a_bad_salt_name_or_value_is_refused(self):
        for salt in ["", "0" * 31, "0" * 33, "G" * 32, "A" * 32, 5, None,
                     "0" * 31 + "\n"]:
            with self.subTest(salt=salt), self.assertRaises(Refused) as c:
                apart.fingerprint(salt, "text", "v")
            self.assertEqual(c.exception.reason, apart.SALT)
        for name in ["", "Text", "1st", "a-b", "a b", "k" * 65, 5, None,
                     "text\n"]:
            with self.subTest(name=name), self.assertRaises(Refused) as c:
                apart.fingerprint(trial_salt(0), name, "v")
            self.assertEqual(c.exception.reason, apart.ENTRY)
        with self.assertRaises(Refused) as c:
            apart.fingerprint(trial_salt(0), "text", 1.5)
        self.assertEqual(c.exception.reason, apart.VALUE)


class TestValues(unittest.TestCase):

    def test_the_allowed_values_are_allowed(self):
        for value in VALUES_ALLOWED:
            with self.subTest(value=value):
                self.assertTrue(apart.value_allowed(value))

    def test_what_json_can_hold_and_is_refused(self):
        for case in vectors()["values_refused"]:
            with self.subTest(case["name"]):
                self.assertFalse(apart.value_allowed(case["value"]))

    def test_what_only_python_can_hold_is_refused(self):
        class Text(str):
            pass

        class Whole(int):
            pass

        class Many(list):
            pass

        class Named(dict):
            pass

        for value in [float("nan"), float("inf"), -0.0, 1e300, b"bytes",
                      ("a", "b"), {"a"}, Text("a"), Whole(1), Many(),
                      Named(), object(), "\ud800", {"\ud800": 1}, {1: "a"},
                      {None: "a"}, ["a", ("b",)], 2 ** 53, -(2 ** 53)]:
            with self.subTest(value=repr(value)):
                self.assertFalse(apart.value_allowed(value))

    def test_nesting_stops_at_the_limit(self):
        def nested(depth, wrap):
            value = 0
            for _ in range(depth):
                value = wrap(value)
            return value
        for wrap in (lambda v: [v], lambda v: {"k": v}):
            self.assertTrue(
                apart.value_allowed(nested(apart.MAX_NESTING, wrap)))
            self.assertFalse(
                apart.value_allowed(nested(apart.MAX_NESTING + 1, wrap)))


class TestWriting(unittest.TestCase):

    def test_the_chain_is_checked_by_the_kernels_own_check(self):
        log = room()
        self.assertTrue(World.verify_log(log.entries))
        self.assertEqual(log.head(), log.entries[-1]["hash"])

    def test_no_value_kept_apart_is_anywhere_in_the_log(self):
        log = room()
        text = json.dumps(log.entries)
        for _, _, _, _, kept in WRITTEN:
            for value in kept.values():
                if isinstance(value, str):
                    self.assertNotIn(json.dumps(value), text)
        for fields in log.contents.values():
            for salt, _ in fields.values():
                self.assertNotIn(salt, text)

    def test_the_log_is_the_same_whatever_is_taken_out(self):
        log = room()
        before = json.dumps(log.entries, sort_keys=True)
        contents = copy.deepcopy(log.contents)
        for fields in contents.values():
            fields.clear()
        self.assertEqual(json.dumps(log.entries, sort_keys=True), before)
        self.assertTrue(World.verify_log(log.entries))
        states = apart.check(log.entries, contents)
        self.assertEqual({s for e in states.values() for s in e.values()},
                         {apart.MISSING})

    def test_two_runs_give_different_logs(self):
        self.assertNotEqual(room().head(), room().head())

    def test_the_same_words_twice_have_different_fingerprints(self):
        log = Log({"said": ["text"]})
        one = log.append(1, "said", None, {}, {"text": "yes"})
        two = log.append(2, "said", None, {}, {"text": "yes"})
        prints = [e["apart"]["text"] for e in log.entries[1:]]
        self.assertNotEqual(prints[0], prints[1])
        self.assertEqual(apart.check(log.entries, log.contents),
                         {one: {"text": "present"}, two: {"text": "present"}})

    def test_what_is_given_is_copied(self):
        log = Log({"showed": ["thing"]})
        thing, data = {"words": ["a"]}, {"where": ["here"]}
        log.append(1, "showed", None, data, {"thing": thing})
        thing["words"].append("b")
        data["where"].append("there")
        self.assertEqual(apart.check(log.entries, log.contents),
                         {log.head(): {"thing": "present"}})
        self.assertEqual(log.entries[-1]["data"], {"where": ["here"]})

    def test_a_refused_entry_is_not_appended_and_the_log_goes_on(self):
        log = room()
        entries = copy.deepcopy(log.entries)
        contents = copy.deepcopy(log.contents)
        refusals = [
            ((9, "said", None, {}, {"name": "ada"}), apart.UNTABLED),
            ((9, "said", None, {"text": "open"}, {}), apart.OPEN),
            ((9, "said", None, {}, {"text": 1.5}), apart.VALUE),
            ((9, "said", None, {}, {"Text": "x"}), apart.ENTRY),
            ((9, "said", None, None, {}), apart.ENTRY),
            ((9, 5, None, {}, {}), apart.ENTRY),
        ]
        for step, why in refusals:
            with self.subTest(why), self.assertRaises(Refused) as c:
                log.append(*step)
            self.assertEqual(c.exception.reason, why)
            self.assertEqual(log.entries, entries)
            self.assertEqual(log.contents, contents)
        # The same for a mark and for what answers one.
        said = entries[3]["hash"]
        salt, value = contents[said]["text"]
        attempts = [
            (lambda: mark(log, log.head(), "nothing"), apart.BAD_MARK),
            (lambda: mark(log, log.head(), "nothing",
                          apart={"reason": "kept apart, and still refused"}),
             apart.BAD_MARK),
            (lambda: log.mark(9, said, "text", "", PRIVATE), apart.BAD_MARK),
            (lambda: log.keep_public(9, log.head(), salt, value, KEEPER,
                                     APPEAL, trial_decision(1)),
             apart.BAD_KEPT),
            (lambda: stays(log, log.head()), apart.BAD_STAYS),
        ]
        for attempt, why in attempts:
            with self.subTest(why), self.assertRaises(Refused) as c:
                attempt()
            self.assertEqual(c.exception.reason, why)
            self.assertEqual(log.entries, entries)
            self.assertEqual(log.contents, contents)
        # The log still takes an entry, and still holds.
        made = mark(log, said, "text", tick=9, apart={"reason": "asked"})
        states = apart.check(log.entries, log.contents)
        self.assertEqual(states[said]["text"], "unfinished")
        self.assertEqual(states[made], {"reason": "present"})

    def test_a_value_too_deep_to_copy_is_refused_not_a_crash(self):
        log = Log({"showed": ["thing"]})
        deep = "x"
        for _ in range(100000):
            deep = [deep]
        with self.assertRaises(Refused) as c:
            log.append(1, "showed", None, {}, {"thing": deep})
        self.assertEqual(c.exception.reason, apart.VALUE)
        with self.assertRaises(Refused) as c:
            log.append(1, "showed", None, {}, ["thing"])
        self.assertEqual(c.exception.reason, apart.ENTRY)
        self.assertEqual(len(log.entries), 1)

    def test_what_python_can_hold_and_json_cannot_is_never_written(self):
        # A key that isn't text is written by JSON as text: True as
        # "true", a field's name. It would put a field the table keeps
        # apart into the open, in the chain, for good.
        log = Log({"said": ["null", "true"], "showed": ["thing"]})
        before = copy.deepcopy(log.entries)
        nan = float("nan")
        for data in [{True: "in the open"}, {None: "in the open"},
                     {False: 1}, {1: "a"}, {"deep": {True: 1}},
                     {"list": [{None: 1}]}, {"height": 1.5}, {"n": nan},
                     {"n": float("inf")}, {"n": 2 ** 53}, {"n": 2 ** 64},
                     {"n": -(2 ** 63) - 1}, {"text": "\ud800"},
                     {"\ud800": 1}, {"where": None}, {"set": {1, 2}},
                     {"bytes": b"x"}, {"pair": (1, 2)}, [], None, "data"]:
            with self.subTest(data=repr(data)), \
                    self.assertRaises(Refused) as c:
                log.append(1, "said", None, data, {})
            self.assertEqual(c.exception.reason, apart.ENTRY)
            self.assertEqual(c.exception.where, 1)
        for tick in [1.5, "1", -1, 2 ** 53, None, True, nan]:
            with self.subTest(tick=repr(tick)), \
                    self.assertRaises(Refused) as c:
                log.append(tick, "said", None, {}, {})
            self.assertEqual(c.exception.reason, apart.ENTRY)
        for kind in ["\ud800", 5, None, b"said"]:
            with self.subTest(kind=repr(kind)), \
                    self.assertRaises(Refused) as c:
                log.append(1, kind, None, {}, {})
            self.assertEqual(c.exception.reason, apart.ENTRY)
        for agent in ["\ud800", 5, ["office"], True]:
            with self.subTest(agent=repr(agent)), \
                    self.assertRaises(Refused) as c:
                log.append(1, "said", agent, {}, {})
            self.assertEqual(c.exception.reason, apart.ENTRY)
        deep = "x"
        for _ in range(100000):
            deep = [deep]
        with self.assertRaises(Refused) as c:
            log.append(1, "said", None, {"deep": deep}, {})
        self.assertEqual(c.exception.reason, apart.ENTRY)
        self.assertEqual(log.entries, before)
        self.assertEqual(log.contents, {})
        log.append(apart.MAX_WHOLE, "said", "an office",
                   {"n": apart.MAX_WHOLE}, {"true": "kept apart"})
        self.assertEqual(len(log.entries), 2)

    def test_a_log_reads_back_from_json_as_it_was_written(self):
        # What is checked in memory is what is checked from a file.
        log = room()
        mark(log, log.entries[3]["hash"], "text", apart={"reason": "asked"})
        entries = json.loads(json.dumps(log.entries))
        contents = json.loads(json.dumps(log.contents))
        self.assertEqual(entries, log.entries)
        self.assertEqual(contents, log.contents)
        self.assertEqual(apart.check(entries, contents),
                         apart.check(log.entries, log.contents))
        self.assertEqual(apart.join(entries, contents),
                         apart.join(log.entries, log.contents))

    def test_a_salt_source_that_repeats_or_is_wrong_is_refused(self):
        log = Log({"said": ["key", "text"]},
                  salt=lambda: "0" * 32)
        with self.assertRaises(Refused) as c:
            log.append(1, "said", None, {}, {"key": "k", "text": "t"})
        self.assertEqual(c.exception.reason, apart.SALT_TWICE)
        log.append(1, "said", None, {}, {"text": "t"})
        with self.assertRaises(Refused) as c:
            log.append(2, "said", None, {}, {"text": "u"})
        self.assertEqual(c.exception.reason, apart.SALT_TWICE)
        self.assertEqual(len(log.entries), 2)
        for bad in ["0" * 31, "A" * 32, 7]:
            log = Log({"said": ["text"]}, salt=lambda bad=bad: bad)
            with self.assertRaises(Refused) as c:
                log.append(1, "said", None, {}, {"text": "t"})
            self.assertEqual(c.exception.reason, apart.SALT)

    def test_the_form_and_the_table_are_not_given_as_data(self):
        for key in ("form", "kept_apart"):
            with self.assertRaises(ValueError):
                Log(TABLE, {key: "mine"})

    def test_a_table_that_is_not_well_formed_is_refused_at_the_start(self):
        # A table holding nothing or a fraction is refused as a table
        # too, as the check refuses it, not as an entry out of form.
        for table in [{"said": ["text", "key"]}, {"said": "text"}, [],
                      {"said": ["Text"]}, {"said": [None]}, {"said": [1.5]},
                      {"said": None}, None, 1.5, {"said": ["text", None]}]:
            with self.subTest(table=table), self.assertRaises(Refused) as c:
                Log(table)
            self.assertEqual(c.exception.reason, apart.TABLE)

    def test_the_first_entrys_own_kind_can_keep_fields_apart(self):
        log = Log({"world_created": ["founder"]}, kind="world_created")
        self.assertEqual(apart.check(log.entries, log.contents), {})
        with self.assertRaises(Refused) as c:
            Log({"world_created": ["form"]})
        self.assertEqual(c.exception.reason, apart.OPEN)


class TestChecking(unittest.TestCase):

    def test_the_kernels_own_log_is_not_in_this_form(self):
        self.assertEqual(reason(world_log(), {}), apart.NO_FORM)

    def test_any_change_to_the_contents_is_caught(self):
        log = room()
        whole = apart.check(log.entries, log.contents)
        for entry, fields in log.contents.items():
            for name, (salt, value) in fields.items():
                for changed in [
                        [salt, [value]],
                        [salt[:-1] + ("0" if salt[-1] != "0" else "1"),
                         value]]:
                    contents = copy.deepcopy(log.contents)
                    contents[entry][name] = changed
                    with self.subTest(entry=entry, name=name):
                        self.assertEqual(reason(log.entries, contents),
                                         apart.FINGERPRINT)
        self.assertEqual(apart.check(log.entries, log.contents), whole)

    def test_a_field_cannot_be_moved_to_another_entry_or_name(self):
        log = room()
        hashes = [e["hash"] for e in log.entries]
        contents = copy.deepcopy(log.contents)
        contents[hashes[3]]["text"] = log.contents[hashes[4]]["text"]
        self.assertEqual(reason(log.entries, contents), apart.FINGERPRINT)
        contents = copy.deepcopy(log.contents)
        contents[hashes[3]]["text"] = log.contents[hashes[3]]["key"]
        self.assertEqual(reason(log.entries, contents), apart.FINGERPRINT)

    def test_every_refusal_has_a_place(self):
        log = room()
        try:
            apart.check(log.entries,
                        {log.head(): {"thing": ["0" * 32, "x"]}})
        except Refused as e:
            self.assertEqual(e.where, (log.head(), "thing"))
            self.assertIn(log.head(), str(e))
        entries = copy.deepcopy(log.entries[:2])
        del entries[1]["apart"]
        scan = apart._Scan()
        scan.take(entries[0])
        with self.assertRaises(Refused) as c:
            scan.take(entries[1])
        self.assertEqual(c.exception.reason, apart.ENTRY)
        self.assertEqual(c.exception.where, 1)
        # The form and the table are the first entry's: no place is given.
        with self.assertRaises(Refused) as c:
            apart._Scan().take(entries[1])
        self.assertEqual(c.exception.reason, apart.NO_FORM)
        self.assertIsNone(c.exception.where)

    def test_nothing_sits_beside_an_entrys_data(self):
        # The table reaches `data` and `apart` only, so an entry holds
        # nothing else: a field at the top would be in the open whatever
        # the table says.
        log = room()
        entries = copy.deepcopy(log.entries)
        scan = apart._Scan()
        for entry in entries[:3]:
            scan.take(entry)
        from world.core import _digest
        extra = {k: v for k, v in entries[3].items() if k != "hash"}
        extra["text"] = "in the open"
        extra["hash"] = _digest(extra)
        with self.assertRaises(Refused) as c:
            scan.take(extra)
        self.assertEqual(c.exception.reason, apart.ENTRY)
        self.assertEqual(c.exception.where, 3)
        scan.take(entries[3])   # the scan was not changed by the refusal

    def test_contents_only_python_can_hold_are_refused(self):
        log = room()
        target = log.entries[1]["hash"]
        for contents in [{1: {}}, {target: {}, 1: {}}, {None: {}},
                         {target: {1: ["0" * 32, "x"]}},
                         {target: {"name": ("0" * 32, "x")}},
                         {target: ("name",)}, (), None, "contents"]:
            with self.subTest(contents=repr(contents)):
                self.assertEqual(reason(log.entries, contents),
                                 apart.CONTENTS)

    def test_the_first_fault_in_the_logs_order_is_the_one_named(self):
        from world.core import _digest

        def rehash(entry):
            body = {k: v for k, v in entry.items() if k != "hash"}
            entry["hash"] = _digest(body)

        log = room()
        # A fault in what an entry says, and a broken link after it:
        # the earlier entry's fault is the one named.
        entries = copy.deepcopy(log.entries)
        entries[2]["data"]["height"] = 1.5
        rehash(entries[2])     # its own hash is right; entry 3's link isn't
        self.assertEqual(refusal(entries, {}), (apart.ENTRY, 2))
        entries[2] = copy.deepcopy(log.entries[2])
        entries[5]["data"]["height"] = 1.5
        entries[3]["prev"] = "f" * 64
        self.assertEqual(refusal(entries, {}), (apart.CHAIN, 3))
        # Within one entry: its link, then what it says, then its hash.
        entries = copy.deepcopy(log.entries)
        entries[2]["data"]["height"] = 1.5
        self.assertEqual(refusal(entries, {}), (apart.ENTRY, 2))
        entries[2]["prev"] = "f" * 64
        self.assertEqual(refusal(entries, {}), (apart.CHAIN, 2))
        entries = copy.deepcopy(log.entries)
        entries[2]["tick"] = 99
        self.assertEqual(refusal(entries, {}), (apart.CHAIN, 2))
        # A log that is refused here for its chain is refused by the
        # kernel's own check, and one that holds here holds there.
        self.assertFalse(World.verify_log(entries))
        self.assertTrue(World.verify_log(log.entries))

    def test_the_contents_are_read_in_ascending_order(self):
        # Whatever order a map was built in: Python keeps that order,
        # Rust does not, and both must name the same fault.
        log = room()
        hashes = sorted(e["hash"] for e in log.entries[1:3])
        low, high = hashes

        def changed(entry, field):
            salt, value = log.contents[entry][field]
            return [salt, value + "!"]

        def capitals(entry, field):
            salt, value = log.contents[entry][field]
            return [salt.upper(), value]

        for first, second in [(low, high), (high, low)]:
            contents = {first: {"name": changed(first, "name")},
                        second: {"name": capitals(second, "name")}}
            for built in (contents, dict(reversed(list(contents.items())))):
                want = (apart.FINGERPRINT if first == low else apart.SALT,
                        [low, "name"])
                self.assertEqual(refusal(log.entries, built), want)
        for fields in [{"name": capitals(low, "name"),
                        "key": changed(low, "key")},
                       {"key": changed(low, "key"),
                        "name": capitals(low, "name")}]:
            self.assertEqual(refusal(log.entries, {low: fields}),
                             (apart.FINGERPRINT, [low, "key"]))

    def test_a_mark_stands_until_it_is_answered(self):
        log = room()
        target = log.entries[3]["hash"]

        def state():
            return apart.check(log.entries, log.contents)[target]["text"]
        self.assertEqual(state(), "present")
        one = mark(log, target, "text")
        self.assertEqual(state(), "unfinished")
        keep(log, one)
        self.assertEqual(state(), "kept public")
        # Whoever publishes the log may still lose the field: the record
        # says it is public, and it is not there.
        del log.contents[target]["text"]
        self.assertEqual(state(), "missing")
        mark(log, target, "text", tick=8)
        self.assertEqual(state(), "redacted")

    def test_a_mark_cannot_name_itself_or_what_comes_after(self):
        log = room()
        later = Log(TABLE, FIRST)
        with self.assertRaises(Refused) as c:
            mark(log, later.head(), "name")
        self.assertEqual(c.exception.reason, apart.BAD_MARK)


class TestRedacting(unittest.TestCase):
    """Redacted first, decided after (docs/research/REDACTION.md,
    decisions 4 and 5): a mark, and the one entry that answers it."""

    def setUp(self):
        self.log = room()
        self.said = self.log.entries[3]["hash"]

    def of(self, field="text"):
        return apart.redactions(self.log.entries)[self.said][field]

    def state(self, field="text"):
        return apart.check(self.log.entries,
                           self.log.contents)[self.said][field]

    def test_a_mark_says_its_office_and_its_ground_and_no_decision(self):
        made = mark(self.log, self.said, "text")
        data = self.log.entries[-1]["data"]
        self.assertEqual(data, {"entry": self.said, "field": "text",
                                "office": OFFICE, "ground": PRIVATE})
        self.assertEqual(self.of(), [
            {"id": made, "short": made[:12], "state": "open"}])

    def test_a_mark_without_its_office_or_ground_is_refused(self):
        for office, ground in [("", PRIVATE), (["a", "b"], PRIVATE),
                               (OFFICE, "private"), (OFFICE, {}),
                               (OFFICE, {"kind": "whim", "ref": "x"}),
                               (OFFICE, {"kind": "record", "ref": "x"})]:
            with self.subTest(office=office, ground=ground):
                with self.assertRaises(Refused) as c:
                    self.log.mark(5, self.said, "text", office, ground)
                self.assertEqual(c.exception.reason, apart.BAD_MARK)
        # Nothing is not a value an open field can have, here as anywhere.
        with self.assertRaises(Refused) as c:
            self.log.mark(5, self.said, "text", None, PRIVATE)
        self.assertEqual(c.exception.reason, apart.ENTRY)

    def test_a_field_has_one_mark_that_is_open_or_stands(self):
        first = mark(self.log, self.said, "text")
        with self.assertRaises(Refused) as c:
            mark(self.log, self.said, "text")
        self.assertEqual(c.exception.reason, apart.BAD_MARK)
        # Another field of the same entry is free.
        mark(self.log, self.said, "time")
        self.log.take_out(first)
        stays(self.log, first)
        with self.assertRaises(Refused) as c:
            mark(self.log, self.said, "text")
        self.assertEqual(c.exception.reason, apart.BAD_MARK)

    def test_kept_public_answers_a_mark_and_the_field_can_be_marked_again(
            self):
        first = mark(self.log, self.said, "text")
        keep(self.log, first)
        self.assertEqual(self.state(), "kept public")
        again = mark(self.log, self.said, "text", tick=7)
        self.log.take_out(again)
        self.assertEqual(self.state(), "redacted")
        self.assertEqual([r["state"] for r in self.of()],
                         ["kept public", "open"])
        self.assertEqual([r["id"] for r in self.of()], [first, again])

    def test_a_mark_is_answered_once(self):
        for first, second, why in [(keep, keep, apart.BAD_KEPT),
                                   (keep, stays, apart.BAD_STAYS),
                                   (stays, stays, apart.BAD_STAYS)]:
            with self.subTest(first=first.__name__, second=second.__name__):
                log = room()
                made = mark(log, log.entries[3]["hash"], "text")
                if first is stays:
                    log.take_out(made)
                first(log, made)
                with self.assertRaises(Refused) as c:
                    if second is keep:
                        # Still in the contents after the first keeping.
                        keep(log, made, 2)
                    else:
                        stays(log, made, 2)
                self.assertEqual(c.exception.reason, why)

    def test_what_stands_is_never_made_public_again(self):
        made = mark(self.log, self.said, "text")
        salt, value = self.log.take_out(made)
        stays(self.log, made)
        with self.assertRaises(Refused) as c:
            self.log.keep_public(9, made, salt, value, KEEPER, APPEAL,
                                 trial_decision(2))
        self.assertEqual(c.exception.reason, apart.BAD_KEPT)
        # Refused for the mark, before the salt and value are looked at.
        with self.assertRaises(Refused) as c:
            self.log.keep_public(9, made, salt, value + "!", KEEPER, APPEAL,
                                 trial_decision(2))
        self.assertEqual(c.exception.reason, apart.BAD_KEPT)
        self.assertEqual(c.exception.where, len(self.log.entries))
        self.assertEqual(self.state(), "redacted")
        self.assertEqual(self.of()[0]["state"], "stands")

    def test_an_answer_says_its_office_ground_and_decision(self):
        made = mark(self.log, self.said, "text")
        salt, value = self.log.take_out(made)
        good = (KEEPER, APPEAL, trial_decision(1))
        for i, bad in [(0, ""), (0, 7), (1, {}), (1, "appeal"),
                       (2, ""), (2, "f" * 63), (2, "F" * 64)]:
            said = list(good)
            said[i] = bad
            with self.subTest(i=i, bad=bad):
                with self.assertRaises(Refused) as c:
                    self.log.keep_public(6, made, salt, value, *said)
                self.assertEqual(c.exception.reason, apart.BAD_KEPT)
                with self.assertRaises(Refused) as c:
                    self.log.stays_redacted(6, made, *said)
                self.assertEqual(c.exception.reason, apart.BAD_STAYS)

    def whole(self):
        """Everything the writer holds, as one text: its entries, its
        contents, what it remembers of the salts it has used, and all
        that its scan of the log keeps."""
        return repr([vars(self.log), vars(self.log._scan)])

    def test_neither_the_value_nor_its_salt_is_left_once_taken_out(self):
        salt, value = self.log.contents[self.said]["text"]
        made = mark(self.log, self.said, "text")
        before = copy.deepcopy(self.log.entries)
        # Both are there to be found, before.
        self.assertIn(salt, self.whole())
        self.assertIn(value, self.whole())
        self.assertEqual(self.log.take_out(made), [salt, value])
        kept = json.dumps([self.log.entries, self.log.contents])
        self.assertNotIn(salt, kept)
        self.assertNotIn(value, kept)
        # Nor anywhere else in the writer: a salt it kept would let
        # whoever reads its memory test guesses against the fingerprint,
        # which is public.
        self.assertNotIn(salt, self.whole())
        self.assertNotIn(value, self.whole())
        self.assertEqual(self.log.entries, before)   # the log is not touched
        self.assertEqual(self.state(), "redacted")
        # The other fields of the entry are still there.
        self.assertEqual(sorted(self.log.contents[self.said]),
                         ["key", "time"])

    def test_a_salt_is_never_used_again_though_its_field_is_gone(self):
        # The writer remembers a salt by its hash alone, and that is
        # enough to refuse a source that repeats.
        again = "5a" * 16
        log = Log({"said": ["text"]}, salt=lambda: again)
        said = log.append(1, "said", None, {}, {"text": "once"})
        made = log.mark(2, said, "text", OFFICE, PRIVATE)
        self.assertEqual(log.take_out(made), [again, "once"])
        self.assertNotIn(again, repr([vars(log), vars(log._scan)]))
        with self.assertRaises(Refused) as c:
            log.append(3, "said", None, {}, {"text": "twice"})
        self.assertEqual(c.exception.reason, apart.SALT_TWICE)
        self.assertEqual(len(log.entries), 3)

    def test_the_forms_own_kinds_say_in_the_open_exactly_what_is_named(
            self):
        self.assertEqual(set(apart.SAYS), set(apart.OWN))
        # A mark can hold no decision, and nothing about what was
        # there; a decision, nothing beside what it must say. Each is
        # refused for its own kind's reason, and nothing is written.
        made = mark(self.log, self.said, "text")
        entries = copy.deepcopy(self.log.entries)
        raw = copy.deepcopy(self.log.entries)
        for kind, data, why in [
                (apart.MARK, {"entry": self.said, "field": "time",
                              "office": OFFICE, "ground": PRIVATE,
                              "decision": trial_decision(1)},
                 apart.BAD_MARK),
                (apart.MARK, {"entry": self.said, "field": "time",
                              "office": OFFICE, "ground": PRIVATE,
                              "what": "the time of day"}, apart.BAD_MARK),
                (apart.KEPT, {"mark": made, "office": KEEPER,
                              "ground": APPEAL,
                              "decision": trial_decision(1), "note": "x"},
                 apart.BAD_KEPT),
                (apart.STAYS, {"mark": made, "office": KEEPER,
                               "ground": APPEAL,
                               "decision": trial_decision(1), "note": "x"},
                 apart.BAD_STAYS)]:
            with self.subTest(kind=kind, data=sorted(data)):
                body = {"tick": 9, "kind": kind, "agent": None,
                        "data": data, "apart": {}, "prev": raw[-1]["hash"]}
                log = raw + [{**body, "hash": apart._digest(body)}]
                self.assertEqual(refusal(log, {}), (why, len(raw)))
        self.assertEqual(self.log.entries, entries)

    def test_no_table_keeps_apart_what_an_own_kind_says_in_the_open(self):
        for kind, keys in apart.SAYS.items():
            for key in keys:
                with self.subTest(kind=kind, key=key):
                    with self.assertRaises(Refused) as c:
                        Log({kind: [key]})
                    self.assertEqual(c.exception.reason, apart.TABLE)
        # What else such an entry carries may be kept apart.
        log = Log({apart.MARK: ["reason"], "said": ["text"]})
        said = log.append(1, "said", None, {}, {"text": "t"})
        log.mark(2, said, "text", OFFICE, PRIVATE, apart={"reason": "r"})
        self.assertEqual(len(log.entries), 3)

    def test_an_entry_with_nothing_left_keeps_no_empty_map(self):
        entered = self.log.entries[1]["hash"]
        for field in ("key", "name"):
            self.log.take_out(mark(self.log, entered, field))
        self.assertNotIn(entered, self.log.contents)
        self.assertEqual(
            apart.check(self.log.entries, self.log.contents)[entered],
            {"key": "redacted", "name": "redacted"})

    def test_taking_out_needs_a_mark_that_stands_and_a_field_that_is_there(
            self):
        with self.assertRaises(ValueError):
            self.log.take_out(self.said)             # not a mark
        # What is not even text is refused the same way, never a crash.
        for odd in (None, 7, ["a"], {"a": 1}):
            with self.subTest(odd=odd):
                with self.assertRaises(ValueError):
                    self.log.take_out(odd)
                with self.assertRaises(Refused) as c:
                    self.log.keep_public(6, odd, "0" * 32, "v", KEEPER,
                                         APPEAL, trial_decision(1))
                self.assertEqual(c.exception.reason, apart.BAD_KEPT)
                with self.assertRaises(Refused) as c:
                    self.log.stays_redacted(6, odd, KEEPER, APPEAL,
                                            trial_decision(1))
                # Nothing is not a value an open field can have.
                self.assertEqual(
                    c.exception.reason,
                    apart.ENTRY if odd is None else apart.BAD_STAYS)
        made = mark(self.log, self.said, "text")
        self.log.take_out(made)
        with self.assertRaises(ValueError):
            self.log.take_out(made)                  # already out
        other = mark(self.log, self.said, "time")
        keep(self.log, other)
        with self.assertRaises(ValueError):
            self.log.take_out(other)                 # answered: it is public
        # A mark that stands has its field gone already, through this
        # writer: nothing is left to take out.
        stays(self.log, made)
        with self.assertRaises(ValueError) as c:
            self.log.take_out(made)
        self.assertEqual(str(c.exception),
                         "the field is not in the contents")

    def test_keeping_public_puts_the_field_back_in_the_same_step(self):
        made = mark(self.log, self.said, "text")
        salt, value = self.log.take_out(made)
        self.assertEqual(self.state(), "redacted")
        self.log.keep_public(6, made, salt, value, KEEPER, APPEAL,
                             trial_decision(1), apart={"reason": "public"})
        self.assertEqual(self.state(), "kept public")
        self.assertEqual(self.log.contents[self.said]["text"], [salt, value])
        self.assertEqual(self.log.entries[-1]["data"],
                         {"mark": made, "office": KEEPER, "ground": APPEAL,
                          "decision": trial_decision(1)})
        joined = apart.join(self.log.entries, self.log.contents)[3]
        self.assertEqual(joined["data"]["text"], value)

    def test_keeping_public_refuses_what_the_log_does_not_commit_to(self):
        made = mark(self.log, self.said, "text")
        salt, value = self.log.take_out(made)
        entries = copy.deepcopy(self.log.entries)
        contents = copy.deepcopy(self.log.contents)
        other_salt = self.log.contents[self.said]["time"][0]
        for bad_salt, bad_value, why in [
                (salt, value + "!", apart.FINGERPRINT),
                (other_salt, value, apart.FINGERPRINT),
                (salt.upper(), value, apart.SALT),
                (salt, 1.5, apart.VALUE)]:
            with self.subTest(why=why, salt=bad_salt):
                with self.assertRaises(Refused) as c:
                    self.log.keep_public(6, made, bad_salt, bad_value,
                                         KEEPER, APPEAL, trial_decision(1))
                self.assertEqual(c.exception.reason, why)
                self.assertEqual(c.exception.where, (self.said, "text"))
                self.assertEqual(self.log.entries, entries)
                self.assertEqual(self.log.contents, contents)

    def test_a_refused_answer_puts_nothing_back(self):
        made = mark(self.log, self.said, "text")
        salt, value = self.log.take_out(made)
        contents = copy.deepcopy(self.log.contents)
        with self.assertRaises(Refused):
            self.log.keep_public(6, made, salt, value, "", APPEAL,
                                 trial_decision(1))
        self.assertEqual(self.log.contents, contents)
        self.assertEqual(self.state(), "redacted")

    def test_it_stays_redacted_only_once_it_is_out_of_the_contents(self):
        made = mark(self.log, self.said, "text")
        with self.assertRaises(ValueError):
            stays(self.log, made)
        self.assertEqual(self.of()[0]["state"], "open")
        self.log.take_out(made)
        stays(self.log, made)
        self.assertEqual(self.of()[0]["state"], "stands")

    def test_a_mark_and_its_answer_are_not_written_by_append(self):
        made = mark(self.log, self.said, "text")
        entries = copy.deepcopy(self.log.entries)
        answer = {"mark": made, "office": KEEPER, "ground": APPEAL,
                  "decision": trial_decision(1)}
        for kind, data in [
                (apart.MARK, {"entry": self.said, "field": "time",
                              "office": OFFICE, "ground": PRIVATE}),
                (apart.KEPT, answer), (apart.STAYS, answer)]:
            with self.subTest(kind), self.assertRaises(ValueError):
                self.log.append(6, kind, None, data)
            self.assertEqual(self.log.entries, entries)

    def test_a_decision_alone_never_makes_a_finished_redaction_missing(self):
        # The fault carried from part two: one entry of kind
        # field_kept_public turned a redacted field into a missing one.
        # The writer now puts the field back with it, or writes nothing.
        made = mark(self.log, self.said, "text")
        salt, value = self.log.take_out(made)
        self.log.keep_public(6, made, salt, value, KEEPER, APPEAL,
                             trial_decision(1))
        states = apart.check(self.log.entries, self.log.contents)
        self.assertNotIn("missing",
                         [s for e in states.values() for s in e.values()])

    def test_a_published_log_can_still_be_at_fault(self):
        # The check can't make a publisher honest: it says what it finds.
        made = mark(self.log, self.said, "text")
        keep(self.log, made)
        contents = copy.deepcopy(self.log.contents)
        del contents[self.said]["text"]
        self.assertEqual(
            apart.check(self.log.entries, contents)[self.said]["text"],
            "missing")
        # And a field left in the contents after the decision that it
        # stays redacted is unfinished, and never shown.
        other = mark(self.log, self.said, "time")
        left = copy.deepcopy(self.log.contents)
        self.log.take_out(other)
        stays(self.log, other)
        self.assertEqual(
            apart.check(self.log.entries, left)[self.said]["time"],
            "unfinished")
        self.assertNotIn("time", apart.join(self.log.entries, left)[3]["data"])

    def test_redactions_need_no_contents_and_join_gives_them(self):
        made = mark(self.log, self.said, "text")
        self.log.take_out(made)
        stays(self.log, made)
        found = apart.redactions(self.log.entries)
        self.assertEqual(found, {self.said: {"text": [
            {"id": made, "short": made[:12], "state": "stands"}]}})
        joined = apart.join(self.log.entries, self.log.contents)
        self.assertEqual(joined[3]["redactions"], found[self.said])
        self.assertEqual(joined[1]["redactions"], {})

    def test_a_redactions_id_is_never_shown_like_an_incidents(self):
        # Short ids are worked out over incidents and redactions
        # together, so no two that a room shows begin alike.
        made = mark(self.log, self.said, "text")
        removal = remove(self.log, self.log.entries[4]["hash"])
        shown = apart._shown(self.log._scan)
        self.assertEqual(set(shown), {made, removal})
        ids = [made[:20] + "0" * 44, made[:20] + "1" * 44]
        short = apart._short_ids(ids)
        self.assertEqual(sorted(len(s) for s in short.values()), [21, 21])


def remove(log, entry, n=1, tick=9):
    return log.append(tick, apart.REMOVED, None,
                      {"entry": entry, "office": MODERATOR, "ground": GROUND,
                       "decision": trial_decision(n)}, {"record": f"r{n}"})


def restore(log, incident, n=2, tick=9):
    return log.append(tick, apart.RESTORED, None,
                      {"incident": incident, "office": KEEPER,
                       "ground": GROUND, "decision": trial_decision(n)},
                      {"record": f"r{n}"})


def take_back(log, entry, tick=9):
    return log.append(tick, apart.TAKEN_BACK, None, {"entry": entry},
                      {"record": "taken back"})


def put_back(log, taking, tick=9):
    return log.append(tick, apart.PUT_BACK, None, {"taken_back": taking},
                      {"record": "put back"})


class TestWhatWins(unittest.TestCase):
    """The table in docs/research/REDACTION.md, decision 9, row by row.
    (Its first row, a redacted field, is TestJoining's.)"""

    def setUp(self):
        self.log = room()
        self.said = self.log.entries[3]["hash"]

    def state(self, entry=None):
        its = apart.incidents(self.log.entries).get(entry or self.said)
        return its["state"] if its else apart.AS_WRITTEN

    def refused(self, act, *args):
        entries = copy.deepcopy(self.log.entries)
        with self.assertRaises(Refused) as c:
            act(self.log, *args)
        self.assertEqual(self.log.entries, entries)
        return c.exception.reason

    def test_an_entry_is_as_written_until_something_is_done_to_it(self):
        self.assertEqual(apart.incidents(self.log.entries), {})
        self.assertEqual(self.state(), "as written")

    def test_a_second_removal_of_a_removed_entry_is_refused(self):
        remove(self.log, self.said)
        self.assertEqual(self.state(), "removed")
        self.assertEqual(self.refused(remove, self.said, 3),
                         apart.BAD_REMOVAL)

    def test_a_second_taking_back_is_refused(self):
        take_back(self.log, self.said)
        self.assertEqual(self.state(), "taken back")
        self.assertEqual(self.refused(take_back, self.said),
                         apart.BAD_TAKING_BACK)

    def test_a_removal_of_an_entry_its_author_took_back_is_refused(self):
        take_back(self.log, self.said)
        self.assertEqual(self.refused(remove, self.said),
                         apart.BAD_REMOVAL)

    def test_a_restoring_of_an_entry_that_is_not_removed_is_refused(self):
        self.assertEqual(self.refused(restore, self.said),
                         apart.BAD_RESTORING)
        first = remove(self.log, self.said)
        restore(self.log, first)
        self.assertEqual(self.state(), "restored")
        self.assertEqual(self.refused(restore, first, 4),
                         apart.BAD_RESTORING)

    def test_an_office_does_not_undo_an_authors_taking_back(self):
        taking = take_back(self.log, self.said)
        self.assertEqual(self.refused(restore, taking),
                         apart.BAD_RESTORING)
        self.assertEqual(self.state(), "taken back")

    def test_a_removal_after_a_restoring_is_a_new_incident(self):
        first = remove(self.log, self.said, 1)
        restore(self.log, first, 2)
        second = remove(self.log, self.said, 3)
        self.assertNotEqual(first, second)
        its = apart.incidents(self.log.entries)[self.said]
        self.assertEqual(its["state"], "removed")
        self.assertEqual([(i["id"], i["stands"]) for i in its["incidents"]],
                         [(first, False), (second, True)])
        self.assertEqual(its["incidents"][0]["short"], first[:12])
        self.assertNotEqual(its["incidents"][0]["short"],
                            its["incidents"][1]["short"])

    def test_an_author_takes_back_what_an_office_removed(self):
        removal = remove(self.log, self.said)
        taking = take_back(self.log, self.said)
        self.assertEqual(self.state(), "taken back")
        # It stays hidden whatever the office does. The office can
        # still restore its removal, say after an appeal: the removal
        # stops standing, and the entry stays taken back.
        restore(self.log, removal)
        self.assertEqual(self.state(), "taken back")
        its = apart.incidents(self.log.entries)[self.said]["incidents"]
        self.assertEqual([(i["kind"], i["stands"]) for i in its],
                         [("removed", False), ("taken back", True)])
        # The removal can't be restored twice.
        self.assertEqual(self.refused(restore, removal),
                         apart.BAD_RESTORING)
        # Put back, it shows as restored: an office once removed it.
        put_back(self.log, taking)
        self.assertEqual(self.state(), "restored")

    def test_a_ground_that_is_a_record_is_named_by_its_hash(self):
        ground = {"kind": "record", "ref": "an earlier decision"}
        data = {"entry": self.said, "office": "moderator", "ground": ground,
                "decision": "d" * 64}
        with self.assertRaises(apart.Refused) as caught:
            self.log.append(5, apart.REMOVED, None, data)
        self.assertEqual(caught.exception.reason, apart.BAD_REMOVAL)
        data["ground"] = {"kind": "record", "ref": "e" * 64}
        self.log.append(5, apart.REMOVED, None, data)
        self.assertEqual(self.state(), "removed")
        # Any other kind of ground is named in words.
        self.assertTrue(apart._office_ok(
            {**data, "ground": {"kind": "law", "ref": "e" * 64}}))

    def test_short_ids_are_held_against_their_neighbours(self):
        ids = ["ab" + "0" * 62, "ab" + "0" * 20 + "1" + "0" * 41,
               "cd" + "0" * 62, "ab" + "0" * 30 + "2" + "0" * 31]
        short = apart._short_ids(ids)
        self.assertEqual(short[ids[0]], ids[0][:33])
        self.assertEqual(short[ids[1]], ids[1][:23])
        self.assertEqual(short[ids[2]], ids[2][:12])
        self.assertEqual(short[ids[3]], ids[3][:33])
        # Each is the only id that begins so.
        for one, cut in short.items():
            self.assertEqual([i for i in ids if i.startswith(cut)], [one])
        # An id is never cut longer than it is, and the work ends.
        self.assertEqual(apart._short_ids(["abc", "abcd"]),
                         {"abc": "abc", "abcd": "abcd"})
        self.assertEqual(apart._short_ids([]), {})

    def test_an_author_undoes_their_own_taking_back(self):
        taking = take_back(self.log, self.said)
        put_back(self.log, taking)
        self.assertEqual(self.state(), "as written")
        self.assertEqual(self.refused(put_back, taking),
                         apart.BAD_PUTTING_BACK)
        # Unless an office's removal still stands.
        removal = remove(self.log, self.said)
        again = take_back(self.log, self.said)
        put_back(self.log, again)
        self.assertEqual(self.state(), "removed")
        restore(self.log, removal)
        self.assertEqual(self.state(), "restored")

    def test_a_removal_of_an_entry_with_a_redacted_field(self):
        self.log.take_out(mark(self.log, self.said, "text"))
        remove(self.log, self.said)
        one = apart.join(self.log.entries, self.log.contents)[3]
        self.assertEqual(one["state"], "removed")
        self.assertEqual(one["fields"]["text"], "redacted")
        self.assertNotIn("text", one["data"])

    def test_the_forms_own_entries_cannot_be_removed_or_taken_back(self):
        removal = remove(self.log, self.said)
        taking = take_back(self.log, self.log.entries[4]["hash"])
        made = mark(self.log, self.said, "text")
        kept = keep(self.log, made)
        again = mark(self.log, self.said, "text", tick=7)
        self.log.take_out(again)
        stood = stays(self.log, again, 2, tick=8)
        for own in (removal, taking, made, kept, again, stood):
            self.assertEqual(self.refused(remove, own, 5),
                             apart.BAD_REMOVAL)
            self.assertEqual(self.refused(take_back, own),
                             apart.BAD_TAKING_BACK)

    def test_an_offices_act_says_its_office_ground_and_decision(self):
        good = {"entry": self.said, "office": MODERATOR, "ground": GROUND,
                "decision": trial_decision(1)}
        for change in [{"office": 5}, {"office": ""},
                       {"ground": "the law"}, {"ground": {"kind": "law"}},
                       {"ground": {"kind": "whim", "ref": "x"}},
                       {"ground": {"kind": "law", "ref": 5}},
                       {"ground": {**GROUND, "more": 1}},
                       {"ground": {"kind": "record", "ref": "x"}},
                       {"ground": {"kind": "record", "ref": "F" * 64}},
                       {"decision": "f" * 63}, {"decision": "F" * 64}]:
            with self.subTest(change=change), self.assertRaises(Refused) as c:
                self.log.append(9, apart.REMOVED, None, {**good, **change})
            self.assertEqual(c.exception.reason, apart.BAD_REMOVAL)
        for kind in apart.GROUNDS:
            fresh = room()
            # An earlier record is named by its hash; the rest in words.
            ref = "f" * 64 if kind == "record" else "x"
            fresh.append(9, apart.REMOVED, None,
                         {**good, "entry": fresh.entries[3]["hash"],
                          "ground": {"kind": kind, "ref": ref}})

    def test_nothing_leaves_the_record(self):
        # A removal and a taking back change what is shown, and nothing
        # else: the entry, its contents and the chain are as they were.
        entries = copy.deepcopy(self.log.entries)
        contents = copy.deepcopy(self.log.contents)
        remove(self.log, self.said)
        take_back(self.log, self.log.entries[4]["hash"])
        self.assertEqual(self.log.entries[:len(entries)], entries)
        for entry, fields in contents.items():
            self.assertEqual(self.log.contents[entry], fields)
        joined = apart.join(self.log.entries, self.log.contents)
        self.assertEqual(joined[3]["data"]["text"], "hello, room")
        self.assertEqual(joined[3]["state"], "removed")
        self.assertEqual(joined[4]["state"], "taken back")
        self.assertEqual(joined[5]["state"], "as written")
        self.assertEqual(joined[5]["incidents"], [])
        self.assertTrue(World.verify_log(self.log.entries))

    def test_the_state_needs_no_contents(self):
        log, names = acted_on()
        whole = apart.incidents(log.entries)
        self.assertEqual({v["state"] for v in whole.values()},
                         set(apart.ENTRY_STATES))
        joined = apart.join(log.entries, {})
        for one in joined:
            its = whole.get(one["hash"], {"state": "as written",
                                          "incidents": []})
            self.assertEqual(one["state"], its["state"])
            self.assertEqual(one["incidents"], its["incidents"])

    def test_an_incidents_id_is_shown_as_short_as_is_still_its_own(self):
        a = "abcdef012345" + "0" * 52
        b = "abcdef012345" + "1" + "0" * 51
        c = "0" * 64
        self.assertEqual(apart._short_ids([a, b, c]),
                         {a: a[:13], b: b[:13], c: c[:12]})
        self.assertEqual(apart._short_ids([a]), {a: a[:12]})
        self.assertEqual(apart._short_ids([]), {})
        d = "f" * 63 + "0"
        e = "f" * 63 + "1"
        self.assertEqual(apart._short_ids([d, e]), {d: d, e: e})
        for group in vectors()["short_ids"]:
            self.assertEqual(apart._short_ids(group["ids"]), group["short"])


class TestJoining(unittest.TestCase):

    def test_a_whole_log_reads_as_it_was_written(self):
        log = room()
        joined = apart.join(log.entries, log.contents)
        self.assertEqual(len(joined), len(WRITTEN) + 1)
        for one, (tick, kind, agent, data, kept) in zip(joined[1:], WRITTEN):
            self.assertEqual(one["tick"], tick)
            self.assertEqual(one["kind"], kind)
            self.assertEqual(one["agent"], agent)
            self.assertEqual(one["data"], {**data, **kept})
            self.assertEqual(one["fields"], {n: "present" for n in kept})
            self.assertEqual(one["state"], "as written")
            self.assertEqual(one["incidents"], [])
            self.assertNotIn("apart", one)
        self.assertEqual(joined[0]["data"]["form"], apart.FORM)
        self.assertEqual([j["hash"] for j in joined],
                         [e["hash"] for e in log.entries])

    def test_a_field_under_a_standing_mark_is_never_shown(self):
        log = room()
        target = log.entries[3]["hash"]
        mark(log, target, "text")
        self.assertIn("text", log.contents[target])   # still in the contents
        one = apart.join(log.entries, log.contents)[3]
        self.assertNotIn("text", one["data"])
        self.assertEqual(one["fields"]["text"], "unfinished")
        self.assertNotIn("hello, room", json.dumps(
            apart.join(log.entries, log.contents)))

    def test_joining_changes_neither_the_log_nor_the_contents(self):
        log = room()
        entries = copy.deepcopy(log.entries)
        contents = copy.deepcopy(log.contents)
        joined = apart.join(log.entries, log.contents)
        joined[6]["data"]["thing"]["words"].append("c")
        joined[0]["data"]["kept_apart"]["said"].append("more")
        self.assertEqual(log.entries, entries)
        self.assertEqual(log.contents, contents)

    def test_joining_refuses_what_checking_refuses(self):
        log = room()
        with self.assertRaises(Refused):
            apart.join(log.entries, {"f" * 64: {}})
        with self.assertRaises(Refused):
            apart.join(world_log(), {})


class TestTheVectors(unittest.TestCase):

    def test_the_file_is_what_is_written_now(self):
        # tests/test_vectors.py compares the file byte for byte; this
        # says the same of its parts, for a clearer failure.
        on_disk, now = vectors(), json.loads(json.dumps(log_apart()))
        self.assertEqual(sorted(on_disk), sorted(now))
        for key in now:
            with self.subTest(key):
                self.assertEqual(on_disk[key], now[key])

    def test_the_names_and_limits_are_the_modules(self):
        v = vectors()
        self.assertEqual(v["form"], apart.FORM)
        self.assertEqual(v["mark"], apart.MARK)
        self.assertEqual(v["kept"], apart.KEPT)
        self.assertEqual(v["stays"], apart.STAYS)
        self.assertEqual(v["says"],
                         {kind: list(keys)
                          for kind, keys in apart.SAYS.items()})
        self.assertEqual(v["redaction_states"],
                         list(apart.REDACTION_STATES))
        self.assertEqual(len(apart.REASONS), 20)
        self.assertEqual(v["removed"], apart.REMOVED)
        self.assertEqual(v["restored"], apart.RESTORED)
        self.assertEqual(v["taken_back"], apart.TAKEN_BACK)
        self.assertEqual(v["put_back"], apart.PUT_BACK)
        self.assertEqual(v["grounds"], list(apart.GROUNDS))
        self.assertEqual(v["entry_states"], list(apart.ENTRY_STATES))
        self.assertEqual(v["short"], 12)
        self.assertEqual(v["max_whole"], 2 ** 53 - 1)
        self.assertEqual(v["max_nesting"], apart.MAX_NESTING)
        self.assertEqual(v["states"], list(apart.STATES))
        self.assertEqual(v["reasons"], list(apart.REASONS))
        self.assertEqual(len(set(apart.REASONS)), len(apart.REASONS))

    def test_each_fingerprint(self):
        for case in vectors()["fingerprints"]:
            with self.subTest(case["text"]):
                self.assertEqual(
                    apart.fingerprint_text(case["salt"], case["name"],
                                           case["value"]), case["text"])
                self.assertEqual(
                    apart.fingerprint(case["salt"], case["name"],
                                      case["value"]), case["fingerprint"])

    def test_the_trial_room_written_again_is_the_first_case(self):
        v = vectors()
        count = iter(range(1000))
        log = Log(v["table"], v["first"],
                  salt=lambda: trial_salt(next(count)))
        for step in v["written"]:
            log.append(step["tick"], step["kind"], step["agent"],
                       step["data"], step["apart"])
        self.assertEqual(log.entries, v["holds"][0]["log"])
        self.assertEqual(log.contents, v["holds"][0]["contents"])

    def test_each_case_that_holds(self):
        cases = vectors()["holds"]
        self.assertEqual(len(cases), 7)
        seen = set()
        seen_redactions = set()
        for case in cases:
            with self.subTest(case["name"]):
                self.assertTrue(World.verify_log(case["log"]))
                states = apart.check(case["log"], case["contents"])
                self.assertEqual(states, case["states"])
                self.assertEqual(apart.incidents(case["log"]),
                                 case["incidents"])
                found = apart.redactions(case["log"])
                self.assertEqual(found, case["redactions"])
                self.assertEqual(apart.join(case["log"], case["contents"]),
                                 case["joined"])
                seen.update(s for e in states.values() for s in e.values())
                seen_redactions.update(
                    r["state"] for e in found.values()
                    for f in e.values() for r in f)
        self.assertEqual(seen, set(apart.STATES))
        self.assertEqual(seen_redactions, set(apart.REDACTION_STATES))

    def test_each_case_that_is_refused(self):
        cases = vectors()["refused"]
        self.assertEqual(len(cases), 179)
        for case in cases:
            with self.subTest(case["name"]):
                self.assertEqual(refusal(case["log"], case["contents"]),
                                 (case["reason"], case["where"]))
        self.assertEqual({c["reason"] for c in cases}, set(apart.REASONS))
        self.assertEqual(
            len([c for c in cases if c["name"].startswith("two faults")]), 8)

    def test_only_the_chain_cases_break_the_chain(self):
        # Every other refused log is a chain that holds: it is refused
        # for what it says, never for a hash. (The cases with two faults
        # are left out: some of them break the chain as their second.)
        for case in vectors()["refused"]:
            if case["name"].startswith("two faults"):
                continue
            with self.subTest(case["name"]):
                self.assertEqual(World.verify_log(case["log"]),
                                 case["reason"] != apart.CHAIN)


if __name__ == "__main__":
    unittest.main()

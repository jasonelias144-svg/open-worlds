"""A log whose fields are kept apart (world/apart.py; course step 3b,
part two): the fingerprint, the two checks, the five states of a field,
the function that joins entries and contents, and the shared vectors in
vectors/log-apart.json, which rust/world-log reads too."""
import copy
import json
import unittest

from world import World, apart
from world.apart import Log, Refused
from world.apart_vectors import (FIRST, TABLE, VALUES_ALLOWED, WRITTEN,
                                 log_apart, place, trial_salt)
from world.vectors import FOLDER, world_log


def vectors():
    return json.loads((FOLDER / "log-apart.json").read_text(encoding="ascii"))


def room(salt=apart.new_salt):
    log = Log(TABLE, FIRST, salt=salt)
    for step in WRITTEN:
        log.append(*step)
    return log


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
            ((9, apart.MARK, None,
              {"entry": log.head(), "field": "nothing"}, {}),
             apart.BAD_MARK),
            ((9, apart.MARK, None,
              {"entry": log.head(), "field": "nothing"},
              {"reason": "kept apart, and still refused"}), apart.BAD_MARK),
            ((9, apart.KEPT, None, {"mark": log.head()}, {}),
             apart.BAD_KEPT),
        ]
        for step, why in refusals:
            with self.subTest(why), self.assertRaises(Refused) as c:
                log.append(*step)
            self.assertEqual(c.exception.reason, why)
            self.assertEqual(log.entries, entries)
            self.assertEqual(log.contents, contents)
        # The log still takes an entry, and still holds.
        mark = log.append(9, apart.MARK, "trial office",
                          {"entry": entries[3]["hash"], "field": "text"},
                          {"reason": "asked"})
        states = apart.check(log.entries, log.contents)
        self.assertEqual(states[entries[3]["hash"]]["text"], "unfinished")
        self.assertEqual(states[mark], {"reason": "present"})

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
        log.append(5, apart.MARK, "office",
                   {"entry": log.entries[3]["hash"], "field": "text"},
                   {"reason": "asked"})
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
        for table in [{"said": ["text", "key"]}, {"said": "text"}, [],
                      {"said": ["Text"]}]:
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
        one = log.append(5, apart.MARK, "o", {"entry": target,
                                              "field": "text"})
        two = log.append(5, apart.MARK, "o", {"entry": target,
                                              "field": "text"})
        self.assertEqual(state(), "unfinished")
        log.append(6, apart.KEPT, "o", {"mark": one})
        self.assertEqual(state(), "unfinished")   # the second still stands
        log.append(6, apart.KEPT, "o", {"mark": two})
        self.assertEqual(state(), "kept public")
        log.append(7, apart.KEPT, "o", {"mark": two})   # answered twice
        self.assertEqual(state(), "kept public")
        del log.contents[target]["text"]
        self.assertEqual(state(), "missing")
        log.append(8, apart.MARK, "o", {"entry": target, "field": "text"})
        self.assertEqual(state(), "redacted")

    def test_a_mark_cannot_name_itself_or_what_comes_after(self):
        log = room()
        later = Log(TABLE, FIRST)
        with self.assertRaises(Refused) as c:
            log.append(5, apart.MARK, "o",
                       {"entry": later.head(), "field": "name"})
        self.assertEqual(c.exception.reason, apart.BAD_MARK)


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
            self.assertNotIn("apart", one)
        self.assertEqual(joined[0]["data"]["form"], apart.FORM)
        self.assertEqual([j["hash"] for j in joined],
                         [e["hash"] for e in log.entries])

    def test_a_field_under_a_standing_mark_is_never_shown(self):
        log = room()
        target = log.entries[3]["hash"]
        log.append(5, apart.MARK, "o", {"entry": target, "field": "text"})
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
        self.assertEqual(len(cases), 5)
        seen = set()
        for case in cases:
            with self.subTest(case["name"]):
                self.assertTrue(World.verify_log(case["log"]))
                states = apart.check(case["log"], case["contents"])
                self.assertEqual(states, case["states"])
                self.assertEqual(apart.join(case["log"], case["contents"]),
                                 case["joined"])
                seen.update(s for e in states.values() for s in e.values())
        self.assertEqual(seen, set(apart.STATES))

    def test_each_case_that_is_refused(self):
        cases = vectors()["refused"]
        self.assertEqual(len(cases), 90)
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

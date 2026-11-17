"""The act of redacting (world/redact.py): seal, mark, take out; and the
deciding office's two decisions (docs/research/REDACTION.md, decisions 4
and 5)."""
import copy
import hashlib
import json
import unittest

from formats import records, sealed
from formats import sealed_vectors as parties
from formats.canonical import canonical
from formats.multikey import sealing_secret_from_multikey
from world import apart, apart_vectors, redact, redact_vectors
from world.apart import Refused
from world.redact import RedactError
from world.redact_vectors import (ABOUT, CREATED, DECIDES, FIELD, REDACTS,
                                  _to, office, redacted)

VECTORS = json.loads(redact_vectors.FILE.read_text(encoding="utf-8"))
VALUE = "hello, room"


def secret(name):
    return parties._sealing_secret(name)


def did(name):
    return parties._did(name)


def kept(room, *more):
    """Everything the log keeps, and anything else given, as one text."""
    return json.dumps([room.entries, room.contents, *more])


def state(room, entry, field=FIELD):
    return apart.check(room.entries, room.contents)[entry][field]


def decide(room, mark, envelope, **more):
    return redact.keep_public(
        room, 6, mark, envelope, secret(DECIDES), did(DECIDES),
        apart_vectors.KEEPER, apart_vectors.APPEAL,
        apart_vectors.trial_decision(1), **more)


class TestTheVectors(unittest.TestCase):

    def test_the_file_is_what_this_code_writes_now(self):
        self.assertEqual(
            redact_vectors.FILE.read_text(encoding="utf-8"),
            redact_vectors.text(redact_vectors.current()),
            "rewrite with: python3 -m world.redact_vectors")

    def test_the_names_and_reasons_are_the_modules(self):
        self.assertEqual(VECTORS["format"], redact.FORMAT)
        self.assertEqual(VECTORS["label"], redact.LABEL)
        self.assertEqual(VECTORS["reasons"], list(redact.REASONS))
        self.assertEqual(len(set(redact.REASONS)), 10)
        self.assertEqual(VECTORS["padded"], redact.PADDED)

    def test_each_copy_opens_for_the_one_it_names_and_holds(self):
        log = VECTORS["redacted"]["log"]
        self.assertEqual([c["to"] for c in VECTORS["copies"]],
                         ABOUT + [DECIDES])
        for case in VECTORS["copies"]:
            with self.subTest(case["to"]):
                party = VECTORS["parties"][case["to"]]
                key = sealing_secret_from_multikey(
                    party["sealingSecretMultibase"])
                inside = redact.open_copy(case["envelope"], key,
                                          party["id"], log)
                self.assertEqual(inside, case["inside"])
                self.assertEqual(records.record_hash(inside),
                                 case["record"])
                self.assertEqual(sealed.fingerprint(case["envelope"]),
                                 case["fingerprint"])

    def test_each_refused_record_holds_as_a_record_and_not_to_the_log(self):
        log = VECTORS["redacted"]["log"]
        seen = set()
        for case in VECTORS["refused"]:
            with self.subTest(case["name"]):
                records.check(case["record"])
                with self.assertRaises(RedactError) as c:
                    redact.held_to(case["record"], log)
                self.assertEqual(c.exception.reason, case["reason"])
                seen.add(case["reason"])
        self.assertEqual(seen, {redact.OTHER_LOG, redact.NO_ENTRY,
                                redact.NO_FIELD, redact.NOT_HELD,
                                redact.NOT_A_COPY})
        self.assertEqual(len(VECTORS["refused"]), 9)

    def test_a_text_that_is_not_a_field_is_refused_though_it_hashes(self):
        # A log written by hand commits to texts that are not a field
        # as a log writes one. Each record carries exactly the text its
        # entry's fingerprint is the hash of, and is refused all the
        # same: what is put back must be what a log would write.
        case = VECTORS["odd"]
        log = case["log"]
        self.assertEqual(case["reason"], redact.NOT_HELD)
        redact.held_to(case["holds"], log)
        self.assertEqual(redact.what_was_there(case["holds"])[1], VALUE)
        self.assertEqual(len(case["refused"]), 21)
        for one in case["refused"]:
            with self.subTest(one["name"]):
                record = one["record"]
                records.check(record)
                entry = [e for e in log if e["hash"] == record["entry"]][0]
                self.assertEqual(
                    hashlib.sha256(record["hashed"].encode()).hexdigest(),
                    entry["apart"][FIELD])
                self.assertIsNone(redact.what_was_there(record))
                with self.assertRaises(RedactError) as c:
                    redact.held_to(record, log)
                self.assertEqual(c.exception.reason, redact.NOT_HELD)

    def test_the_logs_in_the_file_hold_with_the_states_they_should(self):
        entry = VECTORS["act"]["entry"]
        for name, want in [("redacted", "redacted"),
                           ("kept", "kept public"),
                           ("stays", "redacted")]:
            with self.subTest(name):
                case = VECTORS[name]
                states = apart.check(case["log"], case["contents"])
                self.assertEqual(states[entry][FIELD], want)
        found = apart.redactions(VECTORS["stays"]["log"])
        self.assertEqual(found[entry][FIELD][0]["state"], "stands")
        found = apart.redactions(VECTORS["redacted"]["log"])
        self.assertEqual(found[entry][FIELD][0]["state"], "open")


class TestRedacting(unittest.TestCase):

    def setUp(self):
        self.room, self.made, self.entry = redacted()

    def test_it_seals_marks_and_takes_out(self):
        self.assertEqual(len(self.made.copies), 2)
        last = self.room.entries[-1]
        self.assertEqual(last["hash"], self.made.mark)
        self.assertEqual(last["kind"], apart.MARK)
        self.assertEqual(last["data"], {
            "entry": self.entry, "field": FIELD,
            "office": apart_vectors.OFFICE,
            "ground": apart_vectors.PRIVATE})
        self.assertNotIn(FIELD, self.room.contents[self.entry])
        self.assertEqual(state(self.room, self.entry), "redacted")
        self.assertEqual(self.room.entries, VECTORS["redacted"]["log"])
        self.assertEqual(self.room.contents,
                         VECTORS["redacted"]["contents"])

    def test_neither_the_value_nor_its_salt_is_left_anywhere(self):
        before = apart_vectors._room()
        salt, value = before.contents[self.entry][FIELD]
        self.assertEqual(value, VALUE)
        self.assertIn(salt, kept(before))
        self.assertIn(value, kept(before))
        everything = kept(self.room, self.made.copies,
                          self.made.office_copy)
        self.assertNotIn(salt, everything)
        self.assertNotIn(value, everything)
        # Nor anywhere else in what the writer holds, or in what the
        # act gave back.
        held = repr([vars(self.room), vars(self.room._scan), self.made])
        self.assertIn(salt, repr([vars(before), vars(before._scan)]))
        self.assertNotIn(salt, held)
        self.assertNotIn(value, held)
        # Nor as bytes in a box: a box is not the value written in hex.
        for envelope in self.made.copies + [self.made.office_copy]:
            self.assertNotIn(value.encode().hex(), envelope["box"])
            self.assertNotIn(salt.encode().hex(), envelope["box"])
        # The log's other fields are untouched.
        self.assertEqual(sorted(self.room.contents[self.entry]),
                         ["key", "time"])

    def test_a_copy_says_what_was_there_and_where(self):
        before = apart_vectors._room()
        salt, value = before.contents[self.entry][FIELD]
        inside = redact.open_copy(self.made.copies[0], secret("ALICE"),
                                  did("ALICE"), self.room.entries)
        self.assertEqual(
            {k: v for k, v in inside.items() if k != "proof"},
            {"format": redact.FORMAT,
             "office": {"key": did(REDACTS),
                        "grant": redact_vectors.GRANT},
             "to": did("ALICE"), "decider": did(DECIDES),
             "log": self.room.entries[0]["hash"],
             "entry": self.entry, "field": FIELD,
             "hashed": apart.fingerprint_text(salt, FIELD, value),
             "pad": inside["pad"]})
        self.assertEqual(redact.what_was_there(inside), [salt, value])
        # Signed by the office that redacted it.
        records.check(inside)
        self.assertEqual(records.signer_field(inside), did(REDACTS))

    def test_whatever_a_log_can_keep_apart_can_be_redacted(self):
        # Among them a map with a key that is not ASCII, which no signed
        # record could hold as a key of its own: a copy carries what was
        # hashed, as text.
        values = apart_vectors.VALUES_ALLOWED
        self.assertTrue(any(type(v) is dict and any(not k.isascii()
                                                    for k in v)
                            for v in values))
        for value in values:
            with self.subTest(value=repr(value)[:40]):
                self.assertTrue(apart.value_allowed(value))
                log = apart.Log({"said": ["text"]})
                said = log.append(1, "said", None, {}, {"text": value})
                salt = log.contents[said]["text"][0]
                made = redact.redact(
                    log, 2, said, "text", office(), apart_vectors.PRIVATE,
                    CREATED, about=[_to("ALICE")], decider=_to(DECIDES))
                self.assertEqual(
                    apart.check(log.entries, log.contents)[said]["text"],
                    "redacted")
                inside = redact.open_copy(made.copies[0], secret("ALICE"),
                                          did("ALICE"), log.entries)
                self.assertEqual(redact.what_was_there(inside),
                                 [salt, value])
                decide(log, made.mark, made.office_copy)
                self.assertEqual(log.contents[said]["text"], [salt, value])
                self.assertEqual(
                    apart.join(log.entries, log.contents)[1]["data"]["text"],
                    value)

    def test_a_copys_length_says_little_of_what_was_there(self):
        # Before it is signed, a record is 1024 bytes or the next power
        # of two. A signature's text is 87 or 88 characters, whatever
        # was signed, so two boxes of one size differ by a byte at most.
        sizes = {}
        for length in (0, 1, 11, 200, 400, 600, 1500, 5000):
            log = apart.Log({"said": ["text"]})
            said = log.append(1, "said", None, {}, {"text": "x" * length})
            made = redact.redact(
                log, 2, said, "text", office(), apart_vectors.PRIVATE,
                CREATED, about=[_to("ALICE")], decider=_to(DECIDES))
            inside = redact.open_copy(made.office_copy, secret(DECIDES),
                                      did(DECIDES), log.entries)
            plain = {k: v for k, v in inside.items() if k != "proof"}
            size = len(canonical(plain))
            self.assertEqual(size & (size - 1), 0, "a power of two")
            self.assertGreaterEqual(size, redact.PADDED)
            self.assertEqual(set(inside["pad"]) - {"0"}, set())
            for envelope in made.copies + [made.office_copy]:
                sizes.setdefault(size, set()).add(
                    len(envelope["box"]) // 2)
        # Five short values share the smallest size.
        self.assertEqual(sorted(sizes), [1024, 2048, 4096, 8192])
        self.assertEqual(len(sizes[1024]) <= 2, True)
        for size, boxes in sizes.items():
            self.assertLessEqual(max(boxes) - min(boxes), 1, size)

    def test_a_record_is_padded_to_one_of_a_few_sizes(self):
        def size(record):
            return len(canonical(dict(record, pad=redact._padding(record))))
        # However small, the smallest size.
        self.assertEqual(size({"pad": ""}), redact.PADDED)
        for exact in (redact.PADDED, 2 * redact.PADDED):
            # Exactly a size already: nothing is added.
            record = {"pad": "", "x": ""}
            record["x"] = "x" * (exact - len(canonical(record)))
            self.assertEqual(redact._padding(record), "")
            # One byte more goes to the next size.
            record["x"] += "x"
            self.assertEqual(size(record), 2 * exact)

    def test_the_copies_are_handed_over_before_anything_is_written(self):
        room = apart_vectors._room()
        entries = copy.deepcopy(room.entries)
        contents = copy.deepcopy(room.contents)
        seen = []

        def store(copies, office_copy):
            # The field is still there, and nothing is marked.
            self.assertEqual(room.entries, entries)
            self.assertEqual(room.contents, contents)
            seen.append((copies, office_copy))

        made = redact.redact(room, 5, self.entry, FIELD, office(),
                             apart_vectors.PRIVATE, CREATED,
                             about=[_to("ALICE")], decider=_to(DECIDES),
                             store=store)
        self.assertEqual(seen, [(made.copies, made.office_copy)])
        self.assertEqual(state(room, self.entry), "redacted")

        # If they can't be kept, nothing is marked and nothing taken out.
        class Full(Exception):
            pass

        def full(copies, office_copy):
            raise Full("no room for them")

        room = apart_vectors._room()
        with self.assertRaises(Full):
            redact.redact(room, 5, self.entry, FIELD, office(),
                          apart_vectors.PRIVATE, CREATED,
                          decider=_to(DECIDES), store=full)
        self.assertEqual(room.entries, entries)
        self.assertEqual(room.contents, contents)
        # The same for a redaction finished after its mark.
        mark = room.mark(5, self.entry, FIELD, apart_vectors.OFFICE,
                         apart_vectors.PRIVATE)
        with self.assertRaises(Full):
            redact.finish(room, mark, office(), CREATED,
                          decider=_to(DECIDES), store=full)
        self.assertEqual(state(room, self.entry), "unfinished")
        seen.clear()
        made = redact.finish(room, mark, office(), CREATED,
                             decider=_to(DECIDES), store=lambda c, o:
                             seen.append((c, o, state(room, self.entry))))
        self.assertEqual(seen, [([], made.office_copy, "unfinished")])
        self.assertEqual(state(room, self.entry), "redacted")

    def test_each_copy_is_for_one_alone(self):
        alice, bob = self.made.copies
        for envelope, name, other in [(alice, "ALICE", "BOB"),
                                      (bob, "BOB", DECIDES),
                                      (self.made.office_copy, DECIDES,
                                       "ALICE")]:
            with self.subTest(name):
                self.assertEqual(envelope["to"], did(name))
                redact.open_copy(envelope, secret(name), did(name),
                                 self.room.entries)
                with self.assertRaises(sealed.SealedError):
                    redact.open_copy(envelope, secret(other), did(other),
                                     self.room.entries)
                # With the right key under another's name, too.
                with self.assertRaises(sealed.SealedError):
                    redact.open_copy(envelope, secret(name), did(other),
                                     self.room.entries)

    def test_no_copy_is_kept_for_someone_with_no_key(self):
        room = apart_vectors._room()
        made = redact.redact(room, 5, self.entry, FIELD, office(),
                             apart_vectors.PRIVATE, CREATED,
                             decider=_to(DECIDES))
        self.assertEqual(made.copies, [])
        self.assertEqual(made.office_copy["to"], did(DECIDES))
        self.assertEqual(state(room, self.entry), "redacted")

    def test_a_redaction_that_cannot_be_made_changes_nothing(self):
        small = bytes(32)                # a sealing key of small order
        cases = [
            ("no such entry", dict(entry="0" * 64), RedactError),
            ("no such field", dict(field="name"), RedactError),
            ("an entry that is not text", dict(entry=["x"]), RedactError),
            ("the same one twice",
             dict(about=[_to("ALICE"), _to("ALICE")]), RedactError),
            ("the deciding office is also asked as a person",
             dict(about=[_to(DECIDES)]), RedactError),
            ("a sealing key no one should seal to",
             dict(about=[(did("ALICE"), small)]), sealed.SealedError),
            ("the deciding office's key is not a key",
             dict(decider=(did(DECIDES), b"short")), sealed.SealedError),
            ("a time that is not a time", dict(created="yesterday"),
             sealed.SealedError),
            ("a grant that is not a hash",
             dict(by=office()._replace(grant="mine")), sealed.SealedError),
            ("a grant that no record could hold",
             dict(by=office()._replace(grant=1.5)), sealed.SealedError),
            ("a ground the log does not take",
             dict(ground={"kind": "whim", "ref": "x"}), Refused),
            ("an office with no name",
             dict(by=office()._replace(name="")), Refused),
        ]
        for name, change, error in cases:
            with self.subTest(name):
                room = apart_vectors._room()
                entries = copy.deepcopy(room.entries)
                contents = copy.deepcopy(room.contents)
                args = dict(tick=5, entry=self.entry, field=FIELD,
                            by=office(), ground=apart_vectors.PRIVATE,
                            created=CREATED, about=[_to("ALICE")],
                            decider=_to(DECIDES))
                args.update(change)
                with self.assertRaises(error) as c:
                    redact.redact(room, **args)
                self.assertEqual(room.entries, entries)
                self.assertEqual(room.contents, contents)
                # No error's text holds any of the field.
                for fields in contents.values():
                    for salt, value in fields.values():
                        self.assertNotIn(salt, str(c.exception))
                        self.assertNotIn(str(value), str(c.exception))

    def test_the_reasons_are_the_ones_named(self):
        room = apart_vectors._room()
        with self.assertRaises(RedactError) as c:
            redact.redact(room, 5, "0" * 64, FIELD, office(),
                          apart_vectors.PRIVATE, CREATED,
                          decider=_to(DECIDES))
        self.assertEqual(c.exception.reason, redact.NOT_THERE)
        with self.assertRaises(RedactError) as c:
            redact.redact(room, 5, self.entry, FIELD, office(),
                          apart_vectors.PRIVATE, CREATED,
                          about=[_to("BOB"), _to("BOB")],
                          decider=_to(DECIDES))
        self.assertEqual(c.exception.reason, redact.TWICE)

    def test_a_field_is_redacted_once(self):
        # It is gone from the contents, and its mark is open.
        with self.assertRaises(RedactError) as c:
            redact.redact(self.room, 6, self.entry, FIELD, office(),
                          apart_vectors.PRIVATE, CREATED,
                          decider=_to(DECIDES))
        self.assertEqual(c.exception.reason, redact.NOT_THERE)
        # A field that is marked and still there is refused by the log,
        # after the copies are made, and nothing is taken out.
        room = apart_vectors._room()
        room.mark(5, self.entry, FIELD, apart_vectors.OFFICE,
                  apart_vectors.PRIVATE)
        contents = copy.deepcopy(room.contents)
        with self.assertRaises(Refused) as c:
            redact.redact(room, 6, self.entry, FIELD, office(),
                          apart_vectors.PRIVATE, CREATED,
                          decider=_to(DECIDES))
        self.assertEqual(c.exception.reason, apart.BAD_MARK)
        self.assertEqual(room.contents, contents)


class TestFinishing(unittest.TestCase):

    def setUp(self):
        self.room = apart_vectors._room()
        self.entry = self.room.entries[3]["hash"]
        self.mark = self.room.mark(5, self.entry, FIELD,
                                   apart_vectors.OFFICE,
                                   apart_vectors.PRIVATE)

    def finish(self, *mark, **more):
        return redact.finish(self.room, mark[0] if mark else self.mark,
                             office(), CREATED, decider=_to(DECIDES),
                             **more)

    def test_a_redaction_that_stopped_after_its_mark_is_finished(self):
        self.assertEqual(state(self.room, self.entry), "unfinished")
        entries = copy.deepcopy(self.room.entries)
        made = self.finish(about=[_to("ALICE")])
        self.assertEqual(made.mark, self.mark)
        self.assertEqual(self.room.entries, entries)   # the log: untouched
        self.assertEqual(state(self.room, self.entry), "redacted")
        self.assertNotIn(VALUE, kept(self.room, made.copies,
                                     made.office_copy))
        inside = redact.open_copy(made.copies[0], secret("ALICE"),
                                  did("ALICE"), self.room.entries)
        self.assertEqual(redact.what_was_there(inside)[1], VALUE)
        # The office's copy then decides, as after any redaction.
        decide(self.room, self.mark, made.office_copy)
        self.assertEqual(state(self.room, self.entry), "kept public")

    def test_only_a_mark_that_is_open_or_stands_is_finished(self):
        for odd in (self.entry, "0" * 64, None, 7):
            with self.subTest(odd=odd):
                with self.assertRaises(RedactError) as c:
                    self.finish(odd)
                self.assertEqual(c.exception.reason, redact.NO_MARK)
        made = self.finish()
        with self.assertRaises(RedactError) as c:
            self.finish()                              # already out
        self.assertEqual(c.exception.reason, redact.NOT_THERE)
        decide(self.room, self.mark, made.office_copy)
        with self.assertRaises(RedactError) as c:
            self.finish()                              # it is public
        self.assertEqual(c.exception.reason, redact.NO_MARK)
        self.assertEqual(state(self.room, self.entry), "kept public")

    def test_a_copy_that_cannot_be_made_takes_nothing_out(self):
        contents = copy.deepcopy(self.room.contents)
        with self.assertRaises(sealed.SealedError):
            self.finish(about=[(did("ALICE"), bytes(32))])
        self.assertEqual(self.room.contents, contents)
        self.assertEqual(state(self.room, self.entry), "unfinished")


class TestDeciding(unittest.TestCase):

    def setUp(self):
        self.room, self.made, self.entry = redacted()

    def test_the_office_keeps_it_public_from_its_copy(self):
        decision = decide(self.room, self.made.mark, self.made.office_copy,
                          apart_fields=VECTORS["kept"]["apart"])
        self.assertEqual(self.room.entries[-1]["hash"], decision)
        self.assertEqual(state(self.room, self.entry), "kept public")
        self.assertEqual(self.room.entries, VECTORS["kept"]["log"])
        self.assertEqual(self.room.contents, VECTORS["kept"]["contents"])
        joined = apart.join(self.room.entries, self.room.contents)[3]
        self.assertEqual(joined["data"][FIELD], VALUE)
        # It is the room as it was, with two entries more.
        before = apart_vectors._room()
        self.assertEqual(self.room.contents[self.entry],
                         before.contents[self.entry])

    def test_the_box_kept_in_the_file_decides_too(self):
        decide(self.room, self.made.mark,
               VECTORS["copies"][-1]["envelope"],
               apart_fields=VECTORS["kept"]["apart"])
        self.assertEqual(self.room.entries, VECTORS["kept"]["log"])

    def test_it_stays_redacted(self):
        case = VECTORS["stays"]
        redact.stays_redacted(self.room, case["tick"], self.made.mark,
                              case["office"], case["ground"],
                              case["decision"],
                              apart_fields=case["apart"])
        self.assertEqual(self.room.entries, case["log"])
        self.assertEqual(self.room.contents, case["contents"])
        self.assertEqual(state(self.room, self.entry), "redacted")
        # And is never made public again, even with the copy in hand.
        entries = copy.deepcopy(self.room.entries)
        contents = copy.deepcopy(self.room.contents)
        with self.assertRaises(Refused) as c:
            decide(self.room, self.made.mark, self.made.office_copy)
        self.assertEqual(c.exception.reason, apart.BAD_KEPT)
        self.assertEqual(self.room.entries, entries)
        self.assertEqual(self.room.contents, contents)

    def test_only_the_deciding_offices_own_copy_decides(self):
        entries = copy.deepcopy(self.room.entries)
        contents = copy.deepcopy(self.room.contents)
        # A person's copy, in the office's hands: it does not open.
        with self.assertRaises(sealed.SealedError):
            decide(self.room, self.made.mark, self.made.copies[0])
        # A person's own copy, opened by that person: it opens, it is
        # what the log held, and it names another as the deciding
        # office.
        with self.assertRaises(RedactError) as c:
            redact.keep_public(
                self.room, 6, self.made.mark, self.made.copies[0],
                secret("ALICE"), did("ALICE"), apart_vectors.KEEPER,
                apart_vectors.APPEAL, apart_vectors.trial_decision(1))
        self.assertEqual(c.exception.reason, redact.NOT_DECIDERS)
        self.assertEqual(self.room.entries, entries)
        self.assertEqual(self.room.contents, contents)
        # Every copy names the same deciding office.
        for envelope, name in [(self.made.copies[0], "ALICE"),
                               (self.made.copies[1], "BOB"),
                               (self.made.office_copy, DECIDES)]:
            inside = redact.open_copy(envelope, secret(name), did(name),
                                      self.room.entries)
            self.assertEqual(inside["decider"], did(DECIDES))
        # The office's copy of another field, redacted by another mark.
        other = redact.redact(self.room, 6, self.entry, "time", office(),
                              apart_vectors.PRIVATE, CREATED,
                              decider=_to(DECIDES))
        with self.assertRaises(RedactError) as c:
            decide(self.room, self.made.mark, other.office_copy)
        self.assertEqual(c.exception.reason, redact.OTHER_FIELD)
        self.assertEqual(state(self.room, self.entry), "redacted")
        self.assertEqual(self.room.entries[:len(entries)], entries)
        self.assertNotIn(FIELD, self.room.contents[self.entry])
        self.assertEqual(
            {k: v for k, v in self.room.contents.items()
             if k != self.entry and k != other.mark},
            {k: v for k, v in contents.items() if k != self.entry})

    def test_what_is_not_a_mark_is_refused_as_the_log_refuses_it(self):
        for odd in (self.entry, "0" * 64, None, ["x"]):
            with self.subTest(odd=odd):
                with self.assertRaises(Refused) as c:
                    decide(self.room, odd, self.made.office_copy)
                self.assertEqual(c.exception.reason, apart.BAD_KEPT)
                self.assertEqual(c.exception.where,
                                 len(self.room.entries))
        # Nor is another of the form's own entries that names an entry:
        # a removal, or a taking back.
        other = self.room.entries[4]["hash"]
        removal = self.room.append(
            7, apart.REMOVED, None,
            {"entry": other, "office": apart_vectors.MODERATOR,
             "ground": apart_vectors.GROUND,
             "decision": apart_vectors.trial_decision(3)})
        taking = self.room.append(7, apart.TAKEN_BACK, None,
                                  {"entry": other})
        for odd in (removal, taking):
            with self.subTest(odd=odd):
                with self.assertRaises(Refused) as c:
                    decide(self.room, odd, self.made.office_copy)
                self.assertEqual(c.exception.reason, apart.BAD_KEPT)
                with self.assertRaises(RedactError) as c:
                    redact.finish(self.room, odd, office(), CREATED,
                                  decider=_to(DECIDES))
                self.assertEqual(c.exception.reason, redact.NO_MARK)

    def test_a_decision_the_log_refuses_puts_nothing_back(self):
        contents = copy.deepcopy(self.room.contents)
        with self.assertRaises(Refused) as c:
            redact.keep_public(
                self.room, 6, self.made.mark, self.made.office_copy,
                secret(DECIDES), did(DECIDES), apart_vectors.KEEPER,
                apart_vectors.APPEAL, "not a hash")
        self.assertEqual(c.exception.reason, apart.BAD_KEPT)
        self.assertEqual(self.room.contents, contents)

    def test_a_copy_is_held_to_the_log_it_is_opened_against(self):
        # Another room, begun the same way, has other salts: the same
        # first entry, and so the same name, but no entry in common
        # after it that keeps a field apart.
        other = apart.Log(apart_vectors.TABLE, apart_vectors.FIRST)
        for step in apart_vectors.WRITTEN:
            other.append(*step)
        self.assertEqual(other.entries[0]["hash"],
                         self.room.entries[0]["hash"])
        with self.assertRaises(RedactError) as c:
            redact.open_copy(self.made.office_copy, secret(DECIDES),
                             did(DECIDES), other.entries)
        self.assertEqual(c.exception.reason, redact.NO_ENTRY)
        # A log that does not hold is refused as a log.
        broken = copy.deepcopy(self.room.entries)
        broken[2]["tick"] += 1
        with self.assertRaises(Refused):
            redact.open_copy(self.made.office_copy, secret(DECIDES),
                             did(DECIDES), broken)
        for odd in (None, {}, "log", []):
            with self.subTest(odd=odd), self.assertRaises(Refused):
                redact.held_to(VECTORS["copies"][0]["inside"], odd)

    def test_what_is_held_to_a_log_need_not_be_a_record_at_all(self):
        log = self.room.entries
        for odd in (None, [], "copy", {}, {"format": "open-worlds/x/v1"}):
            with self.subTest(odd=odd):
                with self.assertRaises(RedactError) as c:
                    redact.held_to(odd, log)
                self.assertEqual(c.exception.reason, redact.NOT_A_COPY)
        # A record of the kind with parts missing or of the wrong type
        # is refused for the first thing that fails, never a crash.
        good = {k: v for k, v in VECTORS["copies"][0]["inside"].items()
                if k != "proof"}
        for change, reason in [
                (dict(log=7), redact.OTHER_LOG),
                (dict(entry=["x"]), redact.NO_ENTRY),
                (dict(field=7), redact.NO_FIELD),
                (dict(field=["text"]), redact.NO_FIELD),
                (dict(hashed=7), redact.NOT_HELD),
                (dict(hashed=["salt", "text", "value"]), redact.NOT_HELD),
                (dict(hashed=""), redact.NOT_HELD),
                (dict(hashed=good["hashed"] + " "), redact.NOT_HELD),
                (dict(hashed="\ud800"), redact.NOT_HELD)]:
            with self.subTest(change=change):
                with self.assertRaises(RedactError) as c:
                    redact.held_to(dict(good, **change), log)
                self.assertEqual(c.exception.reason, reason)
        for missing in ("log", "entry", "field", "hashed"):
            with self.subTest(missing=missing):
                with self.assertRaises(RedactError):
                    redact.held_to({k: v for k, v in good.items()
                                    if k != missing}, log)


class TestOnALogOpenedAgain(unittest.TestCase):
    """The office that decides need not be the writer that redacted. It
    opens the log and the contents as they were published
    (`apart.Log.open`) and goes on from the log's head."""

    def opened(self, log, contents):
        # The trial salts go on where the log's writer stopped: it drew
        # one for each field it kept apart.
        used = sum(len(entry["apart"]) for entry in log)
        return apart.Log.open(log, contents,
                              salt=apart_vectors._salts(used))

    def test_the_office_decides_on_a_log_it_opens(self):
        case = VECTORS["redacted"]
        given = copy.deepcopy(case)
        room = self.opened(given["log"], given["contents"])
        decide(room, given["mark"], VECTORS["copies"][-1]["envelope"],
               apart_fields=VECTORS["kept"]["apart"])
        self.assertEqual(room.entries, VECTORS["kept"]["log"])
        self.assertEqual(room.contents, VECTORS["kept"]["contents"])
        # What was given to open is not touched by what was written.
        self.assertEqual(given, case)
        self.assertNotIn(FIELD, given["contents"][VECTORS["act"]["entry"]])

    def test_that_it_stays_redacted_is_decided_on_a_log_it_opens(self):
        case, stays = VECTORS["redacted"], VECTORS["stays"]
        room = self.opened(case["log"], case["contents"])
        redact.stays_redacted(room, stays["tick"], case["mark"],
                              stays["office"], stays["ground"],
                              stays["decision"],
                              apart_fields=stays["apart"])
        self.assertEqual(room.entries, stays["log"])
        self.assertEqual(room.contents, stays["contents"])

    def test_a_field_is_redacted_on_a_log_opened_again(self):
        before = apart_vectors._room()
        room = self.opened(before.entries, before.contents)
        entry = VECTORS["act"]["entry"]
        act = VECTORS["act"]
        made = redact.redact(
            room, act["tick"], entry, FIELD, office(), act["ground"],
            CREATED, about=[_to(name) for name in ABOUT],
            decider=_to(DECIDES), apart_fields=act["apart"])
        self.assertEqual(made.mark, VECTORS["redacted"]["mark"])
        self.assertEqual(room.entries, VECTORS["redacted"]["log"])
        self.assertEqual(room.contents, VECTORS["redacted"]["contents"])
        # The writer that was opened holds neither the value nor its
        # salt after the act, as the one that wrote the log does not.
        salt = before.contents[entry][FIELD][0]
        held = repr([vars(room), vars(room._scan), made])
        self.assertNotIn(salt, held)
        self.assertNotIn(VALUE, held)

    def test_a_redaction_that_stands_with_its_field_left_in_is_finished(self):
        # A log whose redaction stands, published with the field still
        # in its contents: no writer here leaves that, but a published
        # log can show it, and the check calls the field unfinished.
        stays = VECTORS["stays"]
        entry = VECTORS["act"]["entry"]
        contents = copy.deepcopy(stays["contents"])
        contents[entry][FIELD] = copy.deepcopy(
            apart_vectors._room().contents[entry][FIELD])
        self.assertEqual(
            apart.check(stays["log"], contents)[entry][FIELD],
            "unfinished")
        room = self.opened(stays["log"], contents)
        mark = VECTORS["redacted"]["mark"]
        made = redact.finish(room, mark, office(), CREATED,
                             decider=_to(DECIDES))
        self.assertEqual(room.entries, stays["log"])   # the log: untouched
        self.assertEqual(room.contents, stays["contents"])
        self.assertEqual(state(room, entry), "redacted")
        # The copy made is the field, though no decision can use it:
        # the redaction stands.
        inside = redact.open_copy(made.office_copy, secret(DECIDES),
                                  did(DECIDES), room.entries)
        self.assertEqual(redact.what_was_there(inside)[1], VALUE)
        with self.assertRaises(Refused) as c:
            decide(room, mark, made.office_copy)
        self.assertEqual(c.exception.reason, apart.BAD_KEPT)


if __name__ == "__main__":
    unittest.main()

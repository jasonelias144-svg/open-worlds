"""A council's count (formats/council.py), against
vectors/formats/council-v1.json, which rust/formats checks too: each
case's votes give the count recorded, proposals hold or are refused as
named, and the count never raises on what it is given."""
import json
import unittest

from formats import council, council_vectors, records

VECTORS = json.loads(council_vectors.FILE.read_text(encoding="utf-8"))


class TheVectors(unittest.TestCase):
    def test_the_file_is_what_the_code_writes(self):
        self.assertEqual(council_vectors.FILE.read_text(encoding="utf-8"),
                         council_vectors.text())

    def test_each_case_gives_its_count(self):
        for case in VECTORS["cases"]:
            with self.subTest(case=case["name"]):
                proposal = case.get("proposal", VECTORS["proposal"])
                self.assertEqual(
                    council.tally(proposal, case["votes"], case["births"]),
                    case["tally"])

    def test_the_cases_cover_what_they_name(self):
        tallies = {c["name"]: c["tally"] for c in VECTORS["cases"]}
        decided = [t["outcome"] for t in tallies.values()
                   if t["outcome"] is not None]
        undecided = [t for t in tallies.values() if t["outcome"] is None]
        self.assertTrue(decided and undecided)
        problems = " ".join(p for t in tallies.values()
                            for p in t["problems"])
        for words in ("not a vote that holds", "names another proposal",
                      "a choice the proposal doesn't have",
                      "dated before the proposal opens",
                      "dated after the proposal closes",
                      "by one whose birth no trusted world signed",
                      "one of several votes by one person at one time",
                      "the same vote as votes[",
                      "not a birth record that holds",
                      "not a proposal that holds"):
            self.assertIn(words, problems)


class Proposals(unittest.TestCase):
    def test_each_holds_or_is_refused_for_what_it_names(self):
        why = {
            "a proposal that closes when it opens": "$.closes",
            "a proposal with one choice": "$.choices",
            "a proposal with a choice twice": "$.choices",
            "a proposal trusting no world": "$.trusts",
            "a proposal with a quorum of 0": "$.quorum",
            "a proposal signed by another key than its council's":
                "signed by another key",
        }
        for case in VECTORS["proposals"]:
            with self.subTest(case=case["name"]):
                if case["holds"]:
                    records.check(case["record"])
                    continue
                with self.assertRaises(records.RecordError) as refused:
                    records.check(case["record"])
                self.assertIn(why[case["name"]], str(refused.exception))


class TheCount(unittest.TestCase):
    def setUp(self):
        self.proposal = VECTORS["proposal"]
        first = VECTORS["cases"][0]
        self.votes, self.births = first["votes"], first["births"]

    def test_it_never_raises_on_what_it_is_given(self):
        junk = [None, 5, "a vote", [], {}, {"format": council.VOTE}]
        for proposal in [None, {}, self.proposal]:
            with self.subTest(proposal=proposal):
                council.tally(proposal, junk, junk)

    def test_a_copy_of_a_vote_cancels_nothing(self):
        # Votes are public, so anyone presenting a count could repeat a
        # person's vote; the copy is refused, and the person still counts.
        alone = council.tally(self.proposal, self.votes, self.births)
        votes = self.votes + [self.votes[0]]
        counted = council.tally(self.proposal, votes, self.births)
        self.assertEqual(counted["counts"], alone["counts"])
        self.assertEqual(counted["outcome"], alone["outcome"])
        self.assertEqual(counted["problems"], [
            f"votes[{len(self.votes)}]: the same vote as votes[0]"])

    def test_a_copy_of_a_vote_that_doesnt_count_is_named_a_copy(self):
        other = next(v for c in VECTORS["cases"] for v in c["votes"]
                     if isinstance(v, dict)
                     and v.get("proposal") not in (None, records.record_hash(
                         self.proposal)))
        counted = council.tally(self.proposal, [other, other], self.births)
        self.assertEqual(counted["problems"], [
            "votes[0]: names another proposal",
            "votes[1]: the same vote as votes[0]"])

    def test_a_birth_from_an_untrusted_world_counts_no_one(self):
        untrusted = [b for b in self.births
                     if b["world"] not in self.proposal["trusts"]]
        self.assertEqual(len(untrusted), 1)
        born = untrusted[0]["individual"]
        theirs = next(v for c in VECTORS["cases"] for v in c["votes"]
                      if isinstance(v, dict) and v.get("person") == born)
        counted = council.tally(self.proposal, self.votes + [theirs],
                                self.births)
        self.assertEqual(counted["persons"], 3)
        self.assertEqual(counted["problems"], [
            "votes[3]: by one whose birth no trusted world signed"])

    def test_the_order_of_votes_changes_nothing_but_their_places(self):
        reversed_ = list(reversed(self.votes))
        a = council.tally(self.proposal, self.votes, self.births)
        b = council.tally(self.proposal, reversed_, self.births)
        self.assertEqual(a["counts"], b["counts"])
        self.assertEqual(a["outcome"], b["outcome"])


if __name__ == "__main__":
    unittest.main()

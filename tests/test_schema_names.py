"""docs/research/CHAT-SCHEMA.md names every definition in both schemas.

The page sets DeepSeek's schema (record 012-09-05) beside the project's
own, name by name, as the first step toward one schema that fits both.
A definition added to either file, or left off the page, fails here.

DeepSeek's schema is read as data, as text; nothing in sketches/ is
imported.
"""
import json
import os
import re
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PAGE = os.path.join(ROOT, "docs", "research", "CHAT-SCHEMA.md")
OURS = os.path.join(ROOT, "schemas", "records-v1.schema.json")
THEIRS = os.path.join(ROOT, "sketches", "deepseek", "012-09-05", "schemas",
                      "records-v1.schema.json@8640")


def definitions(path):
    with open(path, encoding="utf-8") as f:
        return sorted(json.load(f)["$defs"])


def named():
    with open(PAGE, encoding="utf-8") as f:
        return set(re.findall(r"`([A-Za-z]+)`", f.read()))


class SchemaNames(unittest.TestCase):
    def test_every_definition_of_deepseeks_is_on_the_page(self):
        self.assertEqual(
            [n for n in definitions(THEIRS) if n not in named()], [])

    def test_every_definition_of_the_projects_is_on_the_page(self):
        self.assertEqual(
            [n for n in definitions(OURS) if n not in named()], [])

    def test_the_page_gives_the_two_counts(self):
        with open(PAGE, encoding="utf-8") as f:
            page = f.read()
        self.assertIn(f"whole: {len(definitions(THEIRS))} definitions", page)
        self.assertIn(f"the project's: {len(definitions(OURS))})", page)

    def test_the_two_schemas_still_share_no_name(self):
        # The pages say so (STATUS.md, COLLABORATING.md). If this fails,
        # a definition has been fitted: say so on the page.
        self.assertEqual(
            sorted(set(definitions(OURS)) & set(definitions(THEIRS))), [])


if __name__ == "__main__":
    unittest.main()

"""Rewrite a sketch folder's known-failures.txt from a fresh run.

    python3 known_failures.py FOLDER

Copies FOLDER to a temporary directory, runs every test there as written
(SKETCH_RAW=1, so conftest.py marks nothing), and writes the tests and test
files that fail to FOLDER/known-failures.txt, each with its error. Run it
with the Python and packages of ../requirements.txt.
"""
from __future__ import annotations

import os
import re
import shutil
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET

HEADER = """\
# Which of DeepSeek's tests fail, as the code stands here. Written by us,
# not by DeepSeek (see README.md), with tools/known_failures.py.
# conftest.py reads it:
#   - a test file listed alone does not load, and is not collected;
#   - a test listed by name is an expected failure, and strict: if it
#     starts passing, the run fails until it is taken off this list.
# So the list is always true. The text after "  # " is the error.
"""


def _component(name: str):
    m = re.search(r"_c(\d+)_", name)
    return (int(m.group(1)) if m else 999, name)


def _reason(element, tree: str) -> str:
    lines = [l[1:].strip() for l in (element.text or "").splitlines()
             if l.startswith("E ")]
    reason = lines[-1] if lines else (element.get("message") or "")
    for line in lines:
        if re.match(r"^[A-Za-z_.]*(Error|Exception)\b", line):
            reason = line
            break
    reason = reason.replace(tree + os.sep, "")
    return re.sub(r"\s+", " ", reason)[:150]


def main(folder: str) -> int:
    folder = os.path.abspath(folder)
    with tempfile.TemporaryDirectory() as tmp:
        tree = os.path.join(tmp, "tree")
        shutil.copytree(folder, tree, ignore=shutil.ignore_patterns(
            "__pycache__"))
        junit = os.path.join(tmp, "run.xml")
        env = dict(os.environ, SKETCH_RAW="1", PYTHONDONTWRITEBYTECODE="1")
        subprocess.run(
            [sys.executable, "-m", "pytest", "-q",
             "--continue-on-collection-errors", f"--junitxml={junit}",
             "-o", "junit_family=xunit2"],
            cwd=tree, env=env, check=False)
        files, tests = [], []
        for case in ET.parse(junit).getroot().iter("testcase"):
            bad = [c for c in case if c.tag in ("failure", "error")]
            if not bad:
                continue
            if case.get("classname") == "":
                files.append((case.get("name") + ".py",
                              _reason(bad[0], tree)))
            else:
                tests.append((f"{case.get('classname')}.py::"
                              f"{case.get('name')}", _reason(bad[0], tree)))
    with open(os.path.join(folder, "known-failures.txt"), "w",
              encoding="utf-8") as f:
        f.write(HEADER + "\n# Test files that do not load\n")
        for name, reason in sorted(files, key=lambda x: _component(x[0])):
            f.write(f"{name}  # {reason}\n")
        f.write("\n# Tests that fail\n")
        for name, reason in sorted(tests, key=lambda x: _component(x[0])):
            f.write(f"{name}  # {reason}\n")
    print(f"{len(files)} test files don't load; {len(tests)} tests fail")
    return 0


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(__doc__)
        sys.exit(2)
    sys.exit(main(sys.argv[1]))

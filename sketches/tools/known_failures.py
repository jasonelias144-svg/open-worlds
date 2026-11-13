"""Rewrite a sketch folder's known-failures.txt from fresh runs.

    python3 known_failures.py FOLDER [RUNS]

Copies FOLDER, with the folders beside it (a record's code may build on
an earlier record's, as 012-05-01's does on 012-04-00's), to a temporary
directory and runs every test there as written (SKETCH_RAW=1, so conftest.py marks nothing), RUNS times (default
8), each with a different hash seed (PYTHONHASHSEED 0, 1, ...), since a
test that depends on the order of a set, or of random keys, can pass in
one run and fail in another. Then writes FOLDER/known-failures.txt: the
test files that don't load, the tests that fail in every run, and, marked
"sometimes:", the tests that fail in some runs only. Run it with the
Python and packages of ../requirements.txt.
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
# not by DeepSeek (see README.md), with tools/known_failures.py, from
# runs under several hash seeds. conftest.py reads it:
#   - a test file listed alone does not load, and is not collected;
#   - a test listed by name is an expected failure, and strict: if it
#     starts passing, the run fails until it is taken off this list;
#   - a test whose error starts with "sometimes:" failed in some runs
#     and passed in others, so either result is accepted.
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
    reason = reason.replace(os.path.dirname(tree) + os.sep, "../")
    # Memory addresses and random keys change from run to run; leave them
    # out, so that rewriting the list changes only what really changed.
    reason = re.sub(r"0x[0-9a-f]+", "0x...", reason)
    reason = re.sub(r"[0-9a-f]{12,}", "<hex>", reason)
    return re.sub(r"\s+", " ", reason)[:150]


def _run(tree: str, junit: str, seed: int):
    """One run: (test files that don't load, failing tests), each a
    dict from name to error."""
    env = dict(os.environ, SKETCH_RAW="1", PYTHONDONTWRITEBYTECODE="1",
               PYTHONHASHSEED=str(seed))
    subprocess.run(
        [sys.executable, "-m", "pytest", "-q",
         "--continue-on-collection-errors", f"--junitxml={junit}",
         "-o", "junit_family=xunit2"],
        cwd=tree, env=env, check=False, stdout=subprocess.DEVNULL)
    files, tests = {}, {}
    for case in ET.parse(junit).getroot().iter("testcase"):
        bad = [c for c in case if c.tag in ("failure", "error")]
        if not bad:
            continue
        if case.get("classname") == "":
            files[case.get("name") + ".py"] = _reason(bad[0], tree)
        else:
            tests[f"{case.get('classname')}.py::{case.get('name')}"] = \
                _reason(bad[0], tree)
    return files, tests


def main(folder: str, runs: int = 8) -> int:
    folder = os.path.abspath(folder)
    with tempfile.TemporaryDirectory() as tmp:
        # The folders beside it come too, at the same relative paths.
        shutil.copytree(os.path.dirname(folder), os.path.join(tmp, "all"),
                        ignore=shutil.ignore_patterns("__pycache__"))
        tree = os.path.join(tmp, "all", os.path.basename(folder))
        results = [_run(tree, os.path.join(tmp, f"run{seed}.xml"), seed)
                   for seed in range(runs)]
    file_names = set().union(*(set(f) for f, _ in results))
    if any(set(f) != file_names for f, _ in results):
        print("warning: which test files load changed between runs")
    files = [(n, next(f[n] for f, _ in results if n in f))
             for n in file_names]
    tests = []
    for name in set().union(*(set(t) for _, t in results)):
        failed = [t[name] for _, t in results if name in t]
        if len(failed) == runs:
            tests.append((name, failed[0]))
        else:
            tests.append((name, f"sometimes: failed in {len(failed)} of "
                                f"{runs} runs (hash seeds 0 to {runs - 1}):"
                                f" {failed[0]}"))
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
    if len(sys.argv) not in (2, 3):
        print(__doc__)
        sys.exit(2)
    sys.exit(main(sys.argv[1], *(int(a) for a in sys.argv[2:])))

"""Ours, not DeepSeek's (see README.md).

Reads known-failures.txt, which says which of DeepSeek's tests fail as the
code stands here:
  - a test file listed alone does not load, so it is not collected
    (sketch_status_test.py checks that it still doesn't load, with the
    same error);
  - a test listed by name is an expected failure, strictly: if it starts
    passing, the run fails until it is taken off the list;
  - a test whose error starts with "sometimes:" fails on some runs and
    passes on others (for example, it depends on the order of random keys
    or of a set), so either result is accepted for it.
A run of the whole folder (pytest with no arguments, as CI runs it) also
fails if the list names a test that doesn't exist. So a green run of the
whole folder means the list is exactly true.

With SKETCH_RAW=1 set, nothing is listed: every test runs as written
(tools/known_failures.py uses this to rewrite the list).
"""
import os
import sys
from pathlib import Path

import pytest

# Components 7, 11, 12, 18 and 20 import the poetry engine, whose code is
# in record 012-03-02's folder; we put that folder on the import path
# instead of copying it here. (Ours, not DeepSeek's.)
_DEPS = Path(__file__).resolve().parent.parent / "012-03-02"
if _DEPS.is_dir() and str(_DEPS) not in sys.path:
    sys.path.insert(0, str(_DEPS))

_HERE = Path(__file__).parent
SOMETIMES = "sometimes:"


def _known():
    files, tests = {}, {}
    text = (_HERE / "known-failures.txt").read_text(encoding="utf-8")
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        entry, _, reason = line.partition("  # ")
        entry = entry.strip()
        (tests if "::" in entry else files)[entry] = reason.strip()
    return files, tests


KNOWN_FILES, KNOWN_TESTS = ({}, {}) if os.environ.get("SKETCH_RAW") \
    else _known()
collect_ignore = sorted(KNOWN_FILES)


def pytest_collection_modifyitems(config, items):
    seen = set()
    for item in items:
        reason = KNOWN_TESTS.get(item.nodeid)
        if reason is not None:
            seen.add(item.nodeid)
            strict = not reason.startswith(SOMETIMES)
            item.add_marker(pytest.mark.xfail(reason=reason, strict=strict))
    # Only a run of the whole folder sees every test, so only then can a
    # listed test be known not to exist. `pytest some_test.py`, `pytest .`
    # or `pytest -k ...` skip this check.
    whole_run = not config.args or config.args == [str(_HERE)]
    stale = sorted(set(KNOWN_TESTS) - seen)
    if whole_run and not config.option.keyword and stale:
        raise pytest.UsageError(
            "known-failures.txt lists tests that don't exist: "
            + ", ".join(stale))

"""Ours, not DeepSeek's (see README.md).

Reads known-failures.txt, which says which of DeepSeek's tests fail as the
code stands here:
  - a test file listed alone does not load, so it is not collected
    (sketch_status_test.py checks that it still doesn't load);
  - a test listed by name is an expected failure, strictly: if it starts
    passing, the run fails until it is taken off the list.
So a green run means the list is exactly true. With SKETCH_RAW=1 set,
nothing is listed: every test runs as written (tools/known_failures.py
uses this to rewrite the list).
"""
import os
from pathlib import Path

import pytest

_HERE = Path(__file__).parent


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
            item.add_marker(pytest.mark.xfail(reason=reason, strict=True))
    whole_run = not config.args or config.args == [str(_HERE)]
    stale = sorted(set(KNOWN_TESTS) - seen)
    if whole_run and not config.option.keyword and stale:
        raise pytest.UsageError(
            "known-failures.txt lists tests that don't exist: "
            + ", ".join(stale))

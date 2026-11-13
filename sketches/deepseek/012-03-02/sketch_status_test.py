"""Ours, not DeepSeek's (see README.md): each test file that
known-failures.txt lists as not loading really doesn't load, and fails
with the error listed. When one starts loading, or fails some other way,
this test fails: rewrite the list (tools/known_failures.py)."""
import importlib

import pytest

from conftest import KNOWN_FILES


def _without_paths(message):
    """The error as known-failures.txt records it: the part before any
    " (" that names a file's path, which differs from machine to
    machine."""
    return message.split(" (")[0]


@pytest.mark.parametrize("filename", sorted(KNOWN_FILES))
def test_listed_file_still_does_not_load(filename):
    with pytest.raises(Exception) as raised:
        importlib.import_module(filename[:-len(".py")])
    error = f"{type(raised.value).__name__}: {raised.value}"
    assert _without_paths(error) == _without_paths(KNOWN_FILES[filename])

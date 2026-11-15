"""Ours, not DeepSeek's (see README.md): each test file that
known-failures.txt lists as not loading really doesn't load, and fails
with the error listed. When one starts loading, or fails some other way,
this test fails: rewrite the list (tools/known_failures.py)."""
import importlib.util
import sys
from pathlib import Path

import pytest

from conftest import KNOWN_FILES


def _without_paths(message):
    """The error as known-failures.txt records it: the part before any
    " (" that names a file's path, which differs from machine to
    machine."""
    return message.split(" (")[0]


def _load(filename):
    """Import a test file from its path, with its own folder first on the
    import path, as pytest does: so a file in a subfolder (such as
    rust/ur-world/examples/) finds the modules beside it."""
    path = Path(__file__).parent / filename
    folder = str(path.parent)
    sys.path.insert(0, folder)
    try:
        spec = importlib.util.spec_from_file_location(path.stem, path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
    finally:
        sys.path.remove(folder)


@pytest.mark.parametrize("filename", sorted(KNOWN_FILES))
def test_listed_file_still_does_not_load(filename):
    with pytest.raises(Exception) as raised:
        _load(filename)
    error = f"{type(raised.value).__name__}: {raised.value}"
    assert _without_paths(error) == _without_paths(KNOWN_FILES[filename])

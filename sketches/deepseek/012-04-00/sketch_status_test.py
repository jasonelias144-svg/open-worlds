"""Ours, not DeepSeek's (see README.md): each test file that
known-failures.txt lists as not loading really doesn't load. When one
starts loading, take it off the list, and its tests will run."""
import importlib

import pytest

from conftest import KNOWN_FILES


@pytest.mark.parametrize("filename", sorted(KNOWN_FILES))
def test_listed_file_still_does_not_load(filename):
    with pytest.raises(Exception):
        importlib.import_module(filename[:-len(".py")])

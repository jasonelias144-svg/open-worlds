"""Writing a record the same way everywhere, before it is hashed or signed.

The form is RFC 8785, the JSON Canonicalization Scheme, written by Trail
of Bits' `rfc8785` (requirements.txt), not by this project. RFC 8785
sorts keys by UTF-16 code units and writes numbers as JavaScript does;
this project's records keep three rules so that every language writes
them alike and no number is ever rounded (docs/research/FORMATS.md,
"Writing JSON the same way everywhere"):

1. keys are ASCII;
2. integers stay within -(2^53 - 1) and 2^53 - 1; a larger value, such as
   a 64-bit seed, is written as a string;
3. no floats: a quantity with a fraction is an integer in a stated unit,
   or a string.

`check` says what breaks a rule, or nothing; `canonical` refuses a value
that breaks one, and otherwise returns its RFC 8785 bytes.
"""
from __future__ import annotations

from typing import Any

import rfc8785

#: The largest integer a record may hold, and RFC 8785's own bound.
MAX_INT = 2 ** 53 - 1


class FormatError(ValueError):
    """A value that breaks one of the rules, so it isn't written."""


def check(value: Any, where: str = "$") -> str:
    """What breaks the rules in `value`, at which place, or "" if
    nothing does. Places are written as JSON paths ($.a[0].b)."""
    if value is None or type(value) is bool:
        return ""
    if type(value) is int:
        if not -MAX_INT <= value <= MAX_INT:
            return f"{where}: integer beyond 2^53 - 1; write it as a string"
        return ""
    if type(value) is float:
        return f"{where}: a float; use an integer in a stated unit"
    if type(value) is str:
        try:
            value.encode("utf-8")
        except UnicodeEncodeError:
            return f"{where}: text that isn't valid Unicode"
        return ""
    if type(value) is list:
        for i, item in enumerate(value):
            problem = check(item, f"{where}[{i}]")
            if problem:
                return problem
        return ""
    if type(value) is dict:
        for key, item in value.items():
            if type(key) is not str:
                return f"{where}: a key that isn't text"
            if not key.isascii():
                return f"{where}: key {key!r} isn't ASCII"
            problem = check(item, f"{where}.{key}")
            if problem:
                return problem
        return ""
    return f"{where}: a {type(value).__name__}, which JSON can't hold"


def canonical(value: Any) -> bytes:
    """The RFC 8785 bytes of `value`, which must keep the rules."""
    problem = check(value)
    if problem:
        raise FormatError(problem)
    return rfc8785.dumps(value)

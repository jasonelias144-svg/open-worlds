# docs/research/jcs_compare.py
"""Does the canonical JSON this project already signs equal RFC 8785 (the
JSON Canonicalization Scheme)? Research for course step 2
(docs/research/FORMATS.md).

It writes the same documents three ways and counts where they agree:

- the form multiverse/identity.py signs: sorted keys, no spaces, UTF-8,
  non-ASCII written as itself;
- the form world logs hash (world/core.py, rust/world-log): the same, but
  non-ASCII escaped as \\uXXXX;
- RFC 8785, by Trail of Bits' reference library, rfc8785 0.1.4.

The documents: five written by hand, then 2,000 random ones (seed 1),
with ASCII keys, strings mixing ASCII, control characters, accents, dashes,
emoji and line separators, and integers within RFC 8785's range,
+-(2**53 - 1). rfc8785 isn't a dependency of the project, so it is
installed apart:

    python3 -m pip install --target /some/dir rfc8785==0.1.4
    python3 -I docs/research/jcs_compare.py /some/dir
"""

import json
import random
import sys

sys.path.insert(0, sys.argv[1])
import rfc8785  # noqa: E402  (found on the path given)


def identity_form(document):
    return json.dumps(document, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False, allow_nan=False).encode("utf-8")


def log_form(document):
    return json.dumps(document, sort_keys=True, separators=(",", ":")).encode()


def documents():
    yield {"name": "ALICE", "key": "ab" * 32, "born": 0, "list": [3, 1, 2],
           "nested": {"z": 1, "a": None, "m": True}}
    yield {"say": "Hello, world.", "tick": 12, "n": -(2**53 - 1)}
    yield {"text": "caf\u00e9 \u2014 \u201cquoted\u201d \u2713",
           "ctrl": "a\tb\nc\x01\x1f\x7f", "esc": "\\ \" /"}
    yield {"astral": "\U0001F600 \U0001D538", "line": "\u2028\u2029"}
    yield {"big": 2**53 - 1, "zero": 0}
    rng = random.Random(1)
    alphabet = "abcXYZ_09 \t\n\"\\\u00e9\u2014\U0001F600\x01\x7f\u2028"
    for _ in range(2000):
        def text(letters, low, high):
            return "".join(rng.choice(letters)
                           for _ in range(rng.randint(low, high)))
        document = {text("abcdefghij_", 1, 6): text(alphabet, 0, 12)
                    for _ in range(rng.randint(1, 5))}
        document["i"] = rng.randint(-(2**53 - 1), 2**53 - 1)
        yield document


def main():
    every = list(documents())
    identity = sum(identity_form(d) == rfc8785.dumps(d) for d in every)
    log = sum(log_form(d) == rfc8785.dumps(d) for d in every)
    print(f"identity form equals RFC 8785: {identity} of {len(every)}")
    print(f"log form equals RFC 8785:      {log} of {len(every)}")
    try:
        rfc8785.dumps({"seed": 2**53})
    except Exception as refusal:  # the library's own error type
        print(f"2**53 refused by RFC 8785: {type(refusal).__name__}")


if __name__ == "__main__":
    main()

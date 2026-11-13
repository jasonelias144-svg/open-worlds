# Shared test vectors

What the Python reference writes, kept as files so that code in any
language can check itself against it, hash for hash. The Rust crate in
[`rust/world-log`](../rust/world-log) reads them in its tests.

| File | What it holds |
|---|---|
| `world-log.json` | The whole log of a short seeded run of the world kernel (`world/core.py`), with every kind of entry it writes. |
| `digests.json` | Bodies chosen to test the edges of writing JSON (key order, escapes, characters outside the basic plane, integers at the ends of 64 bits), each with the exact text the kernel hashes and its SHA-256. |

The files are written by [`world/vectors.py`](../world/vectors.py):

```
python3 -m world.vectors
```

and `tests/test_vectors.py` checks that they are still exactly what the
kernel writes. If the kernel's output changes on purpose, rewrite the
files, and every other language's tests then say whether it still agrees.

## How the kernel writes a log entry

Each entry holds `tick`, `kind`, `agent`, `data` and `prev`, and `hash`:
the SHA-256, in lowercase hex, of the entry without its `hash`, written as
Python's `json.dumps(body, sort_keys=True, separators=(",", ":"))` writes
it:

- keys sorted by code point, no spaces;
- `"` and `\` escaped with a backslash, and `\b \f \n \r \t` as
  themselves;
- every other character outside printable ASCII (space to `~`) as
  `\uXXXX` in lowercase hex, and a character beyond U+FFFF as its UTF-16
  surrogate pair (U+1F642 is `\ud83d\ude42`);
- integers in plain decimal; the log holds no other numbers.

`prev` is the hash of the entry before, or sixty-four zeros for the first.
The text in a log is always valid Unicode: the kernel refuses speech
holding a lone surrogate, which JSON readers in other languages can't
read.

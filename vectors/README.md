# Shared test vectors

What the Python reference writes, kept as files so that code in any
language can check itself against it, hash for hash. The Rust crate in
[`rust/world-log`](../rust/world-log) reads them in its tests.

| File | What it holds |
|---|---|
| `world-log.json` | The whole log of a short seeded run of the world kernel (`world/core.py`), with every kind of entry it writes. |
| `digests.json` | Bodies chosen to test the edges of writing JSON (key order, escapes, characters outside the basic plane, integers at the ends of 64 bits), each with the exact text the kernel hashes and its SHA-256. |
| `ur-garden-log.json` | The Ur-world's Hello World: the whole log of the garden with ALICE and BOB, written by the Rust kernel (`rust/ur-world`). |
| `ur-chunks.json` | The Ur-world's generator, version 1: for three seeds, the ground height of some columns and the hash of some chunks. |
| `formats/eddsa-jcs-2022.json` | Records signed with `eddsa-jcs-2022` (course step 2): the W3C specification's own example, step by step; records this project signs, with their RFC 8785 form; proofs that must be refused; and values that break this project's three rules. Written by `python3 -m formats.vectors`, read by `rust/formats`. |
| `formats/records-v1.json` | The records the offices keep, against `schemas/records-v1.schema.json`: test parties (keys public to everyone, never for anything real), records of every kind that hold, each with its hash, and records that must be refused, each named for why. Written by `python3 -m formats.record_vectors`, read by `rust/formats`. |

The W3C example in `formats/eddsa-jcs-2022.json` is copied from "Data
Integrity EdDSA Cryptosuites v1.0" (W3C Recommendation, 15 May 2025,
Appendix B.3), under the [W3C Software and Document
License](https://www.w3.org/copyright/software-license-2023/); the rest of
this repository is CC0.

The first two are written by the Python kernel,
[`world/vectors.py`](../world/vectors.py):

```
python3 -m world.vectors
```

and `tests/test_vectors.py` checks that they are still exactly what the
kernel writes. If the kernel's output changes on purpose, rewrite the
files, and every other language's tests then say whether it still agrees.

For the Ur-world the Rust kernel is the reference, so the last two are
written by Rust:

```
cd rust && cargo run -p ur-world --example garden -- --vectors ../vectors
```

The Rust tests check that they are still what the kernel writes, and
`tests/test_ur_world_vectors.py` checks them from Python. The garden's log
holds by `World.verify_log`, and the generator, written again in Python from
its documented rules, gives the same heights and chunks.

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
- integers in plain decimal. The kernel writes no other numbers; its seed
  is whatever its operator gives it.

`prev` is the hash of the entry before, or sixty-four zeros for the first.
Text that agents supply is always valid Unicode: the kernel refuses
speech holding a lone surrogate, which JSON readers in other languages
can't read. Text its operator supplies (the rules version, agent ids, the
reason given when taking someone out) isn't checked.

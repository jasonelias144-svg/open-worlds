# Shared test vectors

What the Python reference writes, kept as files so that code in any
language can check itself against it, hash for hash. The Rust crate in
[`rust/world-log`](../rust/world-log) reads them in its tests.

| File | What it holds |
|---|---|
| `world-log.json` | The whole log of a short seeded run of the world kernel (`world/core.py`), with every kind of entry it writes. |
| `digests.json` | Bodies chosen to test the edges of writing JSON (key order, escapes, characters outside the basic plane, integers at the ends of 64 bits), each with the exact text the kernel hashes and its SHA-256. |
| `ur-garden-log.json` | The Ur-world's Hello World: the whole log of the garden with its two scripted stand-ins, WALKER and GARDENER, each entering with a signed arrival (`open-worlds/arrival/v1`), written by the Rust kernel (`rust/ur-world`). The garden is a trial world of its own, and its keys are trial keys made from its seed, public to everyone. |
| `ur-garden-head.json` | The head of that log, signed by the garden's trial world key (`open-worlds/log-head/v1`), covering all of it. |
| `ur-garden-hosted.json` | The three plant worlds that garden hosts in its glasshouses (`rust/ur-world/src/host.rs`): each one's log, signed head and birth record, with the trial template and law they name. The garden's log names each step it gave each of them; `tests/test_ur_world_vectors.py` checks the two against each other. Every key is a trial key, public to everyone. |
| `ur-chunks.json` | The Ur-world's generator, version 1: for three seeds, the ground height of some columns and the hash of some chunks. |
| `plant-world.json` | Plant worlds (`rust/plant-world`): five worlds grown from one template with different dials, one of them in a pot, each with its whole log, its signed head and its signed birth record; the template, signed by a trial key; and the plants' law with its hash. Written by Rust; every step is checked against DeepSeek's sketch, and the rest from Python. |
| `formats/eddsa-jcs-2022.json` | Records signed with `eddsa-jcs-2022` (course step 2): the W3C specification's own example, step by step; records this project signs, with their RFC 8785 form; proofs that must be refused; and values that break this project's three rules. Written by `python3 -m formats.vectors`, read by `rust/formats`. |
| `formats/records-v1.json` | The records the offices keep, who an individual and a world are (identity, birth records, mind record), a world's template, and the project's key list, against `schemas/records-v1.schema.json`: test parties (keys public to everyone, never for anything real), records of every kind that hold, each with its hash, records that must be refused, each named for why, worlds' birth records checked against their template's dials, and key lists checked against the version before. Written by `python3 -m formats.record_vectors`, read by `rust/formats`. |
| `formats/hpke-base-v1.json` | Sealing with HPKE (course step 2): RFC 9180's own example for the suite in use; test recipients; boxes made by Python and by Rust, each opened by the other (Rust also makes its own again from a fixed `ikmE`); and boxes, labels and keys that must be refused. Written by `python3 -m formats.seal_vectors`, which keeps each box that still opens, read by `rust/formats`. |
| `formats/sealed-records-v1.json` | Sealed records (course step 2): world-keys and journal entries that hold and that don't; envelopes that open, with the hash of the record inside; envelopes the opener must refuse, each saying what it was sealed to, under which label, and what is inside; and envelopes refused for their shape. Written by `python3 -m formats.sealed_vectors`, which keeps each box that still opens as stated, read by `rust/formats`. |

The W3C example in `formats/eddsa-jcs-2022.json` (its `w3c` object)
includes material copied from "Data Integrity EdDSA Cryptosuites v1.0",
W3C Recommendation, 15 May 2025, Appendix B.3,
https://www.w3.org/TR/vc-di-eddsa/. Copyright © 2025 World Wide Web
Consortium. https://www.w3.org/copyright/software-license-2023/. The rest
of this repository is CC0.

The first two are written by the Python kernel,
[`world/vectors.py`](../world/vectors.py):

```
python3 -m world.vectors
```

and `tests/test_vectors.py` checks that they are still exactly what the
kernel writes. If the kernel's output changes on purpose, rewrite the
files, and every other language's tests then say whether it still agrees.

For the Ur-world the Rust kernel is the reference, so its three files are
written by Rust:

```
cd rust && cargo run -p ur-world --example garden -- --vectors ../vectors
```

The Rust tests check that they are still what the kernel writes, and
`tests/test_ur_world_vectors.py` checks them from Python. The garden's log
holds by `World.verify_log`, its arrivals and head hold by
`formats/records.py`, and the generator, written again in Python from its
documented rules, gives the same heights and chunks.

The plant worlds are written by Rust too:

```
cd rust && cargo run -p plant-world --example plant -- --vectors ../vectors
```

The folder named after `--vectors` must already exist.

Their rule is DeepSeek's, from record 012-06-02, and the sketch is its
reference: `sketches/deepseek/012-06-02/plant_world_vectors_test.py`,
run by that folder's pytest, grows each world again with the sketch's
own `advance` and must get the same branches and tips at every step.
`tests/test_plant_world_vectors.py` checks the rest from Python, without
importing the sketch: each log holds by `World.verify_log` and grows by
the rule as `rust/plant-world/src/rule.rs` documents it, each head
covers its whole log, and each birth record names its template, law and
dials as `formats/records.py` requires.

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

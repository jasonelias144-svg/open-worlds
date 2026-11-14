# The project's keys: the public halves

`key-list.json` is the project's key list (`open-worlds/key-list/v1`):
which key holds each role, signed by the multiverse's root. Version 1
was made at the ceremony of 2026-11-14 (docs/research/KEYS.md, "As
built, part three"). A reader takes the latest version on `main`, and
checks every version from the one it holds, or from 1 for a new reader
(`formats.records.key_list_chain_problems`).

The private halves are never here. They live only in the project's
private repository; `tests/test_no_private_keys.py` fails on any found in
this one.

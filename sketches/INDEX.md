# Where the sketches and the course meet

This is the one place that states the overlap between the creative side
(this folder) and the development side (the rest of the repository). The
course ([docs/COURSE.md](../docs/COURSE.md)) and
[docs/COLLABORATING.md](../docs/COLLABORATING.md) link here instead of
repeating it.

## The records

Both are verbatim copies. A line starting with `::` is the founder's
message; the rest is DeepSeek's reply.

| Record | What it covers | Lines | SHA-256 |
|---|---|---|---|
| [012-04-00, Patterns and Multiverses](records/012-04-00-DPSK-Patterns_Multiverses.txt) | The multiverse sketch, components 1 to 43, ending with the founder's question about a council | 42,244 | `977a50ead8f1ccfa4f8f8771ce3603b2c7c39e693b5c42bdccf586f6e5b4557b` |
| [012-03-02, Patterns, Texts and Inventions](records/012-03-02-DPSK-Patterns_Texts_and_Inventions.txt) | The poetry engine and its curriculum, which the multiverse sketch builds on | 23,426 | `978eac920205ec2b487efc33f927dfd62da95b12ad78f1760fef9277b74908de` |

## Links from the records

The records link to the founder's GitHub and to this repository's
`docs/COLLABORATING.md`, on purpose: a record that travels on its own
leads back here. `tests/test_record_links.py` fails if a file a record
links to is moved or renamed, so the links keep working.

## Record 012-04-00, component by component

"Line" is where the component begins in the record. "Tests as written"
counts DeepSeek's own tests for it, run together with all the others on
Python 3.12 ([known-failures.txt](deepseek/012-04-00/known-failures.txt)
has each failure's error). "Doesn't load" means the test file fails on
import, so none of its tests run. "Course" is the step it relates to. "In
open-worlds" says whether any of it is in the working code, and how.

| # | What it is | Line | Tests as written | Course | In open-worlds |
|---|---|---|---|---|---|
| 1 | The atom of identity | 236 | 9 of 9 pass | 1, 2 | `multiverse/identity.py`, changed (step 1); since step 2 an identity is a key |
| 2 | The passport | 527 | 5 of 11 | 1, 3 | `multiverse/passport.py`, changed (step 1) |
| 3 | The protocol, WCP/0.1, and its conformance test | 1007 | 13 of 13 | 1, 2 | `multiverse/protocol.py`, `conformance.py`, changed; now WCP/0.2 |
| 4 | The poetry world | 1860 | doesn't load | 1 | `multiverse/poetry_world.py`, changed (step 1) |
| 5 | The chemistry world | 2933 | 13 of 16 | 1, 4 | `multiverse/chemistry_world.py`, changed (step 1) |
| 6 | The multiverse registry | 3861 | 5 of 15 | 1 | `multiverse/registry.py`, changed (step 1) |
| 7 | The first collaboration | 4654 | doesn't load | 1 | `multiverse/collaboration.py`, changed (step 1) |
| 8 | A conformance test any language can be checked with, and an HTTP shim | 5895 | 5 of 11 | 12 | no |
| 8 | A TypeScript implementation (`ts/`), a registry addition (`multiverse_c6.py@7216`) and a cross-language test (`cross_language_test.sh`) | 6862 | not run | 12 | no |
| 9 | Cross-language SDKs and the cross-language test harness (`cross_language_test.sh@7779`) | 7449 | not run | 12 | no |
| 10 | A Go SDK (`go/`) and the full federation test (`cross_language_test.sh@8762`) | 8056 | not run | 12 | no |
| 11 | Language models as apprentices | 8890 | doesn't load | 11 | no |
| 12 | Cost reports | 9971 | doesn't load | 11 | no |
| 13 | Signatures, WCP/0.2 | 10831 | 12 of 12 | 2 | rebuilt in step 2: an identity is its key, and every request is signed |
| 14 | The conformance test for WCP/0.2 | 11541 | 11 of 26 | 2 | rebuilt in step 2 (`multiverse/conformance.py`) |
| 15 | Signed passports | 12695 | 20 of 22 | 3 | no; step 3 is next |
| 16 | Finding a world's key from its manifest | 13648 | 9 of 15 | 3, 12 | no |
| 17 | Signed registries | 14357 | doesn't load | 3, 12 | no |
| 18 | Several models together | 15152 | doesn't load | 11 | no |
| 19 | The federation runner (`federation.py`, `Makefile`) | 15921 | `federation_test.py`: 0 of 4 | 11, 12 | no |
| 20 | Real Hugging Face models | 16671 | doesn't load | 11 | no |
| 21 | Cross-world provenance | 17584 | 5 of 11 | 3, 5 | no |
| 22 | Leaving, with signed departures | 18635 | 3 of 15 | 3 | leaving has been in open-worlds since step 1; signed departures are step 3 |
| 23 | Provenance over several visits | 19519 | 18 of 21 | 3, 5 | no |
| 24 | Signed provenance reports | 20553 | 15 of 15 | 3 | no |
| 25 | A chain of witnesses | 21340 | 20 of 20 | none yet | no |
| 26 | Signed revocations | 22387 | 18 of 18 | none yet | no |
| 27 | Witnesses as a graph (DAG) | 23513 | 19 of 23, and one more on some runs | none yet | no |
| 28 | Signed manifests: trust on first use, key rotation | 24830 | 17 of 19 | 3; keeping keys safely | no |
| 29 | Signed manifests in the registry | 26041 | 3 of 13 | 3, 12 | no |
| 30 | The federation runner, updated (`federation.py@27213`) | 27202 | not collected (an addition) | 12 | no |
| 31 | A signed verdict on a federation run | 27741 | 16 of 16 | none yet | no |
| 32 | Saving and loading a federation as one bundle | 28547 | 4 of 23 | none yet | no |
| 33 | Leaving the chemistry world and the registry | 29885 | 16 of 16 | 1 | in open-worlds since step 1 |
| 34 | Graphs that refer to other worlds' graphs | 30606 | 15 of 16 | none yet | no |
| 35 | Proposed (bundles of several worlds), not built: the founder turned to identity across worlds | 31889 | | | |
| — | Identity across worlds: four meanings of a multidimensional self (no code) | 31899 | | | |
| 36 | A person: one identity above world-level identities | 31975 | 18 of 22 | not yet (proposed: persons, after step 3) | no |
| 37 | A world where persons meet, with co-signed claims | 33328 | 7 of 24 | not yet (persons; the council) | no |
| 38 | A person's signed list of identities | 34540 | 24 of 24 | not yet (persons) | no |
| 39 | Forks and merges | 35681 | 23 of 26 | not yet (persons) | no |
| 40 | One signature across worlds | 37243 | doesn't load | not yet (persons) | no |
| 41 | The octopus architecture | 38861 | 20 of 22 | not yet (architectures, as examples) | no |
| — | Telling architectures apart: four questions (no code) | 40062 | | | |
| 42 | The relay architecture (central and peripheral nervous system) | 40110 | 26 of 28 | not yet (architectures) | no |
| 43 | The swarm architecture | 41207 | 25 of 33 | not yet (architectures) | no |
| — | The founder's last message: a small group that decides for the whole (a council, a triumvirate), not yet answered | 42242 | | | |

In all: as written, 414 of DeepSeek's tests pass and 144 fail. One more
passes on some runs and fails on others: component 27's
`test_combined_to_dict_json`, where two signers tie in the order and the
tie falls either way. Eight test files don't load. The TypeScript and Go
code isn't run here yet.

All 135 code files in the record are written out. Fifteen code blocks in
the record are examples in the prose, not files, and stay in the record:
eight JSON messages in the protocol's description (lines 5635 to 5776),
four commands to run (16439, 16494, 17445, 29748) and three usage
examples (28455, 29754, 29766).

"Not yet" in the Course column means the idea isn't on the course. The
two proposals there (a step for persons after step 3; the architectures
as small examples on the core) are the technical lead's, put to the
founder on 2026-11-13, and not decided.

## Record 012-03-02

The code in this record (the poetry engine, 56 code blocks) isn't written
out here yet. Step 1 brought parts of its components 21 and 22 (the
turn, the critical stances, the apprentice poet) into open-worlds as
`multiverse/apprentice.py`, changed ([docs/MULTIVERSE.md](../docs/MULTIVERSE.md)
says how). Component 11 of
012-04-00 imports one of its files (`poetry_engine_c21`), so writing it
out is what lets component 11 load.

## Changes to DeepSeek's code

None yet: every file in `deepseek/012-04-00/` is exactly as the record
has it. Each change will be listed here, with its reason, and under
`"changed"` in [tools/names-012-04-00.json](tools/names-012-04-00.json).

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
| [012-04-00, Patterns and Multiverses](records/012-04-00-DPSK-Patterns_Multiverses.txt) | The multiverse sketch, components 1 to 63, complete. It ends with DeepSeek proposing component 64, a specification for a first live federation | 70,958 | `6a348012fe321fc758f37f8a7625cc124872f4806beef6096ad475081d409387` |
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
has each failure's error). The tests are always as written; where a row
names a fix, the code it tests has that fix (see "Changes to DeepSeek's
code", below). "Doesn't load" means the test file fails on
import, so none of its tests run. "Course" is the step it relates to. "In
open-worlds" says whether any of it is in the working code, and how.

| # | What it is | Line | Tests as written | Course | In open-worlds |
|---|---|---|---|---|---|
| 1 | The atom of identity | 236 | 9 of 9 pass | 1, 2 | `multiverse/identity.py`, changed (step 1); since step 2 an identity is a key |
| 2 | The passport | 527 | 5 of 11 | 1, 3 | `multiverse/passport.py`, changed (step 1); since step 3 its stamps are signed by worlds |
| 3 | The protocol, WCP/0.1, and its conformance test | 1007 | 13 of 13 | 1, 2 | `multiverse/protocol.py`, `conformance.py`, changed; now WCP/0.4 |
| 4 | The poetry world | 1860 | 18 of 21, with `turns_from_log` attached (fix 2) | 1 | `multiverse/poetry_world.py`, changed (step 1) |
| 5 | The chemistry world | 2933 | 13 of 16 | 1, 4 | `multiverse/chemistry_world.py`, changed (step 1); rebuilt on `chem/` in step 4: real molecules and reactions in a soup that runs in time |
| 6 | The multiverse registry | 3861 | 5 of 15 | 1 | `multiverse/registry.py`, changed (step 1) |
| 7 | The first collaboration | 4654 | doesn't load | 1 | `multiverse/collaboration.py`, changed (step 1) |
| 8 | A conformance test any language can be checked with, and an HTTP shim | 5895 | 5 of 11 | 13 | no |
| 8 | A TypeScript implementation (`ts/`), a registry addition (`multiverse_c6.py@7216`) and a cross-language test (`cross_language_test.sh`) | 6862 | not run | 13 | no |
| 9 | Cross-language SDKs and the cross-language test harness (`cross_language_test.sh@7779`) | 7449 | not run | 13 | no |
| 10 | A Go SDK (`go/`) and the full federation test (`cross_language_test.sh@8762`) | 8056 | not run | 13 | no |
| 11 | Language models as apprentices | 8890 | doesn't load | 12 | no |
| 12 | Cost reports | 9971 | doesn't load | 12 | no |
| 13 | Signatures, WCP/0.2 | 10831 | 12 of 12 | 2 | rebuilt in step 2: an identity is its key, and every request is signed |
| 14 | The conformance test for WCP/0.2 | 11541 | 11 of 26 | 2 | rebuilt in step 2 (`multiverse/conformance.py`) |
| 15 | Signed passports | 12695 | 20 of 22 | 3 | rebuilt in step 3 (`multiverse/passport.py`): a world is a key, and signs stamps for arrivals, departures and things made |
| 16 | Finding a world's key from its manifest | 13648 | 9 of 15 | 3, 13 | partly, in step 3: a manifest names its world's key and is signed by it, and `verify_passport` takes the keys a checker knows; fetching them from a running world is step 13 |
| 17 | Signed registries | 14357 | doesn't load | 3, 13 | no |
| 18 | Several models together | 15152 | doesn't load | 12 | no |
| 19 | The federation runner (`federation.py`, `Makefile`) | 15921 | `federation_test.py`: 0 of 4 | 12, 13 | no |
| 20 | Real Hugging Face models | 16671 | doesn't load | 12 | no |
| 21 | Cross-world provenance | 17584 | 5 of 11 | 3, 5 | partly: since step 5, a journey through several worlds leaves a passport of signed stamps, with what was made in each; no provenance reports |
| 22 | Leaving, with signed departures | 18635 | 3 of 15 | 3 | leaving since step 1; signed departure stamps since step 3, and a leave the world doesn't stamp still ends the visit |
| 23 | Provenance over several visits | 19519 | 18 of 21 | 3, 5 | partly, as 21 (step 5) |
| 24 | Signed provenance reports | 20553 | 15 of 15 | 3 | no |
| 25 | A chain of witnesses | 21340 | 20 of 20 | none yet | no |
| 26 | Signed revocations | 22387 | 18 of 18 | none yet | no |
| 27 | Witnesses as a graph (DAG) | 23513 | 19 of 23, and one more on some runs | none yet | no |
| 28 | Signed manifests: trust on first use, key rotation | 24830 | 17 of 19 | 3, 6 | partly: manifests are signed since step 3, and since step 6 a key can be signed over (`multiverse/succession.py`; both keys sign); no trust-on-first-use store |
| 29 | Signed manifests in the registry | 26041 | 3 of 13 | 3, 13 | no |
| 30 | The federation runner, updated (`federation.py@27213`) | 27202 | not collected (an addition) | 13 | no |
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
| 40 | One signature across worlds | 37243 | 25 of 25, with its demo attached (fix 1) | not yet (persons) | no |
| 41 | The octopus architecture | 38861 | 20 of 22 | not yet (architectures, as examples) | no |
| — | Telling architectures apart: four questions (no code) | 40062 | | | |
| 42 | The relay architecture (central and peripheral nervous system) | 40110 | 26 of 28 | not yet (architectures) | no |
| 43 | The swarm architecture | 41207 | 25 of 33 | not yet (architectures) | no |
| — | The founder: a small group that decides for the whole (a council, a triumvirate) | 42242 | | | |
| 44 | The triumvirate: a council whose signed votes are counted | 42245 | 34 of 38, with its demo attached (fix 1) | not yet (architectures) | no |
| 45 | Deliberation: signed positions that change before the vote | 44028 | 24 of 24, with its demo attached (fix 1) | not yet (architectures) | no |
| 46 | Councils that cite each other's decisions | 45533 | 13 of 22, with its demo attached (fix 1) | not yet (architectures) | no |
| — | The founder: a free tier and a paid tier | 47194 | | | |
| 47 | The autonomic architecture | 47235 | 22 of 29, with its demo attached (fix 1) | not yet (architectures) | no |
| 48 | Federating different architectures | 48345 | 28 of 30, with its demo attached (fix 1) | none yet | no |
| 49 | Saving and loading a federation | 50367 | 32 of 35, with its demo attached (fix 1) | none yet | no |
| 50 | The institutional architecture: units run by a signed policy | 51932 | 22 of 53, with its demo attached (fix 1) | not yet (architectures) | no |
| 51 | A runner that demonstrates every architecture | 53767 | 19 of 20 | none yet | no |
| 52 | The epidemic architecture: units that pass a message along | 54755 | 11 of 29, with its demo attached (fix 1) | not yet (architectures) | no |
| 53 | The runner, updated for seven architectures (additions `multiverse_c51.py@55925`, `@55958`, `@56021`, `multiverse_c51_test.py@56034`) | 55907 | not collected (additions) | none yet | no |
| 54 | The message as a signed attestation | 56214 | 11 of 26, with its demo attached (fix 1) | none yet | no |
| — | The founder: each world has an AI admin that oversees it and drives its development | 57659 | | | |
| 55 | The world curator: a world's voice, which proposes and doesn't decide | 57670 | 26 of 32, with its demo attached (fix 1) | next in line (curators); 3 gives worlds their keys | no |
| 56 | A signed relay chain: each hop signed by sender and receiver | 59175 | 12 of 26, with its demo attached (fix 1) | none yet | no |
| 57 | Contracts between worlds | 61021 | 36 of 37, with its demo attached (fix 1) | next in line (contracts between worlds) | no |
| 58 | Acts that cite a contract | 63085 | 22 of 24, with its demo attached (fix 1) | next in line (contracts between worlds) | no |
| 59 | Announcing a contract to other worlds | 64266 | 22 of 25, with its demo attached (fix 1) | next in line (contracts between worlds) | no |
| — | The founder: a public ledger, like a blockchain, across worlds | 65719 | | | |
| 60 | Announcing a revocation | 65756 | 22 of 25, with its demo attached (fix 1) | next in line (contracts between worlds) | no |
| 61 | The ledger as a store of commitments: a specification (no code) | 67239 | | next in line (a shared log of commitments) | no |
| 62 | The ledger, built: a Merkle log with offline proofs | 67507 | 44 of 45, with its demo attached (fix 1) | next in line (a shared log of commitments) | no |
| 63 | Each world's published rule for contract disputes | 69235 | 20 of 27, with its demo attached (fix 1) | next in line (contracts between worlds) | no |

In all, with fixes 1 and 2 (below): 877 of DeepSeek's tests pass and
274 fail.
One more passes on some runs and fails on others: component 27's
`test_combined_to_dict_json`, where two signers tie in the order and the
tie falls either way (it depends on random keys, so how many of the
eight runs it fails in changes from one rewrite of the list to the
next). 6 test files don't load. Components 7, 11, 12, 18 and 20 import
the poetry engine of record 012-03-02 (`poetry_engine_c21`), not written
out here yet. 17 imports `InMemoryKeyResolver` from component 16, but it
is defined in 15. The TypeScript and Go code isn't run here yet.

Before fix 1, as written: 433 pass, 145 fail, 1 sometimes, and 25 test
files don't load. Eighteen of those, components 40 and 44 to 63, failed
only because DeepSeek gave each demo as a block of its own, after the
module the tests import it from; five more, components 4, 7, 12, 18 and
20, needed `turns_from_log`, which the record gives the same way, after
component 4's module. Fix 1 attaches the demos: 552 more tests run, of
which 426 pass. Fix 2 attaches `turns_from_log`: component 4's 21 tests
run, of which 18 pass; the other four files then stop at the poetry
engine instead.

All 210 code files in the record are written out. Fifteen code blocks in
the record are examples in the prose, not files, and stay in the record:
eight JSON messages in the protocol's description (lines 5635 to 5776),
four commands to run (16439, 16494, 17445, 29748) and three usage
examples (28455, 29754, 29766).

"Not yet" in the Course column means the idea isn't on the course. The
two proposals there (a step for persons after step 3; the architectures
as small examples on the core) are the technical lead's, put to the
founder on 2026-11-13, and not decided. "Next in line" means the course's
list of steps to add as steps are done ([docs/COURSE.md](../docs/COURSE.md)).

The founder's tier idea (line 47194) is about how open-worlds is run, not
about the code: DeepSeek's reply, that tiers belong where the service is
hosted and not in the protocol, keeps "anyone can join" true in the code.
No tier may gate the freedoms the charter protects: leaving, voice and
information.

## Record 012-03-02

The code in this record (the poetry engine, 56 code blocks) isn't written
out here yet. Step 1 brought parts of its components 21 and 22 (the
turn, the critical stances, the apprentice poet) into open-worlds as
`multiverse/apprentice.py`, changed ([docs/MULTIVERSE.md](../docs/MULTIVERSE.md)
says how). Component 11 of
012-04-00 imports one of its files (`poetry_engine_c21`), so writing it
out is what lets component 11 load.

## Changes to DeepSeek's code

Each change is listed here, with its reason, and under `"changed"` in
[tools/names-012-04-00.json](tools/names-012-04-00.json), which
`extract.py check` holds the folder to. Every other file in
`deepseek/012-04-00/` is exactly as the record has it, and git history
shows each change exactly.

**Fix 1 (2026-11-13): the demos, attached.** In components 40 and 44 to
63, the record gives the module, then under the heading "Demo" a block
with its `demo` function, then the tests, which import `demo` from the
module. Each demo block is appended to its module unchanged (18 files,
`multiverse_c40.py`, `multiverse_c44.py` to `multiverse_c50.py`,
`multiverse_c52.py`, `multiverse_c54.py` to `multiverse_c60.py`,
`multiverse_c62.py`, `multiverse_c63.py`). The demo blocks themselves
stay as their own files (`multiverse_c40_demo.py`,
`multiverse_c44_demo.py`, and the `@LINE` files), since they are what
the record has. Read before running: the demos write a JSON summary to
the folder they are given (the tests give each a temporary one), and
component 49's starts two Python processes that load and check the
bundle it just saved. None reaches the network.

**Fix 2 (2026-11-13): `turns_from_log`, attached.** The record follows
component 4's module with "The Reconstruction Helper", an 11-line
function the tests of components 4, 7, 12, 18 and 20 import from
`multiverse_c4`. It is appended to `multiverse_c4.py` unchanged, and stays
as its own file, `multiverse_c4.py@2286`, too.

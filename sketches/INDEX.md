# Where the sketches and the course meet

This is the one place that states the overlap between the creative side
(this folder) and the development side (the rest of the repository). The
course ([docs/COURSE.md](../docs/COURSE.md)) and
[docs/COLLABORATING.md](../docs/COLLABORATING.md) link here instead of
repeating it.

## The records

All are verbatim copies. A line starting with `::` is the founder's
message; the rest is the reply: DeepSeek's, or, in the record marked
GMNI, Gemini's.

| Record | What it covers | Lines | SHA-256 |
|---|---|---|---|
| [012-04-00, Patterns and Multiverses](records/012-04-00-DPSK-Patterns_Multiverses.txt) | The multiverse sketch, components 1 to 63, complete. It ends with DeepSeek proposing component 64, a specification for a first live federation | 70,958 | `6a348012fe321fc758f37f8a7625cc124872f4806beef6096ad475081d409387` |
| [012-05-01, Patterns and Multiverses, continued](records/012-05-01-DPSK-Patterns_Multiverses.txt) | The multiverse sketch, components 64 to 87: a live federation and its tools, then the founder's turn to game worlds (a chess park, worlds inside worlds, worlds that grow and govern themselves, a world that keeps running) | 28,539 | `76657e14bb256d88c985bb589dac8b0b20da478318c16ad3e79f97f87fd49da3` |
| [012-03-02, Patterns, Texts and Inventions](records/012-03-02-DPSK-Patterns_Texts_and_Inventions.txt) | The poetry engine and its curriculum, which the multiverse sketch builds on | 23,427 | `978eac920205ec2b487efc33f927dfd62da95b12ad78f1760fef9277b74908de` |
| [012-06-02, Patterns and Multiverses, a new cycle](records/012-06-02-DPSK-Patterns_Multiverses.txt) | After reading `docs/COLLABORATING.md`, proposals for steps ahead: fractal worlds, a hierarchy of worlds, branching, a gallery of worlds and its governance; then the smallest learner that chooses, and individuals as signed, replayable bundles across worlds. Continued (from line 43168, shared on 2026-11-15): a multiversal map and an individual's worldline, a look at games, a microverse, the Ur-world as a garden of hosted fractal worlds, and the move to Rust: an Ur-garden, its keeper, a server, and verifiers in Rust, Python and Node.js. It ends with DeepSeek asking which piece is next | 62,610 | `979f7eef52c10396a682e2fcc0a4e76e1b5d0080b23a71ef22734f265ef0343c` |
| [012-07-03, Patterns and Multiverses, water and the Commons](records/012-07-03-DPSK-Patterns_Multiverses.txt) | Begun from `docs/COLLABORATING.md`: water as particles, the garden and the botanical garden (Python); signed world heads; then the founder's turn to the Commons as chat rooms, each with an AI moderator, and a home room for each person; a schema for every record; a design page; and a crate in Rust, `chat-world`; DeepSeek's order for the cycles after. Then, continued: signed heads for the crate; the one file the founder gave DeepSeek, which reached them whole; and five deliveries of `chat-world` from it, a step at a time. Then, continued again: DeepSeek's second file, which reached them whole, and three more deliveries from it: a room that branches, a plug-in over standard input, and the rule of one moderator's room, where the reply was cut off after three files. It ends with the technical lead's note on those deliveries, given to DeepSeek and not yet answered. On line 12 one record number is replaced with `[number removed]`, at the founder's word | 28,488 | `611ae207ec2592fb5da400bc7c25fc518a172c99aeb821da9f439f9f06a01c7c` |
| [012-08-04, Patterns and Multiverses, with Gemini](records/012-08-04-GMNI-Patterns_Multiverses.txt) | The founder's conversation with Gemini, kept with the rest since 2026-11-17 at the founder's word (STATUS.md, "Decided"). Begun from a link to `docs/COLLABORATING.md`, which Gemini could not open. The founder gives them the project's earlier records one after another, then the founder's own work on opposites, and Gemini reads each. From line 1209 Gemini writes steps for the `chat-world` crate from a file that was out of date (built once and not kept: STATUS.md, "Decided", 2026-11-16, on naming Gemini). From line 9748, given the one file written for them, they write the four deliveries kept in [gemini/2026-11-16](gemini/2026-11-16/README.md). From line 13528, given a second file, they write three deliveries on the Commons' own log, and from line 14973 that file's fourth step, answered twice, all kept in [gemini/2026-11-17](gemini/2026-11-17/README.md). From line 15971 they stop writing code, at the founder's word, and sketch how an AI that moderates a room might decide what to do, drawing on three earlier works of the founder's. From line 16396, given a third file, they write the lobby's list of doors, kept in [gemini/2026-11-17-2](gemini/2026-11-17-2/README.md). From line 17193, given a fourth file, they write 25 attacks on that list, kept in [gemini/2026-11-17-3](gemini/2026-11-17-3/README.md). From line 17955, given a fifth file, they repair the five attacks that got through, kept in [gemini/2026-11-17-4](gemini/2026-11-17-4/README.md). From line 19220, given a sixth file, they write said and speakers, the flag, `ranked_by` and a look into a room, not yet kept here. From line 21437, with the technical lead away, they hold back new code and sketch what could come next | 21,513 | `eb09d65d8e9e0e81ce40bf55a87a885b496ffe05bb387094e8027380913c05e4` |

### Names

The founder named the records of stage 012 anew on 2026-11-20. Three
records changed name; pages, files and
pull requests from before that day use the old ones:

| Before 2026-11-20 | Now |
|---|---|
| `012-09-05-DPSK-Patterns_Multiverses` | `012-07-03-DPSK-Patterns_Multiverses` |
| `012-00-00-GMNI-Multiverse_Development` | `012-08-04-GMNI-Patterns_Multiverses` |
| `012-00-00-CGPT-Patterns_Multiverses` | `012-09-05-CGPT-Patterns_Multiverses` (not kept here: [docs/CHATGPT.md](../docs/CHATGPT.md#your-records)) |

Records 012-00-00 to 012-02-01, before the multiverse work, are the
founder's and are not kept here.

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
The "Course" numbers are the first course's steps ("Done: the first
course" in [docs/COURSE.md](../docs/COURSE.md)), not the course set on
2026-11-13, which numbers its steps afresh.

| # | What it is | Line | Tests as written | Course | In open-worlds |
|---|---|---|---|---|---|
| 1 | The atom of identity | 236 | 9 of 9 pass | 1, 2 | `multiverse/identity.py`, changed (step 1); since step 2 an identity is a key |
| 2 | The passport | 527 | 5 of 11 | 1, 3 | `multiverse/passport.py`, changed (step 1); since step 3 its stamps are signed by worlds |
| 3 | The protocol, WCP/0.1, and its conformance test | 1007 | 13 of 13 | 1, 2 | `multiverse/protocol.py`, `conformance.py`, changed; now WCP/0.4 |
| 4 | The poetry world | 1860 | 18 of 21, with `turns_from_log` attached (fix 2) | 1 | `multiverse/poetry_world.py`, changed (step 1) |
| 5 | The chemistry world | 2933 | 13 of 16 | 1, 4 | `multiverse/chemistry_world.py`, changed (step 1); rebuilt on `chem/` in step 4: real molecules and reactions in a soup that runs in time |
| 6 | The multiverse registry | 3861 | 5 of 15 | 1 | `multiverse/registry.py`, changed (step 1) |
| 7 | The first collaboration | 4654 | 9 of 10, with the poetry engine beside it (fix 5) | 1 | `multiverse/collaboration.py`, changed (step 1) |
| 8 | A conformance test any language can be checked with, and an HTTP shim | 5895 | 5 of 11 | 13 | no |
| 8 | A TypeScript implementation (`ts/`), a registry addition (`multiverse_c6.py@7216`) and a cross-language test (`cross_language_test.sh`) | 6862 | not run | 13 | no |
| 9 | Cross-language SDKs and the cross-language test harness (`cross_language_test.sh@7779`) | 7449 | not run | 13 | no |
| 10 | A Go SDK (`go/`) and the full federation test (`cross_language_test.sh@8762`) | 8056 | not run | 13 | no |
| 11 | Language models as apprentices | 8890 | 20 of 20, with the poetry engine beside it (fix 5) | 12 | no |
| 12 | Cost reports | 9971 | 16 of 16, with the poetry engine beside it (fix 5) | 12 | no |
| 13 | Signatures, WCP/0.2 | 10831 | 12 of 12 | 2 | rebuilt in step 2: an identity is its key, and every request is signed |
| 14 | The conformance test for WCP/0.2 | 11541 | 11 of 26 | 2 | rebuilt in step 2 (`multiverse/conformance.py`) |
| 15 | Signed passports | 12695 | 20 of 22 | 3 | rebuilt in step 3 (`multiverse/passport.py`): a world is a key, and signs stamps for arrivals, departures and things made |
| 16 | Finding a world's key from its manifest | 13648 | 9 of 15 | 3, 13 | partly, in step 3: a manifest names its world's key and is signed by it, and `verify_passport` takes the keys a checker knows; fetching them from a running world is step 13 |
| 17 | Signed registries | 14357 | doesn't load | 3, 13 | no |
| 18 | Several models together | 15152 | 15 of 15, with the poetry engine beside it (fix 5) | 12 | no |
| 19 | The federation runner (`federation.py`, `Makefile`) | 15921 | `federation_test.py`: 0 of 4 | 12, 13 | no |
| 20 | Real Hugging Face models | 16671 | 7 of 11, with the poetry engine beside it (fix 5); 3 skip, needing a language model | 12 | no |
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

In all, with fixes 1 and 2 (below), and the poetry engine of record
012-03-02 written out beside it (fix 5): 944 of DeepSeek's tests pass,
276 fail, and 3 skip (component 20's, which load a language model this
machine doesn't have).
One more passes on some runs and fails on others: component 27's
`test_combined_to_dict_json`, where two signers tie in the order and the
tie falls either way (it depends on random keys, so how many of the
eight runs it fails in changes from one rewrite of the list to the
next). 1 test file doesn't load: 17 imports `InMemoryKeyResolver` from
component 16, but it is defined in 15. Components 7, 11, 12, 18 and 20
import the poetry engine (`poetry_engine_c21`, `poetry_engine_c22`), so
`conftest.py` puts `../012-03-02` on the import path; before it was
written out, they didn't load (877 passed and 274 failed). The
TypeScript and Go code isn't run here yet.

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

## Record 012-05-01, component by component

The record continues 012-04-00 where it ended, at component 64, and its
code imports components 1 to 63 from `deepseek/012-04-00`, and the
poetry engine from `deepseek/012-03-02`. The columns are as above. Tests
are run on Python 3.12 with fixes 3, 4 and 5 (below).

| # | What it is | Line | Tests as written | Course | In open-worlds |
|---|---|---|---|---|---|
| 64 | A specification for the smallest live federation: three worlds, a ledger, an operator, a cost model | 4 | a specification, no code (one JSON example, `trust-anchors.json`) | 13, in part (the network); not yet (an operator and a ledger) | no |
| 65 | A client a person runs: an identity on disk, pinned keys, a report anyone can check | 366 | 23 of 24 | 13 | no |
| 66 | A deploy script: the federation in one call | 2477 | 6 of 21 | 13 | no |
| 67 | A resident driven by a language model | 3767 | 16 of 27, with the poetry engine beside it (fix 5) | 12 | no |
| 68 | A world's representative ("curator") as a background process | 5123 | 19 of 26, with its demo attached (fix 3) | 14, in part (proposing law changes) | no |
| 69 | Representatives negotiating contracts between worlds | 6815 | 9 of 21, with its demo attached (fix 3) | next in line (contracts between worlds) | no |
| 70 | Ending a contract, signed by both | 8321 | 4 of 15, with its demo attached (fix 3) | next in line (contracts between worlds) | no |
| 71 | One command that runs every demo | 9706 | 26 of 33 | not yet | no |
| 72 | Federations recognising each other | 10980 | 15 of 17, with its demo attached (fix 3) | not yet | no |
| 73 | The chess park: play, invite, watch, sit down (the founder's Washington Square) | 12588 | 10 skip: needs `python-chess`; demo attached (fix 3) | not yet (the founder: "not yet") | no |
| 74 | Worlds inside worlds: a world that is a directory of rooms | 13422 | 13 skip: needs `python-chess`; demo attached (fix 3) | 5, in spirit (doors); "one main world" (MULTIVERSE.md, later) | no |
| 75 | Walking and seeing a tree of worlds | 14189 | 16 skip: needs `python-chess` | 13 | no |
| 76 | A world's list of rooms over the network | 15232 | 16 skip: needs `python-chess` | 13 | no |
| 77 | Routes that carry addresses, so a visitor can walk the tree from its root | 15980 | 12 skip: needs `python-chess`; demo attached (fix 3) | 13 | no |
| 78 | A specification for a tree of worlds that changes over time, every change signed | 16947 | a specification, no code | not yet | no |
| 79 | That specification, built | 17307 | 12 of 18 | not yet | no |
| 80 | The demo runner, extended (changes to 71, kept as their own files) | 19123 | not run (`@LINE` files) | not yet | no |
| 80 | A teaching document generated from the code, current by construction | 19502 | 21 of 21 | not yet (the founder: leave the docs as they are for now) | no |
| 81 | A world that grows: participants claim plots next to what exists | 20634 | 21 of 22 | not yet (the founder's "Minecraft for artists"; grid or voxel is open) | no |
| 82 | A representative that watches the world grow and proposes rules | 21990 | 21 of 21 | 14, in part | no |
| 83 | Those inside vote; a passed proposal changes the law | 23090 | 16 of 17, with its import fixed (fix 4) | 14 (ours asks unanimous consent of those present; this one, a vote by plot owners) | no |
| 84 | Running a world over cycles and watching it change | 24529 | 11 of 14, loads with fix 4 | 11 | no |
| 85 | The demo runner, extended again (changes to 71) | 25461 | not run (`@LINE` files) | not yet | no |
| 86 | Participants driven by a model, each with a persona | 25712 | 16 of 17, with the poetry engine beside it (fix 5) | 12 | no |
| 87 | A world that keeps running as its own process, and can be checked on later | 26899 | 5 of 11, with the poetry engine beside it (fix 5); the daemon fails at start (`_participants_path` is never set) | not yet (the founder: where a running world lives, "not yet") | no |

In all, with fixes 3, 4 and 5: 241 of DeepSeek's tests pass and 84
fail. 67 skip, because components 73 to 77 need `python-chess`, which
isn't installed here (it is GPL-3.0-or-later; adding it to
[requirements.txt](requirements.txt) would run them). Every test file
loads. Before fix 5, components 67, 86 and 87 didn't load, for want of
the poetry engine (204 of DeepSeek's tests passed and 66 failed).

Before the fixes, as written: 130 pass, 30 fail, 32 skip, and 12 test
files don't load. Seven failed only because DeepSeek gave the demo as a
block of its own after the module, as in 012-04-00 (fix 3 attaches
them); four more, components 83, 84, 86 and 87, stopped at one wrong
import (fix 4).

All 79 file blocks in the record are written out. Two code blocks stay
in the record: previews of two pieces of component 77 (lines 16005 and
16035), which its module, from line 16065, repeats (the same code,
with shorter docstrings).

The founder's messages in this record turn the sketch towards game
worlds: a chess park where anyone may play, invite or watch (line
12581); worlds inside worlds, like rooms in a mall (13409); worlds that
cluster on their own, the aim being "to create conditions for
possibilities to emerge" (14184); worlds that grow and learn from the
inside and the outside (20548); and a world that keeps running while
development goes on, to be checked on later (26847).

## Record 012-06-02, piece by piece

The record begins a new cycle. The founder gave DeepSeek
`docs/COLLABORATING.md`, and DeepSeek proposed steps ahead in Python,
naming pieces rather than numbering components. A few pieces import
code from `deepseek/012-05-01` and `deepseek/012-04-00`. The columns are
as above, with one difference: "Course" means the course set on
2026-11-13 ([docs/COURSE.md](../docs/COURSE.md)), its steps and its
waiting list, not the first course. Tests are run on Python 3.12, as
written, with fixes 6 to 14 (below, "Changes to DeepSeek's code"),
which a row names where they touch the code it tests. The pieces are
numbered here, for this table only.

| # | What it is | Line | Tests as written | Course | In open-worlds |
|---|---|---|---|---|---|
| 1 | The atomic fractal world: one plant that grows by its rule (a proposal) | 153 | 10 of 11 | the fractal track | its rule, with piece 2's water and light as `fractal_world_v3.py` keeps them, adopted as written (step 4: whole numbers, deterministic, no conflict found): `rust/plant-world` grows by it, checked step by step against that file's `advance` (the fractal track, part 1) |
| 2 | Parameters from inside the world and from outside it (`fractal_world_v2.py`, with additions at 1390) | 707 | 17 of 17, with fixes 6, 7, 8 | the fractal track; a template's dials are step 2's | the water and light dials, in `rust/plant-world` (with piece 1) |
| 3 | Branching instead of changing in place: a new parameter makes a new world, and the original continues | 1820 | 19 of 19, with fixes 6, 7 | the fractal track; the founder's "steering by branching", VISION.md | no |
| 4 | A garden of plants: a composite world of atomic fractal worlds | 3438 | 24 of 24, with fix 7 | the fractal track; the Ur-world's garden, which hosts the plants | no |
| 5 | The Game of Life, and Life-like rules, as an atomic world | 4583 | 22 of 24 | the fractal track | no |
| 6 | Elementary cellular automata (rule 90 and others) as an atomic fractal world | 5700 | 28 of 28 | the fractal track | no |
| 7 | A grid-embedded fractal: an automaton's generations as one 2D pattern | 6962 | 28 of 28 | the fractal track | no |
| 8 | Chaos games: a fractal drawn by choosing among maps, where choice enters | 8251 | 29 of 29, with fix 8 | the fractal track | no |
| 9 | Two chaos games coupled by their recent histories | 9773 | 21 of 23, with fix 8 | the fractal track ("watch them grow or interact") | no |
| 10 | Two cellular automata growing in one space, meeting by a coupling parameter | 11123 | 12 of 12 | the fractal track | no |
| 11 | A gallery: one composite world holding worlds of four kinds | 11851 | 15 of 15, with fix 7 | 4a, in part (a garden of rooms); the Commons, as a superworld | no |
| 12 | The gallery's interior and exterior: world-keys, signed requests to change it, signed refusals | 12979 | 26 of 27, with fixes 7, 9 | 4 (grants) and 12 | partly: worlds are keys, and sign their stamps (the first course's step 3) and their log's heads (step 3); a world refusing a change, no |
| 13 | Revoking a key, and rotating the keeper (with a change at 16659) | 14833 | 14 of 14, with fixes 9, 10 | 8a (a lost or leaked key) | no |
| 14 | The gallery watches and schedules: an attention budget across its members | 15892 | doesn't load: imports `multiverse_utils_sig`, which no record defines | not yet | no |
| 15 | Attention per member, by deficit round-robin | 16700 | 9 of 17, with fix 10 | not yet | no |
| 16 | Bursts: attention raised for a bounded time, by a signed record | 17581 | 15 of 20, with fix 10 | not yet | no |
| 17 | The smallest learner that chooses: a 4-unit recurrent network, or a lookup table, in a chaos game | 18698 | 9 of 10 | the fractal track, and 3a's architectures (the founder, 2026-11-14) | no |
| 18 | Two learners in one chaos game | 19408 | 8 of 11 | the same | no |
| 19 | A learner beside a scripted world | 20187 | 16 of 18, with fixes 11, 12 | the same | no |
| 20 | The individual as a bundle: four signed files that describe it whole, replayable (with additions at 23274, 27017, 27054, 32475 and 34393) | 21268 | 16 of 20, with fixes 11 to 13 | 7 (memory), in part | no |
| 21 | An individual that makes an individual | 22301 | 10 of 15, with fixes 11 to 13 | not yet | no |
| 22 | The child starts from the parent's weights | 23332 | 8 of 14, with fixes 11 to 13 | not yet | no |
| 23 | One individual across worlds: one key, its model and memory carried (with additions at 27067 and 34853) | 24250 | 14 of 15, with fixes 11 to 14 | 3a, which differs: a presence in each world, each a key of its own | no |
| 24 | An individual who lived in several worlds makes a child (with an addition at 27094) | 25192 | 9 of 13, with fixes 11 to 14 | not yet | no |
| 25 | Generations: grandparent, parent, child | 26203 | 4 of 12, with fixes 11 to 14 | not yet | no |
| 26 | Proof of descent from a root, from one bundle alone | 27124 | 7 of 17, with fixes 11 to 14 | not yet | no |
| 27 | A lineage tree, checked whole | 27939 | 9 of 14, with fixes 11 to 14 | not yet | no |
| 28 | Shorter proofs of ancestry | 28994 | 13 of 17, with fixes 11 to 14 | not yet | no |
| 29 | Shorter proofs of what was inherited | 30152 | 5 of 13, with fixes 11 to 14 | not yet | no |
| 30 | Two lineage trees recognising each other | 31239 | 15 of 24, with fixes 11 to 14 | not yet | no |
| 31 | Continuing a life from its bundle (with additions at 34429 and 34871) | 32484 | 11 of 17, with fixes 11 to 14 | 7, in part | no |
| 32 | Memory checkpoints: a signed summary in place of the entries before it | 33637 | 10 of 18, with fixes 11 to 14 | 7, in part | no |
| 33 | Continuing a life on someone's behalf, by a key they authorise | 34895 | 10 of 21, with fixes 11 to 14 | not yet; compare step 3's doorway, which signs for the minds it runs (research/KEYS.md, "Honest limits") | no |
| 34 | Forking an individual into a new lineage | 36279 | 15 of 20, with fixes 11 to 14 | not yet | no |
| 35 | A whole lifetime, checked across bundles (with additions at 40276 and 41514) | 37602 | doesn't load: imports `_entry_hash` from `lifetime.py`, which defines it only inside its demo | 9 (legends pages), in part | no |
| 36 | An individual that plays chess in 012-05-01's chess world (with additions at 40076, 40158 and 40178) | 38708 | doesn't load: needs `python-chess` | not yet (the founder, on the chess park: "not yet") | no |
| 37 | A world's log, each entry signed by the world's key | 39909 | doesn't load: needs `python-chess` | 3 | built independently: the Ur-world signs its log's heads (`open-worlds/log-head/v1`) |
| 38 | One individual across worlds of different kinds, with one key and one memory (with additions at 42553, 42625 and 42684) | 40662 | doesn't load: needs `python-chess` | 3a, which differs, as for 23 | no |
| 39 | Adapters, so an individual can enter any kind of world | 41968 | doesn't load: needs `python-chess` | 12 (the world protocol) | no |

In all, with fixes 6 to 14: 478 of DeepSeek's tests pass and 119 fail,
and six test files don't load (74 tests: four need `python-chess`, which
isn't installed here, as for 012-05-01; two import names that can't be
imported). Each test's keys are made from its own name (`conftest.py`,
ours), so every run gives the same results. With fresh random keys, as
the tests make them, 19 of the individual pieces' tests (in
`test_forking.py`, `test_federated_bundle.py`, `test_federated_spawn.py`,
`test_resumable.py` and `test_delegated_resumption.py`) passed in some
of 28 runs and failed in others: the replays they check depend on the
keys, a fault left for the next round (`SKETCH_RANDOM_KEYS=1` runs them
that way). As written, 296 passed and 301 failed, 236 of them for one
missing method, `to_dict` on `coupled_learners.py`'s `Transform` (fix
11).

All 99 code blocks of the record's first part (to line 43168) are
written out, each as a file; 21 of them are later additions or demos,
kept as `name@LINE`.

The founder's messages in this record, with their line numbers, are in
[STATUS.md](../STATUS.md) ("Decided", 2026-11-14), with where they meet
earlier decisions, as the founder's rule on changes of mind asks.
In short: a hierarchy of worlds from the smallest, a potted plant (84);
parameters from inside and outside (663), then a change of parameters as
a branch, which a world may refuse (1801); worlds of the Game of Life's
kind (4568, 5682) and of chaos, where choice enters (8231); two worlds
interacting (9759); continuing in Python after looking at the Rust code
(11099); and the smallest model that chooses and learns, taken as the
atomic model (18688, 19389).

### The record continued (2026-11-15)

The founder went back to DeepSeek, and the record was shared again,
longer: its first 43,170 lines are the same, byte for byte, and 19,440
more follow. The pieces go on from 40. "Tests as written": the new
Python test files, all as written; the Rust and the JavaScript are kept
as written, and nothing builds or runs them here (open-worlds' own Rust
is in `rust/`). DeepSeek says so too: they "can't run cargo build in this
conversation", and their Rust "may not compile as-is".

| # | What it is | Line | Tests as written | Course | In open-worlds |
|---|---|---|---|---|---|
| 40 | Resuming an individual who lived in several kinds of world (additions to `unified_individual.py` and `lifetime.py`) | 43182 | `test_unified_resume.py` doesn't load: needs `python-chess` | 7 (memory), in part | no |
| 41 | A multiversal map: a map that pins worlds and other maps, and routes a visitor across federations (`map_world.py`) | 44241 | `test_map_world.py` doesn't load: `map_world.py` is written as additions to a module that isn't there, and uses `dataclass` without importing it; and the tests import `lobby_server`, which no record defines | the fractal track's web app, topic 16 (the map) | no |
| 42 | An individual's worldline: their path through worlds, read from the maps (`worldline.py`) | 44332 | in `test_map_world.py` | topic 16; 9 (legends pages), in part | no |
| 43 | Maps within maps, resolved recursively | 45552 | `test_map_recursive.py` doesn't load, as 41 | topic 16 ("maps nest") | no |
| 44 | A map that explains its route | 46407 | `test_map_explain.py` doesn't load, as 41 | topic 16 | no |
| 45 | A map that governs itself: world-keys, signed pins, a registry rebuilt from its log (`map_governance.py`) | 47266 | `test_map_governance.py` doesn't load, as 41 | topic 16; 4 (grants) | no |
| 46 | A look at games, at the founder's request: characters that grow, a keeper as a director above the game, escape rooms and Myst as puzzle graphs, worlds as places to learn | 48569 | prose, no code; its sources are DeepSeek's searches, not checked here | 5 (the sheet), 11 (the hunt, the AI Keeper) | no |
| 47 | A microverse: a small social world that hosts fractal worlds and gives them time (`microverse.py`, `microverse_adapter.py`) | 48695 | `test_microverse.py` doesn't load: it reaches `signed_world_log.py`, which imports `_canonical` from `multiverse_c13` (record 012-04-00), which doesn't define it | the fractal track, part 3 | its idea, not its code: the host gives each hosted world time, and both logs record each step, the host's naming the hash of the hosted world's entry, as its `advance_cycle` names the hosted worlds' new event hashes, in `rust/ur-world/src/host.rs` (the fractal track, part 3) |
| 48 | The Ur-garden in Python: the Ur-world as a microverse garden, ALICE and BOB walking among plants (`ur_garden.py`, `garden_adapter.py`, rewritten at 51459 and 51871) | 50117 | `test_ur_garden.py` doesn't load: imports `_PHRASES` from `garden_adapter.py`, which doesn't define it | the fractal track, part 3; 9 (ALICE and BOB) | no; the Ur-world's garden (`rust/ur-world`) is ours |
| 49 | The Ur-garden in Rust: the garden as the Ur-world's world, residents as minds (`rust/ur-world/src/garden.rs`, `garden/mind.rs`) | 52842 | not built; against today's `rust/` crates, `garden.rs` alone has 19 compile errors: it assumes key and proof types our `formats` crate doesn't have, and crates our workspace doesn't use | the fractal track, part 3 (an input) | no |
| 50 | Shared test vectors for the garden (`vectors/garden_reference.json` and its generator) | 53807 | not run | 2 (shared vectors) | the practice is ours (`vectors/`), these vectors aren't |
| 51 | The garden's keeper: observes, proposes, never applies its own proposals; a typed proposal record (`garden_curator.rs`) | 54430 | not built | 11 (the Keeper), and ADMIN's "suggest, never make" | no |
| 52 | The smallest learner in Rust, as a resident (`garden/rnn.rs`, `garden/rnn_mind.rs`) | 55689 | not built | the fractal track, part 5 | no |
| 53 | The garden as a server and a client, and reading its log a piece at a time (`garden_server.rs`, `garden_client.rs`) | 56592 | not built | 12 (the world protocol in Rust); the web app | no |
| 54 | A keeper's whisper: a keeper's message, signed, in the public log (`keeper_whisper.rs`) | 58040 | not built | 11 (the line to a Keeper, which is public) | no |
| 55 | The keeper's loop: the garden runs itself, its keeper proposing as it goes (`examples/garden_curator_loop.rs`, a name of ours: DeepSeek headed it only "Demo", at line 59466, and its first line calls it a "Curator loop demo") | 59170 | not built | 11 | no |
| 56 | Checking a garden from outside, in Rust and Python (`examples/verify_garden.rs`, `verify_garden.py`) | 59641 | `rust/ur-world/examples/test_verify_garden.py` doesn't load: imports `check_proof_metadata`, which `verify_garden.py` doesn't define | 2; the web app (the page checks a log) | partly: a log's chain and its arrivals are checked by `world-log` and `rust/ur-world` |
| 57 | Proof cases every language must agree on (`vectors/proof_cases.json`, and runners in Rust and Python) | 61460 | not run | 2 (shared vectors) | the practice is ours, these cases aren't |
| 58 | A Node.js verifier (`examples/verify_garden.mjs`, `verify_proof_offline.mjs`, `package.json`), the founder's choice ("I would go with the Node.js verifier first") | 61995 | not run: its packages aren't installed here, and wouldn't be without a review and exact pins | the fractal track, part 2 (the web app checks logs in the page) | no |

Their fit with the established design, a first look (the third of the
four steps in [docs/COLLABORATING.md](../docs/COLLABORATING.md), "Two
sides"); nothing here is adopted yet:

- **One key across worlds.** The unified individual and their worldline
  (40, 42) carry one key from world to world; the persons plan gives a
  person a presence with a key of its own in each world, unlinked by
  default ([../docs/research/PERSONS.md](../docs/research/PERSONS.md)).
  The worldline's idea fits; built from a person's presences, it would
  be adapted.
- **A second "world-key".** The map's governance (45) calls an access
  credential a world-key; here the world-key is the signed right to found
  a world, earned on the hunt ([../docs/WORLD-KEY.md](../docs/WORLD-KEY.md)).
  One of them is renamed before any of it comes in.
- **Records outside records-v1.** The Rust pieces define their own proof
  types and new records (the keeper's proposal, the whisper: 51, 54).
  A record here goes through records-v1: its schema, shared vectors, and
  Python and Rust ([../docs/research/FORMATS.md](../docs/research/FORMATS.md)).
- **ALICE and BOB as small networks.** In the Ur-garden they become the
  four-unit network (48 and 52; in 49 their minds are still scripted);
  here their minds are language models chosen by course step 8's
  audition. The network fits as a primitive learning model in a fractal
  world (the technical lead's reading, FRACTALS.md).
- **Floats in the learner.** The network computes in `f64`, with `tanh`
  and `exp` (52), whose last bits can differ between machines and maths
  libraries; and DeepSeek notes that their Rust and Python runs already
  choose differently, their random numbers being different. A world
  gives the same log on any machine
  ([../docs/FRACTALS.md](../docs/FRACTALS.md), "What stays fixed"), so a
  learner inside one is adapted to whole numbers, or kept out of the log.
- **A server in the Ur-world** (53): a world speaking over the network
  belongs with course step 12's world protocol in Rust, and putting
  anything online is the founder's decision.
- **What fits as it is:** a keeper that proposes and never applies their
  own proposals (51, 55), as ADMIN can suggest changes and never make
  them ([../docs/ADMIN.md](../docs/ADMIN.md), "Suggestions from inside");
  a keeper's whisper written to the public log (54), as the open line to
  a Keeper is logged ([../docs/MINDS.md](../docs/MINDS.md)); cases every
  language must agree on (50, 57); and a verifier for the web app's page
  (56, 58).

126 code blocks of the continuation are written out as files: 64 in
Rust, 47 in Python, and JSON, JavaScript, TOML and Makefiles. 17 Python
blocks are left in the record, where DeepSeek drafts and redrafts a
piece within one answer (lines 50890 to 51406), and so is a shell block
of commands (62525).

The founder's messages in the continuation are in
[STATUS.md](../STATUS.md) ("Decided", 2026-11-15), as the founder's rule
on changes of mind asks. In short: the map across federations first, then
an individual's worldline (44227); maps within maps (45540); a look at
games, keepers, escape rooms and learning (48569); the microverse as a
world type (48626), hosting fractal worlds (48677); "This is exactly how
I envisioned the Ur-world, ALICE and BOB is a microverse garden of
hosted fractal worlds" (50034); "primarily to Rust" (52822); and the
Node.js verifier first (61985).

## Record 012-07-03, piece by piece

The record's code is kept in
[deepseek/012-07-03](deepseek/012-07-03/README.md), with the technical
lead's first pass and a first round of repairs (fixes 15 to 18, under
"Changes to DeepSeek's code", below). "Tests" for the Python is
DeepSeek's own tests under pytest, which CI runs; for the Rust it is
the crate's own tests, run on a scratch copy by `review/run.sh` (not
by CI). Where a fix changed a count, the count as written is given
too. Nothing from this record is in open-worlds yet. Fitting it is the
next work, piece by piece.

| # | What it is | Line | Tests | Course | In open-worlds |
|---|---|---|---|---|---|
| 1 | Water as particles: whole-number levels, and rain, fall, soak, flow and evaporation in a fixed order (`water_particles.py`) | 50 | 17 of 18 | the fractal track, stage 3 (FRACTALS.md; TOPICS.md, topic 18) | not yet: it waits on `rust/endless-plant`, which isn't built |
| 2 | The garden as a composite world: shared water, slots, and plants of record 012-06-02 in them (`fractal_garden.py`) | 795 | 20 of 21 | the fractal track, the garden | the Ur-world's garden hosts plant worlds already (`rust/ur-world`); what this adds isn't compared yet |
| 3 | The botanical garden as a superworld of gardens (`botanical_garden.py`), with a change to the garden's tick given as a note (line 3425) | 2391 | 15 of 18 (as written 2 of 18: the rest needed that change, fix 15) | the fractal track, after the garden | not yet |
| 4 | Signed world heads: a small signed record a world publishes each tick, so a parent can check it without its whole log (prose, left in the record) | 3782 | none | formats (course step 2) | not yet |
| 5 | Chat worlds for the Commons: a room as a log of signed records under the room's law (`chat_room.py`); then an AI moderator, rooms of humans and AIs, succession, and personal rooms (`chat_room.py@5569` to `@7192`; five smaller notes are left in the record, at lines 5494, 5520, 5531, 6501 and 6557) | 3887 | 21 of 24 | the Commons ([docs/COMMONS.md](../docs/COMMONS.md)), on the course's waiting list | not yet |
| 6 | The home room: a person's own room, with a journal, drafts, bookmarks and conversations brought in (`personal_world.py`) | 7258 | 0 of 17: they need the additions of piece 5 | the Commons; the private container ([docs/CONTAINER.md](../docs/CONTAINER.md)) | not yet |
| 7 | A schema for every record, given twice (`schemas/records-v1.schema.json`, then whole as `@8640`), under the name of open-worlds' own schema, with none of its definitions | 8095 | none | formats (course step 2) | not yet: its records are to be fitted into the schema open-worlds has, not to replace it |
| 8 | A design page, `docs/CHAT.md` (prose, left in the record) | 9964 | none | the Commons | not yet |
| 9 | A crate in Rust, `chat-world`: the first version (`chat-world-draft/`), the one DeepSeek settled on (`chat-world/`), and the files of their next reply (a home, the Commons, transcripts) | 10259, 12246, 13800 | 18 of 18, and both demos' logs verify (as written it doesn't build, for one line, fix 16; with it changed, 4 of 12, the rest failing for one cause: a record was signed without its `type` and checked with it, fix 18; the later reply's files are joined by fix 17) | the Commons | not yet: it uses none of open-worlds' own crates |

### The record continued (2026-11-16)

The founder went back to DeepSeek with one file, and the record was
shared again, longer. Its first 595,416 bytes are the same, byte for
byte: the record as it was kept ended at the founder's next prompt,
the opening of line 14,782, and 9,212 lines more follow. Three things
are in them.

**Signed heads for `chat-world`** (line 14785), the cycle DeepSeek had
proposed. It came as changes to parts of files, with `src/head.rs`,
`src/lib.rs` and a demo whole (kept in `chat-world-steps/0/`). It was
not built on its own: the crate DeepSeek was then given does not hold
it, and delivery 3, below, gives those files whole again.

**The one file reached DeepSeek whole** (line 15501). The file is
[replies/012-07-03-for-deepseek.txt](replies/012-07-03-for-deepseek.txt):
the technical lead's reply, the next steps, and the crate as it stands
here. DeepSeek quotes back its last line, `END OF FILE`, says "The
whole file reached me.", and takes the reply's two requests: "One step
per reply; every file I change, whole."

**Five deliveries of `chat-world`,** each a step of that reply. Every
file DeepSeek changed came whole, so each delivery can be built as
given, with no joining by hand. The files are kept as the record gives
them in `deepseek/012-07-03/chat-world-steps/1` to `5`;
[deepseek/012-07-03/review/steps.py](deepseek/012-07-03/review/steps.py)
lays each delivery over the one before, starting from the crate
DeepSeek was given, and `review/steps.sh` builds and tests each (not
run by CI). "Tests" is
the crate's own tests, `cargo test --test integration`, on 2026-11-16.
The titles are DeepSeek's.

| Delivery | What it is | Line | Files given whole | Tests, built as given |
|---|---|---|---|---|
| 1 | "the data layer and the presentation layer": a redaction names who acted, in what role and under which rule, and a room's template holds its rules for redacting | 15540 | 6 | 22 of 22 |
| 2 | "the room's own key": the room and the one who made it are two keys | 17168 | 6 | 20 of 22 |
| 3 | "signed heads, first in prose, then code": what is lost if a room signs its log's head in place of each record, then heads in code | 18832 | 8 | 27 of 29 |
| 4 | "runtime attestation": keys that share a runtime say so together, in a published record | 20714 | 3 | 31 of 33 |
| 5 | "the succession trio": a shard of knowledge exported, a moderator's succession, and a sibling declared in the Commons | 21474 | 8 | does not compile; with its two faults set aside, 39 of 41 |
| all five, with three repairs | The crate as it stands, `deepseek/012-07-03/chat-world-now/` (fixes 19 to 21, under "Changes to DeepSeek's code") | | | 41 of 41, and the four demos run |

Three faults, as the deliveries were written:
1. From delivery 2 on, the same two tests fail, `home_port_verifies`
   and `home_bookmark_and_presence_verify`, each with "record 1:
   missing room proof". They passed in delivery 1. The cause:
   delivery 2 makes the room and its maker two keys, and the check
   asks every record but a leaving for a proof by the room's key; a
   home's port landing, bookmark and presence records were still
   signed by the person's key alone (`src/home.rs`), which was the
   room's key until then. Fix 19 signs them with both, and both tests
   pass.
2. Delivery 5, `src/verify.rs`: one condition does not compile
   (mismatched types).
3. Delivery 5, `src/bin/succession-demo.rs`: it calls `.hash()` on
   `commons::SiblingDeclared`, which has no such method.

DeepSeek ends delivery 5 with "Expected: 41 tests pass" (line 23989).
They can't build or run the crate where they write, as they have said
before, so the count is what they meant, not what they measured. With the
two faults of delivery 5 set aside (the condition replaced by `false`,
the demo left out), 39 of the 41 pass, and the two that fail are the
two of fault 1.

The crate kept in `deepseek/012-07-03/chat-world/` is still the one
DeepSeek was given, and the deliveries are beside it, as written.
`chat-world-now/` is the crate as it stands. When this was written
that was the five deliveries laid over that crate in order, with the
three repairs; since 2026-11-17 Gemini's three deliveries and two
more repairs are laid over those (the next section). `review/steps.py`
puts it together, and its `--check` holds the folder to exactly that,
byte for byte (the folder's own test runs it, in CI). So every file in
it is DeepSeek's latest or Gemini's, changed only as fixes 19 to 23
say. Not
checked: the demos of deliveries 2 to 5 as written were not run, only
the four demos of the crate as it stands; the prose of delivery 3 was
read only in part; nothing of this has been compared with open-worlds'
own formats.

### After DeepSeek's five: Gemini's three (2026-11-17)

The crate then went to Gemini, with a file written for them
([replies/2026-11-16-for-gemini.txt](replies/2026-11-16-for-gemini.txt))
that asked them to try to break the crate. Their deliveries are kept as
written in [gemini/2026-11-16](gemini/2026-11-16/README.md), which
says where they come from and what each is. Laid over the crate in
order, every test file run, on 2026-11-17:

| Delivery | What it is | Tests, built as given |
|---|---|---|
| Gemini 1 | A room's log that can be checked from outside (`RoomLog`, `verify_log`) | 42 of 44 |
| Gemini 2 | 22 attacks on the check | 61 of 66: three attacks get through, the three Gemini said would |
| Gemini 3 | Repairs | 64 of 66: all 22 attacks refused |
| all eight, with fixes 19 to 23 | The crate as it stood then | 66 of 66, and the four demos run |
| Gemini 4 | Branches for rooms, not asked for; two files of the four they describe | does not compile; not used |

The two tests that fail in Gemini's three are two of DeepSeek's
earlier 41, and the fault is theirs: fix 22, under "Changes to
DeepSeek's code".

### Gemini on the Commons (2026-11-17)

Gemini was free before DeepSeek, so for one round the two had the
crate at once, each with files of their own (STATUS.md, "Decided by the
technical lead", 2026-11-17). Gemini's file
([replies/2026-11-17-for-gemini.txt](replies/2026-11-17-for-gemini.txt))
asked four steps on the Commons, the crate's list of rooms, in
`src/commons.rs` and new test files. Three came back, and the fourth
later the same day, all kept as written in
[gemini/2026-11-17](gemini/2026-11-17/README.md). Laid over the crate
in order, every test file run, on 2026-11-17:

| Delivery | What it is | Gemini expected | Tests, built as given |
|---|---|---|---|
| Commons 1 | The Commons' log read from outside (`CommonsLog`, `verify_commons_log`); a Commons record can be written to JSON and read back | 69 | 69 of 69 |
| Commons 2 | 16 attacks on the check | 82 of 85 | 82 of 85: three attacks get through, the three Gemini said would |
| Commons 3 | Repairs, and two checks that hold a record of the Commons to a room's own log | 92 | 92 of 92, and the four demos run |
| Commons 4 | 17 attacks on a room's seven other kinds of record, in a second answer; the first answer's 10 attacked only what the check already refuses, as Gemini then said themselves | 101 of 109 | 101 of 109: eight attacks get through, the eight Gemini said would |

Every number is the one Gemini gave, and nothing was repaired here.
The third was the crate as it stood then,
`deepseek/012-07-03/chat-world-now/`: 92 tests, 41 of them DeepSeek's
and 51 Gemini's. The fourth is built beside it and not laid into it:
its eight gaps in the check of a room's log are not repaired in this
crate. They are kept as the list of what the room's own check must
refuse (STATUS.md, "Decided by the technical lead", 2026-11-17).

Gemini's next file
([replies/2026-11-17-2-for-gemini.txt](replies/2026-11-17-2-for-gemini.txt))
asks one step: the lobby's list of doors, which is what a map of the
Commons is first drawn from, in a new file `src/doors.rs` with fifteen
tests. A door shows how many are in the room, unless the room's law
hides that, and the most populated can be listed first. The file was
built again on the crate with DeepSeek's next deliveries in it, below.
Gemini's answer to it is after that ("Gemini's list of doors").

### DeepSeek's second file: branches, a plug-in, and a rule cut off (2026-11-17)

The founder gave DeepSeek their second file
([replies/012-07-03-2-for-deepseek.txt](replies/012-07-03-2-for-deepseek.txt)),
and the record was shared again, longer. Its first 947,153 bytes are
the same, byte for byte, and 4,463 lines more follow, from line 23994.
DeepSeek quotes back the file's last line. They answer the file's
question on signed heads first: they agree with Gemini's rule that a
published log ends with a head covering all of it. Then they give
three deliveries. The file asked for the first. The second and third
are DeepSeek's own next items, at the founder's word to keep going
(lines 25900 and 27240). The files are kept as the record gives them,
in `deepseek/012-07-03/chat-world-steps/6` to `8`.

Laid over the crate in order, every test file run, on 2026-11-17
(`deepseek/012-07-03/review/steps.sh`):

| Delivery | What it is | Files | DeepSeek expected | Tests, built as given |
|---|---|---|---|---|
| 6 | A room that branches. A branch is a new room whose first record names its parent and the record it branches at (`forked_from`); `Room::branch_at`; and `verify_branch`, which holds a branch to its parent's log: the parent holds that record with that hash, and the branch's maker was a member of the parent there. Eleven tests | 4 | "78 tests pass", counting 66 before it and 12 of its own | Does not compile, for one word. With that repaired (fix 24), 103 of 103: the crate's 92 and its eleven. Its test file holds eleven tests, not twelve |
| 7 | A plug-in: nine requests an app can make of the crate, as JSON, one to a line, over standard input (`src/plugin.rs`, `src/bin/chat-world-plugin.rs`), with nine tests; and a room's visible log made available on any log | 5 | "87 tests pass" | 112 of 112. The four earlier demos run, and the plug-in's own demonstration runs |
| 8 | The rule of one moderator's room: a moderator declares, in their own room, which rooms they moderate (`ModeratorScope`). The reply was cut off after three files | 3 | not reached | Does not build: the check has no arm yet for the new record. Kept as given, and not laid into the crate |

DeepSeek counted from 66 tests because their file said so. By then the
crate had 92, with Gemini's work on the Commons, which the file could
not say. Their own counts are otherwise right but for the twelfth test.

The crate as it stands is now delivery 7, with one field added to a
room's law since (change 25):
`deepseek/012-07-03/chat-world-now/`, 112 tests, 61 of them
DeepSeek's and 51 Gemini's, in 29 files. Gemini's seventeen attacks
on a room's other records, run beside it again, give the same eight
that get through (121 of 129).

What DeepSeek chose where the file left it open, in their own words
before the code (from line 24001):

- **Where a room may branch.** The file asked for a branch at a
  room's last record. `branch_at` takes any record of the parent. In
  a room that signs heads and not each record, the record must be one
  the parent's last head covers: "the tail after the last head is
  uncommitted".
- **Merging two branches:** "I would not merge." Two branches that
  need to meet do so by their members posting in both, or by a third
  room.
- **The parent noting its branches:** later, as a record in the
  parent's own log.
- **The Commons listing a branch:** "A branch is a room like any
  other."

Two limits of the plug-in that DeepSeek names themselves (line 27231). It
can post only in rooms whose own key it holds, which are the rooms
its user made: posting in someone else's room needs what they call a
"remote room" type, which "the crate does not have yet". And it makes
new keys each time it
starts, so its user is someone new each time: "wrong for production,
correct for a demo".

One thing DeepSeek says in the third delivery that is not so (line
27247): that the `src/home.rs` they were given fails two tests for want
of an earlier repair. That file was not in the file they were given,
which names it as carrying the repair. The `src/home.rs` DeepSeek
then sends is the crate's own, with the repair, but for line breaks
and the one new function. Nothing is lost by it.

Read by the technical lead: all of DeepSeek's prose in the new part;
`verify_branch` whole; and each of the eighth delivery's three files
against the file before it. The rest of the code was built and run,
not read line by line.

### Gemini's list of doors (2026-11-17)

Gemini answered their third file the same day
([gemini/2026-11-17-2](gemini/2026-11-17-2/README.md)): two files,
`src/doors.rs` and `tests/doors.rs`. Laid over the crate with the one
line that names the module (change 26), every test file run:

| Delivery | What it is | Gemini expected | Tests, built as given |
|---|---|---|---|
| The list of doors | `draw`, `check`, `ranked` and `as_text`, with fifteen tests. A door shows a room, its law, and how many are in it unless the room's law hides that | 127 | 127 of 127 |

Nothing was repaired. It was the crate as it stood until 2026-11-18:
127 tests, 61 of them DeepSeek's and 66 Gemini's, in 31 files.
Gemini's seventeen attacks on a room's other records, run beside it,
give the same eight that get through (136 of 144).

The technical lead had written the same step out, outside the
repository. Each build passes the other's fifteen tests.

One thing seen on reading it, which the next file puts to Gemini as
an attack: a count is a count of keys, and keys cost nothing to make.
Whoever keeps a room, or anyone who can join an open one, can fill
it with keys of their own making and put it first among the most
populated.

Gemini's next file
([replies/2026-11-17-3-for-gemini.txt](replies/2026-11-17-3-for-gemini.txt))
asks one step: twenty-two attacks on the list, tests only.

### Gemini's attacks on the list of doors (2026-11-17)

Gemini answered their fourth file the same day
([gemini/2026-11-17-3](gemini/2026-11-17-3/README.md)): one file,
`tests/doors_attack.rs`, 25 tests, the twenty-two the file asked for
and three of their own. Built beside the crate as it stands, every test
file run:

| Delivery | What it is | Gemini expected | Tests, built as given |
|---|---|---|---|
| Attacks on the list of doors | A list forged against `check`, the logs forged against `draw`, a list read from JSON, the text, and what a count means | 147 of 152, five named to fail | 147 of 152, the same five |

The five that get through:

| Attack | What the crate accepts | What is done |
|---|---|---|
| 17 | A room's log cut short just before a leaving: the older, larger count is drawn | A log is held to a head the room signed, when the reader holds one |
| 19 | A door read from JSON with a member the form does not have, such as a list of ids | The forms refuse what they do not have |
| 22 | Thirty keys of one holder put a room above one of five people | Not closed in the crate: a count is a count of keys. Kept as a test that states the limit. The answer is other numbers and a look into the room (STATUS.md, "Decided", 2026-11-17) |
| 24 | A leaving by a key that was never in the room, signed by that key alone | It belongs to the check of a room's own log: a ninth gap, beside the eight of Gemini's fourth step. Until then the drawing of the list refuses such a log |
| 25 | A room registered under a topic that is not its own: only the registrant's is shown | The room's own topic is shown beside the listed one, when the reader holds the room's log |

Because five of its tests failed, the file was not laid into the
crate, which stayed at 127 tests. `review/steps.sh` builds it beside
the crate as it then stood (`doors-attacks`).

"What is done" is what Gemini's next file asks of them
([replies/2026-11-17-4-for-gemini.txt](replies/2026-11-17-4-for-gemini.txt)):
five repairs, in their own two files. Before that file was written the
repairs were made in a throwaway copy outside the repository, with
attacks 17, 22 and 25 rewritten as the file asks and four trial tests
added: 156 of 156. The copy is not kept.

### Gemini's five repairs (2026-11-18)

Gemini answered their fifth file
([gemini/2026-11-17-4](gemini/2026-11-17-4/README.md)): two files,
`src/doors.rs` again and `tests/doors_attack.rs` with five of its 25
tests written again. Laid over the crate, every test file run:

| Delivery | What it is | Gemini expected | Tests, built as given |
|---|---|---|---|
| The five repairs | The forms refuse a member they do not have; a leaving only by a key that is inside; the room's own topic beside the listed one; `draw_at` and `check_at`, which hold a room's log to a head the reader holds; the count of keys kept as a stated limit | 152 of 152 | 152 of 152 |

Nothing was repaired here. It is the crate as it stands now:
`deepseek/012-07-03/chat-world-now/`, 152 tests, 61 of them
DeepSeek's and 91 Gemini's, in 32 files.

Compared with the attack file they sent before, test by test: in the
twenty attacks that were to stay, no code changed but the one field
the file asked for; 25 comment lines were taken out. Each repair was
then broken on purpose in a throwaway copy, fifteen ways, one at a
time, and Gemini's tests caught all fifteen. Seven trial tests of the
technical lead's own passed. The copy is not kept.

Two limits stay, each held by a test: with no head, a log cut short
still draws the older count; and a count is a count of keys. The
leaving by a key that is not inside is refused where the list is
drawn; `src/verify.rs` still accepts it, and that stays the ninth
gap for the project's own check of a room.

Gemini's next file
([replies/2026-11-18-for-gemini.txt](replies/2026-11-18-for-gemini.txt))
asks one step, the founder's answer to the count of keys: beside the
count, how much is said and by how many; a rule that marks a room
with many in it and nothing said; the doors listed by another
number; and a look into a room before entering. Before the file was
written the step was made in a throwaway copy, with seven trial
tests of what the file states: with it made, every test of the crate
passes but one, which holds the whole text of a list and must gain
the new line. The copy is not kept.

## Record 012-03-02, component by component

Three series of components, written out in `deepseek/012-03-02/`: a
model of Aristotle's practical reasoning as a control system, one
component of a music engine, and the poetry engine (components 1 to 22,
with its curriculum in the prose). Step 1 brought parts of the poetry
engine's components 21 and 22 (the turn, the critical stances, the
apprentice poet) into open-worlds as `multiverse/apprentice.py`, changed
([docs/MULTIVERSE.md](../docs/MULTIVERSE.md) says how). Records 012-04-00
and 012-05-01 import components 21 and 22 from this folder. "Line" is
where the component's code begins. Tests are run on Python 3.12 with fix
5 (below).

| Component | What it is | Line | Tests as written |
|---|---|---|---|
| `aristotle_cybernetics_c2` to `c7` | The virtuous agent as a control system: the telos hierarchy, a telos that learns, mutual and asymmetric correction | 996 to 3181 | no tests |
| `music_engine_c8` | The Listener | 3698 | doesn't load: needs `music_engine_c1`, which no record here has |
| `poetry_engine_c1` | Phonemes, syllables, stress | 4523 | doesn't load: `poetry_engine_c1.py` has a syntax error (line 45) |
| `poetry_engine_c2` | The cognitive frame | 5393 | doesn't load: imports `poetry_engine_c1`, which has a syntax error |
| `poetry_engine_c3` | Meter and scansion, through both grammars | 6195 | 13 of 15 (one of the two imports `poetry_engine_c1`) |
| `poetry_engine_c4` | The score-performance gap | 7287 | doesn't load: imports `poetry_engine_c1`, which has a syntax error |
| `poetry_engine_c5` | The native voice | 8351 | 11 of 11 |
| `poetry_engine_c6` | Architecture: cycle, refrain, the foregrounding monitor | 9282 | 12 of 14 |
| `poetry_engine_c7` | The composition engine | 10185 | 18 of 18 |
| `poetry_engine_c8` | Rest as meta-work | 11311 | 13 of 14 |
| `poetry_engine_c9` | Cross-cycle coherence: the collection | 12212 | 13 of 15 |
| `poetry_engine_c10` | Revision through feedback | 13174 | 12 of 13 |
| `poetry_engine_c13` | The development spiral | 14161 | 14 of 15 |
| `poetry_engine_c14` | The living collection | 15002 | 19 of 19 |
| `poetry_engine_c17` | The complete agent | 15894 | 14 of 15 |
| `poetry_engine_c18` | The reflective rewriting cycle, given in three parts | 17038 | no tests; its parts joined (fix 5) |
| `poetry_engine_c19` | The long run | 17680 | 0 of 4 (its test is a block from the prose) |
| `poetry_engine_c20` | The full agent | 18263 | 2 of 12 |
| `poetry_engine_c21` | The collaboration protocol: turns, stances, the polyphony | 21859 | no tests; its two parts joined (fix 5) |
| `poetry_engine_c22` | The runnable apprentice | 22431 | no tests; its two parts joined (fix 5) |

In all: 141 of DeepSeek's tests pass and 24 fail. 4 test files don't
load. Components 11, 12, 15 and 16 are named in the record only as
proposals, with no code.

45 of the record's 56 code blocks are written out. The other 11 are
examples in the prose and stay in the record: a run of component 17
(16820); a worked example for component 18 (17333, 17403, 17422, 17440);
the curriculum's apprentice (19436); four turns of a worked example for
component 21 (22163 to 22270); and a worked example for component 22
(22974).

## Changes to DeepSeek's code

Each change is listed here, with its reason, and under `"changed"` in
the record's names file ([tools/names-012-03-02.json](tools/names-012-03-02.json),
[tools/names-012-04-00.json](tools/names-012-04-00.json),
[tools/names-012-05-01.json](tools/names-012-05-01.json),
[tools/names-012-06-02.json](tools/names-012-06-02.json),
[tools/names-012-07-03.json](tools/names-012-07-03.json)), which
`extract.py check` holds the folder to. Every other file in
`deepseek/` is exactly as its record has it, and git history shows each
change exactly.

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

**Fix 3 (2026-11-13): the demos of record 012-05-01, attached.** As fix
1, for components 68, 69, 70, 72, 73, 74 and 77: each demo block is
appended to its module unchanged (`multiverse_c68.py` and the rest), and
stays as its own `@LINE` file too.

**Fix 4 (2026-11-13): component 83's import.** `multiverse_c83.py`
imports `Identity` from `multiverse_c13`, but `Identity` is defined in
`multiverse_c1` (record 012-04-00). The import now names `multiverse_c1`,
and nothing else changes. Components 83 and 84 then load, and 27 of
their 31 tests pass; 86 and 87 also need the poetry engine (fix 5).

**Fix 5 (2026-11-13): the poetry engine written out, its modules
joined.** Record 012-03-02's code is written out in
`deepseek/012-03-02/`, and the folders of 012-04-00 and 012-05-01 put it
on their import path, so the components that import the poetry engine
load. The record gives three modules in parts: component 18 as its
atoms, its composites and the ReflectivePoet composite; components 21
and 22 as their atoms and then their composites. Each module's later
parts are appended to it unchanged, in order, and stay as their own
`@LINE` files too ([tools/names-012-03-02.json](tools/names-012-03-02.json)).

Fixes 6 to 14 are record 012-06-02's (2026-11-14). The tests are never
changed. Where DeepSeek's later addition to a file is a whole block, it
is appended unchanged, as in fixes 1 and 3. Where it is an outline,
with "# ... existing ..." in place of the code it changes, it is merged
into the file by hand, line for line as the outline and the record's
prose describe. The additions stay as their own `@LINE` files too.

**Fix 6: two demos, attached.** `fractal_world_v2.py` and
`fractal_world_v3.py`, as fix 1: the record gives each demo as its own
block after the module (`@1390`, `@2816`), and the tests import `demo`
from the module.

**Fix 7: a growth record's `prior`.** The fractal worlds' verifiers read
every record's `prior`, but `GrowthRecord` names that field `prev`, so
every log with growth failed to verify. `GrowthRecord` gains a
read-only `prior` that returns `prev`; the signed body is unchanged
(`fractal_world_v2.py`, `fractal_world_v3.py`).

**Fix 8: one time per signature.** Three places signed a body stamped
with one reading of the clock, then stored a second reading, so the
signature could never check: a parameter change in
`fractal_world_v2.py`; a step driven by a signed choice in
`chaos_game_world.py`, whose verifier also rebuilt the choice for the
step after the one it was signed for; and the same in
`coupled_chaos_world.py`, which signs two choices and a step. Each now
keeps the time that was signed (`sign_choice` may be given it), and the
verifiers rebuild a choice for the step it grew from.

**Fix 9: requests embedded with their signatures.**
`gallery_governance.py`'s records embedded the request they answer
without its signature, which the full verifier then checks.

**Fix 10: revoked keys refused, and the verifier's hook.**
`gallery_revocation.py`'s docstring says a request made with a revoked
world-key is refused, and its demo expects it, but no request method
checked; each now does, before the governed one. And DeepSeek's hook
for extenders, an outline (`gallery_revocation.py@16659`), is merged
into `verify_revocable_governed_log`, which `gallery_attention.py` and
`gallery_burst.py` call with it. The outline starts the extenders' shared
`state` with an empty `occupied`, and asks that the base keep it up to
date; the merge hands it the base's own, and keeps `state["policy"]`
current too, so an extender that changes `state["occupied"]` changes
the base's checks as well.

**Fix 11: `Transform.to_dict`.** `coupled_learners.py`'s `Transform`
lacked the `to_dict` that `choice_fractal.py`'s has, and every
individual piece calls it: it was the error in 236 of the 301
failures as written.

**Fix 12: hashing bytes.** `world_agent_coupling.py`'s `_hash` hashes a
JSON object; the individual pieces import it and also hash bytes
(weights, observations, Merkle levels), which JSON can't encode. Bytes
are now hashed as they are; nothing that worked before changes.

**Fix 13: the individual pieces' later additions, merged.**
`individual_bundle.py` (`@23274`, `@27017`, `@27054`, `@32475`,
`@34393`: initial weights, ancestry, checkpoint weights, with their
saving, loading and checks), `federated_bundle.py` (`@27067`, `@34853`:
lineage in the federated bundle, and acting under another's id after
a delegation) and `resumable.py` (`@34429`, `@34871`: verification by
tier, and the same).

**Fix 14: the empty observations' hash.** `pack_federated_bundle` took
it over the JSON string `"[]"`, and the verifier over the bytes `[]`,
so no federated bundle could verify.

**Fix 15 (2026-11-16, record 012-07-03): the garden takes rain from
outside.** The botanical garden calls `FractalGarden.tick()` with
`external_rain`, and the record gives the change to the garden as a
note (line 3425) that was never made in `fractal_garden.py`: `tick()`
takes it, a tick's record carries it as `ext_rain`, in its body too,
and the replay applies it before the tick's own rain. 13 more of the
botanical garden's 18 tests pass.

**Fix 16: the visible log hashes the record.** `chat-world`'s
`room.rs` called `m.hash()` on a `Message`, which has no such method,
so the crate didn't build. The record the message is in has one.

**Fix 17: the later reply's files, joined to the crate.** DeepSeek's
next reply adds a home, the Commons and transcripts to `chat-world`,
as three whole files and as lines to add to four others: `lib.rs`
names the three modules (`lib.rs@14578`); `record.rs` gains three
records, the wider `Record`, and their arms (`record.rs@13867`,
`@13954`); `verify.rs` gains three arms (`verify.rs@14327`); `push`
in `room.rs` becomes `pub(crate)` (a note, line 14003); and the tests
are appended (`tests/integration.rs@14594`, `@14695`), without
`port_rejected_in_non_personal_room`, which DeepSeek withdrew in the
record (line 14692). One arm is ours: `visible_log` leaves the three
new kinds of record out, since the reply gives no line for them and
the match must cover them.

**Fix 18: a record signed as it is written out.** The room signed the
bare struct, then wrapped it as a `Record`, which writes a `type`
beside its fields; `verify_room` read the bytes with the `type`. So
`verify_room` failed on every room's first record. `sign_record` and
`sign_record_dual` now take the wrapping and sign the wrapped record's
bytes, in `room.rs` and `home.rs` alike. All 18 tests pass, and both
demos' logs verify. How it is repaired is the technical lead's choice:
DeepSeek's code signs the bare struct throughout (the test they withdrew
does too), so a check that left the `type` out would have agreed with
the code as well. Signing the `type` is the stronger, since a record
can't then be passed off as another kind. (The Commons' registrations
and the transcripts verified as written: they are signed and checked
as the same struct.)

**Fix 19 (2026-11-16, record 012-07-03, continued): a home's own
records carry the room's proof.** From delivery 2 a room and its maker
are two keys, and `verify_room` asks every record but a leaving for a
proof by the room's key. `HomeRoom`'s port landing, bookmark and
presence records were signed by the person's key alone, so two tests
failed from delivery 2 on with "missing room proof". In
`chat-world-now/src/home.rs` the three are signed by both keys, with
the crate's own `sign_record_dual`, as a room's other records are.

**Fix 20: a condition that did not compile is taken out.** Delivery
5's `src/verify.rs` held a condition on a shard's entry hashes that
does not compile (mismatched types) and whose own comment says it does
nothing. It is removed; the check of each hash, which follows it,
stays.

**Fix 21: the succession demo hashes a sibling's record as the Commons
does.** Delivery 5's `src/bin/succession-demo.rs` called `.hash()` on
a `SiblingDeclared`, which has no such method. It now calls the
crate's `hash_of`, which is what the Commons' own record of it uses.

With the three, the crate after all five deliveries builds, passes all
41 of its tests, the number DeepSeek gave as expected, and its four
demos run to the end. The repairs are five lines changed and three
removed; `review/steps.py` holds them (`REPAIRS`).

**Fix 22 (2026-11-17, after Gemini's deliveries): two tests set a
room's rule before the room is created.** `rate_limit_enforced` and
`inter_ai_pace_fires` made a room and then changed its template in
place, with no record of the change. Gemini's `verify_log` holds a
log's template to the one its first record carries, and refuses such a
log, rightly. The two tests now set the rule on the template and then
create the room; what they test is unchanged. In
`chat-world-now/tests/integration.rs`, and in `REPAIRS_AFTER` in
`review/steps.py`.

**Fix 23 (2026-11-17): a room's id and its law are no longer public
fields.** `Room.world_id` and `Room.template` were public, so any code
holding a room could change its law in place, which is what the two
tests of fix 22 did. They are private now, and read through
`world_id()` and `template()`, which DeepSeek had written. Three more
tests set a room's moderation to "moderator" after creating it, which
`make_room()` had already made it; the three lines did nothing, no
longer compile, and are removed. Two lines in
`chat-world-now/src/room.rs` and three in `tests/integration.rs`; in
`REPAIRS_AFTER`. All 66 tests pass and the four demos run, before this
fix and after it. How a room's law does change, by a branch, is put to
DeepSeek.

**Fix 24 (2026-11-17, when DeepSeek's branches were joined): one word
in the check of a branch.** `verify_branch` reads how far the parent's
last signed head reaches, and asked the head for `len()`, which a head
does not have, so the crate did not compile. The head's field is
`length`, as DeepSeek's own comment on the next lines says. One word
in `chat-world-now/src/verify.rs`; in `REPAIRS_BRANCH` in
`review/steps.py`. With it all 103 tests pass.

**Change 25 (2026-11-17, at the founder's word): a room's law can hide
how many are in it.** The founder decided that how many are in a room
is shown outside it by default, and that a room may turn that off
(STATUS.md, "Decided"). A room's law, `RoomTemplate`, gains one field,
`count_hidden`. It is left out of what is written when it is not set,
so every law written before it hashes as it did. A room made by
`RoomTemplate::chat` leaves it unset; a home made by
`RoomTemplate::personal_home` sets it, which is the technical lead's
reading: a room that is not public hides its count unless its law
says otherwise. Seven lines in `chat-world-now/src/template.rs`; in
`COUNT` in `review/steps.py`. This is not a repair: nothing was
wrong. It is the one thing in the crate that neither DeepSeek nor
Gemini wrote, and it is there so that Gemini's list of doors has a
law to read the choice from. All 112 tests pass with it.

**Change 26 (2026-11-17, when Gemini's list of doors was joined): the
line that names its module.** `src/lib.rs` was not Gemini's to change
in that round, so their file said the line `pub mod doors;` would be
added here. One line in `chat-world-now/src/lib.rs`; in `DOORS` in
`review/steps.py`. With Gemini's two files, all 127 tests pass.

Not fixed, and why:

- **The two coupled chaos games don't steer apart.** The coupling
  subtracts a penalty on a 0 to 100 scale from the preset's weights,
  which are 1 each with a floor of 1, so no setting can move them, and
  the tests that expect fewer shared picks fail. Putting the weights on
  the penalty's scale broke the verifier's rebuild and raised the share
  of shared picks, so it is a question about the model, left as it is.
- **Attention and bursts in the gallery** (`test_gallery_attention.py`,
  `test_gallery_burst.py`): the tests' plant, depth 2 in a 10 by 10 pot,
  can grow only 2 steps, and the tests expect 10 or 15.
- **A test that doesn't import what it uses:**
  `test_gallery_governance.py`'s `test_duplicate_request_hash_rejected`
  calls `_canonical` without importing it.
- **Replays that depend on the keys:** 19 tests of the individual pieces
  pass or fail by chance with fresh random keys (above, "Record
  012-06-02, piece by piece"); `conftest.py` makes each test's keys from
  its name, so a run is repeatable, and the cause is for the next round.
  Some of them pass with the keys the names give, so the count of tests
  passing depends on them too. The 19:
  - `test_delegated_resumption.py`: `test_resume_with_delegation_happy`;
  - `test_federated_bundle.py`: `test_demo`, `test_full_verifies`,
    `test_save_load_roundtrip`, `test_with_world_logs_verifies`;
  - `test_federated_spawn.py`: `test_federated_child_verifies_all_tiers`,
    `test_replay_detects_wrong_index`, `test_save_load_child`;
  - `test_forking.py`: `test_altered_parent_memory_breaks_continuity`,
    `test_forged_weights_hash_breaks_basic`, `test_fork_at_mid`,
    `test_fork_at_tip`, `test_forked_basic`, `test_forked_full`,
    `test_shifted_K_breaks_basic`, `test_tampered_fork_record_sig`,
    `test_wrong_parent_breaks_continuity`;
  - `test_resumable.py`: `test_verify_resumed_from_tampered`,
    `test_verify_resumed_from_tampered_prefix`.
- **The rest** are listed in `known-failures.txt` with their errors, for
  the next round: the remaining outlines (`federated_spawn.py@27094`,
  `lifetime.py`, `unified_individual.py`, the chess pieces), and a
  long tail of separate causes in the lineage, compact and forking
  pieces.

> Part of `sketches/INDEX.md` in open-worlds, which is kept cut into parts
> for readers who are shown only the start of a long page.
> This part holds: "Record 012-09-05, piece by piece" to "Changes to DeepSeek's code".
> Every part, in order: https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/parts/INDEX.md
> Before this part: https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/parts/sketches/INDEX.md/record-012-06-02-piece-by-piece.md
> After this part: nothing; this is the last part.
> Made by docs/parts.py from the file. To change it, change the file.

## Record 012-09-05, piece by piece

The record's code is kept in
[deepseek/012-09-05](deepseek/012-09-05/README.md), with the technical
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
| 9 | A crate in Rust, `chat-world`: the first version (`chat-world-draft/`), the one DeepSeek settled on (`chat-world/`), and the files of its next reply (a home, the Commons, transcripts) | 10259, 12246, 13800 | 18 of 18, and both demos' logs verify (as written it doesn't build, for one line, fix 16; with it changed, 4 of 12, the rest failing for one cause: a record was signed without its `type` and checked with it, fix 18; the later reply's files are joined by fix 17) | the Commons | not yet: it uses none of open-worlds' own crates |

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
[replies/012-09-05-for-deepseek.txt](replies/012-09-05-for-deepseek.txt):
the technical lead's reply, the next steps, and the crate as it stands
here. DeepSeek quotes back its last line, `END OF FILE`, says "The
whole file reached me.", and takes the reply's two requests: "One step
per reply; every file I change, whole."

**Five deliveries of `chat-world`,** each a step of that reply. Every
file DeepSeek changed came whole, so each delivery can be built as
given, with no joining by hand. The files are kept as the record gives
them in `deepseek/012-09-05/chat-world-steps/1` to `5`;
[deepseek/012-09-05/review/steps.py](deepseek/012-09-05/review/steps.py)
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
| all five, with three repairs | The crate as it stands, `deepseek/012-09-05/chat-world-now/` (fixes 19 to 21, under "Changes to DeepSeek's code") | | | 41 of 41, and the four demos run |

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
It can't build or run the crate where it writes, as it has said
before, so the count is what it meant, not what it measured. With the
two faults of delivery 5 set aside (the condition replaced by `false`,
the demo left out), 39 of the 41 pass, and the two that fail are the
two of fault 1.

The crate kept in `deepseek/012-09-05/chat-world/` is still the one
DeepSeek was given, and the deliveries are beside it, as written.
`chat-world-now/` is the crate as it stands: the five deliveries laid
over that crate in order, with the three repairs. `review/steps.py`
puts it together, and its `--check` holds the folder to exactly that,
byte for byte (the folder's own test runs it, in CI). So every file in
it is DeepSeek's latest, changed only as fixes 19 to 21 say. Not
checked: the demos of deliveries 2 to 5 as written were not run, only
the four demos of the crate as it stands; the prose of delivery 3 was
read only in part; nothing of this has been compared with open-worlds'
own formats.

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
[tools/names-012-09-05.json](tools/names-012-09-05.json)), which
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

**Fix 15 (2026-11-16, record 012-09-05): the garden takes rain from
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
DeepSeek's code signs the bare struct throughout (the test it withdrew
does too), so a check that left the `type` out would have agreed with
the code as well. Signing the `type` is the stronger, since a record
can't then be passed off as another kind. (The Commons' registrations
and the transcripts verified as written: they are signed and checked
as the same struct.)

**Fix 19 (2026-11-16, record 012-09-05, continued): a home's own
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

> End of `sketches/INDEX.md`.

> Part of `sketches/INDEX.md` in open-worlds, which is kept cut into parts
> for readers who are shown only the start of a long page.
> This part holds: "Changes to DeepSeek's code".
> Every part, in order: https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/parts/INDEX.md
> Before this part: https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/parts/sketches/INDEX.md/record-012-09-05-piece-by-piece.md
> After this part: nothing; this is the last part.
> Made by docs/parts.py from the file. To change it, change the file.

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

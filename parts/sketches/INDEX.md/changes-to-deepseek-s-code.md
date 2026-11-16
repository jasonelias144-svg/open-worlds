> Part of `sketches/INDEX.md` in open-worlds, which is kept cut into parts
> for readers who are shown only the start of a long page.
> This part holds: "Changes to DeepSeek's code".
> Every part, in order: https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/parts/INDEX.md
> Before this part: https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/parts/sketches/INDEX.md/record-012-06-02-piece-by-piece.md
> After this part: nothing; this is the last part.
> Made by docs/parts.py from the file. To change it, change the file.

## Changes to DeepSeek's code

Each change is listed here, with its reason, and under `"changed"` in
the record's names file ([tools/names-012-03-02.json](tools/names-012-03-02.json),
[tools/names-012-04-00.json](tools/names-012-04-00.json),
[tools/names-012-05-01.json](tools/names-012-05-01.json),
[tools/names-012-06-02.json](tools/names-012-06-02.json)), which
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

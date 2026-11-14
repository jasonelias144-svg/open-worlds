# Reasons on record

The founder, 2026-11-13: "reasoning behind decisions that affect others
should be inspectable, being subject to audit." "We can use Lean to test
the logic of reasoning that is presented." And: "if that reason is good,
sharing it is a good thing, because it is information available to the
multiverse as a reason for a decision that could have implications."

[ADMIN.md](ADMIN.md), "ADMIN in the open", says who gives reasons: every
decision a Keeper or ADMIN makes that affects others goes on record with
its reasons, and stands on them. This page says how: what a decision
record holds, what code checks, and what Lean can check and what it
can't.

Giving reasons is an old duty of public office. The EU's Charter of
Fundamental Rights counts, in the right to good administration, "the
obligation of the administration to give reasons for its decisions"
(Article 41(2)(c),
[FRA](https://fra.europa.eu/en/eu-charter/article/41-right-good-administration)).

## Which decisions

An office's decisions that affect others:

- **a change to a world's conditions** by its Keeper, a gardener's act
  ([DESIGN.md](DESIGN.md), "The gardener, in practice");
- **a path's design** for someone, and each change to it;
- **a proposal to change a world's law.** A Keeper can't change the law
  itself: a change takes effect only by the consent the world's law asks
  for ([DESIGN.md](DESIGN.md), principle 4). The proposal carries its
  reasons; a vote on it needs none, since voting is an individual's own
  act;
- **a grant,** and narrowing, suspending or revoking one;
- **a ruling:** on a complaint, an appeal, an office or a seat.

Not an individual's own acts. They are public, in the record, but an
individual decides nothing for others beyond their acts, which the floor
bounds, and owes no one reasons.

A reason can be one line. What matters is that it is given, and that the
decision stands on it.

## A decision record

Proposed for step 2, with the other formats
([research/FORMATS.md](research/FORMATS.md)):

| Field | What it holds |
|---|---|
| `format` | `open-worlds/decision/v1` |
| `office` | who decides: the office's key, and the grant it acts under |
| `act` | what changes: the kind of act, and the records it makes, by hash |
| `affects` | whom it affects: individuals, worlds or offices, by key |
| `reasons` | why, in plain words; never empty |
| `grounds` | what it rests on: the charter's sections, the world's law, rules, and earlier records, by hash |
| `inputs` | everything read in deciding, by hash; all of it is in the public log |
| `formal` | optional: a proof in Lean, by hash, of a property the rules name for this kind of act, with the version of the model it uses (below) |
| `views` | ADMIN's only: each council member's view |
| `supersedes` | the earlier decision it changes, if any; that one stays on record |
| `appeal` | where an appeal goes |
| `tick` | when |

The office signs the record's RFC 8785 form, as for every record. The act
and its record go into the log as one entry, so the act can't go in
without its reasons. A grant, too, takes effect only from its entry in
the log, with its record, and so does narrowing, suspending or revoking
one: a grant handed over but not logged allows nothing.

Software teams keep decisions in much the same way. Michael Nygard's
architecture decision records (2011) have a context, the decision, a
status, and the consequences, and "All consequences should be listed
here, not just the "positive" ones"; a later decision marks an earlier
one "superseded", with a reference to its replacement
([Cognitect](https://cognitect.com/blog/2011/11/15/documenting-architecture-decisions)).
`supersedes` is borrowed from there; consequences belong in `reasons`.

## What code checks

The world's kernel accepts an office's act only with its record. Which
acts need one is decided by the kind of act, from a list fixed in the
rules, never by the record's own `affects`, so an office can't skip the
record by naming no one. The kernel refuses the act, and logs the
refusal, if:

- `reasons` is empty, or `grounds` names nothing;
- an input isn't in the public log;
- the grant named doesn't allow the act;
- the rules ask for a `formal` part for this kind of act and there is
  none, or Lean's kernel doesn't accept its proof (below).

These are tests 4, 23a and 24 in [ADMIN.md](ADMIN.md). Code can check
that each input listed is in the log. It can check that the list is
complete only where the proxy built the whole context, as for ADMIN and
an AI Keeper; for a Keeper who is also an individual, that rests on
audit (test 23b). And code can check that reasons are given. It can't
check that they are good: that is for audit and appeal (test 23b).

## What Lean checks

Lean is a language for writing proofs, and its kernel checks them
mechanically. As one guide puts it, "Lean's kernel is small enough that
developers can write their own implementation and independently check
proofs" ([Type Checking in Lean
4](https://ammkrn.github.io/type_checking_in_lean4/whats_a_kernel.html)).
So anyone who doubts our checker can write their own.

It has two uses here. The first comes sooner.

1. **Proofs about the rules, once.** Some properties of the rules as code
   must hold in every case, not only in the cases a test tries:
   - a grant can only narrow what its issuer holds, so no chain of grants
     widens;
   - exit is always possible;
   - nothing is removed from a log.

   Lean can prove such a property of a model of the rules, for every case
   at once. Grants come first, at course step 4, where their checks are
   written. The honest limit: a proof is about the model. That the Rust
   world kernel matches the model is checked by test vectors made from it,
   which is evidence, not proof.
2. **Proofs that come with a decision.** Some reasons can be stated
   exactly, such as "no sequence of acts under this new law lets anyone
   hold another in". Then the record can carry a proof, and the world's
   kernel has Lean's kernel check it before the act takes effect. This is
   proof-carrying code, from George Necula (1997): "the untrusted code
   producer must supply with the code a safety proof that attests to the
   code's adherence to a previously defined safety policy"
   ([ACM](https://dl.acm.org/doi/10.1145/263699.263712)). Here the
   producer is an office, the code is its decision, and the policy is the
   floor. Three rules make that hold:
   - **The rules set what is proved, not the office.** Lean's kernel
     checks that a proof proves its statement, not that the statement is
     the right one; a true but beside-the-point statement would pass. So
     the statement comes from a fixed, reviewed list of the floor's
     properties, which the world's kernel applies to the act at hand. The
     office supplies only the proof.
   - **No gaps and no added axioms.** A proof that rests on `sorry`, or on
     any axiom outside a short published list, is refused. Lean accepts
     such proofs as written, and `native_decide` adds an axiom that
     trusts Lean's compiler.
   - **Checked apart, and within limits.** Checking a proof can take
     long, by accident or design. It runs outside the world kernel's
     process, with a limit on time and memory, and a proof that runs out
     is refused.

   It needs laws written in a form Lean can read; until then, the floor
   is checked by code and tests.

   Where a check is one code can simply run (is this grant inside that
   one?), code does it, and a proof would add nothing. Lean is for claims
   about every case.

What Lean can't check:

- **whether the premises are true of the world.** A proof that "no one is
  held in, if the doors work as modelled" says nothing if the model is
  wrong;
- **whether a decision is wise, fair or kind.** Most reasons are
  judgment, and stay in words;
- **anything from a private core,** which can't be a premise, and is
  kept out of decisions by how they run ([ADMIN.md](ADMIN.md), "ADMIN in
  the open", test 23c).

So a record with no `formal` part is normal. Lean checks the logic where
there is logic to check; audit and appeal check the rest.

## When each part is built

- **Course step 2 (formats):** the decision record's schema and test
  vectors.
- **Course step 4 (the kernel):** an office's act refused without its
  record; a model of grants in Lean, with a proof that no chain of grants
  widens, checked by CI with a pinned Lean toolchain, and test vectors
  made from the model.
- **Later, once a world's law can be read by Lean:** proofs that come
  with decisions, starting with changes to a world's law.

## Not checked

- How hard it is to model the kernel's rules in Lean: step 4 finds out,
  starting with grants.
- Whether the record's fields fit every kind of decision: step 2 finds
  out, and the format is versioned.

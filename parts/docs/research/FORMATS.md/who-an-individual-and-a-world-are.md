> Part of `docs/research/FORMATS.md` in open-worlds, which is kept cut into parts
> for readers who are shown only the start of a long page.
> This part holds: "Who an individual and a world are" to "Not checked".
> Every part, in order: https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/parts/INDEX.md
> Before this part: https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/parts/docs/research/FORMATS.md/start.md
> After this part: nothing; this is the last part.
> Made by docs/parts.py from the file. To change it, change the file.

## Who an individual and a world are

**Decided by the technical lead, 2026-11-14:** four more kinds join
`schemas/records-v1.schema.json`, each signed as every record is:

- **An identity** (`open-worlds/identity/v1`): `id`, the did:key, which
  signs it; `name`; `sealingKey`, the key to seal things to them, as
  Multikey (`z6LS...`); and `birth`, their birth record by hash. Signed
  with their own key, it binds the sealing key to them, which "Sealed
  records" left to this record. A sealing key not safe to seal to (at or
  above 2^255 - 19, or of small order) is refused beyond the schema, as
  `formats/seal.py` refuses it.
- **An individual's birth record** (`open-worlds/birth/v1`), signed by the
  world: `individual`, `name`, `tick` and `time`; `mind`, the mind record
  they were born with, by hash; and `words`, the words they were told
  ([MINDS.md](../MINDS.md), "The birth record"). Facts only, written once.
- **A world's birth record** (`open-worlds/world-birth/v1`), signed by the
  world itself, which binds its key to its birth, as an identity binds a
  sealing key: `name`, `law` by hash, `founders` (none for a world the
  project made), `time`, and, for a world made from a template or forked
  from
  another, `template` and `forkedFrom` (the parent world, the tick, and
  the hash of the parent's log there), as decided on 2026-11-14
  ([VISION.md](../VISION.md), "Learning from GitHub"). A world made from
  a template names, in `dials`, exactly what it changed: each dial the
  template declares that it set, as an integer in the unit the template
  states ([PARALLEL-WORLDS.md](../PARALLEL-WORLDS.md), "Parallel
  worlds"). Whether each is a dial of that template, and within its
  range, is checked against the template ("A world's template", below).
  A world's seed, which a founder chooses with its name and law
  ([WORLD-KEY.md](../WORLD-KEY.md), "The workbench, and founding"), is
  one of its template's dials, so it needs no field of its own, if
  every world, a founded one included, is made from a template: the
  kernel's code, with the founder's choices among its dials. Course
  step 12, which builds founding, confirms that or adds the field.

  WORLD-KEY.md had the birth record of a founded world signed by the
  Ur-world and the founders. Decided instead (2026-11-14, on the
  independent review of #46): the world signs its own, and the Ur-world
  and each founder confirm the founding in records of their own, each
  naming the birth record, the Ur-world's also naming the world-keys
  used, which marks them used; a new kind, at course step 12. Every
  record here carries one proof by one key, and so do these; signing one
  record by several keys (Data Integrity's proof sets) would change the
  signing code in both languages for one kind, ten steps early. Until
  then, `founders` is the world's own claim.
- **A mind record** (`open-worlds/mind/v1`), signed by the project's key
  that keeps mind records: the `individual`, and every engine they have
  run on: the model at an exact 40-digit revision, its files by hash (each
  path once, none leaving the model's repository), its settings, its chat
  template by hash, the container image by digest ("Container images",
  above; never a tag alone), and when it began, listed in the order they
  began. Settings are integers or strings: a quantity with a fraction,
  such as a temperature, is a string, since the canonical form has no
  floats.

What the schema can't say is checked where the records meet the kernel
(course step 4), as for the offices' records: that an identity's `birth`
is a birth record of the same individual and name; that a birth record's
`mind` is a mind record of the one born, and its `world` is a world; and
that a mind record's issuer is the project's key for mind records,
published at course step 3. Until then, any key can sign a mind record
naming itself as issuer; it holds as a record, but nothing honours it.

Every time in these records must be a real one (a grant's always had to
be). Shared vectors (`vectors/formats/records-v1.json`): 6 more records
that hold, and 22 more that must be refused, among them an identity
whose sealing key is of small order, a birth record on 30 February, a
mind record whose image is named by a tag, and one whose engines are out
of order.

## A world's template

**Decided by the technical lead, 2026-11-14:** a world's template
(`open-worlds/template/v1`) joins `schemas/records-v1.schema.json`,
signed by the project's key that keeps templates
([PARALLEL-WORLDS.md](../PARALLEL-WORLDS.md), "Parallel worlds";
[VISION.md](../VISION.md), "Ride along, and steer"):

- **`code`:** the reviewed code that runs a world made from it, a
  repository at an exact commit. Users choose settings, never code.
- **`parameters`:** every world-level parameter, each an integer `value`
  in a stated `unit`, with `about`, a sentence saying what it is. Units
  are UCUM codes (the Unified Code for Units of Measure, version 2.2,
  2024, "a code system intended to include all units of measures being
  contemporarily used in international science"): `1` for a plain
  number, `ms`, `10*-3/s` for thousandths per second, `{molecule}` for a
  count. UCUM codes are 7-bit ASCII without spaces, which the schema
  checks; whether a code is well formed UCUM isn't checked. Its licence
  lets software use the codes; the project uses them only as labels and
  doesn't reproduce the specification.
- **Dials:** a parameter with `min` and `max` is a dial, which a world
  may set within that range. Beyond the schema, a dial must have room to
  turn (`min` below `max`), and its value must be within its range.
  Parameters without them are fixed.

A world made from a template names it by hash, and in its birth
record's `dials` exactly what it changed (above). `dial_problems`, in
`formats/records.py` and `rust/formats`, checks the two against each
other: that the world names that template; that each dial it set is
one of the template's dials, within its range; and that it differs from
the template's own value. So two worlds made the same way have the same
birth-record dials, and what two worlds share and where they differ can
be read from their records alone. Mirror worlds are worlds with the same
template and the same dials, the seed among them.

The vectors' template is the chemistry world's law
(`multiverse/chemistry_world.py`, `ChemistryWorldLaw`) at its defaults,
every field an integer in a stated unit, and a test checks that they
still agree. Its dials are the seed, the world time each act lets run,
and the water, glycine and formaldehyde in the soil; its rates are
fixed, as placeholders until course step 8. Shared vectors: the template,
9 templates that must be refused, and 8 pairs of a world's birth record
and a template, 2 that agree and 6 that don't.

Until the project's key for templates is published (course step 3) and
checked where records meet the kernel (step 4), any key can sign a
template naming itself as issuer; it holds as a record, as a mind record
does, but nothing honours it.

Not yet: how the kernel builds a world from a template and its dials,
and the law text it writes for it (course step 4). Until then, a
template's law and rules are carried by its `code`: the law text is
what that code writes from the parameters, and what each rule acts on
is in that code too.

## The key list

From course step 3: the project's key list (`open-worlds/key-list/v1`),
signed by the multiverse's root, names the key that holds each role;
each version names the one before and is signed by its root. Why, and
how it is checked, is in [KEYS.md](KEYS.md).

## Persons

From course step 3a, part two: a link between a person and one of their
presences, `open-worlds/holds/v1`, signed by the person, and
`open-worlds/held-by/v1`, signed by the presence, which holds only when
both name the same person, presence and world; and a person's list of
their presences, `open-worlds/person-list/v1`, versioned and signed by
the person. Presence keys are made from a seed with HKDF-SHA256. Why,
and the exact encoding, are in [PERSONS.md](PERSONS.md).

## Councils

Course step 3a, the council ([research/PERSONS.md](PERSONS.md), "Part
four, second half, built"). A council's proposal,
`open-worlds/proposal/v1`, signed by the council, names its choices (2
to 16), the worlds whose births it trusts, a quorum of persons, and when
votes count, from `opens` to `closes` (it must close after it opens). A
person's vote, `open-worlds/vote/v1`, signed by their identity key,
names the proposal by its hash, a choice by its place, and a time. A
vote is public, and the person's: it shows who voted, and how, under one
identity key across every council. Its time is the voter's own claim,
which nothing witnesses yet (PERSONS.md, "Its limits").
`formats/council.py` and `rust/formats/src/council.rs` count the votes
the same way, against `vectors/formats/council-v1.json`.

## The arrival

From course step 3: an individual enters a world by signing an arrival
(`open-worlds/arrival/v1`): the world's did:key, their own, the name, the
tick, and the hash of the world's log entry just before the arrival's
own, signed by the individual alone. Why, and how the Ur-world holds
names to keys with it, is in [KEYS.md](KEYS.md) (decisions 11 to 18).

## What step 2 defines

Done: signed records (`formats/`, `rust/formats`), the records for the
offices (above), sealing ("Sealing", "As built"), the sealed records
(world-key, journal entry), who an individual and a world are (identity,
birth records, mind record), a world's template, and the chemistry world's
records of what was made ("Writing JSON the same way everywhere"). Each
record has a schema in 2020-12 and test vectors that Python and Rust both
check, except the chemistry world's, which only Python makes and checks.
The design pages named fourteen records for this step: identity, birth
record, mind record, journal entry, routine, sheet, avatar, skill
attestation, world-key credential, grant, decision record, suggestion,
rating, and signed log head. Of these, four moved, with what they describe
(decided by the technical lead, 2026-11-14): the avatar to course step 4,
the sheet and skill attestation to step 5, the routine to step 7. Each
joins records-v1 as a new kind, by the same rules, with vectors in both
languages.

## Not checked

- Whether every record fits these choices: step 2 finds out as each
  schema is written.
- `serde_jcs` against `rfc8785`: step 2's test vectors will check it.
- did:key's test vectors, and VC Data Model 2.0 beyond its definitions and
  securing mechanisms.
- Sealing keys on the curve's twist aren't refused. No secret key has
  one as its public key, so a box sealed to one can't be opened by
  anyone, not even whoever chose the key: `enc` lies on the curve, and
  the twist's order is 4 times a prime of about 2^253 (checked with a
  primality test), so the shared secret would take a discrete logarithm
  in a group that large. The message is lost; nothing is given away.
  Both languages could refuse such keys (one modular power in Python, by
  Euler's criterion; `curve25519-dalek` in Rust) if that is ever wanted.
- Python checks RFC 9180's example only by opening it, through
  `cryptography`'s private `_decrypt_with_aad`, since the example has
  associated data; the test is skipped if that function goes. Rust makes
  the example again in full.

> End of `docs/research/FORMATS.md`.

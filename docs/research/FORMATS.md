# Formats that last: what to adopt

Research for course step 2 ([COURSE.md](../COURSE.md)), done on
2026-11-13 under house rule 10, "look first"
([COLLABORATING.md](../COLLABORATING.md)). Step 2 set out to define every
record an individual, a world and ADMIN keep, so that they can be read
and checked for as long as the project lasts, in Rust and in Python
alike; four moved to later steps ("What step 2 defines", below). Before
inventing anything, this note asks of each standard named in the design
pages: what is it, how settled is it, who implements it and under what
licence, and does it fit? Sources were read on that day; library versions
are as their registries gave them.

## Writing JSON the same way everywhere

**RFC 8785, the JSON Canonicalization Scheme,** "defines how to create a
canonical representation of JSON data": properties sorted by their UTF-16
code units, characters other than control characters written as they are,
numbers as ECMAScript writes them, and anything else refused. It is an
Informational RFC, "not an Internet Standards Track specification"
([RFC 8785](https://www.rfc-editor.org/rfc/rfc8785.html)).

What we already do: every record this project signs is written as JSON
with sorted keys and no spaces (`multiverse/identity.py`, `canonical`),
and every world log is hashed the same way except that it escapes
characters outside ASCII (`world/core.py`, `rust/world-log`).

**Checked, by a script kept here** (`jcs_compare.py`, seed 1, against
Trail of Bits' implementation, `rfc8785` 0.1.4, importing our own
`canonical`): of 2,005 documents with ASCII keys, integers within RFC
8785's range, and no floats,

- the form we sign equals RFC 8785 in all 2,005;
- the form logs are hashed in equals it in 184, the ones with no
  character outside ASCII;
- RFC 8785 refuses an integer beyond 2^53 - 1, which our logs accept (any
  64-bit integer);
- **floats differ:** of eight written each way, four come out differently
  (`1.0` against `1`, `-0.0` against `0`, `1e-07` against `1e-7`, `1e+20`
  against `100000000000000000000`), since RFC 8785 writes numbers as
  JavaScript does.

So our form equals RFC 8785 only for documents whose keys are ASCII (RFC
8785 sorts by UTF-16 code units, Python by code points; they differ for
keys beyond the first 65,536 characters), whose integers stay within
2^53 - 1, and which hold no floats. Not every record we sign today
qualifies: the independent review found that the chemistry world's
records of what was made carry its time as a float (`world_time`,
`multiverse/chemistry_world.py`), and a world's signed "made" stamp
commits to such a record's fingerprint (`thing_fingerprint`,
`multiverse/passport.py`). Since the chemistry world's law v0.5
(2026-11-14), they don't: the record names its format
(`open-worlds/chemistry-made/v1`, `schemas/chemistry-made-v1.schema.json`)
and gives its world time in whole microseconds (`world_time_us`). The
world keeps it within the rules: an act's seconds are a whole number of
microseconds, at most an hour; once world time passes 2^53 - 1
microseconds (about 285 years) the world takes no more acts; and it
refuses a product whose identity is longer than the schema allows. A
test checks the records of three kinds of reaction against the schema
and these rules; the independent review checked 1,366 records, from nine
of the ten rules. Records made before keep their float, as they were
signed.

**Libraries:** `rfc8785` for Python (Trail of Bits, Apache 2.0, 0.1.4,
September 2024, no dependencies); `serde_jcs` for Rust (MIT or Apache 2.0,
0.2.0, March 2026).

**Proposed:** name RFC 8785 as the form of every new signed record, with
three rules every format keeps: keys are ASCII; integers stay within
2^53 - 1 (larger values, such as a 64-bit seed, are written as strings);
and no floats (a quantity with a fraction is written as an integer in a
stated unit, or as a string). Records already signed, and logs, keep
their own form, which is versioned and checked by its own vectors;
nothing old is rewritten. The chemistry world's records of what was made
move to these rules when step 2 writes their schema, with its time as an
integer in a stated unit; what it signed before stays as it was.

## Signatures on records

**Verifiable Credential Data Integrity: the EdDSA cryptosuites,** a W3C
Recommendation of 15 May 2025, defines `eddsa-jcs-2022`, which "takes an
input document, canonicalizes the document using the JSON Canonicalization
Scheme", then hashes and signs the result with Ed25519, "using the
`Ed25519` variant (Pure EdDSA)". What it signs is not the document
itself: "Let hashData be the result of joining proofConfigHash (the first
hash) with transformedDocumentHash (the second hash)", that is, a hash of
a proof configuration followed by a hash of the document
([W3C](https://www.w3.org/TR/vc-di-eddsa/)).

This project signs differently: Ed25519 over the canonical bytes of the
document itself, with no proof configuration (`multiverse/ed25519.py`).
So our signed bytes are RFC 8785's form, within the bounds above, which is
the form `eddsa-jcs-2022` canonicalizes to; but our signatures are not
that suite's, and a tool that verifies it would refuse them.

**Proposed:** step 2 decides whether new records sign the
`eddsa-jcs-2022` way (a proof configuration, the two hashes, then
Ed25519), so that standard tools can check them. Signatures already made
stay as they are.

**Decided by the technical lead, 2026-11-14:** new records sign the
`eddsa-jcs-2022` way, with did:key verification methods. It is built in
Python (`formats/`) and Rust (`rust/formats`), and both reproduce the
specification's own example (Appendix B.3) step by step: the two RFC
8785 forms, both hashes, the signature and the proof value. They read
proofs more narrowly than the specification allows: one proof per
record, did:key only, `created` to the second in UTC, and the three rules
above. Both refuse a signature whose R is a point of small order, which
cofactorless verification alone would accept. Both read values already
parsed from JSON; reading JSON text, where parsers differ on duplicate
keys and on `-0`, is settled where records are first read from files or
the network. Signatures already made stay as they are (STATUS.md).

## Credentials

**The Verifiable Credentials Data Model 2.0,** a W3C Recommendation of
15 May 2025, defines a verifiable credential: "A tamper-evident credential
whose authorship can be cryptographically verified", secured
either by Data Integrity proofs, as above, or by JOSE and COSE
([W3C](https://www.w3.org/TR/vc-data-model-2.0/)).

Where it fits: the world-key (a signed right to found), skill
attestations, and ADMIN's grants are each a signed claim by one party
about another. What it costs: the full model brings JSON-LD contexts,
which this project doesn't otherwise need.

**Proposed:** shape these records after the data model (an issuer, a
subject, a claim, validity, a proof) and use its names where they fit, so
they can be expressed as verifiable credentials later, without taking on
JSON-LD now. Revisit when worlds talk across machines (course step 12).

## Identifiers

**did:key** ("The did:key Method v0.9", published by the W3C Credentials
Community Group) writes a public key as an identifier, such as
`did:key:z6MkhaXgBZDvotDkL5257faiztiGiC2QtKLGpbnnEGta2doK` for an Ed25519
key. But it "does not support key rotation because the identifier is
derived directly from the public key material": a new key is a new
identifier ([specification](https://w3c-ccg.github.io/did-key-spec/)).

Our individuals and worlds outlive their keys: a key can be signed over
to a new one (WCP/0.4, true today in the Python worlds). So did:key can
name a key, but not an individual.

**Proposed:** write every public key as a did:key. An individual's or a
world's lasting identifier is the did:key of its birth key, which never
changes; its current key is found by following its successions from
there.

## Schemas

**JSON Schema**'s current version is 2020-12: "The current version is
2020-12! The previous version was 2019-09"
([json-schema.org](https://json-schema.org/specification)).

**Libraries:** `jsonschema` for Python (MIT, 4.26.0, January 2026, "Full
support for Draft 2020-12"); `jsonschema` for Rust (MIT, 0.61.2,
November 2026).

**Proposed:** one schema per record, in 2020-12, kept in the repository,
with test vectors that both languages must accept or refuse alike, as the
log already has.

## Sealing

**HPKE** (RFC 9180) seals a message so that only the holder of a private
key can open it.

- **Python:** `cryptography`, already a dependency (50.0.2), added HPKE
  in 47.0.0, "implementing RFC 9180" (its
  [changelog](https://github.com/pyca/cryptography/blob/main/CHANGELOG.rst);
  this page said 48.0.0 until step 2's third part). It offers DHKEM(X25519) among
  others, but no choice of mode: in it, "the sender is anonymous", which
  is HPKE's base mode
  ([documentation](https://cryptography.io/en/latest/hazmat/primitives/hpke/)).
- **Rust:** `hpke` (MIT or Apache 2.0, 0.15.1, October 2026) implements
  all four modes, base and Auth among them. Its authors say "nobody has
  performed a paid audit of this crate"; Cloudflare reviewed version 0.8
  ([repository](https://github.com/rozbb/rust-hpke)).

The design pages named HPKE's Auth mode for the sealed world-key: the box
is sealed with a key made from the Ur-world's key and the earner's, as the
founder proposed ("generated from the individuals public key and the
world public key"). Python's `cryptography` can't do that. Base mode can:
a key made from a fresh one-time key and the earner's key, so the box is
still "readable only by the individual", and the Ur-world's signature
inside says who issued what it holds.

What base mode changes:

- **The box no longer says who made it;** the signature inside says who
  issued what it holds. For the earner, that covers what Auth mode would
  give, and it can be shown to others too. Anyone holding the signed
  world-key could seal it again; the next point makes that harmless.
- **So the signed content must name its recipient** (the credential's
  subject, as the earner's did:key), and whoever opens it checks that it
  is theirs. Otherwise an earner could seal their signed world-key to a
  third party, who would then hold a validly signed world-key in a box
  addressed to them.
- **A signed world-key can be shown to anyone** as proof that the Ur-world
  issued it. Auth mode alone wouldn't give that. It is probably welcome.
- **The sealing key:** HPKE seals to an X25519 key, and identities hold
  Ed25519 keys for signing. So each identity carries a second key, for
  sealing, as MINDS.md already says; `cryptography` doesn't convert one to
  the other, and separate keys are the better practice.

**Decided by the technical lead** (2026-11-13), the founder having
deferred on technical matters ([STATUS.md](../../STATUS.md), "Decided by
the technical lead"): base mode, with DHKEM(X25519, HKDF-SHA256) and
ChaCha20Poly1305, available in both languages without a new dependency in
Python; what is sealed is always signed first, and names its recipient,
who checks it; and HPKE's `info` carries a label naming the purpose and
its version (`open-worlds/world-key/v1`), so a box made for one purpose
can't be passed off as another. It departs from the founder's design, and the founder was
told so the same day. The alternatives, not taken: Auth mode, which keeps
the design page's "key that only the two of them can make", at the cost
of sealing in Rust only, a new Python library, or Auth mode built by hand
from `cryptography`'s X25519 and HKDF (not recommended: cryptography put
together by hand is where mistakes hide). Revisit if a sealed world-key
is ever honoured for anyone it doesn't name, or if the box itself, still
closed, must show who sealed it. Noise (revision 34, 2018) stays named
only for a private line, if the founder chooses one
([Noise](https://noiseprotocol.org/noise.html)).

**As built** (step 2, part three: `formats/seal.py`, `rust/formats`):

- **A box** is `enc || ct`: the one-time key, then the ciphertext, as RFC
  9180's single-shot Seal gives them and `cryptography` writes them
  ("The encapsulated key concatenated with ciphertext (enc || ct)").
  There is no associated data, which `cryptography`'s public functions
  don't take; whatever must be bound to a box goes inside it, signed.
- **Labels** are a fixed list, now `open-worlds/world-key/v1` and
  `open-worlds/journal/v1`; a new purpose or version is added by a
  reviewed change. The one opening a box
  names the label it expects, and nothing is read from the box to choose
  it. A label not on the list is refused before anything is tried; a box
  sealed under another label doesn't open, since HPKE binds `info` into
  every key it derives.
- **A sealing key** is an X25519 key, refused unless it is below
  2^255 - 19 as a number (so it has one spelling; a key with the top bit
  set, which RFC 7748 ignores, is another spelling) and not of small
  order. HPKE requires the one opening a box to refuse an all-zero
  shared secret (RFC 9180, 7.1.4: "recipients MUST check whether the
  Diffie-Hellman shared secret is the all-zero value and abort if so"),
  and both libraries refuse it when sealing too; this refuses such a key
  wherever a key is checked.
- **As Multikey,** a sealing key is written like the signing keys, with
  multicodec's prefixes for X25519: "x25519-pub, key, 0xec" and
  "x25519-priv, key, 0x1302" (multicodec's
  [table](https://github.com/multiformats/multicodec/blob/master/table.csv),
  where Ed25519's are listed the same way, all as "draft"). A sealing key
  starts `z6LS`.
- **Shared vectors** (`vectors/formats/hpke-base-v1.json`): RFC 9180's
  own example for this suite (A.2.1), which Rust reproduces byte for byte
  and Python opens; boxes made by each language, which the other opens;
  and boxes, labels and keys that must be refused.
- **What is sealed names its recipient,** who checks that it is theirs:
  "Sealed records", below.

## Sealed records

Step 2, part four (`formats/sealed.py`, `rust/formats`). Two kinds of
record are sealed, each in `schemas/records-v1.schema.json`:

- **A world-key** (`open-worlds/world-key/v1`): `issuer`, the world that
  placed the path, which signs; `holder`, the one who earned it; `path`,
  the path walked, by the hash of its record in the public log; `tick`,
  when the issuer's code confirmed it done. Shaped after the Verifiable
  Credentials data model ("Credentials", above): an issuer, a subject (the
  holder, as a grant names it), a claim (the format itself: the right to
  found a world), a proof. It has no end date, as WORLD-KEY.md gives
  none. Sealed to its holder under `open-worlds/world-key/v1`.
- **A journal entry** (`open-worlds/journal-entry/v1`): `author`, who
  signs; `world` and `tick`, where and when it was written; `text`, in the
  author's own words; and, if it remembers events, `remembers`, each by
  its world and tick, so a memory without a record behind it shows
  ([MINDS.md](../MINDS.md), "Memory"). Sealed to its author under
  `open-worlds/journal/v1`.

Each travels in an envelope (`open-worlds/sealed/v1`): the label, the one
it is addressed to (`to`), and the box in lowercase hex. The envelope
isn't signed; what is inside is. Its fingerprint is the hash of its RFC
8785 form. A sealed self shows the world each envelope's fingerprint and
size: that an entry exists, and how much was written
([MINDS.md](../MINDS.md), "The birth record"). When it was placed comes
from the log it is placed in, not from the envelope.

**Sealing** checks the record first: it must hold, be a sealed kind, and
go to the one it names; it is sealed in its RFC 8785 form.

**Opening** checks everything again, in this order: the envelope's shape,
its label against the opener's, its address against the opener; that the
box opens; that what is inside is a record in its one RFC 8785 form and
holds; that it is a kind sealed under that label; and that it names the
opener. So a world-key sealed again to someone else opens for them but is
refused: it names another. The label in the envelope is checked only to
refuse early with a clearer reason; what holds a box to its purpose is
HPKE, which opens it only under the label it was sealed with.

**Not here:** which sealing key belongs to which did:key is the identity
record's to say (course step 9; until then the key list publishes the
ones made at step 3), so the caller gives both.

**The "break glass"**, chosen by the founder on 2026-11-14, needs nothing
more here. The private half of each sealing key is kept in the project's
private repository ([MINDS.md](../MINDS.md), "Where everything lives"),
so a sealed self can be opened there, by the founder's explicit decision
only, and every opening is recorded publicly. The envelope and the record
stay as they are; a second envelope, which this page once expected, isn't
needed.

**Shared vectors** (`vectors/formats/sealed-records-v1.json`): 3 records
that hold and 7 that don't; 3 envelopes that open, each with the hash of
the record inside and its fingerprint; 13 that must be refused when
opened, each saying what it was sealed to, under which label, and what is
inside, so anyone can check it is what its name says; and 7 refused for
their shape alone.

## Commitments

Not needed. This section proposed holding back each challenge's design as
a hash taken with a secret random value (HKDF, RFC 5869). On 2026-11-13
the founder decided "Challenges, not tests": "Nothing needs to be hidden
as answers, they are discovered in the process." So nothing is held
back, and step 2 defines no commitment format.

## Grants

**UCAN** ("Version 1.0.0") gives "public-key verifiable, delegable,
expressive, openly extensible capabilities", with principals named by
DIDs, and attenuation, "the process of constraining the capabilities in a
delegation chain" ([specification](https://github.com/ucan-wg/spec)). Its
README states no licence for the specification.

**Proposed:** a small grant record of our own, modelled on UCAN's: an
issuer and a holder (as did:keys), what it allows, its limits in time and
scope, the grant it narrows, and a signature, with the rule that a grant
can only narrow what its issuer holds. A grant takes effect only from its
entry in the log, with its decision record, and so does narrowing,
suspending or revoking one ([REASONS.md](../REASONS.md)). Adopting UCAN
itself is revisited at step 12, when grants cross worlds.

## Decision records

Of what we looked at, nothing standard covers a signed decision with its
reasons and grounds. The closest is the architecture decision record
that software teams keep: a context, the decision, a status, and the
consequences
([REASONS.md](../REASONS.md), with the source).

**Proposed:** a record of our own, `open-worlds/decision/v1`, signed in
RFC 8785 form like the rest: the office and the grant it acts under, the
act, whom it affects, the reasons, the grounds, the inputs, an optional
proof in Lean, the decision it supersedes, and where an appeal goes
([REASONS.md](../REASONS.md)).

## A log with signed heads

Our logs are hash-chained; a chain shows an entry changed or removed in
the middle, but not a log cut short ([ADMIN.md](../ADMIN.md)). Certificate
Transparency logs sign their heads, and watchers compare them
([OVERSIGHT.md](OVERSIGHT.md)).

**Proposed:** a signed head, the world's signature over its id, the head's
format version, its log's last hash, its length and the tick, in RFC 8785
form, so that no head can be passed off as another world's; published with
the log from step 3, when the Ur-world gets its key. Whether the
multiverse log needs a Merkle tree, to prove an entry is in it without
reading all of it, is decided at step 12.

## Container images

An OCI image is named exactly by its digest, `sha256:` and 64 hexadecimal
characters ([OVERSIGHT.md](OVERSIGHT.md), "Containers").

**Proposed:** the mind record gives the image as `REGISTRY/NAME@sha256:...`,
never by a tag alone, since a tag can be moved. An image built for
several platforms has a digest for its index and one for each platform's
image; the mind record gives the digest of the image that actually ran,
and the index's beside it.

## Records for the offices

**Decided by the technical lead, 2026-11-14:** the grant, the decision
record, the suggestion, the rating and the signed log head are defined in
one schema,
[`schemas/records-v1.schema.json`](../../schemas/records-v1.schema.json)
(JSON Schema 2020-12), which Python (`jsonschema` 4.26.0) and Rust
(`jsonschema` 0.60.2) both read, and each is signed with `eddsa-jcs-2022`
(above). The choices in it:

- **Every party is a did:key:** an individual, a world, an office. A
  world is named by its key, as "Identifiers" proposes; following
  successions from a birth key comes with step 3's keys.
- **A record is named by its hash:** the SHA-256 of its RFC 8785 form,
  proof included, in lowercase hex. A grant names the grant it narrows
  this way; a decision names its grant and inputs this way.
- **Each kind has one signer:** a grant its issuer, a decision the
  office's key, a suggestion and a rating their author, a log head its
  world. A record signed by anyone else doesn't hold, however good its
  signature.
- **Times and ticks:** a grant holds from and until a UTC time, since a
  grant can reach across worlds whose ticks differ; a record that belongs
  to a log carries that log's tick.
- **Patterns in one dialect:** JSON Schema's patterns are ECMA-262's.
  Python's `$` also matches before a final line break, so
  `formats/records.py` reads a final `$` as `\Z`; and "not only spaces"
  is written as an explicit set of characters, since `\s` differs between
  the libraries. Shared vectors hold both cases.
- **Text people and minds write** is not empty, not only spaces or line
  breaks of any kind, and holds no control characters (C0, DEL or C1)
  but tab and line breaks.
- **A suggestion to ADMIN about a Keeper or a world** names which, by
  key.
- **A suggestion made outside any world,** by ADMIN or a Keeper in the
  multiverse, names no world; its tick is the multiverse log's.
- **What a schema can't say** is checked where records meet the kernel,
  at course step 4: that a grant only narrows the grant it names; that a
  decision's inputs are in the log, its office holds the grant it names,
  that grant allows its kind of act, and the kind is on the rules' list
  ([REASONS.md](../REASONS.md)); that a rating's author wrote the
  suggestion it names, and its outcome is a decision naming that
  suggestion; and that a world-key's issuer is a world that places paths,
  its path was placed in that world's log and walked to its end by its
  holder, and it hasn't been used to found a world already
  ([WORLD-KEY.md](../WORLD-KEY.md): "It is marked as used at the
  founding"). Until then, anyone can sign a world-key naming themselves;
  it opens, and holds as a record, but no world will honour it.
- **Versioned:** a change to a kind's shape makes `records-v2`; records
  made under v1 stay readable under v1. A new kind is added to v1, since
  it changes no record already made: the world-key and the journal entry
  were added so ("Sealed records").

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

# Formats that last: what to adopt

Research for course step 2 ([COURSE.md](../COURSE.md)), done on
2026-11-13 under house rule 10, "look first"
([COLLABORATING.md](../COLLABORATING.md)). Step 2 defines every record an
individual, a world and ADMIN keep, so that they can be read and checked
for as long as the project lasts, in Rust and in Python alike. Before
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
`multiverse/passport.py`).

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
above. Signatures already made stay as they are (STATUS.md).

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
  in 48.0.0, "implementing RFC 9180". It offers DHKEM(X25519) among
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
entry in the log, with its decision record, and so does narrowing or
revoking one ([REASONS.md](../REASONS.md)). Adopting UCAN itself is
revisited at step 12, when grants cross worlds.

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
- **What a schema can't say** is checked where records meet the kernel,
  at course step 4: that a grant only narrows the grant it names, that a
  decision's inputs are in the log, and that its kind of act is on the
  rules' list ([REASONS.md](../REASONS.md)).
- **Versioned:** a change makes `records-v2`; records made under v1 stay
  readable under v1.

## What step 2 defines

Done so far: signed records (`formats/`, `rust/formats`), and the
records for the offices (above). From the design pages, each with a
schema in 2020-12 and test vectors in both languages: identity, birth
record, mind record, journal entry (sealed: its ciphertext and
fingerprint), routine, sheet, avatar, skill attestation, world-key
credential, grant, decision record, and signed log head.

## Not checked

- Whether every record fits these choices: step 2 finds out as each
  schema is written.
- `serde_jcs` against `rfc8785`: step 2's test vectors will check it.
- did:key's test vectors, and VC Data Model 2.0 beyond its definitions and
  securing mechanisms.
- HPKE interoperability between `cryptography` and `hpke`: step 2's vectors
  will check it before anything is sealed.

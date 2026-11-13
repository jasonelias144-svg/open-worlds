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

**Checked, by a script kept here** (`jcs_compare.py`, seed 1, with Trail
of Bits' reference library `rfc8785` 0.1.4): of 2,005 documents with
ASCII keys and integers within RFC 8785's range,

- the form we sign equals RFC 8785 in all 2,005;
- the form logs are hashed in equals it in 184, the ones with no
  character outside ASCII;
- RFC 8785 refuses an integer beyond 2^53 - 1, which our logs accept (any
  64-bit integer).

So the records we already sign are written exactly as RFC 8785 writes
them, as long as keys are ASCII (RFC 8785 sorts by UTF-16 code units,
Python by code points; they differ only for keys beyond the first 65,536
characters) and integers stay within 2^53 - 1.

**Libraries:** `rfc8785` for Python (Trail of Bits, Apache 2.0, 0.1.4,
September 2024, no dependencies); `serde_jcs` for Rust (MIT or Apache 2.0,
0.2.0, March 2026).

**Proposed:** name RFC 8785 as the form of every new signed record, with
two rules every format keeps: keys are ASCII, and integers stay within
2^53 - 1 (larger values, such as a 64-bit seed, are written as strings).
Logs keep their own form, which is versioned and checked by its own
vectors; nothing old is rewritten.

## Signatures on records

**Verifiable Credential Data Integrity: the EdDSA cryptosuites,** a W3C
Recommendation of 15 May 2025, defines `eddsa-jcs-2022`, which
"canonicalizes the document using the JSON Canonicalization Scheme" and
signs it "using the `Ed25519` variant (Pure EdDSA)"
([W3C](https://www.w3.org/TR/vc-di-eddsa/)).

That is what this project already does: Ed25519 over sorted, compact JSON
(course step 2 of the first course, `multiverse/ed25519.py`), which the
check above shows is RFC 8785's form. **Proposed:** keep our signatures,
and describe them as `eddsa-jcs-2022`'s canonical form, so that any tool
that verifies that suite can check our records' bytes.

## Credentials

**The Verifiable Credentials Data Model 2.0,** a W3C Recommendation of
15 May 2025, defines a verifiable credential as "a tamper-evident
credential whose authorship can be cryptographically verified", secured
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

**Libraries:** `jsonschema` for Python (MIT, 4.26.0, January 2026, "full
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

The design pages name HPKE's Auth mode for the sealed world-key, so that
the box itself says the Ur-world sealed it. But the world-key inside is
already signed by the Ur-world, so the signature says that, and base mode
is enough to make the box "readable only by the individual", as the
founder asked.

**Proposed:** base mode, with DHKEM(X25519, HKDF-SHA256) and
ChaCha20Poly1305, available in both languages without a new dependency in
Python; what is sealed is always signed first. The design page changes to
match in step 2. Noise (revision 34, 2018) stays named only for a private
line, if the founder chooses one ([Noise](https://noiseprotocol.org/noise.html)).

## Commitments

A challenge's design is held back as a hash taken together with a secret
random value. **HKDF** (RFC 5869), "a simple Hashed Message Authentication
Code (HMAC)-based key derivation function", derives a value for each
challenge from the world's path secret
([RFC 5869](https://www.rfc-editor.org/rfc/rfc5869.html)). It is in
`cryptography` already.

**Proposed:** the value is 32 bytes, from HKDF-SHA256 over the path secret
with the challenge's id as its label; the commitment is SHA-256 over the
RFC 8785 form of the design, its reasons and the value.

## Grants

**UCAN** ("Version 1.0.0") gives "public-key verifiable, delegable,
expressive, openly extensible capabilities", with principals named by
DIDs, and attenuation, "the process of constraining the capabilities in a
delegation chain" ([specification](https://github.com/ucan-wg/spec)). Its
README states no licence for the specification.

**Proposed:** a small grant record of our own, modelled on UCAN's: an
issuer and a holder (as did:keys), what it allows, its limits in time and
scope, the grant it narrows, and a signature, with the rule that a grant
can only narrow what its issuer holds. Adopting UCAN itself is revisited at
step 12, when grants cross worlds.

## A log with signed heads

Our logs are hash-chained; a chain shows an entry changed or removed in
the middle, but not a log cut short ([ADMIN.md](../ADMIN.md)). Certificate
Transparency logs sign their heads, and watchers compare them
([OVERSIGHT.md](OVERSIGHT.md)).

**Proposed:** a signed head, the world's signature over its log's last
hash, its length and the tick, in RFC 8785 form, published with the log
from step 3, when the Ur-world gets its key. Whether the multiverse log
needs a Merkle tree, to prove an entry is in it without reading all of
it, is decided at step 12.

## Container images

An OCI image is named exactly by its digest, `sha256:` and 64 hexadecimal
characters ([OVERSIGHT.md](OVERSIGHT.md), "Containers").

**Proposed:** the mind record gives the image as `REGISTRY/NAME@sha256:...`,
never by a tag alone, since a tag can be moved.

## What step 2 defines

From the design pages, each with a schema in 2020-12 and test vectors in
both languages: identity, birth record, mind record, journal entry
(sealed: its ciphertext and fingerprint), routine, sheet, avatar, skill
attestation, world-key credential, grant, commitment, and signed log head.

## Not checked

- Whether every record fits these choices: step 2 finds out as each
  schema is written.
- `serde_jcs` against the reference library: step 2's test vectors will
  check it.
- did:key's test vectors, and VC Data Model 2.0 beyond its definitions and
  securing mechanisms.
- HPKE interoperability between `cryptography` and `hpke`: step 2's vectors
  will check it before anything is sealed.

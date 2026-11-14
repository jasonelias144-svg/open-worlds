"""Formats that last (course step 2): records written the same way
everywhere, and signed so that standard tools can check them.

- `canonical`: RFC 8785, the JSON Canonicalization Scheme, with this
  project's three rules (ASCII keys, integers within 2^53 - 1, no floats).
- `multikey`: keys written as Multikey, and Ed25519 keys as did:key.
- `proof`: Data Integrity proofs with the `eddsa-jcs-2022` cryptosuite,
  W3C Recommendation of 15 May 2025.
- `records`: the records the offices keep (grant, decision, suggestion,
  rating, signed log head), checked against schemas/records-v1.schema.json.
- `seal`: a message only one key can open, with HPKE (RFC 9180) and a
  label naming its purpose.

docs/research/FORMATS.md says why each was chosen.
"""

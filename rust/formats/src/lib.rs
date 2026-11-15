//! Formats that last (course step 2): records written the same way
//! everywhere, and signed so that standard tools can check them.
//!
//! The same as the Python package `formats/`, checked against it through
//! `vectors/formats/eddsa-jcs-2022.json`:
//!
//! - [`canonical`]: RFC 8785 with this project's three rules (ASCII keys,
//!   integers within 2^53 - 1, no floats);
//! - [`multikey`]: keys written as Multikey, and Ed25519 keys as did:key;
//! - [`proof`]: Data Integrity proofs with the `eddsa-jcs-2022`
//!   cryptosuite (W3C Recommendation, 15 May 2025);
//! - [`records`]: the records the offices keep, checked against
//!   `schemas/records-v1.schema.json`;
//! - [`seal`]: messages sealed to one key with HPKE (RFC 9180), checked
//!   through `vectors/formats/hpke-base-v1.json`;
//! - [`sealed`]: world-keys and journal entries, signed and sealed to the
//!   one they name, checked through `vectors/formats/sealed-records-v1.json`;
//! - [`persons`]: one individual across worlds: presence keys from a
//!   seed, links that hold only both ways, and a person's list, checked
//!   through `vectors/formats/persons-v1.json`.
//! - [`council`]: a council's count: persons' signed votes on a
//!   proposal, each person counted once, and only persons whose birth a
//!   world the proposal trusts signed.

pub mod canonical;
pub mod council;
pub mod multikey;
pub mod persons;
pub mod proof;
pub mod records;
pub mod seal;
pub mod sealed;

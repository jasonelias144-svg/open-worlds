pub mod error;
pub mod hash;
pub mod did;
pub mod proof;
pub mod template;
pub mod record;
pub mod room;
pub mod verify;

pub use did::{DidKey, Keypair};
pub use error::{Error, Result};
pub use proof::{Proof, ProofOrArray, ProofPurpose};
pub use room::{Member, Room};
pub use template::{ModeratorSpec, RoomTemplate};

pub fn now() -> String {
    chrono::Utc::now().to_rfc3339_opts(chrono::SecondsFormat::Millis, true)
}

pub(crate) fn sign_record<T, F>(
    mut rec: T,
    signer: &Keypair,
    set_proof: F,
) -> Result<T>
where
    T: serde::Serialize,
    F: FnOnce(&mut T, ProofOrArray),
{
    let body = hash::body_for_signing(&rec)?;
    let sig = signer.sign(&body);
    let proof = ProofOrArray::Single(Proof::create(signer, &sig));
    set_proof(&mut rec, proof);
    Ok(rec)
}

pub(crate) fn sign_record_dual<T, F>(
    mut rec: T,
    subject: &Keypair,
    room: &Keypair,
    set_proof: F,
) -> Result<T>
where
    T: serde::Serialize,
    F: FnOnce(&mut T, ProofOrArray),
{
    let body = hash::body_for_signing(&rec)?;
    let subj_sig = subject.sign(&body);
    let room_sig = room.sign(&body);
    let subj_proof = Proof::create(subject, &subj_sig);
    let room_proof = Proof::create(room, &room_sig);
    set_proof(&mut rec, ProofOrArray::array(vec![subj_proof, room_proof]));
    Ok(rec)
}

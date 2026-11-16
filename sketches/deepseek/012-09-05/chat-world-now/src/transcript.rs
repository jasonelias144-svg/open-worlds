use crate::did::{DidKey, Keypair};
use crate::error::{Error, Result};
use crate::hash;
use crate::proof::{Proof, ProofOrArray};
use serde::{Deserialize, Serialize};

#[derive(Clone, Debug, Serialize, Deserialize, PartialEq)]
pub struct TranscriptEntry {
    pub speaker: String,
    pub ts: String,
    pub text: String,
}

#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct Transcript {
    #[serde(rename = "type")]
    pub type_: String,
    pub source_label: String,
    pub entries: Vec<TranscriptEntry>,
    pub porter_id: DidKey,
    pub ts: String,
    pub proof: ProofOrArray,
}

impl Transcript {
    pub fn hash(&self) -> Result<String> {
        hash::hash_of(self)
    }
}

pub fn sign_transcript(
    source_label: &str,
    entries: Vec<TranscriptEntry>,
    porter_kp: &Keypair,
) -> Result<Transcript> {
    let mut t = Transcript {
        type_: "transcript".into(),
        source_label: source_label.into(),
        entries,
        porter_id: porter_kp.did(),
        ts: crate::now(),
        proof: ProofOrArray::placeholder(),
    };
    let body = hash::body_for_signing(&t)?;
    let sig = porter_kp.sign(&body);
    t.proof = ProofOrArray::single(Proof::create(porter_kp, &sig));
    Ok(t)
}

pub fn verify_transcript(t: &Transcript) -> Result<()> {
    if t.type_ != "transcript" {
        return Err(Error::Verification("not a transcript".into()));
    }
    let body = hash::body_for_signing(t)?;
    let proof = t
        .proof
        .find_by_method(&t.porter_id)
        .ok_or_else(|| Error::Verification("missing porter proof".into()))?;
    proof.verify(&body)
}

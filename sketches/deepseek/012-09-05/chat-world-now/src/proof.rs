use crate::did::{DidKey, Keypair};
use crate::error::{Error, Result};
use ed25519_dalek::Signature;
use serde::{Deserialize, Serialize};

#[derive(Clone, Copy, Debug, Serialize, Deserialize, PartialEq)]
#[serde(rename_all = "camelCase")]
pub enum ProofPurpose {
    AssertionMethod,
    Authentication,
}

#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct Proof {
    #[serde(rename = "type")]
    pub type_: String,
    pub cryptosuite: String,
    pub created: String,
    #[serde(rename = "verificationMethod")]
    pub verification_method: DidKey,
    #[serde(rename = "proofPurpose")]
    pub proof_purpose: ProofPurpose,
    #[serde(rename = "proofValue")]
    pub proof_value: String,
}

impl Proof {
    pub fn create(keypair: &Keypair, sig: &Signature) -> Self {
        Proof {
            type_: "DataIntegrityProof".into(),
            cryptosuite: "eddsa-jcs-2022".into(),
            created: crate::now(),
            verification_method: keypair.did(),
            proof_purpose: ProofPurpose::AssertionMethod,
            proof_value: format!("z{}", bs58::encode(sig.to_bytes()).into_string()),
        }
    }

    pub fn placeholder() -> Self {
        Proof {
            type_: "DataIntegrityProof".into(),
            cryptosuite: "eddsa-jcs-2022".into(),
            created: "1970-01-01T00:00:00.000Z".into(),
            verification_method: DidKey::parse(
                "did:key:0000000000000000000000000000000000000000000000000000000000000000",
            )
            .unwrap(),
            proof_purpose: ProofPurpose::AssertionMethod,
            proof_value: "z111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111".into(),
        }
    }

    pub fn verify(&self, body: &[u8]) -> Result<()> {
        let encoded = self
            .proof_value
            .strip_prefix('z')
            .ok_or_else(|| Error::InvalidProof("missing z prefix".into()))?;
        let bytes = bs58::decode(encoded)
            .into_vec()
            .map_err(|e| Error::InvalidProof(e.to_string()))?;
        let arr: [u8; 64] = bytes
            .try_into()
            .map_err(|_| Error::InvalidProof("wrong sig length".into()))?;
        let sig = Signature::from_bytes(&arr);
        self.verification_method
            .verifying_key()?
            .verify_strict(body, &sig)
            .map_err(|e| Error::InvalidProof(e.to_string()))
    }
}

#[derive(Clone, Debug, Serialize, Deserialize)]
#[serde(untagged)]
pub enum ProofOrArray {
    Single(Proof),
    Array(Vec<Proof>),
}

impl ProofOrArray {
    pub fn single(p: Proof) -> Self { ProofOrArray::Single(p) }
    pub fn array(v: Vec<Proof>) -> Self { ProofOrArray::Array(v) }
    pub fn placeholder() -> Self { ProofOrArray::Single(Proof::placeholder()) }
    pub fn to_vec(&self) -> Vec<&Proof> {
        match self {
            ProofOrArray::Single(p) => vec![p],
            ProofOrArray::Array(v) => v.iter().collect(),
        }
    }
    pub fn len(&self) -> usize {
        match self {
            ProofOrArray::Single(_) => 1,
            ProofOrArray::Array(v) => v.len(),
        }
    }
    pub fn find_by_method(&self, did: &DidKey) -> Option<&Proof> {
        self.to_vec().into_iter().find(|p| &p.verification_method == did)
    }
}

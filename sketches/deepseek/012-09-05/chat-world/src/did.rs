use crate::error::{Error, Result};
use ed25519_dalek::{Signature, Signer, SigningKey, Verifier, VerifyingKey};
use serde::{Deserialize, Deserializer, Serialize, Serializer};

#[derive(Clone, PartialEq, Eq, Hash, Debug)]
pub struct DidKey(String);

impl DidKey {
    pub fn from_verifying_key(vk: &VerifyingKey) -> Self {
        DidKey(format!("did:key:{}", hex::encode(vk.to_bytes())))
    }

    pub fn parse(s: &str) -> Result<Self> {
        let rest = s
            .strip_prefix("did:key:")
            .ok_or_else(|| Error::InvalidDid(format!("missing prefix: {s}")))?;
        if rest.len() != 64 {
            return Err(Error::InvalidDid(format!("wrong length: {s}")));
        }
        hex::decode(rest).map_err(|_| Error::InvalidDid(format!("bad hex: {s}")))?;
        Ok(DidKey(s.to_string()))
    }

    pub fn verifying_key(&self) -> Result<VerifyingKey> {
        let rest = self.0.strip_prefix("did:key:").unwrap();
        let bytes = hex::decode(rest).map_err(|_| Error::InvalidDid("bad hex".into()))?;
        let arr: [u8; 32] = bytes
            .try_into()
            .map_err(|_| Error::InvalidDid("wrong length".into()))?;
        VerifyingKey::from_bytes(&arr).map_err(|e| Error::InvalidDid(e.to_string()))
    }

    pub fn as_str(&self) -> &str {
        &self.0
    }
}

impl std::fmt::Display for DidKey {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        f.write_str(&self.0)
    }
}

impl Serialize for DidKey {
    fn serialize<S: Serializer>(&self, s: S) -> std::result::Result<S::Ok, S::Error> {
        s.serialize_str(&self.0)
    }
}

impl<'de> Deserialize<'de> for DidKey {
    fn deserialize<D: Deserializer<'de>>(d: D) -> std::result::Result<Self, D::Error> {
        let s = String::deserialize(d)?;
        DidKey::parse(&s).map_err(serde::de::Error::custom)
    }
}

#[derive(Clone)]
pub struct Keypair {
    signing: SigningKey,
}

impl Keypair {
    pub fn generate() -> Self {
        use rand::rngs::OsRng;
        Keypair { signing: SigningKey::generate(&mut OsRng) }
    }

    pub fn did(&self) -> DidKey {
        DidKey::from_verifying_key(&self.signing.verifying_key())
    }

    pub fn sign(&self, msg: &[u8]) -> Signature {
        self.signing.sign(msg)
    }

    pub fn verify(&self, msg: &[u8], sig: &Signature) -> Result<()> {
        self.signing
            .verifying_key()
            .verify(msg, sig)
            .map_err(|e| Error::InvalidProof(e.to_string()))
    }
}

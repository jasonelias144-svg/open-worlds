use thiserror::Error;

#[derive(Error, Debug)]
pub enum Error {
    #[error("crypto error: {0}")]
    Crypto(String),
    #[error("serialization: {0}")]
    Serialization(String),
    #[error("invalid did: {0}")]
    InvalidDid(String),
    #[error("invalid proof: {0}")]
    InvalidProof(String),
    #[error("chain: {0}")]
    Chain(String),
    #[error("policy: {0}")]
    Policy(String),
    #[error("verification: {0}")]
    Verification(String),
    #[error("io: {0}")]
    Io(#[from] std::io::Error),
}

pub type Result<T> = std::result::Result<T, Error>;

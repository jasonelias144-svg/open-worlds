//! Keys written as Multikey (`z` and base58-btc of a two-byte prefix and
//! the key), and Ed25519 keys as did:key, as `formats/multikey.py` writes
//! them.

/// The prefix of an Ed25519 public key (multicodec 0xed).
pub const ED25519_PUBLIC: [u8; 2] = [0xed, 0x01];
/// The prefix of an Ed25519 secret key (multicodec 0x1300).
pub const ED25519_SECRET: [u8; 2] = [0x80, 0x26];
/// The prefix of an X25519 sealing key (multicodec 0xec).
pub const X25519_PUBLIC: [u8; 2] = [0xec, 0x01];
/// The prefix of an X25519 secret key (multicodec 0x1302).
pub const X25519_SECRET: [u8; 2] = [0x82, 0x26];
const DID_KEY: &str = "did:key:";

fn encode(prefix: [u8; 2], key: &[u8; 32]) -> String {
    let mut raw = Vec::with_capacity(34);
    raw.extend_from_slice(&prefix);
    raw.extend_from_slice(key);
    format!("z{}", bs58::encode(raw).into_string())
}

fn decode(prefix: [u8; 2], text: &str) -> Result<[u8; 32], String> {
    let body = text
        .strip_prefix('z')
        .ok_or("a Multikey starts with z (base58-btc)")?;
    let raw = bs58::decode(body).into_vec().map_err(|e| e.to_string())?;
    let (head, key) = raw.split_at_checked(2).ok_or("too short for a key")?;
    let key: [u8; 32] = key
        .try_into()
        .map_err(|_| "not a key of the expected kind")?;
    if head != prefix {
        return Err("not a key of the expected kind".into());
    }
    if encode(prefix, &key) != text {
        return Err("not the key's one written form".into());
    }
    Ok(key)
}

/// The Multikey of an Ed25519 public key (z6Mk...).
pub fn public_multikey(public: &[u8; 32]) -> String {
    encode(ED25519_PUBLIC, public)
}

/// The Ed25519 public key a Multikey names.
pub fn public_from_multikey(text: &str) -> Result<[u8; 32], String> {
    decode(ED25519_PUBLIC, text)
}

/// The Ed25519 secret key a secret Multikey holds (test vectors only).
pub fn secret_from_multikey(text: &str) -> Result<[u8; 32], String> {
    decode(ED25519_SECRET, text)
}

/// The Multikey of an X25519 sealing key (z6LS...). Whether the key is fit
/// to seal to is [`crate::seal::check_public`]'s to say.
pub fn sealing_multikey(public: &[u8; 32]) -> String {
    encode(X25519_PUBLIC, public)
}

/// The X25519 sealing key a Multikey names.
pub fn sealing_from_multikey(text: &str) -> Result<[u8; 32], String> {
    decode(X25519_PUBLIC, text)
}

/// The X25519 secret key a secret sealing Multikey holds (test vectors
/// only).
pub fn sealing_secret_from_multikey(text: &str) -> Result<[u8; 32], String> {
    decode(X25519_SECRET, text)
}

/// The did:key's one verification method: `did:key:K#K`.
pub fn verification_method(public: &[u8; 32]) -> String {
    let key = public_multikey(public);
    format!("{DID_KEY}{key}#{key}")
}

/// The public key a did:key verification method names; only did:key is
/// read, so nothing is looked up.
pub fn public_from_verification_method(text: &str) -> Result<[u8; 32], String> {
    let rest = text
        .strip_prefix(DID_KEY)
        .ok_or("only did:key verification methods are read")?;
    let (identifier, fragment) = rest
        .split_once('#')
        .ok_or("a did:key method is did:key:K#K")?;
    if identifier != fragment {
        return Err("a did:key method is did:key:K#K".into());
    }
    public_from_multikey(identifier)
}

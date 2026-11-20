use crate::error::{Error, Result};
use serde::Serialize;
use serde_json::Value;
use sha2::{Digest, Sha256};

/// RFC 8785 JCS canonical form. Integers only, ASCII keys — a
/// constrained subset of JCS that our records always satisfy.
pub fn canonicalize<T: Serialize>(value: &T) -> Result<Vec<u8>> {
    let v = serde_json::to_value(value)
        .map_err(|e| Error::Serialization(e.to_string()))?;
    let mut out = String::new();
    walk(&v, &mut out);
    Ok(out.into_bytes())
}

/// Canonicalize with the `proof` field stripped. Used for signing.
pub fn body_for_signing<T: Serialize>(value: &T) -> Result<Vec<u8>> {
    let mut v = serde_json::to_value(value)
        .map_err(|e| Error::Serialization(e.to_string()))?;
    if let Value::Object(map) = &mut v {
        map.remove("proof");
    }
    let mut out = String::new();
    walk(&v, &mut out);
    Ok(out.into_bytes())
}

fn walk(v: &Value, out: &mut String) {
    match v {
        Value::Null => out.push_str("null"),
        Value::Bool(b) => out.push_str(if *b { "true" } else { "false" }),
        Value::Number(n) => {
            if let Some(i) = n.as_i64() {
                out.push_str(&i.to_string());
            } else if let Some(u) = n.as_u64() {
                out.push_str(&u.to_string());
            } else {
                out.push('0');
            }
        }
        Value::String(s) => write_string(s, out),
        Value::Array(arr) => {
            out.push('[');
            for (i, item) in arr.iter().enumerate() {
                if i > 0 { out.push(','); }
                walk(item, out);
            }
            out.push(']');
        }
        Value::Object(map) => {
            let mut keys: Vec<&String> = map.keys().collect();
            keys.sort();
            out.push('{');
            for (i, key) in keys.iter().enumerate() {
                if i > 0 { out.push(','); }
                write_string(key, out);
                out.push(':');
                walk(&map[*key], out);
            }
            out.push('}');
        }
    }
}

fn write_string(s: &str, out: &mut String) {
    out.push('"');
    for c in s.chars() {
        match c {
            '"' => out.push_str("\\\""),
            '\\' => out.push_str("\\\\"),
            '\u{08}' => out.push_str("\\b"),
            '\u{09}' => out.push_str("\\t"),
            '\u{0A}' => out.push_str("\\n"),
            '\u{0C}' => out.push_str("\\f"),
            '\u{0D}' => out.push_str("\\r"),
            c if (c as u32) < 0x20 => {
                out.push_str(&format!("\\u{:04x}", c as u32));
            }
            c => out.push(c),
        }
    }
    out.push('"');
}

pub fn sha256_hex(bytes: &[u8]) -> String {
    let mut h = Sha256::new();
    h.update(bytes);
    hex::encode(h.finalize())
}

/// Hash of the full record, including proofs. This is what `prev`,
/// `target_hash`, and `home_ref` reference.
pub fn hash_of<T: Serialize>(value: &T) -> Result<String> {
    Ok(sha256_hex(&canonicalize(value)?))
}

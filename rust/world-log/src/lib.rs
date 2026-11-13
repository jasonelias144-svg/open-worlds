// rust/world-log/src/lib.rs
//! A world's public record, checked in Rust exactly as the Python kernel
//! (`world/core.py`) writes it: hash for hash.
//!
//! Every event in a world goes into an append-only log. Each entry holds
//! `tick`, `kind`, `agent`, `data` and `prev` (the hash of the entry before
//! it, or [`GENESIS`] for the first), and `hash`: the SHA-256, in lowercase
//! hex, of the entry without its hash, written as Python writes it with
//! `json.dumps(body, sort_keys=True, separators=(",", ":"))`.
//!
//! [`python_json`] writes that text, [`digest`] hashes it, and
//! [`verify_log`] checks a whole log, as `World.verify_log` does in Python.
//!
//! This is the first piece of the world kernel in Rust. The shared test
//! vectors in `vectors/` are written by the Python kernel
//! (`python3 -m world.vectors`), and this crate's tests check it against
//! them.
//!
//! # Limits
//!
//! - Numbers must be integers that fit in 64 bits. The agent kernel writes
//!   no others, apart from the seed its operator gives it, which Python
//!   doesn't check; the chemistry soup's log holds floats. A float, a larger
//!   integer, or JSON's `-0` (which `serde_json` reads as a float, and
//!   Python as 0) is refused here ([`Error::Number`]) rather than risk
//!   writing a different text.
//! - Nesting deeper than [`MAX_DEPTH`] is refused (Python allows more).
//! - A log is only as trustworthy as its last hash. A log cut short still
//!   holds together: compare its head with one you trust.

use serde_json::{Map, Value};
use sha2::{Digest, Sha256};
use std::fmt;

/// The `prev` of a log's first entry: sixty-four zeros.
pub const GENESIS: &str = "0000000000000000000000000000000000000000000000000000000000000000";

/// The deepest nesting written. `serde_json` reads fewer than 128 levels,
/// so anything it reads can be written.
pub const MAX_DEPTH: usize = 128;

/// Why a value can't be written as Python writes it.
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum Error {
    /// A number that isn't an integer in 64 bits (its text, as read).
    Number(String),
    /// Nested deeper than [`MAX_DEPTH`].
    TooDeep,
}

impl fmt::Display for Error {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Error::Number(n) => write!(f, "{n} is not an integer in 64 bits"),
            Error::TooDeep => write!(f, "nested deeper than {MAX_DEPTH}"),
        }
    }
}

impl std::error::Error for Error {}

/// Why a log doesn't hold. Entries are counted from 0.
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum LogError {
    /// The log isn't a list.
    NotAList,
    /// The entry isn't an object with a text `hash`.
    Malformed {
        /// The entry's place in the log.
        index: usize,
    },
    /// The entry's `prev` isn't the hash of the entry before it.
    BrokenChain {
        /// The entry's place in the log.
        index: usize,
    },
    /// The entry's `hash` doesn't match its contents.
    WrongHash {
        /// The entry's place in the log.
        index: usize,
    },
    /// The entry holds a value that can't be written as Python writes it.
    Unwritable {
        /// The entry's place in the log.
        index: usize,
        /// What can't be written.
        error: Error,
    },
}

impl fmt::Display for LogError {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            LogError::NotAList => write!(f, "the log is not a list"),
            LogError::Malformed { index } => {
                write!(f, "entry {index} is not an object with a text hash")
            }
            LogError::BrokenChain { index } => {
                write!(f, "entry {index} does not follow the entry before it")
            }
            LogError::WrongHash { index } => {
                write!(f, "entry {index} does not match its hash")
            }
            LogError::Unwritable { index, error } => write!(f, "entry {index}: {error}"),
        }
    }
}

impl std::error::Error for LogError {}

/// The text Python's `json.dumps(value, sort_keys=True,
/// separators=(",", ":"))` writes for `value`: keys sorted by code point,
/// no spaces, and every character outside printable ASCII escaped as
/// `\uXXXX` in lowercase hex (as a surrogate pair beyond U+FFFF).
pub fn python_json(value: &Value) -> Result<String, Error> {
    let mut out = String::new();
    write_value(value, &mut out, 0)?;
    Ok(out)
}

/// The SHA-256, in lowercase hex, of [`python_json`]'s text: the hash the
/// kernel gives a log entry's body.
pub fn digest(value: &Value) -> Result<String, Error> {
    Ok(sha256_hex(python_json(value)?.as_bytes()))
}

/// The SHA-256 of `bytes`, in lowercase hex.
pub fn sha256_hex(bytes: &[u8]) -> String {
    hex(&Sha256::digest(bytes))
}

/// Checks a whole log, as the Python kernel's `World.verify_log` does: each
/// entry names the hash of the one before it as `prev` ([`GENESIS`] for the
/// first), and its `hash` matches its other fields. Returns the head (the
/// last entry's hash, or [`GENESIS`] for an empty log).
pub fn verify_log(log: &Value) -> Result<&str, LogError> {
    let entries = log.as_array().ok_or(LogError::NotAList)?;
    let mut prev = GENESIS;
    for (index, entry) in entries.iter().enumerate() {
        let fields = entry.as_object().ok_or(LogError::Malformed { index })?;
        let hash = fields
            .get("hash")
            .and_then(Value::as_str)
            .ok_or(LogError::Malformed { index })?;
        if fields.get("prev").and_then(Value::as_str) != Some(prev) {
            return Err(LogError::BrokenChain { index });
        }
        let mut body = String::new();
        write_object(fields, Some("hash"), &mut body, 0)
            .map_err(|error| LogError::Unwritable { index, error })?;
        if sha256_hex(body.as_bytes()) != hash {
            return Err(LogError::WrongHash { index });
        }
        prev = hash;
    }
    Ok(prev)
}

fn write_value(value: &Value, out: &mut String, depth: usize) -> Result<(), Error> {
    match value {
        Value::Null => out.push_str("null"),
        Value::Bool(true) => out.push_str("true"),
        Value::Bool(false) => out.push_str("false"),
        Value::Number(n) => {
            if let Some(i) = n.as_i64() {
                out.push_str(&i.to_string());
            } else if let Some(u) = n.as_u64() {
                out.push_str(&u.to_string());
            } else {
                return Err(Error::Number(n.to_string()));
            }
        }
        Value::String(s) => write_str(s, out),
        Value::Array(items) => {
            if depth >= MAX_DEPTH {
                return Err(Error::TooDeep);
            }
            out.push('[');
            for (i, item) in items.iter().enumerate() {
                if i > 0 {
                    out.push(',');
                }
                write_value(item, out, depth + 1)?;
            }
            out.push(']');
        }
        Value::Object(fields) => write_object(fields, None, out, depth)?,
    }
    Ok(())
}

/// Writes an object with its keys in code-point order (the order of their
/// UTF-8 bytes), leaving out the key `skip`.
fn write_object(
    fields: &Map<String, Value>,
    skip: Option<&str>,
    out: &mut String,
    depth: usize,
) -> Result<(), Error> {
    if depth >= MAX_DEPTH {
        return Err(Error::TooDeep);
    }
    // Sorted here rather than trusting the map's own order, which depends on
    // serde_json's features.
    let mut keys: Vec<&String> = fields.keys().filter(|k| Some(k.as_str()) != skip).collect();
    keys.sort();
    out.push('{');
    for (i, key) in keys.into_iter().enumerate() {
        if i > 0 {
            out.push(',');
        }
        write_str(key, out);
        out.push(':');
        if let Some(value) = fields.get(key) {
            write_value(value, out, depth + 1)?;
        }
    }
    out.push('}');
    Ok(())
}

fn write_str(s: &str, out: &mut String) {
    out.push('"');
    for c in s.chars() {
        match c {
            '"' => out.push_str("\\\""),
            '\\' => out.push_str("\\\\"),
            '\n' => out.push_str("\\n"),
            '\r' => out.push_str("\\r"),
            '\t' => out.push_str("\\t"),
            '\u{8}' => out.push_str("\\b"),
            '\u{c}' => out.push_str("\\f"),
            ' '..='~' => out.push(c),
            _ => {
                let mut units = [0u16; 2];
                for unit in c.encode_utf16(&mut units) {
                    out.push_str("\\u");
                    for shift in [12, 8, 4, 0] {
                        out.push(nibble((*unit >> shift) & 0xf));
                    }
                }
            }
        }
    }
    out.push('"');
}

fn hex(bytes: &[u8]) -> String {
    let mut out = String::with_capacity(bytes.len() * 2);
    for byte in bytes {
        out.push(nibble(u16::from(byte >> 4)));
        out.push(nibble(u16::from(byte & 0xf)));
    }
    out
}

/// One lowercase hex digit (the value is always below 16).
fn nibble(n: u16) -> char {
    char::from_digit(u32::from(n), 16).unwrap_or('0')
}

// Tests may unwrap and index: a failure here is a failed test, not a
// world that crashed.
#[cfg(test)]
#[allow(clippy::unwrap_used, clippy::indexing_slicing)]
mod tests {
    use super::*;
    use serde_json::json;

    fn text(value: Value) -> String {
        python_json(&value).unwrap()
    }

    #[test]
    fn writes_like_python() {
        assert_eq!(text(json!(null)), "null");
        assert_eq!(text(json!([true, false])), "[true,false]");
        assert_eq!(text(json!({"b": 1, "a": [2, 3]})), r#"{"a":[2,3],"b":1}"#);
        assert_eq!(
            text(json!({"b": 0, "B": 0, "_": 0})),
            r#"{"B":0,"_":0,"b":0}"#
        );
        assert_eq!(text(json!(i64::MIN)), "-9223372036854775808");
        assert_eq!(text(json!(u64::MAX)), "18446744073709551615");
        assert_eq!(text(json!("a\"b\\c/")), r#""a\"b\\c/""#);
        assert_eq!(text(json!("\u{8}\u{c}\n\r\t")), r#""\b\f\n\r\t""#);
        assert_eq!(
            text(json!("\u{0}\u{1f} ~\u{7f}")),
            r#""\u0000\u001f ~\u007f""#
        );
        assert_eq!(text(json!("\u{e9}\u{4e2d}")), r#""\u00e9\u4e2d""#);
        assert_eq!(text(json!("\u{1f642}")), r#""\ud83d\ude42""#);
        assert_eq!(text(json!("\u{10ffff}")), r#""\udbff\udfff""#);
    }

    #[test]
    fn hashes_like_python() {
        // In Python: hashlib.sha256(b"{}").hexdigest()
        assert_eq!(
            digest(&json!({})).unwrap(),
            "44136fa355b3678a1146ad16f7e8649e94fb4fc21fe77e8310c060f61caaff8a"
        );
    }

    #[test]
    fn refuses_numbers_it_cannot_write_exactly() {
        assert_eq!(
            python_json(&json!({"x": [1.5]})),
            Err(Error::Number("1.5".into()))
        );
        assert!(python_json(&json!(1.0)).is_err());
        let big: Value = serde_json::from_str("18446744073709551616").unwrap();
        assert!(python_json(&big).is_err());
    }

    #[test]
    fn refuses_nesting_deeper_than_the_limit() {
        let mut deep = json!(0);
        for _ in 0..MAX_DEPTH {
            deep = json!([deep]);
        }
        assert!(python_json(&deep).is_ok());
        assert_eq!(python_json(&json!([deep])), Err(Error::TooDeep));
        assert_eq!(python_json(&json!({"k": deep})), Err(Error::TooDeep));
        let mut deepest_object = json!({});
        for _ in 0..MAX_DEPTH - 1 {
            deepest_object = json!([deepest_object]);
        }
        assert!(python_json(&deepest_object).is_ok());
        assert_eq!(python_json(&json!([deepest_object])), Err(Error::TooDeep));
    }
}

//! Writing a record the same way everywhere, before it is hashed or
//! signed: RFC 8785, written by `serde_jcs`, with three rules every record
//! keeps (docs/research/FORMATS.md): keys are ASCII; integers stay within
//! 2^53 - 1; no floats.

use serde_json::Value;

/// The largest integer a record may hold, and RFC 8785's own bound.
pub const MAX_INT: i64 = (1 << 53) - 1;

/// What breaks the rules in `value`, at which place (`$.a[0].b`), or
/// `None` if nothing does.
pub fn check(value: &Value) -> Option<String> {
    check_at(value, "$")
}

fn check_at(value: &Value, at: &str) -> Option<String> {
    match value {
        Value::Null | Value::Bool(_) | Value::String(_) => None,
        Value::Number(n) => {
            if let Some(i) = n.as_i64() {
                if (-MAX_INT..=MAX_INT).contains(&i) {
                    return None;
                }
                return Some(format!(
                    "{at}: integer beyond 2^53 - 1; write it as a string"
                ));
            }
            if n.is_u64() {
                return Some(format!(
                    "{at}: integer beyond 2^53 - 1; write it as a string"
                ));
            }
            Some(format!("{at}: a float; use an integer in a stated unit"))
        }
        Value::Array(items) => items
            .iter()
            .enumerate()
            .find_map(|(i, item)| check_at(item, &format!("{at}[{i}]"))),
        Value::Object(map) => map.iter().find_map(|(key, item)| {
            if !key.is_ascii() {
                return Some(format!("{at}: key {key:?} isn't ASCII"));
            }
            check_at(item, &format!("{at}.{key}"))
        }),
    }
}

/// The RFC 8785 bytes of `value`, which must keep the rules.
pub fn canonical(value: &Value) -> Result<Vec<u8>, String> {
    if let Some(problem) = check(value) {
        return Err(problem);
    }
    serde_jcs::to_vec(value).map_err(|e| e.to_string())
}

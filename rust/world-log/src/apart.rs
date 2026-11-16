// rust/world-log/src/apart.rs
//! A log whose fields are kept apart from the chain that commits to them
//! (course step 3b, part two; `docs/research/REDACTION.md`), in Rust
//! exactly as `world/apart.py` has it.
//!
//! In the kernel's log an entry's `data` is hashed whole, so nothing can
//! ever be taken out of it. In this form an entry holds, for each field
//! its world keeps apart, only a fingerprint; what the field says is kept
//! beside the log, in the contents. Taking a field out of the contents
//! leaves the log exactly as it was, and the chain still checks.
//!
//! - **The form's name** is [`FORM`]. A log names it in its first entry
//!   (`data.form`), which also holds the table (`data.kept_apart`): for
//!   each kind of entry, the names of the fields kept apart, in ascending
//!   order.
//! - **An entry** holds what the kernel's does, and `apart`: a map from a
//!   field's name to its fingerprint; these seven and nothing else, so
//!   nothing sits beside `data` where the table doesn't reach. A field the
//!   table keeps apart for an entry's kind is never in its `data`. The
//!   chain of a log in this form holds by
//!   [`verify_log`](crate::verify_log), unchanged.
//! - **The open part is held to the same rule as a value kept apart.**
//!   `tick` is a whole number from 0 to 2^53 - 1, `kind` is text, `agent`
//!   is text or nothing, and `data` is a map a fingerprint would allow.
//!   So every log in this form can be written, and checked, in both
//!   languages.
//! - **A fingerprint** ([`fingerprint`]) is the SHA-256, in lowercase hex,
//!   of the list `[salt, name, value]` as [`python_json`](crate::python_json)
//!   writes it. The salt is 32 lowercase hex digits, fresh for each field
//!   of each entry: 128 bits from the operating system, which the caller
//!   supplies, since this crate has no source of randomness. No
//!   fingerprint may appear twice in a log.
//! - **The contents** are a map from an entry's hash to a map from a
//!   field's name to `[salt, value]`.
//! - **Two kinds of entry are the form's own:** a mark ([`MARK`]), which
//!   names an earlier entry (`data.entry`) and a field it keeps apart
//!   (`data.field`); and a decision to keep a field public ([`KEPT`]),
//!   which names an earlier mark (`data.mark`), which then no longer
//!   stands.
//!
//! - **Four more kinds are the form's own,** for what a room shows: a
//!   removal ([`REMOVED`]), an office's, which names in the open an
//!   earlier entry (`data.entry`), the office (`data.office`), the ground
//!   it rests on (`data.ground`, a `kind` and a `ref`) and the hash of
//!   its decision record (`data.decision`); a restoring ([`RESTORED`]),
//!   which names a removal that stands (`data.incident`); a taking back
//!   ([`TAKEN_BACK`]), the author's own (`data.entry`); and a putting
//!   back ([`PUT_BACK`]), which undoes a taking back that stands
//!   (`data.taken_back`). None takes anything out of the log or the
//!   contents. What wins among them is in [`EntryState`] and
//!   `docs/research/REDACTION.md`, decision 9.
//!
//! [`check`] holds the contents to the log and gives every field's
//! [`State`]; [`incidents`] gives every entry's [`EntryState`]; [`join`]
//! gives each entry as a reader uses it; [`Log`] writes the form. Every reason for refusing ([`Refused::reason`]) is in
//! the same fixed words as in Python, checked against
//! `vectors/log-apart.json`.
//!
//! # Limits
//!
//! - A field under a standing mark is never shown by [`join`], even while
//!   it is still in the contents.
//! - An entry that is removed or taken back is still given whole by
//!   [`join`], with its state: nothing has left the record.
//! - This module does not check who may remove, restore or take back:
//!   that needs the signed records and the keys, which are kept apart.
//! - Nothing can be the value of an open field: a field with no value is
//!   left out.
//! - The check holds a world to its table by name: it can't know that an
//!   open field of another name holds what should have been kept apart.
//! - A fingerprint commits a log to a value, and says nothing of who
//!   wrote it: that is a signature's work.
//! - JSON's `-0` is read by Python as 0 and refused here, since
//!   `serde_json` reads it as a float. Nothing writes it.
//! - A file that isn't JSON as the standard has it (`NaN`, a number too
//!   large to read, half of a surrogate pair) is refused by Python's check
//!   and can't be read at all here.
//!
//! # The order of the checks
//!
//! It is part of the form, so that a log or contents with two faults is
//! refused for the same one in both languages. Entries are read in the
//! log's order; for each, its link to the entry before (`prev`), then
//! what it says, then its hash, so this crate is never asked to hash an
//! entry it could not write. The contents are read in ascending order of
//! entry hash, and of field name within an entry.

use crate::{GENESIS, LogError, body_hash, python_json, sha256_hex};
use serde_json::{Map, Value, json};
use std::collections::{BTreeMap, BTreeSet};
use std::fmt;

/// The form's name, in a log's first entry as `data.form`.
pub const FORM: &str = "open-worlds/log-apart/v1";
/// The kind of a mark: an entry that says a field was redacted.
pub const MARK: &str = "field_redacted";
/// The kind of a decision to keep a field public.
pub const KEPT: &str = "field_kept_public";
/// The kind of a removal: an office hides an entry, and says why.
pub const REMOVED: &str = "entry_removed";
/// The kind of a restoring: an office undoes a removal that stands.
pub const RESTORED: &str = "entry_restored";
/// The kind of a taking back: an author hides their own entry.
pub const TAKEN_BACK: &str = "entry_taken_back";
/// The kind of a putting back: an author undoes their own taking back.
pub const PUT_BACK: &str = "entry_put_back";
/// The form's own kinds: none of them can itself be removed or taken back.
pub const OWN: [&str; 6] = [MARK, KEPT, REMOVED, RESTORED, TAKEN_BACK, PUT_BACK];
/// What a ground can be, as in a decision record's grounds.
pub const GROUNDS: [&str; 4] = ["charter", "law", "rule", "record"];
/// The shortest an incident's id is ever shown, in hex digits.
pub const SHORT: usize = 12;
/// The largest whole number a fingerprint allows, 2^53 - 1; the smallest
/// is its negative.
pub const MAX_WHOLE: i64 = 9_007_199_254_740_991;
/// The deepest nesting of lists and maps in a value kept apart.
pub const MAX_NESTING: usize = 32;
/// The longest a ground's reference can be, in characters (code points),
/// as in a decision record's grounds.
pub const MAX_REF: usize = 512;
/// The keys of an entry in this form: these, and no others.
pub const KEYS: [&str; 7] = ["tick", "kind", "agent", "data", "apart", "prev", "hash"];

/// The state of one field kept apart, from the log and the contents
/// together.
#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord)]
pub enum State {
    /// In the contents, and never marked.
    Present,
    /// A mark stands, and the field is gone.
    Redacted,
    /// A mark stands, and the field is still there.
    Unfinished,
    /// Every mark on it was answered by a decision to keep it public, and
    /// it is there.
    KeptPublic,
    /// No mark stands, and it is gone: a fault in whoever published the
    /// log.
    Missing,
}

impl State {
    /// The state in the fixed words Python uses.
    pub fn as_str(self) -> &'static str {
        match self {
            State::Present => "present",
            State::Redacted => "redacted",
            State::Unfinished => "unfinished",
            State::KeptPublic => "kept public",
            State::Missing => "missing",
        }
    }

    /// True if [`join`] shows the field's value.
    pub fn shown(self) -> bool {
        matches!(self, State::Present | State::KeptPublic)
    }
}

impl fmt::Display for State {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.write_str(self.as_str())
    }
}

/// The state of an entry, worked out from the open fields alone: what a
/// room shows of it.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum EntryState {
    /// Never removed, and no taking back of it stands.
    AsWritten,
    /// A removal of it stands, and no taking back.
    Removed,
    /// A taking back of it stands, whatever an office has done.
    TakenBack,
    /// It was removed, and no removal or taking back of it stands now.
    Restored,
}

impl EntryState {
    /// The state in the fixed words Python uses.
    pub fn as_str(self) -> &'static str {
        match self {
            EntryState::AsWritten => "as written",
            EntryState::Removed => "removed",
            EntryState::TakenBack => "taken back",
            EntryState::Restored => "restored",
        }
    }
}

impl fmt::Display for EntryState {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.write_str(self.as_str())
    }
}

/// One removal or taking back of an entry.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct Incident {
    /// The hash of the entry that carries it: the incident's id.
    pub id: String,
    /// The id as it is shown: the fewest hex digits, [`SHORT`] or more,
    /// that no other incident in the log begins with.
    pub short: String,
    /// [`EntryState::Removed`] or [`EntryState::TakenBack`].
    pub kind: EntryState,
    /// Whether it still stands: not restored, or not put back.
    pub stands: bool,
}

/// An entry's state, and its incidents in the log's order.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct Standing {
    /// What a room shows of the entry.
    pub state: EntryState,
    /// Every removal and taking back of it, standing or not.
    pub incidents: Vec<Incident>,
}

/// Where in the contents something was refused: the entry's hash and the
/// field's name, as far as they are known.
#[derive(Debug, Clone, PartialEq, Eq, Default)]
pub struct Place {
    /// The hash of the entry the contents are for.
    pub entry: Option<String>,
    /// The name of the field.
    pub field: Option<String>,
}

impl Place {
    fn entry(entry: &str) -> Place {
        Place {
            entry: Some(entry.to_owned()),
            field: None,
        }
    }

    fn field(entry: &str, field: &str) -> Place {
        Place {
            entry: Some(entry.to_owned()),
            field: Some(field.to_owned()),
        }
    }
}

impl fmt::Display for Place {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match (&self.entry, &self.field) {
            (Some(entry), Some(field)) => write!(f, ": entry {entry}, field {field}"),
            (Some(entry), None) => write!(f, ": entry {entry}"),
            _ => Ok(()),
        }
    }
}

/// Why a log in this form, or its contents, does not hold. Entries are
/// counted from 0.
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum Refused {
    /// The chain does not hold, by [`verify_log`](crate::verify_log).
    Chain(LogError),
    /// The first entry does not name this form, or there is none.
    NoForm,
    /// The table of fields kept apart is not well formed.
    Table,
    /// An entry is not in this form: it doesn't hold exactly [`KEYS`], its
    /// open part isn't as the form has it (a tick from 0 to 2^53 - 1, a
    /// kind that is text, an agent that is text or nothing, data that is a
    /// map a fingerprint would allow), its `apart` isn't a map, or a name
    /// or fingerprint in `apart` isn't one.
    /// Also a field's name that isn't one, given to [`fingerprint`], which
    /// has no place in a log.
    Entry {
        /// The entry's place in the log, if it has one.
        index: Option<usize>,
    },
    /// An entry keeps apart a field the table does not name for its kind.
    Untabled {
        /// The entry's place in the log.
        index: usize,
    },
    /// A field the table keeps apart for an entry's kind is in its open
    /// data.
    Open {
        /// The entry's place in the log.
        index: usize,
    },
    /// A fingerprint appears twice in the log.
    Twice {
        /// The place of the entry that repeats it.
        index: usize,
    },
    /// A mark does not name an earlier entry and a field it keeps apart.
    BadMark {
        /// The mark's place in the log.
        index: usize,
    },
    /// A decision to keep a field public does not name an earlier mark.
    BadKept {
        /// The decision's place in the log.
        index: usize,
    },
    /// A removal does not name an earlier entry that can be removed (one
    /// that is not the form's own, and that no removal or taking back
    /// stands on), with its office, ground and decision.
    BadRemoval {
        /// The removal's place in the log.
        index: usize,
    },
    /// A restoring does not name a removal that stands, with its office,
    /// ground and decision.
    BadRestoring {
        /// The restoring's place in the log.
        index: usize,
    },
    /// A taking back does not name an earlier entry that can be taken
    /// back: one that is not the form's own, with no taking back standing.
    BadTakingBack {
        /// The taking back's place in the log.
        index: usize,
    },
    /// A putting back does not name a taking back that stands.
    BadPuttingBack {
        /// The putting back's place in the log.
        index: usize,
    },
    /// The contents are not a map of maps of `[salt, value]`.
    Contents(Place),
    /// The contents name an entry or a field the log does not keep apart.
    Unknown(Place),
    /// A salt is not 32 lowercase hex digits.
    Salt(Place),
    /// One salt was used for two fields.
    SaltTwice(Place),
    /// A value is not one a fingerprint allows.
    Value(Place),
    /// A field's salt and value do not give the fingerprint the log holds.
    Fingerprint(Place),
    /// Only when writing: the first entry's `form` and `kept_apart` are
    /// written by [`Log::new`], not given to it. (Python raises a
    /// `ValueError`.)
    FirstGiven,
}

impl Refused {
    /// The reason in fixed words, the same as `world/apart.py`'s
    /// `REASONS` for every reason Python has.
    pub fn reason(&self) -> &'static str {
        match self {
            Refused::Chain(_) => "the chain does not hold",
            Refused::NoForm => "the first entry does not name this form",
            Refused::Table => "the table of fields kept apart is not well formed",
            Refused::Entry { .. } => "an entry is not in this form",
            Refused::Untabled { .. } => "a field is kept apart that the table does not name",
            Refused::Open { .. } => "a field the table keeps apart is in the open",
            Refused::Twice { .. } => "a fingerprint appears twice",
            Refused::BadMark { .. } => {
                "a mark does not name an earlier entry and a field it keeps apart"
            }
            Refused::BadKept { .. } => {
                "a decision to keep a field public does not name an earlier mark"
            }
            Refused::BadRemoval { .. } => {
                "a removal does not name an earlier entry that can be removed, \
                 with its office, ground and decision"
            }
            Refused::BadRestoring { .. } => {
                "a restoring does not name a removal that stands, \
                 with its office, ground and decision"
            }
            Refused::BadTakingBack { .. } => {
                "a taking back does not name an earlier entry that can be taken back"
            }
            Refused::BadPuttingBack { .. } => {
                "a putting back does not name a taking back that stands"
            }
            Refused::Contents(_) => "the contents are not well formed",
            Refused::Unknown(_) => {
                "the contents name an entry or a field the log does not keep apart"
            }
            Refused::Salt(_) => "a salt is not 32 lowercase hex digits",
            Refused::SaltTwice(_) => "a salt appears twice",
            Refused::Value(_) => "a value is not one a fingerprint allows",
            Refused::Fingerprint(_) => "the contents do not match the fingerprint",
            Refused::FirstGiven => "the first entry's form and table are written here, not given",
        }
    }
}

impl fmt::Display for Refused {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.write_str(self.reason())?;
        match self {
            Refused::Chain(e) => write!(f, ": {e}"),
            Refused::Entry { index: Some(index) }
            | Refused::Untabled { index }
            | Refused::Open { index }
            | Refused::Twice { index }
            | Refused::BadMark { index }
            | Refused::BadKept { index }
            | Refused::BadRemoval { index }
            | Refused::BadRestoring { index }
            | Refused::BadTakingBack { index }
            | Refused::BadPuttingBack { index } => write!(f, ": entry {index}"),
            Refused::Contents(place)
            | Refused::Unknown(place)
            | Refused::Salt(place)
            | Refused::SaltTwice(place)
            | Refused::Value(place)
            | Refused::Fingerprint(place) => write!(f, "{place}"),
            Refused::NoForm
            | Refused::Table
            | Refused::Entry { index: None }
            | Refused::FirstGiven => Ok(()),
        }
    }
}

impl std::error::Error for Refused {}

/// The state of every field kept apart: from an entry's hash to a map
/// from a field's name to its state. Entries that keep nothing apart are
/// left out.
pub type States = BTreeMap<String, BTreeMap<String, State>>;

fn is_lower_hex(text: &str, digits: usize) -> bool {
    text.len() == digits && text.bytes().all(|b| matches!(b, b'0'..=b'9' | b'a'..=b'f'))
}

/// True for 32 lowercase hex digits.
fn is_salt(text: &str) -> bool {
    is_lower_hex(text, 32)
}

/// True for 64 lowercase hex digits.
fn is_hash(text: &str) -> bool {
    is_lower_hex(text, 64)
}

/// True for a field's name: a lowercase letter, then up to 63 lowercase
/// letters, digits or underscores.
fn is_name(text: &str) -> bool {
    let mut bytes = text.bytes();
    text.len() <= 64
        && matches!(bytes.next(), Some(b'a'..=b'z'))
        && bytes.all(|b| matches!(b, b'a'..=b'z' | b'0'..=b'9' | b'_'))
}

/// True if `value` may be kept apart: text, a whole number from
/// -(2^53 - 1) to 2^53 - 1, true or false, or a list or map of these,
/// nested at most [`MAX_NESTING`] deep.
pub fn value_allowed(value: &Value) -> bool {
    allowed(value, 0)
}

fn allowed(value: &Value, depth: usize) -> bool {
    match value {
        Value::Null => false,
        Value::Bool(_) | Value::String(_) => true,
        Value::Number(n) => n
            .as_i64()
            .is_some_and(|i| (-MAX_WHOLE..=MAX_WHOLE).contains(&i)),
        Value::Array(items) => depth < MAX_NESTING && items.iter().all(|v| allowed(v, depth + 1)),
        Value::Object(fields) => {
            depth < MAX_NESTING && fields.values().all(|v| allowed(v, depth + 1))
        }
    }
}

/// The exact text a fingerprint is the hash of: `[salt, name, value]` as
/// the log writes it.
pub fn fingerprint_text(salt: &str, name: &str, value: &Value) -> Result<String, Refused> {
    if !is_salt(salt) {
        return Err(Refused::Salt(Place::default()));
    }
    if !is_name(name) {
        return Err(Refused::Entry { index: None });
    }
    if !value_allowed(value) {
        return Err(Refused::Value(Place::default()));
    }
    // An allowed value can always be written: its numbers fit, and it is
    // nested far less deeply than the writer's limit.
    python_json(&json!([salt, name, value])).map_err(|_| Refused::Value(Place::default()))
}

/// The fingerprint of one field: the SHA-256, in lowercase hex, of
/// [`fingerprint_text`].
pub fn fingerprint(salt: &str, name: &str, value: &Value) -> Result<String, Refused> {
    Ok(sha256_hex(fingerprint_text(salt, name, value)?.as_bytes()))
}

/// Reads the table, if it is well formed: a map from a kind to a list of
/// names, each list in ascending order with no name twice.
fn read_table(table: Option<&Value>) -> Option<BTreeMap<String, Vec<String>>> {
    let mut read = BTreeMap::new();
    for (kind, names) in table?.as_object()? {
        let mut list: Vec<String> = Vec::new();
        for name in names.as_array()? {
            let name = name.as_str().filter(|n| is_name(n))?;
            if list.last().is_some_and(|last| last.as_str() >= name) {
                return None;
            }
            list.push(name.to_owned());
        }
        read.insert(kind.clone(), list);
    }
    Some(read)
}

/// Reads a log's entries in order, keeping what later entries and the
/// contents are checked against. `take` changes nothing unless the entry
/// holds, so a writer can offer it an entry and go on if it is refused.
#[derive(Debug, Clone, Default)]
struct Scan {
    table: BTreeMap<String, Vec<String>>,
    /// The hash of every entry, in the log's order.
    order: Vec<String>,
    /// For each entry, each field kept apart and its fingerprint.
    apart: BTreeMap<String, BTreeMap<String, String>>,
    /// For each mark, the entry and field it is on.
    marks: BTreeMap<String, (String, String)>,
    /// The marks that no longer stand.
    answered: BTreeSet<String>,
    /// Every fingerprint so far.
    seen: BTreeSet<String>,
    /// Each entry's kind.
    kinds: BTreeMap<String, String>,
    /// Every removal and taking back, in the log's order: the incident's
    /// entry, the entry it is on, and which of the two it is.
    incidents: Vec<(String, String, EntryState)>,
    /// For each removal, the entry it is on.
    removals: BTreeMap<String, String>,
    /// For each taking back, the entry it is on.
    takings: BTreeMap<String, String>,
    /// For each entry, the removal of it that stands.
    removed: BTreeMap<String, String>,
    /// For each entry, the taking back of it that stands.
    taken: BTreeMap<String, String>,
}

/// True if an office's act says, in the open, which office acted, the
/// ground it rests on, and the hash of its decision record. The ground
/// is one a decision record can hold: an earlier record is named by its
/// hash.
fn office_ok(data: &Map<String, Value>) -> bool {
    fn text(value: Option<&Value>) -> Option<&str> {
        value.and_then(Value::as_str).filter(|t| !t.is_empty())
    }
    let ground = data.get("ground").and_then(Value::as_object);
    text(data.get("office")).is_some() && ground.is_some_and(|g| {
        let kind = text(g.get("kind")).filter(|kind| GROUNDS.contains(kind));
        let reference = text(g.get("ref")).filter(|r| r.chars().count() <= MAX_REF);
        g.len() == 2
            && matches!((kind, reference), (Some(kind), Some(r)) if kind != "record" || is_hash(r))
    })
        && data
            .get("decision")
            .and_then(Value::as_str)
            .is_some_and(is_hash)
}

impl Scan {
    /// The hash of an earlier entry that is not one of the form's own, if
    /// `target` names one.
    fn can_be_acted_on<'a>(&self, target: Option<&'a Value>) -> Option<&'a str> {
        let target = target.and_then(Value::as_str)?;
        let kind = self.kinds.get(target)?;
        (!OWN.contains(&kind.as_str())).then_some(target)
    }

    fn take(&mut self, entry: &Value) -> Result<(), Refused> {
        let index = self.order.len();
        let shape = Refused::Entry { index: Some(index) };
        let fields = entry.as_object().ok_or(shape.clone())?;
        let data = fields.get("data").and_then(Value::as_object);
        let first_table = if index == 0 {
            let data = data
                .filter(|d| d.get("form").and_then(Value::as_str) == Some(FORM))
                .ok_or(Refused::NoForm)?;
            Some(read_table(data.get("kept_apart")).ok_or(Refused::Table)?)
        } else {
            None
        };
        let table = first_table.as_ref().unwrap_or(&self.table);
        let kind = fields.get("kind").and_then(Value::as_str);
        let apart = fields.get("apart").and_then(Value::as_object);
        // The callers have seen that `hash` is text, and see to the chain.
        let hash = fields.get("hash").and_then(Value::as_str);
        let (Some(kind), Some(data), Some(apart), Some(hash)) = (kind, data, apart, hash) else {
            return Err(shape);
        };
        if fields.len() != KEYS.len()
            || KEYS.iter().any(|key| !fields.contains_key(*key))
            || !open_ok(fields)
        {
            return Err(shape);
        }
        // BTreeMap: the names in ascending order, whatever order
        // serde_json keeps a map in.
        let mut prints: BTreeMap<String, String> = BTreeMap::new();
        for (name, print) in apart {
            let print = print.as_str().filter(|p| is_hash(p));
            match print {
                Some(print) if is_name(name) => prints.insert(name.clone(), print.to_owned()),
                _ => return Err(shape),
            };
        }
        let named: &[String] = table.get(kind).map_or(&[], Vec::as_slice);
        if prints.keys().any(|name| !named.contains(name)) {
            return Err(Refused::Untabled { index });
        }
        if named.iter().any(|name| data.contains_key(name)) {
            return Err(Refused::Open { index });
        }
        let distinct: BTreeSet<&String> = prints.values().collect();
        if distinct.len() != prints.len() || distinct.iter().any(|p| self.seen.contains(*p)) {
            return Err(Refused::Twice { index });
        }
        let mut mark = None;
        let mut answers = None;
        if kind == MARK {
            let target = data.get("entry").and_then(Value::as_str);
            let field = data.get("field").and_then(Value::as_str);
            match (target, field) {
                (Some(target), Some(field))
                    if self
                        .apart
                        .get(target)
                        .is_some_and(|held| held.contains_key(field)) =>
                {
                    mark = Some((target.to_owned(), field.to_owned()));
                }
                _ => return Err(Refused::BadMark { index }),
            }
        } else if kind == KEPT {
            match data.get("mark").and_then(Value::as_str) {
                Some(named_mark) if self.marks.contains_key(named_mark) => {
                    answers = Some(named_mark.to_owned());
                }
                _ => return Err(Refused::BadKept { index }),
            }
        }
        // What wins, among removing, restoring, taking back and putting
        // back (docs/research/REDACTION.md, decision 9).
        let mut on: Option<String> = None;
        if kind == REMOVED {
            match self.can_be_acted_on(data.get("entry")) {
                Some(target)
                    if !self.removed.contains_key(target)
                        && !self.taken.contains_key(target)
                        && office_ok(data) =>
                {
                    on = Some(target.to_owned());
                }
                _ => return Err(Refused::BadRemoval { index }),
            }
        } else if kind == RESTORED {
            let incident = data.get("incident").and_then(Value::as_str);
            let target = incident.and_then(|i| self.removals.get(i));
            match (incident, target) {
                (Some(incident), Some(target))
                    // Allowed while the author's taking back stands: the
                    // removal stops standing, and the entry stays taken
                    // back.
                    if self.removed.get(target).map(String::as_str) == Some(incident)
                        && office_ok(data) =>
                {
                    on = Some(target.clone());
                }
                _ => return Err(Refused::BadRestoring { index }),
            }
        } else if kind == TAKEN_BACK {
            match self.can_be_acted_on(data.get("entry")) {
                Some(target) if !self.taken.contains_key(target) => {
                    on = Some(target.to_owned());
                }
                _ => return Err(Refused::BadTakingBack { index }),
            }
        } else if kind == PUT_BACK {
            let taking = data.get("taken_back").and_then(Value::as_str);
            let target = taking.and_then(|t| self.takings.get(t));
            match (taking, target) {
                (Some(taking), Some(target))
                    if self.taken.get(target).map(String::as_str) == Some(taking) =>
                {
                    on = Some(target.clone());
                }
                _ => return Err(Refused::BadPuttingBack { index }),
            }
        }
        // The entry holds: only now is anything kept.
        let hash = hash.to_owned();
        self.seen.extend(prints.values().cloned());
        if let Some(table) = first_table {
            self.table = table;
        }
        if let Some(mark) = mark {
            self.marks.insert(hash.clone(), mark);
        }
        if let Some(answers) = answers {
            self.answered.insert(answers);
        }
        if let Some(on) = on {
            if kind == REMOVED {
                self.removals.insert(hash.clone(), on.clone());
                self.removed.insert(on.clone(), hash.clone());
                self.incidents.push((hash.clone(), on, EntryState::Removed));
            } else if kind == RESTORED {
                self.removed.remove(&on);
            } else if kind == TAKEN_BACK {
                self.takings.insert(hash.clone(), on.clone());
                self.taken.insert(on.clone(), hash.clone());
                self.incidents
                    .push((hash.clone(), on, EntryState::TakenBack));
            } else if kind == PUT_BACK {
                self.taken.remove(&on);
            }
        }
        self.kinds.insert(hash.clone(), kind.to_owned());
        self.apart.insert(hash.clone(), prints);
        self.order.push(hash);
        Ok(())
    }
}

/// True if an entry's open part is as the form has it: a tick from 0 to
/// 2^53 - 1, an agent that is text or nothing, and data that is a map a
/// fingerprint would allow. (That the kind is text is seen to where the
/// kind is read: by `take`, and by the writer's own types.)
fn open_ok(fields: &Map<String, Value>) -> bool {
    let tick = fields.get("tick").and_then(Value::as_u64);
    let agent = fields.get("agent");
    tick.is_some_and(|t| t <= MAX_WHOLE.unsigned_abs())
        && agent.is_some_and(|a| a.is_string() || a.is_null())
        && fields
            .get("data")
            .is_some_and(|d| d.is_object() && value_allowed(d))
}

/// Reads a whole log. For each entry in turn: its link to the entry
/// before, then what it says, then its hash. The chain is the kernel's (a
/// log that passes here passes [`verify_log`](crate::verify_log)); the
/// checks are taken an entry at a time so that the first fault in the
/// log's order is the one named, here and in Python.
fn scan(log: &Value) -> Result<Scan, Refused> {
    let entries = log.as_array().ok_or(Refused::Chain(LogError::NotAList))?;
    if entries.is_empty() {
        return Err(Refused::NoForm);
    }
    let mut scan = Scan::default();
    let mut prev = GENESIS;
    for (index, entry) in entries.iter().enumerate() {
        let malformed = Refused::Chain(LogError::Malformed { index });
        let fields = entry.as_object().ok_or(malformed.clone())?;
        let hash = fields
            .get("hash")
            .and_then(Value::as_str)
            .ok_or(malformed)?;
        if fields.get("prev").and_then(Value::as_str) != Some(prev) {
            return Err(Refused::Chain(LogError::BrokenChain { index }));
        }
        scan.take(entry)?;
        // An entry that holds can always be written: its numbers fit and
        // it is nested far less deeply than the writer's limit.
        if body_hash(fields).ok().as_deref() != Some(hash) {
            return Err(Refused::Chain(LogError::WrongHash { index }));
        }
        prev = hash;
    }
    Ok(scan)
}

/// The contents, held to the log: for each entry, each field's value that
/// is there and matches its fingerprint.
fn held<'a>(
    scan: &Scan,
    contents: &'a Value,
) -> Result<BTreeMap<&'a str, BTreeMap<&'a str, &'a Value>>, Refused> {
    let contents = contents
        .as_object()
        .ok_or(Refused::Contents(Place::default()))?;
    // Read in ascending order, so that Python and Rust refuse a contents
    // file with two faults for the same one.
    let sorted: BTreeMap<&str, &Value> = contents.iter().map(|(k, v)| (k.as_str(), v)).collect();
    let mut held = BTreeMap::new();
    let mut salts: BTreeSet<&str> = BTreeSet::new();
    for (entry, fields) in sorted {
        let prints = scan
            .apart
            .get(entry)
            .ok_or_else(|| Refused::Unknown(Place::entry(entry)))?;
        let fields = fields
            .as_object()
            .ok_or_else(|| Refused::Contents(Place::entry(entry)))?;
        let fields: BTreeMap<&str, &Value> = fields.iter().map(|(k, v)| (k.as_str(), v)).collect();
        let mut values = BTreeMap::new();
        for (name, pair) in fields {
            let place = || Place::field(entry, name);
            let print = prints.get(name).ok_or_else(|| Refused::Unknown(place()))?;
            let Some([salt, value]) = pair.as_array().map(Vec::as_slice) else {
                return Err(Refused::Contents(place()));
            };
            let salt = salt
                .as_str()
                .filter(|s| is_salt(s))
                .ok_or_else(|| Refused::Salt(place()))?;
            if !value_allowed(value) {
                return Err(Refused::Value(place()));
            }
            if fingerprint(salt, name, value).ok().as_ref() != Some(print) {
                return Err(Refused::Fingerprint(place()));
            }
            // Only once both match: so this always means a salt that was
            // truly used for two fields, never a field copied elsewhere.
            if !salts.insert(salt) {
                return Err(Refused::SaltTwice(place()));
            }
            values.insert(name, value);
        }
        held.insert(entry, values);
    }
    Ok(held)
}

fn states(scan: &Scan, held: &BTreeMap<&str, BTreeMap<&str, &Value>>) -> States {
    let marked: BTreeSet<&(String, String)> = scan.marks.values().collect();
    let standing: BTreeSet<&(String, String)> = scan
        .marks
        .iter()
        .filter(|(mark, _)| !scan.answered.contains(*mark))
        .map(|(_, field)| field)
        .collect();
    let mut states = States::new();
    for (entry, prints) in &scan.apart {
        for name in prints.keys() {
            let there = held
                .get(entry.as_str())
                .is_some_and(|values| values.contains_key(name.as_str()));
            let field = (entry.clone(), name.clone());
            let state = if standing.contains(&field) {
                if there {
                    State::Unfinished
                } else {
                    State::Redacted
                }
            } else if there {
                if marked.contains(&field) {
                    State::KeptPublic
                } else {
                    State::Present
                }
            } else {
                State::Missing
            };
            states
                .entry(entry.clone())
                .or_default()
                .insert(name.clone(), state);
        }
    }
    states
}

/// Each incident's id as it is shown: the fewest hex digits, [`SHORT`] or
/// more, that no other of `ids` begins with. The ids are 64 hex digits,
/// as an entry's hash is, so a beginning counted in bytes is counted in
/// characters. Sorted, an id shares its longest beginning with one of
/// its two neighbours, so each is held against those two alone. An id
/// is never cut longer than it is.
pub fn short_ids(ids: &[String]) -> BTreeMap<String, String> {
    fn shared(a: &str, b: &str) -> usize {
        a.bytes().zip(b.bytes()).take_while(|(x, y)| x == y).count()
    }
    let order: Vec<&String> = ids.iter().collect::<BTreeSet<_>>().into_iter().collect();
    let mut short = BTreeMap::new();
    for (i, one) in order.iter().enumerate() {
        let before = i.checked_sub(1).and_then(|j| order.get(j));
        let after = order.get(i + 1);
        let most = before
            .into_iter()
            .chain(after)
            .map(|other| shared(one, other))
            .max()
            .unwrap_or(0);
        let n = SHORT.max(most + 1);
        short.insert((*one).clone(), one.get(..n).unwrap_or(one).to_owned());
    }
    short
}

/// The state of every entry that has an incident, with them.
fn entry_states(scan: &Scan) -> BTreeMap<String, Standing> {
    let ids: Vec<String> = scan.incidents.iter().map(|(id, _, _)| id.clone()).collect();
    let short = short_ids(&ids);
    let mut states: BTreeMap<String, Standing> = BTreeMap::new();
    for (id, on, kind) in &scan.incidents {
        let stands = scan.removed.get(on) == Some(id) || scan.taken.get(on) == Some(id);
        states
            .entry(on.clone())
            .or_insert(Standing {
                state: EntryState::AsWritten,
                incidents: Vec::new(),
            })
            .incidents
            .push(Incident {
                id: id.clone(),
                short: short.get(id).cloned().unwrap_or_default(),
                kind: *kind,
                stands,
            });
    }
    for (on, standing) in &mut states {
        standing.state = if scan.taken.contains_key(on) {
            EntryState::TakenBack
        } else if scan.removed.contains_key(on) {
            EntryState::Removed
        } else if standing
            .incidents
            .iter()
            .any(|i| i.kind == EntryState::Removed)
        {
            EntryState::Restored
        } else {
            EntryState::AsWritten
        };
    }
    states
}

/// Checks a log in this form and gives the state of every entry that was
/// ever removed or taken back, with its incidents in the log's order.
/// Every other entry is as written. It needs no contents: what is shown
/// is worked out from the open fields alone.
pub fn incidents(log: &Value) -> Result<BTreeMap<String, Standing>, Refused> {
    Ok(entry_states(&scan(log)?))
}

/// Checks a log in this form and its contents together, and gives the
/// state of every field kept apart. Refuses if the chain doesn't hold,
/// the log isn't in this form, or the contents hold anything the log
/// doesn't commit to.
///
/// A missing field is not refused: it is a state, so that a reader can
/// say which fields a copy of a log has lost.
pub fn check(log: &Value, contents: &Value) -> Result<States, Refused> {
    let scan = scan(log)?;
    let held = held(&scan, contents)?;
    Ok(states(&scan, &held))
}

/// Each entry as a reader uses it, after [`check`]: the entry without its
/// `apart`, its `data` holding the open fields and every field kept apart
/// that is present or kept public, `fields` giving the state of each
/// field kept apart, and the entry's own `state` and `incidents`, all in
/// Python's words. A field under a standing mark is left out even if it
/// is still in the contents. An entry that is removed or taken back is
/// given whole: hiding it is for whatever shows the room.
pub fn join(log: &Value, contents: &Value) -> Result<Vec<Value>, Refused> {
    let scan = scan(log)?;
    let held = held(&scan, contents)?;
    let states = states(&scan, &held);
    let acted_on = entry_states(&scan);
    let entries = log.as_array().ok_or(Refused::Chain(LogError::NotAList))?;
    let none = BTreeMap::new();
    let mut joined = Vec::with_capacity(entries.len());
    for (entry, hash) in entries.iter().zip(&scan.order) {
        let mut one = entry.as_object().cloned().unwrap_or_default();
        one.remove("apart");
        let fields = states.get(hash).unwrap_or(&none);
        let mut shown = Map::new();
        for (name, state) in fields {
            shown.insert(name.clone(), Value::String(state.as_str().to_owned()));
            let value = held
                .get(hash.as_str())
                .and_then(|values| values.get(name.as_str()));
            if let (true, Some(value), Some(Value::Object(data))) =
                (state.shown(), value, one.get_mut("data"))
            {
                data.insert(name.clone(), (*value).clone());
            }
        }
        one.insert("fields".to_owned(), Value::Object(shown));
        let standing = acted_on.get(hash);
        let state = standing.map_or(EntryState::AsWritten, |s| s.state);
        let its: Vec<Value> = standing.map_or(Vec::new(), |s| {
            s.incidents
                .iter()
                .map(|i| {
                    json!({"id": i.id, "short": i.short, "kind": i.kind.as_str(),
                           "stands": i.stands})
                })
                .collect()
        });
        one.insert("state".to_owned(), json!(state.as_str()));
        one.insert("incidents".to_owned(), Value::Array(its));
        joined.push(Value::Object(one));
    }
    Ok(joined)
}

/// Writes a log in this form: the entries, which are the chain, and the
/// contents kept beside it. Every entry is offered to the same check a
/// reader runs before it is appended, so this never writes a log that
/// [`check`] would refuse.
///
/// The caller supplies the salts, one call for each field kept apart, in
/// the ascending order of the fields' names: 128 bits from the operating
/// system, as 32 lowercase hex digits, and never made from a world's
/// seed. The shared test vectors pass fixed salts, which are public to
/// everyone.
#[derive(Debug, Clone)]
pub struct Log {
    entries: Vec<Value>,
    contents: Map<String, Value>,
    scan: Scan,
    salts: BTreeSet<String>,
}

impl Log {
    /// Starts a log: its first entry, of kind `kind`, holds `data` with
    /// the form's name and `table` added. `table` gives, for each kind of
    /// entry, the names of the fields kept apart, in ascending order.
    pub fn new(
        table: &Value,
        data: &Map<String, Value>,
        kind: &str,
        salt: &mut dyn FnMut() -> String,
    ) -> Result<Log, Refused> {
        if data.contains_key("form") || data.contains_key("kept_apart") {
            return Err(Refused::FirstGiven);
        }
        // Before the entry is looked at as a whole, as the check does: so
        // a table that isn't one is refused as that, whatever it holds.
        if read_table(Some(table)).is_none() {
            return Err(Refused::Table);
        }
        let mut first = data.clone();
        first.insert("form".to_owned(), Value::String(FORM.to_owned()));
        first.insert("kept_apart".to_owned(), table.clone());
        let mut log = Log {
            entries: Vec::new(),
            contents: Map::new(),
            scan: Scan::default(),
            salts: BTreeSet::new(),
        };
        log.append(0, kind, None, &first, &Map::new(), salt)?;
        Ok(log)
    }

    /// The entries: the chain.
    pub fn entries(&self) -> &[Value] {
        &self.entries
    }

    /// The contents: for each entry that keeps fields apart, each field's
    /// `[salt, value]`.
    pub fn contents(&self) -> &Map<String, Value> {
        &self.contents
    }

    /// The hash of the last entry.
    pub fn head(&self) -> &str {
        self.scan.order.last().map_or(GENESIS, String::as_str)
    }

    /// The entries and the contents, to keep or to publish.
    pub fn into_parts(self) -> (Vec<Value>, Map<String, Value>) {
        (self.entries, self.contents)
    }

    /// Appends one entry and returns its hash. `data` holds the open
    /// fields, `apart` the fields kept apart, by name. Refuses, and
    /// appends nothing, if the entry would not hold.
    pub fn append(
        &mut self,
        tick: u64,
        kind: &str,
        agent: Option<&str>,
        data: &Map<String, Value>,
        apart: &Map<String, Value>,
        salt: &mut dyn FnMut() -> String,
    ) -> Result<String, Refused> {
        let index = self.entries.len();
        let mut body = Map::new();
        body.insert("tick".to_owned(), json!(tick));
        body.insert("kind".to_owned(), json!(kind));
        body.insert("agent".to_owned(), json!(agent));
        body.insert("data".to_owned(), Value::Object(data.clone()));
        // Before any salt is drawn or anything is hashed.
        if !open_ok(&body) {
            return Err(Refused::Entry { index: Some(index) });
        }
        let sorted: BTreeMap<&String, &Value> = apart.iter().collect();
        let mut prints = Map::new();
        let mut kept = Map::new();
        let mut salts = BTreeSet::new();
        for (name, value) in sorted {
            let salt = salt();
            if !is_salt(&salt) {
                return Err(Refused::Salt(Place::default()));
            }
            if self.salts.contains(&salt) || salts.contains(&salt) {
                return Err(Refused::SaltTwice(Place::default()));
            }
            let print = fingerprint(&salt, name, value)?;
            prints.insert(name.clone(), Value::String(print));
            kept.insert(name.clone(), json!([salt, value]));
            salts.insert(salt);
        }
        body.insert("apart".to_owned(), Value::Object(prints));
        body.insert("prev".to_owned(), json!(self.head()));
        let hash = body_hash(&body).map_err(|_| Refused::Entry { index: Some(index) })?;
        body.insert("hash".to_owned(), Value::String(hash.clone()));
        let entry = Value::Object(body);
        self.scan.take(&entry)?;
        self.entries.push(entry);
        self.salts.extend(salts);
        if !kept.is_empty() {
            self.contents.insert(hash.clone(), Value::Object(kept));
        }
        Ok(hash)
    }
}

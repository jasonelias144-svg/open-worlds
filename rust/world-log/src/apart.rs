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
//!   of the list `[salt, name, value]` as [`python_json`]
//!   writes it. The salt is 32 lowercase hex digits, fresh for each field
//!   of each entry: 128 bits from the operating system, which the caller
//!   supplies, since this crate has no source of randomness. No
//!   fingerprint may appear twice in a log.
//! - **The contents** are a map from an entry's hash to a map from a
//!   field's name to `[salt, value]`.
//! - **Three kinds of entry are the form's own, for a redacted field:**
//!   a mark ([`MARK`]), which names an earlier entry (`data.entry`) and
//!   a field it keeps apart (`data.field`), with the office that marked
//!   it (`data.office`) and the ground it rests on (`data.ground`, a
//!   `kind` and a `ref`); a decision to keep the field public
//!   ([`KEPT`]); and a decision that it stays redacted ([`STAYS`]). A
//!   decision names an open mark (`data.mark`), its office, its ground
//!   and the hash of its decision record (`data.decision`). Redacted
//!   first, decided after: a field has at most one mark that is open or
//!   stands; a mark is answered once; kept public, the field may be
//!   marked again; a mark that stays redacted stands for good, and
//!   nothing in the log makes that field public again.
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
//! - **What the form's own kinds say in the open is fixed** ([`SAYS`]):
//!   each holds exactly the keys named above for it, and nothing else.
//!   So a mark can hold no decision, and nothing beside its ground about
//!   what was redacted. What else such an entry carries is kept apart,
//!   as the table allows. And no table can keep one of those keys apart:
//!   a table that did would make every mark, or every decision,
//!   impossible to write.
//!
//! [`check`] holds the contents to the log and gives every field's
//! [`State`]; [`incidents`] gives every entry's [`EntryState`];
//! [`redactions`] gives every field's redactions, each open, standing
//! or kept public; [`join`] gives each entry as a reader uses it;
//! [`Log`] writes the form, a redaction through [`Log::mark`],
//! [`Log::take_out`], [`Log::keep_public`] and [`Log::stays_redacted`];
//! [`Log::open`] opens a writer on a log and contents that were written
//! before.
//! Every reason for refusing ([`Refused::reason`]) is in the same fixed
//! words as in Python, checked against `vectors/log-apart.json`.
//!
//! # Limits
//!
//! - A field under a mark that is open or stands is never shown by
//!   [`join`], even while it is still in the contents.
//! - An entry that is removed or taken back is still given whole by
//!   [`join`], with its state: nothing has left the record.
//! - This module does not check who may redact, decide, remove, restore
//!   or take back: that needs the signed records and the keys, which are
//!   kept apart. Nor does it seal what is redacted: that is the act of
//!   redacting, beside this module.
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
/// The kind of a decision that a field stays redacted.
pub const STAYS: &str = "field_stays_redacted";
/// The kind of a removal: an office hides an entry, and says why.
pub const REMOVED: &str = "entry_removed";
/// The kind of a restoring: an office undoes a removal that stands.
pub const RESTORED: &str = "entry_restored";
/// The kind of a taking back: an author hides their own entry.
pub const TAKEN_BACK: &str = "entry_taken_back";
/// The kind of a putting back: an author undoes their own taking back.
pub const PUT_BACK: &str = "entry_put_back";
/// The form's own kinds: none of them can itself be removed or taken back.
pub const OWN: [&str; 7] = [MARK, KEPT, STAYS, REMOVED, RESTORED, TAKEN_BACK, PUT_BACK];
/// What each of the form's own kinds says in the open: exactly these
/// keys. No table can keep one of them apart.
pub const SAYS: [(&str, &[&str]); 7] = [
    (MARK, &["entry", "field", "office", "ground"]),
    (KEPT, &["mark", "office", "ground", "decision"]),
    (STAYS, &["mark", "office", "ground", "decision"]),
    (REMOVED, &["entry", "office", "ground", "decision"]),
    (RESTORED, &["incident", "office", "ground", "decision"]),
    (TAKEN_BACK, &["entry"]),
    (PUT_BACK, &["taken_back"]),
];
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
    /// A mark on it is open or stands, and the field is gone.
    Redacted,
    /// A mark on it is open or stands, and the field is still there.
    Unfinished,
    /// Every mark on it was answered by a decision to keep it public, and
    /// it is there.
    KeptPublic,
    /// No mark on it is open or stands, and it is gone: a fault in
    /// whoever published the log.
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

/// What became of a redaction: of a mark, and the entry that answered it.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash)]
pub enum RedactionState {
    /// Marked, and not decided yet.
    Open,
    /// Decided: the field stays redacted, and nothing answers the mark
    /// again.
    Stands,
    /// Decided: the field is kept public, and may be marked again.
    KeptPublic,
}

impl RedactionState {
    /// The state in Python's words.
    pub fn as_str(self) -> &'static str {
        match self {
            RedactionState::Open => "open",
            RedactionState::Stands => "stands",
            RedactionState::KeptPublic => "kept public",
        }
    }
}

impl fmt::Display for RedactionState {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.write_str(self.as_str())
    }
}

/// One redaction of a field.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct Redaction {
    /// The hash of its mark: the redaction's id.
    pub id: String,
    /// The id as it is shown: the fewest hex digits, [`SHORT`] or more,
    /// that no other redaction or incident in the log begins with.
    pub short: String,
    /// Open, standing, or answered by a decision to keep the field public.
    pub state: RedactionState,
}

/// Every field's redactions, in the log's order: from an entry's hash to
/// a map from a field's name to its redactions.
pub type Redactions = BTreeMap<String, BTreeMap<String, Vec<Redaction>>>;

/// What an office's act says in the open: which office acted, and the
/// ground it rests on (a `kind` and a `ref`).
#[derive(Debug, Clone, Copy)]
pub struct Office<'a> {
    /// The office that acted.
    pub office: &'a str,
    /// The ground: why in general terms, never what.
    pub ground: &'a Value,
    /// The entry's agent, if it names one: who acted for the office.
    pub agent: Option<&'a str>,
}

/// What a decision says in the open: its office, its ground, and the
/// hash of its decision record.
#[derive(Debug, Clone, Copy)]
pub struct Decided<'a> {
    /// The office that decided.
    pub office: &'a str,
    /// The ground the decision rests on.
    pub ground: &'a Value,
    /// The hash of the decision record: 64 lowercase hex digits.
    pub decision: &'a str,
    /// The entry's agent, if it names one: who decided for the office.
    pub agent: Option<&'a str>,
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
    /// A mark does not name an earlier entry and a field it keeps apart
    /// that is free to be marked (no mark on it is open or stands), with
    /// its office and ground.
    BadMark {
        /// The mark's place in the log.
        index: usize,
    },
    /// A decision to keep a field public does not name an open mark,
    /// with its office, ground and decision.
    BadKept {
        /// The decision's place in the log.
        index: usize,
    },
    /// A decision that a field stays redacted does not name an open
    /// mark, with its office, ground and decision.
    BadStays {
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
    /// Only when writing: a mark and the decision that answers it are
    /// written by [`Log::mark`], [`Log::keep_public`] and
    /// [`Log::stays_redacted`], not by [`Log::append`]. (Python raises a
    /// `ValueError`.)
    NotByAppend,
    /// Only when writing: no mark of that hash is open or stands, so
    /// nothing is taken out. (Python raises a `ValueError`.)
    NoSuchMark,
    /// Only when writing: the field to take out is not in the contents.
    /// (Python raises a `ValueError`.)
    NotThere,
    /// Only when writing: the field is still in the contents, so it can't
    /// be said to stay redacted. (Python raises a `ValueError`.)
    StillThere,
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
                "a mark does not name an earlier entry and a field it keeps apart \
                 that is free to be marked, with its office and ground"
            }
            Refused::BadKept { .. } => {
                "a decision to keep a field public does not name an open mark, \
                 with its office, ground and decision"
            }
            Refused::BadStays { .. } => {
                "a decision that a field stays redacted does not name an open mark, \
                 with its office, ground and decision"
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
            Refused::NotByAppend => {
                "a mark and the decision that answers it are written by mark, \
                 keep_public and stays_redacted"
            }
            Refused::NoSuchMark => "no mark of that hash is open or stands",
            Refused::NotThere => "the field is not in the contents",
            Refused::StillThere => "the field is still in the contents: take it out first",
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
            | Refused::BadStays { index }
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
            | Refused::FirstGiven
            | Refused::NotByAppend
            | Refused::NoSuchMark
            | Refused::NotThere
            | Refused::StillThere => Ok(()),
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
        // What one of the form's own kinds says in the open can't be
        // kept apart: no such entry could then be written.
        if says(kind).is_some_and(|keys| list.iter().any(|n| keys.contains(&n.as_str()))) {
            return None;
        }
        read.insert(kind.clone(), list);
    }
    Some(read)
}

/// What a writer remembers of a salt it has used: its hash. Enough to
/// refuse a source that repeats, and nothing a fingerprint could be
/// guessed with.
fn used(salt: &str) -> String {
    sha256_hex(salt.as_bytes())
}

/// The keys one of the form's own kinds says in the open, if `kind` is
/// one of them.
fn says(kind: &str) -> Option<&'static [&'static str]> {
    SAYS.iter().find(|(k, _)| *k == kind).map(|(_, keys)| *keys)
}

/// True if an entry of one of the form's own kinds holds, in the open,
/// exactly the keys its kind says.
fn says_only(kind: &str, data: &Map<String, Value>) -> bool {
    says(kind).is_some_and(|keys| {
        data.len() == keys.len() && keys.iter().all(|key| data.contains_key(*key))
    })
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
    /// The marks answered by a decision to keep the field public.
    answered: BTreeSet<String>,
    /// The marks that stand for good.
    stays: BTreeSet<String>,
    /// For each field, its mark that is open or stands, if any.
    marked: BTreeMap<(String, String), String>,
    /// Every mark, in the log's order.
    redactions: Vec<String>,
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

/// True if an office's act says, in the open, which office acted and
/// the ground it rests on. The ground is one a decision record can hold:
/// an earlier record is named by its hash.
fn office_and_ground_ok(data: &Map<String, Value>) -> bool {
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
}

/// True if an office's act says its office and its ground, and the hash
/// of its decision record.
fn office_ok(data: &Map<String, Value>) -> bool {
    office_and_ground_ok(data)
        && data
            .get("decision")
            .and_then(Value::as_str)
            .is_some_and(is_hash)
}

impl Scan {
    /// True if `mark` is a mark that nothing has answered yet.
    fn is_open(&self, mark: &str) -> bool {
        self.marks.contains_key(mark) && !self.answered.contains(mark) && !self.stays.contains(mark)
    }

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
                        .is_some_and(|held| held.contains_key(field))
                        && !self
                            .marked
                            .contains_key(&(target.to_owned(), field.to_owned()))
                        && office_and_ground_ok(data)
                        && says_only(kind, data) =>
                {
                    mark = Some((target.to_owned(), field.to_owned()));
                }
                _ => return Err(Refused::BadMark { index }),
            }
        } else if kind == KEPT || kind == STAYS {
            // Redacted first, decided after: one answer to a mark, and
            // only while it is open.
            match data.get("mark").and_then(Value::as_str) {
                Some(named_mark)
                    if self.is_open(named_mark) && office_ok(data) && says_only(kind, data) =>
                {
                    answers = Some(named_mark.to_owned());
                }
                _ if kind == KEPT => return Err(Refused::BadKept { index }),
                _ => return Err(Refused::BadStays { index }),
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
                        && office_ok(data)
                        && says_only(kind, data) =>
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
                        && office_ok(data)
                        && says_only(kind, data) =>
                {
                    on = Some(target.clone());
                }
                _ => return Err(Refused::BadRestoring { index }),
            }
        } else if kind == TAKEN_BACK {
            match self.can_be_acted_on(data.get("entry")) {
                Some(target) if !self.taken.contains_key(target) && says_only(kind, data) => {
                    on = Some(target.to_owned());
                }
                _ => return Err(Refused::BadTakingBack { index }),
            }
        } else if kind == PUT_BACK {
            let taking = data.get("taken_back").and_then(Value::as_str);
            let target = taking.and_then(|t| self.takings.get(t));
            match (taking, target) {
                (Some(taking), Some(target))
                    if self.taken.get(target).map(String::as_str) == Some(taking)
                        && says_only(kind, data) =>
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
            self.marked.insert(mark.clone(), hash.clone());
            self.marks.insert(hash.clone(), mark);
            self.redactions.push(hash.clone());
        }
        if let Some(answers) = answers {
            if kind == KEPT {
                if let Some(field) = self.marks.get(&answers) {
                    self.marked.remove(field);
                }
                self.answered.insert(answers);
            } else {
                self.stays.insert(answers);
            }
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

/// Every id a room may show, as it is shown: incidents and redactions
/// together, so that no two begin alike.
fn shown_ids(scan: &Scan) -> BTreeMap<String, String> {
    let ids: Vec<String> = scan
        .incidents
        .iter()
        .map(|(id, _, _)| id.clone())
        .chain(scan.redactions.iter().cloned())
        .collect();
    short_ids(&ids)
}

/// Every field's redactions, in the log's order.
fn redactions_of(scan: &Scan) -> Redactions {
    let short = shown_ids(scan);
    let mut found = Redactions::new();
    for mark in &scan.redactions {
        let Some((entry, name)) = scan.marks.get(mark) else {
            continue;
        };
        let state = if scan.answered.contains(mark) {
            RedactionState::KeptPublic
        } else if scan.stays.contains(mark) {
            RedactionState::Stands
        } else {
            RedactionState::Open
        };
        found
            .entry(entry.clone())
            .or_default()
            .entry(name.clone())
            .or_default()
            .push(Redaction {
                id: mark.clone(),
                short: short.get(mark).cloned().unwrap_or_default(),
                state,
            });
    }
    found
}

/// The state of every entry that has an incident, with them.
fn entry_states(scan: &Scan) -> BTreeMap<String, Standing> {
    let short = shown_ids(scan);
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

/// Checks a log in this form and gives every redaction in it: for each
/// entry and each field, that field's redactions in the log's order,
/// each open (marked, and not decided yet), standing (decided: it stays
/// redacted) or answered by a decision to keep the field public. It
/// needs no contents. Whether a redacted field is in fact gone is a
/// field's state, which [`check`] gives.
pub fn redactions(log: &Value) -> Result<Redactions, Refused> {
    Ok(redactions_of(&scan(log)?))
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
/// field kept apart, `redactions` giving each field's redactions, and
/// the entry's own `state` and `incidents`, all in Python's words. A
/// field under a mark that is open or stands is left out even if it is
/// still in the contents. An entry that is removed or taken back is
/// given whole: hiding it is for whatever shows the room.
pub fn join(log: &Value, contents: &Value) -> Result<Vec<Value>, Refused> {
    let scan = scan(log)?;
    let held = held(&scan, contents)?;
    let states = states(&scan, &held);
    let acted_on = entry_states(&scan);
    let redacted = redactions_of(&scan);
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
        let mut of_fields = Map::new();
        for (name, list) in redacted.get(hash).into_iter().flatten() {
            let list: Vec<Value> = list
                .iter()
                .map(|r| json!({"id": r.id, "short": r.short, "state": r.state.as_str()}))
                .collect();
            of_fields.insert(name.clone(), Value::Array(list));
        }
        one.insert("redactions".to_owned(), Value::Object(of_fields));
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

/// The open data of an entry that answers a mark.
fn answer(mark: &str, by: Decided<'_>) -> Map<String, Value> {
    let mut data = Map::new();
    data.insert("mark".to_owned(), json!(mark));
    data.insert("office".to_owned(), json!(by.office));
    data.insert("ground".to_owned(), by.ground.clone());
    data.insert("decision".to_owned(), json!(by.decision));
    data
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
    /// Every salt used, as its hash ([`used`]). A salt itself is kept in
    /// the contents only, and leaves with its field.
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
        log.write(0, kind, None, &first, &Map::new(), salt)?;
        Ok(log)
    }

    /// Opens a writer on a log and its contents as they were written
    /// before, to go on from the log's head. The two are checked together
    /// first, as [`check`] checks them: refuses, for the same reason and
    /// at the same place, if they do not hold.
    ///
    /// The writer keeps copies of both. An entry whose map of fields is
    /// empty is left out of the contents, as this writer leaves it. A
    /// field that is missing or unfinished is not refused: those are
    /// states, and the writer goes on from them. An unfinished redaction
    /// is finished with [`Log::take_out`], also one that was decided
    /// while its field was left in.
    ///
    /// What it can't know is the salt of a field that was taken out
    /// before. So a source of salts that repeats one of those is not
    /// refused here, as it is by the writer that used that salt. If such
    /// a field is kept public, the writer is given its salt, and
    /// remembers it from then on ([`Log::keep_public`]).
    pub fn open(log: &Value, contents: &Value) -> Result<Log, Refused> {
        let scan = scan(log)?;
        held(&scan, contents)?;
        let mut kept = Map::new();
        let mut salts = BTreeSet::new();
        for (entry, fields) in contents.as_object().into_iter().flatten() {
            let Some(fields) = fields.as_object().filter(|fields| !fields.is_empty()) else {
                continue;
            };
            for salt in fields
                .values()
                .filter_map(|pair| pair.get(0).and_then(Value::as_str))
            {
                salts.insert(used(salt));
            }
            kept.insert(entry.clone(), Value::Object(fields.clone()));
        }
        Ok(Log {
            entries: log.as_array().cloned().unwrap_or_default(),
            contents: kept,
            scan,
            salts,
        })
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
    ///
    /// A mark and the decision that answers it are not written here:
    /// [`Log::mark`], [`Log::keep_public`] and [`Log::stays_redacted`]
    /// write them, with the contents changed in the same step.
    pub fn append(
        &mut self,
        tick: u64,
        kind: &str,
        agent: Option<&str>,
        data: &Map<String, Value>,
        apart: &Map<String, Value>,
        salt: &mut dyn FnMut() -> String,
    ) -> Result<String, Refused> {
        if kind == MARK || kind == KEPT || kind == STAYS {
            return Err(Refused::NotByAppend);
        }
        self.write(tick, kind, agent, data, apart, salt)
    }

    /// Appends a mark on `field` of `entry` and returns its hash: the
    /// redaction's id. The field is still in the contents, so its state
    /// is unfinished until [`Log::take_out`]; it is never shown
    /// meanwhile. Whatever is sealed of it is sealed before this.
    pub fn mark(
        &mut self,
        tick: u64,
        entry: &str,
        field: &str,
        by: Office<'_>,
        apart: &Map<String, Value>,
        salt: &mut dyn FnMut() -> String,
    ) -> Result<String, Refused> {
        let mut data = Map::new();
        data.insert("entry".to_owned(), json!(entry));
        data.insert("field".to_owned(), json!(field));
        data.insert("office".to_owned(), json!(by.office));
        data.insert("ground".to_owned(), by.ground.clone());
        self.write(tick, MARK, by.agent, &data, apart, salt)
    }

    /// Takes the field under `mark` out of the contents and returns its
    /// `[salt, value]`, which this writer then keeps nowhere: neither in
    /// the entries, nor in the contents, nor in what it remembers of the
    /// salts it has used. The log itself is not touched.
    ///
    /// The mark is one that is open or stands. A writer that wrote the
    /// whole log never has a field left under a mark that stands, since
    /// [`Log::stays_redacted`] is refused while the field is there. A
    /// writer opened on a published log ([`Log::open`]) can: whoever
    /// published it may have left the field in.
    pub fn take_out(&mut self, mark: &str) -> Result<Value, Refused> {
        let (entry, field) = self
            .scan
            .marks
            .get(mark)
            .filter(|_| !self.scan.answered.contains(mark))
            .ok_or(Refused::NoSuchMark)?;
        let fields = self
            .contents
            .get_mut(entry)
            .and_then(Value::as_object_mut)
            .ok_or(Refused::NotThere)?;
        let pair = fields.remove(field).ok_or(Refused::NotThere)?;
        if fields.is_empty() {
            self.contents.remove(entry);
        }
        Ok(pair)
    }

    /// The decision to keep a field public: puts `pair`, the field's
    /// `[salt, value]` as [`Log::take_out`] gave it, back into the
    /// contents and appends the entry that answers `mark`, in one step,
    /// and returns that entry's hash. Refuses, and changes nothing, if
    /// the mark is not open, if the salt and value are not the ones the
    /// log commits to, or if the entry would not hold.
    pub fn keep_public(
        &mut self,
        tick: u64,
        mark: &str,
        pair: &Value,
        by: Decided<'_>,
        apart: &Map<String, Value>,
        salt: &mut dyn FnMut() -> String,
    ) -> Result<String, Refused> {
        let (entry, field) = self
            .scan
            .marks
            .get(mark)
            .filter(|_| self.scan.is_open(mark))
            .cloned()
            .ok_or(Refused::BadKept {
                index: self.entries.len(),
            })?;
        let place = Place::field(&entry, &field);
        let (its_salt, value) = match pair.as_array().map(Vec::as_slice) {
            Some([its_salt, value]) => (its_salt.as_str(), value),
            _ => return Err(Refused::Contents(place)),
        };
        let its_salt = its_salt
            .filter(|s| is_salt(s))
            .ok_or_else(|| Refused::Salt(place.clone()))?;
        if !value_allowed(value) {
            return Err(Refused::Value(place));
        }
        let print = fingerprint(its_salt, &field, value)?;
        if self
            .scan
            .apart
            .get(&entry)
            .and_then(|held| held.get(&field))
            != Some(&print)
        {
            return Err(Refused::Fingerprint(place));
        }
        // A log written elsewhere can hold two fields that truly share a
        // salt, with this one taken out: it holds as it stands, since the
        // taking out hides the repeat. Putting the field back would show
        // it, in contents the check refuses. No writer here writes such
        // a log.
        let held_elsewhere = self.contents.iter().any(|(other, fields)| {
            fields.as_object().is_some_and(|fields| {
                fields.iter().any(|(name, held)| {
                    (other != &entry || name != &field)
                        && held.get(0).and_then(Value::as_str) == Some(its_salt)
                })
            })
        });
        if held_elsewhere {
            return Err(Refused::SaltTwice(place));
        }
        // From here the writer knows this salt, and it is about to be in
        // the contents again. A writer that never closed remembers it
        // from when it drew it. One that was opened after the field was
        // taken out learns it now: before the entry draws salts of its
        // own, so that a source which repeats it is refused. If the
        // entry is refused the field stays out, and what was learned
        // here is forgotten again.
        let known = used(its_salt);
        let learned = self.salts.insert(known.clone());
        let kept = match self.write(tick, KEPT, by.agent, &answer(mark, by), apart, salt) {
            Ok(kept) => kept,
            Err(refused) => {
                if learned {
                    self.salts.remove(&known);
                }
                return Err(refused);
            }
        };
        if let Value::Object(fields) = self
            .contents
            .entry(entry)
            .or_insert_with(|| Value::Object(Map::new()))
        {
            fields.insert(field, pair.clone());
        }
        Ok(kept)
    }

    /// The decision that a field stays redacted: appends the entry that
    /// answers `mark` for good, and returns its hash. The field must be
    /// out of the contents already. Whoever held a copy for the decision
    /// deletes it when this is written.
    pub fn stays_redacted(
        &mut self,
        tick: u64,
        mark: &str,
        by: Decided<'_>,
        apart: &Map<String, Value>,
        salt: &mut dyn FnMut() -> String,
    ) -> Result<String, Refused> {
        if self.scan.is_open(mark) {
            let there = self.scan.marks.get(mark).is_some_and(|(entry, field)| {
                self.contents
                    .get(entry)
                    .and_then(Value::as_object)
                    .is_some_and(|fields| fields.contains_key(field))
            });
            if there {
                return Err(Refused::StillThere);
            }
        }
        self.write(tick, STAYS, by.agent, &answer(mark, by), apart, salt)
    }

    fn write(
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
            if self.salts.contains(&used(&salt)) || salts.contains(&salt) {
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
        self.salts.extend(salts.iter().map(|salt| used(salt)));
        if !kept.is_empty() {
            self.contents.insert(hash.clone(), Value::Object(kept));
        }
        Ok(hash)
    }
}

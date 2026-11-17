// rust/redact/src/lib.rs
//! The act of redacting a field of a log, and of deciding on it after
//! (course step 3b, part three; `docs/research/REDACTION.md`, decisions 4
//! and 5), as `world/redact.py` does it.
//!
//! Redacting is three things, in this order:
//!
//! 1. **The field is sealed.** Its `[salt, value]` goes into a signed
//!    record (`open-worlds/redacted-field/v1`, [`formats::records`]) that
//!    names the log, the entry and the field. One copy is made for each
//!    person the field is about and one for the office that decides,
//!    each naming the one it is for and sealed to them alone
//!    (`open-worlds/redacted/v1`, [`formats::sealed`]). Someone with no
//!    key gets no copy: none is kept for them.
//! 2. **The mark is appended** ([`world_log::apart`]): which entry and
//!    which field, by which office, and why in general terms, never what.
//! 3. **The field is taken out of the contents.** The log then holds
//!    neither the value nor its salt, anywhere.
//!
//! [`redact`] does the three. If a copy can't be made, nothing is marked.
//! If the mark is refused, nothing is taken out, and the copies made are
//! not given back. If the work stopped after the mark, the log shows a
//! field that is marked and still there, and [`finish`] seals it and
//! takes it out.
//!
//! Deciding comes after. The office that decides opens its copy, holds it
//! to the log and, to keep the field public, puts it back with the
//! decision in one step ([`keep_public`]). Or it decides that the field
//! stays redacted ([`stays_redacted`]), and deletes its copy.
//!
//! **What binds a copy to its place** is the log, not the signature.
//! Whoever opens a copy works out the field's fingerprint again from the
//! salt, the name and the value, and finds it in the entry the copy
//! names, in the log the copy names ([`held_to`]). A copy that does not
//! match is refused, whoever signed it.
//!
//! # Limits
//!
//! - This crate does not check who may redact or decide: that the office
//!   holds the grant it names is for the checks across records.
//! - It does not find a person's sealing key: the caller gives each key,
//!   as everywhere a record is sealed.
//! - It can't delete anything: that the office's copy is gone once a
//!   redaction stands is the office's word, until keys can be destroyed
//!   (course step 8a).
//! - A log is named by the hash of its first entry, which holds its form
//!   and its table. Two logs begun with the same first entry share that
//!   name. What no two logs share is an entry's hash, once a field with
//!   a fresh salt is behind it, and a copy names its entry.

use formats::multikey::did_key;
use formats::{proof, records, sealed};
use serde_json::{Map, Value, json};
use std::fmt;
use world_log::apart::{self, Decided, Log, RedactionState};

/// The format of a redacted field's record.
pub const FORMAT: &str = "open-worlds/redacted-field/v1";
/// The label a redacted field's record is sealed under.
pub const LABEL: &str = "open-worlds/redacted/v1";

/// Why a redaction can't be made, or a copy doesn't hold to its log.
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum Refused {
    /// The field is not in the contents.
    NotThere,
    /// A copy is asked for the same one twice.
    Twice,
    /// What is held to the log is not a redacted field's record.
    NotACopy,
    /// The copy names another log.
    OtherLog,
    /// The copy names an entry the log does not have.
    NoEntry,
    /// The copy names a field the entry does not keep apart.
    NoField,
    /// The copy is not what the log held.
    NotHeld,
    /// The copy is of another field than the mark's.
    OtherField,
    /// Not a mark that is open or stands.
    NoMark,
    /// The log's own refusal, as it is.
    Log(apart::Refused),
    /// A copy that can't be made or opened: the words are those of
    /// [`formats`]. (Python raises `formats.sealed.SealedError`.)
    Sealed(String),
}

/// Every reason of this crate's own, in Python's order.
pub const REASONS: [Refused; 9] = [
    Refused::NotThere,
    Refused::Twice,
    Refused::NotACopy,
    Refused::OtherLog,
    Refused::NoEntry,
    Refused::NoField,
    Refused::NotHeld,
    Refused::OtherField,
    Refused::NoMark,
];

impl Refused {
    /// The reason, in the same fixed words as Python's. For a log's own
    /// refusal it is the log's reason; for a sealed copy's, the words
    /// are not fixed, and this gives a general one.
    pub fn reason(&self) -> &'static str {
        match self {
            Refused::NotThere => "the field is not in the contents",
            Refused::Twice => "a copy is asked for the same one twice",
            Refused::NotACopy => "not a redacted field's record",
            Refused::OtherLog => "the copy names another log",
            Refused::NoEntry => "the copy names an entry the log does not have",
            Refused::NoField => "the copy names a field the entry does not keep apart",
            Refused::NotHeld => "the copy is not what the log held",
            Refused::OtherField => "the copy is of another field than the mark's",
            Refused::NoMark => "not a mark that is open or stands",
            Refused::Log(e) => e.reason(),
            Refused::Sealed(_) => "a copy can't be made or opened",
        }
    }
}

impl fmt::Display for Refused {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Refused::Log(e) => write!(f, "{e}"),
            Refused::Sealed(why) => write!(f, "{}: {why}", self.reason()),
            _ => f.write_str(self.reason()),
        }
    }
}

impl std::error::Error for Refused {}

impl From<apart::Refused> for Refused {
    fn from(e: apart::Refused) -> Refused {
        Refused::Log(e)
    }
}

/// The office that redacts: its name as the log shows it, its signing
/// key, and the hash of the grant it acts under.
#[derive(Debug, Clone, Copy)]
pub struct Office<'a> {
    /// The office's name, as the log shows it.
    pub name: &'a str,
    /// Its signing key: 32 bytes, Ed25519.
    pub secret: &'a [u8; 32],
    /// The hash of the grant it acts under.
    pub grant: &'a str,
}

impl Office<'_> {
    /// The office's did:key.
    pub fn key(&self) -> String {
        did_key(&proof::public_key(self.secret))
    }
}

/// One a copy is made for: their did:key, and the sealing key (32
/// bytes, X25519) that belongs to it.
#[derive(Debug, Clone, Copy)]
pub struct Recipient<'a> {
    /// Their did:key.
    pub key: &'a str,
    /// Their sealing key.
    pub sealing: &'a [u8; 32],
}

/// One who opens a copy: their did:key, and their sealing secret.
#[derive(Debug, Clone, Copy)]
pub struct Opener<'a> {
    /// Their did:key.
    pub key: &'a str,
    /// Their sealing secret: 32 bytes, X25519.
    pub sealing_secret: &'a [u8; 32],
}

/// What is redacted, when, why, and for whom copies are made.
#[derive(Debug, Clone, Copy)]
pub struct Act<'a> {
    /// The tick of the mark.
    pub tick: u64,
    /// The entry, by its hash.
    pub entry: &'a str,
    /// The field's name.
    pub field: &'a str,
    /// The ground: why in general terms, never what.
    pub ground: &'a Value,
    /// The time the copies are signed at.
    pub created: &'a str,
    /// Each person the field is about who has a key.
    pub about: &'a [Recipient<'a>],
    /// The office that decides.
    pub decider: Recipient<'a>,
    /// The mark's agent, if it names one.
    pub agent: Option<&'a str>,
    /// The mark's own fields kept apart, such as a reason.
    pub apart: &'a Map<String, Value>,
}

/// A decision on a mark: when, which mark, by which office, and the
/// decision's own fields kept apart.
#[derive(Debug, Clone, Copy)]
pub struct Answer<'a> {
    /// The tick of the decision.
    pub tick: u64,
    /// The mark it answers, by its hash.
    pub mark: &'a str,
    /// The office, its ground and the hash of its decision record.
    pub by: Decided<'a>,
    /// The decision's own fields kept apart, such as a reason.
    pub apart: &'a Map<String, Value>,
}

/// What [`redact`] gives back.
#[derive(Debug, Clone, PartialEq)]
pub struct Redaction {
    /// The mark's hash: the redaction's id.
    pub mark: String,
    /// The sealed copies for the persons the field is about, in the
    /// order asked.
    pub copies: Vec<Value>,
    /// The sealed copy for the office that decides.
    pub office_copy: Value,
}

/// What names a log: the hash of its first entry.
pub fn log_id(log: &[Value]) -> Option<&str> {
    log.first()?.get("hash")?.as_str()
}

/// A sealed copy of a field that is in the contents, for each one named
/// in `about` and then for `decider`. Changes nothing.
fn copies(
    log: &Log,
    entry: &str,
    field: &str,
    by: &Office<'_>,
    created: &str,
    to: &[Recipient<'_>],
) -> Result<Vec<Value>, Refused> {
    let pair = log
        .contents()
        .get(entry)
        .and_then(Value::as_object)
        .and_then(|fields| fields.get(field))
        .ok_or(Refused::NotThere)?;
    for (n, one) in to.iter().enumerate() {
        if to.iter().skip(n + 1).any(|other| other.key == one.key) {
            return Err(Refused::Twice);
        }
    }
    let id = log_id(log.entries()).ok_or(Refused::NotThere)?;
    let mut made = Vec::with_capacity(to.len());
    for one in to {
        let record = json!({
            "format": FORMAT,
            "office": {"key": by.key(), "grant": by.grant},
            "to": one.key,
            "log": id,
            "entry": entry,
            "field": field,
            "salt": pair.get(0),
            "value": pair.get(1),
        });
        let signed = proof::sign(&record, by.secret, created, "assertionMethod")
            .and_then(|signed| records::check(&signed).map(|_| signed))
            .map_err(|e| Refused::Sealed(format!("only a record that holds is sealed: {e}")))?;
        made.push(sealed::seal_record(&signed, one.sealing).map_err(Refused::Sealed)?);
    }
    Ok(made)
}

fn redaction(mark: String, mut made: Vec<Value>) -> Redaction {
    let office_copy = made.pop().unwrap_or(Value::Null);
    Redaction {
        mark,
        copies: made,
        office_copy,
    }
}

/// Redacts a field of an entry: seals it, marks it, takes it out.
///
/// Refuses, and changes nothing, if the field is not in the contents or
/// one is named twice ([`Refused::NotThere`], [`Refused::Twice`]); if a
/// copy can't be made ([`Refused::Sealed`]); or if the mark does not hold
/// ([`Refused::Log`]).
pub fn redact(
    log: &mut Log,
    act: &Act<'_>,
    by: &Office<'_>,
    salt: &mut dyn FnMut() -> String,
) -> Result<Redaction, Refused> {
    let mut to = act.about.to_vec();
    to.push(act.decider);
    let made = copies(log, act.entry, act.field, by, act.created, &to)?;
    let office = apart::Office {
        office: by.name,
        ground: act.ground,
        agent: act.agent,
    };
    let mark = log.mark(act.tick, act.entry, act.field, office, act.apart, salt)?;
    log.take_out(&mark)?;
    Ok(redaction(mark, made))
}

/// The entry and the field a mark names, if `mark` is one.
fn marked(log: &[Value], mark: &str) -> Option<(String, String)> {
    let entry = log.iter().find(|e| {
        e.get("hash").and_then(Value::as_str) == Some(mark)
            && e.get("kind").and_then(Value::as_str) == Some(apart::MARK)
    })?;
    let text = |key: &str| Some(entry.get("data")?.get(key)?.as_str()?.to_owned());
    Some((text("entry")?, text("field")?))
}

/// Finishes a redaction that stopped after its mark: seals the field,
/// which is still in the contents, and takes it out. The log is not
/// touched. Refuses if `mark` is not a mark that is open or stands
/// ([`Refused::NoMark`]), or its field is no longer in the contents
/// ([`Refused::NotThere`]).
pub fn finish(
    log: &mut Log,
    mark: &str,
    by: &Office<'_>,
    created: &str,
    about: &[Recipient<'_>],
    decider: Recipient<'_>,
) -> Result<Redaction, Refused> {
    let (entry, field) = marked(log.entries(), mark).ok_or(Refused::NoMark)?;
    let found = apart::redactions(&Value::Array(log.entries().to_vec()))?;
    let state = found
        .get(&entry)
        .and_then(|fields| fields.get(&field))
        .and_then(|list| list.iter().find(|r| r.id == mark))
        .map(|r| r.state);
    if !matches!(state, Some(RedactionState::Open | RedactionState::Stands)) {
        return Err(Refused::NoMark);
    }
    let mut to = about.to_vec();
    to.push(decider);
    let made = copies(log, &entry, &field, by, created, &to)?;
    log.take_out(mark)?;
    Ok(redaction(mark.to_owned(), made))
}

/// Holds a redacted field's record to a log: the log is in its form and
/// holds, the record names it, the entry is in it, the entry keeps that
/// field apart, and the salt, the name and the value give the
/// fingerprint the entry holds. It does not check the record's
/// signature: [`formats::records::check`] does, and opening a sealed copy
/// does.
pub fn held_to(record: &Value, log: &Value) -> Result<(), Refused> {
    apart::redactions(log)?;
    let entries = log.as_array().map_or(&[][..], Vec::as_slice);
    if record.get("format").and_then(Value::as_str) != Some(FORMAT) {
        return Err(Refused::NotACopy);
    }
    let named = |key: &str| record.get(key).and_then(Value::as_str);
    if named("log").is_none() || named("log") != log_id(entries) {
        return Err(Refused::OtherLog);
    }
    let entry = entries
        .iter()
        .find(|e| {
            named("entry").is_some() && e.get("hash").and_then(Value::as_str) == named("entry")
        })
        .ok_or(Refused::NoEntry)?;
    let field = named("field").ok_or(Refused::NoField)?;
    let kept = entry
        .get("apart")
        .and_then(|kept| kept.get(field))
        .and_then(Value::as_str)
        .ok_or(Refused::NoField)?;
    let print = named("salt")
        .zip(record.get("value"))
        .and_then(|(salt, value)| apart::fingerprint(salt, field, value).ok())
        .ok_or(Refused::NotHeld)?;
    if print != kept {
        return Err(Refused::NotHeld);
    }
    Ok(())
}

/// The record in a sealed copy, opened by the one it is for with their
/// sealing key, and held to `log`.
pub fn open_copy(envelope: &Value, opener: Opener<'_>, log: &Value) -> Result<Value, Refused> {
    let record = sealed::open_record(envelope, opener.sealing_secret, opener.key, LABEL)
        .map_err(Refused::Sealed)?;
    held_to(&record, log)?;
    Ok(record)
}

/// The decision to keep a field public, by the office that holds the
/// copy made for it: opens the copy, holds it to the log and to the mark,
/// and puts the field back with the decision in one step. Returns the
/// decision's entry's hash.
///
/// Refuses, and changes nothing, if `answer.mark` is not an open mark or
/// the decision does not hold ([`Refused::Log`]); if the copy does not
/// open ([`Refused::Sealed`]); or if it is not the field the mark is on,
/// or not what the log held.
pub fn keep_public(
    log: &mut Log,
    answer: &Answer<'_>,
    envelope: &Value,
    opener: Opener<'_>,
    salt: &mut dyn FnMut() -> String,
) -> Result<String, Refused> {
    let Some(where_) = marked(log.entries(), answer.mark) else {
        return Err(Refused::Log(apart::Refused::BadKept {
            index: log.entries().len(),
        }));
    };
    let record = open_copy(envelope, opener, &Value::Array(log.entries().to_vec()))?;
    let named = |key: &str| record.get(key).and_then(Value::as_str);
    if (named("entry"), named("field")) != (Some(where_.0.as_str()), Some(where_.1.as_str())) {
        return Err(Refused::OtherField);
    }
    let pair = json!([record.get("salt"), record.get("value")]);
    Ok(log.keep_public(
        answer.tick,
        answer.mark,
        &pair,
        answer.by,
        answer.apart,
        salt,
    )?)
}

/// The decision that a field stays redacted: appends it, and returns its
/// entry's hash. The office then deletes the copy made for it. This
/// function can't: that the copy is gone is the office's word.
pub fn stays_redacted(
    log: &mut Log,
    answer: &Answer<'_>,
    salt: &mut dyn FnMut() -> String,
) -> Result<String, Refused> {
    Ok(log.stays_redacted(answer.tick, answer.mark, answer.by, answer.apart, salt)?)
}

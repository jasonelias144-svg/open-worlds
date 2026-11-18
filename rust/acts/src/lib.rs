// rust/acts/src/lib.rs
//! Who may act on a log whose fields are kept apart, held to the signed
//! records (course step 3b, part four, the records' side;
//! `docs/research/REDACTION.md`, decisions 7 to 9), as `world/acts.py`
//! checks it, against the same vectors (`vectors/acts.json`).
//!
//! `world_log::apart` holds an act to its shape: what a removal, a
//! restoring, a taking back, a putting back and a decision on a
//! redaction say in the open, and what each can be done to. It can't say
//! who may do them. That needs the signed record each act carries, which
//! is kept apart like anything else a person gives, and the grants. This
//! crate holds every act in a log to its record:
//!
//! - **An office's act carries a decision record**
//!   (`open-worlds/decision/v1`), in the field `record`, kept apart. Four
//!   kinds of entry are an office's act and carry one: a removal, a
//!   restoring, the decision to keep a redacted field public, and the
//!   decision that it stays redacted. The record must hold as a record;
//!   its hash must be the one the entry names in the open; its kind of
//!   act must be the one the rules fix for that kind of entry
//!   ([`ACTS`]); the records it is on must be exactly the one thing the
//!   entry acts on; its office's key must be the office the entry shows;
//!   its first ground must be the ground the entry shows; and it can't
//!   be dated, by its tick, after the entry that carries it. A
//!   restoring's decision supersedes the removal's. A removal and a
//!   restoring name the one who wrote the entry among those they affect,
//!   where that key is still there to read.
//! - **The office must hold a grant for the act.** The grant the
//!   decision names must be among the grants given, hold as a record,
//!   name the office's key as its holder, allow that kind of act, be for
//!   this room, and have been in force when the decision was signed. If
//!   it narrows another grant, the one above must be among the grants
//!   given too, be held by the one who issued the grant below, and allow
//!   the same act, in this room, at that time; and so on, at most
//!   [`MAX_CHAIN`] grants, up to a grant that narrows nothing, which
//!   must come from the room's key.
//! - **An author's act carries a record of its own,** signed by the
//!   author (`open-worlds/taking-back/v1`, `open-worlds/putting-back/v1`).
//!   A taking back names the entry, and the putting back that last put
//!   that entry back, if there was one; a putting back names the taking
//!   back it undoes. The signer must be the one who wrote the entry: the
//!   key in the field the rules name for that kind of entry. If that key
//!   is no longer in the contents, the act is reported as held with its
//!   signer not checked; if the entry never held one, it is refused.
//! - **A decision is carried by one entry.** No two entries of a log
//!   name the same decision.
//! - **Which kinds of entry an act may be on** is for the room's rules.
//!   A field of one of the form's own entries can always be marked.
//! - **A mark carries no record.** Who marked is checked where the
//!   field's sealed copy is opened: [`office_may`] holds the office that
//!   signed a copy to its grant.
//!
//! The order of the checks is part of the form, so that a log with two
//! faults is refused for the same one here and in Python.
//!
//! Limits, as in `world/acts.py`. A world checks an act when it writes
//! the entry; a reader can make the check again only while the records
//! are still there. The room's key is the rules' word, until the room
//! signs its heads (course step 3c). A grant is held to be in force by
//! the time its decision says it was signed; nothing here revokes a
//! grant before its end. Only the path from the office's grant up to the
//! room is checked, for the one act. An author whose key was signed over
//! to a new one can't take back with the new key (course step 8a).
//! Nothing here writes a log.

use formats::records;
use serde_json::{Map, Value};
use std::collections::{BTreeMap, BTreeSet};
use std::fmt;
use world_log::apart::{self, KEPT, MARK, PUT_BACK, REMOVED, RESTORED, STAYS, TAKEN_BACK};

/// The field, kept apart, that holds an act's signed record.
pub const RECORD: &str = "record";
/// The format of a decision record.
pub const DECISION: &str = "open-worlds/decision/v1";
/// The format of a grant.
pub const GRANT: &str = "open-worlds/grant/v1";
/// The format of an author's taking back.
pub const TAKING_BACK: &str = "open-worlds/taking-back/v1";
/// The format of an author's putting back.
pub const PUTTING_BACK: &str = "open-worlds/putting-back/v1";
/// The format of a redacted field's record, which names its office and
/// grant as a decision does.
pub const COPY: &str = "open-worlds/redacted-field/v1";

/// The kinds of act the rules fix for a log in this form: for each kind
/// of entry that is an office's act, the kind of act its decision record
/// says, and its office's grant must allow. A mark carries no decision:
/// its kind of act is the one the grant of the office that redacts must
/// allow.
pub const ACTS: [(&str, &str); 5] = [
    (MARK, "redact-field"),
    (KEPT, "keep-field-public"),
    (STAYS, "keep-field-redacted"),
    (REMOVED, "remove-comment"),
    (RESTORED, "restore-comment"),
];
/// The author's own acts, which are no office's: the kind of entry, and
/// the format of the record the author signs.
pub const OWN_ACTS: [(&str, &str); 2] = [(TAKEN_BACK, TAKING_BACK), (PUT_BACK, PUTTING_BACK)];
/// The kinds of entry the rules say what they may be on.
pub const RULED: [&str; 3] = [MARK, REMOVED, TAKEN_BACK];
/// The longest chain of grants, from an office's own up to the room's.
pub const MAX_CHAIN: usize = 8;

/// What the check found for one act, held to its record.
#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord)]
pub enum State {
    /// The record is there and holds to its entry, and who acted was
    /// allowed to.
    Held,
    /// The record holds to its entry, and the key that wrote the entry
    /// is no longer in the contents, so the signer can't be checked.
    Unchecked,
    /// A mark on the record is open or stands: nothing can be held to it.
    Redacted,
    /// The record is gone with no mark: a fault in whoever published the
    /// log.
    Missing,
}

/// Every state, in Python's order.
pub const STATES: [State; 4] = [
    State::Held,
    State::Unchecked,
    State::Redacted,
    State::Missing,
];

impl State {
    /// The state in the fixed words Python uses.
    pub fn as_str(self) -> &'static str {
        match self {
            State::Held => "held",
            State::Unchecked => "held, signer not checked",
            State::Redacted => "record redacted",
            State::Missing => "record missing",
        }
    }
}

impl fmt::Display for State {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.write_str(self.as_str())
    }
}

/// Why an act is not allowed.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum Reason {
    /// The rules are not well formed, do not fit the log's table, or the
    /// grants are not a list.
    Rules,
    /// An act is on a kind of entry the rules do not allow it on.
    NotOn,
    /// A decision is named by two entries.
    Twice,
    /// An act carries no record.
    NoRecord,
    /// An act's record does not hold, or is of another kind.
    NotARecord,
    /// A decision is not the one its entry names.
    OtherHash,
    /// A decision is of another kind of act than its entry.
    OtherAct,
    /// A record is on another thing than its entry acts on.
    OtherEntry,
    /// A decision's office is not the one its entry shows.
    OtherOffice,
    /// A decision's first ground is not the one its entry shows.
    OtherGround,
    /// A decision is dated after the entry that carries it.
    Later,
    /// A restoring's decision does not supersede the removal's.
    NotSuperseding,
    /// A decision does not name the one who wrote the entry among those
    /// it affects.
    NotAffected,
    /// A grant named is not among the grants given.
    NoGrant,
    /// A grant named does not hold.
    BadGrant,
    /// An office does not hold the grant it names.
    NotHolder,
    /// A grant does not allow the act.
    NotAllowed,
    /// A grant is not for this room.
    Elsewhere,
    /// A grant was not in force when the record was signed.
    NotInForce,
    /// A grant was not issued by the holder of the grant it narrows.
    NotNarrowing,
    /// A grant that narrows nothing does not come from the room's key.
    NotRooms,
    /// A chain of grants is too long.
    TooDeep,
    /// A taking back does not follow the entry's last putting back.
    OtherPlace,
    /// A record is not signed by the one who wrote the entry.
    NotAuthor,
}

/// Every reason, in Python's order.
pub const REASONS: [Reason; 24] = [
    Reason::Rules,
    Reason::NotOn,
    Reason::Twice,
    Reason::NoRecord,
    Reason::NotARecord,
    Reason::OtherHash,
    Reason::OtherAct,
    Reason::OtherEntry,
    Reason::OtherOffice,
    Reason::OtherGround,
    Reason::Later,
    Reason::NotSuperseding,
    Reason::NotAffected,
    Reason::NoGrant,
    Reason::BadGrant,
    Reason::NotHolder,
    Reason::NotAllowed,
    Reason::Elsewhere,
    Reason::NotInForce,
    Reason::NotNarrowing,
    Reason::NotRooms,
    Reason::TooDeep,
    Reason::OtherPlace,
    Reason::NotAuthor,
];

impl Reason {
    /// The reason, in the same fixed words as Python's.
    pub fn as_str(self) -> &'static str {
        match self {
            Reason::Rules => {
                "the rules are not well formed, do not fit the log's table, or the grants are not a list"
            }
            Reason::NotOn => "an act is on a kind of entry the rules do not allow it on",
            Reason::Twice => "a decision is named by two entries",
            Reason::NoRecord => "an act carries no record",
            Reason::NotARecord => "an act's record does not hold, or is of another kind",
            Reason::OtherHash => "a decision is not the one its entry names",
            Reason::OtherAct => "a decision is of another kind of act than its entry",
            Reason::OtherEntry => "a record is on another thing than its entry acts on",
            Reason::OtherOffice => "a decision's office is not the one its entry shows",
            Reason::OtherGround => "a decision's first ground is not the one its entry shows",
            Reason::Later => "a decision is dated after the entry that carries it",
            Reason::NotSuperseding => "a restoring's decision does not supersede the removal's",
            Reason::NotAffected => {
                "a decision does not name the one who wrote the entry among those it affects"
            }
            Reason::NoGrant => "a grant named is not among the grants given",
            Reason::BadGrant => "a grant named does not hold",
            Reason::NotHolder => "an office does not hold the grant it names",
            Reason::NotAllowed => "a grant does not allow the act",
            Reason::Elsewhere => "a grant is not for this room",
            Reason::NotInForce => "a grant was not in force when the record was signed",
            Reason::NotNarrowing => "a grant was not issued by the holder of the grant it narrows",
            Reason::NotRooms => "a grant that narrows nothing does not come from the room's key",
            Reason::TooDeep => "a chain of grants is too long",
            Reason::OtherPlace => "a taking back does not follow the entry's last putting back",
            Reason::NotAuthor => "a record is not signed by the one who wrote the entry",
        }
    }
}

impl fmt::Display for Reason {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.write_str(self.as_str())
    }
}

/// Why a log's acts do not hold.
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum Refused {
    /// The log's own refusal, as it is: the log or its contents do not
    /// hold in their form.
    Log(apart::Refused),
    /// An act that is not allowed: the reason, and the place in the log,
    /// from 0, of the entry that carries it, when there is one.
    Act {
        /// Why.
        reason: Reason,
        /// The entry's place in the log.
        at: Option<usize>,
    },
}

impl Refused {
    /// The reason in fixed words: this crate's, or the log's own.
    pub fn reason(&self) -> &'static str {
        match self {
            Refused::Log(e) => e.reason(),
            Refused::Act { reason, .. } => reason.as_str(),
        }
    }

    /// The place in the log of the entry that carries the act, for an
    /// act that is not allowed and has one.
    pub fn at(&self) -> Option<usize> {
        match self {
            Refused::Log(_) => None,
            Refused::Act { at, .. } => *at,
        }
    }
}

impl fmt::Display for Refused {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Refused::Log(e) => write!(f, "{e}"),
            Refused::Act { reason, at: None } => f.write_str(reason.as_str()),
            Refused::Act {
                reason,
                at: Some(at),
            } => write!(f, "{reason}: {at}"),
        }
    }
}

impl std::error::Error for Refused {}

impl From<apart::Refused> for Refused {
    fn from(e: apart::Refused) -> Refused {
        Refused::Log(e)
    }
}

fn fault(reason: Reason, at: Option<usize>) -> Refused {
    Refused::Act { reason, at }
}

/// The value at `path` in `value`, if every step is there.
fn part<'a>(value: &'a Value, path: &[&str]) -> Option<&'a Value> {
    path.iter().try_fold(value, |v, key| v.get(*key))
}

/// The text at `path` in `value`.
fn text<'a>(value: &'a Value, path: &[&str]) -> Option<&'a str> {
    part(value, path)?.as_str()
}

/// True for a field's name, as a log's table holds one.
fn is_name(name: &str) -> bool {
    let mut bytes = name.bytes();
    name.len() <= 64
        && matches!(bytes.next(), Some(b'a'..=b'z'))
        && bytes.all(|b| matches!(b, b'a'..=b'z' | b'0'..=b'9' | b'_'))
}

/// True for an Ed25519 public key as a did:key.
fn is_did(key: &str) -> bool {
    key.strip_prefix("did:key:z6Mk").is_some_and(|rest| {
        rest.len() == 44
            && rest.bytes().all(|b| {
                matches!(b, b'1'..=b'9' | b'A'..=b'H' | b'J'..=b'N' | b'P'..=b'Z'
                    | b'a'..=b'k' | b'm'..=b'z')
            })
    })
}

/// The kinds in a list of kinds of entry, none of them the form's own,
/// in ascending order; nothing if it is not such a list.
fn kinds(list: &Value) -> Option<Vec<&str>> {
    let found: Vec<&str> = list
        .as_array()?
        .iter()
        .map(Value::as_str)
        .collect::<Option<_>>()?;
    let own = found.iter().any(|k| apart::OWN.contains(k));
    let ascending = found.iter().zip(found.iter().skip(1)).all(|(a, b)| a < b);
    (!own && ascending).then_some(found)
}

/// The rules, read: the room's key, who wrote each kind of entry, and
/// what a mark, a removal and a taking back may each be on.
struct Rules<'a> {
    room: &'a str,
    authors: BTreeMap<&'a str, &'a str>,
    on: BTreeMap<&'a str, Vec<&'a str>>,
}

fn read_rules(rules: &Value) -> Option<Rules<'_>> {
    let map = rules.as_object()?;
    if map.len() != 3 {
        return None;
    }
    let room = map.get("room")?.as_str().filter(|key| is_did(key))?;
    let mut authors = BTreeMap::new();
    for (kind, field) in map.get("authors")?.as_object()? {
        let field = field.as_str().filter(|name| is_name(name))?;
        if apart::OWN.contains(&kind.as_str()) {
            return None;
        }
        authors.insert(kind.as_str(), field);
    }
    let given = map.get("on")?.as_object()?;
    if given.len() != RULED.len() {
        return None;
    }
    let mut on = BTreeMap::new();
    for kind in RULED {
        on.insert(kind, kinds(given.get(kind)?)?);
    }
    let taken_back = on.get(TAKEN_BACK)?;
    if !taken_back.iter().all(|kind| authors.contains_key(kind)) {
        return None;
    }
    Some(Rules { room, authors, on })
}

/// True if `rules` are well formed: the room's did:key, the field that
/// holds the key that wrote each kind of entry, and the kinds of entry
/// a mark, a removal and a taking back may each be on. A kind that can
/// be taken back names who wrote it. Whether they fit a log's table is
/// checked with the log.
pub fn rules_ok(rules: &Value) -> bool {
    read_rules(rules).is_some()
}

/// The records given, each under its hash. What can't be hashed as a
/// record can't be named by one, and is left out.
fn by_hash(grants: &Value) -> Result<BTreeMap<String, &Value>, Refused> {
    let list = grants.as_array().ok_or(fault(Reason::Rules, None))?;
    let mut found = BTreeMap::new();
    for grant in list {
        if !grant.is_object() {
            continue;
        }
        if let Ok(hash) = records::record_hash(grant) {
            found.insert(hash, grant);
        }
    }
    Ok(found)
}

/// True if `record` is a record of `kind` that holds.
fn holds(record: &Value, kind: &str) -> bool {
    record.is_object() && text(record, &["format"]) == Some(kind) && records::check(record).is_ok()
}

/// Follows the office's grant up to the room's key. Each grant on the
/// way must hold, be held by the one below's issuer (the first, by the
/// office), allow the act, be for the room, and have been in force when
/// the record was signed.
fn may(
    record: &Value,
    act: &str,
    grants: &BTreeMap<String, &Value>,
    room: &str,
    at: Option<usize>,
) -> Result<(), Refused> {
    let not_a_record = fault(Reason::NotARecord, at);
    let mut name = text(record, &["office", "grant"]).ok_or(not_a_record.clone())?;
    let mut holder = text(record, &["office", "key"]).ok_or(not_a_record.clone())?;
    let signed = text(record, &["proof", "created"]).ok_or(not_a_record)?;
    for depth in 0..MAX_CHAIN {
        let grant = *grants.get(name).ok_or(fault(Reason::NoGrant, at))?;
        if !holds(grant, GRANT) {
            return Err(fault(Reason::BadGrant, at));
        }
        if text(grant, &["holder"]) != Some(holder) {
            let reason = if depth == 0 {
                Reason::NotHolder
            } else {
                Reason::NotNarrowing
            };
            return Err(fault(reason, at));
        }
        let allows = part(grant, &["allows"]).and_then(Value::as_array);
        if !allows.is_some_and(|list| list.iter().any(|a| a.as_str() == Some(act))) {
            return Err(fault(Reason::NotAllowed, at));
        }
        if text(grant, &["within"]) != Some(room) {
            return Err(fault(Reason::Elsewhere, at));
        }
        let begun = text(grant, &["validFrom"]).is_some_and(|from| from <= signed);
        let ended = text(grant, &["validUntil"]).is_some_and(|until| signed >= until);
        if !begun || ended {
            return Err(fault(Reason::NotInForce, at));
        }
        let issuer = text(grant, &["issuer"]).ok_or(fault(Reason::BadGrant, at))?;
        match text(grant, &["narrows"]) {
            None if issuer == room => return Ok(()),
            None => return Err(fault(Reason::NotRooms, at)),
            Some(above) => {
                name = above;
                holder = issuer;
            }
        }
    }
    Err(fault(Reason::TooDeep, at))
}

/// Holds the office that signed `record` to its grant, for `act`: a
/// decision, or a redacted field's record, whose act is the one
/// [`ACTS`] gives for a mark. The record must hold as a record. No log
/// is read, so a refusal names no place.
pub fn office_may(record: &Value, act: &str, grants: &Value, rules: &Value) -> Result<(), Refused> {
    let rules = read_rules(rules).ok_or(fault(Reason::Rules, None))?;
    let grants = by_hash(grants)?;
    let held = [DECISION, COPY].into_iter().any(|kind| holds(record, kind));
    if !held {
        return Err(fault(Reason::NotARecord, None));
    }
    may(record, act, &grants, rules.room, None)
}

/// Who wrote an entry, as far as it can be read.
enum Wrote<'a> {
    /// The entry holds no key at all.
    Never,
    /// The key is no longer in the contents.
    Gone,
    /// The key.
    There(&'a Value),
}

/// A log that holds in its form, with what the acts are held to.
struct Room<'a> {
    entries: BTreeMap<&'a str, &'a Value>,
    states: apart::States,
    contents: &'a Value,
    rules: Rules<'a>,
    grants: BTreeMap<String, &'a Value>,
}

impl<'a> Room<'a> {
    fn readable(&self, entry: &str, field: &str) -> bool {
        self.states
            .get(entry)
            .and_then(|fields| fields.get(field))
            .is_some_and(|state| state.shown())
    }

    /// What the contents hold for a field: its value, without its salt.
    fn held(&self, entry: &str, field: &str) -> Option<&'a Value> {
        part(self.contents, &[entry, field])?.get(1)
    }

    fn kind(&self, entry: &str) -> Option<&'a str> {
        text(self.entries.get(entry)?, &["kind"])
    }

    /// What one of the form's own entries says in the open under `key`.
    fn says(&self, entry: &str, key: &str) -> Option<&'a str> {
        text(self.entries.get(entry)?, &["data", key])
    }

    fn author(&self, entry: &str) -> Wrote<'a> {
        let field = self
            .kind(entry)
            .and_then(|kind| self.rules.authors.get(kind));
        let kept = self
            .entries
            .get(entry)
            .and_then(|e| part(e, &["apart"]))
            .and_then(Value::as_object);
        match (field, kept) {
            (Some(field), Some(kept)) if kept.contains_key(*field) => {
                match self.held(entry, field) {
                    Some(key) if self.readable(entry, field) => Wrote::There(key),
                    _ => Wrote::Gone,
                }
            }
            _ => Wrote::Never,
        }
    }
}

fn act_of(kind: &str) -> Option<&'static str> {
    ACTS.iter().find(|(k, _)| *k == kind).map(|(_, act)| *act)
}

fn own_format(kind: &str) -> Option<&'static str> {
    OWN_ACTS
        .iter()
        .find(|(k, _)| *k == kind)
        .map(|(_, format)| *format)
}

/// Holds an office's act to its decision record: `kind` is the entry's
/// kind, `data` what it says in the open, and `comment` the entry a
/// person wrote that the act is about, if it is about one.
fn office_holds(
    room: &Room<'_>,
    entry: &Value,
    record: &Value,
    comment: Option<&str>,
    at: Option<usize>,
) -> Result<(), Refused> {
    let no = |reason| fault(reason, at);
    let kind = text(entry, &["kind"]).ok_or(no(Reason::NotARecord))?;
    let act = act_of(kind).ok_or(no(Reason::NotARecord))?;
    let data = part(entry, &["data"]).ok_or(no(Reason::NotARecord))?;
    let target = match kind {
        REMOVED => data.get("entry"),
        RESTORED => data.get("incident"),
        _ => data.get("mark"),
    };
    if records::record_hash(record).ok().as_deref() != text(data, &["decision"]) {
        return Err(no(Reason::OtherHash));
    }
    if text(record, &["act", "kind"]) != Some(act) {
        return Err(no(Reason::OtherAct));
    }
    let on = part(record, &["act", "records"]).and_then(Value::as_array);
    if !on.is_some_and(|list| list.len() == 1 && list.first() == target) {
        return Err(no(Reason::OtherEntry));
    }
    if part(record, &["office", "key"]) != data.get("office") {
        return Err(no(Reason::OtherOffice));
    }
    let first = part(record, &["grounds"]).and_then(|g| g.get(0));
    if first.is_none() || first != data.get("ground") {
        return Err(no(Reason::OtherGround));
    }
    let dated = part(record, &["tick"]).and_then(Value::as_i64);
    let written = part(entry, &["tick"]).and_then(Value::as_i64);
    if !matches!((dated, written), (Some(d), Some(w)) if d <= w) {
        return Err(no(Reason::Later));
    }
    if kind == RESTORED {
        let removals = text(data, &["incident"]).and_then(|i| room.says(i, "decision"));
        if removals.is_none() || text(record, &["supersedes"]) != removals {
            return Err(no(Reason::NotSuperseding));
        }
    }
    if let Some(Wrote::There(wrote)) = comment.map(|c| room.author(c)) {
        let affects = part(record, &["affects"]).and_then(Value::as_array);
        if !affects.is_some_and(|list| list.contains(wrote)) {
            return Err(no(Reason::NotAffected));
        }
    }
    may(record, act, &room.grants, room.rules.room, at)
}

/// Checks a log in the form of `world_log::apart` and its contents,
/// then holds every act in it to its signed record, and every office to
/// its grant. Gives a map from the hash of each entry that carries a
/// record to its [`State`]. Refuses with the log's own reason if the log
/// or its contents do not hold, and for the first act, in the log's
/// order, that is not allowed.
pub fn check(
    log: &Value,
    contents: &Value,
    grants: &Value,
    rules: &Value,
) -> Result<BTreeMap<String, State>, Refused> {
    let states = apart::check(log, contents)?;
    let bad_rules = fault(Reason::Rules, None);
    let rules = read_rules(rules).ok_or(bad_rules.clone())?;
    let list = log.as_array().ok_or(bad_rules.clone())?;
    let no_table = Map::new();
    let table = list
        .first()
        .and_then(|first| part(first, &["data", "kept_apart"]))
        .and_then(Value::as_object)
        .unwrap_or(&no_table);
    let fits = rules.authors.iter().all(|(kind, field)| {
        table
            .get(*kind)
            .and_then(Value::as_array)
            .is_some_and(|names| names.iter().any(|n| n.as_str() == Some(*field)))
    });
    if !fits {
        return Err(bad_rules);
    }
    let grants = by_hash(grants)?;
    let mut entries = BTreeMap::new();
    for entry in list {
        if let Some(hash) = text(entry, &["hash"]) {
            entries.insert(hash, entry);
        }
    }
    let room = Room {
        entries,
        states,
        contents,
        rules,
        grants,
    };

    let mut found = BTreeMap::new();
    let mut named: BTreeSet<&str> = BTreeSet::new();
    let mut put_back: BTreeMap<&str, &str> = BTreeMap::new();
    for (index, entry) in list.iter().enumerate() {
        let at = Some(index);
        let no = |reason| fault(reason, at);
        let (Some(kind), Some(here)) = (text(entry, &["kind"]), text(entry, &["hash"])) else {
            continue;
        };
        if !apart::OWN.contains(&kind) {
            continue;
        }
        let says = |key: &str| text(entry, &["data", key]);
        if RULED.contains(&kind) {
            let on_kind = says("entry").and_then(|e| room.kind(e));
            let allowed = room.rules.on.get(kind);
            let ruled_out = on_kind.is_none_or(|k| {
                !apart::OWN.contains(&k) && !allowed.is_some_and(|list| list.contains(&k))
            });
            if ruled_out {
                return Err(no(Reason::NotOn));
            }
        }
        if kind == MARK {
            continue;
        }
        // The entry the act is, in the end, about: the one a person
        // wrote. A decision on a redaction is about a field, not an
        // entry's author.
        let comment = match kind {
            REMOVED | TAKEN_BACK => says("entry"),
            RESTORED => says("incident").and_then(|i| room.says(i, "entry")),
            PUT_BACK => says("taken_back").and_then(|t| room.says(t, "entry")),
            _ => None,
        };
        let after = if kind == TAKEN_BACK {
            comment.and_then(|c| put_back.get(c).copied())
        } else {
            None
        };
        if let (PUT_BACK, Some(comment)) = (kind, comment) {
            put_back.insert(comment, here);
        }
        if act_of(kind).is_some() {
            let decision = says("decision").ok_or(no(Reason::Twice))?;
            if !named.insert(decision) {
                return Err(no(Reason::Twice));
            }
        }
        let carries = part(entry, &["apart"])
            .and_then(Value::as_object)
            .is_some_and(|kept| kept.contains_key(RECORD));
        if !carries {
            return Err(no(Reason::NoRecord));
        }
        let record = match room.held(here, RECORD) {
            Some(record) if room.readable(here, RECORD) => record,
            _ => {
                let missing = room
                    .states
                    .get(here)
                    .and_then(|fields| fields.get(RECORD))
                    .is_some_and(|state| *state == apart::State::Missing);
                found.insert(
                    here.to_owned(),
                    if missing {
                        State::Missing
                    } else {
                        State::Redacted
                    },
                );
                continue;
            }
        };
        let format = if act_of(kind).is_some() {
            DECISION
        } else {
            own_format(kind).ok_or(no(Reason::NotARecord))?
        };
        if !holds(record, format) {
            return Err(no(Reason::NotARecord));
        }
        if act_of(kind).is_some() {
            office_holds(&room, entry, record, comment, at)?;
            found.insert(here.to_owned(), State::Held);
            continue;
        }
        if kind == TAKEN_BACK {
            if text(record, &["entry"]) != comment {
                return Err(no(Reason::OtherEntry));
            }
            if text(record, &["after"]) != after {
                return Err(no(Reason::OtherPlace));
            }
        } else if text(record, &["takenBack"]) != says("taken_back") {
            return Err(no(Reason::OtherEntry));
        }
        let wrote = comment.map_or(Wrote::Never, |c| room.author(c));
        let state = match wrote {
            Wrote::Never => return Err(no(Reason::NotAuthor)),
            Wrote::There(key) if Some(key) != record.get("author") => {
                return Err(no(Reason::NotAuthor));
            }
            Wrote::There(_) => State::Held,
            Wrote::Gone => State::Unchecked,
        };
        found.insert(here.to_owned(), state);
    }
    Ok(found)
}

/// The kinds of act the rules fix for a log in this form, in ascending
/// order: what a grant for a room can allow.
pub fn kinds_of_act() -> Vec<&'static str> {
    let mut all: Vec<&'static str> = ACTS.iter().map(|(_, act)| *act).collect();
    all.sort_unstable();
    all
}

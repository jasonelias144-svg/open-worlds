// rust/formats/src/council.rs
//! A council's count (course step 3a, part four;
//! `docs/research/PERSONS.md`, decision 8, and "Part four, second half,
//! built"). The same as the Python `formats/council.py`, checked against
//! it through `vectors/formats/council-v1.json`, problem for problem.
//!
//! - **A proposal** (`open-worlds/proposal/v1`), signed by its council,
//!   names the choices, when votes count (from `opens` to `closes`, both
//!   included), the fewest distinct persons who must be counted
//!   (`quorum`), and the worlds whose births it trusts (`trusts`).
//! - **A vote** (`open-worlds/vote/v1`), signed by the person's identity
//!   key, names the proposal by its hash and a choice by its place.
//! - **A vote counts** only if it holds, isn't a copy of a vote given
//!   before it, names this proposal, names a choice it has, is dated
//!   from `opens` to `closes`, and its person's birth was signed by a
//!   world the proposal trusts.
//! - **Each person counts once:** the latest of their votes that count.
//!   Two or more at the latest time are refused, all of them.
//! - **The outcome** is the choice with the most persons, if at least
//!   `quorum` persons were counted and no other choice has as many.
//!
//! # Limits
//!
//! - **A vote is public, and the person's.** It is signed by their
//!   identity key, so it shows who voted, and how: there is no secret
//!   ballot here (`docs/research/PERSONS.md`, "Part four, second half,
//!   built").
//! - **A vote's date is the voter's own claim.** Nothing here witnesses
//!   when a vote was made, so a vote signed after the close but dated
//!   before it counts, and replaces the person's earlier one. A count is
//!   final only once the votes are fixed by something that saw them
//!   before the close; that witness isn't built.
//! - **Births are given, not found.** Whoever counts gathers the birth
//!   records; a person whose birth isn't given doesn't count.
//! - **A person is one only as far as their birth shows** (decision 8): a
//!   world that signs two births for one person makes them two.

use std::collections::{BTreeMap, BTreeSet};

use serde_json::Value;

use crate::records::{check, record_hash};

/// A council's proposal.
pub const PROPOSAL: &str = "open-worlds/proposal/v1";
/// A person's vote on one.
pub const VOTE: &str = "open-worlds/vote/v1";
/// An individual's birth record.
pub const BIRTH: &str = "open-worlds/birth/v1";

/// The count of the votes on a proposal.
#[derive(Debug, Clone, Default, PartialEq, Eq)]
pub struct Tally {
    /// How many persons chose each choice, in the proposal's order.
    pub counts: Vec<u64>,
    /// How many persons were counted.
    pub persons: u64,
    /// The choice decided, by its place, if any.
    pub outcome: Option<usize>,
    /// Which votes were counted, by their place in the votes given.
    pub counted: Vec<usize>,
    /// Every problem found, in fixed words.
    pub problems: Vec<String>,
}

fn holds(record: &Value, format: &str) -> bool {
    record.get("format").and_then(Value::as_str) == Some(format) && check(record).is_ok()
}

fn text<'a>(record: &'a Value, field: &str) -> &'a str {
    record.get(field).and_then(Value::as_str).unwrap_or("")
}

/// The count of `votes` on `proposal`, given the birth records `births`
/// (see the module's documentation). It never fails: what doesn't hold is
/// a problem, written in fixed words.
pub fn tally(proposal: &Value, votes: &[Value], births: &[Value]) -> Tally {
    let mut result = Tally::default();
    if !holds(proposal, PROPOSAL) {
        result
            .problems
            .push("proposal: not a proposal that holds".into());
        return result;
    }
    let trusted: BTreeSet<&str> = proposal
        .get("trusts")
        .and_then(Value::as_array)
        .map(|worlds| worlds.iter().filter_map(Value::as_str).collect())
        .unwrap_or_default();
    let mut born = BTreeSet::new();
    for (i, birth) in births.iter().enumerate() {
        if !holds(birth, BIRTH) {
            result
                .problems
                .push(format!("births[{i}]: not a birth record that holds"));
        } else if trusted.contains(text(birth, "world")) {
            born.insert(text(birth, "individual"));
        }
    }
    let this = record_hash(proposal).unwrap_or_default();
    let choices = proposal
        .get("choices")
        .and_then(Value::as_array)
        .map_or(0, Vec::len);
    let (opens, closes) = (text(proposal, "opens"), text(proposal, "closes"));
    // Each person's votes that count so far: their time, and their place.
    let mut by_person: BTreeMap<&str, Vec<(&str, usize)>> = BTreeMap::new();
    // The place of each vote that holds, by its record's hash: a copy
    // given again is refused, so it can't cancel its person's vote.
    let mut first: BTreeMap<String, usize> = BTreeMap::new();
    for (i, vote) in votes.iter().enumerate() {
        let choice = vote
            .get("choice")
            .and_then(Value::as_u64)
            .and_then(|c| usize::try_from(c).ok());
        let time = text(vote, "time");
        let held = holds(vote, VOTE);
        let digest = if held { record_hash(vote).ok() } else { None };
        let copy_of = digest.as_ref().and_then(|d| first.get(d).copied());
        if let (Some(d), None) = (digest, copy_of) {
            first.insert(d, i);
        }
        let problem = if !held {
            Some("not a vote that holds".to_owned())
        } else if let Some(j) = copy_of {
            Some(format!("the same vote as votes[{j}]"))
        } else if text(vote, "proposal") != this {
            Some("names another proposal".to_owned())
        } else if choice.is_none_or(|c| c >= choices) {
            Some("a choice the proposal doesn't have".to_owned())
        } else if time < opens {
            Some("dated before the proposal opens".to_owned())
        } else if time > closes {
            Some("dated after the proposal closes".to_owned())
        } else if !born.contains(text(vote, "person")) {
            Some("by one whose birth no trusted world signed".to_owned())
        } else {
            None
        };
        match problem {
            Some(why) => result.problems.push(format!("votes[{i}]: {why}")),
            None => by_person
                .entry(text(vote, "person"))
                .or_default()
                .push((time, i)),
        }
    }
    let mut counts = vec![0_u64; choices];
    let mut counted = Vec::new();
    for cast in by_person.values() {
        let latest = cast.iter().map(|(t, _)| *t).max().unwrap_or("");
        let last: Vec<usize> = cast
            .iter()
            .filter(|(t, _)| *t == latest)
            .map(|(_, i)| *i)
            .collect();
        match last.as_slice() {
            [one] => {
                let choice = votes
                    .get(*one)
                    .and_then(|v| v.get("choice"))
                    .and_then(Value::as_u64)
                    .and_then(|c| usize::try_from(c).ok());
                if let Some(slot) = choice.and_then(|c| counts.get_mut(c)) {
                    *slot += 1;
                    counted.push(*one);
                }
            }
            several => result.problems.extend(
                several
                    .iter()
                    .map(|i| format!("votes[{i}]: one of several votes by one person at one time")),
            ),
        }
    }
    counted.sort_unstable();
    result.persons = u64::try_from(counted.len()).unwrap_or(u64::MAX);
    let quorum = proposal.get("quorum").and_then(Value::as_u64).unwrap_or(1);
    result.outcome = outcome(&counts, result.persons, quorum);
    result.counts = counts;
    result.counted = counted;
    result
}

fn outcome(counts: &[u64], persons: u64, quorum: u64) -> Option<usize> {
    if persons < quorum {
        return None;
    }
    let most = counts.iter().max()?;
    let mut leaders = counts.iter().enumerate().filter(|(_, n)| *n == most);
    match (leaders.next(), leaders.next()) {
        (Some((i, _)), None) => Some(i),
        _ => None,
    }
}

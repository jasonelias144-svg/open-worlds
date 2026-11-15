//! A plant world: a primary world that grows by its rule and dials alone.
//!
//! It has a key of its own, which names it, and a log that remembers every
//! step, in the same format as every world's log here (`world-log`): each
//! entry holds `tick`, `kind`, `agent`, `data` and `prev`, and its `hash`.
//! The log begins with `world_created`, naming the world, the template it
//! was made from and the dials it set; each step that grows a branch is a
//! `grew` entry, with the branches and the tips they end in; and when
//! nothing more can grow, a `finished` entry says why. Nothing outside the
//! rule changes it, so the same template and dials give the same log on
//! any machine, and [`log_problems`] can check any log by growing it again.
//!
//! The world signs its log's heads (`open-worlds/log-head/v1`), as the
//! Ur-world does, and its own birth record (`open-worlds/world-birth/v1`),
//! which names its template and its law by hash.

use formats::multikey::{did_key, public_from_multikey};
use formats::proof::{public_key, sign};
use formats::records;
use serde_json::{Map, Value, json};
use sha2::{Digest, Sha256};
use world_log::GENESIS;

use crate::rule::{Dials, Pot, Segment, Tip, advance};

/// The rule a plant world grows by, as its first entry names it.
pub const RULE: &str = "open-worlds/plant-rule/v1";

/// The template's name.
pub const TEMPLATE_NAME: &str = "A fractal plant";

/// Where every plant begins: at the origin, pointing up, not yet split.
pub const FIRST_TIP: Tip = Tip {
    x: 0,
    y: 0,
    dir: 0,
    depth: 0,
};

/// The did:key of the holder of `secret`.
pub fn did(secret: &[u8; 32]) -> String {
    did_key(&public_key(secret))
}

/// A key made from a seed and a label, for trial worlds, tests and the
/// shared vectors only. Anyone who knows the seed can make it, so it
/// protects nothing.
pub fn trial_secret(seed: u64, label: &str) -> [u8; 32] {
    Sha256::digest(format!(
        "open-worlds trial key, never for anything real: {seed}: {label}"
    ))
    .into()
}

/// The world's law, as data: what happens in a plant world. Its birth
/// record names it by hash ([`law_hash`]).
pub fn law() -> Value {
    json!({
        "rule": RULE,
        "world": [
            "A plant begins as one tip at the origin, pointing up. A place is written (x, y): x grows to the right and y downward, as on a screen.",
            "Each step, every tip that hasn't split as many times as the dials allow grows one branch in its direction, as long as the dial for branches says, and splits into two tips, turned 45 degrees to either side.",
            "With no water, nothing grows. With light below 3, a tip may split only half as many times.",
            "If the world has a pot, a branch whose end would fall outside it isn't grown. Without one, the world grows as far as the plant does.",
        ],
        "change": "This world takes no change from outside: it grows by its rule and dials alone.",
    })
}

/// The SHA-256 of the law's RFC 8785 form, in lowercase hex.
pub fn law_hash() -> Result<String, String> {
    records::record_hash(&law())
}

/// The plant's template (`open-worlds/template/v1`), signed by the holder
/// of `issuer`: each dial with the template's value and its range
/// ([`Dials::RANGES`]), and the reviewed code that runs it, `repo` at
/// `revision`. `created` is the signer's clock, `YYYY-MM-DDTHH:MM:SSZ`.
pub fn template(
    issuer: &[u8; 32],
    repo: &str,
    revision: &str,
    created: &str,
) -> Result<Value, String> {
    let mut parameters = Map::new();
    for ((name, min, max, unit, about), (_, value)) in
        Dials::RANGES.iter().zip(Dials::default().values())
    {
        parameters.insert(
            (*name).into(),
            json!({ "value": value, "unit": unit, "about": about, "min": min, "max": max }),
        );
    }
    let record = json!({
        "format": "open-worlds/template/v1",
        "issuer": did(issuer),
        "name": TEMPLATE_NAME,
        "code": { "repo": repo, "revision": revision },
        "parameters": parameters,
    });
    let signed = sign(&record, issuer, created, "assertionMethod")?;
    records::check(&signed)?;
    Ok(signed)
}

/// A plant world, growing.
#[derive(Debug, Clone)]
pub struct PlantWorld {
    key: String,
    template: String,
    dials: Dials,
    pot: Option<Pot>,
    frontier: Vec<Tip>,
    segments: Vec<Segment>,
    tick: u64,
    log: Vec<Value>,
    finished: bool,
}

impl PlantWorld {
    /// A new world named by `key` (a did:key), made from the template whose
    /// hash is `template`, with `dials` set and, if it has one, a `pot`. Its
    /// log begins with `world_created`. Refused, with the reason, if the key
    /// isn't an Ed25519 did:key, the hash isn't 64 lowercase hex digits, or
    /// a dial is outside its range.
    pub fn new(key: &str, template: &str, dials: Dials, pot: Option<Pot>) -> Result<Self, String> {
        let multikey = key
            .strip_prefix("did:key:")
            .ok_or("the world's key is not a did:key")?;
        public_from_multikey(multikey)?;
        if template.len() != 64
            || !template
                .bytes()
                .all(|b| b.is_ascii_digit() || (b'a'..=b'f').contains(&b))
        {
            return Err("the template's hash is not 64 lowercase hex digits".into());
        }
        let problems = dials.problems();
        if !problems.is_empty() {
            return Err(problems.join("; "));
        }
        let mut world = PlantWorld {
            key: key.into(),
            template: template.into(),
            dials,
            pot,
            frontier: vec![FIRST_TIP],
            segments: Vec::new(),
            tick: 0,
            log: Vec::new(),
            finished: false,
        };
        world.record(
            "world_created",
            json!({
                "world": key,
                "template": template,
                "rule": RULE,
                "dials": dials.json(),
                "pot": pot.map_or(Value::Null, |p| p.json()),
                "tip": FIRST_TIP.json(),
            }),
        )?;
        Ok(world)
    }

    /// The world's key, which names it.
    pub fn key(&self) -> &str {
        &self.key
    }

    /// The hash of the template it was made from.
    pub fn template(&self) -> &str {
        &self.template
    }

    /// The dials it set.
    pub fn dials(&self) -> Dials {
        self.dials
    }

    /// Its pot, if it has one.
    pub fn pot(&self) -> Option<Pot> {
        self.pot
    }

    /// The tips still to grow.
    pub fn frontier(&self) -> &[Tip] {
        &self.frontier
    }

    /// Every branch grown so far, in the order grown.
    pub fn segments(&self) -> &[Segment] {
        &self.segments
    }

    /// The tick: how many steps the world has taken.
    pub fn tick(&self) -> u64 {
        self.tick
    }

    /// The world's log, from its first entry.
    pub fn log(&self) -> &[Value] {
        &self.log
    }

    /// The hash of the log's last entry.
    pub fn last_hash(&self) -> &str {
        self.log
            .last()
            .and_then(|e| e.get("hash"))
            .and_then(Value::as_str)
            .unwrap_or(GENESIS)
    }

    /// Whether it has finished: nothing more can grow.
    pub fn finished(&self) -> bool {
        self.finished
    }

    /// One step: true if a branch grew (a `grew` entry), false if nothing
    /// more can grow (a `finished` entry, written once) or the world had
    /// already finished. Refused only if the log can't be written, which a
    /// world made by [`PlantWorld::new`] never meets.
    pub fn grow(&mut self) -> Result<bool, String> {
        if self.finished {
            return Ok(false);
        }
        if !self.dials.can_grow() {
            return self.finish("There is no water, so nothing grows.");
        }
        let (segments, tips) = advance(&self.frontier, &self.dials, self.pot.as_ref())?;
        if segments.is_empty() {
            return self.finish(
                "Every tip has split as many times as it may, or would grow past the pot.",
            );
        }
        self.tick += 1;
        self.record(
            "grew",
            json!({
                "segments": segments.iter().map(Segment::json).collect::<Vec<_>>(),
                "tips": tips.iter().map(Tip::json).collect::<Vec<_>>(),
            }),
        )?;
        self.segments.extend(segments);
        self.frontier = tips;
        Ok(true)
    }

    /// Steps until it finishes, or `limit` steps; how many steps grew.
    pub fn grow_until_finished(&mut self, limit: u64) -> Result<u64, String> {
        let mut grown = 0;
        for _ in 0..limit {
            if !self.grow()? {
                break;
            }
            grown += 1;
        }
        Ok(grown)
    }

    /// The world's signed head of its log as it is now
    /// (`open-worlds/log-head/v1`): its length, the hash of its last entry
    /// and the tick, signed with `secret`, which must be the world's own
    /// key. `created` is the signer's clock, `YYYY-MM-DDTHH:MM:SSZ`.
    pub fn head(&self, secret: &[u8; 32], created: &str) -> Result<Value, String> {
        self.own(secret)?;
        let record = json!({
            "format": "open-worlds/log-head/v1",
            "world": self.key,
            "length": self.log.len(),
            "last": self.last_hash(),
            "tick": self.tick,
        });
        let signed = sign(&record, secret, created, "assertionMethod")?;
        records::check(&signed)?;
        Ok(signed)
    }

    /// The world's birth record (`open-worlds/world-birth/v1`), signed with
    /// `secret`, which must be the world's own key: its name, its law by
    /// hash ([`law_hash`]), no founders (the project made it), its template
    /// by hash, and the dials it set to something other than the
    /// template's value, if any (records-v1 names only those). `time` is
    /// when it was born, `YYYY-MM-DDTHH:MM:SSZ`, and also the signer's
    /// clock.
    pub fn birth(&self, secret: &[u8; 32], name: &str, time: &str) -> Result<Value, String> {
        self.own(secret)?;
        let mut record = json!({
            "format": "open-worlds/world-birth/v1",
            "world": self.key,
            "name": name,
            "law": law_hash()?,
            "founders": [],
            "template": self.template,
            "time": time,
        });
        let mut set = Map::new();
        for ((name, value), (_, given)) in self
            .dials
            .values()
            .into_iter()
            .zip(Dials::default().values())
        {
            if value != given {
                set.insert(name.into(), json!(value));
            }
        }
        if !set.is_empty()
            && let Some(fields) = record.as_object_mut()
        {
            fields.insert("dials".into(), Value::Object(set));
        }
        let signed = sign(&record, secret, time, "assertionMethod")?;
        records::check(&signed)?;
        Ok(signed)
    }

    fn own(&self, secret: &[u8; 32]) -> Result<(), String> {
        if did(secret) == self.key {
            Ok(())
        } else {
            Err("only the world's own key signs for it".into())
        }
    }

    fn finish(&mut self, reason: &str) -> Result<bool, String> {
        self.tick += 1;
        self.record("finished", json!({ "reason": reason }))?;
        self.finished = true;
        self.frontier.clear();
        Ok(false)
    }

    fn record(&mut self, kind: &str, data: Value) -> Result<(), String> {
        let mut entry = Map::new();
        entry.insert("tick".into(), json!(self.tick));
        entry.insert("kind".into(), json!(kind));
        entry.insert("agent".into(), Value::Null);
        entry.insert("data".into(), data);
        entry.insert("prev".into(), json!(self.last_hash()));
        let hash = world_log::digest(&Value::Object(entry.clone())).map_err(|e| e.to_string())?;
        entry.insert("hash".into(), json!(hash));
        self.log.push(Value::Object(entry));
        Ok(())
    }
}

fn int(value: &Value) -> Option<i64> {
    value.as_i64()
}

fn read_dials(value: &Value) -> Option<Dials> {
    let object = value.as_object()?;
    if object.len() != Dials::RANGES.len() {
        return None;
    }
    Some(Dials {
        branch_length: int(object.get("branchLength")?)?,
        max_depth: int(object.get("maxDepth")?)?,
        water: int(object.get("water")?)?,
        light: int(object.get("light")?)?,
    })
}

fn read_pot(value: &Value) -> Option<Option<Pot>> {
    if value.is_null() {
        return Some(None);
    }
    match value.as_array()?.as_slice() {
        [x, y, width, height] => Some(Some(Pot {
            x: int(x)?,
            y: int(y)?,
            width: int(width)?,
            height: int(height)?,
        })),
        _ => None,
    }
}

/// Where a plant world's log differs from what its rule makes, or an empty
/// list. It reads the world, template, dials and pot from the first entry,
/// grows the world again from them, and compares every entry, hash and
/// all: so a log whose chain holds but whose plant didn't grow by the rule
/// is caught too. Each problem names the entry's place in the log,
/// counting from 0. A log may stop early (a plant still growing); it may
/// not go on past `finished`.
pub fn log_problems(log: &[Value]) -> Vec<String> {
    let Some(first) = log.first() else {
        return vec!["the log is empty".into()];
    };
    let data = first.get("data").unwrap_or(&Value::Null);
    let text = |key: &str| data.get(key).and_then(Value::as_str).unwrap_or("");
    let tip = data.get("tip");
    if first.get("kind").and_then(Value::as_str) != Some("world_created")
        || text("rule") != RULE
        || tip != Some(&FIRST_TIP.json())
    {
        return vec!["[0]: not a plant world's world_created entry".into()];
    }
    let (Some(dials), Some(pot)) = (
        data.get("dials").and_then(read_dials),
        data.get("pot").and_then(read_pot),
    ) else {
        return vec!["[0]: its dials or pot can't be read".into()];
    };
    let mut world = match PlantWorld::new(text("world"), text("template"), dials, pot) {
        Ok(world) => world,
        Err(reason) => return vec![format!("[0]: {reason}")],
    };
    for (place, entry) in log.iter().enumerate() {
        if place > 0 {
            if world.finished() {
                return vec![format!("[{place}]: an entry after `finished`")];
            }
            if let Err(reason) = world.grow() {
                return vec![format!("[{place}]: {reason}")];
            }
        }
        if world.log().get(place) != Some(entry) {
            return vec![format!("[{place}]: not what the rule makes here")];
        }
    }
    Vec::new()
}

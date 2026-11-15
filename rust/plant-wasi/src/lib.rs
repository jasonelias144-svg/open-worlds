//! A plant world in the browser: the fractal track's part 4
//! (`docs/FRACTALS.md`), first step.
//!
//! The plant world's own code (`plant-world`), built as a WebAssembly
//! command for WASI (`wasm32-wasip1`), so a page runs the same code the
//! reference does rather than a copy of its rule. A command needs only a
//! `main`: no exported functions, so no `unsafe`, and no dependency beyond
//! the plant world's own. The browser gives it the five WASI calls it
//! uses (`web/lib/wasi.js`): standard input and output, an empty
//! environment, and exit. It asks for no clock and no randomness.
//!
//! A request is one JSON object, with exactly these fields:
//! - `key`: the world's key, a did:key;
//! - `template`: the hash of the template it is made from;
//! - `dials`: `branchLength`, `maxDepth`, `water` and `light`, whole
//!   numbers within the rule's ranges;
//! - `pot`: `[x, y, width, height]`, or `null` for none;
//! - `ticks`: how many steps to grow at most, from 0 to [`MAX_TICKS`].
//!
//! The answer is the world's log, a JSON array, as
//! `plant_world::world::PlantWorld` writes it: the world grown from its
//! first entry, until it finishes or has taken `ticks` steps.
//!
//! # Limits
//!
//! - Each request grows the world from its first entry again. A world
//!   that runs for hours will need to start from a checkpoint instead.
//! - It signs nothing: a page holds no world's key.
//! - One rule, the plant world's; the endless plant of living worlds'
//!   first stage comes next (`docs/FRACTALS.md`, "Where it leads").

use plant_world::rule::{Dials, Pot};
use plant_world::world::PlantWorld;
use serde_json::{Map, Value};

/// The most steps one request may ask for.
pub const MAX_TICKS: u64 = 10_000;

/// The fields a request has, sorted.
const FIELDS: [&str; 5] = ["dials", "key", "pot", "template", "ticks"];

/// The dials a request sets, sorted.
const DIALS: [&str; 4] = ["branchLength", "light", "maxDepth", "water"];

/// The world's log for `request`, as JSON text, or why the request is
/// refused.
pub fn respond(request: &str) -> Result<String, String> {
    let value: Value =
        serde_json::from_str(request).map_err(|e| format!("the request isn't JSON: {e}"))?;
    let fields = value.as_object().ok_or("the request isn't a JSON object")?;
    let mut names: Vec<&str> = fields.keys().map(String::as_str).collect();
    names.sort_unstable();
    if names != FIELDS {
        return Err(format!(
            "the request must have exactly the fields {}",
            FIELDS.join(", ")
        ));
    }
    let text = |name: &str| {
        fields
            .get(name)
            .and_then(Value::as_str)
            .ok_or(format!("its {name} isn't text"))
    };
    let dials = read_dials(fields.get("dials"))?;
    let pot = read_pot(fields.get("pot"))?;
    let ticks = fields
        .get("ticks")
        .and_then(Value::as_u64)
        .filter(|t| *t <= MAX_TICKS)
        .ok_or(format!(
            "its ticks must be a whole number from 0 to {MAX_TICKS}"
        ))?;
    let mut world = PlantWorld::new(text("key")?, text("template")?, dials, pot)?;
    world.grow_until_finished(ticks)?;
    serde_json::to_string(&Value::Array(world.log().to_vec()))
        .map_err(|e| format!("its log can't be written: {e}"))
}

/// A whole number, if `value` is one.
fn whole(value: Option<&Value>) -> Option<i64> {
    value.and_then(Value::as_i64)
}

fn read_dials(value: Option<&Value>) -> Result<Dials, String> {
    let dials: &Map<String, Value> = value
        .and_then(Value::as_object)
        .ok_or("its dials aren't a JSON object")?;
    let mut names: Vec<&str> = dials.keys().map(String::as_str).collect();
    names.sort_unstable();
    if names != DIALS {
        return Err(format!("its dials must be exactly {}", DIALS.join(", ")));
    }
    let dial =
        |name: &str| whole(dials.get(name)).ok_or(format!("its dial {name} isn't a whole number"));
    Ok(Dials {
        branch_length: dial("branchLength")?,
        max_depth: dial("maxDepth")?,
        water: dial("water")?,
        light: dial("light")?,
    })
}

fn read_pot(value: Option<&Value>) -> Result<Option<Pot>, String> {
    match value {
        Some(Value::Null) => Ok(None),
        Some(Value::Array(items)) => match items.as_slice() {
            [x, y, width, height] => {
                let n = |v: &Value| v.as_i64().ok_or("its pot must be four whole numbers");
                Ok(Some(Pot {
                    x: n(x)?,
                    y: n(y)?,
                    width: n(width)?,
                    height: n(height)?,
                }))
            }
            _ => Err("its pot must be four whole numbers".into()),
        },
        _ => Err("its pot must be four whole numbers, or null".into()),
    }
}

//! The shared vectors, `vectors/plant-world.json`: what this crate writes,
//! kept as a file so Python can check it against DeepSeek's sketch, and
//! so a change on either side shows.

use serde_json::{Value, json};

use crate::rule::{Dials, Pot};
use crate::world::{PlantWorld, law, law_hash, template, trial_secret};
use formats::records::record_hash;

/// The repository and commit the trial template names: the commit this
/// crate was built on, not one that contains it (see the crate's Limits).
pub const TRIAL_CODE: (&str, &str) = (
    "jasonelias144-svg/open-worlds",
    "24540957e600470055730c59b8c9f8c64fdc9bb6",
);

/// The signers' clock in the vectors, so they are the same on every run.
pub const TRIAL_TIME: &str = "2026-11-15T00:00:00Z";

/// The worlds the vectors grow: a name, a seed for the world's trial key,
/// the dials, and a pot or none.
pub fn cases() -> Vec<(&'static str, u64, Dials, Option<Pot>)> {
    let dials = |branch_length, max_depth, water, light| Dials {
        branch_length,
        max_depth,
        water,
        light,
    };
    vec![
        ("the template's own values", 1, Dials::default(), None),
        ("a larger plant", 2, dials(3, 8, 10, 10), None),
        (
            "too little light: half the depth",
            3,
            dials(3, 7, 10, 2),
            None,
        ),
        ("no water: nothing grows", 4, dials(2, 6, 0, 10), None),
        (
            "in a pot that stops some branches",
            5,
            dials(2, 6, 10, 10),
            Some(Pot {
                x: -6,
                y: -10,
                width: 13,
                height: 11,
            }),
        ),
    ]
}

/// Everything in `vectors/plant-world.json`.
pub fn shared_vectors() -> Result<Value, String> {
    let keeper = trial_secret(0, "template keeper");
    let template = template(&keeper, TRIAL_CODE.0, TRIAL_CODE.1, TRIAL_TIME)?;
    let template_hash = record_hash(&template)?;
    let mut worlds = Vec::new();
    for (name, seed, dials, pot) in cases() {
        let secret = trial_secret(seed, "plant world");
        let mut world = PlantWorld::new(&crate::world::did(&secret), &template_hash, dials, pot)?;
        world.grow_until_finished(64)?;
        worlds.push(json!({
            "name": name,
            "seed": seed,
            "birth": world.birth(&secret, name, TRIAL_TIME)?,
            "log": world.log(),
            "head": world.head(&secret, TRIAL_TIME)?,
        }));
    }
    Ok(json!({
        "about": "Plant worlds (rust/plant-world), written by `cargo run -p plant-world --example plant -- --vectors ../vectors`. Every key is a trial key made from a seed and public to everyone, never for anything real. The template is signed by a trial key and names the commit the crate was built on.",
        "template": template,
        "templateHash": template_hash,
        "law": law(),
        "lawHash": law_hash()?,
        "worlds": worlds,
    }))
}

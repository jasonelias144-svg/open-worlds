// rust/ur-world/src/story.rs
//! The log told as a story, and a map of what has been seen: how the
//! examples show what happened.

use serde_json::Value;

use crate::space::{CHUNK, Material};
use crate::world::World;

fn text(v: Option<&Value>) -> String {
    match v {
        Some(Value::String(s)) => s.clone(),
        Some(other) => other.to_string(),
        None => String::new(),
    }
}

/// The log, told as a story: one line for each event, with the chunks that
/// came into view counted rather than listed, then a summary.
pub fn tell(world: &World) -> String {
    let mut out = Vec::new();
    let mut explored = 0;
    let mut last_tick = None;
    let came_into_view = |out: &mut Vec<String>, explored: &mut usize| {
        if *explored > 0 {
            out.push(format!("        ({explored} chunks came into view)"));
            *explored = 0;
        }
    };
    for entry in world.log() {
        let kind = text(entry.get("kind"));
        let who = text(entry.get("agent"));
        let data = entry.get("data");
        let field = |key: &str| text(data.and_then(|d| d.get(key)));
        let tick = text(entry.get("tick"));
        if kind == "explored" {
            explored += 1;
            continue;
        }
        came_into_view(&mut out, &mut explored);
        let what = match kind.as_str() {
            "world_created" => format!(
                "The world is created from seed {}: {}.",
                field("seed"),
                field("begins")
            ),
            "entered" => format!("{who} enters, at {}.", field("pos")),
            "said" => format!("{who} says: {}", Value::String(field("text"))),
            "planted" => format!("{who} plants a {} at {}.", field("what"), field("at")),
            "moved" => format!("{who} moves to {}.", field("to")),
            "fell" => format!("{who} falls to {}.", field("to")),
            "blocked" => format!("{who} can't {} {}.", field("action"), field("dir")),
            "unreadable" => format!(
                "{who}'s reply can't be read as an action: {}",
                Value::String(field("reply"))
            ),
            "unanswered" => format!("{who} doesn't answer in time."),
            "shaped" => format!("The operator makes {} {}.", field("at"), field("to")),
            "exited" => format!("{who} leaves ({}).", field("reason")),
            other => format!("{other} {who}"),
        };
        let stamp = if last_tick.as_ref() == Some(&tick) {
            String::new()
        } else {
            format!("[{tick}]")
        };
        last_tick = Some(tick);
        out.push(format!("{stamp:>7} {what}"));
    }
    came_into_view(&mut out, &mut explored);
    out.push(String::new());
    out.push(format!(
        "{} log entries; head {}.",
        world.log().len(),
        world
            .log()
            .last()
            .and_then(|e| e.get("hash"))
            .and_then(Value::as_str)
            .unwrap_or("")
    ));
    out.push(format!(
        "{} chunks explored; {} cell(s) changed and stored.",
        world.explored().len(),
        world.changes().len()
    ));
    out.join("\n")
}

/// A map seen from above, one character a cell: what lies on top in each
/// explored column, each inhabitant by the first letter of its name, and
/// blank where no one has looked.
pub fn map(world: &World) -> String {
    let explored = world.explored();
    let (Some(west), Some(east), Some(north), Some(south)) = (
        explored.iter().map(|c| c.x).min(),
        explored.iter().map(|c| c.x).max(),
        explored.iter().map(|c| c.z).min(),
        explored.iter().map(|c| c.z).max(),
    ) else {
        return String::new();
    };
    // Each inhabitant by the first letter of its name, or by a digit when
    // that letter is taken, or is one the map already uses.
    let mut used: Vec<char> = "T.:=^~*".chars().collect();
    let mut digits = ('1'..='9').chain(std::iter::repeat('@'));
    let mut people: Vec<(char, String, crate::space::Cell)> = Vec::new();
    for (name, at) in world.inhabitants() {
        let first = name.chars().next().and_then(|c| c.to_uppercase().next());
        let letter = match first {
            Some(c) if c.is_alphabetic() && !used.contains(&c) => c,
            _ => digits.next().unwrap_or('@'),
        };
        used.push(letter);
        people.push((letter, name, at));
    }
    let mut out = Vec::new();
    let named: Vec<String> = people
        .iter()
        .map(|(letter, name, _)| format!("{letter} = {name}"))
        .collect();
    let mut key = String::from("North is up. ");
    if !named.is_empty() {
        key.push_str(&named.join(", "));
        key.push_str(", ");
    }
    key.push_str("T = the tree (its crown), ~ water,");
    out.push(key);
    out.push("* flower; the land by height: . 0 or below, : 1 to 3, = 4 to 7, ^ 8 and up;".into());
    out.push("blank: not yet explored.".into());
    for z in north * CHUNK..(south + 1) * CHUNK {
        let mut row = String::new();
        for x in west * CHUNK..(east + 1) * CHUNK {
            let here = people.iter().find(|(_, _, c)| c.x == x && c.z == z);
            let ch = match (here, world.surface(x, z)) {
                (Some((letter, _, _)), _) => *letter,
                (None, None) => ' ',
                (None, Some((y, m))) => match m {
                    Material::Grass | Material::Soil if y <= 0 => '.',
                    Material::Grass | Material::Soil if y <= 3 => ':',
                    Material::Grass | Material::Soil if y <= 7 => '=',
                    Material::Grass | Material::Soil | Material::Rock => '^',
                    Material::Water => '~',
                    Material::Wood | Material::Leaves => 'T',
                    Material::Flower => '*',
                    Material::Air => ' ',
                },
            };
            row.push(ch);
        }
        out.push(row.trim_end().to_owned());
    }
    out.join("\n")
}

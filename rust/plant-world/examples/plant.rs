//! Grow a plant and print it; or, with `--vectors DIR`, write the shared
//! vectors to `DIR/plant-world.json`.
//!
//! ```text
//! cargo run -p plant-world --example plant
//! cargo run -p plant-world --example plant -- 4 9
//! cargo run -p plant-world --example plant -- --vectors ../vectors
//! ```
//!
//! The two numbers, if given, are the dials `branchLength` and `maxDepth`.

use std::collections::BTreeMap;
use std::process::ExitCode;

use plant_world::rule::{Dials, Segment};
use plant_world::vectors::shared_vectors;
use plant_world::world::{PlantWorld, did, trial_secret};

/// The plant drawn in text: `|` and `-` for straight branches, `/` and `\`
/// for slanted ones, `o` where the plant began.
fn draw(segments: &[Segment]) -> String {
    let mut cells: BTreeMap<(i64, i64), char> = BTreeMap::new();
    for s in segments {
        let (dx, dy) = ((s.x2 - s.x1).signum(), (s.y2 - s.y1).signum());
        let mark = match (dx, dy) {
            (0, _) => '|',
            (_, 0) => '-',
            (a, b) if a == b => '\\',
            _ => '/',
        };
        let steps = (s.x2 - s.x1).abs().max((s.y2 - s.y1).abs());
        for i in 1..=steps {
            cells.insert((s.y1 + dy * i, s.x1 + dx * i), mark);
        }
    }
    cells.insert((0, 0), 'o');
    let (Some(top), Some(bottom)) = (
        cells.keys().map(|k| k.0).min(),
        cells.keys().map(|k| k.0).max(),
    ) else {
        return String::new();
    };
    let left = cells.keys().map(|k| k.1).min().unwrap_or(0);
    let right = cells.keys().map(|k| k.1).max().unwrap_or(0);
    let mut out = String::new();
    for y in top..=bottom {
        let line: String = (left..=right)
            .map(|x| cells.get(&(y, x)).copied().unwrap_or(' '))
            .collect();
        out.push_str(line.trim_end());
        out.push('\n');
    }
    out
}

fn run(args: &[String]) -> Result<(), String> {
    if let [flag, dir] = args
        && flag == "--vectors"
    {
        let text = serde_json::to_string_pretty(&shared_vectors()?).map_err(|e| e.to_string())?;
        let path = format!("{dir}/plant-world.json");
        std::fs::write(&path, text + "\n").map_err(|e| format!("{path}: {e}"))?;
        println!("wrote {path}");
        return Ok(());
    }
    let number = |at: usize, default: i64| -> Result<i64, String> {
        args.get(at).map_or(Ok(default), |a| {
            a.parse().map_err(|_| format!("not a whole number: {a}"))
        })
    };
    let dials = Dials {
        branch_length: number(0, 3)?,
        max_depth: number(1, 7)?,
        ..Dials::default()
    };
    let secret = trial_secret(7, "plant world");
    let mut world = PlantWorld::new(&did(&secret), &"0".repeat(64), dials, None)?;
    let grown = world.grow_until_finished(64)?;
    print!("{}", draw(world.segments()));
    println!(
        "\n{} steps, {} branches, {} entries in its log",
        grown,
        world.segments().len(),
        world.log().len()
    );
    Ok(())
}

fn main() -> ExitCode {
    let args: Vec<String> = std::env::args().skip(1).collect();
    match run(&args) {
        Ok(()) => ExitCode::SUCCESS,
        Err(reason) => {
            eprintln!("{reason}");
            ExitCode::FAILURE
        }
    }
}

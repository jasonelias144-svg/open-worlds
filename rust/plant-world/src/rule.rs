//! The plant's rule: each tip grows one branch, then splits in two, 45
//! degrees to either side, until it reaches its depth.
//!
//! This is DeepSeek's rule as written in record 012-06-02
//! (`sketches/deepseek/012-06-02/fractal_world_v3.py`, `advance`), and the
//! sketch is its reference: the shared vectors
//! (`vectors/plant-world.json`) are checked against the sketch's own
//! `advance` from Python (`tests/test_plant_world_vectors.py`), step by
//! step. Its numbers keep the sketch's names, written in camelCase where
//! they are a template's parameters.
//!
//! Places are whole numbers. `x` grows to the right and `y` downward, as
//! on a screen, so a plant that grows up grows toward smaller `y`.

use serde_json::{Value, json};

/// The eight directions a branch can point, 45 degrees apart: straight up
/// first, then turning clockwise.
pub const DIRECTIONS: [(i64, i64); 8] = [
    (0, -1),
    (1, -1),
    (1, 0),
    (1, 1),
    (0, 1),
    (-1, 1),
    (-1, 0),
    (-1, -1),
];

/// The plant's dials: the numbers a world made from the template may set,
/// each within its range ([`Dials::RANGES`]).
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct Dials {
    /// How far each branch reaches, in cells.
    pub branch_length: i64,
    /// How many times a tip may split.
    pub max_depth: i64,
    /// Water: with none, nothing grows.
    pub water: i64,
    /// Light: below 3, a tip may split only half as many times.
    pub light: i64,
}

impl Default for Dials {
    /// The template's values, as in the sketch's `WorldTemplate`.
    fn default() -> Self {
        Dials {
            branch_length: 2,
            max_depth: 4,
            water: 10,
            light: 10,
        }
    }
}

impl Dials {
    /// Each dial's name, the least and the most a world may set it to, its
    /// unit (a UCUM code) and what it is. The ranges keep every place a
    /// plant reaches far inside 64 bits: a branch is at most 16 cells and
    /// a tip splits at most 12 times, so no place is more than 208 cells
    /// from where the plant began.
    pub const RANGES: [(&'static str, i64, i64, &'static str, &'static str); 4] = [
        (
            "branchLength",
            1,
            16,
            "{cell}",
            "How far each branch reaches, in cells.",
        ),
        ("maxDepth", 1, 12, "1", "How many times a tip may split."),
        ("water", 0, 10, "1", "Water: with none, nothing grows."),
        (
            "light",
            0,
            10,
            "1",
            "Light: below 3, a tip may split only half as many times.",
        ),
    ];

    /// The dials by name, in the order of [`Dials::RANGES`].
    pub fn values(&self) -> [(&'static str, i64); 4] {
        [
            ("branchLength", self.branch_length),
            ("maxDepth", self.max_depth),
            ("water", self.water),
            ("light", self.light),
        ]
    }

    /// The dials as a JSON object, by name.
    pub fn json(&self) -> Value {
        let mut map = serde_json::Map::new();
        for (name, value) in self.values() {
            map.insert(name.into(), json!(value));
        }
        Value::Object(map)
    }

    /// Where a dial is outside its range, or an empty list.
    pub fn problems(&self) -> Vec<String> {
        Self::RANGES
            .iter()
            .zip(self.values())
            .filter(|((_, min, max, _, _), (_, value))| value < min || value > max)
            .map(|((name, min, max, _, _), (_, value))| {
                format!("{name}: {value} is outside {min} to {max}")
            })
            .collect()
    }

    /// How many times a tip may split, given the light: the sketch's
    /// `effective_max_depth`. Python's `//` rounds down, as `div_euclid`
    /// does for a positive divisor.
    pub fn effective_max_depth(&self) -> i64 {
        if self.light >= 3 {
            self.max_depth
        } else {
            self.max_depth.div_euclid(2)
        }
    }

    /// Whether anything can grow: the sketch's `can_grow`.
    pub fn can_grow(&self) -> bool {
        self.water > 0
    }
}

/// A growing tip: where it is, the direction it points (an index into
/// [`DIRECTIONS`]), and how many times the branch it ends has split.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct Tip {
    /// Across, growing to the right.
    pub x: i64,
    /// Down, growing downward.
    pub y: i64,
    /// Its direction, 0 to 7.
    pub dir: u8,
    /// How many times the branch it ends has split.
    pub depth: i64,
}

impl Tip {
    /// `[x, y, dir, depth]`, as the sketch writes a tip.
    pub fn json(&self) -> Value {
        json!([self.x, self.y, self.dir, self.depth])
    }
}

/// A branch grown in one step: from `(x1, y1)` to `(x2, y2)`.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct Segment {
    /// Where it starts, across.
    pub x1: i64,
    /// Where it starts, down.
    pub y1: i64,
    /// Where it ends, across.
    pub x2: i64,
    /// Where it ends, down.
    pub y2: i64,
}

impl Segment {
    /// `[x1, y1, x2, y2]`, as the sketch writes a segment.
    pub fn json(&self) -> Value {
        json!([self.x1, self.y1, self.x2, self.y2])
    }
}

/// A pot: a wall a plant can't grow past, if a world sets one. A branch
/// whose end would fall outside it isn't grown. Its cells run from `x` to
/// `x + width - 1` across and from `y` to `y + height - 1` down.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct Pot {
    /// Its left edge.
    pub x: i64,
    /// Its top edge.
    pub y: i64,
    /// How many cells across.
    pub width: i64,
    /// How many cells down.
    pub height: i64,
}

impl Pot {
    /// Whether `(x, y)` is inside. A sum too large for 64 bits counts as
    /// outside.
    pub fn holds(&self, x: i64, y: i64) -> bool {
        match (
            self.x.checked_add(self.width),
            self.y.checked_add(self.height),
        ) {
            (Some(right), Some(bottom)) => self.x <= x && x < right && self.y <= y && y < bottom,
            _ => false,
        }
    }

    /// `[x, y, width, height]`, as the sketch writes a pot.
    pub fn json(&self) -> Value {
        json!([self.x, self.y, self.width, self.height])
    }
}

/// One step of growth: the branches grown, and the tips they end in.
/// Each tip below its depth grows a branch in its direction, unless its
/// end would fall outside the pot, and the branch's end becomes two tips,
/// one turned 45 degrees each way, in that order (counterclockwise
/// first). With no water, nothing grows and the tips stay as they are.
///
/// It is refused, with a reason, only for a tip whose direction isn't 0 to
/// 7 or whose new place doesn't fit in 64 bits; a world's own tips never
/// are.
pub fn advance(
    tips: &[Tip],
    dials: &Dials,
    pot: Option<&Pot>,
) -> Result<(Vec<Segment>, Vec<Tip>), String> {
    if !dials.can_grow() {
        return Ok((Vec::new(), tips.to_vec()));
    }
    let depth = dials.effective_max_depth();
    let mut segments = Vec::new();
    let mut frontier = Vec::new();
    for tip in tips {
        if tip.depth >= depth {
            continue;
        }
        let &(dx, dy) = DIRECTIONS
            .get(usize::from(tip.dir))
            .ok_or_else(|| format!("a tip's direction is {}, not 0 to 7", tip.dir))?;
        let reach = |at: i64, d: i64| {
            d.checked_mul(dials.branch_length)
                .and_then(|step| at.checked_add(step))
                .ok_or_else(|| "a branch would reach past 64 bits".to_string())
        };
        let (x, y) = (reach(tip.x, dx)?, reach(tip.y, dy)?);
        if pot.is_some_and(|p| !p.holds(x, y)) {
            continue;
        }
        let next = tip
            .depth
            .checked_add(1)
            .ok_or_else(|| "a tip's depth is past 64 bits".to_string())?;
        segments.push(Segment {
            x1: tip.x,
            y1: tip.y,
            x2: x,
            y2: y,
        });
        frontier.push(Tip {
            x,
            y,
            dir: (tip.dir + 7) % 8,
            depth: next,
        });
        frontier.push(Tip {
            x,
            y,
            dir: (tip.dir + 1) % 8,
            depth: next,
        });
    }
    Ok((segments, frontier))
}

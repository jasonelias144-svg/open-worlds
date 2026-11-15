//! The endless rule: energy, shade, dieback, growth priority.
//!
//! Stand-ins marked for the standard's review:
//!   - the log hash uses FNV-1a; the real implementation must use
//!     `formats::canonical` + SHA-256.
//!   - the entry body is a formatted string; the real implementation
//!     must carry the signed JSON entry shape.

use std::collections::HashMap;

pub const DIRECTIONS: [(i32, i32); 8] = [
    (0, -1), (1, -1), (1, 0), (1, 1),
    (0, 1), (-1, 1), (-1, 0), (-1, -1),
];

pub type Direction = u8;

#[derive(Clone, Copy, Debug, PartialEq, Eq, PartialOrd, Ord, Hash)]
pub struct Segment {
    pub x1: i32, pub y1: i32,
    pub x2: i32, pub y2: i32,
}

#[derive(Clone, Copy, Debug, PartialEq, Eq, PartialOrd, Ord, Hash)]
pub struct Tip {
    pub x: i32, pub y: i32,
    pub direction: Direction,
    pub depth: u32,
}

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub struct Template {
    pub branch_length: u32,
    pub light: u32,
    pub shadow: u32,
    pub maintenance: u32,
    pub growth_cost: u32,
    pub reserve: u32,
    pub cap: u32,
    pub has_monad: bool,
}

impl Template {
    pub fn new(
        branch_length: u32, light: u32, shadow: u32,
        maintenance: u32, growth_cost: u32, reserve: u32,
        cap: u32, has_monad: bool,
    ) -> Self {
        Self { branch_length, light, shadow, maintenance,
               growth_cost, reserve, cap, has_monad }
    }
}

/// Build a column map: x -> sorted list of y values covered by segments.
pub fn shadow_map(segments: &[Segment]) -> HashMap<i32, Vec<i32>> {
    let mut map: HashMap<i32, Vec<i32>> = HashMap::new();
    for s in segments {
        for (x, y) in line_cells(s.x1, s.y1, s.x2, s.y2) {
            map.entry(x).or_default().push(y);
        }
    }
    for v in map.values_mut() {
        v.sort_unstable();
    }
    map
}

/// Number of segment cells in the column above (x, y): cells with y' < y.
pub fn shadow_count(map: &HashMap<i32, Vec<i32>>, x: i32, y: i32) -> u32 {
    map.get(&x)
        .map(|ys| ys.partition_point(|&yy| yy < y) as u32)
        .unwrap_or(0)
}

/// Gathered light at a tip: max(0, light - shadow * shadow_count).
pub fn gathered_at(
    template: &Template,
    map: &HashMap<i32, Vec<i32>>,
    tip: &Tip,
) -> u32 {
    let count = shadow_count(map, tip.x, tip.y);
    let lost = template.shadow.saturating_mul(count);
    template.light.saturating_sub(lost)
}

/// Where a tip would grow to, if anywhere.
pub fn next_cell(
    template: &Template,
    tip: &Tip,
    pot: (i32, i32, i32, i32),
) -> Option<(i32, i32)> {
    if tip.depth >= template.cap {
        return None;
    }
    let (dx, dy) = DIRECTIONS[tip.direction as usize];
    let nx = tip.x + dx * template.branch_length as i32;
    let ny = tip.y + dy * template.branch_length as i32;
    let (px, py, pw, ph) = pot;
    if nx < px || nx >= px + pw || ny < py || ny >= py + ph {
        return None;
    }
    Some((nx, ny))
}

/// Grow one segment from a tip. Returns (segment, two new tips).
pub fn grow_from(
    template: &Template,
    tip: &Tip,
    pot: (i32, i32, i32, i32),
) -> Option<(Segment, [Tip; 2])> {
    let (nx, ny) = next_cell(template, tip, pot)?;
    let seg = Segment { x1: tip.x, y1: tip.y, x2: nx, y2: ny };
    let left = Tip {
        x: nx, y: ny,
        direction: (tip.direction + 7) % 8,
        depth: tip.depth + 1,
    };
    let right = Tip {
        x: nx, y: ny,
        direction: (tip.direction + 1) % 8,
        depth: tip.depth + 1,
    };
    Some((seg, [left, right]))
}

/// Bresenham line cells, inclusive of both endpoints.
pub fn line_cells(x1: i32, y1: i32, x2: i32, y2: i32) -> Vec<(i32, i32)> {
    let mut cells = Vec::new();
    let dx = (x2 - x1).abs();
    let dy = -(y2 - y1).abs();
    let sx = if x1 < x2 { 1 } else { -1 };
    let sy = if y1 < y2 { 1 } else { -1 };
    let mut err = dx + dy;
    let (mut x, mut y) = (x1, y1);
    loop {
        cells.push((x, y));
        if x == x2 && y == y2 {
            return cells;
        }
        let e2 = 2 * err;
        if e2 >= dy {
            err += dy;
            x += sx;
        }
        if e2 <= dx {
            err += dx;
            y += sy;
        }
    }
}

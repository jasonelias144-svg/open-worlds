// rust/ur-world/src/generate.rs
//! What is there before anyone has changed it: the generator.
//!
//! Unexplored space holds no data. What a cell holds is worked out, when
//! someone first looks, from the world's seed and the cell's coordinates,
//! by the rules below. The same seed and coordinates always give the same
//! cell, on any machine, in any language: the rules use whole numbers only,
//! and every step is written out here so that another implementation can
//! follow it exactly. The test vectors in `vectors/ur-chunks.json` pin the
//! results.
//!
//! The rules are versioned (`GENERATOR`). A better generator later gets a
//! new number and applies only to land not yet explored; the log records
//! which version made each chunk.
//!
//! At the centre is the one hand-made place: the garden, where the world
//! begins. Flat grass within `GARDEN_RADIUS` of the origin, easing into the
//! hills around it, with a tree at the centre and a spring.

use crate::space::{CHUNK, CHUNK_CELLS, Cell, ChunkCoord, Material};

/// The version of these rules.
pub const GENERATOR: u32 = 1;

/// The height of still water: low ground fills with water up to here.
pub const SEA: i64 = -2;

/// The garden's flat ground reaches this far from the origin, in cells.
pub const GARDEN_RADIUS: i64 = 8;

/// Beyond the garden, the ground eases into the hills over this many cells.
pub const BLEND: i64 = 16;

/// The spring in the garden: one cell of water in the grass.
pub const SPRING: Cell = Cell::new(2, 0, 3);

/// SplitMix64's finishing step: mixes 64 bits so that neighbouring inputs
/// give unrelated outputs. Not cryptography: only a fixed, well-known way to
/// make reproducible variety.
pub const fn mix(mut z: u64) -> u64 {
    z = (z ^ (z >> 30)).wrapping_mul(0xbf58_476d_1ce4_e5b9);
    z = (z ^ (z >> 27)).wrapping_mul(0x94d0_49bb_1331_11eb);
    z ^ (z >> 31)
}

/// A number for a point `(a, b)` of a lattice, one lattice per `layer`.
/// Negative coordinates enter as their two's-complement bits.
pub const fn lattice(seed: u64, layer: u64, a: i64, b: i64) -> u64 {
    let start = mix(seed ^ layer.wrapping_mul(0x9e37_79b9_7f4a_7c15));
    mix(mix(start ^ a.cast_unsigned()) ^ b.cast_unsigned())
}

/// The fine values chosen at lattice points run from 0 to this.
pub const FINE: i64 = 1023;

/// Value noise: a whole number from 0 to `height`.
///
/// At every lattice point, `spacing` cells apart, a fine value from 0 to
/// `FINE` is chosen (`lattice(seed, layer, ..) % 1024`). In between, the
/// four nearest are blended with the smooth step `3t^2 - 2t^3` in each
/// direction (`t` the fraction of the way to the next lattice point), so the
/// land curves rather than running in straight lines. The blend is scaled
/// to `height` and rounded to the nearest, a half rounding up.
///
/// In whole numbers: with `S = spacing` and `f` the offset from the lattice
/// point, a direction's weight is `w = 3 f^2 S - 2 f^3` out of `D = S^3`.
/// The two blends give `total` out of `D^2`, and the result is
/// `(total * height + D^2 * FINE / 2) / (D^2 * FINE)`, rounded down.
pub fn noise(seed: u64, layer: u64, spacing: i64, height: i64, x: i64, z: i64) -> i64 {
    let (gx, fx) = (x.div_euclid(spacing), x.rem_euclid(spacing));
    let (gz, fz) = (z.div_euclid(spacing), z.rem_euclid(spacing));
    let fine = |a: i64, b: i64| i64::try_from(lattice(seed, layer, a, b) % 1024).unwrap_or(0);
    let whole = spacing * spacing * spacing;
    let weight = |f: i64| 3 * f * f * spacing - 2 * f * f * f;
    let (wx, wz) = (weight(fx), weight(fz));
    let north = fine(gx, gz) * (whole - wx) + fine(gx + 1, gz) * wx;
    let south = fine(gx, gz + 1) * (whole - wx) + fine(gx + 1, gz + 1) * wx;
    let total = north * (whole - wz) + south * wz;
    let out_of = whole * whole * FINE;
    (total * height + out_of / 2).div_euclid(out_of)
}

/// The height of the ground's top cell in the column at `(x, z)`.
///
/// Hills: -12, plus three layers of noise: broad (every 128 cells, 0 to 16),
/// middling (every 32 cells, 0 to 8) and small (every 8 cells, 0 to 2). In
/// the garden the ground is flat at 0; around it, at distance `d` (the
/// whole-number square root of `x^2 + z^2`), the hills rise in proportion,
/// `hills * (d - GARDEN_RADIUS) / BLEND`, rounded to the nearest (a half
/// rounds up).
pub fn ground(seed: u64, x: i64, z: i64) -> i64 {
    let hills = -12
        + noise(seed, 1, 128, 16, x, z)
        + noise(seed, 2, 32, 8, x, z)
        + noise(seed, 3, 8, 2, x, z);
    let reach = GARDEN_RADIUS + BLEND;
    if x.abs() >= reach || z.abs() >= reach {
        return hills;
    }
    let d = (x * x + z * z).isqrt();
    if d <= GARDEN_RADIUS {
        0
    } else if d >= reach {
        hills
    } else {
        (hills * (d - GARDEN_RADIUS) + BLEND / 2).div_euclid(BLEND)
    }
}

/// What a cell holds by nature, given its column's ground height: rock deep
/// down, three cells of soil, grass on top (soil under water), then water
/// up to `SEA` and air above.
pub const fn natural(ground: i64, y: i64) -> Material {
    if y > ground {
        if y <= SEA {
            Material::Water
        } else {
            Material::Air
        }
    } else if y == ground {
        if ground < SEA {
            Material::Soil
        } else {
            Material::Grass
        }
    } else if y > ground - 3 {
        Material::Soil
    } else {
        Material::Rock
    }
}

/// The garden's hand-made pieces, if `c` is one: the spring, and the tree at
/// the centre (a trunk four cells high, a crown five across).
pub const fn garden_piece(c: Cell) -> Option<Material> {
    if c.x == SPRING.x && c.y == SPRING.y && c.z == SPRING.z {
        return Some(Material::Water);
    }
    let (ax, az) = (c.x.abs(), c.z.abs());
    if ax == 0 && az == 0 && c.y >= 1 && c.y <= 4 {
        return Some(Material::Wood);
    }
    let crown = (c.y == 4 || c.y == 5) && ax <= 2 && az <= 2 && !(ax == 2 && az == 2);
    let top = c.y == 6 && ax + az <= 1;
    if crown || top {
        Some(Material::Leaves)
    } else {
        None
    }
}

/// What a cell holds before anyone has changed it.
pub fn material(seed: u64, c: Cell) -> Material {
    match garden_piece(c) {
        Some(m) => m,
        None => natural(ground(seed, c.x, c.z), c.y),
    }
}

/// A chunk's cells, in a fixed order: `x` fastest, then `z`, then `y`.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct Chunk {
    coord: ChunkCoord,
    cells: Vec<Material>,
}

impl Chunk {
    /// Where the chunk is.
    pub const fn coord(&self) -> ChunkCoord {
        self.coord
    }

    /// The cell at `c`, if `c` is in this chunk.
    pub fn get(&self, c: Cell) -> Option<Material> {
        let i = index(self.coord, c)?;
        self.cells.get(i).copied()
    }

    /// Change the cell at `c`, if `c` is in this chunk.
    pub fn set(&mut self, c: Cell, m: Material) {
        if let Some(cell) = index(self.coord, c).and_then(|i| self.cells.get_mut(i)) {
            *cell = m;
        }
    }

    /// One byte per cell (the material's number), in the chunk's order.
    pub fn bytes(&self) -> Vec<u8> {
        self.cells.iter().map(|m| *m as u8).collect()
    }

    /// The SHA-256 of `bytes`, in lowercase hex: what the log records when
    /// the chunk is first explored, so anyone can regenerate it and check.
    pub fn hash(&self) -> String {
        world_log::sha256_hex(&self.bytes())
    }
}

/// Where cell `c` sits in chunk `coord`'s list, if it is in that chunk.
fn index(coord: ChunkCoord, c: Cell) -> Option<usize> {
    if c.chunk() != coord {
        return None;
    }
    let o = coord.origin();
    let i = ((c.y - o.y) * CHUNK + (c.z - o.z)) * CHUNK + (c.x - o.x);
    usize::try_from(i).ok()
}

/// The chunk at `coord` as the generator makes it.
pub fn generate(seed: u64, coord: ChunkCoord) -> Chunk {
    let o = coord.origin();
    let mut cells = vec![Material::Air; CHUNK_CELLS];
    for lz in 0..CHUNK {
        for lx in 0..CHUNK {
            let (x, z) = (o.x + lx, o.z + lz);
            let height = ground(seed, x, z);
            for ly in 0..CHUNK {
                let c = Cell::new(x, o.y + ly, z);
                let m = garden_piece(c).unwrap_or(natural(height, c.y));
                let i = usize::try_from((ly * CHUNK + lz) * CHUNK + lx).unwrap_or(0);
                if let Some(cell) = cells.get_mut(i) {
                    *cell = m;
                }
            }
        }
    }
    Chunk { coord, cells }
}

/// The seeds the shared vectors cover: the garden's, and the two extremes.
pub const VECTOR_SEEDS: [u64; 3] = [20_261_113, 0, u64::MAX];

/// The chunks the shared vectors cover: the garden's, under and over it,
/// and some far away (the last at the world's eastern edge).
pub const VECTOR_CHUNKS: [ChunkCoord; 8] = [
    ChunkCoord::new(0, 0, 0),
    ChunkCoord::new(-1, 0, -1),
    ChunkCoord::new(0, -1, 0),
    ChunkCoord::new(0, 1, 0),
    ChunkCoord::new(1, 0, 0),
    ChunkCoord::new(-5, -1, 3),
    ChunkCoord::new(1000, 0, -1000),
    ChunkCoord::new(crate::space::LIMIT / CHUNK, 0, 0),
];

/// The columns whose ground height the shared vectors give.
pub const VECTOR_COLUMNS: [(i64, i64); 8] = [
    (0, 0),
    (8, 0),
    (12, -5),
    (16, 0),
    (-31, 47),
    (100, -100),
    (-65_536, 65_536),
    (crate::space::LIMIT, -crate::space::LIMIT),
];

/// The shared test vectors (`vectors/ur-chunks.json`): for each seed, the
/// ground height of some columns, and the hash of some chunks. Another
/// implementation of the generator agrees with this one when it gives the
/// same numbers.
pub fn vectors() -> serde_json::Value {
    let per_seed: Vec<serde_json::Value> = VECTOR_SEEDS
        .iter()
        .map(|&seed| {
            let ground: Vec<serde_json::Value> = VECTOR_COLUMNS
                .iter()
                .map(|&(x, z)| serde_json::json!({ "x": x, "z": z, "height": ground(seed, x, z) }))
                .collect();
            let chunks: Vec<serde_json::Value> = VECTOR_CHUNKS
                .iter()
                .map(
                    |&c| serde_json::json!({ "chunk": c.json(), "hash": generate(seed, c).hash() }),
                )
                .collect();
            serde_json::json!({ "seed": seed, "ground": ground, "chunks": chunks })
        })
        .collect();
    serde_json::json!({ "generator": GENERATOR, "chunk": CHUNK, "seeds": per_seed })
}

#[cfg(test)]
// Tests may unwrap and index: a failure here is a failed test, not a
// world that crashed.
#[allow(clippy::unwrap_used, clippy::indexing_slicing)]
mod tests {
    use super::*;

    #[test]
    fn mix_is_splitmix64() {
        // The first output of SplitMix64 seeded with 0 is mix(0x9e3779b97f4a7c15).
        assert_eq!(mix(0x9e37_79b9_7f4a_7c15), 0xe220_a839_7b1d_cdaf);
    }

    #[test]
    fn noise_stays_in_range_and_meets_the_lattice() {
        for x in -40..40 {
            for z in [-33, -1, 0, 7, 31] {
                let n = noise(5, 1, 8, 3, x, z);
                assert!((0..=3).contains(&n), "{n} at {x},{z}");
            }
        }
        // On a lattice point the noise is the lattice's fine value, scaled.
        let fine = i64::try_from(lattice(5, 1, -2, 3) % 1024).unwrap();
        assert_eq!(noise(5, 1, 8, 16, -16, 24), (fine * 16 + FINE / 2) / FINE);
        assert_eq!(
            noise(5, 1, 128, 16, i64::from(i32::MAX), -LIMIT_TEST),
            noise(5, 1, 128, 16, i64::from(i32::MAX), -LIMIT_TEST)
        );
    }

    #[test]
    fn the_garden_is_flat_and_the_hills_rise_around_it() {
        for x in -8..=8 {
            for z in -8..=8 {
                if x * x + z * z <= 64 {
                    assert_eq!(ground(1, x, z), 0, "{x},{z}");
                }
            }
        }
        let hills = |x, z| {
            -12 + noise(1, 1, 128, 16, x, z) + noise(1, 2, 32, 8, x, z) + noise(1, 3, 8, 2, x, z)
        };
        // Beyond the easing ring (24 cells out), the hills as they are.
        for (x, z) in [
            (24, 0),
            (0, -30),
            (17, 17),
            (100, 100),
            (-LIMIT_TEST, LIMIT_TEST),
        ] {
            assert_eq!(ground(1, x, z), hills(x, z), "{x},{z}");
        }
        // In the ring, in proportion: 12 cells out is a quarter of the way.
        assert_eq!(ground(1, 12, 0), (hills(12, 0) * 4 + 8).div_euclid(16));
        assert_eq!(ground(1, -9, -9), (hills(-9, -9) * 4 + 8).div_euclid(16));
    }

    const LIMIT_TEST: i64 = crate::space::LIMIT;

    #[test]
    fn the_garden_has_a_tree_and_a_spring() {
        assert_eq!(material(9, Cell::new(0, 0, 0)), Material::Grass);
        assert_eq!(material(9, Cell::new(0, 1, 0)), Material::Wood);
        assert_eq!(material(9, Cell::new(0, 4, 0)), Material::Wood);
        assert_eq!(material(9, Cell::new(1, 4, -1)), Material::Leaves);
        assert_eq!(material(9, Cell::new(2, 5, 2)), Material::Air);
        assert_eq!(material(9, Cell::new(0, 6, 0)), Material::Leaves);
        assert_eq!(material(9, SPRING), Material::Water);
        assert_eq!(material(9, Cell::new(-3, 1, 0)), Material::Air);
        assert_eq!(material(9, Cell::new(-3, -1, 0)), Material::Soil);
        assert_eq!(material(9, Cell::new(-3, -3, 0)), Material::Rock);
    }

    #[test]
    fn a_chunk_is_its_cells() {
        let coord = ChunkCoord::new(-1, 0, 2);
        let chunk = generate(42, coord);
        for c in [
            coord.origin(),
            coord.origin().offset(15, 15, 15),
            coord.origin().offset(3, 9, 12),
        ] {
            assert_eq!(chunk.get(c), Some(material(42, c)));
        }
        assert_eq!(chunk.get(Cell::new(0, 0, 0)), None);
        assert_eq!(chunk.bytes().len(), CHUNK_CELLS);
        assert_eq!(generate(42, coord), chunk);
        assert_ne!(generate(43, coord).hash(), chunk.hash());
    }
}

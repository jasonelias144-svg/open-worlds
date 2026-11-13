// rust/ur-world/src/space.rs
//! Where things are: cells, chunks, directions, and what fills a cell.
//!
//! Space is a grid of cells with whole-number coordinates. `y` is up (as in
//! glTF, Unity and Bevy), `x` is east and `z` is south, so the axes are
//! right-handed. Cells are grouped into chunks of 16 x 16 x 16: a chunk is
//! the piece of the world that comes into being when someone first sees it.

/// The edge of a chunk, in cells.
pub const CHUNK: i64 = 16;

/// The cells in one chunk.
pub const CHUNK_CELLS: usize = 16 * 16 * 16;

/// How far the world reaches from the garden in every direction, in cells:
/// 2^40, about a million million. Far enough to be endless for anyone
/// walking it, and near enough that every sum the world makes stays far
/// from the limits of 64-bit numbers.
pub const LIMIT: i64 = 1 << 40;

/// Whether a coordinate is within `LIMIT` of the garden.
const fn within(v: i64) -> bool {
    -LIMIT <= v && v <= LIMIT
}

/// Whether a chunk coordinate holds any cell within `LIMIT`. A chunk spans
/// `16 v` to `16 v + 15`, and `LIMIT` is a multiple of 16, so that is when
/// `-LIMIT / 16 <= v <= LIMIT / 16`.
const fn chunk_within(v: i64) -> bool {
    -LIMIT / CHUNK <= v && v <= LIMIT / CHUNK
}

/// One cell of space.
#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Hash)]
pub struct Cell {
    /// East (+) and west (-).
    pub x: i64,
    /// Up (+) and down (-).
    pub y: i64,
    /// South (+) and north (-).
    pub z: i64,
}

impl Cell {
    /// The cell at `(x, y, z)`.
    pub const fn new(x: i64, y: i64, z: i64) -> Cell {
        Cell { x, y, z }
    }

    /// The cell `(dx, dy, dz)` away. At the ends of 64-bit numbers, far
    /// outside the world, it stops at the end rather than overflowing.
    pub const fn offset(self, dx: i64, dy: i64, dz: i64) -> Cell {
        Cell::new(
            self.x.saturating_add(dx),
            self.y.saturating_add(dy),
            self.z.saturating_add(dz),
        )
    }

    /// The cell above.
    pub const fn above(self) -> Cell {
        self.offset(0, 1, 0)
    }

    /// The cell below.
    pub const fn below(self) -> Cell {
        self.offset(0, -1, 0)
    }

    /// The neighbouring cell in a direction.
    pub const fn toward(self, dir: Dir) -> Cell {
        let (dx, dz) = dir.step();
        self.offset(dx, 0, dz)
    }

    /// Whether the cell is inside the world (within `LIMIT` on every axis).
    pub const fn inside(self) -> bool {
        // Compared without `abs`, which overflows at i64::MIN.
        within(self.x) && within(self.y) && within(self.z)
    }

    /// The chunk holding this cell.
    pub const fn chunk(self) -> ChunkCoord {
        ChunkCoord {
            x: self.x.div_euclid(CHUNK),
            y: self.y.div_euclid(CHUNK),
            z: self.z.div_euclid(CHUNK),
        }
    }

    /// As the log writes a place: `[x, y, z]`.
    pub fn json(self) -> serde_json::Value {
        serde_json::json!([self.x, self.y, self.z])
    }
}

/// A chunk's place: its cells run from `16 * x` to `16 * x + 15` on each
/// axis.
#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Hash)]
pub struct ChunkCoord {
    /// East (+) and west (-).
    pub x: i64,
    /// Up (+) and down (-).
    pub y: i64,
    /// South (+) and north (-).
    pub z: i64,
}

impl ChunkCoord {
    /// The chunk at `(x, y, z)`.
    pub const fn new(x: i64, y: i64, z: i64) -> ChunkCoord {
        ChunkCoord { x, y, z }
    }

    /// Its lowest-numbered cell (west, down, north corner). For a chunk so
    /// far out that the corner isn't a 64-bit number, it stops at the end
    /// of 64-bit numbers: far outside the world either way.
    pub const fn origin(self) -> Cell {
        Cell::new(
            self.x.saturating_mul(CHUNK),
            self.y.saturating_mul(CHUNK),
            self.z.saturating_mul(CHUNK),
        )
    }

    /// Whether any of its cells is inside the world. Only such chunks can
    /// come into view, and only they are generated.
    pub const fn reachable(self) -> bool {
        chunk_within(self.x) && chunk_within(self.y) && chunk_within(self.z)
    }

    /// As the log writes a chunk: `[x, y, z]`.
    pub fn json(self) -> serde_json::Value {
        serde_json::json!([self.x, self.y, self.z])
    }
}

/// The four directions an inhabitant can step or reach.
#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Hash)]
pub enum Dir {
    /// Toward -z.
    North,
    /// Toward +z.
    South,
    /// Toward +x.
    East,
    /// Toward -x.
    West,
}

impl Dir {
    /// Every direction, in a fixed order.
    pub const ALL: [Dir; 4] = [Dir::North, Dir::South, Dir::East, Dir::West];

    /// The change in `(x, z)` one step makes.
    pub const fn step(self) -> (i64, i64) {
        match self {
            Dir::North => (0, -1),
            Dir::South => (0, 1),
            Dir::East => (1, 0),
            Dir::West => (-1, 0),
        }
    }

    /// Its name in the log.
    pub const fn name(self) -> &'static str {
        match self {
            Dir::North => "north",
            Dir::South => "south",
            Dir::East => "east",
            Dir::West => "west",
        }
    }
}

/// What fills a cell.
#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Hash)]
#[repr(u8)]
pub enum Material {
    /// Empty space.
    Air = 0,
    /// Soil with grass on it.
    Grass = 1,
    /// Soil.
    Soil = 2,
    /// Rock.
    Rock = 3,
    /// Water.
    Water = 4,
    /// A tree's trunk.
    Wood = 5,
    /// A tree's crown.
    Leaves = 6,
    /// A flower someone planted.
    Flower = 7,
}

impl Material {
    /// Whether it bears weight and blocks the way. Air, water and flowers
    /// don't.
    pub const fn solid(self) -> bool {
        matches!(
            self,
            Material::Grass | Material::Soil | Material::Rock | Material::Wood | Material::Leaves
        )
    }

    /// Its name in the log.
    pub const fn name(self) -> &'static str {
        match self {
            Material::Air => "air",
            Material::Grass => "grass",
            Material::Soil => "soil",
            Material::Rock => "rock",
            Material::Water => "water",
            Material::Wood => "wood",
            Material::Leaves => "leaves",
            Material::Flower => "flower",
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn cells_find_their_chunks_on_both_sides_of_zero() {
        assert_eq!(Cell::new(0, 0, 0).chunk(), ChunkCoord::new(0, 0, 0));
        assert_eq!(Cell::new(15, 15, 15).chunk(), ChunkCoord::new(0, 0, 0));
        assert_eq!(Cell::new(16, -1, -16).chunk(), ChunkCoord::new(1, -1, -1));
        assert_eq!(Cell::new(-17, 0, 0).chunk(), ChunkCoord::new(-2, 0, 0));
        assert_eq!(ChunkCoord::new(-2, 0, 1).origin(), Cell::new(-32, 0, 16));
    }

    #[test]
    fn directions_are_right_handed_with_y_up() {
        let c = Cell::new(0, 0, 0);
        assert_eq!(c.toward(Dir::East), Cell::new(1, 0, 0));
        assert_eq!(c.toward(Dir::North), Cell::new(0, 0, -1));
        assert!(Cell::new(LIMIT, -LIMIT, 0).inside());
        assert!(!Cell::new(LIMIT + 1, 0, 0).inside());
        for extreme in [i64::MIN, i64::MAX] {
            assert!(!Cell::new(extreme, 0, 0).inside());
            assert!(!Cell::new(0, extreme, 0).inside());
            assert!(!Cell::new(0, 0, extreme).inside());
        }
    }

    #[test]
    fn nothing_overflows_at_the_ends_of_64_bit_numbers() {
        let top = Cell::new(i64::MAX, i64::MAX, i64::MAX);
        assert_eq!(top.above(), top);
        assert_eq!(top.toward(Dir::East), top);
        let bottom = Cell::new(i64::MIN, i64::MIN, i64::MIN);
        assert_eq!(bottom.below(), bottom);
        assert_eq!(bottom.toward(Dir::West), bottom);
        assert!(!top.chunk().origin().inside());
        assert!(!bottom.chunk().origin().inside());
        assert!(!ChunkCoord::new(i64::MAX, 0, 0).origin().inside());
        assert!(!ChunkCoord::new(0, 0, i64::MIN).origin().inside());
    }

    #[test]
    fn a_chunk_is_reachable_when_any_cell_of_it_is_inside() {
        // Brute force over each axis near both edges: a chunk is reachable
        // exactly when one of its 16 coordinates on that axis is within.
        let edge = LIMIT / CHUNK;
        for v in [
            -edge - 2,
            -edge - 1,
            -edge,
            -edge + 1,
            0,
            edge - 1,
            edge,
            edge + 1,
        ] {
            let any = (0..CHUNK).any(|i| within(v * CHUNK + i));
            assert_eq!(ChunkCoord::new(v, 0, 0).reachable(), any, "x {v}");
            assert_eq!(ChunkCoord::new(0, v, 0).reachable(), any, "y {v}");
            assert_eq!(ChunkCoord::new(0, 0, v).reachable(), any, "z {v}");
        }
        for extreme in [i64::MIN, i64::MAX] {
            assert!(!ChunkCoord::new(extreme, 0, 0).reachable());
            assert!(!ChunkCoord::new(0, extreme, 0).reachable());
            assert!(!ChunkCoord::new(0, 0, extreme).reachable());
        }
    }
}

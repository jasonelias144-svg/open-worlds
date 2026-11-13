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

    /// The cell `(dx, dy, dz)` away.
    pub const fn offset(self, dx: i64, dy: i64, dz: i64) -> Cell {
        Cell::new(self.x + dx, self.y + dy, self.z + dz)
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
        self.x.abs() <= LIMIT && self.y.abs() <= LIMIT && self.z.abs() <= LIMIT
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

    /// Its lowest-numbered cell (west, down, north corner).
    pub const fn origin(self) -> Cell {
        Cell::new(self.x * CHUNK, self.y * CHUNK, self.z * CHUNK)
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
    }
}

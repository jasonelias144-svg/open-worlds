// rust/ur-world/src/world.rs
//! The world kernel: the only authority over the Ur-world's state.
//!
//! Inhabitants never touch the world directly. Each tick, every inhabitant
//! receives an observation and returns an action; the kernel checks the
//! action before it takes effect. The freedoms of the Python kernel hold
//! here too: leaving always succeeds, and what anyone says reaches everyone
//! on the next tick.
//!
//! What the world remembers is small. The ground comes from the generator,
//! so only what has been explored (a set of chunks) and what has been
//! changed (a map of cells) is kept. Every event goes into an append-only,
//! hash-chained log, written exactly as the Python kernel writes its own,
//! so the same checks (`world-log`, `World.verify_log`) hold it.

use std::collections::{BTreeMap, BTreeSet};

use serde_json::{Map, Value, json};

use crate::generate::{self, Chunk, GENERATOR, SEA};
use crate::space::{CHUNK, Cell, ChunkCoord, Dir, LIMIT, Material};

/// The rules' name and version, as the log records it.
pub const RULES: &str = "ur-world/0.1";

/// The most a single `Say` carries, in characters; longer speech is cut.
pub const MAX_SAY: usize = 280;

/// The longest a name may be, in characters.
pub const MAX_NAME: usize = 64;

/// How far anyone falls in one tick, in cells: a deeper drop goes on at
/// the next tick, as the world settles.
pub const MAX_FALL: i64 = 64;

/// How far an inhabitant sees others, in cells (on every axis).
pub const SIGHT: i64 = 16;

/// The chunks within this many chunks of an inhabitant's own come into view.
pub const VIEW: i64 = 1;

/// What an inhabitant can do in a tick.
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum Action {
    /// Nothing.
    Wait,
    /// Step to the neighbouring cell. A step onto a block one cell high
    /// climbs it, if there is headroom; a step off an edge falls.
    Step(Dir),
    /// Speak to everyone in the world: heard on the next tick.
    Say(String),
    /// Plant a flower in the neighbouring cell, if it is open air on grass
    /// or soil.
    Plant(Dir),
    /// Leave the world. Always succeeds.
    Exit,
}

/// What an inhabitant sees at the start of a tick.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct Observation {
    /// The tick.
    pub tick: u64,
    /// The inhabitant's own name.
    pub me: String,
    /// Where it stands.
    pub position: Cell,
    /// Who said what on the last tick.
    pub heard: Vec<(String, String)>,
    /// The 27 cells around and including its own, `x` fastest, then `z`,
    /// then `y`, from `(-1, -1, -1)` to `(1, 1, 1)`: see `at`.
    pub around: Vec<Material>,
    /// Others within `SIGHT`, and where they stand.
    pub others: Vec<(String, Cell)>,
}

impl Observation {
    /// The cell `(dx, dy, dz)` from where it stands, each from -1 to 1.
    pub fn at(&self, dx: i64, dy: i64, dz: i64) -> Option<Material> {
        if dx.abs() > 1 || dy.abs() > 1 || dz.abs() > 1 {
            return None;
        }
        let i = usize::try_from(((dy + 1) * 3 + (dz + 1)) * 3 + (dx + 1)).ok()?;
        self.around.get(i).copied()
    }
}

/// An inhabitant's mind: whatever chooses its actions. In the garden's
/// first version, a short script; later, a model that learns.
pub trait Mind {
    /// Choose this tick's action.
    fn act(&mut self, seen: &Observation) -> Action;
}

/// Why someone can't enter where they asked.
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum EntryError {
    /// The name is empty, too long, or has a control character.
    BadName,
    /// Someone has that name, or had it and left.
    NameTaken,
    /// The cell is outside the world.
    Outside,
    /// The cell is solid.
    Solid,
    /// Nothing solid underneath to stand on.
    NoGround,
    /// Someone stands there.
    Occupied,
}

/// Whether any cell of the chunk is inside the world.
const fn reachable(c: ChunkCoord) -> bool {
    let (low, high) = (
        c.origin(),
        c.origin().offset(CHUNK - 1, CHUNK - 1, CHUNK - 1),
    );
    low.x <= LIMIT
        && high.x >= -LIMIT
        && low.y <= LIMIT
        && high.y >= -LIMIT
        && low.z <= LIMIT
        && high.z >= -LIMIT
}

struct Inhabitant {
    position: Cell,
    mind: Box<dyn Mind>,
}

/// The Ur-world.
pub struct World {
    seed: u64,
    tick: u64,
    explored: BTreeSet<ChunkCoord>,
    changes: BTreeMap<Cell, Material>,
    inhabitants: BTreeMap<String, Inhabitant>,
    occupied: BTreeMap<Cell, String>,
    heard: Vec<(String, String)>,
    names_used: BTreeSet<String>,
    log: Vec<Value>,
}

impl World {
    /// A world from a seed. It begins as the garden, unexplored; it comes
    /// into view around whoever enters.
    pub fn new(seed: u64) -> World {
        let mut world = World {
            seed,
            tick: 0,
            explored: BTreeSet::new(),
            changes: BTreeMap::new(),
            inhabitants: BTreeMap::new(),
            occupied: BTreeMap::new(),
            heard: Vec::new(),
            names_used: BTreeSet::new(),
            log: Vec::new(),
        };
        world.record(
            "world_created",
            None,
            json!({
                "seed": seed,
                "generator": GENERATOR,
                "rules_version": RULES,
                "chunk": CHUNK,
                "sea": SEA,
                "begins": "a garden, with a tree and a spring",
            }),
        );
        world
    }

    /// The seed.
    pub const fn seed(&self) -> u64 {
        self.seed
    }

    /// The tick: how many have passed.
    pub const fn tick(&self) -> u64 {
        self.tick
    }

    /// What the cell holds now.
    pub fn material(&self, c: Cell) -> Material {
        match self.changes.get(&c) {
            Some(m) => *m,
            None => generate::material(self.seed, c),
        }
    }

    /// A chunk as it is now: generated, with any changes made since.
    pub fn chunk(&self, coord: ChunkCoord) -> Chunk {
        let mut chunk = generate::generate(self.seed, coord);
        for (c, m) in &self.changes {
            if c.chunk() == coord {
                chunk.set(*c, *m);
            }
        }
        chunk
    }

    /// The chunks explored so far.
    pub const fn explored(&self) -> &BTreeSet<ChunkCoord> {
        &self.explored
    }

    /// Every cell changed from what the generator made: all the world
    /// stores of its ground.
    pub const fn changes(&self) -> &BTreeMap<Cell, Material> {
        &self.changes
    }

    /// Who is here, and where, by name.
    pub fn inhabitants(&self) -> Vec<(String, Cell)> {
        self.inhabitants
            .iter()
            .map(|(name, i)| (name.clone(), i.position))
            .collect()
    }

    /// Where `name` stands, if here.
    pub fn position(&self, name: &str) -> Option<Cell> {
        self.inhabitants.get(name).map(|i| i.position)
    }

    /// The public record.
    pub fn log(&self) -> &[Value] {
        &self.log
    }

    /// The highest explored cell in the column at `(x, z)` that isn't air,
    /// and its height: what a map seen from above shows.
    pub fn surface(&self, x: i64, z: i64) -> Option<(i64, Material)> {
        let ys: Vec<i64> = self
            .explored
            .iter()
            .filter(|c| c.x == x.div_euclid(CHUNK) && c.z == z.div_euclid(CHUNK))
            .map(|c| c.y)
            .collect();
        let (low, high) = (*ys.iter().min()?, *ys.iter().max()?);
        let mut y = high * CHUNK + CHUNK - 1;
        while y >= low * CHUNK {
            let c = Cell::new(x, y, z);
            if self.explored.contains(&c.chunk()) {
                let m = self.material(c);
                if m != Material::Air {
                    return Some((y, m));
                }
            }
            y -= 1;
        }
        None
    }

    /// Bring someone in, standing at `at`: a free cell that isn't solid,
    /// with solid ground under it.
    pub fn add(&mut self, name: &str, mind: Box<dyn Mind>, at: Cell) -> Result<(), EntryError> {
        if name.is_empty() || name.chars().count() > MAX_NAME || name.chars().any(char::is_control)
        {
            return Err(EntryError::BadName);
        }
        if self.names_used.contains(name) {
            return Err(EntryError::NameTaken);
        }
        if !at.inside() || !at.below().inside() {
            return Err(EntryError::Outside);
        }
        if self.material(at).solid() {
            return Err(EntryError::Solid);
        }
        if !self.material(at.below()).solid() {
            return Err(EntryError::NoGround);
        }
        if self.occupied.contains_key(&at) {
            return Err(EntryError::Occupied);
        }
        self.names_used.insert(name.to_owned());
        self.occupied.insert(at, name.to_owned());
        self.inhabitants
            .insert(name.to_owned(), Inhabitant { position: at, mind });
        self.record("entered", Some(name), json!({ "pos": at.json() }));
        self.explore();
        Ok(())
    }

    /// Take someone out from outside their turn (their keeper pulls them
    /// out). Like `Exit`, this can't be refused.
    pub fn leave(&mut self, name: &str) {
        if self.inhabitants.contains_key(name) {
            self.remove(name, "requested");
            self.settle();
        }
    }

    /// The operator's hand: set a cell, as a gardener shapes a garden. It is
    /// recorded like everything else, with no inhabitant named. A cell
    /// where someone stands can't be made solid.
    pub fn shape(&mut self, c: Cell, m: Material) -> bool {
        if !c.inside() || (m.solid() && self.occupied.contains_key(&c)) {
            return false;
        }
        if generate::material(self.seed, c) == m {
            self.changes.remove(&c);
        } else {
            self.changes.insert(c, m);
        }
        self.record("shaped", None, json!({ "at": c.json(), "to": m.name() }));
        self.settle();
        true
    }

    /// One tick. Everyone observes first; then each acts in turn. The
    /// order is by name, rotated by one place each tick, so no one always
    /// goes first. Then whoever stands on nothing falls, and what has come
    /// into view is explored.
    pub fn step(&mut self) {
        let heard_now = std::mem::take(&mut self.heard);
        let names: Vec<String> = self.inhabitants.keys().cloned().collect();
        let seen: Vec<Observation> = names
            .iter()
            .filter_map(|n| self.observe(n, &heard_now))
            .collect();
        let count = u64::try_from(seen.len()).unwrap_or(0);
        let start = if count == 0 {
            0
        } else {
            usize::try_from(self.tick % count).unwrap_or(0)
        };
        let mut spoken = Vec::new();
        for turn in 0..seen.len() {
            let Some(obs) = seen.get((start + turn) % seen.len()) else {
                continue;
            };
            let action = match self.inhabitants.get_mut(&obs.me) {
                Some(inhabitant) => inhabitant.mind.act(obs),
                None => continue, // left earlier this tick
            };
            self.resolve(&obs.me, action, &mut spoken);
        }
        self.heard = spoken;
        self.settle();
        self.explore();
        self.tick += 1;
    }

    /// `ticks` ticks.
    pub fn run(&mut self, ticks: u64) {
        for _ in 0..ticks {
            self.step();
        }
    }

    fn observe(&self, name: &str, heard: &[(String, String)]) -> Option<Observation> {
        let position = self.position(name)?;
        let mut around = Vec::with_capacity(27);
        for dy in -1..=1 {
            for dz in -1..=1 {
                for dx in -1..=1 {
                    around.push(self.material(position.offset(dx, dy, dz)));
                }
            }
        }
        let others = self
            .inhabitants
            .iter()
            .filter(|(other, i)| {
                other.as_str() != name
                    && (i.position.x - position.x).abs() <= SIGHT
                    && (i.position.y - position.y).abs() <= SIGHT
                    && (i.position.z - position.z).abs() <= SIGHT
            })
            .map(|(other, i)| (other.clone(), i.position))
            .collect();
        Some(Observation {
            tick: self.tick,
            me: name.to_owned(),
            position,
            heard: heard.to_vec(),
            around,
            others,
        })
    }

    fn resolve(&mut self, name: &str, action: Action, spoken: &mut Vec<(String, String)>) {
        match action {
            Action::Wait => {}
            Action::Step(dir) => self.walk(name, dir),
            Action::Say(text) => {
                let text: String = text.chars().take(MAX_SAY).collect();
                spoken.push((name.to_owned(), text.clone()));
                self.record("said", Some(name), json!({ "text": text }));
            }
            Action::Plant(dir) => self.plant(name, dir),
            Action::Exit => self.remove(name, "chose to leave"),
        }
    }

    fn free(&self, c: Cell) -> bool {
        c.inside() && !self.material(c).solid() && !self.occupied.contains_key(&c)
    }

    fn walk(&mut self, name: &str, dir: Dir) {
        let Some(from) = self.position(name) else {
            return;
        };
        let ahead = from.toward(dir);
        let to = if self.free(ahead) {
            Some(ahead)
        } else if ahead.inside()
            && self.material(ahead).solid()
            && self.free(ahead.above())
            && !self.material(from.above()).solid()
        {
            Some(ahead.above()) // climb one block
        } else {
            None
        };
        match to {
            None => self.record(
                "blocked",
                Some(name),
                json!({ "action": "step", "dir": dir.name() }),
            ),
            Some(to) => {
                let to = self.landing(to);
                self.place(name, from, to);
                self.record(
                    "moved",
                    Some(name),
                    json!({ "from": from.json(), "to": to.json() }),
                );
            }
        }
    }

    /// Where someone at `c` comes to rest: falling until something solid,
    /// or someone, is underneath, at most `MAX_FALL` cells.
    fn landing(&self, mut c: Cell) -> Cell {
        let mut fallen = 0;
        while fallen < MAX_FALL && self.free(c.below()) {
            c = c.below();
            fallen += 1;
        }
        c
    }

    fn place(&mut self, name: &str, from: Cell, to: Cell) {
        self.occupied.remove(&from);
        self.occupied.insert(to, name.to_owned());
        if let Some(i) = self.inhabitants.get_mut(name) {
            i.position = to;
        }
    }

    /// Whoever stands on nothing falls, in name order.
    fn settle(&mut self) {
        let names: Vec<String> = self.inhabitants.keys().cloned().collect();
        for name in names {
            let Some(from) = self.position(&name) else {
                continue;
            };
            let to = self.landing(from);
            if to != from {
                self.place(&name, from, to);
                self.record(
                    "fell",
                    Some(&name),
                    json!({ "from": from.json(), "to": to.json() }),
                );
            }
        }
    }

    fn plant(&mut self, name: &str, dir: Dir) {
        let Some(from) = self.position(name) else {
            return;
        };
        let at = from.toward(dir);
        let fertile = matches!(self.material(at.below()), Material::Grass | Material::Soil);
        if self.free(at) && self.material(at) == Material::Air && fertile {
            self.changes.insert(at, Material::Flower);
            self.record(
                "planted",
                Some(name),
                json!({ "at": at.json(), "what": "flower" }),
            );
        } else {
            self.record(
                "blocked",
                Some(name),
                json!({ "action": "plant", "dir": dir.name() }),
            );
        }
    }

    fn remove(&mut self, name: &str, reason: &str) {
        if let Some(i) = self.inhabitants.remove(name) {
            self.occupied.remove(&i.position);
            self.record("exited", Some(name), json!({ "reason": reason }));
        }
    }

    /// Every chunk within `VIEW` of an inhabitant's own comes into view,
    /// unless it lies wholly beyond the world's edge. The first time, the
    /// log records it, who saw it first, which generator made it, and the
    /// hash of what the generator made (changes the operator made there
    /// before are in the log as their own entries), so anyone can
    /// regenerate it and check.
    fn explore(&mut self) {
        let sightings: Vec<(String, ChunkCoord)> = self
            .inhabitants
            .iter()
            .map(|(name, i)| (name.clone(), i.position.chunk()))
            .collect();
        for (name, home) in sightings {
            for dy in -VIEW..=VIEW {
                for dz in -VIEW..=VIEW {
                    for dx in -VIEW..=VIEW {
                        let c = ChunkCoord::new(home.x + dx, home.y + dy, home.z + dz);
                        if !reachable(c) {
                            continue;
                        }
                        if self.explored.insert(c) {
                            let hash = generate::generate(self.seed, c).hash();
                            self.record(
                                "explored",
                                Some(&name),
                                json!({ "chunk": c.json(), "generator": GENERATOR, "hash": hash }),
                            );
                        }
                    }
                }
            }
        }
    }

    fn record(&mut self, kind: &str, agent: Option<&str>, data: Value) {
        let prev = self
            .log
            .last()
            .and_then(|e| e.get("hash"))
            .and_then(Value::as_str)
            .unwrap_or(world_log::GENESIS)
            .to_owned();
        let mut entry = Map::new();
        entry.insert("tick".into(), json!(self.tick));
        entry.insert("kind".into(), json!(kind));
        entry.insert("agent".into(), agent.map_or(Value::Null, |a| json!(a)));
        entry.insert("data".into(), data);
        entry.insert("prev".into(), json!(prev));
        // Every value the world writes is text or a whole number in 64
        // bits, so this can't fail; if it ever did, the entry would fail
        // the log's own check rather than the world stop.
        let hash = world_log::digest(&Value::Object(entry.clone())).unwrap_or_default();
        entry.insert("hash".into(), json!(hash));
        self.log.push(Value::Object(entry));
    }
}

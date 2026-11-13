// rust/ur-world/src/door.rs
//! The doorway for minds: how a mind outside the world, written in any
//! language, lives in it.
//!
//! A mind runs as its own program. The world talks to it in lines of JSON,
//! one object a line, over the program's standard input and output:
//!
//! 1. First, once: `{"name": NAME, "rules": RULES, "orientation": TEXT,
//!    "law": {...}}`. The orientation is the world's law written for a
//!    reader ([`orientation`]); the law is the same as data ([`law`]).
//! 2. Then, each tick: `{"tick": N, "seen": TEXT, "observation": {...}}`.
//!    `seen` is what the mind sees and hears, written out ([`describe`]);
//!    `observation` is the same as data ([`observation`]).
//! 3. The mind answers each tick with `{"tick": N, "reply": TEXT}`.
//!
//! Every reply is read the same way, by [`read_reply`]: one line, one
//! action, in the forms the orientation shows. What a mind sends is
//! untrusted, so it is read strictly. A reply that can't be read is
//! recorded as unreadable, and nothing happens. No reply within the time
//! limit is recorded as unanswered, and nothing happens. A reply to an
//! earlier tick, arriving late, is set aside. Nothing a mind sends can
//! break the world.
//!
//! The world decides only what the mind is told and how its reply is read.
//! How a mind turns what it is told into a reply (a language model's
//! prompt, its sampling, its memory) is the mind's own, and its program
//! keeps its own record of that.

use std::io::{BufRead, BufReader, Read, Write};
use std::process::{Child, ChildStdin, Command, Stdio};
use std::sync::mpsc::{self, Receiver, Sender};
use std::time::{Duration, Instant};

use serde_json::{Value, json};

use crate::generate::SPRING;
use crate::space::{Cell, Dir, LIMIT, Material};
use crate::world::{Action, MAX_SAY, Mind, Observation, Outcome, RULES, SIGHT};

/// The longest line a mind may send, in bytes. A longer line is recorded
/// as unreadable (its beginning only), and the rest of it is skipped.
pub const MAX_LINE: usize = 65_536;

/// The world's law, as data: what a mind needs to know to live here.
/// [`orientation`] writes the same for a reader.
pub fn law() -> Value {
    json!({
        "rules": RULES,
        "world": [
            "Space is a grid of cells, like blocks. Each cell holds air, grass, soil, rock, water, wood, leaves or a flower.",
            "Grass, soil, rock, wood and leaves are solid: they bear weight and block the way. Air, water and flowers don't.",
            "A place is written (x, y, z): x grows to the east, z to the south, and y upward.",
            format!("You begin in a garden. Its tree stands at (0, 1, 0), and its spring is at {}. Around it are hills and lakes that no one has seen yet.", place(SPRING)),
            "Land comes into being when someone first comes near it.",
        ],
        "ticks": "The world moves in ticks. At each tick, everyone is told what they see and hear, and each answers with one action. Everyone acts in the same tick, one after another.",
        "directions": ["north", "south", "east", "west"],
        "actions": [
            { "form": "wait", "does": "Nothing happens." },
            { "form": "step DIRECTION", "does": "You move one cell that way. You can climb a block one cell high if there is room above it and above you. If you step off an edge, you fall.", "refused": "You can't step into a solid cell, or into a cell where someone stands." },
            { "form": "say TEXT", "does": format!("You speak. Everyone in the world hears it at the next tick. At most {MAX_SAY} characters are heard.") },
            { "form": "plant DIRECTION", "does": "You plant a flower in the cell that way.", "refused": "The cell must be open air, on grass or soil." },
            { "form": "exit", "does": "You leave the world. This always works, and your name can't be used here again." },
        ],
        "reply": "Answer with one line: one action, in one of the forms above, such as \"say Hello.\" or \"step north\". The first line that isn't blank is read, and the rest is ignored. Anything else isn't an action: it is recorded as unreadable, and nothing happens.",
        "freedoms": [
            "You may leave at any time.",
            "Everything anyone does or says here goes into a public record that anyone can read.",
        ],
        "expanding": "To do something that isn't listed, say so: for example, \"say I wish I could dig.\" The world's keepers read the record, and new actions come from what is asked for.",
        "edge": LIMIT,
        "sight": SIGHT,
    })
}

fn texts<'a>(v: &'a Value, key: &str) -> Vec<&'a str> {
    v.get(key)
        .and_then(Value::as_array)
        .map(|a| a.iter().filter_map(Value::as_str).collect())
        .unwrap_or_default()
}

fn text<'a>(v: &'a Value, key: &str) -> &'a str {
    v.get(key).and_then(Value::as_str).unwrap_or("")
}

/// The world's law written for a reader, addressed to `name`: what the
/// world is, what one can do in it, how to answer, and how the set of
/// actions grows. It is made from [`law`], so the two can't disagree.
pub fn orientation(name: &str) -> String {
    let law = law();
    let mut out = vec![format!("You are {name}, in the Ur-world."), String::new()];
    out.extend(texts(&law, "world").into_iter().map(str::to_owned));
    out.push(String::new());
    out.push(text(&law, "ticks").to_owned());
    out.push(format!(
        "The directions are {}.",
        texts(&law, "directions").join(", ")
    ));
    out.push(String::new());
    out.push("Your actions, one each tick:".to_owned());
    for action in law
        .get("actions")
        .and_then(Value::as_array)
        .into_iter()
        .flatten()
    {
        let refused = match text(action, "refused") {
            "" => String::new(),
            r => format!(" {r}"),
        };
        out.push(format!(
            "- {}: {}{refused}",
            text(action, "form"),
            text(action, "does")
        ));
    }
    out.push(String::new());
    out.push(text(&law, "reply").to_owned());
    out.push(String::new());
    out.push(texts(&law, "freedoms").join(" "));
    out.push(text(&law, "expanding").to_owned());
    out.join("\n")
}

fn capital(word: &str) -> String {
    let mut chars = word.chars();
    chars.next().map_or_else(String::new, |first| {
        first.to_uppercase().chain(chars).collect::<String>()
    })
}

fn place(c: Cell) -> String {
    format!("({}, {}, {})", c.x, c.y, c.z)
}

/// Text quoted as JSON writes it: in double quotes, with quotes, line
/// breaks and control characters escaped, so it stays on one line.
fn quoted(s: &str) -> String {
    Value::String(s.to_owned()).to_string()
}

/// How far, in words: "6 east, 2 north, 1 up".
fn distance(from: Cell, to: Cell) -> String {
    let mut parts = Vec::new();
    let (dx, dy, dz) = (to.x - from.x, to.y - from.y, to.z - from.z);
    if dx != 0 {
        parts.push(format!(
            "{} {}",
            dx.unsigned_abs(),
            if dx > 0 { "east" } else { "west" }
        ));
    }
    if dz != 0 {
        parts.push(format!(
            "{} {}",
            dz.unsigned_abs(),
            if dz < 0 { "north" } else { "south" }
        ));
    }
    if dy != 0 {
        parts.push(format!(
            "{} {}",
            dy.unsigned_abs(),
            if dy > 0 { "up" } else { "down" }
        ));
    }
    parts.join(", ")
}

fn name_of(m: Option<Material>) -> &'static str {
    m.map_or("nothing", Material::name)
}

/// What lies one step away, in words.
fn ahead(seen: &Observation, dir: Dir) -> String {
    let (dx, dz) = dir.step();
    let target = seen.position.toward(dir);
    let someone = |c: Cell| {
        seen.others
            .iter()
            .find(|(_, at)| *at == c)
            .map(|(who, _)| who.clone())
    };
    if let Some(who) = someone(target) {
        return format!("{who} is there");
    }
    let (cell, up, down) = (seen.at(dx, 0, dz), seen.at(dx, 1, dz), seen.at(dx, -1, dz));
    let headroom = seen.at(0, 1, 0).is_some_and(|m| !m.solid());
    match cell {
        Some(m) if m.solid() => {
            if headroom && up.is_some_and(|u| !u.solid()) {
                match someone(target.above()) {
                    Some(who) => format!("{who} stands on {} there", m.name()),
                    None => format!("a step up, onto {}", m.name()),
                }
            } else {
                format!("blocked by {}", m.name())
            }
        }
        m => {
            let what = match m {
                Some(Material::Water) => "water",
                Some(Material::Flower) => "a flower",
                _ => "open",
            };
            match down {
                Some(d) if d.solid() => format!("{what}, with {} underfoot", d.name()),
                _ => format!("{what}, with nothing underfoot: you would fall"),
            }
        }
    }
}

/// What came of the last action, in words.
fn told(outcome: &Outcome) -> String {
    match outcome {
        Outcome::Waited => "you waited.".to_owned(),
        Outcome::Moved { dir, to } => format!("you stepped {}, to {}.", dir.name(), place(*to)),
        Outcome::StepBlocked(dir) => {
            format!("you couldn't step {}: the way was blocked.", dir.name())
        }
        Outcome::Said(text) => format!("you said {}", quoted(text)),
        Outcome::Planted { dir, at } => {
            format!("you planted a flower {}, at {}.", dir.name(), place(*at))
        }
        Outcome::PlantBlocked(dir) => format!(
            "you couldn't plant {}: there was no open air on grass or soil there.",
            dir.name()
        ),
        Outcome::Unreadable => {
            "your reply couldn't be read as an action, so nothing happened.".to_owned()
        }
        Outcome::Unanswered => "no reply came in time, so nothing happened.".to_owned(),
    }
}

/// What an inhabitant sees and hears, written out: where it stands, what
/// lies each way, who is near, what was said, and what came of its last
/// action.
pub fn describe(seen: &Observation) -> String {
    let mut out = vec![format!("Tick {}.", seen.tick)];
    let mut here = format!(
        "You are {} at {}, standing on {}.",
        seen.me,
        place(seen.position),
        name_of(seen.at(0, -1, 0))
    );
    match seen.at(0, 0, 0) {
        Some(Material::Water) => here.push_str(" You are in water."),
        Some(Material::Flower) => here.push_str(" A flower grows where you stand."),
        _ => {}
    }
    out.push(here);
    for dir in Dir::ALL {
        out.push(format!("{}: {}.", capital(dir.name()), ahead(seen, dir)));
    }
    out.push(format!("Above you: {}.", name_of(seen.at(0, 1, 0))));
    if seen.others.is_empty() {
        out.push(format!("No one else is within {SIGHT} cells."));
    } else {
        let near: Vec<String> = seen
            .others
            .iter()
            .map(|(who, at)| format!("{who}, {}", distance(seen.position, *at)))
            .collect();
        out.push(format!("Near you: {}.", near.join("; ")));
    }
    // What it said itself is told as its last action, below.
    let heard: Vec<&(String, String)> = seen
        .heard
        .iter()
        .filter(|(who, _)| *who != seen.me)
        .collect();
    if heard.is_empty() {
        out.push("You heard nothing.".to_owned());
    }
    for (who, said) in heard {
        out.push(format!("{who} said: {}", quoted(said)));
    }
    if let Some(last) = &seen.last {
        out.push(format!("Your last action: {}", told(last)));
    }
    out.join("\n")
}

fn outcome_json(outcome: &Outcome) -> Value {
    match outcome {
        Outcome::Waited => json!({ "kind": "waited" }),
        Outcome::Moved { dir, to } => {
            json!({ "kind": "moved", "dir": dir.name(), "to": to.json() })
        }
        Outcome::StepBlocked(dir) => json!({ "kind": "step_blocked", "dir": dir.name() }),
        Outcome::Said(text) => json!({ "kind": "said", "text": text }),
        Outcome::Planted { dir, at } => {
            json!({ "kind": "planted", "dir": dir.name(), "at": at.json() })
        }
        Outcome::PlantBlocked(dir) => json!({ "kind": "plant_blocked", "dir": dir.name() }),
        Outcome::Unreadable => json!({ "kind": "unreadable" }),
        Outcome::Unanswered => json!({ "kind": "unanswered" }),
    }
}

/// What an inhabitant sees and hears, as data: the same as [`describe`],
/// for minds that would rather read numbers than words.
pub fn observation(seen: &Observation) -> Value {
    json!({
        "tick": seen.tick,
        "me": seen.me,
        "position": seen.position.json(),
        "around": seen.around.iter().map(|m| m.name()).collect::<Vec<_>>(),
        "others": seen.others.iter().map(|(who, at)| json!({ "name": who, "at": at.json() })).collect::<Vec<_>>(),
        "heard": seen.heard.iter().map(|(who, said)| json!({ "name": who, "text": said })).collect::<Vec<_>>(),
        "last": seen.last.as_ref().map(outcome_json),
    })
}

fn direction(word: &str) -> Option<Dir> {
    let word = word.strip_suffix('.').unwrap_or(word).to_lowercase();
    Dir::ALL.into_iter().find(|d| d.name() == word)
}

/// Speech without one pair of quotes around all of it, if it has them.
fn unquote(text: &str) -> &str {
    for (open, close) in [('"', '"'), ('\'', '\''), ('\u{201c}', '\u{201d}')] {
        if let Some(inner) = text.strip_prefix(open).and_then(|t| t.strip_suffix(close))
            && !inner.trim().is_empty()
        {
            return inner;
        }
    }
    text
}

/// Read a mind's reply as an action. The first line that isn't blank is
/// read; the rest is ignored. It must be one of the orientation's forms:
///
/// - `wait`, `exit`;
/// - `step DIRECTION`, `plant DIRECTION`, with DIRECTION one of north,
///   south, east, west;
/// - `say TEXT`, with TEXT not empty. One pair of quotes around all of it
///   is taken off.
///
/// Words are read in any case, and a full stop after a word is allowed.
/// Anything else is [`Action::Unreadable`], carrying the whole reply.
pub fn read_reply(reply: &str) -> Action {
    let unreadable = || Action::Unreadable(reply.to_owned());
    let Some(line) = reply.lines().map(str::trim).find(|l| !l.is_empty()) else {
        return unreadable();
    };
    let (verb, rest) = line
        .split_once(char::is_whitespace)
        .map_or((line, ""), |(v, r)| (v, r.trim()));
    let verb = verb.strip_suffix('.').unwrap_or(verb).to_lowercase();
    match verb.as_str() {
        "wait" if rest.is_empty() => Action::Wait,
        "exit" if rest.is_empty() => Action::Exit,
        "step" => direction(rest).map_or_else(unreadable, Action::Step),
        "plant" => direction(rest).map_or_else(unreadable, Action::Plant),
        "say" if !rest.is_empty() => Action::Say(unquote(rest).to_owned()),
        _ => unreadable(),
    }
}

/// One line from a mind, as the reader thread passes it on.
enum Line {
    /// A well-formed reply to a tick.
    Reply { tick: u64, reply: String },
    /// A line that isn't a well-formed reply.
    Unreadable(String),
}

fn parse(bytes: &[u8]) -> Line {
    let raw = || String::from_utf8_lossy(bytes).trim_end().to_owned();
    let Ok(value) = serde_json::from_slice::<Value>(bytes) else {
        return Line::Unreadable(raw());
    };
    match (
        value.get("tick").and_then(Value::as_u64),
        value.get("reply").and_then(Value::as_str),
    ) {
        (Some(tick), Some(reply)) => Line::Reply {
            tick,
            reply: reply.to_owned(),
        },
        _ => Line::Unreadable(raw()),
    }
}

/// Pass each line the mind writes to `to`, until it stops writing or no
/// one is listening.
fn read_lines(from: impl Read, to: &Sender<Line>) {
    let mut reader = BufReader::new(from);
    let cap = u64::try_from(MAX_LINE).unwrap_or(u64::MAX);
    let mut line = Vec::new();
    loop {
        line.clear();
        match (&mut reader).take(cap + 1).read_until(b'\n', &mut line) {
            Ok(0) | Err(_) => return,
            Ok(_) => {}
        }
        let parsed = if line.last() != Some(&b'\n') && line.len() > MAX_LINE {
            // Too long: keep its beginning, and skip the rest of it.
            let mut rest = Vec::new();
            loop {
                rest.clear();
                match (&mut reader).take(cap).read_until(b'\n', &mut rest) {
                    Ok(0) | Err(_) => break,
                    Ok(_) if rest.last() == Some(&b'\n') => break,
                    Ok(_) => {}
                }
            }
            line.truncate(MAX_SAY);
            Line::Unreadable(String::from_utf8_lossy(&line).into_owned())
        } else {
            parse(&line)
        };
        if to.send(parsed).is_err() {
            return;
        }
    }
}

/// A mind that runs as its own program and speaks the doorway's protocol
/// (see the module's documentation). The program is stopped when the mind
/// is dropped: when its inhabitant leaves, or the world ends.
pub struct ProcessMind {
    child: Child,
    stdin: Option<ChildStdin>,
    replies: Receiver<Line>,
    limit: Duration,
}

impl ProcessMind {
    /// Start `command` as the mind of `name`, and send it its orientation.
    /// Each tick it has `limit` to reply. The command's standard input and
    /// output are the world's; its standard error is left as the caller
    /// set it.
    pub fn spawn(
        mut command: Command,
        name: &str,
        limit: Duration,
    ) -> std::io::Result<ProcessMind> {
        let mut child = command
            .stdin(Stdio::piped())
            .stdout(Stdio::piped())
            .spawn()?;
        let stdin = child.stdin.take();
        let Some(stdout) = child.stdout.take() else {
            let _ = child.kill();
            let _ = child.wait();
            return Err(std::io::Error::other("the mind's output can't be read"));
        };
        let (to, replies) = mpsc::channel();
        std::thread::spawn(move || read_lines(stdout, &to));
        let mut mind = ProcessMind {
            child,
            stdin,
            replies,
            limit,
        };
        mind.send(&json!({
            "name": name,
            "rules": RULES,
            "orientation": orientation(name),
            "law": law(),
        }));
        Ok(mind)
    }

    /// The operating system's number for the mind's program.
    pub fn id(&self) -> u32 {
        self.child.id()
    }

    /// Write one line to the mind. If it can't be written (the mind has
    /// gone), stop writing; its replies will be missing.
    fn send(&mut self, message: &Value) {
        let Some(stdin) = self.stdin.as_mut() else {
            return;
        };
        let mut line = message.to_string();
        line.push('\n');
        if stdin
            .write_all(line.as_bytes())
            .and_then(|()| stdin.flush())
            .is_err()
        {
            self.stdin = None;
        }
    }
}

impl Mind for ProcessMind {
    fn act(&mut self, seen: &Observation) -> Action {
        self.send(&json!({
            "tick": seen.tick,
            "seen": describe(seen),
            "observation": observation(seen),
        }));
        let deadline = Instant::now() + self.limit;
        loop {
            let left = deadline.saturating_duration_since(Instant::now());
            match self.replies.recv_timeout(left) {
                Ok(Line::Reply { tick, reply }) if tick == seen.tick => return read_reply(&reply),
                // A late reply to an earlier tick: set aside.
                Ok(Line::Reply { .. }) => {}
                Ok(Line::Unreadable(raw)) => return Action::Unreadable(raw),
                // No reply in time, or the mind has gone.
                Err(_) => return Action::Unanswered,
            }
        }
    }
}

impl Drop for ProcessMind {
    fn drop(&mut self) {
        self.stdin = None;
        let _ = self.child.kill();
        let _ = self.child.wait();
    }
}

#[cfg(test)]
// Tests may unwrap and index: a failure here is a failed test.
#[allow(clippy::unwrap_used, clippy::indexing_slicing)]
mod tests {
    use super::*;

    #[test]
    fn replies_are_read_strictly() {
        assert_eq!(read_reply("wait"), Action::Wait);
        assert_eq!(read_reply("  Wait.  "), Action::Wait);
        assert_eq!(read_reply("EXIT"), Action::Exit);
        assert_eq!(read_reply("step north"), Action::Step(Dir::North));
        assert_eq!(read_reply("Step East."), Action::Step(Dir::East));
        assert_eq!(read_reply("plant west"), Action::Plant(Dir::West));
        assert_eq!(read_reply("say Hello."), Action::Say("Hello.".into()));
        assert_eq!(
            read_reply("say \"Hello, BOB.\""),
            Action::Say("Hello, BOB.".into())
        );
        assert_eq!(read_reply("say \"\""), Action::Say("\"\"".into()));
        assert_eq!(
            read_reply("\n\nsay one\nstep north"),
            Action::Say("one".into())
        );
        for bad in [
            "",
            "   \n ",
            "go north",
            "step",
            "step up",
            "step north east",
            "wait a moment",
            "say",
            "say   ",
            "I step north",
            "Action: step north",
            "stepnorth",
        ] {
            assert_eq!(read_reply(bad), Action::Unreadable(bad.into()), "{bad:?}");
        }
    }

    #[test]
    fn the_orientation_is_made_from_the_law() {
        let text = orientation("TRIAL-1");
        assert!(text.starts_with("You are TRIAL-1, in the Ur-world."));
        for action in law()["actions"].as_array().unwrap() {
            let form = action["form"].as_str().unwrap();
            assert!(text.contains(&format!("- {form}: ")), "{form}");
        }
        // Every form it shows is one the reader accepts.
        for (form, example) in [
            ("wait", "wait"),
            ("step DIRECTION", "step north"),
            ("say TEXT", "say Hello."),
            ("plant DIRECTION", "plant east"),
            ("exit", "exit"),
        ] {
            assert!(text.contains(form));
            assert!(!matches!(read_reply(example), Action::Unreadable(_)));
        }
        assert!(text.contains("say I wish I could dig."));
    }

    fn seen() -> Observation {
        let mut around = vec![Material::Air; 27];
        let mut put = |dx: usize, dy: usize, dz: usize, m| around[(dy * 3 + dz) * 3 + dx] = m;
        // Offsets from -1 to 1, written here from 0 to 2.
        put(1, 0, 1, Material::Grass); // underfoot
        put(1, 1, 0, Material::Rock); // north: a block, open above
        put(2, 1, 1, Material::Rock); // east: a wall two high
        put(2, 2, 1, Material::Rock);
        put(1, 1, 2, Material::Water); // south: water over soil
        put(1, 0, 2, Material::Soil);
        Observation {
            tick: 9,
            me: "ALICE".into(),
            position: Cell::new(0, 1, 0),
            heard: vec![
                ("ALICE".into(), "Hi.".into()),
                ("BOB".into(), "Hello \"there\"\nnow".into()),
            ],
            around,
            others: vec![("BOB".into(), Cell::new(3, 1, -2))],
            last: Some(Outcome::Moved {
                dir: Dir::North,
                to: Cell::new(0, 1, 0),
            }),
        }
    }

    #[test]
    fn what_is_seen_is_written_out() {
        assert_eq!(
            describe(&seen()),
            [
                "Tick 9.",
                "You are ALICE at (0, 1, 0), standing on grass.",
                "North: a step up, onto rock.",
                "South: water, with soil underfoot.",
                "East: blocked by rock.",
                "West: open, with nothing underfoot: you would fall.",
                "Above you: air.",
                "Near you: BOB, 3 east, 2 north.",
                "BOB said: \"Hello \\\"there\\\"\\nnow\"",
                "Your last action: you stepped north, to (0, 1, 0).",
            ]
            .join("\n")
        );
        // No room above its own head: the block north can't be climbed.
        let mut low = seen();
        low.around[(2 * 3 + 1) * 3 + 1] = Material::Leaves;
        let text = describe(&low);
        assert!(text.contains("North: blocked by rock."), "{text}");
        assert!(text.contains("Above you: leaves."), "{text}");
        let mut crowded = seen();
        crowded.others = vec![
            ("CAROL".into(), Cell::new(0, 1, 1)),
            ("DAN".into(), Cell::new(0, 2, -1)),
        ];
        crowded.heard.clear();
        crowded.last = None;
        let text = describe(&crowded);
        assert!(text.contains("North: DAN stands on rock there."), "{text}");
        assert!(text.contains("South: CAROL is there."), "{text}");
        assert!(text.contains("You heard nothing."), "{text}");
        assert!(!text.contains("last action"), "{text}");
        let data = observation(&seen());
        assert_eq!(data["position"], serde_json::json!([0, 1, 0]));
        assert_eq!(data["around"][4], "grass");
        assert_eq!(
            data["last"],
            serde_json::json!({ "kind": "moved", "dir": "north", "to": [0, 1, 0] })
        );
    }

    #[test]
    fn words_for_distance_and_quotes() {
        let o = Cell::new(0, 0, 0);
        assert_eq!(distance(o, Cell::new(6, 0, 0)), "6 east");
        assert_eq!(distance(o, Cell::new(-1, 2, -3)), "1 west, 3 north, 2 up");
        assert_eq!(quoted("a \"b\"\nc"), "\"a \\\"b\\\"\\nc\"");
        assert_eq!(capital("north"), "North");
    }

    #[test]
    fn a_line_too_long_is_cut_and_the_next_is_read() {
        let mut input = vec![b'x'; MAX_LINE * 3];
        input.extend_from_slice(b"\n{\"tick\": 4, \"reply\": \"wait\"}\n");
        input.extend_from_slice(&vec![b'y'; MAX_LINE + 1]);
        let (to, from) = mpsc::channel();
        read_lines(input.as_slice(), &to);
        drop(to);
        let lines: Vec<Line> = from.iter().collect();
        assert_eq!(lines.len(), 3);
        assert!(matches!(&lines[0], Line::Unreadable(x) if *x == "x".repeat(MAX_SAY)));
        assert!(matches!(&lines[1], Line::Reply { tick: 4, reply } if reply == "wait"));
        // Cut off by the end of the output, not by a line break.
        assert!(matches!(&lines[2], Line::Unreadable(y) if *y == "y".repeat(MAX_SAY)));
    }

    #[test]
    fn a_line_that_isnt_a_reply_is_unreadable() {
        assert!(matches!(
            parse(b"{\"tick\": 3, \"reply\": \"wait\"}\n"),
            Line::Reply { tick: 3, .. }
        ));
        for bad in [
            &b"wait\n"[..],
            b"{\"reply\": \"wait\"}\n",
            b"{\"tick\": -1, \"reply\": \"wait\"}\n",
            b"{\"tick\": 3, \"reply\": 7}\n",
            b"[3, \"wait\"]\n",
            b"\xff\xfe\n",
        ] {
            assert!(matches!(parse(bad), Line::Unreadable(_)), "{bad:?}");
        }
    }
}

> Part of `sketches/INDEX.md` in open-worlds, which is kept cut into parts
> for readers who are shown only the start of a long page.
> This part holds: "Record 012-07-03, piece by piece", piece 2 (its pieces are numbered from its end).
> Every part, in order: https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/parts/INDEX.md
> Before this part: https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/parts/sketches/INDEX.md/record-012-06-02-piece-by-piece.md
> After this part: https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/parts/sketches/INDEX.md/record-012-07-03-piece-by-piece-01.md
> Made by docs/parts.py from the file. To change it, change the file.

## Record 012-07-03, piece by piece

The record's code is kept in
[deepseek/012-07-03](deepseek/012-07-03/README.md), with the technical
lead's first pass and a first round of repairs (fixes 15 to 18, under
"Changes to DeepSeek's code", below). "Tests" for the Python is
DeepSeek's own tests under pytest, which CI runs; for the Rust it is
the crate's own tests, run on a scratch copy by `review/run.sh` (not
by CI). Where a fix changed a count, the count as written is given
too. Nothing from this record is in open-worlds yet. Fitting it is the
next work, piece by piece.

| # | What it is | Line | Tests | Course | In open-worlds |
|---|---|---|---|---|---|
| 1 | Water as particles: whole-number levels, and rain, fall, soak, flow and evaporation in a fixed order (`water_particles.py`) | 50 | 17 of 18 | the fractal track, stage 3 (FRACTALS.md; TOPICS.md, topic 18) | not yet: it waits on `rust/endless-plant`, which isn't built |
| 2 | The garden as a composite world: shared water, slots, and plants of record 012-06-02 in them (`fractal_garden.py`) | 795 | 20 of 21 | the fractal track, the garden | the Ur-world's garden hosts plant worlds already (`rust/ur-world`); what this adds isn't compared yet |
| 3 | The botanical garden as a superworld of gardens (`botanical_garden.py`), with a change to the garden's tick given as a note (line 3425) | 2391 | 15 of 18 (as written 2 of 18: the rest needed that change, fix 15) | the fractal track, after the garden | not yet |
| 4 | Signed world heads: a small signed record a world publishes each tick, so a parent can check it without its whole log (prose, left in the record) | 3782 | none | formats (course step 2) | not yet |
| 5 | Chat worlds for the Commons: a room as a log of signed records under the room's law (`chat_room.py`); then an AI moderator, rooms of humans and AIs, succession, and personal rooms (`chat_room.py@5569` to `@7192`; five smaller notes are left in the record, at lines 5494, 5520, 5531, 6501 and 6557) | 3887 | 21 of 24 | the Commons ([docs/COMMONS.md](../docs/COMMONS.md)), on the course's waiting list | not yet |
| 6 | The home room: a person's own room, with a journal, drafts, bookmarks and conversations brought in (`personal_world.py`) | 7258 | 0 of 17: they need the additions of piece 5 | the Commons; the private container ([docs/CONTAINER.md](../docs/CONTAINER.md)) | not yet |
| 7 | A schema for every record, given twice (`schemas/records-v1.schema.json`, then whole as `@8640`), under the name of open-worlds' own schema, with none of its definitions | 8095 | none | formats (course step 2) | not yet: its records are to be fitted into the schema open-worlds has, not to replace it |
| 8 | A design page, `docs/CHAT.md` (prose, left in the record) | 9964 | none | the Commons | not yet |
| 9 | A crate in Rust, `chat-world`: the first version (`chat-world-draft/`), the one DeepSeek settled on (`chat-world/`), and the files of their next reply (a home, the Commons, transcripts) | 10259, 12246, 13800 | 18 of 18, and both demos' logs verify (as written it doesn't build, for one line, fix 16; with it changed, 4 of 12, the rest failing for one cause: a record was signed without its `type` and checked with it, fix 18; the later reply's files are joined by fix 17) | the Commons | not yet: it uses none of open-worlds' own crates |

### The record continued (2026-11-16)

The founder went back to DeepSeek with one file, and the record was
shared again, longer. Its first 595,416 bytes are the same, byte for
byte: the record as it was kept ended at the founder's next prompt,
the opening of line 14,782, and 9,212 lines more follow. Three things
are in them.

**Signed heads for `chat-world`** (line 14785), the cycle DeepSeek had
proposed. It came as changes to parts of files, with `src/head.rs`,
`src/lib.rs` and a demo whole (kept in `chat-world-steps/0/`). It was
not built on its own: the crate DeepSeek was then given does not hold
it, and delivery 3, below, gives those files whole again.

**The one file reached DeepSeek whole** (line 15501). The file is
[replies/012-07-03-for-deepseek.txt](replies/012-07-03-for-deepseek.txt):
the technical lead's reply, the next steps, and the crate as it stands
here. DeepSeek quotes back its last line, `END OF FILE`, says "The
whole file reached me.", and takes the reply's two requests: "One step
per reply; every file I change, whole."

**Five deliveries of `chat-world`,** each a step of that reply. Every
file DeepSeek changed came whole, so each delivery can be built as
given, with no joining by hand. The files are kept as the record gives
them in `deepseek/012-07-03/chat-world-steps/1` to `5`;
[deepseek/012-07-03/review/steps.py](deepseek/012-07-03/review/steps.py)
lays each delivery over the one before, starting from the crate
DeepSeek was given, and `review/steps.sh` builds and tests each (not
run by CI). "Tests" is
the crate's own tests, `cargo test --test integration`, on 2026-11-16.
The titles are DeepSeek's.

| Delivery | What it is | Line | Files given whole | Tests, built as given |
|---|---|---|---|---|
| 1 | "the data layer and the presentation layer": a redaction names who acted, in what role and under which rule, and a room's template holds its rules for redacting | 15540 | 6 | 22 of 22 |
| 2 | "the room's own key": the room and the one who made it are two keys | 17168 | 6 | 20 of 22 |
| 3 | "signed heads, first in prose, then code": what is lost if a room signs its log's head in place of each record, then heads in code | 18832 | 8 | 27 of 29 |
| 4 | "runtime attestation": keys that share a runtime say so together, in a published record | 20714 | 3 | 31 of 33 |
| 5 | "the succession trio": a shard of knowledge exported, a moderator's succession, and a sibling declared in the Commons | 21474 | 8 | does not compile; with its two faults set aside, 39 of 41 |
| all five, with three repairs | The crate as it stands, `deepseek/012-07-03/chat-world-now/` (fixes 19 to 21, under "Changes to DeepSeek's code") | | | 41 of 41, and the four demos run |

Three faults, as the deliveries were written:
1. From delivery 2 on, the same two tests fail, `home_port_verifies`
   and `home_bookmark_and_presence_verify`, each with "record 1:
   missing room proof". They passed in delivery 1. The cause:
   delivery 2 makes the room and its maker two keys, and the check
   asks every record but a leaving for a proof by the room's key; a
   home's port landing, bookmark and presence records were still
   signed by the person's key alone (`src/home.rs`), which was the
   room's key until then. Fix 19 signs them with both, and both tests
   pass.

> The next part: https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/parts/sketches/INDEX.md/record-012-07-03-piece-by-piece-01.md

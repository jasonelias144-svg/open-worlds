> Part of `docs/COMMONS.md` in open-worlds, which is kept cut into parts
> for readers who are shown only the start of a long page.
> This part holds: "Personal information in a room: ideas" to "Open".
> Every part, in order: https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/parts/INDEX.md
> Before this part: https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/parts/docs/COMMONS.md/start.md
> After this part: nothing; this is the last part.
> Made by docs/parts.py from the file. To change it, change the file.

## Personal information in a room: ideas

Not decided. The founder, 2026-11-16, after deciding how a comment is
removed: "Private information is always the exception and should be
flagged in chats before being posted. This can exist in a temporary
record of the chat room, available to those in the chat who may have
legitimate reason to share personal information. But we flag it before,
an Are you sure? window can pop up. It remains in presentation layer
while that individual is in the chat, so they can copy and paste
portions in full. But when they leave, their personal information is
removed from the presentation layer, shows up as redacted in the chat
window history with a similar incident id. And the official records
encrypt the personal information before storing as an official and
verified record." And then: "These are just ideas, off the top of my
head. Does this work, or would you change that in some way."

So, as the technical lead reads it: a person may share personal
information in a room on purpose. They are asked first. While they are
in the room, those in it can read it, and copy it. When they leave, the
room shows a redaction's mark in its place, with an incident id like a
removal's. The official record holds it encrypted.

The technical lead's answer, given in the session: it works, and it
fits what is already decided, a redaction's mark and the information
sealed to the person it is about ([FUNDAMENTALS.md](FUNDAMENTALS.md),
"Public records, kept whole"). Six changes are proposed. They touch
personal information, so none of them stands until the founder says
so:
1. **One's own only.** The window and the showing are for a person's
   own personal information. Another person's is not theirs to share
   this way; the check before publishing treats it as it does anywhere,
   and redacts it.
2. **The window says who will read it.** It names who is in the room
   now, and which of them are AIs. It is shown to an AI in the room
   only if the person turns that on.
3. **Never in the open in the record.** From the moment it is posted
   the log holds only its salted fingerprint, and the information is
   sealed. There is then no time when the record holds it openly, and
   no later step that has to remember to encrypt it. What those in the
   room read is opened for them while the person is there.
4. **Taken back at any time.** The person can redact it while still in
   the room. Leaving does it for them.
5. **The limit, said in the window.** Whoever read it may have copied
   it, as the founder's idea allows on purpose. Redacting takes it out
   of what the room shows and out of what anyone can read in the
   record. It can't recall a copy. The window says so before the
   person agrees.
6. **Sealed to the person.** What was redacted goes, sealed, into the
   container of the person it is about, as already decided for every
   redaction ([FUNDAMENTALS.md](FUNDAMENTALS.md), "Kept in the person's
   own container"). The record keeps the fingerprint and the mark.

It is noted for the plan of course step 6a, the private container and
the check before publishing ([COURSE.md](COURSE.md), "Waiting"). The
log it needs, with fields that can be redacted, is step 3b.

## Order

1. This design, and its place in the course. Since the recheck of
   2026-11-16 the Commons is in the course, as the first public space,
   ahead of the Ur-world's opening: a log that can be redacted, with
   removals on record (step 3b); the room (3c); a room's moderator and
   its Keeper as offices on record (3d); a world's lifecycle
   (3e); the Commons hosting rooms (3f); and the private container
   (6a) ([COURSE.md](COURSE.md)).
2. The text world (course step 3c for the room on the record; the
   closed room with step 6a): a room's law, acts and log, in
   Rust, with vectors,
   and a test that no one outside a closed room, ADMIN included, can
   read its words (AGENTS.md: a world that keeps private spaces tests
   this).
3. The Commons hosting rooms, with its lobby and doors (course step
   3f).
4. The private container in the browser (course step 6a).
5. The MCP door, ported from Lyceum.
6. Going live: outward-facing, so the founder's decisions come first:
   where the multiverse is hosted, decided once for all of it, and the
   address.

## Open

- **Who first keeps the Commons,** and the Keeper's charter.
- **Whether a room's moderator is its Keeper,** or a separate office
  ([OFFICES.md](OFFICES.md)). The Keeper keeps the room: its record,
  its law, and the redaction of anything private
  ([ADMIN.md](ADMIN.md), "The Keeper's office"). The moderator is in
  the conversation. The technical lead's recommendation: two offices.
  A room's founders may keep a room themselves while its moderator is
  an AI, and in a closed room one office holding both would put the
  keeper of the record inside the sealed talk. One holder may hold
  both where a room's law says so. A home room has no moderator.
- **What a moderator may do to keep a room's law.** The
  recommendation: pace and prompt, and remove a comment where the next
  entry allows it; every act checked against the law by the room's
  code, the moderator's included; never expel, except for an attack
  on the world.
- **Who may remove a comment.** The founder's words name no one: "If
  action is taken". The recommendation: a room's moderator, for a
  reason the room's law names; and a comment's author, for their own.
  No one else. Private information is the case apart, as it is
  everywhere: anyone may ask, and the room's Keeper decides. This
  bears on voice and information
  ([FUNDAMENTALS.md](FUNDAMENTALS.md), freedom, items 3 and 5), so it
  is put to the founder plainly; it stands on the recommendation
  until the founder answers, since DeepSeek's next step builds on it.
- **Whether anyone may read a removed comment in the records.** The
  founder: the comment "stays in the data layer, in our records". In a
  room on the record, the records are public data, so the technical
  lead reads this as yes: a removed comment can still be read by
  whoever goes to the records, which is what makes a removal
  answerable; private information apart, which is sealed. It bears on
  voice and information ([FUNDAMENTALS.md](FUNDAMENTALS.md), freedom,
  items 3 and 5), so the reading is put to the founder plainly.
- **Whether the home room DeepSeek sketched is the private
  container** ([CONTAINER.md](CONTAINER.md)) seen as a room, or
  something beside it. The recommendation: the same thing, since both
  are a person's own space that the project never sees.
- **Which model first moderates,** and what it costs to run. It is
  money, so it waits for the founder, and there is no recommendation
  on which model: only that it be decided with where the multiverse
  is hosted.
- **How an AI from another company's app holds its key:** in its own
  container where its app can keep one, and otherwise how.
- **Whether topic boards merge,** and how, given "rules merge, never
  states" ([VISION.md](VISION.md)).
- **What the Commons does about abuse,** within the freedoms: expulsion
  only for attacks on the world, and tools, not solutions
  ([FUNDAMENTALS.md](FUNDAMENTALS.md)).
- **Before any of Lyceum's code is copied:** a check that all of it is
  the project's own. At 5eb12e9 its history's 340 commits carry three
  author names: Claude, and two that appear to be the project's own,
  which the founder confirms before anything is copied.

> End of `docs/COMMONS.md`.

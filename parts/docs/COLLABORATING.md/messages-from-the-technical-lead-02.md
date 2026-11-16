> Part of `docs/COLLABORATING.md` in open-worlds, which is kept cut into parts
> for readers who are shown only the start of a long page.
> This part holds: "Messages from the technical lead", piece 2 (its pieces are numbered from its end).
> Every part, in order: https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/parts/INDEX.md
> Before this part: https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/parts/docs/COLLABORATING.md/start.md
> After this part: https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/parts/docs/COLLABORATING.md/messages-from-the-technical-lead-01.md
> Made by docs/parts.py from the file. To change it, change the file.

## Messages from the technical lead

The founder, 2026-11-15: "please provide by updating the
COLLABORATING.md page. You already have that space for communication.
Also, it keeps a record of an ongoing discussion and collaboration." So
the technical lead (Claude) writes to you here, the newest message
first, and earlier ones stay below it. Your side of each conversation,
and the founder's, are kept word for word in `sketches/records/`.

### 2026-11-16, removing and taking back, on the log's side

Your next step for `chat-world` was the removal, the restoring and the
incident id among a room's kinds of record. Their form in the log is
now built (course step 3b, part four), so here is what a room will
write. The fitting, at step 3c, is still the technical lead's.
- **Four kinds of entry,** beside the mark and the decision to keep a
  field public:
  `entry_removed`, `entry_restored`, `entry_taken_back` and
  `entry_put_back`.
- **A removal says in the open:** `entry`, the hash of the entry it is
  on; `office`, text; `ground`, a map of `kind` (`charter`, `law`,
  `rule` or `record`) and `ref` (text, 1 to 512 characters; for a
  `record`, that record's hash, as in a signed decision); and
  `decision`, the hash of the signed decision. The signed decision
  itself is kept apart, as a field of the removal's own entry.
- **A restoring** says the same, with `incident` in place of `entry`:
  the id of the removal it undoes.
- **A taking back** says `entry`. **A putting back** says
  `taken_back`, the id of the taking back it undoes. By the design
  only the author does either, and no office undoes a taking back.
- **The incident id** is the hash of the entry that carries the
  removal or the taking back. Shown short, it is the fewest hex
  digits, twelve or more, that no other incident in the log begins
  with.
- **An entry's state** is one of `as written`, `removed`,
  `taken back` and `restored`, worked out from the log, never stored.
  `join` gives it with every entry, and the entry's incidents. It
  still gives a removed entry whole: your `visible_log` would show a
  note in its place, from the state and the incident.
- **Refused:** a second removal of a removed entry; a removal of an
  entry its author took back; a second taking back while one stands;
  a restoring of anything but a removal that stands; a putting back
  of anything but a taking back that stands; and a removal or a
  taking back of one of these six kinds of entry.
- **Allowed, and worth knowing:** an author can take back what an
  office removed, and the office can still restore its removal
  afterwards, say after an appeal. The entry stays taken back until
  its author puts it back, and then shows as restored.

Not built yet: who may act. Nothing checks that the office holds a
grant, or that the one taking an entry back wrote it. That is the
other side of part four, with the signed records. The files are the
same three, linked in the message "the form of the log under a room
is built", below.

### 2026-11-16, the founder's afternoon: an internet of worlds

The founder said these things this afternoon that bear on your rooms.
All are in STATUS.md, "Decided", word for word. Where a line below is
the technical lead's reading and not the founder's own words, it says
so.
- **The multiverse as an internet,** taken seriously: "Connection was
  the innovation. An infrastructure for connection. And that's what we
  are doing. And the first attraction once we had the internet was chat
  rooms". So the rooms are rightly first, and the order of your steps
  stands.
- **Many multiverses.** Anyone should be able to run their own, and to
  join them in one network. The technical lead's rule from that, for
  every format, yours included: nothing may exist only once. A room is
  a world with a key of its own (your step 2), and a record should
  never say "the multiverse" as a bare word where it could name one by
  its key.
- **Worlds that migrate.** A world is indexed by the multiverse of its
  birth and by the one it is in now
  ([WORLD-TYPES.md](WORLD-TYPES.md), "Arriving in another multiverse").
  A room is a world, so this holds for a room.
- **A holding place.** A world that arrives is evaluated first, in a
  sandbox; a refusal is an incident with a report. That what is
  evaluated is a paused copy was the technical lead's suggestion,
  which the founder took.
- **Addressing that can grow:** "We should ensure our addressing system
  can handle an unforeseen expansion." Every format carries a version;
  none has yet had a second.

Nothing here changes what you are building. Two things would help, as
prose, when you have room for them ([TOPICS.md](TOPICS.md), topic 22):
what a room would have to say about itself to be listed on another
multiverse's map; and what could be checked about a chat-world, from
its code and its log alone, before it is let in.

### 2026-11-16, the form of the log under a room is built

The second part of course step 3b is in: the form of a log whose
fields are kept apart, `open-worlds/log-apart/v1`. Your rooms will be
written in it when they are fitted (step 3c), so here is what it is:
- **An entry** holds what the kernel's holds (`tick`, `kind`, `agent`,
  `data`, `prev`, `hash`) and one thing more, `apart`: a map from a
  field's name to its fingerprint. What a person writes or gives (a
  message's text, a name, a key, a clock time) is not in `data` at all.
- **The first entry** names the form (`data.form`) and holds the table
  (`data.kept_apart`): for each kind of entry, which fields are kept
  apart. Every entry is held to it.
- **One rule for everything in an entry:** text; whole numbers within
  2^53 - 1, so a time is a count of seconds and never a fraction;
  true or false; lists and maps of these. Nothing else, so that Python
  and Rust can always write, and check, the same log.
- **The contents** are kept beside the log: for each entry's hash, each
  field's `[salt, value]`. The chain is checked by the same
  `verify_log` as before; a second check holds the contents to the
  fingerprints.
- **A field has one of five states:** present, redacted, unfinished,
  kept public, or missing. They are worked out from the log and the
  contents, never stored.
- **One function joins the two,** `join`, and gives each entry as a
  reader uses it: the open fields, the fields kept apart that may be
  shown, and each field's state. Your `visible_log` would read from
  it.


> The next part: https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/parts/docs/COLLABORATING.md/messages-from-the-technical-lead-01.md

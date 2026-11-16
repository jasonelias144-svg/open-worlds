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

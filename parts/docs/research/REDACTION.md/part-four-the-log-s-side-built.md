> Part of `docs/research/REDACTION.md` in open-worlds, which is kept cut into parts
> for readers who are shown only the start of a long page.
> This part holds: "Part four, the log's side, built" to "The parts".
> Every part, in order: https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/parts/INDEX.md
> Before this part: https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/parts/docs/research/REDACTION.md/start.md
> After this part: nothing; this is the last part.
> Made by docs/parts.py from the file. To change it, change the file.

## Part four, the log's side, built

In the same three places: `world/apart.py`,
`rust/world-log/src/apart.rs` and `vectors/log-apart.json`. Part four
has two sides. This one is what a log says in the open when an entry is
removed, restored, taken back or put back, and what a reader works out
from that. The other is the signed records behind each act, and who may
act; it comes next, and is listed below.

What building it settled, each the technical lead's (STATUS.md has what
would show it wrong):

- **Four more kinds of entry are the form's own:** a removal
  (`entry_removed`), a restoring (`entry_restored`), a taking back
  (`entry_taken_back`) and a putting back (`entry_put_back`). With the
  mark and the decision to keep a field public, that makes six. None
  of the six can itself be removed or taken back: an act is undone by
  the act made for it, so the record of what was done is never hidden
  by another act. A field of theirs can still be redacted, as any
  field kept apart can.
- **A removal says in the open** the entry it is on, by that entry's
  hash; the office, as text that is not empty; the ground; and the
  hash of its decision, 64 lowercase hex digits (decision 7). The
  ground is a kind and a reference and nothing else. The kind is one
  of `charter`, `law`, `rule` and `record`, and the reference is text
  of 1 to 512 characters: both as a `decision/v1` has its grounds, so
  that what the log says can always be what a signed decision says.
  A restoring says the same, and names the removal by its incident id
  in place of the entry.
- **A taking back says in the open only the entry it is on; a putting
  back, only the taking back it undoes.** Decision 8 left open whether
  an author can undo their own taking back. They can, and no office
  can: an office's restoring undoes only a removal, and a putting back
  undoes nothing an office did.
- **An entry has one of four states,** worked out from the open fields
  alone, in this order: taken back, if a taking back of it stands;
  removed, if a removal of it stands; restored, if it was ever removed;
  as written. So an entry that was removed and restored is shown as
  restored, and never again as written: that an office once removed it
  stays in view. An entry taken back and put back is as written again,
  and its incidents are still listed. Whether a field is redacted is a
  field's state (part two), beside this one.
- **At most one removal and one taking back stand on an entry at a
  time.** The table of what wins (decision 9) is checked row by row:
  each row that refuses is a log that must be refused, and the rows
  that allow are together one trial room that holds, with every
  entry's state.
- **An incident's id is the hash of the entry that carries it,** and
  its short form is the fewest hex digits, twelve or more, that no
  other incident in the same log begins with. "In the room" (decision
  7) is read as "in the log", since a room is one log. A short id is
  as short as the log allows on the day it is shown: a later incident
  can make an earlier one's short form longer. The whole hash never
  changes.
- **The joining function gives every entry its state and its
  incidents,** each with its id, its short id, its kind, and whether
  it still stands. It still gives a removed or taken back entry whole.
  Removing is not redacting: the founder, 2026-11-16, "the comment
  stays in the data layer, in our records". What a room shows in its
  place is the room's view (step 3c).
- **This side does not check who may act.** It holds an act to its
  shape, and to naming something it can be done to. That the office
  holds a grant for the act, that the decision whose hash is given
  exists and says the same, and that the one taking an entry back is
  the one who wrote it, all need signed records and keys: the other
  side.
- **Nineteen reasons for refusing now,** four of them new, one for
  each kind of act. The vectors hold 122 logs or contents that are
  refused and seven that hold.
- **`world-log LOG CONTENTS`** also counts the entries removed, taken
  back and restored.

Three things carried from the last check of part two are done here:
- The open part of an entry can't hold nothing (JSON's `null`)
  anywhere but as its `agent`. A value a fingerprint allows is never
  nothing, and the open `data` is held to the same rule; the pages
  had not said so.
- With contents, the command line now runs the one check of the two
  together. A log with one fault in its chain and another in what it
  says is then refused for the one met first in the log's order, as
  the two libraries refuse it.
- Both writers refuse a table that is not well formed, for that
  reason, before anything is written.

Not done, the records' side of part four:
- The list of kinds of act "the rules fix" (decision 7), with
  `remove-comment` and `restore-comment` on it.
- The checks across records for a decision: its office holds the
  grant it names, and the grant allows the act.
- The author's record kinds in records-v1, for taking back and for
  putting back: the schema, Python and Rust, with vectors.
- The check of a log's acts against their signed records: that the
  hash in the open is the hash of the decision kept apart, and that
  the decision names the same entry and a ground that is the one
  shown. A `decision/v1` can hold several grounds, and the log shows
  one; which one is settled there.
- An author whose key has been signed over to a new one (decision 8).

## The parts

1. This plan.
2. Fingerprints and contents: the form and how a log names it, the two
   checks with the five states of a field, and the function that joins
   entries and contents, in Python and Rust, with vectors. It needs
   nothing from the founder. Built (above).
3. Redacting: the mark, the sealed copies and their label, and
   "redacted first, decided after", with a test that neither the value
   nor its salt is left anywhere in what the log keeps. It waits for
   the founder's answer on the office's copy.
4. Removing, taking back and restoring. The log's side is built
   (above): the four kinds of entry, each entry's state, the incident
   id, and the table of what wins. The records' side is next: the list
   of kinds of act, the checks across records for a decision, and the
   author's record kinds.

> End of `docs/research/REDACTION.md`.

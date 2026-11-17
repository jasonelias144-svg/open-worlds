> Part of `docs/research/REDACTION.md` in open-worlds, which is kept cut into parts
> for readers who are shown only the start of a long page.
> This part holds: "Part four, the log's side, built" to "Part three, the act of redacting, built".
> Every part, in order: https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/parts/INDEX.md
> Before this part: https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/parts/docs/research/REDACTION.md/start.md
> After this part: https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/parts/docs/research/REDACTION.md/a-writer-opened-on-a-log-written-before-built.md
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
  mark and the decision to keep a field public, that makes six (seven
  since part three, below). None
  of them can itself be removed or taken back: an act is undone by
  the act made for it, so the record of what was done is never hidden
  by another act. A field of theirs can still be redacted, as any
  field kept apart can.
- **A removal says in the open** the entry it is on, by that entry's
  hash; the office, as text that is not empty; the ground; and the
  hash of its decision, 64 lowercase hex digits (decision 7). The
  ground is a kind and a reference and nothing else. The kind is one
  of `charter`, `law`, `rule` and `record`; the reference is text of 1
  to 512 characters; and where the kind is `record`, the reference is
  that record's hash. All three are as a `decision/v1` holds its
  grounds, so that a ground the log shows is always one a signed
  decision can hold.
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
  entry's state, each of the four among them.
- **A removal can be restored while its author's taking back stands.**
  The removal stops standing, and the entry stays taken back. Put
  back later, it shows as restored. Decision 9's table had refused
  this, and is changed (the independent review found what refusing it
  would do).
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
  each kind of act. The vectors hold 124 logs or contents that are
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
- Which kinds of entry an act may be on. This side refuses an act on
  one of the form's own kinds and allows it on any other: a
  message, an arrival, even the log's first entry. A room's rules say
  which, with the list of kinds of act (`remove-comment` is on a
  comment).

## Part three, the log's side, built

In the same three places: `world/apart.py`,
`rust/world-log/src/apart.rs` and `vectors/log-apart.json`. Part three
has two sides, as part four has. This one is what a log says in the
open when a field is redacted and when that is decided, and the
writer's steps that keep a log and its contents in step. The other is
the act of redacting: the sealed copies, their label, and to whom they
go. It comes next, and is listed below.

What building it settled, each the technical lead's (STATUS.md has what
would show it wrong):

- **A third kind for a redacted field: `field_stays_redacted`,** the
  decision that a field stays redacted. It is the entry decision 5
  asks for ("an entry says so"). The form's own kinds are now seven.
- **A mark says in the open** the entry and the field, the office that
  marked it, and the ground: why in general terms, never what
  (decision 4). The ground is held to what part four holds a removal's
  to: a kind and a reference, as a signed decision holds them. A mark
  carries no decision: it is made at once, and decided after.
- **A decision names the mark it answers,** with its office, its
  ground and the hash of its decision record. That is so for both
  decisions, to keep the field public and that it stays redacted.
- **What the form's own kinds say in the open is fixed.** An entry of
  one of the seven holds, in the open, exactly the keys its kind says
  and nothing else. So a mark can hold no decision, and nothing beside
  its ground about what was redacted; and a removal, a restoring, a
  taking back and a putting back, of part four, are held to the same.
  What else such an entry carries is kept apart, as the table allows.
  "Never what" can't be checked in full: a ground's reference is free
  text. This closes the easy way to break it. (From the independent
  review of #112.)
- **No table can keep apart what one of those kinds says in the
  open.** A table that kept apart, say, a mark's `entry` would make
  every mark in that log impossible to write, so whoever set a room's
  table could switch redacting off with it. Such a table is refused as
  a table. (From the same review.)
- **A field has at most one mark that is open or stands.** A second
  mark on a field already marked is refused. Part two had allowed any
  number, and then one decision to keep the field public could not
  say which request it answered.
- **A mark is answered once, and only while it is open.** The answer
  is written when the decision and any appeal are over. Until then
  the mark is open and the field is hidden (FUNDAMENTALS.md, "Redacted
  first, decided after": "It stays redacted until any appeal is
  decided"). Kept public, the field may be marked again, as a new
  redaction with a new id. A mark that stays redacted stands for good:
  nothing in the log makes that field public again.
- **A redaction is open, stands, or was kept public.** Its id is the
  hash of its mark. A new function gives every field's redactions in
  the log's order, from the log alone, and the joining function gives
  them with each entry. Short ids are worked out over incidents and
  redactions together, so no two ids a room shows begin alike.
- **The five states of a field are as they were.** A field whose mark
  is open or stands is redacted if it is gone and unfinished if it is
  still there. So a field left in the contents after the decision that
  it stays redacted is unfinished: the check says so, and the joining
  function never shows it.
- **The writer has a step for each act,** and its plain appending
  refuses the three kinds. *Mark* appends the mark. *Take out* removes
  the field's `[salt, value]` from the contents and hands it back; the
  log is not touched, and an entry with nothing left keeps no empty
  map. The writer then holds neither the value nor the salt anywhere:
  it remembers each salt it has used by its hash alone, which is
  enough to refuse a source of salts that repeats, and gives nothing a
  fingerprint could be guessed with. (The independent review of #112
  found the salt still in the writer's memory, in both languages; the
  tests now look at everything the writer holds.) Taking out is
  allowed for a mark that is open or stands; through this writer a
  mark that stands has its field gone already, so that case comes
  only to a writer opened on a published log (below, "A writer opened
  on a log written before, built"). *Keep public* is given the salt
  and the value back. It refuses
  them unless they are the ones the log commits to, then appends the
  decision and puts the field back, in one step, or does neither.
  *Stays redacted* is refused while the field is still in the
  contents. This answers the note carried from part two: through the
  writer, a decision to keep a field public never leaves it missing.
- **The check still can't make a publisher honest.** Whoever
  publishes a log can lose a field afterwards, or leave one in. The
  check says what it finds: missing, or unfinished.
- **Twenty reasons for refusing now,** one of them new, and the two for
  a mark and for keeping public reworded, since they now refuse more.
  The vectors hold 179 logs or contents that are refused and seven
  that hold. The case of the five states is written through the
  writer's steps and holds every state of a field and of a redaction.
  Rust writes it again with its own writer and gets Python's log,
  entry for entry.
- **`world-log LOG CONTENTS`** also counts the redactions: open,
  standing, and kept public.

What this changes in the form. A log with a bare mark, as part two
allowed, is now refused: a mark has to say its office and its ground.
So is an entry of one of the form's own kinds that says more in the
open than its kind names, and a table that keeps one of those keys
apart. No world writes this form yet, and nothing kept anywhere is in
it but the vectors, so the form's name is unchanged. The name is
frozen from the day a world first writes a log in it: after that, a
change to what holds needs a new name.

Not done on this side. The first four are built since: "Part three,
the act of redacting, built", below.
- The sealed record and its label: a signed record that names the
  log, the entry's hash, the field, the salt and the value, inside a
  `sealed/v1` (decision 4).
- To whom it goes: one copy to each person the information is about,
  and one to the office that decides, kept until the decision and any
  appeal are over (decision 5). Where a room finds a person's sealing
  key.
- The act of redacting as one function around the writer's steps:
  seal, mark, take out. And the two decisions around theirs, with the
  office's copy opened for keeping public and deleted either way.
- The test that neither the value nor its salt is left anywhere in
  what the log keeps, across the whole act. This side has it for the
  writer's step alone.
- Who may mark and who may decide. As with part four's log side, this
  side holds an act to its shape and to what it names. That the
  office holds a grant, and that the decision whose hash is given
  exists and names the mark, need the signed records.
- A writer opened on a log and contents that were written before.
  Both writers started a new log only. Built since (below, "A writer
  opened on a log written before, built").

## Part three, the act of redacting, built

In `world/redact.py` and a new Rust crate, `rust/redact`, with
`vectors/redaction.json`; and, for the record that is sealed,
`schemas/records-v1.schema.json`, `formats/` and `rust/formats`. This
is the other side of part three: the sealed copies, and the deciding
office's two steps. Nothing real is redacted by it yet: no world
writes this form, and the keys are trial keys.

What building it settled, each the technical lead's (STATUS.md has what
would show it wrong):

- **The record is `open-worlds/redacted-field/v1`,** a new kind in
  records-v1. It says the office that redacted the field (its key and
  the grant it acts under), which signs; the one this copy is for
  (`to`); the office that decides (`decider`), the same in every copy;
  the log, the entry and the field; what was hashed for the field
  (`hashed`); and a filler of zeros (`pad`). One record is made for
  each one who gets a copy, so each names its own reader.
- **A copy carries exactly what was hashed, as text:** the list of the
  salt, the field's name and the value, written as the log writes it
  (decision 2), and not the value written a second way inside the
  record. The first build carried the salt and the value as fields of
  the record, and the independent review found what that cost: a log
  can keep apart a map whose key is not in ASCII, a signed record
  can't hold such a key, so that field could not be redacted at all,
  and the refusal quoted the key. Now whatever a log can keep apart
  can be redacted, and the tests redact every value the log's vectors
  allow. Nothing of the field is in any refusal's words. And what is
  put back must be what a log would write: a text that hashes to the
  entry's fingerprint and is not a field as a log writes one (written
  with spaces, a key twice, a number with a fraction, half a surrogate
  pair, twenty-one such in the vectors) is refused.
- **It is sealed under a label of its own,** `open-worlds/redacted/v1`,
  in the same envelope as every sealed record. Sealing itself does not
  change. Whoever opens a copy must be the one it names: a copy sealed
  again to someone else is refused by the one who opens it, as a
  world-key is.
- **What binds a copy to its place is the log, not the signature.**
  Whoever opens a copy hashes what it carries and finds that
  fingerprint in the entry the copy names (decision 4). A copy that
  does not match is refused whoever signed it. A copy does not name
  its mark, which is written after it: its mark is the one in the log
  on the same entry and field.
- **Who signed a copy, which office it names and who its deciding
  office is are the record's own word,** until the checks across
  records exist (part four). Whoever holds a field's salt and value
  can write a record that this code takes. That is no way to learn a
  field, since they hold it already; and it is why a log's writer must
  not decide on a copy alone.
- **The order is seal, hand over, mark, take out.** Every copy is made
  before anything is written. If one can't be made (a key no one
  should seal to, say), nothing is marked. The copies are then handed
  to whatever keeps them, while the field is still in the contents and
  nothing is marked: once the field is out, the copies are all that is
  left of it, so if they can't be kept, nothing is marked. If the mark
  is refused, nothing is taken out, and the copies made are not given
  back. They were handed over all the same, so whatever keeps copies
  must expect some with no mark behind them: sealed copies of a field
  that is still public. After it all, neither the value nor its salt
  is anywhere in what the writer holds or in what the act gave back:
  the tests look at all of it.
- **A copy is padded.** Before it is signed, a record is 1024 bytes in
  its RFC 8785 form, or the next power of two above that, so a sealed
  box is one of a few sizes and two boxes of one size differ by a byte
  at most. A short field written in ASCII can't be told from another
  by its box. What the padding does not hide: length is counted as
  the log writes the field, and a log writes every character outside
  ASCII as an escape, seven bytes in the record or fourteen. The
  independent re-check measured it: the smallest box holds 462 letters
  of ASCII, 66 of Cyrillic or of Chinese, and 33 emoji. So a box's
  size can hint at the script as well as the length, and a long field
  still shows roughly how long it is. And an envelope says in the
  clear that it holds a redacted field and whom it is for. So an
  envelope is not placed in the open: it goes to its reader's
  container, or to the office's own store.
- **A redaction that stopped after its mark can be finished.** The log
  then shows a field that is marked and still there (decision 4). The
  office seals the copies from the field as it still stands and takes
  it out; the log is not touched.
- **No copy is made for someone with no key,** and the caller says who
  has one: each person the field is about, with their sealing key, and
  the office that decides, with its own. Where a room finds a person's
  sealing key is the same as for every sealed record: the identity
  record, from course step 9; until then the caller gives it.
- **Only the deciding office's own copy decides.** To keep the field
  public the office opens the copy made for it, which is held to the
  log and to the mark, and the field goes back with the decision in
  one step. Every copy names the deciding office, and the one that
  names its own reader as that office is the office's. A person's copy
  in the office's hands does not open for it; a person's own copy,
  opened by that person, names another as the deciding office and is
  refused; and the office's copy of another field is refused. That the
  field stays redacted is an entry, and the office then deletes its
  copy.
- **A log is named by the hash of its first entry.** Two logs begun
  with the same first entry share that name: the trial room does, with
  any other room of the same rules. What no two logs share is an
  entry's hash, once a field with a fresh salt is behind it, and a
  copy names its entry. A room's first entry should hold something of
  its own, such as its key, so that the name is its own too (step
  3c).
- **The act sits beside the log's form, not in it.** `world/apart.py`
  and `rust/world-log` know nothing of keys or sealing, and `formats`
  knows nothing of logs. The act needs both, so it is a module of its
  own in Python and a crate of its own in Rust.
- **Ten reasons of its own, in fixed words,** the same in both
  languages. A log's own refusals and a sealed record's pass through
  as they are. So does a failure to keep the copies: Python lets
  through whatever the store raises, and Rust carries the store's
  words in one more refusal, which is not among the ten. The vectors
  hold one act on the trial room, the three
  copies it made with the record inside each, the log after each
  decision, nine records that hold as records and are refused when
  held to the log, and a second log, written by hand, whose entries
  commit to the twenty-one texts that are not a field. Rust does the
  same act and gets Python's log, its contents, and the same signed
  records; and decides from the box Python sealed.

Not done:
- **Who may redact and who may decide.** The record names a grant and
  nothing checks it. That, and that the decision whose hash is given
  exists and names the mark, are the checks across records (part four,
  the records' side).
- **Deleting the office's copy.** The code can't: it is the office's
  word until keys can be destroyed (step 8a).
- **Keeping the copies.** The act hands them over and keeps none. What
  receives them is a person's container (step 6a) and the office's own
  store, neither of which is built.
- **An office whose key changes** while it holds a copy: the copy is
  sealed to the old key.
- **A person who has no key when the field is redacted, and gets one
  later.** Nothing was kept for them, as decided.
- **A real redaction.** It waits for the room (step 3c) and for a
  person's container (step 6a).


> The next part: https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/parts/docs/research/REDACTION.md/a-writer-opened-on-a-log-written-before-built.md

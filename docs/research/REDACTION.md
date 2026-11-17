# A log that can be redacted, and removals on record

Course step 3b ([COURSE.md](../COURSE.md)): "Log entries whose fields
are kept apart from the chain that commits to them, by a salted
fingerprint", and "Removing a comment, as a record of its own". As with
each step, this page looks first, then records what the technical lead
decided, then the parts the step is built in. Begun on 2026-11-16.
Part two, the fingerprints and the contents, is built (below, "Part
two, built"); nothing else on this page is.

## What is asked

- **Redaction.** The founder, 2026-11-15: "any public act that contains
  private information will have that private information encrypted in
  the project records and removed or redacted in the public records",
  and "We do not edit historical records as an absolute rule"
  ([FUNDAMENTALS.md](../FUNDAMENTALS.md), "Public records, kept
  whole"). The technical lead's reading there, which stands: a redacted
  field keeps its place, the log still checks, a mark says that
  something was redacted and never what, and what was redacted goes,
  sealed, to the person it is about.
- **Removal.** The founder, 2026-11-16: a removed comment "stays in the
  data layer, in our records"; "If action is taken, it must become part
  of the records to justify the decision to take action"; the room
  shows "a note saying something was removed because of some reason",
  with "a unique event id or incident id"; and "Let's put all this in
  place now, from the beginning" ([COMMONS.md](../COMMONS.md),
  "Removing a comment").

The two are different things. A redaction takes private information
out of everyone's reach but its owner's. A removal takes nothing out of
the record: it changes what a room shows, and says why.

## What was looked at

### In the project

- **One log, for every world.** An entry holds `tick`, `kind`, `agent`,
  `data` and `prev`, and its `hash` is the SHA-256 of the entry without
  its hash, written as the Python kernel writes it (`world/core.py`;
  `rust/world-log`, `digest` and `verify_log`). The plant worlds and
  the Ur-world write their logs this way, and a world's signed head
  (`open-worlds/log-head/v1`) names the last hash.
- **So nothing can be taken out today.** An entry's `data` is hashed
  whole. Removing one field changes the entry's hash, and with it every
  hash after, and every signed head.
- **A decision is already a record** (`open-worlds/decision/v1`): the
  office's key and its grant, the act (a kind, and the records it is
  on), whom it affects, its reasons, its grounds (a charter, a law, a
  rule or a record), its inputs, where an appeal goes, the decision it
  supersedes, and the tick ([REASONS.md](../REASONS.md)).
- **Sealing exists** (`open-worlds/sealed/v1`, HPKE): an envelope to one
  key, with a label that says what is inside. It has two labels today,
  a journal entry and a world-key.

### Outside

- **Selective disclosure by salted hashes** (SD-JWT, RFC 9901, November
  2025). What may be withheld is not written into the signed part.
  For each such claim there is a Disclosure, "a JSON array of three
  elements": a salt, the claim's name and its value. The signed part
  holds only the digest of the Disclosure. Whoever is given a
  Disclosure can check it against the digest; whoever is not learns
  nothing from the digest. On the salt: "The RECOMMENDED minimum length
  of the randomly generated portion of the salt is 128 bits"; "A new
  salt MUST be chosen for each claim independently of other salts"; and
  the issuer "MUST NOT reveal the salt value to any party other than
  the Holder". The randomness is what "makes it infeasible to guess the
  preimage of the digest". It also allows decoy digests, which hide how
  many claims there are
  ([RFC 9901](https://www.rfc-editor.org/rfc/rfc9901.html), sections
  4.2.1, 4.2.3, 4.2.5 and 9.3).
- **A history whose events can be redacted** (Matrix). Before an event
  is signed, a hash of all of it is worked out and kept in the event.
  Then: "The event object is then redacted, following the redaction
  algorithm. Finally it is signed". So the signature is over the form
  that a redaction leaves, and, as the comments in the specification's
  example code say, it can still be checked once the event has been
  redacted. The hash kept in the event "covers the complete event
  including the *unredacted* contents", so a reader can tell whether
  what they hold is whole
  ([Server-Server API](https://spec.matrix.org/latest/server-server-api/),
  "Signing Events"). A redaction is itself an event in the room's
  history (`m.room.redaction`, in the Client-Server API, which was not
  opened for this page).
- **Read from these, by the technical lead.** Matrix gives the shape:
  the chain commits to the form that is left after a redaction, and a
  redaction is an entry of its own. But its second hash has no salt, so
  a short message could be guessed and the guess confirmed against the
  hash; the guess would have to match the whole content, with whatever
  a client added to it. SD-JWT gives the fingerprint that closes that: a fresh salt for
  each field, kept with the content.
- **From memory, not looked up for this page:** in event sourcing a
  mistake is corrected by a new event, never by changing an old one,
  which is the project's rule for ledgers already; and "crypto-
  shredding", forgetting data by destroying the key it was encrypted
  under, which belongs with keys that can be destroyed (course step
  8a).

## Decided by the technical lead

Each is recorded in STATUS.md with what would show it wrong. They were
reworked after the independent review of #100, which found four things
that did not hold together; STATUS.md's Log says what changed.

1. **What is kept apart is fixed kind by kind.** A world's rules say,
   for each kind of entry, which of its fields are kept apart; for
   those the entry holds only a fingerprint. What a person writes or
   gives is kept apart: a message's text, a name, a clock time, and the
   key that acted. What a reader needs to work out an entry's state is
   always in the open, hashed as today: its `kind`, its `tick` and its
   `prev`; and, for the room's own entries (a redaction's mark, a
   removal, a taking back, a restoring), the act, the entry it is on,
   and the office that acted. A reason in free text is kept apart even
   there, since it may turn out to repeat what it should not. A field
   is redacted whole. So an office's key is never redacted, which
   agrees with the rule that the keys which moderate are declared
   (FUNDAMENTALS.md, privacy, item 14).
   - *The key that acted* is kept apart so that the question stays
     open. Nothing about it is hidden unless it is redacted, and
     whether it ever may be is the founder's (below, "For the
     founder").
   - *The tick stays in the open* because it is a count, and says no
     more than the entry's place in the chain already does. A clock
     time is a field like any other, so it can be made coarser or
     redacted (FUNDAMENTALS.md, privacy, item 5). A world whose tick
     follows the clock would give the time away; a room's tick is to
     be a count, which step 3c settles.
2. **The fingerprint** is the SHA-256, in lowercase hex, of the array
   `[salt, name, value]`, written as the log writes everything else.
   The salt is 128 bits from the operating system's random source, as
   32 hex digits, fresh for each field of each entry, and never taken
   from a world's seed (FUNDAMENTALS.md). No fingerprint may appear
   twice in a log, which catches a salt used again. A value is text, a
   whole number from -(2^53 - 1) to 2^53 - 1, true or false, or a list
   or map of these; both languages refuse anything else, so that Python
   never writes what Rust would refuse.
3. **The contents are kept beside the log, not in it.** A log is then
   two things: the entries, which are the chain, and the contents,
   which give `[salt, value]` for each field kept apart, by the entry's
   hash. The log itself is never written again, not even by a
   redaction: only the contents lose a field. The chain is checked
   exactly as today, by the same `verify_log`. A second check holds the
   contents to the fingerprints. Every reader of an entry's `data`
   does change, so one function joins entries and contents, and every
   reader uses it: the Ur-world's host, its checks of links and
   arrivals, and the web app's checks.
   *The alternative,* the contents inside each entry under a key the
   hash skips, keeps a log in one piece and costs little code. It was
   not taken because a redaction would then rewrite the log.
4. **Redacting** is three things, in this order: the field's `[salt,
   value]` is sealed; an entry is appended, the mark, that says which
   entry and which field, when, by which office, and why in general
   terms, never what; and the field is taken out of the contents. The
   salt goes with the value, so no one else can confirm a guess. The
   entry that was redacted is not touched. If the work stops after the
   mark, the log shows a field that is marked and still there, which
   the check reports and the office can finish. The second check gives
   each field one of five states: **present**; **redacted** (gone, with
   a mark); **unfinished** (marked, still there); **kept public**
   (marked, still there, with a later decision to keep it public); and
   **missing** (gone, with no mark), which is a fault in whoever
   published the log.
   - *The sealed copy* is a `sealed/v1` with a label of its own. Inside
     the box is a signed record that names the log, the entry's hash,
     the field, the salt and the value. Whoever opens it works out the
     fingerprint again and finds it in the chain, and that is what
     binds the box to its place. Sealing itself does not change.
   - *To whom:* each person the information is about gets a copy, and
     it is not kept at all for someone who has no key (FUNDAMENTALS.md,
     "Kept in the person's own container"). The person it is about
     need not be the one who wrote it. Where a room finds a person's
     sealing key is part three's.
5. **Redacted first, decided after, and what the office holds.**
   FUNDAMENTALS.md has a redaction made at once and decided after, and
   lets the office decide to keep public what someone asked to redact.
   That needs the office to be able to put it back, and a copy sealed
   only to the person does not allow it: anyone could then erase a
   public act for good by asking. So, decided (2026-11-17, below):
   a second sealed copy goes to the office that decides (in a room, its
   Keeper), and is kept only until the decision and any appeal are
   over. If the redaction stands, that copy is deleted, and an entry
   says so. If the decision is to keep it public, the field goes back
   into the contents from that copy, and the decision says why. This
   qualifies "Kept in the person's own container"; part three waited
   for the founder's answer, and can now be built. The decision is a
   `decision/v1` that names the mark among the records it is on.
6. **A world with no one in it keeps today's form,** and a log says
   which form it is in. With random salts a log is no longer the same,
   byte for byte, on a second run. The plant worlds are checked by
   exactly that, and no person acts in them. So this form is for a
   world persons act in: a room first (step 3c), and the Ur-world
   before anyone is born into it, which is not this step's work. A log
   names its form in its first entry, since a fingerprint can't be told
   from any other 64 hex digits. A run of such a world is repeated
   from its seed and its salts together; once a field has been
   redacted its salt is gone, so the run can't be repeated past it,
   and what remains is that the chain checks.
7. **A moderator's removal is a `decision/v1`,** with no new kind of
   record. The act's kind is `remove-comment`; the records it is on
   name the comment's entry by the entry's own hash, the log's kind of
   hash; it affects the author; its grounds name the part of the room's
   law it rests on. The entry that carries it says in the open the
   act, the entry it is on, the office, the ground, and the decision's
   own hash; the signed decision is in the contents. So if a reason
   has to be redacted, which takes the whole signed decision out, the
   note can still show the ground. Restoring is a `decision/v1`
   of kind `restore-comment` that supersedes the removal.
   - *The incident id is the hash of the entry that carries the
     removal,* shown short: the fewest hex digits, twelve or more, that
     are the only such in the room, with the whole hash one step away.
     A reason that is later redacted does not change it.
   - *Its grant* comes from the room's key and allows `remove-comment`
     in that room; a Keeper needs one for what it does too. How a
     moderator comes to hold one is step 3d's.
   - *Built here for the first time:* the list of kinds of act "the
     rules fix", which does not exist yet, and the checks across
     records for a decision (its office holds the grant it names, and
     the grant allows the act), which `formats/records.py` leaves to
     the kernel. So part four is larger than it reads.
   - *The room's note* shows the incident id and the ground, the part
     of the law, and the reasons where they are still there.
8. **An author taking back their own comment is not a decision.** No
   office acts, so there is no grant, no grounds and no appeal. It is a
   record kind of its own in records-v1, signed by the author, that
   names the entry; the world writes it only if the signer is the one
   who wrote the comment. Its entry's hash is its incident id, in the
   same form. Left open for part four: an author whose key has been
   signed over to a new one; and whether an author can undo it
   (proposed: yes, by a record of their own, and no office can).
9. **What is shown is worked out, never stored, and from the open
   fields alone.** For a log, the state of each entry is: as written,
   removed, taken back, restored, or redacted in some field. It does
   not depend on the contents, which add what was said and why where
   they are still there. A world checks that an act is allowed when it
   writes the entry; a reader does not have to. What wins:

   | Then | Result |
   |---|---|
   | a field is redacted | it wins over everything, for that field: nothing shows it again, unless the office decides to keep it public |
   | a second removal of a removed entry, a second taking back, or a removal of an entry its author took back | refused |
   | a restoring of an entry that is not removed | refused |
   | a restoring of a removal, of an entry its author has since taken back | allowed: the removal no longer stands, and the entry stays taken back: an office does not undo an author's taking back |
   | a removal after a restoring | a new incident, with a new id |
   | an author takes back a comment that an office removed | allowed: it stays hidden even if the removal is later restored |
   | an author undoes their own taking back | the comment shows again, unless an office's removal still stands |
   | a removal of an entry that has a redacted field | allowed: the entry is hidden, and the field stays redacted |

   The room's own view of it is step 3c's. (The row on restoring what
   an author has since taken back was changed in building part four:
   it had been refused, which would have kept a removal overturned on
   appeal from going on record until its author put the entry back.)
10. **In Python and Rust, with shared vectors,** as every format here
    is: logs that hold, and logs that are refused, each for one named
    reason.

## For the founder: decided

Two things here were not the technical lead's alone, and were put to
the founder. Both are decided on the technical lead's recommendation,
under the founder's general guidance of 2026-11-17 (STATUS.md,
"Decided"). Part two needed neither.
- **The office's copy** (decision 5). Decided: yes, only until the
  decision and any appeal are over. It means that for a while an
  office of the project can read what was redacted. Before the
  redaction everyone could.
- **Whether the key that acted may ever be redacted** (decision 1).
  FUNDAMENTALS.md has a person's acts remain "under their keys", and
  the founder's words on a redacted link are "we keep public record of
  the action with private details of the action not included". The
  plan keeps the key apart so that either answer can be built; a log
  that hashed it in the open could never allow it. The cost of
  allowing it: once a key is redacted, no reader can check again that
  an act was that key's, such as that the one who took a comment back
  was the one who wrote it. It would rest on the world's word at the
  time of writing. Decided: the option is kept, and whether to use it
  is decided with the purging of a person who leaves (step 8a).

## Where the founder's last words of 2026-11-16 meet this

This plan was written before them (STATUS.md, "Decided").
- **The first room it is built for is the Ur-room,** the Commons'
  lobby, which is on the record ([COMMONS.md](../COMMONS.md), "The
  Ur-room"). Removals and redactions as planned here are for a room of
  that kind.
- **A private room's words are not this step's.** They are sealed with
  keys the room's members hold ([COMMONS.md](../COMMONS.md), "A
  spectrum of privacy"; course step 6a). There is nothing in them that
  the project can read, so nothing for it to redact, and no office of
  the project's removes a comment there. What a closed room's log
  holds is settled with that level, which is decided (2026-11-17):
  that the room exists, which presences are in it, and that messages
  passed.

## Honest limits

- **Copies.** A redaction takes a field out of what the record keeps.
  It can't recall what someone read or copied before.
- **A leaked copy can be proved real.** Whoever holds a field's salt and
  value can show, against a signed head, that it is what the log held,
  for ever. Plain deletion would not leave that behind.
- **What stays visible.** The entry itself: its kind, its tick and its
  place. That it had a field of a given name, and that it was redacted,
  when, and by which office. The kinds of entry and their field names
  are fixed by a world's rules, so they say nothing a reader of the
  rules didn't know; SD-JWT's decoys are not taken up for that reason.
- **The contents are a second thing to keep.** Whoever publishes a log
  must publish its contents with it, and whoever copies one without the
  other has a chain that checks and says little.
- **Sealing to the person needs the person's key,** and the place it is
  kept is their container, which is course step 6a. Until then this is
  built and tested with trial keys, and nothing real is redacted.
- **"Deleted" rests on the office's word.** Until keys can be destroyed
  (step 8a), that an office's copy is gone is a record and a promise,
  not something a reader can check.
- **What stands is for good.** The decision that a field stays
  redacted is the last word the log takes on that redaction. If it was
  wrong, the person it is about still holds their sealed copy, and can
  show it against the log; the log will not show the field again.
- **A short incident id can be made to collide on purpose,** at a cost
  of about 2^48 hashes for twelve digits. So the room shows as many
  digits as make it the only one, and the whole hash is one step away.

## Part two, built

In `world/apart.py` and `rust/world-log/src/apart.rs`, with
`vectors/log-apart.json`. What building it settled, each the technical
lead's (STATUS.md has what would show it wrong):

- **The form's name is `open-worlds/log-apart/v1`.** A log names it in
  its first entry, as `data.form`.
- **Fingerprints sit in a map of their own.** An entry holds `apart`,
  from a field's name to its fingerprint, beside its open `data`. They
  are not put in `data` where the values would be: a reader that
  doesn't know the form then finds a field absent, and never shows a
  fingerprint as if it were what someone said.
- **The table is in the log.** The first entry holds, for each kind of
  entry, the names of the fields kept apart (`data.kept_apart`). A
  field the table names for an entry's kind is in `apart` or not there
  at all, never in the open `data`; and an entry keeps nothing apart
  that the table doesn't name. So "fixed kind by kind" (decision 1) is
  checked from the log alone.
- **An entry holds its seven keys and nothing else:** `tick`, `kind`,
  `agent`, `data`, `apart`, `prev` and `hash`. The table reaches `data`
  and `apart` only, so a field beside them would be in the open
  whatever the table said.
- **The open part is held to the same rule as a value kept apart.**
  `tick` is a whole number from 0 to 2^53 - 1, `kind` is text, `agent`
  is text or nothing, and `data` is a map a fingerprint would allow: no
  number with a fraction, nothing beyond 2^53 - 1, every key text. This
  came from the independent review of #101. Python's writer had held
  the open part to nothing, so it could write a log that Rust could not
  check, and, through a key that wasn't text, could put a field the
  table keeps apart into the open. Now every log in this form can be
  written and checked in both languages, and the writer refuses before
  anything is hashed.
- **The order of the checks is part of the form.** Entries are read in
  the log's order; for each, its link to the entry before, then what it
  says, then its hash. The contents are read in ascending order of
  entry hash, and of field name within an entry. So a log or contents
  with two faults is refused for the same one, at the same place, in
  both languages. The chain is still the kernel's: a log that holds
  here holds by `verify_log`, unchanged.
- **`agent` is not a field that can be kept apart.** It stays in the
  open, as the kernel has it. A room leaves it empty for a person's
  act and puts who acted, by name and by key, among the fields kept
  apart; that is step 3c's to write.
- **Two kinds of entry are the form's own,** so that a field's state
  can be worked out: a mark (`field_redacted`), which names in the open
  an earlier entry by its hash and a field that entry keeps apart; and
  a decision to keep a field public (`field_kept_public`), which names
  an earlier mark. What else they say (the office, the ground, the
  decision's hash) and the act of redacting are part three's.
- **A mark stands until a decision to keep the field public answers
  it.** The five states, exactly: present (never marked, and there);
  redacted (a mark stands, and it is gone); unfinished (a mark stands,
  and it is still there); kept public (every mark on it was answered,
  and it is there); missing (no mark stands, and it is gone). Decision
  4 had left one case without a name: a field whose mark was answered,
  and which is gone all the same. It is missing: the record says it is
  public, and it isn't there. A field can be marked again after a
  decision to keep it public, and is then redacted again.
- **A field under a standing mark is never shown,** even while it is
  still in the contents. The joining function leaves it out, so a
  redaction cut short hides the field from every reader that uses the
  function.
- **A name** is a lowercase letter and then up to 63 lowercase
  letters, digits or underscores. **Nesting** in a value stops at 32
  lists or maps deep.
- **The contents hold nothing the log doesn't commit to.** An entry
  the log doesn't have, or a field an entry doesn't keep apart, is
  refused. So is one salt used for two fields, which the rule on
  fingerprints (decision 2) can't see when the two values differ.
- **Fifteen reasons for refusing, in fixed words,** the same in both
  languages, each with the same place. The vectors hold 90 logs or
  contents that are refused, each for one reason at one place (eight of
  them hold two faults, to fix which is met first), and five that hold,
  with every field's state and the entries as a reader gets them. Rust
  writes the trial room again from the same salts and gets Python's log
  and contents.
- **`world-log LOG CONTENTS`** checks the two together from the
  command line, counts the fields in each state, and fails if any is
  missing.

Not done in this part, and why:
- **No reader is changed.** No world writes this form yet, so the
  Ur-world's host, its checks of links and arrivals, and the web app's
  checks read what they read before. The room is the first to write it
  (step 3c), and is to use the joining function from its first line.
- **Nothing is redacted.** There is no sealing, and no office. The
  tests take a field out of the contents by hand, to show that the
  chain still checks and what state the field is then in.
- **The trial salts are fixed and public,** so that the vectors are the
  same on every run. Everything else takes its salts from the
  operating system; in Rust the caller supplies them, since
  `world-log` has no source of randomness of its own.
- **Limits.** The check holds a world to its table by name: it can't
  know that an open field of another name holds what should have been
  kept apart. A fingerprint commits a log to a value, and says nothing
  of who wrote it: that is a signature's work, in the signed record a
  room keeps apart (step 3c). JSON's `-0` is read by Python as 0 and
  refused by Rust; nothing writes it. And a file that isn't JSON as the
  standard has it (`NaN`, a number too large to read, half of a
  surrogate pair) is refused by Python's check and can't be read at all
  by Rust.

Carried to part three, from the same review: a single entry of kind
`field_kept_public` turns a finished redaction into a missing field,
and the command line then fails until the field is put back. Nothing in
this part says who may append one. Part three has to: the world writes
it only for the office that decides, with the field put back first or
in the same step. Done: "Part three, the log's side, built", below.

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

## A writer opened on a log written before, built

In `world/apart.py` and `rust/world-log` (`Log.open`), with the act of
redacting tried on such a log in `tests/test_redact.py` and
`rust/redact`. Until now both writers could only begin a new log. A
room that closes and opens again goes on from the log it has, and so
does an office that decides on a log another writer wrote.

What building it settled, each the technical lead's (STATUS.md has
what would show it wrong):

- **It is given a log and its contents, and checks the two together
  first,** as the check of a log against its contents does. A log or
  contents that do not hold are refused, for the same reason and at
  the same place. A field that is missing or unfinished is not
  refused: those are states, and the writer goes on from them.
- **It keeps copies of both.** What it was given is not touched by
  what it writes after, and changing what was given afterwards changes
  nothing in the writer. That holds for the rules too: the table of
  what each kind keeps apart is read from the log's first entry and
  kept as a copy. (The self-review found it shared, in Python: the
  table the writer went by was the very object in the log it had been
  given. Changed afterwards, the writer took an entry that its own
  log's table refuses. Rust can't share it: its writer owns what it
  holds.)
- **What it keeps is what it has checked.** In Python the log is
  checked as it is given, then copied, and the writer reads its own
  copy and goes by that. (The independent review showed why: a map
  that copies as something else passes the check as given, and its
  copy does not hold.) The contents need no second look, since only a
  plain map of plain lists is taken as contents.
- **An entry with no field left is left out of the contents,** as the
  writer leaves it.
- **It remembers the salt of every field still in the contents, by its
  hash alone,** as the writer does. What it can't know is the salt of
  a field that was taken out before it was opened: that salt is gone,
  which is what taking out is for. So a source of salts that repeats
  one of those is not refused by an opened writer, as it would be by
  the writer that used it. Outside tests a salt is 128 bits from the
  machine's random source, and a repeat is not expected. Why a repeat
  would matter: a redacted field's salt, drawn again for a field that
  is published, would put that salt in the open, and guesses at the
  redacted value could then be tried against its fingerprint.
- **A salt it is given back, it remembers from then on.** When a field
  is kept public the writer is handed its salt and value. An opened
  writer learns the salt there, before the entry that keeps the field
  public draws salts of its own; if that entry is refused, the field
  stays out and what was learned is forgotten again. (The independent
  review found this missing, in both languages: an opened writer put
  a field back and then took a repeat of its salt, and so wrote
  contents that its own check refuses, where the writer that never
  closed refuses the repeat.)
- **What it makes possible,** each tried in both languages on the logs
  of `vectors/redaction.json`. The deciding office opens the redacted
  log and keeps the field public from the box in the file, or decides
  that it stays redacted, and gets the log and the contents that the
  writer which never closed got. A field is redacted on a log opened
  again, with the same log, contents and mark; and the opened writer
  then holds neither the value nor its salt. A writer closed and
  opened before every act of the five states writes the log of one
  that never closed. And a redaction that
  stands with its field left in the contents, which no writer here
  leaves but a published log can show, is finished: the field is
  sealed and taken out, and the log is not touched.

Not done:
- **Whose log it is.** Opening checks that a log holds. It does not
  check that whoever opens it may write to it: a log in this form has
  no signature of its own yet. Signed heads are the room's (step 3c).
- **Two writers at once.** Nothing stops two writers opened on the
  same log from each going on. Each would write a log that holds, and
  the two would differ. One writer at a time is the room's to keep
  (step 3c).
- **Where a log is kept.** The writer is given a log and contents
  already read. Reading them from where they are kept, and writing
  them back safely, is the room's (step 3c).

## The parts

1. This plan.
2. Fingerprints and contents: the form and how a log names it, the two
   checks with the five states of a field, and the function that joins
   entries and contents, in Python and Rust, with vectors. It needs
   nothing from the founder. Built (above).
3. Redacting: the mark, the sealed copies and their label, and
   "redacted first, decided after", with a test that neither the value
   nor its salt is left anywhere in what the log keeps. The log's side
   is built (above): what a mark and each decision say in the open, a
   redaction's state, and the writer's steps. So is the act of
   redacting (above): the sealed copies, their label, and the deciding
   office's two steps, with trial keys. The founder's answer on the
   office's copy is given (decision 5). And a writer can be opened on
   a log written before (above), so the office that decides need not
   be the writer that redacted.
4. Removing, taking back and restoring. The log's side is built
   (above): the four kinds of entry, each entry's state, the incident
   id, and the table of what wins. The records' side is next: the list
   of kinds of act, the checks across records for a decision, and the
   author's record kinds.

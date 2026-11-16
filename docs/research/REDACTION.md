# A log that can be redacted, and removals on record

Course step 3b ([COURSE.md](../COURSE.md)): "Log entries whose fields
are kept apart from the chain that commits to them, by a salted
fingerprint", and "Removing a comment, as a record of its own". As with
each step, this page looks first, then records what the technical lead
decided, then the parts the step is built in. Begun on 2026-11-16.
Nothing on this page is built yet.

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
  hash. SD-JWT gives the fingerprint that closes that: a fresh salt for
  each field, kept with the content.
- **From memory, not looked up for this page:** in event sourcing a
  mistake is corrected by a new event, never by changing an old one,
  which is the project's rule for ledgers already; and "crypto-
  shredding", forgetting data by destroying the key it was encrypted
  under, which belongs with keys that can be destroyed (course step
  8a).

## Decided by the technical lead

Each is recorded in STATUS.md with what would show it wrong.

1. **Every field of an entry's `data` is kept apart.** In a log that can
   be redacted, an entry's `data` holds, for each of its fields, only
   the field's fingerprint. `tick`, `kind`, `agent` and `prev` stay as
   they are. What a person did remains "under their keys"
   (FUNDAMENTALS.md), so the key that acted is not something a
   redaction removes. A field is redacted whole; what is inside it is
   not redacted piece by piece.
2. **The fingerprint** is the SHA-256, in lowercase hex, of the array
   `[salt, name, value]`, written as the log writes everything else.
   The salt is 128 bits from the operating system's random source, as
   32 hex digits, fresh for each field of each entry, and never taken
   from a world's seed (FUNDAMENTALS.md).
3. **The contents are kept beside the log, not in it.** A log is then
   two things: the entries, which are the chain, and the contents,
   which give `[salt, value]` for each field of each entry, by the
   entry's hash. The chain is checked exactly as today, by the same
   `verify_log`, so a program that knows nothing of this still checks a
   log's hashes and its signed heads. A second check holds the contents
   to the fingerprints, and says which fields are there and which are
   not.
   *The alternative,* the contents inside each entry under a key the
   hash skips, would change what every reader of every log must skip.
4. **Redacting** is three things, in this order: the field's `[salt,
   value]` is sealed to the person it is about; it is taken out of the
   contents; and an entry is appended that says which entry and which
   field, when, by which office, and why in general terms, never what.
   The salt goes with the value, so no one else can confirm a guess.
   The entry that was redacted is not touched. The sealed copy gets a
   label of its own in `sealed/v1`, and is bound to its log, its entry
   and its field, so that a box made for one field can't be shown as
   another's. `sealed/v1` has no place for that binding today: its
   decision named "a sealed record needs associated data" as the
   reason to look again (STATUS.md), and this is that record. In a
   room, the office that decides is the room's Keeper
   (FUNDAMENTALS.md, "Redacted first, decided after").
5. **Redacted first, decided after,** as FUNDAMENTALS.md has it. The
   mark needs no decision. The decision that follows is a
   `decision/v1` that names the mark among the records it is on.
6. **A world with no one in it keeps today's form.** With random salts
   a log is no longer the same, byte for byte, on a second run. The
   plant worlds are checked by exactly that, and no person acts in
   them. So this form is for a world persons act in: a room first
   (step 3c), and the Ur-world before anyone is born into it. A run of
   such a world is repeated from its seed and its salts together.
7. **A moderator's removal is a `decision/v1`,** with no new kind of
   record: the act's kind is `remove-comment`, its records are the
   comment's entry, it affects the author, and its grounds name the
   part of the room's law it rests on. **The incident id is that
   record's hash,** shown as its first twelve hex digits, with the
   whole hash one step away. Restoring is a `decision/v1` of kind
   `restore-comment` that supersedes the removal, and it is refused for
   a field that was redacted: there is nothing left to show.
8. **An author taking back their own comment is not a decision.** No
   office acts, so there is no grant, no grounds and no appeal. It is a
   small record of its own, signed by the author, that names the entry;
   the check is that the signer is the entry's `agent`. Its hash is its
   incident id, in the same form.
9. **What is shown is worked out, never stored.** This step gives, for
   a log and its contents, the state of each entry: as written,
   removed (with the incident, the reason, and by whom), restored, or
   redacted in some field. The room's own view of it is step 3c's.
10. **In Python and Rust, with shared vectors,** as every format here
    is: logs that hold, and logs that are refused, each for one named
    reason.

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
  holds, if the founder keeps that level as proposed, is settled with
  it.

## Honest limits

- **Copies.** A redaction takes a field out of what the record keeps.
  It can't recall what someone read or copied before.
- **What stays visible.** That an entry had a field of a given name,
  and that it was redacted, when, and by which office. The kinds of
  entry and their field names are fixed by a world's rules, so they say
  nothing a reader of the rules didn't know; SD-JWT's decoys are not
  taken up for that reason.
- **The contents are a second thing to keep.** Whoever publishes a log
  must publish its contents with it, and whoever copies one without the
  other has a chain that checks and says nothing.
- **Sealing to the person needs the person's key,** and the place it is
  kept is their container, which is course step 6a. Until then this is
  built and tested with trial keys, and nothing real is redacted.
- **The key that acted is not redacted.** If purging a person who
  leaves should ever reach their keys in a public log, that is decided
  with the keys that can be destroyed (step 8a), and a log written
  before then would not allow it.

## The parts

1. This plan.
2. Fingerprints and contents: the form, the two checks, in Python and
   Rust, with vectors.
3. Redacting: the mark, the sealed copy and its label, and "redacted
   first, decided after", with a test that neither the value nor its
   salt is left anywhere in what the log keeps.
4. Removing, taking back and restoring: the checks over `decision/v1`,
   the author's record, the incident id, and the state of each entry.

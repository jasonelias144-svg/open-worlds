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
   is redacted whole.
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
   whole number no larger than 2^53 - 1, true or false, or a list or
   map of these; both languages refuse anything else, so that Python
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
   each field one of four states: **present**; **redacted** (gone, with
   a mark); **unfinished** (marked, still there); **missing** (gone,
   with no mark), which is a fault in whoever published the log.
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
   public act for good by asking. So, proposed, and put to the founder:
   a second sealed copy goes to the office that decides (in a room, its
   Keeper), and is kept only until the decision and any appeal are
   over. If the redaction stands, that copy is deleted, and an entry
   says so. If the decision is to keep it public, the field goes back
   into the contents from that copy, and the decision says why. This
   qualifies "Kept in the person's own container", so part three is
   not built before the founder answers. The decision is a
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
   act, the entry it is on, the office, and the decision's own hash;
   the signed decision is in the contents. Restoring is a `decision/v1`
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
   - *The room's note* shows the ground, the part of the law, and the
     reasons where they are still there.
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
   | a removal, or a taking back, of an entry that is already hidden | refused |
   | a restoring of an entry that is not removed, or that its author took back | refused: an office does not undo an author's taking back |
   | a removal after a restoring | a new incident, with a new id |
   | an author takes back a comment that an office removed | allowed: it stays hidden even if the removal is later restored |

   The room's own view of it is step 3c's.
10. **In Python and Rust, with shared vectors,** as every format here
    is: logs that hold, and logs that are refused, each for one named
    reason.

## For the founder

Two things here are not the technical lead's alone, and are put to the
founder in STATUS.md, "Open questions". Part two needs neither.
- **The office's copy** (decision 5). It means that for a while an
  office of the project can read what was redacted. Before the
  redaction everyone could. Recommended: yes, only until the decision
  and any appeal are over.
- **Whether the key that acted may ever be redacted** (decision 1).
  FUNDAMENTALS.md has a person's acts remain "under their keys", and
  the founder's words on a redacted link are "we keep public record of
  the action with private details of the action not included". The
  plan keeps the key apart so that either answer can be built; a log
  that hashed it in the open could never allow it. Recommended: keep
  the option, and decide with the purging of a person who leaves
  (step 8a).

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
- **A short incident id can be made to collide on purpose,** at a cost
  of about 2^48 hashes for twelve digits. So the room shows as many
  digits as make it the only one, and the whole hash is one step away.

## The parts

1. This plan.
2. Fingerprints and contents: the form and how a log names it, the two
   checks with the four states of a field, and the function that joins
   entries and contents, in Python and Rust, with vectors. It needs
   nothing from the founder.
3. Redacting: the mark, the sealed copies and their label, and
   "redacted first, decided after", with a test that neither the value
   nor its salt is left anywhere in what the log keeps. It waits for
   the founder's answer on the office's copy.
4. Removing, taking back and restoring: the list of kinds of act, the
   checks across records for a decision, the author's record kind, the
   incident id, and the table of what wins.

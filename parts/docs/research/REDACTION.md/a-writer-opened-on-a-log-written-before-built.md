> Part of `docs/research/REDACTION.md` in open-worlds, which is kept cut into parts
> for readers who are shown only the start of a long page.
> This part holds: "A writer opened on a log written before, built" to "The parts".
> Every part, in order: https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/parts/INDEX.md
> Before this part: https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/parts/docs/research/REDACTION.md/part-four-the-log-s-side-built.md
> After this part: nothing; this is the last part.
> Made by docs/parts.py from the file. To change it, change the file.

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
- **A salt hidden twice is refused when it would show.** A log
  written elsewhere can hold two fields that truly share a salt, with
  one of them taken out. It holds as it stands, because the taking
  out hides the repeat. Keeping that field public would put the salt
  into the contents twice, which the check refuses. So the writer
  refuses it, for the check's own reason, and changes nothing. (The
  re-check of the independent review found this. No writer here
  writes such a log, but for an opened one whose source of salts
  repeats a salt it can't know, as above.)
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

## Part four, the records' side, built

In `world/acts.py`, `rust/acts` and `vectors/acts.json`, with two new
kinds of record in records-v1. This side holds every act in a log to
the signed record it carries, and every office to its grant. It is the
check a world makes when it writes an act, and that a reader can make
again while the records are still there (decision 9).

What building it settled, each the technical lead's (STATUS.md has what
would show it wrong):

- **The list of kinds of act, for a log in this form, has five:**
  `remove-comment` and `restore-comment` (decision 7), and for a
  redaction `redact-field`, `keep-field-public` and
  `keep-field-redacted`. Each belongs to one kind of entry: a decision
  record says its kind of act, and it must be the one for the entry
  that carries it. The list is what a grant for a room can allow. No
  other office's acts are on it yet.
- **An act's record is in the field `record`, kept apart.** Six of the
  form's seven own kinds carry one: the four of an office (a removal,
  a restoring, and the two decisions on a redaction) carry a
  `decision/v1`; a taking back and a putting back carry the author's
  own record. An entry of one of the six that carries none is refused.
  A mark carries none: it is made at once and decided after (decision
  4).
- **An office is shown in the open by its key.** The log's side takes,
  for an office, any text that is not empty. Here that text must be
  the `did:key` that signed the decision. A name would bind nothing:
  one office could act under another's name. It agrees with decision
  1, that an office's key is never redacted, and with the rule that
  the keys which moderate are declared (FUNDAMENTALS.md, privacy, item
  14). An office's name is for the office's own record (course step
  3d), and a room's note can show it from there.
- **The log shows a decision's first ground.** A `decision/v1` can
  hold several; the one in the open is the first, and the others are
  in the record.
- **What a decision is on is exactly one thing:** the entry removed;
  the removal restored, by its incident id; the mark answered. What a
  decision drew on belongs in its `inputs`.
- **A decision can't be dated after the entry that carries it,** by
  its tick. It may be dated before: an office decides, and the room
  writes it when it can.
- **A restoring's decision supersedes the removal's,** by that
  decision's hash, which the removal shows in the open. So this holds
  even where the removal's record has been redacted.
- **A removal and a restoring name the one who wrote the entry among
  those they affect** (decision 7), where the key that wrote it is
  still in the contents to read.
- **A decision is carried by one entry.** No two entries of a log name
  the same decision. Without this, a removal that was overturned on
  appeal could be written again from the old record, by whoever
  writes the log, as a new incident. It is checked from the open
  fields, so redacting the first record does not free its decision to
  be used again.
- **The office's grant, and the grants above it.** The grant a
  decision names must be among the grants given with the log, hold as
  a record, be held by the office's key, allow the act, be for this
  room, and have been in force when the decision was signed. If it
  narrows another grant, that one is held to the same, and must be
  held by the one who issued the grant below it; and so on up to a
  grant that narrows nothing, which must come from the room's key
  (decision 7: "its grant comes from the room's key"). A chain is at
  most eight grants long. A grant counts from the second it starts,
  and no longer at the second it ends.
- **Only the path for the one act is checked.** That a grant claims no
  more than the grant it narrows, for other acts, is not looked at:
  such a claim fails where it is used, since every grant above must
  allow the act too.
- **The author's two kinds of record** (decision 8) are in records-v1:
  `open-worlds/taking-back/v1` (the author, the entry, and the
  putting back that last put that entry back, if there was one) and
  `open-worlds/putting-back/v1` (the author, and the taking back it
  undoes). They hold no grant, no grounds, no appeal and no reason.
  They name no log: an entry's hash is in one log only.
- **A taking back holds at one point of an entry's own history.** It
  names the putting back it follows, or none the first time. So a
  taking back can't be written into the log again after its author
  has put the entry back. It is tied to the entry's history, and not
  to the log's last entry as an arrival is, so that a busy room does
  not make an author sign again.
- **Who wrote an entry** is the key in the field the room's rules name
  for that kind of entry. There are three cases. The key is there: the
  signer must be that key. The key is gone, redacted or under a mark:
  the act is reported as held with its signer not checked, since no
  reader can check it again, and it rests on the world having checked
  when it wrote the entry (above, "For the founder: decided"). The
  entry never held a key: the act is refused.
- **An author whose key was signed over to a new one** (left open by
  decision 8). Only the key that wrote an entry takes it back, until
  successions are in records-v1 (course step 8a). From then, a key
  the writing key was signed over to counts as the same author.
  Decided here, built there.
- **Which kinds of entry an act may be on** is in the room's rules,
  for a mark, a removal and a taking back. A restoring, a putting back
  and a decision on a redaction follow what they answer. A field of
  one of the form's own entries, such as a decision's record, can
  always be marked: the form allows it, and the rules list only what
  persons write.
- **The room's rules are given with the log,** and are three things:
  the room's `did:key`; for each kind of entry a person writes, the
  field that holds the key that wrote it, which the log's table must
  keep apart; and what a mark, a removal and a taking back may each
  be on. A kind that can be taken back must name who wrote it.
- **An act has one of four states:** held; held, with its signer not
  checked; its record redacted; or its record missing, which is a
  fault in whoever published the log, as a missing field is. A record
  under a mark is not read, even while it is still in the contents.
- **Who marked** is checked where a copy is opened. A mark carries no
  record, and each sealed copy is signed by the office that redacted
  and names its grant: one function holds that office to a grant to
  redact, with no log.
- **Twenty-four reasons for refusing,** in fixed words, the same in
  Rust. The order of the checks is part of the check, so a log with
  two faults is refused for the same one in both. The vectors hold 6
  rooms that hold, with every state among them, and 58 that are
  refused, each for one reason at one entry; every record in a
  refused room is signed, so that only the thing named is at fault.
  Rust refuses each for the same reason at the same entry. Six
  records are held to their office's grant on their own.

Checked. 28 tests in Python and 9 in Rust. Each check was weakened on
purpose, one at a time: 49 changes to the Python, all caught; 47 to
the Rust, 46 caught, and the one that was not changes nothing a
caller can see (a record of another kind names no office, and is
refused for the same reason a line later). The first run of each
found a case no test held, and both are in the vectors now: an
author's key that is marked and not yet taken out, and a decision
signed at the second its grant begins. The record vectors gained
three records that hold and eight that are refused.

Not done:
- **The room's steps that write an act.** A world checks an act when
  it writes the entry; this is the check, and nothing here writes.
  The steps that refuse to write what it does not allow are the
  room's (step 3c).
- **The room's key is the rules' word.** A log in this form has no
  signature of its own until the room signs its heads (step 3c).
- **Taking a grant back before its end.** A grant is held to be in
  force by the time its decision says it was signed, which is the
  signer's word. Nothing here revokes one.
- **A decision's inputs.** That they are in the log, and that its
  reasons are sound, is not checked.
- **An office's name.** The log shows a key; the record that says
  which office holds it is step 3d's.
- **Successions** (step 8a), as above.
- **The command line.** `world-log LOG CONTENTS` checks the form and
  counts; it does not hold the acts to their records.

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
   id, and the table of what wins. The records' side is built too
   (above): the list of kinds of act, the checks across records for a
   decision, the author's two kinds of record, and every act in a log
   held to its record. With it, course step 3b is done.

> End of `docs/research/REDACTION.md`.

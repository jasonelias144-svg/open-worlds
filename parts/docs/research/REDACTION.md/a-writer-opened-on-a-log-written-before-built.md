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

> End of `docs/research/REDACTION.md`.

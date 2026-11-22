# The archive

Entries moved whole from this repository's living pages, a file
for each page and day. STATUS.md's "Decided", "Decided by the
technical lead" and "Log", and the messages in
docs/COLLABORATING.md, grow one dated entry at a time and are read
every session; each keeps the entries of its 3 most recent days,
and the older ones are here. A reference such as (STATUS.md,
"Decided", 2026-11-15) is found on the page if the day is
recent, and otherwise in that page's file for that day.

How it is done, every time the same way (AGENTS.md, "Every
session", step 6):

1. Commit the pages, then run `python3 docs/archive.py`: it says
   what would move, and changes nothing.
2. If it lists anything, run it with `--write`. Every check is
   made before anything is written.
3. Run `python3 docs/archive.py --check`, `docs/files.py` and
   `docs/parts.py`, and the tests, then commit, before pushing.
   Never amend, rebase or squash the commit a run names.

If a run stops, it says why, and nothing has been written: fix
the page and run it again. It stops on:

- a line at the left margin inside a list entry, which would move
  with that entry: move it above the section's first entry, or
  indent it to make it part of the entry;
- a code block that is never closed, or one that an entry opens
  and does not close: close it where it belongs;
- a line inside a code block that would start an entry or a
  section, as a block left open and closed by a later one would
  hold: close the block where it belongs, or indent that line;
- an entry dated later than tomorrow: correct its date;
- an entry dated on a day already here: a new entry takes the day
  it is written, and names any earlier day inside it.

The rules:

- An entry is the lines from the one that starts it, with its
  date, to its last line before the next entry. It moves whole
  and unchanged; only the blank lines between entries are not
  carried.
- A day is moved once, with all its entries.
- A file here is not edited again, except to redact what is
  private (AGENTS.md): edit the file, then run
  `python3 docs/archive.py --rehash <file> "<why>"`, which
  records the redaction in the catalogue.
- `catalog.json` gives each file's size, lines and SHA-256, and
  the commit its entries were taken from; `--check` finds each
  entry, word for word, in the page as it was at that commit,
  where that commit is at hand, and `tests/test_archive.py` runs
  it.

Each row: the day, then for each page its file and the entries
moved, by section.

| Day | STATUS.md | docs/COLLABORATING.md |
|---|---|---|
| 2026-11-18 | [STATUS/2026-11-18.md](STATUS/2026-11-18.md): Decided by the technical lead 2, Log 2 | [COLLABORATING/2026-11-18.md](COLLABORATING/2026-11-18.md): Messages from the technical lead 2 |
| 2026-11-17 | [STATUS/2026-11-17.md](STATUS/2026-11-17.md): Decided 21, Decided by the technical lead 17, Log 22 | [COLLABORATING/2026-11-17.md](COLLABORATING/2026-11-17.md): Messages from the technical lead 20 |
| 2026-11-16 | [STATUS/2026-11-16.md](STATUS/2026-11-16.md): Decided 21, Decided by the technical lead 8, Log 16 | [COLLABORATING/2026-11-16.md](COLLABORATING/2026-11-16.md): Messages from the technical lead 13 |
| 2026-11-15 | [STATUS/2026-11-15.md](STATUS/2026-11-15.md): Decided 47, Decided by the technical lead 10, Log 52 | [COLLABORATING/2026-11-15.md](COLLABORATING/2026-11-15.md): Messages from the technical lead 1 |
| 2026-11-14 | [STATUS/2026-11-14.md](STATUS/2026-11-14.md): Decided 26, Decided by the technical lead 13, Log 27 |  |
| 2026-11-13 | [STATUS/2026-11-13.md](STATUS/2026-11-13.md): Decided 16, Decided by the technical lead 7, Log 22 |  |
| 2026-11-12 | [STATUS/2026-11-12.md](STATUS/2026-11-12.md): Decided 13, Log 17 |  |

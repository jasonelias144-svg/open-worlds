# The archive

Entries moved whole from this repository's living pages, a file
for each page and day. STATUS.md's "Decided", "Decided by the
technical lead" and "Log", and the messages in
docs/COLLABORATING.md, grow one dated entry at a time and are read
every session; each keeps the entries of its 3 most recent days,
and the older ones are here. A reference such as (STATUS.md,
"Decided", 2026-11-15) is found on the page if the day is
recent, and otherwise in that page's file for that day.

How it is done, every time the same way:

- `python3 docs/archive.py` says what a run would move;
  `--write` moves it and writes this page and `catalog.json`;
  `--check` says whether the archive is whole and in step, and
  `tests/test_archive.py` runs it. Run it at the end of a session,
  then `docs/files.py` and `docs/parts.py`.
- An entry is the lines from the one that starts it, with its
  date, to its last line before the next entry. It moves whole
  and unchanged; only the blank lines between entries are not
  carried.
- A day is moved once, with all its entries. A page that later
  holds an entry dated on an archived day stops the run: a new
  entry takes the day it is written.
- A file here is not edited again, except to redact what is
  private (AGENTS.md). `catalog.json` gives each file's size,
  lines and SHA-256, and the commit its entries were taken from,
  so each entry can be found in the page as it was.

Each row: the day, then for each page its file and the entries
moved, by section.

| Day | STATUS.md | docs/COLLABORATING.md |
|---|---|---|
| 2026-11-17 | [STATUS/2026-11-17.md](STATUS/2026-11-17.md): Decided 21, Decided by the technical lead 17, Log 22 |  |
| 2026-11-16 | [STATUS/2026-11-16.md](STATUS/2026-11-16.md): Decided 21, Decided by the technical lead 8, Log 16 | [COLLABORATING/2026-11-16.md](COLLABORATING/2026-11-16.md): Messages from the technical lead 13 |
| 2026-11-15 | [STATUS/2026-11-15.md](STATUS/2026-11-15.md): Decided 47, Decided by the technical lead 10, Log 52 | [COLLABORATING/2026-11-15.md](COLLABORATING/2026-11-15.md): Messages from the technical lead 1 |
| 2026-11-14 | [STATUS/2026-11-14.md](STATUS/2026-11-14.md): Decided 26, Decided by the technical lead 13, Log 27 |  |
| 2026-11-13 | [STATUS/2026-11-13.md](STATUS/2026-11-13.md): Decided 16, Decided by the technical lead 7, Log 22 |  |
| 2026-11-12 | [STATUS/2026-11-12.md](STATUS/2026-11-12.md): Decided 13, Log 17 |  |

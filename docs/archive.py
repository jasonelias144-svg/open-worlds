"""Move a living page's older dated entries into the archive, whole.

Some pages here grow by one dated entry after another: STATUS.md's
"Decided", "Decided by the technical lead" and "Log", and the messages
in docs/COLLABORATING.md. Read every session, they get long. So each
page keeps the entries of its KEEP most recent days, and the older
ones move to archive/<page>/<day>.md, a file for each page and day,
listed in the catalogue (archive/catalog.json, and archive/README.md
for people).

    python3 docs/archive.py           say what a run would move, and nothing else
    python3 docs/archive.py --write   move it, and write the catalogue
    python3 docs/archive.py --check   exit 0 if the archive is whole and in step

The rules (archive/README.md gives them to readers too):

- An entry is the lines from the one that starts it, with its date,
  to its last line before the next entry or the end of its section.
  It moves whole and unchanged; only the blank lines between entries
  are not carried.
- A page keeps the entries of its KEEP most recent days, counted over
  all its dated sections. The rest move, a day at a time.
- A day's file holds that day's entries from each section, in the
  order the page had them, under the section's own heading.
- A day is moved once. If a page later holds an entry dated on a day
  already in the archive, the run stops and says so: a new entry takes
  the day it is written.
- A file in the archive is not edited again, except to redact what is
  private (AGENTS.md); the catalogue gives each file's size and hash,
  and the commit its entries were taken from.
- Each dated section, once anything has moved from it, opens with a
  line saying where its earlier entries are.

Run --write at the end of a session, then docs/files.py and
docs/parts.py, as for any change (AGENTS.md).
"""
import datetime
import hashlib
import json
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = "archive"
KEEP = 3

BULLET = re.compile(r"- (\d{4}-\d{2}-\d{2})\b")
HEADING = re.compile(r"### (\d{4}-\d{2}-\d{2})\b")

# The pages, each with its folder in the archive and its dated sections.
PAGES = [
    ("STATUS.md", "STATUS",
     [("Decided", BULLET),
      ("Decided by the technical lead", BULLET),
      ("Log", BULLET)]),
    ("docs/COLLABORATING.md", "COLLABORATING",
     [("Messages from the technical lead", HEADING)]),
]

POINTER = "*Earlier entries are in the archive, a file for each day: "


class Problem(Exception):
    """The page or the archive is not as the rules need."""


def _fence(line):
    return line.lstrip().startswith("```")


def sections(lines):
    """{name: (start, end)}: each '## ' section's body, as line indexes
    (the heading line itself excluded), headings in code blocks skipped."""
    found, name, start, fenced = {}, None, 0, False
    for i, line in enumerate(lines):
        if _fence(line):
            fenced = not fenced
        if not fenced and line.startswith("## ") and line[3:].strip():
            if name is not None:
                found[name] = (start, i)
            name, start = line[3:].strip(), i + 1
    if name is not None:
        found[name] = (start, len(lines))
    return found


def pointer_text(page, folder):
    """The line that opens a section with entries in the archive."""
    up = "../" * page.count("/")
    return (POINTER + "[" + OUT + "/" + folder + "/](" + up + OUT
            + "/README.md).*")


def entries(lines, start, end, pattern):
    """The section's entries as (date, first, last) line indexes, last
    included and blank lines after it left out, in page order; and the
    index of the first entry (or end)."""
    starts, fenced = [], False
    for i in range(start, end):
        if _fence(lines[i]):
            fenced = not fenced
        m = pattern.match(lines[i])
        if m and not fenced:
            starts.append((i, m.group(1)))
    out = []
    for n, (i, date) in enumerate(starts):
        stop = starts[n + 1][0] if n + 1 < len(starts) else end
        last = stop - 1
        while last > i and not lines[last].strip():
            last -= 1
        out.append((date, i, last))
    return out, (starts[0][0] if starts else end)


def read(path):
    with open(os.path.join(ROOT, path), encoding="utf-8") as f:
        return f.read()


def _split(text):
    lines = text.split("\n")
    return lines


def _strip_pointer(lines, start, end):
    """The section's lines without the pointer line and the blank line
    after it, if the section opens with them."""
    body = lines[start:end]
    if len(body) >= 3 and body[1].startswith(POINTER) and not body[2]:
        body = body[:1] + body[3:]
    return body


def plan(page, folder, specs, keep, archived_days):
    """What a run would move from one page: {day: [(section, [entry
    lines...]), ...]}, the page's text after the move, and the days kept.
    Stops on a page whose dated entries break the rules."""
    text = read(page)
    lines = _split(text)
    found = sections(lines)
    bodies = {}
    for name, pattern in specs:
        if name not in found:
            raise Problem("%s: no section '## %s'" % (page, name))
        start, end = found[name]
        if start >= end or lines[start].strip():
            raise Problem("%s: '## %s' is not followed by a blank line"
                          % (page, name))
        body = _strip_pointer(lines, start, end)
        ents, _ = entries(body, 0, len(body), pattern)
        bodies[name] = (body, ents)
    days = sorted({d for _, ents in bodies.values() for d, _, _ in ents},
                  reverse=True)
    kept = set(days[:keep])
    late = sorted({d for _, ents in bodies.values() for d, _, _ in ents
                   if d in archived_days})
    if late:
        raise Problem("%s: entries dated %s, a day already in the archive; "
                      "a new entry takes the day it is written"
                      % (page, ", ".join(late)))
    moving = {}
    new_bodies = {}
    for name, _ in specs:
        body, ents = bodies[name]
        drop = set()
        for n, (date, first, last) in enumerate(ents):
            if date in kept:
                continue
            stop = ents[n + 1][1] if n + 1 < len(ents) else len(body)
            drop.update(range(first, stop))
            moving.setdefault(date, []).append(
                (name, body[first:last + 1]))
        if not drop:
            new_bodies[name] = body
            continue
        left = [line for i, line in enumerate(body) if i not in drop]
        while len(left) > 1 and not left[-1].strip():
            left.pop()
        left.append("")
        new_bodies[name] = left
    # The page after the move: each dated section rebuilt, the rest as is.
    archived = set(archived_days) | set(moving)
    out = []
    i = 0
    order = sorted(((found[n][0], found[n][1], n) for n, _ in specs))
    for start, end, name in order:
        out.extend(lines[i:start])
        body = new_bodies[name]
        if archived:
            body = body[:1] + [pointer_text(page, folder), ""] + body[1:]
        out.extend(body)
        i = end
    out.extend(lines[i:])
    return moving, "\n".join(out), sorted(kept, reverse=True)


def day_file(page, folder, day, parts, moved_on, commit):
    """The text of one day's file."""
    up = "../" * (folder.count("/") + 2)
    head = [
        "# %s, %s" % (page, day),
        "",
        "Entries dated %s, moved whole and unchanged from" % day,
        "[%s](%s%s) on %s, as they were at commit `%s`." % (
            page, up, page, moved_on, commit[:12]),
        "They are not edited again, except to redact what is private.",
        "The catalogue: [README.md](../README.md).",
    ]
    out = head
    by_section = {}
    for name, lines in parts:
        by_section.setdefault(name, []).append(lines)
    for name in [n for n, _ in parts if n in by_section]:
        if name not in by_section:
            continue
        out += ["", "## " + name]
        for lines in by_section.pop(name):
            out += [""] + lines
    return "\n".join(out) + "\n"


def _facts(path):
    with open(os.path.join(ROOT, path), "rb") as f:
        data = f.read()
    return {"bytes": len(data),
            "lines": data.count(b"\n") + (0 if data.endswith(b"\n")
                                          or not data else 1),
            "sha256": hashlib.sha256(data).hexdigest()}


def load_catalog():
    path = os.path.join(ROOT, OUT, "catalog.json")
    if not os.path.exists(path):
        return {"items": []}
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def catalog_text(items):
    data = {
        "about": ("The archive of this repository: entries moved whole "
                  "from its living pages, a file for each page and day. "
                  "Written by docs/archive.py; archive/README.md says the "
                  "same for people."),
        "fields": {
            "path": "the file, from the repository's root",
            "kind": "what the file is; here always 'archive'",
            "title": "the page and the day",
            "source": "the page the entries were moved from",
            "date": "the day the entries are dated",
            "sections": "each section of the page, and how many entries",
            "moved": "the day they were moved",
            "commit": "the commit the page was at when they were moved",
            "bytes": "the file's size",
            "lines": "its lines",
            "sha256": "its SHA-256",
        },
        "items": sorted(items, key=lambda x: x["path"]),
    }
    return json.dumps(data, indent=1, ensure_ascii=False) + "\n"


def readme_text(items):
    out = [
        "# The archive",
        "",
        "Entries moved whole from this repository's living pages, a file",
        "for each page and day. STATUS.md's \"Decided\", \"Decided by the",
        "technical lead\" and \"Log\", and the messages in",
        "docs/COLLABORATING.md, grow one dated entry at a time and are read",
        "every session; each keeps the entries of its %d most recent days," % KEEP,
        "and the older ones are here. A reference such as (STATUS.md,",
        "\"Decided\", 2026-11-15) is found on the page if the day is",
        "recent, and otherwise in that page's file for that day.",
        "",
        "How it is done, every time the same way:",
        "",
        "- `python3 docs/archive.py` says what a run would move;",
        "  `--write` moves it and writes this page and `catalog.json`;",
        "  `--check` says whether the archive is whole and in step, and",
        "  `tests/test_archive.py` runs it. Run it at the end of a session,",
        "  then `docs/files.py` and `docs/parts.py`.",
        "- An entry is the lines from the one that starts it, with its",
        "  date, to its last line before the next entry. It moves whole",
        "  and unchanged; only the blank lines between entries are not",
        "  carried.",
        "- A day is moved once, with all its entries. A page that later",
        "  holds an entry dated on an archived day stops the run: a new",
        "  entry takes the day it is written.",
        "- A file here is not edited again, except to redact what is",
        "  private (AGENTS.md). `catalog.json` gives each file's size,",
        "  lines and SHA-256, and the commit its entries were taken from,",
        "  so each entry can be found in the page as it was.",
        "",
        "Each row: the day, then for each page its file and the entries",
        "moved, by section.",
        "",
    ]
    pages = [(page, folder) for page, folder, _ in PAGES]
    days = sorted({i["date"] for i in items}, reverse=True)
    out.append("| Day | " + " | ".join(p for p, _ in pages) + " |")
    out.append("|---|" + "---|" * len(pages))
    for day in days:
        cells = []
        for page, folder in pages:
            item = [i for i in items
                    if i["source"] == page and i["date"] == day]
            if not item:
                cells.append("")
                continue
            item = item[0]
            what = ", ".join("%s %d" % (s["name"], s["entries"])
                             for s in item["sections"])
            cells.append("[%s/%s.md](%s/%s.md): %s"
                         % (folder, day, folder, day, what))
        out.append("| %s | %s |" % (day, " | ".join(cells)))
    return "\n".join(out) + "\n"


def _head():
    try:
        return subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT,
                              capture_output=True, check=True,
                              text=True).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        raise Problem("not a git checkout: the commit can't be named")


def run(write, keep=KEEP, today=None):
    """Plan (and with write, do) a run. Returns what moved, per page."""
    catalog = load_catalog()
    items = list(catalog["items"])
    report = []
    pending = []
    for page, folder, specs in PAGES:
        done = {i["date"] for i in items if i["source"] == page}
        moving, new_text, kept = plan(page, folder, specs, keep, done)
        report.append((page, kept, moving))
        pending.append((page, folder, specs, moving, new_text))
    if not write:
        return report
    commit = _head()
    for page, _, _ in PAGES:
        same = subprocess.run(["git", "diff", "--quiet", "HEAD", "--", page],
                              cwd=ROOT).returncode == 0
        if not same:
            raise Problem("%s differs from the last commit: commit it first, "
                          "so the catalogue can name where the entries were"
                          % page)
    today = today or datetime.datetime.now(datetime.timezone.utc).date(
        ).isoformat()
    for page, folder, specs, moving, new_text in pending:
        old = read(page)
        for day, parts in sorted(moving.items()):
            path = "%s/%s/%s.md" % (OUT, folder, day)
            full = os.path.join(ROOT, path)
            if os.path.exists(full):
                raise Problem("%s exists already" % path)
            os.makedirs(os.path.dirname(full), exist_ok=True)
            # Every entry moved is in the page as it was, line for line.
            for _, lines in parts:
                if "\n".join(lines) not in old:
                    raise Problem("%s: an entry of %s is not found whole"
                                  % (page, day))
            with open(full, "w", encoding="utf-8") as f:
                f.write(day_file(page, folder, day, parts, today, commit))
            counts = []
            for name, _ in specs:
                n = sum(1 for s, _ in parts if s == name)
                if n:
                    counts.append({"name": name, "entries": n})
            item = {"path": path, "kind": "archive",
                    "title": "%s, %s" % (page, day), "source": page,
                    "date": day, "sections": counts, "moved": today,
                    "commit": commit}
            item.update(_facts(path))
            items.append(item)
        if moving:
            with open(os.path.join(ROOT, page), "w", encoding="utf-8") as f:
                f.write(new_text)
    with open(os.path.join(ROOT, OUT, "catalog.json"), "w",
              encoding="utf-8") as f:
        f.write(catalog_text(items))
    with open(os.path.join(ROOT, OUT, "README.md"), "w",
              encoding="utf-8") as f:
        f.write(readme_text(items))
    return report


def check():
    """The problems found, as a list of strings: empty if all is well."""
    problems = []
    catalog = load_catalog()
    items = catalog["items"]
    if not items:
        return problems
    listed = {i["path"] for i in items}
    here = set()
    for folder in sorted(os.listdir(os.path.join(ROOT, OUT))):
        full = os.path.join(ROOT, OUT, folder)
        if os.path.isdir(full):
            for name in os.listdir(full):
                here.add("%s/%s/%s" % (OUT, folder, name))
    for path in sorted(here - listed):
        problems.append("%s is not in the catalogue" % path)
    for path in sorted(listed - here):
        problems.append("%s is in the catalogue but missing" % path)
    specs = {page: (folder, s) for page, folder, s in PAGES}
    for item in items:
        path = item["path"]
        if path not in here:
            continue
        for key, value in _facts(path).items():
            if item.get(key) != value:
                problems.append("%s: its %s is not the catalogue's"
                                % (path, key))
        folder, secs = specs[item["source"]]
        lines = _split(read(path))
        found = sections(lines)
        counts = []
        for name, pattern in secs:
            if name not in found:
                continue
            start, end = found[name]
            ents, _ = entries(lines, start, end, pattern)
            for date, _, _ in ents:
                if date != item["date"]:
                    problems.append("%s: an entry dated %s" % (path, date))
            if ents:
                counts.append({"name": name, "entries": len(ents)})
        if counts != item["sections"]:
            problems.append("%s: its entries are not the catalogue's" % path)
    for page, folder, secs in PAGES:
        done = {i["date"] for i in items if i["source"] == page}
        lines = _split(read(page))
        found = sections(lines)
        for name, pattern in secs:
            start, end = found[name]
            if done and not (end - start >= 2
                             and lines[start + 1]
                             == pointer_text(page, folder)):
                problems.append("%s, '%s': it doesn't open with the line "
                                "that points to the archive" % (page, name))
            ents, _ = entries(lines, start, end, pattern)
            for date in sorted({d for d, _, _ in ents} & done):
                problems.append("%s, '%s': entries dated %s, a day in the "
                                "archive" % (page, name, date))
    for name, text in (("catalog.json", catalog_text(items)),
                       ("README.md", readme_text(items))):
        with open(os.path.join(ROOT, OUT, name), encoding="utf-8") as f:
            if f.read() != text:
                problems.append("%s/%s is not what the catalogue makes"
                                % (OUT, name))
    return problems


def main(argv):
    if argv not in ([], ["--write"], ["--check"]):
        print(__doc__)
        return 2
    try:
        if argv == ["--check"]:
            problems = check()
            for p in problems:
                print("PROBLEM: " + p)
            print("archive: %d problem(s)" % len(problems))
            return 1 if problems else 0
        report = run(write=argv == ["--write"])
    except Problem as e:
        print("STOPPED: %s" % e)
        return 1
    for page, kept, moving in report:
        n = sum(len(p) for p in moving.values())
        print("%s: keeps %s; %s %d entr%s from %s" % (
            page, ", ".join(kept), "moved" if argv else "would move", n,
            "y" if n == 1 else "ies",
            ", ".join(sorted(moving)) or "no day"))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

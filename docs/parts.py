"""Write parts/: every long file, cut into parts short enough to be
read whole by a reader who is shown only the start of a page.

A tool that opens a page for a reader may show only its start: the
window this is written for is about 32 KB. A page longer than that
can't be read to its end through its link, however often it is opened.
So each file a reader works from that is longer than LIMIT bytes is kept
here a second time, cut into parts of at most LIMIT bytes, and
parts/INDEX.md gives every part's full link in reading order. The file
itself stays the one to change; the parts are made from it.

    python3 docs/parts.py          # rewrite parts/
    python3 docs/parts.py --check  # exit 1 if parts/ is out of step

tests/test_parts.py runs the check.

How a file is cut. A part holds the file's own text, unchanged, between
a few lines at the top that say where it belongs and one at the bottom
that gives the next part's link. A Markdown page is cut at its "## "
headings: sections that fit are gathered into parts in order, and a
section too long for one part is cut between its top-level items and
gathered from its end. Gathering from the end matters for the pages
that grow at the top of a section, as STATUS.md's "Decided" and "Log"
do: a new entry then changes only that section's first part, and the
parts below keep their names and their text, so a change to the page
changes few parts. (When that first part is full, a new one is added
above it and the section's heading moves into it, and the parts on
either side of the new one change the links at their top and bottom.)
Any other file is cut between its paragraphs, gathered from its start.

Two things it reads more loosely than CommonMark, neither of which
loses text. A line of backticks or tildes counts as a fence however far
it is indented, so that fences inside list items are seen; one indented
four spaces or more, which CommonMark takes for indented code, is read
as a fence too. And a file that isn't Markdown is read for fences the
same way, so a line of tildes in one (an underline in reStructuredText,
say) is taken for an open block, and cuts after it fall between lines
and not between paragraphs.

parts/ is this script's alone. It removes anything there that it did
not write, ignored files included.
"""
import importlib.util
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = "parts"
INDEX = OUT + "/INDEX.md"
BASE = "https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/"
LIMIT = 28000  # bytes in a part, its top and bottom lines included
ROOM = 1500    # of those, kept for the top and bottom lines
BODY = LIMIT - ROOM

# Long files that are left whole: (path or folder, why).
LEFT_WHOLE = [
    ("vectors/", "test vectors, which programs check and nobody reads "
                 "through"),
    ("rust/Cargo.lock", "the lock file cargo writes"),
]


def _load_files_script():
    spec = importlib.util.spec_from_file_location(
        "docs_files", os.path.join(ROOT, "docs", "files.py"))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


FILES = _load_files_script()


def _size(lines):
    return sum(len(line.encode("utf-8")) for line in lines)


def _slug(title):
    """A heading as a file name: its letters and digits, with hyphens."""
    slug = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")
    if len(slug) > 48:
        slug = slug[:48].rsplit("-", 1)[0]
    return slug


_FENCE = re.compile(r"^\s*(`{3,}|~{3,})(.*)$")


def _lines(text):
    """The text as lines, each with its "\\n", cut at "\\n" and nowhere
    else, so that the lines joined are the text whatever else it holds
    (a "\\r", a form feed, no "\\n" at the end)."""
    pieces = text.split("\n")
    return [piece + "\n" for piece in pieces[:-1]] + (
        [pieces[-1]] if pieces[-1] else [])


def _fenced(lines):
    """For each line, whether it is a line of a fenced code block, its
    fences included. A block opens at a line of three or more backticks
    or tildes and closes at the next line of at least as many of the
    same, with nothing after them. One never closed runs to the end."""
    out, fence = [], None
    for line in lines:
        match = _FENCE.match(line.rstrip("\r\n"))
        if fence is None:
            # Backticks followed by more backticks on the line are
            # inline code, not a fence.
            if match and not (match.group(1)[0] == "`"
                              and "`" in match.group(2)):
                fence = match.group(1)
            out.append(fence is not None)
        else:
            out.append(True)
            if (match and match.group(1)[0] == fence[0]
                    and len(match.group(1)) >= len(fence)
                    and not match.group(2).strip()):
                fence = None
    return out


def sections(lines):
    """A Markdown page's lines as [title, lines] pairs, cut at its "## "
    headings. The first pair, titled "", is whatever comes before the
    first heading. A heading inside a code block doesn't count, nor one
    with no title."""
    out = [["", []]]
    for line, fenced in zip(lines, _fenced(lines)):
        if not fenced and line.startswith("## ") and line[3:].strip():
            out.append([line[3:].strip(), []])
        out[-1][1].append(line)
    return [pair for pair in out if pair[1]]


def units(lines):
    """Lines as the pieces a cut may fall between: each begins at a
    top-level list item, a lower heading, or a paragraph that starts at
    the left margin, and never inside a code block."""
    starts, fenced = [0], _fenced(lines)
    for i, line in enumerate(lines):
        if i == 0 or (fenced[i] and fenced[i - 1]):
            continue
        at_margin = line[:1] not in ("", " ", "\t", "\r", "\n")
        after_blank = lines[i - 1].strip() == ""
        if at_margin and (after_blank or (not fenced[i] and (
                line.startswith(("- ", "* ", "### "))
                or re.match(r"\d+\. ", line)))):
            starts.append(i)
    return [lines[a:b] for a, b in zip(starts, starts[1:] + [len(lines)])]


def _fitted(pieces, room):
    """The pieces, with any that is longer than the room given as its
    lines, one by one, so that a cut may fall between any two of them
    (a line longer than the room is left as it is)."""
    out = []
    for piece in pieces:
        if _size(piece) <= room:
            out.append(piece)
        else:
            out.extend([line] for line in piece)
    return out


def gather(pieces, room, from_end=False):
    """Neighbouring pieces joined into runs of at most `room` bytes,
    filled from the start, or from the end."""
    order = list(reversed(pieces)) if from_end else list(pieces)
    runs, current, held = [], [], 0
    for piece in order:
        size = _size(piece)
        if current and held + size > room:
            runs.append(current)
            current, held = [], 0
        current.append(piece)
        held += size
    if current:
        runs.append(current)
    if from_end:
        runs = [list(reversed(run)) for run in reversed(runs)]
    return [sum(run, []) for run in runs]


def cut(path, text, room=BODY):
    """The file's text as parts, in reading order: (name, what it
    holds, lines). The lines of all the parts, joined, are the text."""
    lines = _lines(text)
    if not path.endswith(".md"):
        runs = gather(_fitted(units(lines), room), room)
        return [("%02d" % i, "piece %d" % i, run)
                for i, run in enumerate(runs, 1)]

    parts = []
    group = []  # neighbouring sections that fit in one part together

    def close():
        if not group:
            return
        first, last = group[0][0], group[-1][0]
        name = _slug(first) if first else "start"
        if not first:
            holds = ("the start of the page" if len(group) == 1
                     else 'from the start to "%s"' % last)
        elif first == last:
            holds = '"%s"' % first
        else:
            holds = '"%s" to "%s"' % (first, last)
        parts.append((name, holds, sum((s[1] for s in group), [])))
        del group[:]

    for title, section in sections(lines):
        if _size(section) > room:
            close()
            runs = gather(_fitted(units(section), room), room,
                          from_end=bool(title))
            for i, run in enumerate(runs):
                # A titled section's pieces are numbered from its end,
                # so that a piece keeps its number, and so its name, as
                # the section grows at the top.
                number = len(runs) - i if title else i + 1
                name = "%s-%02d" % (_slug(title) or "start", number)
                holds = ('"%s", piece %d (its pieces are numbered from '
                         'its end)' % (title, number) if title
                         else "the start of the page, piece %d" % number)
                parts.append((name, holds, run))
        else:
            if group and _size(sum((s[1] for s in group), [])) \
                    + _size(section) > room:
                close()
            group.append((title, section))
    close()

    # Two parts of a page never share a name: a name already taken gets
    # the next number that is free.
    used, named = set(), []
    for name, holds, run in parts:
        base = name = name or "part"
        number = 1
        while name in used:
            number += 1
            name = "%s-%d" % (base, number)
        used.add(name)
        named.append((name, holds, run))
    return named


def _target(path, name):
    """Where a part is kept: parts/<the file's path>/<name>.md, or .txt
    for a file that isn't Markdown."""
    ext = ".md" if path.endswith(".md") else ".txt"
    return "%s/%s/%s%s" % (OUT, path, name, ext)


TOP = 7  # the lines at the top of a part that say where it belongs


def render(path, parts):
    """The part files of one file: {where it is kept: its text}.

    A part is TOP lines that say where it belongs, one line that sets
    them off (blank in Markdown, a rule in any other file), the file's
    own text, a "\\n", and then the bottom: in Markdown one line, in any
    other file a rule and one line. unwrap() takes them off again."""
    targets = [_target(path, name) for name, _, _ in parts]
    quote = "> " if path.endswith(".md") else ""
    rule = "" if quote else "-" * 72
    out = {}
    for i, (name, holds, lines) in enumerate(parts):
        before = (BASE + targets[i - 1] if i
                  else "nothing; this is the first part.")
        after = (BASE + targets[i + 1] if i + 1 < len(parts)
                 else "nothing; this is the last part.")
        top = [
            "Part of `%s` in open-worlds, which is kept cut into parts"
            % path,
            "for readers who are shown only the start of a long page.",
            "This part holds: %s." % holds,
            "Every part, in order: " + BASE + INDEX,
            "Before this part: " + before,
            "After this part: " + after,
            "Made by docs/parts.py from the file. To change it, change "
            "the file.",
        ]
        assert len(top) == TOP
        bottom = ("The next part: " + BASE + targets[i + 1]
                  if i + 1 < len(parts) else "End of `%s`." % path)
        out[targets[i]] = (
            "".join(quote + line + "\n" for line in top) + rule + "\n"
            + "".join(lines) + "\n"
            + (rule + "\n" if rule else "") + quote + bottom + "\n")
    return out


def unwrap(target, text):
    """The file's own text in a part file, with the lines render() put
    round it taken off."""
    body = text.split("\n", TOP + 1)[TOP + 1]
    for _ in range(2 if target.endswith(".md") else 3):
        body = body[:body.rindex("\n")]
    return body


def working(paths):
    """The files a reader works from: every file but the files of
    record (docs/FILES.md holds those) and the parts themselves."""
    record = set(FILES.here(paths))
    return [p for p in paths
            if p not in record and not p.startswith(OUT + "/")]


def _left_whole(path):
    for prefix, why in LEFT_WHOLE:
        if path == prefix or (prefix.endswith("/")
                              and path.startswith(prefix)):
            return prefix, why
    return None


def _read(path):
    """A file's text, or None if it isn't text."""
    with open(os.path.join(ROOT, path), "rb") as f:
        data = f.read()
    try:
        return data.decode("utf-8")
    except UnicodeDecodeError:
        return None


def long_files(paths):
    """The working files longer than LIMIT, as (to cut, left whole):
    [(path, text)] and {reason: [paths]}."""
    to_cut, left = [], {}
    for path in working(paths):
        if os.path.getsize(os.path.join(ROOT, path)) <= LIMIT:
            continue
        rule = _left_whole(path)
        text = None if rule else _read(path)
        if rule:
            left.setdefault(rule, []).append(path)
        elif text is None:
            left.setdefault((path, "not text"), []).append(path)
        else:
            to_cut.append((path, text))
    return to_cut, left


def index(cut_files, left):
    """parts/INDEX.md: every part's full link, file by file."""
    out = [
        "# Long pages, in parts",
        "",
        "Some readers are shown only the start of a long page: a tool that",
        "opens pages for them may stop at about 32 KB. So every file a",
        "reader works from that is longer than %s bytes is kept here a"
        % format(LIMIT, ","),
        "second time, cut into parts no longer than that, and this page",
        "gives each part's full link.",
        "",
        "Paste a file's links in the order given, or only the first: each",
        "part ends with the link of the part after it. A part holds the",
        "file's own text, unchanged, between a few lines at the top that",
        "say where it belongs and one at the bottom. Links inside a part",
        "are as the file wrote them, so a link that isn't a full link",
        "won't open from a part.",
        "",
        "The file itself is the one to change. `python3 docs/parts.py`",
        "makes the parts again, and `tests/test_parts.py` fails when they",
        "are out of step with their files.",
    ]
    for path, parts in cut_files:
        out += ["", "## `%s`, in %d parts" % (path, len(parts)), "",
                "```text"]
        out += [BASE + _target(path, name) for name, _, _ in parts]
        out += ["```"]
    out += ["", "## Left whole", "",
            "Longer than %s bytes, and not cut:" % format(LIMIT, ","), ""]
    for (what, why), paths in sorted(left.items()):
        count = " (%d of its files)" % len(paths) if what.endswith("/") \
            else ""
        out.append("- `%s`%s: %s." % (what, count, why))
    out += ["- The files of record, which [docs/FILES.md](../docs/FILES.md)",
            "  lists: the conversation records, the code taken from them,",
            "  what DeepSeek and Gemini were given in reply, and experiment",
            "  001's run logs."]
    return "\n".join(out) + "\n"


def build(paths):
    """Everything under parts/: {path: text}."""
    to_cut, left = long_files(paths)
    if any(path == "INDEX.md" for path, _ in to_cut):
        raise SystemExit("a long file named INDEX.md at the root would "
                         "need the folder parts/INDEX.md, which is the "
                         "index: name it in LEFT_WHOLE or rename it")
    cut_files = [(path, cut(path, text)) for path, text in to_cut]
    out = {INDEX: index(cut_files, left)}
    for path, parts in cut_files:
        out.update(render(path, parts))
    return out


def on_disk():
    """What is under parts/ now: {path: text}."""
    out = {}
    for folder, _, names in os.walk(os.path.join(ROOT, OUT)):
        for name in names:
            full = os.path.join(folder, name)
            rel = os.path.relpath(full, ROOT).replace(os.sep, "/")
            with open(full, "rb") as f:
                out[rel] = f.read().decode("utf-8", "replace")
    return out


def stale(want, have):
    """What differs between the parts as they should be and as they
    are: (missing, changed, left over), each a sorted list of paths."""
    return (sorted(set(want) - set(have)),
            sorted(p for p in want if p in have and want[p] != have[p]),
            sorted(set(have) - set(want)))


def main(argv):
    if argv not in ([], ["--check"]):
        print("usage: python3 docs/parts.py [--check]", file=sys.stderr)
        return 2
    paths = FILES.tracked()
    if paths is None:
        print("not a git checkout: can't list the files", file=sys.stderr)
        return 2
    want, have = build(paths), on_disk()
    missing, changed, extra = stale(want, have)
    if "--check" in argv:
        for label, group in (("missing", missing), ("out of step", changed),
                             ("left over", extra)):
            for path in group[:10]:
                print("%s: %s" % (label, path))
            if len(group) > 10:
                print("%s: and %d more" % (label, len(group) - 10))
        if missing or changed or extra:
            print("parts/ is out of step: run python3 docs/parts.py")
            return 1
        return 0
    for path in missing + changed:
        full = os.path.join(ROOT, path)
        os.makedirs(os.path.dirname(full), exist_ok=True)
        with open(full, "w", encoding="utf-8", newline="") as f:
            f.write(want[path])
    for path in extra:
        os.remove(os.path.join(ROOT, path))
    for folder, _, _ in os.walk(os.path.join(ROOT, OUT), topdown=False):
        if not os.listdir(folder):
            os.rmdir(folder)
    print("%d parts of %d files; %d written, %d removed"
          % (len(want) - 1,
             len({p.rsplit("/", 1)[0] for p in want if p != INDEX}),
             len(missing) + len(changed), len(extra)))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

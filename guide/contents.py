"""The guide's contents, written onto its home page from the outline.

    python3 guide/contents.py            write the contents into guide/README.md
    python3 guide/contents.py --check    exit 1 if the contents are not current

The home page (guide/README.md) lists every chapter in the outline
(guide/OUTLINE.md), with how far it has come. A chapter is "planned"
until its file exists, at guide/<part>/<nn>-<name>.md (for example
guide/I/01-what-open-worlds-is.md); then its progress is the file's
first line that starts with "Progress:" (for example "Progress: draft"
or "Progress: checked at 4366e76"), or "written" if it has none. The
contents sit between two marker lines on the home page, and nothing
else on it is touched.
"""

import glob
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
OUTLINE = os.path.join(HERE, "OUTLINE.md")
HOME = os.path.join(HERE, "README.md")
START = "<!-- contents: written by guide/contents.py; do not edit by hand -->"
END = "<!-- end of contents -->"

PART = re.compile(r"^## (Front matter|Part ([IVX]+)\. .+|Reference)$")
CHAPTER = re.compile(r"^- \*\*((F|R|[IVX]+)\.(\d+)) ([^*]+?)[.,]?\*\*")


class Problem(Exception):
    pass


def chapters(outline_text):
    """[(part heading, [(number, part, n, title), ...]), ...] in order."""
    parts, seen = [], set()
    for line in outline_text.split("\n"):
        heading = PART.match(line)
        if heading:
            parts.append((heading.group(1), []))
            continue
        found = CHAPTER.match(line)
        if found:
            number, part, n, title = found.groups()
            if not parts:
                raise Problem("chapter %s comes before any part" % number)
            if number in seen:
                raise Problem("chapter %s is in the outline twice" % number)
            seen.add(number)
            parts[-1][1].append((number, part, int(n), title.strip()))
    return parts


def chapter_file(part, n):
    """The chapter's file, relative to the guide's folder, or None."""
    found = sorted(glob.glob(os.path.join(HERE, part, "%02d-*.md" % n)))
    if len(found) > 1:
        raise Problem("chapter %s.%d has %d files" % (part, n, len(found)))
    return os.path.relpath(found[0], HERE) if found else None


def progress(path):
    with open(os.path.join(HERE, path), encoding="utf-8") as f:
        for line in f:
            if line.startswith("Progress:"):
                return line[len("Progress:"):].strip() or "written"
    return "written"


def contents_text(outline_text):
    parts = chapters(outline_text)
    total = sum(len(c) for _, c in parts)
    written = 0
    rows = []
    for heading, chs in parts:
        rows += ["", "### " + heading, "", "| Chapter | Title | Progress |",
                 "|---|---|---|"]
        for number, part, n, title in chs:
            path = chapter_file(part, n)
            if path:
                written += 1
                rows.append("| %s | [%s](%s) | %s |"
                            % (number, title, path, progress(path)))
            else:
                rows.append("| %s | %s | planned |" % (number, title))
    head = ["%d chapters in the outline; %d written." % (total, written)]
    return "\n".join([START, ""] + head + rows + ["", END])


def current_home(home_text, contents):
    if home_text.count(START) != 1 or home_text.count(END) != 1:
        raise Problem("guide/README.md must hold each contents marker once")
    before = home_text.split(START)[0]
    after = home_text.split(END, 1)[1]
    return before + contents + after


def main(argv):
    with open(OUTLINE, encoding="utf-8") as f:
        outline_text = f.read()
    with open(HOME, encoding="utf-8") as f:
        home_text = f.read()
    try:
        new = current_home(home_text, contents_text(outline_text))
    except Problem as problem:
        print("PROBLEM: %s" % problem)
        return 1
    if argv[1:] == ["--check"]:
        if new != home_text:
            print("PROBLEM: guide/README.md's contents are not current; "
                  "run python3 guide/contents.py")
            return 1
        print("guide: contents current")
        return 0
    if argv[1:]:
        print(__doc__)
        return 2
    if new != home_text:
        with open(HOME, "w", encoding="utf-8") as f:
            f.write(new)
    print("guide: contents written")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))

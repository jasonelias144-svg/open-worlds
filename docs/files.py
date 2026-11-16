"""Write docs/FILES.md: the full link of every file that
docs/COLLABORATING.md's list leaves out, in groups to paste.

A full link given in a message opens in a conversation with DeepSeek;
the links on COLLABORATING.md, the founder found, did not. So every file
in the repository needs its full link somewhere a person can copy it
from (the founder,
2026-11-15: "Remember links in the collaborating page are not
accessible. So all files need links through this method.").
COLLABORATING.md lists the files a reader works from; this page lists
the rest: DeepSeek's records, the code taken from them, what DeepSeek
was given in reply, and Experiment 001's run logs.

    python3 docs/files.py          # rewrite docs/FILES.md
    python3 docs/files.py --check  # exit 1 if docs/FILES.md is stale

tests/test_collaborating_links.py runs the check.
"""
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PAGE = os.path.join(ROOT, "docs", "FILES.md")
BASE = "https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/"
GROUP_MAX = 40  # links in one group, a paste at a time

# The kinds of file this page holds, in its order: (folder, heading,
# what they are). Every other file is in COLLABORATING.md's list.
KINDS = [
    ("sketches/records/", "DeepSeek's records",
     "each conversation with DeepSeek, word for word; most are too large "
     "to read in one go"),
    ("sketches/deepseek/", "Code taken from DeepSeek's records",
     "DeepSeek's code as each record gave it, a folder per record; "
     "`name@offset` is an earlier version of `name`, found at that "
     "offset in the record"),
    ("sketches/replies/", "What DeepSeek was given",
     "the one file the founder gave DeepSeek at each return, with the "
     "reply and the list of files it was built from "
     "(`docs/reply.py` builds it)"),
    ("experiments/001-first-words/runs/", "Experiment 001's run logs",
     "what each small model said in the first-words experiment, run by "
     "run (the plan and results are in COLLABORATING.md's list)"),
]


def tracked():
    """Every file in the repository, as git sees it: committed, or new
    and not ignored. None if this isn't a git checkout.

    New files count on purpose, so a file gets its line before it is
    committed: a stray file in a local checkout makes the links test
    fail until it is listed, ignored or removed."""
    try:
        out = subprocess.run(
            ["git", "ls-files", "-z", "--cached", "--others",
             "--exclude-standard"],
            cwd=ROOT, capture_output=True, check=True).stdout
    except (OSError, subprocess.CalledProcessError):
        return None
    paths = sorted({p.decode("utf-8") for p in out.split(b"\0") if p})
    return [p for p in paths if os.path.isfile(os.path.join(ROOT, p))]


def here(paths):
    """The paths this page holds."""
    return [p for p in paths if any(p.startswith(k[0]) for k in KINDS)]


def _group(path, folder):
    """The group a path is listed in: its folder's next level down,
    and the one below it in a folder of records."""
    rest = path[len(folder):].split("/")
    depth = 2 if folder == "sketches/deepseek/" else 1
    return folder + "/".join(rest[:min(depth, len(rest) - 1)])


def _count(n):
    return f"{n} file" if n == 1 else f"{n} files"


def _size(n):
    if n >= 1024 * 1024:
        return f"{n / (1024 * 1024):.1f} MB"
    return f"{max(1, round(n / 1024))} KB"


def render(paths):
    """The page, for these paths (from tracked())."""
    mine = here(paths)
    out = [
        "# The rest of the files, by their full links",
        "",
        "Each line opens a file as it is on `main`. A full link given in a",
        "message opens in a conversation with DeepSeek; the links on",
        "COLLABORATING.md, the founder found, did not. So every file has",
        "its full link here or in",
        "[COLLABORATING.md](COLLABORATING.md) (\"Every file, by its full",
        "link\"), in groups to paste (the founder, 2026-11-15: \"Remember",
        "links in the collaborating page are not accessible. So all files",
        "need links through this method.\").",
        "",
        "COLLABORATING.md lists the files a reader works from: every page,",
        "all the code, the tests and the vectors. This page lists the rest,",
        f"{len(mine)} files of record, best sent when a question needs them.",
        "",
        "Written by `python3 docs/files.py`;",
        "`tests/test_collaborating_links.py` fails if a file is added, moved",
        "or removed and this page isn't written again.",
    ]
    for folder, heading, what in KINDS:
        files = [p for p in mine if p.startswith(folder)]
        if not files:
            continue
        sizes = [os.path.getsize(os.path.join(ROOT, p)) for p in files]
        out += ["", f"## {heading}", "",
                f"In `{folder.rstrip('/')}`, {_count(len(files))}, "
                f"{_size(sum(sizes))} in all, the largest "
                f"{_size(max(sizes))}: {what}."]
        groups = {}
        for p in files:
            groups.setdefault(_group(p, folder), []).append(p)
        for name in sorted(groups):
            members = groups[name]
            parts = [members[i:i + GROUP_MAX]
                     for i in range(0, len(members), GROUP_MAX)]
            for i, part in enumerate(parts, 1):
                size = sum(os.path.getsize(os.path.join(ROOT, p))
                           for p in part)
                label = f"**`{name.rstrip('/')}`**"
                if len(parts) > 1:
                    label += f", part {i} of {len(parts)}"
                out += ["", f"{label} ({_count(len(part))}, {_size(size)}):",
                        "", "```text"]
                out += [BASE + p for p in part]
                out += ["```"]
    return "\n".join(out) + "\n"


def main(argv):
    paths = tracked()
    if paths is None:
        print("not a git checkout: can't list the files", file=sys.stderr)
        return 2
    text = render(paths)
    if "--check" in argv:
        with open(PAGE, encoding="utf-8") as f:
            if f.read() != text:
                print("docs/FILES.md is stale: run python3 docs/files.py",
                      file=sys.stderr)
                return 1
        return 0
    with open(PAGE, "w", encoding="utf-8") as f:
        f.write(text)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

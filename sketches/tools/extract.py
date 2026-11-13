"""Take the code out of a conversation record, exactly as written.

The records in ../records are kept verbatim. This tool finds the code
blocks in one (a block opens at a ``` line naming a code language and
closes at the next bare ```), and writes each block that has a file name
to a folder, byte for byte. So anyone can check that the code in
../deepseek is what the record says, or see exactly what was changed.

    python3 extract.py list  RECORD                  every code block
    python3 extract.py write RECORD NAMES OUTDIR     write the named blocks
    python3 extract.py check RECORD NAMES TREE       compare TREE with them
    python3 extract.py check-all SKETCHES            check every record

`check-all` runs `check` for each names file in SKETCHES/tools
(names-*.json), using its "record" and "folder", both relative to
SKETCHES. So a new record needs only its names file. It also fails if a
folder in SKETCHES/deepseek isn't claimed by any names file, since its
code would then be tested but never checked against a record.

NAMES is a JSON file (see names-012-04-00.json): which blocks to take,
and a name for blocks that don't state their own. A name used twice
keeps the plain name for its first block; each later block is written
as name@LINE, LINE being the record line where its code starts.

`check` prints every file that differs from the record or is missing,
and exits 1 if any differs that NAMES doesn't list under "changed", or if
a name in NAMES is given for a line where no code block starts. Files
NAMES lists under "ours" are ignored: they were written here, not by
DeepSeek.
"""
from __future__ import annotations

import json
import os
import re
import sys
from typing import Dict, List

CODE_LANGUAGES = {"python", "py", "typescript", "ts", "go", "makefile",
                  "javascript", "js", "bash", "sh", "json", "toml", "yaml"}
_NAME = re.compile(r"((?:[A-Za-z0-9_-]+/)*[A-Za-z0-9_-]+"
                   r"\.(?:py|ts|go|js|json|toml|yml|yaml|mod|sh)|Makefile)\b")


def read_lines(path: str) -> List[str]:
    with open(path, encoding="utf-8", newline="") as f:
        return f.read().split("\n")


def blocks(lines: List[str]) -> List[Dict]:
    """Every code block: the record line its code starts on (1-based),
    its length, its language, and the file name it states, if any (in
    its first lines, or on the nearest line above it)."""
    found, i = [], 0
    while i < len(lines):
        m = re.match(r"^```([A-Za-z0-9_+-]+)\s*$", lines[i])
        if not (m and m.group(1).lower() in CODE_LANGUAGES):
            i += 1
            continue
        j = i + 1
        while j < len(lines) and not re.match(r"^```\s*$", lines[j]):
            j += 1
        body = lines[i + 1:j]
        name = ""
        for line in body[:4]:
            n = _NAME.search(line)
            if n and (line.lstrip().startswith(("#", '"""', "//", "/*"))
                      or line.strip() == n.group(1)):
                name = n.group(1)
                break
        if not name:
            k = i - 1
            while k >= 0 and not lines[k].strip():
                k -= 1
            n = _NAME.search(lines[k]) if k >= 0 else None
            if n and len(lines[k]) < 140:
                name = n.group(1)
        found.append({"start": i + 2, "lines": len(body),
                      "lang": m.group(1).lower(), "name": name,
                      "text": "\n".join(body) + "\n"})
        i = j + 1
    return found


def named_files(record: str, names_path: str) -> Dict[str, Dict]:
    """File name -> {"start", "text"} for every block NAMES takes.
    Raises ValueError if NAMES gives a name for a line where no code
    block starts: a name one line off would otherwise be ignored, and
    its block silently left out."""
    with open(names_path, encoding="utf-8") as f:
        names = json.load(f)
    given = names.get("names", {})
    languages = set(names.get("languages", []))
    found = blocks(read_lines(record))
    starts = {str(b["start"]) for b in found}
    stray = sorted((k for k in given if k not in starts), key=int)
    if stray:
        raise ValueError("names given for lines where no code block "
                         "starts: " + ", ".join(stray))
    files: Dict[str, Dict] = {}
    for b in found:
        name = given.get(str(b["start"]), b["name"])
        if not name or b["lang"] not in languages:
            continue
        if name in files:
            name = f"{name}@{b['start']}"
        files[name] = {"start": b["start"], "text": b["text"]}
    return files


def write(record: str, names_path: str, out: str) -> None:
    for name, f in named_files(record, names_path).items():
        path = os.path.join(out, name)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8", newline="") as g:
            g.write(f["text"])


def check(record: str, names_path: str, tree: str) -> int:
    with open(names_path, encoding="utf-8") as f:
        names = json.load(f)
    changed = set(names.get("changed", {}))
    ours = set(names.get("ours", []))
    try:
        expected = named_files(record, names_path)
    except ValueError as e:
        print(f"NAMES FILE: {e}")
        return 1
    problems = 0
    for name, f in sorted(expected.items()):
        path = os.path.join(tree, name)
        if not os.path.exists(path):
            print(f"missing: {name} (record line {f['start']})")
            problems += 1
            continue
        with open(path, encoding="utf-8", newline="") as g:
            same = g.read() == f["text"]
        if not same:
            if name in changed:
                print(f"changed, as listed: {name}")
            else:
                print(f"CHANGED BUT NOT LISTED: {name}")
                problems += 1
        elif name in changed:
            print(f"LISTED AS CHANGED BUT IDENTICAL: {name}")
            problems += 1
    for root, _, filenames in os.walk(tree):
        for fn in filenames:
            rel = os.path.relpath(os.path.join(root, fn), tree)
            rel = rel.replace(os.sep, "/")
            if (rel not in expected and rel not in ours
                    and "__pycache__" not in rel):
                print(f"NOT FROM THE RECORD AND NOT LISTED AS OURS: {rel}")
                problems += 1
    print(f"{len(expected)} files from the record; {problems} problem(s)")
    return 1 if problems else 0


def check_all(sketches: str) -> int:
    tools = os.path.join(sketches, "tools")
    found = sorted(n for n in os.listdir(tools)
                   if n.startswith("names-") and n.endswith(".json"))
    if not found:
        print("no names files")
        return 1
    worst = 0
    claimed = set()
    for name in found:
        names_path = os.path.join(tools, name)
        with open(names_path, encoding="utf-8") as f:
            names = json.load(f)
        print(f"== {name}")
        if not isinstance(names.get("record"), str) \
                or not isinstance(names.get("folder"), str):
            print(f'NAMES FILE: {name} needs "record" and "folder"')
            worst = 1
            continue
        claimed.add(os.path.normpath(names["folder"]))
        worst = max(worst, check(os.path.join(sketches, names["record"]),
                                 names_path,
                                 os.path.join(sketches, names["folder"])))
    code = os.path.join(sketches, "deepseek")
    for entry in sorted(os.listdir(code)):
        folder = os.path.normpath(os.path.join("deepseek", entry))
        if os.path.isdir(os.path.join(sketches, folder)) \
                and folder not in claimed:
            print(f"NO NAMES FILE CLAIMS: {folder}")
            worst = 1
    return worst


def main(argv: List[str]) -> int:
    if len(argv) == 2 and argv[0] == "list":
        for b in blocks(read_lines(argv[1])):
            print(f"{b['start']:6d} {b['lines']:5d} {b['lang']:10s} "
                  f"{b['name']}")
        return 0
    if len(argv) == 4 and argv[0] == "write":
        write(*argv[1:])
        return 0
    if len(argv) == 4 and argv[0] == "check":
        return check(*argv[1:])
    if len(argv) == 2 and argv[0] == "check-all":
        return check_all(argv[1])
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

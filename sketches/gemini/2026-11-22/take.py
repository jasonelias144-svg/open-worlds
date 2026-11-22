"""Ours, not Gemini's. Takes Gemini's files out of the conversation they
were written in, and compares them with the ones kept here.

    python3 -I take.py                 compare with ./steps
    python3 -I take.py RECORD          the same, from another copy
    python3 -I take.py RECORD OUT      also write them under OUT

RECORD is the conversation as the founder exported it. With no
argument it is the copy in ../../records, which MANIFEST.json names;
MANIFEST.json gives its size and hash, and this script stops if RECORD
is another file.

The export holds no code fences. A file runs from the line after the
one that names it (`src/contact.rs`, alone on its line) to the line
before the next such line. The last file of a delivery runs to the
delivery's last line, which MANIFEST.json gives: the closing brace of
the last test, followed by an empty line and Gemini's own words. These
deliveries end with no "Expected:" line, as the earlier ones did, so
that line is named here instead of found. Empty lines at a file's end
are dropped. Nothing is run: this only reads and writes text.
"""
import hashlib
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
NAMED = re.compile(r"^((?:src|tests)/[a-z_/-]+\.rs)\s*$")


def main(argv):
    with open(os.path.join(HERE, "MANIFEST.json"), encoding="utf-8") as f:
        manifest = json.load(f)
    record = argv[0] if argv else os.path.join(
        os.path.dirname(os.path.dirname(HERE)), "records",
        manifest["record"]["name"])
    with open(record, "rb") as f:
        raw = f.read()
    if hashlib.sha256(raw).hexdigest() != manifest["record"]["sha256"]:
        sys.exit("this is not the record MANIFEST.json names")
    lines = raw.decode("utf-8").split("\n")
    problems = 0
    taken = {}
    for step, d in manifest["deliveries"].items():
        first, last = d["from"], d["to"]
        if not (lines[first - 1].startswith("::")
                and lines[last - 1] == "}" and lines[last] == ""):
            sys.exit(f"delivery {step} does not begin and end where it did")
        heads = [(i, NAMED.match(lines[i - 1]).group(1))
                 for i in range(first, last) if NAMED.match(lines[i - 1])]
        for n, (i, path) in enumerate(heads):
            end = heads[n + 1][0] - 1 if n + 1 < len(heads) else last
            body = lines[i:end]
            while body and not body[-1].strip():
                body.pop()
            name = f"steps/{step}/{path}"
            taken[name] = ("\n".join(body) + "\n").encode("utf-8")
    if set(taken) != set(manifest["files"]):
        sys.exit("the record gives other files than MANIFEST.json lists")
    for name, data in sorted(taken.items()):
        entry = manifest["files"][name]
        path = os.path.join(HERE, name)
        kept = None
        if os.path.exists(path):
            with open(path, "rb") as f:
                kept = f.read()
        ok = (data == kept
              and hashlib.sha256(data).hexdigest() == entry["sha256"])
        print(("as kept:   " if ok else "DIFFERS:   ") + name)
        problems += not ok
        if len(argv) > 1:
            dest = os.path.join(argv[1], name)
            os.makedirs(os.path.dirname(dest), exist_ok=True)
            with open(dest, "wb") as f:
                f.write(data)
    print(f"{len(taken)} files from the record; {problems} problem(s)")
    return 1 if problems else 0


if __name__ == "__main__":
    if len(sys.argv) not in (1, 2, 3):
        sys.exit(__doc__)
    sys.exit(main(sys.argv[1:]))

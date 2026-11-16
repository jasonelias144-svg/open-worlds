"""Build the one file the founder gives DeepSeek.

The founder, 2026-11-16: "let's put it all in a single file and I will
provide the file. No link necessary. Just one long file within
everything included. But only what is needed to continue working."
So each time the founder returns to DeepSeek, the technical lead's
reply, the next steps and the code as it stands go into one file, and
the founder provides it. This script builds that file, and checks it.

    python3 docs/reply.py SPEC          # write the file SPEC names
    python3 docs/reply.py --check SPEC  # exit 1 if it is out of step

SPEC is a JSON file in sketches/replies/ (its README.md says more):

    text     the reply, a text file beside SPEC: all that comes before
             the code
    out      the file to write, beside SPEC
    root     the folder the code is taken from, from the repository's
             root
    name     the name that folder is given in the file
    files    [[path under root, a note for the reader], ...], in order
    limit    the most bytes the file may have
    current  true while the code under root is as the file has it

The file is the text; then each file, whole, under a line that names
it; then the line END OF FILE, which the reader is asked to quote back.
After writing, the script reads the file back and compares each file
in it with the repository, byte for byte. tests/test_reply.py holds
every current reply to its sources.
"""
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LAST = "END OF FILE"
FENCE = "```"
LANGUAGES = {".rs": "rust", ".toml": "toml", ".py": "python",
             ".json": "json", ".md": "markdown"}
HEADER = re.compile(
    r"----- FILE: (\S+)  \(([^\n]*)\) -----\n```\w+\n(.*?)```\n\n", re.S)


class Problem(Exception):
    """Something that stops a reply being built as its spec says."""


def load(spec_path):
    """The spec, with the folder it is in."""
    with open(spec_path, encoding="utf-8") as f:
        spec = json.load(f)
    for key in ("text", "out", "root", "name", "files", "limit", "current"):
        if key not in spec:
            raise Problem(f"{spec_path}: no \"{key}\"")
    spec["folder"] = os.path.dirname(os.path.abspath(spec_path))
    return spec


def _source(spec, path, root=ROOT):
    """A file's text as it goes into the reply: as it is, with a last
    newline if it has none."""
    with open(os.path.join(root, spec["root"], path), "rb") as f:
        data = f.read()
    try:
        body = data.decode("utf-8")
    except UnicodeDecodeError:
        raise Problem(f"{path}: not text") from None
    if FENCE in body:
        raise Problem(f"{path}: holds a line of three backticks, which "
                      "would end its block early")
    return body if body.endswith("\n") else body + "\n"


def build(spec, root=ROOT):
    """The reply's whole text."""
    with open(os.path.join(spec["folder"], spec["text"]),
              encoding="utf-8") as f:
        text = f.read()
    if not text.endswith("\n\n"):
        raise Problem(f"{spec['text']}: must end with an empty line")
    if HEADER.search(text) or LAST in text.split("\n"):
        raise Problem(f"{spec['text']}: holds a line the file's own "
                      "layout uses")
    parts = [text]
    for path, note in spec["files"]:
        if "\n" in note or " -----" in note:
            raise Problem(f"{path}: its note can't be written on one line")
        language = LANGUAGES.get(os.path.splitext(path)[1], "text")
        parts.append(f"----- FILE: {spec['name']}/{path}  ({note}) -----\n"
                     f"{FENCE}{language}\n{_source(spec, path, root)}"
                     f"{FENCE}\n\n")
    parts.append(LAST + "\n")
    whole = "".join(parts)
    size = len(whole.encode("utf-8"))
    if size > spec["limit"]:
        raise Problem(f"{size} bytes, over the limit of {spec['limit']}")
    problems = read_back(spec, whole, root)
    if problems:
        raise Problem("; ".join(problems))
    return whole


def embedded(whole):
    """The files in a reply: [(name/path, note, text)]."""
    return HEADER.findall(whole)


def read_back(spec, whole, root=ROOT):
    """What is wrong with a reply's text, read as a reader would: a
    file missing or out of order, a file that differs from the
    repository, a last line that isn't the last line."""
    problems = []
    found = embedded(whole)
    want = [f"{spec['name']}/{path}" for path, _ in spec["files"]]
    if [name for name, _, _ in found] != want:
        problems.append("the files in it are not the spec's, in order")
    for (name, _, body), (path, _) in zip(found, spec["files"]):
        if body != _source(spec, path, root):
            problems.append(f"{name} differs from the repository")
    if whole.rstrip("\n").split("\n")[-1] != LAST or \
            not whole.endswith(LAST + "\n"):
        problems.append(f"it doesn't end with the line {LAST}")
    return problems


def check(spec, root=ROOT):
    """What is wrong with the reply as it is kept: [] if nothing."""
    path = os.path.join(spec["folder"], spec["out"])
    if not os.path.isfile(path):
        return [f"{spec['out']} is missing"]
    with open(path, "rb") as f:
        data = f.read()
    problems = []
    if len(data) > spec["limit"]:
        problems.append(f"{len(data)} bytes, over the limit of "
                        f"{spec['limit']}")
    kept = data.decode("utf-8")
    if kept.rstrip("\n").split("\n")[-1] != LAST:
        problems.append(f"it doesn't end with the line {LAST}")
    if spec["current"]:
        try:
            if build(spec, root) != kept:
                problems.append("it is not what its text and the "
                                "repository's files now make")
        except Problem as problem:
            problems.append(str(problem))
    return problems


def main(argv):
    args = argv[1:]
    checking = args[:1] == ["--check"]
    if checking:
        args = args[1:]
    if len(args) != 1:
        print("usage: python3 docs/reply.py [--check] SPEC", file=sys.stderr)
        return 2
    try:
        spec = load(args[0])
        if checking:
            problems = check(spec)
            for problem in problems:
                print(f"{spec['out']}: {problem}", file=sys.stderr)
            return 1 if problems else 0
        whole = build(spec)
    except Problem as problem:
        print(problem, file=sys.stderr)
        return 1
    with open(os.path.join(spec["folder"], spec["out"]), "w",
              encoding="utf-8", newline="\n") as f:
        f.write(whole)
    print(f"{spec['out']}: {len(whole.encode('utf-8'))} bytes, "
          f"{whole.count(chr(10))} lines, {len(spec['files'])} files")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))

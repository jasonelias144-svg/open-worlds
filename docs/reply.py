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
Before writing, the script reads what it has put together as a reader
would, and compares each file in it with the repository, byte for byte;
after writing, it reads the file from disk and does the same again.
tests/test_reply.py holds every current reply to its sources.

A path in SPEC stays where SPEC says: "text" and "out" are file names
beside SPEC, and "root" and each of "files" are paths with no ".." in
them and no leading "/". The file is made to be handed outside the
repository, so nothing from outside the named folder gets into it.
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


KEYS = ("text", "out", "root", "name", "files", "limit", "current")


def load(spec_path):
    """The spec, with the folder it is in."""
    try:
        with open(spec_path, encoding="utf-8") as f:
            spec = json.load(f)
    except (OSError, ValueError):
        raise Problem(f"{spec_path}: can't be read as JSON") from None
    if not isinstance(spec, dict):
        raise Problem(f"{spec_path}: not a JSON object")
    for key in KEYS:
        if key not in spec:
            raise Problem(f"{spec_path}: no \"{key}\"")
    spec["folder"] = os.path.dirname(os.path.abspath(spec_path))
    shape(spec)
    return spec


def _name(value):
    """Whether value is a file's name, with no folder in it."""
    return (isinstance(value, str) and value not in ("", ".", "..")
            and "/" not in value and "\\" not in value
            and not any(ord(c) < 32 for c in value))


def _under(value):
    """Whether value is a path that stays under the folder it starts
    from, and can be written in a header: no "..", no leading "/", no
    empty part, no white space."""
    if not isinstance(value, str) or not value or "\\" in value:
        return False
    if any(c.isspace() or ord(c) < 32 for c in value) \
            or os.path.isabs(value):
        return False
    return all(part not in ("", ".", "..") for part in value.split("/"))


def shape(spec):
    """Stop, with what is wrong, unless the spec is of the shape the
    module's docstring gives."""
    for key in ("text", "out"):
        if not _name(spec[key]):
            raise Problem(f"\"{key}\" must be a file's name, beside the spec")
    if spec["out"] == spec["text"] or spec["out"].endswith(".json"):
        raise Problem("\"out\" must not be the reply's own text, or a spec: "
                      "writing it would overwrite them")
    if not _under(spec["root"]):
        raise Problem("\"root\" must be a path under the repository's root")
    if not _under(spec["name"]) or "/" in spec["name"]:
        raise Problem("\"name\" must be one word")
    if isinstance(spec["limit"], bool) or not isinstance(spec["limit"], int) \
            or spec["limit"] < 1:
        raise Problem("\"limit\" must be a whole number of bytes, above none")
    if not isinstance(spec["current"], bool):
        raise Problem("\"current\" must be true or false")
    files = spec["files"]
    if not isinstance(files, list) or not all(
            isinstance(entry, list) and len(entry) == 2
            and all(isinstance(item, str) for item in entry)
            for entry in files):
        raise Problem("\"files\" must be a list of [path, note] pairs")
    for path, note in files:
        if not _under(path):
            raise Problem(f"{path!r}: a file's path must stay under "
                          "\"root\", with no white space in it")
        if "\n" in note or "\r" in note:
            raise Problem(f"{path}: its note can't be written on one line")


def _source(spec, path, root=ROOT):
    """A file's text as it goes into the reply: as it is, with a last
    newline if it has none."""
    try:
        with open(os.path.join(root, spec["root"], path), "rb") as f:
            data = f.read()
    except OSError:
        raise Problem(f"{path}: can't be read under {spec['root']}") from None
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
    shape(spec)
    try:
        with open(os.path.join(spec["folder"], spec["text"]),
                  encoding="utf-8") as f:
            text = f.read()
    except (OSError, UnicodeDecodeError):
        raise Problem(f"{spec['text']}: can't be read as text") from None
    if not text.endswith("\n\n"):
        raise Problem(f"{spec['text']}: must end with an empty line")
    if HEADER.search(text) or LAST in text.split("\n"):
        raise Problem(f"{spec['text']}: holds a line the file's own "
                      "layout uses")
    parts = [text]
    for path, note in spec["files"]:
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


def ends_as_it_should(whole):
    """Whether a reply's last line is the last line, with one newline
    after it and nothing else."""
    return whole == LAST + "\n" or whole.endswith("\n" + LAST + "\n")


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
    if not ends_as_it_should(whole):
        problems.append(f"it doesn't end with the line {LAST}")
    return problems


def check(spec, root=ROOT):
    """What is wrong with the reply as it is kept: [] if nothing. A
    past reply is a record, no longer held to the repository's files:
    only its size and its last line are looked at here, and
    sketches/replies/README.md's hash holds the rest."""
    shape(spec)
    path = os.path.join(spec["folder"], spec["out"])
    if not os.path.isfile(path):
        return [f"{spec['out']} is missing"]
    with open(path, "rb") as f:
        data = f.read()
    problems = []
    if len(data) > spec["limit"]:
        problems.append(f"{len(data)} bytes, over the limit of "
                        f"{spec['limit']}")
    try:
        kept = data.decode("utf-8")
    except UnicodeDecodeError:
        return problems + ["it is not text"]
    if not ends_as_it_should(kept):
        problems.append(f"it doesn't end with the line {LAST}")
    if spec["current"]:
        try:
            if build(spec, root) != kept:
                problems.append("it is not what its text and the "
                                "repository's files now make")
        except Problem as problem:
            problems.append(str(problem))
    return problems


def main(argv, root=ROOT):
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
            problems = check(spec, root)
            for problem in problems:
                print(f"{spec['out']}: {problem}", file=sys.stderr)
            return 1 if problems else 0
        whole = build(spec, root)
    except Problem as problem:
        print(problem, file=sys.stderr)
        return 1
    out = os.path.join(spec["folder"], spec["out"])
    with open(out, "w", encoding="utf-8", newline="\n") as f:
        f.write(whole)
    with open(out, "rb") as f:
        written = f.read()
    try:
        problems = read_back(spec, written.decode("utf-8"), root)
    except (Problem, UnicodeDecodeError) as problem:
        problems = [str(problem)]
    if written != whole.encode("utf-8"):
        problems.append("what was written is not what was built")
    if problems:
        for problem in problems:
            print(f"{spec['out']}: {problem}", file=sys.stderr)
        print(f"{spec['out']} was written, and is wrong as it stands: "
              "build it again once this is mended", file=sys.stderr)
        return 1
    print(f"{spec['out']}: {len(whole.encode('utf-8'))} bytes, "
          f"{whole.count(chr(10))} lines, {len(spec['files'])} files")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))

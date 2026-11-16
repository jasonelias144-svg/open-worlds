"""Ours, not DeepSeek's (see ../README.md). Puts together the crate as
it stands after each of the five deliveries that record 012-09-05 ends
with. The deliveries' files are kept in ../chat-world-steps/1 to 5,
as the record gives them (../../tools/extract.py checks that). This
lays each delivery over the one before, starting from the crate
DeepSeek was given, ../chat-world.

    python3 steps.py OUT            OUT/1 ... OUT/5
    python3 steps.py --aside OUT    and OUT/5-aside
    python3 steps.py --now OUT      and OUT/now
    python3 steps.py --check        is ../chat-world-now what --now makes?

Nothing is run: this only copies files. Each OUT/N/chat-world is the
crate after delivery N. A file a delivery doesn't give stays as the
delivery before left it.

`--now` also writes OUT/now: delivery 5 with its three faults repaired
(REPAIRS, below, and ../../../INDEX.md, fixes 19 to 21). That is the
crate as it stands, kept in ../chat-world-now. `--check` puts it
together again and compares it with that folder, byte for byte, so
that every file there is known to be DeepSeek's latest, changed only
as REPAIRS says. sketch_status_test.py runs the check.

`--aside` also writes OUT/5-aside: delivery 5 with its two faults set
aside, so that the rest of it can be built and tested. The faults are
not repaired: one condition in src/verify.rs that does not compile is
replaced by `false`, and src/bin/succession-demo.rs is left out.

../chat-world-steps/0 is not used: it is the cycle on signed heads from
before DeepSeek was given the one file, and delivery 3 gives its files
again.
"""
import filecmp
import os
import shutil
import sys
import tempfile

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# The condition in delivery 5's src/verify.rs that does not compile.
FAULT = ('if !looks_like_hash(&k.entry_hashes.iter().any(|_| "x".to_string())'
         '.then(|| "".to_string()).unwrap_or_default()) {')
# The three repairs: (file, what DeepSeek wrote, what it is changed to).
# Each makes the code do what the record says it does, and no more.
SIGN = "crate::sign_record(rec, &self.user_kp, Record::{}, |r, p| r.proof = p)?"
SIGN_BOTH = ("crate::sign_record_dual(rec, &self.user_kp, self.room.keypair(), "
             "Record::{}, |r, p| r.proof = p)?")
REPAIRS = [
    # Fix 19: since delivery 2 a room and its maker are two keys, and
    # every record but a leaving needs the room's proof. A home's three
    # records of its own were still signed by the person's key alone.
    ("src/home.rs", SIGN.format("PortLanding"), SIGN_BOTH.format("PortLanding")),
    ("src/home.rs", SIGN.format("Bookmark"), SIGN_BOTH.format("Bookmark")),
    ("src/home.rs", SIGN.format("Presence"), SIGN_BOTH.format("Presence")),
    # Fix 20: a condition that does not compile and, by its own comment,
    # does nothing. The check of each hash follows it and stays.
    ("src/verify.rs",
     "                " + FAULT + "\n"
     "                    // no-op; per-entry check below\n"
     "                }\n",
     ""),
    # Fix 21: a sibling's record has no hash() of its own; the Commons
    # hashes it with hash_of, and so does the demo now.
    ("src/bin/succession-demo.rs",
     "    let sib_hash = sib.hash()?;\n",
     "    let sib_hash = chat_world::hash::hash_of(&sib)?;\n"),
]


def repaired(before, tree):
    """Copies delivery 5 to `tree` and makes the three repairs."""
    shutil.copytree(before, tree)
    for name, old, new in REPAIRS:
        path = os.path.join(tree, name)
        with open(path, encoding="utf-8", newline="") as f:
            text = f.read()
        if text.count(old) != 1:
            sys.exit(f"{name}: what is repaired is not where it was")
        with open(path, "w", encoding="utf-8", newline="") as f:
            f.write(text.replace(old, new))


def same(a, b):
    """True if two folders hold the same files with the same bytes."""
    found = filecmp.dircmp(a, b)
    if found.left_only or found.right_only or found.funny_files:
        return False
    _, differ, errors = filecmp.cmpfiles(a, b, found.common_files,
                                         shallow=False)
    return not differ and not errors and all(
        same(os.path.join(a, d), os.path.join(b, d))
        for d in found.common_dirs)


def check():
    """Exit 0 if ../chat-world-now is what `--now` makes."""
    with tempfile.TemporaryDirectory() as out:
        main(["--now", out], quiet=True)
        made = os.path.join(out, "now", "chat-world")
        if not same(made, os.path.join(HERE, "chat-world-now")):
            sys.exit("chat-world-now is not the five deliveries with the "
                     "three repairs: run steps.py --now and compare")
    print("chat-world-now is the five deliveries with the three repairs")


def main(argv, quiet=False):
    say = (lambda *a: None) if quiet else print
    aside = argv[:1] == ["--aside"]
    now = argv[:1] == ["--now"]
    (out,) = argv[1:] if aside or now else argv
    before = os.path.join(HERE, "chat-world")
    for step in "12345":
        tree = os.path.join(out, step, "chat-world")
        # The files named file@LINE in ../chat-world are the record's
        # additions, kept beside the files they were joined into.
        shutil.copytree(before, tree,
                        ignore=shutil.ignore_patterns("*@*", "target"))
        given = os.path.join(HERE, "chat-world-steps", step)
        count = 0
        for folder, _, names in sorted(os.walk(given)):
            for name in sorted(names):
                source = os.path.join(folder, name)
                dest = os.path.join(tree, os.path.relpath(source, given))
                os.makedirs(os.path.dirname(dest), exist_ok=True)
                shutil.copyfile(source, dest)
                count += 1
        say(f"delivery {step}: {count} files laid over the crate")
        before = tree
    if aside:
        tree = os.path.join(out, "5-aside", "chat-world")
        shutil.copytree(before, tree)
        os.remove(os.path.join(tree, "src", "bin", "succession-demo.rs"))
        path = os.path.join(tree, "src", "verify.rs")
        with open(path, encoding="utf-8", newline="") as f:
            text = f.read()
        if text.count(FAULT) != 1:
            sys.exit("the condition set aside is not where it was")
        with open(path, "w", encoding="utf-8", newline="") as f:
            f.write(text.replace(FAULT, "if false {"))
        say("delivery 5, two faults set aside: 5-aside")
    if now:
        repaired(before, os.path.join(out, "now", "chat-world"))
        say("delivery 5, three faults repaired: now")


if __name__ == "__main__":
    if sys.argv[1:] == ["--check"]:
        check()
    elif len(sys.argv) in (2, 3):
        main(sys.argv[1:])
    else:
        sys.exit(__doc__)

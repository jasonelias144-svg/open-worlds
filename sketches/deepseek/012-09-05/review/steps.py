"""Ours, not DeepSeek's (see ../README.md). Puts together the crate as
it stands after each of the five deliveries that record 012-09-05 ends
with. The deliveries' files are kept in ../chat-world-steps/1 to 5,
as the record gives them (../../tools/extract.py checks that). This
lays each delivery over the one before, starting from the crate
DeepSeek was given, ../chat-world.

    python3 steps.py OUT            OUT/1 ... OUT/5
    python3 steps.py --aside OUT    and OUT/5-aside

Nothing is run: this only copies files. Each OUT/N/chat-world is the
crate after delivery N. A file a delivery doesn't give stays as the
delivery before left it.

`--aside` also writes OUT/5-aside: delivery 5 with its two faults set
aside, so that the rest of it can be built and tested. The faults are
not repaired: one condition in src/verify.rs that does not compile is
replaced by `false`, and src/bin/succession-demo.rs is left out.

../chat-world-steps/0 is not used: it is the cycle on signed heads from
before DeepSeek was given the one file, and delivery 3 gives its files
again.
"""
import os
import shutil
import sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# The condition in delivery 5's src/verify.rs that does not compile.
FAULT = ('if !looks_like_hash(&k.entry_hashes.iter().any(|_| "x".to_string())'
         '.then(|| "".to_string()).unwrap_or_default()) {')


def main(argv):
    aside = argv[:1] == ["--aside"]
    (out,) = argv[1:] if aside else argv
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
        print(f"delivery {step}: {count} files laid over the crate")
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
        print("delivery 5, two faults set aside: 5-aside")


if __name__ == "__main__":
    if len(sys.argv) not in (2, 3):
        sys.exit(__doc__)
    main(sys.argv[1:])

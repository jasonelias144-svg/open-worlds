"""Ours, not DeepSeek's (see ../README.md). Puts together the crate as
it stands after each delivery: the five of DeepSeek's that record
012-09-05 ends with, then the three of Gemini's that followed, then
Gemini's three on the Commons. Each is laid over the one before,
starting from the crate DeepSeek was given, ../chat-world.

DeepSeek's files are kept in ../chat-world-steps/1 to 5, as the record
gives them (../../tools/extract.py checks that). Gemini's are kept in
../../../gemini/2026-11-16/steps/1 to 3 and
../../../gemini/2026-11-17/steps/1 to 3, as written, each with its
hash in its folder's MANIFEST.json.

    python3 steps.py OUT            OUT/1 ... OUT/5
    python3 steps.py --aside OUT    and OUT/5-aside
    python3 steps.py --now OUT      and OUT/5-repaired, g1, g2, g3,
                                    g3-repaired, c1, c2, c3, now
    python3 steps.py --check        is ../chat-world-now what --now makes?

Nothing is run: this only copies files. Each OUT/N/chat-world is the
crate after delivery N. A file a delivery doesn't give stays as the
delivery before left it.

`--now` goes on from delivery 5:
    5-repaired   delivery 5 with its three faults repaired (REPAIRS;
                 ../../../INDEX.md, fixes 19 to 21). This is the crate
                 Gemini was given.
    g1, g2, g3   Gemini's three deliveries, laid over it in order.
    g3-repaired  g3 with two of the crate's earlier tests corrected
                 and a room's law closed to change in place
                 (REPAIRS_AFTER; fixes 22 and 23). This is the crate
                 Gemini was given the second time.
    c1, c2, c3   Gemini's three deliveries on the Commons
                 (2026-11-17), laid over it in order.
    now          c3, with nothing changed. This is the crate as it
                 stands, kept in ../chat-world-now.

`--check` puts the crate together again and compares it with that
folder, byte for byte, and holds Gemini's files, in both of its
folders, to their hashes. So every file in ../chat-world-now is known
to be the latest that DeepSeek or Gemini gave, changed only as the two
lists of repairs say.
sketch_status_test.py runs the check.

`--aside` also writes OUT/5-aside: delivery 5 with its two faults set
aside, so that the rest of it can be built and tested. The faults are
not repaired: one condition in src/verify.rs that does not compile is
replaced by `false`, and src/bin/succession-demo.rs is left out.

../chat-world-steps/0 is not used: it is the cycle on signed heads from
before DeepSeek was given the one file, and delivery 3 gives its files
again.
"""
import filecmp
import hashlib
import json
import os
import shutil
import sys
import tempfile

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GEMINI = os.path.join(os.path.dirname(os.path.dirname(HERE)),
                      "gemini", "2026-11-16")
# Gemini's second round: the Commons' own log.
GEMINI_COMMONS = os.path.join(os.path.dirname(os.path.dirname(HERE)),
                              "gemini", "2026-11-17")
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

# Fixes 22 and 23, made after Gemini's deliveries. Fix 22: two of the
# crate's earlier tests built a room and then changed its template in
# place, with no
# record of the change. Gemini's check holds a log's template to the
# one its first record carries, and rightly refuses that. The tests now
# set the rule before the room is created; what they test is unchanged.
MADE = ("    let mut room = Room::create(template, Keypair::generate(), "
        "&Keypair::generate()).unwrap();\n")
REPAIRS_AFTER = [
    ("tests/integration.rs",
     "    let mut room = make_room();\n"
     "    room.template.rate_limit_count = 2;\n"
     "    room.template.rate_limit_window = 5;\n",
     "    let mut template = RoomTemplate::chat(\"t\", \"test\");\n"
     "    template.rate_limit_count = 2;\n"
     "    template.rate_limit_window = 5;\n" + MADE),
    ("tests/integration.rs",
     "    let mut room = make_room();\n"
     "    room.template.inter_ai_pace = 1;\n",
     "    let mut template = RoomTemplate::chat(\"t\", \"test\");\n"
     "    template.inter_ai_pace = 1;\n" + MADE),
    # Fix 23: a room's id and its law are no longer public fields, so
    # nothing outside the room's own code can change them in place. They
    # are read through world_id() and template(), which the crate had.
    ("src/room.rs",
     "pub struct Room {\n"
     "    pub world_id: DidKey,\n"
     "    pub template: RoomTemplate,\n",
     "pub struct Room {\n"
     "    world_id: DidKey,\n"
     "    template: RoomTemplate,\n"),
] + [
    # Fix 23, the other half: three tests set a room's moderation to
    # "moderator" after creating it. make_room() had made it so already,
    # so the three lines did nothing, and they no longer compile.
    ("tests/integration.rs",
     "fn " + name + "() -> Result<()> {\n"
     "    let mut room = make_room();\n"
     "    room.template.moderation = \"moderator\".into();\n",
     "fn " + name + "() -> Result<()> {\n"
     "    let mut room = make_room();\n")
    for name in ("moderator_can_redact_other",
                 "non_moderator_cannot_redact_other",
                 "human_can_override_ai")
]


def lay(given, tree):
    """Copies every file under `given` over `tree`; says how many."""
    count = 0
    for folder, _, names in sorted(os.walk(given)):
        for name in sorted(names):
            source = os.path.join(folder, name)
            dest = os.path.join(tree, os.path.relpath(source, given))
            os.makedirs(os.path.dirname(dest), exist_ok=True)
            shutil.copyfile(source, dest)
            count += 1
    return count


def repaired(before, tree, repairs=None):
    """Copies `before` to `tree` and makes the repairs: the three to
    delivery 5, unless another list is given."""
    shutil.copytree(before, tree)
    for name, old, new in (REPAIRS if repairs is None else repairs):
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


def gemini_as_written(kept=None):
    """Stops unless each of Gemini's files has the hash its folder's
    MANIFEST.json gives, and the folder holds no other file. Both of
    Gemini's folders, unless one is given."""
    if kept is None:
        gemini_as_written(GEMINI)
        gemini_as_written(GEMINI_COMMONS)
        return
    with open(os.path.join(kept, "MANIFEST.json"), encoding="utf-8") as f:
        files = json.load(f)["files"]
    found = set()
    for folder, _, names in os.walk(os.path.join(kept, "steps")):
        for name in names:
            path = os.path.join(folder, name)
            found.add(os.path.relpath(path, kept).replace(os.sep, "/"))
    if found != set(files):
        sys.exit("Gemini's files are not the ones MANIFEST.json lists")
    for name, entry in files.items():
        with open(os.path.join(kept, name), "rb") as f:
            if hashlib.sha256(f.read()).hexdigest() != entry["sha256"]:
                sys.exit(f"{name} is not as Gemini wrote it")


def check():
    """Exit 0 if ../chat-world-now is what `--now` makes."""
    gemini_as_written()
    with tempfile.TemporaryDirectory() as out:
        main(["--now", out], quiet=True)
        made = os.path.join(out, "now", "chat-world")
        if not same(made, os.path.join(HERE, "chat-world-now")):
            sys.exit("chat-world-now is not the deliveries with the listed "
                     "repairs: run steps.py --now and compare")
    print("chat-world-now is DeepSeek's five deliveries and Gemini's six, "
          "with the listed repairs")


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
        count = lay(os.path.join(HERE, "chat-world-steps", step), tree)
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
        tree = os.path.join(out, "5-repaired", "chat-world")
        repaired(before, tree)
        say("delivery 5, three faults repaired: 5-repaired")
        before = tree
        for step in "123":
            tree = os.path.join(out, "g" + step, "chat-world")
            shutil.copytree(before, tree)
            count = lay(os.path.join(GEMINI, "steps", step), tree)
            say(f"Gemini's delivery {step}: {count} files laid over: g{step}")
            before = tree
        tree = os.path.join(out, "g3-repaired", "chat-world")
        repaired(before, tree, REPAIRS_AFTER)
        say("two earlier tests corrected, a room's law closed: g3-repaired")
        before = tree
        for step in "123":
            tree = os.path.join(out, "c" + step, "chat-world")
            shutil.copytree(before, tree)
            count = lay(os.path.join(GEMINI_COMMONS, "steps", step), tree)
            say(f"Gemini's delivery {step} on the Commons: "
                f"{count} files laid over: c{step}")
            before = tree
        shutil.copytree(before, os.path.join(out, "now", "chat-world"))
        say("nothing changed after it: now")


if __name__ == "__main__":
    if sys.argv[1:] == ["--check"]:
        check()
    elif len(sys.argv) in (2, 3):
        main(sys.argv[1:])
    else:
        sys.exit(__doc__)

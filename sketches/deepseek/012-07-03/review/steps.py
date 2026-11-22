"""Ours, not DeepSeek's (see ../README.md). Puts together the crate as
it stands after each delivery: the five of DeepSeek's that followed
their first file, then the three of Gemini's that followed, then
Gemini's three on the Commons, then DeepSeek's from their second file,
then Gemini's list of doors and its repairs, then DeepSeek's rule of one
moderator's room, then what Gemini's list of doors shows besides the
count.
Each is laid over the one before, starting from the crate DeepSeek
was given, ../chat-world.

DeepSeek's files are kept in ../chat-world-steps/1 to 11, as the record
gives them (../../tools/extract.py checks that). Gemini's are kept in
../../../gemini/2026-11-16/steps/1 to 3 and
../../../gemini/2026-11-17/steps/1 to 3, ../../../gemini/2026-11-17-2,
../../../gemini/2026-11-17-3, ../../../gemini/2026-11-17-4 and
../../../gemini/2026-11-18, as written, each with its hash in its
folder's MANIFEST.json. Gemini's eight prototypes, in
../../../gemini/2026-11-22, are held to their hashes too, and laid
nowhere.

    python3 steps.py OUT            OUT/1 ... OUT/5
    python3 steps.py --aside OUT    and OUT/5-aside
    python3 steps.py --now OUT      and OUT/5-repaired, g1, g2, g3,
                                    g3-repaired, c1, c2, c3, d6,
                                    d6-repaired, d7, d7-count, doors,
                                    c4, doors-attacks, repairs, d8,
                                    now, joined, joined-fix, said,
                                    look
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
    d6           c3 with DeepSeek's delivery 6 laid over it: a room
                 that branches (../chat-world-steps/6). It does not
                 compile, for one word.
    d6-repaired  d6 with that word repaired (REPAIRS_BRANCH;
                 ../../../INDEX.md, fix 24).
    d7           DeepSeek's delivery 7 laid over it: the plug-in
                 (../chat-world-steps/7).
    d7-count     d7, with one field added to a room's law (COUNT;
                 ../../../INDEX.md, change 25): whether how many are in
                 the room is hidden outside it.
    doors        d7-count, with Gemini's list of doors laid over it
                 (../../../gemini/2026-11-17-2/steps/1) and the one
                 line that names its module (DOORS; change 26). This
                 was the crate as it stood until 2026-11-18, and the
                 three stages that follow were built beside it.
    c4           doors, with the fourth step of Gemini's round on the
                 Commons laid over it: 17 attacks on a room's seven
                 other kinds of record
                 (../../../gemini/2026-11-17/steps/4). Eight of them
                 get through, so it is built beside the crate as it
                 stands and is not laid into it. Gemini's first answer
                 to that step (steps/4-first) is kept and not used:
                 the second replaces it.
    doors-attacks  doors, with Gemini's 25 attacks on the list of
                 doors laid over it
                 (../../../gemini/2026-11-17-3/steps/1). Five of them
                 got through, so it was built beside the crate and
                 not laid into it.
    repairs      doors, with Gemini's repairs of those five laid over
                 it (../../../gemini/2026-11-17-4/steps/1): the list
                 of doors again, and the attacks with three of them
                 written again. This was the crate as it stood until
                 2026-11-21.
    d8           repairs, with DeepSeek's delivery 8 laid over it: the
                 rule of one moderator's room (../chat-world-steps/8).
                 The founder's first copy of the record ended after its
                 third file; the copy of 2026-11-21 holds all six. It
                 does not build, for one type: a head's length is not
                 turned into a usize.
    now          d8, with DeepSeek's delivery 9 laid over it: their
                 src/verify.rs again, with that type turned
                 (../chat-world-steps/9). This was the crate as it
                 stood until 2026-11-22.
    joined       now, with DeepSeek's delivery 10 laid over it: a room
                 one has joined but does not keep, and the keeper's
                 side that accepts what its members send
                 (../chat-world-steps/10), and the line that names the
                 list of doors' module, which their src/lib.rs leaves
                 out (DOORS again). Two of its tests fail, so it is
                 built beside the crate as it stands and is not laid
                 into it.
    joined-fix   joined, with DeepSeek's delivery 11 laid over it: the
                 keeper's side checks a redaction and an override as
                 the log's check does (../chat-world-steps/11). Three
                 of its tests fail; beside the crate, like joined.
    said         now, with Gemini's answer to their sixth file laid
                 over it: what a door shows besides the count (said
                 and speakers), the flag on a room with many in it
                 and nothing said, the doors listed by another number,
                 and a look into a room
                 (../../../gemini/2026-11-18/steps/1).
    look         said, with one check added to look at the founder's
                 word (LOOK; ../../../INDEX.md, change 27): a room
                 whose law hides how many are in it gives no look.
                 This is the crate as it stands, kept in
                 ../chat-world-now.

`--check` puts the crate together again and compares it with that
folder, byte for byte, and holds Gemini's files, in each of their
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
# Gemini's third round: the lobby's list of doors.
GEMINI_DOORS = os.path.join(os.path.dirname(os.path.dirname(HERE)),
                            "gemini", "2026-11-17-2")
# Gemini's fourth round: their attacks on that list.
GEMINI_ATTACKS = os.path.join(os.path.dirname(os.path.dirname(HERE)),
                              "gemini", "2026-11-17-3")
# Gemini's fifth round: the five attacks that got through, repaired.
GEMINI_REPAIRS = os.path.join(os.path.dirname(os.path.dirname(HERE)),
                              "gemini", "2026-11-17-4")
# Gemini's sixth round: what a door shows besides the count.
GEMINI_SAID = os.path.join(os.path.dirname(os.path.dirname(HERE)),
                           "gemini", "2026-11-18")
# Gemini's eight prototypes, of their own choosing: kept, laid nowhere.
GEMINI_PROTOTYPES = os.path.join(os.path.dirname(os.path.dirname(HERE)),
                                 "gemini", "2026-11-22")
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


# Fix 24, made when DeepSeek's branches were joined. The check of a
# branch reads how far the parent's last head reaches, and asked the
# head for len(), which a head does not have. Its field is `length`,
# as the comment beside the line says.
REPAIRS_BRANCH = [
    ("src/verify.rs",
     "parent.heads.last().map(|h| h.len() as usize)",
     "parent.heads.last().map(|h| h.length as usize)"),
]


# Change 25, made at the founder's word of 2026-11-17: how many are
# in a room is shown outside it by default, and a room's law can turn
# that off. A room's law gains one field. It is left out of what is
# written when it is not set, so every law written so far hashes as it
# did. A public room's law leaves it unset. A home's sets it: that a
# room which is not public hides its count unless its law says
# otherwise is the technical lead's reading.
_LAST = ("    #[serde(skip_serializing_if = \"Option::is_none\")]\n"
         "    pub moderator: Option<ModeratorSpec>,\n")
_MADE = "            moderator: None,\n        }\n    }\n\n    pub fn "
COUNT = [
    ("src/template.rs", _LAST + "}\n",
     _LAST +
     "    /// How many are in the room is shown outside it, unless this\n"
     "    /// is set. Left out of what is written when it is not set, so\n"
     "    /// a law written before this field hashes as it did.\n"
     "    #[serde(default, skip_serializing_if = \"is_false\")]\n"
     "    pub count_hidden: bool,\n"
     "}\n"),
    ("src/template.rs", _MADE + "personal_home",
     _MADE.replace("        }\n", "            count_hidden: false,\n        }\n")
     + "personal_home"),
    ("src/template.rs", _MADE + "hash",
     _MADE.replace("        }\n", "            count_hidden: true,\n        }\n")
     + "hash"),
]


# Change 26, made when Gemini's list of doors was joined: the one
# line that names its module. Gemini's file said this line would be
# added here, since src/lib.rs was not Gemini's to change.
DOORS = [
    ("src/lib.rs", "pub mod commons;\n", "pub mod commons;\npub mod doors;\n"),
]


# Change 27, made at the founder's word of 2026-11-22: a room whose
# law hides how many are in it gives no look. A look shows who wrote
# each message, so the authors could be counted, and the count the law
# hides would be given away. The founder chose this of the two that
# hold (a look that names no author, or no look), on the technical
# lead's recommendation: a room that hides its count has chosen not to
# be seen from outside, and its messages may show who is there even
# without their authors. One check in look, after the one that refuses
# a closed room or a home.
LOOK = [
    ("src/doors.rs",
     "            \"look refused: room is not open and non-personal\".into(),\n"
     "        ));\n"
     "    }\n",
     "            \"look refused: room is not open and non-personal\".into(),\n"
     "        ));\n"
     "    }\n"
     "\n"
     "    if room.template.count_hidden {\n"
     "        return Err(Error::Policy(\n"
     "            \"look refused: the room's law hides how many are in it\".into(),\n"
     "        ));\n"
     "    }\n"),
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
    MANIFEST.json gives, and the folder holds no other file. Each of
    Gemini's folders, unless one is given."""
    if kept is None:
        gemini_as_written(GEMINI)
        gemini_as_written(GEMINI_COMMONS)
        gemini_as_written(GEMINI_DOORS)
        gemini_as_written(GEMINI_ATTACKS)
        gemini_as_written(GEMINI_REPAIRS)
        gemini_as_written(GEMINI_SAID)
        gemini_as_written(GEMINI_PROTOTYPES)
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
        made = os.path.join(out, "look", "chat-world")
        if not same(made, os.path.join(HERE, "chat-world-now")):
            sys.exit("chat-world-now is not the deliveries with the listed "
                     "repairs: run steps.py --now and compare")
    print("chat-world-now is DeepSeek's nine deliveries and Gemini's nine, "
          "with the listed repairs and changes")


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
        tree = os.path.join(out, "d6", "chat-world")
        shutil.copytree(before, tree)
        count = lay(os.path.join(HERE, "chat-world-steps", "6"), tree)
        say(f"DeepSeek's delivery 6, a room that branches: "
            f"{count} files laid over: d6")
        before = tree
        tree = os.path.join(out, "d6-repaired", "chat-world")
        repaired(before, tree, REPAIRS_BRANCH)
        say("one word repaired: d6-repaired")
        before = tree
        tree = os.path.join(out, "d7", "chat-world")
        shutil.copytree(before, tree)
        count = lay(os.path.join(HERE, "chat-world-steps", "7"), tree)
        say(f"DeepSeek's delivery 7, the plug-in: "
            f"{count} files laid over: d7")
        before = tree
        tree = os.path.join(out, "d7-count", "chat-world")
        repaired(before, tree, COUNT)
        say("a room's law can hide its count: d7-count")
        before = tree
        tree = os.path.join(out, "doors", "chat-world")
        repaired(before, tree, DOORS)
        count = lay(os.path.join(GEMINI_DOORS, "steps", "1"), tree)
        say(f"Gemini's list of doors: {count} files laid over, and its "
            f"module named: doors")
        before = tree
        tree = os.path.join(out, "c4", "chat-world")
        shutil.copytree(before, tree)
        count = lay(os.path.join(GEMINI_COMMONS, "steps", "4"), tree)
        say(f"Gemini's fourth step, beside the crate as it stood: "
            f"{count} file laid over: c4")
        tree = os.path.join(out, "doors-attacks", "chat-world")
        shutil.copytree(before, tree)
        count = lay(os.path.join(GEMINI_ATTACKS, "steps", "1"), tree)
        say(f"Gemini's attacks on the list of doors, beside the crate as "
            f"it stood: {count} file laid over: doors-attacks")
        tree = os.path.join(out, "repairs", "chat-world")
        shutil.copytree(before, tree)
        count = lay(os.path.join(GEMINI_REPAIRS, "steps", "1"), tree)
        say(f"Gemini's repairs of the five attacks that got through: "
            f"{count} files laid over: repairs")
        before = tree
        tree = os.path.join(out, "d8", "chat-world")
        shutil.copytree(before, tree)
        count = lay(os.path.join(HERE, "chat-world-steps", "8"), tree)
        say(f"DeepSeek's delivery 8, the rule of one moderator's room: "
            f"{count} files laid over: d8")
        before = tree
        tree = os.path.join(out, "now", "chat-world")
        shutil.copytree(before, tree)
        count = lay(os.path.join(HERE, "chat-world-steps", "9"), tree)
        say(f"DeepSeek's delivery 9, the check again with one type "
            f"turned: {count} file laid over: now")
        before = tree
        tree = os.path.join(out, "joined", "chat-world")
        shutil.copytree(before, tree)
        count = lay(os.path.join(HERE, "chat-world-steps", "10"), tree)
        repaired(tree, tree + "-doors", DOORS)
        shutil.rmtree(tree)
        os.rename(tree + "-doors", tree)
        say(f"DeepSeek's delivery 10, a room one has joined, beside the "
            f"crate as it stands: {count} files laid over, and the list "
            f"of doors named again: joined")
        before = tree
        tree = os.path.join(out, "joined-fix", "chat-world")
        shutil.copytree(before, tree)
        count = lay(os.path.join(HERE, "chat-world-steps", "11"), tree)
        say(f"DeepSeek's delivery 11, the keeper's side checked as the "
            f"log is, beside the crate as it stands: {count} files laid "
            f"over: joined-fix")
        tree = os.path.join(out, "said", "chat-world")
        shutil.copytree(os.path.join(out, "now", "chat-world"), tree)
        count = lay(os.path.join(GEMINI_SAID, "steps", "1"), tree)
        say(f"Gemini's answer to their sixth file, what a door shows "
            f"besides the count, laid over now: {count} files: said")
        repaired(tree, os.path.join(out, "look", "chat-world"), LOOK)
        say("no look into a room whose law hides its count: look")


if __name__ == "__main__":
    if sys.argv[1:] == ["--check"]:
        check()
    elif len(sys.argv) in (2, 3):
        main(sys.argv[1:])
    else:
        sys.exit(__doc__)

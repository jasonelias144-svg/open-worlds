"""Ours, not DeepSeek's (see README.md): the Rust sketch here, as it
stands after the changes README.md lists, is what README.md says it
is. It reads the files as text, and neither builds nor runs them;
review/run.sh does that, outside CI.

If one of these fails, the sketch has been changed again: say so in
README.md and INDEX.md, list the file under "changed" in
../../tools/names-012-09-05.json, and change the test with them."""
import re
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).parent
CRATE = HERE / "chat-world"


def _source(name):
    return (CRATE / "src" / name).read_text(encoding="utf-8")


def _visible_log():
    room = _source("room.rs")
    return room[room.index("pub fn visible_log("):]


def test_the_visible_log_hashes_the_record_a_message_is_in():
    # Fix 16. As written it called m.hash(), and Message has no such
    # method, so the crate didn't build.
    room = _source("room.rs")
    assert "m.hash()" not in room
    assert "let hash = rec.hash().unwrap_or_default();" in _visible_log()
    record = _source("record.rs")
    message = record[record.index("impl Message {"):]
    message = message[:message.index("\n}\n")]
    assert "fn hash" not in message
    assert re.search(r"impl Record \{\s+pub fn hash\(", record)


def test_the_later_files_are_joined_to_the_crate():
    # Fix 17: the three modules, the three records and their arms, and
    # the later tests, without the one DeepSeek withdrew.
    lib = _source("lib.rs")
    record = _source("record.rs")
    verify = _source("verify.rs")
    for module in ("transcript", "home", "commons"):
        assert (CRATE / "src" / f"{module}.rs").is_file(), module
        assert lib.count(f"pub mod {module};") == 1, module
    enum = record[record.index("pub enum Record {"):]
    enum = enum[:enum.index("}")]
    for kind in ("PortLanding", "Bookmark", "Presence"):
        assert f"    {kind}({kind})," in enum, kind
        assert record.count(f"pub struct {kind} {{") == 1, kind
        assert f"Record::{kind}(" in verify, kind
    assert "pub(crate) fn push(&mut self, rec: Record)" in _source("room.rs")
    tests = (CRATE / "tests" / "integration.rs").read_text(encoding="utf-8")
    assert tests.count("#[test]") == 18
    assert "port_rejected_in_non_personal_room" not in tests


def test_a_record_is_signed_as_it_is_written_out():
    # Fix 18. A Record is written with a "type" beside its fields. As
    # written, the bare struct was signed and the Record was checked,
    # so no signature verified. Now both read the same bytes.
    assert '#[serde(tag = "type", rename_all = "snake_case")]\npub enum Record' \
        in _source("record.rs")
    lib = _source("lib.rs")
    assert "hash::body_for_signing(&rec)" not in lib
    assert lib.count(
        "let body = hash::body_for_signing(&wrap(rec.clone()))?;") == 2
    assert "let body = hash::body_for_signing(rec)?;" in _source("verify.rs")
    stripped = _source("hash.rs")
    assert 'map.remove("proof");' in stripped
    assert 'map.remove("type");' not in stripped
    # Every place a record is signed passes the wrapping: seven in
    # room.rs, three in home.rs, and nowhere else.
    calls = []
    for path in sorted((CRATE / "src").glob("*.rs")):
        source = path.read_text(encoding="utf-8")
        found = re.findall(r"crate::sign_record(?:_dual)?\((.*?)\)\?;",
                           source, re.S)
        assert len(found) == {"room.rs": 7, "home.rs": 3}.get(path.name, 0), \
            path.name
        calls += found
    assert len(calls) == 10
    for call in calls:
        assert re.search(r", Record::\w+, \|r, p\| r\.proof = p$", call), call


def test_a_redaction_is_read_after_the_message_it_hides():
    # A finding, not fixed: the visible log goes through the records
    # once, in order, and notes a redaction when it reaches it, which
    # is after the message. So a redacted message's text still shows.
    log = _visible_log()
    assert log.count("for rec in &self.records {") == 1
    assert log.count("redacted_hashes.insert(") == 1
    assert log.count("redacted_hashes.contains(") == 1


def test_it_uses_none_of_open_worlds_own_crates():
    cargo = (CRATE / "Cargo.toml").read_text(encoding="utf-8")
    for ours in ("formats", "world-log", "path ="):
        assert ours not in cargo, ours
    for theirs in ("chrono", "rand", "hex", "thiserror"):
        assert re.search(rf"(?m)^{theirs} = ", cargo), theirs


def test_its_keys_are_hex_and_its_time_is_the_clock():
    # open-worlds' own did:key is the Multikey form (z6Mk...), and a
    # record's time is given to it, never read from the clock inside.
    assert 'format!("did:key:{}", hex::encode(vk.to_bytes()))' in \
        _source("did.rs")
    assert "chrono::Utc::now()" in _source("lib.rs")


def test_the_crate_as_it_stands_is_the_deliveries_with_the_listed_repairs():
    # Fixes 19 to 24, changes 25 and 26. chat-world-now is put together here, so nothing in
    # the record says what it must hold. review/steps.py does: the crate
    # DeepSeek was given, DeepSeek's five deliveries laid over it in
    # order, three repairs, Gemini's three deliveries, two earlier tests
    # corrected, a room's law closed to change in place, Gemini's three
    # deliveries on the Commons, DeepSeek's branches with one word
    # repaired, DeepSeek's plug-in, one field added to a room's law at
    # the founder's word, Gemini's list of doors with the line that
    # names its module, and Gemini's repairs of the five attacks on it
    # that got through. This runs its check, which also holds Gemini's
    # files to their hashes.
    done = subprocess.run(
        [sys.executable, "-I", str(HERE / "review" / "steps.py"), "--check"],
        capture_output=True, text=True)
    assert done.returncode == 0, done.stdout + done.stderr
    tests = HERE / "chat-world-now" / "tests"
    for name, count in (("integration.rs", 41), ("outside.rs", 3),
                        ("attack.rs", 22), ("commons_outside.rs", 3),
                        ("commons_attack.rs", 16),
                        ("commons_across.rs", 7),
                        ("branch.rs", 11), ("plugin.rs", 9),
                        ("doors.rs", 15), ("doors_attack.rs", 25)):
        text = (tests / name).read_text(encoding="utf-8")
        assert text.count("#[test]") == count, name
    # Change 25: the one field, left out of what is written when it is
    # not set; unset for a public room, set for a home.
    law = (HERE / "chat-world-now" / "src" / "template.rs").read_text(
        encoding="utf-8")
    assert ('    #[serde(default, skip_serializing_if = "is_false")]\n'
            '    pub count_hidden: bool,\n') in law
    assert law.count("count_hidden: false,") == 1
    assert law.count("count_hidden: true,") == 1


def test_geminis_files_are_the_ones_their_record_gives():
    # Gemini's deliveries are laid over the crate by review/steps.py.
    # They are kept in ../../gemini/2026-11-16 and 2026-11-17, taken
    # out of Gemini's conversation record by each folder's take.py. Run
    # with no argument, it takes them out of the record again and
    # compares.
    for folder, count in (("2026-11-16", 10), ("2026-11-17", 7),
                          ("2026-11-17-2", 2), ("2026-11-17-3", 1),
                          ("2026-11-17-4", 2)):
        take = HERE.parent.parent / "gemini" / folder / "take.py"
        done = subprocess.run([sys.executable, "-I", str(take)],
                              capture_output=True, text=True)
        assert done.returncode == 0, done.stdout + done.stderr
        assert (f"{count} files from the record; 0 problem(s)"
                in done.stdout), folder
    # The fourth step of the second round was answered twice: ten
    # attacks that the check already refuses, then seventeen, eight of
    # which get through (review/steps.sh, c4). Neither is in the crate
    # as it stands.
    steps = HERE.parent.parent / "gemini" / "2026-11-17" / "steps"
    for name, count in (("4-first", 10), ("4", 17)):
        text = (steps / name / "tests" / "attack_more.rs").read_text(
            encoding="utf-8")
        assert text.count("#[test]") == count, name
    assert not (HERE / "chat-world-now" / "tests" / "attack_more.rs").exists()
    # The 25 attacks on the list of doors: five got through as first
    # written (review/steps.sh, doors-attacks), so that file was kept
    # beside the crate. Gemini then repaired the list and wrote three
    # of the attacks again; that file, still 25 tests, is the one in
    # the crate as it stands.
    gemini = HERE.parent.parent / "gemini"
    first = (gemini / "2026-11-17-3" / "steps" / "1" / "tests"
             / "doors_attack.rs").read_bytes()
    again = (gemini / "2026-11-17-4" / "steps" / "1" / "tests"
             / "doors_attack.rs").read_bytes()
    assert first.count(b"#[test]") == 25
    assert again.count(b"#[test]") == 25
    now = HERE / "chat-world-now"
    assert (now / "tests" / "doors_attack.rs").read_bytes() == again
    assert (now / "tests" / "doors_attack.rs").read_bytes() != first
    assert (now / "src" / "doors.rs").read_bytes() == (
        gemini / "2026-11-17-4" / "steps" / "1" / "src"
        / "doors.rs").read_bytes()


def test_the_delivery_that_was_cut_off_is_kept_and_not_laid_in():
    # DeepSeek's eighth delivery, the rule of one moderator's room, was
    # cut off after three files. They are kept as given. The crate as
    # it stands does not hold them: its records have no moderator's
    # scope, which those three files add.
    given = HERE / "chat-world-steps" / "8"
    names = sorted(str(p.relative_to(given)).replace("\\", "/")
                   for p in given.rglob("*") if p.is_file())
    assert names == ["src/home.rs", "src/record.rs", "src/room.rs"]
    assert "ModeratorScope" in (given / "src" / "record.rs").read_text(
        encoding="utf-8")
    now = HERE / "chat-world-now" / "src"
    for name in ("record.rs", "room.rs", "home.rs", "verify.rs"):
        assert "ModeratorScope" not in (now / name).read_text(
            encoding="utf-8"), name

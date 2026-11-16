"""Ours, not DeepSeek's (see README.md): the Rust sketch here, as it
stands after the changes README.md lists, is what README.md says it
is. It reads the files as text, and neither builds nor runs them;
review/run.sh does that, outside CI.

If one of these fails, the sketch has been changed again: say so in
README.md and INDEX.md, list the file under "changed" in
../../tools/names-012-09-05.json, and change the test with them."""
import re
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
    for name in ("room.rs", "home.rs"):
        for call in re.findall(r"crate::sign_record(?:_dual)?\(([^\n]*)\)\?;",
                               _source(name)):
            assert re.search(r", Record::\w+, \|r, p\| r\.proof = p$", call), call


def test_a_redaction_is_read_after_the_message_it_hides():
    # A finding, not fixed: the visible log goes through the records
    # once, in order, and notes a redaction when it reaches it, which
    # is after the message. So a redacted message's text still shows.
    log = _visible_log()
    assert log.count("for rec in &self.records {") == 1
    loop = log[log.index("for rec in &self.records {"):]
    assert loop.index("redacted_hashes.insert(") < \
        loop.index("redacted_hashes.contains(")
    assert log.count("redacted_hashes.insert(") == 1


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

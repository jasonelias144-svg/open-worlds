"""Ours, not DeepSeek's (see README.md): the Rust sketch here, as
written, is what README.md says it is. It reads DeepSeek's files as
text, and neither builds nor runs them; review/run.sh does that,
outside CI.

If one of these fails, the sketch has been changed: say so in README.md
and INDEX.md, list the file under "changed" in
../../tools/names-012-09-05.json, and change the test with them."""
import re
from pathlib import Path

HERE = Path(__file__).parent
CRATE = HERE / "chat-world"


def _source(name):
    return (CRATE / "src" / name).read_text(encoding="utf-8")


def test_room_rs_calls_a_method_message_does_not_have():
    # Finding 1: it doesn't build as written.
    assert "let hash = m.hash().unwrap_or_default();" in _source("room.rs")
    record = _source("record.rs")
    message = record[record.index("impl Message {"):]
    message = message[:message.index("\n}\n")]
    assert "fn hash" not in message
    assert re.search(r"impl Record \{\s+pub fn hash\(", record)


def test_a_record_is_signed_without_its_type_and_checked_with_it():
    # Finding 2's cause. The room signs the bare struct, then wraps it
    # as a Record, which writes a "type" beside the struct's fields;
    # the check reads the bytes of the Record, type included.
    record = _source("record.rs")
    assert '#[serde(tag = "type", rename_all = "snake_case")]\npub enum Record' \
        in record
    room = _source("room.rs")
    assert re.search(
        r"let signed = crate::sign_record_dual\(rec, [^\n]+\n"
        r"\s+let out = Record::Message\(signed\);", room)
    signing = _source("lib.rs")
    assert signing.count("let body = hash::body_for_signing(&rec)?;") == 2
    assert "let body = hash::body_for_signing(rec)?;" in _source("verify.rs")
    stripped = _source("hash.rs")
    assert 'map.remove("proof");' in stripped
    assert 'map.remove("type");' not in stripped


def test_the_later_files_are_not_named_by_the_crate():
    # The crate's lib.rs is the one from DeepSeek's main reply. Its
    # later reply gives three more files and says which lines to add.
    lib = _source("lib.rs")
    later = (CRATE / "src" / "lib.rs@14578").read_text(encoding="utf-8")
    for name in ("transcript", "home", "commons"):
        assert (CRATE / "src" / f"{name}.rs").is_file(), name
        assert f"pub mod {name};" not in lib, name
        assert f"pub mod {name};" in later, name


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

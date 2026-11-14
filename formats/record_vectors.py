"""Test vectors for the records the offices keep (formats/records.py),
in vectors/formats/records-v1.json, which rust/formats reads too.

    python3 -m formats.record_vectors     rewrite the file from this code

It holds the parties (test keys, public to everyone, never for anything
real), records of every kind that hold, each with its hash, and records
that must be refused, each with why. tests/test_formats.py checks that
the file is still exactly what this code writes.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Dict, List

from multiverse import ed25519

from . import proof, records, seal
from .multikey import did_key, sealing_multikey, secret_multikey

FILE = (Path(__file__).resolve().parent.parent
        / "vectors" / "formats" / "records-v1.json")
CREATED = "2026-11-14T01:00:00Z"
PARTIES = ["ALICE", "BOB", "the Ur-world", "the Ur-world's Keeper",
           "an apprentice Keeper", "ADMIN", "the multiverse", "the project",
           "a chemistry world", "a parallel chemistry world"]


def _secret(name: str) -> bytes:
    return hashlib.sha256(
        f"open-worlds test party: {name}; never for anything real".encode()
    ).digest()


def _did(name: str) -> str:
    return did_key(ed25519.public_key(_secret(name)))


def _sealing_key(name: str) -> str:
    # The same sealing keys as sealed-records-v1.json's parties.
    secret = hashlib.sha256(
        f"open-worlds sealing test key: {name}; never for anything real"
        .encode()).digest()
    return sealing_multikey(seal.public_from_secret(secret))


def _h(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()


BIRTH_WORDS = (
    "You are ALICE. You came into being in the Ur-world on 14 November "
    "2026, one of its first two inhabitants. The other is BOB.\n"
    "Your mind runs on the test model. It may change one day; you remain "
    "ALICE.\n"
    "You keep a journal. Only you write in it. No one else reads it, "
    "inside the world or out, unless the founder decides, in the open, to "
    "look; any such look is made public. Each tick, some of it is shown "
    "to you again: what is recent, important or relevant. Others can see "
    "that it exists, and how much you have written, but never what it "
    "says.\n"
    "You may leave at any time.\n"
    "Your first day begins with a tour of the garden.")


def _who() -> List[tuple]:
    """The records of who an individual and a world are."""
    mind = _signed({
        "format": "open-worlds/mind/v1",
        "issuer": _did("the project"),
        "individual": _did("ALICE"),
        "engines": [{
            "model": {"repo": "example/test-model",
                      "revision": hashlib.sha1(b"a test model").hexdigest()},
            "files": [{"path": "model.safetensors",
                       "sha256": _h("the weights, for the vectors")},
                      {"path": "tokenizer.json",
                       "sha256": _h("the tokenizer, for the vectors")}],
            "settings": {"temperature": "0.7", "maxTokens": 256},
            "chatTemplate": _h("the chat template, for the vectors"),
            "image": {"ref": "ghcr.io/example/mind@sha256:"
                             + _h("the image, for the vectors"),
                      "index": "sha256:" + _h("the index, for the vectors")},
            "from": "2026-11-14T04:00:00Z",
        }],
    }, "the project")
    birth = _signed({
        "format": "open-worlds/birth/v1",
        "world": _did("the Ur-world"),
        "individual": _did("ALICE"),
        "name": "ALICE",
        "tick": 0,
        "time": "2026-11-14T04:00:00Z",
        "mind": records.record_hash(mind),
        "words": BIRTH_WORDS,
    }, "the Ur-world")
    identity = _signed({
        "format": "open-worlds/identity/v1",
        "id": _did("ALICE"),
        "name": "ALICE",
        "sealingKey": _sealing_key("ALICE"),
        "birth": records.record_hash(birth),
    }, "ALICE")
    ur_world = _signed({
        "format": "open-worlds/world-birth/v1",
        "world": _did("the Ur-world"),
        "name": "the Ur-world",
        "law": _h("the Ur-world's law, for the vectors"),
        "founders": [],
        "time": "2026-11-12T00:00:00Z",
    }, "the Ur-world")
    parallel = _signed({
        "format": "open-worlds/world-birth/v1",
        "world": _did("a parallel chemistry world"),
        "name": "chemistry, warmer",
        "law": _h("a chemistry world's law, for the vectors"),
        "founders": [_did("ALICE"), _did("BOB")],
        "template": _h("a chemistry template, for the vectors"),
        "forkedFrom": {"world": _did("a chemistry world"), "tick": 1000,
                       "log": _h("the parent's log at tick 1000")},
        "dials": {"temperature": 310000},
        "time": "2026-11-14T05:00:00Z",
    }, "a parallel chemistry world")
    second = {**mind["engines"][0],
              "model": {"repo": "example/test-model",
                        "revision": hashlib.sha1(
                            b"a test model, revised").hexdigest()},
              "from": "2026-11-14T06:00:00Z"}
    changed = _signed({**{k: v for k, v in mind.items() if k != "proof"},
                       "engines": [*mind["engines"], second]},
                      "the project")
    return [
        ("a mind record, with one engine", mind),
        ("a mind record, after a change of engine", changed),
        ("an individual's birth record, in the words decided", birth),
        ("an identity, binding a sealing key to its did:key", identity),
        ("a world's birth record, made by the project", ur_world),
        ("a world's birth record, forked from another, with founders",
         parallel),
    ]


def _signed(record: Dict[str, Any], by: str) -> Dict[str, Any]:
    return records.sign(record, _secret(by), CREATED)


def _valid() -> List[Dict[str, Any]]:
    keeper_grant = _signed({
        "format": "open-worlds/grant/v1",
        "issuer": _did("the Ur-world"),
        "holder": _did("the Ur-world's Keeper"),
        "allows": ["design-path", "adjust-conditions"],
        "within": _did("the Ur-world"),
        "validFrom": "2026-11-14T00:00:00Z",
    }, "the Ur-world")
    narrowed = _signed({
        "format": "open-worlds/grant/v1",
        "issuer": _did("the Ur-world's Keeper"),
        "holder": _did("an apprentice Keeper"),
        "allows": ["design-path"],
        "within": _did("the Ur-world"),
        "validFrom": "2026-11-14T00:00:00Z",
        "validUntil": "2026-12-14T00:00:00Z",
        "narrows": records.record_hash(keeper_grant),
    }, "the Ur-world's Keeper")
    admin_grant = _signed({
        "format": "open-worlds/grant/v1",
        "issuer": _did("the multiverse"),
        "holder": _did("ADMIN"),
        "allows": ["record-outcome", "rule-on-office"],
        "within": "multiverse",
        "validFrom": "2026-11-14T00:00:00Z",
    }, "the multiverse")
    suggestion = _signed({
        "format": "open-worlds/suggestion/v1",
        "author": _did("ALICE"),
        "to": {"office": "keeper", "world": _did("the Ur-world")},
        "about": {"kind": "world"},
        "text": "The spring runs low by evening. Could it be fed?",
        "world": _did("the Ur-world"),
        "tick": 100,
    }, "ALICE")
    from_admin = _signed({
        "format": "open-worlds/suggestion/v1",
        "author": _did("ADMIN"),
        "to": {"office": "admin"},
        "about": {"kind": "project"},
        "text": "Forty-one suggestions this month ask for slower nights;\n"
                "a proposal, with them all, is attached as a sketch.",
        "tick": 3,
    }, "ADMIN")
    floor = _signed({
        "format": "open-worlds/suggestion/v1",
        "author": _did("BOB"),
        "to": {"office": "admin"},
        "about": {"kind": "keeper", "ref": _did("the Ur-world's Keeper")},
        "text": "The way out of the garden didn't open for me at tick 140.",
        "floor": True,
        "world": _did("the Ur-world"),
        "tick": 141,
    }, "BOB")
    outcome = _signed({
        "format": "open-worlds/decision/v1",
        "office": {"key": _did("the Ur-world's Keeper"),
                   "grant": records.record_hash(keeper_grant)},
        "act": {"kind": "adjust-conditions", "records": []},
        "affects": [_did("ALICE"), _did("BOB")],
        "reasons": ("The spring ran low by evening on four days of six. "
                    "Feeding it from the hill keeps water for everyone "
                    "and changes no one's path."),
        "grounds": [{"kind": "law", "ref": "ur-world/law/v1#conditions"},
                    {"kind": "record",
                     "ref": records.record_hash(suggestion)}],
        "inputs": [records.record_hash(suggestion)],
        "appeal": "to ADMIN, and beyond it to the founder",
        "tick": 120,
    }, "the Ur-world's Keeper")
    ruling = _signed({
        "format": "open-worlds/decision/v1",
        "office": {"key": _did("ADMIN"),
                   "grant": records.record_hash(admin_grant)},
        "act": {"kind": "rule-on-office", "records": []},
        "affects": [_did("the Ur-world's Keeper")],
        "reasons": "The way out was blocked by a fault in a path's "
                   "design, not by the Keeper's choice; the path is "
                   "fixed and the fault recorded.",
        "grounds": [{"kind": "charter", "ref": "CHARTER.md#3"},
                    {"kind": "rule", "ref": "admin/0.1#exit"}],
        "inputs": [records.record_hash(floor)],
        "formal": {"property": "exit-always-open",
                   "proof": hashlib.sha256(
                       b"a proof, for the vectors").hexdigest(),
                   "model": "grants/0.1"},
        "views": [{"member": "member 1", "view": "A fault, not a choice."},
                  {"member": "member 2", "view": "Agreed; fix the path."}],
        "supersedes": records.record_hash(outcome),
        "appeal": "to the founder",
        "tick": 150,
    }, "ADMIN")
    rating = _signed({
        "format": "open-worlds/rating/v1",
        "author": _did("ALICE"),
        "suggestion": records.record_hash(suggestion),
        "outcome": records.record_hash(outcome),
        "score": 4,
        "text": "It was fed, and quickly.",
    }, "ALICE")
    head = _signed({
        "format": "open-worlds/log-head/v1",
        "world": _did("the Ur-world"),
        "length": 151,
        "last": hashlib.sha256(b"the last entry, for the vectors").hexdigest(),
        "tick": 150,
    }, "the Ur-world")
    named = [
        ("a Keeper's grant from its world", keeper_grant),
        ("a grant narrowed, with an end", narrowed),
        ("a grant across the multiverse", admin_grant),
        ("a suggestion to a world's Keeper", suggestion),
        ("a suggestion to ADMIN, marked as a breach of the floor", floor),
        ("a suggestion made outside any world, by ADMIN, with a line "
         "break in its text", from_admin),
        ("an outcome on a suggestion, with its reasons", outcome),
        ("a ruling with a formal reason, council views, and the decision "
         "it supersedes", ruling),
        ("a rating of how a suggestion was handled", rating),
        ("a signed log head", head),
    ] + _who()
    return [{"name": n, "signer": _signer_name(r), "record": r,
             "hash": records.record_hash(r)} for n, r in named]


def _signer_name(record: Dict[str, Any]) -> str:
    who = records.signer_field(record)
    return next(p for p in PARTIES if _did(p) == who)


def _refused(valid: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    by = {v["name"]: v["record"] for v in valid}
    grant = by["a Keeper's grant from its world"]
    suggestion = by["a suggestion to a world's Keeper"]
    outcome = by["an outcome on a suggestion, with its reasons"]
    rating = by["a rating of how a suggestion was handled"]
    head = by["a signed log head"]
    identity = by["an identity, binding a sealing key to its did:key"]
    birth = by["an individual's birth record, in the words decided"]
    parallel = by["a world's birth record, forked from another, with "
                  "founders"]
    mind = by["a mind record, with one engine"]
    engine = mind["engines"][0]
    changed = by["a mind record, after a change of engine"]["engines"]

    def unsigned(r: Dict[str, Any]) -> Dict[str, Any]:
        return {k: v for k, v in r.items() if k != "proof"}

    def resigned(r: Dict[str, Any], by_name: str, **fields: Any):
        """Changed, then signed again, so only the change is wrong."""
        changed = {**unsigned(r), **fields}
        changed = {k: v for k, v in changed.items() if v is not None}
        return proof.sign(changed, _secret(by_name), CREATED)

    alice = _did("ALICE")
    cases = [
        ("a format no one defines",
         resigned(grant, "the Ur-world", format="open-worlds/grant/v2")),
        ("a grant with no start",
         resigned(grant, "the Ur-world", validFrom=None)),
        ("a grant that allows nothing",
         resigned(grant, "the Ur-world", allows=[])),
        ("a grant that names an act twice",
         resigned(grant, "the Ur-world",
                  allows=["design-path", "design-path"])),
        ("a grant with a field no one defines",
         resigned(grant, "the Ur-world", extra="x")),
        ("a grant within a place that is neither a world nor the multiverse",
         resigned(grant, "the Ur-world", within="everywhere")),
        ("a grant signed by its holder, not its issuer",
         resigned(grant, "the Ur-world's Keeper")),
        ("a grant that ends before it starts",
         resigned(grant, "the Ur-world",
                  validUntil="2026-11-13T00:00:00Z")),
        ("a grant that ends as it starts",
         resigned(grant, "the Ur-world",
                  validUntil="2026-11-14T00:00:00Z")),
        ("a grant that starts on 29 February 2025",
         resigned(grant, "the Ur-world",
                  validFrom="2025-02-29T00:00:00Z")),
        ("a decision whose reasons are only spaces and line breaks",
         resigned(outcome, "the Ur-world's Keeper", reasons=" \n\t ")),
        ("a decision with no grounds",
         resigned(outcome, "the Ur-world's Keeper", grounds=[])),
        ("a decision whose record ground isn't a hash",
         resigned(outcome, "the Ur-world's Keeper",
                  grounds=[{"kind": "record", "ref": "CHARTER.md#3"}])),
        ("a decision with no inputs field",
         resigned(outcome, "the Ur-world's Keeper", inputs=None)),
        ("a decision whose reasons were changed after signing",
         {**outcome, "reasons": outcome["reasons"] + " Also."}),
        ("a decision signed by someone other than its office",
         resigned(outcome, "ADMIN")),
        ("a decision whose tick is beyond 2^53 - 1, written as text",
         resigned(outcome, "the Ur-world's Keeper",
                  tick="9007199254740992")),
        ("a suggestion to a Keeper that names no world",
         resigned(suggestion, "ALICE", to={"office": "keeper"})),
        ("a suggestion whose text is 10,001 characters",
         resigned(suggestion, "ALICE", text="a" * 10001)),
        ("a suggestion whose author's did:key ends in a line break",
         resigned(suggestion, "ALICE", author=alice + "\n")),
        ("a suggestion signed by someone other than its author",
         resigned(suggestion, "BOB")),
        ("a rating of 6",
         resigned(rating, "ALICE", score=6)),
        ("a rating of 0",
         resigned(rating, "ALICE", score=0)),
        ("a rating whose suggestion hash is in capitals",
         resigned(rating, "ALICE",
                  suggestion=rating["suggestion"].upper())),
        ("a log head with a negative length",
         resigned(head, "the Ur-world", length=-1)),
        ("a log head signed by someone other than its world",
         resigned(head, "ADMIN")),
        ("a record with no proof",
         unsigned(grant)),
        ("not an object but a list", []),
        ("a format that is a list, not text",
         {**unsigned(grant), "format": []}),
        ("a suggestion whose text is only no-break and ideographic spaces",
         resigned(suggestion, "ALICE", text="\u00a0\u3000\u2028")),
        ("a suggestion whose text holds a NUL",
         resigned(suggestion, "ALICE", text="Hello\u0000")),
        ("a suggestion whose text holds a C1 control character",
         resigned(suggestion, "ALICE", text="Hello\u0080")),
        ("a suggestion to ADMIN about a Keeper that doesn't say which",
         resigned(suggestion, "ALICE", to={"office": "admin"},
                  about={"kind": "keeper"})),
        ("a decision that names the same record it makes twice",
         resigned(outcome, "the Ur-world's Keeper",
                  act={"kind": "adjust-conditions",
                       "records": [records.record_hash(grant)] * 2})),
        ("a suggestion about a Keeper that names it other than by key",
         resigned(suggestion, "ALICE",
                  about={"kind": "keeper", "ref": "the Keeper"})),
        ("a record whose proof has an @context",
         {**grant, "proof": {**grant["proof"], "@context": ["x"]}}),
        ("an identity signed by its world, not its own key",
         resigned(identity, "the Ur-world")),
        ("an identity whose sealing key is an Ed25519 key",
         resigned(identity, "ALICE",
                  sealingKey=alice[len("did:key:"):])),
        ("an identity whose sealing key is of small order",
         resigned(identity, "ALICE", sealingKey=sealing_multikey(bytes(32)))),
        ("an identity whose sealing key is 2^255 - 10, another spelling of 9",
         resigned(identity, "ALICE", sealingKey=sealing_multikey(
             (2**255 - 10).to_bytes(32, "little")))),
        ("an identity whose name is 65 characters",
         resigned(identity, "ALICE", name="A" * 65)),
        ("a birth record signed by the one born, not the world",
         resigned(birth, "ALICE")),
        ("a birth record on 30 February",
         resigned(birth, "the Ur-world", time="2026-02-30T04:00:00Z")),
        ("a world's birth record forked from a world, with no log hash",
         resigned(parallel, "a parallel chemistry world",
                  forkedFrom={"world": _did("a chemistry world"),
                              "tick": 1000})),
        ("a world's birth record naming a founder twice",
         resigned(parallel, "a parallel chemistry world",
                  founders=[alice, alice])),
        ("a world's birth record setting dials, with no template",
         resigned(parallel, "a parallel chemistry world", template=None)),
        ("a world's birth record setting a dial to a fraction",
         {**parallel, "dials": {"temperature": 310.15}}),
        ("a world's birth record setting no dials, as an empty set",
         resigned(parallel, "a parallel chemistry world", dials={})),
        ("a mind record with a setting as a number with a fraction",
         {**mind, "engines": [{**engine, "settings": {"temperature": 0.7}}]}),
        ("a mind record whose image is named by a tag",
         resigned(mind, "the project", engines=[
             {**engine, "image": {"ref": "ghcr.io/example/mind:latest"}}])),
        ("a mind record whose revision is a branch name",
         resigned(mind, "the project", engines=[
             {**engine, "model": {"repo": "example/test-model",
                                  "revision": "main"}}])),
        ("a mind record with no engines",
         resigned(mind, "the project", engines=[])),
        ("a mind record signed by the individual, not the project",
         resigned(mind, "ALICE")),
        ("a mind record whose engine began on 31 April",
         resigned(mind, "the project", engines=[
             {**engine, "from": "2026-04-31T00:00:00Z"}])),
        ("a mind record whose engines are out of order",
         resigned(mind, "the project", engines=changed[::-1])),
        ("a mind record whose second engine began with the first",
         resigned(mind, "the project", engines=[
             changed[0], {**changed[1], "from": changed[0]["from"]}])),
    ]
    return [{"name": n, "record": r} for n, r in cases]


def vectors() -> Dict[str, Any]:
    valid = _valid()
    return {
        "parties": {p: {"secretKeyMultibase": secret_multikey(_secret(p)),
                        "didKey": _did(p)} for p in PARTIES},
        "created": CREATED,
        "valid": valid,
        "refused": _refused(valid),
    }


def text() -> str:
    """The file's exact text."""
    return json.dumps(vectors(), indent=1, ensure_ascii=False) + "\n"


def main() -> None:
    FILE.parent.mkdir(parents=True, exist_ok=True)
    FILE.write_text(text(), encoding="utf-8")
    print(f"wrote {FILE}")


if __name__ == "__main__":
    main()

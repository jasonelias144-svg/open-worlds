"""Signing a key over to a new one (course step 6, part two).

An individual is its key, and so is a world (identity.py). A key may have
to be replaced: it is old, or kept somewhere no longer safe. Replacing it
must not cut the individual off from its history, or a world from the
stamps it gave. So, while the old key still can, it signs over to the new
one: a succession, signed by both keys.

- **The old key hands over.** Only its holder can say that a new key
  continues it.
- **The new key accepts.** Otherwise anyone could hang their history on
  someone else's key.
- **It names whose key it is:** a world's id, or "" for an individual. A
  world's succession can't be used for another world, or for an
  individual.

After it, the old key is retired: a world that knows the succession
refuses requests the old key signs, and stamps given to the old key count
for the new one. A key is signed over once. If a stolen old key signs over
again, to a key of the thief's, there are two successions of one key, and
a passport that carries both is refused; a world keeps the first it saw.
So sign over while the old key is still safe.

From the DeepSeek sketch's component 28, where a world's new manifest is
signed by its old key. Changed from the sketch: the new key signs too;
individuals sign over as worlds do; and a world doesn't have to be asked
for its new manifest to see the change: a passport carries the
successions its stamps need.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Dict, Iterable, List, Optional, Tuple

from .identity import Signer, signature_valid, token_problem
from .protocol import PROTOCOL_VERSION


@dataclass(frozen=True)
class Succession:
    """`old` signed over to `new`. `of` is the world id whose key this
    is, or "" for an individual's. `timestamp` is the signers' own claim.
    `wcp` is the protocol version it was signed under."""
    of: str
    old: str
    new: str
    timestamp: str
    old_signature: str = ""
    new_signature: str = ""
    wcp: str = PROTOCOL_VERSION

    def document(self) -> Dict:
        """What both keys sign."""
        return {"wcp": self.wcp, "kind": "succession", "of": self.of,
                "old": self.old, "new": self.new, "time": self.timestamp}

    def entry(self) -> Dict:
        """The succession as a plain passport entry."""
        return dict(self.document(), entry="succession",
                    old_signature=self.old_signature,
                    new_signature=self.new_signature)

    @classmethod
    def from_entry(cls, entry: object) -> "Succession":
        """Read a succession entry; ValueError if it isn't one. Reading
        doesn't check the signatures: `succession_problem` does."""
        if type(entry) is not dict or entry.get("entry") != "succession":
            raise ValueError("not a succession")
        fields = {}
        for name, key in (("of", "of"), ("old", "old"), ("new", "new"),
                          ("timestamp", "time"),
                          ("old_signature", "old_signature"),
                          ("new_signature", "new_signature"),
                          ("wcp", "wcp")):
            value = entry.get(key)
            if type(value) is not str:
                raise ValueError(f"{key} must be plain text")
            fields[name] = value
        return cls(**fields)


def sign_over(old: Signer, new: Signer, of: str = "",
              timestamp: Optional[str] = None) -> Succession:
    """`old` signs over to `new`, and `new` accepts. `of` is the world id
    when the key is a world's ("" for an individual's)."""
    if not isinstance(old, Signer) or not isinstance(new, Signer):
        raise ValueError("both keys must be Signers")
    if old.token == new.token:
        raise ValueError("a key can't be signed over to itself")
    if type(of) is not str:
        raise ValueError("of must be plain text")
    if timestamp is None:
        timestamp = datetime.now(timezone.utc).isoformat()
    unsigned = Succession(of, old.token, new.token, timestamp)
    document = unsigned.document()
    return Succession(of, old.token, new.token, timestamp,
                      old.sign(document), new.sign(document))


def succession_problem(s: object) -> str:
    """Why `s` isn't a usable succession, or "": its fields must be plain
    text, both keys usable and different, and both signatures good."""
    if type(s) is not Succession:
        return "not a succession"
    for value in vars(s).values():
        if type(value) is not str:
            return "its fields must be plain text"
    if token_problem(s.old) or token_problem(s.new):
        return "it doesn't name two usable keys"
    if s.old == s.new:
        return "it signs a key over to itself"
    document = s.document()
    if not signature_valid(s.old, document, s.old_signature):
        return "the old key's signature does not verify"
    if not signature_valid(s.new, document, s.new_signature):
        return "the new key's signature does not verify"
    return ""


class Lineage:
    """Who signed over to whom: at most one successor for each key of
    each world or individual. Built from successions that are usable
    (`succession_problem`); `add` reports a second successor of a key
    instead of taking it."""

    def __init__(self, successions: Iterable[Succession] = ()):
        self._next: Dict[Tuple[str, str], Succession] = {}
        self._before: Dict[Tuple[str, str], str] = {}
        for s in successions:
            self.add(s)

    def add(self, s: Succession) -> str:
        """Take `s`, or say why not: "" if taken (or already known). A
        key is signed over once, and a new key continues one key: a line,
        never a fork or a merge."""
        problem = succession_problem(s)
        if problem:
            return problem
        known = self._next.get((s.of, s.old))
        if known is not None:
            if known.new != s.new:
                return ("that key was already signed over to another key "
                        f"({known.new[:12]}…)")
            return ""
        if (s.of, s.new) in self._before:
            return "the new key already continues another key"
        self._next[(s.of, s.old)] = s
        self._before[(s.of, s.new)] = s.old
        return ""

    def successor(self, of: str, key: str) -> Optional[str]:
        s = self._next.get((of, key))
        return None if s is None else s.new

    def retired(self, of: str, key: str) -> bool:
        """Whether `key` has been signed over to another."""
        return (of, key) in self._next

    def latest(self, of: str, key: str) -> str:
        """The key `key` was signed over to, and so on, to the last."""
        seen = {key}
        while True:
            nxt = self.successor(of, key)
            if nxt is None or nxt in seen:
                return key
            seen.add(nxt)
            key = nxt

    def leads_to(self, of: str, earlier: str, later: str) -> bool:
        """Whether `earlier` is `later`, or was signed over to it, directly
        or through other keys."""
        seen = set()
        key: Optional[str] = earlier
        while key is not None and key not in seen:
            if key == later:
                return True
            seen.add(key)
            key = self.successor(of, key)
        return False

    def earlier_keys(self, of: str, key: str) -> List[str]:
        """The keys that were signed over, directly or not, to `key`,
        nearest first."""
        found: List[str] = []
        seen = {key}
        while (of, key) in self._before:
            key = self._before[(of, key)]
            if key in seen:
                break
            seen.add(key)
            found.append(key)
        return found

    def successions(self, of: Optional[str] = None) -> List[Succession]:
        """The successions known, all or only those of `of`."""
        return [s for (who, _), s in self._next.items()
                if of is None or who == of]

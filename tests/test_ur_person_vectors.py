"""A person in the Ur-world, checked from Python (course step 3a, part
three; docs/research/PERSONS.md).

The person's Hello World is built in Rust (rust/ur-world/src/person.rs),
the reference. Its shared vectors (vectors/ur-person.json) hold one trial
person with a presence in each of three trial worlds at once. Python checks
them independently:

- the person's presence seed is a trial key's, the SHA-256 of words that
  say "never for anything real";
- each world's log holds by the Python kernel's check, World.verify_log,
  and the head its world signed covers it;
- each presence's key is the one formats/persons.py makes from the seed,
  its world and its counter, and it signed the presence's arrival there,
  under its name;
- every link shown (`linked`) is one the world would take, checked as
  rust/ur-world's link_log_problems checks it: shown by one who is here,
  holding by formats/persons.py's link_problems, naming the log's world,
  and the presence's own (the key its name entered with), with no
  presence showing two; and that check finds a link the world refuses;
- what a local said in the first world, the person's presence in the
  second says in its own, on the tick the presence in the first heard it;
- no world's log names another world, or another world's presence, and
  only the third names the person, in the link its presence showed.

Rewrite the vectors with:
    cd rust && cargo run -p ur-world --example person -- --vectors ../vectors
"""
import copy
import hashlib
import json
import unittest
from pathlib import Path

from formats import persons, records
from formats.multikey import did_key
from multiverse import ed25519
from world import World

VECTORS = Path(__file__).resolve().parent.parent / "vectors"
TRIAL = json.loads((VECTORS / "ur-person.json").read_text(encoding="utf-8"))
SEED = bytes.fromhex(TRIAL["seed"]["hex"])


def link_log_problems(log):
    """Where the links shown in an Ur-world log fail, or []: as
    rust/ur-world/src/link.rs's link_log_problems, with the same words."""
    first = log[0] if log else {}
    world = first.get("data", {}).get("world") \
        if first.get("kind") == "world_created" else None
    if not isinstance(world, str):
        return ["[0]: not a world_created entry that names its world"]
    found, keys, here, links = [], {}, set(), {}
    for i, entry in enumerate(log):
        who, data = entry.get("agent"), entry.get("data") or {}
        kind = entry.get("kind")
        if kind == "entered":
            keys.setdefault(who, (data.get("arrival") or {}).get("individual"))
            here.add(who)
        elif kind == "exited":
            here.discard(who)
        elif kind == "linked":
            if who not in here:
                found.append(f"[{i}]: a link shown by one who isn't here")
                continue
            if "holds" not in data or "held_by" not in data:
                found.append(f"[{i}]: an entry with no link")
                continue
            holds, held_by = data["holds"], data["held_by"]
            presence = keys.get(who)
            problems = persons.link_problems(holds, held_by)
            if problems:
                why = "the link doesn't hold: " + "; ".join(problems)
            elif holds["world"] != world:
                why = "the link names another world"
            elif holds["presence"] != presence:
                why = "the link is another presence's"
            elif presence in links:
                why = ("this presence's link is shown here already"
                       if links[presence] == holds["person"] else
                       "this presence is held by another person here")
            else:
                links[presence] = holds["person"]
                continue
            found.append(f"[{i}]: a link the world refuses: {why}")
    return found


class TheTrialPerson(unittest.TestCase):

    def test_the_seed_is_a_trial_keys(self):
        made_from = TRIAL["seed"]["from"]
        self.assertIn("never for anything real", made_from)
        self.assertIn(TRIAL["seed"]["label"], made_from)
        self.assertEqual(hashlib.sha256(made_from.encode()).digest(), SEED)

    def test_three_worlds_each_with_a_presence_of_its_own(self):
        names = [w["presence"]["name"] for w in TRIAL["worlds"]]
        self.assertEqual(names, ["ASH", "BIRCH", "CEDAR"])
        keys = [w["presence"]["key"] for w in TRIAL["worlds"]]
        self.assertEqual(len(set(keys + [TRIAL["person"]])), 4)
        for w in TRIAL["worlds"]:
            with self.subTest(world=w["name"]):
                world = w["log"][0]["data"]["world"]
                p = w["presence"]
                self.assertEqual(
                    persons.presence_key(SEED, world, p["counter"]), p["key"])
                arrivals = [e["data"]["arrival"] for e in w["log"]
                            if e["kind"] == "entered"
                            and e["agent"] == p["name"]]
                self.assertEqual(len(arrivals), 1)
                records.check(arrivals[0])
                self.assertEqual(arrivals[0]["individual"], p["key"])
                self.assertEqual(arrivals[0]["world"], world)


class EachWorldsLog(unittest.TestCase):

    def test_it_holds_and_its_head_covers_it(self):
        for w in TRIAL["worlds"]:
            with self.subTest(world=w["name"]):
                log, head = w["log"], w["head"]
                self.assertTrue(World.verify_log(log))
                self.assertEqual(log[0]["data"]["rules_version"],
                                 "ur-world/0.5")
                records.check(head)
                self.assertEqual(head["world"], log[0]["data"]["world"])
                self.assertEqual(head["length"], len(log))
                self.assertEqual(head["last"], log[-1]["hash"])
                self.assertGreaterEqual(head["tick"], log[-1]["tick"])

    def test_every_link_shown_is_one_the_world_would_take(self):
        shown = []
        for w in TRIAL["worlds"]:
            with self.subTest(world=w["name"]):
                self.assertEqual(link_log_problems(w["log"]), [])
                shown += [(w["name"], e["agent"]) for e in w["log"]
                          if e["kind"] == "linked"]
        self.assertEqual(shown, [("the third trial world", "CEDAR")])
        third = TRIAL["worlds"][2]
        linked = next(e for e in third["log"] if e["kind"] == "linked")
        self.assertEqual(linked["data"]["holds"]["person"], TRIAL["person"])
        self.assertEqual(linked["data"]["holds"]["presence"],
                         third["presence"]["key"])

    def test_the_check_finds_a_link_the_world_would_refuse(self):
        first, third = TRIAL["worlds"][0]["log"], TRIAL["worlds"][2]["log"]
        at = next(i for i, e in enumerate(third) if e["kind"] == "linked")

        def changed(log, change):
            log = copy.deepcopy(log)
            change(log)
            return link_log_problems(log)

        def agent(name):
            return lambda log: log[at].update(agent=name)

        def twice(log):
            log.append(copy.deepcopy(log[at]))

        def unsigned(log):
            log[at]["data"]["holds"]["time"] = "2026-11-16T00:00:00Z"

        refuses = f"[{at}]: a link the world refuses: "
        self.assertEqual(changed(third, agent("NOBODY")),
                         [f"[{at}]: a link shown by one who isn't here"])
        self.assertEqual(changed(third, twice), [
            f"[{len(third)}]: a link the world refuses: "
            "this presence's link is shown here already"])
        found = changed(third, unsigned)
        self.assertEqual(len(found), 1)
        self.assertTrue(found[0].startswith(
            refuses + "the link doesn't hold: holds:"), found)
        # Brought into the first world, under its presence's name.
        moved = copy.deepcopy(third[at])
        moved["agent"] = "ASH"
        self.assertEqual(link_log_problems(first + [moved]), [
            f"[{len(first)}]: a link the world refuses: "
            "the link names another world"])

    def test_the_check_takes_only_the_presences_own_link_once(self):
        # Links for ASH, the person's presence in the first world, made
        # here with two trial identities of Python's own: a link holds
        # for any person's key.
        first = TRIAL["worlds"][0]
        log, world = first["log"], first["log"][0]["data"]["world"]
        ash = persons.presence_secret(SEED, world, 0)
        end = len(log)

        def trial_key(label):
            return hashlib.sha256(
                "open-worlds trial key, never for anything real: "
                f"a Python check: {label}".encode()).digest()

        def shown(by, identity):
            person = did_key(ed25519.public_key(identity))
            presence = did_key(ed25519.public_key(ash))
            fields = {"person": person, "presence": presence,
                      "world": world, "time": "2026-11-15T00:00:00Z"}
            holds = records.sign({"format": persons.HOLDS, **fields},
                                 identity, fields["time"])
            held_by = records.sign({"format": persons.HELD_BY, **fields},
                                   ash, fields["time"])
            return {"kind": "linked", "agent": by,
                    "data": {"holds": holds, "held_by": held_by}}

        one, two = trial_key("one"), trial_key("two")
        self.assertEqual(link_log_problems(log + [shown("ASH", one)]), [])
        self.assertEqual(link_log_problems(log + [shown("TEACHER", one)]), [
            f"[{end}]: a link the world refuses: "
            "the link is another presence's"])
        self.assertEqual(
            link_log_problems(log + [shown("ASH", one), shown("ASH", two)]),
            [f"[{end + 1}]: a link the world refuses: "
             "this presence is held by another person here"])


class ThroughThePerson(unittest.TestCase):

    def said(self, w):
        return [(e["tick"], e["agent"], e["data"]["text"])
                for e in TRIAL["worlds"][w]["log"] if e["kind"] == "said"]

    def test_a_lesson_goes_from_one_world_to_another_only_through_them(self):
        lesson = TRIAL["lesson"]
        self.assertEqual(self.said(0), [(0, "TEACHER", lesson)])
        # Heard by ASH at tick 1, and said by BIRCH at tick 1.
        self.assertEqual(self.said(1), [(1, "BIRCH", lesson)])
        self.assertEqual(self.said(2), [])

    def test_no_world_names_another_and_only_a_shown_link_the_person(self):
        worlds = TRIAL["worlds"]
        for i, w in enumerate(worlds):
            with self.subTest(world=w["name"]):
                text = json.dumps(w["log"])
                for j, other in enumerate(worlds):
                    if i != j:
                        self.assertNotIn(other["log"][0]["data"]["world"],
                                         text)
                        self.assertNotIn(other["presence"]["key"], text)
                unlinked = json.dumps([e for e in w["log"]
                                       if e["kind"] != "linked"])
                self.assertNotIn(TRIAL["person"], unlinked)
        self.assertIn(TRIAL["person"], json.dumps(worlds[2]["log"]))


if __name__ == "__main__":
    unittest.main()

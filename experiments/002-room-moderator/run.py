"""Try a local DeepSeek facilitator against two synthetic, signed Commons rooms."""

import argparse
import functools
import json
from pathlib import Path
import subprocess
import sys
import time

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1]))
from minds.room_moderator import audition, local_completion

ROOMS = {
    "rehearsal": "did:key:7e4efc767d67b4c81c3e936d251000a6ec5414e7fb6b9cdb5fb1a6ff0c2ccc43",
    "garden": "did:key:8d54b97a0f07b0e4fdf8997d577b5d0e52119af8ca7343d2ff1a6bfc053c0351",
}


def verified_view(plugin, room_id, log):
    if log.get("world_id") != room_id:
        raise ValueError("wrong room")
    seed = log["records"][0]
    if seed.get("world_id") != room_id or seed.get("template") != log["template"] or seed.get("type") != "room_created":
        raise ValueError("room law does not match its signed seed")
    template = seed["template"]
    if template.get("personal") is not False or template.get("join_policy") != "open":
        raise ValueError("audition requires a public, non-personal trial room")
    commands = [("import_room_log", {"log_json": log}), ("verify_room", {"room_id": room_id}),
                ("read_room", {"room_id": room_id}), ("export_room_log", {"room_id": room_id})]
    lines = [{"home_name": "disposable audition reader"}]
    lines.extend({"id": i, "method": method, "params": params} for i, (method, params) in enumerate(commands, 1))
    output = subprocess.run([plugin, "--stdin-server"], input="".join(json.dumps(line) + "\n" for line in lines),
                            text=True, capture_output=True, timeout=20, check=True)
    events = [json.loads(line) for line in output.stdout.splitlines()]
    if len(events) != 5 or events[0].get("event") != "ready":
        raise ValueError("unexpected room reader response")
    results = []
    for i, response in enumerate(events[1:], 1):
        if response.get("id") != i or response.get("error") or not isinstance(response.get("result"), dict):
            raise ValueError(f"room reader rejected {commands[i-1][0]}")
        results.append(response["result"])
    imported, verified, visible, exported = results
    if imported.get("room_id") != room_id or verified.get("ok") is not True:
        raise ValueError("room did not verify")
    if exported.get("room_id") != room_id or exported.get("log_json") != log or visible.get("room_id") != room_id:
        raise ValueError("room snapshot changed")
    return template["topic"], visible


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plugin", type=Path, required=True, help="compiled chat-world-plugin binary")
    parser.add_argument("--local-port", type=int, default=18191, metavar="PORT")
    parser.add_argument("--room", choices=ROOMS, action="append", help="default: both trial rooms")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--baseline", action="store_true", help="replay the original autonomous audition")
    mode.add_argument("--invite", metavar="ROOM:SEQ", help="select the latest visible participant turn in one trial room")
    args = parser.parse_args()
    if not 1 <= args.local_port <= 65535:
        parser.error("--local-port must be between 1 and 65535")
    invitation = None
    if args.invite:
        room, separator, seq = args.invite.partition(":")
        if not separator or room not in (args.room or ROOMS) or not seq.isascii() or not seq.isdecimal():
            parser.error("--invite must name a selected trial room and a sequence number")
        invitation = ROOMS[room], int(seq)
    failed = False
    for name in args.room or ROOMS:
        start = time.monotonic()
        record = {"case": name, "mode": "autonomous" if args.baseline else "invited", "invitation": args.invite}
        try:
            path = HERE / "rooms" / (name + ".json")
            initial = path.read_bytes()
            topic, view = verified_view(args.plugin.resolve(), ROOMS[name], json.loads(initial))
            record.update(audition(ROOMS[name], topic, view, functools.partial(local_completion, args.local_port),
                                   invitation=invitation, baseline=args.baseline))
            if path.read_bytes() != initial:
                raise ValueError("input file changed during audition")
        except (OSError, ValueError, KeyError, subprocess.SubprocessError) as exc:
            record["error"] = str(exc)
        record["seconds"] = round(time.monotonic() - start, 3)
        print(json.dumps(record, ensure_ascii=False), flush=True)
        failed |= "error" in record
    return int(failed)


if __name__ == "__main__":
    sys.exit(main())

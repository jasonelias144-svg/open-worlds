# minds/wanderer.py
"""A mind with no model behind it: the smallest program that lives in the
Ur-world through its doorway (rust/ur-world/src/door.rs).

It greets the world, then walks, turning right whenever its way is
blocked. It reads the world's messages, one JSON object a line, from its
standard input, and answers each tick with one line on its standard
output. Only the Python standard library is used.

    cd rust
    cargo run -p ur-world --example door -- \\
        --mind TRIAL-1=python3 -I ../minds/wanderer.py \\
        --mind TRIAL-2=python3 -I ../minds/wanderer.py
"""

import json
import sys

TURN_RIGHT = {"north": "east", "east": "south", "south": "west", "west": "north"}


def reply(tick, text):
    sys.stdout.write(json.dumps({"tick": tick, "reply": text}) + "\n")
    sys.stdout.flush()


def main():
    name = "?"
    heading = "east"
    greeted = False
    for line in sys.stdin:
        try:
            message = json.loads(line)
        except ValueError:
            continue
        if not isinstance(message, dict):
            continue
        if "orientation" in message:
            name = str(message.get("name", name))
            continue
        tick = message.get("tick")
        if not isinstance(tick, int):
            continue
        seen = message.get("observation") or {}
        last = seen.get("last") or {}
        if not greeted:
            greeted = True
            reply(tick, f"say Hello. I am {name}, a wanderer with no model behind me.")
            continue
        if last.get("kind") == "step_blocked":
            heading = TURN_RIGHT.get(heading, "east")
        reply(tick, f"step {heading}")


if __name__ == "__main__":
    main()

"""Take the controls of the curiosity world in a terminal."""
import argparse

from field import GOLD, HOME, WALL, State, Track, step

SIGNS = {"+": 1, "0": 0, "-": -1}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--track", choices=("intact", "one-gap", "wide-gap", "off"), default="intact")
    choice = parser.parse_args().track
    track = Track(choice != "off", {"one-gap": (7,), "wide-gap": (6, 7, 8)}.get(choice, ()))
    state = State()
    print("Bring A and B together. Once bonded, take A to 9 and back to 3.")
    print("Set each end to +, - or 0. Opposites bond on contact. A positive charge follows its gradient.")
    for tick in range(1, 17):
        line = ["·"] * (WALL + 1)
        line[state.a], line[state.b] = "A", "B"
        print(f"{tick:2}   {''.join(line)}   A={state.a}  B={state.b}  bonded={state.bonded}")
        print(f"     Gradients A {track.gradient(state.a):+}, B {track.gradient(state.b):+}; "
              f"target {HOME if state.gold else GOLD}")
        while True:
            try:
                move = input("Charges for A B (+-, -+, 0+, etc.), or leave: ").strip().replace(" ", "")
            except EOFError:
                return
            if move.lower() == "leave":
                return
            if len(move) == 2 and all(c in SIGNS for c in move):
                break
            print("Use exactly two charge symbols.")
        state, event = step(state, [SIGNS[c] for c in move], track, tick)
        print(f"     Forces {event['forces']}; positions {event['positions']}")
        if event["new_bond"]:
            print("     A and B bonded.")
        if event["home"]:
            print("     Round trip complete.")
            return
    print("Sixteen ticks elapsed.")


if __name__ == "__main__":
    main()

"""One-dimensional invented elements whose only action is changing charge."""
from dataclasses import dataclass

WALL = 14
GOLD, HOME = 9, 3
CHARGES = {"positive": 1, "neutral": 0, "negative": -1}
NAMES = {value: name for name, value in CHARGES.items()}


def sign(n):
    return (n > 0) - (n < 0)


@dataclass(frozen=True)
class State:
    a: int = 2
    b: int = 5
    bonded: bool = False
    gold: bool = False

    def __post_init__(self):
        if not 0 <= self.a < self.b <= WALL or self.bonded and self.b != self.a + 1:
            raise ValueError("beads must be ordered, in bounds and adjacent when bonded")


@dataclass(frozen=True)
class Track:
    powered: bool = True
    missing: tuple = ()

    def pad(self, gap):
        """The pad between gap and gap+1; the two boundary half-pads count."""
        if not self.powered or gap in self.missing:
            return 0
        return 1 if gap % 2 else -1

    def gradient(self, x):
        return self.pad(x - 1) - self.pad(x)


def step(state, charges, track, tick):
    if len(charges) != 2 or any(type(q) is not int or q not in NAMES for q in charges):
        raise ValueError("each end must choose -1, 0 or 1")
    if type(tick) is not int or tick < 1:
        raise ValueError("tick numbers start at one")
    qa, qb = charges
    xy = [state.a, state.b]
    bonded = state.bonded
    if bonded:
        forces = [qa * track.gradient(state.a), qb * track.gradient(state.b)]
        shift = sign(sum(forces))
        if 0 <= state.a + shift and state.b + shift <= WALL:
            xy = [x + shift for x in xy]
    else:
        toward = -qa * qb
        forces = [toward, -toward]
        for i in ((0, 1) if tick % 2 else (1, 0)):
            if toward > 0 and xy[1] == xy[0] + 1:
                break
            xy[i] = max(0, min(WALL, xy[i] + forces[i]))
        bonded = toward > 0 and xy[1] == xy[0] + 1
    gold = state.gold or (bonded and xy[0] == GOLD)
    result = State(*xy, bonded, gold)
    return result, {"tick": tick, "charges": list(charges), "forces": forces, "positions": xy,
                    "bonded": bonded, "new_bond": bonded and not state.bonded,
                    "gold": gold, "home": bonded and gold and xy[0] == HOME}


def feedback(state, track):
    if not state.bonded:
        return [1, -1]
    direction = -1 if state.gold else 1
    return [direction * sign(track.gradient(x)) for x in (state.a, state.b)]


def run_rule(name, track, choose, limit):
    state = State()
    frames = []
    for tick in range(1, limit + 1):
        state, frame = step(state, choose(state, tick), track, tick)
        frames.append(frame)
        if frame["home"]:
            break
    return {"name": name, "powered": track.powered, "missing_pads": list(track.missing),
            "start": [2, 5], "frames": frames, "stop": "home" if frames[-1]["home"] else "tick limit"}


def controls():
    on = Track()
    runs = [run_rule(name, on, lambda s, t: pair, 1)
            for name, pair in (("opposite", [1, -1]), ("alike", [1, 1]), ("neutral partner", [1, 0]))]
    reference = run_rule("switching", on, lambda s, t: feedback(s, on), 16)
    sequence = [f["charges"] for f in reference["frames"]]
    runs += [reference, run_rule("pads off", Track(powered=False), lambda s, t: sequence[t - 1], len(sequence)),
             run_rule("frozen", on, lambda s, t: sequence[min(t - 1, 1)], len(sequence))]
    for name, gaps in (("one pad missing", (7,)), ("three pads missing", (6, 7, 8))):
        track = Track(missing=gaps)
        runs.append(run_rule(name, track, lambda s, t: feedback(s, track), 16))
    return runs

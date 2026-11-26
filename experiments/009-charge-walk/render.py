"""Render three recorded trajectories side by side. Requires Pillow."""
import argparse
import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from field import GOLD, HOME, WALL, Track

INK, PAPER, MUTED = "#172C35", "#F7F8F3", "#445D60"
TEAL, PLUM, SUN = "#116B67", "#664682", "#946500"
NAMES = {"switching": "Switch charge at each site", "frozen": "Hold both charges fixed",
         "pads off": "Same switches, pads off", "solo": "7B pilots both ends", "pair": "Two pilots share a bond",
         "preview": "7B sees a one-tick preview"}
SIGNS = {1: "+", -1: "−", 0: "0"}


def font(size, bold=False):
    return ImageFont.truetype("DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf", size)


def frame_image(records, tick, subtitle):
    image = Image.new("RGB", (960, 592), PAPER)
    draw = ImageDraw.Draw(image)
    draw.text((36, 18), "Can a molecule walk?", fill=INK, font=font(36, True))
    draw.text((38, 70), subtitle, fill=MUTED, font=font(17))
    draw.text((922, 43), f"Tick {tick:02}", anchor="rm", fill=INK, font=font(23, True))
    def site(x):
        return 70 + x * 58
    for row, rec in enumerate(records):
        y = 111 + 148 * row
        draw.rounded_rectangle((28, y, 932, y + 134), radius=15, fill="#FFFFFF", outline="#D4DDDA")
        draw.text((45, y + 9), NAMES[rec["name"]], fill=INK, font=font(19, True))
        data = rec["frames"][min(tick, len(rec["frames"])) - 1] if tick and rec["frames"] else None
        a, b = data["positions"] if data else rec["start"]
        qa, qb = data["charges"] if data else (0, 0)
        bonded = data and data["bonded"]
        track = Track(rec["powered"], tuple(rec["missing_pads"]))
        if tick > len(rec["frames"]) or (rec["stop"] == "home" and tick == len(rec["frames"])):
            note = rec["stop"]
        elif data and data["new_bond"]:
            note = "bond formed"
        elif data and data["gold"] and a == GOLD:
            note = "gold reached"
        else:
            note = "bonded" if bonded else "free beads"
        draw.text((911, y + 12), note, fill=MUTED, font=font(16), anchor="ra")
        axis = y + 69
        draw.line((site(0), axis, site(WALL), axis), fill="#9DAEAB", width=2)
        for x in range(WALL + 1):
            draw.line((site(x), axis-4, site(x), axis+4), fill="#80948E", width=2)
            label = {HOME: "3 · home", GOLD: "9 · gold"}.get(x, str(x) if x in (0, WALL) else "")
            if label:
                draw.text((site(x), y+105), label, fill=SUN if x == GOLD else MUTED,
                          anchor="ma", font=font(14, x in (HOME, GOLD)))
        for gap in range(-1, WALL + 1):
            cx, cy = site(gap + .5), axis + 21
            val = track.pad(gap)
            draw.rounded_rectangle((cx-9, cy-8, cx+9, cy+8), radius=3,
                                   fill={1:"#F9D4A7",-1:"#CEE1F2",0:"#E5E9E5"}[val])
            draw.text((cx, cy), SIGNS[val] if val else "·", anchor="mm", fill=INK, font=font(13, True))
        if bonded:
            draw.line((site(a), axis, site(b), axis), fill=INK, width=7)
        for x, label, color in ((a, "A"+SIGNS[qa], TEAL), (b, "B"+SIGNS[qb], PLUM)):
            cx = site(x)
            draw.ellipse((cx-20, axis-20, cx+20, axis+20), fill=color)
            draw.text((cx, axis-1), label, anchor="mm", fill="white", font=font(16, True))
    draw.text((38, 561), "Letters identify the beads. Signs show their chosen charges. Small squares are fixed pads.",
              font=font(16), fill=MUTED)
    return image


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path)
    parser.add_argument("--pilots", action="store_true")
    args = parser.parse_args()
    folder = Path(__file__).resolve().parent
    controls = {r["name"]: r for r in json.loads((folder / "controls.json").read_text())}
    if args.pilots:
        records = [json.loads((folder / f"{n}.json").read_text()) for n in ("solo", "pair", "preview")]
        subtitle = "Three live DeepSeek trials, starting with the same two beads and the same goal."
    else:
        records = [controls[n] for n in ("switching", "frozen", "pads off")]
        subtitle = "Three recorded runs on the same lane. The line joining A and B marks a bond."
    frames = [frame_image(records, t, subtitle) for t in range(1 + max(len(r["frames"]) for r in records))]
    durations = [700] * len(frames)
    durations[0], durations[-1] = 1300, 2200
    frames[0].save(args.output, save_all=True, append_images=frames[1:], duration=durations, loop=0, disposal=2)


if __name__ == "__main__":
    main()

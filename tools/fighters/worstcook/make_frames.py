"""Generate Worst Cook's sprite frames (see tools/fighters/cutout.py).

Usage (repo root):
    python3 -I tools/fighters/worstcook/make_frames.py [<out_art_dir>]

There is no separate illustration: source.png is the first idle pose cut from
idle_crouch.jpg (already transparent, faces right), and the cut-out pipeline
poses it for every KFM action the sheets don't cover. Effects:
  6000  a burnt pancake, spinning (6 frames)
Hand-drawn sheets (green screen, cut out by tools/fighters/greensheet.py):
  7600  idle_crouch.jpg, 6 poses: 0-3 idle (action 0), 4 half-crouch (actions 10
        and 12), 5 crouching (action 11)
  7500  walk.jpg, 6 poses, all facing right (actions 20 and 21)
  7400  jump.jpg, 5 poses: crouch, rise, apex, fall, land (actions 40-47)
  7200  punch_kick.jpg, 6 poses: 0-2 light punch (action 200), 3-5 heavy kick (action 240)
  7300  guard_hit.jpg, 5 poses: stand guard, low guard, hit high, hit low, launched
        (actions 120-151 and 5000-5050)

  python3 -I tools/fighters/worstcook/make_frames.py --sheets [<art_dir>]
re-cuts only the sheets into an existing art/ (keeps everything else).
"""
import math
import os
import random
import sys

from PIL import Image, ImageDraw, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
import cutout  # noqa: E402
import greensheet  # noqa: E402

# Sheet format and anchors: tools/fighters/greensheet.py. Nothing he wears is green.
# Drawing sizes are cap widths vs the idle sheet's (~92 px).
CLEAN = {"despill": 2}
SHEETS = {
    "idle_crouch.jpg": (7600, {k: "feet" for k in range(6)}, 1.0, (), CLEAN),
    "walk.jpg": (7500, {k: "feet" for k in range(6)}, 1.03, (), CLEAN),
    # one-legged kick poses keep the body in place, so he steps into the kick
    "punch_kick.jpg": (7200, {3: "body", 4: "body"}, 0.92, (), CLEAN),
    "guard_hit.jpg": (7300, {4: "air_body"}, 1.03, (), CLEAN),
    "jump.jpg": (7400, {0: "feet", 1: "air_body", 2: "air_body", 3: "air_body", 4: "feet"}, 0.81, (), CLEAN),
}
# Measured on idle_crouch.jpg's first pose (487 px tall; the game idle is ~420), in its pixels.
CAL = {"scale": 420 / 487, "back_foot_to_axis": 158, "head_to_axis": -42, "body_to_axis": 9}


def pancake(k, size=110):
    """Frame k of 6: a charred pancake tumbling end over end, trailing smoke."""
    ss = 4
    S, c = size * ss, size * ss // 2
    im = Image.new("RGBA", (S, S))
    d = ImageDraw.Draw(im)
    a = 36 * ss
    b = max(5 * ss, abs(math.cos(math.pi * k / 6)) * 36 * ss)  # flips: full disc -> edge-on
    d.ellipse([c - a, c - b, c + a, c + b], fill=(25, 15, 8, 255))
    d.ellipse([c - a + 3 * ss, c - b + 2 * ss, c + a - 3 * ss, c + b - 2 * ss], fill=(92, 52, 22, 255))
    rnd = random.Random(7)
    for _ in range(10):  # scorch marks
        x, y = rnd.uniform(-0.65, 0.65), rnd.uniform(-0.6, 0.6)
        r = rnd.uniform(3, 8) * ss
        d.ellipse([c + x * a - r, c + y * b - r * b / a, c + x * a + r, c + y * b + r * b / a], fill=(30, 18, 10, 255))
    smoke = Image.new("RGBA", (S, S))
    sd = ImageDraw.Draw(smoke)
    for i in range(4):  # trailing puffs behind it (left = behind when thrown right)
        r = (10 + 3 * i) * ss
        x, y = c - a - (6 + 14 * i) * ss, c - (8 + 6 * ((k + i) % 3)) * ss
        sd.ellipse([x - r, y - r, x + r, y + r], fill=(110, 105, 100, 150 - 30 * i))
    smoke = smoke.filter(ImageFilter.GaussianBlur(3 * ss))
    return Image.alpha_composite(smoke, im).resize((size, size), Image.LANCZOS)


def effects(out_dir, axes):
    greensheet.cut_sheets(HERE, SHEETS, CAL, out_dir, axes)
    for k in range(6):
        pancake(k).save(os.path.join(out_dir, "6000_%d.png" % k), optimize=True)
        axes.append("6000_%d 55 55" % k)


CONFIG = {
    "source": os.path.join(HERE, "source.png"),
    "background": "alpha",
    "mirror": False,
    "hip": (235, 300),
    "ground": 546,
    "feet_x": 218,
    "split_upper": 320,
    "split_lower": 300,
    "x_range": (60, 386),
    "top": 60,
    "glow_point": (357, 175),     # raised front hand
    "glow_color": (255, 140, 40),
    "scale": 420 / 487,
    "head_box": (210, 60, 320, 170),
    "bust_box": (188, 55, 342, 235),
    "icon_bg": (40, 24, 22),
    "effects": effects,
}

if __name__ == "__main__" and "--sheets" in sys.argv:
    args = [a for a in sys.argv[1:] if a != "--sheets"]
    greensheet.recut(HERE, SHEETS, CAL, args[0] if args else os.path.join(HERE, "art"))
elif __name__ == "__main__":
    cutout.generate(CONFIG, sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "art"))

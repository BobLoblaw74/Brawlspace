"""Generate GrapeMan's sprite frames from source.png (see tools/fighters/cutout.py).

Usage (repo root):
    python3 -I tools/fighters/grapeman/make_frames.py [<out_art_dir>]

The source faces left, so it is mirrored. Effects: a spinning grape projectile
(group 6000) and a juice splat for when it lands (group 6001).

Hand-drawn sheets (green screen, cut out by tools/fighters/greensheet.py):
  7600  idle_crouch.jpg, 6 poses: 0-3 idle (action 0), 4 half-crouch (actions 10
        and 12), 5 crouching (action 11)
  7500  walk.jpg, 6 poses: 0-2 walk cycle, 3-5 the same drawn facing left (mirrored;
        actions 20 and 21)
  7400  jump.jpg, 5 poses: crouch, rise, apex, fall, land (actions 40-47)

  python3 -I tools/fighters/grapeman/make_frames.py --sheets [<art_dir>]
re-cuts only the sheets into an existing art/ (keeps everything else).
"""
import math
import os
import sys

from PIL import Image, ImageDraw, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
import cutout  # noqa: E402
import greensheet  # noqa: E402

# Hand-drawn sheets (format and anchors: tools/fighters/greensheet.py).
SHEETS = {
    # the idle stance widens and narrows: keep his body centred between his feet
    "idle_crouch.jpg": (7600, {k: "feet" for k in range(6)}, 1.0, ()),
    # a stride: centred between the feet (his "head" anchor would measure the vine crown)
    "walk.jpg": (7500, {k: "feet" for k in range(6)}, 1.0, (3, 4, 5)),
    # drawn ~0.89x (landing crouch vs the idle's half-crouch, by area and height)
    "jump.jpg": (7400, {0: "feet", 1: "air_body", 2: "air_body", 3: "air_body", 4: "feet"}, 0.89, ()),
}
# Measured on idle_crouch.jpg's first pose (529 px tall; the game idle is 421), in its pixels.
CAL = {"scale": 421 / 529, "back_foot_to_axis": 158, "head_to_axis": 0, "body_to_axis": 4.5}

INK = (38, 12, 52, 255)


def grape(angle, size=110, r=34):
    """One shiny grape with a stem and leaf, rotated by `angle` degrees."""
    ss = 4  # supersample for smooth edges
    S, R, c = size * ss, r * ss, size * ss // 2
    im = Image.new("RGBA", (S, S))
    d = ImageDraw.Draw(im)
    # stem + leaf (drawn upright, the whole grape rotates)
    d.line([(c, c - R + 6 * ss), (c + 4 * ss, c - R - 12 * ss)], fill=(92, 60, 30, 255), width=5 * ss)
    d.ellipse([c + 2 * ss, c - R - 20 * ss, c + 24 * ss, c - R - 6 * ss], fill=(86, 160, 60, 255), outline=INK, width=2 * ss)
    # body: dark rim -> purple core
    d.ellipse([c - R, c - R, c + R, c + R], fill=INK)
    for i, col in enumerate([(78, 26, 108), (104, 40, 140), (126, 58, 168), (146, 78, 190)]):
        rr = R - 3 * ss - i * 5 * ss
        off = i * 3 * ss
        d.ellipse([c - rr - off, c - rr - off, c + rr - off, c + rr - off], fill=col + (255,))
    # glossy highlights
    d.ellipse([c - R * 0.55, c - R * 0.6, c - R * 0.1, c - R * 0.25], fill=(235, 215, 255, 220))
    d.ellipse([c + R * 0.25, c + R * 0.3, c + R * 0.45, c + R * 0.5], fill=(200, 170, 240, 160))
    im = im.rotate(angle, resample=Image.BICUBIC)
    return im.resize((size, size), Image.LANCZOS)


def splat(k, size=180):
    """Juice burst frame k of 4: droplets fly out and fade."""
    im = Image.new("RGBA", (size, size))
    d = ImageDraw.Draw(im)
    c = size // 2
    fade = 1.0 - k * 0.22
    blob = 26 + k * 8
    d.ellipse([c - blob, c - blob * 0.8, c + blob, c + blob * 0.8], fill=(110, 30, 140, int(200 * fade)))
    for i in range(10):
        a = math.radians(i * 36 + 13)
        dist = 30 + k * 18 + (i % 3) * 8
        x, y = c + math.cos(a) * dist, c + math.sin(a) * dist * 0.85
        rr = max(3, 9 - k * 2 - (i % 2) * 2)
        d.ellipse([x - rr, y - rr, x + rr, y + rr], fill=(150, 60, 190, int(255 * fade)))
    d.ellipse([c - 10, c - 14, c + 4, c - 2], fill=(230, 200, 255, int(180 * fade)))
    return im.filter(ImageFilter.SMOOTH)


def effects(out_dir, axes):
    greensheet.cut_sheets(HERE, SHEETS, CAL, out_dir, axes)
    for k in range(6):  # 6000: grape spinning (60 degrees per frame)
        grape(-k * 60).save(os.path.join(out_dir, "6000_%d.png" % k), optimize=True)
        axes.append("6000_%d 55 55" % k)
    for k in range(4):  # 6001: splat
        splat(k).save(os.path.join(out_dir, "6001_%d.png" % k), optimize=True)
        axes.append("6001_%d 90 90" % k)


CONFIG = {
    "source": os.path.join(HERE, "source.png"),
    "mirror": True,               # drawn facing left; fighters face right
    "hip": (410, 400),
    "ground": 560,
    "feet_x": 440,
    "split_upper": 395,
    "split_lower": 385,
    "x_range": (190, 750),
    "top": 0,
    "torso_boxes": [(335, 380, 472, 448)],  # bottom of the grape bunch hangs between the legs
    "leg_polys": [  # thigh tops emerge from under the bunch at y~365: underlay so lunges never show a gap
        [(258, 404), (300, 378), (332, 368), (346, 352), (380, 350), (386, 392), (372, 412), (258, 430)],
        [(458, 360), (520, 348), (566, 358), (578, 404), (458, 404)],
    ],
    "leg_cut": [  # the visible part of each thigh above split_upper
        [(250, 397), (300, 376), (345, 367), (374, 372), (380, 397)],
        [(468, 376), (520, 366), (565, 372), (580, 397), (468, 397)],
    ],
    "glow_point": (712, 222),     # forward (clawed) hand
    "glow_color": (190, 90, 255),
    "scale": 0.76,
    "head_box": (410, 85, 560, 235),
    "bust_box": (215, 0, 695, 560),
    "icon_bg": (40, 20, 52),
    "effects": effects,
    "lunge": 0.4,                 # legs join under the bunch: slide less, lean more
}

if __name__ == "__main__" and "--sheets" in sys.argv:
    args = [a for a in sys.argv[1:] if a != "--sheets"]
    greensheet.recut(HERE, SHEETS, CAL, args[0] if args else os.path.join(HERE, "art"))
elif __name__ == "__main__":
    cutout.generate(CONFIG, sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "art"))

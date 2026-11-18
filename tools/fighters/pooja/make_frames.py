"""Generate Pooja's sprite frames from source.png (see tools/fighters/cutout.py).

Usage (repo root):
    python3 -I tools/fighters/pooja/make_frames.py [<out_art_dir>]

The source already faces right, on white. Her apron and kurta hang over the
hips, so the legs are traced exactly (leg_shapes). Effects:
  6000  a medjool date, tumbling (6 frames)
  6001  squish burst when a date lands (4 frames)
  6002  "?!" haggle flash for the counter stance
Hand-drawn sheets (green screen, cut out by tools/fighters/greensheet.py):
  7600  idle_crouch.jpg, 6 poses: 0-3 idle (action 0), 4 half-crouch (actions 10
        and 12), 5 crouching (action 11)
  7400  jump.jpg, 5 poses: crouch, rise, apex, fall, land (actions 40-47)

  python3 -I tools/fighters/pooja/make_frames.py --sheets [<art_dir>]
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

# Hand-drawn sheets (format and anchors: tools/fighters/greensheet.py).
SHEETS = {
    # the idle stance widens and narrows: keep her body centred between her feet
    "idle_crouch.jpg": (7600, {k: "feet" for k in range(6)}, 1.0, ()),
    # drawn ~0.66x (crouches vs the idle sheet's, by area and height); in the air her
    # head leans forward by varying amounts, so the body is what stays put
    "jump.jpg": (7400, {0: "feet", 1: "air_body", 2: "air_body", 3: "air_body", 4: "feet"}, 0.66, ()),
}
# Measured on idle_crouch.jpg's first pose (497 px tall; the game idle is 419), in its pixels.
CAL = {"scale": 419 / 497, "back_foot_to_axis": 168, "head_to_axis": -18, "body_to_axis": 6}

INK = (40, 20, 12, 255)


def date_fruit(k, size=80):
    """A glossy, wrinkled medjool date with a little stem cap, rotating 60 degrees per frame."""
    ss = 4
    S, c = size * ss, size * ss // 2
    im = Image.new("RGBA", (S, S))
    d = ImageDraw.Draw(im)
    a, b = 26 * ss, 15 * ss  # half length / half width (oval)
    d.ellipse([c - a, c - b, c + a, c + b], fill=INK)
    d.ellipse([c - a + 2 * ss, c - b + 2 * ss, c + a - 2 * ss, c + b - 2 * ss], fill=(112, 52, 24, 255))
    d.ellipse([c - a + 5 * ss, c - b + 4 * ss, c + a - 8 * ss, c + b - 3 * ss], fill=(140, 70, 30, 255))
    rnd = random.Random(31)
    for _ in range(9):  # wrinkles
        x0 = c + rnd.uniform(-a * 0.7, a * 0.6)
        y0 = c + rnd.uniform(-b * 0.6, b * 0.6)
        d.arc([x0 - 8 * ss, y0 - 3 * ss, x0 + 8 * ss, y0 + 3 * ss], rnd.uniform(180, 220), rnd.uniform(320, 360),
              fill=(70, 30, 12, 255), width=ss)
    d.ellipse([c - a * 0.55, c - b * 0.7, c - a * 0.05, c - b * 0.35], fill=(220, 160, 110, 170))  # gloss
    d.rectangle([c + a - 4 * ss, c - 3 * ss, c + a + 2 * ss, c + 3 * ss], fill=(205, 170, 100, 255), outline=INK)  # cap
    im = im.rotate(-60 * k, resample=Image.BICUBIC)
    return im.resize((size, size), Image.LANCZOS)


def squish(k, size=150):
    """Frame k of 4: sticky date bits and a syrupy splat, fading."""
    im = Image.new("RGBA", (size, size))
    d = ImageDraw.Draw(im)
    c = size // 2
    fade = 1.0 - 0.23 * k
    r = 12 + 7 * k
    d.ellipse([c - r, c - r * 0.8, c + r, c + r * 0.8], fill=(120, 55, 20, int(170 * fade)))
    rnd = random.Random(12)
    for i in range(11):
        ang = rnd.uniform(0, 2 * math.pi)
        dist = 12 + k * (12 + rnd.uniform(0, 8))
        x, y = c + math.cos(ang) * dist, c + math.sin(ang) * dist + k * k
        rr = max(2, 6 - k - (i % 2))
        d.ellipse([x - rr, y - rr, x + rr, y + rr], fill=(95, 40, 15, int(255 * fade)))
        d.ellipse([x - rr * 0.5, y - rr * 0.7, x, y - rr * 0.2], fill=(230, 170, 110, int(200 * fade)))
    return im


def haggle_flash(size=120):
    """A comic '?!' burst shown over her head during the counter stance."""
    im = Image.new("RGBA", (size, size))
    d = ImageDraw.Draw(im)
    c = size // 2
    pts = []
    for i in range(20):
        r = 54 if i % 2 == 0 else 36
        ang = math.pi * i / 10.0
        pts.append((c + math.cos(ang) * r, c + math.sin(ang) * r))
    d.polygon(pts, fill=(255, 230, 90, 235), outline=INK)
    # "?" and "!" drawn with simple strokes (no font dependency)
    d.arc([c - 26, c - 26, c - 2, c - 2], 180, 90, fill=INK, width=7)
    d.line([(c - 14, c - 2), (c - 14, c + 10)], fill=INK, width=7)
    d.ellipse([c - 18, c + 16, c - 10, c + 24], fill=INK)
    d.line([(c + 14, c - 26), (c + 14, c + 8)], fill=INK, width=8)
    d.ellipse([c + 10, c + 16, c + 18, c + 24], fill=INK)
    return im


def effects(out_dir, axes):
    greensheet.cut_sheets(HERE, SHEETS, CAL, out_dir, axes)
    for k in range(6):
        date_fruit(k).save(os.path.join(out_dir, "6000_%d.png" % k), optimize=True)
        axes.append("6000_%d 40 40" % k)
    for k in range(4):
        squish(k).save(os.path.join(out_dir, "6001_%d.png" % k), optimize=True)
        axes.append("6001_%d 75 75" % k)
    haggle_flash().save(os.path.join(out_dir, "6002_0.png"), optimize=True)
    axes.append("6002_0 60 60")


CONFIG = {
    "source": os.path.join(HERE, "source.png"),
    "mirror": False,              # already faces right
    "hip": (515, 360),
    "ground": 552,
    "feet_x": 505,
    "split_upper": 360,
    "split_lower": 350,
    "x_range": (310, 730),
    "top": 25,
    # apron and kurta hang over the hips: trace trousers + sandals exactly
    "leg_shapes": [
        [(370, 392), (420, 398), (448, 430), (460, 452), (440, 472), (400, 500), (388, 520), (385, 553),
         (322, 553), (322, 525), (345, 500), (342, 450), (350, 415)],                    # back leg
        [(590, 385), (655, 383), (670, 420), (678, 470), (665, 495), (690, 515), (690, 537), (600, 538),
         (585, 515), (585, 490), (572, 470), (575, 430)],                                  # front leg
    ],
    # cloth just above each leg (under the kurta tail / apron): uncovered, not a hole, when she lunges
    "leg_polys": [
        [(350, 330), (470, 330), (475, 440), (440, 470), (345, 470)],
        [(555, 330), (690, 330), (690, 430), (560, 450)],
    ],
    "leg_shape_grow": 15,         # her trousers have a thick ink outline: pull all of it in with the legs
    "lunge": 0.7,
    "glow_point": (690, 150),     # raised front hand
    "glow_color": (255, 170, 80),
    "scale": 0.8,
    "head_box": (470, 35, 610, 175),
    "bust_box": (325, 30, 715, 485),
    "icon_bg": (52, 32, 20),
    "effects": effects,
}

if __name__ == "__main__" and "--sheets" in sys.argv:
    args = [a for a in sys.argv[1:] if a != "--sheets"]
    greensheet.recut(HERE, SHEETS, CAL, args[0] if args else os.path.join(HERE, "art"))
elif __name__ == "__main__":
    cutout.generate(CONFIG, sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "art"))

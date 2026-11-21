"""Generate Bibble Babble's sprite frames (see tools/fighters/cutout.py).

Usage (repo root):
    python3 -I tools/fighters/bibblebabble/make_frames.py [<out_art_dir>]

source.png is the first idle pose cut from idle_crouch.jpg (already transparent,
faces right); the cut-out pipeline poses it for every action the sheets don't cover.
Effects:
  6000  a rubber chicken, tumbling (6 frames)
  6001  feather puff where a chicken lands (4 frames)
  6002  a shopping bag, skidding (4 frames)
  6003  "SQUAWK!" shockwave ring (4 frames)
Hand-drawn sheets (green screen, cut out by tools/fighters/greensheet.py):
  7600  idle_crouch.jpg, 5 poses: 0-3 idle (action 0), 4 crouching (actions 10-12)
  7500  walk.jpg, 6 poses, all facing right (actions 20 and 21)
  7400  jump.jpg, 5 poses: crouch, rise, apex, fall, land (actions 40-47)
  7200  punch_kick.jpg, 6 poses: 0-2 light punch (action 200), 3-5 heavy kick (action 240)
  7300  guard_hit.jpg, 5 poses: stand guard (hugging the chicken), low guard, hit high,
        hit low, launched (bags flying: kept with the pose)

  python3 -I tools/fighters/bibblebabble/make_frames.py --sheets [<art_dir>]
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
# Sizes vs the idle sheet, by comparing matching stances side by side.
CLEAN = {"despill": 2}
SHEETS = {
    "idle_crouch.jpg": (7600, {k: "feet" for k in range(5)}, 1.0, (), CLEAN),
    "walk.jpg": (7500, {k: "feet" for k in range(6)}, 0.79, (), CLEAN),
    # one-legged kick poses keep the body in place, so he steps into the kick
    "punch_kick.jpg": (7200, {3: "body", 4: "body"}, 0.86, (), CLEAN),
    # the launched pose drops both bags: big pieces, so keep them with the pose
    "guard_hit.jpg": (7300, {4: "air_body"}, 0.82, (), dict(CLEAN, min_area=10000)),
    "jump.jpg": (7400, {0: "feet", 1: "air_body", 2: "air_body", 3: "air_body", 4: "feet"}, 0.68, (), CLEAN),
}
# Measured on idle_crouch.jpg's first pose (482 px tall; he stands ~400 in game), in its pixels.
CAL = {"scale": 400 / 482, "back_foot_to_axis": 143, "head_to_axis": -25, "body_to_axis": -10}

INK = (35, 25, 15, 255)
YELLOW = (236, 190, 60, 255)


def chicken(size=120, ss=4):
    """A rubber chicken: long yellow body, red comb, open orange beak, dangling legs (faces right)."""
    S = size * ss
    im = Image.new("RGBA", (S, S))
    d = ImageDraw.Draw(im)
    u = ss
    d.ellipse([18 * u, 48 * u, 82 * u, 76 * u], fill=YELLOW, outline=INK, width=2 * u)            # body
    d.polygon([(70 * u, 56 * u), (92 * u, 30 * u), (98 * u, 36 * u), (80 * u, 64 * u)], fill=YELLOW,
              outline=INK)                                                                            # neck
    d.ellipse([86 * u, 20 * u, 106 * u, 40 * u], fill=YELLOW, outline=INK, width=2 * u)            # head
    d.polygon([(90 * u, 22 * u), (94 * u, 12 * u), (98 * u, 20 * u), (102 * u, 12 * u), (104 * u, 24 * u)],
              fill=(210, 40, 40, 255), outline=INK)                                                   # comb
    d.polygon([(105 * u, 28 * u), (116 * u, 26 * u), (106 * u, 32 * u), (115 * u, 36 * u), (104 * u, 35 * u)],
              fill=(240, 130, 30, 255), outline=INK)                                                  # squawking beak
    d.ellipse([96 * u, 25 * u, 101 * u, 30 * u], fill=INK)                                           # eye
    for x in (36, 52):                                                                               # legs
        d.line([(x * u, 74 * u), (x * u - 4 * u, 96 * u)], fill=(240, 130, 30, 255), width=3 * u)
        d.line([(x * u - 4 * u, 96 * u), (x * u - 10 * u, 100 * u)], fill=(240, 130, 30, 255), width=3 * u)
    d.polygon([(18 * u, 60 * u), (6 * u, 52 * u), (10 * u, 66 * u)], fill=YELLOW, outline=INK)     # tail
    return im.resize((size, size), Image.LANCZOS)


def feather_puff(k, size=140):
    """Frame k of 4: yellow feathers and a white puff, drifting out and fading."""
    im = Image.new("RGBA", (size, size))
    d = ImageDraw.Draw(im)
    c = size / 2
    fade = 1.0 - 0.24 * k
    r = 14 + 8 * k
    d.ellipse([c - r, c - r, c + r, c + r], fill=(255, 255, 240, int(150 * fade)))
    rnd = random.Random(9)
    for _ in range(9):
        a = rnd.uniform(0, 2 * math.pi)
        dist = 12 + k * (11 + rnd.uniform(0, 8))
        x, y = c + math.cos(a) * dist, c + math.sin(a) * dist + k * 3
        t = a + k * 0.6
        dx, dy = math.cos(t) * 8, math.sin(t) * 8
        d.ellipse([x - abs(dx) - 3, y - abs(dy) - 3, x + abs(dx) + 3, y + abs(dy) + 3],
                  fill=(250, 215, 90, int(255 * fade)), outline=(150, 110, 30, int(255 * fade)))
    return im


def shopping_bag(k, size=110):
    """Frame k of 4: a stuffed plastic bag sliding along the floor, wobbling, with a dust trail."""
    im = Image.new("RGBA", (size, size))
    d = ImageDraw.Draw(im)
    wob = (-4, 0, 4, 0)[k]
    for i in range(3):  # dust behind it
        r = 8 + 3 * i
        x = 14 - 2 * i * k % 6
        d.ellipse([x - r + i * 6, size - 16 - r + i * 2, x + r + i * 6, size - 16 + r], fill=(190, 175, 150, 110 - 30 * i))
    body = [(34, size - 10), (96, size - 10), (100 + wob, 46), (86, 34), (44, 34), (30 + wob, 46)]
    d.polygon(body, fill=(225, 225, 215, 235), outline=INK)
    d.line([(46, 36), (54, 14), (64, 36)], fill=INK, width=3)       # handles
    d.line([(70, 36), (78, 14), (86, 36)], fill=INK, width=3)
    for x, y, col in ((52, 62, (120, 160, 90, 255)), (74, 74, (190, 80, 60, 255)), (60, 86, (200, 170, 90, 255))):
        d.ellipse([x - 9, y - 9, x + 9, y + 9], fill=col)           # groceries showing through
    return im


def squawk(k, size=320):
    """Frame k of 4: a jagged shockwave ring with "SQUAWK!" as bold strokes, expanding."""
    im = Image.new("RGBA", (size, size))
    d = ImageDraw.Draw(im)
    c = size / 2
    fade = 1.0 - 0.2 * k
    r = 70 + 22 * k
    pts = []
    for i in range(28):
        rr = r + (14 if i % 2 else -6)
        a = math.pi * 2 * i / 28
        pts.append((c + math.cos(a) * rr, c + math.sin(a) * rr))
    d.polygon(pts, outline=(255, 230, 90, int(255 * fade)))
    d.ellipse([c - r + 10, c - r + 10, c + r - 10, c + r - 10], outline=(255, 255, 255, int(200 * fade)), width=5)
    # "!!" marks flying out: no font dependency
    for a in (-0.5, 0.0, 0.5):
        x, y = c + math.cos(a) * (r + 20), c + math.sin(a) * (r + 20)
        d.line([(x, y - 16), (x, y + 2)], fill=(255, 80, 60, int(255 * fade)), width=6)
        d.ellipse([x - 3, y + 7, x + 3, y + 13], fill=(255, 80, 60, int(255 * fade)))
    return im


def effects(out_dir, axes):
    greensheet.cut_sheets(HERE, SHEETS, CAL, out_dir, axes)
    base = chicken()
    for k in range(6):
        base.rotate(-60 * k, resample=Image.BICUBIC).save(os.path.join(out_dir, "6000_%d.png" % k), optimize=True)
        axes.append("6000_%d 60 60" % k)
    for k in range(4):
        feather_puff(k).save(os.path.join(out_dir, "6001_%d.png" % k), optimize=True)
        axes.append("6001_%d 70 70" % k)
        shopping_bag(k).save(os.path.join(out_dir, "6002_%d.png" % k), optimize=True)
        axes.append("6002_%d 65 110" % k)  # anchored on the floor
        squawk(k).save(os.path.join(out_dir, "6003_%d.png" % k), optimize=True)
        axes.append("6003_%d 160 160" % k)


CONFIG = {
    "source": os.path.join(HERE, "source.png"),
    "background": "alpha",
    "mirror": False,
    "hip": (260, 345),
    "ground": 542,
    "feet_x": 256,
    "split_upper": 360,
    "split_lower": 340,
    "x_range": (60, 481),
    "top": 60,
    "torso_boxes": [(60, 290, 165, 440)],  # the shopping bag hangs below the belt
    "glow_point": (440, 230),     # the rubber chicken
    "glow_color": (255, 210, 70),
    "scale": 400 / 482,
    "head_box": (220, 60, 350, 190),
    "bust_box": (194, 54, 376, 266),
    "icon_bg": (30, 32, 52),
    "effects": effects,
}

if __name__ == "__main__" and "--sheets" in sys.argv:
    args = [a for a in sys.argv[1:] if a != "--sheets"]
    greensheet.recut(HERE, SHEETS, CAL, args[0] if args else os.path.join(HERE, "art"))
elif __name__ == "__main__":
    cutout.generate(CONFIG, sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "art"))

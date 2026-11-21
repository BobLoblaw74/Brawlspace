"""Generate CuddlePuss's sprite frames from source.png (see tools/fighters/cutout.py).

Usage (repo root):
    python3 -I tools/fighters/cuddlepuss/make_frames.py [<out_art_dir>]

The source faces left on white, so it is mirrored. Effects:
  6000  hairball, spinning, with stray hairs (6 frames)
  6001  puff of fur when it lands (4 frames)
Hand-drawn sheets (see SHEETS; animated in cuddlepuss_anims.air):
  7040  jump, from jump.png (8 frames; actions 40/41/42/43/47)
  7200  standing light punch, from punch.png (8 frames; action 200)
Green-screen sheets (GREEN_SHEETS, cut by tools/fighters/greensheet.py):
  7600  idle_crouch.jpg, 6 poses: 0-3 idle (action 0), 4 half-crouch (10, 12), 5 crouching (11)
  7500  walk.jpg, 6 poses, all facing right (actions 20 and 21)
  7250  punch_kick.jpg, 6 poses: 3-5 heavy kick (action 240); 0-2 are cut but unused
        (punch.png already drives the light punch)
  7300  guard_hit.jpg, 5 poses: stand guard, low guard, hit high, hit low, launched
  prep_sheets() resizes them to the working size first (the big ones are ~1050 px per
  pose, the punch/kick sheet ~170): <name>.png next to each .jpg.

  python3 -I tools/fighters/cuddlepuss/make_frames.py --sheets [<art_dir>]
re-slices only the sheets into an existing art/ (keeps everything else).
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

INK = (20, 20, 22, 255)


def hairball(k, size=110, r=26):
    """A matted ball of grey/black fur with stray hairs; rotates 60 degrees per frame."""
    ss = 3
    S, R, c = size * ss, r * ss, size * ss // 2
    im = Image.new("RGBA", (S, S))
    d = ImageDraw.Draw(im)
    rnd = random.Random(4242)
    # stray hairs poking out (drawn first, under the ball)
    for _ in range(28):
        a = rnd.uniform(0, 2 * math.pi)
        r0, r1 = R * rnd.uniform(0.7, 0.95), R * rnd.uniform(1.15, 1.55)
        bend = rnd.uniform(-0.35, 0.35)
        pts = [(c + math.cos(a) * r0, c + math.sin(a) * r0),
               (c + math.cos(a + bend * 0.5) * (r0 + r1) / 2, c + math.sin(a + bend * 0.5) * (r0 + r1) / 2),
               (c + math.cos(a + bend) * r1, c + math.sin(a + bend) * r1)]
        shade = rnd.choice([(60, 60, 64), (120, 120, 126), (200, 200, 205)])
        d.line(pts, fill=shade + (255,), width=2 * ss)
    d.ellipse([c - R, c - R, c + R, c + R], fill=INK)
    d.ellipse([c - R + 3 * ss, c - R + 3 * ss, c + R - 3 * ss, c + R - 3 * ss], fill=(52, 52, 56, 255))
    # matted texture: short curly strokes
    for _ in range(70):
        a = rnd.uniform(0, 2 * math.pi)
        rr = R * math.sqrt(rnd.uniform(0, 0.8))
        x, y = c + math.cos(a) * rr, c + math.sin(a) * rr
        ang = rnd.uniform(0, math.pi)
        L = rnd.uniform(4, 9) * ss
        shade = rnd.choice([(90, 90, 96), (150, 150, 156), (215, 215, 220), (30, 30, 34)])
        d.line([(x - math.cos(ang) * L / 2, y - math.sin(ang) * L / 2), (x + math.cos(ang) * L / 2, y + math.sin(ang) * L / 2)],
               fill=shade + (255,), width=max(1, int(1.5 * ss)))
    d.ellipse([c - R * 0.55, c - R * 0.6, c - R * 0.15, c - R * 0.3], fill=(170, 170, 176, 160))  # damp sheen
    im = im.rotate(-60 * k, resample=Image.BICUBIC)
    return im.resize((size, size), Image.LANCZOS)


def fur_puff(k, size=170):
    """Frame k of 4: tufts of fur burst outward and drift, fading."""
    im = Image.new("RGBA", (size, size))
    d = ImageDraw.Draw(im)
    c = size // 2
    fade = 1.0 - 0.23 * k
    rnd = random.Random(777)
    for i in range(14):
        a = rnd.uniform(0, 2 * math.pi)
        dist = (14 + rnd.uniform(0, 14)) + k * (14 + rnd.uniform(0, 10))
        x, y = c + math.cos(a) * dist, c + math.sin(a) * dist + k * 4  # drifts down a little
        for j in range(5):  # a tuft = a few short curved hairs
            ang = a + rnd.uniform(-0.8, 0.8)
            L = rnd.uniform(6, 13)
            shade = rnd.choice([(70, 70, 74), (160, 160, 166), (235, 235, 240)])
            d.line([(x, y), (x + math.cos(ang) * L, y + math.sin(ang) * L)], fill=shade + (int(255 * fade),), width=2)
    r = 12 + 5 * k
    d.ellipse([c - r, c - r, c + r, c + r], fill=(220, 220, 225, int(120 * fade)))
    return im


# Hand-drawn sheets: <file>: (sprite group, airborne cells, cells already facing right).
# Every sheet is a row of 640x640 cells drawn facing left on transparent, feet on the
# same ground line; the odd cell drawn facing right is left unmirrored.
SHEETS = {
    "jump.png": (7040, (3, 4, 5, 6), ()),
    "punch.png": (7200, (), (5,)),
}
SHEET_CELL = 640
SHEET_GROUND = 618        # feet line of the standing cells
SHEET_SCALE = 420 / 313   # sheet stance is 313 px tall; the game idle is 420


def sheet_frames(name, out_dir, axes):
    """Slice one sheet into <group>_<k>.png. Airborne cells are anchored at their own
    feet (physics sets the height); the rest on the shared ground line."""
    group, air, facing_right = SHEETS[name]
    sheet = Image.open(os.path.join(HERE, name)).convert("RGBA")
    for k in range(sheet.width // SHEET_CELL):
        cell = sheet.crop((k * SHEET_CELL, 0, (k + 1) * SHEET_CELL, SHEET_CELL))
        if k not in facing_right:
            cell = cell.transpose(Image.FLIP_LEFT_RIGHT)
        bb = cell.getchannel("A").point(lambda v: 255 if v > 40 else 0).getbbox()
        ground = bb[3] if k in air else SHEET_GROUND
        cell = cell.resize((round(SHEET_CELL * SHEET_SCALE),) * 2, Image.LANCZOS)
        bb = cell.getbbox()
        cell = cell.crop(bb)
        ax = round(SHEET_CELL / 2 * SHEET_SCALE) - bb[0]
        ay = round(ground * SHEET_SCALE) - bb[1]
        cutout.save_png(cell, os.path.join(out_dir, "%d_%d.png" % (group, k)))
        axes.append("%d_%d %d %d" % (group, k, ax, ay))


# Green-screen sheets: resized from the .jpg to these working sizes (poses ~500 px tall).
PREP = {"idle_crouch": 0.47, "walk": 0.47, "guard_hit": 0.47, "punch_kick": 3.0}
CLEAN = {"despill": 2}
GREEN_SHEETS = {
    "idle_crouch.png": (7600, {k: "feet" for k in range(6)}, 1.0, (), CLEAN),
    "walk.png": (7500, {k: "feet" for k in range(6)}, 1.03, (), CLEAN),
    "punch_kick.png": (7250, {3: "body", 4: "body"}, 1.04, (), CLEAN),
    "guard_hit.png": (7300, {4: "air_body"}, 1.0, (), CLEAN),
}
# Measured on idle_crouch.png's first pose (494 px tall; the game idle is ~420), in its pixels.
CAL = {"scale": 420 / 494, "back_foot_to_axis": 114, "head_to_axis": -15, "body_to_axis": -25}


def prep_sheets():
    for name, f in PREP.items():
        im = Image.open(os.path.join(HERE, name + ".jpg")).convert("RGB")
        im.resize((round(im.width * f), round(im.height * f)), Image.LANCZOS).save(os.path.join(HERE, name + ".png"))


def effects(out_dir, axes):
    for name in SHEETS:
        sheet_frames(name, out_dir, axes)
    prep_sheets()
    greensheet.cut_sheets(HERE, GREEN_SHEETS, CAL, out_dir, axes)
    for k in range(6):
        hairball(k).save(os.path.join(out_dir, "6000_%d.png" % k), optimize=True)
        axes.append("6000_%d 55 55" % k)
    for k in range(4):
        fur_puff(k).save(os.path.join(out_dir, "6001_%d.png" % k), optimize=True)
        axes.append("6001_%d 85 85" % k)


CONFIG = {
    "source": os.path.join(HERE, "source.png"),
    "mirror": True,               # drawn facing left; fighters face right
    "hip": (520, 345),            # waistband
    "ground": 560,
    "feet_x": 510,
    "split_upper": 345,
    "split_lower": 335,
    "x_range": (200, 820),
    "top": 20,
    "torso_boxes": [(370, 328, 420, 345)],  # underside of the tail dips just below the waistband
    "glow_point": (760, 165),     # forward paw: specials glow here
    "glow_color": (255, 205, 230),
    "scale": 0.78,
    "head_box": (475, 35, 625, 185),
    "bust_box": (445, 28, 655, 273),
    "icon_bg": (30, 30, 38),
    "effects": effects,
}

def sheets_only(out_dir):
    """Re-slice the hand-drawn sheets into an existing art dir, replacing their axis.txt lines."""
    axes = []
    for name in SHEETS:
        sheet_frames(name, out_dir, axes)
    groups = tuple("%d_" % g for g, _, _ in SHEETS.values())
    path = os.path.join(out_dir, "axis.txt")
    with open(path) as f:
        kept = [l for l in f.read().splitlines() if not l.startswith(groups)]
    with open(path, "w") as f:
        f.write("\n".join(kept + axes) + "\n")


if __name__ == "__main__" and "--sheets" in sys.argv:
    args = [a for a in sys.argv[1:] if a != "--sheets"]
    out = args[0] if args else os.path.join(HERE, "art")
    sheets_only(out)
    prep_sheets()
    greensheet.recut(HERE, GREEN_SHEETS, CAL, out)
elif __name__ == "__main__":
    cutout.generate(CONFIG, sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "art"))

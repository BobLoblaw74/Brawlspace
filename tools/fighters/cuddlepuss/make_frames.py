"""Generate CuddlePuss's sprite frames from source.png (see tools/fighters/cutout.py).

Usage (repo root):
    python3 -I tools/fighters/cuddlepuss/make_frames.py [<out_art_dir>]

The source faces left on white, so it is mirrored. Effects:
  6000  hairball, spinning, with stray hairs (6 frames)
  6001  puff of fur when it lands (4 frames)
Hand-drawn sheets:
  7040  jump, from jump.png (8 frames; actions 40/41/42/43/47 in cuddlepuss_anims.air)

  python3 -I tools/fighters/cuddlepuss/make_frames.py --jump [<art_dir>]
re-slices only jump.png into an existing art/ (keeps everything else).
"""
import math
import os
import random
import sys

from PIL import Image, ImageDraw, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
import cutout  # noqa: E402

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


JUMP_SHEET = os.path.join(HERE, "jump.png")
JUMP_CELL = 640          # 8 cells of 640x640, drawn facing left on transparent
JUMP_GROUND = 618        # feet line of the standing cells
JUMP_SCALE = 420 / 313   # sheet stance is 313 px tall; the game idle is 420
JUMP_AIR = (3, 4, 5, 6)  # airborne cells: anchored at their own feet (physics sets the height)


def jump_frames(out_dir, axes):
    sheet = Image.open(JUMP_SHEET).convert("RGBA")
    n = sheet.width // JUMP_CELL
    for k in range(n):
        cell = sheet.crop((k * JUMP_CELL, 0, (k + 1) * JUMP_CELL, JUMP_CELL)).transpose(Image.FLIP_LEFT_RIGHT)
        alpha = cell.getchannel("A").point(lambda v: 255 if v > 40 else 0)
        bb = alpha.getbbox()
        ground = bb[3] if k in JUMP_AIR else JUMP_GROUND
        cell = cell.resize((round(JUMP_CELL * JUMP_SCALE),) * 2, Image.LANCZOS)
        bb = cell.getbbox()
        cell = cell.crop(bb)
        ax = round(JUMP_CELL / 2 * JUMP_SCALE) - bb[0]
        ay = round(ground * JUMP_SCALE) - bb[1]
        cutout.save_png(cell, os.path.join(out_dir, "7040_%d.png" % k))
        axes.append("7040_%d %d %d" % (k, ax, ay))


def effects(out_dir, axes):
    jump_frames(out_dir, axes)
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
    "bust_box": (300, 10, 780, 570),
    "icon_bg": (30, 30, 38),
    "effects": effects,
}

def jump_only(out_dir):
    """Re-slice jump.png into an existing art dir, replacing its 7040 lines in axis.txt."""
    axes = []
    jump_frames(out_dir, axes)
    path = os.path.join(out_dir, "axis.txt")
    with open(path) as f:
        kept = [l for l in f.read().splitlines() if not l.startswith("7040_")]
    with open(path, "w") as f:
        f.write("\n".join(kept + axes) + "\n")


if __name__ == "__main__" and "--jump" in sys.argv:
    args = [a for a in sys.argv[1:] if a != "--jump"]
    jump_only(args[0] if args else os.path.join(HERE, "art"))
elif __name__ == "__main__":
    cutout.generate(CONFIG, sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "art"))

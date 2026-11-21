"""Generate Juanana's sprite frames from source.png (see tools/fighters/cutout.py).

Usage (repo root):
    python3 -I tools/fighters/juanana/make_frames.py [<out_art_dir>]

The source is pixel art on a painted checkerboard, facing left: it is cut out
with the checker remover, mirrored, and prescaled. Effects:
  6000  glow stick, spinning, with lightning crackle (8 frames)
  6001  electric zap burst (4 frames)
  6002  banana peel lying on the floor
"""
import math
import os
import random
import sys

from PIL import Image, ImageDraw, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
import cutout  # noqa: E402

INK = (24, 20, 16, 255)


def lightning(d, rnd, x0, y0, x1, y1, col, width=2, jag=7, steps=6):
    pts = [(x0, y0)]
    for i in range(1, steps):
        t = i / float(steps)
        pts.append((x0 + (x1 - x0) * t + rnd.uniform(-jag, jag), y0 + (y1 - y0) * t + rnd.uniform(-jag, jag)))
    pts.append((x1, y1))
    d.line(pts, fill=col, width=width)


def pill(d, box, fill, outline=None, width=0):
    """Rounded bar (Pillow 5 lacks a rounded-rectangle primitive): rectangle + end caps."""
    x0, y0, x1, y1 = box
    if outline and width:
        pill(d, box, outline)
        x0, y0, x1, y1 = x0 + width, y0 + width, x1 - width, y1 - width
    r = (y1 - y0) / 2.0
    d.rectangle([x0 + r, y0, x1 - r, y1], fill=fill)
    d.ellipse([x0, y0, x0 + 2 * r, y1], fill=fill)
    d.ellipse([x1 - 2 * r, y0, x1, y1], fill=fill)


def glow_stick(k, size=150):
    """Frame k of 8: the stick spins 45 degrees per frame, crackle is re-rolled each frame."""
    im = Image.new("RGBA", (size, size))
    glow = Image.new("RGBA", (size, size))
    c = size // 2
    L, T = 50, 9  # half length, half thickness
    gd = ImageDraw.Draw(glow)
    pill(gd, [c - L - 8, c - T - 8, c + L + 8, c + T + 8], (70, 150, 255, 150))
    glow = glow.filter(ImageFilter.GaussianBlur(7))
    d = ImageDraw.Draw(im)
    pill(d, [c - L, c - T, c + L, c + T], (110, 190, 255, 255), outline=(40, 90, 200, 255), width=2)
    pill(d, [c - L + 4, c - T + 4, c + L - 4, c + T - 4], (215, 240, 255, 255))
    d.line([(c - L + 8, c - 1), (c + L - 8, c - 1)], fill=(255, 255, 255, 255), width=3)
    rnd = random.Random(k * 7919)
    for _ in range(3):
        side = rnd.choice((-1, 1))
        xa = rnd.uniform(-L, L)
        lightning(d, rnd, c + xa, c + side * (T + 2), c + xa + rnd.uniform(-22, 22), c + side * (T + rnd.uniform(14, 26)),
                  (150, 200, 255, 255), width=2, jag=5, steps=4)
    out = Image.alpha_composite(glow, im)
    return out.rotate(-45 * k, resample=Image.BICUBIC)


def zap(k, size=170):
    """Frame k of 4: electric burst with bolts flying outward, fading."""
    im = Image.new("RGBA", (size, size))
    d = ImageDraw.Draw(im)
    c = size // 2
    fade = 1.0 - 0.24 * k
    r = 22 + 10 * k
    d.ellipse([c - r, c - r, c + r, c + r], fill=(160, 210, 255, int(150 * fade)))
    d.ellipse([c - r // 2, c - r // 2, c + r // 2, c + r // 2], fill=(255, 255, 255, int(230 * fade)))
    rnd = random.Random(31 + k)
    for i in range(7):
        a = math.radians(i * (360 / 7.0) + rnd.uniform(-12, 12))
        r0, r1 = r * 0.6, r + 24 + 10 * k
        lightning(d, rnd, c + math.cos(a) * r0, c + math.sin(a) * r0, c + math.cos(a) * r1, c + math.sin(a) * r1,
                  (130, 190, 255, int(255 * fade)), width=3, jag=6, steps=4)
    return Image.alpha_composite(im.filter(ImageFilter.GaussianBlur(4)), im)


def banana_peel(scale=2):
    """A splayed banana peel lying on the floor, drawn chunky to match the pixel art."""
    w, h = 64, 30
    im = Image.new("RGBA", (w, h))
    d = ImageDraw.Draw(im)
    yellow, shade, tip = (250, 214, 40, 255), (214, 160, 20, 255), (110, 70, 30, 255)
    # three lobes fanning out from the stem
    d.polygon([(30, 18), (4, 24), (2, 28), (16, 29), (32, 23)], fill=shade, outline=INK)
    d.polygon([(34, 18), (60, 22), (62, 27), (48, 29), (32, 23)], fill=yellow, outline=INK)
    d.polygon([(28, 20), (24, 6), (30, 2), (36, 6), (36, 20)], fill=yellow, outline=INK)
    d.polygon([(26, 19), (38, 19), (40, 27), (24, 27)], fill=(255, 236, 120, 255), outline=INK)
    d.rectangle([29, 0, 33, 3], fill=tip)
    d.rectangle([1, 26, 4, 28], fill=tip)
    d.rectangle([59, 24, 62, 26], fill=tip)
    return im.resize((w * scale, h * scale), Image.NEAREST)


def effects(out_dir, axes):
    for k in range(8):
        glow_stick(k).save(os.path.join(out_dir, "6000_%d.png" % k), optimize=True)
        axes.append("6000_%d 75 75" % k)
    for k in range(4):
        zap(k).save(os.path.join(out_dir, "6001_%d.png" % k), optimize=True)
        axes.append("6001_%d 85 85" % k)
    peel = banana_peel()
    peel.save(os.path.join(out_dir, "6002_0.png"), optimize=True)
    axes.append("6002_0 %d %d" % (peel.width // 2, peel.height - 2))


CONFIG = {
    "source": os.path.join(HERE, "source.png"),
    "background": "checker",      # fake transparency painted into the pixels
    "mirror": True,               # drawn facing left; fighters face right
    "prescale": 0.6,              # 768x1024 source -> same working size as the others
    "hip": (245, 405),
    "ground": 595,
    "feet_x": 200,
    "split_upper": 405,
    "split_lower": 395,
    "x_range": (10, 430),
    "top": 50,
    # The cape hangs behind the back leg and a glow stick crosses the thigh, so a
    # horizontal split can't separate them: trace the legs exactly instead.
    # Cape tip (55-110) and the suit's banana tip (255-295) stay with the torso.
    "leg_shapes": [
        [(158, 396), (238, 396), (242, 425), (215, 448), (185, 462), (165, 482), (150, 505), (120, 530),
         (95, 540), (90, 600), (15, 600), (22, 560), (45, 530), (62, 505), (80, 475), (105, 445), (118, 425),
         (140, 408)],                                                     # back leg
        [(292, 396), (352, 388), (370, 385), (385, 400), (383, 440), (368, 455), (358, 480), (392, 505),
         (388, 535), (300, 538), (298, 505), (318, 480), (318, 455), (300, 440), (292, 425)],  # front leg
    ],
    "lunge": 0.7,
    "glow_point": (345, 318),     # front hand gripping a glow stick
    "glow_color": (100, 170, 255),
    "scale": 0.77,
    "head_box": (225, 130, 355, 260),
    "bust_box": (199, 124, 381, 336),
    "icon_bg": (44, 38, 12),
    "effects": effects,
}

if __name__ == "__main__":
    cutout.generate(CONFIG, sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "art"))

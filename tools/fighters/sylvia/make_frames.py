"""Generate Sylvia's sprite frames (see tools/fighters/cutout.py).

Usage (repo root):
    python3 -I tools/fighters/sylvia/make_frames.py [<out_art_dir>]

sheet.jpg is one green-screen drawing with five rows of poses separated by drawn
lines. split_sheet() cuts it into the five sheets the other fighters use
(enlarged 3.5x: the poses are drawn ~145 px tall), and source.png is the first
idle pose, which the cut-out pipeline poses for every action the sheets don't
cover. She wears green, so the key only removes the saturated screen green.
Effects:
  6000  a tarot card, spinning (6 frames)
  6001  card burst: gold sparkles where a card lands (4 frames)
  6002  The Tower: a giant card that falls on the opponent
  6010-6012  Wheel of Fortune draws: The Star, The Sun, The Fool
Sheets (cut by tools/fighters/greensheet.py):
  7600  idle_crouch.png, 6 poses: 0-3 idle, 4 half-crouch, 5 crouching
  7500  walk.png, 6 poses, all facing right
  7400  jump.png, 5 poses: crouch, rise, apex, fall, land
  7200  punch_kick.png, 6 poses: 0-2 card throw / light punch, 3-5 heavy kick
  7300  guard_hit.png, 5 poses: stand guard, low guard, hit high, hit low, launched

  python3 -I tools/fighters/sylvia/make_frames.py --sheets [<art_dir>]
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

ROWS = [("idle_crouch", 0, 153), ("walk", 157, 311), ("jump", 315, 466),
        ("punch_kick", 470, 618), ("guard_hit", 622, 768)]  # between the drawn divider lines
ENLARGE = 3.5


def split_sheet():
    im = Image.open(os.path.join(HERE, "sheet.jpg")).convert("RGB")
    for name, y0, y1 in ROWS:
        row = im.crop((0, y0, im.width, y1))
        row.resize((round(row.width * ENLARGE), round(row.height * ENLARGE)), Image.LANCZOS) \
            .save(os.path.join(HERE, name + ".png"))


# Her top and skirt are green: key only the screen (greenness ~240; her clothes stay
# under ~90), then scrub the rim the enlarged JPEG edge leaves.
CLEAN = {"key": (100, 170), "despill": 5}
SHEETS = {
    "idle_crouch.png": (7600, {k: "feet" for k in range(6)}, 1.0, (), CLEAN),
    "walk.png": (7500, {k: "feet" for k in range(6)}, 1.0, (), CLEAN),
    "punch_kick.png": (7200, {3: "body", 4: "body"}, 1.0, (), CLEAN),
    "guard_hit.png": (7300, {4: "air_body"}, 1.0, (), CLEAN),
    "jump.png": (7400, {0: "feet", 1: "air_body", 2: "air_body", 3: "air_body", 4: "feet"}, 1.0, (), CLEAN),
}
# Measured on idle_crouch.png's first pose (505 px tall; she stands ~390 in game), in its pixels.
CAL = {"scale": 390 / 505, "back_foot_to_axis": 184, "head_to_axis": 0, "body_to_axis": 4}

INK = (30, 20, 40, 255)
CREAM = (246, 234, 205, 255)
PURPLE = (88, 40, 120, 255)
GOLD = (230, 185, 70, 255)


def card(w, h, ss=4):
    """A blank tarot card (cream face, gold border) at ss x supersampling."""
    im = Image.new("RGBA", (w * ss, h * ss))
    d = ImageDraw.Draw(im)
    d.rectangle([0, 0, w * ss - 1, h * ss - 1], fill=INK)
    d.rectangle([ss, ss, w * ss - 1 - ss, h * ss - 1 - ss], fill=CREAM)
    d.rectangle([4 * ss, 4 * ss, w * ss - 1 - 4 * ss, h * ss - 1 - 4 * ss], outline=GOLD, width=ss)
    return im, d


def star(d, cx, cy, r, fill, points=5):
    pts = []
    for i in range(points * 2):
        rr = r if i % 2 == 0 else r * 0.45
        a = -math.pi / 2 + math.pi * i / points
        pts.append((cx + math.cos(a) * rr, cy + math.sin(a) * rr))
    d.polygon(pts, fill=fill, outline=INK)


def card_back(w=44, h=70):
    """The card back she throws: purple, with a gold star."""
    ss = 4
    im, d = card(w, h, ss)
    d.rectangle([4 * ss, 4 * ss, (w - 4) * ss, (h - 4) * ss], fill=PURPLE, outline=GOLD, width=ss)
    star(d, w * ss / 2, h * ss / 2, 13 * ss, GOLD)
    return im.resize((w, h), Image.LANCZOS)


def spinning_card(k, size=90):
    """Frame k of 6: the card tumbling edge-over (its width follows cos)."""
    c = card_back()
    sx = max(0.12, abs(math.cos(math.pi * k / 6)))
    c = c.resize((max(4, round(c.width * sx)), c.height), Image.LANCZOS).rotate(-30 * k, expand=True,
                                                                               resample=Image.BICUBIC)
    im = Image.new("RGBA", (size, size))
    glow = Image.new("RGBA", (size, size))
    ImageDraw.Draw(glow).ellipse([18, 18, size - 18, size - 18], fill=(200, 120, 255, 90))
    im.alpha_composite(glow.filter(ImageFilter.GaussianBlur(8)))
    im.alpha_composite(c, ((size - c.width) // 2, (size - c.height) // 2))
    return im


def card_burst(k, size=140):
    """Frame k of 4: gold and violet sparkles flying out, fading."""
    im = Image.new("RGBA", (size, size))
    d = ImageDraw.Draw(im)
    c = size / 2
    fade = 1.0 - 0.24 * k
    rnd = random.Random(5)
    for i in range(12):
        a = rnd.uniform(0, 2 * math.pi)
        dist = 10 + k * (12 + rnd.uniform(0, 8))
        col = GOLD if i % 2 else (200, 140, 255, 255)
        star(d, c + math.cos(a) * dist, c + math.sin(a) * dist, max(3, 9 - 2 * k), col[:3] + (int(255 * fade),), 4)
    return im


def face_card(title, art, w=120, h=200):
    """A face-up major arcana card: art(draw, ss, w, h) fills the picture; a title bar below."""
    ss = 4
    im, d = card(w, h, ss)
    art(d, ss, w, h)
    d.rectangle([10 * ss, (h - 34) * ss, (w - 10) * ss, (h - 14) * ss], fill=CREAM, outline=INK, width=ss)
    # the title is lettered as simple bars (no font dependency): one tick per letter
    n = len(title)
    for i in range(n):
        x = (w / 2 - n * 3 + i * 6) * ss
        d.rectangle([x, (h - 28) * ss, x + 3 * ss, (h - 20) * ss], fill=INK)
    return im.resize((w, h), Image.LANCZOS)


def tower_art(d, ss, w, h):
    d.rectangle([10 * ss, 10 * ss, (w - 10) * ss, (h - 40) * ss], fill=(40, 30, 70, 255))
    d.rectangle([(w / 2 - 18) * ss, 60 * ss, (w / 2 + 18) * ss, (h - 40) * ss], fill=(150, 140, 130, 255), outline=INK,
                width=ss)
    for y in (80, 110, 140):  # windows
        d.rectangle([(w / 2 - 5) * ss, y * ss, (w / 2 + 5) * ss, (y + 10) * ss], fill=(255, 190, 60, 255))
    d.polygon([((w / 2 - 24) * ss, 60 * ss), ((w / 2 + 24) * ss, 60 * ss), ((w / 2) * ss, 34 * ss)], fill=GOLD,
              outline=INK)  # crown, knocked loose
    d.line([(20 * ss, 12 * ss), (45 * ss, 35 * ss), (35 * ss, 40 * ss), (w / 2 * ss, 52 * ss)], fill=(255, 250, 150, 255),
           width=4 * ss)  # lightning


def star_art(d, ss, w, h):
    d.rectangle([10 * ss, 10 * ss, (w - 10) * ss, (h - 40) * ss], fill=(30, 40, 100, 255))
    star(d, w / 2 * ss, 60 * ss, 30 * ss, GOLD, 8)
    for x, y in ((26, 30), (94, 34), (30, 110), (92, 120), (60, 140)):
        star(d, x * ss, y * ss, 7 * ss, (255, 255, 255, 255))


def sun_art(d, ss, w, h):
    d.rectangle([10 * ss, 10 * ss, (w - 10) * ss, (h - 40) * ss], fill=(255, 210, 120, 255))
    cx, cy = w / 2 * ss, 80 * ss
    for i in range(16):
        a = math.pi * i / 8
        d.line([(cx, cy), (cx + math.cos(a) * 48 * ss, cy + math.sin(a) * 48 * ss)], fill=(240, 140, 40, 255), width=3 * ss)
    d.ellipse([cx - 28 * ss, cy - 28 * ss, cx + 28 * ss, cy + 28 * ss], fill=(255, 200, 40, 255), outline=INK, width=ss)


def fool_art(d, ss, w, h):
    d.rectangle([10 * ss, 10 * ss, (w - 10) * ss, (h - 40) * ss], fill=(170, 220, 240, 255))
    d.polygon([(10 * ss, (h - 40) * ss), (70 * ss, 120 * ss), ((w - 10) * ss, (h - 40) * ss)], fill=(120, 100, 80, 255))
    d.ellipse([46 * ss, 50 * ss, 74 * ss, 78 * ss], fill=(240, 200, 170, 255), outline=INK, width=ss)  # head
    d.polygon([(44 * ss, 54 * ss), (60 * ss, 30 * ss), (76 * ss, 54 * ss)], fill=(200, 40, 60, 255), outline=INK)  # cap
    d.rectangle([50 * ss, 78 * ss, 70 * ss, 118 * ss], fill=(220, 180, 40, 255), outline=INK, width=ss)  # body
    d.line([(70 * ss, 90 * ss), (96 * ss, 70 * ss)], fill=INK, width=2 * ss)  # waving at nothing


def effects(out_dir, axes):
    greensheet.cut_sheets(HERE, SHEETS, CAL, out_dir, axes)
    for k in range(6):
        spinning_card(k).save(os.path.join(out_dir, "6000_%d.png" % k), optimize=True)
        axes.append("6000_%d 45 45" % k)
    for k in range(4):
        card_burst(k).save(os.path.join(out_dir, "6001_%d.png" % k), optimize=True)
        axes.append("6001_%d 70 70" % k)
    face_card("THE TOWER", tower_art, 140, 230).save(os.path.join(out_dir, "6002_0.png"), optimize=True)
    axes.append("6002_0 70 230")  # anchored at its bottom edge: it lands on the floor
    for i, (title, art) in enumerate((("THE STAR", star_art), ("THE SUN", sun_art), ("THE FOOL", fool_art))):
        face_card(title, art).save(os.path.join(out_dir, "601%d_0.png" % i), optimize=True)
        axes.append("601%d_0 60 100" % i)


CONFIG = {
    "source": os.path.join(HERE, "source.png"),
    "background": "alpha",
    "mirror": False,
    "hip": (250, 340),
    "ground": 565,
    "feet_x": 244,
    "split_upper": 345,
    "split_lower": 330,
    "x_range": (60, 466),
    "top": 60,
    "glow_point": (420, 180),     # the hand holding the cards
    "glow_color": (190, 120, 255),
    "scale": 390 / 505,
    "head_box": (170, 62, 310, 202),
    "bust_box": (142, 55, 338, 284),
    "icon_bg": (36, 22, 48),
    "effects": effects,
}

if __name__ == "__main__":
    split_sheet()
    if "--sheets" in sys.argv:
        args = [a for a in sys.argv[1:] if a != "--sheets"]
        greensheet.recut(HERE, SHEETS, CAL, args[0] if args else os.path.join(HERE, "art"))
    else:
        cutout.generate(CONFIG, sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "art"))

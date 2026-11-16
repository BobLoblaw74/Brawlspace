"""Generate HotNight's sprite frames from source.png (see tools/fighters/cutout.py).

Usage (repo root):
    python3 -I tools/fighters/hotnight/make_frames.py [<out_art_dir>]

The source already faces right, on white. Her long dress and the grocery bag
hang over her legs, so the legs are traced exactly (leg_shapes). Effects:
  6000  plastic water bottle, tumbling end over end (8 frames)
  6001  water splash (4 frames)
  6002  sparkle of water droplets for Hydrate (4 frames)
"""
import math
import os
import random
import sys

from PIL import Image, ImageDraw, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
import cutout  # noqa: E402

INK = (30, 40, 60, 255)


def bottle(k, size=130):
    """Clear plastic bottle with a blue cap and label, rotating 45 degrees per frame."""
    ss = 3
    S, c = size * ss, size * ss // 2
    im = Image.new("RGBA", (S, S))
    d = ImageDraw.Draw(im)
    L, W = 40 * ss, 13 * ss  # half length, half width of the body
    # body (lying horizontally, cap on the right)
    d.rectangle([c - L, c - W, c + L - 14 * ss, c + W], fill=INK)
    d.ellipse([c - L - 6 * ss, c - W, c - L + 6 * ss, c + W], fill=INK)
    d.polygon([(c + L - 14 * ss, c - W), (c + L - 2 * ss, c - 6 * ss), (c + L - 2 * ss, c + 6 * ss),
               (c + L - 14 * ss, c + W)], fill=INK)
    inner = (170, 215, 240, 235)
    d.rectangle([c - L + 2 * ss, c - W + 2 * ss, c + L - 15 * ss, c + W - 2 * ss], fill=inner)
    d.ellipse([c - L - 4 * ss, c - W + 2 * ss, c - L + 6 * ss, c + W - 2 * ss], fill=inner)
    d.polygon([(c + L - 15 * ss, c - W + 2 * ss), (c + L - 4 * ss, c - 4 * ss), (c + L - 4 * ss, c + 4 * ss),
               (c + L - 15 * ss, c + W - 2 * ss)], fill=inner)
    # water inside (lower two thirds) with a bright line
    d.rectangle([c - L + 3 * ss, c - 3 * ss, c + L - 16 * ss, c + W - 3 * ss], fill=(80, 160, 225, 230))
    d.line([(c - L + 4 * ss, c - 3 * ss), (c + L - 17 * ss, c - 3 * ss)], fill=(225, 245, 255, 255), width=ss * 2)
    # ribs and label
    for x in (c - 22 * ss, c - 14 * ss):
        d.line([(x, c - W + 2 * ss), (x, c + W - 2 * ss)], fill=(120, 170, 210, 255), width=ss)
    d.rectangle([c - 6 * ss, c - W + 1 * ss, c + 14 * ss, c + W - 1 * ss], fill=(240, 245, 250, 255), outline=INK)
    d.rectangle([c - 3 * ss, c - 4 * ss, c + 11 * ss, c + 4 * ss], fill=(40, 120, 200, 255))
    # cap
    d.rectangle([c + L - 3 * ss, c - 6 * ss, c + L + 5 * ss, c + 6 * ss], fill=(30, 90, 190, 255), outline=INK, width=ss)
    # highlight
    d.line([(c - L + 2 * ss, c - W + 5 * ss), (c + L - 18 * ss, c - W + 5 * ss)], fill=(255, 255, 255, 200), width=2 * ss)
    im = im.rotate(-45 * k, resample=Image.BICUBIC)
    return im.resize((size, size), Image.LANCZOS)


def splash(k, size=180):
    """Frame k of 4: burst of water drops and a spray ring, fading."""
    im = Image.new("RGBA", (size, size))
    d = ImageDraw.Draw(im)
    c = size // 2
    fade = 1.0 - 0.23 * k
    r = 18 + 10 * k
    d.ellipse([c - r, c - r, c + r, c + r], outline=(160, 215, 255, int(220 * fade)), width=4)
    rnd = random.Random(99)
    for i in range(16):
        a = rnd.uniform(0, 2 * math.pi)
        dist = 16 + k * (14 + rnd.uniform(0, 10)) + rnd.uniform(0, 10)
        x, y = c + math.cos(a) * dist, c + math.sin(a) * dist + k * k * 1.5  # drops fall a little
        rr = max(2, 7 - k - (i % 3))
        d.ellipse([x - rr, y - rr * 1.3, x + rr, y + rr], fill=(70, 150, 225, int(255 * fade)))
        d.ellipse([x - rr * 0.4, y - rr * 0.9, x, y - rr * 0.3], fill=(230, 245, 255, int(255 * fade)))
    return im


def sparkle(k, size=160):
    """Frame k of 4: rising droplets and glints around her while she drinks."""
    im = Image.new("RGBA", (size, size))
    d = ImageDraw.Draw(im)
    c = size // 2
    rnd = random.Random(5)
    for i in range(10):
        x = c + rnd.uniform(-60, 60)
        y = c + 50 - ((rnd.uniform(0, 100) + k * 22) % 110)
        rr = rnd.uniform(3, 6)
        d.ellipse([x - rr, y - rr * 1.3, x + rr, y + rr], fill=(110, 190, 255, 210))
        if i % 3 == 0:
            d.line([(x - 8, y), (x + 8, y)], fill=(255, 255, 255, 230), width=2)
            d.line([(x, y - 8), (x, y + 8)], fill=(255, 255, 255, 230), width=2)
    return im


def effects(out_dir, axes):
    for k in range(8):
        bottle(k).save(os.path.join(out_dir, "6000_%d.png" % k), optimize=True)
        axes.append("6000_%d 65 65" % k)
    for k in range(4):
        splash(k).save(os.path.join(out_dir, "6001_%d.png" % k), optimize=True)
        axes.append("6001_%d 90 90" % k)
    for k in range(4):
        sparkle(k).save(os.path.join(out_dir, "6002_%d.png" % k), optimize=True)
        axes.append("6002_%d 80 80" % k)


CONFIG = {
    "source": os.path.join(HERE, "source.png"),
    "mirror": False,              # already faces right
    "holes": [(592, 236)],        # gap between her bag arm and body
    "hip": (520, 330),
    "ground": 562,
    "feet_x": 525,
    "split_upper": 330,
    "split_lower": 320,
    "x_range": (340, 730),
    "top": 20,
    # dress and bag hang over the legs: trace the visible trousers + boots exactly
    "leg_shapes": [
        [(392, 318), (440, 315), (452, 400), (450, 470), (460, 500), (455, 540), (400, 548),
         (350, 548), (352, 520), (380, 495), (378, 440), (376, 380)],              # back leg
        [(585, 462), (690, 458), (698, 505), (712, 548), (705, 566), (640, 568),
         (628, 525), (600, 495)],                                                   # front leg
    ],
    "lunge": 0.7,
    "glow_point": (470, 120),     # the bottle she's holding up
    "glow_color": (90, 170, 255),
    "scale": 0.78,
    "head_box": (465, 25, 595, 155),
    "bust_box": (335, 20, 715, 463),
    "icon_bg": (40, 20, 30),
    "effects": effects,
}

if __name__ == "__main__":
    cutout.generate(CONFIG, sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "art"))

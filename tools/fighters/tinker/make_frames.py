"""Generate Tinker's sprite frames from source.png (see tools/fighters/cutout.py).

Usage (repo root):
    python3 -I tools/fighters/tinker/make_frames.py [<out_art_dir>]
"""
import os
import sys

from PIL import Image, ImageDraw, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
import cutout  # noqa: E402


def radar_pulse(out_dir, axes):
    """Group 6000: expanding green radar rings (projectile), 6 frames."""
    for k in range(6):
        size = 260
        im = Image.new("RGBA", (size, size))
        d = ImageDraw.Draw(im)
        c = size // 2
        for j in range(3):
            r = 34 + j * 26 + k * 6
            a = int(255 * (1 - j * 0.25))
            d.arc([c - r, c - r, c + r, c + r], -55, 55, fill=(80, 255, 140, a), width=9 - j * 2)
        d.ellipse([c - 16, c - 16, c + 16, c + 16], fill=(170, 255, 200, 230))
        glow = im.filter(ImageFilter.GaussianBlur(8))
        im = Image.alpha_composite(glow, im)
        im.save(os.path.join(out_dir, "6000_%d.png" % k), optimize=True)
        axes.append("6000_%d %d %d" % (k, c, c))


CONFIG = {
    "source": os.path.join(HERE, "source.png"),
    "mirror": False,
    "hip": (530, 330),            # belt buckle
    "ground": 562,
    "feet_x": 520,
    "split_upper": 345,
    "split_lower": 330,
    "x_range": (250, 800),
    "top": 30,
    "torso_boxes": [(680, 280, 800, 372)],  # forward fist hangs below the belt
    "glow_point": (705, 228),     # radar gauntlet
    "glow_color": (90, 255, 140),
    "scale": 0.82,
    "head_box": (470, 40, 610, 180),
    "bust_box": (330, 40, 770, 553),
    "icon_bg": (28, 40, 34),
    "effects": radar_pulse,
}

if __name__ == "__main__":
    cutout.generate(CONFIG, sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "art"))

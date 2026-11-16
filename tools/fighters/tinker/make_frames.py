"""Generate Tinker's sprite frames from a single illustration (cut-out animation).

Usage (repo root):
    python3 -I tools/fighters/tinker/make_frames.py <out_art_dir>

Takes tools/fighters/tinker/source.png (character on a white background),
cuts the figure out, splits it at the belt into an upper and a lower half, and
poses those halves (lean, lunge, squash, rotate) to produce one frame for every
sprite number the Kung Fu Man 720 template uses, so the template's animations,
timings and hitboxes drive the new art. Also renders the radar-pulse projectile
(group 6000) and both portraits (9000,0 / 9000,1). Output is a folder of
<group>_<item>.png + axis.txt for tools/png_to_sff.py.

Replace any generated PNG with a hand-drawn frame of the same name to upgrade
the animation piece by piece.
"""
import math
import os
import sys

from PIL import Image, ImageChops, ImageDraw, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "source.png")

# --- source-image landmarks (pixels in source.png) ---
HIP = (530, 330)          # belt buckle: pivot between halves
GROUND = 562              # soles of the boots
FEET_X = 520              # horizontal anchor (between the feet)
SPLIT_UPPER = 345         # upper half keeps rows < this (belt included)
SPLIT_LOWER = 330         # lower half keeps rows >= this
GAUNTLET = (705, 228)     # radar dish / gauntlet centre (glow effects)
SCALE = 0.82              # source -> game pixels (fighter ~420 px tall, like KFM 720)

# canvas (in source pixels) every frame is composed on
CW, CH = 1200, 760
OX, OY = 340, 120         # where the source image's (0,0) sits on the canvas

# sprite numbers to generate: read from the KFM 720 template so that every
# sprite its animations reference exists (item numbers are not contiguous,
# e.g. 5000 has 0,10,11,20,...). Effects/portraits (9000) are made separately.
TEMPLATE_SFF = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(HERE))),
                            "content", "chars", "kfm720", "kfm720.sff")


def template_groups():
    import struct
    d = open(TEMPLATE_SFF, "rb").read()
    so, n = struct.unpack_from("<II", d, 36)
    groups = {}
    for i in range(n):
        g, it = struct.unpack_from("<HH", d, so + i * 28)
        if g != 9000:
            groups.setdefault(g, []).append(it)
    return {g: sorted(items) for g, items in groups.items()}


# ---------------------------------------------------------------- cut-out
def cut_out(img):
    """Make the white background transparent (border-connected + large enclosed areas)."""
    rgb = img.convert("RGB")
    w, h = rgb.size
    work = rgb.copy()
    key = (255, 0, 255)

    def is_white(p):
        return p[0] > 232 and p[1] > 232 and p[2] > 232

    px = work.load()
    seeds = [(x, 0) for x in range(0, w, 8)] + [(x, h - 1) for x in range(0, w, 8)] + \
            [(0, y) for y in range(0, h, 8)] + [(w - 1, y) for y in range(0, h, 8)]
    for s in seeds:
        if is_white(px[s]):
            ImageDraw.floodfill(work, s, key, thresh=40)
    # enclosed white gaps (e.g. between arm and body) larger than ~600 px
    for y in range(0, h, 5):
        for x in range(0, w, 5):
            if is_white(px[x, y]):
                trial = work.copy()
                ImageDraw.floodfill(trial, (x, y), key, thresh=40)
                diff = ImageChops.difference(trial, work).convert("L").point(lambda v: 255 if v else 0)
                area = diff.histogram()[255]
                if area > 600:
                    work = trial
                else:  # small highlight inside the drawing: mark it so it is not re-tested
                    ImageDraw.floodfill(work, (x, y), (200, 200, 201), thresh=40)
                px = work.load()
    mask = Image.new("L", (w, h), 255)
    mpx, wpx = mask.load(), work.load()
    for y in range(h):
        for x in range(w):
            if wpx[x, y] == key:
                mpx[x, y] = 0
    mask = mask.filter(ImageFilter.MinFilter(3))  # eat the 1 px white fringe
    out = rgb.convert("RGBA")
    out.putalpha(mask)
    return out


# ---------------------------------------------------------------- posing
class Pose:
    def __init__(self, ua=0.0, udx=0.0, udy=0.0, la=0.0, sy=1.0, wa=0.0, wdx=0.0, wdy=0.0,
                 sx=1.0, tint=0.0, glow=0.0, dark=0.0):
        self.__dict__.update(locals())
        del self.__dict__["self"]


def layer(part, box, dx, dy):
    lay = Image.new("RGBA", (CW, CH))
    lay.paste(part, (int(round(box[0] + OX + dx)), int(round(box[1] + OY + dy))), part)
    return lay


def add_glow(lay, cx, cy, strength):
    if strength <= 0:
        return lay
    glow = Image.new("RGBA", (CW, CH))
    g = ImageDraw.Draw(glow)
    for r, a in ((90, 40), (60, 70), (34, 110)):
        g.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(90, 255, 140, int(a * strength)))
    glow = glow.filter(ImageFilter.GaussianBlur(14))
    return Image.alpha_composite(lay, glow)


HAND_BOX = (680, 280, 800, 372)   # forward fist hangs below the belt line: keep it on the torso
_halves = {}


def split_halves(src):
    """Upper half = rows above the belt plus the forward hand; lower half = legs only."""
    key = id(src)
    if key not in _halves:
        upper_box = (250, 30, 800, HAND_BOX[3])
        lower_box = (250, SPLIT_LOWER, 800, src.height)
        upper, lower = src.crop(upper_box), src.crop(lower_box)
        um = Image.new("L", upper.size, 0)
        ImageDraw.Draw(um).rectangle([0, 0, upper.width, SPLIT_UPPER - upper_box[1]], fill=255)
        ImageDraw.Draw(um).rectangle([HAND_BOX[0] - upper_box[0], HAND_BOX[1] - upper_box[1],
                                      HAND_BOX[2] - upper_box[0], upper.height], fill=255)
        upper.putalpha(ImageChops.multiply(upper.getchannel("A"), um))
        lm = Image.new("L", lower.size, 255)
        ImageDraw.Draw(lm).rectangle([HAND_BOX[0] - lower_box[0], 0,
                                      HAND_BOX[2] - lower_box[0], HAND_BOX[3] - lower_box[1]], fill=0)
        lower.putalpha(ImageChops.multiply(lower.getchannel("A"), lm))
        _halves[key] = (upper, lower, upper_box, lower_box)
    return _halves[key]


def compose(src, p):
    upper, lower, upper_box, lower_box = split_halves(src)

    # legs: squash toward the ground, then swing around the hip
    lh = lower.height
    if p.sy != 1.0:
        lower = lower.resize((lower.width, max(1, int(lh * p.sy))), Image.BICUBIC)
    l_top = src.height - lower.height  # keep the soles planted
    hip_y = GROUND - (GROUND - HIP[1]) * p.sy
    low = layer(lower, (lower_box[0], l_top), 0, 0)
    if p.la:
        low = low.rotate(p.la, resample=Image.BICUBIC, center=(HIP[0] + OX, hip_y + OY))

    # torso: follows the hip, then leans / lunges
    up_dy = (hip_y - HIP[1]) + p.udy
    up = layer(upper, upper_box, p.udx, up_dy)
    up = add_glow(up, GAUNTLET[0] + OX + p.udx, GAUNTLET[1] + OY + up_dy, p.glow)
    if p.ua:
        up = up.rotate(p.ua, resample=Image.BICUBIC, center=(HIP[0] + OX + p.udx, hip_y + OY + up_dy))

    fig = Image.alpha_composite(low, up)

    # whole-body rotation (tumbles, knockdowns) about the figure's centre
    if p.wa:
        cy = (GROUND + 40 * p.sy + 300) / 2 + OY
        fig = fig.rotate(p.wa, resample=Image.BICUBIC, center=(FEET_X + OX, cy))
        if abs(p.wa) >= 45:  # falling / lying: drop onto the ground line
            bb = fig.getbbox()
            if bb:
                fig = ImageChops.offset(fig, 0, int(GROUND + OY - bb[3]))
    if p.sx != 1.0:  # turning: squash horizontally about the anchor
        squashed = fig.resize((max(1, int(CW * p.sx)), CH), Image.BICUBIC)
        fig = Image.new("RGBA", (CW, CH))
        fig.paste(squashed, (int((FEET_X + OX) * (1 - p.sx)), 0), squashed)
    if p.wdx or p.wdy:
        fig = ImageChops.offset(fig, int(p.wdx), int(p.wdy))
    if p.tint or p.dark:
        r, g, b, a = fig.split()
        if p.tint:
            r = r.point(lambda v: int(v + (255 - v) * p.tint))
            g = g.point(lambda v: int(v * (1 - p.tint * 0.6)))
            b = b.point(lambda v: int(v * (1 - p.tint * 0.6)))
        if p.dark:
            r, g, b = (c.point(lambda v: int(v * (1 - p.dark))) for c in (r, g, b))
        fig = Image.merge("RGBA", (r, g, b, a))
    return fig


def bump(t):
    """0 -> 1 -> 0 over t in [0,1] (attack extension curve)."""
    return math.sin(math.pi * min(1.0, max(0.0, t)))


def pose_for(group, k, n):
    t = k / (n - 1) if n > 1 else 1.0
    s = bump(t)
    crouch, air = 0.62, 0.86
    if group == 0:   return Pose(udy=4 * math.sin(2 * math.pi * k / n), ua=0.8 * math.sin(2 * math.pi * k / n))
    if group == 5:   return Pose(sx=0.55)
    if group == 6:   return Pose(sx=0.55, sy=crouch)
    if group == 11:  return Pose(sy=[0.8, crouch, crouch][min(k, 2)])
    if group == 20:  return Pose(la=7 * math.sin(2 * math.pi * k / n), ua=-3, wdy=-6 * abs(math.sin(2 * math.pi * k / n)))
    if group == 21:  return Pose(la=-6 * math.sin(2 * math.pi * k / n), ua=4, wdy=-5 * abs(math.sin(2 * math.pi * k / n)))
    if group == 41:  return Pose(sy=0.8 if k < 2 else air, ua=-4 * t, la=8 * s)
    if group == 42:  return Pose(sy=0.78, wa=-360.0 * (k + 1) / (n + 1))
    if group == 43:  return Pose(sy=0.8)
    if group == 100: return Pose(ua=-14, udx=12, la=12 * math.sin(2 * math.pi * k / n), wdy=-6 * abs(math.sin(2 * math.pi * k / n)))
    if group == 181: return Pose(ua=5 * s, udy=-14 * s, glow=0.6 + 0.4 * s)
    if group in (191, 192): return Pose(glow=0.5 + 0.5 * s, ua=-3 * s)
    if group == 120: return Pose(ua=9, udx=-8, dark=0.08)
    if group == 121: return Pose(ua=9, udx=-6, sy=crouch, dark=0.08)
    if group == 122: return Pose(ua=9, sy=air, dark=0.08)
    if group in (5000, 5001, 5002):
        return Pose(ua=(18, 12, 8)[group - 5000] * bump((k + 1) / (n + 1)), udx=-10 * s, tint=0.45 if k == 0 else 0)
    if group in (5010, 5011, 5012):
        return Pose(ua=10 * bump((k + 1) / (n + 1)), la=-10 * s, tint=0.45 if k == 0 else 0)
    if group == 5020: return Pose(sy=crouch, ua=14 * bump((k + 1) / (n + 1)), tint=0.45 if k == 0 else 0)
    if group in (5030, 5031, 5032): return Pose(sy=air, wa=20 + 45 * t, tint=0.3 if k == 0 else 0)
    if group in (5040, 5041, 5042): return Pose(sy=air, wa=65 + 25 * t)
    if group in (5060, 5061, 5062): return Pose(wa=90)
    if group in (5070, 5071, 5072): return Pose(wa=50 + 40 * t)
    if group == 5300: return Pose(wa=6 * math.sin(2 * math.pi * k / n), ua=-4 * math.cos(2 * math.pi * k / n))
    if group == 200: return Pose(udx=38 * s, ua=-8 * s)
    if group == 210: return Pose(udx=62 * s, ua=-13 * s, la=-4 * s)
    if group == 230: return Pose(la=-32 * s, ua=10 * s)
    if group == 240: return Pose(la=-48 * s, ua=16 * s, wdy=-10 * s)
    if group == 400: return Pose(sy=crouch, udx=34 * s, ua=-8 * s)
    if group == 410: return Pose(sy=crouch, udx=40 * s, ua=-20 * s, udy=-30 * s)
    if group == 430: return Pose(sy=crouch, la=-28 * s, ua=6 * s)
    if group == 440: return Pose(sy=crouch * 0.95, la=-55 * s, ua=12 * s)
    if group == 600: return Pose(sy=air, udx=34 * s, ua=-10 * s)
    if group == 610: return Pose(sy=air, udx=52 * s, ua=-16 * s)
    if group == 630: return Pose(sy=air, la=-36 * s, ua=10 * s)
    if group == 640: return Pose(sy=air, la=-50 * s, ua=14 * s)
    if group == 800: return Pose(udx=50 * bump(t * 2), ua=-30 * max(0.0, t * 2 - 1) if t > 0.5 else -6 * s)
    if group == 1000: return Pose(udx=70 * s, ua=-15 * s, glow=0.3 + 0.7 * s)
    if group in (1050, 1052, 1055): return Pose(la=-52 * s, ua=12 * s, wdx=24 * t)
    if group == 1100: return Pose(wdy=-60 * s, ua=-20 * s, la=-18 * s, glow=s)
    if group == 1210: return Pose(udx=52 * s, ua=-25 * s, glow=0.8 * s)
    if group in (1300, 1320, 1340):
        return Pose(ua=10, udx=-10, sy={1300: 1.0, 1320: crouch, 1340: air}[group], glow=0.7)
    if group == 1400: return Pose(wa=-10 * s, wdx=40 * s, udx=30 * s, glow=0.5 * s)
    return Pose()


def save_png(im, path):
    """256-colour PNG with alpha: ~4-5x smaller than RGBA, visually identical for this art."""
    im.convert("RGBA").quantize(256, method=2).save(path, optimize=True)


def save_frame(fig, out_dir, group, item, axes):
    small = fig.resize((int(CW * SCALE), int(CH * SCALE)), Image.LANCZOS)
    bb = small.getbbox()
    ax, ay = int(round((FEET_X + OX) * SCALE)), int(round((GROUND + OY) * SCALE))
    if bb:  # trim empty canvas, keep the anchor
        small = small.crop(bb)
        ax, ay = ax - bb[0], ay - bb[1]
    save_png(small, os.path.join(out_dir, "%d_%d.png" % (group, item)))
    axes.append("%d_%d %d %d" % (group, item, ax, ay))


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


def portraits(src, out_dir, axes):
    head = src.crop((470, 40, 610, 180)).resize((100, 100), Image.LANCZOS)
    bg = Image.new("RGBA", (100, 100), (28, 40, 34, 255))
    save_png(Image.alpha_composite(bg, head), os.path.join(out_dir, "9000_0.png"))
    bust = src.crop((330, 40, 770, 553))  # 440x513, same 6:7 ratio as 480x560
    save_png(bust.resize((480, 560), Image.LANCZOS), os.path.join(out_dir, "9000_1.png"))
    axes += ["9000_0 0 0", "9000_1 0 0"]


def main():
    out_dir = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "art")
    os.makedirs(out_dir, exist_ok=True)
    src = cut_out(Image.open(SRC))
    src.save(os.path.join(HERE, "cutout.png"))
    axes = ["# generated by make_frames.py: <group>_<item> <axis x> <axis y>"]
    count = 0
    for group, items in template_groups().items():
        n = len(items)
        for k, item in enumerate(items):
            save_frame(compose(src, pose_for(group, k, n)), out_dir, group, item, axes)
            count += 1
    radar_pulse(out_dir, axes)
    portraits(src, out_dir, axes)
    with open(os.path.join(out_dir, "axis.txt"), "w") as f:
        f.write("\n".join(axes) + "\n")
    print("generated %d pose frames + 6 projectile + 2 portraits in %s" % (count, out_dir))


if __name__ == "__main__":
    main()

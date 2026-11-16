"""Shared cut-out animation pipeline: one illustration -> a full fighter sprite set.

A fighter's make_frames.py describes its source image with a config dict and
calls generate(). The figure is cut out of its white background, split at the
hips into an upper half (torso, arms, head) and a lower half (legs), and the
halves are posed (lean, lunge, squash, swing, tumble) to produce one frame for
every sprite number the Kung Fu Man 720 template uses, so the template's
animations, timings and hitboxes drive the new art.

Config keys (all coordinates are pixels in the source image, after mirroring):
  source        path to the PNG (figure on a white background)
  background    "white" (default) or "checker" for a painted grey/white checkerboard
  holes         optional points inside small enclosed background gaps (e.g. between an
                arm and the body) that the automatic cut-out kept; they are cleared
  mirror        True if the figure faces left in the source (fighters face right)
  prescale      optional resize applied after mirroring; landmarks are in the
                prescaled image's pixels
  hip           (x, y) pivot between the halves
  ground        y of the soles
  feet_x        x of the anchor point between the feet
  split_upper   upper half keeps rows above this
  split_lower   lower half keeps rows from this down (overlap hides the seam)
  x_range       (left, right) horizontal extent of the figure
  top           y of the top of the figure
  torso_boxes   boxes below split_upper that belong to the upper half (a hanging
                hand, a costume hem); they are removed from the legs layer
  glow_point    (x, y) where special-move glows are drawn (hand/gadget)
  glow_color    (r, g, b)
  scale         source -> game pixels (KFM 720 stands ~420 px tall)
  head_box      square crop for the 100x100 select icon
  bust_box      6:7 crop for the 480x560 large portrait
  icon_bg       (r, g, b) background behind the select icon
  effects       callable(out_dir, axes) that writes projectile/effect sprites
  leg_polys     polygons above split_lower copied into the legs layer as an underlay
                (thigh tops that disappear under a costume); the torso layer is drawn
                over them unchanged, so moving the torso never exposes a gap
  leg_cut       polygons of thigh that is visible above split_upper: moved from the
                torso layer to the legs layer (prevents a doubled, jagged thigh edge)
  leg_shapes    optional polygons tracing each leg exactly; when given, the legs layer
                is just these shapes and everything else (capes, props, costume tips)
                stays with the torso. Replaces split rows / torso_boxes / leg_* keys
  lunge         optional multiplier for forward torso slides (default 1.0); lower it
                when the legs join the body under a costume that would expose a gap
"""
import math
import os
import struct

from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageOps

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
TEMPLATE_SFF = os.path.join(ROOT, "content", "chars", "kfm720", "kfm720.sff")

CW, CH = 1200, 760   # canvas every frame is composed on (source pixels)
OX, OY = 340, 120    # where the source image's (0,0) sits on the canvas


def template_groups():
    """Sprite numbers used by the KFM 720 template (items are not contiguous)."""
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
                if diff.histogram()[255] > 600:
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


def cut_out_checker(img):
    """Remove a checkerboard painted into the pixels (fake transparency).

    Background = light, colour-neutral pixels connected to the border, plus
    enclosed neutral regions that contain both checker tones (so bright but
    uniform areas such as glowing highlights are kept).
    """
    rgb = img.convert("RGB")
    w, h = rgb.size
    data = rgb.tobytes()
    cand = bytearray(w * h)
    tone = bytearray(w * h)  # 1 = light square, 2 = grey square
    for i in range(w * h):
        r, g, b = data[3 * i], data[3 * i + 1], data[3 * i + 2]
        hi, lo = max(r, g, b), min(r, g, b)
        if hi - lo <= 14 and lo >= 172:
            cand[i] = 1
            tone[i] = 1 if lo >= 230 else (2 if 180 <= hi <= 212 else 0)
    bg = bytearray(w * h)
    seen = bytearray(w * h)

    def flood(start):
        stack, comp = [start], []
        seen[start] = 1
        while stack:
            i = stack.pop()
            comp.append(i)
            x, y = i % w, i // w
            for j in ((i - 1) if x > 0 else -1, (i + 1) if x < w - 1 else -1,
                      (i - w) if y > 0 else -1, (i + w) if y < h - 1 else -1):
                if j >= 0 and cand[j] and not seen[j]:
                    seen[j] = 1
                    stack.append(j)
        return comp

    border = [x for x in range(w)] + [(h - 1) * w + x for x in range(w)] + \
             [y * w for y in range(h)] + [y * w + w - 1 for y in range(h)]
    for i in border:
        if cand[i] and not seen[i]:
            for j in flood(i):
                bg[j] = 1
    for i in range(w * h):  # enclosed gaps (between arms/legs): must look like checker
        if cand[i] and not seen[i]:
            comp = flood(i)
            if len(comp) > 300:
                n1 = sum(1 for j in comp if tone[j] == 1)
                n2 = sum(1 for j in comp if tone[j] == 2)
                if n1 > 0.15 * len(comp) and n2 > 0.15 * len(comp):
                    for j in comp:
                        bg[j] = 1
    mask = Image.frombytes("L", (w, h), bytes(0 if v else 255 for v in bg))
    mask = mask.filter(ImageFilter.MinFilter(3))
    out = rgb.convert("RGBA")
    out.putalpha(mask)
    return out


# ---------------------------------------------------------------- posing
class Pose:
    def __init__(self, ua=0.0, udx=0.0, udy=0.0, la=0.0, sy=1.0, wa=0.0, wdx=0.0, wdy=0.0,
                 sx=1.0, tint=0.0, glow=0.0, dark=0.0):
        self.__dict__.update(locals())
        del self.__dict__["self"]


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
    if group == 230: return Pose(la=32 * s, ua=10 * s)
    if group == 240: return Pose(la=48 * s, ua=16 * s, wdy=-10 * s)
    if group == 400: return Pose(sy=crouch, udx=34 * s, ua=-8 * s)
    if group == 410: return Pose(sy=crouch, udx=40 * s, ua=-20 * s, udy=-30 * s)
    if group == 430: return Pose(sy=crouch, la=28 * s, ua=6 * s)
    if group == 440: return Pose(sy=crouch * 0.95, la=55 * s, ua=12 * s)
    if group == 600: return Pose(sy=air, udx=34 * s, ua=-10 * s)
    if group == 610: return Pose(sy=air, udx=52 * s, ua=-16 * s)
    if group == 630: return Pose(sy=air, la=36 * s, ua=10 * s)
    if group == 640: return Pose(sy=air, la=50 * s, ua=14 * s)
    if group == 800: return Pose(udx=50 * bump(t * 2), ua=-30 * max(0.0, t * 2 - 1) if t > 0.5 else -6 * s)
    if group == 1000: return Pose(udx=70 * s, ua=-15 * s, glow=0.3 + 0.7 * s)
    if group in (1050, 1052, 1055): return Pose(la=52 * s, ua=12 * s, wdx=24 * t)
    if group == 1100: return Pose(wdy=-60 * s, ua=-20 * s, la=18 * s, glow=s)
    if group == 1210: return Pose(udx=52 * s, ua=-25 * s, glow=0.8 * s)
    if group in (1300, 1320, 1340):
        return Pose(ua=10, udx=-10, sy={1300: 1.0, 1320: crouch, 1340: air}[group], glow=0.7)
    if group == 1400: return Pose(wa=-10 * s, wdx=40 * s, udx=30 * s, glow=0.5 * s)
    return Pose()


class Rig:
    def __init__(self, cfg, src):
        self.c, self.src = cfg, src
        x0, x1 = cfg["x_range"]
        top = cfg["top"]
        boxes = cfg.get("torso_boxes", [])
        cuts = cfg.get("leg_cut", [])
        polys = cfg.get("leg_polys", []) + cuts
        upper_bottom = max([cfg["split_upper"]] + [b[3] for b in boxes])
        lower_top = min([cfg["split_lower"]] + [y for poly in polys for _, y in poly])
        self.upper_box = (x0, top, x1, upper_bottom)
        self.lower_box = (x0, lower_top, x1, src.height)
        upper, lower = src.crop(self.upper_box), src.crop(self.lower_box)
        um = Image.new("L", upper.size, 0)
        ImageDraw.Draw(um).rectangle([0, 0, upper.width, cfg["split_upper"] - top], fill=255)
        lm = Image.new("L", lower.size, 0)
        ImageDraw.Draw(lm).rectangle([0, cfg["split_lower"] - lower_top, lower.width, lower.height], fill=255)
        for b in boxes:
            ImageDraw.Draw(um).rectangle([b[0] - x0, b[1] - top, b[2] - x0, b[3] - top], fill=255)
            ImageDraw.Draw(lm).rectangle([b[0] - x0, b[1] - lower_top, b[2] - x0, b[3] - lower_top], fill=0)
        ul = Image.new("L", lower.size, 0)
        for poly in cfg.get("leg_polys", []):  # hidden thigh tops: non-rotating underlay
            ImageDraw.Draw(ul).polygon([(x - x0, y - lower_top) for x, y in poly], fill=255)
        for poly in cuts:   # visible thigh: legs layer only (swings with the leg)
            ImageDraw.Draw(lm).polygon([(x - x0, y - lower_top) for x, y in poly], fill=255)
            ImageDraw.Draw(um).polygon([(x - x0, y - top) for x, y in poly], fill=0)
        underlay = lower.copy()
        underlay.putalpha(ImageChops.multiply(lower.getchannel("A"), ul))
        shapes = cfg.get("leg_shapes")
        if shapes:  # exact leg outlines: override the row-based split
            lower_top = min(y for poly in shapes for _, y in poly)
            self.upper_box = (x0, top, x1, src.height)
            self.lower_box = (x0, lower_top, x1, src.height)
            upper, lower = src.crop(self.upper_box), src.crop(self.lower_box)
            um = Image.new("L", upper.size, 255)
            lm = Image.new("L", lower.size, 0)
            ul = Image.new("L", lower.size, 0)
            grow = cfg.get("leg_shape_grow", 7)  # px; pulls the legs' ink outline in with them
            for poly in shapes:
                ImageDraw.Draw(lm).polygon([(x - x0, y - lower_top) for x, y in poly], fill=255)
            if grow > 1:
                lm = lm.filter(ImageFilter.MaxFilter(grow | 1))
            um.paste(ImageChops.invert(lm), (0, lower_top - top))
        upper.putalpha(ImageChops.multiply(upper.getchannel("A"), um))
        lower.putalpha(ImageChops.multiply(lower.getchannel("A"), lm))
        self.upper, self.lower = upper, lower
        self.underlay = underlay if ul.getbbox() else None

    @staticmethod
    def layer(part, box, dx, dy):
        lay = Image.new("RGBA", (CW, CH))
        lay.paste(part, (int(round(box[0] + OX + dx)), int(round(box[1] + OY + dy))), part)
        return lay

    def add_glow(self, lay, cx, cy, strength):
        if strength <= 0:
            return lay
        r0, g0, b0 = self.c["glow_color"]
        glow = Image.new("RGBA", (CW, CH))
        g = ImageDraw.Draw(glow)
        for r, a in ((90, 40), (60, 70), (34, 110)):
            g.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(r0, g0, b0, int(a * strength)))
        glow = glow.filter(ImageFilter.GaussianBlur(14))
        return Image.alpha_composite(lay, glow)

    def compose(self, p):
        c = self.c
        hip, ground, feet_x = c["hip"], c["ground"], c["feet_x"]
        # hips follow the torso vertically: crouch squashes the legs, a rising torso stretches them
        hip_y = ground - (ground - hip[1]) * p.sy + p.udy
        leg_sy = (ground - hip_y) / float(ground - hip[1])

        def legs_layer(part):
            if leg_sy != 1.0:  # squash/stretch toward the ground, soles planted
                part = part.resize((part.width, max(1, int(round(part.height * leg_sy)))), Image.BICUBIC)
            return self.layer(part, (self.lower_box[0], self.src.height - part.height), 0, 0)

        low = legs_layer(self.lower)
        under = legs_layer(self.underlay) if self.underlay is not None else None
        if p.la:  # ...then swing the front leg around the hip (back leg counters slightly)
            pivot = (hip[0] + OX, hip_y + OY)
            split_x = int(hip[0] + OX)
            back = low.copy()
            ImageDraw.Draw(back).rectangle([split_x, 0, CW, CH], fill=(0, 0, 0, 0))
            front = low.copy()
            ImageDraw.Draw(front).rectangle([0, 0, split_x - 1, CH], fill=(0, 0, 0, 0))
            low = Image.alpha_composite(back.rotate(-0.3 * p.la, resample=Image.BICUBIC, center=pivot),
                                        front.rotate(p.la, resample=Image.BICUBIC, center=pivot))

        if under is not None:  # the underlay sits beneath the legs and never rotates
            low = Image.alpha_composite(under, low)
        up_dy = hip_y - hip[1]  # torso follows the hip, then leans / lunges
        udx = p.udx * c.get("lunge", 1.0)
        if udx:  # shear the legs so the hips travel with the torso while the feet stay planted
            g_y, h_y = ground + OY, hip_y + OY
            k = udx / float(g_y - h_y)
            low = low.transform((CW, CH), Image.AFFINE, (1, k, -k * g_y, 0, 1, 0), resample=Image.BICUBIC)
        up = self.layer(self.upper, self.upper_box, udx, up_dy)
        gp = c["glow_point"]
        up = self.add_glow(up, gp[0] + OX + udx, gp[1] + OY + up_dy, p.glow)
        if p.ua:
            up = up.rotate(p.ua, resample=Image.BICUBIC, center=(hip[0] + OX + udx, hip_y + OY + up_dy))
        fig = Image.alpha_composite(low, up)

        if p.wa:  # whole-body rotation (tumbles, knockdowns)
            cy = ground - 131 + 20 * p.sy + OY
            fig = fig.rotate(p.wa, resample=Image.BICUBIC, center=(feet_x + OX, cy))
            if abs(p.wa) >= 45:  # falling / lying: drop onto the ground line
                bb = fig.getbbox()
                if bb:
                    fig = ImageChops.offset(fig, 0, int(ground + OY - bb[3]))
        if p.sx != 1.0:  # turning: squash horizontally about the anchor
            squashed = fig.resize((max(1, int(CW * p.sx)), CH), Image.BICUBIC)
            fig = Image.new("RGBA", (CW, CH))
            fig.paste(squashed, (int((feet_x + OX) * (1 - p.sx)), 0), squashed)
        if p.wdx or p.wdy:
            fig = ImageChops.offset(fig, int(p.wdx), int(p.wdy))
        if p.tint or p.dark:
            r, g, b, a = fig.split()
            if p.tint:
                r = r.point(lambda v: int(v + (255 - v) * p.tint))
                g = g.point(lambda v: int(v * (1 - p.tint * 0.6)))
                b = b.point(lambda v: int(v * (1 - p.tint * 0.6)))
            if p.dark:
                r, g, b = (ch.point(lambda v: int(v * (1 - p.dark))) for ch in (r, g, b))
            fig = Image.merge("RGBA", (r, g, b, a))
        return fig


def save_png(im, path):
    """256-colour PNG with alpha: ~4-5x smaller than RGBA, visually identical for this art."""
    im.convert("RGBA").quantize(256, method=2).save(path, optimize=True)


def save_frame(cfg, fig, out_dir, group, item, axes):
    scale = cfg["scale"]
    small = fig.resize((int(CW * scale), int(CH * scale)), Image.LANCZOS)
    bb = small.getbbox()
    ax, ay = int(round((cfg["feet_x"] + OX) * scale)), int(round((cfg["ground"] + OY) * scale))
    if bb:  # trim empty canvas, keep the anchor
        small = small.crop(bb)
        ax, ay = ax - bb[0], ay - bb[1]
    save_png(small, os.path.join(out_dir, "%d_%d.png" % (group, item)))
    axes.append("%d_%d %d %d" % (group, item, ax, ay))


def portraits(cfg, src, out_dir, axes):
    head = src.crop(cfg["head_box"]).resize((100, 100), Image.LANCZOS)
    bg = Image.new("RGBA", (100, 100), tuple(cfg["icon_bg"]) + (255,))
    save_png(Image.alpha_composite(bg, head), os.path.join(out_dir, "9000_0.png"))
    save_png(src.crop(cfg["bust_box"]).resize((480, 560), Image.LANCZOS), os.path.join(out_dir, "9000_1.png"))
    axes += ["9000_0 0 0", "9000_1 0 0"]


def generate(cfg, out_dir):
    os.makedirs(out_dir, exist_ok=True)
    img = Image.open(cfg["source"]).convert("RGB")
    if cfg.get("mirror"):
        img = ImageOps.mirror(img)
    if cfg.get("background") == "checker":
        src = cut_out_checker(img)
    else:
        src = cut_out(img)
    for pt in cfg.get("holes", []):  # small enclosed gaps the automatic pass kept
        marked = img.copy()
        ImageDraw.floodfill(marked, pt, (255, 0, 255), thresh=40)
        gap = ImageChops.difference(marked, img).convert("L").point(lambda v: 255 if v else 0)
        gap = gap.filter(ImageFilter.MaxFilter(3))
        src.putalpha(ImageChops.subtract(src.getchannel("A"), gap))
    if cfg.get("prescale"):
        f = cfg["prescale"]
        src = src.resize((int(src.width * f), int(src.height * f)), Image.LANCZOS)
    src.save(os.path.join(os.path.dirname(cfg["source"]), "cutout.png"))
    rig = Rig(cfg, src)
    axes = ["# generated by the cut-out pipeline: <group>_<item> <axis x> <axis y>"]
    count = 0
    for group, items in template_groups().items():
        for k, item in enumerate(items):
            save_frame(cfg, rig.compose(pose_for(group, k, len(items))), out_dir, group, item, axes)
            count += 1
    cfg["effects"](out_dir, axes)
    portraits(cfg, src, out_dir, axes)
    with open(os.path.join(out_dir, "axis.txt"), "w") as f:
        f.write("\n".join(axes) + "\n")
    print("generated %d pose frames + effects + 2 portraits in %s" % (count, out_dir))

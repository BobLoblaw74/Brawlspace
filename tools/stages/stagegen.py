"""Generic stage generator: one illustration -> a parallax Ikemen GO stage.

A stage folder (tools/stages/<id>/) has source.png/.jpg and a make_stage.py
that calls build(CONFIG). Everything is described in source-image pixels.

CONFIG keys
  id, name          file id (content/stages/<id>.def) and display name
  source            path to the illustration
  scale             source -> game pixels (720p screen; ~1.9 for a 1024-wide image)
  ground_y          source row where the fighters' feet go
  zoffset           screen row of the ground line (default 610)
  layers            back to front: [{"name", "delta", "polys"}]
                      delta  scroll speed relative to the camera (1 = moves with
                             the ground, 0.4 = far away); far layers move less
                      polys  source-pixel polygons this layer owns; omit for the
                             back layer, which is always the whole image. Each
                             entry is a point list, or {"poly": [...], "behind":
                             "keep"|"fill"}: what farther layers show where this
                             region used to be once the layers slide apart.
                             "fill" (default) blends it in from the surroundings
                             (best over sky, water, plain walls); "keep" leaves
                             the original pixels (best for foliage, where a
                             slightly doubled leaf edge looks natural, and for
                             detailed things like a bridge, which blur badly)
  elements          optional moving pieces: [{"name", "layer", "poly", "motion",
                      "pivot", "amp", "period", "phase"}]
                      motion "sway" rotates by +/-amp degrees about pivot,
                             "bob" moves up/down by +/-amp source px (with a
                             slight tilt); period in game ticks (60 = 1 s)
  glow              optional pulsing neon glow: {"layer", "min_y", "max_y",
                      "boost", "pulse", "polys"} (bright saturated pixels between
                      min_y and max_y, added on top of that layer; "polys"
                      limits it to those source-pixel regions, e.g. to skip a
                      bright prop that shouldn't pulse)
  shadow_color      (r, g, b) tint of the fighters' shadows
  music             optional background music, a path the engine resolves from the
                    content root, e.g. "sound/song.ogg" (OGG recommended; the file
                    lives in content/sound/); music_volume sets bgmvolume (default 100)
  feather           mask edge softness in source px (default 2)

How depth works: each layer is cut out with its polygons. Wherever a nearer
layer (or a moving element) covers it, the hidden area is filled in from the
surrounding pixels (pyramid inpainting), so when the layers slide apart the
gaps show plausible background instead of holes or doubled objects.
"""
import colorsys
import math
import os
import subprocess
import sys

from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageMath

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
STAGES = os.path.join(ROOT, "content", "stages")
FRAMES = 12  # frames per moving element loop


# ---------------------------------------------------------------- masks / inpaint
def poly_mask(size, polys):
    m = Image.new("L", size, 0)
    d = ImageDraw.Draw(m)
    for p in polys:
        d.polygon([tuple(pt) for pt in p], fill=255)
    return m


def _down(img, known):
    w, h = max(1, img.width // 2), max(1, img.height // 2)
    prem = ImageChops.multiply(img, Image.merge("RGB", (known, known, known))).resize((w, h), Image.BOX)
    k = known.resize((w, h), Image.BOX)
    chans = [ImageMath.eval("convert(min(p * 255 / max(k, 1), 255), 'L')", p=c, k=k) for c in prem.split()]
    return Image.merge("RGB", chans), k.point(lambda v: 255 if v > 0 else 0)


def inpaint(img, unknown):
    """Fill pixels where unknown=255 from their surroundings (coarse-to-fine pyramid)."""
    known = ImageChops.invert(unknown.point(lambda v: 255 if v > 127 else 0))
    if known.getextrema()[0] == 255:  # nothing unknown
        return img
    if min(img.size) <= 2:
        stat = [int(sum(i * n for i, n in enumerate(c.histogram())) / max(1, img.width * img.height)) for c in img.split()]
        return Image.new("RGB", img.size, tuple(stat))
    small, sk = _down(img, known)
    filled = inpaint(small, ImageChops.invert(sk))
    up = filled.resize(img.size, Image.BILINEAR)
    return Image.composite(img, up, known)


# ---------------------------------------------------------------- pieces
def glow_layer(img, min_y, max_y, boost, polys=None):
    w, h = img.size
    px = img.load()
    out = Image.new("RGB", (w, h))
    opx = out.load()
    inside = poly_mask(img.size, polys).load() if polys else None
    for y in range(max(0, min_y), min(h, max_y)):
        for x in range(w):
            if inside and not inside[x, y]:
                continue
            r, g, b = px[x, y]
            _, s, v = colorsys.rgb_to_hsv(r / 255.0, g / 255.0, b / 255.0)
            if v > 0.82 and s > 0.45:
                opx[x, y] = (r, g, b)
    out = out.filter(ImageFilter.GaussianBlur(6))
    return out.point(lambda c: min(255, int(c * boost)))


def element_frames(cfg, el, layer_img_big, scale):
    """Cut the element out of its (scaled) layer image and animate it in place."""
    poly = [(x * scale, y * scale) for x, y in el["poly"]]
    xs, ys = [p[0] for p in poly], [p[1] for p in poly]
    pad = int(12 * scale)
    box = (int(min(xs)) - pad, int(min(ys)) - pad, int(max(xs)) + pad, int(max(ys)) + pad)
    piece = layer_img_big.crop(box).convert("RGBA")
    m = Image.new("L", piece.size, 0)
    ImageDraw.Draw(m).polygon([(x - box[0], y - box[1]) for x, y in poly], fill=255)
    m = m.filter(ImageFilter.GaussianBlur(cfg.get("feather", 2) * scale * 0.6))
    piece.putalpha(ImageChops.multiply(piece.getchannel("A"), m))
    pv = el.get("pivot")
    pivot = ((pv[0] * scale - box[0]), (pv[1] * scale - box[1])) if pv else (piece.width / 2, piece.height / 2)
    frames = []
    for k in range(FRAMES):
        t = 2 * math.pi * (k / float(FRAMES) + el.get("phase", 0.0))
        if el["motion"] == "sway":
            f = piece.rotate(el["amp"] * math.sin(t), resample=Image.BICUBIC, center=pivot)
        elif el["motion"] == "bob":
            f = piece.rotate(el["amp"] * 0.4 * math.sin(t + 0.8), resample=Image.BICUBIC, center=pivot)
            f = ImageChops.offset(f, 0, int(round(el["amp"] * scale * math.sin(t))))
        else:
            raise SystemExit("unknown motion %r" % el["motion"])
        frames.append(f)
    return frames, box


# ---------------------------------------------------------------- build
def build(cfg):
    sid, scale = cfg["id"], cfg["scale"]
    here = os.path.dirname(os.path.abspath(cfg["source"]))
    art = os.path.join(here, "art")
    os.makedirs(art, exist_ok=True)
    for f in os.listdir(art):
        if f.endswith(".png") or f == "axis.txt":
            os.remove(os.path.join(art, f))
    src = Image.open(cfg["source"]).convert("RGB")
    W, H = src.size
    BW, BH = int(round(W * scale)), int(round(H * scale))
    feather = cfg.get("feather", 2)
    layers = cfg["layers"]
    elements = cfg.get("elements", [])

    def polys_of(L, which=None):
        out = []
        for p in L.get("polys") or []:
            poly, behind = (p["poly"], p.get("behind", "fill")) if isinstance(p, dict) else (p, "fill")
            if which is None or behind == which:
                out.append(poly)
        return out

    masks = [Image.new("L", (W, H), 255) if i == 0 or not L.get("polys") else poly_mask((W, H), polys_of(L))
             for i, L in enumerate(layers)]
    fill_masks = [poly_mask((W, H), polys_of(L, "fill")) if i > 0 else Image.new("L", (W, H), 0)
                  for i, L in enumerate(layers)]
    el_masks = [poly_mask((W, H), [e["poly"]]).filter(ImageFilter.MaxFilter(9)) for e in elements]

    axes, bgs, actions = [], [], []
    for i, L in enumerate(layers):
        hidden = Image.new("L", (W, H), 0)
        for j in range(i + 1, len(layers)):  # covered by nearer "fill" regions
            hidden = ImageChops.lighter(hidden, fill_masks[j].filter(ImageFilter.MaxFilter(7)))
        for e, em in zip(elements, el_masks):  # moving elements of this layer
            if e["layer"] == i:
                hidden = ImageChops.lighter(hidden, em)
        own = masks[i]
        if i > 0:  # don't invent pixels outside this layer's own area
            hidden = ImageChops.multiply(hidden, own.filter(ImageFilter.MaxFilter(5)))
        content = inpaint(src, hidden)
        big = content.resize((BW, BH), Image.LANCZOS).filter(ImageFilter.UnsharpMask(radius=2, percent=60, threshold=2))
        if i == 0:
            sprite, bbox = big, (0, 0, BW, BH)
        else:
            alpha = own.filter(ImageFilter.GaussianBlur(feather)).resize((BW, BH), Image.BILINEAR)
            sprite = big.convert("RGBA")
            sprite.putalpha(alpha)
            bbox = alpha.getbbox()
            sprite = sprite.crop(bbox)
        sprite.save(os.path.join(art, "%d_0.png" % i), optimize=True)
        axes.append("%d_0 %d %d" % (i, BW // 2 - bbox[0], -bbox[1]))
        bgs.append(("Layer %s" % L["name"], "normal", "spriteno = %d, 0" % i, L["delta"]))

        # moving elements on this layer (cut from the unfilled source so they look original)
        orig_big = src.resize((BW, BH), Image.LANCZOS)
        for n, e in enumerate(elements):
            if e["layer"] != i:
                continue
            frames, box = element_frames(cfg, e, orig_big, scale)
            group = 100 + n
            for k, fr in enumerate(frames):
                fr.save(os.path.join(art, "%d_%d.png" % (group, k)), optimize=True)
                axes.append("%d_%d %d %d" % (group, k, BW // 2 - box[0], -box[1]))
            tick = max(1, int(round(e.get("period", 120) / float(FRAMES))))
            actions.append((200 + n, ["%d,%d, 0,0, %d" % (group, k, tick) for k in range(FRAMES)]))
            bgs.append(("Element %s" % e["name"], "anim", "actionno = %d" % (200 + n), L["delta"]))

        g = cfg.get("glow")
        if g and g.get("layer", 0) == i:
            glow = glow_layer(src, g["min_y"], g.get("max_y", int(H * 0.75)), g.get("boost", 1.7), g.get("polys"))
            glow.resize((BW, BH), Image.LANCZOS).save(os.path.join(art, "50_0.png"), optimize=True)
            axes.append("50_0 %d 0" % (BW // 2))
            pulse = g.get("pulse", (110, 160, 190, 160))
            actions.append((300, ["50,0, 0,0, 20, , AS%dD256" % a for a in pulse]))
            bgs.append(("Glow", "anim", "actionno = 300", L["delta"]))

    # stage-select thumbnail 240x100 (sprite 9000,1)
    thumb = src.resize((240, int(round(H * 240.0 / W))), Image.LANCZOS)
    off = max(0, (thumb.height - 100) // 2)
    thumb.crop((0, off, 240, off + 100)).save(os.path.join(art, "9000_1.png"), optimize=True)
    axes.append("9000_1 0 0")
    with open(os.path.join(art, "axis.txt"), "w") as f:
        f.write("\n".join(axes) + "\n")
    subprocess.run([sys.executable, "-I", os.path.join(ROOT, "tools", "png_to_sff.py"), art,
                    os.path.join(STAGES, sid + ".sff")], check=True)

    z = cfg.get("zoffset", 610)
    top = z - int(round(cfg["ground_y"] * scale))
    bx = BW // 2 - 640 - 10
    bh = max(0, -top - 10)
    sc = cfg.get("shadow_color", (0, 0, 0))
    out = [DEF_HEAD.format(name=cfg["name"], bx=bx, bh=bh, z=z, sid=sid, sc="%d,%d,%d" % tuple(sc),
                           music=(" " + cfg["music"]) if cfg.get("music") else "", music_volume=cfg.get("music_volume", 100))]
    out.append("[Begin Action 9000]\n9000,1, 0,0, -1\n")
    for num, lines in actions:
        out.append("[Begin Action %d]\n%s\n" % (num, "\n".join(lines)))
    for n, (title, typ, spr, delta) in enumerate(bgs):
        # mask = 1 lets the engine use each sprite's transparency (only the back layer is opaque)
        out.append("[BG %s]\ntype = %s\n%s\nlayerno = 0\nstart = 0, %d\ndelta = %g, 1\nmask = %d\n"
                   % (title, typ, spr, top, delta, 0 if n == 0 else 1))
    with open(os.path.join(STAGES, sid + ".def"), "w") as f:
        f.write("\n".join(out))
    print("stage written: content/stages/%s.def (%dx%d, %d layers, %d elements, pan +/-%d)"
          % (sid, BW, BH, len(layers), len(elements), bx))


DEF_HEAD = """; {name} - generated by tools/stages/stagegen.py (edit tools/stages/{sid}/make_stage.py)
[Info]
name = "{name}"
displayname = "{name}"
mugenversion = 1.0
author = "Brawlspace"

[Camera]
startx = 0
starty = 0
boundleft = -{bx}
boundright = {bx}
boundhigh = -{bh}
boundlow = 0
verticalfollow = .2
floortension = 200
tension = 200
cuthigh = 0
cutlow = 0

[PlayerInfo]
p1startx = -280
p1starty = 0
p1facing = 1
p2startx = 280
p2starty = 0
p2facing = -1
p3startx = -400
p3starty = 0
p3facing = 1
p4startx = 400
p4starty = 0
p4facing = -1
leftbound  = -4000
rightbound =  4000

[Bound]
screenleft = 60
screenright = 60

[StageInfo]
zoffset = {z}
autoturn = 1
resetBG = 1
localcoord = 1280, 720
xscale = 1
yscale = 1
portraitscale = 4

[Shadow]
intensity = 110
color = {sc}
yscale = .3
fade.range = 0,0

[Reflection]
intensity = 0

[Music]
bgmusic ={music}
bgmvolume = {music_volume}

[BGdef]
spr = {sid}.sff
debugbg = 0
"""

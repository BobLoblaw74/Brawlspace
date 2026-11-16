"""Pack a folder of PNG frames into an Ikemen GO / MUGEN SFFv2 sprite file.

Usage (repo root):
    python3 -I tools/png_to_sff.py <art_dir> <out.sff> [--clsn]

<art_dir> holds one PNG per sprite named <group>_<item>.png (e.g. 0_0.png,
9000_1.png). Sprites are stored as 32-bit PNG (SFFv2 format 12), so any PNG
with transparency works as-is: no palette conversion needed.

Anchor (axis) per sprite, in pixels from the image's top-left corner:
  * default: bottom-center of the image (feet on the ground line)
  * override in <art_dir>/axis.txt, one line per sprite:  <group>_<item> <x> <y>
    ("default <x> <y>" sets a fallback for all sprites; '#' starts a comment)
  * portraits (group 9000) default to the top-left corner (0,0)

Byte-identical PNGs are stored once and linked. A 256-color placeholder palette
1,1 is included because the character palette system expects one.

--clsn prints a suggested Clsn2 (hurtbox) for every sprite, computed from its
opaque pixels relative to the axis, ready to paste into the .air file (needs
Pillow; skipped with a warning if it is not installed).
"""
import argparse
import hashlib
import os
import re
import struct
import sys

NAME_RE = re.compile(r"^(\d+)_(\d+)\.png$", re.I)
NODE = struct.Struct("<HHHHhhHBBIIHH")  # 28-byte SFFv2 sprite header
PAL_NODE = struct.Struct("<HHHHII")     # 16-byte SFFv2 palette header
HEADER_SIZE = 512


def png_size(data, name):
    if data[:8] != b"\x89PNG\r\n\x1a\n" or data[12:16] != b"IHDR":
        raise SystemExit("%s: not a valid PNG" % name)
    return struct.unpack(">II", data[16:24])


def read_axes(art_dir):
    axes, default = {}, None
    path = os.path.join(art_dir, "axis.txt")
    if not os.path.exists(path):
        return axes, default
    with open(path) as f:
        for n, line in enumerate(f, 1):
            line = line.split("#", 1)[0].strip()
            if not line:
                continue
            parts = line.split()
            if len(parts) != 3:
                raise SystemExit("axis.txt line %d: expected '<group>_<item> <x> <y>'" % n)
            key, x, y = parts[0], int(parts[1]), int(parts[2])
            if key.lower() == "default":
                default = (x, y)
            else:
                m = re.match(r"^(\d+)_(\d+)$", key)
                if not m:
                    raise SystemExit("axis.txt line %d: bad sprite id %r" % (n, key))
                axes[(int(m.group(1)), int(m.group(2)))] = (x, y)
    return axes, default


def collect(art_dir):
    sprites = []
    for fn in os.listdir(art_dir):
        m = NAME_RE.match(fn)
        if m:
            g, i = int(m.group(1)), int(m.group(2))
            if g > 65535 or i > 65535:
                raise SystemExit("%s: group/item must be 0-65535" % fn)
            sprites.append((g, i, os.path.join(art_dir, fn)))
        elif fn.lower().endswith(".png"):
            print("skipping %s (name must be <group>_<item>.png)" % fn, file=sys.stderr)
    if not sprites:
        raise SystemExit("no <group>_<item>.png files in %s" % art_dir)
    sprites.sort()
    return sprites


def build(art_dir, out_path):
    sprites = collect(art_dir)
    axes, default_axis = read_axes(art_dir)
    unknown = set(axes) - {(g, i) for g, i, _ in sprites}
    for g, i in sorted(unknown):
        print("axis.txt: no sprite %d_%d (ignored)" % (g, i), file=sys.stderr)

    ldata = bytearray()
    palette = bytes(b for c in range(256) for b in (c, c, c, 0))  # placeholder 1,1
    pal_ofs = len(ldata)
    ldata += palette

    nodes, seen, report = [], {}, []
    for idx, (g, i, path) in enumerate(sprites):
        data = open(path, "rb").read()
        w, h = png_size(data, path)
        if w > 65535 or h > 65535:
            raise SystemExit("%s: image too large" % path)
        if (g, i) in axes:
            ax, ay = axes[(g, i)]
        elif default_axis and g != 9000:
            ax, ay = default_axis
        elif g == 9000:
            ax, ay = 0, 0
        else:
            ax, ay = w // 2, h
        digest = hashlib.sha1(data).hexdigest()
        if digest in seen:  # identical image: link to the first copy
            link = seen[digest]
            nodes.append([g, i, w, h, ax, ay, link, 12, 32, 0, 0, 0, 0])
        else:
            seen[digest] = idx
            ofs = len(ldata)
            ldata += struct.pack("<I", w * h * 4) + data  # PNG blocks start with decoded size
            nodes.append([g, i, w, h, ax, ay, 0, 12, 32, ofs, 4 + len(data), 0, 0])
        report.append((g, i, path, w, h, ax, ay))

    spr_off = HEADER_SIZE
    pal_off = spr_off + len(nodes) * NODE.size
    ldata_off = pal_off + PAL_NODE.size
    total = ldata_off + len(ldata)

    out = bytearray(HEADER_SIZE)
    out[0:12] = b"ElecbyteSpr\x00"
    out[12:16] = bytes((0, 1, 0, 2))  # version 2.01
    out[24:28] = bytes((0, 1, 0, 2))  # compatible version
    struct.pack_into("<IIIIIIII", out, 36,
                     spr_off, len(nodes), pal_off, 1, ldata_off, len(ldata), total, 0)
    for n in nodes:
        out += NODE.pack(*n)
    out += PAL_NODE.pack(1, 1, 256, 0, pal_ofs, len(palette))
    out += ldata
    with open(out_path, "wb") as f:
        f.write(out)

    linked = sum(1 for n in nodes if n[10] == 0)
    print("wrote %s: %d sprites (%d linked duplicates), %.1f KB"
          % (out_path, len(nodes), linked, len(out) / 1024.0))
    missing = [s for s in ((0, 0), (9000, 0), (9000, 1)) if s not in {(g, i) for g, i, _ in sprites}]
    if missing:
        print("note: missing recommended sprites: %s" % ", ".join("%d_%d" % s for s in missing))
    return report


def print_clsn(report):
    try:
        from PIL import Image
    except ImportError:
        print("--clsn needs Pillow (pip install pillow); skipped", file=sys.stderr)
        return
    print("\n; Suggested Clsn2 hurtboxes (x1,y1,x2,y2 relative to the axis); paste above the frame in .air")
    for g, i, path, w, h, ax, ay in report:
        if g == 9000:
            continue
        bbox = Image.open(path).convert("RGBA").getchannel("A").point(lambda a: 255 if a > 32 else 0).getbbox()
        if not bbox:
            continue
        x1, y1, x2, y2 = bbox
        print("; %d,%d\nClsn2: 1\n Clsn2[0] = %d, %d, %d, %d"
              % (g, i, x1 - ax, y1 - ay, x2 - ax, y2 - ay))


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("art_dir")
    ap.add_argument("out_sff")
    ap.add_argument("--clsn", action="store_true", help="print suggested hurtboxes")
    a = ap.parse_args()
    if not os.path.isdir(a.art_dir):
        raise SystemExit("not a folder: %s" % a.art_dir)
    rep = build(a.art_dir, a.out_sff)
    if a.clsn:
        print_clsn(rep)

"""Export an SFFv2 sprite file to <group>_<item>.png frames plus axis.txt.

Usage (repo root):
    python3 -I tools/sff_to_png.py <in.sff> <out_dir> [--palette N]

The output folder is exactly what tools/png_to_sff.py packs, so this is useful to
  * pull reference poses out of the template (e.g. kfm720) to draw over, and
  * round-trip an existing fighter into an editable PNG folder.
Paletted sprites are rendered with their own SFF palette (or palette 1,N with
--palette N); color index 0 becomes transparent. Needs Pillow.
Supported sprite formats: raw (0), RLE8 (2), PNG8/24/32 (10-12). RLE5/LZ5
sprites are reported and skipped.
"""
import argparse
import io
import os
import struct
import sys

try:
    from PIL import Image
except ImportError:
    raise SystemExit("needs Pillow: pip install pillow")

NODE = struct.Struct("<HHHHhhHBBIIHH")
PAL_NODE = struct.Struct("<HHHHII")


def rle8(data, n):
    out, i = bytearray(), 0
    while len(out) < n and i < len(data):
        b = data[i]
        i += 1
        if b & 0xC0 == 0x40:
            out += bytes((data[i],)) * (b & 0x3F)
            i += 1
        else:
            out.append(b)
    return bytes(out[:n]).ljust(n, b"\0")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("sff")
    ap.add_argument("out_dir")
    ap.add_argument("--palette", type=int, default=0, help="force palette 1,N for paletted sprites")
    a = ap.parse_args()

    d = open(a.sff, "rb").read()
    if d[:12] != b"ElecbyteSpr\x00" or d[15] != 2:
        raise SystemExit("only SFFv2 files are supported")
    spr_off, spr_num, pal_off, pal_num, lofs, _, tofs, _ = struct.unpack_from("<IIIIIIII", d, 36)

    pals, pal_by_id = [], {}
    for p in range(pal_num):
        g, it, ncol, link, ofs, ln = PAL_NODE.unpack_from(d, pal_off + p * 16)
        if ln == 0:
            pals.append(pals[link])
        else:
            raw = d[lofs + ofs: lofs + ofs + ncol * 4]
            pals.append([tuple(raw[k * 4: k * 4 + 3]) for k in range(ncol)])
        pal_by_id[(g, it)] = p
    forced = pal_by_id.get((1, a.palette)) if a.palette else None
    if a.palette and forced is None:
        raise SystemExit("palette 1,%d not found" % a.palette)

    os.makedirs(a.out_dir, exist_ok=True)
    nodes = [list(NODE.unpack_from(d, spr_off + i * 28)) for i in range(spr_num)]
    axis_lines, done, skipped = [], 0, []
    for idx, n in enumerate(nodes):
        g, it, w, h, ax, ay, link, fmt, depth, ofs, ln, palidx, flags = n
        src = n
        if ln == 0:  # linked sprite: same pixels as an earlier one
            src = nodes[link]
            _, _, w, h, _, _, _, fmt, depth, ofs, ln, palidx, flags = src
        base = (tofs if flags & 1 else lofs) + ofs
        blob = d[base: base + ln]
        pal = pals[forced if forced is not None else palidx] if pals else None
        try:
            if fmt in (10, 11, 12):
                img = Image.open(io.BytesIO(blob[4:]))
                if fmt == 10 or img.mode == "P":
                    idxs = img.convert("P") if img.mode != "P" else img
                    img = paletted(idxs.tobytes(), idxs.size, pal)
                else:
                    img = img.convert("RGBA")
            elif fmt == 0 and depth == 8:
                img = paletted(blob[:w * h], (w, h), pal)
            elif fmt == 2:
                img = paletted(rle8(blob[4:], w * h), (w, h), pal)
            else:
                skipped.append("%d_%d (format %d)" % (g, it, fmt))
                continue
        except Exception as e:  # keep exporting the rest
            skipped.append("%d_%d (%s)" % (g, it, e))
            continue
        img.save(os.path.join(a.out_dir, "%d_%d.png" % (g, it)))
        axis_lines.append("%d_%d %d %d" % (g, it, ax, ay))
        done += 1

    with open(os.path.join(a.out_dir, "axis.txt"), "w") as f:
        f.write("# <group>_<item> <axis x> <axis y>  (exported from %s)\n" % os.path.basename(a.sff))
        f.write("\n".join(axis_lines) + "\n")
    print("exported %d sprites to %s" % (done, a.out_dir))
    if skipped:
        print("skipped %d: %s" % (len(skipped), ", ".join(skipped[:10])), file=sys.stderr)


def paletted(indices, size, pal):
    if pal is None:
        raise ValueError("no palette")
    lut = [(c[0], c[1], c[2], 255) for c in pal] + [(0, 0, 0, 255)] * (256 - len(pal))
    lut[0] = (0, 0, 0, 0)
    img = Image.new("RGBA", size)
    img.putdata([lut[i] for i in indices])
    return img


if __name__ == "__main__":
    main()

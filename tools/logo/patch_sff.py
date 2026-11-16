"""Swap the title logo sprites (group 0, items 0-3) in the motif's system.sff.

Usage (repo root): python3 -I tools/logo/patch_sff.py [path/to/system.sff]

The new PNGs (tools/logo/out/layer0..3.png) are appended after the SFF's data
blocks and the four sprite headers are repointed at them (SFFv2 format 12 =
PNG, 32-bit). Re-runnable: the file is first truncated back to the end of its
original ldata/tdata blocks, dropping any previously appended logo.
"""
import os
import struct
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
SFF = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, "content", "data", "ikemen1", "system.sff")
NODE = struct.Struct("<HHHHhhHBBIIHH")  # 28-byte SFFv2 sprite header


def png_size(data):
    if data[:8] != b"\x89PNG\r\n\x1a\n":
        raise SystemExit("not a PNG")
    return struct.unpack(">II", data[16:24])


with open(SFF, "rb") as f:
    d = bytearray(f.read())
if bytes(d[:12]) != b"ElecbyteSpr\x00" or d[15] != 2:
    raise SystemExit("not an SFFv2 file")

spr_off, spr_num = struct.unpack_from("<II", d, 36)
lofs, llen, tofs, tlen = struct.unpack_from("<IIII", d, 52)
data_end = max(lofs + llen, tofs + tlen)
del d[data_end:]  # drop logo data appended by an earlier run

targets = {}
for i in range(spr_num):
    fields = list(NODE.unpack_from(d, spr_off + i * NODE.size))
    if fields[0] == 0 and fields[1] in (0, 1, 2, 3):
        targets[fields[1]] = (i, fields)
if sorted(targets) != [0, 1, 2, 3]:
    raise SystemExit("sprites 0,0-0,3 not all present")

for item in range(4):
    png = open(os.path.join(HERE, "out", "layer%d.png" % item), "rb").read()
    w, h = png_size(png)
    pos = len(d)
    d += struct.pack("<I", w * h * 4) + png  # format 10-12 blocks start with the decoded size
    i, fl = targets[item]
    fl[2], fl[3] = w, h                      # size
    fl[4], fl[5] = w // 2, h // 2            # axis: centered, like the stock logo
    fl[6] = 0                                # not linked
    fl[7], fl[8] = 12, 32                    # PNG, 32-bit
    fl[9], fl[10] = pos - lofs, 4 + len(png)  # offset relative to ldata, length
    fl[12] = 0                               # flags: data lives in ldata space
    NODE.pack_into(d, spr_off + i * NODE.size, *fl)
    print("sprite 0,%d -> %dx%d PNG, %d bytes" % (item, w, h, len(png)))

with open(SFF, "wb") as f:
    f.write(d)
print("patched", SFF)

"""Pack Tinker's warped (279) body frames into reference sheets for a manual Gemini redraw.

Writes redraw/sheet_NN.png (frames on white, up to ROW slots per row, ROWS rows per
sheet, read left to right, top to bottom) and redraw/sheets.json mapping each sheet to
its frame names in that order. Every sheet uses the same prompt, redraw/PROMPT.txt.

Usage (repo root): python3 -I tools/fighters/tinker/make_sheets.py
"""
import glob
import json
import os

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "redraw")
ROW, ROWS, GAP = 6, 2, 60
SKIP = {6000, 9000}  # radar pulse effect and portraits: not body frames

PROMPT = """\
Image 1 is the character Tinker. Image 2 is a sheet of crude, distorted animation frames of him.
Redraw every figure on image 2 as a clean, hand-drawn fighting-game sprite: keep exactly the
same number of figures in exactly the same order and layout, and give each one exactly the same
pose, limb positions, body proportions, size and facing direction as on image 2, but with the
face, outfit, gadgets, colours and inked comic style of image 1, with no warping or smearing.
Keep every figure complete and separate from its neighbours, nothing cropped.
Background: flat solid magenta #FF00FF everywhere, no shadows, no floor, no text, no borders.
"""


def frames():
    names = [os.path.basename(p)[:-4] for p in glob.glob(os.path.join(HERE, "art", "*_*.png"))]
    names = [n for n in names if int(n.split("_")[0]) not in SKIP]
    return sorted(names, key=lambda n: tuple(map(int, n.split("_"))))


def pack(names):
    """Rows of up to ROW slots (frames wider than 600 px take 2), ROWS rows per sheet."""
    rows, row, used = [], [], 0
    for n in names:
        w = Image.open(os.path.join(HERE, "art", n + ".png")).width
        slots = 2 if w > 600 else 1
        if used + slots > ROW:
            rows.append(row)
            row, used = [], 0
        row.append(n)
        used += slots
    rows.append(row)
    return [rows[i:i + ROWS] for i in range(0, len(rows), ROWS)]


def render(sheet_rows):
    ims = [[Image.open(os.path.join(HERE, "art", n + ".png")).convert("RGBA") for n in r] for r in sheet_rows]
    w = max(sum(i.width for i in r) + GAP * (len(r) + 1) for r in ims)
    h = sum(max(i.height for i in r) for r in ims) + GAP * (len(ims) + 1)
    sheet = Image.new("RGBA", (w, h), (255, 255, 255, 255))
    y = GAP
    for r in ims:
        x = GAP
        for i in r:
            sheet.alpha_composite(i, (x, y))
            x += i.width + GAP
        y += max(i.height for i in r) + GAP
    return sheet.convert("RGB")


def main():
    os.makedirs(OUT, exist_ok=True)
    manifest = {}
    for k, sheet_rows in enumerate(pack(frames())):
        name = "sheet_%02d" % k
        render(sheet_rows).save(os.path.join(OUT, name + ".png"), optimize=True)
        manifest[name] = sheet_rows
    with open(os.path.join(OUT, "sheets.json"), "w") as f:
        json.dump(manifest, f, indent=1)
    with open(os.path.join(OUT, "PROMPT.txt"), "w") as f:
        f.write(PROMPT)
    n = sum(len(r) for s in manifest.values() for r in s)
    print(len(manifest), "sheets,", n, "frames")


if __name__ == "__main__":
    main()

"""Cut Gemini's redrawn sheets (redraw/sheet_NN.png, see make_sheets.py) into Tinker's frames.

Each figure is written to every frame sheets.json lists for it, replacing the warped frame:
scaled by one factor per sheet (the median of old frame height / new figure height, so a
sheet keeps its own proportions), bottom-aligned to the old frame and with its body centre
where the old body centre was, so axes, motion and hitboxes keep working.

Usage (repo root):
    python3 -I tools/fighters/tinker/cut_sheets.py <out_dir> [sheet_00 ...]   # preview
    python3 -I tools/fighters/tinker/cut_sheets.py --apply [sheet_00 ...]     # into art/
Without sheet names, every redraw/sheet_NN.png present is cut. Writes
<out_dir>/compare_<sheet>.png (old above new) for review.
"""
import glob
import json
import os
import shutil
import statistics
import sys

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
import greensheet  # noqa: E402

ART = os.path.join(HERE, "art")
RD = os.path.join(HERE, "redraw")


def body_x(im):
    """Body centre x (greensheet.body_centre) of an image, in its own coordinates."""
    box = im.getchannel("A").point(lambda a: 255 if a > 128 else 0).getbbox()
    return box, box[0] + greensheet.body_centre(im.crop(box))


def cut(sheet, manifest, out_dir, axes):
    figs = greensheet.figures(os.path.join(RD, sheet + ".png"), keying=(40, 110, "magenta"), rows=True)
    want = manifest[sheet]
    if len(figs) != len(want):
        sys.exit("%s: %d figures, expected %d: redo it in Gemini" % (sheet, len(figs), len(want)))
    old = {f: Image.open(os.path.join(ART, f + ".png")).convert("RGBA") for w in want for f in w["frames"]}
    s = statistics.median(body_x(old[w["frames"][0]])[0][3] - body_x(old[w["frames"][0]])[0][1]
                          for w in want) / statistics.median(f.height for f, _ in figs)
    pairs = []
    for (fig, _), w in zip(figs, want):
        fig = fig.resize((round(fig.width * s), round(fig.height * s)), Image.LANCZOS)
        _, nbx = body_x(fig)
        for name in w["frames"]:
            (_, _, _, ob), obx = body_x(old[name])
            oax, oay = axes[name]
            greensheet.save_png(fig, os.path.join(out_dir, name + ".png"))
            axes[name] = (round(nbx + oax - obx), round(fig.height - (ob - oay)))
            pairs.append((old[name], fig))
    # review sheet: old frames above their redraws
    cw, ch = max(max(a.width, b.width) for a, b in pairs), max(a.height + b.height for a, b in pairs)
    cmp_ = Image.new("RGBA", (cw * len(pairs), ch), (255, 255, 255, 255))
    for k, (a, b) in enumerate(pairs):
        cmp_.alpha_composite(a, (k * cw, 0))
        cmp_.alpha_composite(b, (k * cw, a.height))
    cmp_.convert("RGB").save(os.path.join(out_dir, "compare_%s.png" % sheet))


def main(args):
    apply = args[:1] == ["--apply"]
    out_dir = ART if apply else args[0]
    sheets = args[1:] or sorted(os.path.basename(p)[:-4] for p in glob.glob(os.path.join(RD, "sheet_*.png")))
    with open(os.path.join(RD, "sheets.json")) as f:
        manifest = json.load(f)
    path = os.path.join(ART, "axis.txt")
    with open(path) as f:
        lines = f.read().splitlines()
    axes = {l.split()[0]: tuple(map(int, l.split()[1:])) for l in lines if l and not l.startswith("#")}
    os.makedirs(out_dir, exist_ok=True)
    for sheet in sheets:
        cut(sheet, manifest, out_dir, axes)
    out = [l if not l or l.startswith("#") else "%s %d %d" % ((l.split()[0],) + axes[l.split()[0]])
           for l in lines]
    with open(path if apply else os.path.join(out_dir, "axis.txt"), "w") as f:
        f.write("\n".join(out) + "\n")
    if apply:  # compare sheets are for review, not the build
        for p in glob.glob(os.path.join(ART, "compare_*.png")):
            shutil.move(p, os.path.join(RD, os.path.basename(p)))


if __name__ == "__main__":
    main(sys.argv[1:])

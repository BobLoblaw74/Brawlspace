"""Cut figures out of a green-screen sprite sheet (e.g. an AI-generated row of poses).

    figures(path) -> [(rgba_image, (x0, y0, x1, y1)), ...]   left to right
    cut_sheets(here, sheets, cal, out_dir, axes)   sprites + axes for a fighter's sheets
    recut(here, sheets, cal, out_dir)              same, into an existing art/ + axis.txt

Keys out the green with a soft edge, removes green spill from that edge, erases a drawn
floor line (rows opaque across most of the sheet), then splits the sheet into
connected figures, so poses whose bounding boxes overlap (a kick reaching over the
next pose) still come apart. Pieces smaller than min_area pixels (a leaf tip or vine end
that doesn't touch the body) join the nearest figure within `attach` pixels; anything
further away is dropped as noise.
"""
import os
from collections import deque

from PIL import Image

KEY_SOLID = 40   # greenness (g - max(r, b)) at or below this: fully opaque
KEY_CLEAR = 110  # at or above this: fully transparent


def key(im):
    im = im.convert("RGB")
    w, h = im.size
    src = im.load()
    out = Image.new("RGBA", (w, h))
    dst = out.load()
    for y in range(h):
        for x in range(w):
            r, g, b = src[x, y]
            d = g - max(r, b)
            if d <= KEY_SOLID:
                a = 255
            elif d >= KEY_CLEAR:
                a = 0
            else:
                a = round(255 * (KEY_CLEAR - d) / (KEY_CLEAR - KEY_SOLID))
            if 0 < a < 255 and d > 0:
                g = max(r, b)  # despill the soft edge only: green props (the bag) stay green
            dst[x, y] = (r, g, b, a)
    return out


def erase_floor_line(rgba, span=0.5, max_rows=8):
    """Clear rows that are opaque across more than `span` of the width (a floor line drawn
    under the poses), except where a figure covers them: a pixel stays when the pixels
    just above and below the band are both opaque (a boot standing on the line)."""
    w, h = rgba.size
    a = rgba.getchannel("A").load()
    rows = [y for y in range(h) if sum(1 for x in range(w) if a[x, y] > 128) > span * w]
    bands = []
    for y in rows:
        if bands and y == bands[-1][1] + 1:
            bands[-1][1] = y
        else:
            bands.append([y, y])
    px = rgba.load()
    for y0, y1 in bands:
        y0, y1 = max(0, y0 - 1), min(h - 1, y1 + 1)  # its anti-aliased edges too
        if y1 - y0 + 1 > max_rows:
            continue  # too thick to be a line
        for x in range(w):
            above = y0 > 0 and a[x, y0 - 1] > 128
            below = y1 < h - 1 and a[x, y1 + 1] > 128
            if not (above and below):
                for y in range(y0, y1 + 1):
                    r, g, b, _ = px[x, y]
                    px[x, y] = (r, g, b, 0)
    return rgba


def box_gap(a, b):
    """Pixel gap between two (x0, y0, x1, y1) boxes; 0 if they overlap."""
    dx = max(a[0] - b[2], b[0] - a[2], 0)
    dy = max(a[1] - b[3], b[1] - a[3], 0)
    return max(dx, dy)


def figures(path, min_area=2000, threshold=128, attach=40):
    rgba = erase_floor_line(key(Image.open(path)))
    w, h = rgba.size
    alpha = rgba.getchannel("A").load()
    label = [[0] * w for _ in range(h)]
    comps = []
    for y0 in range(h):
        for x0 in range(w):
            if label[y0][x0] or alpha[x0, y0] < threshold:
                continue
            n = len(comps) + 1
            label[y0][x0] = n
            q = deque([(x0, y0)])
            px = []
            while q:
                x, y = q.popleft()
                px.append((x, y))
                for nx, ny in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
                    if 0 <= nx < w and 0 <= ny < h and not label[ny][nx] and alpha[nx, ny] >= threshold:
                        label[ny][nx] = n
                        q.append((nx, ny))
            comps.append(px)
    def bbox(px):
        xs = [p[0] for p in px]
        ys = [p[1] for p in px]
        return (min(xs), min(ys), max(xs) + 1, max(ys) + 1)

    big = {n: bbox(px) for n, px in enumerate(comps, 1) if len(px) >= min_area}
    for n, px in enumerate(comps, 1):
        if n in big or not big:
            continue
        b = bbox(px)
        owner = min(big, key=lambda m: box_gap(b, big[m]))
        if box_gap(b, big[owner]) <= attach:
            for x, y in px:
                label[y][x] = owner
            o = big[owner]
            big[owner] = (min(o[0], b[0]), min(o[1], b[1]), max(o[2], b[2]), max(o[3], b[3]))
    out = []
    for n, box in big.items():
        # keep this figure's pixels plus the soft (sub-threshold) edge touching them
        fig = Image.new("RGBA", (box[2] - box[0], box[3] - box[1]))
        crop = rgba.crop(box)
        cp, fp = crop.load(), fig.load()
        for y in range(box[1], box[3]):
            row = label[y]
            for x in range(box[0], box[2]):
                l = row[x]
                if l == n:
                    fp[x - box[0], y - box[1]] = cp[x - box[0], y - box[1]]
                elif l == 0 and alpha[x, y] and any(
                        0 <= x + dx < w and 0 <= y + dy < h and label[y + dy][x + dx] == n
                        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1), (2, 0), (-2, 0), (0, 2), (0, -2))):
                    fp[x - box[0], y - box[1]] = cp[x - box[0], y - box[1]]
        out.append((fig, box))
    out.sort(key=lambda f: f[1][0])
    return out


# ---------------------------------------------------------------------------
# Fighter sheets.
#
# sheets: {<file>: (sprite group, {pose: anchor}, drawing size, mirrored poses)}
#   Poses face right (mirrored poses are drawn facing left and get flipped), standing on
#   the sheet's floor. Drawing size is relative to the sheet the calibration was
#   measured on (estimate it from figure areas and head widths). Anchors:
#     "foot" (default)  back foot planted: the axis is a fixed distance in front of it
#     "feet"            centred between the feet: a stance that widens and narrows
#                       (an idle shuffle) breathes around a steady body
#     "head"            head kept in place: a one-legged pose (a kick) steps in, not back
#     "air"             airborne: centred, anchored at its lowest point
#     "air_head"        airborne: head kept in place, anchored at its lowest point
#     "air_body"        airborne: body kept in place (centre of mass below the top 30%,
#                       which skips headgear like a vine crown), anchored at its lowest point
#     "body"            the same on the ground: "head" for a fighter whose top is headgear
# cal: measured on one stance pose (drawing size 1.0), in its sheet pixels:
#   {"scale": game px per sheet px (game idle height / sheet stance height),
#    "back_foot_to_axis": back boot's left edge -> midpoint of the feet,
#    "head_to_axis": head centre -> midpoint of the feet,
#    "body_to_axis": body centre (see "air_body") -> midpoint of the feet; optional}
# ---------------------------------------------------------------------------


def back_boot_left(fig, rows=30):
    """Left edge of the leftmost boot on the floor (the planted back foot)."""
    a = fig.getchannel("A").load()
    w, h = fig.size
    return next(x for x in range(w) if any(a[x, y] > 128 for y in range(h - rows, h)))


def feet_centre(fig, rows=30):
    """Midpoint between the outer edges of the boots on the floor."""
    a = fig.getchannel("A").load()
    w, h = fig.size
    xs = [x for x in range(w) if any(a[x, y] > 128 for y in range(h - rows, h))]
    return (xs[0] + xs[-1]) / 2


def body_centre(fig, skip=0.3):
    """Mean x of the opaque pixels below the top `skip` of the figure."""
    a = fig.getchannel("A").load()
    xs = [x for y in range(int(fig.height * skip), fig.height) for x in range(fig.width) if a[x, y] > 128]
    return sum(xs) / len(xs)


def head_centre(fig, rows=60):
    """Mean x of the opaque pixels in the top rows (the head)."""
    a = fig.getchannel("A").load()
    xs = [x for y in range(rows) for x in range(fig.width) if a[x, y] > 128]
    return sum(xs) / len(xs)


def save_png(im, path):
    """256-colour PNG with alpha, as tools/fighters/cutout.py writes."""
    im.convert("RGBA").quantize(256, method=2).save(path, optimize=True)


def cut_sheet(path, group, anchors, size, mirrored, cal, out_dir, axes):
    scale = cal["scale"] / size
    for k, (fig, _) in enumerate(figures(path)):
        if k in mirrored:
            fig = fig.transpose(Image.FLIP_LEFT_RIGHT)
        anchor = anchors.get(k, "foot")
        if anchor in ("head", "air_head"):
            ax = (head_centre(fig, round(60 * size)) + cal["head_to_axis"] * size) * scale
        elif anchor in ("air_body", "body"):
            ax = (body_centre(fig) - cal.get("body_to_axis", 0) * size) * scale
        elif anchor == "feet":
            ax = feet_centre(fig, round(30 * size)) * scale
        elif anchor == "air":
            ax = fig.width / 2 * scale
        else:
            ax = (back_boot_left(fig, round(30 * size)) + cal["back_foot_to_axis"] * size) * scale
        ay = fig.height * scale
        fig = fig.resize((round(fig.width * scale), round(fig.height * scale)), Image.LANCZOS)
        save_png(fig, os.path.join(out_dir, "%d_%d.png" % (group, k)))
        axes.append("%d_%d %d %d" % (group, k, round(ax), round(ay)))


def cut_sheets(here, sheets, cal, out_dir, axes):
    for name, (group, anchors, size, mirrored) in sheets.items():
        cut_sheet(os.path.join(here, name), group, anchors, size, mirrored, cal, out_dir, axes)


def recut(here, sheets, cal, out_dir):
    """Re-cut the sheets into an existing art dir, replacing their axis.txt lines."""
    axes = []
    cut_sheets(here, sheets, cal, out_dir, axes)
    groups = tuple("%d_" % s[0] for s in sheets.values())
    path = os.path.join(out_dir, "axis.txt")
    with open(path) as f:
        kept = [l for l in f.read().splitlines() if not l.startswith(groups)]
    with open(path, "w") as f:
        f.write("\n".join(kept + axes) + "\n")

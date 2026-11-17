"""Cut figures out of a green-screen sprite sheet (e.g. an AI-generated row of poses).

    figures(path) -> [(rgba_image, (x0, y0, x1, y1)), ...]   left to right

Keys out the green with a soft edge, removes green spill from that edge, then splits the sheet into
connected figures, so poses whose bounding boxes overlap (a kick reaching over the
next pose) still come apart. Specks smaller than min_area pixels are dropped.
"""
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


def figures(path, min_area=2000, threshold=128):
    rgba = key(Image.open(path))
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
    out = []
    for n, px in enumerate(comps, 1):
        if len(px) < min_area:
            continue
        xs = [p[0] for p in px]
        ys = [p[1] for p in px]
        box = (min(xs), min(ys), max(xs) + 1, max(ys) + 1)
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

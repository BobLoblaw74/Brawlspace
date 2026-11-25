"""Redraw warped cut-out frames with Gemini, keeping each frame's pose and placement.

Each frame is sent with source.png (character/style reference); Gemini returns the pose
redrawn on flat magenta, which is keyed out, then scaled and placed onto the original
frame's bounding box so axes and animation motion are unchanged.

Usage (repo root):
    python3 -I tools/fighters/tinker/gemini_redraw.py <out_dir> <frame> [<frame> ...]
    e.g. ... /tmp/out 0_0 0_1 0_2
Needs GEMINI_API_KEY.
"""
import base64
import io
import json
import os
import sys
import urllib.request

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
MODEL = "gemini-3-pro-image"
PROMPT = (
    "Image 1 is the character Tinker. Image 2 is a crude, distorted animation frame of him. "
    "Redraw image 2 as a clean, hand-drawn fighting-game sprite: exactly the same pose, limb "
    "positions, body proportions, framing and facing direction as image 2, but with the face, "
    "outfit, gadgets, colours and inked comic style of image 1, with no warping or smearing. "
    "Full body, nothing cropped. Background: flat solid magenta #FF00FF, no shadow, no floor, "
    "no text."
)


def b64png(im):
    buf = io.BytesIO()
    im.save(buf, "PNG")
    return base64.b64encode(buf.getvalue()).decode()


def on_white(im):
    bg = Image.new("RGBA", im.size, (255, 255, 255, 255))
    bg.alpha_composite(im.convert("RGBA"))
    return bg.convert("RGB")


def generate(src, frame):
    body = {
        "contents": [{"parts": [
            {"text": PROMPT},
            {"inline_data": {"mime_type": "image/png", "data": b64png(src)}},
            {"inline_data": {"mime_type": "image/png", "data": b64png(on_white(frame))}},
        ]}],
        "generationConfig": {"responseModalities": ["IMAGE"]},
    }
    req = urllib.request.Request(
        "https://generativelanguage.googleapis.com/v1beta/models/%s:generateContent" % MODEL,
        json.dumps(body).encode(),
        {"Content-Type": "application/json", "x-goog-api-key": os.environ["GEMINI_API_KEY"]},
    )
    with urllib.request.urlopen(req, timeout=300) as r:
        resp = json.load(r)
    for part in resp["candidates"][0]["content"]["parts"]:
        data = part.get("inlineData") or part.get("inline_data")
        if data:
            return Image.open(io.BytesIO(base64.b64decode(data["data"]))).convert("RGB")
    raise RuntimeError("no image in response: %s" % json.dumps(resp)[:500])


def key_magenta(im, solid=40, clear=110):
    """Alpha from magenta-ness min(r, b) - g; the soft edge has its magenta removed."""
    out = im.convert("RGBA")
    px = out.load()
    for y in range(out.height):
        for x in range(out.width):
            r, g, b, _ = px[x, y]
            m = min(r, b) - g
            if m <= solid:
                continue
            a = 0 if m >= clear else 255 * (clear - m) // (clear - solid)
            px[x, y] = (min(r, g + solid), g, min(b, g + solid), a)
    return out


def fit(new, old):
    """Scale the keyed figure to the old frame's bbox height, bottom-centre aligned."""
    new = new.crop(new.getchannel("A").point(lambda a: 255 if a > 128 else 0).getbbox())
    l, t, r, b = old.getchannel("A").getbbox()
    s = (b - t) / new.height
    new = new.resize((max(1, round(new.width * s)), b - t), Image.LANCZOS)
    out = Image.new("RGBA", old.size)
    out.alpha_composite(new, ((l + r - new.width) // 2, t))  # shortcut: may clip if wider than canvas
    return out


def main(out_dir, names):
    os.makedirs(out_dir, exist_ok=True)
    src = Image.open(os.path.join(HERE, "source.png")).convert("RGB")
    for name in names:
        old = Image.open(os.path.join(HERE, "art", name + ".png")).convert("RGBA")
        raw = generate(src, old)
        raw.save(os.path.join(out_dir, name + "_raw.png"))
        fit(key_magenta(raw), old).save(os.path.join(out_dir, name + ".png"))
        print(name, "ok", flush=True)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2:])

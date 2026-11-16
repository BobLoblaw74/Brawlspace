"""Render the Brawlspace title logo layers as transparent PNGs via headless Chrome.

Writes tools/logo/out/layer0.png .. layer3.png (699x257, same frame as the stock
Ikemen logo so the title screen positions/animations still line up):
  layer0 = "BRAWL" + impact emblem    layer1 = "SPACE"
  layer2 = shadow of layer0           layer3 = shadow of layer1
Then run tools/logo/patch_sff.py to put them into content/data/ikemen1/system.sff.
"""
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "out")
CHROME = os.environ.get("CHROME_BIN", "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome")
W, H = 699, 257
FONT = "font-family:'Avenir Next Condensed','Futura','Arial Black',sans-serif;font-weight:900;font-style:italic"

DEFS = """
<defs>
  <linearGradient id="chrome" x1="0" y1="0" x2="0" y2="1">
    <stop offset="0" stop-color="#ffffff"/><stop offset=".45" stop-color="#f1f3f8"/>
    <stop offset=".55" stop-color="#b9c0cf"/><stop offset="1" stop-color="#e9ecf3"/>
  </linearGradient>
  <linearGradient id="heat" x1="0" y1="0" x2="0" y2="1">
    <stop offset="0" stop-color="#ffd23f"/><stop offset=".5" stop-color="#ff7a1a"/>
    <stop offset="1" stop-color="#e8174a"/>
  </linearGradient>
  <radialGradient id="core" cx=".4" cy=".35" r=".75">
    <stop offset="0" stop-color="#ffb347"/><stop offset=".6" stop-color="#ff5a1f"/>
    <stop offset="1" stop-color="#b3122e"/>
  </radialGradient>
</defs>"""


def burst(cx, cy, r1, r2, n=10):
    import math
    pts = []
    for i in range(n * 2):
        r = r1 if i % 2 == 0 else r2
        a = math.pi * i / n - math.pi / 2
        pts.append("%.1f,%.1f" % (cx + r * math.cos(a), cy + r * math.sin(a)))
    return " ".join(pts)


def emblem(shadow):
    if shadow:
        return '<circle cx="100" cy="104" r="92" fill="#22285a"/>'
    return (
        '<circle cx="96" cy="98" r="92" fill="#1b1f3a"/>'
        '<circle cx="96" cy="98" r="84" fill="#ffffff"/>'
        '<circle cx="96" cy="98" r="74" fill="url(#core)"/>'
        '<polygon points="%s" fill="#fff7e0" stroke="#1b1f3a" stroke-width="4" stroke-linejoin="round"/>'
        % burst(96, 98, 58, 26)
    )


def word(text, x, y, size, fill, shadow, spacing):
    if shadow:
        return ('<text x="%d" y="%d" font-size="%d" letter-spacing="%d" style="%s" fill="#22285a" '
                'stroke="#22285a" stroke-width="18" stroke-linejoin="round">%s</text>'
                % (x + 6, y + 8, size, spacing, FONT, text))
    return ('<text x="%d" y="%d" font-size="%d" letter-spacing="%d" style="%s;paint-order:stroke" '
            'fill="url(#%s)" stroke="#1b1f3a" stroke-width="12" stroke-linejoin="round">%s</text>'
            % (x, y, size, spacing, FONT, fill, text))


LAYERS = {
    0: lambda: emblem(False) + word("BRAWL", 150, 152, 158, "chrome", False, 4),
    1: lambda: word("SPACE", 318, 242, 104, "heat", False, 6),
    2: lambda: emblem(True) + word("BRAWL", 150, 152, 158, "chrome", True, 4),
    3: lambda: word("SPACE", 318, 242, 104, "heat", True, 6),
}


def render(n):
    html = os.path.join(OUT, "layer%d.html" % n)
    png = os.path.join(OUT, "layer%d.png" % n)
    with open(html, "w") as f:
        f.write('<!doctype html><html><body style="margin:0;background:transparent">'
                '<svg xmlns="http://www.w3.org/2000/svg" width="%d" height="%d">%s%s</svg></body></html>'
                % (W, H, DEFS, LAYERS[n]()))
    profile = os.path.join(OUT, ".chrome-profile")
    subprocess.run([CHROME, "--headless=new", "--hide-scrollbars", "--force-device-scale-factor=1",
                    "--user-data-dir=" + profile, "--no-first-run", "--no-default-browser-check",
                    "--default-background-color=00000000", "--window-size=%d,%d" % (W, H),
                    "--screenshot=" + png, "file://" + html],
                   check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=60)
    print("rendered", png)


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    for n in (sys.argv[1:] or ["0", "1", "2", "3"]):
        render(int(n))

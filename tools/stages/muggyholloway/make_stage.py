"""Build the Muggy Holloway stage (see tools/stages/stagegen.py).

Usage (repo root):
    python3 -I tools/stages/muggyholloway/make_stage.py

An apartment-complex walkway at night in two depth layers, like KCAL News: the
building (doors, windows, the railing and the courtyard beyond) scrolls a little
slower, and the walkway floor moves with the fighters, with what stands on it: the
potted plants, the open stairwell and its railing, the boxes and the trash bag.
HotNight's home stage.

The stairwell's front edge is near the bottom of the picture, so the ground line is
set low (ground_y 400, zoffset 670): the fighters stand in front of the stairwell
instead of inside it, and the picture still reaches the bottom of the screen
(670 - 400 * 1.9 + 434 * 1.9 = 735 >= 720).
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
from stagegen import build  # noqa: E402


def fill(poly):
    return {"behind": "fill", "poly": poly}


CONFIG = {
    "id": "muggyholloway",
    "name": "Muggy Holloway",
    "source": os.path.join(HERE, "source.png"),
    "scale": 1.9,           # 1024x434 -> 1946x825
    "ground_y": 400,
    "zoffset": 670,
    "shadow_color": (20, 20, 40),
    "music": "sound/apartment_complex.ogg",
    "layers": [
        {"name": "Building", "delta": 0.95},
        {"name": "Walkway", "delta": 1.0, "polys": [
            # the walkway, back to the wall base, the far railing and the lockers
            {"behind": "keep", "poly": [(0, 410), (130, 355), (220, 345), (350, 300), (450, 255), (555, 230),
                                        (562, 308), (942, 308), (960, 330), (1024, 330), (1024, 434), (0, 434)]},
            fill([(0, 318), (40, 300), (80, 298), (105, 302), (138, 318), (138, 392), (100, 410), (45, 425),
                  (0, 428)]),                                                   # potted plants
            fill([(660, 262), (895, 262), (895, 412), (660, 412)]),             # stairwell and its railing
            fill([(910, 276), (958, 276), (958, 324), (910, 324)]),             # box by the railing
            fill([(958, 326), (1024, 322), (1024, 434), (958, 434)]),           # open box and trash bag
        ]},
    ],
}

if __name__ == "__main__":
    build(CONFIG)

"""Build the Drugstore Maze stage (see tools/stages/stagegen.py).

Usage (repo root):
    python3 -I tools/stages/drugstoremaze/make_stage.py

A neighborhood drugstore in two depth layers, like KCAL News: the store (wall
shelves, aisles, the pharmacy counter, the doors) scrolls a little slower, and the
tiled floor moves with the fighters, with the two checkouts in front standing on
it (left: register, candy rack and basket stand; right: display rack, register and
the basket stack). Bibble Babble's home stage.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
from stagegen import build  # noqa: E402


def fill(poly):
    return {"behind": "fill", "poly": poly}


CONFIG = {
    "id": "drugstoremaze",
    "name": "Drugstore Maze",
    "source": os.path.join(HERE, "source.png"),
    "scale": 1.9,           # 1024x434 -> 1946x825
    "ground_y": 380,        # the tiles in front of the aisles
    "shadow_color": (40, 40, 50),
    "layers": [
        {"name": "Store", "delta": 0.95},
        {"name": "Floor", "delta": 1.0, "polys": [
            # the tiles, back to the shelf bases, the pharmacy counter and the doors
            {"behind": "keep", "poly": [(0, 380), (40, 372), (60, 330), (120, 322), (270, 318), (350, 318),
                                        (360, 322), (450, 320), (455, 282), (495, 278), (750, 276), (775, 300),
                                        (820, 306), (870, 300), (1024, 300), (1024, 434), (0, 434)]},
            # left checkout: counter, register, candy rack, basket stand
            fill([(35, 312), (75, 302), (76, 278), (170, 278), (172, 236), (200, 236), (205, 270), (222, 280),
                  (222, 300), (260, 306), (262, 368), (205, 368), (203, 400), (125, 410), (40, 405),
                  (35, 380)]),
            # right checkout: display rack with hand-sanitizer bottles, register, basket stack
            fill([(850, 300), (868, 282), (872, 270), (905, 270), (912, 295), (927, 297), (930, 300),
                  (965, 298), (965, 232), (1012, 232), (1024, 240), (1024, 434), (880, 434), (880, 420), (850, 418)]),
        ]},
    ],
}

if __name__ == "__main__":
    build(CONFIG)

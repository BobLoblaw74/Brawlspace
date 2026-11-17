"""Build the Indio Dates Paradise stage (see tools/stages/stagegen.py).

Usage (repo root):
    python3 -I tools/stages/indiodates/make_stage.py

An indoor shop: the floor must move with the fighters (delta 1.0) or their
feet would skate, so the fixtures share the floor's layer, the back wall moves
a little slower, and the corner trash cans move faster as a foreground.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
from stagegen import build  # noqa: E402

CONFIG = {
    "id": "indiodates",
    "name": "Indio Dates Paradise",
    "source": os.path.join(HERE, "source.jpg"),
    "scale": 1.9,           # 1024x434 -> 1946x825
    "ground_y": 370,        # front of the shop floor (lower would leave a gap under the image)
    "shadow_color": (60, 20, 40),
    "layers": [
        # far: back wall, window, jar shelves, the date-shake poster, ceiling
        {"name": "Wall", "delta": 0.92},
        # mid: the floor and everything standing on it
        {"name": "Floor", "delta": 1.0, "polys": [
            {"behind": "keep", "poly": [(0, 300), (1024, 300), (1024, 434), (0, 434)]},          # floor
            {"behind": "fill", "poly": [(118, 205), (175, 200), (200, 160), (240, 175), (300, 185),
                                        (395, 200), (395, 300), (118, 300)]},                    # display case
            {"behind": "fill", "poly": [(64, 150), (92, 147), (108, 165), (126, 205), (124, 300), (54, 300),
                                        (52, 205), (66, 172)]},                                   # lollipop tree
            {"behind": "fill", "poly": [(365, 168), (420, 165), (470, 175), (530, 175), (532, 300),
                                        (395, 300)]},                                             # register counter
            {"behind": "fill", "poly": [(600, 158), (634, 158), (650, 200), (652, 300), (590, 300),
                                        (588, 200)]},                                             # candy tier stand
            {"behind": "fill", "poly": [(658, 250), (760, 245), (810, 255), (900, 258), (960, 255),
                                        (1000, 265), (1000, 300), (658, 300)]},                   # crates and cart
        ]},
        # front: the two trash cans in the near corners
        {"name": "Foreground", "delta": 1.1, "polys": [
            {"behind": "fill", "poly": [(0, 324), (64, 324), (66, 434), (0, 434)]},
            {"behind": "fill", "poly": [(960, 324), (1024, 324), (1024, 434), (958, 434)]},
        ]},
    ],
    "elements": [
        # signs hanging from the ceiling sway a little, out of step
        {"name": "Candies Sign", "layer": 0, "motion": "sway", "amp": 1.2, "period": 210,
         "pivot": (255, 0), "poly": [(178, 0), (332, 0), (332, 72), (178, 72)]},
        {"name": "Fudge Sign", "layer": 0, "motion": "sway", "amp": 1.5, "period": 190, "phase": 0.4,
         "pivot": (416, 18), "poly": [(352, 18), (480, 18), (480, 96), (352, 96)]},
        {"name": "Soda Fountain Sign", "layer": 0, "motion": "sway", "amp": 0.8, "period": 240, "phase": 0.7,
         "pivot": (705, 0), "poly": [(598, 0), (812, 0), (812, 68), (598, 68)]},
        {"name": "Open Sign", "layer": 0, "motion": "sway", "amp": 1.5, "period": 170, "phase": 0.2,
         "pivot": (285, 85), "poly": [(242, 82), (328, 82), (328, 134), (242, 134)]},
    ],
}

if __name__ == "__main__":
    build(CONFIG)

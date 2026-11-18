"""Build the Cat Pad stage (see tools/stages/stagegen.py).

Usage (repo root):
    python3 -I tools/stages/catpad/make_stage.py

Three depth layers: the room with its windows (slowest), the floor with the
furniture that stands on it (moves with the fighters), and the corner plants
(foreground).
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
from stagegen import build  # noqa: E402


def fill(poly):
    return {"behind": "fill", "poly": poly}


CONFIG = {
    "id": "catpad",
    "name": "Cat Pad",
    "source": os.path.join(HERE, "source.png"),
    "scale": 1.9,           # 1024x434 -> 1946x825
    "ground_y": 365,        # on the rug
    "shadow_color": (60, 30, 10),
    "music": "sound/velvet_prowl.ogg",  # "Velvet Prowl"
    "layers": [
        # room: walls, fireplace, wallpaper, and the windows with the yard beyond.
        # (The yard stays on this layer: a separate yard layer exposed blurred
        # strips behind every window frame as the layers slid apart.)
        {"name": "Room", "delta": 0.9},
        # floor: the floorboards, rug, toys, and the furniture standing on the floor
        {"name": "Floor", "delta": 1.0, "polys": [
            {"behind": "keep", "poly": [(0, 290), (1024, 290), (1024, 434), (0, 434)]},
            fill([(20, 8), (232, 8), (234, 300), (20, 300)]),                                  # left cat tower + cabinet
            fill([(712, 8), (762, 8), (760, 40), (752, 95), (800, 100), (800, 300), (690, 300),
                  (690, 95), (730, 90), (735, 45)]),                                           # tall cat tree
            fill([(768, 238), (920, 248), (920, 352), (768, 342)]),                            # tunnel cage
        ]},
        # foreground: corner plants with the food jars
        {"name": "Plants", "delta": 1.1, "polys": [
            fill([(0, 205), (70, 205), (110, 260), (138, 340), (138, 434), (0, 434)]),
            fill([(900, 215), (1024, 215), (1024, 434), (900, 434)]),
        ]},
    ],
    "elements": [
        # pendant lamps over the fireplace swing gently from the ceiling
        {"name": "Lamp Left", "layer": 0, "motion": "sway", "amp": 2.0, "period": 200,
         "pivot": (372, 4), "poly": [(360, 0), (386, 0), (388, 104), (358, 104)]},
        {"name": "Lamp Middle", "layer": 0, "motion": "sway", "amp": 1.6, "period": 230, "phase": 0.4,
         "pivot": (393, 10), "poly": [(386, 10), (402, 10), (406, 140), (380, 140)]},
        {"name": "Lamp Right", "layer": 0, "motion": "sway", "amp": 1.8, "period": 215, "phase": 0.7,
         "pivot": (414, 4), "poly": [(404, 0), (428, 0), (432, 112), (400, 112)]},
        # palm outside the right window sways in the breeze
        {"name": "Palm", "layer": 0, "motion": "sway", "amp": 2.0, "period": 260,
         "pivot": (922, 160), "poly": [(882, 82), (958, 82), (958, 160), (882, 160)]},
    ],
}

if __name__ == "__main__":
    build(CONFIG)

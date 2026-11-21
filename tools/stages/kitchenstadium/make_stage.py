"""Build the Kitchen Stadium stage (see tools/stages/stagegen.py).

Usage (repo root):
    python3 -I tools/stages/kitchenstadium/make_stage.py

A TV cooking-show set in two depth layers, like KCAL News: the studio (brick walls,
the curved kitchen platform with the Red Team and Blue Team kitchens, the bleachers)
scrolls a little slower, and the concrete floor in front of the platform moves with
the fighters, with the three studio cameras standing on it. The neon sign, the team
signs and the scoreboard pulse. Worst Cook's home stage.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
from stagegen import build  # noqa: E402


def fill(poly):
    return {"behind": "fill", "poly": poly}


CONFIG = {
    "id": "kitchenstadium",
    "name": "Kitchen Stadium",
    "source": os.path.join(HERE, "source.png"),
    "scale": 1.9,           # 1024x434 -> 1946x825
    "ground_y": 365,        # concrete floor in front of the platform
    "shadow_color": (25, 22, 40),
    "layers": [
        {"name": "Studio", "delta": 0.95},
        {"name": "Floor", "delta": 1.0, "polys": [
            # concrete floor, up to the platform's curved front edge and the bleacher railing
            {"behind": "keep", "poly": [(0, 292), (172, 292), (180, 312), (200, 324), (300, 327), (400, 318),
                                        (500, 307), (560, 306), (640, 312), (712, 318), (790, 312), (835, 302),
                                        (870, 312), (940, 335), (1024, 345), (1024, 434), (0, 434)]},
            # studio cameras, traced so the wall and kitchen behind them stay put
            fill([(12, 190), (90, 190), (64, 246), (48, 250), (47, 300), (28, 300), (30, 262), (16, 245),
                  (14, 215)]),                                                               # tripod camera
            fill([(98, 218), (136, 218), (138, 228), (197, 229), (197, 248), (182, 256), (178, 290),
                  (168, 300), (128, 300), (126, 290), (110, 280), (110, 250), (98, 245)]),   # CAM 1
            fill([(806, 245), (858, 244), (858, 228), (884, 228), (884, 246), (890, 255), (886, 282),
                  (866, 286), (866, 312), (836, 312), (836, 285), (808, 282)]),              # CAM 2
        ]},
    ],
    # neon: the KITCHEN STADIUM sign, the two team signs and the scoreboard
    "glow": {"layer": 0, "min_y": 15, "max_y": 165, "boost": 1.6, "pulse": (90, 150, 180, 150),
             "polys": [[(395, 38), (636, 38), (636, 162), (395, 162)],
                       [(198, 104), (324, 104), (324, 160), (198, 160)],
                       [(688, 104), (812, 104), (812, 160), (688, 160)],
                       [(682, 16), (830, 16), (830, 114), (682, 114)]]},
}

if __name__ == "__main__":
    build(CONFIG)

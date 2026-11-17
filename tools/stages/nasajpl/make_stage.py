"""Build the NASA JPL stage (see tools/stages/stagegen.py).

Usage (repo root):
    python3 -I tools/stages/nasajpl/make_stage.py
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
from stagegen import build  # noqa: E402

CONFIG = {
    "id": "nasajpl",
    "name": "NASA JPL",
    "source": os.path.join(HERE, "source.png"),
    "scale": 1.9,           # 1024x434 -> 1946x825
    "ground_y": 360,        # middle of the plaza
    "shadow_color": (20, 20, 50),
    "layers": [
        # far: sunset sky and the San Gabriel mountains (the whole image)
        {"name": "Far", "delta": 0.5},
        # mid: JPL hangar, Mission Control, tanks, dishes, rovers, utility poles.
        # Behind them is sky and mountain, so fill it in when the layers slide apart.
        {"name": "Mid", "delta": 0.8, "polys": [
            {"behind": "fill", "poly": [
                (0, 120), (60, 125), (110, 118), (160, 120), (170, 155), (225, 155), (232, 95), (245, 95),
                (250, 110), (282, 100), (500, 100), (505, 135), (540, 135), (545, 115), (575, 115),
                (578, 145), (600, 140), (615, 110), (622, 80), (640, 70), (700, 65), (740, 75), (770, 90),
                (780, 110), (830, 108), (845, 120), (850, 145), (870, 135), (880, 125), (925, 135),
                (940, 110), (1024, 105), (1024, 300), (0, 300)]},
            {"behind": "fill", "poly": [(38, 10), (62, 10), (62, 300), (38, 300)]},          # left utility pole
            {"behind": "fill", "poly": [(930, 5), (1000, 5), (1000, 60), (978, 60), (978, 300),
                                        (958, 300), (958, 60), (930, 60)]},                  # floodlight mast
            {"behind": "fill", "poly": [(835, 55), (875, 55), (870, 150), (840, 150)]},       # cell tower
        ]},
        # front: the plaza with the painted JPL / NASA, barriers, railings, crates, fences
        {"name": "Front", "delta": 1.0, "polys": [
            {"behind": "keep", "poly": [(0, 282), (1024, 282), (1024, 434), (0, 434)]},
            {"behind": "keep", "poly": [(0, 225), (42, 225), (42, 300), (0, 300)]},           # left fence
            {"behind": "keep", "poly": [(938, 225), (1024, 225), (1024, 300), (938, 300)]},   # right fence
        ]},
    ],
    "elements": [
        # rooftop dishes on Mission Control slowly pan, out of step with each other
        {"name": "Roof Dish 1", "layer": 1, "motion": "sway", "amp": 3.5, "period": 220,
         "pivot": (645, 106), "poly": [(620, 70), (668, 70), (668, 110), (620, 110)]},
        {"name": "Roof Dish 2", "layer": 1, "motion": "sway", "amp": 3.0, "period": 260, "phase": 0.33,
         "pivot": (690, 102), "poly": [(666, 62), (716, 62), (716, 106), (666, 106)]},
        {"name": "Roof Dish 3", "layer": 1, "motion": "sway", "amp": 3.5, "period": 240, "phase": 0.66,
         "pivot": (748, 102), "poly": [(728, 76), (768, 76), (768, 106), (728, 106)]},
        # big dish beside Mission Control and the dish on the left yard
        {"name": "Side Dish", "layer": 1, "motion": "sway", "amp": 2.5, "period": 300, "phase": 0.2,
         "pivot": (888, 168), "poly": [(864, 120), (924, 120), (924, 172), (864, 172)]},
        {"name": "Yard Dish", "layer": 1, "motion": "sway", "amp": 3.0, "period": 280, "phase": 0.5,
         "pivot": (103, 228), "poly": [(80, 188), (130, 188), (130, 232), (80, 232)]},
    ],
}

if __name__ == "__main__":
    build(CONFIG)

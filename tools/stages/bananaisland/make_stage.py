"""Build the Banana Island stage (see tools/stages/stagegen.py).

Usage (repo root):
    python3 -I tools/stages/bananaisland/make_stage.py
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
from stagegen import build  # noqa: E402

CONFIG = {
    "id": "bananaisland",
    "name": "Banana Island",
    "source": os.path.join(HERE, "source.png"),
    "scale": 1.9,           # 1024x434 -> 1946x825
    "ground_y": 345,        # middle of the dirt clearing
    "shadow_color": (40, 20, 10),
    "layers": [
        # far: sky, bridge, skyline, river, distant shore (the whole image)
        {"name": "Far", "delta": 0.55},
        # mid: shack, banana grove, shrine, gazebo with hammocks, houseboats
        # (the top edge hugs the treetops so the bridge stays entirely on the far layer)
        {"name": "Mid", "delta": 0.8, "polys": [
            # shack + banana grove: foliage, so farther layers keep the original pixels behind it
            {"behind": "keep", "poly": [
                (20, 300), (20, 130), (40, 50), (90, 20), (150, 15), (200, 30), (222, 80), (232, 140),
                (280, 125), (320, 110), (370, 100), (420, 100), (450, 120), (480, 140), (505, 160),
                (540, 195), (540, 300)]},
            # gazebo, houseboats, near shore: over smooth river and sky, so fill behind them
            {"behind": "fill", "poly": [
                (540, 195), (600, 178), (700, 185), (780, 200), (830, 205), (880, 200), (880, 300),
                (540, 300)]},
        ]},
        # front: the dirt clearing, fences, benches, jars and the big side banana trees
        {"name": "Front", "delta": 1.0, "polys": [
            {"behind": "keep", "poly": [(0, 292), (1024, 292), (1024, 434), (0, 434)]},
            {"behind": "keep", "poly": [(0, 10), (60, 10), (90, 60), (165, 100), (120, 230), (55, 300), (0, 300)]},
            {"behind": "keep", "poly": [(1024, 0), (800, 0), (780, 40), (880, 80), (905, 180), (900, 300),
                                        (1024, 300)]},
        ]},
    ],
    "elements": [
        # banana bunch + flower hanging from the right tree: slow sway from the stalk
        {"name": "Banana Bunch", "layer": 2, "motion": "sway", "amp": 3.0, "period": 150,
         "pivot": (940, 62), "poly": [(918, 62), (962, 62), (968, 120), (955, 165), (930, 165), (915, 120)]},
        # canopy longboat on the river: gentle bob
        {"name": "Longboat", "layer": 1, "motion": "bob", "amp": 1.5, "period": 110,
         "poly": [(832, 240), (905, 238), (910, 275), (828, 278)]},
        # small rowboat with a fisherman: bob, out of phase with the longboat
        {"name": "Rowboat", "layer": 1, "motion": "bob", "amp": 1.2, "period": 95, "phase": 0.35,
         "poly": [(784, 228), (838, 228), (838, 252), (784, 252)]},
        # hammocks under the gazebo: swing a little from their tie points
        {"name": "Hammock Left", "layer": 1, "motion": "sway", "amp": 2.5, "period": 130,
         "pivot": (637, 238), "poly": [(612, 236), (662, 236), (662, 266), (612, 266)]},
        {"name": "Hammock Right", "layer": 1, "motion": "sway", "amp": 2.0, "period": 140, "phase": 0.5,
         "pivot": (735, 240), "poly": [(688, 238), (788, 238), (788, 272), (688, 272)]},
    ],
}

if __name__ == "__main__":
    build(CONFIG)

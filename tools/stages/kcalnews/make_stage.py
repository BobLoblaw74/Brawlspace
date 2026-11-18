"""Build the KCAL News stage (see tools/stages/stagegen.py).

Usage (repo root):
    python3 -I tools/stages/kcalnews/make_stage.py

A TV news studio in two depth layers: the studio with its video wall, control-room
windows and green screen (slower), and the floor with everything standing on it, the
anchor desk on its riser, the studio cameras and the tripod monitors (moves with the
fighters). The video wall and its light strips pulse softly.

The cameras were a third, nearer layer at first, but sliding them against the floor
uncovered the blurred fill behind them as grey smears beside every camera and tripod,
so they move with the floor instead. The studio's parallax is gentle (0.95) for the
same reason: what slides apart uncovers less fill behind the desk and camera tops.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
from stagegen import build  # noqa: E402


def fill(poly):
    return {"behind": "fill", "poly": poly}


CONFIG = {
    "id": "kcalnews",
    "name": "KCAL News",
    "source": os.path.join(HERE, "source.png"),
    "scale": 1.9,           # 1024x434 -> 1946x825
    "ground_y": 372,        # studio floor, in front of the desk riser
    "shadow_color": (20, 25, 50),
    "music": "sound/prime_time_takedown.ogg",  # "Prime Time Takedown"
    "layers": [
        # studio: lighting rig, video wall, control-room windows, green screen, server rack
        {"name": "Studio", "delta": 0.95},
        # floor and everything standing on it: the anchor desk on its riser, the studio
        # cameras on their pedestals and the two tripod monitors
        {"name": "Floor", "delta": 1.0, "polys": [
            {"behind": "keep", "poly": [(0, 292), (290, 292), (300, 300), (720, 300), (830, 320),
                                        (1024, 335), (1024, 434), (0, 434)]},
            # desk + riser, traced around the chairs, laptops and mics on top so none of the
            # video wall behind them comes along (it would tear from the wall when panning)
            fill([(336, 247), (352, 240), (353, 217), (384, 217), (386, 236),             # left chair
                  (392, 222), (431, 222), (434, 238), (442, 218), (473, 218), (476, 236),  # laptops
                  (487, 236), (488, 214), (503, 214), (505, 236),                          # mic
                  (521, 233), (522, 216), (551, 216), (552, 233),                          # middle chair
                  (579, 236), (580, 216), (598, 216), (600, 236),                          # mic
                  (641, 236), (642, 216), (676, 216), (678, 240),                          # right chair
                  (690, 247), (700, 258), (712, 290), (730, 297), (730, 320), (712, 334),
                  (300, 334), (296, 318), (298, 297), (330, 285), (336, 258)]),
            # cameras and monitors, traced tightly so no window or green screen behind
            # them comes along
            fill([(47, 195), (80, 195), (82, 210), (110, 207), (167, 207), (160, 247), (158, 288),
                  (140, 290), (140, 300), (113, 302), (112, 340), (160, 352), (162, 398), (140, 412),
                  (60, 412), (48, 398), (50, 352), (88, 340), (88, 302), (68, 298), (62, 284),
                  (42, 284), (42, 264), (65, 262), (63, 240), (60, 215), (47, 213)]),        # CAM 1
            fill([(183, 220), (268, 220), (268, 272), (264, 300), (217, 300), (216, 350), (232, 372),
                  (265, 408), (256, 412), (212, 370), (205, 370), (192, 412), (184, 410), (203, 352),
                  (206, 272), (183, 272)]),                                                  # left monitor
            fill([(757, 220), (840, 220), (840, 272), (820, 275), (818, 305), (817, 352), (835, 380),
                  (852, 410), (842, 414), (815, 375), (810, 375), (775, 414), (762, 412), (805, 352),
                  (808, 305), (763, 305), (760, 272)]),                                      # right monitor
            fill([(882, 213), (927, 213), (940, 218), (972, 215), (975, 200), (1007, 200), (1007, 222),
                  (992, 228), (990, 262), (1013, 272), (1013, 292), (987, 292), (987, 310), (970, 312),
                  (970, 347), (1003, 358), (1005, 400), (992, 414), (900, 414), (892, 400), (895, 358),
                  (938, 347), (938, 312), (917, 308), (917, 297), (887, 297), (887, 262),
                  (882, 260)]),                                                              # CAM 2
        ]},
    ],
    # the video wall and the cyan light strips around it pulse; limited to that region so
    # the (bright, saturated) green screen doesn't
    "glow": {"layer": 0, "min_y": 95, "max_y": 250, "boost": 1.6, "pulse": (90, 150, 180, 150),
             "polys": [[(230, 95), (795, 95), (795, 250), (230, 250)]]},
}

if __name__ == "__main__":
    build(CONFIG)

"""Build the SluttyWood stage (see tools/stages/stagegen.py).

Usage (repo root):
    python3 -I tools/stages/sluttywood/make_stage.py

One flat layer (splitting it would break the lamp posts and palm trees),
plus a softly pulsing glow over the neon signs, string lights and lamps.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
from stagegen import build  # noqa: E402

CONFIG = {
    "id": "sluttywood",
    "name": "SluttyWood",
    "source": os.path.join(HERE, "source.jpg"),
    "scale": 1.9,           # 1024x434 -> 1946x825
    "ground_y": 375,        # asphalt just above the near rainbow crosswalk
    "shadow_color": (30, 0, 40),
    "music": "sound/stiletto_command.ogg",  # "Stiletto Command"
    "layers": [{"name": "Street", "delta": 1.0}],
    # glow only below the skyline (the sunset sky is bright too) and above the crosswalks
    "glow": {"layer": 0, "min_y": 135, "max_y": 325, "boost": 1.7, "pulse": (110, 160, 190, 160)},
}

if __name__ == "__main__":
    build(CONFIG)

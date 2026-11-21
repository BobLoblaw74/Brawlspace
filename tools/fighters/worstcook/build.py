"""Build Worst Cook into content/chars/worstcook (see tools/fighters/assemble.py).

Usage (repo root):
    python3 -I tools/fighters/worstcook/build.py [--frames]

  --frames   regenerate art/ from source.png and the sheets first (~1 min).
             Without it the existing art/ is packed as-is.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
from assemble import assemble  # noqa: E402

assemble(
    "worstcook", "Worst Cook", HERE,
    projectile="Burnt Pancake",
    stats=[(r"(?m)^life = 1000", "life = 1050"),
           (r"(?m)^walk\.fwd  = 9\.6", "walk.fwd  = 9.0"),
           (r"(?m)^walk\.back = -8\.8", "walk.back = -8.2")],
    quotes=["Dinner is served. Well, it was served at you.",
            "Health inspector? Never heard of him.",
            "Seasoned with defeat. Your defeat.",
            "Raw on the inside, like your technique.",
            "Kitchen's closed. You're the one who got burnt.",
            "Send it back? Nobody sends it back."],
    movelist="""<#f0f000>:Throws:</>
Kitchen Toss							[_B/_F]_+^Y

<#f0f000>:Special Moves:</>
Burnt Pancake_EX						_QDF^P
Floury Uppercut_EX						_DSF^P
Dish Towel Swat_EX						_QDB^P
Shoulder Charge_EX						_QDF^K
Boot Knee_EX							_F_F^K

<#f0f000>:Super Moves:</>
Kitchen Nightmare <#bebebe>(1000)</>	_QDF_QDF^P
Order Up Uppercut <#bebebe>(1000)</>	_QDB_QDB^P
""",
    argv=sys.argv,
)

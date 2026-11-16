"""Build Tinker into content/chars/tinker (see tools/fighters/assemble.py).

Usage (repo root):
    python3 -I tools/fighters/tinker/build.py [--frames]

  --frames   regenerate art/ from source.png first (~1 min). Without it the
             existing art/ is packed as-is, keeping hand-drawn replacements.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
from assemble import assemble  # noqa: E402

assemble(
    "tinker", "Tinker", HERE,
    projectile="Radar Pulse",
    stats=[(r"(?m)^life = 1000", "life = 950"),
           (r"(?m)^defence = 100", "defence = 105"),
           (r"(?m)^walk\.fwd  = 9\.6", "walk.fwd  = 8.8"),
           (r"(?m)^walk\.back = -8\.8", "walk.back = -8.0")],
    quotes=["Signal acquired. Opponent... neutralized.",
            "I checked the specs. You were never going to win.",
            "Everything's fixable. Except that fighting style.",
            "Pocket full of tools, and I only needed one.",
            "Radar never lies. You telegraphed every move.",
            "Hold still, I'm recalibrating your attitude."],
    movelist="""<#f0f000>:Throws:</>
Toolbelt Toss							[_B/_F]_+^Y

<#f0f000>:Special Moves:</>
Radar Pulse_EX							_QDF^P
Antenna Uppercut_EX						_DSF^P
Wrench Swing_EX							_QDB^P
Shoulder Charge_EX						_QDF^K
Boot Knee_EX							_F_F^K

<#f0f000>:Super Moves:</>
Overclock Barrage <#bebebe>(1000)</>	_QDF_QDF^P
Satellite Uppercut <#bebebe>(1000)</>	_QDB_QDB^P
""",
    argv=sys.argv,
)

"""Build GrapeMan into content/chars/grapeman (see tools/fighters/assemble.py).

Usage (repo root):
    python3 -I tools/fighters/grapeman/build.py [--frames]

  --frames   regenerate art/ from source.png first (~1 min). Without it the
             existing art/ is packed as-is, keeping hand-drawn replacements.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
from assemble import assemble  # noqa: E402

assemble(
    "grapeman", "GrapeMan", HERE,
    projectile="Grape Shot",
    stats=[(r"(?m)^life = 1000", "life = 1050"),
           (r"(?m)^attack = 100", "attack = 95"),
           (r"(?m)^jump\.neu = 0,-33\.6", "jump.neu = 0,-36.0")],
    quotes=["You've been crushed. Like a grape. Because I'm a grape.",
            "Sour grapes? I'd be sour too.",
            "That was a vine-tage beatdown.",
            "Raisin the bar, one fight at a time.",
            "I heard it through the grapevine: you lose.",
            "Stay fresh. Don't end up a raisin."],
    movelist="""<#f0f000>:Throws:</>
Vine Toss								[_B/_F]_+^Y

<#f0f000>:Special Moves:</>
Grape Shot_EX							_QDF^P
Vine Uppercut_EX						_DSF^P
Bunch Blow_EX							_QDB^P
Rolling Raisin_EX						_QDF^K
Stomping Knee_EX						_F_F^K

<#f0f000>:Super Moves:</>
Harvest Barrage <#bebebe>(1000)</>		_QDF_QDF^P
Vineyard Uppercut <#bebebe>(1000)</>	_QDB_QDB^P
""",
    argv=sys.argv,
)

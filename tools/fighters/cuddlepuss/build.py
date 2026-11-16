"""Build CuddlePuss into content/chars/cuddlepuss (see tools/fighters/assemble.py).

Usage (repo root):
    python3 -I tools/fighters/cuddlepuss/build.py [--frames]

  --frames   regenerate art/ from source.png first (~1 min). Without it the
             existing art/ is packed as-is, keeping hand-drawn replacements.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
from assemble import assemble  # noqa: E402

assemble(
    "cuddlepuss", "CuddlePuss", HERE,
    projectile="Hairball",
    stats=[(r"(?m)^life = 1000", "life = 1100"),
           (r"(?m)^attack = 100", "attack = 105"),
           (r"(?m)^walk\.fwd  = 9\.6", "walk.fwd  = 8.4"),
           (r"(?m)^walk\.back = -8\.8", "walk.back = -7.6")],
    quotes=["You've got to be kitten me. That was it?",
            "I always land on my feet. You landed on your face.",
            "Purr-fectly executed.",
            "Nine lives, and I didn't even need the second one.",
            "Don't make me cough up another one.",
            "Curiosity didn't kill this cat. It beat you up."],
    movelist="""<#f0f000>:Throws:</>
Scruff Toss								[_B/_F]_+^Y

<#f0f000>:Special Moves:</>
Hairball_EX								_QDF^P
Scratch Fever_EX						_DSF^P
Paw Swipe_EX							_QDB^P
Pounce_EX								_QDF^K
Kitty Knee_EX							_F_F^K

<#f0f000>:Super Moves:</>
Nine Lives Barrage <#bebebe>(1000)</>	_QDF_QDF^P
Catastrophe Uppercut <#bebebe>(1000)</>	_QDB_QDB^P
""",
    argv=sys.argv,
)

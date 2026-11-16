"""Build Juanana into content/chars/juanana (see tools/fighters/assemble.py).

Usage (repo root):
    python3 -I tools/fighters/juanana/build.py [--frames]

  --frames   regenerate art/ from source.png first (~1 min). Without it the
             existing art/ is packed as-is, keeping hand-drawn replacements.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
from assemble import assemble, sub1  # noqa: E402

PEEL_ENTRIES = """;---------------------------------------------------------------------------
;Banana Peel - drop it just ahead (one on screen at a time)
[State -1, Banana Peel Drop]
type = ChangeState
value = 1600
triggerall = command = "QCB_a"
triggerall = NumProjID(1600) = 0
trigger1 = var(1) ;Use combo condition (above)

;---------------------------------------------------------------------------
;Banana Peel - slide it far across the floor
[State -1, Banana Peel Slide]
type = ChangeState
value = 1610
triggerall = command = "QCB_b"
triggerall = NumProjID(1600) = 0
trigger1 = var(1) ;Use combo condition (above)

"""


def cmd_hook(cmd):
    # inputs for the peel: QCB + A / B
    cmd = sub1(r'\[Command\]\s*\nname = "FF_ab"',
               '[Command]\nname = "QCB_a"\ncommand = ~D, DB, B, a\n\n'
               '[Command]\nname = "QCB_b"\ncommand = ~D, DB, B, b\n\n'
               '[Command]\nname = "FF_ab"', cmd)
    # QCF,QCF+P super -> Rave Barrage
    cmd = sub1(r"(\[State -1, Triple Kung Fu Palm\]\s*\ntype = ChangeState\s*\nvalue = )3000", r"\g<1>3100", cmd)
    cmd = cmd.replace("[State -1, Triple Kung Fu Palm]", "[State -1, Rave Barrage]")
    cmd = cmd.replace("trigger2 = stateno != [3000,3050)", "trigger2 = stateno != [3100,3150)")
    # peel entries go right before the blocking entries
    idx = cmd.index("[State -1, High Kung Fu Blocking High]")
    idx = cmd.rindex(";---", 0, idx)
    return cmd[:idx] + PEEL_ENTRIES + cmd[idx:]


assemble(
    "juanana", "Juanana", HERE,
    projectile="Glow Stick Toss",
    stats=[(r"(?m)^walk\.fwd  = 9\.6", "walk.fwd  = 10.4"),
           (r"(?m)^walk\.back = -8\.8", "walk.back = -9.6"),
           (r"(?m)^run\.fwd  = 18\.4, 0", "run.fwd  = 20.8, 0")],
    quotes=["Don't hate me 'cause I'm a-peel-ing.",
            "You just got split. Banana style.",
            "Lights out. Glow sticks on.",
            "Watch your step next time. Seriously.",
            "Top banana. Bottom rung. You know which is which.",
            "This party doesn't stop. You did, though."],
    movelist="""<#f0f000>:Throws:</>
Bunch Toss								[_B/_F]_+^Y

<#f0f000>:Special Moves:</>
Glow Stick Toss_EX						_QDF^P
Banana Peel (drop)						_QDB^A
Banana Peel (slide)						_QDB^B
Electro Uppercut_EX						_DSF^P
Peel Slap_EX							_QDB^P
Split Rush_EX							_QDF^K
Bunch Knee_EX							_F_F^K

<#f0f000>:Super Moves:</>
Rave Barrage <#bebebe>(1000)</>			_QDF_QDF^P
Banana Split <#bebebe>(1000)</>			_QDB_QDB^P
""",
    argv=sys.argv,
    cmd_hook=cmd_hook,
)

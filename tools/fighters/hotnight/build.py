"""Build HotNight into content/chars/hotnight (see tools/fighters/assemble.py).

Usage (repo root):
    python3 -I tools/fighters/hotnight/build.py [--frames]

  --frames   regenerate art/ from source.png first (~1 min). Without it the
             existing art/ is packed as-is, keeping hand-drawn replacements.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
from assemble import assemble, sub1  # noqa: E402

EXTRA_ENTRIES = """;---------------------------------------------------------------------------
;Hydrate - only from neutral, and only when hurt
[State -1, Hydrate]
type = ChangeState
value = 1600
triggerall = command = "QCB_a"
triggerall = life < lifemax
trigger1 = statetype = S
trigger1 = ctrl

;---------------------------------------------------------------------------
;Tote Bag Swing
[State -1, Tote Bag Swing]
type = ChangeState
value = 1610
triggerall = command = "QCB_b"
trigger1 = var(1) ;Use combo condition (above)

"""


def cmd_hook(cmd):
    cmd = sub1(r'\[Command\]\s*\nname = "FF_ab"',
               '[Command]\nname = "QCB_a"\ncommand = ~D, DB, B, a\n\n'
               '[Command]\nname = "QCB_b"\ncommand = ~D, DB, B, b\n\n'
               '[Command]\nname = "FF_ab"', cmd)
    cmd = sub1(r"(\[State -1, Triple Kung Fu Palm\]\s*\ntype = ChangeState\s*\nvalue = )3000", r"\g<1>3100", cmd)
    cmd = cmd.replace("[State -1, Triple Kung Fu Palm]", "[State -1, Bulk Buy Barrage]")
    cmd = cmd.replace("trigger2 = stateno != [3000,3050)", "trigger2 = stateno != [3100,3150)")
    idx = cmd.index("[State -1, High Kung Fu Blocking High]")
    idx = cmd.rindex(";---", 0, idx)
    return cmd[:idx] + EXTRA_ENTRIES + cmd[idx:]


assemble(
    "hotnight", "HotNight", HERE,
    projectile="Water Bottle Toss",
    stats=[(r"(?m)^attack = 100", "attack = 108"),
           (r"(?m)^defence = 100", "defence = 95")],
    quotes=["Stay hydrated, honey. You clearly didn't.",
            "Healthy living, for less. Less of you, mostly.",
            "That's what you get for skipping your eight glasses.",
            "I didn't spill a drop. You did.",
            "Hot night. Cold shoulder. Done.",
            "Grab your bags, sweetie. You're leaving."],
    movelist="""<#f0f000>:Throws:</>
Checkout Toss							[_B/_F]_+^Y

<#f0f000>:Special Moves:</>
Water Bottle Toss_EX					_QDF^P
Hydrate (heal)							_QDB^A
Tote Bag Swing							_QDB^B
Rising Slap_EX							_DSF^P
Sleeve Slash_EX							_QDB^P
Stomp Rush_EX							_QDF^K
Boot Knee_EX							_F_F^K

<#f0f000>:Super Moves:</>
Bulk Buy Barrage <#bebebe>(1000)</>		_QDF_QDF^P
Last Call Uppercut <#bebebe>(1000)</>	_QDB_QDB^P
""",
    argv=sys.argv,
    cmd_hook=cmd_hook,
)

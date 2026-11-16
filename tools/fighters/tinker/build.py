"""Build Tinker into content/chars/tinker from the KFM 720 template + this folder.

Usage (repo root):
    python3 -I tools/fighters/tinker/build.py [--frames]

  --frames   regenerate art/ from source.png first (make_frames.py, ~1 min).
             Without it, the existing art/ folder is packed as-is, so
             hand-drawn replacements dropped into art/ are kept.

Writes tinker.cmd/.cns/.air (template + Tinker's changes), tinker.sff (packed
from art/), movelist.dat, and fixes the .def. Re-runnable.
"""
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
KFM = os.path.join(ROOT, "content", "chars", "kfm720")
OUT = os.path.join(ROOT, "content", "chars", "tinker")
ART = os.path.join(HERE, "art")
PY = sys.executable


def rd(p):
    with open(p, encoding="latin-1") as f:
        return f.read()


def wr(p, s):
    with open(p, "w", encoding="latin-1") as f:
        f.write(s)


def sub1(pattern, repl, s, flags=0):
    new, n = re.subn(pattern, repl, s, count=1, flags=flags)
    if n != 1:
        raise SystemExit("pattern not found: %r" % pattern)
    return new


if not os.path.isdir(OUT):
    subprocess.run([PY, "-I", os.path.join(ROOT, "tools", "new_character.py"), "tinker", "Tinker"], check=True)

if "--frames" in sys.argv or not os.path.isdir(ART):
    subprocess.run([PY, "-I", os.path.join(HERE, "make_frames.py"), ART], check=True)

# ---- commands: Kung Fu Palm -> Radar Pulse (one on screen at a time)
cmd = rd(os.path.join(KFM, "kfm720.cmd"))
for label, old, new in (("Fast", "1020", "1520"), ("Light", "1000", "1500"), ("Strong", "1010", "1510")):
    cmd = sub1(r"\[State -1, %s Kung Fu Palm\]\s*\ntype = ChangeState\s*\nvalue = %s\s*\n" % (label, old),
               "[State -1, %s Radar Pulse]\ntype = ChangeState\nvalue = %s\n"
               "triggerall = NumProjID(1500) = 0\n" % (label, new), cmd)
wr(os.path.join(OUT, "tinker.cmd"), cmd)

# ---- constants + states
cns = rd(os.path.join(KFM, "kfm720.cns"))
for pat, repl in ((r"(?m)^life = 1000", "life = 950"),
                  (r"(?m)^defence = 100", "defence = 105"),
                  (r"(?m)^walk\.fwd  = 9\.6", "walk.fwd  = 8.8"),
                  (r"(?m)^walk\.back = -8\.8", "walk.back = -8.0")):
    cns = sub1(pat, repl, cns)
quotes = [
    "Signal acquired. Opponent... neutralized.",
    "I checked the specs. You were never going to win.",
    "Everything's fixable. Except that fighting style.",
    "Pocket full of tools, and I only needed one.",
    "Radar never lies. You telegraphed every move.",
    "Hold still, I'm recalibrating your attitude.",
]
cns = sub1(r"(?ms)^\[Quotes\].*?(?=^\[(?!Quotes))",
           "[Quotes]\n" + "\n".join('victory%d = "%s"' % (i + 1, q) for i, q in enumerate(quotes)) + "\n\n",
           cns)
cns = re.sub(r"(?ms)^\[\w\w\.Quotes\].*?(?=^\[(?!\w\w\.Quotes))", "", cns)  # drop translated KFM quotes
cns += rd(os.path.join(HERE, "tinker_states.cns"))
wr(os.path.join(OUT, "tinker.cns"), cns)

# ---- animations
wr(os.path.join(OUT, "tinker.air"), rd(os.path.join(KFM, "kfm720.air")) + rd(os.path.join(HERE, "tinker_anims.air")))

# ---- def: one palette (sprites are true-color)
defp = os.path.join(OUT, "tinker.def")
d = rd(defp)
d = re.sub(r"(?m)^pal\.defaults\s*=.*$", "pal.defaults = 1", d)
d = re.sub(r"(?m)^ai\s*=.*\n", "", d)
wr(defp, d)

# ---- move list
wr(os.path.join(OUT, "movelist.dat"), """<#f0f000>:Throws:</>
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
""")

# ---- sprites
subprocess.run([PY, "-I", os.path.join(ROOT, "tools", "png_to_sff.py"), ART, os.path.join(OUT, "tinker.sff")], check=True)
print("Tinker built in", OUT)

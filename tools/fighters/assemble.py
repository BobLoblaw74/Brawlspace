"""Assemble a cut-out fighter into content/chars/<id> from the KFM 720 template.

Used by each fighter's build.py. Steps:
  1. scaffold content/chars/<id> with tools/new_character.py if it doesn't exist
  2. regenerate art/ with the fighter's make_frames.py (with --frames, or if art/ is missing)
  3. <id>.cmd: KFM's Kung Fu Palm inputs -> the fighter's projectile states 1500/1510/1520
  4. <id>.cns: KFM states + stat changes + quotes + the fighter's <id>_states.cns
  5. <id>.air: KFM animations + the fighter's <id>_anims.air
  6. .def (single palette), movelist.dat, and <id>.sff packed from art/
"""
import os
import re
import subprocess
import sys

FIGHTERS = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(FIGHTERS))
KFM = os.path.join(ROOT, "content", "chars", "kfm720")
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


def assemble(fid, name, here, projectile, stats, quotes, movelist, argv, cmd_hook=None):
    out = os.path.join(ROOT, "content", "chars", fid)
    art = os.path.join(here, "art")
    if not os.path.isdir(out):
        subprocess.run([PY, "-I", os.path.join(ROOT, "tools", "new_character.py"), fid, name], check=True)
    if "--frames" in argv or not os.path.isdir(art):
        subprocess.run([PY, "-I", os.path.join(here, "make_frames.py"), art], check=True)

    cmd = rd(os.path.join(KFM, "kfm720.cmd"))
    for label, old, new in (("Fast", "1020", "1520"), ("Light", "1000", "1500"), ("Strong", "1010", "1510")):
        cmd = sub1(r"\[State -1, %s Kung Fu Palm\]\s*\ntype = ChangeState\s*\nvalue = %s\s*\n" % (label, old),
                   "[State -1, %s %s]\ntype = ChangeState\nvalue = %s\n"
                   "triggerall = NumProjID(1500) = 0\n" % (label, projectile, new), cmd)
    if cmd_hook:  # fighter-specific inputs (extra specials, remapped supers)
        cmd = cmd_hook(cmd)
    wr(os.path.join(out, fid + ".cmd"), cmd)

    cns = rd(os.path.join(KFM, "kfm720.cns"))
    for pat, repl in stats:
        cns = sub1(pat, repl, cns)
    cns = sub1(r"(?ms)^\[Quotes\].*?(?=^\[(?!Quotes))",
               "[Quotes]\n" + "\n".join('victory%d = "%s"' % (i + 1, q) for i, q in enumerate(quotes)) + "\n\n",
               cns)
    cns = re.sub(r"(?ms)^\[\w\w\.Quotes\].*?(?=^\[(?!\w\w\.Quotes))", "", cns)  # drop KFM's translated quotes
    cns += rd(os.path.join(here, fid + "_states.cns"))
    wr(os.path.join(out, fid + ".cns"), cns)

    wr(os.path.join(out, fid + ".air"), rd(os.path.join(KFM, "kfm720.air")) + rd(os.path.join(here, fid + "_anims.air")))

    defp = os.path.join(out, fid + ".def")
    d = rd(defp)
    d = re.sub(r"(?m)^pal\.defaults\s*=.*$", "pal.defaults = 1", d)  # true-colour sprites: one palette
    d = re.sub(r"(?m)^ai\s*=.*\n", "", d)
    wr(defp, d)

    wr(os.path.join(out, "movelist.dat"), movelist)
    subprocess.run([PY, "-I", os.path.join(ROOT, "tools", "png_to_sff.py"), art, os.path.join(out, fid + ".sff")],
                   check=True)
    print("%s built in %s" % (name, out))

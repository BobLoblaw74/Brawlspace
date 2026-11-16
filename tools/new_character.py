"""Scaffold a new Brawlspace fighter from the Kung Fu Man 720 template.

Usage (from the repo root):
    python3 -I tools/new_character.py <id> "<Display Name>" [--author "Name"] [--stage stages/x.def]

Creates content/chars/<id>/ with <id>.def/.cmd/.cns/.air/.sff/.snd/movelist.dat
copied from kfm720 (sprites, sounds and moves start identical to KFM), sets the
name/author, drops KFM's arcade storyboards, and adds the fighter to
content/data/select.def. From there, replace the sprites (.sff), sounds (.snd)
and edit the moves (.cmd/.cns/.air) to make the character your own.
"""
import argparse
import datetime
import os
import re
import shutil
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CHARS = os.path.join(ROOT, "content", "chars")
TEMPLATE = os.path.join(CHARS, "kfm720")
SELECT = os.path.join(ROOT, "content", "data", "select.def")

ap = argparse.ArgumentParser()
ap.add_argument("id", help="folder/file id: letters, digits, _ or -")
ap.add_argument("name", help="display name shown in game")
ap.add_argument("--author", default="Brawlspace")
ap.add_argument("--stage", default="stages/stage0-720.def")
a = ap.parse_args()

if not re.fullmatch(r"[A-Za-z0-9_-]+", a.id):
    sys.exit("id may only contain letters, digits, _ and -")
dst = os.path.join(CHARS, a.id)
if os.path.exists(dst):
    sys.exit("content/chars/%s already exists" % a.id)

os.makedirs(dst)
renames = {
    "kfm720.def": a.id + ".def",
    "kfm720.cmd": a.id + ".cmd",
    "kfm720.cns": a.id + ".cns",
    "kfm720.air": a.id + ".air",
    "kfm720.sff": a.id + ".sff",
    "kfm.snd": a.id + ".snd",
    "movelist.dat": "movelist.dat",
}
for src, out in renames.items():
    shutil.copyfile(os.path.join(TEMPLATE, src), os.path.join(dst, out))

defp = os.path.join(dst, a.id + ".def")
with open(defp, encoding="latin-1") as f:
    d = f.read()
today = datetime.date.today()
d = re.sub(r'(?m)^name\s*=.*$', 'name = "%s"' % a.name, d, count=1)
d = re.sub(r'(?m)^displayname\s*=.*$', 'displayname = "%s"' % a.name, d, count=1)
d = re.sub(r'(?m)^author\s*=.*$', 'author = "%s"' % a.author, d, count=1)
d = re.sub(r'(?m)^versiondate\s*=.*$', 'versiondate = %02d,%02d,%d' % (today.month, today.day, today.year), d, count=1)
for old, new in renames.items():
    if old.endswith(".def") or old == "movelist.dat":
        continue
    d = re.sub(r'(?m)^(\w+\s*=\s*)%s' % re.escape(old), r'\g<1>%s' % new, d)
d = re.sub(r'(?ms)^\[Arcade\].*\Z', '', d)  # KFM's intro/ending storyboards don't apply
d = "; %s - scaffolded from Kung Fu Man 720 (Elecbyte, CC BY-NC).\n" \
    "; Replace %s.sff / %s.snd with original art and sound before any commercial use.\n\n" % (a.name, a.id, a.id) + d
with open(defp, "w", encoding="latin-1") as f:
    f.write(d)

with open(SELECT, encoding="utf-8") as f:
    s = f.read()
line = "%s, %s\n" % (a.id, a.stage)
m = re.search(r'(?m)^randomselect\s*$', s)
if m:
    s = s[:m.start()] + line + s[m.start():]
else:
    m = re.search(r'(?m)^\[Characters\]\s*\n', s)
    s = s[:m.end()] + line + s[m.end():]
with open(SELECT, "w", encoding="utf-8") as f:
    f.write(s)

print("created content/chars/%s and added it to select.def" % a.id)
print("rebuild content: bash build/wasm.sh --shell-only")

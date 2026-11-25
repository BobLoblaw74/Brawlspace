"""Redraw a fighter's warped cut-out frames with Gemini: write the prompts, cut the results.

The warped frames are one drawing bent and stretched, so they carry no pose information;
showing them to Gemini makes it copy them. Instead every frame gets a written pose,
identical poses are drawn once, and the unique poses are packed PER_SHEET to a request.
Each request attaches the character reference (source.png, or redraw/reference.png for a
fighter whose source faces left) plus the text of redraw/sheet_NN.txt; the answer is saved
as redraw/sheet_NN.png.

Usage (repo root):
    python3 -I tools/fighters/gemini_sheets.py <fighter> prompts
    python3 -I tools/fighters/gemini_sheets.py <fighter> cut <out_dir> [sheet_00 ...]  # preview
    python3 -I tools/fighters/gemini_sheets.py <fighter> cut --apply [sheet_00 ...]    # into art/
`cut` without sheet names takes every redraw/sheet_NN.png present and writes
compare_<sheet>.png (old frames above their redraws) for review.

A fighter is set up by tools/fighters/<fighter>/redraw_config.py, which defines FIGHTER:
  name        "Tinker": the prompt's "Image 1 is the character <name>"
  look        what every figure must keep from image 1 (face, outfit, props)
  poses       {sprite group: [pose per art item, in item order] or {item: pose}};
              generic_poses() covers the moves every fighter shares
  screen      "magenta" or "green": the background asked for and keyed out
  key         (solid, clear) keying thresholds (greensheet.key); raise them for a green
              screen when the fighter wears green
  scale       (game px, sheet, figure): that figure (1-based) is drawn that tall in game;
              Gemini draws the fighter the same size on every sheet, so one scale fits all
  air         optional built .air: only frames it uses are redrawn (the rest are replaced
              by hand-drawn sheets)
  mirror      True if source.png faces left: prompts attach redraw/reference.png instead
  use_figure  after review: {sheet: {figure: figure whose drawing its frames use}} (1-based)
"""
import glob
import importlib.util
import json
import os
import re
import shutil
import sys

from PIL import Image

FIGHTERS = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, FIGHTERS)
import greensheet  # noqa: E402

PER_SHEET, PER_ROW = 8, 4
SKIP = {6000, 6001, 9000}  # projectiles/effects and portraits: not body frames
HAND = 7000  # groups from here up are cut from hand-drawn sheets (greensheet.py): keep them
SCREENS = {"magenta": "magenta #FF00FF", "green": "pure green #00FF00"}

HEADER = """\
Image 1 is the character {name}. Draw a sprite sheet of him for a 2D fighting game: {n} separate \
full-body figures in {rows} row(s) of up to {per_row}, numbered left to right, top to bottom, \
with these poses:

{list}

Every figure: {look}; the same scale throughout (a standing figure fills most of the row height); \
facing right like image 1; whole body visible, nothing cropped; a clear gap between figures, no \
overlap. Only draw what each pose asks for (no opponent, no effects, no motion lines). \
Background: flat solid {screen} everywhere, no shadows, no floor, no text, no numbers, \
no borders.
"""


# --- pose helpers ----------------------------------------------------------

def sym(*poses, hold=1):
    """A move that plays forward then back: a, b, c -> a, b, c, b, a (hold=2: a, b, c, c, b, a)."""
    return list(poses) + [poses[-1]] * (hold - 1) + list(poses[-2::-1])


def walk(how):
    """Two steps of 4 phases, each held 2 frames. The phases differ by stride width (what
    reads at game size); the upper body stays the same so only the legs move."""
    steps = ["long stride: feet far apart, %s foot flat on the ground ahead, the other foot "
             "behind on its toes",
             "weight down on the %s foot ahead, both knees bent, feet still apart",
             "passing: feet close together under his hips, the other knee lifted forward past "
             "the %s leg, that foot off the ground",
             "the other leg reaching forward ahead of the %s leg, heel about to touch down"]
    out = []
    for leg in ("near (closer to the viewer)", "far"):
        for st in steps:
            out += ["%s, %s; upper body and arms the same as in his stance" % (how, st % leg)] * 2
    return out


def hit(kind, n):
    return {k: "%s, %s" % (kind, p) for k, p in n.items()}


def generic_poses(stance, crouch, air):
    """Moves every fighter shares (KFM template groups); a fighter overrides what differs."""
    p = {
        0: ["%s, chest slightly raised (breathing in)" % stance, stance, stance,
            "%s, shoulders slightly lowered (breathing out)" % stance,
            "%s, shoulders lowered further (breathing out)" % stance,
            "%s, shoulders lowered further (breathing out)" % stance],
        5: ["turning around: body seen from the front, mid-turn, fists up"],
        6: ["turning around while crouching: body seen from the front, knees bent, fists up"],
        11: ["half crouch, knees bent, lowering his body", crouch, crouch],
        20: walk("walking forward in his guard"),
        21: walk("stepping backward cautiously, guard up, leaning back"),
        41: ["crouched, about to jump straight up", "pushing off the ground, legs straightening",
             air, air, air, "at the top of a jump, legs hanging loose, arms out for balance",
             "falling, legs extending down to land", "falling, legs extending down to land",
             "falling, legs extending down to land"],
        42: ["forward somersault: diving forward, tucking into a ball",
             "forward somersault: tucked in a ball, rotated a quarter turn",
             "forward somersault: tucked in a ball, upside down",
             "forward somersault: tucked in a ball, three-quarter turn",
             "forward somersault: uncurling, legs swinging under him",
             "end of a forward somersault: upright in the air, legs reaching down to land"],
        43: ["jumping backwards: leaning back in mid-air, knees tucked"] * 2,
        100: ["running hard, leaning forward, right foot striking the ground",
              "running hard, leaning forward, both feet off the ground, left knee driving forward",
              "running hard, leaning forward, left leg reaching forward",
              "running hard, leaning forward, left foot striking the ground",
              "running hard, leaning forward, both feet off the ground, right knee driving forward",
              "running hard, leaning forward, right leg reaching forward"],
        121: ["crouching block: knees deeply bent, both forearms raised in front of his face"],
        122: ["blocking in mid-air: knees tucked, both forearms crossed in front of his face"],
        200: ["starting a jab: leaning forward, back fist moving forward",
              "light jab: back fist fully extended straight forward at head height",
              "starting a jab: leaning forward, back fist moving forward"],
        230: ["chambering a kick: front knee raised to waist height",
              "quick front kick: front leg straight out at stomach height",
              "chambering a kick: front knee raised to waist height"],
        240: sym("chambering a heavy kick: front knee raised high, leaning back",
                 "heavy kick rising: front leg swinging up and out",
                 "high roundhouse kick: boot at head height, leg fully straight, arms out for balance", hold=2),
        400: ["crouching jab starting: %s, fist moving forward" % crouch,
              "crouching jab: crouched low, back fist fully extended forward"],
        430: ["crouching low kick: crouched, front foot sliding forward",
              "crouching low kick: crouched, front leg straight out along the floor",
              "crouching low kick: crouched, front leg straight out along the floor",
              "crouching low kick: crouched, front foot sliding forward"],
        440: sym("low sweep starting: crouched low, one hand on the floor, starting to spin",
                 "low sweep: spinning on one knee, leg swinging round",
                 "low sweep: spinning on one knee, leg swinging forward along the floor",
                 "low sweep at full reach: one hand on the floor, leg fully extended forward "
                 "along the floor"),
        600: [air, "jumping jab: in mid-air, knees tucked, back fist extended forward"],
        630: [air, "jumping kick: in mid-air, front leg kicking straight forward"],
        640: [air, "flying kick: in mid-air, front leg fully extended diagonally down and forward, "
              "back leg tucked", air],
        800: ["throw: reaching forward with both hands to grab",
              "throw: gripping an opponent's collar with both hands (draw no opponent)",
              "throw: lifting with both hands, leaning back",
              "throw: twisting his hips, hands swinging to his side",
              "throw: hands swinging over his shoulder",
              "throw: hurling something behind him, arms over his shoulder",
              "throw: follow-through, arms behind him, body twisted",
              "throw: follow-through, arms behind him, body twisted",
              "after a throw: bent forward, catching his breath",
              "after a throw: bent forward, catching his breath",
              "after a throw: straightening up",
              "after a throw: straightening up",
              "after a throw: almost back in his stance"],
        1052: [stance, "landing from a jump: knees bent, absorbing the landing",
               "landing from a jump: knees bent, absorbing the landing", stance],
        5000: hit("hit in the face", {0: "head snapped back", 10: "leaning back, recoiling",
                                      11: "leaning far back, recoiling", 20: "leaning back, recoiling",
                                      21: "head snapped back"}),
        5010: hit("hit in the stomach", {0: "flinching forward", 10: "doubled over",
                                         20: "doubled over", 21: "flinching forward"}),
        5020: hit("hit while crouching", {0: "crouched, flinching", 10: "crouched, recoiling back",
                                          20: "crouched, flinching"}),
        5030: hit("knocked backwards off his feet", {
            0: "feet leaving the ground, body arching back", 10: "flying back, arms flailing",
            20: "flying back, body tilted 30 degrees backwards",
            30: "flying back, body tilted 45 degrees backwards",
            31: "flying back, body tilted 50 degrees backwards",
            40: "flying back, body tilted 60 degrees backwards",
            50: "flying back, body tilted 75 degrees backwards, almost horizontal"}),
        5040: {0: "falling flat on his back in the air, body horizontal",
               1: "the back of his shoulders hitting the ground, legs up",
               10: "bouncing off the ground on his back, legs up",
               11: "bouncing off the ground on his back, legs coming down",
               20: "lying flat on his back on the ground, dazed"},
        5060: {0: "tumbling backwards in the air, head lower than feet",
               1: "tumbling backwards in the air, head lower than feet",
               10: "tumbling backwards in the air, body horizontal, face up"},
        5070: {0: "tripped: legs swept out from under him, falling back",
               10: "tripped: falling backwards, body tilted 60 degrees",
               20: "tumbling backwards in the air, body horizontal, face up"},
        5300: ["dizzy: swaying to the left, arms limp, eyes spinning",
               "dizzy: slumped, knees buckling, eyes spinning",
               "dizzy: swaying to the right, arms limp, eyes spinning",
               "dizzy: wobbling upright, arms limp, eyes spinning"],
    }
    # medium/hard variants reuse the light reaction's drawings
    for base in (5000, 5010, 5030, 5040, 5060, 5070):
        for g in (base + 1, base + 2):
            p[g] = p[base]
    return p


# --- prompts ---------------------------------------------------------------

def load(fighter):
    path = os.path.join(FIGHTERS, fighter, "redraw_config.py")
    spec = importlib.util.spec_from_file_location(fighter + "_redraw_config", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    cfg = dict(mod.FIGHTER)
    cfg["here"] = os.path.join(FIGHTERS, fighter)
    cfg["out"] = os.path.join(cfg["here"], "redraw")
    return cfg


def frames(cfg):
    """(group, item) of every body frame to redraw, plus all items of each group (pose
    lists are indexed by position among all of a group's items)."""
    names = [os.path.basename(p)[:-4] for p in glob.glob(os.path.join(cfg["here"], "art", "*_*.png"))]
    every = sorted(tuple(map(int, n.split("_"))) for n in names if int(n.split("_")[0]) not in SKIP and int(n.split("_")[0]) < HAND)
    if cfg.get("air"):
        with open(cfg["air"], errors="replace") as f:
            used = {tuple(map(int, m)) for m in re.findall(r"(?m)^\s*(\d+)\s*,\s*(\d+)\s*,", f.read())}
        fr = [f for f in every if f in used]
    else:
        fr = every
    return fr, every


def write_prompts(cfg):
    fr, every = frames(cfg)
    poses = cfg["poses"]
    figures = {}  # pose text -> frame names, in first-use order
    for g, i in fr:
        items = [k for gg, k in every if gg == g]
        p = poses[g]
        ok = set(items) <= set(p) if isinstance(p, dict) else len(p) == len(items)
        assert ok, (g, items)
        pose = p[i] if isinstance(p, dict) else p[items.index(i)]
        figures.setdefault(pose, []).append("%d_%d" % (g, i))
    figs = list(figures.items())
    out = cfg["out"]
    os.makedirs(out, exist_ok=True)
    for old in glob.glob(os.path.join(out, "sheet_*.txt")):  # never the returned .png sheets
        os.remove(old)
    manifest = {}
    for k in range(0, len(figs), PER_SHEET):
        chunk = figs[k:k + PER_SHEET]
        name = "sheet_%02d" % (k // PER_SHEET)
        text = HEADER.format(name=cfg["name"], look=cfg["look"], screen=SCREENS[cfg["screen"]],
                             n=len(chunk), rows=-(-len(chunk) // PER_ROW), per_row=PER_ROW,
                             list="\n".join("%d. %s" % (j + 1, p) for j, (p, _) in enumerate(chunk)))
        with open(os.path.join(out, name + ".txt"), "w") as f:
            f.write(text)
        manifest[name] = [{"pose": p, "frames": list(f)} for p, f in chunk]
        for src, dst in cfg.get("use_figure", {}).get(name, {}).items():
            manifest[name][dst - 1]["frames"] += manifest[name][src - 1]["frames"]
            manifest[name][src - 1]["frames"] = []
    with open(os.path.join(out, "sheets.json"), "w") as f:
        json.dump(manifest, f, indent=1)
    if cfg.get("mirror"):
        src = Image.open(os.path.join(cfg["here"], "source.png"))
        src.transpose(Image.FLIP_LEFT_RIGHT).save(os.path.join(out, "reference.png"))
    print(len(manifest), "sheets,", len(figs), "unique poses,", len(fr), "frames")


# --- cutting ---------------------------------------------------------------

def body_x(im):
    """Body centre x (greensheet.body_centre) of an image, in its own coordinates."""
    box = im.getchannel("A").point(lambda a: 255 if a > 128 else 0).getbbox()
    return box, box[0] + greensheet.body_centre(im.crop(box))


def sheet_figures(cfg, sheet):
    return greensheet.figures(os.path.join(cfg["out"], sheet + ".png"),
                              keying=tuple(cfg["key"]) + (cfg["screen"],), rows=True)


def cut(cfg, sheet, manifest, out_dir, axes, scale):
    """Each figure goes to every frame sheets.json lists for it: scaled, bottom-aligned to
    the old frame and with its body centre where the old one was, so axes, motion and
    hitboxes keep working."""
    figs = sheet_figures(cfg, sheet)
    want = manifest[sheet]
    if len(figs) != len(want):
        sys.exit("%s: %d figures, expected %d: redo it in Gemini" % (sheet, len(figs), len(want)))
    art = os.path.join(cfg["here"], "art")
    old = {f: Image.open(os.path.join(art, f + ".png")).convert("RGBA") for w in want for f in w["frames"]}
    pairs = []
    for (fig, _), w in zip(figs, want):
        fig = fig.resize((round(fig.width * scale), round(fig.height * scale)), Image.LANCZOS)
        _, nbx = body_x(fig)
        for name in w["frames"]:
            (_, _, _, ob), obx = body_x(old[name])
            oax, oay = axes[name]
            greensheet.save_png(fig, os.path.join(out_dir, name + ".png"))
            axes[name] = (round(nbx + oax - obx), round(fig.height - (ob - oay)))
            pairs.append((old[name], fig))
    cw, ch = max(max(a.width, b.width) for a, b in pairs), max(a.height + b.height for a, b in pairs)
    cmp_ = Image.new("RGBA", (cw * len(pairs), ch), (255, 255, 255, 255))
    for k, (a, b) in enumerate(pairs):
        cmp_.alpha_composite(a, (k * cw, 0))
        cmp_.alpha_composite(b, (k * cw, a.height))
    cmp_.convert("RGB").save(os.path.join(out_dir, "compare_%s.png" % sheet))


def cut_main(cfg, args):
    apply = args[:1] == ["--apply"]
    art = os.path.join(cfg["here"], "art")
    out_dir = art if apply else args[0]
    sheets = args[1:] or sorted(os.path.basename(p)[:-4]
                                for p in glob.glob(os.path.join(cfg["out"], "sheet_*.png")))
    with open(os.path.join(cfg["out"], "sheets.json")) as f:
        manifest = json.load(f)
    game_px, ref_sheet, ref_fig = cfg["scale"]
    scale = game_px / sheet_figures(cfg, ref_sheet)[ref_fig - 1][0].height
    path = os.path.join(art, "axis.txt")
    with open(path) as f:
        lines = f.read().splitlines()
    axes = {l.split()[0]: tuple(map(int, l.split()[1:])) for l in lines if l and not l.startswith("#")}
    os.makedirs(out_dir, exist_ok=True)
    for sheet in sheets:
        cut(cfg, sheet, manifest, out_dir, axes, scale)
    out = [l if not l or l.startswith("#") else "%s %d %d" % ((l.split()[0],) + axes[l.split()[0]])
           for l in lines]
    with open(path if apply else os.path.join(out_dir, "axis.txt"), "w") as f:
        f.write("\n".join(out) + "\n")
    if apply:  # compare sheets are for review, not the build
        for p in glob.glob(os.path.join(art, "compare_*.png")):
            shutil.move(p, os.path.join(cfg["out"], os.path.basename(p)))


if __name__ == "__main__":
    if len(sys.argv) < 3 or sys.argv[2] not in ("prompts", "cut"):
        sys.exit(__doc__)
    cfg = load(sys.argv[1])
    if sys.argv[2] == "prompts":
        write_prompts(cfg)
    else:
        cut_main(cfg, sys.argv[3:])

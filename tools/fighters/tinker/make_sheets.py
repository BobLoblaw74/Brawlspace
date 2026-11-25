"""Write text-only Gemini prompts that redraw Tinker's 279 warped body frames as real poses.

The warped frames are all the same drawing bent and stretched, so they carry no pose
information; showing them to Gemini makes it copy them. Instead every frame gets a written
pose (POSES), identical poses are drawn once, and the unique poses are packed PER_SHEET to a
request. Each request attaches only source.png (the character) plus redraw/sheet_NN.txt.

Writes redraw/sheet_NN.txt (the prompt) and redraw/sheets.json: for each sheet, its
figures in reading order, each with the frames that use it.

Usage (repo root): python3 -I tools/fighters/tinker/make_sheets.py
"""
import glob
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "redraw")
PER_SHEET, PER_ROW = 8, 4
SKIP = {6000, 9000}  # radar pulse effect and portraits: not body frames
# after review: {sheet: {figure: figure whose drawing its frames use instead}} (1-based);
# the drawn figure stays on the sheet with no frames, so the sheet layout is unchanged.
# sheet_00's four breathing figures came back as different-looking drawings: the idle
# holds figure 2 instead of flickering.
USE_FIGURE = {"sheet_00": {1: 2, 3: 2, 4: 2}}

STANCE = "his fighting stance exactly as in image 1"
CROUCH = "crouching low, knees deeply bent, back fist up by his chin, gauntlet arm forward"
AIR = "in mid-air, knees tucked up, fists up"


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


POSES = {
    0: ["%s, chest slightly raised (breathing in)" % STANCE, STANCE, STANCE,
        "%s, shoulders slightly lowered (breathing out)" % STANCE,
        "%s, shoulders lowered further (breathing out)" % STANCE,
        "%s, shoulders lowered further (breathing out)" % STANCE],
    5: ["turning around: body seen from the front, mid-turn, fists up"],
    6: ["turning around while crouching: body seen from the front, knees bent, fists up"],
    11: ["half crouch, knees bent, lowering his body", CROUCH, CROUCH],
    20: walk("walking forward in his guard"),
    21: walk("stepping backward cautiously, guard up, leaning back"),
    41: ["crouched, about to jump straight up", "pushing off the ground, legs straightening",
         AIR, AIR, AIR, "at the top of a jump, legs hanging loose, arms out for balance",
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
    120: ["standing block: both forearms raised in front of his face, gauntlet as a shield"] * 3,
    121: ["crouching block: knees deeply bent, both forearms raised in front of his face"],
    122: ["blocking in mid-air: knees tucked, both forearms crossed in front of his face"],
    181: sym("victory: standing tall, starting to raise the radar gauntlet",
             "victory: radar gauntlet raised to shoulder height, other fist pumping",
             "victory: radar gauntlet raised high overhead, grinning",
             "victory: radar gauntlet thrust straight up overhead, other fist pumping, big grin"),
    191: ["intro: standing, adjusting the dials on his gauntlet with his other hand, eyes on it",
          "intro: standing, twisting the radar dish into position with his other hand"] * 2,
    192: ["intro: holding the radar gauntlet up proudly beside his face, dish pointed forward"] * 2,
    200: ["starting a jab: leaning forward, back fist moving forward",
          "light jab: back fist fully extended straight forward at head height",
          "starting a jab: leaning forward, back fist moving forward"],
    210: sym("winding up a heavy punch: shoulders twisted back, gauntlet fist pulled back",
             "heavy punch halfway: hips turning, gauntlet fist driving forward",
             "heavy punch at full reach: gauntlet arm locked straight forward, body leaning in", hold=2),
    230: ["chambering a kick: front knee raised to waist height",
          "quick front kick: front leg straight out at stomach height",
          "chambering a kick: front knee raised to waist height"],
    240: sym("chambering a heavy kick: front knee raised high, leaning back",
             "heavy kick rising: front leg swinging up and out",
             "high roundhouse kick: boot at head height, leg fully straight, arms out for balance", hold=2),
    400: ["crouching jab starting: %s, fist moving forward" % CROUCH,
          "crouching jab: crouched low, back fist fully extended forward"],
    410: sym("crouching heavy punch wind-up: crouched low, gauntlet fist pulled back",
             "crouching heavy punch halfway: crouched low, gauntlet fist driving forward",
             "crouching heavy punch: crouched low, gauntlet arm locked straight forward"),
    430: ["crouching low kick: crouched, front foot sliding forward",
          "crouching low kick: crouched, front leg straight out along the floor",
          "crouching low kick: crouched, front leg straight out along the floor",
          "crouching low kick: crouched, front foot sliding forward"],
    440: sym("low sweep starting: crouched low, one hand on the floor, starting to spin",
             "low sweep: spinning on one knee, leg swinging round",
             "low sweep: spinning on one knee, leg swinging forward along the floor",
             "low sweep at full reach: one hand on the floor, leg fully extended forward "
             "along the floor"),
    600: [AIR, "jumping jab: in mid-air, knees tucked, back fist extended forward"],
    610: [AIR, "jumping heavy punch: in mid-air, gauntlet fist punching forward and down",
          "jumping heavy punch: in mid-air, gauntlet fist punching forward and down", AIR],
    630: [AIR, "jumping kick: in mid-air, front leg kicking straight forward"],
    640: [AIR, "flying kick: in mid-air, front leg fully extended diagonally down and forward, "
          "back leg tucked", AIR],
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
    1000: sym("radar pulse: pulling the radar gauntlet back to his hip",
              "radar pulse: thrusting the radar gauntlet forward",
              "radar pulse: gauntlet arm locked straight forward, dish aimed at the enemy",
              "radar pulse: gauntlet arm locked straight forward, dish aimed at the enemy, "
              "other hand bracing his forearm", hold=2),
    1050: sym("boot knee: dipping low, ready to dash", "boot knee: dashing forward low",
              "boot knee: leaping forward, knee rising",
              "boot knee: flying knee, front knee driven forward at chest height, fists back", hold=2),
    1052: [STANCE, "landing from a jump: knees bent, absorbing the landing",
           "landing from a jump: knees bent, absorbing the landing", STANCE],
    1055: sym("knee strike: crouching, ready to spring up",
              "knee strike: springing up off one foot", "knee strike: knee rising, body airborne",
              "knee strike: airborne, knee thrust straight up at head height, fists pulled down", hold=2),
    1100: sym("antenna uppercut: crouching very low, gauntlet fist down by the floor",
              "antenna uppercut: springing up, gauntlet fist swinging upward",
              "antenna uppercut: rising uppercut, gauntlet fist at chin height",
              "antenna uppercut: leaving the ground, gauntlet arm stretched straight up",
              "antenna uppercut: in the air, whole body stretched straight up, gauntlet fist "
              "high overhead", hold=2),
    1210: sym("wrench swing: drawing a big wrench from his toolbelt, raised behind his head",
              "wrench swing: swinging the big wrench forward and down",
              "wrench swing: big wrench straight out in front at full reach",
              "wrench swing: follow-through, big wrench swung low past his front knee"),
    1300: ["high parry: gauntlet forearm raised at head height, deflecting"] * 3,
    1320: ["low parry: crouching, gauntlet forearm lowered to deflect at shin height"] * 3,
    1340: ["air parry: in mid-air, knees tucked, gauntlet forearm raised to deflect"] * 2,
    1400: [STANCE] + ["shoulder charge: launching forward low, shoulder first"]
          + ["shoulder charge: body nearly horizontal, front shoulder driving forward, "
             "back leg stretched out behind"] * 4
          + ["shoulder charge: slowing, straightening up", STANCE],
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
        POSES[g] = POSES[base]

HEADER = """\
Image 1 is the character Tinker. Draw a sprite sheet of him for a 2D fighting game: {n} separate \
full-body figures in {rows} row(s) of up to {per_row}, numbered left to right, top to bottom, \
with these poses:

{list}

Every figure: the radar dish on his front gauntlet exactly as in image 1 (never left \
out); the same face, outfit, tool belt, colours and inked comic \
style as image 1; the same scale throughout (a standing figure fills most of the row height); \
facing right like image 1; whole body visible, nothing cropped; a clear gap between figures, no \
overlap. Only draw what each pose asks for (no opponent, no effects, no motion lines). \
Background: flat solid magenta #FF00FF everywhere, no shadows, no floor, no text, no numbers, \
no borders.
"""


def frames():
    names = [os.path.basename(p)[:-4] for p in glob.glob(os.path.join(HERE, "art", "*_*.png"))]
    return sorted((tuple(map(int, n.split("_"))) for n in names if int(n.split("_")[0]) not in SKIP))


def pose_of(g, i, items):
    p = POSES[g]
    return p[i] if isinstance(p, dict) else p[items.index(i)]


def main():
    fr = frames()
    figures = {}  # pose text -> frame names, in first-use order
    for g, i in fr:
        items = [k for gg, k in fr if gg == g]
        ok = set(items) <= set(POSES[g]) if isinstance(POSES[g], dict) else len(POSES[g]) == len(items)
        assert ok, (g, items)
        figures.setdefault(pose_of(g, i, items), []).append("%d_%d" % (g, i))
    figs = list(figures.items())
    os.makedirs(OUT, exist_ok=True)
    for old in glob.glob(os.path.join(OUT, "sheet_*.txt")):  # never the returned .png sheets
        os.remove(old)
    manifest = {}
    for k in range(0, len(figs), PER_SHEET):
        chunk = figs[k:k + PER_SHEET]
        name = "sheet_%02d" % (k // PER_SHEET)
        text = HEADER.format(n=len(chunk), rows=-(-len(chunk) // PER_ROW), per_row=PER_ROW,
                             list="\n".join("%d. %s" % (j + 1, p) for j, (p, _) in enumerate(chunk)))
        with open(os.path.join(OUT, name + ".txt"), "w") as f:
            f.write(text)
        manifest[name] = [{"pose": p, "frames": list(f)} for p, f in chunk]
        for src, dst in USE_FIGURE.get(name, {}).items():
            manifest[name][dst - 1]["frames"] += manifest[name][src - 1]["frames"]
            manifest[name][src - 1]["frames"] = []
    with open(os.path.join(OUT, "sheets.json"), "w") as f:
        json.dump(manifest, f, indent=1)
    for old in ("PROMPT.txt",):
        if os.path.exists(os.path.join(OUT, old)):
            os.remove(os.path.join(OUT, old))
    print(len(manifest), "sheets,", len(figs), "unique poses,", len(fr), "frames")


if __name__ == "__main__":
    main()

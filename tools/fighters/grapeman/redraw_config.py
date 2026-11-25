"""GrapeMan's Gemini redraw (see tools/fighters/gemini_sheets.py). Attach redraw/reference.png
(source.png mirrored to face right). Only the frames his built .air still uses are redrawn:
idle, crouch, walk, jump, light punch, heavy kick, guard and the main hit reactions already
come from his hand-drawn sheets (make_frames.py SHEETS)."""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
from gemini_sheets import generic_poses, sym  # noqa: E402

STANCE = "his fighting stance exactly as in image 1"
CROUCH = "crouching low, knees deeply bent, clawed hands raised in front of him"
AIR = "in mid-air, knees tucked up, clawed hands up"

POSES = generic_poses(STANCE, CROUCH, AIR)
POSES.update({
    181: sym("victory: standing tall, fists clenched at his sides, grinning",
             "victory: one fist raised to shoulder height",
             "victory: both fists raised high overhead",
             "victory: both arms thrust straight up overhead, head thrown back laughing"),
    191: ["intro: standing, plucking a single grape from his chest with one hand, eyeing it",
          "intro: standing, popping the grape into his mouth, grinning"] * 2,
    192: ["intro: flexing both arms, the vines on his forearms pulled tight"] * 2,
    210: sym("winding up a heavy punch: shoulders twisted back, vine-wrapped fist pulled back",
             "heavy punch halfway: hips turning, vine-wrapped fist driving forward",
             "heavy punch at full reach: arm locked straight forward, body leaning in", hold=2),
    410: sym("crouching heavy punch wind-up: crouched low, vine-wrapped fist pulled back",
             "crouching heavy punch halfway: crouched low, fist driving forward",
             "crouching heavy punch: crouched low, arm locked straight forward"),
    610: [AIR, "jumping heavy punch: in mid-air, fist punching forward and down",
          "jumping heavy punch: in mid-air, fist punching forward and down", AIR],
    1000: sym("grape shot: plucking a grape from his chest, throwing hand drawn back by his ear",
              "grape shot: throwing arm whipping forward over his shoulder",
              "grape shot: throwing arm fully extended forward, hand open, just released",
              "grape shot: throwing arm fully extended forward, hand open, other hand on his "
              "chest", hold=2),
    1050: sym("stomping knee: dipping low, ready to dash", "stomping knee: dashing forward low",
              "stomping knee: leaping forward, knee rising",
              "stomping knee: flying knee, front knee driven forward at chest height, "
              "arms back", hold=2),
    1055: sym("knee strike: crouching, ready to spring up",
              "knee strike: springing up off one foot", "knee strike: knee rising, body airborne",
              "knee strike: airborne, knee thrust straight up at head height, arms pulled down",
              hold=2),
    1100: sym("vine uppercut: crouching very low, vine-wrapped fist down by the floor",
              "vine uppercut: springing up, fist swinging upward",
              "vine uppercut: rising uppercut, fist at chin height",
              "vine uppercut: leaving the ground, arm stretched straight up",
              "vine uppercut: in the air, whole body stretched straight up, fist high overhead",
              hold=2),
    1210: sym("bunch blow: twisting his torso back, both arms swung behind him",
              "bunch blow: swinging his big round grape-bunch body forward",
              "bunch blow: belly thrust far forward, arms flung back, leaning into it",
              "bunch blow: follow-through, bent forward over his front knee"),
    1300: ["high parry: vine-wrapped forearm raised at head height, deflecting"] * 3,
    1320: ["low parry: crouching, vine-wrapped forearm lowered to deflect at shin height"] * 3,
    1340: ["air parry: in mid-air, knees tucked, vine-wrapped forearm raised to deflect"] * 2,
    1400: [STANCE, "rolling raisin: diving forward, curling into a ball",
           "rolling raisin: curled into a tight round ball of grapes, head tucked at the front",
           "rolling raisin: curled into a tight round ball, rolled a quarter turn forward",
           "rolling raisin: curled into a tight round ball, rolled upside down",
           "rolling raisin: curled into a tight round ball, rolled three-quarters of a turn",
           "rolling raisin: uncurling, feet coming down", STANCE],
})

FIGHTER = {
    "name": "GrapeMan",
    "look": "the same face and glasses, purple grape-bunch costume, leafy vine crown, "
            "vine-wrapped forearms, boots, colours and inked comic style as image 1",
    "poses": POSES,
    "screen": "green",  # his costume is purple, too close to magenta
    "key": (80, 160),   # only the saturated screen keys out, not his green leaves
    "scale": (421, "sheet_00", 1),  # his stance; the hand-drawn idle is 421 px tall in game
    "air": os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(HERE))),
                        "content", "chars", "grapeman", "grapeman.air"),
    "mirror": True,
}

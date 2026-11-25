"""Tinker's Gemini redraw (see tools/fighters/gemini_sheets.py). Attach source.png."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from gemini_sheets import generic_poses, sym  # noqa: E402

STANCE = "his fighting stance exactly as in image 1"
CROUCH = "crouching low, knees deeply bent, back fist up by his chin, gauntlet arm forward"
AIR = "in mid-air, knees tucked up, fists up"

POSES = generic_poses(STANCE, CROUCH, AIR)
POSES.update({
    120: ["standing block: both forearms raised in front of his face, gauntlet as a shield"] * 3,
    181: sym("victory: standing tall, starting to raise the radar gauntlet",
             "victory: radar gauntlet raised to shoulder height, other fist pumping",
             "victory: radar gauntlet raised high overhead, grinning",
             "victory: radar gauntlet thrust straight up overhead, other fist pumping, big grin"),
    191: ["intro: standing, adjusting the dials on his gauntlet with his other hand, eyes on it",
          "intro: standing, twisting the radar dish into position with his other hand"] * 2,
    192: ["intro: holding the radar gauntlet up proudly beside his face, dish pointed forward"] * 2,
    210: sym("winding up a heavy punch: shoulders twisted back, gauntlet fist pulled back",
             "heavy punch halfway: hips turning, gauntlet fist driving forward",
             "heavy punch at full reach: gauntlet arm locked straight forward, body leaning in", hold=2),
    410: sym("crouching heavy punch wind-up: crouched low, gauntlet fist pulled back",
             "crouching heavy punch halfway: crouched low, gauntlet fist driving forward",
             "crouching heavy punch: crouched low, gauntlet arm locked straight forward"),
    610: [AIR, "jumping heavy punch: in mid-air, gauntlet fist punching forward and down",
          "jumping heavy punch: in mid-air, gauntlet fist punching forward and down", AIR],
    1000: sym("radar pulse: pulling the radar gauntlet back to his hip",
              "radar pulse: thrusting the radar gauntlet forward",
              "radar pulse: gauntlet arm locked straight forward, dish aimed at the enemy",
              "radar pulse: gauntlet arm locked straight forward, dish aimed at the enemy, "
              "other hand bracing his forearm", hold=2),
    1050: sym("boot knee: dipping low, ready to dash", "boot knee: dashing forward low",
              "boot knee: leaping forward, knee rising",
              "boot knee: flying knee, front knee driven forward at chest height, fists back", hold=2),
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
})

FIGHTER = {
    "name": "Tinker",
    "look": "the radar dish on his front gauntlet exactly as in image 1 (never left out); the "
            "same face, outfit, tool belt, colours and inked comic style as image 1",
    "poses": POSES,
    "screen": "magenta",  # his gadgets glow green
    "key": (40, 110),
    "scale": (423, "sheet_00", 2),  # the stance; the original stance frame is 423 px tall
}

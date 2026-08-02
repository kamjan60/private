"""Old-RPG / dark-fantasy wizard: 32x32, 4 directions x 3-frame walk cycle.

Worked example for tools/pixel-art-toolkit/pixel_lib.py — every technique here is
documented in ../../reference/ (color/shading, dithering, animation timing).
"""
import os
import sys

from PIL import Image

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
from pixel_lib import blank, px, row, dither_row, outline_pass, mirror, compose_sheet

W, H = 32, 32
SCALE = 8
OUT = os.path.dirname(__file__)

# Old-RPG / dark-fantasy palette: desaturated, cool-leaning, low-key.
# Gold traded for tarnished bronze, gem swapped for a glowing arcane green
# (the one saturated accent in an otherwise muted set), skin sallow, beard
# dingy off-white rather than clean bright white. See ../../reference/
# color-and-shading.md for the "dark-fantasy variant" rules this follows.
OUTLINE    = (12, 9, 14, 255)
HAT_MAIN   = (58, 40, 66, 255)
HAT_DARK   = (36, 24, 44, 255)
HAT_LIGHT  = (86, 62, 96, 255)
BAND_GOLD  = (120, 96, 48, 255)     # tarnished bronze, not shiny gold
SKIN       = (188, 165, 142, 255)   # sallow, aged
SKIN_DARK  = (144, 122, 104, 255)
ROBE_MAIN  = (54, 40, 68, 255)
ROBE_DARK  = (30, 20, 42, 255)      # shadow, cool violet-black
ROBE_LIGHT = (108, 130, 118, 255)   # cold, sickly-pale rim light (not warm pink)
ROBE_DEEP  = (18, 12, 26, 255)      # deepest fold tone, dithered with ROBE_DARK
STAFF      = (66, 48, 36, 255)
GEM        = (86, 210, 140, 255)    # glowing arcane green — the one saturated accent
GEM_DARK   = (34, 110, 78, 255)
BOOT       = (24, 18, 28, 255)
BOOT_DARK  = (14, 10, 16, 255)
EYE        = (200, 210, 150, 255)   # faint witch-light glint instead of a flat black dot
BEARD      = (196, 194, 188, 255)   # dingy off-white
BEARD_SHADE= (140, 138, 134, 255)

BOB = 2

# ---------------------------------------------------------------- DOWN (front)
def draw_down(leg_offset):
    img = blank(W, H)
    y0 = -BOB if leg_offset == 0 else 0

    row(img, 2+y0, 15, 16, HAT_DARK)
    row(img, 3+y0, 14, 17, HAT_MAIN)
    row(img, 4+y0, 13, 18, HAT_MAIN)
    row(img, 5+y0, 11, 20, HAT_MAIN)
    px(img, 11, 5+y0, HAT_LIGHT)
    row(img, 6+y0, 7, 24, HAT_MAIN)
    row(img, 7+y0, 9, 22, BAND_GOLD)
    row(img, 8+y0, 10, 21, HAT_DARK)

    row(img, 9+y0, 12, 19, SKIN)
    row(img, 10+y0, 11, 20, SKIN)
    px(img, 14, 10+y0, EYE); px(img, 17, 10+y0, EYE)
    row(img, 11+y0, 11, 20, SKIN)
    row(img, 12+y0, 11, 20, SKIN)
    row(img, 13+y0, 11, 20, SKIN_DARK)

    # shoulders / cape flare
    row(img, 14+y0, 7, 24, ROBE_MAIN)
    row(img, 15+y0, 6, 25, ROBE_MAIN)

    # staff, right side
    for yy in range(13, 31):
        px(img, 26, yy, STAFF)
    px(img, 26, 12, GEM); px(img, 25, 12, GEM_DARK); px(img, 27, 12, GEM_DARK)

    # robe taper
    robe_rows = [
        (16, 9, 22), (17, 9, 22), (18, 8, 23), (19, 8, 23),
        (20, 7, 24), (21, 7, 24), (22, 6, 25), (23, 6, 25),
        (24, 5, 26), (25, 5, 26), (26, 4, 27), (27, 4, 27),
        (28, 3, 28),
    ]
    shade_rows = {18, 22, 26}
    for yy, x0, x1 in robe_rows:
        if yy == 28:
            dither_row(img, yy + y0, x0, x1, ROBE_DARK, ROBE_DEEP)
        elif yy in shade_rows:
            row(img, yy + y0, x0, x1, ROBE_DARK)
        else:
            row(img, yy + y0, x0, x1, ROBE_MAIN)
    for yy in range(16, 28):
        px(img, 15, yy + y0, ROBE_LIGHT)
        px(img, 16, yy + y0, ROBE_LIGHT)

    # long hair: sideburns beside the face, then peeking past the shoulders
    for yy in range(8, 14):
        row(img, yy + y0, 9, 10, BEARD)
        row(img, yy + y0, 21, 22, BEARD)
    row(img, 14+y0, 8, 9, BEARD); row(img, 14+y0, 22, 23, BEARD)
    row(img, 15+y0, 7, 8, BEARD); row(img, 15+y0, 23, 24, BEARD)

    # beard: starts over the mouth (mustache width), widens over the jaw,
    # tapers down and curls into two tufts at the tip instead of a single point
    beard_rows = [
        (12, 13, 18), (13, 11, 20), (14, 10, 21), (15, 10, 21),
        (16, 11, 20), (17, 11, 20), (18, 12, 19), (19, 12, 19),
        (20, 13, 18), (21, 13, 18),
    ]
    for yy, x0, x1 in beard_rows:
        row(img, yy + y0, x0, x1, BEARD)
    row(img, 22+y0, 12, 13, BEARD); row(img, 22+y0, 18, 19, BEARD)
    row(img, 23+y0, 12, 12, BEARD); row(img, 23+y0, 19, 19, BEARD)
    for yy in range(13, 22):
        px(img, 15, yy + y0, BEARD_SHADE)
        px(img, 16, yy + y0, BEARD_SHADE)

    # boots
    lf = 10 + leg_offset * 2
    rf = 19 - leg_offset * 2
    for yy in (29, 30, 31):
        row(img, yy, lf, lf + 2, BOOT if yy < 31 else BOOT_DARK)
        row(img, yy, rf, rf + 2, BOOT if yy < 31 else BOOT_DARK)

    return outline_pass(img, OUTLINE)

# ------------------------------------------------------------------ UP (back)
def draw_up(leg_offset):
    img = blank(W, H)
    y0 = -BOB if leg_offset == 0 else 0

    row(img, 2+y0, 15, 16, HAT_DARK)
    row(img, 3+y0, 14, 17, HAT_MAIN)
    row(img, 4+y0, 13, 18, HAT_MAIN)
    row(img, 5+y0, 11, 20, HAT_MAIN)
    row(img, 6+y0, 7, 24, HAT_DARK)
    row(img, 7+y0, 9, 22, BAND_GOLD)
    row(img, 8+y0, 10, 21, HAT_MAIN)

    # back of head fully hooded, no face
    row(img, 9+y0, 11, 20, HAT_MAIN)
    row(img, 10+y0, 11, 20, HAT_MAIN)
    row(img, 11+y0, 11, 20, HAT_DARK)
    row(img, 12+y0, 10, 21, ROBE_MAIN)
    row(img, 13+y0, 9, 22, ROBE_MAIN)

    row(img, 14+y0, 7, 24, ROBE_MAIN)
    row(img, 15+y0, 6, 25, ROBE_MAIN)

    for yy in range(13, 31):
        px(img, 5, yy, STAFF)
    px(img, 5, 12, GEM); px(img, 4, 12, GEM_DARK); px(img, 6, 12, GEM_DARK)

    robe_rows = [
        (16, 9, 22), (17, 9, 22), (18, 8, 23), (19, 8, 23),
        (20, 7, 24), (21, 7, 24), (22, 6, 25), (23, 6, 25),
        (24, 5, 26), (25, 5, 26), (26, 4, 27), (27, 4, 27),
        (28, 3, 28),
    ]
    shade_rows = {18, 22, 26}
    for yy, x0, x1 in robe_rows:
        if yy == 28:
            dither_row(img, yy + y0, x0, x1, ROBE_DARK, ROBE_DEEP)
        elif yy in shade_rows:
            row(img, yy + y0, x0, x1, ROBE_DARK)
        else:
            row(img, yy + y0, x0, x1, ROBE_MAIN)
    # spine seam (fold down the back), lower half only — hair covers the top
    for yy in range(20, 28):
        px(img, 15, yy + y0, ROBE_DARK)
        px(img, 16, yy + y0, ROBE_DARK)

    # long hair flowing down the back, drawn on top of the cape
    for yy in range(9, 20):
        row(img, yy + y0, 14, 17, BEARD)
    for yy in range(9, 20):
        px(img, 15, yy + y0, BEARD_SHADE)
        px(img, 16, yy + y0, BEARD_SHADE)

    lf = 10 + leg_offset * 2
    rf = 19 - leg_offset * 2
    for yy in (29, 30, 31):
        row(img, yy, lf, lf + 2, BOOT if yy < 31 else BOOT_DARK)
        row(img, yy, rf, rf + 2, BOOT if yy < 31 else BOOT_DARK)

    return outline_pass(img, OUTLINE)

# ------------------------------------------------------------- SIDE (right); mirror for left
# Facing right (higher x = forward). Tip of hat leans back (low x), brim juts
# forward over the brow, nose/beard build out from a stepped profile silhouette.
def draw_side(stride):
    img = blank(W, H)
    y0 = -BOB if stride == 0 else 0

    row(img, 2+y0, 15, 16, HAT_DARK)
    row(img, 3+y0, 13, 17, HAT_MAIN)
    row(img, 4+y0, 12, 19, HAT_MAIN)
    row(img, 5+y0, 10, 23, HAT_MAIN)
    row(img, 6+y0, 12, 21, BAND_GOLD)
    row(img, 7+y0, 13, 20, HAT_DARK)

    # hair trailing behind the head (opposite the facing direction)
    for yy in range(8, 14):
        row(img, yy + y0, 9, 13, BEARD)
    row(img, 14+y0, 8, 12, BEARD)
    row(img, 15+y0, 7, 11, BEARD)
    for yy in range(9, 14):
        px(img, 11, yy + y0, BEARD_SHADE)

    # profile face: forehead -> brow -> nose bridge -> nose tip -> mouth -> chin
    row(img, 8+y0, 14, 19, SKIN)
    row(img, 9+y0, 14, 20, SKIN)
    px(img, 15, 9+y0, EYE)
    row(img, 10+y0, 14, 22, SKIN)
    row(img, 11+y0, 14, 24, SKIN)       # nose bridge to tip
    px(img, 24, 11+y0, SKIN_DARK)       # nostril shade
    row(img, 12+y0, 14, 21, SKIN)       # under-nose / mouth line
    row(img, 13+y0, 14, 20, SKIN_DARK)  # chin, receded from the nose

    # shoulders / cape
    row(img, 14+y0, 8, 25, ROBE_MAIN)
    row(img, 15+y0, 6, 25, ROBE_MAIN)

    # staff, forward hand, clear of the face
    for yy in range(13, 31):
        px(img, 26, yy, STAFF)
    px(img, 26, 12, GEM); px(img, 25, 12, GEM_DARK); px(img, 27, 12, GEM_DARK)

    robe_rows = [
        (16, 4, 25), (17, 3, 24), (18, 2, 24), (19, 1, 23),
        (20, 1, 23), (21, 0, 22), (22, 0, 21), (23, 0, 21),
        (24, 0, 20), (25, 0, 21), (26, 0, 19), (27, 0, 22),
    ]
    shade_rows = {17, 20, 23, 26}
    for yy, x0, x1 in robe_rows:
        if yy == 27:
            dither_row(img, yy + y0, x0, x1, ROBE_DARK, ROBE_DEEP)
        elif yy in shade_rows:
            row(img, yy + y0, x0, x1, ROBE_DARK)
        else:
            row(img, yy + y0, x0, x1, ROBE_MAIN)

    # beard: overlaps the mouth, hangs past the chin, hooks forward at the tip
    beard_rows = [
        (11, 15, 21), (12, 13, 21), (13, 12, 20), (14, 11, 19),
        (15, 11, 18), (16, 11, 17), (17, 12, 17), (18, 13, 17),
        (19, 14, 18), (20, 15, 19), (21, 16, 19),
    ]
    for yy, x0, x1 in beard_rows:
        row(img, yy + y0, x0, x1, BEARD)
    for yy in range(12, 21):
        px(img, 14, yy + y0, BEARD_SHADE)

    # legs in profile: front leg toward the face, back leg trailing
    front = 18 + stride * 2
    back = 9 - stride * 2
    for yy in (28, 29, 30):
        row(img, yy, front, front + 2, BOOT)
        row(img, yy, back, back + 2, BOOT)
    row(img, 31, front, front + 2, BOOT_DARK)
    row(img, 31, back, back + 2, BOOT_DARK)

    return outline_pass(img, OUTLINE)

frames = {
    "down":  [draw_down(-1), draw_down(0), draw_down(1)],
    "left":  [mirror(draw_side(1)), mirror(draw_side(0)), mirror(draw_side(-1))],
    "right": [draw_side(-1), draw_side(0), draw_side(1)],
    "up":    [draw_up(-1), draw_up(0), draw_up(1)],
}

order = ["down", "left", "right", "up"]

sheet = compose_sheet([frames[d] for d in order], W, H)
sheet.save(os.path.join(OUT, "wizard_sheet.png"))

big = sheet.resize((sheet.width * SCALE, sheet.height * SCALE), Image.NEAREST)
big.save(os.path.join(OUT, "wizard_sheet_preview.png"))

print("done", sheet.size)

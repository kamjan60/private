"""Four distinct wizard silhouettes/shapes (not recolors) - single idle
front-facing frame each, 32x32, same dark-fantasy palette family as
../wizard/draw.py. Exercises pixel_lib.py on varied shapes.
"""
import os
import sys

from PIL import Image

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
from pixel_lib import blank, px, row, dither_row, outline_pass, compose_sheet

W, H = 32, 32
SCALE = 8
OUT = os.path.dirname(__file__)

OUTLINE     = (12, 9, 14, 255)
SKIN        = (188, 165, 142, 255)
SKIN_DARK   = (144, 122, 104, 255)
SKIN_SHADOW = (96, 82, 76, 255)     # deep-hood face shadow (variant 2)
BOOT        = (24, 18, 28, 255)
BOOT_DARK   = (14, 10, 16, 255)
BEARD       = (196, 194, 188, 255)
BEARD_SHADE = (140, 138, 134, 255)

# ============================================================ V1: Classic Sorcerer
# Tall conical hat, straight tapered robe, long curled beard. Baseline shape
# from the wizard example - single idle frame.
def draw_v1():
    HAT_MAIN, HAT_DARK, HAT_LIGHT = (58, 40, 66, 255), (36, 24, 44, 255), (86, 62, 96, 255)
    BAND = (120, 96, 48, 255)
    ROBE_MAIN, ROBE_DARK, ROBE_LIGHT, ROBE_DEEP = (54, 40, 68, 255), (30, 20, 42, 255), (108, 130, 118, 255), (18, 12, 26, 255)
    STAFF, GEM, GEM_DARK = (66, 48, 36, 255), (86, 210, 140, 255), (34, 110, 78, 255)
    EYE = (200, 210, 150, 255)

    img = blank(W, H)
    row(img, 0, 15, 16, HAT_DARK)
    row(img, 1, 14, 17, HAT_MAIN)
    row(img, 2, 13, 18, HAT_MAIN)
    row(img, 3, 11, 20, HAT_MAIN)
    px(img, 11, 3, HAT_LIGHT)
    row(img, 4, 7, 24, HAT_MAIN)
    row(img, 5, 9, 22, BAND)
    row(img, 6, 10, 21, HAT_DARK)

    row(img, 7, 12, 19, SKIN)
    row(img, 8, 11, 20, SKIN)
    px(img, 14, 8, EYE); px(img, 17, 8, EYE)
    row(img, 9, 11, 20, SKIN)
    row(img, 10, 11, 20, SKIN)
    row(img, 11, 11, 20, SKIN_DARK)

    row(img, 12, 7, 24, ROBE_MAIN)
    row(img, 13, 6, 25, ROBE_MAIN)
    for yy in range(11, 29):
        px(img, 26, yy, STAFF)
    px(img, 26, 10, GEM); px(img, 25, 10, GEM_DARK); px(img, 27, 10, GEM_DARK)

    robe_rows = [
        (14, 9, 22), (15, 9, 22), (16, 8, 23), (17, 8, 23),
        (18, 7, 24), (19, 7, 24), (20, 6, 25), (21, 6, 25),
        (22, 5, 26), (23, 5, 26), (24, 4, 27), (25, 4, 27),
        (26, 3, 28),
    ]
    shade = {16, 20, 24}
    for yy, x0, x1 in robe_rows:
        if yy == 26:
            dither_row(img, yy, x0, x1, ROBE_DARK, ROBE_DEEP)
        elif yy in shade:
            row(img, yy, x0, x1, ROBE_DARK)
        else:
            row(img, yy, x0, x1, ROBE_MAIN)
    for yy in range(14, 26):
        px(img, 15, yy, ROBE_LIGHT); px(img, 16, yy, ROBE_LIGHT)

    for yy in range(6, 12):
        row(img, yy, 9, 10, BEARD); row(img, yy, 21, 22, BEARD)
    row(img, 12, 8, 9, BEARD); row(img, 12, 22, 23, BEARD)
    row(img, 13, 7, 8, BEARD); row(img, 13, 23, 24, BEARD)

    beard_rows = [
        (10, 13, 18), (11, 11, 20), (12, 10, 21), (13, 10, 21),
        (14, 11, 20), (15, 11, 20), (16, 12, 19), (17, 12, 19),
        (18, 13, 18), (19, 13, 18),
    ]
    for yy, x0, x1 in beard_rows:
        row(img, yy, x0, x1, BEARD)
    row(img, 20, 12, 13, BEARD); row(img, 20, 18, 19, BEARD)
    row(img, 21, 12, 12, BEARD); row(img, 21, 19, 19, BEARD)
    for yy in range(11, 20):
        px(img, 15, yy, BEARD_SHADE); px(img, 16, yy, BEARD_SHADE)

    for yy in (27, 28, 29):
        row(img, yy, 10, 12, BOOT if yy < 29 else BOOT_DARK)
        row(img, yy, 19, 21, BOOT if yy < 29 else BOOT_DARK)
    return outline_pass(img, OUTLINE)


# ============================================================ V2: Hooded Wanderer
# No pointed hat - deep rounded hood, face lost in shadow, hunched shoulders,
# bell-shaped ankle-length cloak (near-full canvas width at the hem), plain
# gnarled walking staff, no glowing gem. Much wider silhouette than V1.
def draw_v2():
    HOOD_MAIN, HOOD_DARK = (46, 44, 58, 255), (26, 24, 34, 255)
    CLOAK_MAIN, CLOAK_DARK, CLOAK_DEEP = (58, 54, 70, 255), (34, 32, 46, 255), (20, 18, 28, 255)
    STAFF = (58, 44, 34, 255)
    EYE = (150, 190, 210, 255)

    img = blank(W, H)
    # rounded hood, no point
    row(img, 3, 14, 17, HOOD_DARK)
    row(img, 4, 12, 19, HOOD_MAIN)
    row(img, 5, 10, 21, HOOD_MAIN)
    row(img, 6, 9, 22, HOOD_MAIN)
    row(img, 7, 8, 23, HOOD_DARK)   # hood opening shadow band

    # face lost in shadow - just glinting eyes, everything else dark
    row(img, 8, 12, 19, SKIN_SHADOW)
    px(img, 14, 9, EYE); px(img, 17, 9, EYE)
    row(img, 9, 12, 19, SKIN_SHADOW)
    row(img, 10, 12, 19, (60, 56, 66, 255))  # chin swallowed by shadow

    # hunched shoulders - start wide immediately below the hood, higher than V1
    row(img, 11, 5, 26, CLOAK_MAIN)
    row(img, 12, 3, 28, CLOAK_MAIN)

    # bell-shaped taper: much more dramatic flare than V1, hem near full width
    cloak_rows = [
        (13, 3, 28), (14, 2, 29), (15, 2, 29), (16, 1, 30),
        (17, 1, 30), (18, 0, 31), (19, 0, 31), (20, 0, 31),
        (21, 0, 31), (22, 0, 31), (23, 0, 31), (24, 0, 31),
        (25, 0, 31), (26, 0, 31), (27, 0, 31),
    ]
    shade = {15, 19, 23}
    for yy, x0, x1 in cloak_rows:
        if yy == 27:
            dither_row(img, yy, x0, x1, CLOAK_DARK, CLOAK_DEEP)
        elif yy in shade:
            row(img, yy, x0, x1, CLOAK_DARK)
        else:
            row(img, yy, x0, x1, CLOAK_MAIN)
    for yy in range(13, 27):
        px(img, 15, yy, (70, 66, 82, 255)); px(img, 16, yy, (70, 66, 82, 255))

    # staff drawn last so it reads on top of the cloak instead of being
    # painted over by the wide bell taper
    for yy in range(10, 30):
        px(img, 4, yy, STAFF)

    # ankle-length: only a sliver of boot shows at the very bottom, centered
    row(img, 28, 14, 16, BOOT)
    row(img, 29, 14, 16, BOOT_DARK)
    return outline_pass(img, OUTLINE)


# ============================================================ V3: Court Mage
# No hat - short neat hair + a tall ornate popped collar/ruff fanning out
# behind the head. Boxy, rectangular robe (barely tapers) instead of a cone,
# a cinched belt line, holds a closed book instead of a staff.
def draw_v3():
    HAIR = (60, 52, 46, 255)
    COLLAR_MAIN, COLLAR_DARK = (70, 30, 40, 255), (46, 18, 26, 255)
    ROBE_MAIN, ROBE_DARK, ROBE_LIGHT = (44, 46, 72, 255), (26, 28, 48, 255), (90, 96, 130, 255)
    BELT, BUCKLE = (40, 30, 20, 255), (150, 130, 60, 255)
    BOOK_COVER, BOOK_PAGES = (80, 24, 30, 255), (196, 180, 140, 255)
    EYE = (170, 190, 220, 255)

    img = blank(W, H)
    # collar fans out behind the head first (drawn first so head sits in front)
    row(img, 5, 8, 23, COLLAR_DARK)
    row(img, 6, 6, 25, COLLAR_MAIN)
    row(img, 7, 5, 26, COLLAR_MAIN)
    row(img, 8, 6, 25, COLLAR_DARK)

    # short neat hair, bare head (no hat)
    row(img, 4, 13, 18, HAIR)
    row(img, 5, 12, 19, HAIR)
    row(img, 6, 12, 19, SKIN)
    row(img, 7, 12, 19, SKIN)
    px(img, 14, 7, EYE); px(img, 17, 7, EYE)
    row(img, 8, 12, 19, SKIN)
    row(img, 9, 12, 19, SKIN_DARK)

    # boxy shoulders, straight sides (rectangular, not tapered)
    row(img, 10, 9, 22, ROBE_MAIN)
    row(img, 11, 8, 23, ROBE_MAIN)

    # rectangular robe body - same width almost top to bottom, minimal taper
    body_rows = [
        (12, 8, 23), (13, 8, 23), (14, 8, 23), (15, 8, 23),
        (16, 8, 23), (17, 8, 23),
    ]
    for yy, x0, x1 in body_rows:
        row(img, yy, x0, x1, ROBE_MAIN)
    for yy in range(12, 18):
        px(img, 15, yy, ROBE_LIGHT); px(img, 16, yy, ROBE_LIGHT)

    # cinched belt line breaks up the boxiness
    row(img, 18, 7, 24, BELT)
    px(img, 15, 18, BUCKLE); px(img, 16, 18, BUCKLE)

    # skirt below the belt, only slight flare (still boxy overall)
    skirt_rows = [
        (19, 7, 24), (20, 7, 24), (21, 6, 25), (22, 6, 25),
        (23, 5, 26), (24, 5, 26), (25, 4, 27),
    ]
    shade = {20, 23}
    for yy, x0, x1 in skirt_rows:
        color = ROBE_DARK if yy in shade else ROBE_MAIN
        row(img, yy, x0, x1, color)

    # book held at chest height, in front of the robe
    row(img, 13, 10, 15, BOOK_COVER)
    row(img, 14, 10, 15, BOOK_PAGES)
    row(img, 15, 10, 15, BOOK_COVER)

    for yy in (26, 27, 28):
        row(img, yy, 9, 12, BOOT if yy < 28 else BOOT_DARK)
        row(img, yy, 19, 22, BOOT if yy < 28 else BOOT_DARK)
    return outline_pass(img, OUTLINE)


# ============================================================ V4: Necromancer
# Tall, gaunt, narrow silhouette. Hat point bends to one side instead of
# standing straight. Jagged tattered hem (zigzag, not a smooth taper). Staff
# topped with a small skull instead of a gem. Glowing red eyes.
def draw_v4():
    HAT_MAIN, HAT_DARK = (34, 28, 40, 255), (18, 14, 22, 255)
    ROBE_MAIN, ROBE_DARK, ROBE_DEEP = (36, 30, 42, 255), (20, 16, 26, 255), (10, 8, 14, 255)
    STAFF, SKULL = (48, 40, 34, 255), (200, 195, 185, 255)
    EYE = (210, 40, 40, 255)

    img = blank(W, H)
    # crooked hat: point offset right and bent, leaning off-axis
    px(img, 18, 0, HAT_DARK)
    row(img, 1, 17, 19, HAT_MAIN)
    row(img, 2, 15, 20, HAT_MAIN)
    row(img, 3, 13, 21, HAT_MAIN)   # brim skewed, wider on the bent side
    row(img, 4, 12, 20, HAT_DARK)

    # gaunt face - narrower than the other variants
    row(img, 5, 14, 17, SKIN_DARK)
    px(img, 14, 5, EYE); px(img, 17, 5, EYE)
    row(img, 6, 14, 17, SKIN_DARK)
    row(img, 7, 14, 17, (60, 50, 56, 255))

    # narrow shoulders - much slimmer than V1/V2/V3
    row(img, 8, 11, 20, ROBE_MAIN)
    row(img, 9, 10, 21, ROBE_MAIN)

    for yy in range(7, 30):
        px(img, 23, yy, STAFF)
    px(img, 22, 6, SKULL); px(img, 23, 6, SKULL); px(img, 24, 6, SKULL)
    px(img, 22, 5, SKULL); px(img, 24, 5, SKULL)

    # tall, thin, mostly straight - very little taper (bony, not billowing)
    robe_rows = [
        (10, 10, 21), (11, 10, 21), (12, 9, 22), (13, 9, 22),
        (14, 9, 22), (15, 9, 22), (16, 8, 23), (17, 8, 23),
        (18, 8, 23), (19, 8, 23), (20, 7, 24), (21, 7, 24),
        (22, 7, 24), (23, 7, 24), (24, 6, 25), (25, 6, 25),
    ]
    shade = {13, 17, 21, 25}
    for yy, x0, x1 in robe_rows:
        color = ROBE_DARK if yy in shade else ROBE_MAIN
        row(img, yy, x0, x1, color)

    # jagged tattered hem instead of a clean edge - ragged strips at uneven depths
    hem_strips = [(6, 1), (9, 3), (12, 0), (15, 4), (18, 1), (21, 3), (24, 0)]
    for x_off, depth in hem_strips:
        xx = 6 + x_off
        for d in range(depth + 1):
            dither_row(img, 26 + d, xx, xx + 1, ROBE_DARK, ROBE_DEEP)

    for yy in (28, 29):
        row(img, yy, 12, 14, BOOT if yy < 29 else BOOT_DARK)
        row(img, yy, 17, 19, BOOT if yy < 29 else BOOT_DARK)
    return outline_pass(img, OUTLINE)


variants = [
    ("Classic Sorcerer", draw_v1()),
    ("Hooded Wanderer", draw_v2()),
    ("Court Mage", draw_v3()),
    ("Necromancer", draw_v4()),
]

sheet = compose_sheet([[frame] for _, frame in variants], W, H)
sheet.save(os.path.join(OUT, "variants_sheet.png"))

big = sheet.resize((sheet.width * SCALE, sheet.height * SCALE), Image.NEAREST)
big.save(os.path.join(OUT, "variants_sheet_preview.png"))

for name, frame in variants:
    slug = name.lower().replace(" ", "_")
    frame.save(os.path.join(OUT, f"{slug}.png"))

print("done", [name for name, _ in variants])

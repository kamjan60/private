"""8 different 64x64 heroes: 6 old-wizard variants (beard + long hair,
varied hat style AND varied width - not all canvas-wide) plus 1 warrior
and 1 elf archer. Single idle front frame each.
"""
import os
import sys

from PIL import Image

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
from pixel_lib import blank, px, row, dither_row, outline_pass, compose_sheet

W = H = 64
SCALE = 6
OUT = os.path.dirname(__file__)
CX = 32

OUTLINE = (12, 9, 14, 255)
BOOT = (24, 18, 28, 255)
BOOT_DARK = (14, 10, 16, 255)


def lerp(a, b, t):
    return a + (b - a) * t


# ============================================================ shared mage body
def draw_mage(hat, shoulder_half, hem_half, palette, staff_top):
    p = palette
    img = blank(W, H)

    face_half = 6
    if hat == "none":
        face_top = 12
        row(img, 4, CX - face_half - 1, CX + face_half, p["HAIR"])
        row(img, 6, CX - face_half - 2, CX + face_half + 1, p["HAIR"])
        row(img, 8, CX - face_half - 2, CX + face_half + 1, p["HAIR"])
        row(img, 10, CX - face_half - 1, CX + face_half, p["HAIR"])
    elif hat == "hood":
        face_top = 16
        row(img, 4, CX - 8, CX + 7, p["HAT_DARK"])
        row(img, 6, CX - 10, CX + 9, p["HAT_MAIN"])
        row(img, 8, CX - 11, CX + 10, p["HAT_MAIN"])
        row(img, 10, CX - 11, CX + 10, p["HAT_MAIN"])
        row(img, 12, CX - 10, CX + 9, p["HAT_DARK"])
        row(img, 14, CX - 9, CX + 8, p["HAT_DARK"])
    elif hat == "turban":
        face_top = 15
        row(img, 3, CX - 4, CX + 3, p["HAT_DARK"])
        row(img, 5, CX - 8, CX + 7, p["HAT_MAIN"])
        row(img, 7, CX - 9, CX + 8, p["BAND"])
        row(img, 9, CX - 9, CX + 8, p["HAT_MAIN"])
        row(img, 11, CX - 8, CX + 7, p["HAT_MAIN"])
        row(img, 13, CX - 7, CX + 6, p["HAT_DARK"])
        for yy in range(9, 20):
            px(img, CX + 9, yy, p["HAT_MAIN"])
            px(img, CX + 10, yy, p["HAT_DARK"])
    else:
        face_top = 20
        if hat == "cone":
            row(img, 2, CX - 1, CX, p["HAT_DARK"])
            row(img, 4, CX - 3, CX + 2, p["HAT_MAIN"])
            row(img, 6, CX - 5, CX + 4, p["HAT_MAIN"])
            row(img, 8, CX - 7, CX + 6, p["HAT_MAIN"])
            row(img, 10, CX - 10, CX + 9, p["HAT_MAIN"])
            px(img, CX - 10, 10, p["HAT_LIGHT"])
            row(img, 12, CX - 9, CX + 8, p["BAND"])
            row(img, 14, CX - 8, CX + 7, p["HAT_DARK"])
            row(img, 16, CX - 8, CX + 7, p["HAT_DARK"])
        elif hat == "wide_brim":
            row(img, 2, CX - 2, CX + 1, p["HAT_DARK"])
            row(img, 4, CX - 5, CX + 4, p["HAT_MAIN"])
            row(img, 6, CX - 9, CX + 8, p["HAT_MAIN"])
            row(img, 8, CX - 14, CX + 13, p["HAT_MAIN"])
            row(img, 10, CX - 12, CX + 11, p["BAND"])
            row(img, 12, CX - 10, CX + 9, p["HAT_DARK"])
            row(img, 14, CX - 9, CX + 8, p["HAT_DARK"])
            row(img, 16, CX - 8, CX + 7, p["HAT_DARK"])
        elif hat == "bent":
            row(img, 1, CX + 4, CX + 5, p["HAT_DARK"])
            row(img, 3, CX + 2, CX + 7, p["HAT_MAIN"])
            row(img, 5, CX - 2, CX + 8, p["HAT_MAIN"])
            row(img, 7, CX - 6, CX + 9, p["HAT_MAIN"])
            row(img, 9, CX - 9, CX + 8, p["HAT_MAIN"])
            row(img, 11, CX - 9, CX + 8, p["BAND"])
            row(img, 13, CX - 8, CX + 7, p["HAT_DARK"])
            row(img, 16, CX - 8, CX + 7, p["HAT_DARK"])
        for yy_pair in [(3, 4), (5, 6), (7, 8), (9, 10), (11, 12), (13, 14), (15, 16)]:
            pass

    row(img, face_top, CX - face_half, CX + face_half - 1, p["SKIN"])
    row(img, face_top + 1, CX - face_half, CX + face_half - 1, p["SKIN"])
    for dx in (-4, -3, 2, 3):
        px(img, CX + dx, face_top + 1, p["EYE"])
    row(img, face_top + 2, CX - face_half, CX + face_half - 1, p["SKIN"])
    row(img, face_top + 3, CX - face_half, CX + face_half - 1, p["SKIN_DARK"])

    for yy in range(face_top, face_top + 6):
        row(img, yy, CX - face_half - 4, CX - face_half - 1, p["HAIR"])
        row(img, yy, CX + face_half, CX + face_half + 3, p["HAIR"])
    row(img, face_top + 6, CX - face_half - 3, CX - face_half - 1, p["HAIR"])
    row(img, face_top + 6, CX + face_half, CX + face_half + 2, p["HAIR"])

    shoulder_y = face_top + 4
    row(img, shoulder_y, CX - shoulder_half, CX + shoulder_half - 1, p["ROBE_MAIN"])
    row(img, shoulder_y + 1, CX - shoulder_half - 2, CX + shoulder_half + 1, p["ROBE_MAIN"])

    robe_top = shoulder_y + 2
    robe_bottom = 55
    span = robe_bottom - robe_top
    for i in range(span + 1):
        y = robe_top + i
        t = i / span
        half = lerp(shoulder_half, hem_half, t)
        x0, x1 = int(CX - half), int(CX + half) - 1
        if i == span:
            dither_row(img, y, x0, x1, p["ROBE_DARK"], p["ROBE_DEEP"])
        elif i % 5 == 4:
            row(img, y, x0, x1, p["ROBE_DARK"])
        else:
            row(img, y, x0, x1, p["ROBE_MAIN"])
    for y in range(robe_top, robe_bottom):
        px(img, CX - 1, y, p["ROBE_LIGHT"])
        px(img, CX, y, p["ROBE_LIGHT"])

    staff_x = CX + shoulder_half + 5
    tip_y = shoulder_y - 4
    for y in range(tip_y + 2, 60):
        px(img, staff_x, y, p["STAFF"])
        px(img, staff_x + 1, y, p["STAFF"])
    if staff_top == "gem":
        row(img, tip_y, staff_x - 1, staff_x + 2, p["ACCENT"])
        px(img, staff_x - 2, tip_y, p["ACCENT_DARK"]); px(img, staff_x + 3, tip_y, p["ACCENT_DARK"])
    elif staff_top == "skull":
        row(img, tip_y, staff_x - 2, staff_x + 3, p["ACCENT"])
        row(img, tip_y - 2, staff_x - 1, staff_x + 2, p["ACCENT"])
    elif staff_top == "crystal":
        row(img, tip_y - 2, staff_x, staff_x + 1, p["ACCENT_DARK"])
        row(img, tip_y, staff_x - 1, staff_x + 2, p["ACCENT"])

    beard_top = face_top + 2
    beard_len = 20
    for i in range(beard_len - 3):
        y = beard_top + i
        t = i / (beard_len - 4)
        half = lerp(7, 1, t)
        x0, x1 = int(CX - half), int(CX + half) - 1
        row(img, y, x0, x1, p["HAIR"])
    for i in range(3):
        y = beard_top + beard_len - 3 + i
        offset = 2 + i
        row(img, y, CX - offset - 1, CX - offset, p["HAIR"])
        row(img, y, CX + offset - 1, CX + offset, p["HAIR"])
    for y in range(beard_top + 1, beard_top + beard_len - 4):
        px(img, CX - 1, y, p["HAIR_SHADE"])
        px(img, CX, y, p["HAIR_SHADE"])

    row(img, 57, CX - 9, CX - 4, BOOT)
    row(img, 58, CX - 9, CX - 4, BOOT)
    row(img, 59, CX - 9, CX - 4, BOOT_DARK)
    row(img, 57, CX + 3, CX + 8, BOOT)
    row(img, 58, CX + 3, CX + 8, BOOT)
    row(img, 59, CX + 3, CX + 8, BOOT_DARK)

    return outline_pass(img, OUTLINE)


# ============================================================ warrior
def draw_warrior(palette):
    p = palette
    img = blank(W, H)

    row(img, 6, CX - 6, CX + 5, p["METAL_DARK"])
    row(img, 8, CX - 8, CX + 7, p["METAL"])
    row(img, 10, CX - 8, CX + 7, p["METAL"])
    row(img, 10, CX - 2, CX + 1, p["SKIN_DARK"])  # eye-slit shadow
    for dx in (-2, -1, 1, 2):
        px(img, CX + dx, 12, p["EYE"])
    row(img, 12, CX - 8, CX + 7, p["METAL"])
    row(img, 14, CX - 7, CX + 6, p["METAL_DARK"])
    px(img, CX - 1, 4, p["ACCENT"]); px(img, CX, 4, p["ACCENT"])  # plume
    px(img, CX - 1, 2, p["ACCENT"]); px(img, CX, 2, p["ACCENT"])

    row(img, 15, CX - 5, CX + 4, p["SKIN"])  # jaw visible under open helm
    row(img, 16, CX - 5, CX + 4, p["SKIN_DARK"])

    # pauldrons (shoulder armor) - wide, blocky, distinct from a robe taper
    row(img, 17, CX - 14, CX + 13, p["METAL_DARK"])
    row(img, 18, CX - 15, CX + 14, p["METAL"])
    row(img, 19, CX - 15, CX + 14, p["METAL"])
    row(img, 20, CX - 13, CX + 12, p["METAL_DARK"])

    # breastplate torso, narrower than the pauldrons (real waist, not a cone)
    torso_rows = [
        (21, 10, 11), (22, 10, 11), (23, 9, 10), (24, 9, 10),
        (25, 9, 10), (26, 9, 10), (27, 9, 10), (28, 9, 10),
    ]
    for yy, hw0, hw1 in torso_rows:
        row(img, yy, CX - hw0, CX + hw1, p["METAL"])
    for yy in range(21, 29):
        px(img, CX - 1, yy, p["METAL_LIGHT"])
    row(img, 24, CX - 9, CX + 8, p["ACCENT_DARK"])  # chest emblem band

    # arms, visibly separate from torso (a real gap, not a merged blob)
    for yy in range(19, 34):
        row(img, yy, CX - 18, CX - 15, p["METAL"])
    for yy in range(19, 30):
        row(img, yy, CX + 15, CX + 18, p["METAL"])  # shield arm shorter, shield covers below

    # belt
    row(img, 29, CX - 10, CX + 9, p["BELT"])
    px(img, CX - 1, 29, p["ACCENT"]); px(img, CX, 29, p["ACCENT"])

    # legs, two separate armored columns with a real gap between them
    for yy in range(30, 52):
        row(img, yy, CX - 8, CX - 3, p["METAL_DARK"] if yy % 6 == 5 else p["METAL"])
        row(img, yy, CX + 3, CX + 8, p["METAL_DARK"] if yy % 6 == 5 else p["METAL"])

    # sabatons (armored boots)
    row(img, 52, CX - 8, CX - 3, p["METAL_DARK"])
    row(img, 53, CX - 8, CX - 3, p["METAL_DARK"])
    row(img, 52, CX + 3, CX + 8, p["METAL_DARK"])
    row(img, 53, CX + 3, CX + 8, p["METAL_DARK"])

    # sword, diagonal-ish held at the right side
    sword_x = CX + 20
    for i, yy in enumerate(range(10, 46)):
        px(img, sword_x, yy, p["BLADE"] if yy < 34 else p["HILT"])
    row(img, 34, sword_x - 3, sword_x + 3, p["HILT_DARK"])  # crossguard
    px(img, sword_x, 9, p["BLADE"])

    # round shield, left side
    for yy in range(20, 34):
        for xx in range(CX - 24, CX - 17):
            if (xx - (CX - 20)) ** 2 + (yy - 27) ** 2 <= 12:
                px(img, xx, yy, p["SHIELD"])
    px(img, CX - 20, 27, p["ACCENT"])

    return outline_pass(img, OUTLINE)


# ============================================================ elf archer
def draw_archer(palette):
    p = palette
    img = blank(W, H)

    # tied-back hair, no hood - crown + a rear ponytail
    row(img, 6, CX - 5, CX + 4, p["HAIR"])
    row(img, 8, CX - 6, CX + 5, p["HAIR"])
    for yy in range(10, 30):
        row(img, yy, CX + 3, CX + 5, p["HAIR"])  # ponytail down the back

    row(img, 9, CX - 6, CX + 5, p["SKIN"])
    row(img, 10, CX - 6, CX + 5, p["SKIN"])
    for dx in (-3, -2, 1, 2):
        px(img, CX + dx, 10, p["EYE"])
    # pointed ears - the elf tell
    px(img, CX - 8, 9, p["SKIN"]); px(img, CX - 9, 8, p["SKIN"])
    px(img, CX + 7, 9, p["SKIN"]); px(img, CX + 8, 8, p["SKIN"])
    row(img, 11, CX - 6, CX + 5, p["SKIN"])
    row(img, 12, CX - 6, CX + 5, p["SKIN_DARK"])

    # slender shoulders - narrower than the mage's, a real waist below
    row(img, 13, CX - 9, CX + 8, p["TUNIC_MAIN"])
    row(img, 14, CX - 10, CX + 9, p["TUNIC_MAIN"])

    torso_rows = [
        (15, 8), (16, 8), (17, 7), (18, 7), (19, 6), (20, 6),
        (21, 6), (22, 6), (23, 6), (24, 6),
    ]
    for i, (yy, hw) in enumerate(torso_rows):
        color = p["TUNIC_DARK"] if i % 4 == 3 else p["TUNIC_MAIN"]
        row(img, yy, CX - hw, CX + hw - 1, color)
    for yy in range(15, 25):
        px(img, CX - 1, yy, p["TUNIC_LIGHT"])

    row(img, 25, CX - 8, CX + 7, p["BELT"])
    px(img, CX - 1, 25, p["ACCENT"])

    # separate slender legs in leggings
    for yy in range(26, 52):
        color = p["LEG_DARK"] if yy % 6 == 5 else p["LEG_MAIN"]
        row(img, yy, CX - 6, CX - 2, color)
        row(img, yy, CX + 2, CX + 6, color)

    row(img, 52, CX - 6, CX - 2, BOOT)
    row(img, 53, CX - 6, CX - 2, BOOT_DARK)
    row(img, 52, CX + 2, CX + 6, BOOT)
    row(img, 53, CX + 2, CX + 6, BOOT_DARK)

    # quiver on the back
    for yy in range(12, 24):
        row(img, yy, CX - 16, CX - 13, p["QUIVER"])
    for i, xx in enumerate(range(CX - 15, CX - 12)):
        px(img, xx, 11 - (i % 2), p["ARROW_FLETCH"])

    # bow, held diagonally in front, full-height arc approximated with steps
    bow_pts = [
        (CX + 14, 8), (CX + 16, 12), (CX + 17, 18), (CX + 17, 24),
        (CX + 16, 30), (CX + 14, 34), (CX + 12, 38),
    ]
    for i in range(len(bow_pts) - 1):
        x0, y0 = bow_pts[i]
        x1, y1 = bow_pts[i + 1]
        steps = max(abs(x1 - x0), abs(y1 - y0), 1)
        for s in range(steps + 1):
            xx = round(lerp(x0, x1, s / steps))
            yy = round(lerp(y0, y1, s / steps))
            px(img, xx, yy, p["BOW"])
    # bowstring
    for yy in range(10, 37):
        px(img, CX + 13, yy, p["STRING"])

    return outline_pass(img, OUTLINE)


MAGE_PALETTES = {
    "Elder Sorcerer": dict(
        HAT_MAIN=(58, 40, 66, 255), HAT_DARK=(36, 24, 44, 255), HAT_LIGHT=(86, 62, 96, 255),
        BAND=(120, 96, 48, 255), SKIN=(188, 165, 142, 255), SKIN_DARK=(144, 122, 104, 255),
        ROBE_MAIN=(54, 40, 68, 255), ROBE_DARK=(30, 20, 42, 255), ROBE_LIGHT=(108, 130, 118, 255),
        ROBE_DEEP=(18, 12, 26, 255), STAFF=(66, 48, 36, 255), EYE=(200, 210, 150, 255),
        HAIR=(196, 194, 188, 255), HAIR_SHADE=(140, 138, 134, 255),
        ACCENT=(86, 210, 140, 255), ACCENT_DARK=(34, 110, 78, 255),
    ),
    "Storm Warden": dict(
        HAT_MAIN=(38, 52, 70, 255), HAT_DARK=(22, 32, 46, 255), HAT_LIGHT=(64, 84, 104, 255),
        BAND=(150, 150, 158, 255), SKIN=(180, 160, 148, 255), SKIN_DARK=(138, 118, 108, 255),
        ROBE_MAIN=(40, 58, 78, 255), ROBE_DARK=(22, 34, 50, 255), ROBE_LIGHT=(120, 150, 170, 255),
        ROBE_DEEP=(14, 20, 32, 255), STAFF=(70, 60, 48, 255), EYE=(170, 220, 235, 255),
        HAIR=(210, 214, 222, 255), HAIR_SHADE=(158, 162, 172, 255),
        ACCENT=(120, 200, 240, 255), ACCENT_DARK=(50, 120, 160, 255),
    ),
    "Hermit Druid": dict(
        HAT_MAIN=(0, 0, 0, 0), HAT_DARK=(0, 0, 0, 0), HAT_LIGHT=(0, 0, 0, 0), BAND=(0, 0, 0, 0),
        SKIN=(196, 168, 138, 255), SKIN_DARK=(150, 124, 100, 255),
        ROBE_MAIN=(58, 58, 34, 255), ROBE_DARK=(34, 34, 18, 255), ROBE_LIGHT=(126, 132, 74, 255),
        ROBE_DEEP=(20, 20, 10, 255), STAFF=(74, 56, 32, 255), EYE=(150, 200, 110, 255),
        HAIR=(222, 218, 200, 255), HAIR_SHADE=(168, 164, 148, 255),
        ACCENT=(150, 200, 110, 255), ACCENT_DARK=(80, 120, 60, 255),
    ),
    "Blood Magus": dict(
        HAT_MAIN=(60, 24, 30, 255), HAT_DARK=(36, 12, 16, 255), HAT_LIGHT=(94, 40, 46, 255),
        BAND=(90, 30, 30, 255), SKIN=(182, 156, 140, 255), SKIN_DARK=(140, 114, 100, 255),
        ROBE_MAIN=(70, 26, 32, 255), ROBE_DARK=(42, 14, 18, 255), ROBE_LIGHT=(140, 70, 66, 255),
        ROBE_DEEP=(24, 8, 10, 255), STAFF=(50, 32, 28, 255), EYE=(230, 120, 60, 255),
        HAIR=(210, 200, 195, 255), HAIR_SHADE=(158, 150, 146, 255),
        ACCENT=(220, 60, 60, 255), ACCENT_DARK=(120, 24, 24, 255),
    ),
    "Grey Pilgrim": dict(
        HAT_MAIN=(64, 64, 68, 255), HAT_DARK=(40, 40, 44, 255), HAT_LIGHT=(0, 0, 0, 0), BAND=(0, 0, 0, 0),
        SKIN=(190, 168, 148, 255), SKIN_DARK=(146, 124, 106, 255),
        ROBE_MAIN=(70, 70, 74, 255), ROBE_DARK=(42, 42, 46, 255), ROBE_LIGHT=(150, 150, 156, 255),
        ROBE_DEEP=(24, 24, 28, 255), STAFF=(78, 60, 42, 255), EYE=(220, 220, 225, 255),
        HAIR=(224, 222, 220, 255), HAIR_SHADE=(170, 168, 166, 255),
        ACCENT=(230, 230, 235, 255), ACCENT_DARK=(150, 150, 158, 255),
    ),
    "Desert Seer": dict(
        HAT_MAIN=(120, 90, 40, 255), HAT_DARK=(80, 58, 24, 255), HAT_LIGHT=(0, 0, 0, 0),
        BAND=(180, 140, 60, 255),
        SKIN=(168, 132, 96, 255), SKIN_DARK=(128, 98, 68, 255),
        ROBE_MAIN=(150, 110, 50, 255), ROBE_DARK=(100, 70, 30, 255), ROBE_LIGHT=(210, 170, 90, 255),
        ROBE_DEEP=(60, 40, 16, 255), STAFF=(90, 66, 40, 255), EYE=(60, 160, 170, 255),
        HAIR=(230, 220, 200, 255), HAIR_SHADE=(180, 170, 152, 255),
        ACCENT=(60, 190, 200, 255), ACCENT_DARK=(20, 110, 120, 255),
    ),
}

WARRIOR_PALETTE = dict(
    METAL=(120, 122, 130, 255), METAL_DARK=(70, 72, 80, 255), METAL_LIGHT=(180, 182, 190, 255),
    SKIN=(188, 156, 132, 255), SKIN_DARK=(144, 116, 96, 255), EYE=(40, 30, 26, 255),
    BELT=(70, 44, 26, 255), ACCENT=(200, 40, 40, 255), ACCENT_DARK=(120, 20, 20, 255),
    BLADE=(210, 212, 218, 255), HILT=(90, 60, 34, 255), HILT_DARK=(60, 40, 22, 255),
    SHIELD=(150, 30, 30, 255),
)

ARCHER_PALETTE = dict(
    HAIR=(220, 190, 100, 255), SKIN=(210, 178, 150, 255), SKIN_DARK=(168, 138, 112, 255),
    EYE=(60, 140, 90, 255), TUNIC_MAIN=(46, 90, 64, 255), TUNIC_DARK=(28, 60, 42, 255),
    TUNIC_LIGHT=(90, 150, 110, 255), BELT=(70, 50, 30, 255), ACCENT=(200, 170, 60, 255),
    LEG_MAIN=(58, 50, 40, 255), LEG_DARK=(38, 32, 26, 255),
    QUIVER=(70, 46, 30, 255), ARROW_FLETCH=(200, 60, 60, 255),
    BOW=(96, 66, 38, 255), STRING=(220, 220, 210, 255),
)


heroes = [
    ("Elder Sorcerer", draw_mage("cone", 16, 22, MAGE_PALETTES["Elder Sorcerer"], "gem")),
    ("Storm Warden", draw_mage("wide_brim", 15, 26, MAGE_PALETTES["Storm Warden"], "crystal")),
    ("Hermit Druid", draw_mage("none", 13, 15, MAGE_PALETTES["Hermit Druid"], "none")),
    ("Blood Magus", draw_mage("bent", 16, 24, MAGE_PALETTES["Blood Magus"], "skull")),
    ("Grey Pilgrim", draw_mage("hood", 14, 17, MAGE_PALETTES["Grey Pilgrim"], "none")),
    ("Desert Seer", draw_mage("turban", 15, 20, MAGE_PALETTES["Desert Seer"], "crystal")),
    ("Ironclad Warrior", draw_warrior(WARRIOR_PALETTE)),
    ("Elf Archer", draw_archer(ARCHER_PALETTE)),
]

sheet = compose_sheet([[frame] for _, frame in heroes], W, H)
sheet.save(os.path.join(OUT, "heroes_sheet.png"))
big = sheet.resize((sheet.width * SCALE, sheet.height * SCALE), Image.NEAREST)
big.save(os.path.join(OUT, "heroes_sheet_preview.png"))

for name, frame in heroes:
    slug = name.lower().replace(" ", "_")
    frame.save(os.path.join(OUT, f"{slug}.png"))

print("done", [n for n, _ in heroes])

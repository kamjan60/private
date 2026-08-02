"""Classic old-wizard variations - always an old man with a long beard and
long hair, differing only in hat style, palette, and staff. Scalable: unit
size U drives every coordinate, so the same layout renders at 16x32 (U=1)
or 32x64 (U=2) etc. Single idle front frame each.
"""
import os
import sys

from PIL import Image

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
from pixel_lib import blank, px, row, dither_row, outline_pass, compose_sheet

OUTLINE = (12, 9, 14, 255)
BOOT = (24, 18, 28, 255)
BOOT_DARK = (14, 10, 16, 255)


def draw_wizard(hat, palette, staff_top, U=1):
    """hat: 'cone' | 'wide_brim' | 'bent' | 'none'
    palette: dict of HAT_MAIN/HAT_DARK/HAT_LIGHT/BAND/SKIN/SKIN_DARK/
             ROBE_MAIN/ROBE_DARK/ROBE_LIGHT/ROBE_DEEP/STAFF/EYE/HAIR/HAIR_SHADE/
             ACCENT/ACCENT_DARK
    staff_top: 'gem' | 'skull' | 'none' | 'crystal'
    U: unit size in pixels - all layout numbers below are in "units" and
       get multiplied by U, so the whole sprite scales cleanly.
    """
    p = palette
    W, H = 16 * U, 32 * U

    def u(n):
        return n * U

    img = blank(W, H)

    # ---- hat (or bare head with just long hair, for 'none') ----
    face_top = u(6)
    if hat == "cone":
        row(img, u(0), u(7), u(8) + U - 1, p["HAT_DARK"])
        row(img, u(1), u(6), u(9) + U - 1, p["HAT_MAIN"])
        row(img, u(2), u(5), u(10) + U - 1, p["HAT_MAIN"])
        row(img, u(3), u(3), u(12) + U - 1, p["HAT_MAIN"])
        for i in range(U):
            px(img, u(3) + i, u(3), p["HAT_LIGHT"])
        row(img, u(4), u(4), u(11) + U - 1, p["BAND"])
        row(img, u(5), u(5), u(10) + U - 1, p["HAT_DARK"])
    elif hat == "wide_brim":
        row(img, u(0), u(6), u(9) + U - 1, p["HAT_DARK"])
        row(img, u(1), u(5), u(10) + U - 1, p["HAT_MAIN"])
        row(img, u(2), u(3), u(12) + U - 1, p["HAT_MAIN"])
        row(img, u(3), u(1), u(14) + U - 1, p["HAT_MAIN"])
        row(img, u(4), u(3), u(12) + U - 1, p["BAND"])
        row(img, u(5), u(4), u(11) + U - 1, p["HAT_DARK"])
    elif hat == "bent":
        row(img, u(0), u(9), u(9) + U - 1, p["HAT_DARK"])
        row(img, u(1), u(8), u(10) + U - 1, p["HAT_MAIN"])
        row(img, u(2), u(6), u(11) + U - 1, p["HAT_MAIN"])
        row(img, u(3), u(4), u(12) + U - 1, p["HAT_MAIN"])
        row(img, u(4), u(4), u(11) + U - 1, p["BAND"])
        row(img, u(5), u(5), u(10) + U - 1, p["HAT_DARK"])
    else:  # 'none' - bare head, hair takes over from the top
        face_top = u(4)
        row(img, u(4), u(5), u(10) + U - 1, p["HAIR"])
        row(img, u(5), u(4), u(11) + U - 1, p["HAIR"])

    # ---- face ----
    row(img, face_top, u(5), u(10) + U - 1, p["SKIN"])
    row(img, face_top + U, u(5), u(10) + U - 1, p["SKIN"])
    for i in range(U):
        px(img, u(6) + i, face_top + U, p["EYE"])
        px(img, u(9) + i, face_top + U, p["EYE"])
    row(img, face_top + 2 * U, u(5), u(10) + U - 1, p["SKIN"])
    row(img, face_top + 3 * U, u(5), u(10) + U - 1, p["SKIN_DARK"])

    # ---- long hair: sideburns beside the face, then past the shoulders ----
    hy = face_top
    for i in range(5):
        row(img, hy + i * U, u(3), u(4) + U - 1, p["HAIR"])
        row(img, hy + i * U, u(11), u(12) + U - 1, p["HAIR"])
    row(img, hy + 5 * U, u(2), u(3) + U - 1, p["HAIR"])
    row(img, hy + 5 * U, u(12), u(13) + U - 1, p["HAIR"])
    row(img, hy + 6 * U, u(1), u(2) + U - 1, p["HAIR"])
    row(img, hy + 6 * U, u(13), u(14) + U - 1, p["HAIR"])

    # ---- shoulders / robe ----
    sy = hy + 5 * U
    row(img, sy, u(2), u(13) + U - 1, p["ROBE_MAIN"])
    row(img, sy + U, u(1), u(14) + U - 1, p["ROBE_MAIN"])

    # staff, right side
    staff_x = u(14)
    boot_y = H - 3 * U
    for yy in range(sy - U, boot_y):
        for i in range(max(1, U // 2)):
            px(img, staff_x + i, yy, p["STAFF"])
    tip_y = sy - 2 * U
    if staff_top == "gem":
        row(img, tip_y, staff_x, staff_x + U - 1, p["ACCENT"])
        row(img, tip_y, staff_x - U, staff_x - 1, p["ACCENT_DARK"])
        row(img, tip_y, staff_x + U, min(staff_x + 2 * U - 1, W - 1), p["ACCENT_DARK"])
    elif staff_top == "skull":
        row(img, tip_y, staff_x - U, staff_x + U - 1, p["ACCENT"])
        row(img, tip_y - U, staff_x, staff_x + U - 1, p["ACCENT"])
    elif staff_top == "crystal":
        row(img, tip_y - U, staff_x, staff_x + U - 1, p["ACCENT_DARK"])
        row(img, tip_y, staff_x, staff_x + U - 1, p["ACCENT"])
    # 'none' -> plain staff, no topper

    # robe taper down to a wide hem, spanning dynamically to just above the boots
    start_y = sy + 2 * U
    end_y = boot_y - U          # last taper row, right before the boots
    span = end_y - start_y
    step = max(U, span // 12)   # ~12 taper steps regardless of scale
    yy = start_y
    fold = 0
    last_row_drawn = start_y
    while yy <= end_y:
        is_last = (yy + step) > end_y
        if is_last:
            x0, x1 = u(0), u(15) + U - 1
            dither_row(img, yy, x0, x1, p["ROBE_DARK"], p["ROBE_DEEP"])
        else:
            widen = fold >= 1
            x0 = u(1) if not widen else u(0)
            x1 = (u(14) + U - 1) if not widen else (u(15) + U - 1)
            color = p["ROBE_DARK"] if fold % 3 == 2 else p["ROBE_MAIN"]
            for r in range(min(step, end_y - yy + 1)):
                row(img, yy + r, x0, x1, color)
        last_row_drawn = yy
        yy += step
        fold += 1
    for i in range(U):
        for yy in range(start_y, end_y):
            px(img, u(7) + i, yy, p["ROBE_LIGHT"])
            px(img, u(8) + i, yy, p["ROBE_LIGHT"])

    # ---- beard: overlaps the mouth, curls into tufts at the tip ----
    by = face_top + 2 * U
    beard_rows = [
        (0, u(6), u(9) + U - 1), (U, u(5), u(10) + U - 1),
        (2 * U, u(4), u(11) + U - 1), (3 * U, u(4), u(11) + U - 1),
        (4 * U, u(5), u(10) + U - 1), (5 * U, u(5), u(10) + U - 1),
        (6 * U, u(6), u(9) + U - 1), (7 * U, u(6), u(9) + U - 1),
    ]
    for off, x0, x1 in beard_rows:
        row(img, by + off, x0, x1, p["HAIR"])
    row(img, by + 8 * U, u(5), u(6) + U - 1, p["HAIR"])
    row(img, by + 8 * U, u(9), u(10) + U - 1, p["HAIR"])
    row(img, by + 9 * U, u(5), u(5) + U - 1, p["HAIR"])
    row(img, by + 9 * U, u(10), u(10) + U - 1, p["HAIR"])
    for i in range(U):
        for yy in range(by + U, by + 8 * U):
            px(img, u(7) + i, yy, p["HAIR_SHADE"])
            px(img, u(8) + i, yy, p["HAIR_SHADE"])

    # boots
    row(img, boot_y, u(4), u(6) + U - 1, BOOT)
    row(img, boot_y, u(9), u(11) + U - 1, BOOT)
    row(img, boot_y + U, u(4), u(6) + U - 1, BOOT)
    row(img, boot_y + U, u(9), u(11) + U - 1, BOOT)
    row(img, boot_y + 2 * U, u(4), u(6) + U - 1, BOOT_DARK)
    row(img, boot_y + 2 * U, u(9), u(11) + U - 1, BOOT_DARK)

    return outline_pass(img, OUTLINE)


PALETTES = {
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
        HAT_MAIN=(0, 0, 0, 0), HAT_DARK=(0, 0, 0, 0), HAT_LIGHT=(0, 0, 0, 0),
        BAND=(0, 0, 0, 0), SKIN=(196, 168, 138, 255), SKIN_DARK=(150, 124, 100, 255),
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
}

VARIANT_SPECS = [
    ("Elder Sorcerer", "cone", "gem"),
    ("Storm Warden", "wide_brim", "crystal"),
    ("Hermit Druid", "none", "none"),
    ("Blood Magus", "bent", "skull"),
]


def build(U, out_dir, sheet_scale):
    os.makedirs(out_dir, exist_ok=True)
    W, H = 16 * U, 32 * U
    variants = [(name, draw_wizard(hat, PALETTES[name], top, U=U)) for name, hat, top in VARIANT_SPECS]

    sheet = compose_sheet([[frame] for _, frame in variants], W, H)
    sheet.save(os.path.join(out_dir, "classics_sheet.png"))

    big = sheet.resize((sheet.width * sheet_scale, sheet.height * sheet_scale), Image.NEAREST)
    big.save(os.path.join(out_dir, "classics_sheet_preview.png"))

    for name, frame in variants:
        slug = name.lower().replace(" ", "_")
        frame.save(os.path.join(out_dir, f"{slug}.png"))

    print("done", W, H, [n for n, _ in variants])


if __name__ == "__main__":
    build(U=1, out_dir=os.path.dirname(__file__), sheet_scale=10)

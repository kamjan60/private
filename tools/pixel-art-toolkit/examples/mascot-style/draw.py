"""Flat mascot / sticker style validation sprite - see
../../reference/flat-mascot-style.md. Curled hat tip, wavy beard bottom,
shepherd's-crook staff, gesturing off-hand, muted desaturated palette,
flat 2-tone shading, internal outline seams (not just outer silhouette).
"""
import os
import sys

from PIL import Image

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
from pixel_lib import blank, px, row, outline_pass, compose_sheet

W = H = 64
SCALE = 8
OUT = os.path.dirname(__file__)
CX = 32

OUTLINE      = (26, 22, 20, 255)
HAT_MAIN     = (90, 84, 80, 255)
HAT_DARK     = (56, 51, 47, 255)
HAT_LIGHT    = (138, 128, 120, 255)
FACE_SHADOW  = (46, 42, 40, 255)
ROBE_MAIN    = (120, 111, 102, 255)
ROBE_SHADOW  = (84, 76, 69, 255)
BEARD        = (238, 232, 220, 255)
BEARD_SHADE  = (199, 191, 175, 255)
STAFF        = (122, 90, 58, 255)
STAFF_DARK   = (90, 64, 38, 255)
SKIN         = (201, 171, 140, 255)
BOOT         = (40, 34, 30, 255)


def draw_mascot_wizard():
    img = blank(W, H)

    # ---- hat: wide brim, tall crown, tip curls into a hook ----
    px(img, CX + 5, 0, OUTLINE)
    row(img, 1, CX + 3, CX + 5, HAT_MAIN)
    row(img, 2, CX + 1, CX + 4, HAT_MAIN)
    row(img, 3, CX - 1, CX + 3, HAT_MAIN)
    row(img, 4, CX - 3, CX + 2, HAT_MAIN)
    row(img, 5, CX - 5, CX + 2, HAT_MAIN)
    row(img, 6, CX - 7, CX + 3, HAT_MAIN)
    row(img, 7, CX - 14, CX + 13, HAT_MAIN)      # wide brim
    row(img, 8, CX - 13, CX + 12, HAT_LIGHT)     # brim catch-light edge
    row(img, 9, CX - 9, CX + 8, OUTLINE)         # internal seam: hat -> face

    # ---- face: mostly lost in hat shadow, no visible eyes ----
    row(img, 10, CX - 6, CX + 5, FACE_SHADOW)
    row(img, 11, CX - 6, CX + 5, FACE_SHADOW)
    row(img, 12, CX - 6, CX + 5, FACE_SHADOW)

    # ---- shoulders / robe ----
    row(img, 13, CX - 6, CX + 5, ROBE_MAIN)
    row(img, 14, CX - 9, CX + 8, ROBE_MAIN)
    row(img, 15, CX - 11, CX + 10, ROBE_MAIN)

    robe_top, robe_bottom = 16, 54
    span = robe_bottom - robe_top
    for i in range(span + 1):
        y = robe_top + i
        t = i / span
        half = 11 + (14 - 11) * t   # very gentle taper - plain silhouette, not a dramatic cone
        x0, x1 = int(CX - half), int(CX + half) - 1
        row(img, y, x0, x1, ROBE_MAIN)
    # single flat shadow shape (not a ramp): the hem third, left side only
    for y in range(robe_top + int(span * 0.62), robe_bottom + 1):
        t = (y - robe_top) / span
        half = 11 + (14 - 11) * t
        x0 = int(CX - half)
        row(img, y, x0, x0 + int(half * 0.55), ROBE_SHADOW)
    row(img, robe_bottom, int(CX - 14), int(CX + 13), OUTLINE)  # hem seam

    # ---- beard: long, constant-width, wavy bottom edge (not a taper-to-point) ----
    # drawn per-column so the hem can dip/rise independently per column - a
    # real scalloped wave, not just a shrinking row width.
    beard_top = 12
    beard_x0, beard_x1 = CX - 6, CX + 5
    # bottom offset (rows below beard_top) per column - two gentle scallops
    depths = [7, 9, 11, 12, 11, 9, 9, 11, 12, 11, 9, 7]
    for i, x in enumerate(range(beard_x0, beard_x1 + 1)):
        bottom = beard_top + depths[i]
        for y in range(beard_top, bottom + 1):
            px(img, x, y, BEARD_SHADE if y == bottom else BEARD)
    for y in range(beard_top + 1, beard_top + 11):
        px(img, CX - 1, y, BEARD_SHADE)
        px(img, CX, y, BEARD_SHADE)
    # internal seam: beard -> robe, following the same wave
    for i, x in enumerate(range(beard_x0, beard_x1 + 1)):
        px(img, x, beard_top + depths[i] + 1, OUTLINE)

    # ---- staff: shepherd's-crook curl at the top ----
    staff_x = CX - 17
    for y in range(8, 58):
        px(img, staff_x, y, STAFF)
        px(img, staff_x + 1, y, STAFF)
    # crook: curls left-and-down from the top of the staff
    crook = [(0, -2), (1, -3), (2, -3), (3, -2), (3, 0), (2, 2), (1, 3)]
    for dx, dy in crook:
        px(img, staff_x + dx, 8 + dy, STAFF_DARK)
        px(img, staff_x + dx + 1, 8 + dy, STAFF)

    # ---- gesturing off-hand, drawn separate from the robe silhouette ----
    hand_y = 30
    row(img, hand_y, CX + 13, CX + 17, SKIN)
    row(img, hand_y + 1, CX + 13, CX + 17, SKIN)
    for i, fx in enumerate(range(CX + 13, CX + 18)):
        px(img, fx, hand_y + 2, SKIN if i % 2 == 0 else FACE_SHADOW)
    row(img, hand_y - 2, CX + 10, CX + 14, ROBE_MAIN)  # sleeve stub connecting to robe

    # holding hand for the staff
    row(img, 28, staff_x - 2, staff_x + 3, SKIN)
    row(img, 29, staff_x - 2, staff_x + 3, SKIN)

    # ---- boots peeking under the hem ----
    row(img, 55, CX - 6, CX - 2, BOOT)
    row(img, 56, CX - 6, CX - 2, BOOT)
    row(img, 55, CX + 2, CX + 6, BOOT)
    row(img, 56, CX + 2, CX + 6, BOOT)

    return outline_pass(img, OUTLINE)


frame = draw_mascot_wizard()
frame.save(os.path.join(OUT, "mascot_wizard.png"))
big = frame.resize((W * SCALE, H * SCALE), Image.NEAREST)
big.save(os.path.join(OUT, "mascot_wizard_preview.png"))
print("done")

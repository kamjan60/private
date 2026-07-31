"""64x64 knight - same dark-fantasy treatment as the wizards, different
skeleton.

Where the wizards are a cone (robe swallows the body, no limbs read), an
armoured figure has to show construction: pauldrons wider than the chest,
a waist, two separated legs, and arms clear of the torso. The silhouette
does the work - closed helm, hard shoulder line, weapon and shield
breaking the outline on both sides.

Style rules kept from the wizards: desaturated palette, flat two-tone
shading (base + one shadow, no ramps), 1px outline, and exactly one
saturated accent - here crimson, used on the plume and the shield device
and nowhere else.
"""
import os

from PIL import Image

SIZE = 64
SCALE = 8
OUT = os.path.dirname(__file__)

OUTLINE   = (18, 17, 24, 255)
STEEL_L   = (146, 155, 170, 255)
STEEL     = (100, 108, 124, 255)
STEEL_D   = (62, 68, 82, 255)
STEEL_DEEP = (40, 44, 54, 255)
LEATHER   = (74, 58, 44, 255)
LEATHER_D = (48, 37, 28, 255)
VOID      = (14, 13, 18, 255)
ACCENT    = (200, 50, 60, 255)      # the single saturated colour
ACCENT_D  = (122, 26, 34, 255)
BRASS     = (138, 112, 56, 255)     # tarnished, not shiny gold


class Canvas:
    def __init__(self):
        self.img = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
        self.p = self.img.load()

    def put(self, x, y, c):
        if 0 <= x < SIZE and 0 <= y < SIZE:
            self.p[x, y] = c

    def span(self, y, x0, x1, c):
        for x in range(x0, x1 + 1):
            self.put(x, y, c)

    def spans(self, table, c):
        for y, x0, x1 in table:
            self.span(y, x0, x1, c)

    def outline(self, color):
        src = self.img.copy().load()
        for y in range(SIZE):
            for x in range(SIZE):
                if src[x, y][3] != 0:
                    continue
                for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nx, ny = x + dx, y + dy
                    if 0 <= nx < SIZE and 0 <= ny < SIZE and src[nx, ny][3] != 0:
                        self.put(x, y, color)
                        break


c = Canvas()

# ------------------------------------------------------------------- legs
# Two separate columns with a real gap - the single change that stops an
# armoured figure reading as a robe.
for y in range(44, 56):
    tone = STEEL_D if y % 5 == 4 else STEEL
    c.span(y, 23, 30, tone)
    c.span(y, 33, 40, tone)
for y in range(44, 56):                    # lit edge, one light direction
    c.span(y, 23, 24, STEEL_L)
    c.span(y, 33, 34, STEEL_L)
    c.put(30, y, STEEL_DEEP)
    c.put(40, y, STEEL_DEEP)

# sabatons - wider than the greave so the figure plants on the ground
c.spans([(56, 21, 31), (57, 21, 31), (58, 21, 30)], STEEL_D)
c.spans([(56, 32, 42), (57, 32, 42), (58, 33, 42)], STEEL_D)
c.spans([(58, 21, 30), (58, 33, 42)], STEEL_DEEP)

# ------------------------------------------------------------------ torso
TORSO = [
    (23, 26, 37), (24, 25, 38), (25, 25, 38), (26, 24, 39),
    (27, 24, 39), (28, 24, 39), (29, 24, 39), (30, 24, 39),
    (31, 24, 39), (32, 25, 38), (33, 25, 38), (34, 26, 37),
    (35, 26, 37),
]
c.spans(TORSO, STEEL)
for y, x0, x1 in TORSO:                    # lit left plane, shaded right
    c.span(y, x0, x0 + 1, STEEL_L)
    c.span(y, x1 - 2, x1, STEEL_D)
# breastplate ridge down the centre line
for y in range(24, 35):
    c.put(31, y, STEEL_L)
    c.put(32, y, STEEL_D)

# belt
c.spans([(36, 24, 39), (37, 24, 39)], LEATHER)
c.span(37, 24, 39, LEATHER_D)
c.spans([(36, 30, 33)], BRASS)

# tassets - armoured skirt, flares then stops well above the knee
c.spans([
    (38, 23, 40), (39, 23, 40), (40, 22, 41), (41, 22, 41),
    (42, 22, 41), (43, 23, 40),
], STEEL)
c.spans([(42, 22, 41), (43, 23, 40)], STEEL_D)
c.put(31, 44, STEEL_DEEP); c.put(32, 44, STEEL_DEEP)

# -------------------------------------------------------------------- arms
# Left arm hangs behind the shield; the right one stops at shoulder height
# because that is where the shouldered grip sits.
for y in range(26, 42):
    c.span(y, 19, 23, STEEL_D if y % 5 == 4 else STEEL)
    c.put(19, y, STEEL_L)
for y in range(26, 34):
    c.span(y, 40, 44, STEEL_D if y % 5 == 4 else STEEL)
    c.put(40, y, STEEL_L)

# --------------------------------------------------------------- pauldrons
# Wider than the chest. This overhang is what makes armour read as armour.
c.spans([
    (21, 21, 42), (22, 19, 44), (23, 18, 45), (24, 17, 46),
    (25, 17, 46), (26, 18, 45), (27, 19, 44),
], STEEL)
c.spans([(24, 17, 19), (25, 17, 19), (26, 18, 20)], STEEL_L)
c.spans([(24, 44, 46), (25, 44, 46), (26, 43, 45), (27, 41, 44)], STEEL_D)
c.spans([(27, 19, 44)], STEEL_D)

# -------------------------------------------------------------------- helm
HELM = [
    (6, 27, 36), (7, 25, 38), (8, 24, 39), (9, 24, 39),
    (10, 23, 40), (11, 23, 40), (12, 23, 40), (13, 23, 40),
    (14, 23, 40), (15, 23, 40), (16, 24, 39), (17, 24, 39),
    (18, 25, 38), (19, 26, 37), (20, 27, 36),
]
c.spans(HELM, STEEL)
for y, x0, x1 in HELM:
    c.span(y, x0, x0 + 1, STEEL_L)
    c.span(y, x1 - 1, x1, STEEL_D)
# visor slit - a hard void, no eyes. Same trick as the necromancer's cowl.
c.spans([(13, 25, 38), (14, 25, 38)], VOID)
# breath holes, a sparse row so they read as perforation not as a stripe
for x in (28, 30, 32, 34, 36):
    c.put(x, 17, STEEL_DEEP)
# gorget under the helm
c.spans([(21, 27, 36), (22, 27, 36)], STEEL_D)

# ------------------------------------------------------------------- plume
c.spans([
    (0, 30, 32), (1, 29, 33), (2, 29, 34), (3, 30, 35),
    (4, 30, 36), (5, 30, 35), (6, 30, 33),
], ACCENT)
c.spans([(2, 33, 34), (3, 34, 35), (4, 34, 36), (5, 33, 35)], ACCENT_D)

# ------------------------------------------------------------------- sword
# Shouldered: the blade lies back against the pauldron and rises to the
# upper right, with the grip continuing down-left along the same axis and
# the hand closed on it at shoulder height. A sword held bolt-upright in a
# straight arm reads as a prop being presented, not carried.
# The blade's lower run overlaps the pauldron, so it visibly bears on the
# shoulder instead of hanging in the air beside it.
for y in range(5, 28):
    x0 = 42 + (27 - y) // 2
    c.put(x0, y, STEEL_L)
    c.put(x0 + 1, y, STEEL)
    c.put(x0 + 2, y, STEEL_D)
c.put(53, 4, STEEL_L); c.put(54, 4, STEEL)            # point

# crossguard sits just under the shoulder, across the blade axis
c.span(28, 39, 46, BRASS)
c.span(29, 40, 46, BRASS)

# grip drops from the guard to the hand; pommel caps it
c.spans([(30, 41, 43), (31, 41, 43), (32, 41, 43), (33, 41, 43)], LEATHER)
c.spans([(34, 40, 43), (35, 40, 43)], BRASS)

# gauntlet closed around the grip, at the end of the right arm
c.spans([(30, 40, 45), (31, 40, 45), (32, 40, 45), (33, 40, 44)], STEEL_D)
for y in range(30, 34):
    c.put(40, y, STEEL_L)

# ------------------------------------------------------------------ shield
SHIELD = [
    (25, 13, 25), (26, 12, 25), (27, 12, 25), (28, 12, 25),
    (29, 12, 25), (30, 12, 25), (31, 12, 25), (32, 13, 25),
    (33, 13, 25), (34, 14, 24), (35, 14, 24), (36, 15, 24),
    (37, 15, 23), (38, 16, 23), (39, 16, 22), (40, 17, 22),
    (41, 17, 21), (42, 18, 21), (43, 18, 20), (44, 19, 20),
]
c.spans(SHIELD, STEEL)
for y, x0, x1 in SHIELD:
    c.span(y, x0, x0 + 1, STEEL_L)
    c.span(y, x1 - 1, x1, STEEL_D)
# crimson device - the accent's second and last appearance
c.spans([(28, 17, 21), (29, 17, 21)], ACCENT)
for y in range(27, 39):
    c.put(18, y, ACCENT)
    c.put(19, y, ACCENT)
c.spans([(38, 18, 19), (37, 18, 19)], ACCENT_D)

c.outline(OUTLINE)

c.img.save(os.path.join(OUT, "knight.png"))
c.img.resize((SIZE * SCALE, SIZE * SCALE), Image.NEAREST).save(
    os.path.join(OUT, "knight_preview.png"))
print("done")

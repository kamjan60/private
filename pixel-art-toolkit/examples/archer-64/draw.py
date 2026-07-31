"""64x64 elf archer - same dark-fantasy treatment, a third body type.

The wizards are a cone, the warden is a slab; this one has to read as
slight. Narrow shoulders, a real waist, legs close together, and the mass
pushed out into the longbow and the cloak instead of onto the body. Where
the warden's silhouette is built from overhang, this one is built from a
tall thin vertical broken by one big curve.

One saturated accent as always: pale elven gold, on the circlet, the eyes
and the arrow fletchings.
"""
import math
import os

from PIL import Image

SIZE = 64
SCALE = 8
OUT = os.path.dirname(__file__)

OUTLINE    = (12, 16, 14, 255)
SKIN       = (198, 170, 138, 255)
SKIN_D     = (150, 122, 94, 255)
HAIR       = (214, 208, 190, 255)   # pale elven blond, desaturated
HAIR_D     = (158, 152, 136, 255)
CLOAK      = (44, 58, 46, 255)
CLOAK_D    = (26, 36, 30, 255)
CLOAK_HI   = (74, 92, 72, 255)
TUNIC      = (58, 70, 54, 255)
TUNIC_D    = (36, 46, 36, 255)
LEATHER    = (74, 58, 40, 255)
LEATHER_D  = (46, 36, 24, 255)
BOW        = (106, 74, 46, 255)
BOW_D      = (70, 48, 28, 255)
STRING     = (184, 180, 164, 255)
QUIVER     = (58, 44, 30, 255)
BOOT       = (38, 32, 24, 255)
BOOT_D     = (24, 20, 15, 255)
ACCENT     = (232, 200, 106, 255)   # elven gold
ACCENT_D   = (160, 132, 48, 255)


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

# =================================================================== cloak
# Drawn first: it hangs behind everything and is the only wide shape on the
# sprite, so the body can stay narrow without the silhouette going weedy.
# Kept deliberately narrow and stopping above the knee: flared wide it
# swallows the body and the figure reads as another robed caster.
for y in range(23, 43):
    t = (y - 23) / 19.0
    half = 7 + 6 * t
    x0, x1 = int(32 - half), int(32 + half)
    c.span(y, x0, x1, CLOAK if (y - 23) % 6 != 5 else CLOAK_D)
    c.put(x0, y, CLOAK_HI)
    c.put(x1, y, CLOAK_D)
# ragged hem
for x0, depth in ((19, 2), (23, 4), (28, 1), (32, 3), (37, 2), (41, 4)):
    for d in range(depth):
        c.span(43 + d, x0, x0 + 3, CLOAK_D)

# ================================================================== quiver
# Slung on the back, canted so it does not parrot the body's vertical.
for i, y in enumerate(range(20, 38)):
    x0 = 40 + i // 4
    c.span(y, x0, x0 + 5, QUIVER if y % 5 != 4 else LEATHER_D)
    c.put(x0, y, LEATHER)
# arrow shafts and gold fletchings above the rim
for dx in (0, 3, 6):
    x = 40 + dx
    for y in range(12, 21):
        c.put(x, y, BOW_D)
    c.spans([(12, x - 1, x + 1), (13, x - 1, x + 1)], ACCENT)
    c.put(x, 14, ACCENT_D)

# ==================================================================== bow
# A longbow: one continuous curve, tips further out than the belly. This is
# the sprite's big shape - everything else is deliberately narrow.
for y in range(5, 56):
    x = 13 + (y - 30) ** 2 / 96.0
    xi = int(round(x))
    c.put(xi, y, BOW)
    c.put(xi + 1, y, BOW_D)
c.spans([(4, 18, 20), (56, 18, 20)], BOW_D)     # nocks
for y in range(5, 56):                          # string, tip to tip
    c.put(20, y, STRING)

# =================================================================== legs
for y in range(40, 54):
    tone = TUNIC_D if y % 5 == 4 else LEATHER
    c.span(y, 27, 30, tone)
    c.span(y, 33, 36, tone)
    c.put(27, y, LEATHER)
    c.put(33, y, LEATHER)
c.spans([(54, 26, 31), (55, 26, 31), (56, 26, 30)], BOOT)
c.spans([(54, 32, 37), (55, 32, 37), (56, 33, 37)], BOOT)
c.spans([(56, 26, 30), (56, 33, 37)], BOOT_D)

# ================================================================== torso
TORSO = [
    (22, 26, 37), (23, 25, 38), (24, 25, 38), (25, 25, 38),
    (26, 26, 37), (27, 26, 37), (28, 26, 37), (29, 27, 36),
    (30, 27, 36), (31, 27, 36), (32, 27, 36), (33, 27, 36),
    (34, 26, 37), (35, 26, 37), (36, 26, 37), (37, 26, 37),
]
c.spans(TORSO, TUNIC)
for y, x0, x1 in TORSO:
    c.put(x0, y, CLOAK_HI)
    c.span(y, x1 - 1, x1, TUNIC_D)
# crossed baldric, the one diagonal on an otherwise vertical figure
for i, y in enumerate(range(23, 36)):
    x = 27 + i * 8 // 13
    c.put(x, y, LEATHER)
    c.put(x + 1, y, LEATHER_D)

c.spans([(38, 25, 38), (39, 25, 38)], LEATHER)
c.span(39, 25, 38, LEATHER_D)
c.spans([(38, 31, 32)], ACCENT_D)

# =================================================================== arms
# Left arm reaches out and down to the bow grip; right hangs.
for i, y in enumerate(range(24, 32)):
    x0 = 24 - i
    c.span(y, x0, x0 + 3, TUNIC if y % 5 != 4 else TUNIC_D)
    c.put(x0, y, CLOAK_HI)
for y in range(24, 38):
    c.span(y, 38, 41, TUNIC if y % 5 != 4 else TUNIC_D)
    c.put(38, y, CLOAK_HI)

# ==================================================================== head
# narrow face - a wide one reads dwarvish however long the ears are
c.spans([(12, 28, 35), (13, 28, 35), (14, 28, 35), (15, 28, 35),
         (16, 28, 35), (17, 28, 35), (18, 29, 34)], SKIN)
c.spans([(19, 29, 34), (20, 30, 33)], SKIN_D)

# hair: crown, then long strands past the shoulders
c.spans([(5, 29, 34), (6, 27, 36), (7, 26, 37), (8, 26, 37),
         (9, 26, 37), (10, 26, 37), (11, 26, 37)], HAIR)
for y in range(11, 30):
    c.span(y, 26, 27, HAIR)
    c.span(y, 36, 37, HAIR)
    c.put(27, y, HAIR_D)
    c.put(36, y, HAIR_D)
c.spans([(30, 26, 27), (31, 26, 27)], HAIR_D)
c.spans([(30, 36, 37), (31, 36, 37)], HAIR_D)
c.spans([(6, 27, 29), (7, 26, 28)], HAIR_D)

# Pointed ears: thin, angled up and back, sitting above eye level. Drawn
# thick and level with the eyes they merge with the face into one wide
# horizontal band and read as a hat brim rather than as ears.
c.spans([(10, 24, 25), (11, 24, 26), (12, 25, 27), (13, 26, 27)], SKIN)
c.spans([(10, 38, 39), (11, 37, 39), (12, 36, 38), (13, 36, 37)], SKIN)
c.put(24, 11, SKIN_D); c.put(39, 11, SKIN_D)
c.put(24, 10, SKIN); c.put(39, 10, SKIN)

# circlet and eyes carry the accent
c.span(11, 28, 35, ACCENT_D)
c.spans([(11, 30, 33)], ACCENT)
c.spans([(15, 29, 30), (15, 33, 34)], ACCENT)
c.spans([(16, 29, 30), (16, 33, 34)], ACCENT_D)

# =================================================================== hands
c.spans([(29, 16, 21), (30, 16, 21), (31, 17, 21)], SKIN)   # on the bow grip
c.put(16, 29, SKIN_D); c.put(16, 30, SKIN_D)
c.spans([(38, 38, 42), (39, 38, 42), (40, 39, 42)], SKIN)   # hanging

c.outline(OUTLINE)

c.img.save(os.path.join(OUT, "archer.png"))
c.img.resize((SIZE * SCALE, SIZE * SCALE), Image.NEAREST).save(
    os.path.join(OUT, "archer_preview.png"))
print("done")

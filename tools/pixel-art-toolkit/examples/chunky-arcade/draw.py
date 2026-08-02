"""Bright outline-free arcade wizard - thin, old, at 32x32 and 16x16.

A different pixel-art dialect from the rest of this repo. Where the
dark-fantasy sprites are outlined, desaturated and hold to a single
saturated accent, this one inverts all three:

* **No outline at all.** Shapes are held apart by hue and value contrast
  between neighbours.
* **Therefore saturate.** That follows directly - with no dark line doing
  the separating, desaturated neighbours fuse into one blob. Several
  competing saturated colours are the structure here, not a mistake.
* **Low resolution on purpose.** A feature gets two or three pixels, so
  nothing is subtle: both eyes become one dark bar and the nose is gone.

Build is thin and old rather than the usual wide robe cone - narrow
shoulders, a robe that barely flares, and a beard almost as long as the
body. The 16x16 is redrawn, not downscaled: at that size the hat brim and
the beard each get one row, so the proportions have to be re-planned
rather than resampled.
"""
import os

from PIL import Image

SCALE_32 = 12
SCALE_16 = 24
OUT = os.path.dirname(__file__)

PURPLE_L = (166, 118, 214, 255)
PURPLE   = (124, 80, 182, 255)
PURPLE_D = (92, 58, 140, 255)
SKIN     = (226, 172, 122, 255)
SKIN_D   = (196, 138, 92, 255)
EYEBAND  = (36, 24, 48, 255)
BEARD    = (214, 214, 222, 255)
BEARD_D  = (162, 162, 172, 255)
YELLOW   = (244, 216, 64, 255)
WOOD     = (140, 92, 58, 255)
WOOD_D   = (104, 64, 40, 255)
CRYS_L   = (170, 216, 248, 255)
CRYS     = (74, 158, 232, 255)
CRYS_D   = (42, 110, 200, 255)
GREEN    = (122, 208, 72, 255)
BOOT     = (32, 24, 40, 255)


class Grid:
    def __init__(self, w, h):
        self.w, self.h = w, h
        self.img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        self.p = self.img.load()

    def put(self, x, y, c):
        if 0 <= x < self.w and 0 <= y < self.h:
            self.p[x, y] = c

    def span(self, y, x0, x1, c):
        for x in range(x0, x1 + 1):
            self.put(x, y, c)

    def spans(self, table, c):
        for y, x0, x1 in table:
            self.span(y, x0, x1, c)


# ============================================================ 32x32 version
def build_32():
    g = Grid(32, 32)

    # staff, held clear on the right - the vertical the thin body leans against
    for y in range(4, 30):
        g.put(20, y, WOOD)
        g.put(21, y, WOOD_D)
    g.span(17, 20, 21, GREEN)

    # crystal head, three flat blues, no blending
    g.spans([(0, 19, 22), (1, 18, 23), (2, 18, 23), (3, 19, 22)], CRYS)
    g.spans([(0, 19, 20), (1, 18, 20)], CRYS_L)
    g.spans([(2, 22, 23), (3, 21, 22)], CRYS_D)

    # hat: narrow crown, brim only slightly wider - a broad brim on a thin
    # body reads as a mushroom
    g.spans([(1, 12, 13), (2, 11, 14), (3, 11, 14),
             (4, 10, 15), (5, 10, 15)], PURPLE)
    g.spans([(2, 11, 12), (3, 11, 12), (4, 10, 11), (5, 10, 11)], PURPLE_L)
    g.spans([(6, 8, 17), (7, 8, 17)], PURPLE_D)

    # face - one bar for the eyes, no room for two
    g.span(8, 10, 15, SKIN)
    g.span(9, 10, 15, EYEBAND)
    g.span(10, 10, 15, SKIN)
    g.put(15, 10, SKIN_D)

    # robe: barely flares. Shoulders 8 wide, hem 12 - an old man, not a cone
    ROBE = [
        (11, 9, 16), (12, 9, 16), (13, 9, 16), (14, 8, 17),
        (15, 8, 17), (16, 8, 17), (17, 8, 17), (18, 7, 18),
        (19, 7, 18), (20, 7, 18), (21, 7, 18), (22, 6, 18),
        (23, 6, 18), (24, 6, 18), (25, 6, 18), (26, 6, 17),
    ]
    g.spans(ROBE, PURPLE)
    for y, x0, x1 in ROBE:
        g.put(x0, y, PURPLE_L)
        g.put(x1, y, PURPLE_D)

    # beard over the robe - tucked behind the collar it collapses to a sliver
    g.spans([
        (11, 10, 15), (12, 10, 15), (13, 10, 15), (14, 10, 15),
        (15, 11, 14), (16, 11, 14), (17, 11, 14), (18, 12, 13),
        (19, 12, 13),
    ], BEARD)
    g.spans([(12, 14, 15), (13, 14, 15), (14, 14, 15), (15, 14, 14)], BEARD_D)

    for sx, sy in ((7, 17), (16, 15), (7, 23), (15, 21), (11, 25)):
        g.put(sx, sy, YELLOW)
        g.put(sx + 1, sy, YELLOW)

    g.spans([(15, 18, 20), (16, 18, 20)], SKIN)      # hand on the staff
    g.spans([(27, 7, 10), (28, 7, 10)], BOOT)
    g.spans([(27, 13, 16), (28, 13, 16)], BOOT)
    return g.img


# ============================================================ 16x16 version
def build_16():
    """Redrawn, not downscaled. At 16px the brim is one row and the beard
    three, so the figure has to be re-proportioned: the hat takes a quarter
    of the height and the robe stops at a flat hem with no boots showing."""
    g = Grid(16, 16)

    for y in range(2, 14):
        g.put(12, y, WOOD)
    g.put(12, 9, GREEN)
    g.spans([(0, 11, 13), (1, 11, 13)], CRYS)
    g.put(11, 0, CRYS_L)
    g.put(13, 1, CRYS_D)

    g.spans([(0, 6, 7), (1, 5, 8)], PURPLE)
    g.put(5, 1, PURPLE_L)
    g.span(2, 4, 9, PURPLE_D)           # brim: only 2px wider than the crown,
                                        # any more and it reads as a mushroom

    g.span(3, 5, 8, SKIN)
    g.span(4, 5, 8, EYEBAND)

    # 8px at the hem, not 10 - the whole point is a thin old man
    ROBE = [(5, 4, 9), (6, 4, 9), (7, 4, 9), (8, 3, 10),
            (9, 3, 10), (10, 3, 10), (11, 3, 10), (12, 3, 10)]
    g.spans(ROBE, PURPLE)
    for y, x0, x1 in ROBE:
        g.put(x0, y, PURPLE_L)
        g.put(x1, y, PURPLE_D)

    g.spans([(5, 5, 8), (6, 5, 8), (7, 6, 7), (8, 6, 7), (9, 6, 7)], BEARD)
    g.put(8, 5, BEARD_D); g.put(8, 6, BEARD_D); g.put(7, 9, BEARD_D)

    g.put(4, 10, YELLOW); g.put(9, 8, YELLOW)
    g.spans([(7, 11, 12)], SKIN)
    g.spans([(13, 4, 5), (13, 8, 9)], BOOT)
    return g.img


big = build_32()
big.save(os.path.join(OUT, "wizard_32.png"))
big.resize((32 * SCALE_32, 32 * SCALE_32), Image.NEAREST).save(
    os.path.join(OUT, "wizard_32_preview.png"))

small = build_16()
small.save(os.path.join(OUT, "wizard_16.png"))
small.resize((16 * SCALE_16, 16 * SCALE_16), Image.NEAREST).save(
    os.path.join(OUT, "wizard_16_preview.png"))

# side-by-side at matched display height, to check the 16 still reads
combo = Image.new("RGBA", (32 * 12 + 16 * 24 + 24, 32 * 12), (0, 0, 0, 0))
combo.paste(big.resize((32 * 12, 32 * 12), Image.NEAREST), (0, 0))
combo.paste(small.resize((16 * 24, 16 * 24), Image.NEAREST), (32 * 12 + 24, 0))
combo.save(os.path.join(OUT, "compare_preview.png"))
print("done")

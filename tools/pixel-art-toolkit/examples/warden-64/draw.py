"""64x64 primal warden - black plate, wolf helm, greatsword carried
horizontally across both shoulders.

Pose note: an earlier pass slung the sword diagonally down the back. That
forces the crossguard to sit at an angle to match the blade, and any guard
drawn as a level bar then reads as broken off-axis. Carrying the sword
level across the shoulders removes the problem instead of solving it - the
blade is horizontal, so the guard is simply vertical and everything is
square to everything else. It also gives a far stronger silhouette: the
weapon spans nearly the full canvas and breaks the outline on both sides.

Black armour cannot be painted black. At near-zero value there is no room
left to shade, so the plate sits at a dark slate, the outline carries the
true black, and cool rim light does the modelling.

One saturated accent, as with the other sprites: ember amber, in the
wolf's eyes and nowhere else.
"""
import os

from PIL import Image

SIZE = 64
SCALE = 8
OUT = os.path.dirname(__file__)

OUTLINE   = (10, 10, 14, 255)
PLATE_HI  = (86, 92, 106, 255)    # cool rim light - the only thing modelling the black
PLATE     = (46, 50, 60, 255)
PLATE_D   = (30, 33, 41, 255)
PLATE_DEEP = (19, 21, 27, 255)
FUR       = (68, 58, 46, 255)
FUR_HI    = (98, 84, 66, 255)
FUR_D     = (42, 35, 27, 255)
LEATHER   = (56, 44, 34, 255)
LEATHER_D = (36, 28, 21, 255)
BLADE_HI  = (140, 148, 162, 255)
BLADE     = (92, 100, 114, 255)
BLADE_D   = (58, 64, 76, 255)
BONE      = (206, 200, 184, 255)
VOID      = (12, 12, 16, 255)
ACCENT    = (240, 146, 46, 255)   # ember
ACCENT_D  = (150, 70, 16, 255)


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

# ==================================================================== legs
for y in range(45, 57):
    tone = PLATE_D if y % 5 == 4 else PLATE
    c.span(y, 24, 30, tone)
    c.span(y, 34, 40, tone)
for y in range(45, 57):
    c.span(y, 24, 25, PLATE_HI)
    c.span(y, 34, 35, PLATE_HI)
    c.put(30, y, PLATE_DEEP)
    c.put(40, y, PLATE_DEEP)

c.spans([(57, 22, 32), (58, 22, 32), (59, 23, 32)], PLATE_D)
c.spans([(57, 33, 42), (58, 33, 42), (59, 33, 41)], PLATE_D)
c.spans([(59, 23, 32), (59, 33, 41)], PLATE_DEEP)

# =================================================================== torso
TORSO = [
    (24, 26, 38), (25, 25, 39), (26, 25, 39), (27, 24, 40),
    (28, 24, 40), (29, 24, 40), (30, 24, 40), (31, 24, 40),
    (32, 25, 39), (33, 25, 39), (34, 26, 38), (35, 26, 38),
]
c.spans(TORSO, PLATE)
for y, x0, x1 in TORSO:
    c.span(y, x0, x0 + 1, PLATE_HI)
    c.span(y, x1 - 2, x1, PLATE_DEEP)
for y in range(25, 35):                    # sternum ridge
    c.put(31, y, PLATE_HI)
    c.put(32, y, PLATE_DEEP)

c.spans([(36, 24, 40), (37, 24, 40)], LEATHER)
c.span(37, 24, 40, LEATHER_D)
c.span(38, 24, 40, PLATE_DEEP)             # hard break so the belt reads
                                           # separately from the strips below

# hanging leather strips instead of plate tassets - less refined, primal.
# Uneven lengths, gaps between them, so they read as strips not a skirt.
for x0, end in ((24, 45), (29, 43), (34, 46), (38, 42)):
    for y in range(39, end):
        c.span(y, x0, x0 + 3, LEATHER if y % 4 != 3 else LEATHER_D)
    c.span(end - 1, x0, x0 + 3, LEATHER_D)

# ==================================================================== arms
# Left arm hangs; the right forearm comes up so the hand can rest over the
# blade lying on the shoulder.
for y in range(26, 40):
    c.span(y, 19, 23, PLATE_D if y % 5 == 4 else PLATE)
    c.put(19, y, PLATE_HI)
# right arm runs up on the diagonal so the hand can sit on the crossguard
for y in range(22, 32):
    x0 = 46 - (y - 22) * 5 // 9
    c.span(y, x0, x0 + 3, PLATE_D if y % 5 == 4 else PLATE)
    c.put(x0, y, PLATE_HI)

# ============================================================= fur mantle
FUR_ROWS = [
    (25, 18, 46), (26, 16, 47), (27, 15, 48),
    (28, 15, 48), (29, 16, 47),
]
c.spans(FUR_ROWS, FUR)
c.spans([(25, 18, 21), (26, 16, 20), (27, 15, 19)], FUR_HI)
c.spans([(27, 43, 48), (28, 42, 48), (29, 41, 47)], FUR_D)
for x0, depth in ((16, 3), (20, 1), (23, 4), (27, 2), (36, 2), (40, 4), (44, 1)):
    for d in range(depth):
        c.span(30 + d, x0, x0 + 2, FUR_D if d else FUR)

# =============================================================== greatsword
# Level across both shoulders, behind the neck. Drawn after the mantle so it
# visibly bears on the shoulders, and before the helm so it passes behind
# the head.
for y, tone in ((21, BLADE_HI), (22, BLADE), (23, BLADE_HI), (24, BLADE), (25, BLADE_D)):
    c.span(y, 5, 44, tone)
c.spans([(22, 3, 5), (23, 2, 5), (24, 3, 5)], BLADE)     # point
c.put(2, 23, BLADE_HI)

# crossguard: vertical, square to the blade - the whole reason for this pose
for y in range(16, 31):
    c.span(y, 45, 47, BLADE_D)
    c.put(45, y, BLADE_HI)

# grip and pommel continue past the guard, clear of the shoulder
for y in range(21, 26):
    c.span(y, 48, 56, LEATHER)
c.span(25, 48, 56, LEATHER_D)
c.spans([(20, 57, 60), (21, 57, 61), (22, 57, 61),
         (23, 57, 61), (24, 57, 61), (25, 57, 60)], BLADE_D)
c.spans([(21, 57, 58), (22, 57, 58)], BLADE_HI)

# =============================================================== wolf helm
# Drawn over the blade: the sword passes behind the head.
c.spans([(3, 23, 25), (4, 23, 26), (5, 23, 27), (6, 23, 28)], PLATE)
c.spans([(3, 38, 40), (4, 37, 40), (5, 36, 40), (6, 35, 40)], PLATE)
c.spans([(4, 24, 25), (5, 24, 26), (6, 24, 27)], PLATE_D)   # inner ear
c.spans([(4, 38, 39), (5, 37, 39), (6, 36, 39)], PLATE_D)

SKULL = [
    (7, 24, 39), (8, 23, 40), (9, 22, 41), (10, 22, 41),
    (11, 22, 41), (12, 22, 41), (13, 22, 41), (14, 23, 40),
    (15, 23, 40), (16, 24, 39),
]
c.spans(SKULL, PLATE)
for y, x0, x1 in SKULL:
    c.span(y, x0, x0 + 1, PLATE_HI)
    c.span(y, x1 - 2, x1, PLATE_DEEP)

# muzzle: a narrower block pushed down out of the skull
MUZZLE = [
    (15, 27, 36), (16, 27, 36), (17, 27, 36), (18, 28, 35),
    (19, 28, 35), (20, 29, 34),
]
c.spans(MUZZLE, PLATE_D)
c.spans([(15, 27, 28), (16, 27, 28), (17, 27, 28)], PLATE)
c.spans([(19, 29, 34), (20, 29, 34)], VOID)                 # muzzle shadow / mouth
c.spans([(19, 29, 30), (19, 33, 34)], BONE)                 # fangs

# brow ridge over the eyes, then the ember glow
c.spans([(10, 24, 29), (10, 34, 39)], PLATE_DEEP)
c.spans([(11, 25, 28), (11, 35, 38)], ACCENT_D)
c.spans([(11, 26, 27), (11, 36, 37)], ACCENT)
c.spans([(12, 26, 27), (12, 36, 37)], ACCENT_D)

# Gorget: this is what makes the sword read as being *behind* the warden
# rather than laid across his chest. The blade sits at shoulder height, so
# the head never covers it - the neck does, and it has to run the full
# depth of the blade to do that.
for y in range(21, 27):
    c.span(y, 27, 36, PLATE_D)
    c.put(27, y, PLATE)
    c.put(36, y, PLATE_DEEP)

# ================================================ hand closed on the crossguard
# Set on the diagonal, following the forearm, so it reads as a grip rather
# than a block parked next to the guard.
c.spans([(19, 44, 49), (20, 43, 49), (21, 43, 48), (22, 42, 48)], PLATE_D)
c.put(44, 19, PLATE_HI); c.put(43, 20, PLATE_HI); c.put(43, 21, PLATE_HI)
c.put(46, 20, PLATE_DEEP); c.put(46, 22, PLATE_DEEP)

c.outline(OUTLINE)

c.img.save(os.path.join(OUT, "warden.png"))
c.img.resize((SIZE * SCALE, SIZE * SCALE), Image.NEAREST).save(
    os.path.join(OUT, "warden_preview.png"))
print("done")

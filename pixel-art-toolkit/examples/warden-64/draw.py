"""64x64 primal warden - black plate, wolf helm, greatsword slung across
the back.

Two things drive the construction:

* The sword is drawn *first*, so the torso and legs occlude its middle
  run. Only the hilt above the right shoulder and the blade emerging past
  the left hip stay visible, which is what actually reads as "carried on
  the back" - a fully visible blade just looks held out behind.
* Black armour cannot be painted black. At near-zero value there is no
  room left to shade, so the plate sits at a dark slate and the *outline*
  is the true black; the silhouette still reads, and cool rim light does
  the modelling.

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

# ============================================================== greatsword
# Drawn before the body so the torso occludes its middle run.
# Blade descends from the guard down-left across the back.
# The angle matters more than the length: shallow, and the whole blade
# hides behind the torso; steep, and it emerges clear of the left hip.
for y in range(22, 58):
    x0 = int(42 - (y - 22) * 0.85)
    c.span(y, x0, x0 + 5, BLADE)
    c.put(x0, y, BLADE_HI)                 # lit long edge
    c.put(x0 + 5, y, BLADE_D)
    c.put(x0 + 2, y, BLADE_HI)             # fuller down the centre
c.spans([(58, 9, 12), (59, 10, 11)], BLADE_D)   # tip
# NOTE: only the blade goes behind the body. The hilt is drawn near the end
# of this file, on top of everything, because it stands clear above the
# shoulder - buried under the fur mantle it read as a shapeless lump.

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

# ============================================================= fur mantle
# Ragged lower edge - the silhouette break that separates this from the
# clean plate knight.
FUR_ROWS = [
    (21, 18, 46), (22, 16, 47), (23, 15, 48), (24, 15, 48),
    (25, 15, 48), (26, 16, 47),
]
c.spans(FUR_ROWS, FUR)
c.spans([(21, 18, 21), (22, 16, 20), (23, 15, 19), (24, 15, 18)], FUR_HI)
c.spans([(24, 43, 48), (25, 42, 48), (26, 41, 47)], FUR_D)
# ragged tufts hanging off the bottom, uneven lengths
for x0, depth in ((16, 3), (20, 1), (23, 4), (27, 2), (36, 2), (40, 4), (44, 1)):
    for d in range(depth):
        c.span(27 + d, x0, x0 + 2, FUR_D if d else FUR)

# ==================================================================== arms
for y in range(26, 40):
    c.span(y, 19, 23, PLATE_D if y % 5 == 4 else PLATE)
    c.put(19, y, PLATE_HI)
# right arm is raised, reaching back over the shoulder for the grip
for y in range(18, 31):
    x0 = 41 + (30 - y) // 4
    c.span(y, x0, x0 + 4, PLATE_D if y % 5 == 4 else PLATE)
    c.put(x0, y, PLATE_HI)

# =============================================================== wolf helm
# Ears on top, muzzle pushed forward and down, eyes the only saturated
# colour on the whole sprite.
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
c.put(31, 21, VOID); c.put(32, 21, VOID)

# brow ridge over the eyes, then the ember glow
c.spans([(10, 24, 29), (10, 34, 39)], PLATE_DEEP)
c.spans([(11, 25, 28), (11, 35, 38)], ACCENT_D)
c.spans([(11, 26, 27), (11, 36, 37)], ACCENT)
c.spans([(12, 26, 27), (12, 36, 37)], ACCENT_D)

# gorget filling the neck gap so the helm does not float
c.spans([(21, 27, 36), (22, 28, 35)], PLATE_D)

# ====================================== hilt, on top of everything else
# crossguard - long and straight, the giveaway that this is a two-hander
# Steel tones, not plate tones: against black armour a dark guard vanishes
# into the arm behind it.
c.spans([(19, 37, 55), (20, 38, 54)], BLADE_D)
c.spans([(19, 37, 39), (19, 52, 55)], BLADE_HI)

# grip, long enough for two hands
for y in range(12, 19):
    c.span(y, 44, 47, LEATHER)
    c.put(44, y, LEATHER_D)
# pommel
c.spans([(9, 43, 48), (10, 43, 48), (11, 44, 47)], PLATE_D)
c.spans([(9, 43, 44)], PLATE_HI)

# ================================================ hand closed on the grip
c.spans([(13, 42, 49), (14, 42, 49), (15, 42, 49), (16, 43, 49)], PLATE_D)
for y in range(13, 17):
    c.put(42, y, PLATE_HI)
c.spans([(14, 45, 46)], PLATE_DEEP)

c.outline(OUTLINE)

c.img.save(os.path.join(OUT, "warden.png"))
c.img.resize((SIZE * SCALE, SIZE * SCALE), Image.NEAREST).save(
    os.path.join(OUT, "warden_preview.png"))
print("done")

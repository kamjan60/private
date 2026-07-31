"""Pure hand-authored 64x64 pixel art - every pixel placed deliberately.

No vector supersampling here: the silhouette is written out as explicit
per-row spans, the way a pixel artist works a sprite row by row. Slower to
author than the shape-based renderer, but nothing is left to a downsample
filter - clusters, hem steps and the eye placement are exactly as specified.

Dark-fantasy palette: desaturated violets and greys, one saturated accent
(the staff orb + eye glow) and nothing else competing with it.
"""
import os

from PIL import Image

SIZE = 64
SCALE = 8
OUT = os.path.dirname(__file__)

OUT_L = (20, 17, 26, 255)      # outline
HAT_D = (36, 29, 48, 255)
HAT_M = (54, 43, 69, 255)
HAT_L = (74, 60, 92, 255)
BAND  = (122, 97, 52, 255)     # tarnished bronze
FACE  = (28, 23, 36, 255)      # face lost in brim shadow
SKIN  = (176, 141, 110, 255)
GLOW  = (124, 224, 192, 255)   # the ONE saturated accent
GLOW_D = (58, 138, 118, 255)
BEARD = (216, 212, 204, 255)
BRD_S = (160, 156, 150, 255)
ROBE  = (61, 51, 80, 255)
ROBE_D = (42, 35, 56, 255)
ROBE_L = (84, 74, 104, 255)
STAFF = (90, 66, 48, 255)
STF_D = (62, 45, 32, 255)
BOOT  = (26, 21, 32, 255)

img = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
px = img.load()


def put(x, y, c):
    if 0 <= x < SIZE and 0 <= y < SIZE:
        px[x, y] = c


def span(y, x0, x1, c):
    for x in range(x0, x1 + 1):
        put(x, y, c)


def spans(table, c):
    for y, x0, x1 in table:
        span(y, x0, x1, c)


# --------------------------------------------------------------- hat crown
# Tapers upward and hooks over to the right at the tip. Written as spans so
# the curl is exactly the shape intended, not whatever a filter produces.
spans([
    (4, 35, 38), (5, 34, 39), (6, 33, 39), (7, 32, 39),
    (8, 30, 38), (9, 29, 38), (10, 28, 38), (11, 27, 39),
    (12, 26, 39), (13, 26, 40), (14, 25, 40), (15, 24, 41),
    (16, 24, 41), (17, 23, 42), (18, 23, 42),
], HAT_M)
# the underside of the curl reads darker than the sunlit outer edge
spans([(5, 37, 39), (6, 36, 39), (7, 35, 39), (8, 34, 38)], HAT_D)
# single light edge down the left face of the crown - one light direction only
spans([(9, 29, 29), (10, 28, 28), (11, 27, 27), (12, 26, 26),
       (13, 26, 26), (14, 25, 25), (15, 24, 24), (16, 24, 24)], HAT_L)

# hat band
spans([(19, 22, 43), (20, 22, 43)], BAND)
span(20, 22, 43, BAND)
spans([(21, 22, 43)], HAT_D)

# --------------------------------------------------------------------- brim
spans([
    (22, 17, 46), (23, 13, 50), (24, 11, 52),
], HAT_M)
spans([
    (25, 12, 51), (26, 16, 47),
], HAT_D)

# --------------------------------------------------------------------- face
spans([(27, 25, 38), (28, 25, 38), (29, 25, 38),
       (30, 26, 37), (31, 26, 37)], FACE)
# glowing eyes - the accent used at its smallest and most deliberate
span(28, 27, 28, GLOW)
span(28, 35, 36, GLOW)
put(29, 27, GLOW_D); put(29, 28, GLOW_D)
put(29, 35, GLOW_D); put(29, 36, GLOW_D)

# --------------------------------------------------------------------- robe
ROBE_SIL = [
    (32, 24, 39), (33, 23, 40), (34, 22, 41), (35, 21, 42),
    (36, 21, 42), (37, 20, 43), (38, 20, 43), (39, 20, 43),
    (40, 19, 44), (41, 19, 44), (42, 19, 44), (43, 18, 45),
    (44, 18, 45), (45, 18, 45), (46, 17, 46), (47, 17, 46),
    (48, 17, 46), (49, 16, 47), (50, 16, 47), (51, 16, 47),
    (52, 16, 47), (53, 15, 48), (54, 15, 48), (55, 15, 48),
    (56, 15, 48),
]
spans(ROBE_SIL, ROBE)
# one flat shadow band across the hem third - two tones per surface, no ramp
for y, x0, x1 in ROBE_SIL:
    if y >= 48:
        span(y, x0, x1, ROBE_D)
# a single lit fold down the centre seam
for y, x0, x1 in ROBE_SIL:
    if y < 48:
        span(y, 31, 32, ROBE_L)

# -------------------------------------------------------------------- beard
spans([
    (30, 28, 35), (31, 27, 36), (32, 27, 36), (33, 26, 37),
    (34, 26, 37), (35, 26, 37), (36, 26, 37), (37, 26, 37),
    (38, 26, 37), (39, 26, 37), (40, 27, 36), (41, 27, 36),
    (42, 27, 36), (43, 28, 35), (44, 28, 35), (45, 29, 34),
    (46, 30, 33), (47, 31, 32),
], BEARD)
# shade only along the parting, so the beard still reads as one mass
for y in range(32, 46):
    put(31, y, BRD_S)
    put(32, y, BRD_S)

# -------------------------------------------------------------------- staff
for y in range(11, 58):
    put(12, y, STAFF)
    put(13, y, STF_D)
# orb at the head of the staff
spans([(6, 11, 14), (7, 10, 15), (8, 10, 15), (9, 10, 15), (10, 11, 14)], GLOW_D)
spans([(7, 11, 13), (8, 11, 14), (9, 12, 14)], GLOW)
put(7, 11, GLOW)

# -------------------------------------------------------------------- hands
spans([(36, 10, 15), (37, 10, 15), (38, 11, 15)], SKIN)
spans([(41, 43, 48), (42, 43, 48), (43, 44, 47)], SKIN)

# -------------------------------------------------------------------- boots
spans([(57, 22, 28), (58, 22, 28), (59, 22, 28)], BOOT)
spans([(57, 35, 41), (58, 35, 41), (59, 35, 41)], BOOT)

# ------------------------------------------------------------- 1px outline
src = img.copy()
sp = src.load()
for y in range(SIZE):
    for x in range(SIZE):
        if sp[x, y][3] != 0:
            continue
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nx, ny = x + dx, y + dy
            if 0 <= nx < SIZE and 0 <= ny < SIZE and sp[nx, ny][3] != 0:
                put(x, y, OUT_L)
                break

img.save(os.path.join(OUT, "pure_wizard.png"))
img.resize((SIZE * SCALE, SIZE * SCALE), Image.NEAREST).save(
    os.path.join(OUT, "pure_wizard_preview.png"))
print("done")

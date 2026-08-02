"""The substructure: what lies between the compartments.

The space around the rooms was pure black, which is not a background but
the absence of one. Structurally it is the inside of the hull -- frames,
girders, conduit runs, the odd vent -- so that is what it draws.

It is deliberately very low contrast. This tile sits under everything and
must never compete with a lit room: at a glance it should read as depth and
texture, not as somewhere you could walk. Values stay between the void and
roughly a third of the way to the floor plating.

Seamless at 96x96. The period is deliberately not the 32 of the floor tiles,
so the two grids never line up into one obvious lattice.
"""
import os
from PIL import Image

T = 96
OUT = os.path.dirname(os.path.abspath(__file__))

VOID     = (6, 8, 13, 255)
FRAME    = (14, 18, 28, 255)
FRAME_HI = (20, 26, 39, 255)
GIRDER   = (17, 22, 34, 255)
CONDUIT  = (12, 17, 27, 255)
BOLT     = (26, 33, 48, 255)
WARMHINT = (28, 22, 18, 255)


def lcg(seed):
    s = seed
    while True:
        s = (1103515245 * s + 12345) & 0x7FFFFFFF
        yield s / 0x7FFFFFFF


img = Image.new("RGBA", (T, T), VOID)
p = img.load()


def put(x, y, c):
    p[int(x) % T, int(y) % T] = c


def hline(y, x0, x1, c):
    for x in range(x0, x1):
        put(x, y, c)


def vline(x, y0, y1, c):
    for y in range(y0, y1):
        put(x, y, c)


# main frames: a wide bay every 48, so the eye reads structure rather than grid
for x in (0, 48):
    vline(x, 0, T, FRAME)
    vline(x + 1, 0, T, FRAME_HI)
    vline(x + 2, 0, T, GIRDER)
for y in (0, 48):
    hline(y, 0, T, FRAME)
    hline(y + 1, 0, T, FRAME_HI)
    hline(y + 2, 0, T, GIRDER)

# cross-bracing inside each bay, offset per bay so the tile does not read
# as four identical quarters
for (ox, oy, tilt) in ((0, 0, 1), (48, 0, -1), (0, 48, -1), (48, 48, 1)):
    for i in range(6, 42, 2):
        put(ox + i, oy + (i if tilt > 0 else 46 - i), GIRDER)

# conduit runs, thin and continuous so they carry the eye across the tile
for y in (20, 22, 68):
    hline(y, 0, T, CONDUIT)
for x in (34, 82):
    vline(x, 0, T, CONDUIT)

# bolts on the frames
rnd = lcg(9001)
for i in range(0, T, 12):
    put(0, i + 4, BOLT)
    put(48, i + 9, BOLT)
    put(i + 4, 0, BOLT)
    put(i + 9, 48, BOLT)

# a couple of cold spots and one warm one: something behind the wall is still
# drawing power, and it should be barely perceptible
for i in range(9):
    x, y = int(next(rnd) * T), int(next(rnd) * T)
    put(x, y, FRAME_HI)
put(58, 30, WARMHINT)
put(59, 30, WARMHINT)
put(58, 31, (22, 18, 15, 255))

img.save(os.path.join(OUT, "void.png"))

# tiled preview: the only way to see whether it repeats badly
tile = Image.new("RGBA", (T * 3, T * 3))
for ty in range(3):
    for tx in range(3):
        tile.paste(img, (tx * T, ty * T))
tile.resize((tile.width * 2, tile.height * 2), Image.NEAREST).save(
    os.path.join(OUT, "void_preview.png"))
print("wrote void.png", img.size, "(seamless)")

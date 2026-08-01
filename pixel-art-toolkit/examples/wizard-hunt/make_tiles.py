"""Floor tiles for the wreck: deck plating, corridor grating, and decals.

The renderer was filling every compartment with one flat colour, which read
as a diagram rather than a place. These are 32x32 tiles laid down with a
per-cell variant chosen from the tile's own coordinates, so a room looks
worked-in without anybody authoring a map.

Output is one strip, `tiles.png`, indexed left to right:

    0 1 2  deck plating, three wear states
    3 4    corridor grating, two wear states
    5      hazard chevron, for corridor mouths
    6 7    decals: a drain and a scorch, sprinkled sparsely
"""
import os
from PIL import Image

T = 32
OUT = os.path.dirname(os.path.abspath(__file__))

# The wreck's palette: cold steel with a little warmth in the rust, kept dark
# enough that the fog still does the work of hiding things.
BASE     = (18, 24, 38, 255)
PLATE    = (26, 34, 52, 255)
PLATE_HI = (36, 46, 68, 255)
PLATE_LO = (14, 19, 30, 255)
SEAM     = (11, 15, 24, 255)
RUST     = (58, 40, 34, 255)
RUST_HI  = (78, 54, 42, 255)
GRATE    = (20, 27, 42, 255)
GRATE_HI = (32, 42, 62, 255)
HAZARD   = (92, 72, 30, 255)
HAZARD_HI= (126, 98, 38, 255)


class Tile:
    def __init__(self, fill=BASE):
        self.img = Image.new("RGBA", (T, T), fill)
        self.p = self.img.load()

    def put(self, x, y, c):
        if 0 <= x < T and 0 <= y < T:
            self.p[x, y] = c

    def rect(self, x0, y0, x1, y1, c):
        for y in range(y0, y1 + 1):
            for x in range(x0, x1 + 1):
                self.put(x, y, c)

    def hline(self, y, x0, x1, c):
        for x in range(x0, x1 + 1):
            self.put(x, y, c)

    def vline(self, x, y0, y1, c):
        for y in range(y0, y1 + 1):
            self.put(x, y, c)


def deck(wear):
    """Riveted plating. Seams run the full tile so neighbours line up."""
    t = Tile(PLATE)
    # a lit top-left edge and a shaded bottom-right sells thickness at 1:1
    t.hline(0, 0, T - 1, SEAM)
    t.vline(0, 0, T - 1, SEAM)
    t.hline(1, 1, T - 1, PLATE_HI)
    t.vline(1, 1, T - 1, PLATE_HI)
    t.hline(T - 1, 0, T - 1, PLATE_LO)
    t.vline(T - 1, 0, T - 1, PLATE_LO)
    # rivets, inset from the seam
    for (x, y) in ((4, 4), (T - 5, 4), (4, T - 5), (T - 5, T - 5)):
        t.put(x, y, PLATE_HI)
        t.put(x, y + 1, PLATE_LO)
    if wear >= 1:
        # a half-seam across the middle: breaks the grid without new geometry
        t.hline(T // 2, 3, T - 4, PLATE_LO)
    if wear >= 2:
        for i in range(6):
            t.put(20 + (i % 3), 8 + i, RUST if i % 2 else RUST_HI)
            t.put(9 + (i % 2), 21 + (i % 4), RUST)
    return t.img


def grating(wear):
    """Corridor floor: open grid, darker, colder. A corridor should read as
    somewhere you pass through and would rather not linger."""
    t = Tile(GRATE)
    for x in range(0, T, 4):
        t.vline(x, 0, T - 1, GRATE_HI)
    for y in range(0, T, 8):
        t.hline(y, 0, T - 1, SEAM)
        t.hline(y + 1, 0, T - 1, GRATE_HI)
    t.hline(0, 0, T - 1, SEAM)
    t.vline(0, 0, T - 1, SEAM)
    if wear >= 1:
        for i in range(5):
            t.put(6 + i, 12 + (i % 3), RUST)
            t.put(23 - i, 25 - (i % 2), RUST_HI)
    return t.img


def hazard():
    """Chevrons, for the stretch of floor right inside a hatch."""
    t = Tile(GRATE)
    for y in range(T):
        for x in range(T):
            if ((x + y) // 6) % 2 == 0:
                t.put(x, y, HAZARD if (x + y) % 12 < 6 else HAZARD_HI)
    t.hline(0, 0, T - 1, SEAM)
    t.hline(T - 1, 0, T - 1, SEAM)
    return t.img


def drain():
    t = Tile(PLATE)
    t.rect(11, 11, 20, 20, PLATE_LO)
    for y in range(12, 20, 2):
        t.hline(y, 12, 19, SEAM)
    t.rect(11, 11, 20, 11, PLATE_HI)
    return t.img


def scorch():
    """Not a spell trace -- just an old burn, so the wreck looks used and a
    real residue mark still has to be shown by the renderer, not the floor."""
    t = Tile(PLATE)
    for i in range(9):
        t.rect(10 + i // 3, 9 + i, 21 - i // 2, 10 + i, (22, 22, 28, 255))
    t.rect(13, 13, 18, 18, (16, 16, 20, 255))
    return t.img


TILES = [deck(0), deck(1), deck(2), grating(0), grating(1), hazard(), drain(), scorch()]

sheet = Image.new("RGBA", (T * len(TILES), T), (0, 0, 0, 0))
for i, im in enumerate(TILES):
    sheet.paste(im, (i * T, 0), im)

sheet.save(os.path.join(OUT, "tiles.png"))
sheet.resize((sheet.width * 4, T * 4), Image.NEAREST).save(os.path.join(OUT, "tiles_preview.png"))
print("wrote tiles.png", sheet.size, f"({len(TILES)} tiles)")

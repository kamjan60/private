"""Bulkheads: the hull sections the compartments are built out of.

The walls were a three-pixel canvas stroke -- the only thing left on screen
that was not pixel art, and it showed next to plated floors and riveted
props. These are proper wall bands with a face, a lit edge, rivets and the
occasional weld seam, stamped along each wall segment.

The sheet is one strip with three known rectangles, because a wall is not a
square tile:

    H   (0,0)-(31,11)    horizontal band, 32 long x 12 thick
    V   (32,0)-(43,31)   vertical band, 12 thick x 32 long
    C   (44,0)-(55,11)   corner block, 12 x 12

Bands are drawn symmetrically -- lit on both faces -- so the renderer can
stamp them without knowing which side of the wall the room is on.
"""
import os
from PIL import Image

OUT = os.path.dirname(os.path.abspath(__file__))
TH = 12                     # wall thickness in pixels
L = 32                      # tile length

CORE     = (22, 28, 44, 255)
FACE     = (34, 44, 66, 255)
FACE_HI  = (52, 66, 96, 255)
EDGE     = (12, 16, 26, 255)
RIVET    = (68, 84, 116, 255)
RIVET_LO = (18, 23, 36, 255)
WELD     = (46, 40, 34, 255)
RUST     = (72, 50, 40, 255)


class W:
    def __init__(self, w, h):
        self.img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        self.p = self.img.load()
        self.w, self.h = w, h

    def put(self, x, y, c):
        if 0 <= int(x) < self.w and 0 <= int(y) < self.h:
            self.p[int(x), int(y)] = c

    def rect(self, x0, y0, x1, y1, c):
        for y in range(int(y0), int(y1) + 1):
            for x in range(int(x0), int(x1) + 1):
                self.put(x, y, c)


def band(length, thick, horizontal):
    """One run of bulkhead. Both faces are lit and the middle is dark, so a
    band reads as a solid slab from either side and the renderer never has to
    know which way the room is."""
    w, h = (length, thick) if horizontal else (thick, length)
    g = W(w, h)
    g.rect(0, 0, w - 1, h - 1, CORE)

    def across(i, c):
        """i counts through the thickness, whichever axis that is."""
        if horizontal:
            g.rect(0, i, w - 1, i, c)
        else:
            g.rect(i, 0, i, h - 1, c)

    across(0, EDGE)
    across(1, FACE_HI)
    across(2, FACE)
    across(thick - 1, EDGE)
    across(thick - 2, FACE_HI)
    across(thick - 3, FACE)

    # rivets down both faces, and a weld seam every other tile
    for n in range(3, length, 8):
        if horizontal:
            g.put(n, 2, RIVET); g.put(n, 3, RIVET_LO)
            g.put(n, thick - 3, RIVET); g.put(n, thick - 4, RIVET_LO)
        else:
            g.put(2, n, RIVET); g.put(3, n, RIVET_LO)
            g.put(thick - 3, n, RIVET); g.put(thick - 4, n, RIVET_LO)

    seam = length // 2
    if horizontal:
        g.rect(seam, 1, seam, thick - 2, WELD)
        g.rect(seam + 1, 1, seam + 1, thick - 2, EDGE)
        g.rect(6, thick - 4, 9, thick - 4, RUST)
    else:
        g.rect(1, seam, thick - 2, seam, WELD)
        g.rect(1, seam + 1, thick - 2, seam + 1, EDGE)
        g.rect(thick - 4, 6, thick - 4, 9, RUST)
    return g.img


def corner(thick):
    g = W(thick, thick)
    g.rect(0, 0, thick - 1, thick - 1, CORE)
    g.rect(0, 0, thick - 1, 0, EDGE)
    g.rect(0, 0, 0, thick - 1, EDGE)
    g.rect(1, 1, thick - 2, 1, FACE_HI)
    g.rect(1, 1, 1, thick - 2, FACE_HI)
    g.rect(2, 2, thick - 3, thick - 3, FACE)
    g.rect(thick - 1, 0, thick - 1, thick - 1, EDGE)
    g.rect(0, thick - 1, thick - 1, thick - 1, EDGE)
    g.put(thick // 2, thick // 2, RIVET)
    g.put(thick // 2, thick // 2 + 1, RIVET_LO)
    return g.img


sheet = Image.new("RGBA", (L + TH + TH, L), (0, 0, 0, 0))
sheet.paste(band(L, TH, True), (0, 0))
sheet.paste(band(L, TH, False), (L, 0))
sheet.paste(corner(TH), (L + TH, 0))
sheet.save(os.path.join(OUT, "walls.png"))

bg = Image.new("RGBA", (sheet.width, L), (13, 19, 32, 255))
bg.alpha_composite(sheet)
bg.resize((bg.width * 6, L * 6), Image.NEAREST).save(os.path.join(OUT, "walls_preview.png"))
print("wrote walls.png", sheet.size, f"(H 0,0 {L}x{TH} | V {L},0 {TH}x{L} | C {L+TH},0 {TH}x{TH})")

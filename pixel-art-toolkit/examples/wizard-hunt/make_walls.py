"""Bulkheads, and the things bolted to them.

A plain riveted band all the way round a room is still wallpaper: nothing
happens on it. These are wall sections with fittings -- viewports onto
space, wall screens, pipe runs, stencilled placards, vent louvres and torn
plating with the wiring showing.

The sheet is a strip of known rectangles, because a wall is not a square
tile. Horizontal sections are 32 long x 12 thick, vertical ones 12 x 32, and
there is one corner block:

    H[i]  (i*32, 0)              32 x 12   i in 0..6
    V[i]  (224 + i*12, 0)        12 x 32   i in 0..6
    C     (308, 0)               12 x 12

Feature order (both orientations): plain, viewport, screen, pipes, placard,
vent, damage.

Bands stay lit on both faces so the renderer can stamp one without knowing
which side of it the room is on. Viewports are the exception the client has
to think about: a window is only stamped where there is genuinely nothing on
the far side, which the client tests by sampling a point beyond the wall.
"""
import os
from PIL import Image

OUT = os.path.dirname(os.path.abspath(__file__))
TH, L = 12, 32
FEATURES = ["plain", "viewport", "screen", "pipes", "placard", "vent", "damage"]

CORE     = (22, 28, 44, 255)
FACE     = (34, 44, 66, 255)
FACE_HI  = (52, 66, 96, 255)
EDGE     = (12, 16, 26, 255)
RIVET    = (68, 84, 116, 255)
RIVET_LO = (18, 23, 36, 255)
WELD     = (46, 40, 34, 255)
RUST     = (72, 50, 40, 255)
SPACE    = (5, 6, 11, 255)
STAR     = (150, 172, 210, 255)
STAR_DIM = (74, 88, 116, 255)
GLASS    = (30, 44, 66, 255)
SCREEN   = (72, 158, 190, 255)
SCREEN_LO= (28, 70, 92, 255)
PIPE     = (86, 96, 116, 255)
PIPE_LO  = (44, 52, 68, 255)
BRASS    = (146, 116, 58, 255)
STENCIL  = (188, 168, 96, 255)
WIRE_A   = (150, 90, 40, 255)
WIRE_B   = (60, 90, 130, 255)
SPARK    = (255, 214, 150, 255)


def lcg(seed):
    s = seed
    while True:
        s = (1103515245 * s + 12345) & 0x7FFFFFFF
        yield s / 0x7FFFFFFF


class Band:
    """Draws in wall-local coordinates: `a` runs along the wall, `b` across
    its thickness. One set of drawing code serves both orientations."""

    def __init__(self, horizontal):
        self.hz = horizontal
        w, h = (L, TH) if horizontal else (TH, L)
        self.img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        self.p = self.img.load()
        self.w, self.h = w, h

    def put(self, a, b, c):
        x, y = (a, b) if self.hz else (b, a)
        if 0 <= int(x) < self.w and 0 <= int(y) < self.h:
            self.p[int(x), int(y)] = c

    def fill(self, a0, b0, a1, b1, c):
        for b in range(int(b0), int(b1) + 1):
            for a in range(int(a0), int(a1) + 1):
                self.put(a, b, c)

    def base(self):
        self.fill(0, 0, L - 1, TH - 1, CORE)
        for b, c in ((0, EDGE), (1, FACE_HI), (2, FACE),
                     (TH - 1, EDGE), (TH - 2, FACE_HI), (TH - 3, FACE)):
            self.fill(0, b, L - 1, b, c)
        for n in range(3, L, 8):
            self.put(n, 2, RIVET); self.put(n, 3, RIVET_LO)
            self.put(n, TH - 3, RIVET); self.put(n, TH - 4, RIVET_LO)


def make(feature, horizontal, seed):
    g = Band(horizontal)
    g.base()
    rnd = lcg(seed)

    if feature == "plain":
        g.fill(L // 2, 1, L // 2, TH - 2, WELD)
        g.fill(L // 2 + 1, 1, L // 2 + 1, TH - 2, EDGE)
        g.fill(6, TH - 4, 9, TH - 4, RUST)

    elif feature == "viewport":
        # a hole cut clean through: frame, glass, and space beyond
        g.fill(6, 2, L - 7, TH - 3, EDGE)
        g.fill(7, 3, L - 8, TH - 4, SPACE)
        for i in range(7):
            a = 8 + int(next(rnd) * (L - 17))
            b = 4 + int(next(rnd) * (TH - 8))
            g.put(a, b, STAR if next(rnd) > 0.55 else STAR_DIM)
        # a smear of reflection on the inner pane, so it reads as glass
        g.fill(8, 3, 12, 3, GLASS)
        g.fill(L - 12, TH - 4, L - 9, TH - 4, GLASS)
        for a in (6, L - 7):
            g.fill(a, 2, a, TH - 3, FACE_HI)

    elif feature == "screen":
        g.fill(8, 3, L - 9, TH - 4, EDGE)
        g.fill(9, 4, L - 10, TH - 5, SCREEN_LO)
        for b in range(4, TH - 4, 2):
            g.fill(10, b, L - 11, b, SCREEN)
        g.put(L - 9, 3, BRASS)

    elif feature == "pipes":
        for b in (3, TH - 4):
            g.fill(0, b, L - 1, b, PIPE)
            g.fill(0, b + 1, L - 1, b + 1, PIPE_LO)
        for a in (7, 23):
            g.fill(a, 2, a, TH - 3, PIPE_LO)
            g.put(a, 3, BRASS)
        g.fill(14, TH - 5, 17, TH - 5, RUST)

    elif feature == "placard":
        g.fill(5, 3, L - 6, TH - 4, EDGE)
        g.fill(6, 4, L - 7, TH - 5, (40, 36, 26, 255))
        for a in range(8, L - 8, 4):
            g.fill(a, 5, a + 1, TH - 6, STENCIL)
        g.fill(6, 4, L - 7, 4, BRASS)

    elif feature == "vent":
        g.fill(6, 3, L - 7, TH - 4, EDGE)
        for b in range(4, TH - 3, 2):
            g.fill(7, b, L - 8, b, (46, 56, 76, 255))
        g.put(6, 3, RIVET); g.put(L - 7, TH - 4, RIVET)

    elif feature == "damage":
        # plating torn back, wiring showing, one live contact
        for a in range(9, 23):
            depth = 2 + int(next(rnd) * 3)
            g.fill(a, 3, a, 3 + depth, (10, 12, 20, 255))
        g.fill(10, 5, 21, 5, WIRE_A)
        g.fill(12, 7, 19, 7, WIRE_B)
        for a in (11, 16, 20):
            g.put(a, 4, RUST)
        g.put(17, 6, SPARK)
        g.fill(8, 3, 8, TH - 4, FACE_HI)
        g.fill(23, 3, 23, TH - 4, FACE_HI)

    return g.img


def corner():
    g = Band(True)
    im = Image.new("RGBA", (TH, TH), CORE)
    p = im.load()
    for i in range(TH):
        p[i, 0] = EDGE; p[0, i] = EDGE
        p[i, TH - 1] = EDGE; p[TH - 1, i] = EDGE
    for i in range(1, TH - 1):
        p[i, 1] = FACE_HI; p[1, i] = FACE_HI
    for y in range(2, TH - 2):
        for x in range(2, TH - 2):
            p[x, y] = FACE
    p[TH // 2, TH // 2] = RIVET
    p[TH // 2, TH // 2 + 1] = RIVET_LO
    return im


W = L * len(FEATURES) + TH * len(FEATURES) + TH
sheet = Image.new("RGBA", (W, L), (0, 0, 0, 0))
for i, f in enumerate(FEATURES):
    sheet.paste(make(f, True, 100 + i * 7), (i * L, 0))
for i, f in enumerate(FEATURES):
    sheet.paste(make(f, False, 900 + i * 13), (L * len(FEATURES) + i * TH, 0))
sheet.paste(corner(), (L * len(FEATURES) + TH * len(FEATURES), 0))
sheet.save(os.path.join(OUT, "walls.png"))

bg = Image.new("RGBA", (W, L), (13, 19, 32, 255))
bg.alpha_composite(sheet)
bg.resize((bg.width * 4, L * 4), Image.NEAREST).save(os.path.join(OUT, "walls_preview.png"))
print("wrote walls.png", sheet.size, "features:", ", ".join(FEATURES))

"""The substructure between the compartments: machinery, not emptiness.

The first attempt drew this almost black and it read as nothing. Richness
and prominence are separate problems: draw the tile at full contrast like
any other art, then knock it back at the end with a desaturate-and-dim pass.
Drawing it dim in the first place just loses the detail.

So this is real equipment -- ribs, duct runs with flanges, cable looms,
pressure tanks, walkway grating, junction boxes, chevrons -- rendered
properly and then pushed behind the action by a single filter.

Seamless at 128. That period is deliberately not the floor's 32 nor the
wall's 32: equal periods line the grids up into one lattice.
"""
import os
from PIL import Image

T = 128
OUT = os.path.dirname(os.path.abspath(__file__))

# Drawn at full strength. GREY and DIM at the bottom put it in its place.
GREY_MIX = 0.62      # how far toward luminance
DIM = 0.46           # and how far down
TINT = (0.92, 0.97, 1.12)   # a touch of blue kept back, so it is not neutral

RIB      = (74, 84, 104, 255)
RIB_HI   = (108, 120, 144, 255)
RIB_LO   = (40, 47, 62, 255)
DUCT     = (92, 98, 112, 255)
DUCT_HI  = (128, 136, 152, 255)
DUCT_LO  = (52, 57, 70, 255)
FLANGE   = (150, 130, 84, 255)
CABLE_A  = (150, 92, 48, 255)
CABLE_B  = (66, 104, 150, 255)
CABLE_C  = (110, 116, 76, 255)
TANK     = (104, 100, 92, 255)
TANK_HI  = (146, 142, 132, 255)
TANK_LO  = (58, 56, 52, 255)
GRATE    = (70, 78, 94, 255)
GRATE_HI = (100, 110, 128, 255)
BOX      = (86, 94, 112, 255)
BOX_LED  = (120, 220, 160, 255)
CHEV_A   = (168, 138, 52, 255)
CHEV_B   = (44, 42, 36, 255)
BOLT     = (140, 150, 170, 255)
BACK     = (26, 31, 44, 255)
BACK_LO  = (18, 22, 33, 255)


def lcg(seed):
    s = seed
    while True:
        s = (1103515245 * s + 12345) & 0x7FFFFFFF
        yield s / 0x7FFFFFFF


img = Image.new("RGBA", (T, T), BACK)
px = img.load()


def put(x, y, c):
    px[int(x) % T, int(y) % T] = c


def rect(x0, y0, x1, y1, c):
    for y in range(int(y0), int(y1) + 1):
        for x in range(int(x0), int(x1) + 1):
            put(x, y, c)


def hline(y, x0, x1, c):
    rect(x0, y, x1, y, c)


def vline(x, y0, y1, c):
    rect(x, y0, x, y1, c)


rnd = lcg(31337)

# ---------------------------------------------------------------- backing
# a coarse plate grid so the whole tile is not one flat value
for y in range(0, T, 16):
    hline(y, 0, T - 1, BACK_LO)
for x in range(0, T, 16):
    vline(x, 0, T - 1, BACK_LO)

# ---------------------------------------------------------------- ribs
# structural frames crossing the tile, wrapping at the edges
for x in (0, 64):
    vline(x, 0, T - 1, RIB_LO)
    vline(x + 1, 0, T - 1, RIB)
    vline(x + 2, 0, T - 1, RIB_HI)
    vline(x + 3, 0, T - 1, RIB)
    vline(x + 4, 0, T - 1, RIB_LO)
    for y in range(5, T, 11):
        put(x + 2, y, BOLT)
for y in (32,):
    hline(y, 0, T - 1, RIB_LO)
    hline(y + 1, 0, T - 1, RIB)
    hline(y + 2, 0, T - 1, RIB_HI)
    hline(y + 3, 0, T - 1, RIB)
    hline(y + 4, 0, T - 1, RIB_LO)
    for x in range(5, T, 11):
        put(x, y + 2, BOLT)

# ---------------------------------------------------------------- ducts
# a fat duct running the full width, with flanged joints
DY = 74
rect(0, DY, T - 1, DY + 13, DUCT)
hline(DY, 0, T - 1, DUCT_LO)
hline(DY + 1, 0, T - 1, DUCT_HI)
hline(DY + 13, 0, T - 1, DUCT_LO)
hline(DY + 12, 0, T - 1, DUCT_LO)
for x in (18, 82):
    rect(x, DY - 2, x + 3, DY + 15, DUCT_LO)
    rect(x + 1, DY - 2, x + 2, DY + 15, FLANGE)

# a narrower duct dropping down the right-hand side
DX = 104
rect(DX, 0, DX + 8, T - 1, DUCT)
vline(DX, 0, T - 1, DUCT_LO)
vline(DX + 1, 0, T - 1, DUCT_HI)
vline(DX + 8, 0, T - 1, DUCT_LO)
for y in (24, 96):
    rect(DX - 2, y, DX + 10, y + 3, DUCT_LO)
    rect(DX - 2, y + 1, DX + 10, y + 1, FLANGE)

# ---------------------------------------------------------------- cables
# a loom sagging between two anchor points, three strands out of phase
import math
for i, col in enumerate((CABLE_A, CABLE_B, CABLE_C)):
    for x in range(0, T):
        y = 52 + int(6 * math.sin(x / 20.0)) + int(3 * math.sin(x / 7.0 + i)) + i * 2
        put(x, y, col)
for x in (12, 60, 100):
    rect(x, 44, x + 2, 48, BOX)

# ---------------------------------------------------------------- tank
rect(20, 4, 44, 26, TANK)
hline(4, 20, 44, TANK_HI)
vline(20, 4, 26, TANK_HI)
hline(26, 20, 44, TANK_LO)
vline(44, 4, 26, TANK_LO)
for y in (10, 18):
    hline(y, 20, 44, TANK_LO)
rect(29, 0, 35, 4, DUCT_LO)
rect(31, 0, 33, 4, FLANGE)

# ---------------------------------------------------------------- walkway
rect(0, 96, 96, 108, GRATE)
for x in range(0, 97, 4):
    vline(x, 96, 108, GRATE_HI)
hline(96, 0, 96, RIB_LO)
hline(108, 0, 96, RIB_LO)
for x in range(0, 97, 24):
    rect(x, 92, x + 2, 96, RIB)

# ---------------------------------------------------------------- junctions
for (bx, by) in ((70, 8), (8, 68), (86, 40)):
    rect(bx, by, bx + 11, by + 9, BOX)
    hline(by, bx, bx + 11, RIB_HI)
    hline(by + 9, bx, bx + 11, RIB_LO)
    put(bx + 3, by + 4, BOX_LED)
    put(bx + 7, by + 6, CABLE_A)
    rect(bx + 2, by + 7, bx + 9, by + 7, RIB_LO)

# ---------------------------------------------------------------- chevrons
for i in range(0, 24):
    x = 56 + i
    y = 116 + (i % 6)
    put(x, y, CHEV_A if (i // 3) % 2 == 0 else CHEV_B)
    put(x, y + 1, CHEV_A if (i // 3) % 2 == 0 else CHEV_B)

# a scatter of loose bolts and rust so nothing looks machine-perfect
for _ in range(26):
    x, y = int(next(rnd) * T), int(next(rnd) * T)
    put(x, y, BOLT if next(rnd) > 0.5 else RIB_LO)


# ---------------------------------------------------------------- knock back
# Richness and prominence are separate. The art above is drawn properly;
# this is the only thing that pushes it behind the action.
out = Image.new("RGBA", (T, T))
o = out.load()
for y in range(T):
    for x in range(T):
        r, g, b, a = px[x, y]
        lum = 0.299 * r + 0.587 * g + 0.114 * b
        r = r + (lum - r) * GREY_MIX
        g = g + (lum - g) * GREY_MIX
        b = b + (lum - b) * GREY_MIX
        o[x, y] = (
            max(0, min(255, int(r * DIM * TINT[0]))),
            max(0, min(255, int(g * DIM * TINT[1]))),
            max(0, min(255, int(b * DIM * TINT[2]))),
            255
        )

out.save(os.path.join(OUT, "void.png"))

tile = Image.new("RGBA", (T * 2, T * 2))
for ty in range(2):
    for tx in range(2):
        tile.paste(out, (tx * T, ty * T))
tile.resize((tile.width * 2, tile.height * 2), Image.NEAREST).save(
    os.path.join(OUT, "void_preview.png"))
print("wrote void.png", out.size, f"(seamless, grey {GREY_MIX}, dim {DIM})")

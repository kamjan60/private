"""Interior fittings for the wreck: one 32x32 prop per thing a room contains.

The compartments were named rooms full of identical plating -- a diagram
with labels on it. These are the objects that make a room look like the
thing it is called, plus the light fixtures that are still drawing power.

Anything with a screen, a coolant window or a live indicator is also a light
source: the client bakes a warm or cold pool under it when it stamps the
prop, which is where "some lights still work" comes from. A room with no lit
prop stays genuinely dark.

Index order matters -- the client indexes this sheet by position.
"""
import os
from PIL import Image

T = 32
OUT = os.path.dirname(os.path.abspath(__file__))

PLATE    = (26, 34, 52, 255)
PLATE_HI = (40, 52, 76, 255)
PLATE_LO = (14, 19, 30, 255)
DARK     = (11, 15, 24, 255)
STEEL    = (96, 108, 130, 255)
STEEL_LO = (58, 68, 86, 255)
BRASS    = (146, 116, 58, 255)
RUST     = (78, 54, 42, 255)
SCREEN   = (86, 196, 236, 255)
SCREEN_LO= (34, 96, 128, 255)
WARM     = (255, 206, 122, 255)
WARM_LO  = (150, 112, 56, 255)
CRYO     = (150, 220, 255, 255)
CORE     = (255, 150, 70, 255)
CLOTH    = (74, 44, 62, 255)
WOOD     = (86, 62, 44, 255)


class P:
    def __init__(self):
        self.img = Image.new("RGBA", (T, T), (0, 0, 0, 0))
        self.p = self.img.load()

    def put(self, x, y, c):
        if 0 <= int(x) < T and 0 <= int(y) < T:
            self.p[int(x), int(y)] = c

    def rect(self, x0, y0, x1, y1, c):
        for y in range(int(y0), int(y1) + 1):
            for x in range(int(x0), int(x1) + 1):
                self.put(x, y, c)

    def box(self, x0, y0, x1, y1, fill, hi=None, lo=None):
        """A block with a lit top edge and a shaded bottom -- the whole trick
        for reading solidity at this size."""
        self.rect(x0, y0, x1, y1, fill)
        if hi:
            self.rect(x0, y0, x1, y0, hi)
            self.rect(x0, y0, x0, y1, hi)
        if lo:
            self.rect(x0, y1, x1, y1, lo)
            self.rect(x1, y0, x1, y1, lo)


def console(f=0):
    p = P()
    p.box(5, 12, 26, 25, PLATE, PLATE_HI, PLATE_LO)
    p.box(7, 6, 24, 14, PLATE_LO, PLATE, DARK)
    p.rect(9, 8, 22, 12, SCREEN_LO)
    for y in range(8, 13, 2):
        p.rect(10, y, 21, y, SCREEN)
    p.rect(8, 17, 23, 17, STEEL_LO)
    # a chase running along the panel: the eye reads motion long before it
    # reads which lamp moved
    for i, x in enumerate(range(9, 23, 3)):
        p.put(x, 20, WARM if (i + f) % 3 else WARM_LO)
    return p.img


def screens(f=0):
    p = P()
    p.box(3, 5, 28, 20, PLATE_LO, PLATE, DARK)
    for i, x in enumerate((5, 13, 21)):
        p.rect(x, 7, x + 6, 17, SCREEN_LO)
        # one panel drops out on its own beat, so the bank never pulses as one
        if (f + i * 2) % 7 == 3:
            p.rect(x, 7, x + 6, 17, (16, 22, 34, 255))
            continue
        p.rect(x + 1, 8 + ((i + f) % 4), x + 5, 8 + ((i + f) % 4), SCREEN)
        p.rect(x + 1, 12 + ((i + f) % 3), x + 4, 12 + ((i + f) % 3), SCREEN)
    p.rect(3, 21, 28, 22, STEEL_LO)
    return p.img


def crate():
    p = P()
    p.box(6, 10, 25, 27, PLATE, PLATE_HI, PLATE_LO)
    p.rect(6, 16, 25, 16, PLATE_LO)
    p.rect(15, 10, 16, 27, PLATE_LO)
    p.rect(9, 12, 12, 14, BRASS)
    return p.img


def barrel():
    p = P()
    p.box(10, 8, 21, 27, STEEL_LO, STEEL, DARK)
    for y in (12, 18, 24):
        p.rect(10, y, 21, y, PLATE_LO)
    p.rect(11, 9, 20, 9, STEEL)
    p.rect(13, 14, 18, 16, RUST)
    return p.img


def bunk():
    p = P()
    p.box(3, 12, 28, 25, PLATE, PLATE_HI, PLATE_LO)
    p.rect(5, 14, 26, 19, CLOTH)
    p.rect(5, 14, 11, 19, (96, 60, 80, 255))
    p.rect(3, 25, 5, 28, STEEL_LO)
    p.rect(26, 25, 28, 28, STEEL_LO)
    return p.img


def locker():
    p = P()
    p.box(8, 4, 24, 28, PLATE, PLATE_HI, PLATE_LO)
    p.rect(16, 4, 16, 28, PLATE_LO)
    p.put(14, 16, BRASS)
    p.put(18, 16, BRASS)
    p.rect(10, 7, 14, 8, PLATE_LO)
    return p.img


def pew():
    p = P()
    p.box(3, 16, 28, 21, WOOD, (118, 86, 60, 255), (54, 38, 26, 255))
    p.rect(3, 8, 28, 15, (0, 0, 0, 0))
    p.box(3, 9, 28, 14, WOOD, (118, 86, 60, 255), (54, 38, 26, 255))
    p.rect(5, 22, 7, 27, (54, 38, 26, 255))
    p.rect(24, 22, 26, 27, (54, 38, 26, 255))
    return p.img


def altar(f=0):
    p = P()
    p.box(6, 14, 25, 27, PLATE, PLATE_HI, PLATE_LO)
    p.box(11, 6, 20, 15, PLATE_LO, PLATE, DARK)
    p.rect(13, 8, 18, 13, WARM_LO)
    # the flame leans, it does not just brighten
    lean = (0, 1, 0, -1)[f % 4]
    p.rect(14 + lean, 9, 17 + lean, 12, WARM)
    p.put(15 + lean, 7, (255, 236, 190, 255))
    p.rect(15, 3, 16, 6, BRASS)
    p.rect(13, 4, 18, 4, BRASS)
    return p.img


def cryopod(f=0):
    p = P()
    p.box(8, 3, 23, 29, PLATE, PLATE_HI, PLATE_LO)
    p.rect(11, 6, 20, 25, DARK)
    p.rect(11, 6, 20, 25, (18, 34, 48, 255))
    p.rect(12, 8, 19, 23, (26, 58, 78, 255))
    # coolant scrolling upward through the window
    for i, y in enumerate(range(9, 23, 3)):
        lit = (i + f) % 3 == 0
        p.rect(13, y, 18, y, CRYO if lit else (60, 130, 170, 255))
    p.rect(9, 27, 22, 28, STEEL_LO)
    p.put(10, 5, CRYO if f % 2 == 0 else (60, 130, 170, 255))
    return p.img


def rack(f=0):
    p = P()
    p.box(5, 2, 26, 29, PLATE_LO, PLATE, DARK)
    for i, y in enumerate(range(5, 27, 4)):
        p.rect(7, y, 24, y + 2, (20, 26, 40, 255))
        for x in range(8, 24, 3):
            p.put(x, y + 1, SCREEN if (x + i + f * 3) % 4 else (36, 46, 66, 255))
    return p.img


def bench():
    p = P()
    p.box(2, 13, 29, 19, STEEL_LO, STEEL, DARK)
    p.rect(4, 20, 6, 28, PLATE_LO)
    p.rect(25, 20, 27, 28, PLATE_LO)
    p.rect(8, 9, 13, 12, PLATE)
    p.rect(16, 10, 22, 12, BRASS)
    p.put(19, 8, WARM)
    return p.img


def pipes():
    p = P()
    for i, x in enumerate((6, 13, 20)):
        p.rect(x, 0, x + 3, 31, STEEL_LO)
        p.rect(x, 0, x, 31, STEEL)
        p.rect(x + 3, 0, x + 3, 31, DARK)
        for y in range(4 + i * 3, 32, 11):
            p.rect(x - 1, y, x + 4, y + 1, PLATE)
    p.rect(24, 12, 29, 15, RUST)
    return p.img


def core(f=0):
    p = P()
    p.box(4, 4, 27, 27, PLATE, PLATE_HI, PLATE_LO)
    p.rect(8, 8, 23, 23, DARK)
    # the core breathes: radius, not brightness, so it never strobes
    grow = (0, 1, 2, 1)[f % 4]
    for r in range(7 + grow, 1, -1):
        c = (255, 150 + max(0, 7 - r) * 12, 70, 255) if r > 4 else (255, 226, 170, 255)
        for y in range(16 - r, 16 + r + 1):
            for x in range(16 - r, 16 + r + 1):
                if (x - 16) ** 2 + (y - 16) ** 2 <= r * r:
                    p.put(x, y, c)
    p.rect(4, 28, 27, 29, STEEL_LO)
    return p.img


def table():
    p = P()
    p.box(3, 11, 28, 20, PLATE, PLATE_HI, PLATE_LO)
    p.rect(6, 21, 8, 27, PLATE_LO)
    p.rect(23, 21, 25, 27, PLATE_LO)
    p.rect(9, 13, 13, 15, STEEL_LO)
    p.rect(18, 14, 21, 16, BRASS)
    return p.img


def shelf():
    p = P()
    p.box(4, 2, 27, 29, PLATE_LO, PLATE, DARK)
    for y in range(5, 28, 6):
        p.rect(6, y, 25, y + 3, (22, 28, 44, 255))
        for x in range(7, 25, 2):
            p.rect(x, y, x, y + 3, (46, 40, 58, 255) if x % 4 else (64, 52, 44, 255))
        p.rect(6, y + 4, 25, y + 4, PLATE_LO)
    return p.img


def lamp(f=0):
    """The fixture that still works -- mostly. It gutters on one frame in four,
    which is the whole brief: a wreck where the lights are steady is a wreck
    that still has a crew."""
    p = P()
    p.rect(11, 2, 20, 3, STEEL_LO)
    dim = f % 4 == 2
    p.rect(10, 4, 21, 7, WARM_LO if not dim else (78, 58, 30, 255))
    p.rect(12, 4, 19, 6, WARM if not dim else WARM_LO)
    if not dim:
        p.rect(13, 8, 18, 8, (255, 236, 190, 255))
    return p.img


# name, draw fn, animated?  -- index order is the client's contract
PROPS = [
    ("konsola", console, True), ("ekrany", screens, True), ("skrzynia", crate, False),
    ("beczka", barrel, False), ("koja", bunk, False), ("szafka", locker, False),
    ("lawka", pew, False), ("oltarz", altar, True), ("kriokomora", cryopod, True),
    ("serwer", rack, True), ("warsztat", bench, False), ("rury", pipes, False),
    ("rdzen", core, True), ("stol", table, False), ("regal", shelf, False),
    ("lampa", lamp, True)
]
FRAMES = 4

# The still sheet: every prop at rest. The client bakes the unlit ones into a
# room's floor once and never touches them again.
sheet = Image.new("RGBA", (T * len(PROPS), T), (0, 0, 0, 0))
for i, (_, fn, anim) in enumerate(PROPS):
    im = fn(0) if anim else fn()
    sheet.paste(im, (i * T, 0), im)
sheet.save(os.path.join(OUT, "props.png"))

# The moving sheet: only the props that carry a light, four frames each, laid
# out as [prop index * FRAMES + frame]. These are drawn live over the baked
# floor, which is why they are a separate file rather than more columns here.
anim_idx = [i for i, (_, _, a) in enumerate(PROPS) if a]
fx = Image.new("RGBA", (T * len(PROPS) * FRAMES, T), (0, 0, 0, 0))
for i in anim_idx:
    fn = PROPS[i][1]
    for f in range(FRAMES):
        im = fn(f)
        fx.paste(im, ((i * FRAMES + f) * T, 0), im)
fx.save(os.path.join(OUT, "props_fx.png"))

bg = Image.new("RGBA", (T * len(PROPS), T), (26, 34, 52, 255))
bg.alpha_composite(sheet)
bg.resize((bg.width * 3, T * 3), Image.NEAREST).save(os.path.join(OUT, "props_preview.png"))

# a strip of just the animated ones, all four frames, for reviewing the motion
strip = Image.new("RGBA", (T * FRAMES, T * len(anim_idx)), (26, 34, 52, 255))
for r, i in enumerate(anim_idx):
    for f in range(FRAMES):
        im = PROPS[i][1](f)
        strip.paste(im, (f * T, r * T), im)
strip.resize((strip.width * 4, strip.height * 4), Image.NEAREST).save(
    os.path.join(OUT, "props_anim_preview.png"))

print("wrote props.png", sheet.size, "and props_fx.png", fx.size,
      "->", ", ".join(PROPS[i][0] for i in anim_idx))

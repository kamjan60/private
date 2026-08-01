"""Sprite sheets for "I'm Not a Wizard, Harry".

Six space marines in the outline-free arcade dialect, one sheet: columns
are the two walk frames, rows are variant*4 + direction (down/left/right/up).

The marines must be told apart at a glance for the deduction to work, so
each gets its own armour hue *and* a distinct visor colour. Silhouette is
identical across all six on purpose - the game is about who was where, not
about spotting a different-shaped body.
"""
import os

from PIL import Image

S = 32
DIRS = ["down", "left", "right", "up"]
OUT = os.path.dirname(__file__)

DARK   = (28, 30, 40, 255)
STEEL  = (96, 104, 122, 255)
STEEL_D = (58, 64, 78, 255)
BOOT   = (34, 34, 44, 255)
GUN    = (52, 56, 68, 255)
GUN_D  = (36, 38, 48, 255)

# armour main / light / dark, visor
VARIANTS = [
    ("Vance",  (196, 62, 62, 255),  (232, 112, 96, 255),  (128, 34, 40, 255),  (255, 214, 120, 255)),
    ("Okoye",  (58, 132, 208, 255), (110, 182, 240, 255), (32, 84, 148, 255),  (150, 240, 255, 255)),
    ("Reyes",  (72, 172, 96, 255),  (128, 216, 140, 255), (40, 112, 62, 255),  (196, 255, 160, 255)),
    ("Ilves",  (196, 148, 52, 255), (236, 196, 96, 255),  (134, 96, 26, 255),  (255, 236, 168, 255)),
    ("Petrov", (154, 92, 196, 255), (198, 148, 232, 255), (100, 56, 136, 255), (222, 178, 255, 255)),
    ("Sato",   (208, 122, 60, 255), (240, 172, 108, 255), (140, 76, 30, 255),  (255, 208, 150, 255)),
]


class G:
    def __init__(self):
        self.img = Image.new("RGBA", (S, S), (0, 0, 0, 0))
        self.p = self.img.load()

    def put(self, x, y, c):
        if 0 <= x < S and 0 <= y < S:
            self.p[x, y] = c

    def span(self, y, x0, x1, c):
        for x in range(x0, x1 + 1):
            self.put(x, y, c)

    def spans(self, t, c):
        for y, x0, x1 in t:
            self.span(y, x0, x1, c)


def marine(main, light, dark, visor, facing, step):
    g = G()
    dy = -1 if step == 1 else 0
    back = facing == "up"
    side = facing in ("left", "right")

    # backpack sits behind the body, and is the whole read of the back view
    if back:
        g.spans([(13 + dy, 10, 21), (14 + dy, 10, 21), (15 + dy, 10, 21),
                 (16 + dy, 10, 21), (17 + dy, 11, 20)], STEEL_D)
        g.spans([(12 + dy, 12, 14), (12 + dy, 17, 19)], STEEL)

    # legs: the only thing that animates, so they must sit on contrast
    off = 2 if step == 0 else -2
    la = off if not side else off
    ra = -off if not side else off // 2
    for x0, a in ((12, la), (16, ra)):
        for y in range(24 + dy, 29 + dy):
            g.span(y, x0 + a, x0 + 3 + a, dark if (y % 4 == 3) else main)
        g.span(29 + dy, x0 + a, x0 + 3 + a, BOOT)
        g.span(30 + dy, x0 + a, x0 + 3 + a, BOOT)

    # torso and pauldrons
    g.spans([(15 + dy, 9, 22), (16 + dy, 9, 22)], dark)
    g.spans([(17 + dy, 11, 20), (18 + dy, 11, 20), (19 + dy, 11, 20),
             (20 + dy, 11, 20), (21 + dy, 11, 20), (22 + dy, 11, 20),
             (23 + dy, 11, 20)], main)
    for y in range(17 + dy, 24 + dy):
        g.put(11, y, light)
        g.put(20, y, dark)
    g.span(20 + dy, 12, 19, dark)          # belt line

    # helmet
    g.spans([(7 + dy, 12, 19), (8 + dy, 11, 20), (9 + dy, 11, 20),
             (10 + dy, 11, 20), (11 + dy, 11, 20), (12 + dy, 11, 20),
             (13 + dy, 12, 19)], main if not back else dark)
    g.span(8 + dy, 11, 12, light)

    if not back:
        # visor: the per-marine identifier, kept bright so it reads small
        if side:
            vx0, vx1 = (11, 17) if facing == "left" else (14, 20)
        else:
            vx0, vx1 = 12, 19
        g.spans([(10 + dy, vx0, vx1), (11 + dy, vx0, vx1)], visor)
        g.span(12 + dy, vx0 + 1, vx1 - 1, DARK)

    # rifle, held across the body
    gx = 21 if facing != "left" else 6
    g.spans([(18 + dy, gx, gx + 4), (19 + dy, gx, gx + 4)], GUN)
    g.span(20 + dy, gx + 1, gx + 3, GUN_D)
    return g.img


sheet = Image.new("RGBA", (S * 2, S * 4 * len(VARIANTS)), (0, 0, 0, 0))
for vi, (name, main, light, dark, visor) in enumerate(VARIANTS):
    for di, d in enumerate(DIRS):
        for step in range(2):
            f = marine(main, light, dark, visor, d, step)
            sheet.paste(f, (step * S, (vi * 4 + di) * S), f)

sheet.save(os.path.join(OUT, "marines.png"))
sheet.resize((sheet.width * 3, sheet.height * 3), Image.NEAREST).save(
    os.path.join(OUT, "marines_preview.png"))
print("done", sheet.size, [v[0] for v in VARIANTS])

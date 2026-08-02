"""Arcade wizard walk cycles - 32x32, 4 directions x 3 frames.

Same outline-free saturated dialect as ../chunky-arcade/. Animating in
this style is mostly about what you *cannot* do: with no outline, a part
that moves 1px into a same-value neighbour simply vanishes, so the moving
elements (boots, hem, beard) all sit against a contrasting colour.

Facing is carried by the head and the staff. The torso is eight pixels
wide - there is nothing there to rotate.
"""
import os

from PIL import Image

SIZE = 32
SCALE = 8
OUT = os.path.dirname(__file__)

PURPLE_L = (166, 118, 214, 255)
PURPLE   = (124, 80, 182, 255)
PURPLE_D = (92, 58, 140, 255)
SKIN     = (226, 172, 122, 255)
SKIN_D   = (196, 138, 92, 255)
EYEBAND  = (36, 24, 48, 255)
BEARD    = (214, 214, 222, 255)
BEARD_D  = (162, 162, 172, 255)
YELLOW   = (244, 216, 64, 255)
WOOD     = (140, 92, 58, 255)
WOOD_D   = (104, 64, 40, 255)
CRYS_L   = (170, 216, 248, 255)
CRYS     = (74, 158, 232, 255)
CRYS_D   = (42, 110, 200, 255)
GREEN    = (122, 208, 72, 255)
BOOT     = (32, 24, 40, 255)


class Grid:
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


def staff(g, dy, sx):
    for y in range(4 + dy, 30 + dy):
        g.put(sx, y, WOOD)
        g.put(sx + 1, y, WOOD_D)
    g.span(17 + dy, sx, sx + 1, GREEN)
    g.spans([(0 + dy, sx - 1, sx + 2), (1 + dy, sx - 2, sx + 3),
             (2 + dy, sx - 2, sx + 3), (3 + dy, sx - 1, sx + 2)], CRYS)
    g.spans([(0 + dy, sx - 1, sx), (1 + dy, sx - 2, sx)], CRYS_L)
    g.spans([(2 + dy, sx + 2, sx + 3), (3 + dy, sx + 1, sx + 2)], CRYS_D)


def hat(g, dy, back=False):
    g.spans([(1 + dy, 12, 13), (2 + dy, 11, 14), (3 + dy, 11, 14),
             (4 + dy, 10, 15), (5 + dy, 10, 15)],
            PURPLE_D if back else PURPLE)
    if not back:
        g.spans([(2 + dy, 11, 12), (3 + dy, 11, 12),
                 (4 + dy, 10, 11), (5 + dy, 10, 11)], PURPLE_L)
    g.spans([(6 + dy, 8, 17), (7 + dy, 8, 17)], PURPLE_D)


def head(g, dy, facing):
    if facing == "back":
        # no face, no beard: walking away shows the underside of the brim
        # and the back of the robe collar
        g.span(8 + dy, 10, 15, PURPLE_D)
        return
    if facing == "left":
        fx0, fx1 = 9, 14
    elif facing == "right":
        fx0, fx1 = 11, 16
    else:
        fx0, fx1 = 10, 15
    g.span(8 + dy, fx0, fx1, SKIN)
    g.span(9 + dy, fx0, fx1, EYEBAND)
    g.span(10 + dy, fx0, fx1, SKIN)
    g.put(fx1, 10 + dy, SKIN_D)


def robe(g, dy):
    rows = [
        (11, 9, 16), (12, 9, 16), (13, 9, 16), (14, 8, 17),
        (15, 8, 17), (16, 8, 17), (17, 8, 17), (18, 7, 18),
        (19, 7, 18), (20, 7, 18), (21, 7, 18), (22, 6, 18),
        (23, 6, 18), (24, 6, 18), (25, 6, 18), (26, 6, 17),
    ]
    for y, x0, x1 in rows:
        g.span(y + dy, x0, x1, PURPLE)
        g.put(x0, y + dy, PURPLE_L)
        g.put(x1, y + dy, PURPLE_D)


def beard(g, dy, facing):
    if facing == "back":
        return
    shift = {"left": -1, "right": 1}.get(facing, 0)
    g.spans([
        (11 + dy, 10 + shift, 15 + shift), (12 + dy, 10 + shift, 15 + shift),
        (13 + dy, 10 + shift, 15 + shift), (14 + dy, 10 + shift, 15 + shift),
        (15 + dy, 11 + shift, 14 + shift), (16 + dy, 11 + shift, 14 + shift),
        (17 + dy, 11 + shift, 14 + shift), (18 + dy, 12 + shift, 13 + shift),
        (19 + dy, 12 + shift, 13 + shift),
    ], BEARD)
    g.spans([(12 + dy, 14 + shift, 15 + shift), (13 + dy, 14 + shift, 15 + shift),
             (14 + dy, 14 + shift, 15 + shift)], BEARD_D)


def stars(g, dy):
    for sx, sy in ((7, 17), (16, 15), (7, 23), (15, 21), (11, 25)):
        g.put(sx, sy + dy, YELLOW)
        g.put(sx + 1, sy + dy, YELLOW)


def boots(g, dy, la, ra):
    g.spans([(27 + dy, 7 + la, 10 + la), (28 + dy, 7 + la, 10 + la)], BOOT)
    g.spans([(27 + dy, 13 + ra, 16 + ra), (28 + dy, 13 + ra, 16 + ra)], BOOT)


def build(facing, step):
    g = Grid()
    dy = -1 if step == 1 else 0
    stride = (-2, 0, 2)[step]
    side = facing in ("left", "right")
    la, ra = (-stride, stride) if not side else (stride, stride // 2)

    sx = 6 if facing == "left" else 20
    staff(g, dy, sx)
    robe(g, dy)
    boots(g, dy, la, ra)
    stars(g, dy)
    hat(g, dy, back=(facing == "back"))
    head(g, dy, facing)
    beard(g, dy, facing)
    # hand on the staff, on whichever side it is being carried
    g.spans([(15 + dy, sx - 2, sx), (16 + dy, sx - 2, sx)] if facing == "left"
            else [(15 + dy, sx - 2, sx), (16 + dy, sx - 2, sx)], SKIN)
    return g.img


ROWS = [("down", "front"), ("left", "left"), ("right", "right"), ("up", "back")]

sheet = Image.new("RGBA", (SIZE * 3, SIZE * 4), (0, 0, 0, 0))
for r, (label, facing) in enumerate(ROWS):
    for step in range(3):
        f = build(facing, step)
        sheet.paste(f, (step * SIZE, r * SIZE), f)
        f.save(os.path.join(OUT, f"{label}_{step}.png"))

sheet.save(os.path.join(OUT, "arcade_sheet.png"))
sheet.resize((sheet.width * SCALE, sheet.height * SCALE), Image.NEAREST).save(
    os.path.join(OUT, "arcade_sheet_preview.png"))

for label, facing in ROWS:
    frames = [build(facing, s).resize((SIZE * 6, SIZE * 6), Image.NEAREST)
              for s in (0, 1, 2, 1)]
    frames[0].save(os.path.join(OUT, f"walk_{label}.gif"), save_all=True,
                   append_images=frames[1:], duration=130, loop=0, disposal=2)
print("done")

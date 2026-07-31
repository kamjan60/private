"""Elf archer animation set: 4-direction walk cycles plus a bow-draw attack.

Layout of the output sheet - 4 rows (down / left / right / up), 6 columns
(walk 0-2, attack 0-2).

Construction notes:

* Every frame is assembled from the same part functions with a direction
  argument, rather than being drawn by hand. Twenty-four hand-plotted
  frames would drift out of register with each other almost immediately.
* The passing frame of each walk lifts the whole body 1px. Without that
  bob the cycle reads as a slide even with the legs animating correctly.
* Facing is carried by the head and the bow, not by the torso: at this
  size a torso has too few pixels to show rotation, so the head loses its
  face when walking away and the bow swaps sides.
"""
import os

from PIL import Image

SIZE = 64
SCALE = 5
OUT = os.path.dirname(__file__)
CX = 32

OUTLINE   = (12, 16, 14, 255)
SKIN      = (198, 170, 138, 255)
SKIN_D    = (150, 122, 94, 255)
HAIR      = (214, 208, 190, 255)
HAIR_D    = (158, 152, 136, 255)
CLOAK     = (44, 58, 46, 255)
CLOAK_D   = (26, 36, 30, 255)
CLOAK_HI  = (74, 92, 72, 255)
TUNIC     = (58, 70, 54, 255)
TUNIC_D   = (36, 46, 36, 255)
LEATHER   = (74, 58, 40, 255)
LEATHER_D = (46, 36, 24, 255)
BOW       = (106, 74, 46, 255)
BOW_D     = (70, 48, 28, 255)
STRING    = (184, 180, 164, 255)
QUIVER    = (58, 44, 30, 255)
BOOT      = (38, 32, 24, 255)
BOOT_D    = (24, 20, 15, 255)
ACCENT    = (232, 200, 106, 255)
ACCENT_D  = (160, 132, 48, 255)


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


# --------------------------------------------------------------------- parts
def legs(c, dy, la, ra, side):
    """la/ra: per-leg horizontal offset. In side view the offsets read as
    stride length; face-on they read as weight shifting."""
    for off, lean in ((la, -1), (ra, 1)):
        x0 = CX - 5 + off if lean < 0 else CX + 1 + off
        for y in range(40 + dy, 54 + dy):
            tone = TUNIC_D if (y - dy) % 5 == 4 else LEATHER
            c.span(y, x0, x0 + 3, tone)
            c.put(x0, y, LEATHER)
        c.spans([(54 + dy, x0 - 1, x0 + 4), (55 + dy, x0 - 1, x0 + 4)], BOOT)
        c.span(56 + dy, x0 - 1, x0 + 4, BOOT_D)


def cloak(c, dy, narrow=False):
    bottom = 40 if narrow else 43
    for y in range(23 + dy, bottom + dy):
        t = (y - dy - 23) / float(bottom - 23)
        half = 7 + (4 if narrow else 6) * t
        x0, x1 = int(CX - half), int(CX + half)
        c.span(y, x0, x1, CLOAK if (y - dy - 23) % 6 != 5 else CLOAK_D)
        c.put(x0, y, CLOAK_HI)
        c.put(x1, y, CLOAK_D)
    for x0, depth in ((CX - 13, 2), (CX - 8, 3), (CX - 2, 1), (CX + 4, 3), (CX + 9, 2)):
        for d in range(depth):
            c.span(bottom + dy + d, x0, x0 + 3, CLOAK_D)


def torso(c, dy, back=False):
    rows = [
        (22, 26, 37), (23, 25, 38), (24, 25, 38), (25, 25, 38),
        (26, 26, 37), (27, 26, 37), (28, 26, 37), (29, 27, 36),
        (30, 27, 36), (31, 27, 36), (32, 27, 36), (33, 27, 36),
        (34, 26, 37), (35, 26, 37), (36, 26, 37), (37, 26, 37),
    ]
    for y, x0, x1 in rows:
        c.span(y + dy, x0, x1, TUNIC)
        c.put(x0, y + dy, CLOAK_HI)
        c.span(y + dy, x1 - 1, x1, TUNIC_D)
    if not back:                              # baldric only shows from the front
        for i, y in enumerate(range(23, 36)):
            x = 27 + i * 8 // 13
            c.put(x, y + dy, LEATHER)
            c.put(x + 1, y + dy, LEATHER_D)
    c.spans([(38 + dy, 25, 38), (39 + dy, 25, 38)], LEATHER)
    c.span(39 + dy, 25, 38, LEATHER_D)
    if not back:
        c.span(38 + dy, 31, 32, ACCENT_D)


def head(c, dy, facing):
    """facing: 'front' | 'back' | 'left' | 'right'."""
    if facing == "back":
        # Walking away: hair only, no face. A flat slab of one colour reads
        # as a blank card at this size, so it gets a centre parting, a lit
        # crown and a shaded right fall - the same modelling the front view
        # gets from its features.
        c.spans([(5 + dy, 29, 34), (6 + dy, 27, 36), (7 + dy, 26, 37),
                 (8 + dy, 26, 37), (9 + dy, 26, 37), (10 + dy, 26, 37)], HAIR)
        for y in range(11, 30):
            c.span(y + dy, 26, 37, HAIR)
            c.span(y + dy, 35, 37, HAIR_D)
            c.span(y + dy, 31, 32, HAIR_D)          # parting
        c.spans([(6 + dy, 28, 31), (7 + dy, 27, 30)], (236, 232, 218, 255))
        c.spans([(30 + dy, 26, 37), (31 + dy, 27, 36), (32 + dy, 29, 34)], HAIR_D)
        # ear tips still just break the silhouette from behind
        c.spans([(10 + dy, 24, 25), (11 + dy, 24, 26)], SKIN_D)
        c.spans([(10 + dy, 38, 39), (11 + dy, 37, 39)], SKIN_D)
        return

    if facing == "front":
        fx0, fx1 = 28, 35
        eye_l, eye_r = (29, 30), (33, 34)
    elif facing == "right":
        fx0, fx1 = 29, 37          # profile pushed toward the facing side
        eye_l, eye_r = (34, 35), None
    else:                          # left
        fx0, fx1 = 26, 34
        eye_l, eye_r = (28, 29), None

    for y in range(12, 18):
        c.span(y + dy, fx0, fx1, SKIN)
    c.spans([(18 + dy, fx0 + 1, fx1 - 1), (19 + dy, fx0 + 1, fx1 - 1)], SKIN_D)
    if facing == "right":
        c.span(16 + dy, fx1, fx1 + 1, SKIN)      # nose
    elif facing == "left":
        c.span(16 + dy, fx0 - 1, fx0, SKIN)

    # hair crown and side falls
    c.spans([(5 + dy, 29, 34), (6 + dy, 27, 36), (7 + dy, 26, 37),
             (8 + dy, 26, 37), (9 + dy, 26, 37), (10 + dy, 26, 37),
             (11 + dy, 26, 37)], HAIR)
    for y in range(11, 30):
        c.span(y + dy, 26, 27, HAIR)
        c.span(y + dy, 36, 37, HAIR)
        c.put(27, y + dy, HAIR_D)
        c.put(36, y + dy, HAIR_D)
    c.spans([(30 + dy, 26, 27), (31 + dy, 26, 27),
             (30 + dy, 36, 37), (31 + dy, 36, 37)], HAIR_D)

    # pointed ears, thin and above eye level
    c.spans([(10 + dy, 24, 25), (11 + dy, 24, 26), (12 + dy, 25, 27)], SKIN)
    c.spans([(10 + dy, 38, 39), (11 + dy, 37, 39), (12 + dy, 36, 38)], SKIN)

    c.span(11 + dy, fx0, fx1, ACCENT_D)          # circlet
    c.span(11 + dy, 30, 33, ACCENT)
    for pair in (eye_l, eye_r):
        if pair:
            c.span(15 + dy, pair[0], pair[1], ACCENT)
            c.span(16 + dy, pair[0], pair[1], ACCENT_D)


def quiver(c, dy, facing):
    if facing == "left":
        base = 20
    elif facing == "right":
        base = 38
    else:
        base = 40 if facing == "front" else 22
    for i, y in enumerate(range(20, 38)):
        x0 = base + i // 4
        c.span(y + dy, x0, x0 + 5, QUIVER if y % 5 != 4 else LEATHER_D)
        c.put(x0, y + dy, LEATHER)
    for dx in (0, 3, 6):
        x = base + dx
        for y in range(12, 21):
            c.put(x, y + dy, BOW_D)
        c.spans([(12 + dy, x - 1, x + 1), (13 + dy, x - 1, x + 1)], ACCENT)


def bow_at_rest(c, dy, bx):
    """Longbow carried vertically. bx is the belly of the curve."""
    for y in range(5, 56):
        x = bx + (y - 30) ** 2 / 96.0
        xi = int(round(x))
        c.put(xi, y + dy, BOW)
        c.put(xi + 1, y + dy, BOW_D)
    tip = bx + 6
    c.spans([(4 + dy, tip - 1, tip + 1), (56 + dy, tip - 1, tip + 1)], BOW_D)
    for y in range(5, 56):
        c.put(tip + 1, y + dy, STRING)


def bow_drawn(c, dy, bx, pull, facing):
    """Bow held out and the string hauled back. `pull` 0..2 is how far.

    The string is what animates, not the bow: an archer's draw reads
    entirely from the string angle and the arrow sliding back.
    """
    for y in range(10, 50):
        x = bx + (y - 30) ** 2 / 128.0
        xi = int(round(x))
        c.put(xi, y + dy, BOW)
        c.put(xi + 1, y + dy, BOW_D)
    tip_top, tip_bot = 10, 49
    nock_x = bx + 5 + pull * 3
    for y in range(tip_top, 31):                 # upper string limb
        t = (y - tip_top) / float(30 - tip_top)
        c.put(int(round(bx + 5 + (nock_x - bx - 5) * t)), y + dy, STRING)
    for y in range(30, tip_bot + 1):             # lower limb
        t = (y - tip_bot) / float(30 - tip_bot)
        c.put(int(round(bx + 5 + (nock_x - bx - 5) * t)), y + dy, STRING)
    if pull < 2:                                 # arrow still nocked
        d = 1 if facing != "left" else -1
        for i in range(14):
            c.put(nock_x - d * i, 30 + dy, BOW_D)
        c.spans([(30 + dy, nock_x - d, nock_x)], ACCENT)


# ------------------------------------------------------------------- frames
def build(facing, kind, step):
    c = Canvas()
    dy = -1 if (kind == "walk" and step == 1) else 0
    side = facing in ("left", "right")

    if kind == "walk":
        # A 2px stride was almost invisible once the cloak covers the thighs;
        # side views get a longer one because the legs swing along the
        # viewing axis rather than across it.
        stride = (-3, 0, 3)[step] * (2 if side else 1)
        la, ra = (-stride, stride) if not side else (stride, -stride)
    else:
        la = ra = 0

    if facing == "back":
        quiver(c, dy, "back")
    legs(c, dy, la, ra, side)
    cloak(c, dy, narrow=(kind == "attack"))
    torso(c, dy, back=(facing == "back"))
    if facing != "back":
        quiver(c, dy, facing)

    if kind == "walk":
        bx = 14 if facing in ("front", "back", "left") else 44
        bow_at_rest(c, dy, bx)
    else:
        bx = 20 if facing == "left" else 40
        if facing in ("front", "back"):
            bx = 40
        bow_drawn(c, dy, bx, step, facing)

    head(c, dy, facing)
    c.outline(OUTLINE)
    return c.img


ROWS = ["front", "left", "right", "back"]
LABEL = {"front": "down", "left": "left", "right": "right", "back": "up"}

sheet = Image.new("RGBA", (SIZE * 6, SIZE * 4), (0, 0, 0, 0))
for r, facing in enumerate(ROWS):
    for step in range(3):
        f = build(facing, "walk", step)
        sheet.paste(f, (step * SIZE, r * SIZE), f)
        f.save(os.path.join(OUT, f"{LABEL[facing]}_walk_{step}.png"))
    for step in range(3):
        f = build(facing, "attack", step)
        sheet.paste(f, ((3 + step) * SIZE, r * SIZE), f)
        f.save(os.path.join(OUT, f"{LABEL[facing]}_attack_{step}.png"))

sheet.save(os.path.join(OUT, "archer_sheet.png"))
sheet.resize((sheet.width * SCALE, sheet.height * SCALE), Image.NEAREST).save(
    os.path.join(OUT, "archer_sheet_preview.png"))

# walk-cycle GIF, front facing, at classic pixel-art speed
frames = [build("front", "walk", s).resize((SIZE * 4, SIZE * 4), Image.NEAREST)
          for s in (0, 1, 2, 1)]
frames[0].save(os.path.join(OUT, "walk_down.gif"), save_all=True,
               append_images=frames[1:], duration=120, loop=0, disposal=2)
print("done")

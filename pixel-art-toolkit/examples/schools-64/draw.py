"""Four 64x64 wizards, one per school of magic.

Pure hand-authored pixel art - explicit per-row spans, no supersampling.
The schools differ in silhouette (hat/hood shape), staff head, and palette,
not just a recolour: an angular icicle crown reads differently from a
drooping flame-singed brim even before colour is considered.

Shared across all four: old man, long beard, one saturated accent (the
staff head plus matching eye glow) against an otherwise desaturated body.
"""
import os

from PIL import Image

SIZE = 64
SCALE = 8
OUT = os.path.dirname(__file__)


class Canvas:
    def __init__(self):
        self.img = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
        self.px = self.img.load()

    def put(self, x, y, c):
        if 0 <= x < SIZE and 0 <= y < SIZE:
            self.px[x, y] = c

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


# --------------------------------------------------------------- hat shapes
def hat_icicle(c, p):
    """Frost: tall, narrow, hard-angled crown - reads as a shard of ice."""
    rows = []
    left, right = 31, 32
    for i, y in enumerate(range(3, 19)):
        rows.append((y, left, right))
        if i % 2 == 0:
            left -= 1
        right += 1
    c.spans(rows, p["hat"])
    # facet: one lit plane down the left plus a hard dark plane on the right
    for y, l, r in rows:
        c.put(l, y, p["hat_light"])
        c.put(l + 1, y, p["hat_light"])
        c.span(y, r - 2, r, p["hat_dark"])
    c.spans([(19, 22, 43), (20, 22, 43)], p["band"])
    c.spans([(21, 22, 43)], p["hat_dark"])
    # narrow, angular brim - frost doesn't droop
    c.spans([(22, 18, 45), (23, 15, 48), (24, 14, 49)], p["hat"])
    c.spans([(25, 15, 48), (26, 18, 45)], p["hat_dark"])


def hat_singed(c, p):
    """Fire: heavy drooping brim, crown tip flopping over to the left."""
    c.spans([
        (5, 22, 25), (6, 21, 27), (7, 21, 29), (8, 22, 31),
        (9, 24, 33), (10, 26, 34), (11, 27, 35), (12, 26, 36),
        (13, 26, 37), (14, 25, 38), (15, 25, 39), (16, 24, 40),
        (17, 24, 40), (18, 23, 41),
    ], p["hat"])
    c.spans([(6, 21, 23), (7, 21, 24), (8, 22, 25)], p["hat_light"])
    c.spans([(12, 33, 36), (13, 34, 37), (14, 35, 38),
             (15, 36, 39), (16, 37, 40), (17, 37, 40)], p["hat_dark"])
    c.spans([(19, 22, 42), (20, 22, 42)], p["band"])
    c.spans([(21, 22, 42)], p["hat_dark"])
    # brim sags lower on the left than the right
    c.spans([(22, 15, 47), (23, 11, 50), (24, 10, 51), (25, 11, 50)], p["hat"])
    c.spans([(26, 12, 49), (27, 16, 45)], p["hat_dark"])


def hat_hood(c, p):
    """Necromancy: no hat at all - a deep cowl swallowing the whole head.

    Sits low enough that its hem meets the shoulders; drawn any higher it
    detaches and reads as a helmet hovering over the robe.
    """
    c.spans([
        (14, 27, 36), (15, 25, 38), (16, 24, 39), (17, 23, 40),
        (18, 22, 41), (19, 22, 41), (20, 21, 42), (21, 21, 42),
        (22, 21, 42), (23, 20, 43), (24, 20, 43), (25, 20, 43),
        (26, 20, 43), (27, 20, 43), (28, 21, 43), (29, 21, 44),
        (30, 21, 44), (31, 22, 44),
    ], p["hat"])
    for y in range(15, 31):
        c.put(24 if y > 19 else 25, y, p["hat_light"])
    c.spans([(16, 36, 39), (17, 37, 40), (18, 38, 41), (19, 38, 41),
             (20, 39, 42), (21, 39, 42), (22, 39, 42), (23, 40, 43),
             (24, 40, 43), (25, 40, 43)], p["hat_dark"])
    # cowl opening - a hard black void, no brim line
    c.spans([(22, 26, 37), (23, 25, 38), (24, 25, 38), (25, 25, 38),
             (26, 25, 38), (27, 25, 38), (28, 25, 38), (29, 26, 37)], p["face"])


def hat_curled(c, p):
    """Arcane: the classic pointed hat, tip hooking over backwards."""
    c.spans([
        (4, 35, 38), (5, 34, 39), (6, 33, 39), (7, 32, 39),
        (8, 30, 38), (9, 29, 38), (10, 28, 38), (11, 27, 39),
        (12, 26, 39), (13, 26, 40), (14, 25, 40), (15, 24, 41),
        (16, 24, 41), (17, 23, 42), (18, 23, 42),
    ], p["hat"])
    c.spans([(5, 37, 39), (6, 36, 39), (7, 35, 39), (8, 34, 38)], p["hat_dark"])
    c.spans([(9, 29, 29), (10, 28, 28), (11, 27, 27), (12, 26, 26),
             (13, 26, 26), (14, 25, 25), (15, 24, 24), (16, 24, 24)], p["hat_light"])
    c.spans([(19, 22, 43), (20, 22, 43)], p["band"])
    c.spans([(21, 22, 43)], p["hat_dark"])
    c.spans([(22, 17, 46), (23, 13, 50), (24, 11, 52)], p["hat"])
    c.spans([(25, 12, 51), (26, 16, 47)], p["hat_dark"])


# -------------------------------------------------------------- staff heads
def head_shard(c, p):
    """Frost: an angular crystal, all straight edges."""
    c.spans([(4, 12, 13), (5, 11, 14), (6, 11, 14), (7, 10, 15),
             (8, 11, 14), (9, 11, 14), (10, 12, 13)], p["accent_dark"])
    c.spans([(5, 12, 13), (6, 12, 13), (7, 12, 14), (8, 12, 13)], p["accent"])
    c.put(6, 11, p["accent"])


def head_flame(c, p):
    """Fire: a teardrop flame, wider low and licking up to a point."""
    c.spans([(3, 12, 12), (4, 11, 13), (5, 11, 13), (6, 10, 14),
             (7, 10, 15), (8, 10, 15), (9, 11, 14), (10, 12, 13)], p["accent_dark"])
    c.spans([(5, 12, 12), (6, 11, 13), (7, 11, 14), (8, 12, 14)], p["accent"])
    c.spans([(6, 12, 12), (7, 12, 13)], p["accent_hot"])


def head_skull(c, p):
    """Necromancy: a small skull, brow ridge and two sockets."""
    c.spans([(5, 10, 15), (6, 9, 16), (7, 9, 16), (8, 9, 16)], p["bone"])
    c.spans([(9, 10, 15), (10, 11, 14)], p["bone"])
    c.spans([(7, 10, 11), (7, 14, 15), (8, 10, 11), (8, 14, 15)], p["accent"])
    c.spans([(10, 12, 13)], p["bone_dark"])


def head_orb(c, p):
    """Arcane: an orb with a broken ring of light around it."""
    c.spans([(5, 11, 14), (6, 10, 15), (7, 10, 15), (8, 10, 15),
             (9, 11, 14)], p["accent_dark"])
    c.spans([(6, 11, 13), (7, 11, 14), (8, 12, 14)], p["accent"])
    c.put(6, 11, p["accent_hot"])
    # orbiting sparks, deliberately not a closed ring
    c.put(8, 3, p["accent"]); c.put(17, 6, p["accent"]); c.put(7, 12, p["accent"])


# ---------------------------------------------------------------- shared body
ROBE_SIL = [
    (32, 24, 39), (33, 23, 40), (34, 22, 41), (35, 21, 42),
    (36, 21, 42), (37, 20, 43), (38, 20, 43), (39, 20, 43),
    (40, 19, 44), (41, 19, 44), (42, 19, 44), (43, 18, 45),
    (44, 18, 45), (45, 18, 45), (46, 17, 46), (47, 17, 46),
    (48, 17, 46), (49, 16, 47), (50, 16, 47), (51, 16, 47),
    (52, 16, 47), (53, 15, 48), (54, 15, 48), (55, 15, 48),
    (56, 15, 48),
]

BEARD_SIL = [
    (30, 28, 35), (31, 27, 36), (32, 27, 36), (33, 26, 37),
    (34, 26, 37), (35, 26, 37), (36, 26, 37), (37, 26, 37),
    (38, 26, 37), (39, 26, 37), (40, 27, 36), (41, 27, 36),
    (42, 27, 36), (43, 28, 35), (44, 28, 35), (45, 29, 34),
    (46, 30, 33), (47, 31, 32),
]


def body(c, p, hooded=False):
    if not hooded:
        c.spans([(27, 25, 38), (28, 25, 38), (29, 25, 38),
                 (30, 26, 37), (31, 26, 37)], p["face"])

    c.spans(ROBE_SIL, p["robe"])
    for y, x0, x1 in ROBE_SIL:
        if y >= 48:                       # one flat shadow band, no ramp
            c.span(y, x0, x1, p["robe_dark"])
        else:
            c.span(y, 31, 32, p["robe_light"])

    c.spans(BEARD_SIL, p["beard"])
    for y in range(32, 46):
        c.put(31, y, p["beard_shade"])
        c.put(32, y, p["beard_shade"])

    for y in range(11, 58):               # staff shaft
        c.put(12, y, p["staff"])
        c.put(13, y, p["staff_dark"])

    c.spans([(36, 10, 15), (37, 10, 15), (38, 11, 15)], p["skin"])
    c.spans([(41, 43, 48), (42, 43, 48), (43, 44, 47)], p["skin"])
    c.spans([(57, 22, 28), (58, 22, 28), (59, 22, 28)], p["boot"])
    c.spans([(57, 35, 41), (58, 35, 41), (59, 35, 41)], p["boot"])


def eyes(c, p):
    """Drawn after the headwear: the necromancer's cowl opening is filled
    with face-shadow, which would otherwise paint straight over them."""
    c.span(28, 27, 28, p["accent"])
    c.span(28, 35, 36, p["accent"])
    for x in (27, 28, 35, 36):
        c.put(x, 29, p["accent_dark"])


SCHOOLS = {
    "frost": dict(
        hat=hat_icicle, head=head_shard, hooded=False,
        palette=dict(
            outline=(16, 20, 30, 255), hat=(58, 78, 104, 255), hat_dark=(36, 50, 72, 255),
            hat_light=(96, 124, 152, 255), band=(140, 150, 160, 255), face=(20, 28, 40, 255),
            skin=(168, 160, 156, 255), beard=(226, 236, 242, 255), beard_shade=(168, 186, 200, 255),
            robe=(46, 64, 88, 255), robe_dark=(30, 44, 62, 255), robe_light=(78, 100, 128, 255),
            staff=(96, 104, 112, 255), staff_dark=(62, 70, 80, 255), boot=(22, 30, 42, 255),
            accent=(150, 232, 252, 255), accent_dark=(70, 140, 180, 255), accent_hot=(230, 250, 255, 255),
        )),
    "fire": dict(
        hat=hat_singed, head=head_flame, hooded=False,
        palette=dict(
            outline=(28, 14, 12, 255), hat=(92, 42, 34, 255), hat_dark=(60, 24, 20, 255),
            hat_light=(132, 66, 44, 255), band=(150, 112, 46, 255), face=(34, 18, 14, 255),
            skin=(188, 142, 108, 255), beard=(230, 216, 200, 255), beard_shade=(176, 154, 138, 255),
            robe=(84, 38, 32, 255), robe_dark=(56, 22, 18, 255), robe_light=(122, 60, 44, 255),
            staff=(88, 60, 40, 255), staff_dark=(58, 38, 26, 255), boot=(32, 18, 14, 255),
            accent=(255, 150, 44, 255), accent_dark=(178, 68, 24, 255), accent_hot=(255, 232, 150, 255),
        )),
    "death": dict(
        hat=hat_hood, head=head_skull, hooded=True,
        palette=dict(
            outline=(14, 18, 14, 255), hat=(44, 50, 44, 255), hat_dark=(26, 32, 28, 255),
            hat_light=(66, 74, 64, 255), band=(80, 84, 70, 255), face=(10, 14, 12, 255),
            skin=(150, 148, 130, 255), beard=(198, 202, 186, 255), beard_shade=(140, 146, 132, 255),
            robe=(40, 46, 40, 255), robe_dark=(24, 30, 26, 255), robe_light=(62, 70, 60, 255),
            staff=(72, 66, 54, 255), staff_dark=(48, 44, 36, 255), boot=(18, 22, 18, 255),
            accent=(148, 240, 120, 255), accent_dark=(64, 140, 60, 255), accent_hot=(214, 255, 190, 255),
            bone=(214, 214, 196, 255), bone_dark=(150, 150, 134, 255),
        )),
    "arcane": dict(
        hat=hat_curled, head=head_orb, hooded=False,
        palette=dict(
            outline=(20, 17, 26, 255), hat=(54, 43, 69, 255), hat_dark=(36, 29, 48, 255),
            hat_light=(74, 60, 92, 255), band=(122, 97, 52, 255), face=(28, 23, 36, 255),
            skin=(176, 141, 110, 255), beard=(216, 212, 204, 255), beard_shade=(160, 156, 150, 255),
            robe=(61, 51, 80, 255), robe_dark=(42, 35, 56, 255), robe_light=(84, 74, 104, 255),
            staff=(90, 66, 48, 255), staff_dark=(62, 45, 32, 255), boot=(26, 21, 32, 255),
            accent=(180, 150, 255, 255), accent_dark=(96, 72, 168, 255), accent_hot=(238, 226, 255, 255),
        )),
}


rendered = []
for name, cfg in SCHOOLS.items():
    p = cfg["palette"]
    c = Canvas()
    body(c, p, hooded=cfg["hooded"])
    cfg["hat"](c, p)
    eyes(c, p)
    cfg["head"](c, p)
    c.outline(p["outline"])
    c.img.save(os.path.join(OUT, f"{name}.png"))
    rendered.append(c.img)

sheet = Image.new("RGBA", (SIZE * len(rendered), SIZE), (0, 0, 0, 0))
for i, im in enumerate(rendered):
    sheet.paste(im, (i * SIZE, 0), im)
sheet.save(os.path.join(OUT, "schools_sheet.png"))
sheet.resize((sheet.width * SCALE, sheet.height * SCALE), Image.NEAREST).save(
    os.path.join(OUT, "schools_sheet_preview.png"))
print("done", list(SCHOOLS))

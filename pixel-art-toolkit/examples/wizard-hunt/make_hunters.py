"""Hunter classes for "I'm Not a Wizard, Harry" - techno-gothic, 32x32.

Dark fantasy wearing high tech: blackened plate and heavy cloaks, but with
powered lenses, glowing rune-etching and cabling. The palette does most of
that work - everything structural sits at near-black slate so the one
saturated per-class glow reads as *powered* rather than as paint.

Six classes, each with its own headgear silhouette, weapon and glow hue,
because in a multiplayer round you must name who you saw at a glance. The
shared dark body keeps them a squad; the head and the weapon carry the
identity.

Sheet layout: columns are the two walk frames, rows are class*4 + direction
(down/left/right/up).
"""
import os

from PIL import Image

S = 32
DIRS = ["down", "left", "right", "up"]
OUT = os.path.dirname(__file__)

# shared techno-gothic base
PLATE_HI = (92, 100, 118, 255)
PLATE    = (52, 57, 70, 255)
PLATE_D  = (33, 36, 46, 255)
PLATE_XD = (20, 22, 29, 255)
LEATHER  = (58, 46, 38, 255)
BOOT     = (26, 26, 34, 255)
BRASS    = (146, 116, 58, 255)
BRASS_D  = (98, 76, 34, 255)
CABLE    = (40, 42, 52, 255)
STEEL    = (128, 136, 152, 255)
VOID     = (12, 13, 18, 255)

# Order must match CLASS_NAMES in ../../wizard-hunt-online/src/classes.js:
# the client indexes sheet rows by class position, so a reordering here
# silently gives every player somebody else's body.
CLASSES = [
    ("Strażnik", (44, 46, 56, 255), (26, 27, 34, 255),
     (196, 210, 232, 255), (108, 124, 150, 255), "greathelm", "hammer"),
    ("Zwiadowca", (36, 62, 46, 255), (22, 40, 30, 255),
     (140, 240, 150, 255), (52, 138, 70, 255), "hood", "crossbow"),
    ("Strzelec", (30, 52, 96, 255), (18, 32, 62, 255),
     (120, 208, 255, 255), (44, 118, 172, 255), "visorcap", "rifle"),
    ("Inkwizytor", (74, 30, 38, 255), (46, 18, 24, 255),
     (255, 168, 72, 255), (166, 96, 26, 255), "widebrim", "pistol"),
    ("Chirurg", (58, 56, 40, 255), (36, 34, 24, 255),
     (216, 232, 120, 255), (128, 146, 48, 255), "beak", "censer"),
    ("Runarz", (56, 34, 74, 255), (34, 20, 46, 255),
     (198, 130, 255, 255), (110, 62, 158, 255), "techcowl", "rod"),
    ("Archiwista", (40, 46, 62, 255), (24, 28, 40, 255),
     (159, 180, 216, 255), (86, 104, 142, 255), "datavisor", "slate"),
    ("Technik", (62, 48, 28, 255), (38, 30, 18, 255),
     (255, 210, 122, 255), (166, 124, 48, 255), "lamphelm", "torch"),
]


class G:
    def __init__(self):
        self.img = Image.new("RGBA", (S, S), (0, 0, 0, 0))
        self.p = self.img.load()

    def put(self, x, y, c):
        if 0 <= x < S and 0 <= y < S:
            self.p[x, y] = c

    def span(self, y, x0, x1, c):
        for x in range(int(x0), int(x1) + 1):
            self.put(x, y, c)

    def spans(self, t, c):
        for y, x0, x1 in t:
            self.span(y, x0, x1, c)


def head(g, kind, dy, glow, glow_d, cloak, cloak_d, back, side, facing):
    if kind == "widebrim":
        g.spans([(5 + dy, 13, 18), (6 + dy, 12, 19), (7 + dy, 12, 19)], PLATE_D)
        g.spans([(8 + dy, 7, 24), (9 + dy, 8, 23)], PLATE_XD)     # wide brim
        if not back:
            g.spans([(10 + dy, 12, 19), (11 + dy, 12, 19)], VOID)
            g.spans([(10 + dy, 13, 14)], glow)                    # single lens
            g.put(15, 10 + dy, glow_d)
    elif kind == "greathelm":
        g.spans([(5 + dy, 12, 19), (6 + dy, 11, 20), (7 + dy, 11, 20),
                 (8 + dy, 11, 20), (9 + dy, 11, 20), (10 + dy, 11, 20),
                 (11 + dy, 12, 19)], PLATE if not back else PLATE_D)
        g.span(6 + dy, 11, 12, PLATE_HI)
        if not back:
            g.spans([(8 + dy, 12, 19)], VOID)                     # visor slit
            g.spans([(8 + dy, 13, 14), (8 + dy, 17, 18)], glow)
        g.spans([(4 + dy, 15, 16)], BRASS)                        # crest spike
    elif kind == "hood":
        g.spans([(5 + dy, 13, 18), (6 + dy, 11, 20), (7 + dy, 10, 21),
                 (8 + dy, 10, 21), (9 + dy, 10, 21), (10 + dy, 11, 20),
                 (11 + dy, 12, 19)], cloak)
        g.spans([(6 + dy, 11, 13), (7 + dy, 10, 12)], cloak_d)
        if not back:
            g.spans([(9 + dy, 12, 19), (10 + dy, 13, 18)], VOID)  # shadowed face
            g.spans([(9 + dy, 13, 14), (9 + dy, 17, 18)], glow)
    elif kind == "beak":
        g.spans([(5 + dy, 13, 18), (6 + dy, 12, 19), (7 + dy, 12, 19),
                 (8 + dy, 12, 19), (9 + dy, 12, 19)], PLATE_D)
        if not back:
            g.spans([(7 + dy, 13, 14), (7 + dy, 17, 18)], glow)   # goggle lenses
            # the beak, jutting toward whichever way the class is facing
            bx = 19 if facing != "left" else 12
            step = 1 if facing != "left" else -1
            for i in range(4):
                g.put(bx + step * i, 10 + dy + i // 2, BRASS if i < 2 else BRASS_D)
    elif kind == "visorcap":
        g.spans([(6 + dy, 12, 19), (7 + dy, 11, 20), (8 + dy, 11, 20),
                 (9 + dy, 11, 20), (10 + dy, 11, 20), (11 + dy, 12, 19)], PLATE)
        g.span(7 + dy, 11, 12, PLATE_HI)
        if not back:
            g.spans([(9 + dy, 11, 20)], VOID)                    # long optic bar
            g.spans([(9 + dy, 12, 18)], glow)
        # rangefinder stalk, the marksman's silhouette tell
        g.spans([(5 + dy, 18, 19), (6 + dy, 19, 20)], BRASS)
    elif kind == "techcowl":
        g.spans([(5 + dy, 12, 19), (6 + dy, 11, 20), (7 + dy, 11, 20),
                 (8 + dy, 11, 20), (9 + dy, 11, 20), (10 + dy, 12, 19)], PLATE_D)
        g.spans([(6 + dy, 11, 12)], PLATE_HI)
        if not back:
            g.spans([(8 + dy, 12, 19)], VOID)
            g.spans([(8 + dy, 14, 17)], glow)                     # single wide band
        for i, yy in enumerate(range(11, 17)):                    # cables to the back
            g.put(9 - (i // 3), yy + dy, CABLE)
            g.put(22 + (i // 3), yy + dy, CABLE)
    elif kind == "datavisor":
        # low scribe's cap: the silhouette has to stay flat, because this is
        # the class people confuse with the Chirurg down a dark corridor and
        # the confusion should come from the body, not from a copied hat
        g.spans([(6 + dy, 12, 19), (7 + dy, 11, 20), (8 + dy, 11, 20),
                 (9 + dy, 11, 20)], PLATE_D)
        g.span(7 + dy, 11, 13, PLATE_HI)
        if not back:
            g.spans([(10 + dy, 12, 19)], VOID)
            # one lens, not two: the asymmetry is the reading-eye tell
            side_x = (16, 18) if facing != "left" else (13, 15)
            g.span(10 + dy, side_x[0], side_x[1], glow)
            g.put(side_x[0] - 1 if facing != "left" else side_x[1] + 1, 10 + dy, glow_d)
        g.spans([(4 + dy, 19, 19), (5 + dy, 19, 19)], BRASS)      # stub aerial
    elif kind == "lamphelm":
        g.spans([(6 + dy, 12, 19), (7 + dy, 11, 20), (8 + dy, 11, 20),
                 (9 + dy, 11, 20), (10 + dy, 11, 20), (11 + dy, 12, 19)],
                PLATE if not back else PLATE_D)
        g.span(7 + dy, 11, 12, PLATE_HI)
        # the lamp: the one class that carries its own light source, which is
        # exactly what act III is about
        g.spans([(3 + dy, 14, 17), (4 + dy, 14, 17)], BRASS)
        g.span(4 + dy, 15, 16, glow)
        if not back:
            g.spans([(9 + dy, 12, 19)], VOID)                     # rebreather grille
            for x in range(13, 19, 2):
                g.put(x, 9 + dy, glow_d)
            g.spans([(11 + dy, 13, 18)], PLATE_D)


def weapon(g, kind, dy, glow, glow_d, facing):
    left = facing == "left"
    gx = 6 if left else 25          # off-hand side keeps it clear of the body
    if kind == "pistol":
        g.spans([(18 + dy, gx - 1, gx + 2), (19 + dy, gx - 1, gx + 2)], PLATE)
        g.put(gx + (2 if not left else -1), 18 + dy, glow)
    elif kind == "sword":
        for y in range(6 + dy, 22 + dy):
            g.put(gx, y, STEEL)
            g.put(gx + 1, y, glow_d)
        g.span(21 + dy, gx - 2, gx + 3, BRASS)
        g.put(gx, 5 + dy, glow)
    elif kind == "hammer":
        for y in range(10 + dy, 24 + dy):
            g.put(gx, y, LEATHER)
        g.spans([(9 + dy, gx - 2, gx + 2), (10 + dy, gx - 2, gx + 2),
                 (11 + dy, gx - 2, gx + 2)], PLATE)
        g.span(10 + dy, gx - 2, gx - 1, glow)
    elif kind == "rifle":
        # long barrel - reads as the only ranged weapon on the squad
        step = 1 if not left else -1
        for i in range(11):
            g.put(gx + step * (i - 4), 18 + dy, STEEL if i > 3 else PLATE)
        g.spans([(19 + dy, gx - 2, gx + 2)], PLATE_D)
        g.put(gx + step * 7, 18 + dy, glow)
    elif kind == "crossbow":
        for y in range(15 + dy, 22 + dy):
            g.put(gx, y, LEATHER)
        g.spans([(17 + dy, gx - 2, gx + 2)], PLATE_D)
        g.spans([(16 + dy, gx - 3, gx - 2), (16 + dy, gx + 2, gx + 3)], STEEL)
        g.put(gx, 15 + dy, glow)
    elif kind == "censer":
        for y in range(12 + dy, 19 + dy):
            g.put(gx, y, CABLE)                                   # hanging chain
        g.spans([(19 + dy, gx - 1, gx + 1), (20 + dy, gx - 1, gx + 1)], BRASS)
        g.put(gx, 20 + dy, glow)
    elif kind == "rod":
        for y in range(8 + dy, 24 + dy):
            g.put(gx, y, PLATE_D)
        g.spans([(7 + dy, gx - 1, gx + 1), (8 + dy, gx - 1, gx + 1)], glow)
        g.put(gx, 6 + dy, glow_d)
    elif kind == "slate":
        # held flat at the chest rather than out to the side: this is the one
        # hunter whose hands are busy reading instead of pointing. Chest-held
        # means it has to disappear when he turns his back, or the screen
        # glows through him.
        if facing == "up":
            g.spans([(16 + dy, 14, 17), (17 + dy, 14, 17)], PLATE_D)  # its harness
            return
        cx = 12 if left else 19
        g.spans([(15 + dy, cx - 3, cx + 3), (16 + dy, cx - 3, cx + 3),
                 (17 + dy, cx - 3, cx + 3), (18 + dy, cx - 3, cx + 3),
                 (19 + dy, cx - 3, cx + 3)], PLATE_D)
        g.spans([(16 + dy, cx - 2, cx + 2), (17 + dy, cx - 2, cx + 2),
                 (18 + dy, cx - 2, cx + 2)], glow_d)
        g.spans([(16 + dy, cx - 2, cx + 2), (18 + dy, cx - 1, cx + 1)], glow)
        g.spans([(14 + dy, cx - 3, cx + 3)], BRASS_D)
    elif kind == "torch":
        for y in range(14 + dy, 22 + dy):
            g.put(gx, y, LEATHER)
        g.spans([(19 + dy, gx - 1, gx + 1), (20 + dy, gx - 1, gx + 1)], BRASS)
        # cutting flame, short and bright - the Technik is the walking lamp
        g.put(gx, 13 + dy, glow)
        g.put(gx, 12 + dy, glow_d)
        g.spans([(21 + dy, gx - 2, gx + 2)], PLATE_D)             # gas bottle


def hunter(cfg, facing, step):
    name, cloak, cloak_d, glow, glow_d, hkind, wkind = cfg
    g = G()
    dy = -1 if step == 1 else 0
    back = facing == "up"
    side = facing in ("left", "right")

    # legs animate; they sit against the cloak so the motion stays visible
    off = 2 if step == 0 else -2
    la = off
    ra = -off if not side else off // 2
    for x0, a in ((12, la), (17, ra)):
        for y in range(24 + dy, 29 + dy):
            g.span(y, x0 + a, x0 + 2 + a, PLATE_D if y % 4 == 3 else PLATE)
        g.spans([(29 + dy, x0 + a, x0 + 2 + a), (30 + dy, x0 + a, x0 + 2 + a)], BOOT)

    # cloak: the class colour, and the only large area of hue on the sprite
    g.spans([(13 + dy, 10, 21), (14 + dy, 9, 22), (15 + dy, 9, 22),
             (16 + dy, 8, 23), (17 + dy, 8, 23), (18 + dy, 8, 23),
             (19 + dy, 8, 23), (20 + dy, 9, 22), (21 + dy, 9, 22),
             (22 + dy, 10, 21), (23 + dy, 11, 20)], cloak)
    for y in range(13, 24):
        g.put(8 if y > 15 else 9, y + dy, cloak_d)
        g.span(y + dy, 21 if y > 15 else 20, 23 if y > 15 else 22, cloak_d)

    if not back:
        # blackened breastplate over the cloak, with a lit rune seam
        g.spans([(14 + dy, 12, 19), (15 + dy, 12, 19), (16 + dy, 12, 19),
                 (17 + dy, 12, 19), (18 + dy, 12, 19), (19 + dy, 13, 18),
                 (20 + dy, 13, 18)], PLATE_D)
        for y in range(14, 20):
            g.put(12, y + dy, PLATE_HI)
        g.spans([(16 + dy, 15, 16)], glow_d)
        g.put(15, 15 + dy, glow)
        g.span(21 + dy, 12, 19, BRASS_D)                # belt
    else:
        # back view: a powered spine unit instead of the chest rune
        g.spans([(14 + dy, 13, 18), (15 + dy, 13, 18), (16 + dy, 13, 18),
                 (17 + dy, 13, 18)], PLATE_XD)
        for y in range(14, 18):
            g.put(15, y + dy, glow_d)
            g.put(16, y + dy, glow_d)

    weapon(g, wkind, dy, glow, glow_d, facing)
    head(g, hkind, dy, glow, glow_d, cloak, cloak_d, back, side, facing)
    return g.img


sheet = Image.new("RGBA", (S * 2, S * 4 * len(CLASSES)), (0, 0, 0, 0))
for ci, cfg in enumerate(CLASSES):
    for di, d in enumerate(DIRS):
        for step in range(2):
            f = hunter(cfg, d, step)
            sheet.paste(f, (step * S, (ci * 4 + di) * S), f)

sheet.save(os.path.join(OUT, "hunters.png"))
sheet.resize((sheet.width * 3, sheet.height * 3), Image.NEAREST).save(
    os.path.join(OUT, "hunters_preview.png"))

# a contact sheet of just the front-facing pose, for reviewing the classes
row = Image.new("RGBA", (S * len(CLASSES), S), (0, 0, 0, 0))
for ci, cfg in enumerate(CLASSES):
    f = hunter(cfg, "down", 0)
    row.paste(f, (ci * S, 0), f)
row.resize((row.width * 6, S * 6), Image.NEAREST).save(
    os.path.join(OUT, "hunters_classes.png"))
print("done", sheet.size, [c[0] for c in CLASSES])

"""Hunter sprites for "I'm Not a Wizard, Harry" - people, 32x32.

The first sheet drew eight sealed helmets on eight identical blocks, and it
read as a squad of robots. Nothing about that was the palette: a head with no
face, a torso with no neck and no layers, and one silhouette copy-pasted eight
times gives you machines no matter what colour you paint them.

So this sheet is built the other way round. There is one human body function
driven by a *build* -- shoulder width, waist, torso length, leg spacing,
posture -- and eight builds that differ enough to tell apart by outline
alone. On top of that each class gets its own face: skin tone, hair, and a
head treatment showing as much of the person as the job allows. The Strażnik
wears a hard shell with the visor up; the Chirurg wears a respirator over the
mouth and nothing over the eyes; the Archiwista wears reading optics and is
the only one going grey.

Equipment is drawn too. Each class picks one of three items before the round,
and the sheet carries all three, so what somebody is carrying is part of how
they look rather than a line in a menu.

Three files are written:

    hunters.png       the bodies
    hunters_glow.png  only the pixels that are their own light source
    hunters.json      what is where, by name

That last one used to be a formula instead -- `(class * 3 + item) * 4 +
direction` -- copied into the client and implied by classes.js, so reordering
either axis silently handed players somebody else's body with no error
anywhere. Rows are now decided here, once, while the sprite is being drawn,
and written down. Nothing downstream recomputes them, and a name cannot drift
the way an index can. Reordering CLASSES is safe after a regeneration;
renaming an item without one fails the test suite by name.

The glow sheet exists because the client has no shaders. SS14 marks a layer
unshaded and skips lighting for it; here the equivalent is draw order, so
these pixels are blitted after the fog and a lamp stops fading at the same
rate as the body carrying it.
"""
import json
import os

from PIL import Image

S = 32
DIRS = ["down", "left", "right", "up"]
OUT = os.path.dirname(os.path.abspath(__file__))

# ---------------------------------------------------------------- palette
# Four skin tones and four hair colours, dealt out so the squad reads as
# eight people rather than one person in eight hats.
SKINS = [
    ((206, 158, 122, 255), (156, 112, 84, 255), (232, 186, 150, 255)),
    ((236, 196, 158, 255), (184, 140, 108, 255), (252, 220, 188, 255)),
    ((162, 114, 82, 255), (114, 76, 54, 255), (196, 148, 112, 255)),
    ((120, 82, 60, 255), (82, 54, 40, 255), (154, 110, 82, 255)),
]
HAIRS = {
    "brown": ((58, 44, 38, 255), (86, 66, 54, 255)),
    "black": ((32, 30, 34, 255), (56, 54, 60, 255)),
    "sand":  ((122, 98, 62, 255), (162, 136, 92, 255)),
    "grey":  ((132, 130, 128, 255), (170, 168, 164, 255)),
    "red":   ((124, 66, 40, 255), (162, 96, 58, 255)),
}

EYE      = (30, 34, 44, 255)
STUBBLE  = (86, 70, 62, 255)
# Trousers are squad issue and deliberately not derived from the coat: a dark
# saturated coat shades to near-black, and on the first pass the Inkwizytor,
# Runarz and Technik lost their legs into their own hems and walked around as
# blobs. One neutral slate for everybody also does something useful -- the
# builds differ, the uniform below the waist does not, so they still read as
# one squad.
TROUSER  = (58, 56, 66, 255)
TROUSER_LO = (40, 38, 48, 255)
BOOT     = (26, 24, 30, 255)
# The vest is issued kit and so is one grey for everybody. Deriving it from
# each class's coat put a dark purple plate on a dark purple coat and the
# Runarz's whole torso read as a single slab -- the layering was there in the
# code and invisible on screen. The class colour now lives only in the coat,
# which is the larger area anyway.
VEST     = (60, 64, 78, 255)
VEST_HI  = (92, 98, 116, 255)
VEST_LO  = (36, 39, 48, 255)
STRAP    = (72, 54, 38, 255)
STRAP_HI = (104, 78, 54, 255)
STEEL    = (120, 132, 152, 255)
STEEL_LO = (72, 82, 98, 255)
GEAR     = (84, 90, 104, 255)
GEAR_HI  = (116, 124, 142, 255)
RUBBER   = (40, 42, 48, 255)
BRASS    = (146, 116, 58, 255)
GLASS    = (214, 150, 72, 255)
GLASS_HI = (242, 196, 118, 255)
CANVAS   = (78, 76, 64, 255)
CANVAS_LO = (48, 48, 40, 255)
CANVAS_HI = (108, 104, 86, 255)


class G:
    def __init__(self):
        self.img = Image.new("RGBA", (S, S), (0, 0, 0, 0))
        self.p = self.img.load()

    def put(self, x, y, c):
        if 0 <= int(x) < S and 0 <= int(y) < S:
            self.p[int(x), int(y)] = c

    def span(self, y, x0, x1, c):
        for x in range(int(x0), int(x1) + 1):
            self.put(x, y, c)

    def rect(self, x0, y0, x1, y1, c):
        for y in range(int(y0), int(y1) + 1):
            self.span(y, x0, x1, c)


# ---------------------------------------------------------------- the body
#
# A build is the whole of what makes two hunters different at a glance, before
# any hat or weapon: how wide they are at the shoulder, how wide at the waist,
# where the shoulders sit, and how far apart the feet are.
#
#   sh     shoulder half-width      5 lean .. 8 heavy
#   wa     waist half-width         4 lean .. 8 heavy
#   top    y of the shoulders       13 tall .. 16 short
#   legw   half-width of a leg      1 or 2
#   gap    space between the legs
#   lean   1 = shoulders pushed forward, for the ones who stoop

def build(sh=6, wa=6, top=15, legw=1, gap=3, lean=0):
    return dict(sh=sh, wa=wa, top=top, legw=legw, gap=gap, lean=lean)


def body(g, b, pal, facing, step):
    """Everything from the collar down. Layered on purpose: trousers, coat,
    vest over the coat, straps over the vest. One flat block from shoulder to
    hip is the single biggest reason a sprite reads as manufactured."""
    coat, coat_hi, coat_lo = pal["coat"], pal["coat_hi"], pal["coat_lo"]
    vest, vest_hi, vest_lo = VEST, VEST_HI, VEST_LO
    skin, skin_lo, skin_hi = pal["skin"]
    back = facing == "up"
    side = facing in ("left", "right")
    top, sh, wa = b["top"], b["sh"], b["wa"]
    lf, rt = 16 - sh, 15 + sh          # shoulder line
    lw, rw = 16 - wa, 15 + wa          # waist line

    # legs: they swing, and the swing is what sells the walk at this size
    off = 1 if step == 0 else -1
    w = b["legw"]
    lx, rx = 16 - b["gap"] - w, 15 + b["gap"] + w
    for cx0, a in ((lx, off), (rx, -off)):
        g.rect(cx0 - w + a, 24, cx0 + w + a, 28, TROUSER)
        g.rect(cx0 - w + a, 24, cx0 - w + a, 28, TROUSER_LO)     # outer edge shaded
        g.rect(cx0 - w + a, 29, cx0 + w + a, 31, BOOT)
        g.span(29, cx0 - w + a, cx0 + w + a, (44, 42, 50, 255))  # boot cuff

    # coat: shoulders at the top, hem flaring past the waist
    for y in range(top, 25):
        t = (y - top) / max(1, 24 - top)
        x0 = round(lf + (lw - lf) * t * 0.4)
        x1 = round(rt + (rw - rt) * t * 0.4)
        g.span(y, x0, x1, coat)
        g.put(x0, y, coat_lo)
        g.put(x1, y, coat_hi)
    g.span(top, lf + 1, rt - 1, coat_hi)
    g.rect(lw, 23, rw, 24, coat_lo)

    if not back:
        # armour vest, shorter than the coat so two layers stay visible
        g.rect(lf + 2, top + 1, rt - 2, top + 5, vest)
        g.rect(lf + 3, top + 6, rt - 3, top + 7, vest)      # tapered to the waist,
        g.span(top + 2, lf + 3, rt - 3, vest_hi)            # so it is not a slab
        g.span(top + 7, lf + 3, rt - 3, vest_lo)
        g.put(lf + 2, top + 1, vest_lo)                     # notched at the collar
        g.put(rt - 2, top + 1, vest_lo)
        g.put(15, top + 3, pal["glow_lo"])          # chest status light
        g.put(16, top + 3, pal["glow"])
        # straps: one over a shoulder, one round the waist. Asymmetry is the
        # cheapest thing that stops a figure looking stamped out
        for y in range(top + 1, top + 8):
            g.put(lf + 3 + (y - top) // 3, y, STRAP)
        g.span(top + 8, lw, rw, STRAP)
        g.span(top + 8, 15, 16, STRAP_HI)
    else:
        g.rect(lf + 3, top + 1, rt - 3, top + 5, coat_lo)   # pack on the back
        g.rect(15, top + 1, 16, top + 5, pal["glow_lo"])

    # arms: one shoulder armoured, the other sleeve rolled back to skin
    g.rect(lf - 2, top + 1, lf - 1, top + 8, coat)
    g.rect(rt + 1, top + 1, rt + 2, top + 5, coat)
    # an arm the same colour as the torso, touching the torso, is not an arm.
    # One shaded column on the inner edge is all it takes to detach them
    g.rect(lf - 1, top + 2, lf - 1, top + 8, coat_lo)
    g.rect(rt + 1, top + 2, rt + 1, top + 5, coat_lo)
    g.rect(lf - 2, top, lf, top + 1, STEEL_LO)              # pauldron, one side
    g.span(top, lf - 2, lf - 1, STEEL)
    g.rect(rt + 1, top + 6, rt + 2, top + 8, skin)          # rolled sleeve
    g.put(rt + 1, top + 6, skin_hi)

    if side:
        # turned: the far arm disappears behind the body and the near one
        # crosses it, or the figure reads as facing you with a twisted head
        g.rect(lf - 2, top, lf, top + 8, coat)
        g.rect(lf - 1, top + 4, rt, top + 5, coat_hi)


def face(g, b, pal, facing, hair_kind, stubble=False, mouth=True):
    """Nine pixels of person. The eyes sit two apart with the bridge of the
    nose between them: two adjacent lit pixels read as a visor slit, which is
    the whole robot problem in miniature."""
    skin, skin_lo, skin_hi = pal["skin"]
    top = b["top"]
    hy = top - 10                       # head top; head is nine rows tall
    x0, x1 = 12, 19
    back = facing == "up"

    g.rect(14, top - 1, 17, top, skin_lo)                   # neck
    g.rect(x0, hy, x1, hy + 8, skin)
    g.rect(x0, hy, x0, hy + 8, skin_lo)
    g.rect(x1, hy, x1, hy + 8, skin_hi)
    g.span(hy + 1, x0 + 1, x1 - 1, skin_hi)
    g.span(hy + 3, x0 + 1, x1 - 1, skin_lo)                 # brow shadow

    if facing in ("left", "right"):
        # A turned head is not a front head with an eye rubbed out. Both eyes
        # go to the leading side, the far one drops entirely, and a nose sticks
        # out at the edge -- without that the walk cycle plays four directions
        # of somebody staring straight at the camera.
        d = 1 if facing == "right" else -1
        eye_x, nose_x = 16 + d * 2, x1 if d > 0 else x0
        g.put(eye_x, hy + 4, EYE)
        g.put(eye_x - d, hy + 4, skin_lo)                   # brow beside it
        g.put(nose_x, hy + 4, skin_hi)                      # the nose, at the edge
        g.put(nose_x, hy + 5, skin_lo)
        if mouth:
            g.put(16 + d * 2, hy + 7, skin_lo)
    elif not back:
        g.put(14, hy + 4, EYE)
        g.put(17, hy + 4, EYE)
        g.put(15, hy + 4, skin_lo)                          # the bridge of the nose
        g.put(16, hy + 4, skin_lo)
        if mouth:
            g.span(hy + 7, 15, 16, skin_lo)
    if stubble:
        g.span(hy + 8, x0 + 1, x1 - 1, STUBBLE)

    hc, hh = HAIRS[hair_kind]
    return hy, hc, hh


def hair(g, hy, hc, hh, facing, style="short"):
    back = facing == "up"
    side = facing in ("left", "right")
    if style != "bald":
        if style == "crop":
            g.span(hy, 13, 18, hc)
            g.span(hy - 1, 14, 17, hc)
            g.span(hy - 1, 15, 16, hh)
        else:
            g.span(hy - 1, 13, 18, hc)
            g.span(hy, 12, 19, hc)
            g.put(12, hy + 1, hc)
            g.put(19, hy + 1, hc)
            g.span(hy - 1, 15, 17, hh)
        if side:
            # the trailing side of the skull, so a turned head has a back to it
            t0, t1 = (12, 13) if facing == "right" else (18, 19)
            g.rect(t0, hy, t1, hy + 3, hc)
    if back and style != "bald":
        # walking away, you see skull and nape -- not a bare face with a wig
        # on top, which is what the first pass drew for half the squad
        g.rect(12, hy, 19, hy + 7, hc)
        g.span(hy + 1, 14, 17, hh)


# ---------------------------------------------------------------- heads
#
# Eight treatments, each showing as much of the person as the job allows.
# The rules learned the hard way: nothing dark may cross the brow, because at
# this size a band there covers both eyes at once and the face becomes a
# visor; and any cloth over the head needs three pixels of thickness with a
# lit inner rim, or it reads as long hair rather than as something worn.

def head_shell(g, b, pal, facing):          # Strażnik: hard shell, visor up
    hy, hc, hh = face(g, b, pal, facing, pal["hair"], stubble=True)
    back = facing == "up"
    g.span(hy - 1, 12, 19, STEEL_LO)
    g.span(hy, 11, 20, STEEL)
    g.rect(11, hy + 1, 11, hy + 5, STEEL_LO)
    g.rect(20, hy + 1, 20, hy + 5, STEEL_LO)
    g.span(hy + 1, 12, 19, STEEL_LO)
    g.rect(12, hy - 3, 19, hy - 2, STEEL)                   # visor swung up
    g.span(hy - 3, 13, 18, STEEL_LO)
    g.span(hy - 2, 13, 18, pal["glow_lo"])                  # glass lit underneath:
    g.put(14, hy - 2, pal["glow"])                          # lit on top it is a hatband
    g.put(11, hy - 2, GEAR); g.put(20, hy - 2, GEAR)        # hinges
    if back:
        g.rect(12, hy + 1, 19, hy + 6, STEEL_LO)            # shell from behind
        g.span(hy + 3, 13, 18, STEEL)
    else:
        g.rect(11, hy + 6, 11, hy + 7, STRAP)               # chinstrap
        g.rect(20, hy + 6, 20, hy + 7, STRAP)


def head_goggles(g, b, pal, facing):        # Zwiadowca: goggles up, scarf down
    hy, hc, hh = face(g, b, pal, facing, pal["hair"])
    hair(g, hy, hc, hh, facing)
    g.span(hy + 2, 12, 19, RUBBER)                          # strap round the back
    if facing == "up":
        return                                              # from behind, only the strap
    g.rect(12, hy - 1, 19, hy + 1, RUBBER)
    g.rect(13, hy, 15, hy + 1, GLASS)
    g.rect(16, hy, 18, hy + 1, GLASS)
    g.put(13, hy, GLASS_HI); g.put(16, hy, GLASS_HI)
    g.put(15, hy, STEEL); g.put(16, hy, STEEL)              # bridge between cups
    g.put(11, hy, GEAR); g.put(20, hy, GEAR)                # pivots break the outline
    g.rect(13, hy + 8, 18, b["top"], (96, 72, 58, 255))     # scarf at the throat


def head_headset(g, b, pal, facing):        # Strzelec: nothing on the face
    hy, hc, hh = face(g, b, pal, facing, pal["hair"], stubble=True)
    hair(g, hy, hc, hh, facing)
    g.span(hy, 12, 19, GEAR)                                # band on the hairline
    g.span(hy - 1, 14, 17, GEAR_HI)
    g.rect(11, hy + 1, 11, hy + 4, GEAR)                    # earcups
    g.rect(20, hy + 1, 20, hy + 4, GEAR)
    if facing != "up":
        g.put(20, hy + 5, STEEL_LO)                         # optic arm past the eye
        g.put(20, hy + 4, GLASS_HI)                         # lens beside it, never over
        g.rect(11, hy + 5, 11, hy + 7, RUBBER)              # boom mic to the jaw
        g.put(12, hy + 7, RUBBER)


def head_hood(g, b, pal, facing):           # Inkwizytor: hood over a soft cap
    hy, hc, hh = face(g, b, pal, facing, pal["hair"], mouth=False)
    # cloth three pixels thick, dark outside and lit on the inner rim. Without
    # that thickness a hood is a flat curtain beside the cheeks and reads as
    # long hair -- it did, through two passes, and recolouring did not help
    g.span(hy - 3, 14, 17, CANVAS_LO)
    g.span(hy - 2, 12, 19, CANVAS)
    g.rect(10, hy - 1, 21, hy + 1, CANVAS)
    g.rect(9, hy + 2, 11, b["top"] + 2, CANVAS)
    g.rect(20, hy + 2, 22, b["top"] + 2, CANVAS)
    g.rect(9, hy + 2, 9, b["top"] + 2, CANVAS_LO)
    g.rect(22, hy + 2, 22, b["top"] + 2, CANVAS_LO)
    g.span(b["top"] + 2, 9, 11, CANVAS_LO)
    g.span(b["top"] + 2, 20, 22, CANVAS_LO)
    g.rect(11, hy + 1, 11, hy + 7, CANVAS_HI)               # lit rim of the opening
    g.rect(20, hy + 1, 20, hy + 7, CANVAS_HI)
    g.span(hy, 12, 19, CANVAS_HI)
    if facing != "up":
        g.rect(12, hy + 1, 19, hy + 2, (40, 40, 34, 255))   # shadow on the brow
        g.put(14, hy + 4, EYE)
        g.put(17, hy + 4, EYE)
    else:
        g.rect(12, hy, 19, hy + 7, CANVAS)


def head_mask(g, b, pal, facing):           # Chirurg: respirator, eyes bare
    hy, hc, hh = face(g, b, pal, facing, pal["hair"], mouth=False)
    hair(g, hy, hc, hh, facing)
    if facing == "up":
        return
    # the cup covers the mouth and nothing else: wider than four pixels it
    # stops being worn on a face and becomes the bottom half of a helmet
    g.span(hy + 5, 13, 18, pal["skin"][1])                  # cheekbone kept bare
    g.rect(14, hy + 6, 17, hy + 8, GEAR)
    g.span(hy + 6, 14, 17, GEAR_HI)
    g.span(hy + 8, 14, 17, STEEL_LO)
    g.put(13, hy + 6, RUBBER); g.put(18, hy + 6, RUBBER)    # straps to the ears
    g.put(12, hy + 5, RUBBER); g.put(19, hy + 5, RUBBER)
    g.put(15, hy + 7, pal["glow_lo"]); g.put(16, hy + 7, pal["glow"])


def head_circlet(g, b, pal, facing):        # Runarz: shaved, etched, banded
    hy, hc, hh = face(g, b, pal, facing, pal["hair"], stubble=True)
    hair(g, hy, hc, hh, facing, style="bald")
    g.span(hy, 12, 19, pal["skin"][2])                      # bare scalp catching light
    g.span(hy + 1, 12, 19, STEEL_LO)                        # the band itself
    g.span(hy + 1, 13, 18, STEEL)
    if facing != "up":
        g.put(13, hy + 1, pal["glow"])
        g.put(18, hy + 1, pal["glow_lo"])
        g.put(12, hy + 6, pal["glow_lo"])                   # etching down the temple
        g.put(12, hy + 7, pal["glow_lo"])
    g.put(15, hy - 1, STEEL_LO)                             # stud on the crown
    g.put(16, hy - 1, STEEL)


def head_optics(g, b, pal, facing):         # Archiwista: older, reading optics
    hy, hc, hh = face(g, b, pal, facing, pal["hair"])
    hair(g, hy, hc, hh, facing, style="crop")
    if facing == "up":
        return
    g.span(hy + 4, 13, 18, STEEL_LO)                        # the frame, thin
    g.rect(13, hy + 4, 14, hy + 4, GLASS)
    g.rect(17, hy + 4, 18, hy + 4, GLASS)
    g.put(13, hy + 4, GLASS_HI)
    g.put(14, hy + 4, EYE); g.put(17, hy + 4, EYE)          # eyes read through them
    g.put(12, hy + 3, STEEL_LO); g.put(19, hy + 3, STEEL_LO)
    g.span(hy + 6, 14, 17, pal["skin"][1])                  # lines round the mouth
    g.put(13, hy + 2, pal["skin"][1])
    g.put(18, hy + 2, pal["skin"][1])


def head_cap(g, b, pal, facing):            # Technik: flat cap, lamp on it
    hy, hc, hh = face(g, b, pal, facing, pal["hair"], stubble=True)
    hair(g, hy, hc, hh, facing)
    g.span(hy - 1, 12, 19, (52, 50, 46, 255))
    g.span(hy, 11, 20, (68, 66, 60, 255))
    g.span(hy, 13, 17, (92, 88, 80, 255))
    if facing != "up":
        g.span(hy + 1, 11, 20, (40, 38, 34, 255))           # the peak, one row
        g.rect(19, hy - 2, 20, hy - 1, BRASS)               # lamp clipped to it
        g.put(20, hy - 2, pal["glow"])
        g.put(21, hy - 1, pal["glow_lo"])                   # spill, so it is a lamp


# ---------------------------------------------------------------- items
#
# Twenty-four, three per class. Held out to the side where the body will not
# swallow them, and suppressed on the back view -- a chest-held slate went on
# glowing through a hunter who had turned away, which is the same draw-order
# trap as the hood.

def item_art(g, b, pal, item, facing):
    if facing == "up" and item not in ("dron", "kamizelki", "zaklocacz", "generator"):
        return
    glow, glow_lo = pal["glow"], pal["glow_lo"]
    left = facing == "left"
    hx = 12 if left else 19             # the hand, on whichever side leads
    d = -1 if left else 1
    y = b["top"] + 5

    def bar(x0, x1, yy, c):
        g.span(yy, min(x0, x1), max(x0, x1), c)

    if item == "tarcza":                                    # Strażnik
        g.rect(hx + d * 2, y - 6, hx + d * 4, y + 4, STEEL_LO)
        g.rect(hx + d * 3, y - 5, hx + d * 3, y + 3, STEEL)
        g.put(hx + d * 3, y - 1, glow)
    elif item == "kamizelki":
        g.rect(hx + d * 2, y - 4, hx + d * 4, y + 1, (68, 62, 50, 255))
        g.span(y - 3, hx + d * 2, hx + d * 4, (96, 88, 70, 255))
        g.put(hx + d * 3, y, glow_lo)
    elif item == "kotwica":
        for i in range(6):
            g.put(hx + d * 2, y - 4 + i, STEEL_LO)
        bar(hx + d, y + 2, hx + d * 4, STEEL)
        g.put(hx + d * 2, y - 5, glow)

    elif item == "dron":                                    # Zwiadowca
        g.rect(hx + d * 2, y - 7, hx + d * 5, y - 6, GEAR)
        g.put(hx + d * 2, y - 8, STEEL); g.put(hx + d * 5, y - 8, STEEL)
        g.put(hx + d * 3, y - 5, glow)
    elif item == "czujnik":
        g.rect(hx + d * 3, y - 3, hx + d * 3, y + 3, STEEL_LO)
        g.rect(hx + d * 2, y - 5, hx + d * 4, y - 4, GEAR)
        g.put(hx + d * 3, y - 5, glow)
    elif item == "optyka":
        g.rect(hx + d * 2, y - 2, hx + d * 4, y, GEAR)      # a long scope, carried
        g.put(hx + d * 4, y - 1, glow)

    elif item == "karabin":                                 # Strzelec
        for i in range(9):
            g.put(hx + d * (i - 1), y, STEEL if i > 3 else GEAR)
        g.span(y + 1, min(hx, hx + d * 2), max(hx, hx + d * 2), STEEL_LO)
        g.put(hx + d * 8, y, glow)
    elif item == "siatka":
        g.rect(hx + d, y - 1, hx + d * 4, y + 1, GEAR)
        g.rect(hx + d * 2, y - 2, hx + d * 3, y - 2, STEEL_LO)   # the drum
        g.put(hx + d * 4, y, glow)
    elif item == "znacznik":
        g.rect(hx + d, y - 1, hx + d * 3, y, GEAR)
        g.put(hx + d * 3, y - 2, glow)
        g.put(hx + d * 4, y - 3, glow_lo)

    elif item == "kadzidlo":                                # Inkwizytor
        for i in range(4):
            g.put(hx + d * 2, y - 4 + i, (40, 42, 52, 255))     # the chain
        g.rect(hx + d, y, hx + d * 3, y + 2, BRASS)
        g.put(hx + d * 2, y + 3, glow)
    elif item == "kajdany":
        g.rect(hx + d * 2, y - 1, hx + d * 3, y, STEEL_LO)
        g.rect(hx + d * 2, y + 2, hx + d * 3, y + 3, STEEL_LO)
        g.put(hx + d * 2, y + 1, STEEL)
    elif item == "wykrywacz":
        for i in range(7):
            g.put(hx + d * 2, y - 5 + i, STEEL_LO)
        g.put(hx + d * 2, y - 6, glow)
        g.put(hx + d, y - 6, glow_lo); g.put(hx + d * 3, y - 6, glow_lo)

    elif item == "stabilizator":                            # Chirurg
        g.rect(hx + d * 2, y - 2, hx + d * 3, y, GEAR)
        g.rect(hx + d * 2, y + 1, hx + d * 3, y + 1, STEEL)
        g.put(hx + d * 2, y - 3, glow); g.put(hx + d * 3, y - 3, glow_lo)
    elif item == "stymulanty":
        for i in range(3):                                  # vials on a bandolier
            g.put(hx + d * (2 + i), y - 2, GLASS)
            g.put(hx + d * (2 + i), y - 1, glow_lo)
    elif item == "autopsja":
        g.rect(hx + d * 2, y - 1, hx + d * 5, y - 1, STEEL)     # a saw blade
        for i in range(2, 6):
            g.put(hx + d * i, y - 2, STEEL_LO if i % 2 else GEAR_HI)
        g.rect(hx + d, y - 1, hx + d, y + 1, STRAP)

    elif item == "ekstraktor":                              # Runarz
        g.rect(hx + d * 2, y - 1, hx + d * 3, y + 1, GEAR)
        g.put(hx + d * 4, y - 2, STEEL); g.put(hx + d * 4, y + 2, STEEL)
        g.put(hx + d * 4, y, glow)
    elif item == "pieczec":
        g.rect(hx + d * 2, y - 2, hx + d * 4, y, BRASS)
        g.span(y - 1, hx + d * 2, hx + d * 4, glow_lo)
        g.put(hx + d * 3, y - 1, glow)
    elif item == "zaklocacz":
        g.rect(hx + d * 2, y - 2, hx + d * 4, y + 1, GEAR)
        for i in range(3):
            g.put(hx + d * 3, y - 3 - i, STEEL_LO)          # aerial
        g.put(hx + d * 3, y - 6, glow)

    elif item == "czytnik":                                 # Archiwista
        g.rect(hx + d, y - 3, hx + d * 4, y + 1, GEAR)
        g.rect(hx + d * 2, y - 2, hx + d * 3, y, glow_lo)
        g.span(y - 2, hx + d * 2, hx + d * 3, glow)
    elif item == "kopia":
        g.rect(hx + d, y - 2, hx + d * 4, y + 1, (52, 50, 56, 255))
        g.put(hx + d * 2, y - 1, GEAR_HI); g.put(hx + d * 4, y - 1, GEAR_HI)
        g.put(hx + d * 3, y + 1, glow_lo)
    elif item == "filtr":
        g.rect(hx + d * 2, y - 3, hx + d * 3, y + 1, GEAR)
        g.span(y - 3, hx + d * 2, hx + d * 3, STEEL)
        g.put(hx + d * 2, y, glow)

    elif item == "generator":                               # Technik
        g.rect(hx + d * 2, y - 3, hx + d * 4, y + 1, GEAR)
        g.span(y - 1, hx + d * 2, hx + d * 4, glow)
        g.span(y, hx + d * 2, hx + d * 4, glow_lo)
    elif item == "kamera":
        g.rect(hx + d * 3, y - 2, hx + d * 3, y + 2, STEEL_LO)
        g.rect(hx + d * 2, y - 4, hx + d * 4, y - 3, GEAR)
        g.put(hx + d * 4, y - 3, glow)
    elif item == "rygiel":
        g.rect(hx + d * 2, y - 1, hx + d * 2, y + 3, STEEL_LO)
        g.rect(hx + d, y - 3, hx + d * 3, y - 2, STEEL)     # a heavy bolt driver
        g.put(hx + d * 2, y - 4, glow_lo)


# ---------------------------------------------------------------- classes
#
# Order must match CLASS_NAMES in ../../wizard-hunt-online/src/classes.js, and
# each item list must match that class's items in the same order. The client
# indexes sheet rows by both positions, so an edit here without an edit there
# hands players somebody else's body and somebody else's kit.

def pal_for(skin, hair_kind, coat, glow):
    def sh(c, f):
        return (int(c[0] * f), int(c[1] * f), int(c[2] * f), 255)
    return dict(
        skin=SKINS[skin], hair=hair_kind,
        coat=coat, coat_hi=sh(coat, 1.32), coat_lo=sh(coat, 0.62),
        glow=glow, glow_lo=sh(glow, 0.55),
    )


CLASSES = [
    # name, build, head, palette, three items in classes.js order
    ("Strażnik",
     build(sh=8, wa=7, top=14, legw=2, gap=3),
     head_shell,
     pal_for(2, "black", (54, 58, 68), (196, 210, 232, 255)),
     ["tarcza", "kamizelki", "kotwica"]),

    ("Zwiadowca",
     build(sh=5, wa=4, top=14, legw=1, gap=3),
     head_goggles,
     pal_for(1, "sand", (48, 62, 50), (140, 240, 150, 255)),
     ["dron", "czujnik", "optyka"]),

    ("Strzelec",
     build(sh=6, wa=5, top=15, legw=1, gap=3),
     head_headset,
     pal_for(0, "brown", (58, 62, 52), (120, 208, 255, 255)),
     ["karabin", "siatka", "znacznik"]),

    ("Inkwizytor",
     build(sh=6, wa=6, top=13, legw=1, gap=2),
     head_hood,
     pal_for(3, "black", (72, 44, 44), (255, 168, 72, 255)),
     ["kadzidlo", "kajdany", "wykrywacz"]),

    ("Chirurg",
     build(sh=5, wa=5, top=16, legw=1, gap=2),
     head_mask,
     pal_for(1, "red", (74, 76, 62), (216, 232, 120, 255)),
     ["stabilizator", "stymulanty", "autopsja"]),

    ("Runarz",
     build(sh=7, wa=7, top=16, legw=2, gap=2),
     head_circlet,
     pal_for(2, "black", (62, 46, 74), (198, 130, 255, 255)),
     ["ekstraktor", "pieczec", "zaklocacz"]),

    ("Archiwista",
     build(sh=5, wa=7, top=15, legw=1, gap=3, lean=1),
     head_optics,
     pal_for(1, "grey", (52, 56, 68), (159, 180, 216, 255)),
     ["czytnik", "kopia", "filtr"]),

    ("Technik",
     build(sh=7, wa=6, top=16, legw=2, gap=3),
     head_cap,
     pal_for(3, "brown", (70, 56, 40), (255, 210, 122, 255)),
     ["generator", "kamera", "rygiel"]),
]


def hunter(cfg, item, facing, step):
    _, b, headfn, pal, _ = cfg
    g = G()
    bb = dict(b)
    if b["lean"] and facing != "up":
        bb["top"] = b["top"] + 1                            # a stoop, one pixel
    body(g, bb, pal, facing, step)
    item_art(g, bb, pal, item, facing)
    headfn(g, bb, pal, facing)
    return g.img


# ---------------------------------------------------------------- the sheet
#
# The row a state lives on is decided here, once, while it is being drawn --
# and then written down. Nothing else recomputes it. That is the whole point
# of the manifest: the client used to carry a copy of the formula
# `(class * 3 + item) * 4 + direction`, so did classes.js, and reordering
# either axis silently handed players somebody else's body with no error
# anywhere. A name cannot drift the way an index can.

FRAMES = 2


def emissive(img, pal):
    """The pixels that are their own light source, on a transparent field.

    A second sheet rather than a channel trick, because the client has no
    shaders: SS14 marks a layer unshaded and skips lighting for it, and with
    one canvas and one gradient the only equivalent is draw order. These
    pixels get drawn *after* the fog, so a lamp at the edge of somebody's
    vision stops fading at the same rate as the body carrying it.

    What counts as emissive is the generator's own existing convention -- a
    class's `glow` and `glow_lo` are the powered colours, used for the chest
    light, the Technik's lamp, the Strażnik's lit visor, the Runarz's etching
    and every item indicator. Amber goggle glass is *not* here: a lens
    catching light is not a lens producing it.
    """
    out = Image.new("RGBA", img.size, (0, 0, 0, 0))
    keep = {pal["glow"], pal["glow_lo"]}
    src, dst = img.load(), out.load()
    for y in range(img.height):
        for x in range(img.width):
            c = src[x, y]
            if c in keep:
                dst[x, y] = c
    return out


states = []
row = 0
rows_total = sum(len(cfg[4]) for cfg in CLASSES) * len(DIRS)
sheet = Image.new("RGBA", (S * FRAMES, S * rows_total), (0, 0, 0, 0))
glow_sheet = Image.new("RGBA", (S * FRAMES, S * rows_total), (0, 0, 0, 0))

for cfg in CLASSES:
    for item in cfg[4]:
        states.append({
            "name": f"{cfg[0]}/{item}",
            "row": row,
            "directions": len(DIRS),
            "frames": FRAMES,
        })
        for di, _d in enumerate(DIRS):
            for step in range(FRAMES):
                f = hunter(cfg, item, _d, step)
                at = (step * S, (row + di) * S)
                sheet.paste(f, at, f)
                gl = emissive(f, cfg[3])
                glow_sheet.paste(gl, at, gl)
        row += len(DIRS)

sheet.save(os.path.join(OUT, "hunters.png"))
glow_sheet.save(os.path.join(OUT, "hunters_glow.png"))

# The manifest, after RSI's meta.json. Field order is the insertion order of
# these literals and `states` is built in draw order, so regenerating an
# unchanged sheet gives a byte-identical file -- a manifest that churned
# would make every diff in this directory unreadable.
#
# ensure_ascii=False on purpose: `Strażnik` is the key the client looks up,
# and escaping it to ż would work but make the file unreadable by the
# person most likely to need to read it.
manifest = {
    "version": 1,
    "size": {"x": S, "y": S},
    "sheets": {"base": "hunters.png", "emissive": "hunters_glow.png"},
    "directions": list(DIRS),
    "states": states,
}
with open(os.path.join(OUT, "hunters.json"), "w", encoding="utf-8") as fh:
    json.dump(manifest, fh, ensure_ascii=False, indent=2)
    fh.write("\n")

# a contact sheet of the front pose, one row per class, one column per item:
# the only honest way to check that eight people read as eight people
PAD = 4
contact = Image.new("RGBA", ((S + PAD) * 3, (S + PAD) * len(CLASSES)), (22, 28, 42, 255))
for ci, cfg in enumerate(CLASSES):
    for ii, item in enumerate(cfg[4]):
        f = hunter(cfg, item, "down", 0)
        contact.paste(f, (ii * (S + PAD), ci * (S + PAD)), f)
contact.resize((contact.width * 5, contact.height * 5), Image.NEAREST).save(
    os.path.join(OUT, "hunters_classes.png"))

# and every class side by side at the size it is actually played at
line = Image.new("RGBA", ((S + 2) * len(CLASSES), S + 4), (22, 28, 42, 255))
for ci, cfg in enumerate(CLASSES):
    f = hunter(cfg, cfg[4][0], "down", 0)
    line.paste(f, (ci * (S + 2) + 1, 2), f)
line.resize((line.width * 3, line.height * 3), Image.NEAREST).save(
    os.path.join(OUT, "hunters_actual.png"))

# all four facings, so the turned and back views get looked at too
turn = Image.new("RGBA", ((S + PAD) * 4, (S + PAD) * len(CLASSES)), (22, 28, 42, 255))
for ci, cfg in enumerate(CLASSES):
    for di, d in enumerate(DIRS):
        f = hunter(cfg, cfg[4][0], d, 0)
        turn.paste(f, (di * (S + PAD), ci * (S + PAD)), f)
turn.resize((turn.width * 5, turn.height * 5), Image.NEAREST).save(
    os.path.join(OUT, "hunters_facings.png"))

print("done", sheet.size, rows_total, "rows,", len(states), "states")

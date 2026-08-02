"""Five designs for one hunter: people carrying equipment, not machines.

The current sprites read as robots for two reasons, and neither is the
colour. Every head is a sealed helmet with a glowing slit -- no face, no
skin, no hair -- and every body is one solid block from shoulder to hip with
no neck and no layers.

So all five keep the same class (Strzelec, the marksman), the same palette
family and the same 32x32 frame, and vary only how much of the person is
showing and how the kit is worn. The point is to compare the design language,
not five different characters.

    A  Odkryta twarz   no helmet at all: hair, stubble, headset, one eyepiece
    B  Gogle na czole  goggles pushed up, scarf pulled down off the mouth
    C  Półmaska        lower-face respirator, eyes and brow bare
    D  Kaptur          hood over a soft cap, cables into a neck port
    E  Hełm otwarty    hard shell, visor raised, face visible in the opening

Shared human corrections applied to all five: a visible neck, shoulders
narrower than the old block, a jacket layered over a vest so the torso is
not one silhouette, asymmetric kit (one pauldron, one rolled sleeve), and
fabric colours warmer than the steel so cloth does not read as plate.
"""
import os
from PIL import Image

S = 32
OUT = os.path.dirname(os.path.abspath(__file__))

SKIN     = (206, 158, 122, 255)
SKIN_LO  = (156, 112, 84, 255)
SKIN_HI  = (232, 186, 150, 255)
HAIR     = (58, 44, 38, 255)
HAIR_HI  = (86, 66, 54, 255)
STUBBLE  = (86, 70, 62, 255)
EYE      = (30, 34, 44, 255)

COAT     = (58, 62, 52, 255)      # olive field jacket
COAT_HI  = (78, 84, 70, 255)
COAT_LO  = (36, 40, 32, 255)
VEST     = (46, 52, 66, 255)      # armour vest over it
VEST_HI  = (66, 76, 94, 255)
VEST_LO  = (28, 32, 42, 255)
STRAP    = (72, 54, 38, 255)
STRAP_HI = (104, 78, 54, 255)
BOOT     = (34, 32, 38, 255)
STEEL    = (120, 132, 152, 255)
STEEL_LO = (72, 82, 98, 255)
GLOW     = (120, 208, 255, 255)
GLOW_LO  = (52, 118, 168, 255)
LENS     = (214, 150, 72, 255)    # amber goggle glass, warm against the steel
LENS_HI  = (242, 196, 118, 255)
RUBBER   = (40, 42, 48, 255)
GEAR     = (84, 90, 104, 255)     # kit that must not read as a shadow
GEAR_HI  = (116, 124, 142, 255)
CLOTH    = (96, 72, 58, 255)      # scarf / hood cloth


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


def body(g):
    """Everything below the chin. Shared, so the heads are the only variable.

    Narrower than the old sprite and layered: jacket first, vest over it,
    straps over that. One pauldron and one rolled sleeve, because a perfectly
    symmetric figure reads as manufactured."""
    # legs
    g.rect(12, 25, 14, 30, COAT_LO)
    g.rect(17, 25, 19, 30, COAT_LO)
    g.rect(12, 30, 14, 31, BOOT)
    g.rect(17, 30, 19, 31, BOOT)

    # jacket: shoulders slope in, hem flares slightly
    g.rect(10, 15, 21, 25, COAT)
    g.span(15, 11, 20, COAT_HI)
    g.rect(10, 24, 21, 25, COAT_LO)
    g.rect(10, 16, 10, 23, COAT_LO)
    g.rect(21, 16, 21, 23, COAT_HI)

    # armour vest over the jacket, shorter, so two layers are visible
    g.rect(12, 16, 19, 22, VEST)
    g.span(16, 13, 18, VEST_HI)
    g.rect(12, 22, 19, 22, VEST_LO)
    g.put(15, 18, GLOW_LO)                     # a status light on the chest
    g.put(16, 18, GLOW)

    # straps: one over the shoulder, one round the waist
    for y in range(16, 23):
        g.put(13 + (y - 16) // 3, y, STRAP)
    g.span(23, 11, 20, STRAP)
    g.span(23, 15, 16, STRAP_HI)

    # arms: right one armoured at the shoulder, left sleeve rolled to skin
    g.rect(8, 16, 9, 23, COAT)
    g.rect(8, 15, 10, 16, STEEL_LO)            # pauldron, one side only
    g.span(15, 8, 9, STEEL)
    g.rect(22, 16, 23, 20, COAT)
    g.rect(22, 21, 23, 23, SKIN)               # rolled sleeve
    g.put(22, 21, SKIN_HI)

    # rifle held across the body, muzzle to the right
    g.rect(19, 20, 27, 20, STEEL_LO)
    g.rect(19, 19, 24, 19, STEEL)
    g.put(27, 20, GLOW)
    g.rect(17, 20, 18, 22, STEEL_LO)


def face(g, dy=0, mouth=True, stubble=True):
    """The human part. Eyes sit one pixel apart with a bridge between them --
    two adjacent lit pixels read as a single visor, which is exactly the
    robot problem."""
    g.rect(12, 5 + dy, 19, 13 + dy, SKIN)
    g.rect(12, 5 + dy, 12, 13 + dy, SKIN_LO)
    g.rect(19, 5 + dy, 19, 13 + dy, SKIN_HI)
    g.span(6 + dy, 13, 18, SKIN_HI)
    # brow shadow gives the face a top edge without an outline
    g.span(8 + dy, 13, 18, SKIN_LO)
    g.put(14, 9 + dy, EYE)
    g.put(17, 9 + dy, EYE)
    g.put(15, 9 + dy, SKIN_LO)                 # the bridge of the nose
    g.put(16, 9 + dy, SKIN_LO)
    if mouth:
        g.span(12 + dy, 15, 16, SKIN_LO)
    if stubble:
        g.span(13 + dy, 13, 18, STUBBLE)
    # neck: the single most humanising pixel run on the whole sprite
    g.rect(14, 14 + dy, 17, 15 + dy, SKIN_LO)


def hair(g, dy=0):
    g.span(4 + dy, 13, 18, HAIR)
    g.span(5 + dy, 12, 19, HAIR)
    g.put(12, 6 + dy, HAIR)
    g.put(19, 6 + dy, HAIR)
    g.span(4 + dy, 15, 17, HAIR_HI)


# ---------------------------------------------------------------- designs

def design_a():
    """No helmet at all. Headset with a boom mic and one eyepiece."""
    g = G()
    body(g)
    face(g)
    hair(g)
    # the band rides on the hairline, not on the brow: anything dark crossing
    # row 8 or 9 covers both eyes at once and the face becomes a visor again
    g.span(5, 12, 19, GEAR)
    g.span(4, 14, 17, GEAR_HI)
    g.rect(11, 6, 11, 9, GEAR)                 # earcups, one per side
    g.rect(20, 6, 20, 9, GEAR)
    g.put(11, 7, GEAR_HI)
    g.put(20, 10, STEEL_LO)                    # eyepiece arm swings past the eye
    g.put(20, 9, LENS_HI)                      # lit lens beside it, never over it
    g.rect(11, 10, 11, 12, RUBBER)             # boom mic down to the jaw
    g.put(12, 12, RUBBER)
    return g


def design_b():
    """Goggles pushed up onto the forehead, scarf pulled down off the mouth."""
    g = G()
    body(g)
    face(g)
    hair(g)
    g.span(7, 12, 19, RUBBER)                  # strap round the back of the head
    g.rect(12, 4, 19, 6, RUBBER)               # goggles sat on the forehead
    g.rect(13, 5, 15, 6, LENS)
    g.rect(16, 5, 18, 6, LENS)
    g.put(13, 5, LENS_HI); g.put(16, 5, LENS_HI)
    g.put(15, 5, STEEL); g.put(16, 5, STEEL)   # nose bridge between the cups
    g.put(11, 5, GEAR); g.put(20, 5, GEAR)     # the pivots break the outline
    g.rect(13, 13, 18, 15, CLOTH)              # scarf bunched at the throat
    g.span(13, 14, 17, (122, 94, 74, 255))
    return g


def design_c():
    """Lower-face respirator. Eyes and brow bare, hair loose."""
    g = G()
    body(g)
    face(g, mouth=False, stubble=False)
    hair(g)
    # the cup covers the mouth and nothing else. Drawn in mid grey, not the
    # near-black rubber: at this size a dark shape wider than four pixels stops
    # being an object worn on a face and becomes the bottom half of a helmet
    g.rect(14, 11, 17, 13, GEAR)
    g.span(11, 14, 17, GEAR_HI)
    g.rect(14, 13, 17, 13, STEEL_LO)
    g.put(13, 11, RUBBER); g.put(18, 11, RUBBER)     # straps back to the ears
    g.put(12, 10, RUBBER); g.put(19, 10, RUBBER)
    g.put(15, 12, GLOW_LO); g.put(16, 12, GLOW_LO)   # filter indicator
    g.span(10, 13, 18, SKIN_LO)                      # cheekbone, kept bare
    return g


def design_d():
    """Hood over a soft cap. Face in shadow but the proportions stay human."""
    g = G()
    body(g)
    face(g, stubble=False)
    # hood drawn AFTER the face, so it can shade the brow rather than being
    # hidden behind it -- the same draw-order trap as the beard and the robe
    # a hood only one pixel wider than the skull is a haircut. This one is four
    # wider and hangs past the shoulders, so the silhouette alone tells it apart
    # across a dark room -- which is the whole job of a design variant
    # Canvas grey-green, deliberately nowhere near the hair brown: in the first
    # pass the hood was CLOTH, one hue off the hair, and the whole design read
    # as a hunter with long hair instead of a hunter wearing something.
    HOOD    = (78, 76, 64, 255)
    HOOD_LO = (48, 48, 40, 255)
    HOOD_HI = (108, 104, 86, 255)
    # Cloth three pixels thick, dark on the outside and lit on the inside edge.
    # That thickness is the entire difference between a hood and hair: hair
    # frames a face too, and both earlier passes read as long hair because the
    # drape was a flat two-pixel curtain with no rim around the opening.
    g.span(2, 14, 17, HOOD)                    # a peak, so the crown is angular
    g.span(3, 12, 19, HOOD)
    g.rect(10, 4, 21, 6, HOOD)
    g.rect(9, 7, 11, 17, HOOD)                 # one continuous mass from the
    g.rect(20, 7, 22, 17, HOOD)                # crown into the shoulders
    g.rect(9, 7, 9, 17, HOOD_LO)               # outer edge in shadow
    g.rect(22, 7, 22, 17, HOOD_LO)
    g.span(17, 9, 11, HOOD_LO)                 # square hem: cloth is cut,
    g.span(17, 20, 22, HOOD_LO)                # hair tapers
    g.span(2, 14, 17, HOOD_LO)
    g.rect(11, 6, 11, 15, HOOD_HI)             # the lit inner rim of the opening
    g.rect(20, 6, 20, 15, HOOD_HI)
    g.span(5, 12, 19, HOOD_HI)
    g.rect(12, 6, 19, 7, (40, 40, 34, 255))    # shadow across the brow, not the eyes
    g.put(14, 9, EYE); g.put(17, 9, EYE)
    g.put(20, 13, GLOW_LO)                     # cable into a neck port
    g.put(20, 14, GLOW_LO)
    g.rect(19, 15, 21, 16, STEEL_LO)
    return g


def design_e():
    """Hard shell, visor raised. A helmet you can see a person inside."""
    g = G()
    body(g)
    face(g, stubble=False)
    g.span(4, 12, 19, STEEL_LO)                # shell
    g.span(5, 11, 20, STEEL)
    g.rect(11, 6, 11, 10, STEEL_LO)
    g.rect(20, 6, 20, 10, STEEL_LO)
    g.span(6, 12, 19, STEEL_LO)
    g.rect(12, 2, 19, 3, STEEL)                # visor swung up above the brow
    g.span(2, 13, 18, STEEL_LO)
    g.span(3, 13, 18, GLOW_LO)                 # glass reads on the underside:
    g.put(14, 3, GLOW)                          # lit along the top it was a hatband
    g.put(11, 3, GEAR); g.put(20, 3, GEAR)     # hinges, so the visor is attached
    g.put(11, 4, GEAR_HI); g.put(20, 4, GEAR_HI)
    g.put(19, 5, GLOW)                          # lamp on the shell
    g.rect(11, 11, 11, 12, STRAP)              # chinstrap
    g.rect(20, 11, 20, 12, STRAP)
    return g


DESIGNS = [
    ("A · odkryta twarz", design_a),
    ("B · gogle na czole", design_b),
    ("C · półmaska", design_c),
    ("D · kaptur", design_d),
    ("E · hełm otwarty", design_e),
]

sheet = Image.new("RGBA", (S * len(DESIGNS), S), (0, 0, 0, 0))
for i, (_, fn) in enumerate(DESIGNS):
    im = fn().img
    sheet.paste(im, (i * S, 0), im)
sheet.save(os.path.join(OUT, "hunter_designs.png"))

# review sheet: on the deck plating, big, with breathing room between them
PAD, Z = 10, 8
w = (S + PAD) * len(DESIGNS) * Z
big = Image.new("RGBA", (w, (S + PAD) * Z), (22, 28, 42, 255))
for i, (_, fn) in enumerate(DESIGNS):
    im = fn().img.resize((S * Z, S * Z), Image.NEAREST)
    big.paste(im, (int((i * (S + PAD) + PAD / 2) * Z), int(PAD / 2 * Z)), im)
big.save(os.path.join(OUT, "hunter_designs_preview.png"))

# and the same row at the size it is actually played at, which is the only
# honest test of whether a face survives
small = Image.new("RGBA", ((S + 4) * len(DESIGNS), S + 4), (22, 28, 42, 255))
for i, (_, fn) in enumerate(DESIGNS):
    im = fn().img
    small.paste(im, (i * (S + 4) + 2, 2), im)
small.resize((small.width * 2, small.height * 2), Image.NEAREST).save(
    os.path.join(OUT, "hunter_designs_actual.png"))

print("wrote hunter_designs.png", sheet.size, "->", ", ".join(n for n, _ in DESIGNS))

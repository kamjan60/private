"""Flat mascot / sticker style, drawn with Pillow's ImageDraw vector
primitives instead of hand-plotted rows.

Why this beats per-pixel plotting for this style:
  * curves (curled hat tip, wavy beard hem, shepherd's crook) come out
    smooth instead of stair-stepped guesswork,
  * stroking each shape after filling it gives the style's *internal*
    outlines (hat->face, beard->robe) for free,
  * shapes are authored in readable 64-unit logical coordinates.

Pipeline: draw everything at SS x supersample -> BOX downsample (area
average, so edges land on real coverage) -> snap every pixel back to the
flat palette -> outline_pass to guarantee a closed silhouette. The snap is
what keeps it *pixel art*: no antialiased half-tones survive.

See ../../reference/flat-mascot-style.md for the style rules.
"""
import math
import os
import sys

from PIL import Image, ImageDraw

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
from pixel_lib import outline_pass

SIZE = 64          # logical canvas
SS = 8             # supersample factor
PREVIEW = 8
OUT = os.path.dirname(__file__)
CX = 32.0

OUTLINE     = (26, 22, 20, 255)
HAT_MAIN    = (90, 84, 80, 255)
HAT_DARK    = (56, 51, 47, 255)
HAT_LIGHT   = (138, 128, 120, 255)
FACE_SHADOW = (46, 42, 40, 255)
ROBE_MAIN   = (120, 111, 102, 255)
ROBE_SHADOW = (84, 76, 69, 255)
BEARD       = (238, 232, 220, 255)
BEARD_SHADE = (199, 191, 175, 255)
STAFF       = (122, 90, 58, 255)
STAFF_DARK  = (90, 64, 38, 255)
SKIN        = (201, 171, 140, 255)
BOOT        = (40, 34, 30, 255)

PALETTE = [OUTLINE, HAT_MAIN, HAT_DARK, HAT_LIGHT, FACE_SHADOW, ROBE_MAIN,
           ROBE_SHADOW, BEARD, BEARD_SHADE, STAFF, STAFF_DARK, SKIN, BOOT]

STROKE = 1.15      # outline thickness in logical units (~1px after downsample)


def s(v):
    """logical unit -> device pixel"""
    return v * SS


def pts(seq):
    return [(s(x), s(y)) for x, y in seq]


def shape(draw, poly, fill, stroke=STROKE, outline=OUTLINE):
    """Fill a polygon, then stroke its border. Stroking as a separate closed
    line (rather than polygon(width=)) keeps joints clean and works the same
    for the internal seams between overlapping shapes."""
    dev = pts(poly)
    if fill is not None:
        draw.polygon(dev, fill=fill)
    if stroke:
        draw.line(dev + [dev[0]], fill=outline, width=max(1, int(s(stroke))), joint="curve")


def thick_line(draw, a, b, width, fill):
    draw.line([(s(a[0]), s(a[1])), (s(b[0]), s(b[1]))],
              fill=fill, width=max(1, int(s(width))))


def taper_spine(spine):
    """Build a closed polygon from a spine of (x, y, half_width) points -
    used for the tapering, curling hat crown."""
    left, right = [], []
    n = len(spine)
    for i, (x, y, hw) in enumerate(spine):
        if i == 0:
            nx, ny = spine[1][0] - x, spine[1][1] - y
        elif i == n - 1:
            nx, ny = x - spine[-2][0], y - spine[-2][1]
        else:
            nx = spine[i + 1][0] - spine[i - 1][0]
            ny = spine[i + 1][1] - spine[i - 1][1]
        ln = math.hypot(nx, ny) or 1.0
        px_, py_ = -ny / ln * hw, nx / ln * hw
        left.append((x + px_, y + py_))
        right.append((x - px_, y - py_))
    return left + right[::-1]


def beard_shape(x_top_l, x_top_r, y_top, x_bot_l, x_bot_r, y_flat, bulge, samples=40):
    """Tapering band closed by a single rounded (elliptical) bottom.

    A sine-scalloped hem was the first attempt and it snapped to sharp
    zig-zag teeth on the 64px grid - the lobe cusps are sub-pixel. One
    broad arc survives the downsample as an actual curve.
    """
    cx = (x_bot_l + x_bot_r) / 2.0
    rx = (x_bot_r - x_bot_l) / 2.0
    bottom = []
    for i in range(samples + 1):
        t = i / samples
        x = x_bot_l + (x_bot_r - x_bot_l) * t
        u = max(-1.0, min(1.0, (x - cx) / rx))
        bottom.append((x, y_flat + bulge * math.sqrt(max(0.0, 1.0 - u * u))))
    return [(x_top_l, y_top), (x_bot_l, y_flat)] + bottom + [(x_top_r, y_top)]


def robe_edge(t, side, y_top, y_bot, x_top, x_bot, bulge):
    """One point on a convex robe side, so the robe and its cast shadow can
    be built from the exact same curve."""
    b = math.sin(t * math.pi) * bulge * side
    return (x_top + (x_bot - x_top) * t + b, y_top + (y_bot - y_top) * t)


def bulged(x_top_l, x_top_r, y_top, x_bot_l, x_bot_r, y_bot, bulge, samples=24):
    """Trapezoid with gently convex sides - the robe silhouette."""
    left = [robe_edge(i / samples, -1, y_top, y_bot, x_top_l, x_bot_l, bulge)
            for i in range(samples + 1)]
    right = [robe_edge(i / samples, 1, y_top, y_bot, x_top_r, x_bot_r, bulge)
             for i in range(samples + 1)]
    return left + right[::-1]


def render():
    img = Image.new("RGBA", (SIZE * SS, SIZE * SS), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)

    # ---- boots (drawn first; the robe hem overlaps their tops) ----
    for bx in (CX - 7.5, CX + 1.5):
        shape(d, [(bx, 52), (bx + 6, 52), (bx + 6, 58), (bx, 58)], BOOT)

    # ---- robe: plain, gentle flare, convex sides ----
    robe = bulged(CX - 10, CX + 10, 26, CX - 15, CX + 15, 56.5, bulge=1.6)
    shape(d, robe, ROBE_MAIN)

    # single flat shadow shape - lower-left of the robe, hard edged, no ramp
    shadow = [(CX - 14.2, 56.2), (CX - 2.5, 56.2), (CX - 3.5, 38), (CX - 11.4, 38)]
    shape(d, shadow, ROBE_SHADOW, stroke=0)

    # ---- staff with a shepherd's-crook top ----
    staff_x = 14.0
    thick_line(d, (staff_x, 13.0), (staff_x, 59.5), 2.3, STAFF)
    crook_r = 4.6
    d.arc([s(staff_x - crook_r), s(9.0 - crook_r), s(staff_x + crook_r), s(9.0 + crook_r)],
          start=90, end=0, fill=STAFF, width=int(s(2.3)))
    d.arc([s(staff_x - crook_r), s(9.0 - crook_r), s(staff_x + crook_r), s(9.0 + crook_r)],
          start=200, end=310, fill=STAFF_DARK, width=int(s(1.0)))

    # ---- face: narrow, sits in hat shadow, no drawn eyes ----
    shape(d, [(CX - 6.5, 17), (CX + 6.5, 17), (CX + 6, 27), (CX - 6, 27)], FACE_SHADOW)

    # ---- beard: constant width, scalloped wavy hem ----
    beard = wavy_band(CX - 7.2, CX + 7.2, 23.5, 40.0, amp=1.9, waves=2.0)
    shape(d, beard, BEARD)
    # one soft shade band, flat (no dithering, no ramp)
    d.polygon(pts([(CX - 1.4, 25), (CX + 1.4, 25), (CX + 1.4, 39), (CX - 1.4, 39)]),
              fill=BEARD_SHADE)

    # ---- hat: wide brim ellipse + tapering crown that curls at the tip ----
    crown = taper_spine([
        (CX - 0.5, 17.5, 10.5), (CX + 0.5, 13.5, 9.0), (CX + 2.5, 9.5, 7.2),
        (CX + 5.5, 6.3, 5.4), (CX + 9.5, 4.6, 3.9), (CX + 13.0, 5.6, 2.8),
        (CX + 14.4, 8.4, 2.0), (CX + 12.6, 10.2, 1.4),
    ])
    shape(d, crown, HAT_MAIN)

    brim = [(CX - 22, 17.4), (CX - 12, 14.4), (CX + 12, 14.4), (CX + 22, 17.4),
            (CX + 12, 20.2), (CX - 12, 20.2)]
    shape(d, brim, HAT_MAIN)
    # brim underside = the hat's single flat shadow; top edge catches light
    d.polygon(pts([(CX - 19, 18.4), (CX + 19, 18.4), (CX + 11, 20.0), (CX - 11, 20.0)]),
              fill=HAT_DARK)
    d.line(pts([(CX - 17, 15.6), (CX - 6, 14.9)]), fill=HAT_LIGHT, width=int(s(1.1)))

    # ---- hands: one grips the staff, one gestures free of the silhouette ----
    shape(d, [(staff_x - 2.6, 29), (staff_x + 2.6, 29), (staff_x + 2.6, 33.5), (staff_x - 2.6, 33.5)], SKIN)
    shape(d, [(CX + 9, 33), (CX + 15.5, 34.5), (CX + 15, 39), (CX + 9, 37.5)], SKIN)
    d.line(pts([(CX + 13.2, 35.4), (CX + 13.0, 38.4)]), fill=OUTLINE, width=int(s(0.9)))

    # ---- supersample -> pixel grid ----
    small = img.resize((SIZE, SIZE), Image.BOX)
    return snap_to_palette(small)


def snap_to_palette(img):
    """Kill the antialiasing the downsample introduced: hard alpha cut, then
    every surviving pixel jumps to its nearest palette entry."""
    out = img.copy()
    p = out.load()
    for y in range(out.height):
        for x in range(out.width):
            r, g, b, a = p[x, y]
            if a < 110:
                p[x, y] = (0, 0, 0, 0)
                continue
            best, best_d = PALETTE[0], None
            for c in PALETTE:
                dist = (r - c[0]) ** 2 + (g - c[1]) ** 2 + (b - c[2]) ** 2
                if best_d is None or dist < best_d:
                    best, best_d = c, dist
            p[x, y] = best
    return out


frame = outline_pass(render(), OUTLINE)
frame.save(os.path.join(OUT, "mascot_pillow.png"))
frame.resize((SIZE * PREVIEW, SIZE * PREVIEW), Image.NEAREST).save(
    os.path.join(OUT, "mascot_pillow_preview.png"))
print("done")

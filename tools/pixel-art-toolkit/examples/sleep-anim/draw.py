"""Sleep spell - 40x48, 8-frame loop.

A deliberate counterweight to the fireball and the chain lightning. Those
two are fast, high-contrast and saturated; this one has to read as slow
and soft, so almost every choice is inverted: a muted lavender ramp, a
languid 200ms frame, and motion that drifts instead of snapping.

Three Z glyphs carry the spell. They are the whole signifier - a soft
violet aura on its own could be any enchantment - and they are spaced a
third of the loop apart so one is always mid-rise. Staggering them this
way also keeps the frame count honest: a single Z rising and fading would
leave frames where nothing moves.

The ground ring is an ellipse rather than a circle. Drawn as a circle it
reads as a bubble floating in front of the target instead of a rune lying
on the floor beneath it.
"""
import math
import os

from PIL import Image

W, H = 40, 48
FRAMES = 8
SCALE = 8
OUT = os.path.dirname(__file__)

Z_HI   = (236, 230, 255, 255)
Z_MID  = (176, 160, 232, 255)
Z_LOW  = (106, 92, 168, 255)
RING_HI = (200, 184, 248, 255)
RING    = (136, 120, 208, 255)
RING_LO = (74, 63, 128, 255)
MOTE    = (216, 208, 240, 255)

CX = 20
GROUND_Y = 41


class Frame:
    def __init__(self):
        self.img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        self.p = self.img.load()

    def put(self, x, y, c):
        x, y = int(round(x)), int(round(y))
        if 0 <= x < W and 0 <= y < H:
            self.p[x, y] = c


def draw_z(fr, cx, cy, scale, colour):
    """Z glyph. Two horizontal bars joined by a diagonal - at 3-5px the
    diagonal has to be a clean staircase or the letter turns to mush."""
    if scale >= 2:
        w, h = 5, 6
    else:
        w, h = 3, 4
    x0 = cx - w // 2
    for i in range(w):                       # top and bottom bars
        fr.put(x0 + i, cy, colour)
        fr.put(x0 + i, cy + h - 1, colour)
    for j in range(1, h - 1):                # diagonal, top-right to bottom-left
        t = (j - 1) / max(h - 3, 1)
        fr.put(x0 + round((w - 1) * (1 - t)), cy + j, colour)


def draw_ring(fr, phase):
    """Flattened ellipse on the ground, pulsing outward."""
    pulse = 0.5 + 0.5 * math.sin(phase)
    rx = 9.0 + 4.0 * pulse
    ry = rx * 0.44          # any flatter and the outline has no interior left
    colour = RING_HI if pulse > 0.66 else (RING if pulse > 0.25 else RING_LO)

    def ellipse(r_x, r_y, col, dashed=False):
        # Sample count has to scale with the radius. Fixed at the outer
        # ring's count, the inner one's samples bunch up and flood it into
        # a solid blob instead of staying an outline.
        steps = max(12, int(r_x * 8))
        for i in range(steps):
            if dashed and (i * 5 // steps) % 2:
                continue
            a = i / steps * 2 * math.pi
            fr.put(CX + math.cos(a) * r_x, GROUND_Y + math.sin(a) * r_y, col)

    ellipse(rx, ry, colour)
    # Inner ring is dashed. Solid, it is only two pixels tall at this
    # flattening and fills in regardless of sample count - and a broken
    # circle reads as a rune rather than as a smudge.
    ellipse(rx * 0.58, ry * 0.58, RING_LO, dashed=True)


def build(f):
    fr = Frame()
    phase = f / FRAMES * 2 * math.pi
    draw_ring(fr, phase)

    # drifting motes, orbiting slowly and bobbing
    for i in range(5):
        a = phase * 0.6 + i * (2 * math.pi / 5)
        r = 11 + 2 * math.sin(phase + i)
        fr.put(CX + math.cos(a) * r, GROUND_Y - 4 + math.sin(a) * r * 0.3, MOTE)

    for i in range(3):
        # thirds of the loop apart, so one Z is always mid-rise
        t = ((f / FRAMES) + i / 3.0) % 1.0
        y = GROUND_Y - 6 - t * 32
        x = CX + math.sin(t * math.pi * 1.4 + i * 2.0) * 6   # lazy sideways drift
        scale = 2 if t > 0.35 else 1
        # fades as it rises: bright low, gone at the top
        # Holds the bright tone most of the rise and only drops on the last
        # stretch. Fading evenly across the whole climb leaves the upper Z
        # too faint to read against a light background.
        colour = Z_HI if t < 0.55 else (Z_MID if t < 0.85 else Z_LOW)
        draw_z(fr, x, y, scale, colour)
    return fr.img


frames = [build(f) for f in range(FRAMES)]
for i, im in enumerate(frames):
    im.save(os.path.join(OUT, f"sleep_{i}.png"))

sheet = Image.new("RGBA", (W * FRAMES, H), (0, 0, 0, 0))
for i, im in enumerate(frames):
    sheet.paste(im, (i * W, 0), im)
sheet.save(os.path.join(OUT, "sleep_sheet.png"))
sheet.resize((sheet.width * 4, H * 4), Image.NEAREST).save(
    os.path.join(OUT, "sleep_sheet_preview.png"))

big = [im.resize((W * SCALE, H * SCALE), Image.NEAREST) for im in frames]
big[0].save(os.path.join(OUT, "sleep.gif"), save_all=True,
            append_images=big[1:], duration=200, loop=0, disposal=2)
print("done")

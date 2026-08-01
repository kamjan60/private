"""Flying fireball - 32x32, 6-frame loop, outline-free arcade dialect.

Built as a field rather than as drawn shapes: for every column the flame
has a half-height, and each pixel picks its colour from how far it sits
from the centre line as a fraction of that height. Concentric bands fall
out of that automatically - deep red at the edge, orange, yellow, white
core - which is exactly how a flame reads, and it keeps the bands in
register while the silhouette wobbles.

The wobble is a sine along the trail whose phase advances each frame. Two
details matter for it to read as fire rather than as a wagging tail:

* The head barely moves. Only the trail's amplitude ramps up toward the
  tail, so the projectile stays anchored and the flame whips behind it.
* The tail end is deliberately ragged - every other column is clipped a
  little short - because a smoothly tapering point reads as a comet or a
  teardrop, not as combustion.

Loops seamlessly: the phase covers exactly one full period across the six
frames.
"""
import math
import os

from PIL import Image

SIZE = 32
FRAMES = 6
SCALE = 8
OUT = os.path.dirname(__file__)

WHITE  = (255, 246, 214, 255)
YELLOW = (255, 212, 74, 255)
ORANGE = (255, 140, 26, 255)
RED    = (232, 72, 26, 255)
DEEP   = (168, 32, 16, 255)
EMBER  = (255, 233, 138, 255)

CY = 16          # centre line
HEAD_X = 22      # centre of the round leading head
HEAD_R = 7.0
TAIL_X = 2


def half_height(x, phase):
    """Flame half-height at column x, in pixels."""
    if x > HEAD_X + HEAD_R:
        return 0.0
    if x >= HEAD_X:
        # round leading edge
        d = (x - HEAD_X) / HEAD_R
        return HEAD_R * math.sqrt(max(0.0, 1.0 - d * d))
    if x < TAIL_X:
        return 0.0
    # Trail: tapers toward the tail and wobbles harder the further back it
    # is. Two sines at unrelated frequencies rather than one - a single
    # wave (or worse, clipping alternate columns) produces a regular
    # sawtooth that reads as a fish skeleton, not as fire.
    t = (x - TAIL_X) / float(HEAD_X - TAIL_X)
    base = HEAD_R * (t ** 0.75)
    slow = 0.26 * (1.0 - t) * math.sin(x * 0.55 + phase)
    fast = 0.13 * math.sin(x * 1.27 - phase * 1.7)
    return base * (1.0 + slow + fast)


def build(frame):
    phase = frame / float(FRAMES) * 2 * math.pi
    img = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    p = img.load()

    for x in range(SIZE):
        h = half_height(x, phase)
        if h <= 0.4:
            continue
        hi = int(round(h))
        for dy in range(-hi, hi + 1):
            y = CY + dy
            if not (0 <= y < SIZE):
                continue
            # Concentric bands come from distance-to-centreline as a
            # fraction of the local height, so they stay in register while
            # the silhouette wobbles.
            r = abs(dy) / max(h, 0.001)
            # The white core is anchored to the head, not smeared along the
            # whole trail - run it as a band and it reads as a painted
            # stripe rather than as the hottest point.
            core = math.hypot(x - HEAD_X, dy)
            if core < 3.0:
                c = WHITE
            elif core < 4.6:
                c = YELLOW
            elif r > 0.84:
                c = DEEP
            elif r > 0.58:
                c = RED
            elif r > 0.30:
                c = ORANGE
            else:
                c = YELLOW
            p[x, y] = c

    # Detached embers shedding off the flame. Offsets are large enough to
    # clear the trail - placed inside it they just repaint pixels the field
    # already covered and nothing reads as a separate spark. Positions wrap
    # over the loop so they stream backwards continuously.
    for i, (start, oy, colour) in enumerate((
            (19, -6, EMBER), (15, 6, ORANGE), (11, -8, ORANGE), (7, 7, EMBER))):
        ex = (start - frame * 3) % 26
        ey = CY + oy + (1 if (frame + i) % 3 == 0 else 0)
        if 0 <= ex < SIZE and 0 <= ey < SIZE:
            p[ex, ey] = colour

    return img


frames = [build(f) for f in range(FRAMES)]

for i, f in enumerate(frames):
    f.save(os.path.join(OUT, f"fireball_{i}.png"))

sheet = Image.new("RGBA", (SIZE * FRAMES, SIZE), (0, 0, 0, 0))
for i, f in enumerate(frames):
    sheet.paste(f, (i * SIZE, 0), f)
sheet.save(os.path.join(OUT, "fireball_sheet.png"))
sheet.resize((sheet.width * SCALE, SIZE * SCALE), Image.NEAREST).save(
    os.path.join(OUT, "fireball_sheet_preview.png"))

big = [f.resize((SIZE * 6, SIZE * 6), Image.NEAREST) for f in frames]
big[0].save(os.path.join(OUT, "fireball.gif"), save_all=True,
            append_images=big[1:], duration=80, loop=0, disposal=2)
print("done")

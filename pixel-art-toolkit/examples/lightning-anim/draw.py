"""Chain lightning - 64x32, 8-frame loop.

The animation tells the spell rather than just flickering: the arc builds
one hop at a time across four targets, holds at full chain while the bolt
re-randomises, then dissipates. A bolt that merely wobbles in place reads
as an electrical effect; one that reaches the next node reads as *chain*
lightning.

Bolt geometry is midpoint displacement along each hop, with the offset
tapered by sin(t*pi) so the path is pinned exactly at both nodes and only
wanders in between. Without that taper the arc detaches from its targets
and the chain stops reading as connected.

Every frame reseeds the displacement, which is what gives lightning its
characteristic instability - the same two points joined by a different
path each frame. The RNG is a fixed LCG rather than `random`, so the loop
renders byte-identically every run.
"""
import math
import os

from PIL import Image

W, H = 64, 32
FRAMES = 8
SCALE = 8
OUT = os.path.dirname(__file__)

CORE  = (255, 255, 255, 255)
HOT   = (216, 244, 255, 255)
ARC   = (90, 200, 255, 255)
GLOW  = (42, 106, 216, 255)
DIM   = (26, 42, 104, 255)

NODES = [(4, 21), (22, 8), (41, 24), (59, 11)]


def lcg(s):
    return (1103515245 * s + 12345) & 0x7FFFFFFF


def hop_points(a, b, seed, segments=11, amp=4.5):
    """Jagged path from a to b, pinned at both ends."""
    x0, y0 = a
    x1, y1 = b
    dx, dy = x1 - x0, y1 - y0
    L = math.hypot(dx, dy) or 1.0
    nx, ny = -dy / L, dx / L
    pts, s = [], seed
    for i in range(segments + 1):
        t = i / segments
        s = lcg(s)
        r = ((s >> 8) % 2000) / 1000.0 - 1.0
        taper = math.sin(t * math.pi)      # zero at both nodes
        off = r * amp * taper
        pts.append((x0 + dx * t + nx * off, y0 + dy * t + ny * off))
    return pts


class Frame:
    def __init__(self):
        self.img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        self.p = self.img.load()

    def put(self, x, y, c, over=True):
        x, y = int(round(x)), int(round(y))
        if not (0 <= x < W and 0 <= y < H):
            return
        if not over and self.p[x, y][3] != 0:
            return
        self.p[x, y] = c

    def stroke(self, pts, core, halo, outer):
        """Draw the polyline: 1px core, a 4-neighbour halo, a sparse outer
        glow. Painting the halo first and the core last keeps the core
        unbroken - drawn the other way round the halo eats into it and the
        bolt looks dotted."""
        dense = []
        for i in range(len(pts) - 1):
            (ax, ay), (bx, by) = pts[i], pts[i + 1]
            steps = int(max(abs(bx - ax), abs(by - ay))) + 1
            for s in range(steps + 1):
                t = s / max(steps, 1)
                dense.append((ax + (bx - ax) * t, ay + (by - ay) * t))
        # Outer glow only every third sample. Applied to every pixel it
        # doubles the apparent thickness and the bolt reads as a ribbon
        # rather than as lightning, which wants to look thin and sharp.
        if outer:
            for i, (x, y) in enumerate(dense):
                if i % 3:
                    continue
                for ox, oy in ((1, 1), (-1, -1), (1, -1), (-1, 1)):
                    self.put(x + ox, y + oy, outer, over=False)
        if halo:
            for x, y in dense:
                for ox, oy in ((1, 0), (0, 1)):
                    self.put(x + ox, y + oy, halo, over=False)
        if core:
            for x, y in dense:
                self.put(x, y, core)

    def fork(self, pts, seed, colour):
        """Short dead-end branch off the main path - real lightning forks."""
        if len(pts) < 6:
            return
        s = lcg(seed)
        i = 2 + (s >> 8) % (len(pts) - 4)
        ax, ay = pts[i]
        s = lcg(s)
        dx = 1.0 if (s >> 8) % 2 else -1.0
        s = lcg(s)
        dy = 1.0 if (s >> 8) % 2 else -1.0
        for step in range(1, 5):
            self.put(ax + dx * step, ay + dy * step * 0.8, colour)

    def burst(self, node, size):
        x, y = node
        for r in range(1, size + 1):
            c = CORE if r == 1 else (HOT if r == 2 else ARC)
            self.put(x + r, y, c); self.put(x - r, y, c)
            self.put(x, y + r, c); self.put(x, y - r, c)
        self.put(x, y, CORE)


def build(f):
    """Every frame carries the whole chain.

    A build-up-then-dissipate cycle was tried first and looked better as a
    one-shot, but as a loop its near-empty tail frame reads as a blink -
    the same failure the fireball had. A sustained chain that re-randomises
    each frame loops cleanly and is what a channelled spell should look
    like anyway.
    """
    fr = Frame()
    amp = (4.6, 3.8, 5.2, 4.2, 5.0, 3.6, 4.8, 4.0)[f]

    # Every frame gets identical colour treatment; only the geometry
    # changes. Dimming alternate frames was tried and the darker ones read
    # as a strobe - at this palette contrast a value pulse is far more
    # visible than the path re-randomising, and it looks like a fault
    # rather than like lightning.
    for h in range(3):
        seed = 7919 * (f + 1) + 104729 * h + 13
        pts = hop_points(NODES[h], NODES[h + 1], seed, amp=amp)
        fr.stroke(pts, CORE, ARC, GLOW)
        if f % 2 == 0:
            fr.fork(pts, seed + 31, ARC)

    for node in NODES:
        fr.burst(node, 3)
    return fr.img


frames = [build(f) for f in range(FRAMES)]
for i, im in enumerate(frames):
    im.save(os.path.join(OUT, f"lightning_{i}.png"))

sheet = Image.new("RGBA", (W * FRAMES, H), (0, 0, 0, 0))
for i, im in enumerate(frames):
    sheet.paste(im, (i * W, 0), im)
sheet.save(os.path.join(OUT, "lightning_sheet.png"))
sheet.resize((sheet.width * 4, H * 4), Image.NEAREST).save(
    os.path.join(OUT, "lightning_sheet_preview.png"))

big = [im.resize((W * SCALE, H * SCALE), Image.NEAREST) for im in frames]
big[0].save(os.path.join(OUT, "lightning.gif"), save_all=True,
            append_images=big[1:], duration=70, loop=0, disposal=2)
print("done")

"""Impact effects for the three schools that had no sprite sheet yet.

Fire, air and water already had one from the effect work we did earlier
(fireball, chain lightning, sleep aura). Earth, dark and light were falling
back to a plain expanding ring drawn in canvas, which looked nothing like
the rest of the game.

Each is an eight-frame 32x32 impact, authored to the same rules as the other
sheets: no frame goes near-empty (a blank frame in a loop reads as a blink),
geometry varies rather than brightness, and every random is drawn from a
fixed seed so a regeneration is identical.
"""
import os
from PIL import Image

S, N = 32, 8
OUT = os.path.dirname(os.path.abspath(__file__))
C = S // 2


def lcg(seed):
    s = seed
    while True:
        s = (1103515245 * s + 12345) & 0x7FFFFFFF
        yield s / 0x7FFFFFFF


class F:
    def __init__(self):
        self.img = Image.new("RGBA", (S, S), (0, 0, 0, 0))
        self.p = self.img.load()

    def put(self, x, y, c):
        x, y = int(x), int(y)
        if 0 <= x < S and 0 <= y < S:
            self.p[x, y] = c

    def disc(self, cx, cy, r, c):
        for y in range(int(cy - r), int(cy + r) + 1):
            for x in range(int(cx - r), int(cx + r) + 1):
                if (x - cx) ** 2 + (y - cy) ** 2 <= r * r:
                    self.put(x, y, c)

    def ring(self, cx, cy, r, c, thick=1):
        steps = max(12, int(r * 8))
        import math
        for i in range(steps):
            a = i / steps * math.tau
            for t in range(thick):
                self.put(cx + math.cos(a) * (r + t), cy + math.sin(a) * (r + t), c)


def earth(i):
    """Slabs heaved up and settling. The shape changes, the colour does not --
    dimming alternate frames is what makes an effect strobe."""
    import math
    f = F()
    k = i / (N - 1)
    rnd = lcg(41)
    dust = (74, 58, 42, 255)
    rock = (150, 118, 78, 255)
    rock_d = (96, 74, 46, 255)
    # Dust is a flat bed hugging the floor, not a ball. Drawn first and kept
    # low, so the shards that follow stand clear of it -- a round cloud at
    # this size simply swallows them and the effect becomes a brown blob.
    spread = 6 + 9 * math.sin(k * math.pi)
    for y in range(-3, 4):
        half = spread * math.sqrt(max(0.0, 1 - (y / 3.6) ** 2))
        for x in range(int(-half), int(half) + 1):
            f.put(C + x, C + 6 + y, dust)

    # shards after the dust, and rising out of the top of it
    for j in range(7):
        a = next(rnd) * math.tau
        rise = 4 + 10 * math.sin(min(1.0, k * 1.2) * math.pi)
        d = 3 + next(rnd) * 8
        x = C + math.cos(a) * d
        y = C + 5 - rise - next(rnd) * 3
        h = 3 + next(rnd) * 4
        for t in range(int(h)):
            f.put(x, y + t, rock if t < 2 else rock_d)
        f.put(x + 1, y + 1, rock_d)
    return f.img


def dark(i):
    """A bloom that collapses inward instead of expanding: the school that
    takes things away should not look like an explosion."""
    import math
    f = F()
    k = i / (N - 1)
    rnd = lcg(97)
    r = 13 - 9 * k
    void = (16, 10, 26, 255)
    edge = (107, 75, 138, 255)
    spark = (168, 132, 200, 255)
    f.disc(C, C, max(2.0, r * 0.72), void)
    f.ring(C, C, max(2.5, r), edge, 2)
    # tendrils drawn inward, so the eye reads a pull rather than a push
    for j in range(9):
        a = next(rnd) * math.tau
        for t in range(4):
            rr = r + 3 - t
            f.put(C + math.cos(a) * rr, C + math.sin(a) * rr, spark if t == 0 else edge)
    return f.img


def light(i):
    """A flash with rays. Light is this game's school of lying, so it wants to
    look like revelation while being nothing of the sort."""
    import math
    f = F()
    k = i / (N - 1)
    core = (255, 244, 208, 255)
    warm = (255, 217, 128, 255)
    pale = (255, 233, 168, 255)
    r = 3 + 8 * math.sin(k * math.pi)
    f.disc(C, C, max(1.5, r * 0.45), core)
    f.ring(C, C, max(2.0, r), warm, 1)
    rays = 8
    for j in range(rays):
        a = j / rays * math.tau + k * 0.5
        for t in range(int(4 + 9 * math.sin(k * math.pi))):
            rr = r + 1 + t
            f.put(C + math.cos(a) * rr, C + math.sin(a) * rr, pale if t % 2 else warm)
    return f.img


for name, fn in (("earth", earth), ("dark", dark), ("light", light)):
    sheet = Image.new("RGBA", (S * N, S), (0, 0, 0, 0))
    for i in range(N):
        fr = fn(i)
        sheet.paste(fr, (i * S, 0), fr)
    sheet.save(os.path.join(OUT, f"fx_{name}.png"))
    sheet.resize((sheet.width * 4, S * 4), Image.NEAREST).save(
        os.path.join(OUT, f"fx_{name}_preview.png"))
    print("wrote", f"fx_{name}.png", sheet.size)

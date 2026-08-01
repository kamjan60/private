"""Helpers for procedural pixel-art spell effects.

The constructions here (field, displaced path, parametric outline,
staggered emitters) cover most combat VFX. See ../SKILL.md for which to
reach for and the failure modes each one has.
"""
import math

from PIL import Image


# ------------------------------------------------------------------ random
def lcg(state):
    """Deterministic LCG step. Used instead of `random` so an effect renders
    byte-identically every run - important when frames of one loop must keep
    their particle positions stable."""
    return (1103515245 * state + 12345) & 0x7FFFFFFF


def rand_unit(state):
    """-> (new_state, value in [-1, 1])."""
    s = lcg(state)
    return s, ((s >> 8) % 2000) / 1000.0 - 1.0


# ------------------------------------------------------------------ canvas
class Canvas:
    def __init__(self, w, h):
        self.w, self.h = w, h
        self.img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        self.p = self.img.load()

    def put(self, x, y, c, only_empty=False):
        x, y = int(round(x)), int(round(y))
        if not (0 <= x < self.w and 0 <= y < self.h):
            return
        if only_empty and self.p[x, y][3] != 0:
            return
        self.p[x, y] = c

    def span(self, y, x0, x1, c):
        for x in range(int(x0), int(x1) + 1):
            self.put(x, y, c)


# ------------------------------------------------------------------- field
def flame_field(x, phase, head_x, head_r, tail_x,
                slow_amp=0.26, slow_freq=0.55, fast_amp=0.13, fast_freq=1.27):
    """Half-height of a flame at column x.

    Round leading head, tapering trail, and irregularity from *two* sines at
    unrelated frequencies - a single wave (or clipping alternate columns)
    gives a regular sawtooth that reads as a fish skeleton rather than fire.
    The slow wave's amplitude ramps toward the tail so the head stays
    anchored and only the trail whips.
    """
    if x > head_x + head_r:
        return 0.0
    if x >= head_x:
        d = (x - head_x) / head_r
        return head_r * math.sqrt(max(0.0, 1.0 - d * d))
    if x < tail_x:
        return 0.0
    t = (x - tail_x) / float(head_x - tail_x)
    base = head_r * (t ** 0.75)
    slow = slow_amp * (1.0 - t) * math.sin(x * slow_freq + phase)
    fast = fast_amp * math.sin(x * fast_freq - phase * 1.7)
    return base * (1.0 + slow + fast)


def flame_colour(x, dy, h, head_x, ramp, core_r=3.0, halo_r=4.6,
                 bands=(0.84, 0.58, 0.30)):
    """Pick a colour for one flame pixel.

    `ramp` runs hot to cool: (core, halo, mid, warm, edge). Bands are keyed
    to |dy|/h so they stay in register while the silhouette wobbles, but the
    core is keyed to *distance from the head* - written as a row band it
    smears into a painted stripe down the whole trail instead of reading as
    the hottest point.
    """
    core, halo, mid, warm, edge = ramp
    d = math.hypot(x - head_x, dy)
    if d < core_r:
        return core
    if d < halo_r:
        return halo
    r = abs(dy) / max(h, 1e-6)
    if r > bands[0]:
        return edge
    if r > bands[1]:
        return warm
    if r > bands[2]:
        return mid
    return halo


# ----------------------------------------------------------- displaced path
def displaced_path(a, b, seed, segments=11, amp=4.5):
    """Jagged path between two points, pinned at both ends.

    The sin(t*pi) taper is what keeps it pinned. Without it the path drifts
    off its endpoints and a chain of these stops reading as connected.
    """
    (x0, y0), (x1, y1) = a, b
    dx, dy = x1 - x0, y1 - y0
    L = math.hypot(dx, dy) or 1.0
    nx, ny = -dy / L, dx / L
    pts, s = [], seed
    for i in range(segments + 1):
        t = i / segments
        s, r = rand_unit(s)
        off = r * amp * math.sin(t * math.pi)
        pts.append((x0 + dx * t + nx * off, y0 + dy * t + ny * off))
    return pts


def densify(pts):
    """Polyline -> per-pixel samples, for stroking."""
    out = []
    for i in range(len(pts) - 1):
        (ax, ay), (bx, by) = pts[i], pts[i + 1]
        steps = int(max(abs(bx - ax), abs(by - ay))) + 1
        for s in range(steps + 1):
            t = s / max(steps, 1)
            out.append((ax + (bx - ax) * t, ay + (by - ay) * t))
    return out


def stroke_path(canvas, pts, core, halo=None, outer=None, outer_every=3):
    """Stroke a path: sparse outer glow, 2-neighbour halo, 1px core.

    Core goes down last so the halo cannot eat into it and leave the bolt
    looking dotted. `outer_every` controls apparent thickness - applied to
    every sample the glow doubles the visual weight and the bolt reads as a
    ribbon instead of lightning.
    """
    dense = densify(pts)
    if outer:
        for i, (x, y) in enumerate(dense):
            if i % outer_every:
                continue
            for ox, oy in ((1, 1), (-1, -1), (1, -1), (-1, 1)):
                canvas.put(x + ox, y + oy, outer, only_empty=True)
    if halo:
        for x, y in dense:
            for ox, oy in ((1, 0), (0, 1)):
                canvas.put(x + ox, y + oy, halo, only_empty=True)
    for x, y in dense:
        canvas.put(x, y, core)


# ------------------------------------------------------- parametric outline
def ellipse_points(cx, cy, rx, ry, dashed=False, dash_period=5):
    """Outline samples. Sample count scales with the radius, otherwise a
    small ellipse's points bunch up and flood it solid.

    Note that scaling alone is not enough below about 3px of vertical
    radius: the outline has no interior left and fills regardless. Use
    `dashed` there - it also reads as a rune rather than a smudge.
    """
    steps = max(12, int(rx * 8))
    out = []
    for i in range(steps):
        if dashed and (i * dash_period // steps) % 2:
            continue
        a = i / steps * 2 * math.pi
        out.append((cx + math.cos(a) * rx, cy + math.sin(a) * ry))
    return out


def staggered_phase(frame, frames, index, count):
    """Phase for emitter `index` of `count`, spaced evenly round the loop.

    Staggering is what stops a rising-glyph effect having frames where
    nothing is mid-flight.
    """
    return ((frame / float(frames)) + index / float(count)) % 1.0


# ------------------------------------------------------------------ output
def save_effect(frames, out_dir, name, frame_ms=80, scale=8, sheet_scale=4):
    """Write per-frame PNGs, a horizontal sheet, a scaled sheet preview and
    a GIF. Returns the sheet image."""
    import os
    w, h = frames[0].size
    for i, im in enumerate(frames):
        im.save(os.path.join(out_dir, f"{name}_{i}.png"))

    sheet = Image.new("RGBA", (w * len(frames), h), (0, 0, 0, 0))
    for i, im in enumerate(frames):
        sheet.paste(im, (i * w, 0), im)
    sheet.save(os.path.join(out_dir, f"{name}_sheet.png"))
    sheet.resize((sheet.width * sheet_scale, h * sheet_scale),
                 Image.NEAREST).save(os.path.join(out_dir, f"{name}_sheet_preview.png"))

    big = [im.resize((w * scale, h * scale), Image.NEAREST) for im in frames]
    big[0].save(os.path.join(out_dir, f"{name}.gif"), save_all=True,
                append_images=big[1:], duration=frame_ms, loop=0, disposal=2)
    return sheet

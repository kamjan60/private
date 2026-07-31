#!/usr/bin/env python3
"""Shape-based pixel-art renderer for fantasy / dark-fantasy sprites.

Takes a declarative JSON spec of *shapes* (polygons, tapered spines, arcs,
rounded bands, dithered gradients) and renders true 1:1 pixel art, plus
optional sprite sheet, scaled preview, and animated GIF.

Why shapes instead of a per-pixel list: a 64x64 sprite is up to 4096
pixels. Authoring that as explicit {x,y,color} entries is slow, token-heavy
and off-by-one prone, and every curve ends up hand-plotted into stair-steps.
A wizard here is ~20 shapes.

Pipeline per frame:
    draw shapes at supersample x  ->  BOX downsample (area coverage)
    ->  hard alpha cut  ->  snap every pixel to the declared palette
    ->  optional 1px auto-outline

The snap is what keeps the output *pixel art* rather than a shrunk
vector drawing: no antialiased half-tones survive it.

Usage:
    python3 render_sprite.py spec.json -o out/
    python3 render_sprite.py spec.json -o out/ --preview-scale 8 --gif
"""

import argparse
import json
import math
import os
import sys

try:
    from PIL import Image, ImageDraw
except ImportError:
    print("Error: Pillow is not installed. Run: pip install Pillow", file=sys.stderr)
    sys.exit(1)


# --------------------------------------------------------------- color utils

def parse_hex(value):
    """'#rrggbb' / '#rrggbbaa' / [r,g,b(,a)] -> (r, g, b, a)."""
    if isinstance(value, (list, tuple)):
        c = tuple(value)
        return c + (255,) if len(c) == 3 else c
    s = str(value).strip().lstrip("#")
    if len(s) == 6:
        return tuple(int(s[i:i + 2], 16) for i in (0, 2, 4)) + (255,)
    if len(s) == 8:
        return tuple(int(s[i:i + 2], 16) for i in (0, 2, 4, 6))
    raise ValueError(f"Unrecognized color: {value!r}")


class Palette:
    """Named colors plus nearest-match snapping.

    Snapping is deliberately strict: the rendered sprite can only ever
    contain declared colors, so a spec that claims a 12-color palette
    really is 12 colors. The reference skill only *suggested* a color
    budget; this enforces it.
    """

    def __init__(self, mapping):
        self.by_name = {k: parse_hex(v) for k, v in mapping.items()}
        self.colors = list(dict.fromkeys(self.by_name.values()))

    def get(self, name):
        if name is None:
            return None
        if isinstance(name, (list, tuple)) or str(name).startswith("#"):
            return parse_hex(name)
        if name not in self.by_name:
            raise KeyError(f"Color '{name}' is not in the palette. "
                           f"Known: {', '.join(sorted(self.by_name))}")
        return self.by_name[name]

    def nearest(self, rgb):
        r, g, b = rgb
        best, best_d = self.colors[0], None
        for c in self.colors:
            d = (r - c[0]) ** 2 + (g - c[1]) ** 2 + (b - c[2]) ** 2
            if best_d is None or d < best_d:
                best, best_d = c, d
        return best


# ------------------------------------------------------------ shape geometry

def taper_polygon(spine):
    """[(x, y, half_width), ...] -> closed polygon following the spine.

    For anything that tapers along a curved path: witch-hat crowns that
    curl at the tip, tails, banners, tentacles, smoke wisps.
    """
    left, right = [], []
    n = len(spine)
    for i, (x, y, hw) in enumerate(spine):
        if i == 0:
            dx, dy = spine[1][0] - x, spine[1][1] - y
        elif i == n - 1:
            dx, dy = x - spine[-2][0], y - spine[-2][1]
        else:
            dx = spine[i + 1][0] - spine[i - 1][0]
            dy = spine[i + 1][1] - spine[i - 1][1]
        ln = math.hypot(dx, dy) or 1.0
        nx, ny = -dy / ln * hw, dx / ln * hw
        left.append((x + nx, y + ny))
        right.append((x - nx, y - ny))
    return left + right[::-1]


def band_polygon(x_top, x_bot, y_top, y_flat, bulge, samples=40):
    """Tapering band closed by one broad elliptical bottom - beards, cloaks,
    hanging cloth.

    Sine-scalloped hems were tried first and snap to sharp zig-zag teeth on
    a 64px grid (the cusps land sub-pixel). One wide arc survives downsampling
    as an actual curve.
    """
    x_top_l, x_top_r = x_top
    x_bot_l, x_bot_r = x_bot
    cx = (x_bot_l + x_bot_r) / 2.0
    rx = max((x_bot_r - x_bot_l) / 2.0, 1e-6)
    bottom = []
    for i in range(samples + 1):
        t = i / samples
        x = x_bot_l + (x_bot_r - x_bot_l) * t
        u = max(-1.0, min(1.0, (x - cx) / rx))
        bottom.append((x, y_flat + bulge * math.sqrt(max(0.0, 1.0 - u * u))))
    return [(x_top_l, y_top), (x_bot_l, y_flat)] + bottom + [(x_top_r, y_top)]


def bulged_polygon(x_top, x_bot, y_top, y_bot, bulge, samples=24):
    """Trapezoid with convex sides - robes, tunics, tree trunks, towers."""
    x_top_l, x_top_r = x_top
    x_bot_l, x_bot_r = x_bot
    left, right = [], []
    for i in range(samples + 1):
        t = i / samples
        b = math.sin(t * math.pi) * bulge
        y = y_top + (y_bot - y_top) * t
        left.append((x_top_l + (x_bot_l - x_top_l) * t - b, y))
        right.append((x_top_r + (x_bot_r - x_top_r) * t + b, y))
    return left + right[::-1]


BAYER4 = [
    [0, 8, 2, 10],
    [12, 4, 14, 6],
    [3, 11, 1, 9],
    [15, 7, 13, 5],
]


# ----------------------------------------------------------------- rendering

class Renderer:
    def __init__(self, spec):
        self.w, self.h = spec["size"]
        self.ss = int(spec.get("supersample", 8))
        self.palette = Palette(spec["palette"])
        self.outline_color = self.palette.get(spec.get("outline")) if spec.get("outline") else None
        self.auto_outline = bool(spec.get("auto_outline", True))
        self.default_stroke = float(spec.get("stroke_width", 1.15))
        self.alpha_cut = int(spec.get("alpha_cut", 110))

    def s(self, v):
        return v * self.ss

    def pts(self, seq, dx=0.0, dy=0.0):
        return [(self.s(x + dx), self.s(y + dy)) for x, y in seq]

    # -- individual shape handlers ------------------------------------------
    def draw_shape(self, d, shape, dx, dy):
        kind = shape.get("type", "polygon")
        fill = self.palette.get(shape.get("fill"))
        stroke = shape.get("stroke")
        stroke_color = self.palette.get(stroke) if stroke else None
        if stroke is None and self.outline_color is not None and shape.get("outline", True):
            stroke_color = self.outline_color
        sw = float(shape.get("stroke_width", self.default_stroke))

        if kind in ("polygon", "rect", "taper", "band", "bulged"):
            poly = self.resolve_polygon(kind, shape)
            dev = self.pts(poly, dx, dy)
            if fill is not None:
                d.polygon(dev, fill=fill)
            if stroke_color is not None and sw > 0:
                d.line(dev + [dev[0]], fill=stroke_color,
                       width=max(1, int(self.s(sw))), joint="curve")

        elif kind == "ellipse":
            cx, cy = shape["center"]
            rx, ry = shape["radius"] if isinstance(shape["radius"], (list, tuple)) \
                else (shape["radius"], shape["radius"])
            box = [self.s(cx + dx - rx), self.s(cy + dy - ry),
                   self.s(cx + dx + rx), self.s(cy + dy + ry)]
            d.ellipse(box, fill=fill,
                      outline=stroke_color if sw > 0 else None,
                      width=max(1, int(self.s(sw))) if stroke_color and sw > 0 else 1)

        elif kind == "line":
            a, b = shape["from"], shape["to"]
            d.line([(self.s(a[0] + dx), self.s(a[1] + dy)),
                    (self.s(b[0] + dx), self.s(b[1] + dy))],
                   fill=fill, width=max(1, int(self.s(shape.get("width", 1)))))

        elif kind == "arc":
            cx, cy = shape["center"]
            r = shape["radius"]
            box = [self.s(cx + dx - r), self.s(cy + dy - r),
                   self.s(cx + dx + r), self.s(cy + dy + r)]
            d.arc(box, start=shape["start"], end=shape["end"], fill=fill,
                  width=max(1, int(self.s(shape.get("width", 1)))))

        elif kind == "gradient":
            self.draw_gradient(d, shape, dx, dy)

        elif kind == "scatter":
            self.draw_scatter(d, shape, dx, dy)

        else:
            raise ValueError(f"Unknown shape type: {kind!r}")

    def resolve_polygon(self, kind, shape):
        if kind == "polygon":
            return [tuple(p) for p in shape["points"]]
        if kind == "rect":
            x0, y0, x1, y1 = shape["box"]
            return [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]
        if kind == "taper":
            return taper_polygon([tuple(p) for p in shape["spine"]])
        if kind == "band":
            return band_polygon(shape["x_top"], shape["x_bottom"], shape["y_top"],
                                shape["y_flat"], shape.get("bulge", 2.0))
        if kind == "bulged":
            return bulged_polygon(shape["x_top"], shape["x_bottom"], shape["y_top"],
                                  shape["y_bottom"], shape.get("bulge", 1.5))
        raise ValueError(kind)

    def draw_gradient(self, d, shape, dx, dy):
        """Bayer-dithered vertical blend between two palette colors.

        Blocks are aligned to the *final* pixel grid (not the supersampled
        one), so each output pixel ends up a single flat palette color and
        the dither survives downsampling intact. Skies, fog banks, cave
        depth, torch falloff.
        """
        x0, y0, x1, y1 = shape["box"]
        top = self.palette.get(shape["from"])
        bot = self.palette.get(shape["to"])
        for py in range(int(y0), int(y1) + 1):
            t = (py - y0) / max(1e-6, (y1 - y0))
            for px_ in range(int(x0), int(x1) + 1):
                thr = BAYER4[py % 4][px_ % 4] / 16.0
                color = bot if t > thr else top
                gx, gy = self.s(px_ + dx), self.s(py + dy)
                d.rectangle([gx, gy, gx + self.ss - 1, gy + self.ss - 1], fill=color)

    def draw_scatter(self, d, shape, dx, dy):
        """Seeded pseudo-random specks in a box - stars, embers, rubble, moss.

        Uses its own LCG rather than `random` so a spec always renders
        byte-identically, which matters when frames of one animation must
        keep their scatter stable.
        """
        x0, y0, x1, y1 = shape["box"]
        color = self.palette.get(shape.get("fill"))
        count = int(shape.get("count", 20))
        size = float(shape.get("size", 1))
        seed = int(shape.get("seed", 1)) & 0xFFFFFFFF
        for _ in range(count):
            seed = (1103515245 * seed + 12345) & 0x7FFFFFFF
            fx = x0 + (x1 - x0) * ((seed >> 8) % 10000) / 10000.0
            seed = (1103515245 * seed + 12345) & 0x7FFFFFFF
            fy = y0 + (y1 - y0) * ((seed >> 8) % 10000) / 10000.0
            gx, gy = self.s(math.floor(fx) + dx), self.s(math.floor(fy) + dy)
            d.rectangle([gx, gy, gx + self.ss * size - 1, gy + self.ss * size - 1], fill=color)

    # -- frame pipeline ------------------------------------------------------
    def render_frame(self, frame):
        img = Image.new("RGBA", (self.w * self.ss, self.h * self.ss), (0, 0, 0, 0))
        d = ImageDraw.Draw(img)
        dx, dy = frame.get("offset", [0, 0])
        for shape in frame["shapes"]:
            self.draw_shape(d, shape, dx + shape.get("dx", 0), dy + shape.get("dy", 0))
        small = img.resize((self.w, self.h), Image.BOX)
        snapped = self.snap(small)
        return self.outline_pass(snapped) if (self.auto_outline and self.outline_color) else snapped

    def snap(self, img):
        out = img.copy()
        p = out.load()
        for y in range(out.height):
            for x in range(out.width):
                r, g, b, a = p[x, y]
                p[x, y] = (0, 0, 0, 0) if a < self.alpha_cut else self.palette.nearest((r, g, b))
        return out

    def outline_pass(self, img):
        """Fill transparent pixels that touch an opaque one, guaranteeing a
        closed silhouette even where a stroke thinned out in the downsample."""
        out = img.copy()
        src = img.load()
        dst = out.load()
        for y in range(img.height):
            for x in range(img.width):
                if src[x, y][3] != 0:
                    continue
                for ax, ay in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nx, ny = x + ax, y + ay
                    if 0 <= nx < img.width and 0 <= ny < img.height and src[nx, ny][3] != 0:
                        dst[x, y] = self.outline_color
                        break
        return out


def compose_sheet(frames, cols, cell_w, cell_h):
    rows = math.ceil(len(frames) / cols)
    sheet = Image.new("RGBA", (cell_w * cols, cell_h * rows), (0, 0, 0, 0))
    for i, f in enumerate(frames):
        sheet.paste(f, ((i % cols) * cell_w, (i // cols) * cell_h), f)
    return sheet


def main():
    ap = argparse.ArgumentParser(description="Render a shape-based pixel-art spec to PNG.")
    ap.add_argument("spec", help="Path to the JSON spec, or '-' for stdin")
    ap.add_argument("-o", "--output-dir", default=".", help="Directory for rendered files")
    ap.add_argument("--preview-scale", type=int, default=8,
                    help="Nearest-neighbour upscale for the *_preview.png files (0 to skip)")
    ap.add_argument("--gif", action="store_true", help="Also write an animated GIF of the frames")
    ap.add_argument("--sheet-columns", type=int, default=None,
                    help="Override the sprite-sheet column count")
    args = ap.parse_args()

    raw = sys.stdin.read() if args.spec == "-" else open(args.spec).read()
    spec = json.loads(raw)

    r = Renderer(spec)
    os.makedirs(args.output_dir, exist_ok=True)

    frames = spec.get("frames") or [{"name": spec.get("name", "sprite"),
                                     "shapes": spec["shapes"]}]
    rendered, names = [], []
    for i, frame in enumerate(frames):
        name = frame.get("name", f"frame_{i}")
        img = r.render_frame(frame)
        rendered.append(img)
        names.append(name)
        path = os.path.join(args.output_dir, f"{name}.png")
        img.save(path)
        print(f"  {path}  ({r.w}x{r.h})")

    if args.preview_scale:
        for name, img in zip(names, rendered):
            p = os.path.join(args.output_dir, f"{name}_preview.png")
            img.resize((r.w * args.preview_scale, r.h * args.preview_scale),
                       Image.NEAREST).save(p)

    if len(rendered) > 1:
        cols = args.sheet_columns or spec.get("sheet", {}).get("columns", len(rendered))
        sheet = compose_sheet(rendered, cols, r.w, r.h)
        sp = os.path.join(args.output_dir, "sheet.png")
        sheet.save(sp)
        print(f"  {sp}  ({sheet.width}x{sheet.height}, {cols} cols)")
        if args.preview_scale:
            sheet.resize((sheet.width * args.preview_scale, sheet.height * args.preview_scale),
                         Image.NEAREST).save(os.path.join(args.output_dir, "sheet_preview.png"))

    if args.gif and len(rendered) > 1:
        ms = spec.get("gif", {}).get("frame_ms", 120)
        scale = max(1, args.preview_scale or 1)
        big = [f.resize((r.w * scale, r.h * scale), Image.NEAREST) for f in rendered]
        gp = os.path.join(args.output_dir, "anim.gif")
        big[0].save(gp, save_all=True, append_images=big[1:], duration=ms,
                    loop=0, disposal=2, transparency=0)
        print(f"  {gp}  ({ms}ms/frame)")

    print(f"palette: {len(r.palette.colors)} colors")


if __name__ == "__main__":
    main()

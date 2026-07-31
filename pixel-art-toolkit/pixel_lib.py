"""Small procedural pixel-art helper library (PIL-based, no Aseprite needed).

Draw sprites pixel-by-pixel or row-by-row, add a 1px auto-outline, dither
between two colors on a row, and compose a set of per-direction frame lists
into a grid sprite sheet.

Technique notes (color ramps, dithering, animation timing) live in
reference/ - derived from willibrandon/pixel-plugin's skill docs (MIT).
"""
from PIL import Image


def blank(w, h):
    return Image.new("RGBA", (w, h), (0, 0, 0, 0))


def px(img, x, y, color):
    w, h = img.size
    if 0 <= x < w and 0 <= y < h:
        img.putpixel((x, y), color)


def row(img, y, x0, x1, color):
    for x in range(x0, x1 + 1):
        px(img, x, y, color)


def col(img, x, y0, y1, color):
    for y in range(y0, y1 + 1):
        px(img, x, y, color)


def dither_row(img, y, x0, x1, color_a, color_b):
    """2x2 checkerboard dither (50% mix) — see reference/dithering-patterns.md
    for the fuller pattern library (25%/75% mixes, Bayer 4x4, directional)."""
    for x in range(x0, x1 + 1):
        c = color_a if (x + y) % 2 == 0 else color_b
        px(img, x, y, c)


def outline_pass(img, outline_color):
    """Fill every transparent pixel that borders an opaque one with
    outline_color — a cheap 1px auto-outline for silhouette readability."""
    src = img.copy()
    w, h = img.size
    for y in range(h):
        for x in range(w):
            if src.getpixel((x, y))[3] != 0:
                continue
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                nx, ny = x + dx, y + dy
                if 0 <= nx < w and 0 <= ny < h and src.getpixel((nx, ny))[3] != 0:
                    img.putpixel((x, y), outline_color)
                    break
    return img


def mirror(img):
    return img.transpose(Image.FLIP_LEFT_RIGHT)


def compose_sheet(frames_by_row, cell_w, cell_h):
    """frames_by_row: ordered list of frame-lists (one list per row, e.g. per
    direction). All inner lists must be the same length (frame count)."""
    cols = len(frames_by_row[0])
    rows = len(frames_by_row)
    sheet = Image.new("RGBA", (cell_w * cols, cell_h * rows), (0, 0, 0, 0))
    for row_i, frames in enumerate(frames_by_row):
        for col_i, frame in enumerate(frames):
            sheet.paste(frame, (col_i * cell_w, row_i * cell_h), frame)
    return sheet

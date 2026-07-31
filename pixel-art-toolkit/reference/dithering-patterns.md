# Dithering Patterns Reference

Condensed from `willibrandon/pixel-plugin`'s `pixel-art-professional` skill
(`dithering-patterns.md`, MIT licensed — see ATTRIBUTION.md). Use with
`pixel_lib.dither_row()` (2x2 checkerboard) or by hand for the other ratios.

Dithering fakes an in-between color by alternating two real colors in a
pattern — useful for cloth/metal/stone texture, gradients under a limited
palette, or an authentic retro look (real hardware palettes were tiny).

## Ordered (Bayer) vs error diffusion

- **Ordered / Bayer matrix** — fixed repeating pattern (2x2, 4x4, 8x8).
  Predictable, regular, cheap. Best for textures, backgrounds, retro feel.
- **Error diffusion (Floyd-Steinberg)** — spreads quantization error to
  neighboring pixels. More organic/irregular. Best for smooth gradients,
  natural imagery. Not implemented in `pixel_lib.py` (needs a full-image
  quantization pass, not a per-row helper) — do this in a real image editor
  or with `PIL.Image.quantize(dither=Image.FLOYDSTEINBERG)` if ever needed.

## 2-color patterns (50% mix) — what `dither_row()` does

```
A B A B
B A B A
```
Even 50/50, very regular. `dither_row(img, y, x0, x1, color_a, color_b)`
alternates by `(x + y) % 2` so adjacent rows offset correctly into a
checkerboard, not vertical stripes.

## 25% mix (mostly A, flecks of B)

```
A A B A
A A A A
B A A A
A A A A
```

## 75% mix (mostly B, flecks of A)

```
B B A B
B B B B
A B B B
B B B B
```

## Bayer 2x2 threshold matrix

```
0 2
3 1
```
Compare a pixel's value against the matrix cell at `(x%2, y%2)`; above
threshold -> lighter color, at/below -> darker. Same shape as the checkerboard
above once you fold "threshold compare" back down to two fixed colors.

## Bayer 4x4 (subtler, less obviously patterned)

```
 0  8  2 10
12  4 14  6
 3 11  1  9
15  7 13  5
```

## Directional patterns (weave / sketch texture)

**Diagonal weave:**
```
A B . . A B . .
B A . . B A . .
. . A B . . A B
. . B A . . B A
```

**Crosshatch:**
```
A B A . A B A .
B . B A B . B A
A B A . A B A .
. A . B . A . B
```

## When to reach for which

- Cloth/fabric fold shadow: 50% checkerboard on the deepest fold only (see
  the wizard example's robe hem) — keeps the rest of the shading flat/cell
  so the dither reads as an intentional texture accent, not noise everywhere.
- Smooth gradient under a tiny palette: 25%/75% mixes as intermediate steps
  between two flat bands.
- Rough/ancient surface (stone, weathered metal): crosshatch or diagonal weave
  instead of checkerboard — less regular, reads as texture rather than a
  screen-door effect.

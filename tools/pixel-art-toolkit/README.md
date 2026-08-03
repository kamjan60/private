# Pixel Art Toolkit

> **Deprecated.** The library, reference docs, and generic examples moved to
> [`kamjan60/claude-toolkit`](https://github.com/kamjan60/claude-toolkit).
> `examples/wizard-hunt/` (the game-specific sprite pipeline) moved to
> [`kamjan60/i-am-not-a-wizard-harry`](https://github.com/kamjan60/i-am-not-a-wizard-harry)
> instead. This copy is unmaintained.

Procedural pixel-art generation with plain Python/PIL — no Aseprite
required. Grew out of a one-off (a 4-direction wizard sprite) plus the
tool-agnostic technique knowledge pulled out of `willibrandon/pixel-plugin`'s
skill docs (that plugin needs a real Aseprite install; the *techniques* in
its docs don't).

## Contents

- `pixel_lib.py` — small helper module: `blank`, `px`, `row`, `col`,
  `dither_row` (2x2 checkerboard), `outline_pass` (auto 1px outline),
  `mirror`, `compose_sheet` (grid a set of per-direction frame lists into one
  sprite sheet).
- `reference/color-and-shading.md` — shading types, the hue-shift shadow/
  highlight rule, antialiasing rules, retro palette table + swatches.
- `reference/dithering-patterns.md` — the pattern library (checkerboard,
  25%/75% mixes, Bayer 4x4, directional weave/crosshatch) and when to use each.
- `reference/animation-and-sprites.md` — frame-rate/timing table, classic
  walk/run/idle cycle structures, animation principles, common sprite sizes.
- `ATTRIBUTION.md` — source + MIT license text for the above.
- `examples/wizard/` — the sprite that exercised all of this: a 32x32,
  4-direction (down/left/right/up), 3-frame-walk-cycle old-RPG/dark-fantasy
  wizard. `draw.py` is a worked example of using `pixel_lib.py` plus every
  technique in `reference/`.

## Using it for a new sprite

1. `from pixel_lib import blank, px, row, dither_row, outline_pass, mirror, compose_sheet`
2. Draw each frame with `row()`/`px()` calls, following
   `reference/color-and-shading.md` for the palette (base + hue-shifted
   shadow/highlight, one saturated accent if going for a moody/desaturated
   look).
3. Reach for `dither_row()` on one deep fold/shadow area for texture, not
   everywhere — see `reference/dithering-patterns.md`.
4. Call `outline_pass(frame, OUTLINE)` per frame.
5. `compose_sheet([frames_down, frames_left, frames_right, frames_up], cell_w, cell_h)`
   to get the final sheet.
6. Pick per-frame timing from `reference/animation-and-sprites.md` (a 3-frame
   walk at classic pixel-art speed is ~100-120ms/frame).

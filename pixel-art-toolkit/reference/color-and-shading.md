# Color & Shading Reference

Condensed from `willibrandon/pixel-plugin`'s `pixel-art-professional` skill docs
(MIT licensed, Copyright (c) 2025 Brandon Williams — see ATTRIBUTION.md). That
plugin applies this through Aseprite MCP tools; here it's just the technique
knowledge, applied by hand in `pixel_lib.py` drawing code.

## Shading types

- **Flat** — single color per surface. Iconic, simple. Good for UI/small icons.
- **Cell (hard)** — 2-3 colors per surface, hard edges between them. Bold,
  readable, cartoon-ish. Good default for small sprites (32x32 and under).
- **Soft (dithered)** — gradual transitions via dithering. Reads as smoother
  surfaces at the cost of a busier silhouette.
- **Pixel clusters** — manual dithering with hand-placed pixels for texture
  (fabric, metal, stone).

## The shading workflow

1. Pick a light source direction.
2. Base color = midtone.
3. Shadow = darker **and hue-shifted toward blue/purple** — not just the same
   hue at lower value. Flat-darkened shadows read as muddy.
4. Highlight = lighter **and hue-shifted toward warm** (yellow/white) — same
   reasoning, the other direction.
5. Shadows go on surfaces facing away from the light; highlights on surfaces
   facing it.
6. Optional: a faint reflected-light tone in the deepest shadow, for depth.

**Common mistakes to avoid:**
- Pure black shadows / pure white highlights (use hue-shifted dark/light tones).
- No hue shift at all (shadow/highlight = same hue as base, just value-scaled).
- "Pillow shading" — darkening around the silhouette edges instead of shading
  from an actual light direction. Reads as flat/glowing, not lit.

## Color ramps

A ramp is a sequence from deep shadow to bright highlight:
`deep shadow -> shadow -> base -> highlight -> bright highlight` (3 or 5 steps).
Build it by hue-shifting, not just scaling brightness — shadows lean cool,
highlights lean warm (or toward the actual light color).

## Antialiasing (AA)

- Use on: diagonal lines/curves at 64x64+ that read as jagged.
- Skip on: sprites <= 16x16 (nothing to smooth), intentionally blocky styles,
  high-contrast silhouettes, very limited palettes.
- Manual technique: 1px-wide intermediate color between edge and background,
  placed only at the "steps" of a diagonal — not the whole edge.

## Palette sizes (for a retro-authentic look)

| Colors | Reference hardware |
|---|---|
| 4 | Game Boy, ZX Spectrum per-sprite |
| 8 | CGA, early arcade |
| 16 | NES, Master System, early VGA |
| 32 | SNES per-background, Amiga OCS |
| 64 | Genesis, PC Engine |
| 256 | VGA, SNES full palette, Amiga AGA |

### Ready-made retro palettes

Game Boy (4, darkest->lightest green):
`#0F380F #306230 #8BAC0F #9BBC0F`

PICO-8 (16):
`#000000 #1D2B53 #7E2553 #008751 #AB5236 #5F574F #C2C3C7 #FFF1E8
#FF004D #FFA300 #FFEC27 #00E436 #29ADFF #83769C #FF77A8 #FFCCAA`

C64 (16):
`#000000 #FFFFFF #880000 #AAFFEE #CC44CC #00CC55 #0000AA #EEEE77
#DD8855 #664400 #FF7777 #333333 #777777 #AAFF66 #0088FF #BBBBBB`

## Dark-fantasy / grimdark variant (not in the source docs — our own extension)

Applying the same hue-shift rule but starting from a desaturated, cool base
instead of a vivid one:

- Base tones desaturated and value-compressed (avoid bright saturated
  midtones); keep exactly **one** saturated accent (a glowing rune, gem,
  eyes) so it actually pops against the muted rest.
- Shadow hue-shift goes further cool (near-black violet) than a cheerful
  palette would.
- Highlight hue-shift goes toward **cold** tones (pale blue-green) instead of
  warm yellow — reserve warm highlights for actual firelight/torches.
- Metals read as tarnished (bronze/iron, not polished gold) unless the piece
  is meant to look magical/pristine.

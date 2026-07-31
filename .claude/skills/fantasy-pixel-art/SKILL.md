---
name: Fantasy Pixel Art
description: >
  Generate fantasy and dark-fantasy pixel art — character sprites, items,
  enemies, UI panels, and parallax backgrounds — as true 1:1 PNGs, sprite
  sheets, and animated GIFs. Use when the user asks for a "pixel art
  sprite", "pixel character", "sprite sheet", "walk cycle", "pixel
  background", "tileset", "game asset", "wizard/knight/enemy sprite",
  "dark fantasy pixel art", or wants existing pixel art restyled or
  animated. Art is authored as declarative shapes and rendered by a
  bundled Python script — no external API, no Aseprite.
version: 1.0.0
---

# Fantasy Pixel Art

Design sprites as **shapes**, not as thousands of individual pixels. A
bundled renderer rasterizes them at high resolution, downsamples onto the
pixel grid, and snaps every pixel back to a locked palette — so curves come
out smooth and the result is still genuine pixel art.

## Prerequisites

Pillow: `pip install Pillow` (check with `python3 -c "import PIL"`).

## Why shapes

A 64×64 sprite is up to 4096 pixels. Authoring that as an explicit
`{x, y, color}` list is slow, burns enormous context, and every curve
becomes hand-plotted stair-steps. The wizard in
`references/example-wizard.json` is **18 shapes**.

Each shape is filled *and* stroked, which is what produces the outlines
**between** regions (hat over face, beard over robe) — not just around the
silhouette. That internal outlining is most of what makes fantasy sprites
read clearly at small sizes.

## Workflow

### 1. Pick a canvas size

| Size | Use |
|---|---|
| 16×16 | items, icons, inventory, tiles |
| 32×32 | small enemies, NPCs, props |
| 64×64 | hero characters, bosses, detailed items |
| 128×64 | wide bosses, banners, UI panels |
| 160×90 or larger | backgrounds, parallax layers |

Sprites are usually taller than wide. A humanoid at 64×64 wants roughly:
head 8-10px tall, body to ~y=55, feet on the floor line, and it should
**not** fill the full canvas width — leave breathing room, or the character
reads as a blob. Aim for a body about half the canvas width.

### 2. Lock a palette

8-16 named colors. Every color must be declared; the renderer snaps to
them, so an undeclared shade cannot leak in. Name colors by **role**
(`robe`, `robe_shadow`, `outline`), never by hue (`purple1`) — roles
survive a recolor, hue names don't.

Read `references/style-guide.md` before choosing colors. The two style
families and their rules live there. Short version for dark fantasy:
desaturated and cool, shadows hue-shifted toward blue/violet rather than
just darkened, and **at most one saturated accent** in the whole sprite
(a rune, a gem, glowing eyes) — that restraint is what sells the mood.

### 3. Write the spec

JSON, rendered by `scripts/render_sprite.py`. Coordinates are in canvas
units and may be fractional — sub-pixel positions are meaningful because
drawing happens supersampled.

```json
{
  "name": "knight",
  "size": [64, 64],
  "supersample": 8,
  "outline": "outline",
  "auto_outline": true,
  "stroke_width": 1.15,
  "palette": {"outline": "#1a1614", "armor": "#5a6470", "armor_dark": "#333b45"},
  "shapes": [
    {"type": "bulged", "x_top": [24, 40], "x_bottom": [20, 44],
     "y_top": 26, "y_bottom": 54, "bulge": 1.5, "fill": "armor"}
  ]
}
```

Top-level keys: `size`, `palette`, `shapes` (or `frames`), plus optional
`supersample` (default 8), `outline` (palette name for auto-outlining),
`auto_outline`, `stroke_width`, `alpha_cut`, `sheet`, `gif`.

### 4. Shape vocabulary

Every shape takes `fill` (palette name) and optionally `stroke`,
`stroke_width`, `outline: false` (skip stroking — use for shading patches
*inside* an already-outlined shape), and `dx`/`dy` nudges.

| `type` | Fields | Use for |
|---|---|---|
| `polygon` | `points: [[x,y],…]` | anything explicit |
| `rect` | `box: [x0,y0,x1,y1]` | boxes, shading patches |
| `ellipse` | `center`, `radius` (num or `[rx,ry]`) | heads, hands, shields, gems |
| `line` | `from`, `to`, `width` | staffs, spears, seams |
| `arc` | `center`, `radius`, `start`, `end`, `width` | crooks, bows, arches, horns |
| `taper` | `spine: [[x,y,half_width],…]` | curling hat crowns, tails, capes, smoke |
| `band` | `x_top`, `x_bottom`, `y_top`, `y_flat`, `bulge` | beards, hanging cloth |
| `bulged` | `x_top`, `x_bottom`, `y_top`, `y_bottom`, `bulge` | robes, tunics, trunks, towers |
| `gradient` | `box`, `from`, `to` | dithered skies, fog, torch falloff |
| `scatter` | `box`, `fill`, `count`, `size`, `seed` | stars, embers, rubble, moss |

`taper` is the workhorse for fantasy silhouettes: a spine of points each
carrying a half-width, so a witch hat that narrows *and* curls over at the
tip is one shape. `band`'s bottom is a single broad arc — a sine-scalloped
hem was tried and snaps into sharp zig-zag teeth on a 64px grid, because
the cusps land sub-pixel.

Arc angles: 0° is 3 o'clock, increasing **clockwise**.

Draw back-to-front. Typical order: rear props → boots → body → shadow
patches → head/face → hair/beard → headwear → held items → hands.

### 5. Render

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/skills/fantasy-pixel-art/scripts/render_sprite.py" \
  spec.json -o out/ --preview-scale 8
```

Writes `out/<name>.png` at true 1:1 and `out/<name>_preview.png` upscaled
for viewing. **Always view the preview with the Read tool** — pixel art
must be looked at, not assumed. Then iterate on the spec.

| Flag | Default | Meaning |
|---|---|---|
| `-o, --output-dir` | `.` | where files land |
| `--preview-scale` | `8` | nearest-neighbour preview upscale, `0` to skip |
| `--gif` | off | also write `anim.gif` (needs 2+ frames) |
| `--sheet-columns` | from spec | sprite-sheet column count |

### 6. Animate (optional)

Replace `shapes` with `frames`, each `{"name":…, "offset":[dx,dy], "shapes":[…]}`.
Multiple frames automatically produce `sheet.png`; add `--gif` for
`anim.gif`.

```json
"frames": [
  {"name": "walk_0", "shapes": [...]},
  {"name": "walk_1", "offset": [0, -1], "shapes": [...]}
],
"sheet": {"columns": 3},
"gif": {"frame_ms": 120}
```

Cycle structure and timing tables are in `references/style-guide.md`. Key
numbers: a 3-frame walk is contact / passing (body bobs up 1-2px) /
contact-mirrored, at **~100-120ms per frame**. Slower than that reads
floaty. For a hooded or masked character with no visible face, put the
personality in the free hand, weapon, and cloak-hem follow-through.

Keep a `scatter` shape's `seed` fixed across frames or the specks will
crawl between them.

## Rules that keep output looking hand-made

- **One accent color, maximum.** Everything else desaturated.
- **Flat shading beats gradients.** Two tones per surface (base + shadow),
  hard-edged. Reach for `gradient` only on skies and fog.
- **No pillow shading.** Do not shade inward from every silhouette edge —
  that reads as an inflated cushion. Commit to one light direction.
- **Silhouette first.** If it isn't readable as a solid black shape, no
  amount of interior detail rescues it.
- **Skip antialiasing under 32×32.** There isn't room; it just muddies.
- **Faces are optional.** Below ~48px, a shadowed face under a hat brim
  reads better than tiny eyes, and it ages a character instantly.

## Troubleshooting

| Symptom | Cause / fix |
|---|---|
| `Color 'x' is not in the palette` | Every `fill`/`stroke` must be a declared palette name (or a literal `#hex`) |
| Shapes look soft or blurred | `supersample` too low, or `alpha_cut` too low letting edge pixels survive |
| Outline broken in places | Keep `auto_outline: true`; raise `stroke_width` toward 1.4 |
| Zig-zag teeth on a curve | The curve's detail is sub-pixel — enlarge the feature or simplify it |
| Sprite reads as a blob | Silhouette too wide/uniform; narrow the body, add a gap between limbs |
| Shading looks like plastic | Too many tones. Cut to base + one shadow |

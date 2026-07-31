# Fantasy Pixel Art — Style Guide

Two style families, then the rules that apply to both.

---

## Family A — Dark fantasy (default)

Grimdark, moody, the look of a cursed dungeon crawler.

- **Desaturated and cool.** Violets, slate greys, cold browns. Nothing
  candy-colored.
- **Shadows are hue-shifted, not just darkened.** Push shadow tones toward
  blue/violet as they darken. A shadow that is only "the base color at 60%
  brightness" reads muddy and cheap.
- **Highlights lean cold too** (pale blue-green), *unless* the light source
  in the scene is fire — then warm highlights are correct and become a
  storytelling device.
- **Exactly one saturated accent per sprite.** A rune, a gem, an orb,
  glowing eyes. Everything else muted. This single point of chroma is what
  carries the whole mood; two accents halve the effect, three kill it.
- **Metals are tarnished** — bronze, blackened iron. Polished gold reads
  as "loot icon," not as a worn character.

Reference palette (a 64×64 wizard):

| Role | Hex |
|---|---|
| outline | `#14111a` |
| hat main / dark / light | `#362b45` / `#241d30` / `#4a3c5c` |
| band (tarnished bronze) | `#7a6134` |
| face shadow | `#1c1724` |
| robe main / dark / light | `#3d3350` / `#2a2338` / `#544a68` |
| beard / shade | `#d8d4cc` / `#a8a49c` |
| staff | `#5a4230` |
| **accent** (orb, eyes) | `#7ce0c0` |

---

## Family B — Flat mascot / sticker

Muted clipart look: readable at thumbnail size, friendly, no VFX.

- **Bold outline everywhere — including *between* internal regions**
  (hat vs. face, beard vs. robe), not just around the silhouette.
- **Two-tone flat shading, maximum.** Base plus one hard-edged shadow
  shape. No dithering, no ramps, no hue-shift drama.
- **Near-neutral palette**: greys, taupe, warm browns, cream.
  **No saturated accent at all** — the restraint is the style.
- **Silhouette tells the story, not the face.** Face sits in hat shadow,
  often with no drawn eyes. Read the character from hat shape, beard and
  posture.
- **Give it a gesturing off-hand.** One hand holds the prop; the other is
  drawn clear of the body silhouette, doing something. This is the single
  biggest difference between "a cone with a face" and a character.

| Role | Hex |
|---|---|
| outline | `#1a1614` |
| hat main / dark / light | `#5a5450` / `#38332f` / `#8a8078` |
| robe main / shadow | `#786f66` / `#544c45` |
| beard / shade | `#eee8dc` / `#c7bfaf` |
| staff wood | `#7a5a3a` |

---

## Shared craft rules

### Shading

Pick **one** light direction and commit. Shade the surfaces facing away
from it; leave the rest.

The failure mode to avoid is **pillow shading** — darkening inward from
every silhouette edge at once. It has no light direction, so the sprite
looks like an inflated cushion. If the shading is symmetrical on both
sides of the character, it is pillow shading.

Two tones per surface is usually right. Three is a lot. Gradients belong
to skies, not to cloth.

### Dithering

A 2×2 checkerboard between two palette colors fakes an intermediate tone.
Use it on **one** area — the deepest hem fold, a fog band, a stone
texture — and leave the rest flat. Dither everywhere reads as noise or as
a screen-door, not as texture.

Rough/ancient surfaces (weathered stone, old metal) want the irregular
crosshatch pattern instead of the regular checkerboard.

### Antialiasing

Skip it below 32×32 — there is no room, and it only muddies the clusters.
At 64×64 and up, apply it sparingly: a single intermediate pixel at the
*steps* of a long diagonal, never along a whole edge.

### Silhouette

Squint, or fill the sprite solid black. If it isn't identifiable, no
amount of interior detail will save it. Fixes: narrow the body, put a
visible gap between limbs, exaggerate the one distinctive feature (hat
curl, pauldron, bow), and vary the outline — a uniform blob is the enemy.

Do **not** let the body fill the canvas width. A 64×64 character usually
wants a body about half the canvas wide, with the props (staff, cloak,
weapon) using the rest.

---

## Animation

### Frame timing

| FPS | ms/frame | Feel |
|---|---|---|
| 30 | 33 | modern, smooth |
| 15 | 67 | retro game |
| 12 | 83 | traditional "on twos" |
| 10 | 100 | classic pixel art |
| 4 | 250 | idle / breathing |

A 3-frame walk cycle lands at **~100-120ms per frame**. Slower reads
floaty — 200ms/frame was tried and looked like the character was wading.

### Cycle structure

**Walk (3-frame):** contact → passing (whole body bobs **up** 1-2px, feet
together) → contact mirrored.

**Walk (4-frame):** contact → down (compression) → passing → up (push-off).

**Idle breathing (2-4 frame):** neutral → rise 1-2px → hold → settle. Very
small movement, long holds (200ms+).

### Principles that still matter at 64px

- **Anticipation** — one windup frame before an action makes it land.
- **Follow-through** — cloth, hair and beards keep moving 1-2 frames after
  the body stops. On a hooded or masked character with no visible face,
  this *is* the performance: animate the free hand, the weapon and the
  cloak hem, because nothing else can carry expression.
- **Squash & stretch** — 1-2px of deformation on impact sells weight.
- **Ease** — hold the extreme poses longer than the in-betweens rather
  than using uniform timing.

### Sprite sheets

Lay out one row per direction (down / left / right / up), one column per
frame, every cell the same size. Mirror the side-facing row rather than
drawing both — but only if the character is symmetrical (a staff held in
one hand will swap sides, which is usually acceptable and occasionally
not).

Keep any `scatter` shape's `seed` constant across frames, or the specks
crawl between them.

---
name: Spell FX Animation
description: >
  Generate looping pixel-art spell and combat effects — fireballs, chain
  lightning, sleep/status auras, explosions, heals, shields, projectiles,
  impacts — as sprite sheets, GIFs, and preview pages. Use when the user
  asks for a "spell effect", "fireball", "lightning", "magic animation",
  "VFX", "particle effect", "explosion", "projectile", "buff aura",
  "status effect", "attack animation", or wants an existing effect
  restyled, retimed, or looped. Effects are generated procedurally with
  Python/Pillow — no external API, no Aseprite.
version: 1.0.0
---

# Spell FX Animation

Procedural looping effects. The idea that separates these from character
sprites: **an effect is a field or a path evaluated per frame, not a
drawing you nudge**. Hand-animating flame or lightning frame by frame
drifts out of register immediately; expressing it as a function of
position and phase keeps every frame consistent by construction.

## Prerequisites

Pillow: `pip install Pillow`. Helpers live in `scripts/fx_lib.py`.

## Pick the construction, not the drawing

| Effect | Build it as |
|---|---|
| flame, fireball, jet, breath | **field** — per-column height, colour by distance from the axis as a fraction of that height |
| lightning, arcs, cracks, roots | **displaced path** — subdivide a line, offset perpendicular, taper the offset at both ends |
| aura, rune circle, shield | **parametric outline** — ellipse/polygon sampled per frame, radius driven by phase |
| status glyphs (sleep Z, poison bubble, rage mark) | **staggered emitters** — N copies of one glyph, phase-offset by 1/N of the loop |
| explosion, impact, shockwave | **expanding ring + decaying particles**, radius as a function of phase |
| heal, buff motes | **orbiters** — particles on a parametric path around the target |

`scripts/fx_lib.py` provides `flame_field`, `displaced_path`,
`ellipse_points`, `lcg`/`rand_unit` (deterministic RNG), `Canvas` and
`save_effect`.

## The rules that matter

These are mistakes worth avoiding, not theory. Every one of them was hit
while building the reference effects.

### 1. Never let a loop frame go near-empty

The most common failure. A build-up-then-dissipate cycle looks right as a
one-shot and reads as a **blink** when looped, because the sparse tail
frame flashes past. Either sustain the effect across all frames and vary
only its geometry, or render it explicitly as a one-shot and say so.

### 2. Vary geometry, not brightness

Dimming alternate frames reads as a strobe or a rendering fault. At the
contrast a saturated FX palette runs, a value pulse is far more visible
than a shape change. Keep every frame's colour treatment identical and let
the silhouette do the animating. Pulse brightness only when the pulse *is*
the effect (a heartbeat aura, a charging glow), and keep it gentle.

### 3. Anchor hot cores by distance, not by row

A white core written as "the middle rows of the strip" smears into a
painted stripe down the whole length. Threshold on distance from the
actual hot point instead; the core stays a point and reads as the hottest
part.

### 4. Irregularity needs two frequencies

Clipping alternate columns, or a single sine, produces a regular sawtooth —
fire ends up looking like a fish skeleton. Sum two waves at unrelated
frequencies, e.g. `0.26·sin(0.55x + φ)` plus `0.13·sin(1.27x − 1.7φ)`.

### 5. Pin displaced paths at their endpoints

Taper the perpendicular offset by `sin(t·π)` so it is zero at both ends.
Without it a lightning arc detaches from its targets and a chain stops
reading as connected.

### 6. Glow density controls apparent thickness

An outer glow applied to every sample of a path doubles its visual weight
and a bolt becomes a ribbon. Every second or third sample is usually right
for something that should look thin and sharp.

### 7. Detached particles must clear the silhouette

Sparks and embers offset *inside* the effect only repaint pixels the field
already covered, so nothing reads as a separate particle. Push them well
outside the shape.

### 8. A flat ellipse outline fills in

A ground rune 2px tall has no interior left, so it renders as a solid blob
however sparsely you sample it. Raise the flattening (≈0.44 of the radius,
not 0.3) or draw it dashed — dashed also reads as a rune rather than a
smudge.

### 9. Seed deterministically

Use the bundled LCG, not `random`. Effects must render identically every
run, and a per-frame reseed derived from the frame index is what gives
lightning and fire their instability while staying reproducible.

### 10. Keep a phase-driven loop closed

Driven by `phase = f / FRAMES * 2π` the loop closes by construction. Check
that any extra motion — drifting particles, orbiters — also completes a
whole number of cycles.

## Timing

| Effect | ms/frame | Frames |
|---|---|---|
| lightning, sparks | 60–80 | 6–8 |
| fire, flame loop | 70–100 | 4–8 |
| projectile in flight | 80–120 | 4–6 |
| explosion (one-shot) | 50–90 | 6–12 |
| aura, shield, buff | 120–180 | 6–8 |
| sleep, slow, drowsy status | 180–250 | 6–8 |

Fast effects want tight loops, status effects languid ones. A status aura
running at a lightning cadence looks like an error state.

## Palette

Four to seven colours as a ramp from the hot centre outward — fire: white
→ pale yellow → orange → red → deep red. FX are the one place saturation
should run high: they must stay legible against arbitrary backgrounds and
read at a glance mid-combat.

Shift the ramp's hue to signal type — ice/arcane cyan-violet, poison
green-yellow, holy white-gold, shadow violet-black — but keep its
*structure* identical across a family so the set reads as one game's magic.

## Workflow

1. Choose the construction from the table above.
2. Set canvas, frame count and timing. Projectiles are usually wider than
   tall (`64x32`); auras and status effects taller (`40x48`).
3. Write the generator against `scripts/fx_lib.py`.
4. Render, then **view the sheet preview with the Read tool** — check
   specifically for a near-empty frame and for brightness pulsing.
5. Save the sheet, per-frame PNGs and a GIF.

## Embedding in a page

Animate a strip with `background-position-x` in **pixels**, one container
width per frame:

```css
.fx { image-rendering: pixelated; animation: burn .48s steps(1) infinite; }
@keyframes burn {
  0%   { background-position-x: 0; }
  25%  { background-position-x: -256px; }   /* one container width */
  50%  { background-position-x: -512px; }
}
```

Percentages do **not** work: a percentage in `background-position` resolves
against (container width − image width), not as a per-frame step, so the
frames scatter and the sprite appears to blink. Each display size therefore
needs its own keyframe set.

Always pair the animation with a `prefers-reduced-motion` rule that pauses
it.

## Troubleshooting

| Symptom | Cause |
|---|---|
| Sprite blinks once per loop | A near-empty frame (rule 1), or percentage offsets in CSS |
| Strobing | Per-frame brightness variation (rule 2) |
| Reads as a ribbon, not a bolt | Glow on every path sample (rule 6) |
| Regular zig-zag "fish skeleton" | Single-frequency irregularity (rule 4) |
| Arc floats off its target | Missing endpoint taper (rule 5) |
| Ground rune is a solid blob | Ellipse too flat (rule 8) |
| Sparks invisible | Particles inside the silhouette (rule 7) |
| Loop stutters at the wrap | Secondary motion not completing whole cycles (rule 10) |

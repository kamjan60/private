# Animation Timing & Sprite Sizing Reference

Condensed from `willibrandon/pixel-plugin`'s `pixel-art-animator` and
`pixel-art-creator` skill docs (MIT licensed — see ATTRIBUTION.md).

## Frame duration by target FPS

| FPS | ms/frame | Use case |
|---|---|---|
| 60 | 16-17 | very smooth, fast modern animation |
| 30 | 33 | standard modern animation |
| 24 | 42 | film-like |
| 20 | 50 | smooth retro |
| 15 | 67 | retro game animation |
| 12 | 83 | traditional "on twos" |
| 10 | 100 | classic pixel-art animation |
| 8 | 125 | slower |
| 4 | 250 | idle/breathing |

A 3-frame walk cycle (contact / passing / contact-mirrored) at classic
pixel-art speed lands around **100-120ms per frame** — a full 3-frame loop
in ~0.3-0.36s. (First pass on the wizard sprite used 200ms/frame, which read
as floaty; dropped to 120ms per this table.)

## Classic cycle structures

**Walk (4-pose canonical; collapses to 3 if you merge contact poses):**
1. Contact (leading foot forward)
2. Down (compression / passing-frame bob)
3. Pass (other foot passing under the body)
4. Up (push-off)

**Run (8-pose):** contact-down-pass-up, twice (mirrored), faster cadence than
walk.

**Idle breathing (2-4 pose):** normal -> slight rise (1-2px) -> hold -> back
down. Very small vertical offset, long hold per frame (200ms+).

## Animation principles worth keeping even at tiny scale

- **Timing** — slow actions get more frames/longer holds; fast actions get
  fewer frames and short holds (impacts: 30-50ms).
- **Anticipation** — a windup pose before the main action reads as weightier.
- **Follow-through** — trailing elements (hair, cloth, a beard) settle 1-2
  frames after the body stops.
- **Squash & stretch** — 1-2px of deformation on impact/landing sells weight.
- **Ease in/out** — hold the start and end poses longer than the middle of a
  motion instead of even timing throughout.

## Common sprite dimensions

| Class | Sizes |
|---|---|
| NES/Game Boy sprite | 8x8, 8x16 |
| SNES/Genesis sprite | 8x8 up to 64x64 |
| Small modern character | 32x32, 48x48 |
| Medium modern character | 64x64, 96x96 |
| Tile | 16x16, 32x32 |
| Icon | 16 / 24 / 32 / 48 / 64 / 128 |

32x32 (used for the wizard) sits at the top of "small" — room for a face,
hands, and a readable silhouette in all 4 directions without needing AA.

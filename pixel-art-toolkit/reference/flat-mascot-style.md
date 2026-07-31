# Flat Mascot / Sticker Style

Target style reference (derived from a supplied example image — a
Shutterstock-style pixel-art wizard clipart), captured here so future
generations in this repo default to it instead of the earlier
dark-fantasy/hue-shifted treatment in `color-and-shading.md`. That variant
is still valid as an alternate style; this is the one to reach for unless
asked otherwise.

## What makes it read as "sticker," not "game sprite"

1. **Bold outline everywhere, not just the silhouette.** Most of our earlier
   work only outlined the outer silhouette (`outline_pass`: transparent ->
   opaque boundary). This style also puts a dark outline **between major
   internal regions** — hat vs. face-shadow, beard vs. robe, staff vs. hand.
   Practically: after drawing each big shape, run a thin dark border along
   its edge against the *next* shape too, not only against transparency.
2. **Two-tone flat shading, max.** Base color + a single flat shadow shape
   (usually the skirt/hem, or the side away from an implied light). No
   dithering, no 3+ step ramps, no hue-shifted shadow/highlight drama. The
   shadow is a clean hard-edged shape, not a gradient or a fold pattern.
3. **Desaturated, near-neutral palette.** Greys, taupe, warm browns, cream.
   **No saturated accent color** — no glowing gem, no magic green, nothing
   that reads as "fantasy VFX." If the source needs a single warm note it's
   the staff wood or a cream beard, not a lit gem.
4. **Silhouette does the storytelling, not the face.** The face sits in hat
   shadow and is mostly *not drawn* — no visible eyes. Read the character
   from hat shape + beard + posture, not facial expression.
5. **A gesturing off-hand.** One hand holds the prop (staff); the other is
   drawn separate from the robe silhouette, fingers blocked in, doing
   something (holding the cloak open, resting at the hip) — this is what
   makes it feel alive instead of a stiff cone with a face.

## Specific shape vocabulary (this character family)

- **Hat**: wide brim, tall crown, **tip curls over into a hook** instead of
  standing straight (our earlier `cone`/`bent` hat styles were straight or
  leaning — this one actively curls, like a shepherd's crook echoed at the
  top of the head).
- **Beard**: long, reaches the chest, **wavy rounded bottom edge** — not the
  pointed twin-tuft curl used in the dark-fantasy variant. Think 2-3 soft
  scallops, not a taper to a point.
- **Staff**: wood-brown, topped with a **curved shepherd's-crook** (spiral
  hook), not a gem/skull/crystal.
- **Robe**: plain, minimal fold detail (1-2 faint vertical lines at most),
  rounded shoulders, hem around mid-calf, boots barely peeking out.

## Palette starting point

| Role | Color | Notes |
|---|---|---|
| Outline | near-black `#1a1614` | used for outer silhouette AND internal region borders |
| Hat main | taupe-grey `#5a5450` | |
| Hat shadow | dark grey `#38332f` | |
| Hat highlight | warm light grey `#8a8078` | brim curl / edge catch-light only |
| Robe main | warm grey-brown `#786f66` | |
| Robe shadow | `#544c45` | one flat shadow shape (hem/one side), not a ramp |
| Beard / hair | cream-white `#eee8dc` | |
| Beard shadow | pale warm grey `#c7bfaf` | sparingly, under the chin curve only |
| Staff wood | mid brown `#7a5a3a` | |
| Skin (rare, mostly hidden) | muted tan `#c9ab8c` | only where the shadow doesn't fully cover it |

Swap hue as needed per-character (this doc's dark-fantasy sibling shows how
to build a palette family) but **keep the desaturation and the "no glowing
accent" rule** — that restraint is most of what reads as "clipart" rather
than "game item icon."

## Animation & sprite-sheet notes

Nothing about this style blocks the existing animation/timing guidance in
`animation-and-sprites.md` — walk-cycle structure, frame timing, and
`compose_sheet()` all apply unchanged. The only style-specific animation
note: because the face carries no expression, personality in an idle/attack
animation has to come from the free hand, staff, and beard/robe hem motion
(follow-through) — animate those first when adding frames.

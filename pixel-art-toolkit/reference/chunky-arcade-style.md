# Chunky Arcade Style

A third dialect alongside `color-and-shading.md` (dark fantasy) and
`flat-mascot-style.md`. Bright, outline-free, very low resolution - the
look of a mobile/arcade wizard icon rather than a moody dungeon sprite.
Worked example: `examples/chunky-arcade/`.

## The rules, most of which invert the dark-fantasy ones

**No outline at all.** Not a thin one - none. Shapes are held apart purely
by hue and value contrast between neighbours.

**Therefore: saturate.** This follows directly from the rule above. With
no dark line separating shapes, desaturated neighbours fuse into a single
blob. Vivid purple against vivid blue against yellow *is* the structure.
This is the one style where the "single accent" discipline is wrong -
several saturated colours competing is the point.

**Low resolution on purpose.** 32x32, or 16x16 for an icon. A feature gets
two or three pixels, so nothing can be subtle: two eyes become one dark
bar, a nose disappears entirely, a beard is a grey slab with one darker
edge.

**Redraw between sizes, never downscale.** At 16x16 the hat brim is one
row and the beard three, so the proportions have to be re-planned from
scratch. Resampling a 32x32 turns every deliberate 1px step into mush.

**Keep the build thin.** Narrow shoulders and a robe that barely flares -
8px at the shoulder to 12px at the hem on a 32px canvas. The wide robe
cone is the dark-fantasy silhouette; here it just makes a squat blob, and
an old wizard should read as frail.

**Two flat tones per surface, stepped hard.** A lit plane down one side,
a shadow plane down the other, one step each, no ramps and no dithering.

**Blocky silhouette.** Edges move in jumps of 1-2px per row. No attempt at
smooth curves - at this size a curve reads as a mistake.

**Hold one edge with a prop.** A staff off to one side gives the thin body
a vertical to sit against and stops the sprite reading as a lone sliver.

**Decorative motifs do the storytelling.** At this size there is no room
for a face to carry character, so a wizard is established by yellow stars
on the robe and a big crystal on the staff. Pick the two or three iconic
marks of the archetype and place them boldly.

## Starting palette

| Role | Hex |
|---|---|
| robe light / main / dark | `#a676d6` / `#7c50b6` / `#5c3a8c` |
| skin / shade | `#e2ac7a` / `#c48a5c` |
| eye bar | `#241830` |
| beard / light | `#b0b0ba` / `#d4d4dc` |
| stars | `#f4d840` |
| staff / dark | `#8c5c3a` / `#684028` |
| crystal light / main / dark | `#aad8f8` / `#4a9ee8` / `#2a6ec8` |
| gem | `#7ad048` |
| boots | `#201828` |

## Draw-order trap

The beard must go down **after** the robe. Drawn before it, the collar
covers it and what should be the character's most identifiable feature
collapses to a two-pixel grey sliver. Same reasoning applies to any
element that hangs over the body: hair, scarves, tabards.

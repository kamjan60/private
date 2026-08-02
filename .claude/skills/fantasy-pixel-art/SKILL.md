---
name: Fantasy Pixel Art
description: >
  Generate fantasy and dark-fantasy pixel art — character sprites, walk
  cycles, items, enemies, interior props, floor tilesets and UI panels — as
  true 1:1 PNGs, sprite sheets and animated GIFs. Use when the user asks for
  a "pixel art sprite", "pixel character", "sprite sheet", "walk cycle",
  "tileset", "props", "room interior", "game asset", "wizard/knight/enemy
  sprite", "dark fantasy pixel art", or wants existing pixel art restyled or
  animated. Everything is plotted pixel by pixel with Python and Pillow — no
  external API, no Aseprite, no image model.
version: 2.0.0
---

# Fantasy Pixel Art

Pixel art here is **code that plots pixels**, not a prompt and not a filter
over a bigger image. A sprite is a Python function that writes spans and
single pixels into a small canvas, at the size it will actually be shown.

That constraint is the method. At 32×32 a face is nine pixels, so every one
of them is a decision — and the only way to know whether a decision worked
is to render it and look at it.

## The loop

1. Write a generator: one function per subject, taking a frame index if it
   moves.
2. Run it. Save at 1:1 **and** a nearest-neighbour upscale for review.
3. **Look at the upscale.** Not the code — the picture.
4. Fix what is actually wrong, not what you assumed would be wrong.

Step 3 is not optional and cannot be replaced by reasoning. Every rule below
exists because something read fine in the source and was wrong on screen.

```python
from PIL import Image

class G:
    def __init__(self, w=32, h=32):
        self.img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        self.p = self.img.load()
    def put(self, x, y, c):
        if 0 <= int(x) < self.img.width and 0 <= int(y) < self.img.height:
            self.p[int(x), int(y)] = c
    def span(self, y, x0, x1, c):
        for x in range(int(x0), int(x1) + 1): self.put(x, y, c)
    def rect(self, x0, y0, x1, y1, c):
        for y in range(int(y0), int(y1) + 1): self.span(y, x0, x1, c)

img.resize((img.width * 4, img.height * 4), Image.NEAREST).save("preview.png")
```

`scripts/render_sprite.py` renders a declarative shape spec when the subject
suits one. For anything with character, write the spans by hand.

## Rules, each one a mistake already made

**Draw order is anatomy.** Whatever is in front is drawn last. A beard
plotted before the robe collapsed to a two-pixel sliver behind it. Dust
drawn as a disc before the rock shards swallowed every shard and the effect
became a brown blob. A hood drawn after the eyes painted its face void
straight over them. When something disappears, check the order before you
touch the shape.

**A prop held in front vanishes on the back view.** A chest-held slate went
on glowing through the body when the character turned away. Anything the
body should occlude is suppressed — or replaced by its harness — when facing
away.

**Silhouette first, colour second.** Squint at the upscale: if two classes
are the same blob, no palette will separate them. Give each a distinct
outline — a wide brim, a helm lamp, a flat scribe's cap — before choosing a
hue.

**Animate geometry, not brightness.** Dimming alternate frames strobes. A
wobble, a lean, a change of radius reads as motion: the reactor core
breathes by growing two pixels, never by fading.

**No frame in a loop may go near-empty.** A blank tail frame reads as a
blink, not a fade. Sustain something every frame, even if it is only a dust
bed or an ember.

**Irregularity needs two frequencies.** One sine gives a comb; clipping on
alternate columns gives a fish skeleton. Sum two sines with unrelated
periods.

**Glow spill is what makes a light source.** A bright rectangle is a
coloured rectangle. The same rectangle with a dimmer halo bleeding one pixel
onto the surface around it is a lamp.

**Detached particles must clear the silhouette.** Embers inside the body are
invisible. Push them outside the shape or do not draw them.

**Measure text that has to fit.** A spell name longer than its chip spilled
onto the floor behind it. Measure and truncate rather than guessing a
character count.

**Seed deterministically.** A small LCG, never `random`. Regenerating a
sheet must give the identical sheet, or every review compares two different
pictures.

```python
def lcg(seed):
    s = seed
    while True:
        s = (1103515245 * s + 12345) & 0x7FFFFFFF
        yield s / 0x7FFFFFFF
```

**Give each instance its own phase.** Ten fittings on one clock blink like
fairy lights. Offset by index so a room flickers unevenly.

## Sheets and their contracts

A sheet is an index agreement between the generator and whatever draws it.
Write the layout in both places and say they are coupled.

* characters — `(class * dirs + dir)` rows, frames across
* effects — one row, `frame * W` across
* props — one column per prop; animated variants in a **second** sheet laid
  out `(prop * frames + frame)`, so the still sheet stays usable for baking

Reordering a class table without reordering the sheet hands every player
somebody else's body, silently. It has happened here. Comment the coupling.

**The CSS trap.** Animating `background-position-x` in *percentages*
resolves against (container width − image width), not per frame, so frames
scatter onto empty strip. Use pixel offsets, one keyframe set per display
size.

## Interiors: tiles, props, baked light

A room of one flat fill is a diagram. Three things fix it:

1. **Tiles with seams and wear** — 32×32 plating, two or three wear states,
   rare decals. Choose the variant from the tile's own coordinates, so the
   room looks worked-in and looks the same every time.
2. **Props against the walls**, furnished from a seed made of the room's
   name. Keep the middle clear: it is where people walk and fight.
3. **Light from the fittings, not a wash.** Darken the whole floor, then add
   a radial pool under each thing that actually emits, composited with
   `lighter`. A room with nothing lit stays dark, and that contrast is the
   atmosphere.

Bake floor, dead props and static pools into one cached canvas per room —
tiling live is thousands of draw calls a frame. Draw only the lit fittings
on top, live, so they can animate.

## Palette

Four to six values per material, and stay on them. Dark-fantasy interiors
want cold steel biased slightly blue, one warm accent for working light, one
cold accent for screens, and rust as the only saturated colour that is not a
light.

Never pure black for shadow — use the darkest tone in the palette, so
shadows stay in the same world as the lit surfaces.

## Verify before claiming

Render the upscale and read it back. For animation, lay every frame out side
by side and check the loop closes: the last frame must lead into the first.
If it ships into a game, screenshot it *in the game* — props that looked
correct in isolation vanished under a lighting pass that was too strong.

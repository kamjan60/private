# Phase 0 — Research

**Feature**: Manifest sprite'ów i warstwa nieoświetlana
**Date**: 2026-08-02

---

## R1. What actually dims a hunter today

**This one corrects the spec.** The spec says Act III dims the chest light
along with everything else. That is the right *outcome* to want and the wrong
*cause*, and planning against the wrong cause would have produced a fix in
the wrong file.

Read of `public/client.js` `draw()` and `src/round.js`:

| Mechanism | Where | Does it dim an actor? |
|---|---|---|
| Act darkness | `ACT_VISION = [1.0, 0.75, 0.5]` multiplies `vision` server-side | **No.** It shrinks the radius. Nothing is tinted. |
| Compartment wash (`doused` / `lit`) | `client.js`, inside the map loop | **No.** Drawn before the actors, so it darkens the plating and the people standing on it stay lit. |
| The fog | one radial gradient over the whole viewport, drawn **after** the actors | **Yes — and it is the only one.** |

So the real defect is narrower and sharper than the spec states:

> The fog is a flat screen-space overlay drawn after the sprites, so a lamp at
> the edge of your vision fades at exactly the same rate as the body carrying
> it. Act III makes this worse only because it shrinks the radius, putting
> more of what you can see into the faded band.

And a second one falls out of the same read, which the spec did not mention:

> A doused compartment darkens the floor and not the people. Zgaszenie makes
> the room go dark around hunters who stay fully lit.

**Decision**: keep User Story 2's outcome exactly as written — it is still
what we want — and retarget the work at the fog pass and the compartment
wash. Fix the fog in this feature; log the doused-actor gap as a follow-up
rather than widening scope silently.

**Rationale**: the acceptance scenarios in the spec are written against
observable brightness, not against a mechanism, so they survive the
correction unchanged. That is the argument for writing them that way.

**Alternatives considered**: rewriting the spec to match the code. Rejected —
the spec describes what a player should see, and it is right about that. The
mechanism belongs here.

---

## R2. How an unshaded layer works without shaders

SS14 marks a sprite layer unshaded and its renderer skips the lighting pass
for it. We have no shaders and no lighting pass — we have one gradient fill.
The equivalent is **draw order**.

**Decision**: a second sprite sheet holding only the emissive pixels, in the
same layout as the base sheet. During the actor pass, record what needs a
glow. After the fog fill, restore the world transform and draw the recorded
glow sprites.

**Rationale**:

- It is the smallest change that produces the right result: the emissive
  pixels are simply not underneath the thing that darkens.
- The generator already knows which colours are emissive (`glow`, `glow_lo`,
  `GLASS_HI`, lamp pixels), so splitting the layer is a change in where a
  pixel is written, not new art.
- Cost is one `drawImage` per visible actor that has any emissive pixel, and
  the fog culls the actor list to at most eight.

**Alternatives considered**:

- *Per-actor gradient holes* — punch a hole in the fog around each lamp.
  Rejected: the fog is one fill, and N holes means N fills or a much more
  expensive composite, for a worse result (it would reveal the body too).
- *One sheet, emissive stored in the alpha channel* — clever, and would halve
  the asset count. Rejected: it forces per-pixel work in JS or a second
  canvas to extract, which is exactly the cost this avoids.
- *`globalCompositeOperation = "lighter"` for the glow pass* — already used
  for the floor light pools. **Adopted as an option, not a default**: a lamp
  drawn with `lighter` over a dark background blooms nicely, but over a light
  floor it blows out. Decide by looking at it (see quickstart), not here.

**Constraint carried forward**: the glow pass must multiply by the same
`globalAlpha` the body used. A layer that ignores dimming must not also
ignore transparency, or Cień lights the mage up in exactly the dark he needs.
This is FR-012 and it is the one thing in this feature that fails silently.

---

## R3. Manifest format and how it reaches the client

**Decision**: the generator writes `hunters.json` next to `hunters.png`,
shaped after an RSI `meta.json`: version, frame size, sheet filenames,
direction order, and a list of named states each carrying its row, its
direction count and its frame count.

The client obtains it exactly the way it already obtains images:

```
served:   fetch("assets/hunters.json") once at boot, before the first frame
artifact: window.__MANIFEST, inlined by tools/build-sandbox.js
```

**Rationale**: `window.__ASSETS` already exists for precisely this split, and
`client.js` already prefers it over the network path. Following the same
shape means the artifact build needs one more line and the client needs one
more branch it already has a pattern for.

**Alternatives considered**:

- *A `.js` file assigning a global*, loaded with a `<script>` tag. Attractive
  because it is synchronous and identical in both modes. Rejected because the
  Node tests would have to `eval` it to check anything, and the tests are the
  main reason the manifest exists.
- *Generating a JS constant into `client.js`* — reintroduces a build step.
- *Keeping the arithmetic and merely testing it harder* — this is what we
  have. The header test catches a resize and cannot catch a reordering, and
  no test can catch a reordering while the order is the contract.

**Naming**: a state is `"<class>/<itemId>"`, e.g. `"Chirurg/stabilizator"`.
Both halves already travel on the wire as `cls` and are derivable from `it`,
and both are stable identifiers rather than positions. UTF-8 in JSON handles
`Strażnik` without ceremony.

---

## R4. Failure modes, and which one is allowed to be quiet

**Decision**:

| Situation | Behaviour |
|---|---|
| Manifest missing or unparseable at boot | Hard stop with a message naming the file. Never render. |
| Manifest names a state the sheet is too small to contain | Test failure, before the game runs. |
| Sheet has rows no state claims | Test failure. Wasted pixels almost always mean a stale manifest. |
| Server sends a class/item the manifest does not know | Draw the first state, warn **once per session**, keep playing. |

**Rationale**: the first three are developer errors and should be loud and
early. The fourth happens to a player mid-round, where a hard stop would be a
worse outcome than a wrong hat — but warning on every frame at 60 fps would
bury the console, which is how the current class of bug stayed invisible.

---

## R5. What the existing PNG-header test becomes

`test/wiring.test.js` currently reads the IHDR and asserts the sheet height
equals `classes × items × 4 × 32`. It catches "you added a class and forgot
to regenerate" and is blind to "you swapped two items".

**Decision**: replace it with a manifest/table agreement test — every
`class/item` pair in `classes.js` has a state, every state maps to a real
pair, and the manifest's own row arithmetic fits inside the PNG. Keep reading
the IHDR, but use it to bound the manifest rather than to guess at the table.

**Rationale**: same cost, strictly larger coverage, and it fails with the
name of the offending state instead of a pair of numbers.

---

## R6. Cost of the artifact constraint

`sandbox/artifact.html` is 239 KB today with every asset inlined as base64.

The manifest is roughly 100 states' worth of small objects — on the order of
4–6 KB of JSON before compression, inlined as text rather than base64.

A second sheet (emissive only) is mostly transparent and compresses hard;
`hunters.png` is 22 KB at full colour, so the glow sheet should land far
under that.

**Decision**: SC-007's 5 KB budget covers the manifest but **not** the second
sheet. Flag this: the emissive sheet is a real addition to a file that has to
travel to a phone. Measure it before assuming, and if it lands badly, the
fallback is to widen the base sheet by one frame column rather than ship a
second image.

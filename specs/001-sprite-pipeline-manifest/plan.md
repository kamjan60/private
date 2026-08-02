# Implementation Plan: Manifest sprite'ów i warstwa nieoświetlana

**Branch**: `claude/plugin-installation-3oluvd` | **Date**: 2026-08-02 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/001-sprite-pipeline-manifest/spec.md`

## Summary

Kill the implicit row formula and stop the fog from eating the lamps.

Today a hunter's sprite row is `(class * 3 + item) * 4 + direction`, written
out in three places across two languages and enforced by nothing stronger
than a PNG-header size check. Reordering either axis silently draws players
somebody else's body — and because classes are unique per round, a wrong
silhouette is forged evidence, not a cosmetic bug. The fix, borrowed from
SS14's RSI format, is a manifest emitted by the generator and looked up by
name: nothing outside the manifest computes a row, and the tests fail on a
reordering instead of only on a resize.

The second half is SS14's unshaded layer. Phase 0 found the spec's premise
was wrong about the mechanism — act darkness only shrinks the vision radius,
and the compartment wash is drawn *before* the actors so it never touches
them. The single thing that dims a hunter is the fog: one screen-space
gradient drawn after the sprites, which fades a lamp at exactly the rate it
fades the body carrying it. With no shaders available the equivalent of
"unshaded" is draw order — a second, emissive-only sheet drawn after the fog,
in world space, at the actor's own alpha.

That last clause is the whole risk. A layer that ignores darkness must not
also ignore transparency, or Cień lights the mage up in precisely the dark he
needs.

## Technical Context

**Language/Version**: Node.js 22 (server, tests); browser JavaScript with no
transpilation or bundling (client); Python 3 + Pillow (sprite generator)

**Primary Dependencies**: `ws` ^8.18.0 is the only runtime dependency and
this feature adds none. Pillow for art generation, Playwright for the browser
test — both development-only.

**Storage**: Files. `public/assets/hunters.png`, the new
`public/assets/hunters.json`, and a new emissive sheet. No database, no
persistence; the manifest is a build artifact regenerated from source.

**Testing**: `npm test` — a hand-rolled harness (`test/run.js`) over four
files, 80 assertions, no browser. `node test/browser.js` drives the real
client under Playwright on an emulated iPhone 13 and takes a screenshot.

**Target Platform**: Mobile browsers first (iPhone Safari is the primary
surface — the owner plays on a handset), desktop browsers second, plus a
single-file build that runs inside a claude.ai Artifact under a strict CSP
with no network access at all.

**Project Type**: Real-time multiplayer web game. Authoritative Node server
over WebSocket at 15 Hz, canvas 2D client on `requestAnimationFrame`.

**Performance Goals**: Client holds `requestAnimationFrame` on a handset with
at most 8 actors on screen. The glow pass adds at most one `drawImage` per
visible actor per frame — bounded by the server-side fog culling at 8.

**Constraints**:
- No build step and no new runtime dependencies. Anything requiring
  compilation is out.
- `sandbox/artifact.html` must stay one self-contained file that works with
  zero network. Every asset is inlined; the manifest must inline as literal
  JSON.
- The generator must stay deterministic — a churning manifest makes every
  diff unreadable.
- No game rule changes. This is renderer and asset-format work.

**Scale/Scope**: 8 classes × 3 items × 4 directions × 2 frames = 192 frames
across 96 sheet rows, 24 named states. Stages 1 and 2 only; stages 3–5 are
specified but out of scope for this plan.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

**`.specify/memory/constitution.md` is the unmodified template.** Every
principle is still a `[PRINCIPLE_N_NAME]` placeholder. There are no ratified
project principles, so there is no gate to pass and **claiming this feature
passed one would be theatre**.

Rather than invent gates retroactively, the check is run against the
constraints this repository actually documents and enforces — README,
`CLAUDE.md`, and the existing test suite:

| De-facto principle | Source | Status |
|---|---|---|
| Server is authoritative, including the fog; cull before serialising | README §Architecture, `snapshot.js` | **Pass** — renderer-only change, no snapshot fields added |
| No new runtime dependencies; no build step | `package.json` (one dep), no bundler | **Pass** — JSON and a PNG, read by existing code paths |
| The artifact must remain one offline file | `tools/build-sandbox.js` | **Pass with a flag** — R6 warns the emissive sheet's size is unmeasured; SC-007's budget covers the manifest only |
| Sprite-sheet order is a documented coupling | README, `classes.js` header comment | **Improved** — the coupling stops being a comment and becomes a tested contract |
| Pixel art is verified by looking, not by reasoning | `.claude/skills/fantasy-pixel-art/SKILL.md` | **Carried into quickstart** — step 4 requires reading the screenshot, and leaves the composite mode to be decided by eye |

**Post-Phase-1 re-check**: unchanged. The design adds one asset file, one
manifest and one draw pass; it removes a duplicated formula. Nothing in
Phase 1 introduced a dependency, a build step, or a rule change. The single
open risk is the emissive sheet's contribution to artifact size, tracked in
Complexity Tracking below rather than waved through.

## Project Structure

### Documentation (this feature)

```text
specs/001-sprite-pipeline-manifest/
├── plan.md                        # This file
├── spec.md                        # Feature specification
├── research.md                    # Phase 0 — corrects the spec's premise about dimming
├── data-model.md                  # Phase 1 — manifest, state, layer
├── quickstart.md                  # Phase 1 — how to prove it works
├── contracts/
│   └── hunters-manifest.md        # Phase 1 — the hunters.json contract
├── checklists/
│   └── requirements.md            # Spec quality checklist
└── tasks.md                       # Phase 2 output (/speckit-tasks — not created here)
```

### Source Code (repository root)

```text
pixel-art-toolkit/examples/wizard-hunt/
└── make_hunters.py                # emits the sheet; gains the manifest and the emissive split

wizard-hunt-online/
├── public/
│   ├── client.js                  # sheetRow() dies; manifest lookup and the glow pass
│   └── assets/
│       ├── hunters.png            # base layer (existing)
│       ├── hunters_glow.png       # emissive layer (new)
│       └── hunters.json           # manifest (new)
├── src/
│   └── classes.js                 # itemIndex() stays; the order comment loses its teeth
├── tools/
│   └── build-sandbox.js           # inlines the manifest and the second sheet
└── test/
    └── wiring.test.js             # PNG-header test replaced by manifest agreement
```

**Structure Decision**: The existing layout is kept exactly. This feature
changes five files and adds two assets; it introduces no directory, no
module boundary and no layer. The generator stays the only thing that knows
sheet geometry, which is precisely the property being formalised — the
manifest is that knowledge written down instead of re-derived by every
consumer.

## Complexity Tracking

The Constitution Check has no ratified gates to violate, but two design
decisions cost something and should not be adopted silently:

| Decision | Why needed | Simpler alternative rejected because |
|---|---|---|
| A second sprite sheet for emissive pixels | With no shaders, "unshaded" can only mean "drawn after the thing that darkens", and that needs the glow pixels separable from the body | Storing emissive in the alpha channel halves the assets but forces per-pixel work in JS or an offscreen canvas — the cost this design exists to avoid. **Fallback if size disappoints (R6): widen the base sheet by a frame column instead of shipping a second image.** |
| A JSON manifest fetched at boot rather than a `<script>` global | The Node tests are the main reason the manifest exists, and they must read it without `eval` | A `.js` file assigning a global is synchronous and identical in both delivery modes — genuinely nicer for the client, and rejected only because it makes the tests worse |

**Not carried**: SS14's entity-component architecture, its shader pipeline,
and 8-direction sprites. The manifest *declares* direction count so eight
would not require touching the client, but nothing draws eight today and
speculatively generating them would triple the sheet for no player.

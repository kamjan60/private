# tarot-reveal

Fusion card-reveal generator for **The Dread Deck** pilot. Separate module
from `apps/resolve-agent` (that one edits gameplay footage; this one builds
Fusion compositions for the 22 Major Arcana reveal cards). Shares the same
Resolve connection code (`grimcader.resolve_conn.connect()`).

## Requirements

- DaVinci Resolve **Studio** running, project open, External Scripting =
  Local (Preferences > System > General).
- Fusion page open with an active comp (drop an empty Fusion Clip/Title on
  `AI Jester Timeline` first) — `fusion.GetCurrentComp()` needs a target.
- Python 3.6–3.11 (Resolve scripting API constraint, same as resolve-agent).
- Source images: `D:\OBS Store movies\Images\Tarot\Cards-png\` — 22 major
  arcana (`00-TheFool.png` … `21-TheWorld.png`) + `CardBacks.png` (rewers).

## Files

```
data/cards.json          number/filename/card_name/relic_text/curse_text
                          — fill relic_text + curse_text per card before batch run
scripts/
  tarot_lib/
    cards_io.py           loads cards.json, resolves image paths
    fusion_conn.py         Resolve/Fusion connection + dump_inputs() debug helper
    template_build.py     the CardReveal node-graph rig (single source of truth)
  build_template.py       builds ONE preview rig in the current comp — run
                           this first, eyeball the flip, patch template_build.py
                           CONFIG if any tool/input ID is wrong for your version
  generate_reveals.py     batch: all 22 cards -> fusion/generated/*.comp
  build_ceremony.py       STUB — Phase 2, assembles Victory/Death Draw onto
                           the timeline. Not implemented.
fusion/generated/          batch output (.comp per card), gitignored candidate
```

## Rig

One rigid "card" body, front+back image planes glued back-to-back in 3D —
only one face ever points at the camera:

- `Transform3D_Flip.Rotation.Y` — keyframed 180 -> 0. The only animated value.
  Same for every card, every ceremony.
- `Transform3D_Orient.Rotation.Z` — static, set per ceremony: `0` = Upright
  (relic), `180` = Reversed (curse). Not baked into cards.json — the same
  card can be relic in one draw and curse in another.
- 3 `TextPlus` 2D overlays composited after the 3D render: card name, status
  (RELIC/CURSE), effect text.

## Status

Phase 1 (`build_template.py`) — **verified live** against Resolve Studio +
Fusion (2026-07-26): rig builds cleanly in a Fusion Composition comp,
including the Y-flip keyframes and the MaterialInput texture wiring
(ImagePlane3D has no plain "Image" input — the 2D source connects into
`MaterialInput` and Fusion auto-wraps it; camera connects into Renderer3D's
`CameraSelector`). `generate_reveals.py` (the 22-card batch loop) uses the
same verified `template_build.py` — not yet run end-to-end for all 22, only
the single-card preview.

Two environment fixes were needed and are now permanent in the shared
`apps/resolve-agent/grimcader/resolve_conn.py`:
- `os.add_dll_directory()` for `fusionscript.dll`'s own dependencies (Python
  3.8+ dropped implicit PATH-based DLL search).
- Default `RESOLVE_SCRIPT_LIB` corrected to this machine's actual install:
  `D:\Da Vinci Resolve\Blackmagic Design\DaVinci Resolve\fusionscript.dll`
  (not the stock `C:\Program Files\...` path).
Python runtime: system Python 3.11 was missing (old `.work/whisper-env`
pointed at a dead user profile) — reinstalled via
`winget install Python.Python.3.11`. Real interpreter now at
`C:\Users\Jester\AppData\Local\Programs\Python\Python311\python.exe` (no
`python`/`py` launcher on PATH — call this full path directly).

Fusion Composition placed as a **generator on its own video track** — not an
Adjustment Clip (adjustment clips force a `MediaIn1` passthrough of the
tracks below, wrong model for a self-contained generated card asset).

Phase 2 (`build_ceremony.py`) — not started, waiting on the full 22-card
batch being verified.

## Next steps

1. ~~Fill `relic_text` / `curse_text` for all 22 cards~~ — done, sourced from
   `The_Dread_Deck_Full_Rules_v5_EN.pdf`. Rulebook's recommended **pilot deck
   is 16 cards** (excludes Wheel, Death, Devil, Tower, Judgement) — decide
   whether the draw pool for this episode should be limited to those 16.
2. ~~`build_template.py` single-card preview~~ — done, verified live.
3. Eyeball the built rig in the Fusion viewer (flip timing, text legibility,
   card scale/position) and say if anything needs adjusting before batch.
4. `<python path> scripts/generate_reveals.py` — batch all 22 to
   `fusion/generated/*.comp`.
5. Only then: design/implement `build_ceremony.py` (Victory/Death assembly).

Run scripts with the full interpreter path (no `python` on PATH):
```
C:\Users\Jester\AppData\Local\Programs\Python\Python311\python.exe scripts\generate_reveals.py
```

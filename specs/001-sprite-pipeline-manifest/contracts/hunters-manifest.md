# Contract — `hunters.json`

**Producer**: `tools/pixel-art-toolkit/examples/wizard-hunt/make_hunters.py`
**Consumers**: `apps/wizard-hunt-online/` — `public/client.js`,
`test/wiring.test.js`, `tools/build-sandbox.js` (the app's own tools/, not the
repo-root one)
**Location**: `apps/wizard-hunt-online/public/assets/hunters.json`

This is the only interface this feature exposes. It replaces an implicit
contract — the row formula `(class * 3 + item) * 4 + direction` — that was
duplicated across three files in two languages and enforced by nothing.

---

## Shape

```json
{
  "version": 1,
  "size": { "x": 32, "y": 32 },
  "sheets": {
    "base": "hunters.png",
    "emissive": "hunters_glow.png"
  },
  "directions": ["down", "left", "right", "up"],
  "states": [
    { "name": "Strażnik/tarcza",     "row": 0,  "directions": 4, "frames": 2 },
    { "name": "Strażnik/kamizelki",  "row": 4,  "directions": 4, "frames": 2 },
    { "name": "Strażnik/kotwica",    "row": 8,  "directions": 4, "frames": 2 },
    { "name": "Zwiadowca/dron",      "row": 12, "directions": 4, "frames": 2 }
  ]
}
```

`states` above is truncated for illustration; the real file lists all 24.

---

## Guarantees the producer makes

1. `states` is non-empty, names are unique, and every name is
   `"<class>/<itemId>"` using the exact strings from `src/classes.js`.
2. Rows are contiguous from 0 and cover the image exactly: the sum of every
   state's `directions`, times `size.y`, equals the sheet height.
3. Every sheet named in `sheets` exists and has identical dimensions.
4. The file is UTF-8 JSON with no trailing content. Class names carry
   diacritics (`Strażnik`, `Zwiadowca`) and are not escaped or transliterated.
5. Regenerating from unchanged sources produces a byte-identical file. The
   generator seeds deterministically, and a manifest that churned would make
   every diff unreadable.

## Guarantees the consumers make

1. **No consumer computes a row.** The only permitted lookup is by name,
   then `row + dir`. A regression here is the entire bug this feature exists
   to kill, so it is worth a grep in review: `* 3`, `* 4`, `sheetRow`.
2. The client reads `size`, `directions` and `frames` rather than assuming
   32, 4 and 2.
3. An unknown `version` is refused at boot, not coerced.
4. An unknown state name resolves to `states[0]` and warns once per session.

---

## Delivery

Two paths, matching how images already reach the client:

| Mode | Source | Notes |
|---|---|---|
| Served | `fetch("assets/hunters.json")` at boot | Must complete before the first frame. |
| Artifact | `window.__MANIFEST`, inlined by `build-sandbox.js` | A strict CSP forbids fetching anything; the manifest goes in as literal JSON, not base64. |

The client prefers `window.__MANIFEST` when present, exactly as it already
prefers `window.__ASSETS` over `ASSETS` for images.

---

## Failure behaviour

| Condition | Required behaviour |
|---|---|
| Manifest absent, unfetchable, or unparseable | Refuse to start. Message names the file and the mode. Never render a frame. |
| `version` not understood | Same as above, message names both versions. |
| State named but outside the image | Test failure at `npm test`, message names the state. |
| Image rows no state claims | Test failure, message gives the first unclaimed row. |
| `(cls, it)` with no matching state | Draw `states[0]`, `console.warn` once per session, keep playing. |

The asymmetry is deliberate: the first four are developer errors and belong
before the game runs; the last happens to a player mid-round, where dropping
them out of a thirty-minute session is worse than a wrong hat.

---

## Compatibility

`version` is bumped only when an existing field changes meaning. Adding an
optional field (`delays`, a new entry in `sheets`, a stage-3 `tint` block)
does not bump it — consumers ignore what they do not know, which is what
makes stages 3 to 5 additive rather than a second migration.

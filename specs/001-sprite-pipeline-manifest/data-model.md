# Phase 1 — Data Model

**Feature**: Manifest sprite'ów i warstwa nieoświetlana
**Date**: 2026-08-02

The feature adds no game state. Everything below is asset description: it is
produced by the generator, consumed by the client and the tests, and never
travels over the socket. The one wire change is that `it` (apparent item
index) already exists and stays.

---

## Manifest

The single source of truth for where anything is in the sheet. Written by
`make_hunters.py`, read by `client.js` and `test/wiring.test.js`.

| Field | Type | Rule |
|---|---|---|
| `version` | integer | 1. Bumped only on a breaking shape change; the client refuses a version it does not know. |
| `size` | `{x, y}` | Frame size in pixels. Currently 32×32. The client must read it rather than assume it. |
| `sheets` | `{base, emissive}` | Filenames relative to the asset directory. `emissive` may be absent — a manifest without one is valid and means no glow pass. |
| `directions` | string[] | Order of directions within a state, e.g. `["down","left","right","up"]`. The index into this array is what the server's `dir` means. |
| `states` | State[] | Every drawable state. Order within the array carries no meaning; the first entry is the documented fallback. |

**Invariants**

- `states` is non-empty.
- State names are unique.
- `directions.length` ≥ 1 and every state's `directions` ≤ it.
- Every row implied by a state exists inside the PNG: for the last state,
  `(row + directions) * size.y` ≤ image height.
- Rows are contiguous and every row of the image is claimed. A gap means a
  stale manifest, and it fails the tests rather than silently wasting pixels.

---

## State

One named, drawable thing. Today: a class wearing one of its three items.

| Field | Type | Rule |
|---|---|---|
| `name` | string | `"<class>/<itemId>"`, e.g. `"Chirurg/stabilizator"`. Both halves are stable identifiers that already exist in `src/classes.js`. Never a position. |
| `row` | integer | First sheet row for this state. An internal detail of the manifest: nothing outside it may compute this. |
| `directions` | integer | How many consecutive rows from `row` this state occupies. 4 today. |
| `frames` | integer | Frames across, i.e. sheet columns used. 2 today. |
| `delays` | number[] | Optional, milliseconds per frame. Absent means the client keeps its current step timing. Declared so a third frame does not require touching the client. |

**Resolution**

```
row_for(name, dir) = states[name].row + clamp(dir, 0, states[name].directions - 1)
column(step)       = step * size.x
```

The `clamp` is not decoration: a state with fewer directions than the world
has must degrade to its first, not read a neighbour's row.

---

## Layer

Why a sprite is drawn in more than one pass. Two today, a third in stage 3.

| Layer | Sheet | Drawn | Obeys darkness | Obeys transparency |
|---|---|---|---|---|
| `base` | `hunters.png` | with the actors, under the fog | yes | yes |
| `emissive` | `hunters_glow.png` | after the fog, in world space | **no** | **yes** |
| `tint` (stage 3) | greyscale coat | with the actors | yes | yes |

The two columns on the right are the whole feature. `emissive` exists to say
no in exactly one of them, and the constraint that fails silently is the
other one: an emissive layer that also ignores transparency undoes Cień.

**Suppression rules**

- A corpse draws `base` only. Dead kit does not glow.
- An actor the viewer cannot see is absent from the snapshot, so no rule is
  needed for the fog — the culling already happened on the server.

---

## Apparent class and apparent item

Unchanged by this feature, restated because the state name is built from
them and getting it wrong leaks the mage.

- `cls` on the wire is `apparentClass(p)` — the disguise if one is up.
- `it` on the wire is `apparentItem(p)` — the disguised class's item list,
  falling back to index 0 when the real item is not in it.
- The client turns `(cls, it)` into a state name. **The mage's real class must
  never be an input to that name.** It is not sent, so this holds by
  construction; it is written down because a future "draw your own body from
  your own truth" shortcut would break it.

---

## What is not in the model

- No new socket fields. `cls`, `it`, `dir`, `step` already carry everything.
- No persistence. The manifest is a build artifact, regenerated from source.
- No per-player state. Two players seeing the same actor resolve the same
  state name.

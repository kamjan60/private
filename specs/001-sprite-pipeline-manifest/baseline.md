# Baseline — measured on unmodified HEAD

Captured before any implementation, because SC-006, SC-007 and SC-008 are
comparisons and every one of these numbers stops being obtainable once the
work starts.

**Commit**: `c2dbf71` (tasks committed, no implementation yet)
**Date**: 2026-08-02

| Measurement | Value | Criterion |
|---|---|---|
| `sandbox/artifact.html` | 244 394 B (238.7 KiB) | SC-007 — growth must stay ≤ 5 KB for the manifest; the emissive sheet is **not** covered by that budget (research R6) |
| `sandbox/sandbox.html` | 244 564 B | — |
| `public/assets/hunters.png` | 22 892 B | reference for judging the emissive sheet's size |
| `npm test` wall clock | 11.865 s | SC-008 — must not get slower |
| Full-light screenshot | `scratchpad/baseline-full-light.png`, 666.7 KiB | SC-006 — the change must be invisible at full light |

The screenshot is the one that cannot be recreated. Everything else can be
re-measured by checking out the commit above; a screenshot of the old
renderer cannot be taken once the renderer has changed, which is why T001
came first.

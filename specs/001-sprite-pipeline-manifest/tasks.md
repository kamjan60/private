---

description: "Task list for the sprite manifest and unshaded layer"
---

# Tasks: Manifest sprite'ów i warstwa nieoświetlana

**Input**: Design documents from `/specs/001-sprite-pipeline-manifest/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/, quickstart.md

**Tests**: Included, and not as a preference. The spec asks for them directly
— FR-005 (mismatch detected both ways), FR-009 (replace the header test),
SC-002 (failure names the state) — and the defect this feature exists to kill
is one that no test currently catches. Tests are the deliverable here as much
as the renderer is.

**Organization**: By user story. US1 and US2 are both P1 and independently
shippable; either can go out without the other.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to
- Exact file paths in every description

## Path Conventions

Paths are repository-relative. Two trees are involved:

- `pixel-art-toolkit/examples/wizard-hunt/` — the Python generator
- `wizard-hunt-online/` — server, client, tests, artifact build

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Capture the "before" numbers. Every one of these becomes
unmeasurable the moment implementation starts, and three success criteria
(SC-006, SC-007, SC-008) are comparisons against them.

- [ ] T001 Capture the full-light baseline screenshot by running `node test/browser.js` from `wizard-hunt-online/` on the current HEAD and copying the output PNG to the scratchpad as `baseline-full-light.png` — SC-006 compares against this and it cannot be recreated later
- [ ] T002 [P] Record the baseline artifact size with `node tools/build-sandbox.js && ls -l sandbox/artifact.html` in `wizard-hunt-online/`, noting the byte count for the SC-007 budget
- [ ] T003 [P] Record the baseline test duration with `time npm test` in `wizard-hunt-online/` for SC-008

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: One seam that both stories draw through. Today `client.js` computes
sheet rows at two call sites; US1 replaces how a row is found and US2 adds a
second pass over the same rows. Funnelling both through one resolver and one
draw helper first means each story then changes one function instead of hunting
call sites.

**⚠️ CRITICAL**: No user story work begins until this is done.

- [ ] T004 Extract a single sprite-draw helper in `wizard-hunt-online/public/client.js` that every sheet blit goes through, taking (class, item, dir, step, x, y, alpha) and internally calling the existing `sheetRow`; convert `drawActor` and the spell-wheel portrait to use it, changing no visible output
- [ ] T005 Verify T004 changed nothing visible: run `node test/browser.js` in `wizard-hunt-online/` and diff the screenshot against `baseline-full-light.png` from T001 — any difference here is a bug introduced by the refactor, not by the feature

**Checkpoint**: One place decides where a sprite lives. Both stories can start.

---

## Phase 3: User Story 1 - Sylwetka zawsze zgadza się z osobą (Priority: P1) 🎯 MVP

**Goal**: Nothing outside the manifest computes a sheet row. Reordering
classes or items becomes invisible to the client, and a mismatch fails the
test suite by name instead of drawing somebody else's body.

**Independent Test**: Swap two items in one class in `src/classes.js`, run
`npm test` — it must fail naming the state. Regenerate the sheet, run again —
it must pass with zero edits to `client.js`.

### Tests for User Story 1

> Write these first. They must fail against the current arithmetic-indexed
> sheet, because that is the proof they test something the old header check
> did not.

- [ ] T006 [P] [US1] Add a manifest/table agreement test in `wizard-hunt-online/test/wiring.test.js`: every `class/itemId` pair from `classes.js` has a state in `public/assets/hunters.json`, and every state maps back to a real pair — the failure message names the offending state (SC-002)
- [ ] T007 [P] [US1] Add a manifest/sheet geometry test in `wizard-hunt-online/test/wiring.test.js`: rows are contiguous from 0, and the sum of every state's `directions` times `size.y` equals the PNG height exactly — a gap fails and names the first unclaimed row (FR-005)
- [ ] T008 [US1] Add a manifest self-consistency test in `wizard-hunt-online/test/wiring.test.js`: `version` is 1, state names are unique, `directions` is non-empty, and every sheet named in `sheets` exists on disk

### Implementation for User Story 1

- [ ] T009 [US1] Build the state table in `pixel-art-toolkit/examples/wizard-hunt/make_hunters.py` from the existing `CLASSES` list, naming each state `"<class>/<itemId>"` and recording its first row, direction count and frame count as the sheet is written
- [ ] T010 [US1] Emit `hunters.json` from `make_hunters.py` per `contracts/hunters-manifest.md` — version, size, sheets, directions, states — with sorted keys and a stable field order so regenerating an unchanged sheet produces a byte-identical file (contract guarantee 5)
- [ ] T011 [US1] Copy the generated `hunters.png` and `hunters.json` into `wizard-hunt-online/public/assets/` and confirm T006–T008 now pass
- [ ] T012 [US1] Add a manifest loader in `wizard-hunt-online/public/client.js` that prefers `window.__MANIFEST` and otherwise fetches `assets/hunters.json`, refusing an unknown `version`, and gate the first frame on it — matching how `window.__ASSETS` is already preferred over `ASSETS` for images
- [ ] T013 [US1] Make a missing or unparseable manifest a hard stop in `wizard-hunt-online/public/client.js`: show a message naming the file, and draw no frame at all rather than a frame of wrong bodies followed by an error (FR-008)
- [ ] T014 [US1] Replace the body of the T004 resolver in `wizard-hunt-online/public/client.js` with a name lookup — `states[cls + "/" + itemId].row + clamp(dir, 0, directions - 1)` — reading `size`, `directions` and `frames` from the manifest instead of assuming 32, 4 and 2
- [ ] T015 [US1] Map the wire's `it` index back to an item id in `wizard-hunt-online/public/client.js` using `DEF.classes`, so the state name is built from identifiers rather than positions (FR-002)
- [ ] T016 [US1] Implement the unknown-state fallback in `wizard-hunt-online/public/client.js`: draw `states[0]` and `console.warn` exactly once per session, never per frame (FR-004)
- [ ] T017 [US1] Delete `sheetRow` and the `(class * 3 + item) * 4 + dir` arithmetic from `wizard-hunt-online/public/client.js`, then grep the repository for `* 3`, `* 4` and `sheetRow` to confirm no consumer computes a row (contract, consumer guarantee 1)
- [ ] T018 [US1] Remove the superseded PNG-header test `the sprite sheet has a row for every class and every item` from `wizard-hunt-online/test/wiring.test.js` (FR-009)
- [ ] T019 [US1] Inline the manifest as literal JSON into `window.__MANIFEST` in `wizard-hunt-online/tools/build-sandbox.js` — as text, not base64 — and confirm no `fetch` remains on the artifact path
- [ ] T020 [US1] Run the reorder proof from `quickstart.md` step 2a end to end: swap two of Technik's items, confirm the test fails by name, regenerate, confirm it passes with no client edit, then restore

**Checkpoint**: US1 is complete and shippable. The class-order footgun is gone
and the README's warning comment is now an enforced contract.

---

## Phase 4: User Story 2 - Ciemność ma punkty światła (Priority: P1)

**Goal**: A lamp at the edge of vision stays lit while the body carrying it
fades into the fog.

**Independent Test**: Stand so another hunter is at the edge of your vision.
Their chest light, visor or lamp reads at least 3× brighter than the body
pixels beside it, while the body is visibly fogged.

**Note on the premise**: research.md R1 found the spec was wrong about the
cause. The act only shrinks the vision radius and the compartment wash never
touches actors — the fog is the only thing that dims a hunter. These tasks
target the fog. The doused-actor gap is out of scope and recorded as FR-011a.

### Tests for User Story 2

- [ ] T021 [P] [US2] Add a brightness assertion to `wizard-hunt-online/test/browser.js`: sample canvas pixels at an actor near the fog's edge via `page.evaluate` and assert an emissive pixel is at least 3× the luminance of an adjacent body pixel (SC-004)
- [ ] T022 [P] [US2] Add an invisibility assertion to `wizard-hunt-online/test/browser.js`: with Cień up, assert no pixel of the caster's own sprite exceeds the luminance of the rest of it (SC-005) — this is the failure that is silent, so it gets a test rather than a look

### Implementation for User Story 2

- [ ] T023 [US2] Split emissive pixels into a second image in `pixel-art-toolkit/examples/wizard-hunt/make_hunters.py`: write glow colours to `hunters_glow.png` in the identical layout, transparent everywhere else, leaving the base sheet otherwise unchanged
- [ ] T024 [US2] Add `sheets.emissive` to the manifest emitted by `make_hunters.py`, keeping it optional per the contract so a manifest without one stays valid
- [ ] T025 [US2] Load the emissive sheet in `wizard-hunt-online/public/client.js` through the existing `ASSETS` / `window.__ASSETS` mechanism, reading its filename from the manifest rather than hardcoding it
- [ ] T026 [US2] Collect glow draws during the actor pass in `wizard-hunt-online/public/client.js` — position, row, step and the actor's own alpha — instead of drawing them inline
- [ ] T027 [US2] Draw the collected glow sprites after the fog fill in `wizard-hunt-online/public/client.js`, restoring the world transform for the pass and multiplying by each actor's recorded alpha so invisibility still applies (FR-011, FR-012)
- [ ] T028 [US2] Suppress the emissive layer for corpses in `wizard-hunt-online/public/client.js` — dead kit does not glow (FR-013)
- [ ] T029 [US2] Apply the same glow rule to the base camera feeds in `wizard-hunt-online/public/client.js`, so the base and the field do not render two different games (FR-015)
- [ ] T030 [US2] Decide the composite mode by looking: screenshot the glow pass with `source-over` and with `globalCompositeOperation = "lighter"` over both a doused compartment and a lit one, then pick — research.md R2 left this open deliberately, and `source-over` wins any tie
- [ ] T031 [US2] Inline `hunters_glow.png` in `wizard-hunt-online/tools/build-sandbox.js` and measure the artifact's growth against the T002 baseline; if the second sheet blows the budget, take R6's fallback and widen the base sheet by a frame column instead of shipping a second image
- [ ] T032 [US2] Confirm SC-006 by diffing a full-light screenshot against `baseline-full-light.png` from T001 — at full light the change must be invisible

**Checkpoint**: US2 is complete and shippable. Both P1 stories done.

---

## Phase 5: Polish & Cross-Cutting Concerns

- [ ] T033 [P] Update the sprite-sheet section of `wizard-hunt-online/README.md`: the coupling is now a manifest and a test, not a comment and a hope
- [ ] T034 [P] Update the ORDER MATTERS header comment in `wizard-hunt-online/src/classes.js` — reordering is now safe after regeneration, and the comment should say what is actually true
- [ ] T035 [P] Note the manifest and the emissive layer in `pixel-art-toolkit/examples/wizard-hunt/make_hunters.py`'s module docstring, replacing the row-formula description
- [ ] T036 Record the emissive-layer rule in `.claude/skills/fantasy-pixel-art/SKILL.md` — a lit fitting drawn under the darkening pass is a lit fitting that goes out, which is the same class of mistake as drawing the background dim instead of dimming it
- [ ] T037 Run `quickstart.md` end to end, including the deliberate-failure steps 2a, 2b and 3, and confirm every SC in its Done-when table
- [ ] T038 Confirm SC-008 with `time npm test` against the T003 baseline

---

## Deferred (specified, not planned)

US3 (colour bands), US4 (in-hand kit) and US5 (lying silhouette) are
specified in `spec.md` with requirements FR-016 through FR-020, and are
deliberately outside this plan. They are additive: the contract's
compatibility rule means each can land later by adding optional manifest
fields without a version bump or a second migration.

No task IDs are issued for them here. Issuing tasks for work nobody has
scheduled is how a task list stops being a plan and becomes a wish.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies. Must happen on unmodified HEAD — its
  entire purpose is capturing "before".
- **Foundational (Phase 2)**: Depends on Setup. Blocks both stories.
- **US1 (Phase 3)** and **US2 (Phase 4)**: Both depend only on Foundational.
- **Polish (Phase 5)**: Depends on whichever stories shipped.

### User Story Dependencies

- **US1 (P1)**: Independent. Ships alone.
- **US2 (P1)**: Independent. Ships alone — it draws through the T004 resolver
  and does not care whether that resolver reads a manifest or computes a row.
  T024 touches the manifest, so if US2 ships first, that task moves into US1.

### Within Each Story

- Tests before implementation. T006–T008 must fail against the current sheet;
  T021–T022 must fail against the current fog pass. A test that passes before
  the work is a test measuring nothing.
- Generator before client: the client cannot read a manifest that does not
  exist yet (T009–T011 before T012–T017).
- The artifact build comes last within each story, because it packages
  whatever the story produced.

### Parallel Opportunities

- T002, T003 in parallel (different measurements, both read-only).
- T006, T007 in parallel — same file, so only with care; prefer sequential if
  one hand is doing both.
- T021, T022 in parallel with the whole of US1: different files, different story.
- T033, T034, T035 in parallel — three different files.
- **US1 and US2 in parallel** once Phase 2 lands, if two people are on it.
  They collide in exactly one place: T019 and T031 both edit
  `tools/build-sandbox.js`.

---

## Parallel Example: US1 tests

```bash
# Both must FAIL before any implementation lands:
Task: "Manifest/table agreement test in wizard-hunt-online/test/wiring.test.js"
Task: "Manifest/sheet geometry test in wizard-hunt-online/test/wiring.test.js"
```

## Parallel Example: US2 alongside US1

```bash
# Different files, different stories, no shared state:
Task: "Brightness assertion in wizard-hunt-online/test/browser.js"
Task: "Emissive split in pixel-art-toolkit/examples/wizard-hunt/make_hunters.py"
```

---

## Implementation Strategy

### MVP (US1 only)

1. Phase 1 — capture baselines on unmodified HEAD.
2. Phase 2 — the draw seam.
3. Phase 3 — the manifest.
4. **Stop and validate**: quickstart step 2a. Reorder must be invisible.
5. Ship. The footgun is gone and nothing else changed.

### Incremental Delivery

1. Setup + Foundational → one place decides where a sprite lives.
2. US1 → reordering is safe, mismatch fails by name → ship.
3. US2 → the dark has points of light in it → ship.
4. Polish → docs tell the truth, quickstart passes end to end.

### Notes

- Commit per task or per logical group.
- T001's screenshot is load-bearing for SC-006 and cannot be recreated once
  implementation starts. Do it first or lose the criterion.
- T012 introduces asynchrony into boot for the first time. The served path
  fetches; the artifact path does not. Both must be exercised — a manifest
  that works served and breaks offline fails the one surface the owner
  actually plays on.
- The one silent failure in this feature is FR-012. T022 exists because
  looking at a screenshot will not catch it reliably, and the consequence is
  the mage's own invisibility spell lighting him up.

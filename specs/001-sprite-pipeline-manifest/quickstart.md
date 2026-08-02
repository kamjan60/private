# Quickstart — validating the sprite manifest and the unshaded layer

**Feature**: Manifest sprite'ów i warstwa nieoświetlana
**Date**: 2026-08-02

Everything below runs from `wizard-hunt-online/` unless stated. No build
step, no new dependencies.

## Prerequisites

```bash
cd wizard-hunt-online
npm install                     # ws only
python3 -c "import PIL; print(PIL.__version__)"
```

---

## 1. Regenerate the art and the manifest

```bash
python3 ../pixel-art-toolkit/examples/wizard-hunt/make_hunters.py
cp ../pixel-art-toolkit/examples/wizard-hunt/hunters.png       public/assets/
cp ../pixel-art-toolkit/examples/wizard-hunt/hunters_glow.png  public/assets/
cp ../pixel-art-toolkit/examples/wizard-hunt/hunters.json      public/assets/
```

**Expect**: 24 states listed, every name `"<class>/<itemId>"`.

```bash
python3 -c "import json;m=json.load(open('public/assets/hunters.json'));print(len(m['states']),m['states'][0]['name'])"
```

**Determinism** (contract guarantee 5) — running it twice changes nothing:

```bash
md5sum public/assets/hunters.json && python3 ../pixel-art-toolkit/examples/wizard-hunt/make_hunters.py && md5sum ../pixel-art-toolkit/examples/wizard-hunt/hunters.json
```

---

## 2. The test that replaces the PNG-header check

```bash
npm test
```

**Expect**: the manifest/table agreement test passes, and the old
`the sprite sheet has a row for every class and every item` is gone.

### 2a. A reorder is now invisible, which is the point

Written first as "swap two items, watch the test fail". That expectation was
wrong, and wrong in the feature's favour: **a reorder is no longer a defect**,
so there is nothing for a test to catch. Names bind, so the sprite stays
correct even without regenerating the sheet.

```bash
# in src/classes.js, swap "generator" and "rygiel" in Technik's items
npm test          # expect: PASS. Nothing broke, because nothing is indexed
```

Then show what the old code would have done with the same edit — this is
SC-001, and the clearest single demonstration of the whole feature:

```bash
node -e '
const {itemsOf,CLASS_NAMES}=require("./src/classes");
const m=JSON.parse(require("fs").readFileSync("public/assets/hunters.json","utf8"));
const cls="Technik", it=0, id=itemsOf(cls)[it].id;
console.log("carried:", id);
console.log("by name :", m.states.find(s=>s.name===cls+"/"+id).name);
console.log("by index:", m.states.find(s=>s.row===(CLASS_NAMES.indexOf(cls)*3+it)*4).name);
'
# expect:  carried: rygiel / by name: Technik/rygiel / by index: Technik/generator
git checkout src/classes.js
```

### 2b. The failure that *should* be loud: a renamed or added item

```bash
# in src/classes.js, rename "kamera" to "kamera-v2"
npm test
# expect: no sprite state "Technik/kamera-v2" -- rerun make_hunters.py
git checkout src/classes.js
```

### 2c. And the reverse direction, a stale manifest

```bash
# hand-edit public/assets/hunters.json: delete the last state
npm test          # expect: failure naming the first unclaimed row
```

---

## 3. Boot behaviour

```bash
mv public/assets/hunters.json /tmp/ && npm start
```

Open the game. **Expect**: it refuses to start with a message naming
`hunters.json`, and **no frame is drawn** — not a frame of wrong bodies
followed by an error. Restore it afterwards.

---

## 4. The unshaded layer, looked at rather than reasoned about

```bash
node test/browser.js
```

**Expect**: all existing assertions still pass, plus the new brightness one.
The screenshot lands in the scratchpad path the harness prints.

Then look at it, because this is art and the rule is that step 3 cannot be
replaced by reasoning:

- **Near the player, full light** — SC-006: identical to before. Compare
  against a screenshot taken on `main`. Any visible difference here is a bug,
  not an improvement.
- **At the edge of vision** — SC-004: the chest light, the Strażnik's visor
  and the Technik's lamp stay bright while the body fades into the fog. The
  ratio to the adjacent body pixels must be at least 3×.
- **Under Cień** — SC-005: cast it, look at your own body. Nothing on the
  sprite may be brighter than anything else on it. This is the one that fails
  silently, so check it deliberately rather than trusting the code.
- **A corpse in a dark room** — no glow at all.

### Deciding the composite mode

R2 left `globalCompositeOperation = "lighter"` open on purpose. Take both
screenshots and pick:

- over the dark plating of a doused room — `lighter` blooms, and probably wins
- over a `lit` compartment's warm wash — `lighter` may blow out to white

If they disagree, `source-over` is the safe answer and the bloom is not worth
a blown-out lamp.

---

## 5. The single-file build

```bash
node tools/build-sandbox.js
ls -l sandbox/artifact.html
```

**Expect** (SC-007): the manifest is inlined as literal JSON in
`window.__MANIFEST`, no `fetch` remains on the artifact path, and growth
over the previous 239 KB is measured and reported.

R6 flagged this: the 5 KB budget covers the manifest, **not** the second
sheet. Measure `hunters_glow.png` before assuming it fits. If it does not,
the fallback is a wider base sheet rather than a second image.

Open `sandbox/artifact.html` with no network and confirm the hunters render.

---

## Done when

| Criterion | Checked by |
|---|---|
| SC-001 reorder is invisible to the client | step 2a |
| SC-002 mismatch caught both ways, state named | steps 2a, 2b |
| SC-003 a fourth item touches one table | add one, run step 1 + `npm test` |
| SC-004 glow ≥ 3× adjacent body at the fog's edge | step 4 |
| SC-005 nothing brighter under Cień | step 4 |
| SC-006 full light is unchanged | step 4, against a `main` screenshot |
| SC-007 artifact still offline, growth measured | step 5 |
| SC-008 test suite no slower | `time npm test`, before and after |

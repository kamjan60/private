"use strict";
/**
 * Static wiring checks: things that are cheap to get wrong in a table and
 * expensive to discover mid-round.
 */

const assert = require("assert");
const fs = require("fs");
const path = require("path");

const { SPELLS } = require("../src/spells");
const { CLASS_NAMES, CLASSES, itemsOf, itemIndex } = require("../src/classes");
const { COMPARTMENTS } = require("../src/map");
const { MAX_PLAYERS, ACT_VISION, ACTS } = require("../src/rules");

let passed = 0;
function test(name, fn) {
  try { fn(); passed++; console.log("  ok   " + name); }
  catch (e) { console.log("  FAIL " + name + "\n       " + e.message); process.exitCode = 1; }
}

const read = (f) => fs.readFileSync(path.join(__dirname, "..", "src", f), "utf8");

test("every module loads", () => {
  for (const m of ["rules", "classes", "spells", "map", "evidence", "round",
    "tribunal", "base", "room", "effects", "actions", "snapshot"]) {
    require("../src/" + m);
  }
});

test("every spell has an effect handler", () => {
  const src = read("effects.js");
  const missing = SPELLS.filter((s) => !src.includes(`case "${s.effect}"`));
  assert.deepStrictEqual(missing.map((s) => s.id), []);
});

test("every active item is spendable somewhere", () => {
  const src = read("actions.js");
  const gaps = [];
  for (const n of CLASS_NAMES) {
    for (const it of itemsOf(n)) {
      if (it.kind !== "active") continue;
      // items marked viaChannel are spent by holding, not by a button
      if (it.viaChannel) { assert.ok(src.includes(it.id), `${it.id} claims a channel but has none`); continue; }
      if (!src.includes(`case "${it.id}"`)) gaps.push(`${n}/${it.id}`);
    }
  }
  assert.deepStrictEqual(gaps, []);
});

test("there is exactly one class per seat", () => {
  assert.strictEqual(CLASS_NAMES.length, MAX_PLAYERS,
    "classes are unique per round, so the table has to seat the maximum exactly");
});

test("every class declares stats and three items", () => {
  for (const n of CLASS_NAMES) {
    const c = CLASSES[n];
    for (const k of ["vision", "taser", "hp", "speed", "glow", "blurb"]) {
      assert.ok(c[k] !== undefined, `${n} is missing ${k}`);
    }
    assert.strictEqual(c.items.length, 3, `${n} must offer exactly three items`);
    const ids = c.items.map((i) => i.id);
    assert.strictEqual(new Set(ids).size, 3, `${n} has a duplicate item id`);
    for (const it of c.items) {
      assert.ok(["passive", "active", "cooldown"].includes(it.kind), `${n}/${it.id} bad kind`);
      if (it.kind === "active") assert.ok(it.charges > 0, `${n}/${it.id} needs charges`);
      if (it.kind === "cooldown") assert.ok(it.cooldown > 0, `${n}/${it.id} needs a cooldown`);
    }
  }
});

test("item ids are unique across all classes", () => {
  const all = CLASS_NAMES.flatMap((n) => itemsOf(n).map((i) => i.id));
  const dupes = all.filter((id, i) => all.indexOf(id) !== i);
  assert.deepStrictEqual(dupes, [], "the client keys items by id alone");
});

test("spell ids are unique", () => {
  const ids = SPELLS.map((s) => s.id);
  assert.strictEqual(new Set(ids).size, ids.length);
});

test("every spell declares a school, charges, cast time and target", () => {
  for (const s of SPELLS) {
    for (const k of ["school", "charges", "castMs", "target", "effect", "desc"]) {
      assert.ok(s[k] !== undefined, `${s.id} is missing ${k}`);
    }
    assert.ok(["point", "actor", "self", "compartment"].includes(s.target), `${s.id} bad target`);
    assert.ok(s.castMs >= 400, `${s.id} has no meaningful tell`);
  }
});

test("compartments are five per act and uniquely named", () => {
  for (let a = 0; a < ACTS; a++) {
    assert.strictEqual(COMPARTMENTS.filter((c) => c.section === a).length, 5);
  }
  const names = COMPARTMENTS.map((c) => c.name);
  assert.strictEqual(new Set(names).size, names.length,
    "a log entry naming a room has to be unambiguous");
});

test("the wreck only ever gets darker", () => {
  for (let i = 1; i < ACT_VISION.length; i++) {
    assert.ok(ACT_VISION[i] < ACT_VISION[i - 1], "act " + i + " is not darker");
  }
});

test("the snapshot never serialises a role or a real log id", () => {
  const src = read("snapshot.js");
  // forBase hardcodes role "base"; the living view sends only the reader's
  // own role. Neither may ever reach for somebody else's.
  assert.ok(!/o\.role/.test(src), "snapshot must never read another player's role");
  assert.ok(!/realId/.test(src), "snapshot must never touch a transit entry's real id");
});

// ---------------------------------------------------------------- the sheet
//
// These replace a test that read the PNG header and compared its height to
// classes x items x 4 x 32. That caught "you added a class and forgot to
// regenerate" and was blind to "you swapped two items" -- and a swap is the
// failure that matters, because it hands players somebody else's body with
// no error anywhere. While the row was computed by arithmetic, no test could
// have caught it: the order *was* the contract. The manifest is what makes
// these assertions possible at all.

const ASSETS = path.join(__dirname, "..", "public", "assets");

function manifest() {
  return JSON.parse(fs.readFileSync(path.join(ASSETS, "hunters.json"), "utf8"));
}

function pngSize(file) {
  const png = fs.readFileSync(path.join(ASSETS, file));
  assert.strictEqual(png.toString("ascii", 1, 4), "PNG", `${file} is not a PNG`);
  return { w: png.readUInt32BE(16), h: png.readUInt32BE(20) };
}

test("the manifest describes exactly the classes and items that exist", () => {
  const m = manifest();
  const byName = new Map(m.states.map((s) => [s.name, s]));

  for (const cls of CLASS_NAMES) {
    for (const it of itemsOf(cls)) {
      const name = `${cls}/${it.id}`;
      assert.ok(byName.has(name),
        `no sprite state "${name}" -- rerun make_hunters.py`);
    }
  }
  const wanted = new Set(
    CLASS_NAMES.flatMap((c) => itemsOf(c).map((it) => `${c}/${it.id}`)));
  for (const s of m.states) {
    assert.ok(wanted.has(s.name),
      `manifest state "${s.name}" is not in the class table -- stale manifest`);
  }
  assert.strictEqual(m.states.length, wanted.size);
});

test("the manifest accounts for every row of the sheet", () => {
  const m = manifest();
  const base = pngSize(m.sheets.base);

  // rows contiguous from zero: a gap is wasted pixels and almost always a
  // manifest regenerated against a different sheet
  let row = 0;
  for (const s of m.states) {
    assert.strictEqual(s.row, row,
      `state "${s.name}" starts at row ${s.row}, expected ${row}`);
    row += s.directions;
  }
  assert.strictEqual(row * m.size.y, base.h,
    `manifest claims ${row} rows, ${m.sheets.base} holds ${base.h / m.size.y}`);
  assert.strictEqual(base.w, m.size.x * Math.max(...m.states.map((s) => s.frames)),
    "sheet width does not match the widest state's frame count");
});

test("the manifest is internally consistent", () => {
  const m = manifest();
  assert.strictEqual(m.version, 1, "unknown manifest version");
  assert.ok(m.size && m.size.x > 0 && m.size.y > 0, "no frame size");
  assert.ok(Array.isArray(m.directions) && m.directions.length > 0, "no directions");
  assert.ok(m.states.length > 0, "no states");

  const seen = new Set();
  for (const s of m.states) {
    assert.ok(!seen.has(s.name), `duplicate state "${s.name}"`);
    seen.add(s.name);
    assert.ok(s.directions >= 1 && s.directions <= m.directions.length,
      `state "${s.name}" claims ${s.directions} directions`);
    assert.ok(s.frames >= 1, `state "${s.name}" has no frames`);
  }
  // every sheet named must exist, and the layers must line up pixel for pixel
  const base = pngSize(m.sheets.base);
  for (const [layer, file] of Object.entries(m.sheets)) {
    const got = pngSize(file);
    assert.deepStrictEqual(got, base,
      `layer "${layer}" (${file}) is ${got.w}x${got.h}, base is ${base.w}x${base.h}`);
  }
});

test("no consumer computes a sprite row", () => {
  // The whole point. A row may only come from the manifest, by name; the
  // moment something multiplies its way to one, the class-order footgun is
  // back and no other test in this file would notice.
  //
  // Comments are stripped first, because the client documents the formula it
  // used to carry and explaining a mistake must not count as making it. The
  // stripping is deliberately conservative -- block comments, and lines that
  // *begin* with a comment marker -- so a `//` inside a string can never
  // swallow real code and hide a genuine violation.
  const client = fs.readFileSync(
    path.join(__dirname, "..", "public", "client.js"), "utf8")
    .replace(/\/\*[\s\S]*?\*\//g, "")
    .split("\n").filter((l) => !/^\s*(\/\/|\*)/.test(l)).join("\n");

  assert.ok(!/sheetRow/.test(client), "client.js still has a sheetRow()");
  assert.ok(!/\*\s*3\s*\+/.test(client),
    "client.js still computes a row from a class position");
  assert.ok(/STATES\[/.test(client), "client.js no longer looks a state up by name");
});

test("a disguise borrows kit as well as a class", () => {
  // The mage's own item is not in the borrowed class's list, and a sprite
  // holding a censer while wearing a Technik's cap would give him away for
  // nothing. Falling back to the first item is what keeps the disguise whole.
  // An item from another class falls back to the first slot.
  assert.strictEqual(itemIndex("Technik", "kadzidlo"), 0);
  // This used to also assert itemIndex("Technik", "rygiel") === 2 -- a
  // hardcoded position, which is the very brittleness the manifest exists to
  // remove, and it duly broke the first time the table was reordered. What
  // matters is that an item maps to its own slot, whatever that slot is.
  for (const cls of CLASS_NAMES) {
    itemsOf(cls).forEach((it, i) => {
      assert.strictEqual(itemIndex(cls, it.id), i, `${cls}/${it.id} is out of order`);
    });
  }
});

console.log(`\n${passed} passed`);

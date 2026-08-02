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

test("the sprite sheet has a row for every class and every item", () => {
  // The sheet is laid out (class * 3 + item) * 4 + direction. Adding a class
  // or a fourth item to one without regenerating hunters.png does not throw
  // anywhere -- it silently draws somebody else's body, which is the exact
  // failure this whole coupling is commented about. Read the PNG header
  // rather than trusting that somebody remembered.
  const png = fs.readFileSync(path.join(__dirname, "..", "public", "assets", "hunters.png"));
  assert.strictEqual(png.toString("ascii", 1, 4), "PNG");
  const width = png.readUInt32BE(16), height = png.readUInt32BE(20);
  const wanted = CLASS_NAMES.reduce((n, c) => n + itemsOf(c).length, 0) * 4 * 32;
  assert.strictEqual(width, 64, "two walk frames across");
  assert.strictEqual(height, wanted,
    `sheet is ${height / 32} rows, the class table needs ${wanted / 32}` +
    " -- rerun make_hunters.py");
});

test("a disguise borrows kit as well as a class", () => {
  // The mage's own item is not in the borrowed class's list, and a sprite
  // holding a censer while wearing a Technik's cap would give him away for
  // nothing. Falling back to the first item is what keeps the disguise whole.
  assert.strictEqual(itemIndex("Technik", "kadzidlo"), 0);
  assert.strictEqual(itemIndex("Technik", "rygiel"), 2);
  for (const cls of CLASS_NAMES) {
    itemsOf(cls).forEach((it, i) => {
      assert.strictEqual(itemIndex(cls, it.id), i, `${cls}/${it.id} is out of order`);
    });
  }
});

console.log(`\n${passed} passed`);

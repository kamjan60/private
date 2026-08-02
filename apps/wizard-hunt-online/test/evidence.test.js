"use strict";
/**
 * Evidence rules, exercised without a server or a socket.
 *
 * These are the assertions the design argument rests on, so they are worth
 * more than coverage: if "a log entry never survives contact with a
 * disguise" stops being true, the game stops being about deduction.
 */

const assert = require("assert");
const {
  makeEvidence, logTransit, readLog, eraseLog, copyLog,
  addResidue, readResidue, makeCorpse, readCorpse
} = require("../src/evidence");
const { RESIDUE_MS, FILTER_WINDOW_MS, CORPSE_TRACE_MS } = require("../src/rules");

let passed = 0;
function test(name, fn) {
  try { fn(); passed++; console.log("  ok   " + name); }
  catch (e) { console.log("  FAIL " + name + "\n       " + e.message); process.exitCode = 1; }
}

const T0 = 1000000;

console.log("transit logs");

test("log records the class, never the name", () => {
  const ev = makeEvidence();
  logTransit(ev, "Mostek", { realId: 7, apparentClass: "Chirurg", kind: "in", act: 0, t: T0 });
  const [e] = readLog(ev, "Mostek", { act: 0, now: T0 });
  assert.strictEqual(e.cls, "Chirurg");
  assert.ok(!("realId" in e), "reader must not receive the real player id");
  assert.ok(!("name" in e), "reader must not receive a name");
});

test("a disguised mage writes somebody else's class", () => {
  const ev = makeEvidence();
  // the mage is really the Technik, wearing the Chirurg
  logTransit(ev, "Kaplica", { realId: 3, apparentClass: "Chirurg", kind: "in", act: 0, t: T0 });
  const [e] = readLog(ev, "Kaplica", { act: 0, now: T0 });
  assert.strictEqual(e.cls, "Chirurg", "the log must record what the sensors saw");
});

test("only the current act is readable", () => {
  const ev = makeEvidence();
  logTransit(ev, "Mesa", { realId: 1, apparentClass: "Runarz", kind: "in", act: 0, t: T0 });
  logTransit(ev, "Mesa", { realId: 1, apparentClass: "Runarz", kind: "in", act: 1, t: T0 + 5 });
  assert.strictEqual(readLog(ev, "Mesa", { act: 0, now: T0 }).length, 1);
  assert.strictEqual(readLog(ev, "Mesa", { act: 1, now: T0 }).length, 1);
});

test("Wymazanie hides the caster's entries and only his", () => {
  const ev = makeEvidence();
  logTransit(ev, "Reaktor", { realId: 3, apparentClass: "Technik", kind: "in", act: 1, t: T0 });
  logTransit(ev, "Reaktor", { realId: 4, apparentClass: "Chirurg", kind: "in", act: 1, t: T0 + 10 });
  const n = eraseLog(ev, "Reaktor", { realId: 3, act: 1 });
  assert.strictEqual(n, 1);
  const seen = readLog(ev, "Reaktor", { act: 1, now: T0 + 20 });
  assert.deepStrictEqual(seen.map((e) => e.cls), ["Chirurg"]);
});

test("Filtr still sees erased entries inside its sixty seconds", () => {
  const ev = makeEvidence();
  logTransit(ev, "Archiwum", { realId: 3, apparentClass: "Technik", kind: "in", act: 2, t: T0 });
  eraseLog(ev, "Archiwum", { realId: 3, act: 2 });
  const plain = readLog(ev, "Archiwum", { act: 2, now: T0 + 5000 });
  const filtered = readLog(ev, "Archiwum", { act: 2, now: T0 + 5000, filterLogs: true });
  assert.strictEqual(plain.length, 0, "an ordinary reader sees the hole");
  assert.strictEqual(filtered.length, 1, "the Archiwista reads straight off the tape");
});

test("Filtr drops entries older than its window", () => {
  const ev = makeEvidence();
  logTransit(ev, "Śluza", { realId: 2, apparentClass: "Zwiadowca", kind: "in", act: 2, t: T0 });
  const late = T0 + FILTER_WINDOW_MS + 1;
  assert.strictEqual(readLog(ev, "Śluza", { act: 2, now: late, filterLogs: true }).length, 0);
  assert.strictEqual(readLog(ev, "Śluza", { act: 2, now: late }).length, 1);
});

test("Kopia survives a later erase", () => {
  const ev = makeEvidence();
  logTransit(ev, "Warsztat", { realId: 3, apparentClass: "Runarz", kind: "in", act: 1, t: T0 });
  copyLog(ev, "Warsztat", 1);
  eraseLog(ev, "Warsztat", { realId: 3, act: 1 });
  assert.strictEqual(readLog(ev, "Warsztat", { act: 1, now: T0 + 10 }).length, 1);
});

console.log("residue");

test("residue reports a school and no person", () => {
  const ev = makeEvidence();
  addResidue(ev, "Kaplica", { school: "ogien", realId: 3, t: T0 });
  const r = readResidue(ev, "Kaplica", { now: T0 + 1000 });
  assert.deepStrictEqual(r, ["ogien"]);
});

test("residue fades after its window", () => {
  const ev = makeEvidence();
  addResidue(ev, "Kaplica", { school: "ogien", realId: 3, t: T0 });
  assert.deepStrictEqual(readResidue(ev, "Kaplica", { now: T0 + RESIDUE_MS + 1 }), []);
});

test("Wykrywacz reads the whole act", () => {
  const ev = makeEvidence();
  addResidue(ev, "Kaplica", { school: "mrok", realId: 3, t: T0 });
  const late = T0 + RESIDUE_MS + 60000;
  assert.deepStrictEqual(
    readResidue(ev, "Kaplica", { now: late, residueAct: true, actStart: T0 - 1000 }),
    ["mrok"]
  );
});

test("a planted trace is indistinguishable from a real one", () => {
  const ev = makeEvidence();
  addResidue(ev, "Mesa", { school: "woda", realId: 3, t: T0, fake: true });
  const r = readResidue(ev, "Mesa", { now: T0 + 100 });
  assert.deepStrictEqual(r, ["woda"], "the reader must not be told it was planted");
});

test("Wymazanie clears the caster's residue too", () => {
  const ev = makeEvidence();
  addResidue(ev, "Reaktor", { school: "ogien", realId: 3, t: T0 });
  addResidue(ev, "Reaktor", { school: "woda", realId: 5, t: T0 });
  eraseLog(ev, "Reaktor", { realId: 3, act: 0 });
  assert.deepStrictEqual(readResidue(ev, "Reaktor", { now: T0 + 100 }), ["woda"]);
});

console.log("corpses");

test("a body gives the school, never the caster", () => {
  const c = makeCorpse({ x: 1, y: 2, cls: "Chirurg", name: "Kaz", id: 4, school: "ogien", t: T0 });
  const r = readCorpse(c, { now: T0 + 1000 });
  assert.strictEqual(r.school, "ogien");
  assert.ok(!("caster" in r) && !("by" in r));
});

test("the trace goes cold", () => {
  const c = makeCorpse({ x: 1, y: 2, cls: "Chirurg", name: "Kaz", id: 4, school: "ogien", t: T0 });
  assert.strictEqual(readCorpse(c, { now: T0 + CORPSE_TRACE_MS + 1 }), null);
});

test("Kadzidło keeps it legible three times as long", () => {
  const c = makeCorpse({ x: 1, y: 2, cls: "Chirurg", name: "Kaz", id: 4, school: "ogien", t: T0 });
  const late = T0 + CORPSE_TRACE_MS + 1;
  assert.ok(readCorpse(c, { now: late, traceMult: 3 }), "Kadzidło should still read it");
});

test("the fuzzed time is stable between reads", () => {
  const c = makeCorpse({ x: 1, y: 2, cls: "Chirurg", name: "Kaz", id: 9, school: "woda", t: T0 });
  const a = readCorpse(c, { now: T0 + 1000 });
  const b = readCorpse(c, { now: T0 + 9000 });
  assert.strictEqual(a.t, b.t, "two hunters comparing notes must not see a contradiction");
  assert.strictEqual(a.exact, false);
});

test("Autopsja gives the exact time", () => {
  const c = makeCorpse({ x: 1, y: 2, cls: "Chirurg", name: "Kaz", id: 9, school: "woda", t: T0 });
  const r = readCorpse(c, { now: T0 + 1000, exactTime: true });
  assert.strictEqual(r.t, T0);
  assert.strictEqual(r.exact, true);
});

console.log(`\n${passed} passed`);

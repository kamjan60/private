"use strict";
/** Acts, artifact accounting, the closed path, and the tribunal's arithmetic. */

const assert = require("assert");
const R = require("../src/round");
const T = require("../src/tribunal");
const {
  ACT_MS, ACTS, ARTIFACTS_PER_ACT, ARTIFACTS_TO_WIN, ARTIFACTS_LOST_TO_CLOSE,
  TRIBUNAL_COOLDOWN, ACQUITTED_IMMUNE_MS, TRIBUNAL_VOTE_MS
} = require("../src/rules");

let passed = 0;
function test(name, fn) {
  try { fn(); passed++; console.log("  ok   " + name); }
  catch (e) { console.log("  FAIL " + name + "\n       " + e.message); process.exitCode = 1; }
}

const T0 = 1000000;
// a fixed shuffle so layouts are reproducible across runs
let seed = 7;
const rand = () => ((seed = (1103515245 * seed + 12345) & 0x7fffffff) / 0x7fffffff);

console.log("acts and artifacts");

test("act I opens with four artifacts, all in its own section", () => {
  const r = R.makeRound(T0, rand);
  const a = R.actArtifacts(r, 0);
  assert.strictEqual(a.length, ARTIFACTS_PER_ACT);
  assert.ok(a.every((x) => x.act === 0));
  assert.strictEqual(new Set(a.map((x) => x.room)).size, ARTIFACTS_PER_ACT,
    "one artifact per compartment");
});

test("the act ends when its artifacts are all resolved", () => {
  const r = R.makeRound(T0, rand);
  assert.ok(!R.actOver(r, T0 + 1000));
  for (const a of R.actArtifacts(r, 0)) R.secure(r, a.id);
  assert.ok(R.actOver(r, T0 + 1000));
});

test("the act ends when its ten minutes are up", () => {
  const r = R.makeRound(T0, rand);
  assert.ok(!R.actOver(r, T0 + ACT_MS - 1));
  assert.ok(R.actOver(r, T0 + ACT_MS));
});

test("advancing strands whatever was left behind", () => {
  const r = R.makeRound(T0, rand);
  const open = R.actArtifacts(r, 0);
  R.secure(r, open[0].id);
  const res = R.advanceAct(r, T0 + ACT_MS, rand);
  assert.strictEqual(res.stranded, ARTIFACTS_PER_ACT - 1);
  assert.strictEqual(r.lost, ARTIFACTS_PER_ACT - 1);
  assert.strictEqual(r.act, 1);
  assert.strictEqual(R.actArtifacts(r, 1).length, ARTIFACTS_PER_ACT);
});

test("the wreck goes dark act by act", () => {
  const r = R.makeRound(T0, rand);
  const seen = [];
  for (let i = 0; i < ACTS; i++) { seen.push(R.visionMult(r)); R.advanceAct(r, T0, rand); }
  assert.deepStrictEqual(seen, [1.0, 0.75, 0.5]);
  assert.strictEqual(R.advanceAct(r, T0, rand), null, "there is no fourth act");
});

test("Pożoga and Zawał take an artifact out of play", () => {
  const r = R.makeRound(T0, rand);
  const a = R.actArtifacts(r, 0)[0];
  assert.ok(R.lose(r, a.id, "pozoga"));
  assert.strictEqual(r.lost, 1);
  assert.strictEqual(R.lose(r, a.id, "zawal"), null, "it can only be lost once");
});

test("Pieczęć protects an artifact from being destroyed but not from the clock", () => {
  const r = R.makeRound(T0, rand);
  const a = R.actArtifacts(r, 0)[0];
  R.sealWithRune(r, a.id);
  assert.strictEqual(R.lose(r, a.id, "pozoga"), null, "Pieczęć should hold");
  assert.ok(R.lose(r, a.id, "czas"), "but running out of time still loses it");
});

test("four lost closes the artifact path", () => {
  const r = R.makeRound(T0, rand);
  for (let i = 0; i < ARTIFACTS_LOST_TO_CLOSE - 1; i++) {
    R.lose(r, R.openArtifacts(r)[0].id, "pozoga");
    assert.ok(!R.pathClosed(r), `still open after ${i + 1} lost`);
  }
  R.advanceAct(r, T0 + ACT_MS, rand);
  assert.ok(r.lost >= ARTIFACTS_LOST_TO_CLOSE);
  assert.ok(R.pathClosed(r));
});

test("the closed path really is unreachable", () => {
  // 12 artifacts, 9 to win: losing 4 leaves 8, and 8 < 9.
  assert.ok(R.ARTIFACTS_TOTAL - ARTIFACTS_LOST_TO_CLOSE < ARTIFACTS_TO_WIN);
});

console.log("winning");

test("nine secured wins it for the hunters", () => {
  const r = R.makeRound(T0, rand);
  for (let act = 0; act < ACTS; act++) {
    for (const a of R.actArtifacts(r, act)) {
      if (r.secured < ARTIFACTS_TO_WIN) R.secure(r, a.id);
    }
    if (act < ACTS - 1) R.advanceAct(r, T0, rand);
  }
  const w = R.checkWin(r, { mageEjected: false, hunterCount: 4, now: T0 });
  assert.strictEqual(w.winner, "hunters");
});

test("convicting the mage wins it immediately", () => {
  const r = R.makeRound(T0, rand);
  assert.strictEqual(R.checkWin(r, { mageEjected: true, hunterCount: 5, now: T0 }).winner, "hunters");
});

test("one hunter left wins it for the mage", () => {
  const r = R.makeRound(T0, rand);
  assert.strictEqual(R.checkWin(r, { mageEjected: false, hunterCount: 1, now: T0 }).winner, "mage");
});

test("surviving the full thirty minutes wins it for the mage", () => {
  const r = R.makeRound(T0, rand);
  const late = T0 + ACTS * ACT_MS;
  assert.strictEqual(R.checkWin(r, { mageEjected: false, hunterCount: 4, now: late }).winner, "mage");
});

test("a decided round stays decided", () => {
  const r = R.makeRound(T0, rand);
  R.checkWin(r, { mageEjected: true, hunterCount: 5, now: T0 });
  assert.strictEqual(R.checkWin(r, { mageEjected: false, hunterCount: 1, now: T0 }), null);
});

console.log("tribunal");

test("a majority of the living convicts", () => {
  const trib = T.makeTribunal();
  T.open(trib, { accusedId: 1, accuserId: 2, now: T0 });
  const living = [1, 2, 3, 4, 5];
  T.vote(trib, 2, "tak"); T.vote(trib, 3, "tak"); T.vote(trib, 4, "tak");
  T.vote(trib, 5, "nie"); T.vote(trib, 1, "nie");
  const res = T.resolve(trib, living, T0 + 1000);
  assert.strictEqual(res.convicted, true);
  assert.strictEqual(res.counts.tak, 3);
});

test("a tie releases", () => {
  const trib = T.makeTribunal();
  T.open(trib, { accusedId: 1, accuserId: 2, now: T0 });
  const living = [1, 2, 3, 4];
  T.vote(trib, 2, "tak"); T.vote(trib, 3, "tak");
  T.vote(trib, 4, "nie"); T.vote(trib, 1, "nie");
  assert.strictEqual(T.resolve(trib, living, T0 + 1000).convicted, false);
});

test("abstentions count against conviction", () => {
  const trib = T.makeTribunal();
  T.open(trib, { accusedId: 1, accuserId: 2, now: T0 });
  const living = [1, 2, 3, 4, 5];
  T.vote(trib, 2, "tak"); T.vote(trib, 3, "tak");
  // 1, 4 and 5 say nothing at all
  const res = T.resolve(trib, living, T0 + 1000);
  assert.strictEqual(res.convicted, false);
  assert.strictEqual(res.counts.wstrzym, 3, "silence is an abstention");
});

test("votes are published after the verdict", () => {
  const trib = T.makeTribunal();
  T.open(trib, { accusedId: 1, accuserId: 2, now: T0 });
  T.vote(trib, 2, "tak");
  const res = T.resolve(trib, [1, 2], T0 + 10);
  assert.deepStrictEqual(res.cast.find((c) => c.id === 2), { id: 2, vote: "tak" });
});

test("the mage swinging a three-hander wins the round for him", () => {
  // two hunters and the mage: the mage votes with one hunter against the
  // other, and the hunters are down to one.
  const trib = T.makeTribunal();
  T.open(trib, { accusedId: 3, accuserId: 1, now: T0 });
  const living = [1, 2, 3];   // 2 is the mage
  T.vote(trib, 1, "tak"); T.vote(trib, 2, "tak"); T.vote(trib, 3, "nie");
  assert.strictEqual(T.resolve(trib, living, T0).convicted, true);
  const r = R.makeRound(T0, rand);
  assert.strictEqual(R.checkWin(r, { mageEjected: false, hunterCount: 1, now: T0 }).winner, "mage");
});

test("tribunals rest two minutes between sittings", () => {
  const trib = T.makeTribunal();
  T.open(trib, { accusedId: 1, accuserId: 2, now: T0 });
  T.resolve(trib, [1, 2, 3], T0);
  assert.strictEqual(T.canBind(trib, 5, T0 + TRIBUNAL_COOLDOWN - 1).ok, false);
  assert.strictEqual(T.canBind(trib, 5, T0 + TRIBUNAL_COOLDOWN).ok, true);
});

test("somebody just released cannot be dragged back", () => {
  const trib = T.makeTribunal();
  T.open(trib, { accusedId: 9, accuserId: 2, now: T0 });
  T.vote(trib, 2, "nie");
  T.resolve(trib, [2, 9], T0);
  const past = T0 + TRIBUNAL_COOLDOWN + 1;
  assert.strictEqual(past < T0 + ACQUITTED_IMMUNE_MS, false,
    "cooldown outlasts immunity, so check immunity inside its own window");
  assert.strictEqual(T.canBind(trib, 9, T0 + ACQUITTED_IMMUNE_MS - 1).ok, false);
  assert.strictEqual(T.canBind(trib, 9, T0 + TRIBUNAL_COOLDOWN).ok, true);
});

test("a sitting cannot start while one is running", () => {
  const trib = T.makeTribunal();
  T.open(trib, { accusedId: 1, accuserId: 2, now: T0 });
  assert.strictEqual(T.canBind(trib, 4, T0 + 10).ok, false);
});

test("the vote closes on its own after a minute", () => {
  const trib = T.makeTribunal();
  T.open(trib, { accusedId: 1, accuserId: 2, now: T0 });
  assert.strictEqual(T.expired(trib, T0 + TRIBUNAL_VOTE_MS - 1), false);
  assert.strictEqual(T.expired(trib, T0 + TRIBUNAL_VOTE_MS), true);
});

test("it closes early once everyone has spoken", () => {
  const trib = T.makeTribunal();
  T.open(trib, { accusedId: 1, accuserId: 2, now: T0 });
  T.vote(trib, 1, "nie");
  assert.strictEqual(T.everyoneVoted(trib, [1, 2]), false);
  T.vote(trib, 2, "tak");
  assert.strictEqual(T.everyoneVoted(trib, [1, 2]), true);
});

console.log(`\n${passed} passed`);

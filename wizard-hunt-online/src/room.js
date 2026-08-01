"use strict";
/**
 * Room and player state, and the phases a round moves through:
 *
 *   lobby -> loadout -> play -> end
 *
 * with `play` briefly suspended whenever a tribunal is sitting. The world
 * does not step while people are voting, so nobody loses a body because
 * they were reading the screen.
 */

const {
  MIN_PLAYERS, MAX_PLAYERS, LOADOUT_MS, TASER_COOLDOWN, BOOK_SLOTS
} = require("./rules");
const { CLASSES, dealClasses, statsFor, itemsOf } = require("./classes");
const { PRESETS, buildBook, spell } = require("./spells");
const { makeEvidence } = require("./evidence");
const { makeTribunal } = require("./tribunal");
const { makeRound } = require("./round");
const { makeBase } = require("./base");
const { compartmentAt, spawnIn, sectionOf } = require("./map");

const now = () => Date.now();
const rooms = new Map();

function code() {
  const A = "ABCDEFGHJKLMNPQRSTUVWXYZ";
  let s;
  do { s = Array.from({ length: 4 }, () => A[Math.floor(Math.random() * A.length)]).join(""); }
  while (rooms.has(s));
  return s;
}

function makeRoom() {
  const room = {
    id: code(), phase: "lobby", players: new Map(), hostId: null, nextId: 1,
    round: null, evidence: null, tribunal: makeTribunal(), base: null,
    balls: [], delayed: [], walls: [], corpses: [], pings: [], markers: [],
    sealedTemp: new Map(),   // compartment -> until (Rygiel, Kotwica, base doors)
    doused: new Map(),       // compartment -> until (Zgaszenie)
    lit: new Map(),          // compartment -> until (Generator, base lights)
    events: [], loadoutEndsAt: 0, winner: null, tick: 0
  };
  rooms.set(room.id, room);
  return room;
}

function makePlayer(id, name, ws) {
  return {
    id, name, ws, role: "hunter", cls: null, item: null, stats: null, book: null,
    x: 0, y: 0, dir: 0, step: 0, phase: 0, comp: null,
    hp: 1, alive: true, down: false, ejected: false,
    input: { x: 0, y: 0 }, holding: false,
    stunUntil: 0, stunImmune: false, silenceUntil: 0, blindUntil: 0,
    slowUntil: 0, slowMul: 1, hasteUntil: 0, hasteMul: 1, proneUntil: 0,
    channel: null, windup: null, castReadyAt: 0, taserReadyAt: 0, lock: null,
    disguisedAs: null, disguiseUntil: 0, invisibleUntil: 0,
    itemCharges: 0, itemReadyAt: 0, vests: 0, usedRevive: false,
    lastPingAt: 0, loadoutReady: false
  };
}

const list = (room) => [...room.players.values()];
const connected = (room) => list(room).filter((p) => p.ws && p.ws.readyState === 1);
const alive = (room) => list(room).filter((p) => p.alive && !p.ejected);
const hunters = (room) => alive(room).filter((p) => p.role !== "mage");
const theMage = (room) => list(room).find((p) => p.role === "mage");
const inBase = (room) => list(room).filter((p) => !p.alive || p.ejected);

function pushEvent(room, msg, kind) {
  room.events.push({ msg, kind, at: now() });
  if (room.events.length > 40) room.events.shift();
}

// ------------------------------------------------------------------ loadout

/**
 * Deal roles and unique classes, then open the loadout screen.
 *
 * The mage walks through exactly the same screen as everybody else plus a
 * book tab, so the time somebody spends choosing gives nothing away.
 */
function startLoadout(room) {
  const ps = list(room);
  if (ps.length < MIN_PLAYERS || ps.length > MAX_PLAYERS) {
    return { ok: false, why: `Potrzeba od ${MIN_PLAYERS} do ${MAX_PLAYERS} graczy.` };
  }
  const classes = dealClasses(ps.length);
  const mageIdx = Math.floor(Math.random() * ps.length);
  ps.forEach((p, i) => {
    p.cls = classes[i];
    p.role = i === mageIdx ? "mage" : "hunter";
    p.item = null;
    p.book = null;
    p.loadoutReady = false;
  });
  room.phase = "loadout";
  room.loadoutEndsAt = now() + LOADOUT_MS;
  return { ok: true };
}

function chooseLoadout(room, p, { itemId, book }) {
  if (room.phase !== "loadout") return false;
  const item = itemsOf(p.cls).find((it) => it.id === itemId);
  if (!item) return false;
  p.item = item.id;
  if (p.role === "mage") {
    const ids = Array.isArray(book) ? book.slice(0, BOOK_SLOTS) : [];
    if (ids.length !== BOOK_SLOTS) return false;
    try { p.book = buildBook(ids); } catch { return false; }
  }
  p.loadoutReady = true;
  return true;
}

/** Nobody blocks seven other people because they cannot make up their mind. */
function fillMissingLoadouts(room) {
  for (const p of list(room)) {
    if (p.loadoutReady) continue;
    const items = itemsOf(p.cls);
    p.item = items[Math.floor(Math.random() * items.length)].id;
    if (p.role === "mage") {
      const names = Object.keys(PRESETS);
      p.book = buildBook(PRESETS[names[Math.floor(Math.random() * names.length)]]);
    }
    p.loadoutReady = true;
  }
}

const loadoutDone = (room) =>
  list(room).every((p) => p.loadoutReady) || now() >= room.loadoutEndsAt;

// ------------------------------------------------------------------ round

function startRound(room) {
  fillMissingLoadouts(room);
  room.round = makeRound(now());
  room.evidence = makeEvidence();
  room.tribunal = makeTribunal();
  room.base = makeBase();
  room.balls = []; room.delayed = []; room.walls = []; room.corpses = [];
  room.pings = []; room.markers = []; room.events = [];
  room.sealedTemp.clear(); room.doused.clear(); room.lit.clear();
  room.winner = null;
  room.phase = "play";

  const rooms0 = sectionOf(0);
  for (const p of list(room)) {
    const c = rooms0[Math.floor(Math.random() * rooms0.length)];
    const s = spawnIn(c);
    Object.assign(p, {
      x: s.x, y: s.y, dir: 0, step: 0, phase: 0, comp: c.name,
      alive: true, down: false, ejected: false,
      stunUntil: 0, stunImmune: false, silenceUntil: 0, blindUntil: 0,
      slowUntil: 0, slowMul: 1, hasteUntil: 0, hasteMul: 1, proneUntil: 0,
      channel: null, windup: null, castReadyAt: 0, taserReadyAt: 0, lock: null,
      disguisedAs: null, disguiseUntil: 0, invisibleUntil: 0,
      vests: 0, usedRevive: false, lastPingAt: 0, input: { x: 0, y: 0 }, holding: false
    });
    p.stats = statsFor(p.cls, p.item);
    p.hp = p.stats.hp;
    const it = itemsOf(p.cls).find((i) => i.id === p.item);
    p.itemCharges = it && it.kind === "active" ? it.charges : 0;
    p.itemReadyAt = 0;
    p.taserReadyAt = now();
  }
  pushEvent(room, "Wrak otwarty. Akt I — Rozpoznanie.", "start");
  return room.round;
}

/** The apparent class: what the sensors and everybody else's eyes report.
 *  You always see your own real class. */
function apparentClass(p) {
  return p.disguisedAs && now() < p.disguiseUntil ? p.disguisedAs : p.cls;
}

function endRound(room, winner, msg) {
  room.phase = "end";
  room.winner = winner;
  const m = theMage(room);
  return { t: "end", winner, msg, mage: m ? { id: m.id, name: m.name, cls: m.cls } : null };
}

module.exports = {
  rooms, now, makeRoom, makePlayer, list, connected, alive, hunters, theMage, inBase,
  pushEvent, startLoadout, chooseLoadout, fillMissingLoadouts, loadoutDone,
  startRound, endRound, apparentClass
};

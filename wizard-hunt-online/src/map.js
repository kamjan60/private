"use strict";
/**
 * The wreck: fifteen compartments on three decks, joined by corridors.
 *
 * Corridors are not doors and not a loading screen -- they are rooms in
 * their own right. They are long enough to be caught halfway down, they hold
 * several people at once, and crucially **no camera looks into one**. That
 * makes a corridor the only place on the ship where a killing has no witness
 * but the walls, which is exactly the space a mage needs and exactly the
 * space hunters should think twice about entering in company.
 *
 * They are also logged. The sensors record who went in and who came out, so
 * "two entered and one left" is the hardest evidence in the game -- and the
 * disguise is the only thing that can lie about it.
 *
 * Everything here is derived from the room grid and a declared link list, so
 * geometry cannot drift out of step with connectivity.
 */

const { W, H } = require("./rules");

const WALL = 8;                 // wall thickness, also the collision margin
const ROOM_W = 300, ROOM_H = 360;
const GAP_X = 140, GAP_Y = 200; // corridor lengths
const MARGIN = 80;
const HALL = 76;                // corridor width

const COLS = 5, ROWS = 3;
const colX = (i) => MARGIN + i * (ROOM_W + GAP_X);
const rowY = (r) => MARGIN + r * (ROOM_H + GAP_Y);

const NAMES = [
  ["Mostek", "Ładownia", "Mesa", "Kwatery", "Obserwatorium"],
  ["Medyczny", "Kaplica", "Warsztat", "Kriokomory", "Maszynownia"],
  ["Reaktor", "Archiwum", "Śluza", "Serwerownia", "Zbrojownia"]
];

const COMPARTMENTS = [];
for (let r = 0; r < ROWS; r++) {
  for (let i = 0; i < COLS; i++) {
    COMPARTMENTS.push({
      name: NAMES[r][i], kind: "room", section: r,
      x: colX(i), y: rowY(r), w: ROOM_W, h: ROOM_H, col: i, row: r
    });
  }
}

/**
 * Connectivity. Each deck is a chain, and three shafts run down between
 * decks so a new act opens the floor below rather than an island.
 */
const LINKS = [];
for (let r = 0; r < ROWS; r++) {
  for (let i = 0; i < COLS - 1; i++) LINKS.push([NAMES[r][i], NAMES[r][i + 1]]);
}
for (const i of [0, 2, 4]) {
  for (let r = 0; r < ROWS - 1; r++) LINKS.push([NAMES[r][i], NAMES[r + 1][i]]);
}

const ROOM_BY_NAME = new Map(COMPARTMENTS.map((c) => [c.name, c]));

/** A corridor is named for what it joins, so a log entry reads as a place. */
function makeCorridor([aName, bName]) {
  const a = ROOM_BY_NAME.get(aName), b = ROOM_BY_NAME.get(bName);
  if (!a || !b) throw new Error(`link to nowhere: ${aName} - ${bName}`);
  const name = `Łącznik ${aName}–${bName}`;

  if (a.row === b.row) {
    const left = a.col < b.col ? a : b, right = a.col < b.col ? b : a;
    return {
      name, kind: "corridor", ends: [left.name, right.name], axis: "x",
      // a corridor opens with the later of the two decks it touches
      section: Math.max(a.section, b.section),
      x: left.x + left.w, y: left.y + (ROOM_H - HALL) / 2, w: GAP_X, h: HALL
    };
  }
  const top = a.row < b.row ? a : b, bottom = a.row < b.row ? b : a;
  return {
    name, kind: "corridor", ends: [top.name, bottom.name], axis: "y",
    section: Math.max(a.section, b.section),
    x: top.x + (ROOM_W - HALL) / 2, y: top.y + top.h, w: HALL, h: GAP_Y
  };
}

const CORRIDORS = LINKS.map(makeCorridor);
const ZONES = COMPARTMENTS.concat(CORRIDORS);
const BY_NAME = new Map(ZONES.map((z) => [z.name, z]));

/**
 * Openings, derived from geometry: wherever a corridor abuts a room, both
 * lose that stretch of wall. Nothing is hand-placed, so a doorway cannot end
 * up leading into vacuum.
 */
const OPENINGS = new Map();     // zone name -> [{ side, from, to }]
function opening(name, side, from, to) {
  if (!OPENINGS.has(name)) OPENINGS.set(name, []);
  OPENINGS.get(name).push({ side, from, to });
}
for (const c of CORRIDORS) {
  const [n1, n2] = c.ends;
  const r1 = ROOM_BY_NAME.get(n1), r2 = ROOM_BY_NAME.get(n2);
  if (c.axis === "x") {
    opening(r1.name, "e", c.y, c.y + c.h);
    opening(c.name, "w", c.y, c.y + c.h);
    opening(r2.name, "w", c.y, c.y + c.h);
    opening(c.name, "e", c.y, c.y + c.h);
  } else {
    opening(r1.name, "s", c.x, c.x + c.w);
    opening(c.name, "n", c.x, c.x + c.w);
    opening(r2.name, "n", c.x, c.x + c.w);
    opening(c.name, "s", c.x, c.x + c.w);
  }
}

function zone(name) {
  const z = BY_NAME.get(name);
  if (!z) throw new Error(`unknown zone: ${name}`);
  return z;
}
const compartment = zone;
const isCorridor = (name) => { const z = BY_NAME.get(name); return !!z && z.kind === "corridor"; };
const sectionOf = (act) => COMPARTMENTS.filter((c) => c.section === act);

/** Which zone contains this point -- room or corridor -- or null for hull. */
function compartmentAt(x, y) {
  for (const z of ZONES) {
    if (x >= z.x && x <= z.x + z.w && y >= z.y && y <= z.y + z.h) return z;
  }
  return null;
}

/**
 * A zone's walls, with its openings cut out. `sealed` closes them again --
 * that is Rygiel, Zawał, the base's doors, and a deck that has not opened.
 */
function wallsOf(z, sealed) {
  const segs = [];
  const sides = {
    n: { fixed: z.y, from: z.x, to: z.x + z.w, horizontal: true },
    s: { fixed: z.y + z.h, from: z.x, to: z.x + z.w, horizontal: true },
    w: { fixed: z.x, from: z.y, to: z.y + z.h, horizontal: false },
    e: { fixed: z.x + z.w, from: z.y, to: z.y + z.h, horizontal: false }
  };
  const holes = sealed ? [] : (OPENINGS.get(z.name) || []);
  for (const [side, s] of Object.entries(sides)) {
    const gaps = holes.filter((h) => h.side === side)
      .map((h) => [h.from, h.to]).sort((a, b) => a[0] - b[0]);
    let cursor = s.from;
    for (const [gs, ge] of gaps) {
      if (gs > cursor) segs.push(seg(s, cursor, gs));
      cursor = Math.max(cursor, ge);
    }
    if (cursor < s.to) segs.push(seg(s, cursor, s.to));
  }
  return segs;
}

function seg(s, from, to) {
  return s.horizontal
    ? { x1: from, y1: s.fixed, x2: to, y2: s.fixed }
    : { x1: s.fixed, y1: from, x2: s.fixed, y2: to };
}

/**
 * Can a body of radius `r` stand here?
 *
 * Only zones are floor; the space around them is hull and vacuum, so nobody
 * walks off the ship and no shove can put them there. A zone whose deck has
 * not opened yet is closed, which is how an act unlocks its section without
 * needing a separate gate.
 */
function free(x, y, r, state) {
  if (x < r || y < r || x > W - r || y > H - r) return false;
  const here = compartmentAt(x, y);
  if (!here) return false;
  if (state && typeof state.act === "number" && here.section > state.act) return false;

  for (const z of ZONES) {
    if (x < z.x - r - WALL || x > z.x + z.w + r + WALL) continue;
    if (y < z.y - r - WALL || y > z.y + z.h + r + WALL) continue;
    const shut = (state && state.sealed && state.sealed.has(z.name)) ||
      (state && typeof state.act === "number" && z.section > state.act);
    for (const s of wallsOf(z, shut)) {
      if (segmentHit(x, y, r + WALL / 2, s)) return false;
    }
  }
  for (const s of (state && state.walls) || []) {
    if (segmentHit(x, y, r + WALL / 2, s)) return false;
  }
  return true;
}

function segmentHit(px, py, r, s) {
  const dx = s.x2 - s.x1, dy = s.y2 - s.y1;
  const len2 = dx * dx + dy * dy;
  let t = len2 ? ((px - s.x1) * dx + (py - s.y1) * dy) / len2 : 0;
  t = t < 0 ? 0 : t > 1 ? 1 : t;
  const cx = s.x1 + t * dx, cy = s.y1 + t * dy;
  return (px - cx) ** 2 + (py - cy) ** 2 < r * r;
}

/** A spawn point well inside a zone, clear of its walls. */
function spawnIn(z, rand = Math.random) {
  const pad = Math.min(40, Math.min(z.w, z.h) / 3);
  return {
    x: Math.round(z.x + pad + rand() * (z.w - pad * 2)),
    y: Math.round(z.y + pad + rand() * (z.h - pad * 2))
  };
}

module.exports = {
  COMPARTMENTS, CORRIDORS, ZONES, LINKS, OPENINGS,
  WALL, ROOM_W, ROOM_H, HALL,
  zone, compartment, compartmentAt, isCorridor, sectionOf, wallsOf, free, spawnIn
};

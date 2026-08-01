"use strict";
/**
 * The wreck: fifteen compartments in three sections, one section per act.
 *
 * Compartments have solid walls and door gaps. That is new -- the previous
 * build had no collision at all and compartments were only named rectangles.
 * The Earth school needs walls to mean anything: Rygiel shuts a compartment's
 * doors, Zawał shuts them for good, and neither is a threat in open space.
 *
 * Doors are declared as a side plus a centre offset along that side, so a
 * compartment's geometry stays readable and the door positions move with the
 * room if it is resized.
 */

const { W, H } = require("./rules");

const WALL = 8;           // wall thickness, also the collision margin
const DOOR_W = 70;

/** side: "n" | "s" | "w" | "e"; at: centre of the gap along that side */
const COMPARTMENTS = [
  // ---------------------------------------------------- act I, pokład górny
  { name: "Mostek",         section: 0, x: 60,   y: 60,   w: 340, h: 400,
    doors: [{ side: "s", at: 170 }, { side: "e", at: 300 }] },
  { name: "Ładownia",       section: 0, x: 440,  y: 60,   w: 380, h: 400,
    doors: [{ side: "s", at: 190 }, { side: "w", at: 300 }] },
  { name: "Mesa",           section: 0, x: 860,  y: 60,   w: 300, h: 400,
    doors: [{ side: "s", at: 150 }, { side: "e", at: 260 }] },
  { name: "Kwatery",        section: 0, x: 1200, y: 60,   w: 340, h: 400,
    doors: [{ side: "s", at: 170 }, { side: "w", at: 260 }] },
  { name: "Obserwatorium",  section: 0, x: 1580, y: 60,   w: 360, h: 400,
    doors: [{ side: "s", at: 180 }] },

  // ---------------------------------------------------- act II, pokład dolny
  { name: "Medyczny",       section: 1, x: 60,   y: 600,  w: 320, h: 400,
    doors: [{ side: "n", at: 160 }, { side: "e", at: 300 }] },
  { name: "Kaplica",        section: 1, x: 420,  y: 600,  w: 400, h: 400,
    doors: [{ side: "n", at: 200 }, { side: "s", at: 200 }] },
  { name: "Warsztat",       section: 1, x: 860,  y: 600,  w: 340, h: 400,
    doors: [{ side: "n", at: 170 }, { side: "e", at: 300 }] },
  { name: "Kriokomory",     section: 1, x: 1240, y: 600,  w: 320, h: 400,
    doors: [{ side: "n", at: 160 }, { side: "w", at: 300 }] },
  { name: "Maszynownia",    section: 1, x: 1600, y: 600,  w: 340, h: 400,
    doors: [{ side: "n", at: 170 }, { side: "s", at: 170 }] },

  // ---------------------------------------------------- act III, rdzeń
  { name: "Reaktor",        section: 2, x: 60,   y: 1140, w: 380, h: 400,
    doors: [{ side: "n", at: 190 }, { side: "e", at: 300 }] },
  { name: "Archiwum",       section: 2, x: 480,  y: 1140, w: 320, h: 400,
    doors: [{ side: "n", at: 160 }, { side: "w", at: 300 }] },
  { name: "Śluza",          section: 2, x: 840,  y: 1140, w: 300, h: 400,
    doors: [{ side: "n", at: 150 }] },
  { name: "Serwerownia",    section: 2, x: 1180, y: 1140, w: 360, h: 400,
    doors: [{ side: "n", at: 180 }, { side: "e", at: 300 }] },
  { name: "Zbrojownia",     section: 2, x: 1580, y: 1140, w: 360, h: 400,
    doors: [{ side: "n", at: 180 }, { side: "w", at: 300 }] }
];

const BY_NAME = new Map(COMPARTMENTS.map((c) => [c.name, c]));

function compartment(name) {
  const c = BY_NAME.get(name);
  if (!c) throw new Error(`unknown compartment: ${name}`);
  return c;
}

function sectionOf(act) { return COMPARTMENTS.filter((c) => c.section === act); }

/** Which compartment contains this point, or null for the corridors. */
function compartmentAt(x, y) {
  for (const c of COMPARTMENTS) {
    if (x >= c.x && x <= c.x + c.w && y >= c.y && y <= c.y + c.h) return c;
  }
  return null;
}

/**
 * A compartment's walls as segments, with the door gaps cut out.
 * `sealed` closes the gaps -- that is Rygiel, Zawał, and the base's doors.
 */
function wallsOf(c, sealed) {
  const segs = [];
  const sides = {
    n: { fixed: c.y, from: c.x, to: c.x + c.w, horizontal: true },
    s: { fixed: c.y + c.h, from: c.x, to: c.x + c.w, horizontal: true },
    w: { fixed: c.x, from: c.y, to: c.y + c.h, horizontal: false },
    e: { fixed: c.x + c.w, from: c.y, to: c.y + c.h, horizontal: false }
  };
  for (const [side, s] of Object.entries(sides)) {
    const gaps = sealed
      ? []
      : c.doors.filter((d) => d.side === side)
          .map((d) => {
            const centre = s.from + d.at;
            return [centre - DOOR_W / 2, centre + DOOR_W / 2];
          })
          .sort((a, b) => a[0] - b[0]);
    let cursor = s.from;
    for (const [gs, ge] of gaps) {
      if (gs > cursor) segs.push(seg(s, cursor, gs));
      cursor = ge;
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
 * Can a body of radius `r` stand at (x, y)?
 *
 * `state` supplies what is currently shut: `state.sealed` is a Set of
 * compartment names, `state.walls` is a list of temporary Mur / Kotwica
 * segments. Only compartments in an unlocked section are solid -- locked
 * sections are handled by keeping players out of them entirely.
 */
function free(x, y, r, state) {
  if (x < r || y < r || x > W - r || y > H - r) return false;
  for (const c of COMPARTMENTS) {
    // cheap reject: only the compartments we are near can block us
    if (x < c.x - r - WALL || x > c.x + c.w + r + WALL) continue;
    if (y < c.y - r - WALL || y > c.y + c.h + r + WALL) continue;
    const sealed = state && state.sealed && state.sealed.has(c.name);
    for (const s of wallsOf(c, sealed)) {
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

/** A spawn point inside a compartment, clear of its walls. */
function spawnIn(c, rand = Math.random) {
  const pad = 40;
  return {
    x: Math.round(c.x + pad + rand() * (c.w - pad * 2)),
    y: Math.round(c.y + pad + rand() * (c.h - pad * 2))
  };
}

module.exports = {
  COMPARTMENTS, WALL, DOOR_W,
  compartment, compartmentAt, sectionOf, wallsOf, free, spawnIn
};

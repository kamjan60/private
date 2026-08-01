"use strict";
/**
 * The wreck: fifteen compartments in three sections, one section per act.
 *
 * Compartments are sealed boxes joined by airlocks. There is no walkable
 * space between them: the void outside used to be open floor, which let
 * players drift off the ship and made a transit log something you could
 * simply route around.
 *
 * Walls are solid on all four sides. A hatch is not a gap -- you press
 * against it, it takes you, and it puts you out the far side a couple of
 * seconds later. That delay is the point: nobody follows you through
 * instantly, and fleeing a fight costs the pursuer nothing to match.
 */

const { W, H } = require("./rules");

const WALL = 8;           // wall thickness, also the collision margin
const DOOR_W = 70;   // drawn width of a hatch; walls are solid regardless

const COMPARTMENTS = [
  // ---------------------------------------------------- act I, pokład górny
  { name: "Mostek",         section: 0, x: 60,   y: 60,   w: 340, h: 400 },
  { name: "Ładownia",       section: 0, x: 440,  y: 60,   w: 380, h: 400 },
  { name: "Mesa",           section: 0, x: 860,  y: 60,   w: 300, h: 400 },
  { name: "Kwatery",        section: 0, x: 1200, y: 60,   w: 340, h: 400 },
  { name: "Obserwatorium",  section: 0, x: 1580, y: 60,   w: 360, h: 400 },

  // ---------------------------------------------------- act II, pokład dolny
  { name: "Medyczny",       section: 1, x: 60,   y: 600,  w: 320, h: 400 },
  { name: "Kaplica",        section: 1, x: 420,  y: 600,  w: 400, h: 400 },
  { name: "Warsztat",       section: 1, x: 860,  y: 600,  w: 340, h: 400 },
  { name: "Kriokomory",     section: 1, x: 1240, y: 600,  w: 320, h: 400 },
  { name: "Maszynownia",    section: 1, x: 1600, y: 600,  w: 340, h: 400 },

  // ---------------------------------------------------- act III, rdzeń
  { name: "Reaktor",        section: 2, x: 60,   y: 1140, w: 380, h: 400 },
  { name: "Archiwum",       section: 2, x: 480,  y: 1140, w: 320, h: 400 },
  { name: "Śluza",          section: 2, x: 840,  y: 1140, w: 300, h: 400 },
  { name: "Serwerownia",    section: 2, x: 1180, y: 1140, w: 360, h: 400 },
  { name: "Zbrojownia",     section: 2, x: 1580, y: 1140, w: 360, h: 400 },
];

/**
 * The wreck's connectivity, declared rather than inferred.
 *
 * Every pair here becomes one airlock. Doors are derived from the geometry
 * of the pair, so the two hatches always line up and no compartment can end
 * up with a door that leads nowhere -- which is exactly what happened when
 * doors were hand-placed and the space between rooms was open void.
 *
 * Each section is a chain, and three shafts run down between sections so a
 * new act opens the deck below rather than a disconnected island.
 */
const LINKS = [
  // deck by deck, west to east
  ["Mostek", "Ładownia"], ["Ładownia", "Mesa"], ["Mesa", "Kwatery"],
  ["Kwatery", "Obserwatorium"],
  ["Medyczny", "Kaplica"], ["Kaplica", "Warsztat"], ["Warsztat", "Kriokomory"],
  ["Kriokomory", "Maszynownia"],
  ["Reaktor", "Archiwum"], ["Archiwum", "Śluza"], ["Śluza", "Serwerownia"],
  ["Serwerownia", "Zbrojownia"],
  // shafts down to the next deck
  ["Mostek", "Medyczny"], ["Mesa", "Warsztat"], ["Obserwatorium", "Maszynownia"],
  ["Medyczny", "Reaktor"], ["Warsztat", "Śluza"], ["Maszynownia", "Zbrojownia"]
];

const BY_NAME = new Map(COMPARTMENTS.map((c) => [c.name, c]));

/** Where the two hatches of a link sit, and which way you face going through. */
function makeDoor(aName, bName, i) {
  const a = BY_NAME.get(aName), b = BY_NAME.get(bName);
  if (!a || !b) throw new Error(`link to nowhere: ${aName} - ${bName}`);
  const horizontal = Math.abs((a.x + a.w / 2) - (b.x + b.w / 2)) >
                     Math.abs((a.y + a.h / 2) - (b.y + b.h / 2));
  if (horizontal) {
    const left = a.x < b.x ? a : b, right = a.x < b.x ? b : a;
    const y = Math.round(
      (Math.max(left.y, right.y) + Math.min(left.y + left.h, right.y + right.h)) / 2
    );
    return {
      id: i, a: left.name, b: right.name, axis: "x",
      ax: left.x + left.w, ay: y, bx: right.x, by: y
    };
  }
  const top = a.y < b.y ? a : b, bottom = a.y < b.y ? b : a;
  const x = Math.round(
    (Math.max(top.x, bottom.x) + Math.min(top.x + top.w, bottom.x + bottom.w)) / 2
  );
  return {
    id: i, a: top.name, b: bottom.name, axis: "y",
    ax: x, ay: top.y + top.h, bx: x, by: bottom.y
  };
}

const DOORS = LINKS.map(([a, b], i) => makeDoor(a, b, i));

/** Both hatches of every lock this compartment touches, with the far side. */
function doorsOf(name) {
  const out = [];
  for (const d of DOORS) {
    if (d.a === name) out.push({ door: d, x: d.ax, y: d.ay, to: d.b });
    if (d.b === name) out.push({ door: d, x: d.bx, y: d.by, to: d.a });
  }
  return out;
}

/**
 * The hatch this player is trying to walk through, if any.
 *
 * Walls are solid all the way round -- a hatch is not a gap you slip through
 * but a thing you press against and are then sealed inside.
 */
function doorUnder(x, y, dx, dy, compName, reach) {
  let best = null, bd = reach;
  for (const h of doorsOf(compName)) {
    const d = Math.hypot(h.x - x, h.y - y);
    if (d > bd) continue;
    // must actually be pushing outward through it, not brushing past
    const nx = h.x - x, ny = h.y - y, l = Math.hypot(nx, ny) || 1;
    if ((dx * nx + dy * ny) / l < 0.3) continue;
    bd = d; best = h;
  }
  return best;
}

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
 * A compartment's walls: four solid sides, no gaps.
 *
 * Hatches are not holes. You walk up to one, it takes you, and it puts you
 * out the other side a couple of seconds later -- so there is nothing here
 * for a body to slip through, and no void outside to slip into.
 */
function wallsOf(c) {
  return [
    { x1: c.x, y1: c.y, x2: c.x + c.w, y2: c.y },
    { x1: c.x, y1: c.y + c.h, x2: c.x + c.w, y2: c.y + c.h },
    { x1: c.x, y1: c.y, x2: c.x, y2: c.y + c.h },
    { x1: c.x + c.w, y1: c.y, x2: c.x + c.w, y2: c.y + c.h }
  ];
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
  // Only compartments are floor. Everything else is hull and vacuum, and a
  // shove must not be able to put a body out there.
  if (!compartmentAt(x, y)) return false;
  for (const c of COMPARTMENTS) {
    // cheap reject: only the compartments we are near can block us
    if (x < c.x - r - WALL || x > c.x + c.w + r + WALL) continue;
    if (y < c.y - r - WALL || y > c.y + c.h + r + WALL) continue;
    for (const s of wallsOf(c)) {
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
  COMPARTMENTS, LINKS, DOORS, WALL, DOOR_W,
  compartment, compartmentAt, sectionOf, wallsOf, free, spawnIn,
  doorsOf, doorUnder, makeDoor
};

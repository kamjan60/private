"use strict";
/**
 * The base: what the dead and the ejected do instead of watching.
 *
 * They crew the station -- cameras, doors, emergency lighting -- and the
 * feeds show class silhouettes and never names, so a disguise fools the
 * base exactly as it fools the living. Nobody down here ever learns who the
 * mage is, which is the whole reason they are allowed to keep talking on
 * voice: at a thirty-minute round the alternative is asking half the table
 * to sit in silence for twenty-five minutes, and nobody does.
 *
 * The action pool is shared by everyone in the base and refills each act.
 * Per-person charges would turn a fifth death into an air-traffic control
 * tower, which is the opposite of the balance the design wants.
 */

const {
  BASE_ACT_CHARGES, BASE_LIGHT_MS, BASE_CAMERA_VIEWS, BASE_CAMERAS_DEAD_IN_ACT3
} = require("./rules");
const { COMPARTMENTS } = require("./map");

function makeBase() {
  return {
    charges: BASE_ACT_CHARGES,
    act: 0,
    /**
     * Rooms with a working camera; act III kills half of them.
     *
     * Corridors are deliberately absent. Nothing watches a corridor, which
     * is what makes one the only place aboard where a killing leaves no
     * witness -- and why "two went in, one came out" has to be argued from
     * the transit log rather than seen.
     */
    cameras: COMPARTMENTS.map((c) => c.name),
    /** extra cameras dropped by the Technik, always live */
    field: new Set(),
    /** playerId -> [compartment, compartment] currently on their screens */
    watching: new Map()
  };
}

/** New act: the pool refills, and in the last act half the cameras fail.
 *  The base grows in people as the round goes on but loses its eyes. */
function onAct(base, act) {
  base.act = act;
  base.charges = BASE_ACT_CHARGES;
  if (act === 2) {
    const keep = Math.ceil(COMPARTMENTS.length * (1 - BASE_CAMERAS_DEAD_IN_ACT3));
    const shuffled = COMPARTMENTS.map((c) => c.name);
    for (let i = shuffled.length - 1; i > 0; i--) {
      const j = Math.floor(Math.random() * (i + 1));
      [shuffled[i], shuffled[j]] = [shuffled[j], shuffled[i]];
    }
    base.cameras = shuffled.slice(0, keep);
  }
}

const liveCameras = (base) => [...new Set([...base.cameras, ...base.field])];

/** Watching costs nothing -- it is the one thing the base can always do. */
function watch(base, playerId, comps) {
  const live = new Set(liveCameras(base));
  const picked = (comps || []).filter((c) => live.has(c)).slice(0, BASE_CAMERA_VIEWS);
  base.watching.set(playerId, picked);
  return picked;
}

function spend(base, n = 1) {
  if (base.charges < n) return false;
  base.charges -= n;
  return true;
}

/** Doors and lights come out of the shared pool. */
function toggleDoor(base, room, compName, now) {
  if (!spend(base)) return { ok: false, why: "Baza nie ma już mocy w tym akcie." };
  if (room.sealedTemp.has(compName)) {
    room.sealedTemp.delete(compName);
    return { ok: true, opened: true };
  }
  room.sealedTemp.set(compName, now + 20000);
  return { ok: true, opened: false };
}

function light(base, room, compName, now) {
  if (!spend(base)) return { ok: false, why: "Baza nie ma już mocy w tym akcie." };
  room.lit.set(compName, now + BASE_LIGHT_MS);
  return { ok: true };
}

function addFieldCamera(base, compName) { base.field.add(compName); }

module.exports = {
  makeBase, onAct, liveCameras, watch, toggleDoor, light, addFieldCamera, spend
};

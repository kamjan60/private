"use strict";
/**
 * Every tuning number the round depends on, in one place.
 *
 * The spec these come from lives in
 * docs/superpowers/specs/2026-08-01-wizard-hunt-rules-design.md.
 * When a number here disagrees with that document, the document is what
 * we argued about, so fix the code.
 */

// ---------------------------------------------------------------- session
const TICK_HZ = 15;
const TICK_MS = 1000 / TICK_HZ;
const MIN_PLAYERS = 5;
const MAX_PLAYERS = 8;          // one unique class each, and there are eight

// ---------------------------------------------------------------- world
const W = 2000, H = 1600;
const SPEED_BASE = 2.5;
/**
 * Compartments are joined by airlocks, not open floor. Stepping into one
 * seals you in for this long before the far side opens.
 *
 * The void between rooms used to be walkable, which let players drift off
 * the ship entirely and made the transit log meaningless. Locking the
 * passage instead turns every room change into a committed, timed act: you
 * cannot follow somebody through instantly, and you cannot flee through one
 * mid-fight without buying the pursuer two and a half seconds.
 */
const LOCK_MS = 2500;
const DOOR_REACH = 30;      // how close you must be to a hatch to enter it

// ---------------------------------------------------------------- acts
const ACTS = 3;
const ACT_MS = 600000;                    // ten minutes each, thirty total
const ACT_VISION = [1.0, 0.75, 0.5];      // the wreck goes dark
const ARTIFACTS_PER_ACT = 4;
const ARTIFACTS_TOTAL = ACTS * ARTIFACTS_PER_ACT;   // 12
const ARTIFACTS_TO_WIN = 9;
/**
 * Losing this many closes the artifact path for good: 12 - 4 = 8, and 8 is
 * short of the 9 hunters need. From that moment the tribunal is their only
 * road, which is the road they can be wrong on. This is the mage's clock.
 */
const ARTIFACTS_LOST_TO_CLOSE = ARTIFACTS_TOTAL - ARTIFACTS_TO_WIN + 1;

// ---------------------------------------------------------------- hunters
const TASER_STUN_MS = 3600;     // long enough to close the distance and bind
const TASER_COOLDOWN = 6000;
const BIND_MS = 1800;           // channel that opens a tribunal
const BIND_MS_SHACKLES = 900;   // Inkwizytor's Kajdany
const EXTRACT_MS = 2800;
const EXTRACT_MS_FAST = 1400;   // Runarz's Ekstraktor
const MARKSMAN_RANGE = 330;

// ---------------------------------------------------------------- tribunal
const TRIBUNAL_VOTE_MS = 60000;
const TRIBUNAL_COOLDOWN = 120000;   // between tribunals, room-wide
const ACQUITTED_IMMUNE_MS = 60000;  // a released player cannot be re-bound

// ---------------------------------------------------------------- mage
const BOOK_SLOTS = 10;
const CAST_GLOBAL_COOLDOWN = 3000;
const CAST_RANGE_DEFAULT = 210;
const BALL_SPEED = 7.6;         // px per tick
const BALL_LIFE = 2400;
const BALL_HIT_R = 22;

// ---------------------------------------------------------------- evidence
const LOG_WINDOW = "act";       // transit logs only show the current act
const CORPSE_TRACE_MS = 120000;
const CORPSE_TRACE_MS_INCENSE = 360000;   // Inkwizytor's Kadzidło
const CORPSE_TIME_FUZZ_MS = 30000;        // ±30 s unless an autopsy is done
const RESIDUE_MS = 90000;
const FILTER_WINDOW_MS = 60000;           // Archiwista's Filtr

// ---------------------------------------------------------------- base
const BASE_CAMERA_VIEWS = 2;    // simultaneous feeds per person in the base
const BASE_ACT_CHARGES = 6;     // doors + lights, shared by the whole base
const BASE_LIGHT_MS = 20000;
const BASE_CAMERAS_DEAD_IN_ACT3 = 0.5;    // half the cameras fail in act III

// ---------------------------------------------------------------- pings
const PING_COOLDOWN = 8000;
const PING_MS = 20000;
const PING_KINDS = ["podejrzany", "czysto", "bylem-tu", "zwloki"];

// ---------------------------------------------------------------- lobby
const LOADOUT_MS = 90000;       // then everyone undecided gets a random pick

module.exports = {
  TICK_HZ, TICK_MS, MIN_PLAYERS, MAX_PLAYERS,
  W, H, SPEED_BASE, LOCK_MS, DOOR_REACH,
  ACTS, ACT_MS, ACT_VISION, ARTIFACTS_PER_ACT, ARTIFACTS_TOTAL,
  ARTIFACTS_TO_WIN, ARTIFACTS_LOST_TO_CLOSE,
  TASER_STUN_MS, TASER_COOLDOWN, BIND_MS, BIND_MS_SHACKLES,
  EXTRACT_MS, EXTRACT_MS_FAST, MARKSMAN_RANGE,
  TRIBUNAL_VOTE_MS, TRIBUNAL_COOLDOWN, ACQUITTED_IMMUNE_MS,
  BOOK_SLOTS, CAST_GLOBAL_COOLDOWN, CAST_RANGE_DEFAULT,
  BALL_SPEED, BALL_LIFE, BALL_HIT_R,
  LOG_WINDOW, CORPSE_TRACE_MS, CORPSE_TRACE_MS_INCENSE, CORPSE_TIME_FUZZ_MS,
  RESIDUE_MS, FILTER_WINDOW_MS,
  BASE_CAMERA_VIEWS, BASE_ACT_CHARGES, BASE_LIGHT_MS, BASE_CAMERAS_DEAD_IN_ACT3,
  PING_COOLDOWN, PING_MS, PING_KINDS,
  LOADOUT_MS
};

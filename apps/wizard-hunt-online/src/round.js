"use strict";
/**
 * Acts, artifacts and who won.
 *
 * The round is three ten-minute acts and the wreck goes dark as they pass.
 * Each act puts four artifacts in its own section; anything not extracted
 * before the act ends is lost for good, as is anything the mage burns or
 * buries.
 *
 * Losing four closes the artifact path -- 12 total, 9 needed, so 8 reachable
 * is not enough. From that moment the hunters can only win by convicting
 * somebody, which is the only thing they can be wrong about. That is the
 * mage's clock, and it is why stalling is a strategy for him rather than a
 * failure to act.
 */

const {
  ACTS, ACT_MS, ACT_VISION, ARTIFACTS_PER_ACT, ARTIFACTS_TOTAL,
  ARTIFACTS_TO_WIN, ARTIFACTS_LOST_TO_CLOSE
} = require("./rules");
const { sectionOf, spawnIn } = require("./map");

function makeRound(now, rand = Math.random) {
  const r = {
    act: 0,
    actStartedAt: now,
    startedAt: now,
    artifacts: [],
    nextArtifactId: 0,
    secured: 0,
    lost: 0,
    sealed: new Set(),      // compartments closed for good by Zawał
    winner: null,
    endMsg: null
  };
  layoutAct(r, 0, rand);
  return r;
}

/** Four of the section's five compartments get an artifact. Which five are
 *  empty is re-rolled every round so the sweep cannot be memorised. */
function layoutAct(round, act, rand = Math.random) {
  const rooms = sectionOf(act).slice();
  for (let i = rooms.length - 1; i > 0; i--) {
    const j = Math.floor(rand() * (i + 1));
    [rooms[i], rooms[j]] = [rooms[j], rooms[i]];
  }
  for (const c of rooms.slice(0, ARTIFACTS_PER_ACT)) {
    const p = spawnIn(c, rand);
    round.artifacts.push({
      id: round.nextArtifactId++, act, room: c.name,
      x: p.x, y: p.y, state: "open", sealedByRune: false
    });
  }
}

const visionMult = (round) => ACT_VISION[round.act];
const actEndsAt = (round) => round.actStartedAt + ACT_MS;
const openArtifacts = (round) => round.artifacts.filter((a) => a.state === "open");
const actArtifacts = (round, act) => round.artifacts.filter((a) => a.act === act);

/**
 * The artifact path is dead once too many are gone to reach nine. Hunters
 * are told -- hiding it would only make them waste the rest of the round
 * walking to rooms that cannot save them.
 */
const pathClosed = (round) => round.lost >= ARTIFACTS_LOST_TO_CLOSE;

function secure(round, id) {
  const a = round.artifacts.find((x) => x.id === id);
  if (!a || a.state !== "open") return null;
  a.state = "secured";
  round.secured++;
  return a;
}

/** Pożoga, Zawał, or an act running out with the artifact still in the room. */
function lose(round, id, cause) {
  const a = round.artifacts.find((x) => x.id === id);
  if (!a || a.state !== "open") return null;
  if (a.sealedByRune && (cause === "pozoga" || cause === "zawal")) return null;
  a.state = "lost";
  a.cause = cause;
  round.lost++;
  return a;
}

/** Runarz's Pieczęć. Does not extract it -- somebody still has to come back. */
function sealWithRune(round, id) {
  const a = round.artifacts.find((x) => x.id === id);
  if (!a || a.state !== "open" || a.sealedByRune) return null;
  a.sealedByRune = true;
  return a;
}

/**
 * Move to the next act. Everything still lying in the old section is lost,
 * which is what makes the act timer bite.
 */
function advanceAct(round, now, rand = Math.random) {
  if (round.act >= ACTS - 1) return null;
  const stranded = actArtifacts(round, round.act).filter((a) => a.state === "open");
  for (const a of stranded) lose(round, a.id, "czas");
  round.act++;
  round.actStartedAt = now;
  layoutAct(round, round.act, rand);
  return { act: round.act, stranded: stranded.length };
}

/** True when the current act is over: its artifacts are all resolved, or
 *  its ten minutes are up. */
function actOver(round, now) {
  if (now >= actEndsAt(round)) return true;
  return actArtifacts(round, round.act).every((a) => a.state !== "open");
}

const roundOver = (round, now) => now >= round.startedAt + ACTS * ACT_MS;

/**
 * Who won, if anybody has.
 *
 *   hunters   nine artifacts secured, or the mage convicted
 *   mage      one hunter left, or the full thirty minutes survived
 */
function checkWin(round, { mageEjected, hunterCount, now }) {
  if (round.winner) return null;
  if (mageEjected) return end(round, "hunters", "Mag został schwytany.");
  if (hunterCount <= 1) return end(round, "mage", "Zostało za mało łowców.");
  if (round.secured >= ARTIFACTS_TO_WIN) {
    return end(round, "hunters", "Artefakty zabezpieczone.");
  }
  if (roundOver(round, now)) {
    return end(round, "mage", "Wrak pochłonął resztę. Mag przetrwał.");
  }
  return null;
}

function end(round, winner, msg) {
  round.winner = winner;
  round.endMsg = msg;
  return { winner, msg };
}

module.exports = {
  makeRound, layoutAct, advanceAct, actOver, roundOver,
  secure, lose, sealWithRune, checkWin,
  visionMult, actEndsAt, openArtifacts, actArtifacts, pathClosed,
  ARTIFACTS_TOTAL, ARTIFACTS_TO_WIN, ARTIFACTS_LOST_TO_CLOSE
};

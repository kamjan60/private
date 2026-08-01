"use strict";
/**
 * Everything the hunters can learn without being told: transit logs, the
 * school of magic left on a corpse, and casting residue in a compartment.
 *
 * The rule the whole game hangs on: no single piece of evidence names the
 * mage. A log entry proves somebody was *present*, not guilty. A corpse
 * says which school killed it, never who cast. Residue says a school was
 * cast here, never by whom. Only a stack of them, argued over out loud,
 * convicts -- and the mage can forge every layer.
 *
 * Everything here is a pure function over an evidence state object, so the
 * rules can be tested without a server, a socket, or a clock.
 */

const {
  CORPSE_TRACE_MS, CORPSE_TRACE_MS_INCENSE, CORPSE_TIME_FUZZ_MS,
  RESIDUE_MS, FILTER_WINDOW_MS
} = require("./rules");

function makeEvidence() {
  return {
    /** compartment name -> array of transit entries */
    logs: new Map(),
    /** compartment name -> array of residue marks */
    residue: new Map(),
    /** key `${comp}@${act}` -> frozen copy taken by Archiwista's Kopia */
    copies: new Map()
  };
}

// -------------------------------------------------------------- transit logs

/**
 * Record a player entering or leaving a compartment.
 *
 * `apparentClass` is what the station's sensors saw, which is not always
 * what walked past: a disguised mage writes the class he is wearing. That
 * single substitution is what stops the log from being a confession.
 *
 * `realId` is kept so Wymazanie can find the mage's own entries, and is
 * never serialised to a client.
 */
function logTransit(ev, compName, { realId, apparentClass, kind, act, t }) {
  if (!compName) return;
  let arr = ev.logs.get(compName);
  if (!arr) ev.logs.set(compName, (arr = []));
  arr.push({ realId, cls: apparentClass, kind, act, t, erased: false });
}

/**
 * Read a compartment's log.
 *
 *   act          only the current act is visible, per the design
 *   filterLogs   Archiwista's Filtr: last 60 s only, but erasure-proof
 *   now          needed by the filter window
 *
 * Returns entries stripped of anything the reader has no right to, which
 * for a log means the real player id.
 */
function readLog(ev, compName, { act, filterLogs = false, now = Date.now() } = {}) {
  const copied = ev.copies.get(`${compName}@${act}`);
  const arr = copied || ev.logs.get(compName) || [];
  return arr
    .filter((e) => e.act === act)
    .filter((e) => (filterLogs ? now - e.t <= FILTER_WINDOW_MS : !e.erased))
    .map((e) => ({ cls: e.cls, kind: e.kind, t: e.t }));
}

/**
 * Wymazanie. Marks the caster's own entries in this compartment and act as
 * erased, and wipes the residue he left there.
 *
 * It marks rather than deletes on purpose: Archiwista's Filtr reads the
 * last sixty seconds straight off the tape and so still sees them. A mage
 * who cleans up in front of an Archiwista has left a different kind of
 * evidence -- a hole -- which is exactly the trade the design wants.
 */
function eraseLog(ev, compName, { realId, act }) {
  const arr = ev.logs.get(compName) || [];
  let n = 0;
  for (const e of arr) {
    if (e.realId === realId && e.act === act && !e.erased) { e.erased = true; n++; }
  }
  ev.residue.set(compName, (ev.residue.get(compName) || []).filter((r) => r.realId !== realId));
  return n;
}

/** Archiwista's Kopia: freeze this act's log so it survives the act change. */
function copyLog(ev, compName, act) {
  const arr = (ev.logs.get(compName) || []).filter((e) => e.act === act);
  ev.copies.set(`${compName}@${act}`, arr.map((e) => ({ ...e })));
  return arr.length;
}

/** Act rollover. Copies stay; live entries for old acts stop being readable
 *  because readLog filters on act, so nothing needs deleting here. */
function hasCopy(ev, compName, act) {
  return ev.copies.has(`${compName}@${act}`);
}

// -------------------------------------------------------------- residue

/** Casting leaves a mark of its school. `realId` lets Wymazanie find it. */
function addResidue(ev, compName, { school, realId, t, fake = false }) {
  if (!compName) return;
  let arr = ev.residue.get(compName);
  if (!arr) ev.residue.set(compName, (arr = []));
  arr.push({ school, realId, t, fake });
}

/**
 * What magic was worked here recently?
 *
 * `residueAct` is Inkwizytor's Wykrywacz: instead of the ninety-second
 * window everyone else gets, he reads the whole act. Returns schools only --
 * residue never carries a person, and a planted mark is indistinguishable
 * from a real one, which is the point of Fałszywy ślad.
 */
function readResidue(ev, compName, { now = Date.now(), residueAct = false, actStart = 0 } = {}) {
  const arr = ev.residue.get(compName) || [];
  const cutoff = residueAct ? actStart : now - RESIDUE_MS;
  const schools = new Set();
  for (const r of arr) if (r.t >= cutoff) schools.add(r.school);
  return [...schools];
}

// -------------------------------------------------------------- corpses

function makeCorpse({ x, y, cls, name, id, school, t }) {
  return { x, y, cls, name, id, school, t };
}

/**
 * Read a body.
 *
 *   traceMult   Inkwizytor's Kadzidło keeps the trace legible three times
 *               as long
 *   exactTime   Chirurg's Autopsja gives the real time of death; everyone
 *               else gets it fuzzed by up to thirty seconds
 *
 * Returns null once the trace is cold -- the body is still there to find,
 * but it has stopped saying anything.
 */
function readCorpse(corpse, { now = Date.now(), traceMult = 1, exactTime = false } = {}) {
  const window = (traceMult > 1 ? CORPSE_TRACE_MS_INCENSE : CORPSE_TRACE_MS);
  if (now - corpse.t > window) return null;
  if (exactTime) return { school: corpse.school, t: corpse.t, exact: true };
  // Deterministic fuzz: the same body must not wobble between reads, or
  // two hunters comparing notes would think they had found a contradiction.
  const jitter = ((corpse.id * 2654435761) % (CORPSE_TIME_FUZZ_MS * 2)) - CORPSE_TIME_FUZZ_MS;
  return { school: corpse.school, t: corpse.t + jitter, exact: false };
}

module.exports = {
  makeEvidence,
  logTransit, readLog, eraseLog, copyLog, hasCopy,
  addResidue, readResidue,
  makeCorpse, readCorpse
};

"use strict";
/**
 * Casting: the wind-up, the interrupt, and what each of the twenty-four
 * spells actually does.
 *
 * Every cast is a spend. Ten slots is the whole round's ammunition, so the
 * mage cannot change style halfway -- and since a corpse carries the school
 * that killed it, his book leaves a signature the hunters can read.
 *
 * Every cast is also a tell. The wind-up blooms at the mage's position for
 * anyone with line of sight, and a taser landing inside it interrupts the
 * cast AND eats the charge. Without that the mage is unbeatable; with it,
 * being seen is the risk he manages.
 */

const {
  CAST_GLOBAL_COOLDOWN, CAST_RANGE_DEFAULT, BALL_SPEED, BALL_LIFE, BALL_HIT_R,
  W, H
} = require("./rules");
const { spell } = require("./spells");
const { compartmentAt, isCorridor, free } = require("./map");
const { addResidue, eraseLog, makeCorpse } = require("./evidence");
const R = require("./round");

const dist = (a, b) => Math.hypot(a.x - b.x, a.y - b.y);

function charge(p, spellId) {
  return (p.book || []).find((b) => b.id === spellId) || null;
}

/**
 * Begin a cast. Fails loudly enough for the client to explain itself, and
 * silently commits nothing until the wind-up resolves -- except the charge,
 * which is reserved now so an interrupt can eat it.
 */
function beginCast(room, p, spellId, aim, now, extra = {}) {
  if (p.role !== "mage" || !p.alive || p.ejected) return { ok: false };
  if (room.phase !== "play") return { ok: false, why: "Nie teraz." };
  if (p.windup) return { ok: false, why: "Już rzucasz." };
  if (now < p.castReadyAt) return { ok: false, why: "Zaklęcia stygną." };
  if (now < p.stunUntil || now < p.proneUntil) return { ok: false, why: "Nie możesz." };
  if (now < p.silenceUntil) return { ok: false, why: "Cisza." };

  const comp = compartmentAt(p.x, p.y);
  if (comp && room.jammed && (room.jammed.get(comp.name) || 0) > now) {
    return { ok: false, why: "Zakłócacz blokuje magię." };
  }

  const s = spell(spellId);
  const c = charge(p, spellId);
  if (!c || c.charges <= 0) return { ok: false, why: "Brak ładunków." };
  if (s.target === "compartment" && !comp) {
    return { ok: false, why: "To zaklęcie działa tylko w przedziale." };
  }

  c.charges--;                        // reserved: an interrupt keeps it spent
  // How far to throw it, as a fraction of the spell's reach. A Mur is
  // useless if it can only ever appear at maximum range -- the doorway you
  // want to block is usually the one you are standing next to.
  const dist = Math.max(0.15, Math.min(1, Number(extra.dist) || 1));
  p.windup = {
    spellId, at: now + s.castMs, school: s.school, dist,
    aim: aim || { x: 1, y: 0 }, comp: comp ? comp.name : null, extra
  };
  return { ok: true, castMs: s.castMs, school: s.school };
}

/** A taser landing during the wind-up. The charge is already gone. */
function interrupt(p) {
  if (!p.windup) return null;
  const id = p.windup.spellId;
  p.windup = null;
  return id;
}

function resolveCast(room, p, now, api) {
  const w = p.windup;
  if (!w) return null;
  p.windup = null;
  p.castReadyAt = now + CAST_GLOBAL_COOLDOWN;

  const s = spell(w.spellId);
  // Casting stains the room with its school. This is the residue hunters
  // read, and it is why a mage who fights in the open writes his own file.
  addResidue(room.evidence, w.comp, { school: s.school, realId: p.id, t: now });

  apply(room, p, s, w, now, api);
  return { spell: s, comp: w.comp };
}

// ------------------------------------------------------------------ helpers

/** Everyone a spell could reach: alive, not ejected, and not sealed in a
 *  hatch. A body inside an airlock is out of the world for those seconds. */
const livingOthers = (room, p) =>
  [...room.players.values()].filter((o) => o.alive && !o.ejected && o.id !== p.id);

function aimPoint(p, aim, range) {
  const len = Math.hypot(aim.x, aim.y) || 1;
  return { x: p.x + (aim.x / len) * range, y: p.y + (aim.y / len) * range };
}

function nearestTarget(room, p, range) {
  let best = null, bd = range;
  for (const o of livingOthers(room, p)) {
    const d = dist(p, o);
    if (d < bd) { bd = d; best = o; }
  }
  return best;
}

// ------------------------------------------------------------------ dispatch

function apply(room, p, s, w, now, api) {
  const range = s.range || CAST_RANGE_DEFAULT;
  // Only spells that land somewhere take the thrower's chosen distance. A
  // projectile flies until it hits, a cone is a shape, and a targeted spell
  // picks the nearest body -- none of them has a landing point to shorten.
  const throwRange = (s.target === "point" && s.effect !== "projectile")
    ? range * (w.dist || 1)
    : range;
  const at = aimPoint(p, w.aim, throwRange);

  switch (s.effect) {
    case "projectile": {
      const len = Math.hypot(w.aim.x, w.aim.y) || 1;
      room.balls.push({
        x: p.x, y: p.y, vx: (w.aim.x / len) * BALL_SPEED, vy: (w.aim.y / len) * BALL_SPEED,
        by: p.id, school: s.school, born: now
      });
      break;
    }
    case "cone": {
      for (const o of livingOthers(room, p)) {
        if (dist(p, o) > range) continue;
        const dx = o.x - p.x, dy = o.y - p.y;
        const dot = (dx * w.aim.x + dy * w.aim.y) / ((Math.hypot(dx, dy) || 1) * (Math.hypot(w.aim.x, w.aim.y) || 1));
        if (dot > 0.6) api.hit(room, o, p, s.school);
      }
      break;
    }
    case "delayed_blast":
      room.delayed.push({ x: at.x, y: at.y, at: now + s.delayMs, r: s.radius, by: p.id, school: s.school });
      break;
    case "burn_artifact": {
      if (isCorridor(w.comp)) break;        // corridors hold no artifacts
      const a = room.round.artifacts.find((x) => x.room === w.comp && x.state === "open");
      if (a && R.lose(room.round, a.id, "pozoga")) api.artifactLost(room, a, "spalony");
      break;
    }
    case "sleep": {
      const t = nearestTarget(room, p, range);
      if (t) api.stun(t, s.durationMs, now);
      break;
    }
    case "slow_area":
      for (const o of livingOthers(room, p)) {
        if (Math.hypot(o.x - at.x, o.y - at.y) <= s.radius) {
          o.slowUntil = now + s.durationMs; o.slowMul = 1 - s.slow;
        }
      }
      break;
    case "silence": {
      const t = nearestTarget(room, p, range);
      if (t) { t.silenceUntil = now + s.durationMs; t.channel = null; }
      break;
    }
    case "stun_immunity":
      p.stunImmune = true;
      break;
    case "chain_stun": {
      let from = p, hit = 0;
      const done = new Set([p.id]);
      while (hit < s.jumps) {
        let best = null, bd = range;
        for (const o of livingOthers(room, p)) {
          if (done.has(o.id)) continue;
          const d = dist(from, o);
          if (d < bd) { bd = d; best = o; }
        }
        if (!best) break;
        api.stun(best, s.durationMs, now);
        done.add(best.id); from = best; hit++;
      }
      break;
    }
    case "shove": {
      const t = nearestTarget(room, p, range);
      if (t) {
        const dx = t.x - p.x, dy = t.y - p.y, len = Math.hypot(dx, dy) || 1;
        api.move(t, t.x + (dx / len) * s.push, t.y + (dy / len) * s.push);
      }
      break;
    }
    case "haste":
      p.hasteUntil = now + s.durationMs; p.hasteMul = s.speed;
      break;
    case "stun_area":
      for (const o of livingOthers(room, p)) {
        if (Math.hypot(o.x - at.x, o.y - at.y) <= s.radius) api.stun(o, s.durationMs, now);
      }
      break;
    case "wall": {
      const len = Math.hypot(w.aim.x, w.aim.y) || 1;
      const nx = -w.aim.y / len, ny = w.aim.x / len;   // across the aim, not along it
      room.walls.push({
        x1: at.x - nx * 55, y1: at.y - ny * 55,
        x2: at.x + nx * 55, y2: at.y + ny * 55,
        until: now + s.durationMs
      });
      break;
    }
    case "seal_doors":
      room.sealedTemp.set(w.comp, now + s.durationMs);
      break;
    case "quake":
      for (const o of livingOthers(room, p)) {
        const c = compartmentAt(o.x, o.y);
        if (c && c.name === w.comp) { o.channel = null; o.proneUntil = now + s.durationMs; }
      }
      break;
    case "collapse": {
      // burying a corridor would cut the ship in two and strand the round
      if (isCorridor(w.comp)) break;
      room.round.sealed.add(w.comp);
      const a = room.round.artifacts.find((x) => x.room === w.comp && x.state === "open");
      if (a && R.lose(room.round, a.id, "zawal")) api.artifactLost(room, a, "zasypany");
      break;
    }
    case "douse":
      room.doused.set(w.comp, now + s.durationMs);
      break;
    case "erase_log":
      eraseLog(room.evidence, w.comp, { realId: p.id, act: room.round.act });
      break;
    case "plant_residue":
      addResidue(room.evidence, w.comp, {
        school: w.extra.school || "ogien", realId: p.id, t: now, fake: true
      });
      break;
    case "invisible":
      p.invisibleUntil = now + s.durationMs;
      break;
    case "disguise": {
      const other = livingOthers(room, p)
        .filter((o) => o.cls !== p.cls)
        .sort((a, b) => dist(p, a) - dist(p, b))[0];
      const asCls = w.extra.cls || (other && other.cls);
      if (asCls) { p.disguisedAs = asCls; p.disguiseUntil = now + s.durationMs; }
      break;
    }
    case "decoy": {
      // "a copy of the mage walks off": a stationary twin fools nobody, so
      // it inherits a heading and strolls until it fades
      const len = Math.hypot(w.aim.x, w.aim.y) || 1;
      const vx = (w.aim.x / len) * 1.15, vy = (w.aim.y / len) * 1.15;
      room.markers.push({
        kind: "decoy", x: Math.round(p.x), y: Math.round(p.y), vx, vy,
        dir: Math.abs(vx) > Math.abs(vy) ? (vx < 0 ? 1 : 2) : (vy < 0 ? 3 : 0),
        step: 0, phase: 0,
        cls: p.disguisedAs || p.cls, until: now + s.durationMs
      });
      break;
    }
    case "blind": {
      const t = nearestTarget(room, p, range);
      if (t) t.blindUntil = now + s.durationMs;
      break;
    }
    case "fake_silhouette":
      room.markers.push({
        kind: "fake-silhouette", room: w.comp,
        x: Math.round(p.x), y: Math.round(p.y),
        // a forged silhouette carries forged kit too: the base draws bodies
        // from the same sheet as the field, so a class with no item would be
        // the one figure on screen holding nothing
        cls: w.extra.cls || "Zwiadowca", it: 0, until: now + s.durationMs
      });
      break;
    default:
      throw new Error(`spell ${s.id} has no effect handler: ${s.effect}`);
  }
}

/** Fireballs and delayed blasts, integrated here so a client can never
 *  claim a hit it did not land. */
function stepProjectiles(room, now, api) {
  room.balls = room.balls.filter((b) => {
    b.x += b.vx; b.y += b.vy;
    const victim = [...room.players.values()].find(
      (o) => o.alive && !o.ejected && o.id !== b.by &&
        Math.hypot(o.x - b.x, o.y - b.y) < BALL_HIT_R
    );
    const outside = b.x < 0 || b.y < 0 || b.x > W || b.y > H;
    const spent = now - b.born > BALL_LIFE;
    if (victim || outside || spent) {
      api.fx(room, b.school, b.x, b.y);
      if (victim) api.hit(room, victim, room.players.get(b.by), b.school);
      return false;
    }
    return true;
  });

  room.delayed = room.delayed.filter((d) => {
    if (now < d.at) return true;
    api.fx(room, d.school, d.x, d.y);
    for (const o of room.players.values()) {
      if (!o.alive || o.ejected || o.id === d.by) continue;
      if (Math.hypot(o.x - d.x, o.y - d.y) <= d.r) api.hit(room, o, room.players.get(d.by), d.school);
    }
    return false;
  });

  room.walls = room.walls.filter((w) => w.until > now);

  // decoys walk, and stop at a wall rather than strolling into vacuum
  for (const m of room.markers) {
    if (m.kind !== "decoy" || !m.vx) continue;
    if (free(m.x + m.vx, m.y + m.vy, 12, { sealed: new Set(), walls: [], act: room.round.act })) {
      m.x += m.vx; m.y += m.vy;
      m.phase += 1.15;
      m.step = Math.floor(m.phase / 10) % 2;
    } else {
      m.vx = 0; m.vy = 0;
    }
  }
  room.markers = room.markers.filter((m) => m.until > now);
  room.pings = room.pings.filter((p) => p.until > now);
}

module.exports = { beginCast, interrupt, resolveCast, stepProjectiles, charge };

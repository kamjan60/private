"use strict";
/**
 * What a body can do: move, taser, channel, use its one item, and ping.
 *
 * Movement is integrated here from input vectors, never from client-reported
 * positions, so a patched client cannot walk onto an artifact or into taser
 * range. Crossing a compartment threshold writes a transit entry -- that
 * write is the single most important line in the file, because it is where
 * the evidence game gets its raw material and where a disguise poisons it.
 */

const {
  SPEED_BASE, TASER_STUN_MS, TASER_COOLDOWN, MARKSMAN_RANGE,
  BIND_MS, BIND_MS_SHACKLES, EXTRACT_MS, EXTRACT_MS_FAST,
  PING_COOLDOWN, PING_MS, PING_KINDS, CORRIDOR_ARM_MS, CORRIDOR_SHUT_MS
} = require("./rules");
const { findItem } = require("./classes");
const { free, compartmentAt, isCorridor } = require("./map");
const { logTransit, makeCorpse } = require("./evidence");
const { apparentClass, pushEvent, alive, hunters } = require("./room");
const { interrupt } = require("./effects");
const T = require("./tribunal");
const R = require("./round");
const B = require("./base");

const dist = (a, b) => Math.hypot(a.x - b.x, a.y - b.y);

// ------------------------------------------------------------------ movement

function collisionState(room, now) {
  const sealed = new Set(room.round.sealed);
  for (const [c, until] of room.sealedTemp) if (until > now) sealed.add(c);
  // a corridor is only solid once its warning has run out
  for (const [c, cyc] of room.cycling) {
    if (now >= cyc.shutAt && now < cyc.until) sealed.add(c);
  }
  // the act gates the decks: a zone belonging to a later section is simply
  // not floor yet, so no separate bulkhead state is needed
  return { sealed, walls: room.walls, act: room.round.act };
}

/**
 * Step one player. Slides along walls rather than sticking to them, because
 * a corridor you cannot round a corner in is a corridor nobody uses.
 */
function step(room, p, now) {
  if (now < p.stunUntil || now < p.proneUntil) { p.channel = null; return; }

  const ix = p.input.x, iy = p.input.y;
  const len = Math.hypot(ix, iy);
  if (len <= 0.01) return;

  let sp = SPEED_BASE * p.stats.speed;
  if (p.hasteUntil > now) sp *= p.hasteMul;
  if (p.slowUntil > now) sp *= p.slowMul;

  const nx = (ix / len) * sp, ny = (iy / len) * sp;
  const st = collisionState(room, now);
  const before = p.comp;

  if (free(p.x + nx, p.y + ny, 12, st)) { p.x += nx; p.y += ny; }
  else if (free(p.x + nx, p.y, 12, st)) { p.x += nx; }
  else if (free(p.x, p.y + ny, 12, st)) { p.y += ny; }
  else return;

  p.dir = Math.abs(nx) > Math.abs(ny) ? (nx < 0 ? 1 : 2) : (ny < 0 ? 3 : 0);
  p.phase += sp;
  p.step = Math.floor(p.phase / 10) % 2;
  if (p.channel) p.channel = null;   // channels break on movement, always

  /*
   * Stepping into a corridor slams both hatches for a couple of seconds.
   * That is what makes a corridor a killing box rather than a shortcut: if
   * the mage followed you in, you are shut in with him.
   *
   * It fires only once the body is clear of the doorway. Sealing the moment
   * they cross would close the wall on top of them and leave them standing
   * inside it, unable to move in any direction.
   */
  if (p.enteringHall) {
    const z = compartmentAt(p.x, p.y);
    if (!z || z.name !== p.enteringHall) {
      p.enteringHall = null;
    } else {
      const deep = Math.min(p.x - z.x, z.x + z.w - p.x, p.y - z.y, z.y + z.h - p.y);
      if (deep > 20) {
        const cyc = room.cycling.get(z.name);
        if (!cyc || cyc.until <= now) {
          room.cycling.set(z.name, {
            shutAt: now + CORRIDOR_ARM_MS,
            until: now + CORRIDOR_ARM_MS + CORRIDOR_SHUT_MS
          });
        }
        p.enteringHall = null;
      }
    }
  }

  const comp = compartmentAt(p.x, p.y);
  const name = comp ? comp.name : null;
  if (name !== before) {
    // The sensors log what they saw, and a disguised mage is seen as
    // somebody else. This is the forgery the whole investigation runs on.
    if (before) {
      logTransit(room.evidence, before, {
        realId: p.id, apparentClass: apparentClass(p), kind: "out",
        act: room.round.act, t: now
      });
    }
    if (name) {
      logTransit(room.evidence, name, {
        realId: p.id, apparentClass: apparentClass(p), kind: "in",
        act: room.round.act, t: now
      });
      fireSensors(room, p, name, now);
      // armed on entry, fired a step later once they are clear of the doorway
      p.enteringHall = isCorridor(name) ? name : null;
    }
    p.comp = name;
  }
}

/** Zwiadowca's Czujnik ruchu. Reports a class, like everything else does. */
function fireSensors(room, p, compName, now) {
  for (const s of room.markers) {
    if (s.kind !== "sensor" || s.room !== compName || s.until <= now) continue;
    if (s.by === p.id) continue;
    room.pings.push({
      kind: "czujnik", by: s.by, byName: "Czujnik", room: compName,
      x: s.x, y: s.y, cls: apparentClass(p), until: now + PING_MS
    });
  }
}

// ------------------------------------------------------------------ damage

/** Zimna krew, vests and the Guardian's second wind all live here. */
function stun(p, ms, now) {
  if (p.stunImmune) { p.stunImmune = false; return false; }
  p.stunUntil = Math.max(p.stunUntil, now + ms);
  p.channel = null;
  interrupt(p);
  return true;
}

function hit(room, target, source, school, api) {
  const now = Date.now();
  if (!target.alive || target.ejected) return;

  if (target.vests > 0) {
    target.vests--;
    pushEvent(room, `${target.name} stracił kamizelkę.`, "hurt");
    return;
  }
  if (target.item === "tarcza" && now >= target.itemReadyAt) {
    const it = findItem(target.cls, "tarcza");
    target.itemReadyAt = now + it.cooldown;
    pushEvent(room, `${target.name} przyjął zaklęcie na tarczę.`, "hurt");
    return;
  }

  target.hp--;
  if (target.hp > 0) {
    pushEvent(room, `${target.name} przyjął zaklęcie i utrzymał się na nogach.`, "hurt");
    return;
  }

  target.down = true;
  target.alive = false;
  target.channel = null;
  room.corpses.push(makeCorpse({
    x: Math.round(target.x), y: Math.round(target.y),
    cls: target.cls, name: target.name,
    id: Number(String(target.id).replace(/\D/g, "")) || 1,
    school, t: now
  }));
  pushEvent(room, `${target.name} przestał odpowiadać.`, "kill");
  api.toBase(room, target);
}

// ------------------------------------------------------------------ taser

function taser(room, p, aim, now) {
  if (!p.alive || p.ejected || room.phase !== "play") return { ok: false };
  if (now < p.taserReadyAt) return { ok: false, why: "Tazer się ładuje." };
  if (now < p.stunUntil || now < p.proneUntil) return { ok: false };

  const rifle = p.item === "karabin" && p.itemCharges > 0;
  const range = rifle ? MARKSMAN_RANGE : p.stats.taser;
  const len = Math.hypot(aim.x, aim.y) || 1;

  let best = null, bd = range;
  for (const o of room.players.values()) {
    if (!o.alive || o.ejected  || o.id === p.id) continue;
    const d = dist(p, o);
    if (d > bd) continue;
    // must be roughly in front, so a taser is aimed rather than a radius
    const dot = ((o.x - p.x) * aim.x + (o.y - p.y) * aim.y) / ((d || 1) * len);
    if (dot < 0.35 && d > 40) continue;
    bd = d; best = o;
  }

  p.taserReadyAt = now + TASER_COOLDOWN;
  if (rifle) p.itemCharges--;
  if (!best) return { ok: true, hit: null };

  const casting = !!best.windup;
  const landed = stun(best, TASER_STUN_MS, now);
  if (casting && landed) {
    pushEvent(room, `${best.name} został przerwany w pół gestu.`, "cast");
  }
  return { ok: true, hit: best.id, interrupted: casting, landed };
}

// ------------------------------------------------------------------ channels

/**
 * One button, three jobs, decided by what you are standing next to:
 * extract an artifact, bind a stunned player, stabilise a downed hunter.
 * All three break on movement, which is what makes them a commitment.
 */
function hold(room, p, now) {
  if (!p.alive || p.ejected || room.phase !== "play") return;
  if (now < p.stunUntil || now < p.proneUntil || now < p.silenceUntil) { p.channel = null; return; }
  if (p.channel) return;

  const stunnedNear = [...room.players.values()].find(
    (o) => o.alive && !o.ejected && o.id !== p.id &&
      o.stunUntil > now && dist(p, o) < 46
  );
  if (stunnedNear) {
    const can = T.canBind(room.tribunal, stunnedNear.id, now);
    if (!can.ok) return { blocked: can.why };
    const ms = p.stats.bindFast ? BIND_MS_SHACKLES : BIND_MS;
    p.channel = { kind: "bind", targetId: stunnedNear.id, start: now, ms };
    return;
  }

  const art = room.round.artifacts.find(
    (a) => a.state === "open" && a.act <= room.round.act && dist(p, a) < 44
  );
  if (art) {
    const ms = p.stats.extractFast ? EXTRACT_MS_FAST : EXTRACT_MS;
    p.channel = { kind: "extract", targetId: art.id, start: now, ms };
    return;
  }

  if (p.item === "stabilizator" && p.itemCharges > 0) {
    const body = room.corpses.find((c) => dist(p, c) < 44);
    if (body) {
      const target = [...room.players.values()].find((o) => o.name === body.name);
      if (target && !target.alive && !target.ejected) {
        p.channel = { kind: "stabilise", targetId: target.id, start: now, ms: 2600 };
      }
    }
  }
}

function finishChannel(room, p, now, api) {
  const ch = p.channel;
  p.channel = null;
  if (!ch) return null;

  if (ch.kind === "extract") {
    const a = R.secure(room.round, ch.targetId);
    if (!a) return null;
    pushEvent(room, `${p.name} zabezpieczył artefakt: ${a.room}.`, "artifact");
    // Extraction dumps the compartment's log for this act. The errand and
    // the evidence are the same errand, which is why nobody has to make a
    // second trip to a terminal.
    return { kind: "extract", artifact: a, log: a.room };
  }

  if (ch.kind === "bind") {
    const target = room.players.get(ch.targetId);
    if (!target || !target.alive || target.ejected) return null;
    const can = T.canBind(room.tribunal, target.id, now);
    if (!can.ok) return null;
    T.open(room.tribunal, { accusedId: target.id, accuserId: p.id, now });
    room.phase = "tribunal";
    pushEvent(room, `${p.name} związał ${target.name}. Trybunał.`, "start");
    return { kind: "tribunal", accused: target, accuser: p };
  }

  if (ch.kind === "stabilise") {
    const target = room.players.get(ch.targetId);
    if (!target || target.alive || target.ejected) return null;
    p.itemCharges--;
    target.alive = true; target.down = false; target.hp = 1;
    room.corpses = room.corpses.filter((c) => c.name !== target.name);
    pushEvent(room, `${p.name} postawił ${target.name} na nogi.`, "good");
    return { kind: "stabilise", target };
  }
  return null;
}

// ------------------------------------------------------------------ items

function useItem(room, p, payload, now) {
  if (!p.alive || p.ejected || room.phase !== "play") return { ok: false };
  const it = findItem(p.cls, p.item);
  if (!it || it.kind !== "active") return { ok: false, why: "Ten przedmiot działa sam." };
  // spent by holding over a body, so say that rather than falling through to
  // the unknown-item branch and calling the player's own kit unrecognised
  if (it.viaChannel) return { ok: false, why: "Stań nad rannym i przytrzymaj." };
  if (p.itemCharges <= 0) return { ok: false, why: "Zużyte." };

  const comp = compartmentAt(p.x, p.y);
  const spend = () => { p.itemCharges--; };

  switch (p.item) {
    case "kamizelki": {
      const near = [...room.players.values()].find(
        (o) => o.alive && !o.ejected && o.id !== p.id && dist(p, o) < 60
      );
      if (!near) return { ok: false, why: "Nikogo obok." };
      near.vests++; spend();
      pushEvent(room, `${p.name} dał kamizelkę: ${near.name}.`, "good");
      return { ok: true };
    }
    case "kotwica": {
      const a = payload.aim || { x: 1, y: 0 };
      const len = Math.hypot(a.x, a.y) || 1;
      const nx = -a.y / len, ny = a.x / len;
      room.walls.push({
        x1: p.x - nx * 50, y1: p.y - ny * 50, x2: p.x + nx * 50, y2: p.y + ny * 50,
        until: now + it.durationMs
      });
      spend(); return { ok: true };
    }
    case "dron":
      if (!payload.room) return { ok: false, why: "Wskaż przedział." };
      room.markers.push({ kind: "drone", room: payload.room, by: p.id, until: now + it.durationMs });
      spend(); return { ok: true };
    case "czujnik":
      if (!comp) return { ok: false, why: "Musisz stać w przedziale." };
      room.markers.push({
        kind: "sensor", room: comp.name, by: p.id,
        x: Math.round(p.x), y: Math.round(p.y), until: now + 600000
      });
      spend(); return { ok: true };
    case "siatka": {
      const at = payload.aim
        ? { x: p.x + payload.aim.x * 120, y: p.y + payload.aim.y * 120 } : { x: p.x, y: p.y };
      for (const o of room.players.values()) {
        if (!o.alive || o.ejected || o.id === p.id) continue;
        if (Math.hypot(o.x - at.x, o.y - at.y) <= it.radius) {
          o.slowUntil = now + it.durationMs; o.slowMul = 0.4;
        }
      }
      spend(); return { ok: true };
    }
    case "znacznik": {
      const t = room.players.get(payload.targetId);
      if (!t || !t.alive || t.ejected) return { ok: false, why: "Brak celu." };
      room.markers.push({
        kind: "tag", targetId: t.id, by: p.id, until: now + it.durationMs
      });
      spend(); return { ok: true };
    }
    case "stymulanty":
      p.hasteUntil = now + it.durationMs; p.hasteMul = 1.4;
      spend(); return { ok: true };
    case "pieczec": {
      const a = room.round.artifacts.find(
        (x) => x.state === "open" && x.act <= room.round.act && dist(p, x) < 44
      );
      if (!a) return { ok: false, why: "Brak artefaktu obok." };
      if (!R.sealWithRune(room.round, a.id)) return { ok: false, why: "Już opieczętowany." };
      spend(); return { ok: true };
    }
    case "zaklocacz":
      if (!comp) return { ok: false, why: "Musisz stać w przedziale." };
      if (!room.jammed) room.jammed = new Map();
      room.jammed.set(comp.name, now + it.durationMs);
      spend(); return { ok: true };
    case "kopia": {
      if (!comp) return { ok: false, why: "Musisz stać w przedziale." };
      require("./evidence").copyLog(room.evidence, comp.name, room.round.act);
      spend(); return { ok: true, copied: comp.name };
    }
    case "generator":
      if (!comp) return { ok: false, why: "Musisz stać w przedziale." };
      room.lit.set(comp.name, now + it.durationMs);
      spend(); return { ok: true };
    case "kamera":
      if (!comp) return { ok: false, why: "Musisz stać w przedziale." };
      B.addFieldCamera(room.base, comp.name);
      spend(); return { ok: true };
    case "rygiel":
      if (!comp) return { ok: false, why: "Musisz stać w przedziale." };
      room.sealedTemp.set(comp.name, now + it.durationMs);
      spend(); return { ok: true };
    case "karabin":
      return { ok: false, why: "Karabin strzela tazerem." };
    default:
      return { ok: false, why: "Nieznany przedmiot." };
  }
}

// ------------------------------------------------------------------ pings

function ping(room, p, { kind, x, y, targetId }, now) {
  if (!PING_KINDS.includes(kind)) return { ok: false };
  if (now < p.lastPingAt + PING_COOLDOWN) return { ok: false, why: "Za szybko." };
  if (now < p.silenceUntil) return { ok: false, why: "Cisza." };
  p.lastPingAt = now;
  const comp = compartmentAt(x, y);
  room.pings.push({
    kind, by: p.id, byName: p.name, targetId: targetId || null,
    x: Math.round(x), y: Math.round(y), room: comp ? comp.name : null,
    until: now + PING_MS
  });
  return { ok: true };
}

module.exports = { step, stun, hit, taser, hold, finishChannel, useItem, ping, collisionState };

"use strict";
/**
 * What each player is allowed to know, built fresh for every one of them.
 *
 * The dark overlay in the renderer is a vignette over data the client was
 * never sent -- it is not the security. Culling happens here, before
 * anything is serialised, so stripping the fog client-side reveals nothing
 * and a patched client learns no more than an honest one.
 *
 * Two things never leave this file under any circumstances: who the mage is,
 * and the real player id behind a transit-log entry.
 */

const { W, H } = require("./rules");
const { visionMult } = require("./round");
const { apparentClass } = require("./room");
const { liveCameras } = require("./base");
const { compartmentAt } = require("./map");

/** How far this player can see right now, after the act, the lights and
 *  whatever has been done to their eyes. */
function visionOf(room, p, now) {
  let r = p.stats.vision * visionMult(room.round);
  if (p.blindUntil > now) r *= 0.25;
  const comp = compartmentAt(p.x, p.y);
  if (comp) {
    if ((room.doused.get(comp.name) || 0) > now) r *= 0.45;
    if ((room.lit.get(comp.name) || 0) > now) r = p.stats.vision;   // full, act aside
  }
  return r;
}

/** A body as somebody else sees it: apparent class, no role, no book. */
function actorView(o, now) {
  return {
    id: o.id, name: o.name, cls: apparentClass(o),
    x: Math.round(o.x), y: Math.round(o.y), dir: o.dir, step: o.step,
    stunned: o.stunUntil > now, down: o.down,
    channel: o.channel ? o.channel.kind : null,
    casting: !!o.windup
  };
}

/** A camera feed: silhouettes only. The base is told a class and a position
 *  and nothing that would let it put a name to either. */
function silhouette(o) {
  return {
    cls: apparentClass(o), x: Math.round(o.x), y: Math.round(o.y),
    dir: o.dir, step: o.step
  };
}

function forLiving(room, me, now) {
  const r = visionOf(room, me, now);
  const near = (o) => Math.hypot(o.x - me.x, o.y - me.y) <= r;

  const actors = [];
  for (const o of room.players.values()) {
    if (!o.alive || o.ejected) continue;
    if (o.id === me.id) { actors.push(actorView(o, now)); continue; }
    if (o.invisibleUntil > now) continue;
    if (!near(o)) continue;
    actors.push(actorView(o, now));
  }

  return {
    me: {
      id: me.id, cls: me.cls, role: me.role, item: me.item,
      hp: me.hp, vests: me.vests, vision: Math.round(r),
      stunUntil: me.stunUntil, silenceUntil: me.silenceUntil,
      itemCharges: me.itemCharges, itemReadyAt: me.itemReadyAt,
      taserReadyAt: me.taserReadyAt, castReadyAt: me.castReadyAt,
      // the book, with what is left in it -- only ever sent to its owner
      book: me.role === "mage" ? me.book.map((b) => ({ ...b })) : null,
      channel: me.channel ? { kind: me.channel.kind, start: me.channel.start, ms: me.channel.ms } : null,
      windup: me.windup ? { spell: me.windup.spellId, at: me.windup.at } : null
    },
    actors,
    corpses: room.corpses.filter(near).map((c) => ({
      id: c.id, x: c.x, y: c.y, cls: c.cls, name: c.name
    })),
    artifacts: room.round.artifacts
      .filter((a) => a.act <= room.round.act && near(a))
      .map((a) => ({ id: a.id, x: a.x, y: a.y, state: a.state, sealed: a.sealedByRune })),
    balls: room.balls.filter(near).map((b) => ({ x: Math.round(b.x), y: Math.round(b.y), school: b.school })),
    walls: room.walls.map((w) => ({ ...w })),
    markers: room.markers.filter((m) => m.until > now).map((m) => ({ ...m })),
    pings: room.pings.filter((p) => p.until > now).map((p) => ({ ...p })),
    sealed: [...room.sealedTemp.entries()].filter(([, u]) => u > now).map(([c]) => c)
      .concat([...room.round.sealed]),
    cycling: [...room.cycling.entries()].filter(([, u]) => u > now)
      .map(([c, u]) => ({ room: c, until: u })),
    doused: [...room.doused.entries()].filter(([, u]) => u > now).map(([c]) => c),
    lit: [...room.lit.entries()].filter(([, u]) => u > now).map(([c]) => c)
  };
}

/**
 * The base sees only what its cameras see. It gets no `me` body, no artifact
 * positions it has not got a lens on, and above all no roles.
 */
function forBase(room, me, now) {
  const live = new Set(liveCameras(room.base));
  const watching = (room.base.watching.get(me.id) || []).filter((c) => live.has(c));
  const feeds = watching.map((name) => {
    const bodies = [];
    for (const o of room.players.values()) {
      if (!o.alive || o.ejected) continue;
      if (o.invisibleUntil > now) continue;
      const comp = compartmentAt(o.x, o.y);
      if (!comp || comp.name !== name) continue;
      bodies.push(silhouette(o));
    }
    // Fałszywa sylwetka: the mage feeds the base a class that is not there
    for (const f of room.markers) {
      if (f.kind === "fake-silhouette" && f.room === name && f.until > now) {
        bodies.push({ cls: f.cls, x: f.x, y: f.y, dir: 0, step: 0 });
      }
    }
    return { room: name, bodies };
  });

  return {
    me: { id: me.id, cls: me.cls, role: "base", base: true },
    base: {
      charges: room.base.charges,
      cameras: liveCameras(room.base),
      watching
    },
    feeds,
    corpses: room.corpses.map((c) => ({ id: c.id, x: c.x, y: c.y, cls: c.cls, name: c.name })),
    artifacts: room.round.artifacts
      .filter((a) => a.act <= room.round.act)
      .map((a) => ({ id: a.id, x: a.x, y: a.y, state: a.state, room: a.room })),
    sealed: [...room.sealedTemp.entries()].filter(([, u]) => u > now).map(([c]) => c)
      .concat([...room.round.sealed]),
    lit: [...room.lit.entries()].filter(([, u]) => u > now).map(([c]) => c)
  };
}

/** The parts of the round everybody may see, dead or alive. */
function common(room, now) {
  return {
    t: "state", tick: room.tick, phase: room.phase,
    act: room.round.act, actEndsAt: room.round.actStartedAt + require("./rules").ACT_MS,
    secured: room.round.secured, lost: room.round.lost,
    toWin: require("./rules").ARTIFACTS_TO_WIN,
    pathClosed: require("./round").pathClosed(room.round),
    hunters: [...room.players.values()].filter((p) => p.alive && !p.ejected).length,
    events: room.events.slice(-6),
    w: W, h: H
  };
}

function snapshotFor(room, me, now) {
  const base = common(room, now);
  const view = (!me.alive || me.ejected) ? forBase(room, me, now) : forLiving(room, me, now);
  return Object.assign(base, view);
}

module.exports = { snapshotFor, visionOf, forLiving, forBase, common };

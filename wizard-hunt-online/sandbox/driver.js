"use strict";
/**
 * Single-player driver: the real rules, in the page, with no server.
 *
 * An Artifact cannot hold the online game -- its CSP blocks outbound
 * WebSockets and there is no shared state between viewers. So instead of
 * reimplementing the game in a toy, this bundles the actual src/ modules and
 * speaks the same message protocol the client already knows, with a local
 * tick loop and bots in the other seats.
 *
 * That means the range is not an approximation. The evidence, the charges,
 * the wind-up, the tribunal arithmetic and the fog culling are the shipped
 * code; only the transport is fake.
 */

const RULES = require("./rules");
const Room = require("./room");
const A = require("./actions");
const E = require("./effects");
const R = require("./round");
const T = require("./tribunal");
const B = require("./base");
const { readLog, readResidue, readCorpse } = require("./evidence");
const { snapshotFor } = require("./snapshot");
const { compartmentAt, free, COMPARTMENTS, wallsOf } = require("./map");
const { CLASSES, CLASS_NAMES, itemsOf } = require("./classes");
const { SPELLS, SCHOOLS, PRESETS } = require("./spells");

const BOT_NAMES = ["Vessel", "Corvid", "Marrow", "Halden", "Tocsin", "Quill", "Aster"];

function makeDriver(onMessage, opts) {
  opts = opts || {};
  const room = Room.makeRoom();
  const outbox = [];
  let human = null;
  let timer = null;

  const now = Room.now;
  const send = (p, m) => { if (p === human) outbox.push(m); };
  const broadcast = (m) => outbox.push(m);
  const flush = () => { while (outbox.length) onMessage(outbox.shift()); };

  const api = {
    hit: (rm, target, source, school) => A.hit(rm, target, source, school, api),
    stun: (p, ms, t) => A.stun(p, ms, t),
    move: (p, x, y) => {
      const st = A.collisionState(room, now());
      if (free(x, y, 12, st)) { p.x = x; p.y = y; }
    },
    fx: (rm, school, x, y) => broadcast({ t: "fx", school, x: Math.round(x), y: Math.round(y) }),
    artifactLost: (rm, a, how) => Room.pushEvent(rm, `Artefakt w ${a.room} — ${how}.`, "bad"),
    toBase: (rm, p) => { send(p, { t: "toBase" }); B.watch(rm.base, p.id, []); }
  };

  // ------------------------------------------------------------ seats
  function seat(name) {
    const p = Room.makePlayer("p" + room.nextId++, name, null);
    p.room = room;
    room.players.set(p.id, p);
    if (!room.hostId) room.hostId = p.id;
    return p;
  }

  human = seat(opts.name || "Ty");
  const count = Math.max(RULES.MIN_PLAYERS, Math.min(RULES.MAX_PLAYERS, opts.players || 6));
  for (let i = 1; i < count; i++) seat(BOT_NAMES[(i - 1) % BOT_NAMES.length]);
  const bots = () => Room.list(room).filter((p) => p !== human);

  function hello() {
    send(human, {
      t: "joined", id: human.id, room: room.id, host: true,
      classes: CLASS_NAMES.map((n) => ({ name: n, ...CLASSES[n], items: itemsOf(n) })),
      spells: SPELLS, schools: SCHOOLS, presets: PRESETS, slots: RULES.BOOK_SLOTS,
      map: COMPARTMENTS.map((c) => ({
        name: c.name, section: c.section, x: c.x, y: c.y, w: c.w, h: c.h,
        walls: wallsOf(c, false)
      })),
      w: RULES.W, h: RULES.H, sandbox: true
    });
    broadcast({
      t: "lobby", host: human.id, phase: "lobby",
      min: RULES.MIN_PLAYERS, max: RULES.MAX_PLAYERS,
      players: Room.list(room).map((p) => ({ id: p.id, name: p.name }))
    });
    flush();
  }

  // ------------------------------------------------------------ loadout
  function begin(forceRole) {
    const r = Room.startLoadout(room);
    if (!r.ok) { send(human, { t: "error", msg: r.why }); flush(); return; }

    // The range exists so you can try being the mage on purpose; a one-in-six
    // roll would make that a chore rather than a choice.
    if (forceRole === "mage" && human.role !== "mage") swapMage(human);
    if (forceRole === "hunter" && human.role === "mage") swapMage(bots()[0]);

    send(human, {
      t: "loadout", cls: human.cls, role: human.role, items: itemsOf(human.cls),
      endsAt: room.loadoutEndsAt, slots: RULES.BOOK_SLOTS
    });
    flush();
  }

  function swapMage(to) {
    const old = Room.theMage(room);
    if (old) old.role = "hunter";
    to.role = "mage";
  }

  function choose(itemId, book) {
    if (!Room.chooseLoadout(room, human, { itemId, book })) {
      send(human, { t: "error", msg: "Zły wybór wyposażenia." });
      flush(); return;
    }
    send(human, { t: "loadoutOk" });
    Room.fillMissingLoadouts(room);
    start();
  }

  function start() {
    Room.startRound(room);
    send(human, {
      t: "role", role: human.role, cls: human.cls, item: human.item,
      book: human.role === "mage" ? human.book : null, perk: CLASSES[human.cls].blurb
    });
    broadcast({ t: "act", act: 0, endsAt: room.round.actStartedAt + RULES.ACT_MS });
    flush();
    if (timer) clearInterval(timer);
    timer = setInterval(tick, RULES.TICK_MS);
  }

  // ------------------------------------------------------------ bots
  const wander = new Map();

  function driveBots(t) {
    for (const p of bots()) {
      if (!p.alive || p.ejected) continue;
      let w = wander.get(p.id);
      if (!w || t > w.until) {
        // head for an unclaimed artifact when there is one, otherwise drift
        const art = room.round.artifacts.filter(
          (a) => a.state === "open" && a.act <= room.round.act
        )[0];
        const tx = art ? art.x : Math.random() * RULES.W;
        const ty = art ? art.y : Math.random() * RULES.H;
        w = { tx, ty, until: t + 2500 + Math.random() * 2500 };
        wander.set(p.id, w);
      }
      const dx = w.tx - p.x, dy = w.ty - p.y;
      const d = Math.hypot(dx, dy) || 1;
      if (d < 40) {
        p.input.x = 0; p.input.y = 0;
        p.holding = true;                 // stand on it and extract
      } else {
        p.input.x = dx / d; p.input.y = dy / d;
        p.holding = false;
      }
    }
  }

  // ------------------------------------------------------------ tick
  function tick() {
    const t = now();

    if (room.phase === "tribunal") {
      const living = Room.alive(room).map((p) => p.id);
      // bots make up their minds quickly and at random: this is a range, not
      // an opponent, and a real read is what the voice channel is for
      for (const p of bots()) {
        if (!p.alive || p.ejected) continue;
        if (!room.tribunal.active.votes.has(p.id)) {
          T.vote(room.tribunal, p.id, Math.random() < 0.45 ? "tak" : "nie");
        }
      }
      if (T.expired(room.tribunal, t) || T.everyoneVoted(room.tribunal, living)) verdict(living, t);
      flush();
      return;
    }
    if (room.phase !== "play") { flush(); return; }

    room.tick++;
    driveBots(t);

    for (const p of room.players.values()) {
      if (!p.alive || p.ejected) continue;
      if (p.windup && t >= p.windup.at) {
        const done = E.resolveCast(room, p, t, api);
        if (done) broadcast({ t: "fx", school: done.spell.school, x: Math.round(p.x), y: Math.round(p.y) });
      }
      A.step(room, p, t);
      if (p.holding) A.hold(room, p, t); else p.channel = null;
      if (p.channel && t - p.channel.start >= p.channel.ms) {
        const out = A.finishChannel(room, p, t, api);
        if (out && out.kind === "extract" && p === human) sendLog(out.log, t);
        if (out && out.kind === "tribunal") { openTribunal(out, t); flush(); return; }
      }
      if (p.disguiseUntil && t > p.disguiseUntil) { p.disguisedAs = null; p.disguiseUntil = 0; }
    }

    E.stepProjectiles(room, t, api);

    if (R.actOver(room.round, t)) {
      const adv = R.advanceAct(room.round, t);
      if (adv) {
        B.onAct(room.base, adv.act);
        const names = ["I — Rozpoznanie", "II — Awaria", "III — Ciemność"];
        Room.pushEvent(room, `Akt ${names[adv.act]}. Straconych: ${room.round.lost}.`, "start");
        broadcast({ t: "act", act: adv.act, endsAt: room.round.actStartedAt + RULES.ACT_MS });
      }
    }

    const w = R.checkWin(room.round, {
      mageEjected: false, hunterCount: Room.hunters(room).length, now: t
    });
    if (w) { broadcast(Room.endRound(room, w.winner, w.msg)); clearInterval(timer); }

    send(human, snapshotFor(room, human, t));
    flush();
  }

  function sendLog(compName, t) {
    send(human, {
      t: "log", room: compName, act: room.round.act,
      entries: readLog(room.evidence, compName, {
        act: room.round.act, filterLogs: human.stats.filterLogs, now: t
      }),
      residue: readResidue(room.evidence, compName, {
        now: t, residueAct: human.stats.residueAct, actStart: room.round.actStartedAt
      })
    });
  }

  function openTribunal(out, t) {
    broadcast({
      t: "tribunal",
      accused: { id: out.accused.id, name: out.accused.name, cls: out.accused.cls },
      accuser: { id: out.accuser.id, name: out.accuser.name, cls: out.accuser.cls },
      endsAt: t + RULES.TRIBUNAL_VOTE_MS,
      voters: Room.alive(room).map((p) => ({ id: p.id, name: p.name }))
    });
  }

  function verdict(living, t) {
    const res = T.resolve(room.tribunal, living, t);
    room.phase = "play";
    if (!res) return;
    const accused = room.players.get(res.accusedId);
    let mageEjected = false;
    if (res.convicted && accused) {
      accused.ejected = true; accused.alive = false; accused.channel = null;
      mageEjected = accused.role === "mage";
      Room.pushEvent(room, `${accused.name} odesłany do bazy.`, mageEjected ? "good" : "bad");
      api.toBase(room, accused);
    } else if (accused) {
      Room.pushEvent(room, `${accused.name} wypuszczony.`, "stun");
    }
    broadcast({
      t: "verdict", convicted: res.convicted,
      accused: accused ? { id: accused.id, name: accused.name } : null,
      counts: res.counts, cast: res.cast
    });
    const w = R.checkWin(room.round, {
      mageEjected, hunterCount: Room.hunters(room).length, now: t
    });
    if (w) { broadcast(Room.endRound(room, w.winner, w.msg)); clearInterval(timer); }
  }

  // ------------------------------------------------------------ inbox
  function handle(m) {
    const t = now();
    switch (m.t) {
      case "join": hello(); break;
      case "start": begin(m.as); break;
      case "loadout": choose(m.item, m.book); break;
      case "input":
        human.input.x = Math.max(-1, Math.min(1, Number(m.x) || 0));
        human.input.y = Math.max(-1, Math.min(1, Number(m.y) || 0));
        human.holding = !!m.hold;
        break;
      case "taser": {
        const r = A.taser(room, human, { x: Number(m.ax) || 1, y: Number(m.ay) || 0 }, t);
        if (r && r.why) send(human, { t: "toast", msg: r.why });
        break;
      }
      case "cast": {
        const r = E.beginCast(room, human, String(m.spell),
          { x: Number(m.ax) || 1, y: Number(m.ay) || 0 }, t, { cls: m.cls, school: m.school });
        if (!r.ok) { if (r.why) send(human, { t: "toast", msg: r.why }); break; }
        broadcast({ t: "windup", id: human.id, school: r.school, ms: r.castMs });
        break;
      }
      case "item": {
        const r = A.useItem(room, human, m, t);
        if (r && r.why) send(human, { t: "toast", msg: r.why });
        break;
      }
      case "ping": {
        const r = A.ping(room, human, {
          kind: String(m.kind), x: Number(m.x) || 0, y: Number(m.y) || 0, targetId: m.targetId
        }, t);
        if (r && r.why) send(human, { t: "toast", msg: r.why });
        break;
      }
      case "readLog": {
        if (!human.stats || !human.stats.readLogs) break;
        const c = compartmentAt(human.x, human.y);
        if (c) sendLog(c.name, t);
        break;
      }
      case "readCorpse": {
        const body = room.corpses.find((c) => c.id === Number(m.id));
        if (!body || !human.stats) break;
        send(human, {
          t: "corpse", id: body.id,
          read: readCorpse(body, {
            now: t, traceMult: human.stats.traceMult, exactTime: human.stats.exactTime
          })
        });
        break;
      }
      case "vote":
        if (room.phase === "tribunal") T.vote(room.tribunal, human.id, String(m.vote));
        break;
      case "watch":
        if (!human.alive || human.ejected) {
          send(human, { t: "watching", rooms: B.watch(room.base, human.id, m.rooms || []) });
        }
        break;
      case "door": if (!human.alive || human.ejected) B.toggleDoor(room.base, room, String(m.room), t); break;
      case "light": if (!human.alive || human.ejected) B.light(room.base, room, String(m.room), t); break;
      case "again": if (timer) clearInterval(timer); reset(); break;
    }
    flush();
  }

  function reset() {
    room.phase = "lobby";
    for (const p of room.players.values()) {
      p.alive = true; p.ejected = false; p.down = false; p.loadoutReady = false;
    }
    broadcast({
      t: "lobby", host: human.id, phase: "lobby",
      min: RULES.MIN_PLAYERS, max: RULES.MAX_PLAYERS,
      players: Room.list(room).map((p) => ({ id: p.id, name: p.name }))
    });
    flush();
  }

  return { handle, room, human };
}

module.exports = { makeDriver };

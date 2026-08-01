"use strict";
/**
 * I'm Not a Wizard, Harry -- http and websocket wiring, and the tick loop.
 *
 * The rules live in src/. This file owns transport and scheduling and
 * nothing else, which is the point of the split: the previous build was one
 * six-hundred-line file and the investigation game would not have fitted
 * inside it.
 *
 * The server is authoritative, and that includes the fog. Movement is
 * integrated from input vectors, casts are resolved and hit-tested here,
 * and every snapshot is culled per player before it is serialised.
 */

const http = require("http");
const fs = require("fs");
const path = require("path");
const { WebSocketServer } = require("ws");

const RULES = require("./src/rules");
const { TICK_MS, ACT_MS, MIN_PLAYERS, MAX_PLAYERS } = RULES;
const Room = require("./src/room");
const A = require("./src/actions");
const E = require("./src/effects");
const R = require("./src/round");
const T = require("./src/tribunal");
const B = require("./src/base");
const { readLog, readResidue, readCorpse } = require("./src/evidence");
const { snapshotFor } = require("./src/snapshot");
const { compartmentAt, free, ZONES, wallsOf } = require("./src/map");
const { CLASSES, CLASS_NAMES, itemsOf } = require("./src/classes");
const { SPELLS, SCHOOLS, PRESETS } = require("./src/spells");

const PORT = process.env.PORT || 8080;
const { rooms, now } = Room;

// ------------------------------------------------------------------ transport

const MIME = {
  ".html": "text/html", ".js": "text/javascript", ".css": "text/css",
  ".png": "image/png", ".ico": "image/x-icon", ".json": "application/json"
};

const server = http.createServer((req, res) => {
  const url = req.url === "/" ? "/index.html" : req.url.split("?")[0];
  const file = path.join(__dirname, "public", path.normalize(url).replace(/^(\.\.[/\\])+/, ""));
  fs.readFile(file, (err, data) => {
    if (err) { res.writeHead(404); res.end("nie ma"); return; }
    res.writeHead(200, { "Content-Type": MIME[path.extname(file)] || "application/octet-stream" });
    res.end(data);
  });
});

const wss = new WebSocketServer({ server });

const send = (p, m) => { if (p && p.ws && p.ws.readyState === 1) p.ws.send(JSON.stringify(m)); };
const broadcast = (room, m) => { for (const p of room.players.values()) send(p, m); };

function lobbyMsg(room) {
  return {
    t: "lobby", host: room.hostId, phase: room.phase,
    min: MIN_PLAYERS, max: MAX_PLAYERS,
    players: Room.list(room).map((p) => ({ id: p.id, name: p.name }))
  };
}

// ------------------------------------------------------------------ the api
// Callbacks the rules modules need to reach back into transport. Passing
// them in keeps src/ free of sockets entirely, which is what lets the rules
// be tested without one.

const api = {
  hit: (room, target, source, school) => A.hit(room, target, source, school, api),
  stun: (p, ms, t) => A.stun(p, ms, t),
  move: (p, x, y) => {
    const room = p.room;
    if (!room) return;
    const st = A.collisionState(room, now());
    if (free(x, y, 12, st)) { p.x = x; p.y = y; }
  },
  fx: (room, school, x, y) =>
    broadcast(room, { t: "fx", school, x: Math.round(x), y: Math.round(y) }),
  artifactLost: (room, a, how) =>
    Room.pushEvent(room, `Artefakt w ${a.room} — ${how}.`, "bad"),
  toBase: (room, p) => {
    send(p, { t: "toBase" });
    B.watch(room.base, p.id, []);
  }
};

// ------------------------------------------------------------------ tick

function stepRoom(room) {
  const t = now();

  if (room.phase === "loadout") {
    if (!Room.loadoutDone(room)) return;
    Room.startRound(room);
    for (const p of room.players.values()) {
      send(p, {
        t: "role", role: p.role, cls: p.cls, item: p.item,
        book: p.role === "mage" ? p.book : null, perk: CLASSES[p.cls].blurb
      });
    }
    broadcast(room, { t: "act", act: 0, endsAt: room.round.actStartedAt + ACT_MS });
    return;
  }

  if (room.phase === "tribunal") {
    const living = Room.alive(room).map((p) => p.id);
    if (T.expired(room.tribunal, t) || T.everyoneVoted(room.tribunal, living)) {
      resolveTribunal(room, living, t);
    }
    return;
  }

  if (room.phase !== "play") return;
  room.tick++;

  for (const p of room.players.values()) {
    if (!p.alive || p.ejected) continue;

    if (p.windup && t >= p.windup.at) {
      const done = E.resolveCast(room, p, t, api);
      if (done) {
        broadcast(room, {
          t: "fx", school: done.spell.school, x: Math.round(p.x), y: Math.round(p.y)
        });
      }
    }

    A.step(room, p, t);
    if (p.holding) A.hold(room, p, t); else p.channel = null;

    if (p.channel && t - p.channel.start >= p.channel.ms) {
      const out = A.finishChannel(room, p, t, api);
      if (out && out.kind === "extract") sendLog(room, p, out.log, t);
      if (out && out.kind === "tribunal") { openTribunal(room, out, t); return; }
    }

    if (p.disguiseUntil && t > p.disguiseUntil) { p.disguisedAs = null; p.disguiseUntil = 0; }
  }

  E.stepProjectiles(room, t, api);

  if (R.actOver(room.round, t)) {
    const adv = R.advanceAct(room.round, t);
    if (adv) {
      B.onAct(room.base, adv.act);
      const names = ["I — Rozpoznanie", "II — Awaria", "III — Ciemność"];
      Room.pushEvent(room,
        `Akt ${names[adv.act]}. Straconych artefaktów: ${room.round.lost}.`, "start");
      broadcast(room, { t: "act", act: adv.act, endsAt: room.round.actStartedAt + ACT_MS });
    }
  }

  const w = R.checkWin(room.round, {
    mageEjected: false, hunterCount: Room.hunters(room).length, now: t
  });
  if (w) broadcast(room, Room.endRound(room, w.winner, w.msg));
}

/**
 * Extraction hands over the compartment's log for this act. The errand and
 * the evidence are the same errand, so nobody has to make a second trip to
 * a terminal to learn anything.
 */
function sendLog(room, p, compName, t) {
  send(p, {
    t: "log", room: compName, act: room.round.act,
    entries: readLog(room.evidence, compName, {
      act: room.round.act, filterLogs: p.stats.filterLogs, now: t
    }),
    residue: readResidue(room.evidence, compName, {
      now: t, residueAct: p.stats.residueAct, actStart: room.round.actStartedAt
    })
  });
}

/** The vote screen carries the accused and the accuser and nothing else.
 *  The case is what people say out loud; a tribunal that showed the
 *  evidence would be an adding machine rather than an argument. */
function openTribunal(room, out, t) {
  broadcast(room, {
    t: "tribunal",
    accused: { id: out.accused.id, name: out.accused.name, cls: out.accused.cls },
    accuser: { id: out.accuser.id, name: out.accuser.name, cls: out.accuser.cls },
    endsAt: t + RULES.TRIBUNAL_VOTE_MS,
    voters: Room.alive(room).map((p) => ({ id: p.id, name: p.name }))
  });
}

function resolveTribunal(room, living, t) {
  const res = T.resolve(room.tribunal, living, t);
  room.phase = "play";
  if (!res) return;

  const accused = room.players.get(res.accusedId);
  let mageEjected = false;
  if (res.convicted && accused) {
    accused.ejected = true;
    accused.alive = false;
    accused.channel = null;
    mageEjected = accused.role === "mage";
    Room.pushEvent(room, `${accused.name} odesłany do bazy.`, mageEjected ? "good" : "bad");
    api.toBase(room, accused);
  } else if (accused) {
    Room.pushEvent(room, `${accused.name} wypuszczony.`, "stun");
  }

  broadcast(room, {
    t: "verdict", convicted: res.convicted,
    accused: accused ? { id: accused.id, name: accused.name } : null,
    counts: res.counts, cast: res.cast
  });

  const w = R.checkWin(room.round, {
    mageEjected, hunterCount: Room.hunters(room).length, now: t
  });
  if (w) broadcast(room, Room.endRound(room, w.winner, w.msg));
}

const loop = setInterval(() => {
  for (const room of rooms.values()) {
    try { stepRoom(room); } catch (e) { console.error(`[${room.id}]`, e); }
    if (room.phase === "play" || room.phase === "tribunal") {
      const t = now();
      for (const p of room.players.values()) {
        try { send(p, snapshotFor(room, p, t)); } catch (e) { console.error("snapshot", e); }
      }
    }
  }
}, TICK_MS);

// ------------------------------------------------------------------ sockets

wss.on("connection", (ws) => {
  let room = null, player = null;
  const fail = (msg) => ws.send(JSON.stringify({ t: "error", msg }));

  ws.on("message", (raw) => {
    let m;
    try { m = JSON.parse(raw); } catch { return; }
    const t = now();

    if (m.t === "join") {
      const name = String(m.name || "Bezimienny").slice(0, 16);
      if (m.room) {
        room = rooms.get(String(m.room).toUpperCase());
        if (!room) return fail("Nie ma takiego pokoju.");
        if (room.players.size >= MAX_PLAYERS) return fail(`Pokój pełny (${MAX_PLAYERS}).`);
        if (room.phase !== "lobby") return fail("Runda już trwa.");
      } else {
        room = Room.makeRoom();
      }
      player = Room.makePlayer("p" + room.nextId++, name, ws);
      player.room = room;
      room.players.set(player.id, player);
      if (!room.hostId) room.hostId = player.id;
      send(player, {
        t: "joined", id: player.id, room: room.id, host: room.hostId === player.id,
        classes: CLASS_NAMES.map((n) => ({ name: n, ...CLASSES[n], items: itemsOf(n) })),
        spells: SPELLS, schools: SCHOOLS, presets: PRESETS, slots: RULES.BOOK_SLOTS,
        // the map is public knowledge: it is the wreck, not information
        // about anybody in it, and the renderer needs the geometry
        map: ZONES.map((z) => ({
          name: z.name, kind: z.kind, section: z.section,
          x: z.x, y: z.y, w: z.w, h: z.h, walls: wallsOf(z, false)
        })),
        w: RULES.W, h: RULES.H
      });
      broadcast(room, lobbyMsg(room));
      return;
    }

    if (!room || !player) return;

    switch (m.t) {
      case "start": {
        if (player.id !== room.hostId || room.phase !== "lobby") break;
        const r = Room.startLoadout(room);
        if (!r.ok) { send(player, { t: "error", msg: r.why }); break; }
        for (const p of room.players.values()) {
          send(p, {
            t: "loadout", cls: p.cls, role: p.role, items: itemsOf(p.cls),
            endsAt: room.loadoutEndsAt, slots: RULES.BOOK_SLOTS
          });
        }
        break;
      }

      case "loadout":
        if (Room.chooseLoadout(room, player, { itemId: m.item, book: m.book })) {
          send(player, { t: "loadoutOk" });
          broadcast(room, {
            t: "ready",
            ready: Room.list(room).filter((p) => p.loadoutReady).length,
            of: room.players.size
          });
        } else {
          send(player, { t: "error", msg: "Zły wybór wyposażenia." });
        }
        break;

      case "input":
        player.input.x = Math.max(-1, Math.min(1, Number(m.x) || 0));
        player.input.y = Math.max(-1, Math.min(1, Number(m.y) || 0));
        player.holding = !!m.hold;
        break;

      case "taser": {
        const r = A.taser(room, player, { x: Number(m.ax) || 1, y: Number(m.ay) || 0 }, t);
        if (r && r.why) send(player, { t: "toast", msg: r.why });
        break;
      }

      case "cast": {
        const r = E.beginCast(
          room, player, String(m.spell),
          { x: Number(m.ax) || 1, y: Number(m.ay) || 0 }, t,
          { cls: m.cls, school: m.school, dist: m.d }
        );
        if (!r.ok) { if (r.why) send(player, { t: "toast", msg: r.why }); break; }
        // the tell: everyone with line of sight sees the bloom
        broadcast(room, { t: "windup", id: player.id, school: r.school, ms: r.castMs });
        break;
      }

      case "item": {
        const r = A.useItem(room, player, m, t);
        if (r && r.why) send(player, { t: "toast", msg: r.why });
        break;
      }

      case "ping": {
        const r = A.ping(room, player, {
          kind: String(m.kind), x: Number(m.x) || 0, y: Number(m.y) || 0, targetId: m.targetId
        }, t);
        if (r && r.why) send(player, { t: "toast", msg: r.why });
        break;
      }

      case "readLog": {
        if (!player.stats || !player.stats.readLogs) break;   // Archiwista only
        const c = compartmentAt(player.x, player.y);
        if (c) sendLog(room, player, c.name, t);
        break;
      }

      case "readCorpse": {
        const body = room.corpses.find((c) => c.id === Number(m.id));
        if (!body || !player.stats) break;
        send(player, {
          t: "corpse", id: body.id,
          read: readCorpse(body, {
            now: t, traceMult: player.stats.traceMult, exactTime: player.stats.exactTime
          })
        });
        break;
      }

      case "vote":
        if (room.phase === "tribunal" && player.alive && !player.ejected) {
          T.vote(room.tribunal, player.id, String(m.vote));
        }
        break;

      case "watch":
        if (!player.alive || player.ejected) {
          const w = B.watch(room.base, player.id, Array.isArray(m.rooms) ? m.rooms : []);
          send(player, { t: "watching", rooms: w });
        }
        break;

      case "door": {
        if (player.alive && !player.ejected) break;
        const r = B.toggleDoor(room.base, room, String(m.room), t);
        if (!r.ok) send(player, { t: "toast", msg: r.why });
        break;
      }

      case "light": {
        if (player.alive && !player.ejected) break;
        const r = B.light(room.base, room, String(m.room), t);
        if (!r.ok) send(player, { t: "toast", msg: r.why });
        break;
      }

      case "again":
        if (player.id === room.hostId && room.phase === "end") {
          room.phase = "lobby";
          for (const p of room.players.values()) {
            p.alive = true; p.ejected = false; p.down = false; p.loadoutReady = false;
          }
          broadcast(room, lobbyMsg(room));
        }
        break;
    }
  });

  ws.on("close", () => {
    if (!room || !player) return;
    room.players.delete(player.id);
    if (room.players.size === 0) { rooms.delete(room.id); return; }
    if (room.hostId === player.id) room.hostId = [...room.players.keys()][0];
    broadcast(room, lobbyMsg(room));
    if (room.phase === "play") {
      const w = R.checkWin(room.round, {
        mageEjected: false, hunterCount: Room.hunters(room).length, now: now()
      });
      if (w) broadcast(room, Room.endRound(room, w.winner, w.msg));
    }
  });
});

server.listen(PORT, () => console.log(`wizard-hunt on http://localhost:${PORT}`));
module.exports = { server, rooms, loop };

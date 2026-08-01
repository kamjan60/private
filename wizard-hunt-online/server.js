// "I'm Not a Wizard, Harry" - authoritative game server.
//
// A derelict station. Hunters sweep it for magic-tech artifacts while one of
// them is secretly a mage picking them off. Hunters do not need to kill the
// mage - they need to *capture* him: stun him, then bind him while he is
// down. That single rule is what makes the classes matter, because only the
// Marksman can land a stun at range and only the Tank can survive being
// wrong about who the mage is.
//
// The server owns all state and integrates movement from client input
// vectors rather than trusting client-reported positions, so a patched
// client cannot teleport onto an artifact or into taser range. Fog of war is
// enforced server-side too: each client is only sent the entities its own
// vision radius can see, so the fog cannot be stripped by editing the
// renderer.
"use strict";

const http = require("http");
const fs = require("fs");
const path = require("path");
const { WebSocketServer } = require("ws");

const PORT = process.env.PORT || 8080;
const TICK_HZ = 15;
const W = 1400, H = 900;
const MIN_PLAYERS = 3;

const SPEED_BASE = 2.5;
const TASER_STUN_MS = 3600;       // long enough to close and bind
const CAPTURE_MS = 1800;          // channel to bind a stunned mage
const EXTRACT_MS = 2800;          // channel to pull an artifact
const CAST_WINDUP_MS = 1300;      // the mage's tell - victims can break line
const CAST_COOLDOWN = 9000;
const CAST_RANGE = 210;
const BLEND_COOLDOWN = 16000;     // decoy FX, the mage's misdirection tool
const CAMERA_MS = 5000;

// Aimed spells. The mage throws rather than selects: a fireball is a
// travelling body that can miss and be dodged, and the storm is an area
// stun that sets up a kill instead of being one.
const BALL_SPEED = 7.6;           // px per tick
const BALL_LIFE = 2400;
const BALL_HIT_R = 22;
const BALL_COOLDOWN = 4200;
const STORM_COOLDOWN = 14000;
const STORM_REACH = 260;          // how far from the mage it lands
const STORM_R = 130;
const STORM_STUN_MS = 3200;
const DISGUISE_COOLDOWN = 30000;
const DISGUISE_MS = 14000;

// Class kit. Every hunter carries a taser; the differences are reach,
// eyesight, toughness and one unique verb each.
const CLASSES = {
  "Strażnik":    { vision: 210, taser: 62, hp: 2, speed: 0.86, glow: "#c4d2e8",
                   perk: "Pancerz: przeżywa pierwsze trafienie zaklęciem." },
  "Zwiadowca":   { vision: 330, taser: 58, hp: 1, speed: 1.14, glow: "#8cf096",
                   perk: "Dalekowzroczność + podgląd kamer stacji." },
  "Strzelec":    { vision: 250, taser: 58, hp: 1, speed: 1.0,  glow: "#78d0ff",
                   perk: "Karabin: ogłuszenie z dystansu (330 px)." },
  "Inkwizytor":  { vision: 240, taser: 70, hp: 1, speed: 1.0,  glow: "#ffa848",
                   perk: "Dłuższy zasięg tazera, wyczuwa świeże zwłoki." },
  "Chirurg":     { vision: 230, taser: 58, hp: 1, speed: 0.98, glow: "#d8e878",
                   perk: "Stabilizacja: raz na rundę podnosi rannego łowcę." },
  "Runarz":      { vision: 235, taser: 58, hp: 1, speed: 0.96, glow: "#c682ff",
                   perk: "Ekstrakcja artefaktów dwa razy szybciej." }
};
const CLASS_NAMES = Object.keys(CLASSES);
const MARKSMAN_RANGE = 330;
const SPELLS = ["fire", "bolt", "sleep"];

const rooms = new Map();
const rnd = (a, b) => a + Math.random() * (b - a);
const dist = (a, b) => Math.hypot(a.x - b.x, a.y - b.y);
const now = () => Date.now();

function code() {
  const A = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789";
  let s = "";
  for (let i = 0; i < 4; i++) s += A[Math.floor(Math.random() * A.length)];
  return rooms.has(s) ? code() : s;
}

// Rooms are the derelict's compartments; artifacts only spawn inside them so
// the sweep has structure instead of being a scatter across open floor.
const COMPARTMENTS = [
  { x: 60,  y: 60,  w: 380, h: 240, name: "Mostek" },
  { x: 500, y: 60,  w: 400, h: 200, name: "Ładownia" },
  { x: 960, y: 60,  w: 380, h: 260, name: "Reaktor" },
  { x: 60,  y: 360, w: 320, h: 240, name: "Medyczny" },
  { x: 440, y: 320, w: 420, h: 280, name: "Kaplica" },
  { x: 920, y: 380, w: 420, h: 220, name: "Warsztat" },
  { x: 120, y: 660, w: 400, h: 180, name: "Kriokomory" },
  { x: 580, y: 660, w: 380, h: 180, name: "Maszynownia" },
  { x: 1020, y: 660, w: 320, h: 180, name: "Śluza" }
];

function makeRoom() {
  const id = code();
  const room = {
    id, phase: "lobby", players: new Map(), corpses: [], artifacts: [],
    balls: [], hostId: null, winner: null, tick: 0
  };
  rooms.set(id, room);
  return room;
}

function layoutArtifacts() {
  return COMPARTMENTS.map((c, i) => ({
    id: i,
    x: Math.round(c.x + rnd(50, c.w - 50)),
    y: Math.round(c.y + rnd(50, c.h - 50)),
    done: false, room: c.name
  }));
}

function broadcast(room, msg) {
  const data = JSON.stringify(msg);
  for (const p of room.players.values()) if (p.ws.readyState === 1) p.ws.send(data);
}
function send(p, msg) { if (p.ws.readyState === 1) p.ws.send(JSON.stringify(msg)); }

function pushEvent(room, msg, kind) {
  broadcast(room, { t: "event", ev: { k: kind || "info", msg, at: now() } });
}

const alive = (room) => [...room.players.values()].filter((p) => p.alive);
const hunters = (room) => alive(room).filter((p) => p.role !== "mage");
const theMage = (room) => [...room.players.values()].find((p) => p.role === "mage");

// -------------------------------------------------------------------- round
function startRound(room) {
  const list = [...room.players.values()];
  if (list.length < MIN_PLAYERS) return;

  const mageIdx = Math.floor(Math.random() * list.length);
  const pool = CLASS_NAMES.slice().sort(() => Math.random() - 0.5);
  list.forEach((p, i) => {
    p.role = i === mageIdx ? "mage" : "hunter";
    // The mage carries a class too, and a real kit - he has to pass as one of
    // them, so he cannot be the only player without a taser or a loadout.
    p.cls = pool[i % pool.length];
    const k = CLASSES[p.cls];
    p.hp = k.hp;
    p.alive = true;
    p.down = false;
    p.x = rnd(150, W - 150); p.y = rnd(150, H - 150);
    p.dir = 0; p.step = 0; p.phase = 0;
    p.input = { x: 0, y: 0 }; p.holding = false;
    p.stunUntil = 0;
    p.castAt = now() + 6000;
    p.blendAt = now() + 8000;
    p.ballAt = now() + 5000;
    p.stormAt = now() + 10000;
    p.disguiseAt = 0;
    p.disguisedAs = null;
    p.disguiseUntil = 0;
    p.taserAt = 0;
    p.windup = null;
    p.channel = null;
    p.usedRevive = false;
    p.cameraUntil = 0;
  });

  room.phase = "play";
  room.balls = [];
  room.corpses = [];
  room.artifacts = layoutArtifacts();
  room.winner = null;

  for (const p of room.players.values()) {
    send(p, {
      t: "role", role: p.role, cls: p.cls, perk: CLASSES[p.cls].perk,
      vision: CLASSES[p.cls].vision,
      objective: p.role === "mage"
        ? "Wybij łowców zaklęciami. Rzucanie ma widoczny narzut — rzucaj bez świadków."
        : "Wynieś artefakty ze stacji albo obezwładnij maga i zwiąż go."
    });
  }
  pushEvent(room, "Wrak zasilony. Jeden z was nie jest łowcą.", "start");
}

function endRound(room, winner, msg) {
  room.phase = "end";
  room.winner = winner;
  const m = theMage(room);
  broadcast(room, { t: "end", winner, msg, mage: m ? { id: m.id, name: m.name } : null });
}

function checkWin(room) {
  if (room.phase !== "play") return;
  const m = theMage(room);
  if (!m || !m.alive) return endRound(room, "hunters", "Mag został schwytany.");
  if (hunters(room).length <= 1) return endRound(room, "mage", "Zostało za mało łowców.");
  if (room.artifacts.length && room.artifacts.every((a) => a.done)) {
    return endRound(room, "hunters", "Wszystkie artefakty zabezpieczone.");
  }
}

// ------------------------------------------------------------------ actions
function applyHit(room, target, sourceName) {
  target.hp--;
  if (target.hp > 0) {
    send(target, { t: "hurt" });
    pushEvent(room, `${target.name} przyjął zaklęcie i utrzymał się na nogach.`, "hurt");
    return;
  }
  // Downed, not dead: the Chirurg gets a window to stabilise them, which is
  // what makes carrying a medic a real decision rather than a label.
  target.down = true;
  target.alive = false;
  room.corpses.push({
    x: Math.round(target.x), y: Math.round(target.y),
    cls: target.cls, name: target.name, id: target.id, at: now()
  });
  send(target, { t: "died" });
  pushEvent(room, `${target.name} przestał odpowiadać.`, "kill");
  checkWin(room);
}

function doCastStart(room, p) {
  if (room.phase !== "play" || p.role !== "mage" || !p.alive) return;
  if (now() < p.castAt || now() < p.stunUntil || p.windup) return;
  const target = hunters(room)
    .filter((h) => dist(h, p) <= CAST_RANGE)
    .sort((a, b) => dist(a, p) - dist(b, p))[0];
  if (!target) { send(p, { t: "toast", msg: "Nikogo w zasięgu." }); return; }

  p.windup = { targetId: target.id, at: now() + CAST_WINDUP_MS };
  // Broadcast the wind-up so anyone with line of sight sees who is casting.
  // Without a tell the mage is unbeatable; with one, being seen is the risk.
  broadcast(room, { t: "windup", x: Math.round(p.x), y: Math.round(p.y), by: p.id });
}

function resolveCast(room, p) {
  const wu = p.windup;
  p.windup = null;
  p.castAt = now() + CAST_COOLDOWN;
  const target = room.players.get(wu.targetId);
  if (!target || !target.alive) return;
  if (dist(target, p) > CAST_RANGE * 1.15) {
    pushEvent(room, "Zaklęcie rozproszyło się — cel zerwał kontakt.", "info");
    return;
  }
  const spell = SPELLS[Math.floor(Math.random() * SPELLS.length)];
  broadcast(room, { t: "fx", spell, x: Math.round(target.x), y: Math.round(target.y) });
  applyHit(room, target, p.name);
}

function doBlend(room, p) {
  // The mage's misdirection: a decoy bloom somewhere he is not, so an FX
  // sighting is evidence rather than proof.
  if (room.phase !== "play" || p.role !== "mage" || !p.alive) return;
  if (now() < p.blendAt) return;
  p.blendAt = now() + BLEND_COOLDOWN;
  const a = Math.random() * Math.PI * 2, r = rnd(240, 460);
  const x = Math.max(50, Math.min(W - 50, p.x + Math.cos(a) * r));
  const y = Math.max(50, Math.min(H - 50, p.y + Math.sin(a) * r));
  broadcast(room, { t: "fx", spell: "sleep", x: Math.round(x), y: Math.round(y), decoy: true });
}

function doFireball(room, p, aim) {
  if (room.phase !== "play" || p.role !== "mage" || !p.alive) return;
  if (now() < p.ballAt || now() < p.stunUntil) return;
  const len = Math.hypot(aim.x, aim.y);
  if (len < 0.01) return;
  p.ballAt = now() + BALL_COOLDOWN;
  room.balls.push({
    id: "b" + (room.tick + Math.random()),
    x: p.x, y: p.y - 10,
    vx: (aim.x / len) * BALL_SPEED, vy: (aim.y / len) * BALL_SPEED,
    by: p.id, born: now()
  });
}

function doStorm(room, p, aim) {
  if (room.phase !== "play" || p.role !== "mage" || !p.alive) return;
  if (now() < p.stormAt || now() < p.stunUntil) return;
  const len = Math.hypot(aim.x, aim.y) || 1;
  p.stormAt = now() + STORM_COOLDOWN;
  const tx = Math.max(30, Math.min(W - 30, p.x + (aim.x / len) * STORM_REACH));
  const ty = Math.max(30, Math.min(H - 30, p.y + (aim.y / len) * STORM_REACH));

  // Area stun, not area damage: it sets a kill up rather than being one, so
  // the mage still has to close and commit.
  const caught = alive(room).filter(
    (o) => o.id !== p.id && Math.hypot(o.x - tx, o.y - ty) < STORM_R
  );
  caught.forEach((o) => {
    o.stunUntil = now() + STORM_STUN_MS;
    o.channel = null;
    send(o, { t: "stunned", until: o.stunUntil });
  });
  broadcast(room, {
    t: "storm", x: Math.round(tx), y: Math.round(ty), r: STORM_R,
    hits: caught.map((o) => ({ x: Math.round(o.x), y: Math.round(o.y) }))
  });
  pushEvent(room, "Wyładowanie łańcuchowe na pokładzie.", "stun");
}

function doDisguise(room, p) {
  // Wearing someone else's colours: the mage keeps his own name but renders
  // as another class, so a witness who only glimpsed a silhouette is wrong.
  if (room.phase !== "play" || p.role !== "mage" || !p.alive) return;
  if (now() < p.disguiseAt) return;
  const near = alive(room)
    .filter((o) => o.id !== p.id && dist(o, p) < 260)
    .sort((a, b) => dist(a, p) - dist(b, p))[0];
  if (!near) { send(p, { t: "toast", msg: "Nikogo w pobliżu." }); return; }
  p.disguiseAt = now() + DISGUISE_COOLDOWN;
  p.disguisedAs = near.cls;
  p.disguiseUntil = now() + DISGUISE_MS;
  send(p, { t: "toast", msg: "Przebranie: " + near.cls });
}

function doTaser(room, p) {
  if (room.phase !== "play" || !p.alive || now() < p.stunUntil) return;
  if (now() < p.taserAt) return;
  const k = CLASSES[p.cls];
  const range = p.cls === "Strzelec" ? MARKSMAN_RANGE : k.taser;
  p.taserAt = now() + (p.cls === "Strzelec" ? 6500 : 4200);

  const target = alive(room)
    .filter((o) => o.id !== p.id && dist(o, p) <= range)
    .sort((a, b) => dist(a, p) - dist(b, p))[0];
  broadcast(room, {
    t: "shot", from: { x: Math.round(p.x), y: Math.round(p.y) },
    to: target ? { x: Math.round(target.x), y: Math.round(target.y) } : null,
    ranged: p.cls === "Strzelec"
  });
  if (!target) return;
  target.stunUntil = now() + TASER_STUN_MS;
  target.windup = null;                 // a stun interrupts a cast mid-wind-up
  send(target, { t: "stunned", until: target.stunUntil });
  pushEvent(room, `${p.name} obezwładnił kogoś.`, "stun");
}

function doHold(room, p) {
  // One context-sensitive verb: bind a stunned mage, revive a downed hunter,
  // or extract an artifact - whichever you are standing on.
  if (room.phase !== "play" || !p.alive || now() < p.stunUntil) { p.channel = null; return; }

  if (p.role !== "mage") {
    const captive = alive(room).find(
      (o) => o.id !== p.id && now() < o.stunUntil && dist(o, p) < 52
    );
    if (captive) {
      startChannel(p, "capture", captive.id, CAPTURE_MS);
      return;
    }
    if (p.cls === "Chirurg" && !p.usedRevive) {
      const body = room.corpses.find((c) => Math.hypot(c.x - p.x, c.y - p.y) < 52);
      if (body) { startChannel(p, "revive", body.id, CAPTURE_MS); return; }
    }
  }

  const art = room.artifacts.find(
    (a) => !a.done && Math.hypot(a.x - p.x, a.y - p.y) < 40
  );
  if (art) {
    const ms = p.cls === "Runarz" ? EXTRACT_MS / 2 : EXTRACT_MS;
    startChannel(p, "extract", art.id, ms);
    return;
  }
  p.channel = null;
}

function startChannel(p, kind, targetId, ms) {
  if (!p.channel || p.channel.kind !== kind || p.channel.target !== targetId) {
    p.channel = { kind, target: targetId, start: now(), ms };
  }
}

function finishChannel(room, p) {
  const c = p.channel;
  p.channel = null;
  if (c.kind === "extract") {
    const a = room.artifacts.find((x) => x.id === c.target);
    if (a && !a.done) {
      a.done = true;
      pushEvent(room, `${p.name} zabezpieczył artefakt (${a.room}).`, "artifact");
      checkWin(room);
    }
  } else if (c.kind === "capture") {
    const o = room.players.get(c.target);
    if (!o || !o.alive) return;
    if (o.role === "mage") {
      o.alive = false;
      pushEvent(room, `${p.name} związał maga. ${o.name} był magiem.`, "good");
      checkWin(room);
    } else {
      // Binding an innocent costs you: they are out of the round.
      o.alive = false;
      room.corpses.push({
        x: Math.round(o.x), y: Math.round(o.y), cls: o.cls, name: o.name, id: o.id, at: now()
      });
      send(o, { t: "died", by: "bound" });
      pushEvent(room, `${p.name} związał ${o.name}. To nie był mag.`, "bad");
      checkWin(room);
    }
  } else if (c.kind === "revive") {
    const idx = room.corpses.findIndex((x) => x.id === c.target);
    if (idx < 0) return;
    const body = room.corpses[idx];
    const victim = room.players.get(body.id);
    room.corpses.splice(idx, 1);
    p.usedRevive = true;
    if (victim) {
      victim.alive = true; victim.down = false;
      victim.hp = 1; victim.x = body.x; victim.y = body.y;
      victim.stunUntil = now() + 1200;
      send(victim, { t: "revived" });
      pushEvent(room, `${p.name} ustabilizował ${victim.name}.`, "good");
    }
  }
}

function doCamera(room, p) {
  if (p.cls !== "Zwiadowca" || !p.alive || room.phase !== "play") return;
  if (now() < p.cameraUntil) return;
  p.cameraUntil = now() + CAMERA_MS + 12000;
  send(p, { t: "camera", until: now() + CAMERA_MS });
}

// --------------------------------------------------------------- simulation
function stepRoom(room) {
  if (room.phase !== "play") return;
  room.tick++;
  const t = now();

  for (const p of room.players.values()) {
    if (!p.alive) continue;

    if (p.windup && t >= p.windup.at) resolveCast(room, p);

    if (t < p.stunUntil) { p.channel = null; continue; }

    const ix = p.input.x, iy = p.input.y;
    const len = Math.hypot(ix, iy);
    if (len > 0.01) {
      const sp = SPEED_BASE * CLASSES[p.cls].speed;
      const nx = (ix / len) * sp, ny = (iy / len) * sp;
      p.x = Math.max(16, Math.min(W - 16, p.x + nx));
      p.y = Math.max(24, Math.min(H - 10, p.y + ny));
      p.dir = Math.abs(nx) > Math.abs(ny) ? (nx < 0 ? 1 : 2) : (ny < 0 ? 3 : 0);
      p.phase += sp;
      p.step = Math.floor(p.phase / 10) % 2;
      // moving cancels a channel, so extraction is a real commitment
      if (p.channel) p.channel = null;
    }

    if (p.holding) doHold(room, p); else p.channel = null;
    if (p.channel && t - p.channel.start >= p.channel.ms) finishChannel(room, p);

    if (p.disguiseUntil && t > p.disguiseUntil) { p.disguisedAs = null; p.disguiseUntil = 0; }
  }

  // Fireballs are integrated server-side and hit-tested here, so a client
  // cannot claim a hit it did not land.
  room.balls = room.balls.filter((b) => {
    b.x += b.vx; b.y += b.vy;
    const victim = alive(room).find(
      (o) => o.id !== b.by && Math.hypot(o.x - b.x, o.y - b.y) < BALL_HIT_R
    );
    const outside = b.x < 0 || b.y < 0 || b.x > W || b.y > H;
    if (victim || outside || t - b.born > BALL_LIFE) {
      broadcast(room, { t: "fx", spell: "fire", x: Math.round(b.x), y: Math.round(b.y) });
      if (victim) {
        const caster = room.players.get(b.by);
        applyHit(room, victim, caster ? caster.name : "?");
      }
      return false;
    }
    return true;
  });

  // Per-player snapshot: fog of war is applied here, not in the client, so it
  // cannot be removed by patching the renderer.
  for (const me of room.players.values()) {
    const seeAll = !me.alive || (me.cameraUntil && t < me.cameraUntil - 12000);
    const R = CLASSES[me.cls] ? CLASSES[me.cls].vision : 240;
    const visible = (o) => seeAll || Math.hypot(o.x - me.x, o.y - me.y) <= R;

    send(me, {
      t: "state",
      you: {
        id: me.id, x: Math.round(me.x), y: Math.round(me.y), hp: me.hp,
        stun: Math.max(0, me.stunUntil - t),
        cast: Math.max(0, me.castAt - t), blend: Math.max(0, me.blendAt - t),
        taser: Math.max(0, me.taserAt - t),
        ball: Math.max(0, me.ballAt - t), storm: Math.max(0, me.stormAt - t),
        disguise: Math.max(0, me.disguiseAt - t),
        disguised: me.disguisedAs || null,
        windup: me.windup ? Math.max(0, me.windup.at - t) : 0,
        ch: me.channel ? Math.min(1, (t - me.channel.start) / me.channel.ms) : 0,
        chKind: me.channel ? me.channel.kind : null,
        vision: R, seeAll
      },
      players: [...room.players.values()].filter((p) => p.alive && visible(p)).map((p) => ({
        id: p.id, name: p.name,
        // Everyone else sees the disguise; you always see your own real class.
        cls: (p.disguisedAs && p.id !== me.id) ? p.disguisedAs : p.cls,
        x: Math.round(p.x), y: Math.round(p.y),
        dir: p.dir, step: p.step, stun: p.stunUntil > t,
        casting: !!p.windup, me: p.id === me.id
      })),
      balls: room.balls.filter(visible).map((b) => ({
        x: Math.round(b.x), y: Math.round(b.y),
        a: Math.atan2(b.vy, b.vx)
      })),
      corpses: room.corpses.filter(visible),
      artifacts: room.artifacts.filter((a) => a.done || visible(a)),
      left: room.artifacts.filter((a) => !a.done).length,
      total: room.artifacts.length,
      hunters: hunters(room).length
    });
  }
}

setInterval(() => { for (const room of rooms.values()) stepRoom(room); }, 1000 / TICK_HZ);

// -------------------------------------------------------------- connections
let nextId = 1;
const server = http.createServer((req, res) => {
  const url = req.url === "/" ? "/index.html" : req.url.split("?")[0];
  const file = path.join(__dirname, "public", path.normalize(url).replace(/^(\.\.[/\\])+/, ""));
  fs.readFile(file, (err, data) => {
    if (err) { res.writeHead(404); return res.end("not found"); }
    const types = { ".html": "text/html", ".js": "text/javascript", ".png": "image/png", ".css": "text/css" };
    res.writeHead(200, { "Content-Type": types[path.extname(file)] || "application/octet-stream" });
    res.end(data);
  });
});

const wss = new WebSocketServer({ server });

wss.on("connection", (ws) => {
  let room = null, player = null;

  ws.on("message", (raw) => {
    let m;
    try { m = JSON.parse(raw); } catch { return; }

    if (m.t === "join") {
      const name = String(m.name || "Bezimienny").slice(0, 16);
      if (m.room) {
        room = rooms.get(String(m.room).toUpperCase());
        if (!room) { ws.send(JSON.stringify({ t: "error", msg: "Nie ma takiego pokoju." })); return; }
      } else {
        room = makeRoom();
      }
      player = {
        id: "p" + nextId++, name, ws, cls: CLASS_NAMES[0], role: "hunter",
        x: rnd(200, W - 200), y: rnd(200, H - 200), dir: 0, step: 0, phase: 0,
        hp: 1, alive: true, down: false, input: { x: 0, y: 0 }, holding: false,
        stunUntil: 0, castAt: 0, blendAt: 0, taserAt: 0, windup: null,
        channel: null, usedRevive: false, cameraUntil: 0
      };
      room.players.set(player.id, player);
      if (!room.hostId) room.hostId = player.id;
      send(player, { t: "joined", id: player.id, room: room.id, host: room.hostId === player.id });
      broadcast(room, {
        t: "lobby", host: room.hostId, phase: room.phase,
        players: [...room.players.values()].map((p) => ({ id: p.id, name: p.name }))
      });
      return;
    }

    if (!room || !player) return;
    switch (m.t) {
      case "start":  if (player.id === room.hostId && room.phase !== "play") startRound(room); break;
      case "input":
        player.input.x = Math.max(-1, Math.min(1, Number(m.x) || 0));
        player.input.y = Math.max(-1, Math.min(1, Number(m.y) || 0));
        player.holding = !!m.hold;
        break;
      case "cast":   doCastStart(room, player); break;
      case "blend":  doBlend(room, player); break;
      case "taser":  doTaser(room, player); break;
      case "camera": doCamera(room, player); break;
      case "ball":   doFireball(room, player, { x: Number(m.ax) || 0, y: Number(m.ay) || 0 }); break;
      case "storm":  doStorm(room, player, { x: Number(m.ax) || 0, y: Number(m.ay) || 0 }); break;
      case "disguise": doDisguise(room, player); break;
    }
  });

  ws.on("close", () => {
    if (!room || !player) return;
    room.players.delete(player.id);
    if (room.players.size === 0) { rooms.delete(room.id); return; }
    if (room.hostId === player.id) room.hostId = [...room.players.keys()][0];
    broadcast(room, {
      t: "lobby", host: room.hostId, phase: room.phase,
      players: [...room.players.values()].map((p) => ({ id: p.id, name: p.name }))
    });
    if (room.phase === "play") checkWin(room);
  });
});

server.listen(PORT, () => console.log(`wizard-hunt on http://localhost:${PORT}`));
module.exports = { server, rooms, COMPARTMENTS, CLASSES };

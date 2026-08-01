"use strict";
/**
 * A real round, driven by scripted websocket clients against the real
 * server. The unit tests prove the rules; this proves the wiring, and it is
 * where the previous build's genuine bugs lived -- an ordering mistake
 * between two modules never shows up in either module's own tests.
 *
 * Runs in-process on a spare port so it needs no fixtures and no cleanup
 * beyond closing the server.
 */

process.env.PORT = process.env.TEST_PORT || "8099";

const assert = require("assert");
const WebSocket = require("ws");
const { server, loop, rooms } = require("../server");
const { MIN_PLAYERS } = require("../src/rules");

let passed = 0, failed = 0;
function check(name, fn) {
  try { fn(); passed++; console.log("  ok   " + name); }
  catch (e) { failed++; console.log("  FAIL " + name + "\n       " + e.message); }
}

const wait = (ms) => new Promise((r) => setTimeout(r, ms));

/** A scripted client that keeps the last of every message type it saw. */
function bot(name, roomCode) {
  const b = {
    name, ws: null, id: null, room: null, host: false,
    last: {}, seen: [], states: 0
  };
  return new Promise((resolve) => {
    b.ws = new WebSocket(`ws://127.0.0.1:${process.env.PORT}`);
    b.ws.on("open", () => b.ws.send(JSON.stringify({ t: "join", name, room: roomCode })));
    b.ws.on("message", (raw) => {
      const m = JSON.parse(raw);
      b.last[m.t] = m;
      if (m.t !== "state") b.seen.push(m.t); else b.states++;
      if (m.t === "joined") { b.id = m.id; b.room = m.room; b.host = m.host; resolve(b); }
    });
    b.send = (m) => b.ws.send(JSON.stringify(m));
  });
}

(async () => {
  console.log("live round");

  // ------------------------------------------------------------- lobby
  const host = await bot("Kaz", null);
  const others = [];
  for (let i = 1; i < MIN_PLAYERS; i++) others.push(await bot("Bot" + i, host.room));
  const all = [host, ...others];
  await wait(120);

  check("everyone is in one room", () => {
    assert.strictEqual(all.length, MIN_PLAYERS);
    assert.ok(all.every((b) => b.room === host.room));
    assert.strictEqual(host.last.lobby.players.length, MIN_PLAYERS);
  });

  check("the class table reaches the client", () => {
    assert.strictEqual(host.last.joined.classes.length, 8);
    assert.strictEqual(host.last.joined.spells.length, 24);
    assert.strictEqual(Object.keys(host.last.joined.presets).length, 3);
  });

  // ------------------------------------------------------------- loadout
  host.send({ t: "start" });
  await wait(150);

  check("everyone gets a class and exactly one is the mage", () => {
    const roles = all.map((b) => b.last.loadout.role);
    assert.strictEqual(roles.filter((r) => r === "mage").length, 1);
    const classes = all.map((b) => b.last.loadout.cls);
    assert.strictEqual(new Set(classes).size, MIN_PLAYERS, "classes must be unique");
  });

  check("the loadout screen offers three items", () => {
    assert.ok(all.every((b) => b.last.loadout.items.length === 3));
  });

  const mage = all.find((b) => b.last.loadout.role === "mage");
  const hunterBots = all.filter((b) => b !== mage);

  // everyone but one hunter picks; the straggler must not block the round
  for (const b of all.slice(0, all.length - 1)) {
    b.send({
      t: "loadout", item: b.last.loadout.items[0].id,
      book: b === mage ? host.last.joined.presets["Rzeźnik"] : undefined
    });
  }
  await wait(120);

  check("a chosen loadout is accepted", () => {
    assert.ok(host.last.loadoutOk, "host's pick was not acknowledged");
  });

  // ------------------------------------------------------------- round
  // the loadout timer is 90 s, so nudge the room rather than waiting it out
  const room = rooms.get(host.room);
  room.loadoutEndsAt = Date.now() - 1;
  await wait(200);

  check("the round starts and the straggler got a random loadout", () => {
    assert.strictEqual(room.phase, "play");
    assert.ok(all.every((b) => b.last.role), "everybody should have been told their role");
    assert.ok([...room.players.values()].every((p) => p.item), "every player needs an item");
  });

  check("only the mage is handed a book", () => {
    const withBook = all.filter((b) => b.last.role.book);
    assert.strictEqual(withBook.length, 1);
    assert.strictEqual(withBook[0], mage);
    assert.ok(withBook[0].last.role.book.length > 0);
  });

  check("snapshots are flowing", () => {
    assert.ok(all.every((b) => b.states > 0), "every client should be receiving state");
  });

  // ------------------------------------------------------------- fog
  check("nobody is told anybody else's role", () => {
    for (const b of all) {
      const s = b.last.state;
      assert.strictEqual(s.me.role, b.last.role.role, "you know your own role");
      for (const a of s.actors) {
        assert.ok(!("role" in a), `${b.name} was sent a role for ${a.name}`);
      }
    }
  });

  check("the fog is cut server-side", () => {
    // park two players far apart and confirm neither appears in the other's
    // snapshot at all -- not hidden, absent
    const ps = [...room.players.values()];
    ps[0].x = 200; ps[0].y = 200;
    ps[1].x = 1800; ps[1].y = 1400;
    const { snapshotFor } = require("../src/snapshot");
    const s = snapshotFor(room, ps[0], Date.now());
    assert.ok(!s.actors.some((a) => a.id === ps[1].id),
      "a player outside vision must not be serialised at all");
  });

  // ------------------------------------------------------------- airlocks
  const M = require("../src/map");
  const { readLog } = require("../src/evidence");
  const { LOCK_MS } = require("../src/rules");
  const walker = [...room.players.values()].find((p) => p.role !== "mage");

  check("the void between compartments is not floor", () => {
    const st = { sealed: new Set(), walls: [] };
    // a point squarely in the gap between the first two rooms
    const a = M.compartment("Mostek"), b = M.compartment("Ładownia");
    const gapX = (a.x + a.w + b.x) / 2;
    assert.strictEqual(M.free(gapX, a.y + a.h / 2, 12, st), false,
      "a shove must not be able to put a body outside the hull");
    assert.strictEqual(M.free(a.x + a.w / 2, a.y + a.h / 2, 12, st), true);
  });

  const hatch = M.doorsOf("Mostek").find((h) => h.to === "Ładownia");
  walker.comp = "Mostek";
  walker.lock = null;
  walker.x = hatch.x - 22; walker.y = hatch.y;
  walker.input = { x: 1, y: 0 };
  await wait(250);

  check("pressing a hatch seals you into the lock", () => {
    assert.ok(walker.lock, "the walker should be inside the airlock");
    assert.strictEqual(walker.lock.to, "Ładownia");
    assert.strictEqual(walker.comp, null, "you are in neither room while locked");
  });

  check("somebody in a lock is unreachable and invisible", () => {
    const other = [...room.players.values()].find((p) => p.id !== walker.id && p.alive);
    other.x = walker.x; other.y = walker.y;
    const { snapshotFor } = require("../src/snapshot");
    const s = snapshotFor(room, other, Date.now());
    assert.ok(!s.actors.some((a) => a.id === walker.id),
      "a body inside a lock must not be serialised onto the floor");
  });

  await wait(LOCK_MS + 400);

  check("the far hatch opens into the next compartment", () => {
    assert.strictEqual(walker.lock, null, "the lock should have cycled");
    assert.strictEqual(walker.comp, "Ładownia");
    const c = M.compartmentAt(walker.x, walker.y);
    assert.ok(c && c.name === "Ładownia", "and it must put you inside, not on the wall");
  });

  check("the passage writes both halves of the transit log", () => {
    const out = readLog(room.evidence, "Mostek", { act: 0, now: Date.now() });
    const into = readLog(room.evidence, "Ładownia", { act: 0, now: Date.now() });
    assert.ok(out.some((e) => e.kind === "out"), "leaving was not recorded");
    assert.ok(into.some((e) => e.kind === "in"), "arriving was not recorded");
    assert.ok(into.every((e) => !("realId" in e)), "an entry leaked a real id");
  });

  walker.input = { x: 0, y: 0 };

  // ------------------------------------------------------------- extraction
  const walkerBot = all.find((b) => b.id === walker.id);
  const target = room.round.artifacts.find((a) => a.act === 0 && a.state === "open");
  walker.x = target.x; walker.y = target.y;
  walker.comp = target.room;
  walkerBot.send({ t: "input", x: 0, y: 0, hold: true });
  await wait(3200);
  walkerBot.send({ t: "input", x: 0, y: 0, hold: false });
  await wait(120);

  check("extraction secures the artifact and hands over the log", () => {
    assert.strictEqual(room.round.secured, 1);
    assert.ok(walkerBot.last.log, "the extractor was not sent the compartment log");
    assert.strictEqual(walkerBot.last.log.room, target.room);
  });

  // ------------------------------------------------------------- casting
  const magePl = room.players.get(mage.id);
  const victim = [...room.players.values()].find((p) => p.role !== "mage" && p.alive);
  magePl.x = victim.x + 40; magePl.y = victim.y;
  magePl.castReadyAt = 0;
  mage.send({ t: "cast", spell: "kula_ognia", ax: -1, ay: 0 });
  await wait(120);

  check("a cast broadcasts its tell to everyone", () => {
    assert.ok(mage.last.windup, "the caster saw no wind-up");
    const witness = all.find((b) => b !== mage);
    assert.ok(witness.last.windup, "nobody else saw the tell");
    assert.strictEqual(witness.last.windup.school, "ogien");
  });

  check("the charge is spent at the start of the cast", () => {
    const e = magePl.book.find((b) => b.id === "kula_ognia");
    assert.strictEqual(e.charges, 5, "Rzeźnik takes kula_ognia twice: 6 charges, one spent");
  });

  await wait(1400);
  check("the fireball kills and leaves the school on the body", () => {
    assert.strictEqual(victim.alive, false, "the victim should be down");
    const body = room.corpses.find((c) => c.name === victim.name);
    assert.ok(body, "no body was left");
    assert.strictEqual(body.school, "ogien", "the corpse must carry the school that killed it");
  });

  check("the dead are moved to the base and see camera feeds, not the field", () => {
    const b = all.find((x) => x.id === victim.id);
    assert.ok(b.last.toBase, "the victim was not told they are in the base");
    assert.strictEqual(b.last.state.me.role, "base");
    assert.ok(Array.isArray(b.last.state.feeds), "the base needs feeds");
    assert.ok(!("actors" in b.last.state), "the base must not get the field view");
  });

  // ------------------------------------------------------------- interrupt
  magePl.castReadyAt = 0;
  const cop = [...room.players.values()].find((p) => p.role !== "mage" && p.alive);
  const copBot = all.find((b) => b.id === cop.id);
  cop.x = magePl.x + 30; cop.y = magePl.y;
  cop.taserReadyAt = 0;
  const before = magePl.book.find((b) => b.id === "pochodnia").charges;
  mage.send({ t: "cast", spell: "pochodnia", ax: 1, ay: 0 });
  await wait(80);
  copBot.send({ t: "taser", ax: -1, ay: 0 });
  await wait(150);

  check("a taser in the wind-up interrupts the cast and eats the charge", () => {
    assert.strictEqual(magePl.windup, null, "the cast should have been interrupted");
    assert.ok(magePl.stunUntil > Date.now(), "the mage should be stunned");
    const after = magePl.book.find((b) => b.id === "pochodnia").charges;
    assert.strictEqual(after, before - 1, "an interrupted cast still costs its charge");
  });

  // ------------------------------------------------------------- tribunal
  copBot.send({ t: "input", x: 0, y: 0, hold: true });
  await wait(2200);
  copBot.send({ t: "input", x: 0, y: 0, hold: false });
  await wait(150);

  check("binding a stunned player opens a tribunal", () => {
    assert.strictEqual(room.phase, "tribunal");
    assert.ok(copBot.last.tribunal, "no tribunal screen was broadcast");
    assert.strictEqual(copBot.last.tribunal.accused.id, magePl.id);
    assert.strictEqual(copBot.last.tribunal.accuser.id, cop.id);
  });

  check("the tribunal screen carries no evidence", () => {
    const scr = copBot.last.tribunal;
    assert.deepStrictEqual(
      Object.keys(scr).sort(),
      ["accused", "accuser", "endsAt", "t", "voters"].sort(),
      "the vote screen must show only who is accused and who caught them"
    );
  });

  const living = [...room.players.values()].filter((p) => p.alive && !p.ejected);
  for (const p of living) {
    const b = all.find((x) => x.id === p.id);
    if (b) b.send({ t: "vote", vote: p.role === "mage" ? "nie" : "tak" });
  }
  await wait(300);

  check("convicting the mage ends the round for the hunters", () => {
    assert.ok(copBot.last.verdict, "no verdict was broadcast");
    assert.strictEqual(copBot.last.verdict.convicted, true);
    assert.ok(copBot.last.end, "the round should have ended");
    assert.strictEqual(copBot.last.end.winner, "hunters");
  });

  check("the mage is only named once the round is over", () => {
    assert.strictEqual(copBot.last.end.mage.id, magePl.id);
  });

  check("votes are published with the verdict", () => {
    assert.ok(Array.isArray(copBot.last.verdict.cast));
    assert.ok(copBot.last.verdict.cast.length > 0);
  });

  // ------------------------------------------------------------- done
  for (const b of all) b.ws.close();
  clearInterval(loop);
  server.close();
  console.log(`\n${passed} passed${failed ? `, ${failed} failed` : ""}`);
  process.exit(failed ? 1 : 0);
})().catch((e) => {
  console.error("harness blew up:", e);
  clearInterval(loop);
  server.close();
  process.exit(1);
});

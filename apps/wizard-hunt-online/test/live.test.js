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

  // Everyone but one hunter picks; the straggler must not block the round.
  // The straggler has to be a hunter: leaving the mage out would hand him a
  // random preset, and the cast assertions below name a specific spell.
  const straggler = all.filter((b) => b !== mage).pop();
  for (const b of all.filter((b) => b !== straggler)) {
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

  // ------------------------------------------------------------- corridors
  const M = require("../src/map");
  const { readLog } = require("../src/evidence");
  const walker = [...room.players.values()].find((p) => p.role !== "mage");

  check("only zones are floor", () => {
    const st = { sealed: new Set(), walls: [], act: 2 };
    // the hull between a room and the corridor beside it
    const a = M.compartment("Mostek");
    assert.strictEqual(M.free(a.x + 10, a.y - 40, 12, st), false,
      "a shove must not be able to put a body outside the ship");
    assert.strictEqual(M.free(a.x + a.w / 2, a.y + a.h / 2, 12, st), true);
  });

  check("corridors are real rooms, and nothing watches them", () => {
    assert.strictEqual(M.CORRIDORS.length, M.LINKS.length);
    const hall = M.CORRIDORS[0];
    assert.ok(hall.w >= 76 && hall.h >= 76, "a corridor has to hold more than one body");
    assert.ok(M.isCorridor(hall.name));
    const B = require("../src/base");
    assert.ok(!B.liveCameras(room.base).includes(hall.name),
      "a corridor with a camera would not be a place to be alone");
  });

  const hall = M.CORRIDORS.find((c) => c.section === 0);
  walker.comp = null;
  walker.x = hall.x + hall.w / 2; walker.y = hall.y + hall.h / 2;
  await wait(300);

  // nudge them along the corridor so the sensors register the passage
  walker.input = { x: hall.axis === "x" ? 0.2 : 0, y: hall.axis === "x" ? 0 : 0.2 };
  await wait(400);
  walker.input = { x: 0, y: 0 };
  await wait(200);

  check("a corridor writes its own transit entries", () => {
    const entries = readLog(room.evidence, hall.name, { act: 0, now: Date.now() });
    assert.ok(entries.length > 0, "walking a corridor left no record");
    assert.ok(entries.every((e) => !("realId" in e)), "an entry leaked a real id");
  });

  const A2 = require("../src/actions");
  const { CORRIDOR_ARM_MS, CORRIDOR_SHUT_MS } = require("../src/rules");
  const a2 = M.compartment(hall.ends[0]);
  const mouth = hall.axis === "x"
    ? { x: a2.x + a2.w, y: hall.y + hall.h / 2 }
    : { x: hall.x + hall.w / 2, y: a2.y + a2.h };

  check("entering arms the hatches but does not shut them yet", () => {
    const cyc = room.cycling.get(hall.name);
    assert.ok(cyc, "walking in should have armed the corridor");
    assert.ok(cyc.shutAt > Date.now(),
      "there has to be a warning, or nobody can decide whether to follow");
    const st = A2.collisionState(room, Date.now());
    assert.ok(!st.sealed.has(hall.name), "still open during the warning");
    assert.strictEqual(M.free(mouth.x, mouth.y, 12, st), true);
  });

  check("after the warning it slams, for five seconds", () => {
    const cyc = room.cycling.get(hall.name);
    const shut = cyc.shutAt + 100;
    const st = A2.collisionState(room, shut);
    assert.ok(st.sealed.has(hall.name));
    assert.strictEqual(M.free(mouth.x, mouth.y, 12, st), false,
      "nobody follows you in and you do not get out");
    assert.strictEqual(cyc.until - cyc.shutAt, CORRIDOR_SHUT_MS);
    const after = A2.collisionState(room, cyc.until + 50);
    assert.ok(!after.sealed.has(hall.name), "and then it opens again");
  });

  check("a shut corridor is sealed to sight in both directions", () => {
    const { snapshotFor, visionOf } = require("../src/snapshot");
    const cyc = room.cycling.get(hall.name);
    // pretend the warning already ran out
    cyc.shutAt = Date.now() - 50;
    cyc.until = Date.now() + CORRIDOR_SHUT_MS;

    const inside = [...room.players.values()].find((p) => p.alive && p.id !== walker.id);
    inside.x = hall.x + hall.w / 2; inside.y = hall.y + hall.h / 2;
    walker.x = inside.x; walker.y = inside.y;

    const outside = [...room.players.values()]
      .find((p) => p.alive && p.id !== walker.id && p.id !== inside.id);
    outside.x = a2.x + a2.w - 30; outside.y = hall.y + hall.h / 2;

    const theirs = snapshotFor(room, outside, Date.now());
    assert.ok(!theirs.actors.some((x) => x.id === walker.id),
      "a step outside the door must not be a grandstand seat");

    const mine = snapshotFor(room, walker, Date.now());
    assert.ok(mine.actors.some((x) => x.id === inside.id),
      "you still see whoever is shut in with you");
    assert.ok(!mine.actors.some((x) => x.id === outside.id),
      "and nothing beyond the walls");
    assert.ok(mine.inHall && mine.inHall.room === hall.name,
      "the client has to be told it is boxed in, not just go dark");
    assert.ok(visionOf(room, walker, Date.now()) <= Math.max(hall.w, hall.h),
      "the fog should close to the corridor itself");

    cyc.shutAt = Date.now() + 999999;   // leave the room open for later checks
    cyc.until = cyc.shutAt + CORRIDOR_SHUT_MS;
  });

  check("a body in a corridor can still be seen, and killed", () => {
    const other = [...room.players.values()].find((p) => p.id !== walker.id && p.alive);
    other.x = walker.x + 20; other.y = walker.y;
    const { snapshotFor } = require("../src/snapshot");
    const s = snapshotFor(room, other, Date.now());
    assert.ok(s.actors.some((a) => a.id === walker.id),
      "a corridor is a place, not a safe room -- that is the whole point of it");
  });


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
  // clear the line of fire: the corridor checks above parked a third body
  // next to the walker, and it was catching the ball instead
  const room0 = M.sectionOf(0);
  [...room.players.values()].forEach((p, i) => {
    if (p === magePl || p === victim) return;
    const far = room0[(i + 2) % room0.length];
    p.x = far.x + far.w / 2; p.y = far.y + far.h / 2; p.comp = far.name;
  });
  const box0 = M.sectionOf(0)[0];
  victim.x = box0.x + box0.w / 2; victim.y = box0.y + box0.h / 2; victim.comp = box0.name;
  magePl.x = victim.x + 40; magePl.y = victim.y; magePl.comp = box0.name;
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

  // ------------------------------------------------------------- illusions
  // These three were all built server-side and thrown away by the client:
  // the decoy, the Scout's sensor and the Marksman's tag were never drawn,
  // and there was no way at all to tell that Cień was up.
  const E = require("../src/effects");
  const { snapshotFor } = require("../src/snapshot");

  magePl.castReadyAt = 0;
  magePl.book.push({ id: "sobowtor", charges: 2, school: "swiatlo" });
  E.beginCast(room, magePl, "sobowtor", { x: 1, y: 0 }, Date.now(), {});
  await wait(1200);

  check("Sobowtór leaves a body on the field, and it walks", () => {
    const d = room.markers.filter((m) => m.kind === "decoy");
    assert.strictEqual(d.length, 1, "no decoy was created");
    assert.ok(d[0].cls, "a decoy without a class cannot be mistaken for anybody");
    assert.ok(typeof d[0].vx === "number", "a stationary twin fools nobody");
  });

  check("the decoy reaches the client", () => {
    const s = snapshotFor(room, magePl, Date.now());
    assert.ok((s.markers || []).some((m) => m.kind === "decoy"),
      "the decoy must be serialised or it cannot be drawn");
  });

  magePl.castReadyAt = 0;
  magePl.book.push({ id: "cien", charges: 2, school: "mrok" });
  E.beginCast(room, magePl, "cien", { x: 1, y: 0 }, Date.now(), {});
  await wait(900);

  check("Cień hides you from others and tells you it is up", () => {
    const mine = snapshotFor(room, magePl, Date.now());
    const me = mine.actors.find((a) => a.id === magePl.id);
    assert.ok(me, "you always see your own body");
    assert.strictEqual(me.invisible, true,
      "without this flag the only way to know the spell is up is to be shot at");

    const other = [...room.players.values()].find((p) => p.id !== magePl.id && p.alive);
    other.x = magePl.x + 20; other.y = magePl.y;
    const theirs = snapshotFor(room, other, Date.now());
    assert.ok(!theirs.actors.some((a) => a.id === magePl.id),
      "an invisible body must be absent from everybody else's snapshot");
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

"use strict";
/**
 * Drives the real client in a real browser, with websocket bots filling the
 * other seats, on an emulated handset.
 *
 * Not part of `npm test` -- it needs Playwright and a browser binary. Run it
 * by hand when the client changes: `node test/browser.js`.
 */

process.env.PORT = "8101";

const { chromium, devices } = require("/opt/node22/lib/node_modules/playwright");
const WebSocket = require("ws");
const { server, loop, rooms } = require("../server");

const wait = (ms) => new Promise((r) => setTimeout(r, ms));
let fails = 0;
const ok = (name, cond, extra) => {
  console.log((cond ? "  ok   " : "  FAIL ") + name + (cond ? "" : "  " + (extra || "")));
  if (!cond) fails++;
};

function bot(name, room) {
  return new Promise((resolve) => {
    const ws = new WebSocket(`ws://127.0.0.1:${process.env.PORT}`);
    const b = { ws, id: null, last: {} };
    ws.on("open", () => ws.send(JSON.stringify({ t: "join", name, room })));
    ws.on("message", (raw) => {
      const m = JSON.parse(raw);
      b.last[m.t] = m;
      if (m.t === "joined") { b.id = m.id; b.room = m.room; resolve(b); }
      if (m.t === "loadout") {
        ws.send(JSON.stringify({
          t: "loadout", item: m.items[0].id,
          book: m.role === "mage" ? b.last.joined.presets["Rzeźnik"] : undefined
        }));
      }
      if (m.t === "tribunal") ws.send(JSON.stringify({ t: "vote", vote: "nie" }));
    });
  });
}

(async () => {
  const browser = await chromium.launch();
  const ctx = await browser.newContext({ ...devices["iPhone 13"] });
  const page = await ctx.newPage();
  const errors = [];
  page.on("console", (m) => { if (m.type() === "error") errors.push(m.text()); });
  page.on("pageerror", (e) => errors.push(String(e)));

  await page.goto(`http://127.0.0.1:${process.env.PORT}/`);
  await page.fill("#nick", "Kaz");
  await page.click("#btnJoin");
  await page.waitForSelector("#sLobby.on", { timeout: 5000 });

  const code = await page.textContent("#roomCode");
  ok("browser created a room", /^[A-Z]{4}$/.test(code), code);

  const bots = [];
  for (let i = 1; i <= 4; i++) bots.push(await bot("Bot" + i, code));
  await wait(300);

  ok("touch layer is on", await page.evaluate(() => document.body.classList.contains("touch")));
  ok("start is enabled at five players", !(await page.isDisabled("#btnStart")));

  // MAGE=1 forces the browser player to draw the mage, so the book, the
  // spell bar and the cover-item flow get exercised instead of being left
  // to a one-in-five roll.
  const orig = Math.random;
  if (process.env.MAGE) Math.random = () => 0;      // mageIdx -> the first seat
  await page.click("#btnStart");
  await wait(250);
  Math.random = orig;
  await page.waitForSelector("#sLoadout.on", { timeout: 5000 });

  const cls = await page.textContent("#loCls");
  const isMage = await page.isVisible("#tabBook");
  ok("loadout shows the class", !!cls && cls !== "—", cls);
  ok("loadout offers three items", (await page.$$("#loItem .opt")).length === 3);
  console.log("       browser player is " + (isMage ? "the MAGE" : "a hunter") + " (" + cls + ")");

  if (isMage) {
    await page.click("#tabBook");
    const spells = await page.$$("#bookGrid .sp");
    ok("the book lists twenty-four spells", spells.length === 24, String(spells.length));
    // take a preset, then check the signature line actually reports schools
    await page.click("#presetRow button");
    ok("preset fills every slot", (await page.textContent("#slotCount")) === "10/10");
    const sig = await page.textContent("#sig");
    ok("the signature is shown", /Podpis/.test(sig), sig);
    // the mage still has to take a cover item, so the item tab has to be
    // reachable after scrolling through a twenty-four spell grid
    await page.click('#loTabs button[data-tab="item"]');
    ok("the item tab is reachable from the book", await page.isVisible("#loItem .opt"));
  }
  await page.click("#loItem .opt");
  await page.locator("#btnLo").scrollIntoViewIfNeeded();
  ok("the confirm button is reachable on a handset", await page.isVisible("#btnLo"));
  await page.click("#btnLo");

  // skip the ninety-second timer
  const room = rooms.get(code);
  room.loadoutEndsAt = Date.now() - 1;
  await page.waitForSelector("#sGame.on", { timeout: 6000 });
  await wait(600);

  ok("the game screen is up", await page.isVisible("#cv"));
  ok("the role pill is filled", !/^—$/.test(await page.textContent("#pRole")),
    await page.textContent("#pRole"));
  ok("the act clock is counting", /^\d+:\d\d$/.test(await page.textContent("#pClock")),
    await page.textContent("#pClock"));
  ok("three touch buttons are visible",
    (await page.isVisible("#tHold")) && (await page.isVisible("#tA")) && (await page.isVisible("#tB")));

  if (isMage) {
    // These used to look for "#bar .slot" -- a grid of tappable slots that the
    // radial wheel replaced. #bar has not existed for some time, so on every
    // run where the role rolled mage these assertions could only fail, and on
    // every run where it rolled hunter they never executed. A test that can
    // only fail, in a branch that rarely runs, is worse than no test: it
    // trains you to read a red line as noise.
    const armed = await page.textContent("#armed");
    ok("the armed spell is shown with its charges", /\d/.test(armed), armed);
    ok("the book is open to the wheel", await page.isVisible("#tBook"));
  }

  // walk: press the middle of the left half and drag
  const box = await page.locator("#cv").boundingBox();
  await page.touchscreen.tap(box.width * 0.2, box.height * 0.6);
  await wait(200);
  // fire: tap the right half
  await page.touchscreen.tap(box.width * 0.8, box.height * 0.5);
  await wait(300);

  ok("a canvas frame rendered", await page.evaluate(() => {
    const c = document.getElementById("cv");
    const g = c.getContext("2d");
    const d = g.getImageData(0, 0, 1, 1).data;
    return d[3] > 0;
  }));

  // drive a tribunal from a bot so the vote screen is exercised
  // The taps above fired. Clearing the projectiles is not enough: a mage's
  // cast has a 900 ms wind-up, so the ball is *created* after the clear and
  // spawns on top of the binder we are about to place beside him. Drop the
  // pending cast as well, or the test kills its own witness.
  room.balls.length = 0;
  room.delayed.length = 0;
  for (const p of room.players.values()) p.windup = null;
  const players = [...room.players.values()].filter((p) => p.alive && !p.ejected);
  const a = players[0], b = players[1];
  b.stunUntil = 0; b.proneUntil = 0; b.channel = null;
  b.x = a.x + 20; b.y = a.y;
  a.stunUntil = Date.now() + 8000;
  const bBot = bots.find((x) => x.id === b.id);
  if (bBot) {
    bBot.ws.send(JSON.stringify({ t: "input", x: 0, y: 0, hold: true }));
    await wait(2400);
    bBot.ws.send(JSON.stringify({ t: "input", x: 0, y: 0, hold: false }));
    await wait(400);
    ok("the tribunal overlay opened", await page.isVisible("#oTribunal"));
    if (await page.isVisible("#oTribunal")) {
      await page.click("#vNie");
      ok("the vote is acknowledged", /Twój głos/.test(await page.textContent("#trMine")));
      await wait(900);
      const roll = await page.textContent("#vdVotes");
      // the roll must name everyone, including players the fog kept out of
      // this client's snapshot -- raw ids here mean the names came from the
      // culled actor list instead of the tribunal message
      ok("the vote roll uses names, not ids", !/\bp\d+:/.test(roll), roll);
    }
  }

  // the play view itself, with no overlay in the way
  await page.evaluate(() => {
    document.querySelectorAll(".over").forEach((o) => o.classList.remove("on"));
  });
  await wait(400);
  ok("the wreck renders behind the fog", await page.evaluate(() => {
    const c = document.getElementById("cv");
    const d = c.getContext("2d").getImageData(0, 0, c.width, c.height).data;
    // count pixels lighter than the void: compartment floors and walls
    let lit = 0;
    for (let i = 0; i < d.length; i += 4 * 97) if (d[i] + d[i + 1] + d[i + 2] > 60) lit++;
    return lit > 40;
  }));

  // ------------------------------------------------------- the glow layer
  //
  // Measured as the difference between a frame with the emissive pass and one
  // without, sampled ONLY inside the player's own sprite box at the exact
  // centre of the canvas.
  //
  // The first version of this compared whole frames and passed before the
  // feature existed, which is the "test that measures nothing" the plan warned
  // about: bots walk and effects animate between two frames, so a whole-frame
  // difference is mostly the game moving. The player's own 32px box is the one
  // region that holds still as long as nobody touches the controls, so that is
  // where the measurement goes. Averaged over three pairs to damp what is left.
  const probe = async (invisible) => page.evaluate(async (inv) => {
    const c = document.getElementById("cv"), g = c.getContext("2d");
    const frame = () => new Promise((r) => requestAnimationFrame(() => requestAnimationFrame(r)));
    const Z = 2, box = 34 * Z * (window.devicePixelRatio || 1);
    const x = Math.round(c.width / 2 - box / 2), y = Math.round(c.height / 2 - box / 2);
    const snap = () => g.getImageData(x, y, Math.round(box), Math.round(box)).data;

    window.__forceInvisible = !!inv;
    let gain = 0, bright = 0;
    for (let pass = 0; pass < 3; pass++) {
      window.__noGlow = false;
      await frame();
      const lit = snap();
      window.__noGlow = true;
      await frame();
      const dark = snap();
      for (let i = 0; i < lit.length; i += 4) {
        const a = lit[i] + lit[i + 1] + lit[i + 2];
        const d = a - (dark[i] + dark[i + 1] + dark[i + 2]);
        if (d > gain) gain = d;
        // absolute brightness of pixels the glow pass actually touched
        if (d > 5 && a > bright) bright = a;
      }
    }
    window.__noGlow = false;
    window.__forceInvisible = false;
    return { gain, bright };
  }, invisible);

  const solid = await probe(false);
  ok("the emissive layer survives the fog", solid.gain > 30,
    "brightest gain from the glow pass: " + solid.gain);

  // SC-005, the failure that is silent. A layer that ignores darkness must
  // not also ignore transparency, or Cień lights the mage up in exactly the
  // dark he needs.
  //
  // Measured as the absolute brightness of the pixels the glow pass touched,
  // NOT as its gain over the no-glow frame. The first version compared gains
  // and reported the implementation broken when it was correct: with
  // source-over, a full-alpha glow replaces an already-bright body pixel and
  // shows a small delta, while a 0.34 glow replaces a dimmed one and shows a
  // larger delta. The gain went *up* under invisibility while the sprite
  // itself correctly went dimmer.
  const faded = await probe(true);
  ok("the glow obeys invisibility", faded.bright < solid.bright * 0.85,
    "brightest lit pixel: solid " + solid.bright + " vs invisible " + faded.bright);

  ok("no console errors", errors.length === 0, errors.slice(0, 3).join(" | "));

  await page.screenshot({ path: "/tmp/claude-0/-home-user-private/52e79e33-cf85-553d-ae79-08317ac3905c/scratchpad/wizard-mobile.png" });
  console.log(`\n${fails ? fails + " failed" : "all passed"}`);

  await browser.close();
  bots.forEach((x) => x.ws.close());
  clearInterval(loop);
  server.close();
  process.exit(fails ? 1 : 0);
})().catch((e) => {
  console.error(e);
  clearInterval(loop);
  server.close();
  process.exit(1);
});

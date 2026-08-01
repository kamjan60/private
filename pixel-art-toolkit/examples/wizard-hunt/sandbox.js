// Single-player sandbox for "I'm Not a Wizard, Harry".
//
// Not the game - a range. Pick any class, including the mage, and walk the
// wreck to feel the kit: fog radius, taser reach, artifact channels, and the
// mage's three verbs. Dummies wander so there is something to aim at.
(function () {
  "use strict";

  var CLASS_ORDER = ["Strażnik", "Zwiadowca", "Strzelec", "Inkwizytor", "Chirurg", "Runarz"];
  var KIT = {
    "Strażnik":   { vision: 210, taser: 62, speed: 0.86, hp: 2, perk: "Pancerz: przeżywa pierwsze trafienie." },
    "Zwiadowca":  { vision: 330, taser: 58, speed: 1.14, hp: 1, perk: "Najdalszy wzrok + kamery (C)." },
    "Strzelec":   { vision: 250, taser: 330, speed: 1.0, hp: 1, perk: "Jedyny tazer dalekiego zasięgu." },
    "Inkwizytor": { vision: 240, taser: 70, speed: 1.0, hp: 1, perk: "Dłuższy zasięg tazera." },
    "Chirurg":    { vision: 230, taser: 58, speed: 0.98, hp: 1, perk: "Stabilizuje rannego (E na ciele)." },
    "Runarz":     { vision: 235, taser: 58, speed: 0.96, hp: 1, perk: "Ekstrakcja 2× szybciej." }
  };
  var MAGE = { vision: 260, speed: 1.04, hp: 1,
    perk: "Fireball (LPM), piorun AoE (PPM), przebranie (F)." };

  var COMPARTMENTS = [
    { x: 60, y: 60, w: 380, h: 240, name: "Mostek" },
    { x: 500, y: 60, w: 400, h: 200, name: "Ładownia" },
    { x: 960, y: 60, w: 380, h: 260, name: "Reaktor" },
    { x: 60, y: 360, w: 320, h: 240, name: "Medyczny" },
    { x: 440, y: 320, w: 420, h: 280, name: "Kaplica" },
    { x: 920, y: 380, w: 420, h: 220, name: "Warsztat" },
    { x: 120, y: 660, w: 400, h: 180, name: "Kriokomory" },
    { x: 580, y: 660, w: 380, h: 180, name: "Maszynownia" },
    { x: 1020, y: 660, w: 320, h: 180, name: "Śluza" }
  ];
  var W = 1400, H = 900, SPR = 32;
  // Zoom adapts to the viewport. Locked at 2 a phone shows ~195 world px of
  // a 210-330 px vision radius, so you would be blind inside your own
  // eyesight. Scaled to the canvas, a handset gets roughly the same field of
  // view as a desktop.
  var ZOOM = 2;
  function fitZoom() {
    ZOOM = Math.max(1, Math.min(2, cv.width / 460));
  }

  var TOUCH = ("ontouchstart" in window) || navigator.maxTouchPoints > 0;
  var stick = { active: false, id: null, ox: 0, oy: 0, x: 0, y: 0 };
  var lastAim = { x: 1, y: 0 };

  var FXDEF = {
    fire: { img: "fireball", w: 32, h: 32, frames: 6, ms: 80 },
    bolt: { img: "lightning", w: 64, h: 32, frames: 8, ms: 70 },
    sleep: { img: "sleep", w: 40, h: 48, frames: 8, ms: 200 }
  };
  var sheets = {};

  var $ = function (id) { return document.getElementById(id); };
  var cv, ctx, keys = {}, mouse = { x: 0, y: 0, down: 0 };
  var me = null, dummies = [], artifacts = [], fx = [], bolts = [], shots = [], balls = [];
  var running = false, last = 0;

  var NAMES = ["Kaz", "Mira", "Doran", "Sivi", "Halle", "Bruk", "Nessa"];

  // ------------------------------------------------------------------ setup
  function boot(sheetMap) {
    sheets = sheetMap;
    cv = $("cv"); ctx = cv.getContext("2d");
    resize();
    window.addEventListener("resize", resize);
    window.addEventListener("orientationchange", function () { setTimeout(resize, 120); });
    buildPicker();
    $("howto").innerHTML = TOUCH
      ? "Lewy kciuk gdziekolwiek po lewej — <b>ruch</b>. Dotknięcie po prawej — " +
        "<b>fireball</b> w to miejsce. Przyciski: przytrzymanie (artefakt), " +
        "piorun AoE, przebranie."
      : "Celuj myszą: <b>LPM</b> rzuca fireballa jako lecący pocisk, <b>PPM</b> wali " +
        "piorunem ogłuszającym w promieniu, <b>F</b> zmienia wygląd na najbliższą postać.";

    document.addEventListener("keydown", function (e) {
      if (!running) return;
      keys[e.code] = true;
      if (e.code === "Space") { e.preventDefault(); useTaser(); }
      if (e.code === "KeyF" && me.mage) disguise();
      if (e.code === "KeyC" && me.cls === "Zwiadowca") { me.seeAllUntil = now() + 5000; toast("Kamery aktywne"); }
      if (e.code === "Escape") quit();
    });
    document.addEventListener("keyup", function (e) { keys[e.code] = false; });
    cv.addEventListener("mousemove", function (e) {
      var r = cv.getBoundingClientRect();
      mouse.x = e.clientX - r.left; mouse.y = e.clientY - r.top;
    });
    cv.addEventListener("mousedown", function (e) {
      e.preventDefault();
      if (!running || !me.mage) return;
      if (e.button === 0) castFireball();
      if (e.button === 2) castStormAt();
    });
    cv.addEventListener("contextmenu", function (e) { e.preventDefault(); });
    $("btnQuit").addEventListener("click", quit);
    if (TOUCH) setupTouch();
  }

  // ------------------------------------------------------------------ touch
  function setupTouch() {
    document.body.classList.add("touch");

    // Left thumb drives a floating stick anchored wherever the finger lands,
    // rather than a fixed pad - on a handset you cannot look down to find it.
    cv.addEventListener("touchstart", function (e) {
      for (var i = 0; i < e.changedTouches.length; i++) {
        var t = e.changedTouches[i];
        var r = cv.getBoundingClientRect();
        var x = t.clientX - r.left, y = t.clientY - r.top;
        if (x < cv.width * 0.45 && !stick.active) {
          stick.active = true; stick.id = t.identifier;
          stick.ox = x; stick.oy = y; stick.x = x; stick.y = y;
        } else if (running && me && me.mage) {
          // Tap the right side to aim and throw in one gesture. A separate
          // aim-then-fire pair needs two thumbs and reads as a chore.
          aimAtScreen(x, y);
          castFireball();
        }
      }
      e.preventDefault();
    }, { passive: false });

    cv.addEventListener("touchmove", function (e) {
      for (var i = 0; i < e.changedTouches.length; i++) {
        var t = e.changedTouches[i];
        if (t.identifier === stick.id) {
          var r = cv.getBoundingClientRect();
          stick.x = t.clientX - r.left; stick.y = t.clientY - r.top;
        }
      }
      e.preventDefault();
    }, { passive: false });

    function endTouch(e) {
      for (var i = 0; i < e.changedTouches.length; i++) {
        if (e.changedTouches[i].identifier === stick.id) {
          stick.active = false; stick.id = null;
        }
      }
    }
    cv.addEventListener("touchend", endTouch);
    cv.addEventListener("touchcancel", endTouch);

    bindBtn("tHold", null, function (down) { keys.KeyE = down; });
    bindBtn("tA", function () {
      if (me.mage) castStormAt(); else useTaser();
    });
    bindBtn("tB", function () {
      if (me.mage) disguise();
      else if (me.cls === "Zwiadowca") { me.seeAllUntil = now() + 5000; toast("Kamery aktywne"); }
    });
  }

  function bindBtn(id, tap, holdFn) {
    var el = $(id);
    if (!el) return;
    el.addEventListener("touchstart", function (e) {
      e.preventDefault(); e.stopPropagation();
      el.classList.add("on");
      if (holdFn) holdFn(true); else if (tap) tap();
    }, { passive: false });
    var off = function (e) {
      e.preventDefault(); e.stopPropagation();
      el.classList.remove("on");
      if (holdFn) holdFn(false);
    };
    el.addEventListener("touchend", off);
    el.addEventListener("touchcancel", off);
  }

  function aimAtScreen(x, y) {
    var dx = x - cv.width / 2, dy = y - cv.height / 2;
    var d = Math.hypot(dx, dy) || 1;
    lastAim = { x: dx / d, y: dy / d };
    mouse.x = x; mouse.y = y;
  }

  function resize() {
    if (!cv) return;
    cv.width = cv.clientWidth; cv.height = cv.clientHeight;
    fitZoom();
    ctx.imageSmoothingEnabled = false;
  }
  function now() { return performance.now(); }

  function buildPicker() {
    var wrap = $("cards");
    wrap.innerHTML = "";
    CLASS_ORDER.forEach(function (cls, i) {
      wrap.appendChild(card(cls, i, KIT[cls].perk, false));
    });
    wrap.appendChild(card("Mag", 5, MAGE.perk, true));
  }

  function card(cls, row, perk, isMage) {
    var d = document.createElement("button");
    d.className = "pick" + (isMage ? " mage" : "");
    var cnv = document.createElement("canvas");
    cnv.width = SPR * 3; cnv.height = SPR * 3;
    var c = cnv.getContext("2d");
    c.imageSmoothingEnabled = false;
    // The mage card shows the arcade wizard, everyone else their class body.
    if (isMage) c.drawImage(sheets.wizard, 0, 0, 32, 32, 0, 0, SPR * 3, SPR * 3);
    else c.drawImage(sheets.hunters, 0, row * 4 * SPR, SPR, SPR, 0, 0, SPR * 3, SPR * 3);
    d.appendChild(cnv);
    var h = document.createElement("strong"); h.textContent = cls;
    var p = document.createElement("small"); p.textContent = perk;
    d.appendChild(h); d.appendChild(p);
    d.addEventListener("click", function () { start(cls, row, isMage); });
    return d;
  }

  // ------------------------------------------------------------------ round
  function start(cls, row, isMage) {
    var kit = isMage ? MAGE : KIT[cls];
    me = {
      x: 700, y: 460, dir: 0, step: 0, phase: 0, cls: isMage ? "Runarz" : cls,
      realRow: isMage ? 5 : row, row: isMage ? 5 : row, mage: !!isMage,
      vision: kit.vision, speed: kit.speed, hp: kit.hp, maxhp: kit.hp,
      taserRange: isMage ? 0 : KIT[cls].taser,
      cd: { taser: 0, ball: 0, storm: 0, disguise: 0 },
      channel: null, seeAllUntil: 0, disguisedUntil: 0
    };
    dummies = [];
    for (var i = 0; i < 7; i++) {
      var r = Math.floor(Math.random() * 6);
      dummies.push({
        name: NAMES[i % NAMES.length], row: r, cls: CLASS_ORDER[r],
        x: 150 + Math.random() * (W - 300), y: 150 + Math.random() * (H - 300),
        tx: 0, ty: 0, dir: 0, step: 0, phase: 0, hp: 1, alive: true, stun: 0
      });
      retarget(dummies[i]);
    }
    artifacts = COMPARTMENTS.map(function (c, i) {
      return { id: i, x: c.x + 50 + Math.random() * (c.w - 100),
               y: c.y + 50 + Math.random() * (c.h - 100), done: false, room: c.name };
    });
    fx = []; bolts = []; shots = []; balls = [];

    $("picker").style.display = "none";
    $("stage").style.display = "block";
    resize();
    $("hRole").innerHTML = isMage ? "<b>MAG</b>" : "ŁOWCA · <b>" + cls + "</b>";
    $("hRole").className = "pill" + (isMage ? " mage" : "");
    $("hPerk").textContent = kit.perk;
    renderKeyHints();
    running = true; last = now();
    requestAnimationFrame(loop);
  }

  function quit() {
    running = false;
    $("stage").style.display = "none";
    $("picker").style.display = "flex";
  }

  function retarget(d) {
    d.tx = 80 + Math.random() * (W - 160);
    d.ty = 80 + Math.random() * (H - 160);
  }

  // ---------------------------------------------------------------- actions
  function aimVector() {
    // Aim is screen-relative: the player is always dead centre of the view.
    // On touch the last tap sets it, so the storm button fires along the same
    // heading as the last fireball instead of needing its own aim gesture.
    if (TOUCH) return lastAim;
    var dx = mouse.x - cv.width / 2, dy = mouse.y - cv.height / 2;
    var d = Math.hypot(dx, dy) || 1;
    return { x: dx / d, y: dy / d };
  }

  function castFireball() {
    if (me.cd.ball > 0) return;
    me.cd.ball = 1400;
    var v = aimVector();
    // A travelling projectile, not a hitscan: it can be dodged and it shows
    // the caster's position for as long as it is in the air.
    balls.push({ x: me.x, y: me.y - 12, vx: v.x * 7.2, vy: v.y * 7.2, born: now() });
  }

  function castStormAt() {
    if (me.cd.storm > 0) return;
    me.cd.storm = 5200;
    var v = aimVector();
    var reach = 260;
    var tx = me.x + v.x * reach, ty = me.y + v.y * reach;
    var R = 130;
    var hit = dummies.filter(function (d) {
      return d.alive && Math.hypot(d.x - tx, d.y - ty) < R;
    });
    hit.forEach(function (d) { d.stun = now() + 3600; });
    // Arcs are drawn from the strike point to each victim, which is what
    // makes an area stun read as chain lightning rather than as a circle.
    bolts.push({ x: tx, y: ty, r: R, targets: hit.map(function (d) { return d; }),
                 born: now(), life: 620 });
    fx.push({ def: FXDEF.bolt, x: tx, y: ty, born: now(), life: 900 });
    toast(hit.length ? "Ogłuszono: " + hit.length : "Piorun w pustkę");
  }

  function disguise() {
    if (me.cd.disguise > 0) return;
    var near = visibleDummies().filter(function (d) { return d.alive; })
      .sort(function (a, b) { return dist(a, me) - dist(b, me); })[0];
    if (!near) { toast("Nikogo w zasięgu, by się podszyć"); return; }
    me.cd.disguise = 18000;
    me.row = near.row;
    me.disguisedUntil = now() + 12000;
    fx.push({ def: FXDEF.sleep, x: me.x, y: me.y, born: now(), life: 900 });
    toast("Przebranie: " + near.cls);
  }

  function useTaser() {
    if (me.mage || me.cd.taser > 0) return;
    me.cd.taser = me.cls === "Strzelec" ? 6500 : 4200;
    var t = dummies.filter(function (d) { return d.alive && dist(d, me) <= me.taserRange; })
      .sort(function (a, b) { return dist(a, me) - dist(b, me); })[0];
    shots.push({ a: { x: me.x, y: me.y }, b: t ? { x: t.x, y: t.y } : null,
                 born: now(), life: 240, ranged: me.cls === "Strzelec" });
    if (t) { t.stun = now() + 3600; toast("Obezwładniony: " + t.name); }
    else toast("Pudło");
  }

  function dist(a, b) { return Math.hypot(a.x - b.x, a.y - b.y); }
  function visibleDummies() {
    var R = me.seeAllUntil > now() ? 99999 : me.vision;
    return dummies.filter(function (d) { return dist(d, me) <= R; });
  }

  // ------------------------------------------------------------------- loop
  function loop(t) {
    if (!running) return;
    var dt = Math.min(48, t - last); last = t;
    update(dt);
    draw();
    requestAnimationFrame(loop);
  }

  function update(dt) {
    for (var k in me.cd) me.cd[k] = Math.max(0, me.cd[k] - dt);
    if (me.disguisedUntil && now() > me.disguisedUntil) { me.row = me.realRow; me.disguisedUntil = 0; }

    var ix = (keys.KeyD || keys.ArrowRight ? 1 : 0) - (keys.KeyA || keys.ArrowLeft ? 1 : 0);
    var iy = (keys.KeyS || keys.ArrowDown ? 1 : 0) - (keys.KeyW || keys.ArrowUp ? 1 : 0);
    if (stick.active) {
      var sdx = stick.x - stick.ox, sdy = stick.y - stick.oy;
      var sd = Math.hypot(sdx, sdy);
      if (sd > 8) {                        // dead zone, or a stationary thumb drifts
        var cl = Math.min(1, sd / 56);
        ix = (sdx / sd) * cl; iy = (sdy / sd) * cl;
      }
    }
    var len = Math.hypot(ix, iy);
    if (len > 0.01) {
      var sp = 2.5 * me.speed * (dt / (1000 / 60));
      me.x = Math.max(16, Math.min(W - 16, me.x + (ix / len) * sp));
      me.y = Math.max(24, Math.min(H - 10, me.y + (iy / len) * sp));
      me.dir = Math.abs(ix) > Math.abs(iy) ? (ix < 0 ? 1 : 2) : (iy < 0 ? 3 : 0);
      me.phase += sp; me.step = Math.floor(me.phase / 10) % 2;
      me.channel = null;                       // moving breaks a channel
    } else if (keys.KeyE) {
      doHold(dt);
    } else {
      me.channel = null;
    }

    dummies.forEach(function (d) {
      if (!d.alive || d.stun > now()) return;
      var dx = d.tx - d.x, dy = d.ty - d.y, dd = Math.hypot(dx, dy);
      if (dd < 8) return retarget(d);
      var s = 1.5 * (dt / (1000 / 60));
      d.x += (dx / dd) * s; d.y += (dy / dd) * s;
      d.dir = Math.abs(dx) > Math.abs(dy) ? (dx < 0 ? 1 : 2) : (dy < 0 ? 3 : 0);
      d.phase += s; d.step = Math.floor(d.phase / 10) % 2;
    });

    // fireballs travel, then detonate on a body or at the end of their run
    balls = balls.filter(function (b) {
      b.x += b.vx * (dt / (1000 / 60)); b.y += b.vy * (dt / (1000 / 60));
      var victim = dummies.filter(function (d) { return d.alive && dist(d, b) < 22; })[0];
      var outside = b.x < 0 || b.y < 0 || b.x > W || b.y > H;
      if (victim || outside || now() - b.born > 2200) {
        fx.push({ def: FXDEF.fire, x: b.x, y: b.y, born: now(), life: 620 });
        if (victim) { victim.alive = false; toast(victim.name + " spalony"); }
        return false;
      }
      return true;
    });
  }

  function doHold(dt) {
    var body = dummies.filter(function (d) { return !d.alive && dist(d, me) < 46; })[0];
    var art = artifacts.filter(function (a) { return !a.done && dist(a, me) < 40; })[0];
    var stunned = dummies.filter(function (d) { return d.alive && d.stun > now() && dist(d, me) < 52; })[0];

    var kind = null, ms = 0, target = null;
    if (!me.mage && stunned) { kind = "capture"; ms = 1800; target = stunned; }
    else if (!me.mage && me.cls === "Chirurg" && body) { kind = "revive"; ms = 1800; target = body; }
    else if (art) { kind = "extract"; ms = me.cls === "Runarz" ? 1400 : 2800; target = art; }

    if (!kind) { me.channel = null; return; }
    if (!me.channel || me.channel.kind !== kind || me.channel.target !== target) {
      me.channel = { kind: kind, target: target, ms: ms, t: 0 };
    }
    me.channel.t += dt;
    if (me.channel.t >= ms) {
      if (kind === "extract") { target.done = true; toast("Artefakt zabezpieczony (" + target.room + ")"); }
      if (kind === "revive") { target.alive = true; target.stun = now() + 900; toast(target.name + " ustabilizowany"); }
      if (kind === "capture") { target.alive = false; toast(target.name + " związany"); }
      me.channel = null;
    }
  }

  // ----------------------------------------------------------------- render
  function draw() {
    ctx.fillStyle = "#05070c"; ctx.fillRect(0, 0, cv.width, cv.height);
    var camX = me.x * ZOOM - cv.width / 2, camY = me.y * ZOOM - cv.height / 2;
    ctx.save(); ctx.translate(-camX, -camY);

    COMPARTMENTS.forEach(function (c) {
      ctx.fillStyle = "rgba(24,32,52,0.78)";
      ctx.fillRect(c.x * ZOOM, c.y * ZOOM, c.w * ZOOM, c.h * ZOOM);
      ctx.strokeStyle = "rgba(120,150,220,0.3)"; ctx.lineWidth = 2;
      ctx.strokeRect(c.x * ZOOM, c.y * ZOOM, c.w * ZOOM, c.h * ZOOM);
      ctx.fillStyle = "rgba(139,154,192,0.5)"; ctx.font = "11px system-ui";
      ctx.fillText(c.name.toUpperCase(), c.x * ZOOM + 8, c.y * ZOOM + 18);
    });

    var t = now();
    artifacts.forEach(function (a) {
      if (!a.done && dist(a, me) > (me.seeAllUntil > t ? 99999 : me.vision)) return;
      var x = a.x * ZOOM, y = a.y * ZOOM;
      if (a.done) { ctx.fillStyle = "rgba(124,232,168,0.55)"; ctx.fillRect(x - 5, y - 5, 10, 10); return; }
      ctx.save(); ctx.translate(x, y); ctx.rotate((t / 400) % (Math.PI * 2));
      ctx.fillStyle = "#c682ff"; ctx.fillRect(-6, -6, 12, 12); ctx.restore();
      ctx.strokeStyle = "rgba(198,130,255," + (0.3 + 0.25 * Math.sin(t / 200)) + ")";
      ctx.lineWidth = 2; ctx.beginPath(); ctx.arc(x, y, 16, 0, 6.29); ctx.stroke();
    });

    visibleDummies().forEach(function (d) { drawActor(d, false); });
    drawActor(me, true);

    // storm arcs
    bolts = bolts.filter(function (b) { return t - b.born < b.life; });
    bolts.forEach(function (b) {
      var k = 1 - (t - b.born) / b.life;
      ctx.strokeStyle = "rgba(120,208,255," + k + ")"; ctx.lineWidth = 2;
      ctx.beginPath(); ctx.arc(b.x * ZOOM, b.y * ZOOM, b.r * ZOOM * (1 - k * 0.15), 0, 6.29); ctx.stroke();
      b.targets.forEach(function (d) {
        ctx.beginPath();
        ctx.moveTo(b.x * ZOOM, b.y * ZOOM);
        // jitter the mid-point so each arc looks struck, not drawn
        var mx = (b.x + d.x) / 2 * ZOOM + (Math.random() - 0.5) * 26;
        var my = (b.y + d.y) / 2 * ZOOM + (Math.random() - 0.5) * 26;
        ctx.quadraticCurveTo(mx, my, d.x * ZOOM, d.y * ZOOM - 20);
        ctx.stroke();
      });
    });

    shots = shots.filter(function (s) { return t - s.born < s.life; });
    shots.forEach(function (s) {
      if (!s.b) return;
      var k = 1 - (t - s.born) / s.life;
      ctx.strokeStyle = (s.ranged ? "rgba(120,208,255," : "rgba(255,255,255,") + k + ")";
      ctx.lineWidth = s.ranged ? 3 : 2;
      ctx.beginPath();
      ctx.moveTo(s.a.x * ZOOM, s.a.y * ZOOM - 20);
      ctx.lineTo(s.b.x * ZOOM, s.b.y * ZOOM - 20);
      ctx.stroke();
    });

    balls.forEach(function (b) {
      var d = FXDEF.fire, fr = Math.floor((t - b.born) / d.ms) % d.frames;
      var ang = Math.atan2(b.vy, b.vx);
      ctx.save();
      ctx.translate(b.x * ZOOM, b.y * ZOOM);
      ctx.rotate(ang);
      ctx.drawImage(sheets.fireball, fr * d.w, 0, d.w, d.h,
        -d.w * ZOOM / 2, -d.h * ZOOM / 2, d.w * ZOOM, d.h * ZOOM);
      ctx.restore();
    });

    fx = fx.filter(function (f) { return t - f.born < f.life; });
    fx.forEach(function (f) {
      var d = f.def, fr = Math.floor((t - f.born) / d.ms) % d.frames;
      ctx.drawImage(sheets[d.img], fr * d.w, 0, d.w, d.h,
        f.x * ZOOM - d.w * ZOOM / 2, f.y * ZOOM - d.h * ZOOM / 2, d.w * ZOOM, d.h * ZOOM);
    });

    ctx.restore();
    drawFog(camX, camY);
    drawOverlay();
  }

  function drawActor(a, isMe) {
    var sx = a.step * SPR, sy = (a.row * 4 + a.dir) * SPR;
    var x = a.x * ZOOM - SPR * ZOOM / 2, y = a.y * ZOOM - SPR * ZOOM;
    if (!a.alive && !isMe) {
      ctx.save(); ctx.globalAlpha = 0.7;
      ctx.translate(a.x * ZOOM, a.y * ZOOM); ctx.rotate(Math.PI / 2);
      ctx.drawImage(sheets.hunters, 0, a.row * 4 * SPR, SPR, SPR,
        -SPR * ZOOM / 2, -SPR * ZOOM / 2, SPR * ZOOM, SPR * ZOOM);
      ctx.restore();
      return;
    }
    if (a.stun > now()) {
      ctx.strokeStyle = "rgba(255,195,92,0.9)"; ctx.lineWidth = 2;
      ctx.beginPath(); ctx.arc(a.x * ZOOM, a.y * ZOOM - 20, 26, 0, 6.29); ctx.stroke();
    }
    ctx.drawImage(sheets.hunters, sx, sy, SPR, SPR, x, y, SPR * ZOOM, SPR * ZOOM);
    ctx.font = "12px system-ui"; ctx.textAlign = "center";
    ctx.fillStyle = isMe ? "#7fd8ff" : "rgba(230,236,250,0.8)";
    ctx.fillText(isMe ? "TY" + (me.disguisedUntil ? " (przebrany)" : "") : a.name,
      a.x * ZOOM, a.y * ZOOM - SPR * ZOOM - 4);
    ctx.textAlign = "left";
  }

  function drawFog(camX, camY) {
    if (me.seeAllUntil > now()) return;
    var cx = me.x * ZOOM - camX, cy = me.y * ZOOM - camY, r = me.vision * ZOOM;
    // One radial gradient: canvas extends the last stop past the end radius,
    // so everything beyond the circle is already opaque.
    var g = ctx.createRadialGradient(cx, cy, r * 0.62, cx, cy, r);
    g.addColorStop(0, "rgba(5,7,12,0)");
    g.addColorStop(1, "rgba(5,7,12,0.985)");
    ctx.fillStyle = g;
    ctx.fillRect(0, 0, cv.width, cv.height);
  }

  function drawOverlay() {
    if (stick.active) {                    // floating stick, drawn where it was placed
      ctx.strokeStyle = "rgba(127,216,255,0.35)"; ctx.lineWidth = 2;
      ctx.beginPath(); ctx.arc(stick.ox, stick.oy, 56, 0, 6.29); ctx.stroke();
      var dx = stick.x - stick.ox, dy = stick.y - stick.oy;
      var d = Math.hypot(dx, dy), c = Math.min(1, d / 56) * 56;
      var nx = d ? dx / d : 0, ny = d ? dy / d : 0;
      ctx.fillStyle = "rgba(127,216,255,0.55)";
      ctx.beginPath(); ctx.arc(stick.ox + nx * c, stick.oy + ny * c, 22, 0, 6.29); ctx.fill();
    }
    // crosshair, so aiming reads as aiming
    if (me.mage && !TOUCH) {
      ctx.strokeStyle = "rgba(198,130,255,0.8)"; ctx.lineWidth = 1.5;
      ctx.beginPath(); ctx.arc(mouse.x, mouse.y, 9, 0, 6.29); ctx.stroke();
      ctx.beginPath();
      ctx.moveTo(mouse.x - 14, mouse.y); ctx.lineTo(mouse.x - 4, mouse.y);
      ctx.moveTo(mouse.x + 4, mouse.y); ctx.lineTo(mouse.x + 14, mouse.y);
      ctx.moveTo(mouse.x, mouse.y - 14); ctx.lineTo(mouse.x, mouse.y - 4);
      ctx.moveTo(mouse.x, mouse.y + 4); ctx.lineTo(mouse.x, mouse.y + 14);
      ctx.stroke();
    }
    if (me.channel) {
      var labels = { extract: "Ekstrakcja", capture: "Wiązanie", revive: "Stabilizacja" };
      var w = 230, x0 = cv.width / 2 - w / 2, y0 = cv.height - 128;
      ctx.fillStyle = "rgba(10,14,24,0.9)"; ctx.fillRect(x0, y0, w, 26);
      ctx.fillStyle = "#7fd8ff";
      ctx.fillRect(x0 + 3, y0 + 3, (w - 6) * Math.min(1, me.channel.t / me.channel.ms), 20);
      ctx.fillStyle = "#05070c"; ctx.font = "12px system-ui"; ctx.textAlign = "center";
      ctx.fillText(labels[me.channel.kind], cv.width / 2, y0 + 18);
      ctx.textAlign = "left";
    }
    $("hArt").textContent = artifacts.filter(function (a) { return a.done; }).length +
      "/" + artifacts.length;
    $("hAlive").textContent = dummies.filter(function (d) { return d.alive; }).length;
    renderKeyHints();
  }

  function renderKeyHints() {
    if (TOUCH) {                           // labels live on the buttons instead
      var A = $("tA"), B = $("tB");
      if (A) {
        // Short labels: anything longer overflows an 80px circle on a handset
        A.querySelector("span").textContent = me.mage ? "PIORUN" : "TAZER";
        A.classList.toggle("cd", (me.mage ? me.cd.storm : me.cd.taser) > 0);
      }
      if (B) {
        var show = me.mage || me.cls === "Zwiadowca";
        B.style.display = show ? "flex" : "none";
        B.querySelector("span").textContent = me.mage ? "MASKA" : "KAMERY";
        B.classList.toggle("cd", me.mage && me.cd.disguise > 0);
      }
      $("keys").innerHTML = me.mage
        ? '<div class="key">Dotknij po prawej — <b>fireball</b></div>'
        : '<div class="key">Lewy kciuk — ruch</div>';
      return;
    }
    var out = [key("WSAD", "ruch", 0), key("E", "przytrzymaj: artefakt / wiązanie", 0)];
    if (me.mage) {
      out.push(key("LPM", "fireball", me.cd.ball));
      out.push(key("PPM", "piorun AoE (stun)", me.cd.storm));
      out.push(key("F", "przebranie", me.cd.disguise));
    } else {
      out.push(key("SPACJA", me.cls === "Strzelec" ? "karabin" : "tazer", me.cd.taser));
      if (me.cls === "Zwiadowca") out.push(key("C", "kamery", 0));
    }
    out.push(key("ESC", "wybór klasy", 0));
    $("keys").innerHTML = out.join("");
  }
  function key(k, label, cd) {
    return '<div class="key' + (cd > 0 ? " cd" : "") + '"><b>' + k + "</b> " + label +
      (cd > 0 ? " (" + (cd / 1000).toFixed(1) + "s)" : "") + "</div>";
  }

  var toastT = null;
  function toast(msg) {
    var el = $("toast");
    el.textContent = msg; el.style.opacity = 1;
    clearTimeout(toastT);
    toastT = setTimeout(function () { el.style.opacity = 0; }, 1800);
  }

  window.__boot = boot;
})();

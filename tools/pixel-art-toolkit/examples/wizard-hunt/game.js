// "I'm Not a Wizard, Harry" - hidden-mage deduction.
//
// One of six marines is a wizard. Every cast leaves an FX bloom on the
// deck; only marines that were close enough to it could have cast. The
// wizard is always in that set, so intersecting the sets across casts
// narrows the field. The player accuses; a wrong accusation costs a
// marine, and the wizard is picking them off in the meantime.
(function () {
  "use strict";

  var Z = 2;                      // sprite zoom
  var ARENA_W = 620, ARENA_H = 380;
  var SPR = 32 * Z;               // on-screen marine size
  var CAST_EVERY = 6200;          // ms between casts
  var KILL_EVERY = 13000;         // ms between wizard kills
  var DETECT_R = 118;             // how close a marine must be to be a suspect
  var CAST_SPREAD = 46;           // FX lands this far from the wizard, at most

  var NAMES = ["Vance", "Okoye", "Reyes", "Ilves", "Petrov", "Sato"];
  var FX = {
    fire:  { cls: "fx-fire",  w: 32, h: 32, label: "ogień" },
    bolt:  { cls: "fx-bolt",  w: 64, h: 32, label: "błyskawica" },
    sleep: { cls: "fx-sleep", w: 40, h: 48, label: "sen" }
  };
  var FX_KEYS = ["fire", "bolt", "sleep"];

  var arena = document.getElementById("arena");
  var roster = document.getElementById("roster");
  var logEl = document.getElementById("log");
  var statusEl = document.getElementById("status");
  var accEl = document.getElementById("accusations");
  var castEl = document.getElementById("castcount");
  var restartBtn = document.getElementById("restart");

  var marines, wizard, casts, accusations, over, lastCast, lastKill, raf;

  function rnd(a, b) { return a + Math.random() * (b - a); }
  function dist(a, b) { return Math.hypot(a.x - b.x, a.y - b.y); }

  function log(msg, kind) {
    var d = document.createElement("div");
    d.className = "log-line" + (kind ? " " + kind : "");
    d.textContent = msg;
    logEl.insertBefore(d, logEl.firstChild);
    while (logEl.childNodes.length > 40) logEl.removeChild(logEl.lastChild);
  }

  function init() {
    cancelAnimationFrame(raf);
    arena.querySelectorAll(".marine, .fx, .bloom").forEach(function (n) { n.remove(); });
    logEl.innerHTML = "";
    casts = [];
    accusations = 2;
    over = false;
    // Offsets are subtracted from the interval, not added to `now` - added,
    // the first cast lands at interval + delay instead of at the delay.
    lastCast = performance.now() - CAST_EVERY + 2500;
    lastKill = performance.now() - KILL_EVERY + 9000;

    marines = NAMES.map(function (name, i) {
      var el = document.createElement("div");
      el.className = "marine";
      el.style.width = SPR + "px";
      el.style.height = SPR + "px";
      el.title = name;
      el.addEventListener("click", function () { accuse(i); });
      arena.appendChild(el);
      return {
        i: i, name: name, el: el,
        x: rnd(40, ARENA_W - 40), y: rnd(40, ARENA_H - 40),
        tx: 0, ty: 0, dir: 0, step: 0, phase: Math.random() * 1000,
        alive: true, seen: 0
      };
    });
    marines.forEach(retarget);
    wizard = Math.floor(Math.random() * marines.length);

    statusEl.textContent = "Namierz maga.";
    statusEl.className = "status";
    renderRoster();
    updateHud();
    log("Patrol rozpoczęty. Jeden z sześciu jest magiem.");
    raf = requestAnimationFrame(tick);
  }

  function retarget(m) {
    m.tx = rnd(30, ARENA_W - 30);
    m.ty = rnd(30, ARENA_H - 30);
  }

  function updateHud() {
    accEl.textContent = accusations;
    castEl.textContent = casts.length;
  }

  function renderRoster() {
    roster.innerHTML = "";
    marines.forEach(function (m) {
      var row = document.createElement("button");
      row.className = "suspect" + (m.alive ? "" : " dead");
      row.disabled = !m.alive || over;
      row.addEventListener("click", function () { accuse(m.i); });

      var chip = document.createElement("span");
      chip.className = "chip";
      chip.style.backgroundPositionY = -(m.i * 4 * 32 * 1.5) + "px";

      var body = document.createElement("span");
      body.className = "s-body";
      var nm = document.createElement("strong");
      nm.textContent = m.name;
      var meta = document.createElement("small");
      if (!m.alive) {
        meta.textContent = "wyeliminowany";
      } else if (casts.length === 0) {
        meta.textContent = "brak danych";
      } else {
        meta.textContent = "w zasięgu " + m.seen + " / " + casts.length + " zaklęć";
      }
      body.appendChild(nm);
      body.appendChild(meta);

      var bar = document.createElement("span");
      bar.className = "bar";
      var fill = document.createElement("i");
      var pct = casts.length ? (m.seen / casts.length) * 100 : 0;
      fill.style.width = pct + "%";
      // A marine present at *every* cast is the strongest lead; one missing
      // from any cast is provably innocent, so the bar is the whole tell.
      if (casts.length && m.seen === casts.length) fill.className = "hot";
      else if (casts.length && m.seen === 0) fill.className = "cold";
      bar.appendChild(fill);
      body.appendChild(bar);

      row.appendChild(chip);
      row.appendChild(body);
      roster.appendChild(row);
    });
  }

  function tick(now) {
    if (!over) {
      step(now);
      if (now - lastCast > CAST_EVERY) { lastCast = now; doCast(); }
      if (now - lastKill > KILL_EVERY) { lastKill = now; doKill(); }
    }
    raf = requestAnimationFrame(tick);
  }

  function step(now) {
    marines.forEach(function (m) {
      if (!m.alive) return;
      var dx = m.tx - m.x, dy = m.ty - m.y;
      var d = Math.hypot(dx, dy);
      if (d < 6) { retarget(m); return; }
      var sp = 0.55;
      m.x += (dx / d) * sp;
      m.y += (dy / d) * sp;
      // facing from the dominant axis; sprite rows are down/left/right/up
      m.dir = Math.abs(dx) > Math.abs(dy) ? (dx < 0 ? 1 : 2) : (dy < 0 ? 3 : 0);
      m.phase += sp;
      m.step = (Math.floor(m.phase / 9) % 2);
      m.el.style.transform = "translate(" + (m.x - SPR / 2) + "px," + (m.y - SPR) + "px)";
      m.el.style.backgroundPosition =
        -(m.step * 32 * Z) + "px " + -((m.i * 4 + m.dir) * 32 * Z) + "px";
    });
  }

  function doCast() {
    var w = marines[wizard];
    if (!w.alive) return;
    var kind = FX_KEYS[Math.floor(Math.random() * FX_KEYS.length)];
    var a = Math.random() * Math.PI * 2;
    var r = rnd(14, CAST_SPREAD);
    var cx = Math.max(30, Math.min(ARENA_W - 30, w.x + Math.cos(a) * r));
    var cy = Math.max(40, Math.min(ARENA_H - 20, w.y + Math.sin(a) * r));

    var suspects = marines.filter(function (m) {
      return m.alive && dist(m, { x: cx, y: cy }) <= DETECT_R;
    }).map(function (m) { return m.i; });
    // the wizard is by construction always inside the radius
    if (suspects.indexOf(wizard) < 0) suspects.push(wizard);

    casts.push({ x: cx, y: cy, kind: kind, suspects: suspects });
    marines.forEach(function (m) {
      if (m.alive && suspects.indexOf(m.i) >= 0) m.seen++;
    });

    spawnFx(kind, cx, cy);
    spawnBloom(cx, cy);
    log("Wykryto zaklęcie: " + FX[kind].label + ". W zasięgu: " +
        suspects.map(function (i) { return marines[i].name; }).join(", "), "cast");
    renderRoster();
    updateHud();
  }

  function spawnFx(kind, x, y) {
    var f = FX[kind];
    var el = document.createElement("div");
    el.className = "fx " + f.cls;
    el.style.width = (f.w * Z) + "px";
    el.style.height = (f.h * Z) + "px";
    el.style.transform = "translate(" + (x - f.w * Z / 2) + "px," + (y - f.h * Z / 2) + "px)";
    arena.appendChild(el);
    setTimeout(function () { el.remove(); }, 1500);
  }

  function spawnBloom(x, y) {
    var b = document.createElement("div");
    b.className = "bloom";
    b.style.transform = "translate(" + (x - DETECT_R) + "px," + (y - DETECT_R) + "px)";
    b.style.width = b.style.height = (DETECT_R * 2) + "px";
    arena.appendChild(b);
    setTimeout(function () { b.remove(); }, 1500);
  }

  function doKill() {
    var w = marines[wizard];
    if (!w.alive) return;
    var victims = marines.filter(function (m) {
      return m.alive && m.i !== wizard && dist(m, w) < 150;
    });
    if (!victims.length) return;
    var v = victims[Math.floor(Math.random() * victims.length)];
    kill(v, "zginął od zaklęcia");
    spawnFx("bolt", v.x, v.y);
    if (marines.filter(function (m) { return m.alive; }).length <= 2) {
      finish(false, "Zostało za mało łowców. Mag wygrał.");
    }
  }

  function kill(m, why) {
    m.alive = false;
    m.el.classList.add("down");
    log(m.name + " " + why + ".", "bad");
    renderRoster();
  }

  function accuse(i) {
    if (over) return;
    var m = marines[i];
    if (!m.alive) return;
    if (i === wizard) {
      m.el.classList.add("revealed");
      finish(true, m.name + " był magiem. Polowanie zakończone.");
      return;
    }
    accusations--;
    kill(m, "był niewinny — egzekucja");
    updateHud();
    if (accusations <= 0) {
      finish(false, "Wyczerpano oskarżenia. Mag wygrał.");
    } else {
      statusEl.textContent = "Pomyłka. Pozostałe oskarżenia: " + accusations;
      statusEl.className = "status warn";
    }
  }

  function finish(win, msg) {
    over = true;
    statusEl.textContent = msg;
    statusEl.className = "status " + (win ? "win" : "lose");
    marines[wizard].el.classList.add("revealed");
    log(msg, win ? "good" : "bad");
    renderRoster();
  }

  restartBtn.addEventListener("click", init);
  init();
})();

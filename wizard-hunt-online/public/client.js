// Client for "I'm Not a Wizard, Harry".
//
// Rendering only - the server owns the simulation and already culls anything
// outside your vision radius, so this file never learns where an unseen
// player is. The dark overlay is presentation; the actual secrecy is that
// the data is not in the socket.
(function () {
  "use strict";

  var CLASS_ORDER = ["Strażnik", "Zwiadowca", "Strzelec", "Inkwizytor", "Chirurg", "Runarz"];
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
  var WORLD_W = 1400, WORLD_H = 900;
  var SPR = 32, ZOOM = 2;

  var sheets = {};
  ["hunters", "fireball", "lightning", "sleep", "wizard"].forEach(function (k) {
    var i = new Image(); i.src = "assets/" + k + ".png"; sheets[k] = i;
  });
  var FXDEF = {
    fire: { img: "fireball", w: 32, h: 32, frames: 6, ms: 80 },
    bolt: { img: "lightning", w: 64, h: 32, frames: 8, ms: 70 },
    sleep: { img: "sleep", w: 40, h: 48, frames: 8, ms: 200 }
  };

  var $ = function (id) { return document.getElementById(id); };
  var cv = $("cv"), ctx = cv.getContext("2d");
  var ws = null, me = null, roomId = null, isHost = false;
  var state = null, role = null, myCls = null, myVision = 240;
  var fx = [], shots = [], windups = [];
  var keys = {}, over = false;

  function resize() {
    cv.width = window.innerWidth; cv.height = window.innerHeight;
    ctx.imageSmoothingEnabled = false;
  }
  window.addEventListener("resize", resize); resize();

  // --------------------------------------------------------------- network
  function connect(name, room) {
    var proto = location.protocol === "https:" ? "wss:" : "ws:";
    ws = new WebSocket(proto + "//" + location.host);
    ws.onopen = function () { ws.send(JSON.stringify({ t: "join", name: name, room: room || null })); };
    ws.onclose = function () { if (!over) showError("Rozłączono z serwerem."); };
    ws.onmessage = function (e) { handle(JSON.parse(e.data)); };
  }

  function showError(msg) { $("err").textContent = msg; $("err2").textContent = msg; }

  function handle(m) {
    switch (m.t) {
      case "error": showError(m.msg); break;
      case "joined":
        me = m.id; roomId = m.room; isHost = m.host;
        $("join").style.display = "none";
        $("lobby").style.display = "block";
        $("roomCode").textContent = m.room;
        break;
      case "lobby":
        isHost = m.host === me;
        var ul = $("plist"); ul.innerHTML = "";
        m.players.forEach(function (p) {
          var li = document.createElement("li");
          li.innerHTML = "<span>" + esc(p.name) + "</span>" +
            (p.id === m.host ? "<small>host</small>" : "");
          ul.appendChild(li);
        });
        $("btnStart").disabled = !isHost || m.players.length < 3;
        $("btnStart").textContent = isHost
          ? (m.players.length < 3 ? "Potrzeba min. 3 graczy" : "Start rundy")
          : "Czekaj na hosta";
        break;
      case "role":
        role = m.role; myCls = m.cls; myVision = m.vision; over = false;
        $("entry").style.display = "none";
        $("game").style.display = "block";
        $("banner").style.display = "none";
        var rp = $("pRole");
        rp.className = "pill" + (m.role === "mage" ? " role-mage" : "");
        rp.innerHTML = (m.role === "mage" ? "MAG" : "ŁOWCA") + " · <b>" + esc(m.cls) + "</b>";
        $("pPerk").textContent = m.perk;
        log(m.objective, m.role === "mage" ? "cast" : "start");
        renderKeys();
        break;
      case "state": state = m; break;
      case "event": log(m.ev.msg, m.ev.k); break;
      case "fx":
        fx.push({ def: FXDEF[m.spell] || FXDEF.fire, x: m.x, y: m.y, born: performance.now(), life: 1500 });
        break;
      case "windup":
        windups.push({ x: m.x, y: m.y, born: performance.now(), life: 1300 });
        break;
      case "shot":
        shots.push({ a: m.from, b: m.to, born: performance.now(), life: 260, ranged: m.ranged });
        break;
      case "stunned": toast("Ogłuszony!"); break;
      case "hurt": toast("Trafiony — pancerz wytrzymał."); break;
      case "died": toast("Zginąłeś. Obserwujesz."); break;
      case "revived": toast("Ustabilizowany."); break;
      case "camera": toast("Kamery aktywne."); break;
      case "toast": toast(m.msg); break;
      case "end": endRound(m); break;
    }
  }

  function endRound(m) {
    over = true;
    var win = (m.winner === "mage") === (role === "mage");
    var b = $("banner");
    b.style.display = "flex";
    b.querySelector(".inner").className = "inner " + (win ? "win" : "lose");
    $("bTitle").textContent = win ? "Wygrana" : "Porażka";
    $("bText").textContent = m.msg + (m.mage ? " Magiem był " + m.mage.name + "." : "");
    $("btnAgain").style.display = isHost ? "block" : "none";
  }

  // ----------------------------------------------------------------- input
  var HELD = { up: 0, down: 0, left: 0, right: 0 };
  document.addEventListener("keydown", function (e) {
    if (keys[e.code]) return;
    keys[e.code] = true;
    if (!ws || ws.readyState !== 1) return;
    if (e.code === "Space") { ws.send(JSON.stringify({ t: "taser" })); e.preventDefault(); }
    if (e.code === "KeyQ" && role === "mage") ws.send(JSON.stringify({ t: "cast" }));
    if (e.code === "KeyF" && role === "mage") ws.send(JSON.stringify({ t: "blend" }));
    if (e.code === "KeyC" && myCls === "Zwiadowca") ws.send(JSON.stringify({ t: "camera" }));
  });
  document.addEventListener("keyup", function (e) { keys[e.code] = false; });

  setInterval(function () {
    if (!ws || ws.readyState !== 1 || !role) return;
    var x = (keys.KeyD || keys.ArrowRight ? 1 : 0) - (keys.KeyA || keys.ArrowLeft ? 1 : 0);
    var y = (keys.KeyS || keys.ArrowDown ? 1 : 0) - (keys.KeyW || keys.ArrowUp ? 1 : 0);
    ws.send(JSON.stringify({ t: "input", x: x, y: y, hold: !!keys.KeyE }));
  }, 1000 / 20);

  // ---------------------------------------------------------------- render
  function draw() {
    requestAnimationFrame(draw);
    ctx.fillStyle = "#05070c";
    ctx.fillRect(0, 0, cv.width, cv.height);
    if (!state || !state.you) return;

    var camX = state.you.x * ZOOM - cv.width / 2;
    var camY = state.you.y * ZOOM - cv.height / 2;
    ctx.save();
    ctx.translate(-camX, -camY);

    drawStation();
    drawArtifacts();
    drawCorpses();
    drawPlayers();
    drawFx();
    ctx.restore();

    drawFog(camX, camY);
    drawHud();
  }

  function drawStation() {
    ctx.strokeStyle = "rgba(120,150,220,0.07)";
    ctx.lineWidth = 1;
    for (var gx = 0; gx <= WORLD_W; gx += 40) {
      ctx.beginPath(); ctx.moveTo(gx * ZOOM, 0); ctx.lineTo(gx * ZOOM, WORLD_H * ZOOM); ctx.stroke();
    }
    for (var gy = 0; gy <= WORLD_H; gy += 40) {
      ctx.beginPath(); ctx.moveTo(0, gy * ZOOM); ctx.lineTo(WORLD_W * ZOOM, gy * ZOOM); ctx.stroke();
    }
    COMPARTMENTS.forEach(function (c) {
      ctx.fillStyle = "rgba(24,32,52,0.75)";
      ctx.fillRect(c.x * ZOOM, c.y * ZOOM, c.w * ZOOM, c.h * ZOOM);
      ctx.strokeStyle = "rgba(120,150,220,0.28)";
      ctx.lineWidth = 2;
      ctx.strokeRect(c.x * ZOOM, c.y * ZOOM, c.w * ZOOM, c.h * ZOOM);
      ctx.fillStyle = "rgba(139,154,192,0.5)";
      ctx.font = "11px system-ui";
      ctx.fillText(c.name.toUpperCase(), c.x * ZOOM + 8, c.y * ZOOM + 18);
    });
  }

  function drawArtifacts() {
    (state.artifacts || []).forEach(function (a) {
      var x = a.x * ZOOM, y = a.y * ZOOM;
      var t = performance.now() / 400;
      if (a.done) {
        ctx.fillStyle = "rgba(124,232,168,0.5)";
        ctx.fillRect(x - 5, y - 5, 10, 10);
      } else {
        ctx.save();
        ctx.translate(x, y);
        ctx.rotate(t % (Math.PI * 2));
        ctx.fillStyle = "#c682ff";
        ctx.fillRect(-6, -6, 12, 12);
        ctx.restore();
        ctx.strokeStyle = "rgba(198,130,255," + (0.3 + 0.25 * Math.sin(t * 2)) + ")";
        ctx.lineWidth = 2;
        ctx.beginPath(); ctx.arc(x, y, 16, 0, Math.PI * 2); ctx.stroke();
      }
    });
  }

  function drawCorpses() {
    (state.corpses || []).forEach(function (c) {
      var row = CLASS_ORDER.indexOf(c.cls); if (row < 0) row = 0;
      ctx.save();
      ctx.globalAlpha = 0.75;
      ctx.translate(c.x * ZOOM, c.y * ZOOM);
      ctx.rotate(Math.PI / 2);
      ctx.drawImage(sheets.hunters, 0, (row * 4) * SPR, SPR, SPR,
        -SPR * ZOOM / 2, -SPR * ZOOM / 2, SPR * ZOOM, SPR * ZOOM);
      ctx.restore();
      ctx.fillStyle = "rgba(255,107,107,0.75)";
      ctx.font = "11px system-ui";
      ctx.fillText("✕ " + c.name, c.x * ZOOM - 16, c.y * ZOOM + 26);
    });
  }

  function drawPlayers() {
    (state.players || []).forEach(function (p) {
      var row = CLASS_ORDER.indexOf(p.cls); if (row < 0) row = 0;
      var sx = p.step * SPR, sy = (row * 4 + p.dir) * SPR;
      var x = p.x * ZOOM - SPR * ZOOM / 2, y = p.y * ZOOM - SPR * ZOOM;

      if (p.casting) {                       // the mage's tell, visible to all
        var pu = 0.5 + 0.5 * Math.sin(performance.now() / 90);
        ctx.strokeStyle = "rgba(198,130,255," + (0.4 + 0.5 * pu) + ")";
        ctx.lineWidth = 3;
        ctx.beginPath(); ctx.arc(p.x * ZOOM, p.y * ZOOM - 20, 30 + pu * 8, 0, Math.PI * 2); ctx.stroke();
      }
      if (p.stun) {
        ctx.strokeStyle = "rgba(255,195,92,0.85)"; ctx.lineWidth = 2;
        ctx.beginPath(); ctx.arc(p.x * ZOOM, p.y * ZOOM - 20, 26, 0, Math.PI * 2); ctx.stroke();
      }
      ctx.drawImage(sheets.hunters, sx, sy, SPR, SPR, x, y, SPR * ZOOM, SPR * ZOOM);

      ctx.font = "12px system-ui";
      ctx.textAlign = "center";
      ctx.fillStyle = p.me ? "#7fd8ff" : "rgba(230,236,250,0.82)";
      ctx.fillText(p.name, p.x * ZOOM, p.y * ZOOM - SPR * ZOOM - 4);
      ctx.textAlign = "left";
    });
  }

  function drawFx() {
    var t = performance.now();
    fx = fx.filter(function (f) { return t - f.born < f.life; });
    fx.forEach(function (f) {
      var d = f.def;
      var frame = Math.floor((t - f.born) / d.ms) % d.frames;
      ctx.drawImage(sheets[d.img], frame * d.w, 0, d.w, d.h,
        f.x * ZOOM - d.w * ZOOM / 2, f.y * ZOOM - d.h * ZOOM / 2, d.w * ZOOM, d.h * ZOOM);
    });

    windups = windups.filter(function (w) { return t - w.born < w.life; });
    windups.forEach(function (w) {
      var k = (t - w.born) / w.life;
      ctx.strokeStyle = "rgba(198,130,255," + (1 - k) + ")";
      ctx.lineWidth = 3;
      ctx.beginPath(); ctx.arc(w.x * ZOOM, w.y * ZOOM, 10 + k * 60, 0, Math.PI * 2); ctx.stroke();
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
  }

  function drawFog(camX, camY) {
    // Cosmetic only. The server has already withheld everything outside the
    // radius, so this is a vignette over missing data, not the security.
    if (state.you.seeAll) return;
    var cx = state.you.x * ZOOM - camX, cy = state.you.y * ZOOM - camY;
    var r = state.you.vision * ZOOM;
    // One gradient is enough: canvas extends a radial gradient's last stop
    // past its end radius, so everything beyond the vision circle is already
    // opaque. Adding a second fill with an anticlockwise arc on top fought
    // the gradient under nonzero winding and left a hard rectangular seam.
    var g = ctx.createRadialGradient(cx, cy, r * 0.62, cx, cy, r);
    g.addColorStop(0, "rgba(5,7,12,0)");
    g.addColorStop(1, "rgba(5,7,12,0.985)");
    ctx.fillStyle = g;
    ctx.fillRect(0, 0, cv.width, cv.height);
  }

  function drawHud() {
    $("pArt").textContent = (state.total - state.left) + "/" + state.total;
    $("pHunters").textContent = state.hunters;

    var y = state.you;
    if (y.ch > 0) {
      var labels = { extract: "Ekstrakcja", capture: "Wiązanie", revive: "Stabilizacja" };
      var w = 220, x0 = cv.width / 2 - w / 2, y0 = cv.height - 132;
      ctx.fillStyle = "rgba(10,14,24,0.9)";
      ctx.fillRect(x0, y0, w, 26);
      ctx.fillStyle = "#7fd8ff";
      ctx.fillRect(x0 + 3, y0 + 3, (w - 6) * y.ch, 20);
      ctx.fillStyle = "#05070c";
      ctx.font = "12px system-ui"; ctx.textAlign = "center";
      ctx.fillText(labels[y.chKind] || "", cv.width / 2, y0 + 18);
      ctx.textAlign = "left";
    }
    if (y.windup > 0) {
      ctx.fillStyle = "rgba(198,130,255,0.9)";
      ctx.font = "14px system-ui"; ctx.textAlign = "center";
      ctx.fillText("RZUCANIE… " + (y.windup / 1000).toFixed(1) + "s", cv.width / 2, 80);
      ctx.textAlign = "left";
    }
    renderKeys();
  }

  function renderKeys() {
    if (!state || !state.you) return;
    var y = state.you, out = [];
    out.push(k("WSAD", "ruch", 0));
    out.push(k("E", "przytrzymaj: artefakt / wiązanie", 0));
    out.push(k("SPACJA", myCls === "Strzelec" ? "karabin" : "tazer", y.taser));
    if (role === "mage") {
      out.push(k("Q", "zaklęcie", y.cast));
      out.push(k("F", "zmyłka", y.blend));
    }
    if (myCls === "Zwiadowca") out.push(k("C", "kamery", 0));
    $("keys").innerHTML = out.join("");
  }
  function k(key, label, cd) {
    return '<div class="key' + (cd > 0 ? " cd" : "") + '"><b>' + key + "</b> " + label +
      (cd > 0 ? " (" + (cd / 1000).toFixed(1) + "s)" : "") + "</div>";
  }

  // ------------------------------------------------------------------ misc
  function log(msg, kind) {
    var d = document.createElement("div");
    d.className = "lg " + (kind || "");
    d.textContent = msg;
    var l = $("log");
    l.insertBefore(d, l.firstChild);
    while (l.childNodes.length > 12) l.removeChild(l.lastChild);
  }
  var toastT = null;
  function toast(msg) {
    var el = $("toast");
    el.textContent = msg; el.style.opacity = 1;
    clearTimeout(toastT);
    toastT = setTimeout(function () { el.style.opacity = 0; }, 2200);
  }
  function esc(s) { return String(s).replace(/[<>&]/g, function (c) {
    return { "<": "&lt;", ">": "&gt;", "&": "&amp;" }[c]; }); }

  $("btnJoin").addEventListener("click", function () {
    var n = $("nick").value.trim();
    if (!n) { showError("Podaj imię."); return; }
    connect(n, $("rcode").value.trim().toUpperCase());
  });
  $("rcode").addEventListener("keydown", function (e) { if (e.key === "Enter") $("btnJoin").click(); });
  $("nick").addEventListener("keydown", function (e) { if (e.key === "Enter") $("btnJoin").click(); });
  $("btnStart").addEventListener("click", function () { ws.send(JSON.stringify({ t: "start" })); });
  $("btnAgain").addEventListener("click", function () { ws.send(JSON.stringify({ t: "start" })); });

  draw();
})();

"use strict";
/**
 * Packs the real game into one self-contained HTML file.
 *
 * An Artifact is a single page behind a strict CSP: no outbound sockets, no
 * external assets, no shared state. So rather than writing a second, weaker
 * copy of the game for the range, this bundles the shipped src/ modules
 * behind a tiny CommonJS shim, swaps the WebSocket for a local driver, and
 * inlines the sprite sheet. The rules you play against are the rules on the
 * server; only the transport and the opponents are fake.
 */

const fs = require("fs");
const path = require("path");

const ROOT = path.join(__dirname, "..");
const MODULES = [
  "rules", "classes", "spells", "map", "evidence", "round",
  "tribunal", "base", "room", "effects", "actions", "snapshot"
];

function readSrc(name) {
  return fs.readFileSync(path.join(ROOT, "src", name + ".js"), "utf8");
}

const modules = MODULES.map((name) =>
  `__def(${JSON.stringify(name)}, function (module, exports, require) {\n${readSrc(name)}\n});`
).join("\n");

const driver = `__def("driver", function (module, exports, require) {\n` +
  fs.readFileSync(path.join(ROOT, "sandbox", "driver.js"), "utf8") + `\n});`;

// every asset the client asks for, inlined: an Artifact may not fetch
const ASSET_FILES = {
  hunters: "hunters.png", tiles: "tiles.png", props: "props.png", propsFx: "props_fx.png",
  ogien: "fireball.png", powietrze: "lightning.png", woda: "sleep.png",
  ziemia: "fx_earth.png", mrok: "fx_dark.png", swiatlo: "fx_light.png"
};
const assets = {};
for (const [k, f] of Object.entries(ASSET_FILES)) {
  assets[k] = "data:image/png;base64," +
    fs.readFileSync(path.join(ROOT, "public", "assets", f)).toString("base64");
}

let client = fs.readFileSync(path.join(ROOT, "public", "client.js"), "utf8");

let html = fs.readFileSync(path.join(ROOT, "public", "index.html"), "utf8");

// ---------------------------------------------------------------- shim
const shim = `
<script>
window.__ASSETS = ${JSON.stringify(assets)};
(function () {
  "use strict";
  var reg = {}, cache = {};
  window.__def = function (name, fn) { reg[name] = fn; };
  function req(id) {
    var name = String(id).replace(/^\\.\\//, "");
    if (cache[name]) return cache[name].exports;
    if (!reg[name]) throw new Error("no module: " + name);
    var m = { exports: {} };
    cache[name] = m;
    reg[name](m, m.exports, req);
    return m.exports;
  }
  window.__require = req;
})();
</script>
<script>__MODULES__</script>
<script>__DRIVER__</script>
<script>
/* The client talks to a WebSocket. Here that socket is the game itself,
   running in the same page, so client.js needs no sandbox-specific branch. */
(function () {
  "use strict";
  window.WebSocket = function () {
    var self = this;
    self.readyState = 1;
    var drv = window.__require("./driver").makeDriver(function (m) {
      if (self.onmessage) self.onmessage({ data: JSON.stringify(m) });
    }, { name: "Ty", players: 6 });
    self.send = function (raw) { drv.handle(JSON.parse(raw)); };
    self.close = function () { self.readyState = 3; };
    setTimeout(function () { if (self.onopen) self.onopen(); }, 0);
  };
})();
</script>
`;

// ---------------------------------------------------------------- ui patch
const patch = `
<script>
/* Range-only chrome: pick which side you want to try, because a one-in-six
   roll would make "let me see how the mage plays" a chore. */
(function () {
  "use strict";
  var role = "random";
  var card = document.querySelector("#sLobby .card");
  var wrap = document.createElement("div");
  wrap.innerHTML =
    "<label>Kim chcesz zagrać</label><div class='row' id='asRow' style='margin-top:0'>" +
    "<button data-as='random' class='on'>Losowo</button>" +
    "<button data-as='hunter'>Łowca</button>" +
    "<button data-as='mage'>Mag</button></div>";
  card.insertBefore(wrap, document.getElementById("btnStart").parentNode);
  [].forEach.call(wrap.querySelectorAll("button"), function (b) {
    b.onclick = function () {
      role = b.dataset.as;
      [].forEach.call(wrap.querySelectorAll("button"), function (x) { x.classList.remove("on"); });
      b.classList.add("on");
    };
  });
  [].forEach.call(wrap.querySelectorAll("button"), function (b) {
    b.classList.toggle("on", b.dataset.as === "random");
  });

  var start = document.getElementById("btnStart");
  start.disabled = false;
  start.textContent = "Wejdź na wrak";
  start.onclick = function () {
    window.__sock.send(JSON.stringify({ t: "start", as: role === "random" ? null : role }));
  };

  document.getElementById("lobbyHint").innerHTML =
    "Poligon dla jednego gracza: pięcioro botów przeczesuje wrak razem z tobą. " +
    "Zasady, mapa, dowody i księga są te same co w grze sieciowej — " +
    "<b>brak tu tylko ludzi po drugiej stronie</b>, więc trybunał głosuje losowo.";
  document.querySelector("#sEntry .card .row button").textContent = "Wejdź";
  document.getElementById("nick").value = "Ty";
})();
</script>
`;

// client.js keeps its socket private, so expose it for the patched start button
client = client.replace("ws.onmessage = function (e)", "window.__sock = ws;\n    ws.onmessage = function (e)");

html = html
  .replace('<script src="client.js"></script>',
    shim.replace("__MODULES__", modules).replace("__DRIVER__", driver) +
    "<script>\n" + client + "\n</script>" + patch);

const out = path.join(ROOT, "sandbox", "sandbox.html");
fs.writeFileSync(out, html);
console.log("wrote", out, Math.round(fs.statSync(out).size / 1024) + " KB");

/**
 * The Artifact host supplies its own doctype, <head> and <body>, so the
 * published copy is the same page with that scaffolding removed. Everything
 * else -- styles, modules, sprite sheet -- stays inline, because the CSP
 * there refuses every external host.
 */
const artifact = html
  .replace(/^[\s\S]*?<head>/, "")
  .replace(/<link rel="icon"[^>]*>/, "")
  .replace("</head>", "")
  .replace(/<body>/, "")
  .replace(/<\/body>\s*<\/html>\s*$/, "");

const artOut = path.join(ROOT, "sandbox", "artifact.html");
fs.writeFileSync(artOut, artifact);
console.log("wrote", artOut, Math.round(fs.statSync(artOut).size / 1024) + " KB");

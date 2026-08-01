"""Assemble the standalone sandbox page with every sprite sheet inlined."""
import base64
import os

HERE = os.path.dirname(os.path.abspath(__file__))
EX = os.path.dirname(HERE)


def b64(p):
    with open(p, "rb") as f:
        return base64.b64encode(f.read()).decode("ascii")


ASSETS = {
    "hunters": os.path.join(HERE, "hunters.png"),
    "fireball": os.path.join(EX, "fireball-anim", "fireball_sheet.png"),
    "lightning": os.path.join(EX, "lightning-anim", "lightning_sheet.png"),
    "sleep": os.path.join(EX, "sleep-anim", "sleep_sheet.png"),
    "wizard": os.path.join(EX, "chunky-arcade", "wizard_32.png"),
}
IMGS = {k: b64(v) for k, v in ASSETS.items()}
JS = open(os.path.join(HERE, "sandbox.js"), encoding="utf-8").read()

HTML = """<!doctype html>
<html lang="pl">
<head>
<meta charset="utf-8" />
<title>I'm Not a Wizard, Harry — poligon</title>
<style>
  :root{
    --bg:#07090f; --panel:#111726; --panel2:#0c1120; --line:rgba(120,150,220,0.16);
    --ink:#e6ecfa; --dim:#8b9ac0; --accent:#7fd8ff; --mage:#c682ff;
  }
  *{box-sizing:border-box;}
  html,body{height:100%;margin:0;}
  body{
    background:radial-gradient(ellipse 90% 60% at 50% 0%, #0f1524, #05070c);
    color:var(--ink); font-family:-apple-system,"Segoe UI",system-ui,sans-serif;
    overflow:hidden;
  }

  /* ------------- class picker ------------- */
  #picker{
    position:absolute; inset:0; display:flex; flex-direction:column;
    align-items:center; justify-content:center; gap:22px; padding:24px; overflow-y:auto;
  }
  #picker h1{ font-size:clamp(20px,3vw,27px); margin:0; text-align:center; }
  #picker .sub{ color:var(--dim); font-size:14px; max-width:66ch; text-align:center;
    line-height:1.6; margin:0; }
  #cards{ display:grid; grid-template-columns:repeat(auto-fit,minmax(168px,1fr));
    gap:12px; width:100%; max-width:880px; }
  .pick{
    background:var(--panel); border:1px solid var(--line); border-radius:14px;
    padding:16px 12px; display:flex; flex-direction:column; align-items:center; gap:8px;
    cursor:pointer; color:inherit; font:inherit; text-align:center;
  }
  .pick:hover{ border-color:var(--accent); }
  .pick.mage{ border-color:rgba(198,130,255,0.42); }
  .pick.mage:hover{ border-color:var(--mage); }
  .pick canvas{ image-rendering:pixelated; }
  .pick strong{ font-size:14.5px; }
  .pick.mage strong{ color:var(--mage); }
  .pick small{ font-size:11.5px; color:var(--dim); line-height:1.45; }

  /* ------------- stage ------------- */
  #stage{ display:none; position:absolute; inset:0; }
  #cv{ display:block; width:100%; height:100%; image-rendering:pixelated; cursor:none; }
  .hud{ position:absolute; pointer-events:none; }
  #top{ top:0; left:0; right:0; display:flex; gap:8px; padding:10px; flex-wrap:wrap; }
  .pill{ background:rgba(10,14,24,0.88); border:1px solid var(--line); border-radius:9px;
    padding:6px 12px; font-size:12.5px; color:var(--dim); }
  .pill b{ color:var(--ink); font-variant-numeric:tabular-nums; }
  .pill.mage{ border-color:rgba(198,130,255,0.45); color:var(--mage); }
  .pill.mage b{ color:var(--mage); }
  #keys{ position:absolute; left:10px; bottom:10px; display:flex; gap:6px; flex-wrap:wrap;
    max-width:calc(100% - 20px); }
  .key{ background:rgba(10,14,24,0.88); border:1px solid var(--line); border-radius:8px;
    padding:6px 10px; font-size:11.5px; color:var(--dim); }
  .key b{ color:var(--ink); }
  .key.cd{ opacity:0.42; }
  #toast{ position:absolute; top:56px; left:50%; transform:translateX(-50%);
    background:rgba(10,14,24,0.92); border:1px solid var(--line); border-radius:10px;
    padding:8px 16px; font-size:13px; opacity:0; transition:opacity .25s; }
  #btnQuit{ position:absolute; top:10px; right:10px; pointer-events:auto;
    background:rgba(10,14,24,0.88); border:1px solid var(--line); color:var(--dim);
    font:inherit; font-size:12.5px; padding:6px 14px; border-radius:9px; cursor:pointer; }
  #btnQuit:hover{ border-color:var(--accent); color:var(--accent); }
</style>
</head>
<body>

<div id="picker">
  <h1>Wybierz klasę i przejdź się po wraku</h1>
  <p class="sub">Poligon, nie rozgrywka: manekiny chodzą, artefakty czekają, nikt cię nie ściga.
    Zagraj łowcą, żeby poczuć zasięg wzroku i tazera, albo <b>Magiem</b> — celuj myszą,
    <b>LPM</b> rzuca fireballa jako lecący pocisk, <b>PPM</b> wali piorunem, który ogłusza
    wszystkich w promieniu, <b>F</b> zmienia twój wygląd na najbliższą postać.</p>
  <div id="cards"></div>
</div>

<div id="stage">
  <canvas id="cv"></canvas>
  <div class="hud" id="top">
    <div class="pill" id="hRole">—</div>
    <div class="pill" id="hPerk">—</div>
    <div class="pill">Artefakty: <b id="hArt">0/0</b></div>
    <div class="pill">Żywi: <b id="hAlive">0</b></div>
  </div>
  <button id="btnQuit">← Klasy</button>
  <div id="keys"></div>
  <div id="toast"></div>
</div>

<script>
__JS__
</script>
<script>
(function () {
  var SRC = __SRC__;
  var loaded = 0, sheets = {}, keys = Object.keys(SRC);
  keys.forEach(function (k) {
    var img = new Image();
    img.onload = function () { if (++loaded === keys.length) window.__boot(sheets); };
    img.src = "data:image/png;base64," + SRC[k];
    sheets[k] = img;
  });
})();
</script>
</body>
</html>
"""

import json
out = HTML.replace("__JS__", JS).replace("__SRC__", json.dumps(IMGS))
path = os.path.join(HERE, "sandbox.html")
with open(path, "w", encoding="utf-8") as f:
    f.write(out)
print("wrote", path, os.path.getsize(path) // 1024, "KB")

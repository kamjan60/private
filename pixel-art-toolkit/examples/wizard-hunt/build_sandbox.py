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
<meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=1, user-scalable=no, viewport-fit=cover" />
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
    /* stop the browser hijacking drags as scroll / pull-to-refresh, and kill
       the tap highlight so buttons do not flash blue on every press */
    touch-action:none; overscroll-behavior:none;
    -webkit-user-select:none; user-select:none;
    -webkit-tap-highlight-color:transparent;
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

  /* ------------- touch controls ------------- */
  #touch{ display:none; }
  body.touch #touch{ display:block; }
  body.touch #cv{ cursor:default; }
  .tbtn{
    position:absolute; pointer-events:auto; display:flex; align-items:center;
    justify-content:center; text-align:center;
    background:rgba(16,22,38,0.9); border:1px solid rgba(120,150,220,0.3);
    color:var(--ink); border-radius:50%; font-size:11px; font-weight:600;
    letter-spacing:0.04em; padding:6px;
  }
  .tbtn span{ pointer-events:none; }
  .tbtn.on{ background:rgba(127,216,255,0.28); border-color:var(--accent); }
  .tbtn.cd{ opacity:0.4; }
  #tHold{ right:calc(16px + env(safe-area-inset-right));
    bottom:calc(140px + env(safe-area-inset-bottom)); width:92px; height:92px;
    border-color:rgba(127,216,255,0.45); font-size:10px; }
  #tA{ right:calc(118px + env(safe-area-inset-right));
    bottom:calc(96px + env(safe-area-inset-bottom)); width:80px; height:80px; }
  #tB{ right:calc(22px + env(safe-area-inset-right));
    bottom:calc(38px + env(safe-area-inset-bottom)); width:80px; height:80px; }

  /* keep the HUD legible on a handset: hints move above the buttons and the
     top pills wrap instead of pushing off-screen */
  body.touch #keys{ bottom:calc(12px + env(safe-area-inset-bottom)); max-width:50%; }
  body.touch #top{ padding-top:calc(10px + env(safe-area-inset-top)); padding-right:86px; }
  @media (max-width:560px){
    .pill{ font-size:11px; padding:5px 9px; }
    /* the perk already reads on the class card; on a handset it only
       collides with the back button */
    #hPerk{ display:none; }
    #picker{ gap:16px; padding:18px 14px 34px; justify-content:flex-start; padding-top:34px; }
    #cards{ grid-template-columns:repeat(2,1fr); gap:10px; }
    .pick{ padding:12px 8px; }
    .pick canvas{ width:64px; height:64px; }
    .pick strong{ font-size:13px; }
    .pick small{ font-size:10.5px; }
    #btnQuit{ top:calc(10px + env(safe-area-inset-top)); }
  }
</style>
</head>
<body>

<div id="picker">
  <h1>Wybierz klasę i przejdź się po wraku</h1>
  <p class="sub">Poligon, nie rozgrywka: manekiny chodzą, artefakty czekają, nikt cię nie ściga.
    Zagraj łowcą, żeby poczuć zasięg wzroku i tazera, albo <b>Magiem</b>.</p>
  <p class="sub" id="howto"></p>
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
  <div id="touch">
    <button class="tbtn" id="tHold"><span>TRZYMAJ</span></button>
    <button class="tbtn" id="tA"><span>TAZER</span></button>
    <button class="tbtn" id="tB"><span>KAMERY</span></button>
  </div>
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

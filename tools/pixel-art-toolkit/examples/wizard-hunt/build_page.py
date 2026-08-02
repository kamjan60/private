"""Assemble the standalone game page: inline every sprite sheet as a data
URI plus the game script, so the artifact has no external requests."""
import base64
import os

HERE = os.path.dirname(os.path.abspath(__file__))
EX = os.path.dirname(HERE)


def b64(path):
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode("ascii")


MARINES = b64(os.path.join(HERE, "marines.png"))
FIRE    = b64(os.path.join(EX, "fireball-anim", "fireball_sheet.png"))
BOLT    = b64(os.path.join(EX, "lightning-anim", "lightning_sheet.png"))
SLEEP   = b64(os.path.join(EX, "sleep-anim", "sleep_sheet.png"))
WIZ     = b64(os.path.join(EX, "chunky-arcade", "wizard_32.png"))
GAME_JS = open(os.path.join(HERE, "game.js"), encoding="utf-8").read()

Z = 2   # must match game.js

HTML = """<!doctype html>
<html lang="pl">
<head>
<meta charset="utf-8" />
<title>I'm Not a Wizard, Harry</title>
<style>
  :root{
    --bg:#0b0e18; --bg2:#060811; --panel:#141a2b; --panel2:#0f1422;
    --line:rgba(120,150,220,0.16); --ink:#e6ecfa; --ink-dim:#8b9ac0;
    --accent:#7fd8ff; --warn:#ffc35c; --bad:#ff6b6b; --good:#7ce8a8;
  }
  *{box-sizing:border-box;}
  body{
    margin:0; min-height:100vh; background:radial-gradient(ellipse 90% 60% at 50% 0%, var(--bg2), var(--bg));
    color:var(--ink); font-family:-apple-system,"Segoe UI",system-ui,sans-serif;
    display:flex; justify-content:center; padding:clamp(16px,3vw,36px);
  }
  .wrap{ width:100%; max-width:1000px; display:flex; flex-direction:column; gap:18px; }

  header h1{ font-size:clamp(20px,3vw,27px); margin:0 0 5px; letter-spacing:-0.01em; }
  header p{ margin:0; color:var(--ink-dim); font-size:14px; line-height:1.55; max-width:74ch; }

  .hud{ display:flex; gap:10px; flex-wrap:wrap; align-items:center; }
  .stat{ background:var(--panel); border:1px solid var(--line); border-radius:10px;
    padding:7px 13px; font-size:12.5px; color:var(--ink-dim); }
  .stat b{ color:var(--ink); font-variant-numeric:tabular-nums; font-size:14px; }
  .status{ flex:1; min-width:200px; font-size:13.5px; padding:7px 13px;
    border-radius:10px; background:var(--panel); border:1px solid var(--line); }
  .status.warn{ color:var(--warn); border-color:rgba(255,195,92,0.4); }
  .status.win{ color:var(--good); border-color:rgba(124,232,168,0.45); }
  .status.lose{ color:var(--bad); border-color:rgba(255,107,107,0.45); }
  button.ghost{ background:var(--panel); border:1px solid var(--line); color:var(--ink);
    font:inherit; font-size:13px; padding:8px 16px; border-radius:10px; cursor:pointer; }
  button.ghost:hover{ border-color:var(--accent); color:var(--accent); }

  .board{ display:grid; grid-template-columns:1fr 268px; gap:16px; }
  @media (max-width:880px){ .board{ grid-template-columns:1fr; } }

  #arena{
    position:relative; width:620px; height:380px; max-width:100%;
    background:
      linear-gradient(rgba(120,150,220,0.05) 1px, transparent 1px) 0 0/31px 31px,
      linear-gradient(90deg, rgba(120,150,220,0.05) 1px, transparent 1px) 0 0/31px 31px,
      radial-gradient(ellipse 70% 60% at 50% 45%, #1a2136, #0a0d16);
    border:1px solid var(--line); border-radius:14px; overflow:hidden;
  }

  .marine{
    position:absolute; left:0; top:0;
    background-image:url("data:image/png;base64,__MARINES__");
    background-size:__MW__px __MH__px;
    image-rendering:pixelated; cursor:pointer;
  }
  .marine:hover{ filter:brightness(1.35) drop-shadow(0 0 6px var(--accent)); }
  .marine.down{ filter:grayscale(1) brightness(0.45); cursor:default; transform-origin:50% 100%; }
  .marine.revealed{ filter:drop-shadow(0 0 9px #b06cff) brightness(1.2); }

  /* FX strips. Offsets are pixels, one container width per frame -
     percentages in background-position resolve against
     (container - image) width and scatter the frames. */
  .fx{ position:absolute; left:0; top:0; image-rendering:pixelated;
       background-repeat:no-repeat; pointer-events:none; }
  .fx-fire{ background-image:url("data:image/png;base64,__FIRE__");
    background-size:__FIREW__px __FIREH__px; animation:aFire .48s steps(1) infinite; }
  .fx-bolt{ background-image:url("data:image/png;base64,__BOLT__");
    background-size:__BOLTW__px __BOLTH__px; animation:aBolt .56s steps(1) infinite; }
  .fx-sleep{ background-image:url("data:image/png;base64,__SLEEP__");
    background-size:__SLEEPW__px __SLEEPH__px; animation:aSleep 1.6s steps(1) infinite; }

  @keyframes aFire{
    0%{background-position-x:0;} 16.6%{background-position-x:-64px;}
    33.3%{background-position-x:-128px;} 50%{background-position-x:-192px;}
    66.6%{background-position-x:-256px;} 83.3%{background-position-x:-320px;} }
  @keyframes aBolt{
    0%{background-position-x:0;} 12.5%{background-position-x:-128px;}
    25%{background-position-x:-256px;} 37.5%{background-position-x:-384px;}
    50%{background-position-x:-512px;} 62.5%{background-position-x:-640px;}
    75%{background-position-x:-768px;} 87.5%{background-position-x:-896px;} }
  @keyframes aSleep{
    0%{background-position-x:0;} 12.5%{background-position-x:-80px;}
    25%{background-position-x:-160px;} 37.5%{background-position-x:-240px;}
    50%{background-position-x:-320px;} 62.5%{background-position-x:-400px;}
    75%{background-position-x:-480px;} 87.5%{background-position-x:-560px;} }

  /* the detection radius, shown for as long as the FX plays */
  .bloom{ position:absolute; left:0; top:0; border-radius:50%; pointer-events:none;
    background:radial-gradient(circle, rgba(127,216,255,0.16), rgba(127,216,255,0.05) 60%, transparent 72%);
    border:1px solid rgba(127,216,255,0.22); animation:bloomIn 1.5s ease-out forwards; }
  @keyframes bloomIn{ from{opacity:0; transform-origin:center; } 15%{opacity:1;} to{opacity:0;} }

  .side{ display:flex; flex-direction:column; gap:14px; min-width:0; }
  .card{ background:var(--panel); border:1px solid var(--line); border-radius:14px; padding:14px; }
  .card h2{ font-size:11px; letter-spacing:0.1em; text-transform:uppercase;
    color:var(--accent); margin:0 0 11px; font-weight:600; }

  .suspect{ display:flex; align-items:center; gap:10px; width:100%; text-align:left;
    background:var(--panel2); border:1px solid var(--line); border-radius:10px;
    padding:7px 9px; margin-bottom:7px; cursor:pointer; color:inherit; font:inherit; }
  .suspect:hover:not(:disabled){ border-color:var(--bad); }
  .suspect:disabled{ opacity:0.42; cursor:default; }
  .suspect.dead strong{ text-decoration:line-through; }
  .chip{ width:36px; height:48px; flex:none; image-rendering:pixelated;
    background-image:url("data:image/png;base64,__MARINES__");
    background-size:__CW__px __CH__px; background-repeat:no-repeat; }
  .s-body{ flex:1; min-width:0; display:flex; flex-direction:column; gap:3px; }
  .s-body strong{ font-size:13px; }
  .s-body small{ font-size:11px; color:var(--ink-dim); }
  .bar{ display:block; height:4px; border-radius:2px; background:rgba(255,255,255,0.08); overflow:hidden; }
  .bar i{ display:block; height:100%; background:var(--ink-dim); transition:width .3s; }
  .bar i.hot{ background:var(--bad); }
  .bar i.cold{ background:var(--good); }

  #log{ max-height:210px; overflow-y:auto; display:flex; flex-direction:column; gap:5px;
    font-size:11.5px; line-height:1.45; }
  .log-line{ color:var(--ink-dim); border-left:2px solid var(--line); padding-left:8px; }
  .log-line.cast{ color:var(--accent); border-color:var(--accent); }
  .log-line.bad{ color:var(--bad); border-color:var(--bad); }
  .log-line.good{ color:var(--good); border-color:var(--good); }

  .how{ font-size:12.5px; color:var(--ink-dim); line-height:1.6; }
  .how b{ color:var(--ink); }
  .how img{ image-rendering:pixelated; width:48px; height:48px; float:right; margin-left:10px; }

  @media (prefers-reduced-motion: reduce){ .fx, .bloom{ animation:none; } }
</style>
</head>
<body>
<div class="wrap">
  <header>
    <h1>I'm Not a Wizard, Harry</h1>
    <p>Sześciu kosmicznych marines na pokładzie. Jeden z nich jest magiem — udaje swojego, rzuca zaklęcia i po kolei zabija łowców. Każde zaklęcie zostawia ślad: tylko marines w zasięgu rozbłysku mogli je rzucić. Mag zawsze jest w tym zbiorze. Przecinaj zbiory i wskaż go, zanim zostanie was dwóch.</p>
  </header>

  <div class="hud">
    <div class="stat">Oskarżenia: <b id="accusations">2</b></div>
    <div class="stat">Zaklęcia: <b id="castcount">0</b></div>
    <div class="status" id="status">Namierz maga.</div>
    <button class="ghost" id="restart">Nowa gra</button>
  </div>

  <div class="board">
    <div id="arena"></div>
    <div class="side">
      <div class="card">
        <h2>Podejrzani</h2>
        <div id="roster"></div>
      </div>
      <div class="card">
        <h2>Jak grać</h2>
        <p class="how">
          <img src="data:image/png;base64,__WIZ__" alt="mag" />
          Kliknij marine — w arenie lub na liście — żeby go oskarżyć.<br><br>
          Pasek pokazuje, przy ilu zaklęciach był w zasięgu. <b>Pełny pasek</b> = był przy każdym, główny trop. <b>Pusty</b> = ma alibi na wszystko, jest niewinny.<br><br>
          Masz <b>2 oskarżenia</b>. Pomyłka zabija niewinnego.
        </p>
      </div>
      <div class="card">
        <h2>Dziennik</h2>
        <div id="log"></div>
      </div>
    </div>
  </div>
</div>
<script>
__GAME__
</script>
</body>
</html>
"""

repl = {
    "__MARINES__": MARINES,
    "__FIRE__": FIRE,
    "__BOLT__": BOLT,
    "__SLEEP__": SLEEP,
    "__WIZ__": WIZ,
    "__GAME__": GAME_JS,
    # marine sheet is 64 x 768 logical
    "__MW__": str(64 * Z), "__MH__": str(768 * Z),
    # roster chip renders the sheet at 1.5x
    "__CW__": str(int(64 * 1.5)), "__CH__": str(int(768 * 1.5)),
    "__FIREW__": str(192 * Z), "__FIREH__": str(32 * Z),
    "__BOLTW__": str(512 * Z), "__BOLTH__": str(32 * Z),
    "__SLEEPW__": str(320 * Z), "__SLEEPH__": str(48 * Z),
}
out = HTML
for k, v in repl.items():
    out = out.replace(k, v)

path = os.path.join(HERE, "index.html")
with open(path, "w", encoding="utf-8") as f:
    f.write(out)
print("wrote", path, os.path.getsize(path) // 1024, "KB")

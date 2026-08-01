"use strict";
/**
 * The eight hunter classes and the three loadout items each of them picks
 * from before the round.
 *
 * ORDER MATTERS. The client indexes sprite-sheet rows by a class's position
 * in CLASS_NAMES, so reordering this object silently hands every player
 * somebody else's body. The generator that draws the sheet
 * (pixel-art-toolkit/examples/wizard-hunt/make_hunters.py) carries the same
 * list and has to be edited in step.
 *
 * Classes are unique within a round, which is why the table has exactly
 * MAX_PLAYERS entries. A transit log entry naming a class therefore names a
 * person -- but it names them as *present*, not as guilty, and the mage can
 * write somebody else's class into it. See the spec, section 5.
 */

/**
 * Item shapes:
 *   kind "passive"   always on; `mods` is merged into the player's stats
 *   kind "cooldown"  fires by itself when its condition is met, then rests
 *   kind "active"    the player spends a charge on purpose
 */
const CLASSES = {
  "Strażnik": {
    vision: 210, taser: 62, hp: 2, speed: 0.86, glow: "#c4d2e8",
    blurb: "Znosi trafienie, którego nikt inny by nie zniósł.",
    items: [
      { id: "tarcza", name: "Tarcza szturmowa", kind: "cooldown", cooldown: 20000,
        desc: "Blokuje jedno zaklęcie od przodu, potem stygnie." },
      { id: "kamizelki", name: "Plecak z kamizelkami", kind: "active", charges: 3,
        desc: "Trzy kamizelki do rozdania. Każda zjada jedno trafienie." },
      { id: "kotwica", name: "Kotwica", kind: "active", charges: 2, durationMs: 20000,
        desc: "Barykada w przejściu na 20 s." }
    ]
  },
  "Zwiadowca": {
    vision: 330, taser: 58, hp: 1, speed: 1.14, glow: "#8cf096",
    blurb: "Widzi najdalej i jako jedyny może zajrzeć tam, gdzie go nie ma.",
    items: [
      { id: "dron", name: "Dron", kind: "active", charges: 3, durationMs: 6000,
        desc: "Odsłania wskazany przedział na 6 s." },
      { id: "czujnik", name: "Czujnik ruchu", kind: "active", charges: 2,
        desc: "Stawiasz czujnik. Pinguje wejścia klasą, nie imieniem." },
      { id: "optyka", name: "Optyka", kind: "passive", mods: { vision: 70 },
        desc: "Wzrok +70 na stałe." }
    ]
  },
  "Strzelec": {
    vision: 250, taser: 58, hp: 1, speed: 1.0, glow: "#78d0ff",
    blurb: "Jedyny, kto ogłuszy z drugiego końca przedziału.",
    items: [
      { id: "karabin", name: "Karabin", kind: "active", charges: 3, range: 330,
        desc: "Ogłuszenie z 330 px." },
      { id: "siatka", name: "Siatka", kind: "active", charges: 2, radius: 90,
        durationMs: 8000, desc: "Spowolnienie 60% w promieniu 90 na 8 s." },
      { id: "znacznik", name: "Znacznik", kind: "active", charges: 3, durationMs: 20000,
        desc: "Znacznik nad celem, widoczny dla wszystkich przez 20 s." }
    ]
  },
  "Inkwizytor": {
    vision: 240, taser: 70, hp: 1, speed: 1.0, glow: "#ffa848",
    blurb: "Czyta trupy i wiąże szybciej, niż ktokolwiek zdąży zaprotestować.",
    items: [
      { id: "kadzidlo", name: "Kadzidło", kind: "passive", mods: { traceMs: 3 },
        desc: "Ślad ze zwłok czytelny trzy razy dłużej." },
      { id: "kajdany", name: "Kajdany", kind: "passive", mods: { bindFast: true },
        desc: "Wiązanie o połowę szybsze." },
      { id: "wykrywacz", name: "Wykrywacz", kind: "passive", mods: { residueAct: true },
        desc: "Pokazuje, czy w przedziale rzucano w tym akcie." }
    ]
  },
  "Chirurg": {
    vision: 230, taser: 58, hp: 1, speed: 0.98, glow: "#d8e878",
    blurb: "Raz na rundę odwraca to, co mag uznał za załatwione.",
    items: [
      // spent by holding over a body, not by a button: reviving is a
      // channel that breaks on movement, like every other commitment
      { id: "stabilizator", name: "Stabilizator", kind: "active", charges: 1,
        viaChannel: true, desc: "Podnosi jednego rannego łowcę." },
      { id: "stymulanty", name: "Stymulanty", kind: "active", charges: 2, durationMs: 10000,
        desc: "+40% prędkości i −50% ogłuszenia na 10 s." },
      { id: "autopsja", name: "Autopsja", kind: "passive", mods: { exactTime: true },
        desc: "Ze zwłok czyta dokładny czas zgonu." }
    ]
  },
  "Runarz": {
    vision: 235, taser: 58, hp: 1, speed: 0.96, glow: "#c682ff",
    blurb: "Wynosi artefakty szybciej, niż mag zdąży ich bronić.",
    items: [
      { id: "ekstraktor", name: "Ekstraktor", kind: "passive", mods: { extractFast: true },
        desc: "Ekstrakcja dwa razy szybsza." },
      { id: "pieczec", name: "Pieczęć", kind: "active", charges: 3,
        desc: "Artefakt odporny na Pożogę i Zawał. Nadal trzeba go wyciągnąć." },
      { id: "zaklocacz", name: "Zakłócacz", kind: "active", charges: 2, durationMs: 15000,
        desc: "Blokuje rzucanie w przedziale na 15 s." }
    ]
  },
  "Archiwista": {
    vision: 225, taser: 58, hp: 1, speed: 0.94, glow: "#9fb4d8",
    blurb: "Czyta rejestry, których nikt inny nie otworzy bez artefaktu.",
    items: [
      { id: "czytnik", name: "Czytnik", kind: "passive", mods: { readLogs: true },
        desc: "Czyta rejestr przedziału bez wyciągania artefaktu." },
      { id: "kopia", name: "Kopia", kind: "active", charges: 2,
        desc: "Zapisuje jeden rejestr tak, że przeżyje zmianę aktu." },
      { id: "filtr", name: "Filtr", kind: "passive", mods: { filterLogs: true },
        desc: "Rejestr z ostatnich 60 s, ale odporny na Wymazanie." }
    ]
  },
  "Technik": {
    vision: 245, taser: 58, hp: 1, speed: 1.02, glow: "#ffd27a",
    blurb: "Zapala światło tam, gdzie mag właśnie je zgasił.",
    items: [
      { id: "generator", name: "Generator", kind: "active", charges: 3, durationMs: 30000,
        desc: "Pełne światło w przedziale na 30 s." },
      { id: "kamera", name: "Kamera polowa", kind: "active", charges: 2,
        desc: "Stawia kamerę, którą widzi baza." },
      { id: "rygiel", name: "Rygiel", kind: "active", charges: 3, durationMs: 20000,
        desc: "Zamyka drzwi przedziału na 20 s." }
    ]
  }
};

const CLASS_NAMES = Object.keys(CLASSES);

/** Row index in the sprite sheet. Kept as a function so callers cannot
 *  accidentally rely on a stale copy of the order. */
function classRow(name) {
  const i = CLASS_NAMES.indexOf(name);
  if (i < 0) throw new Error(`unknown class: ${name}`);
  return i;
}

function itemsOf(className) {
  const c = CLASSES[className];
  if (!c) throw new Error(`unknown class: ${className}`);
  return c.items;
}

function findItem(className, itemId) {
  return itemsOf(className).find((it) => it.id === itemId) || null;
}

/**
 * Deal one unique class to each player. Fewer than eight players means some
 * classes simply do not appear -- and their absence is itself information a
 * careful hunter can use, which is intended.
 */
function dealClasses(count, rand = Math.random) {
  if (count > CLASS_NAMES.length) {
    throw new Error(`${count} players but only ${CLASS_NAMES.length} classes`);
  }
  const pool = CLASS_NAMES.slice();
  for (let i = pool.length - 1; i > 0; i--) {
    const j = Math.floor(rand() * (i + 1));
    [pool[i], pool[j]] = [pool[j], pool[i]];
  }
  return pool.slice(0, count);
}

/** Stats after the chosen item's passive modifiers are folded in. */
function statsFor(className, itemId) {
  const c = CLASSES[className];
  const it = itemId ? findItem(className, itemId) : null;
  const mods = (it && it.kind === "passive" && it.mods) || {};
  return {
    vision: c.vision + (mods.vision || 0),
    taser: c.taser,
    hp: c.hp,
    speed: c.speed,
    glow: c.glow,
    bindFast: !!mods.bindFast,
    extractFast: !!mods.extractFast,
    exactTime: !!mods.exactTime,
    readLogs: !!mods.readLogs,
    filterLogs: !!mods.filterLogs,
    residueAct: !!mods.residueAct,
    traceMult: mods.traceMs || 1
  };
}

module.exports = {
  CLASSES, CLASS_NAMES, classRow, itemsOf, findItem, dealClasses, statsFor
};

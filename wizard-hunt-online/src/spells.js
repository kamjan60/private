"use strict";
/**
 * The book: twenty-four spells across six schools.
 *
 * A spell is data, not code. Adding one is a row in this table plus a case
 * in the effect dispatcher -- that is the whole point of the shape, because
 * the design wants the book to keep growing without the rules growing with it.
 *
 * The mage fills BOOK_SLOTS (10) slots from this table. Duplicates are
 * allowed and stack their charges, so ten slots buy either a narrow, deep
 * kit or a wide, shallow one.
 *
 * Charges are the spine of the evidence game. The mage cannot change style
 * mid-round because he took what he took, and every corpse carries the
 * school that killed it -- so his loadout leaves a signature.
 *
 *   target "point"        aimed with the cursor or a tap, within `range`
 *   target "actor"        nearest valid player within `range`
 *   target "self"         no aim
 *   target "compartment"  the compartment the mage is standing in
 *
 * `castMs` is the wind-up. Throughout it the mage blooms an effect visible
 * to anyone with line of sight, and a taser landing during it interrupts the
 * cast AND eats the charge. Without that tell the mage is unbeatable; with
 * it, being seen is the risk he manages.
 */

const SCHOOLS = {
  ogien:     { name: "Ogień",     colour: "#ff7a3c", job: "obrażenia, pociski" },
  woda:      { name: "Woda",      colour: "#4fc3f7", job: "spowolnienie, otępienie, sen" },
  powietrze: { name: "Powietrze", colour: "#c9e8ff", job: "podmuch, przeskok, burza" },
  ziemia:    { name: "Ziemia",    colour: "#b08050", job: "ściany, ryglowanie, wstrząs" },
  mrok:      { name: "Mrok",      colour: "#6b4b8a", job: "gaszenie świateł, ukrycie, psucie śladów" },
  swiatlo:   { name: "Światło",   colour: "#ffe9a8", job: "przebranie, sobowtór, kłamstwo o tożsamości" }
};

const SPELLS = [
  // ------------------------------------------------------------- ogień
  { id: "kula_ognia", name: "Kula ognia", school: "ogien", charges: 3, castMs: 900,
    target: "point", effect: "projectile", lethal: true,
    desc: "Pocisk. Leci, dopóki nie trafi albo nie zgaśnie." },
  { id: "pochodnia", name: "Pochodnia", school: "ogien", charges: 2, castMs: 600,
    target: "point", range: 120, effect: "cone", lethal: true,
    desc: "Stożek ognia na 120 px. Zabija." },
  { id: "zaplon", name: "Zapłon", school: "ogien", charges: 2, castMs: 700,
    target: "point", delayMs: 3000, radius: 80, effect: "delayed_blast", lethal: true,
    desc: "Znacznik w miejscu. Po 3 s wybucha i zabija w promieniu 80." },
  { id: "pozoga", name: "Pożoga", school: "ogien", charges: 1, castMs: 1400,
    target: "compartment", effect: "burn_artifact",
    desc: "Niszczy artefakt w przedziale. Artefakt przepada." },

  // ------------------------------------------------------------- woda
  { id: "sen", name: "Sen", school: "woda", charges: 2, castMs: 1000,
    target: "actor", durationMs: 4000, effect: "sleep",
    desc: "Cel zasypia na 4 s." },
  { id: "topiel", name: "Topiel", school: "woda", charges: 2, castMs: 800,
    target: "point", radius: 140, durationMs: 6000, slow: 0.6, effect: "slow_area",
    desc: "Spowolnienie 60% w promieniu 140 na 6 s." },
  { id: "cisza", name: "Cisza", school: "woda", charges: 2, castMs: 700,
    target: "actor", durationMs: 8000, effect: "silence",
    desc: "Cel przez 8 s nie pinguje i nie kanałuje." },
  { id: "zimna_krew", name: "Zimna krew", school: "woda", charges: 1, castMs: 800,
    target: "self", effect: "stun_immunity",
    desc: "Mag ignoruje najbliższe ogłuszenie tazerem." },

  // ------------------------------------------------------------- powietrze
  { id: "lancuch", name: "Łańcuch błyskawic", school: "powietrze", charges: 2, castMs: 1000,
    target: "actor", jumps: 3, durationMs: 2500, effect: "chain_stun",
    desc: "Ogłuszenie 2.5 s, przeskakuje do trzech celów." },
  { id: "podmuch", name: "Podmuch", school: "powietrze", charges: 3, castMs: 500,
    target: "actor", push: 200, effect: "shove",
    desc: "Odrzuca cel o 200 px." },
  { id: "ped", name: "Pęd", school: "powietrze", charges: 3, castMs: 400,
    target: "self", durationMs: 5000, speed: 1.8, effect: "haste",
    desc: "Mag +80% prędkości na 5 s." },
  { id: "burza", name: "Burza", school: "powietrze", charges: 2, castMs: 1100,
    target: "point", radius: 130, durationMs: 3200, effect: "stun_area",
    desc: "Ogłuszenie 3.2 s w promieniu 130." },

  // ------------------------------------------------------------- ziemia
  { id: "mur", name: "Mur", school: "ziemia", charges: 3, castMs: 800,
    target: "point", durationMs: 25000, effect: "wall",
    desc: "Ściana w przejściu na 25 s." },
  { id: "rygiel_z", name: "Rygiel", school: "ziemia", charges: 2, castMs: 900,
    target: "compartment", durationMs: 20000, effect: "seal_doors",
    desc: "Zamyka drzwi przedziału na 20 s." },
  { id: "wstrzas", name: "Wstrząs", school: "ziemia", charges: 2, castMs: 1000,
    target: "compartment", durationMs: 1500, effect: "quake",
    desc: "Przerywa wszystkie kanały w przedziale i przewraca na 1.5 s." },
  { id: "zawal", name: "Zawał", school: "ziemia", charges: 1, castMs: 2000,
    target: "compartment", effect: "collapse",
    desc: "Zamyka przedział na stałe. Jego artefakt przepada." },

  // ------------------------------------------------------------- mrok
  { id: "zgaszenie", name: "Zgaszenie", school: "mrok", charges: 3, castMs: 600,
    target: "compartment", durationMs: 40000, effect: "douse",
    desc: "Gasi światło w przedziale na 40 s." },
  { id: "wymazanie", name: "Wymazanie", school: "mrok", charges: 2, castMs: 1200,
    target: "compartment", effect: "erase_log",
    desc: "Kasuje własne wpisy z rejestru przedziału w tym akcie." },
  { id: "falszywy_slad", name: "Fałszywy ślad", school: "mrok", charges: 3, castMs: 800,
    target: "compartment", effect: "plant_residue", pickSchool: true,
    desc: "Podrzuca osad wybranej szkoły." },
  { id: "cien", name: "Cień", school: "mrok", charges: 2, castMs: 500,
    target: "self", durationMs: 5000, effect: "invisible",
    desc: "Niewidzialny przez 5 s. Rejestr i tak go zapisuje." },

  // ------------------------------------------------------------- światło
  { id: "przebranie", name: "Przebranie", school: "swiatlo", charges: 2, castMs: 1000,
    target: "self", durationMs: 14000, effect: "disguise",
    desc: "Renderuje się jako inna klasa przez 14 s. Rejestr zapisuje tę klasę." },
  { id: "sobowtor", name: "Sobowtór", school: "swiatlo", charges: 2, castMs: 900,
    target: "point", durationMs: 8000, effect: "decoy",
    desc: "Kopia maga odchodzi w bok na 8 s." },
  { id: "oslepienie", name: "Oślepienie", school: "swiatlo", charges: 3, castMs: 600,
    target: "actor", durationMs: 6000, vision: 0.25, effect: "blind",
    desc: "Wzrok celu spada do 25% na 6 s." },
  { id: "falszywa_sylwetka", name: "Fałszywa sylwetka", school: "swiatlo", charges: 2,
    castMs: 1000, target: "compartment", durationMs: 15000, effect: "fake_silhouette",
    pickClass: true,
    desc: "Karmi kamery bazy wybraną klasą przez 15 s." }
];

const BY_ID = new Map(SPELLS.map((s) => [s.id, s]));

/**
 * Compartment-scoped spells act on wherever the mage is standing, so they
 * need no aim. Kept as data rather than a hardcoded list in the dispatcher
 * so a new spell declares its own targeting.
 */
const COMPARTMENT_TARGETED = SPELLS
  .filter((s) => s.target === "compartment")
  .map((s) => s.id);

/** Ready-made books, because ten picks from twenty-four on a phone in
 *  ninety seconds is more tapping than anyone wants. Each is a playable
 *  answer to "how do I win", not a difficulty setting. */
const PRESETS = {
  "Rzeźnik": [
    "kula_ognia", "kula_ognia", "pochodnia", "zaplon",
    "sen", "sen", "topiel", "cisza",
    "podmuch", "przebranie"
  ],
  "Budowlaniec": [
    "mur", "mur", "rygiel_z", "zawal",
    "pozoga", "wstrzas", "burza", "podmuch",
    "ped", "przebranie"
  ],
  "Oszust": [
    "przebranie", "przebranie", "sobowtor", "falszywa_sylwetka",
    "wymazanie", "falszywy_slad", "zgaszenie", "cien",
    "oslepienie", "zimna_krew"
  ]
};

function spell(id) {
  const s = BY_ID.get(id);
  if (!s) throw new Error(`unknown spell: ${id}`);
  return s;
}

/**
 * Turn a list of BOOK_SLOTS spell ids into the mage's runtime book:
 * one entry per distinct spell, with duplicate picks folded into charges.
 */
function buildBook(ids) {
  const book = new Map();
  for (const id of ids) {
    const s = spell(id);
    const have = book.get(id);
    if (have) have.charges += s.charges;
    else book.set(id, { id, charges: s.charges, school: s.school });
  }
  return [...book.values()];
}

/** A book's school mix -- what his corpses will end up saying about him. */
function signature(book) {
  const out = {};
  for (const e of book) out[e.school] = (out[e.school] || 0) + e.charges;
  return out;
}

module.exports = {
  SCHOOLS, SPELLS, PRESETS, COMPARTMENT_TARGETED,
  spell, buildBook, signature
};

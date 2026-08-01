# I'm Not a Wizard, Harry

An online hidden-mage **investigation** on a derelict station. A squad sweeps
the wreck for magic-tech artifacts; one of them is a mage picking the rest off
with spells and passing as a hunter while he does it.

The design is not a chase. It is a case. No single piece of evidence names the
mage — each only narrows the field, and he has spells for corrupting every
layer of it. Argument happens on voice; the game supplies pings, not a chat
box, because typing on a phone mid-round does not work.

The full design and the reasoning behind each rule is in
[`docs/superpowers/specs/2026-08-01-wizard-hunt-rules-design.md`](../docs/superpowers/specs/2026-08-01-wizard-hunt-rules-design.md).

## Run it

```bash
npm install
npm start            # http://localhost:8080
npm test             # 74 assertions, no browser needed
node test/browser.js # drives the real client on an emulated iPhone
```

Five to eight players. Classes are unique within a round, and there are
exactly eight of them, which is what sets the ceiling.

## The round

Three acts of ten minutes. The wreck goes dark as they pass: vision is
multiplied by 1.0, then 0.75, then 0.5, and each act unlocks a new section
holding four artifacts.

Artifacts not extracted before an act ends are **lost**, as are any the mage
burns with Pożoga or buries with Zawał.

* **Hunters win** by securing 9 of 12 artifacts, or by convicting the mage.
* **Mage wins** when one hunter is left, or when thirty minutes pass with him
  still in play.

Four lost artifacts puts nine out of reach for good. From that moment the
hunters' only road is the tribunal — the one road they can be wrong on. That
is the mage's clock, and it is why stalling is a strategy for him rather than
a failure to act.

## The tribunal

Tasering somebody and binding them freezes the round and puts every living
player on a vote screen. It carries the accused and whoever bound them, and
nothing else: the case is what people say out loud.

A majority of the living convicts. Ties and abstentions release. Votes are
published afterwards, because how somebody voted is itself evidence. Two
minutes between sittings; a minute of immunity for anyone released.

**The mage may bind and accuse too.** It is his only kill that costs no
charges, and it makes "why did *you* catch him" a question worth asking.

At three players a mage voting with one hunter against the other wins the
round outright — so the fewer of you are left, the more accusing is suicide.

## Evidence

| Source | Says | Does not say |
|---|---|---|
| Compartment transit log | a class and a time | a name you can trust — a disguise writes somebody else's class |
| Corpse | the school that killed it, time ±30 s | who cast |
| Residue | a school was worked here, 90 s | by whom, or whether it was planted |

Extracting an artifact hands over that compartment's log for the current act,
so the errand and the evidence are the same errand. The Archiwista reads logs
without an artifact; his Filtr still sees entries the mage erased.

## Classes

Eight, one per seat, each picking one of three items before the round.

| Class | Vision | Notes |
|---|---|---|
| Strażnik | 210 | survives a hit; slower |
| Zwiadowca | 330 | longest sight, drones and sensors |
| Strzelec | 250 | the only ranged stun, 330 px |
| Inkwizytor | 240 | longer taser, reads bodies and residue |
| Chirurg | 230 | revives one hunter, or times a death exactly |
| Runarz | 235 | fast extraction, seals artifacts against destruction |
| Archiwista | 225 | reads transit logs; erasure-proof filter |
| Technik | 245 | light, field cameras, door locks |

## The book

The mage fills **ten slots** from twenty-four spells across six schools —
ogień, woda, powietrze, ziemia, mrok, światło. Duplicates stack charges. When
a spell runs out it is gone for the round.

Charges are the spine of the evidence game: he cannot change style halfway,
and every corpse carries the school that killed it, so his loadout leaves a
signature. Three presets ship, and they play as three different games:

* **Rzeźnik** kills directly and writes a legible file about himself.
* **Budowlaniec** need not kill at all — he walls artifacts off and wins on
  the clock.
* **Oszust** has *no lethal spell whatsoever* and can only win by tribunal,
  framing hunters with their own hands.

Every cast has a wind-up that blooms for anyone with line of sight, and a
taser landing inside it interrupts the cast **and eats the charge**. Without
that tell the mage is unbeatable; with it, being seen is the risk he manages.

The mage also picks his cover class's item and has to be able to perform it.
Claiming the Chirurg's Stabilizator and never reviving anybody is evidence.

## The base

The dead and the ejected crew the station instead of watching. They get two
camera feeds each from a shared set, plus doors and emergency lights out of a
pool of six per act shared by the whole base.

Feeds show **class silhouettes, never names**, so a disguise fools the base
exactly as it fools the living, and nobody down there ever learns who the mage
is. That is why they are free to keep talking on voice: at a thirty-minute
round, asking half the table to sit silent for twenty-five minutes does not
work, so their talking is made into the mechanic instead of a rule to enforce.

Half the cameras fail in act III. The base grows in people and loses its eyes.

## Controls

Keyboard: `WSAD` move, `E` hold (extract · bind · stabilise), `Space` taser,
`Q`/LMB cast the selected spell, `1`–`9` pick a slot, `F` use item, `R` read
the log here, `Z`/`X` ping.

Touch: the joystick spawns wherever your left thumb lands; tapping the right
half aims and fires; three buttons carry hold, taser/cast and ping.

## Architecture

```
server.js      http + websocket + tick loop, nothing else
src/rules.js   every tuning number
src/classes.js eight classes, twenty-four items
src/spells.js  twenty-four spells as data
src/map.js     fifteen compartments with walls and doors
src/evidence.js logs, corpse traces, residue, and the forgeries
src/round.js   acts, artifacts, win conditions
src/tribunal.js capture, vote, verdict
src/base.js    the dead crew
src/room.js    phases and player state
src/actions.js movement, taser, channels, items, pings
src/effects.js wind-up, interrupt, spell effects
src/snapshot.js per-player culling before serialisation
```

**The server is authoritative, and that includes the fog.** Movement is
integrated from input vectors, casts are hit-tested server-side, and every
snapshot is culled per player *before* it is serialised. A body outside your
vision is absent from the message, not hidden in it, so stripping the overlay
client-side reveals nothing.

The class order in `src/classes.js` must match `CLASSES` in
`../pixel-art-toolkit/examples/wizard-hunt/make_hunters.py`; the client indexes
sheet rows by class position, so a reordering silently hands every player
somebody else's body. Regenerate with:

```bash
python3 ../pixel-art-toolkit/examples/wizard-hunt/make_hunters.py
cp ../pixel-art-toolkit/examples/wizard-hunt/hunters.png public/assets/
```

## Not built yet

* Sound.
* Persistent lobbies and reconnect — a thirty-minute round on mobile data
  needs this, but not in the first pass.
* More than one mage, and interactions between schools.

# I'm Not a Wizard, Harry

Online hidden-mage hunt on a derelict station. A squad of hunters sweeps the
wreck for magic-tech artifacts; one of them is secretly a mage picking the
rest off with spells.

Hunters do not have to kill the mage — they have to **capture** him: stun him
with a taser, then bind him while he is down. That single rule is what makes
the classes matter, because only the Marksman can land a stun at range and
only the Guardian survives being wrong.

## Run it

```bash
npm install
npm start            # http://localhost:8080
```

Open the page, enter a name, leave the room code blank to create a room, and
share the four-letter code. Minimum three players — but three is degenerate,
because one kill already drops the hunters to one. **Five or more** is the
real game.

Deploy anywhere that runs Node and allows WebSocket upgrades; `PORT` is read
from the environment.

## Controls

| Key | Action |
|---|---|
| `WSAD` / arrows | move |
| `E` (hold) | context: extract an artifact, bind a stunned player, stabilise a body |
| `Space` | taser (Marksman: rifle, long range) |
| `Q` | *mage only* — cast at the nearest hunter in range |
| `F` | *mage only* — decoy bloom somewhere you are not |
| `C` | *Scout only* — station cameras, brief full map vision |

## Classes

Everyone carries a taser. The kit differs in reach, eyesight, toughness and
one unique verb.

| Class | Vision | Perk |
|---|---|---|
| Strażnik (Guardian) | 210 | survives the first spell hit; slower |
| Zwiadowca (Scout) | 330 | longest sight, plus station cameras |
| Strzelec (Marksman) | 250 | the only ranged stun (330 px) |
| Inkwizytor (Inquisitor) | 240 | longer taser reach |
| Chirurg (Surgeon) | 230 | stabilise one downed hunter per round |
| Runarz (Runesmith) | 235 | extracts artifacts twice as fast |

The mage is dealt a class and a full kit too. He has to pass as one of them,
so he cannot be the only player without a loadout.

## Win conditions

* **Hunters** — secure all nine artifacts, or bind the mage.
* **Mage** — reduce the hunters to one.

Binding an innocent removes them from the round, so a wrong read costs the
squad a body as surely as the mage does.

## Design notes

**Casting has a visible wind-up.** The mage's kill is not instant: a
1.3 s tell broadcasts a bloom at his position that anyone with line of sight
can see, and a taser during the wind-up interrupts it. Without the tell the
mage is unbeatable; with it, being *seen* is the risk he manages. The decoy
(`F`) exists to muddy exactly that signal, so an FX sighting is evidence
rather than proof.

**The server is authoritative, and that includes the fog.** Movement is
integrated from client input vectors, never from client-reported positions,
so a patched client cannot teleport onto an artifact or into taser range.
Vision is culled per player *before* the snapshot is serialised — the dark
overlay in the renderer is a vignette over data the client was never sent,
not the security itself. Stripping the fog client-side reveals nothing.

**Artifacts sit inside named compartments** rather than scattered on open
floor, so the sweep forces hunters to separate and enter enclosed rooms.
That separation is what creates the isolated moments the mage needs.

**Channels break on movement.** Extraction, binding and stabilising all
require standing still, which is what makes them a commitment rather than a
tap.

## Assets

Sprites and effects are generated procedurally — see `../pixel-art-toolkit`
for the generators and the two skills (`fantasy-pixel-art`, `spell-fx`) that
document the techniques. Regenerate the hunter sheet with:

```bash
python3 ../pixel-art-toolkit/examples/wizard-hunt/make_hunters.py
cp ../pixel-art-toolkit/examples/wizard-hunt/hunters.png public/assets/
```

The class order in that script must match `CLASSES` in `server.js`; the
client indexes sheet rows by class position, so a reordering silently hands
every player somebody else's body.

## Not built yet

* Discussion/vote meetings — the current loop is a live hunt, not a
  round-table. Reporting a body and a timed vote would layer social deduction
  on top.
* Persistent lobbies and reconnect.
* Sound.

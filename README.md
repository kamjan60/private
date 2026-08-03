# private

> **Deprecated layout.** The two apps and the shared toolkit below were split
> into their own repos and are developed there now — this monorepo is kept
> only as historical reference, unmaintained going forward:
> - [`dread-deck`](https://github.com/kamjan60/dread-deck) — was `apps/tarot-reveal/`
> - [`i-am-not-a-wizard-harry`](https://github.com/kamjan60/i-am-not-a-wizard-harry) — was `apps/wizard-hunt-online/`, `specs/001-sprite-pipeline-manifest/`, `docs/superpowers/`, and the `examples/wizard-hunt/` part of the toolkit
> - [`claude-toolkit`](https://github.com/kamjan60/claude-toolkit) — was the rest of `tools/pixel-art-toolkit/`, plus the universal `.claude/skills/` and `.specify/`

Two applications and the toolkit that feeds one of them.

```text
apps/
  wizard-hunt-online/   "I'm Not a Wizard, Harry" — online hidden-mage hunt.
                        Node + ws server, canvas 2D client, and a build that
                        packs the whole game into one offline HTML file.
  tarot-reveal/         Fusion card-reveal generator for The Dread Deck.

tools/
  pixel-art-toolkit/    Procedural pixel art in plain Python and Pillow. Its
                        examples/wizard-hunt/ generates the game's sprite
                        sheets, the emissive layer and hunters.json.

docs/                   Design documents, including the game's rules spec.
specs/                  Spec Kit features: spec, plan, tasks, contracts.
```

## Why the split

`pixel-art-toolkit` sits under `tools/` rather than `apps/` because it is not
an application — it is a generator whose output is committed into the game.
The two directories that produce something a person runs live under `apps/`.

That boundary is not decorative: the game reads `hunters.json` by name and
refuses to start without it, so the toolkit and the app are coupled through a
declared contract rather than through matching array order. See
[`specs/001-sprite-pipeline-manifest/contracts/hunters-manifest.md`](specs/001-sprite-pipeline-manifest/contracts/hunters-manifest.md).

Paths inside each project are relative to that project. Anything crossing a
boundary — the game's regeneration commands, the specs — is written out in
full from the repository root.

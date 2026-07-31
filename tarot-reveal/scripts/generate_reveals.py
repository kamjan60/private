"""Batch-generate all 22 CardReveal .comp files (upright RELIC + reversed
CURSE, 44 files total) by text-templating the verified master template — no
live Fusion API calls, no Resolve round-trips.

Fusion .comp files are plain Lua-table text. We only ever touch three things:
  - Loader_Front's Filename (the front card image)
  - Text_Effect's StyledText (ability name line + word-wrapped one-sentence
    effect, from cards.json's relic_short/curse_short — matches the
    rulebook's own Reveal spec: "Card, name, one-sentence effect")
  - Transform3D_Orient's Rotate.Z, inserted only for the curse variant (180 =
    reversed). Upright is Fusion's own default and isn't written to the file
    at all, so the relic variant needs no change there.
Everything else (flip keyframes, hold/reveal timing, banner, font, colors,
scale) is byte-identical across every generated file, inherited from the
master.

Run:
    python apps/tarot-reveal/scripts/generate_reveals.py
"""

from __future__ import annotations

import re
import sys
import textwrap
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from tarot_lib.cards_io import load_cards

TEMPLATE_PATH = Path(__file__).resolve().parents[1] / "fusion" / "CardReveal_template.comp"
OUT_DIR = Path(__file__).resolve().parents[1] / "fusion" / "generated"

WRAP_WIDTH = 26  # chars/line — matches the manually-verified box fit at the
                 # quick-reference (one-sentence) text length

# Matches the Filename line inside the Loader_Front tool block only (bounded
# by the next tool's opening line so Loader_Back's own Filename is untouched).
_LOADER_FRONT_BLOCK = re.compile(
    r'(Loader_Front = Loader \{.*?Filename = ")(.*?)(",)',
    re.DOTALL,
)
_STYLED_TEXT = re.compile(
    r'(StyledText = Input \{ Value = ")(.*?)(", \},)',
    re.DOTALL,
)
# Reversed (curse) needs a NEW field inserted — Rotate.Z=0 is Fusion's own
# default and is simply absent from the serialized file, so there is nothing
# to find-and-replace; we inject the field as the first Input in the block.
_ORIENT_INPUTS_OPEN = re.compile(
    r'(Transform3D_Orient = Transform3D \{\s*\n\s*Inputs = \{\s*\n)'
)
_ORIENT_ROTATE_Z_FIELD = '\t\t\t\t["Transform3DOp.Rotate.Z"] = Input { Value = 180, },\n'

# Border_BG color — gold (relic) vs purple (curse). Matches the master's
# TopLeftRed/Green/Blue triplet inside the Border_BG tool block specifically
# (bounded so Fill_BG's own color triplet, same field names, is untouched).
_BORDER_COLOR_BLOCK = re.compile(
    r'(Border_BG = Background \{.*?TopLeftRed = Input \{ Value = )([\d.]+)(, \},\s*'
    r'TopLeftGreen = Input \{ Value = )([\d.]+)(, \},\s*'
    r'TopLeftBlue = Input \{ Value = )([\d.]+)(, \},)',
    re.DOTALL,
)
CURSE_BORDER_RGB = (0.55, 0.15, 0.65)  # purple


def _lua_escape(text: str) -> str:
    # Order matters: escape backslashes first, then quotes, then convert
    # real newlines to the literal two-char "\n" a Lua quoted string needs
    # (a raw newline inside "..." breaks the string across file lines).
    return (
        text.replace("\\", "\\\\")
        .replace('"', '\\"')
        .replace("\n", "\\n")
    )


def build_styled_text(full_text: str, short_text: str) -> str:
    # The ability NAME comes from the full rulebook text ("Fool's Escape: ...");
    # the DESCRIPTION line(s) come from the quick-reference one-sentence text
    # instead of the full paragraph.
    name, _, _ = full_text.partition(":")
    name = name.strip()
    wrapped_lines = textwrap.wrap(short_text.strip(), width=WRAP_WIDTH)
    return "\n".join([f"{name}:", *wrapped_lines])


def render_variant(template: str, front_path: str, styled_text: str, reversed_: bool) -> str:
    out = _LOADER_FRONT_BLOCK.sub(
        lambda m, p=front_path: m.group(1) + p + m.group(3), template
    )
    out = _STYLED_TEXT.sub(
        lambda m, t=styled_text: m.group(1) + t + m.group(3), out
    )
    if reversed_:
        out, n = _ORIENT_INPUTS_OPEN.subn(
            lambda m: m.group(1) + _ORIENT_ROTATE_Z_FIELD, out
        )
        if n == 0:
            raise RuntimeError(
                "Transform3D_Orient Inputs block not found — template structure changed?"
            )
        r, g, b = CURSE_BORDER_RGB
        out, n = _BORDER_COLOR_BLOCK.subn(
            lambda m: f"{m.group(1)}{r}{m.group(3)}{g}{m.group(5)}{b}{m.group(7)}", out
        )
        if n == 0:
            raise RuntimeError(
                "Border_BG color block not found — template structure changed?"
            )
    return out


def main() -> int:
    if not TEMPLATE_PATH.exists():
        print(f"Template not found: {TEMPLATE_PATH}")
        print("Export it first from Fusion: File > Export > Fusion Composition...")
        return 1

    template = TEMPLATE_PATH.read_text(encoding="utf-8")
    if not _LOADER_FRONT_BLOCK.search(template):
        print("Loader_Front.Filename pattern not found in template — did the "
              "tool/field names change? Re-check the .comp text structure.")
        return 1
    if not _STYLED_TEXT.search(template):
        print("Text_Effect.StyledText pattern not found in template.")
        return 1
    if not _ORIENT_INPUTS_OPEN.search(template):
        print("Transform3D_Orient Inputs block not found in template.")
        return 1

    cards = load_cards()
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    count = 0
    for card in cards:
        front_path = _lua_escape(str(card.front_path))
        slug = f"{card.number:02d}-{card.card_name.replace(' ', '')}"

        relic_styled = _lua_escape(build_styled_text(card.relic_text, card.relic_short))
        relic_out = render_variant(template, front_path, relic_styled, reversed_=False)
        (OUT_DIR / f"{slug}-relic.comp").write_text(relic_out, encoding="utf-8")

        curse_styled = _lua_escape(build_styled_text(card.curse_text, card.curse_short))
        curse_out = render_variant(template, front_path, curse_styled, reversed_=True)
        (OUT_DIR / f"{slug}-curse.comp").write_text(curse_out, encoding="utf-8")

        count += 2
        print(f"  [{card.number:02d}] {card.card_name} -> {slug}-relic.comp, {slug}-curse.comp")

    print(f"\n{count}/{len(cards) * 2} generated -> {OUT_DIR}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""Build ONE CardReveal rig in the currently active Fusion comp — for manual
inspection/tuning before batch-generating all 22 cards.

Run from IntelliJ (Resolve open, Fusion page active on an empty Fusion
Clip/Title dropped on 'AI Jester Timeline'):

    python apps/tarot-reveal/scripts/build_template.py

Uses The Fool (00) as the preview card. After running, eyeball the flip in
the Fusion viewer; if any tool/input name in tarot_lib/template_build.py is
wrong for your Resolve version, comp.FindTool(...) calls will raise — use
tarot_lib.fusion_conn.dump_inputs(tool) on the offending tool to find the
right ID and patch the CONFIG block at the top of template_build.py.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from tarot_lib.cards_io import load_cards, find_card, CARD_BACK_FILE
from tarot_lib.fusion_conn import get_current_comp
from tarot_lib.template_build import build_card_reveal_comp


def main() -> int:
    cards = load_cards()
    preview = find_card(cards, 0)  # The Fool

    comp = get_current_comp()
    tools = build_card_reveal_comp(
        comp,
        front_image_path=str(preview.front_path),
        back_image_path=str(CARD_BACK_FILE),
    )
    tools["text_name"][template_input("text_styled_text")] = preview.card_name
    tools["text_status"][template_input("text_styled_text")] = "RELIC"
    tools["text_effect"][template_input("text_styled_text")] = preview.relic_text or "(fill relic_text in cards.json)"

    print(f"Built preview rig for: {preview.card_name}")
    print("Inspect in the Fusion viewer, then confirm before running generate_reveals.py.")
    return 0


def template_input(key: str) -> str:
    from tarot_lib.template_build import INPUT
    return INPUT[key]


if __name__ == "__main__":
    raise SystemExit(main())

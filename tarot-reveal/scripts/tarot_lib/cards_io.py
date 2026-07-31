"""Load data/cards.json into plain dataclasses."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

DEFAULT_CARDS_JSON = Path(__file__).resolve().parents[2] / "data" / "cards.json"
CARDS_IMAGE_DIR = Path(r"D:\OBS Store movies\Images\Tarot\Cards-png")
CARD_BACK_FILE = CARDS_IMAGE_DIR / "CardBacks.png"


@dataclass(frozen=True)
class Card:
    number: int
    filename: str
    card_name: str
    relic_short: str
    curse_short: str
    relic_text: str
    curse_text: str
    # Run-mechanics metadata, not used by the Fusion reveal rig: `weight` gates Curse
    # removal (1-2 free, 3 for the price of a Relic, 4-5 unremovable), `curse_fallback`
    # is the pre-declared reduced tier for Curses that can make a game unfinishable.
    # Optional so an older cards.json still loads.
    weight: int | None = None
    timing: str = ""
    curse_fallback: str = ""

    @property
    def front_path(self) -> Path:
        return CARDS_IMAGE_DIR / self.filename


def load_cards(path: str | Path = DEFAULT_CARDS_JSON) -> list[Card]:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    return [Card(**row) for row in data]


def find_card(cards: list[Card], number: int) -> Card:
    for c in cards:
        if c.number == number:
            return c
    raise KeyError(f"No card with number={number} in {DEFAULT_CARDS_JSON}")

from __future__ import annotations

from enum import IntEnum, auto
from typing import NamedTuple


class Dir(NamedTuple):
    x: int
    y: int


UP = Dir(0, -1)
DOWN = Dir(0, 1)
LEFT = Dir(-1, 0)
RIGHT = Dir(1, 0)


class AppScreen(IntEnum):
    MENU = auto()
    LEVEL_SELECT = auto()
    PLAY = auto()
    GAME_OVER = auto()
    WIN_LEVEL = auto()
    CAMPAIGN_COMPLETE = auto()


class PowerupKind(IntEnum):
    SPEED = auto()
    STRENGTH = auto()
    SEE_THROUGH = auto()

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class LevelConfig:
    id: int
    title: str
    ghost_count: int
    ghost_speed_mult: float
    player_speed_mult: float
    lantern_radius_px: int
    lives: int
    weapon_cooldown_s: float
    weapon_range_tiles: int
    weapon_stun_s: float
    frightened_s: float
    buff_speed_duration_s: float
    buff_strength_duration_s: float
    buff_see_duration_s: float
    proximity_pulse: bool


LEVELS: tuple[LevelConfig, ...] = (
    LevelConfig(1, "The Cellar", 2, 0.85, 1.0, 200, 5, 0.55, 4, 1.1, 6.0, 5.0, 5.0, 5.0, False),
    LevelConfig(2, "Rust Halls", 2, 0.9, 1.0, 190, 5, 0.55, 4, 1.05, 5.5, 4.5, 4.5, 4.5, False),
    LevelConfig(3, "Drowned Steps", 2, 0.95, 1.0, 180, 4, 0.6, 4, 1.0, 5.0, 4.0, 4.0, 4.0, True),
    LevelConfig(4, "Descent", 3, 0.95, 1.0, 170, 4, 0.65, 4, 0.95, 4.5, 3.8, 3.8, 3.5, True),
    LevelConfig(5, "Black Well", 3, 1.0, 1.0, 160, 4, 0.65, 4, 0.9, 4.0, 3.5, 3.5, 3.2, True),
    LevelConfig(6, "Sunken Choir", 4, 1.0, 1.0, 150, 3, 0.7, 4, 0.85, 3.5, 3.2, 3.2, 3.0, True),
    LevelConfig(7, "Ash Gate", 4, 1.05, 1.0, 135, 3, 0.75, 4, 0.8, 3.2, 3.0, 3.0, 2.6, True),
    LevelConfig(8, "Grinning Hollow", 4, 1.1, 1.0, 120, 3, 0.8, 3, 0.75, 3.0, 2.8, 2.8, 2.4, True),
    LevelConfig(9, "The Maw", 4, 1.15, 1.0, 105, 2, 0.85, 3, 0.7, 2.6, 2.4, 2.4, 2.0, True),
    LevelConfig(10, "Last Breath", 4, 1.2, 1.0, 90, 2, 0.9, 3, 0.65, 2.4, 2.0, 2.0, 1.7, True),
)


def get_level(n: int) -> LevelConfig:
    n = max(1, min(10, n))
    return LEVELS[n - 1]

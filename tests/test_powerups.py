from game.powerups import BuffState
from game.types import PowerupKind


def test_buff_tick() -> None:
    b = BuffState()
    b.apply_pickup(PowerupKind.SPEED, 2.0)
    assert b.speed_remaining == 2.0
    b.tick(0.5)
    assert abs(b.speed_remaining - 1.5) < 1e-6


def test_refresh_speed() -> None:
    b = BuffState()
    b.apply_pickup(PowerupKind.SPEED, 1.0)
    b.apply_pickup(PowerupKind.SPEED, 3.0)
    assert b.speed_remaining == 3.0

from __future__ import annotations

from dataclasses import dataclass, field

from .types import PowerupKind


@dataclass
class BuffState:
    """Timed buffs on the survivor. Refresh rule: picking up same type refreshes duration."""

    speed_remaining: float = 0.0
    strength_remaining: float = 0.0
    see_through_remaining: float = 0.0

    def tick(self, dt: float) -> None:
        self.speed_remaining = max(0.0, self.speed_remaining - dt)
        self.strength_remaining = max(0.0, self.strength_remaining - dt)
        self.see_through_remaining = max(0.0, self.see_through_remaining - dt)

    def apply_pickup(self, kind: PowerupKind, duration: float) -> None:
        if kind is PowerupKind.SPEED:
            self.speed_remaining = duration
        elif kind is PowerupKind.STRENGTH:
            self.strength_remaining = duration
        elif kind is PowerupKind.SEE_THROUGH:
            self.see_through_remaining = duration

    @property
    def speed_mult(self) -> float:
        return 1.45 if self.speed_remaining > 0 else 1.0

    @property
    def strength_stun_mult(self) -> float:
        return 1.65 if self.strength_remaining > 0 else 1.0

    @property
    def strength_range_bonus_tiles(self) -> float:
        return 1.0 if self.strength_remaining > 0 else 0.0

    def active_labels(self) -> list[tuple[str, float]]:
        out: list[tuple[str, float]] = []
        if self.speed_remaining > 0:
            out.append(("SPD", self.speed_remaining))
        if self.strength_remaining > 0:
            out.append(("STR", self.strength_remaining))
        if self.see_through_remaining > 0:
            out.append(("SEE", self.see_through_remaining))
        return out

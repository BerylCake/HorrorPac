from __future__ import annotations

from typing import TYPE_CHECKING

from .types import Dir, DOWN, LEFT, RIGHT, UP

if TYPE_CHECKING:
    pass


def raycast_hit_ghost_line(session: object, *, range_tiles: int) -> int | None:
    """Grid line from survivor cell in facing direction; stops at wall."""
    px, py = session.player_cell
    dx, dy = session.player_dir.x, session.player_dir.y
    if dx == 0 and dy == 0:
        dy = -1
    for dist in range(1, range_tiles + 1):
        cx = px + dx * dist
        cy = py + dy * dist
        if not session.walkable_cell(cx, cy):
            break
        for i, (gx, gy) in enumerate(session.ghost_cells):
            if session.ghost_banish[i] > 0:
                continue
            if gx == cx and gy == cy:
                return i
    return None


def dir_from_keys(keys: object) -> Dir | None:
    from . import input_bindings as ib

    if keys[ib.SURVIVOR_UP] or keys[ib.SURVIVOR_W]:
        return UP
    if keys[ib.SURVIVOR_DOWN] or keys[ib.SURVIVOR_S]:
        return DOWN
    if keys[ib.SURVIVOR_LEFT] or keys[ib.SURVIVOR_A]:
        return LEFT
    if keys[ib.SURVIVOR_RIGHT] or keys[ib.SURVIVOR_D]:
        return RIGHT
    return None

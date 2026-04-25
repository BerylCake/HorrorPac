from __future__ import annotations

import pygame

from .types import PowerupKind
from .session import GameSession, TILE
from .characters import GHOST_COLORS, draw_ghost, draw_ghost_alpha, draw_survivor


COL_WALL = (35, 40, 55)
COL_FLOOR = (18, 20, 28)
COL_PELLET = (110, 120, 150)
COL_POWER = (180, 90, 200)
COL_SPEED = (80, 200, 255)
COL_STR = (255, 200, 80)
COL_SEE = (200, 220, 255)


def draw_world(
    surf: pygame.Surface,
    session: GameSession,
    offset: tuple[int, int],
) -> None:
    ox, oy = offset
    m = session.maze
    t = session.tile

    surf.fill((0, 0, 0))
    for y in range(m.height):
        for x in range(m.width):
            px = ox + x * t
            py = oy + y * t
            r = pygame.Rect(px, py, t, t)
            if m.walls[y][x]:
                pygame.draw.rect(surf, COL_WALL, r)
            else:
                pygame.draw.rect(surf, COL_FLOOR, r)

    for (x, y) in session.pellets:
        cx = ox + x * t + t // 2
        cy = oy + y * t + t // 2
        pygame.draw.circle(surf, COL_PELLET, (cx, cy), 3)

    for (x, y) in session.power_pellets:
        cx = ox + x * t + t // 2
        cy = oy + y * t + t // 2
        pygame.draw.circle(surf, COL_POWER, (cx, cy), 7)

    for (x, y), kind in session.powerups.items():
        cx = ox + x * t + t // 2
        cy = oy + y * t + t // 2
        if kind is PowerupKind.SPEED:
            col = COL_SPEED
        elif kind is PowerupKind.STRENGTH:
            col = COL_STR
        else:
            col = COL_SEE
        pygame.draw.rect(surf, col, pygame.Rect(cx - 6, cy - 6, 12, 12), border_radius=2)

    # Ghosts (world pass; see-through handled separately)
    fr = session.frightened_remaining > 0
    for i in range(len(session.ghost_px)):
        if session.ghost_banish[i] > 0:
            continue
        gx = int(session.ghost_px[i])
        gy = int(session.ghost_py[i])
        draw_ghost(surf, ox + gx, oy + gy, GHOST_COLORS[i % len(GHOST_COLORS)], frightened=fr)

    # Player
    px = int(session.player_px)
    py = int(session.player_py)
    draw_survivor(surf, ox + px, oy + py, session.player_dir)


def draw_ghost_silhouettes(
    surf: pygame.Surface,
    session: GameSession,
    offset: tuple[int, int],
    alpha: int,
) -> None:
    if alpha <= 0:
        return
    ox, oy = offset
    fr = session.frightened_remaining > 0
    for i in range(len(session.ghost_px)):
        if session.ghost_banish[i] > 0:
            continue
        gx = int(session.ghost_px[i])
        gy = int(session.ghost_py[i])
        draw_ghost_alpha(
            surf,
            ox + gx,
            oy + gy,
            GHOST_COLORS[i % len(GHOST_COLORS)],
            alpha,
            frightened=fr,
        )

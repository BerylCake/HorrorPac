"""Procedural survivor + ghost bodies with simple human cartoon faces."""

from __future__ import annotations

import math

import pygame

from .types import Dir, DOWN, LEFT, RIGHT, UP

GHOST_COLORS = (
    (220, 80, 80),
    (120, 180, 255),
    (255, 160, 80),
    (160, 255, 160),
)
COL_PLAYER = (220, 210, 120)

# Must match session collision radii ~11 / 10
SURVIVOR_R = 11
GHOST_W = 22
GHOST_H = 24


def draw_survivor(
    surf: pygame.Surface,
    cx: int,
    cy: int,
    facing: Dir,
    body_color: tuple[int, int, int] = COL_PLAYER,
) -> None:
    """Wanderer: round body + simple face; mouth opening hints toward facing."""
    pygame.draw.circle(surf, body_color, (cx, cy), SURVIVOR_R)

    # Skin-ish face patch (slightly lighter)
    fc = (240, 225, 190)
    pygame.draw.circle(surf, fc, (cx, cy - 2), 7)

    # Eyes
    eye_off_x, eye_off_y = 3, 0
    pygame.draw.circle(surf, (40, 35, 35), (cx - eye_off_x, cy - 2 + eye_off_y), 2)
    pygame.draw.circle(surf, (40, 35, 35), (cx + eye_off_x, cy - 2 + eye_off_y), 2)
    pygame.draw.circle(surf, (250, 250, 250), (cx - eye_off_x, cy - 2 + eye_off_y), 1)
    pygame.draw.circle(surf, (250, 250, 250), (cx + eye_off_x, cy - 2 + eye_off_y), 1)

    # Mouth wedge: small arc rotated by facing
    mouth_c = (60, 45, 45)
    if facing == RIGHT:
        pygame.draw.arc(surf, mouth_c, (cx - 1, cy + 1, 10, 6), 0.2, math.pi - 0.2, 2)
    elif facing == LEFT:
        pygame.draw.arc(surf, mouth_c, (cx - 9, cy + 1, 10, 6), 0.2, math.pi - 0.2, 2)
    elif facing == UP:
        pygame.draw.arc(surf, mouth_c, (cx - 5, cy - 6, 10, 8), math.pi * 0.15, math.pi * 0.85, 2)
    else:
        pygame.draw.arc(surf, mouth_c, (cx - 5, cy + 2, 10, 8), math.pi * 1.1, math.pi * 1.9, 2)


def _ghost_polygon_points(cx: int, cy: int) -> list[tuple[int, int]]:
    """Classic ghost outline: dome + three bottom bumps."""
    w2, h2 = GHOST_W // 2, GHOST_H // 2
    left, top = cx - w2, cy - h2
    pts: list[tuple[int, int]] = []
    # top arc (left to right)
    for i in range(9):
        a = math.pi + i / 8 * math.pi
        pts.append((int(cx + w2 * 0.9 * math.cos(a)), int(cy - h2 + 8 + 8 * math.sin(a))))
    # down right side
    pts.append((left + GHOST_W, top + h2))
    # bottom scallops
    bump_r = 5
    for bx in (cx - 6, cx, cx + 6):
        for j in range(5, -1, -1):
            a = math.pi * j / 5
            pts.append((int(bx + bump_r * math.cos(a)), int(top + GHOST_H - 6 + bump_r * math.sin(a))))
    pts.append((left, top + h2))
    # up left side
    pts.append((left, top + 10))
    return pts


def draw_ghost(
    surf: pygame.Surface,
    cx: int,
    cy: int,
    color: tuple[int, int, int],
    *,
    frightened: bool = False,
) -> None:
    """Ghost silhouette + human face. Center (cx, cy)."""
    w2, h2 = GHOST_W // 2, GHOST_H // 2
    left, top = cx - w2, cy - h2

    # Main blob: ellipse + rect + three bottom circles (union fill)
    pygame.draw.ellipse(surf, color, (left, top, GHOST_W, GHOST_H - 6))
    pygame.draw.rect(surf, color, (left, top + h2 - 2, GHOST_W, 10))
    for ox in (-6, 0, 6):
        pygame.draw.circle(surf, color, (cx + ox, top + GHOST_H - 5), 6)

    # Face (lighter patch)
    face = (min(255, color[0] + 50), min(255, color[1] + 45), min(255, color[2] + 40))
    pygame.draw.ellipse(surf, face, (cx - 8, cy - 8, 16, 14))

    # Eyes
    ey = 2 if frightened else 0
    pygame.draw.circle(surf, (30, 30, 35), (cx - 4, cy - 4 + ey), 2)
    pygame.draw.circle(surf, (30, 30, 35), (cx + 4, cy - 4 + ey), 2)
    pygame.draw.circle(surf, (250, 250, 250), (cx - 4, cy - 4 + ey), 1)
    pygame.draw.circle(surf, (250, 250, 250), (cx + 4, cy - 4 + ey), 1)

    # Mouth
    if frightened:
        pygame.draw.arc(surf, (50, 40, 45), (cx - 5, cy + 2, 10, 8), math.pi * 0.1, math.pi * 0.9, 2)
    else:
        pygame.draw.arc(surf, (50, 40, 45), (cx - 5, cy + 0, 10, 6), math.pi * 1.1, math.pi * 1.9, 2)


def draw_ghost_alpha(
    surf: pygame.Surface,
    cx: int,
    cy: int,
    color: tuple[int, int, int],
    alpha: int,
    *,
    frightened: bool = False,
) -> None:
    """Ghost for see-through layer with alpha."""
    layer = pygame.Surface((GHOST_W + 8, GHOST_H + 8), pygame.SRCALPHA)
    layer.fill((0, 0, 0, 0))
    draw_ghost(layer, GHOST_W // 2 + 4, GHOST_H // 2 + 4, color, frightened=frightened)
    layer.set_alpha(alpha)
    surf.blit(layer, (cx - GHOST_W // 2 - 4, cy - GHOST_H // 2 - 4))


def draw_ghost_scaled(
    surf: pygame.Surface,
    cx: int,
    cy: int,
    color: tuple[int, int, int],
    scale: float,
    *,
    frightened: bool = False,
) -> None:
    """For jumpscare: draw ghost to temp surface and scale."""
    w, h = int((GHOST_W + 8) * scale), int((GHOST_H + 8) * scale)
    tmp = pygame.Surface((GHOST_W + 8, GHOST_H + 8), pygame.SRCALPHA)
    tmp.fill((0, 0, 0, 0))
    draw_ghost(tmp, GHOST_W // 2 + 4, GHOST_H // 2 + 4, color, frightened=frightened)
    scaled = pygame.transform.smoothscale(tmp, (max(1, w), max(1, h)))
    r = scaled.get_rect(center=(cx, cy))
    surf.blit(scaled, r)

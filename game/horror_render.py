from __future__ import annotations

import pygame

from .session import GameSession


def apply_lantern(screen: pygame.Surface, session: GameSession, offset: tuple[int, int]) -> None:
    """Dark vignette with additive light pool around the wanderer."""
    w, h = screen.get_size()
    ox, oy = offset
    px = ox + int(session.player_px)
    py = oy + int(session.player_py)
    r = max(48, session.cfg.lantern_radius_px)

    dark = pygame.Surface((w, h), pygame.SRCALPHA)
    dark.fill((4, 6, 12, 200))
    screen.blit(dark, (0, 0))

    side = r * 3
    light = pygame.Surface((side, side), pygame.SRCALPHA)
    cx = cy = side // 2
    for rad in range(int(r * 1.35), 0, -3):
        t = rad / max(1.0, float(r * 1.35))
        a = int(70 * (1.0 - t) ** 0.7)
        pygame.draw.circle(light, (70, 80, 110, min(85, a)), (cx, cy), rad)
    screen.blit(light, (px - cx, py - cy), special_flags=pygame.BLEND_RGBA_ADD)

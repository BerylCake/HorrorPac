from __future__ import annotations

import sys
from pathlib import Path

import pygame

from game.horror_render import apply_lantern
from game.jumpscare_render import draw_jumpscare, play_jumpscare_stinger
from game.input_bindings import (
    GHOST0_DOWN,
    GHOST0_LEFT,
    GHOST0_RIGHT,
    GHOST0_UP,
    MENU_BACK,
    MENU_CONFIRM,
    MENU_PAUSE,
)
from game.level_config import LEVELS
from game.render import draw_ghost_silhouettes, draw_world
from game.save import load_max_unlocked, save_max_unlocked
from game.session import TILE, build_session
from game.types import Dir, DOWN, LEFT, RIGHT, UP


SCREEN_W = 960
SCREEN_H = 720


def ghost_human_dir(keys: object, slot: int) -> Dir | None:
    if slot == 0:
        if keys[GHOST0_UP]:
            return UP
        if keys[GHOST0_DOWN]:
            return DOWN
        if keys[GHOST0_LEFT]:
            return LEFT
        if keys[GHOST0_RIGHT]:
            return RIGHT
    return None


def main() -> None:
    pygame.init()
    try:
        pygame.mixer.init(frequency=22050, size=-16, channels=1, buffer=512)
    except pygame.error:
        pass
    pygame.display.set_caption("Horror Maze")
    screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
    clock = pygame.time.Clock()
    font = pygame.font.Font(None, 32)
    small = pygame.font.Font(None, 24)

    root = Path(__file__).resolve().parent
    max_unlocked = load_max_unlocked(root)

    mode = "menu"
    selected_idx = 0  # 0..max_unlocked-1 for level pick
    current_level = 1
    session = None
    human_ghost: set[int] = set()
    message_timer = 0.0
    end_text = ""

    running = True
    while running:
        dt = clock.tick(60) / 1000.0

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN:
                if mode == "menu":
                    if event.key == MENU_CONFIRM:
                        mode = "select"
                        selected_idx = 0
                    elif event.key == MENU_BACK:
                        running = False
                elif mode == "select":
                    if event.key == MENU_BACK:
                        mode = "menu"
                    elif event.key == pygame.K_UP:
                        selected_idx = max(0, selected_idx - 1)
                    elif event.key == pygame.K_DOWN:
                        selected_idx = min(max_unlocked - 1, selected_idx + 1)
                    elif event.key == MENU_CONFIRM:
                        current_level = selected_idx + 1
                        session = build_session(current_level, human_ghost)
                        mode = "play"
                elif mode == "play":
                    if event.key == MENU_PAUSE:
                        mode = "menu"
                    elif event.key == MENU_BACK:
                        mode = "select"
                    elif event.key == pygame.K_h:
                        human_ghost = {0} if not human_ghost else set()
                        session = build_session(current_level, human_ghost)
                elif mode in ("won", "lost"):
                    if event.key == MENU_CONFIRM or event.key == MENU_BACK:
                        mode = "select"
                        selected_idx = min(max(0, current_level), max_unlocked - 1)
                        session = None

        keys = pygame.key.get_pressed()

        if mode == "play" and session is not None:
            gh: dict[int, Dir | None] = {}
            if human_ghost:
                d0 = ghost_human_dir(keys, 0)
                if d0 is not None:
                    gh[0] = d0
            session.tick(dt, keys, gh)
            if session.jumpscare_stinger_pending:
                play_jumpscare_stinger()
                session.jumpscare_stinger_pending = False
            if session.won:
                mode = "won"
                end_text = "Floor cleared. The way forward opens."
                if current_level == 10:
                    end_text = "You escaped the last breath."
                max_unlocked = max(max_unlocked, min(10, current_level + 1))
                save_max_unlocked(max_unlocked, root)
            elif session.lost:
                mode = "lost"
                end_text = "The dark keeps you."

        screen.fill((0, 0, 0))

        if mode == "menu":
            t = font.render("Horror Maze", True, (200, 200, 210))
            screen.blit(t, (SCREEN_W // 2 - t.get_width() // 2, 200))
            t2 = small.render("ENTER: play   ESC: quit   H in-game: toggle ghost P2 (IJKL)", True, (140, 140, 160))
            screen.blit(t2, (SCREEN_W // 2 - t2.get_width() // 2, 280))
        elif mode == "select":
            t = font.render(f"Descend (max unlocked: {max_unlocked})", True, (200, 200, 210))
            screen.blit(t, (80, 60))
            for i in range(max_unlocked):
                label = f"{i+1}. {LEVELS[i].title}"
                col = (240, 240, 250) if i == selected_idx else (160, 160, 180)
                row = small.render(label, True, col)
                screen.blit(row, (120, 120 + i * 32))
            hint = small.render("UP/DOWN, ENTER to start, ESC back", True, (120, 120, 140))
            screen.blit(hint, (80, SCREEN_H - 80))
        elif mode == "play" and session is not None:
            mw = session.maze.width * TILE
            mh = session.maze.height * TILE
            ox = (SCREEN_W - mw) // 2
            oy = (SCREEN_H - mh) // 2 + 10

            draw_world(screen, session, (ox, oy))
            if session.buffs.see_through_remaining > 0:
                draw_ghost_silhouettes(screen, session, (ox, oy), 90)
            apply_lantern(screen, session, (ox, oy))

            if session.cfg.proximity_pulse and session.proximity > 0.65:
                pulse = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
                a = int(40 * session.proximity)
                pulse.fill((80, 0, 0, a))
                screen.blit(pulse, (0, 0))

            if session.jumpscare_remaining > 0:
                draw_jumpscare(screen, session)

            hud_y = 8
            hud = [
                f"Level {current_level} — {session.cfg.title}",
                f"Lives {session.lives}   Score {session.score}",
                f"Weapon CD: {session.weapon_cooldown:.1f}s" if session.weapon_cooldown > 0 else "Weapon: ready (SPACE)",
            ]
            if session.frightened_remaining > 0:
                hud.append(f"Flare: {session.frightened_remaining:.1f}s")
            for b in session.buffs.active_labels():
                hud.append(f"{b[0]}: {b[1]:.1f}s")
            if human_ghost:
                hud.append("P2 ghost: IJKL")
            for line in hud:
                surf = small.render(line, True, (210, 210, 220))
                screen.blit(surf, (12, hud_y))
                hud_y += 22
        elif mode in ("won", "lost"):
            overlay = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 170))
            screen.blit(overlay, (0, 0))
            t = font.render(end_text, True, (230, 230, 240))
            screen.blit(t, (SCREEN_W // 2 - t.get_width() // 2, SCREEN_H // 2 - 40))
            t2 = small.render("ENTER: continue", True, (180, 180, 200))
            screen.blit(t2, (SCREEN_W // 2 - t2.get_width() // 2, SCREEN_H // 2 + 20))
        pygame.display.flip()

    pygame.quit()
    sys.exit(0)


if __name__ == "__main__":
    main()

"""Default keyboard bindings (local multiplayer)."""

import pygame

# Survivor (wanderer)
SURVIVOR_UP = pygame.K_UP
SURVIVOR_DOWN = pygame.K_DOWN
SURVIVOR_LEFT = pygame.K_LEFT
SURVIVOR_RIGHT = pygame.K_RIGHT
SURVIVOR_WEAPON = pygame.K_SPACE

# Alternate WASD for survivor
SURVIVOR_W = pygame.K_w
SURVIVOR_A = pygame.K_a
SURVIVOR_S = pygame.K_s
SURVIVOR_D = pygame.K_d

# Ghost slot 0 (optional human) — IJKL
GHOST0_UP = pygame.K_i
GHOST0_DOWN = pygame.K_k
GHOST0_LEFT = pygame.K_j
GHOST0_RIGHT = pygame.K_l

# Ghost slot 1 — TFGH
GHOST1_UP = pygame.K_t
GHOST1_DOWN = pygame.K_g
GHOST1_LEFT = pygame.K_f
GHOST1_RIGHT = pygame.K_h

MENU_CONFIRM = pygame.K_RETURN
MENU_BACK = pygame.K_ESCAPE
MENU_PAUSE = pygame.K_p

from __future__ import annotations

import json
import math
import time
from dataclasses import dataclass, field

from .ghost_ai import chase_ghost_dirs
from .level_config import LevelConfig
from .mazes.level_data import Maze
from .powerups import BuffState
from .types import Dir, DOWN, LEFT, RIGHT, UP, PowerupKind
from . import weapon as weapon_mod


TILE = 32
PLAYER_R = 11
GHOST_R = 10
# Circle-vs-wall: 8 AABB samples; r>=4 can still snag near cell corners (all four dirs blocked).
GHOST_COLLIDE_R = 3
KILL_DIST = 20
WEAPON_WIDTH = 1  # line

_DEBUG_LOG = "debug-b8a7e1.log"
_SESSION = "b8a7e1"


@dataclass
class GameSession:
    cfg: LevelConfig
    maze: Maze
    tile: int = TILE

    player_px: float = 0.0
    player_py: float = 0.0
    player_dir: Dir = field(default=RIGHT)
    intent_dir: Dir | None = None

    ghost_px: list[float] = field(default_factory=list)
    ghost_py: list[float] = field(default_factory=list)
    ghost_dir: list[Dir] = field(default_factory=list)
    ghost_stun: list[float] = field(default_factory=list)
    ghost_banish: list[float] = field(default_factory=list)
    human_ghost_slots: set[int] = field(default_factory=set)

    pellets: set[tuple[int, int]] = field(default_factory=set)
    power_pellets: set[tuple[int, int]] = field(default_factory=set)
    powerups: dict[tuple[int, int], PowerupKind] = field(default_factory=dict)

    buffs: BuffState = field(default_factory=BuffState)
    frightened_remaining: float = 0.0
    weapon_cooldown: float = 0.0

    lives: int = 3  # overwritten in __post_init__ from cfg
    score: int = 0
    invuln_remaining: float = 0.0

    won: bool = False
    lost: bool = False

    proximity: float = 0.0  # 0..1 nearest ghost normalized

    jumpscare_remaining: float = 0.0
    jumpscare_ghost_index: int = 0
    jumpscare_stinger_pending: bool = False

    def __post_init__(self) -> None:
        sx, sy = self.maze.player_start
        self.player_px = (sx + 0.5) * self.tile
        self.player_py = (sy + 0.5) * self.tile
        self.pellets = set(self.maze.pellets)
        self.power_pellets = set(self.maze.power_pellets)
        self.powerups = dict(self.maze.powerups)

        starts = list(self.maze.ghost_starts)
        while len(starts) < self.cfg.ghost_count:
            starts.append(self.maze.ghost_starts[0] if self.maze.ghost_starts else (1, 1))
        starts = starts[: self.cfg.ghost_count]

        self.ghost_px = []
        self.ghost_py = []
        self.ghost_dir = []
        self.ghost_stun = []
        self.ghost_banish = []
        for gx, gy in starts:
            self.ghost_px.append((gx + 0.5) * self.tile)
            self.ghost_py.append((gy + 0.5) * self.tile)
            self.ghost_dir.append(LEFT)
            self.ghost_stun.append(0.0)
            self.ghost_banish.append(0.0)

        self.lives = self.cfg.lives

    @property
    def player_cell(self) -> tuple[int, int]:
        return int(self.player_px // self.tile), int(self.player_py // self.tile)

    @property
    def ghost_cells(self) -> list[tuple[int, int]]:
        return [
            (int(x // self.tile), int(y // self.tile))
            for x, y in zip(self.ghost_px, self.ghost_py, strict=True)
        ]

    def walkable_cell(self, cx: int, cy: int) -> bool:
        if cx < 0 or cy < 0 or cx >= self.maze.width or cy >= self.maze.height:
            return False
        return not self.maze.walls[cy][cx]

    def wall_at_pixel(self, px: float, py: float, radius: float) -> bool:
        offsets = (
            (-radius, -radius),
            (radius, -radius),
            (-radius, radius),
            (radius, radius),
            (0, -radius),
            (0, radius),
            (-radius, 0),
            (radius, 0),
        )
        for ox, oy in offsets:
            tx = int((px + ox) // self.tile)
            ty = int((py + oy) // self.tile)
            if tx < 0 or ty < 0 or tx >= self.maze.width or ty >= self.maze.height:
                return True
            if self.maze.walls[ty][tx]:
                return True
        return False

    def try_move(self, px: float, py: float, vx: float, vy: float, dt: float, radius: float) -> tuple[float, float]:
        if vx == 0 and vy == 0:
            return px, py
        nx = px + vx * dt
        if not self.wall_at_pixel(nx, py, radius):
            px = nx
        ny = py + vy * dt
        if not self.wall_at_pixel(px, ny, radius):
            py = ny
        return px, py

    def _ghost_nudge_toward_cell_center(self, ox: float, oy: float, dt: float) -> tuple[float, float]:
        """Pull ghost toward the center of its current tile so the circle hitbox does not snag on tile corners."""
        t = self.tile
        cx, cy = int(ox // t), int(oy // t)
        tcx = (cx + 0.5) * t
        tcy = (cy + 0.5) * t
        dx, dy = tcx - ox, tcy - oy
        dist = math.hypot(dx, dy)
        if dist < 0.75:
            return ox, oy
        speed = min(220.0, max(72.0, dist * 5.0))
        vx = (dx / dist) * speed
        vy = (dy / dist) * speed
        return self.try_move(ox, oy, vx, vy, dt, GHOST_COLLIDE_R)

    def tick(self, dt: float, keys: object, human_ghost_dirs: dict[int, Dir | None]) -> None:
        if self.won or self.lost:
            return

        if self.jumpscare_remaining > 0:
            self.jumpscare_remaining = max(0.0, self.jumpscare_remaining - dt)

        self.buffs.tick(dt)
        self.invuln_remaining = max(0.0, self.invuln_remaining - dt)
        self.weapon_cooldown = max(0.0, self.weapon_cooldown - dt)
        self.frightened_remaining = max(0.0, self.frightened_remaining - dt)

        for i in range(len(self.ghost_px)):
            self.ghost_stun[i] = max(0.0, self.ghost_stun[i] - dt)
            self.ghost_banish[i] = max(0.0, self.ghost_banish[i] - dt)

        # --- Player intent from keys ---
        from . import input_bindings as ib

        d = weapon_mod.dir_from_keys(keys)
        if d is not None:
            self.intent_dir = d
            self.player_dir = d

        if self.intent_dir is not None:
            self.player_dir = self.intent_dir

        dx, dy = self.player_dir.x, self.player_dir.y
        base = 150.0 * self.cfg.player_speed_mult * self.buffs.speed_mult
        cx, cy = self.player_cell
        if (cx, cy) in self.maze.slow:
            base *= 0.52
        vx, vy = float(dx) * base, float(dy) * base

        self.player_px, self.player_py = self.try_move(
            self.player_px, self.player_py, vx, vy, dt, PLAYER_R
        )

        # Teleporter
        cell = self.player_cell
        if cell in self.maze.teleporter_pair:
            tx, ty = self.maze.teleporter_pair[cell]
            self.player_px = (tx + 0.5) * self.tile
            self.player_py = (ty + 0.5) * self.tile

        # Pickups
        if cell in self.pellets:
            self.pellets.remove(cell)
            self.score += 10
        if cell in self.power_pellets:
            self.power_pellets.remove(cell)
            self.score += 50
            self.frightened_remaining = self.cfg.frightened_s
        if cell in self.powerups:
            kind = self.powerups.pop(cell)
            dur = {
                PowerupKind.SPEED: self.cfg.buff_speed_duration_s,
                PowerupKind.STRENGTH: self.cfg.buff_strength_duration_s,
                PowerupKind.SEE_THROUGH: self.cfg.buff_see_duration_s,
            }[kind]
            self.buffs.apply_pickup(kind, dur)
            self.score += 25

        if len(self.pellets) == 0 and len(self.power_pellets) == 0:
            self.won = True
            return

        # --- Weapon ---
        if keys[ib.SURVIVOR_WEAPON] and self.weapon_cooldown <= 0:
            rng = self.cfg.weapon_range_tiles + int(self.buffs.strength_range_bonus_tiles)
            stun = self.cfg.weapon_stun_s * self.buffs.strength_stun_mult
            hit = weapon_mod.raycast_hit_ghost_line(self, range_tiles=max(1, rng))
            self.weapon_cooldown = self.cfg.weapon_cooldown_s
            if hit is not None:
                self.ghost_stun[hit] = max(self.ghost_stun[hit], stun)
                self.score += 15

        # --- Ghosts ---
        g_speed = 128.0 * self.cfg.ghost_speed_mult
        if self.frightened_remaining > 0:
            g_speed *= 0.48

        nearest = 1.0
        for i in range(len(self.ghost_px)):
            if self.ghost_banish[i] > 0:
                gx, gy = self.maze.ghost_starts[i % len(self.maze.ghost_starts)]
                self.ghost_px[i] = (gx + 0.5) * self.tile
                self.ghost_py[i] = (gy + 0.5) * self.tile
                continue
            if self.ghost_stun[i] > 0:
                continue

            if i in self.human_ghost_slots and human_ghost_dirs.get(i) is not None:
                dirs_try = [human_ghost_dirs[i]]  # type: ignore[assignment]
            else:
                dirs_try = chase_ghost_dirs(self, i)

            ox, oy = self.ghost_px[i], self.ghost_py[i]
            ox, oy = self._ghost_nudge_toward_cell_center(ox, oy, dt)
            moved = False
            for gd in dirs_try:
                gvx, gvy = float(gd.x) * g_speed, float(gd.y) * g_speed
                npx, npy = self.try_move(ox, oy, gvx, gvy, dt, GHOST_COLLIDE_R)
                if (npx - ox) ** 2 + (npy - oy) ** 2 > 1e-8:
                    self.ghost_px[i] = npx
                    self.ghost_py[i] = npy
                    self.ghost_dir[i] = gd
                    moved = True
                    break
            if not moved:
                self.ghost_px[i] = ox
                self.ghost_py[i] = oy
                self.ghost_dir[i] = dirs_try[0]
                # #region agent log
                if len(dirs_try) > 1:
                    try:
                        payload = {
                            "sessionId": _SESSION,
                            "runId": "ghost-move",
                            "hypothesisId": "H1",
                            "location": "session.py:tick",
                            "message": "ghost_zero_displacement_all_candidates",
                            "data": {
                                "ghost_idx": i,
                                "candidate_dirs": len(dirs_try),
                                "gcx": int(ox // self.tile),
                                "gcy": int(oy // self.tile),
                                "collide_r": GHOST_COLLIDE_R,
                            },
                            "timestamp": int(time.time() * 1000),
                        }
                        with open(_DEBUG_LOG, "a", encoding="utf-8") as f:
                            f.write(json.dumps(payload) + "\n")
                    except OSError:
                        pass
                # #endregion

            gcell = (int(self.ghost_px[i] // self.tile), int(self.ghost_py[i] // self.tile))
            if gcell in self.maze.teleporter_pair:
                tx, ty = self.maze.teleporter_pair[gcell]
                self.ghost_px[i] = (tx + 0.5) * self.tile
                self.ghost_py[i] = (ty + 0.5) * self.tile

            dist = math.hypot(self.ghost_px[i] - self.player_px, self.ghost_py[i] - self.player_py)
            nearest = min(nearest, dist / (self.tile * 12))

        self.proximity = max(0.0, min(1.0, 1.0 - nearest))

        # Kill / collide
        if self.invuln_remaining <= 0:
            for i in range(len(self.ghost_px)):
                if self.ghost_banish[i] > 0 or self.ghost_stun[i] > 0:
                    continue
                if self.frightened_remaining > 0:
                    d = math.hypot(self.ghost_px[i] - self.player_px, self.ghost_py[i] - self.player_py)
                    if d < KILL_DIST:
                        self.ghost_banish[i] = 4.0
                        self.score += 200
                    continue
                d = math.hypot(self.ghost_px[i] - self.player_px, self.ghost_py[i] - self.player_py)
                if d < KILL_DIST:
                    self._life_lost(i)
                    break

    def _life_lost(self, ghost_index: int = 0) -> None:
        last_hit = self.lives <= 1
        self.lives -= 1
        self.jumpscare_ghost_index = ghost_index
        self.jumpscare_remaining = 0.72 if last_hit else 0.52
        self.jumpscare_stinger_pending = True
        self.invuln_remaining = 2.2
        sx, sy = self.maze.player_start
        self.player_px = (sx + 0.5) * self.tile
        self.player_py = (sy + 0.5) * self.tile
        for i in range(len(self.ghost_px)):
            gx, gy = self.maze.ghost_starts[i % len(self.maze.ghost_starts)]
            self.ghost_px[i] = (gx + 0.5) * self.tile
            self.ghost_py[i] = (gy + 0.5) * self.tile
        if self.lives <= 0:
            self.lost = True


def build_session(level_id: int, human_ghost_slots: set[int] | None = None) -> GameSession:
    from .level_config import get_level
    from .mazes.level_data import MAZE_BY_LEVEL

    cfg = get_level(level_id)
    maze = MAZE_BY_LEVEL[level_id]
    hs = human_ghost_slots or set()
    return GameSession(cfg=cfg, maze=maze, human_ghost_slots=hs)

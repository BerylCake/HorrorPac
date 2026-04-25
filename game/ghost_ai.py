from __future__ import annotations

from collections import deque

from .types import Dir, LEFT, RIGHT, DOWN, UP


def ranked_ghost_dirs(session: object, ghost_idx: int) -> list[Dir]:
    """All walkable directions from the ghost tile, best chase first (or flee if frightened).

    Deterministic ordering (no random shuffle) so ghosts commit to pursuit. Tie-break with
    pixel-space Manhattan to the center of the adjacent cell for smoother chasing.
    """
    px = session.player_px
    py = session.player_py
    gx = session.ghost_px[ghost_idx]
    gy = session.ghost_py[ghost_idx]
    tile = session.tile
    frightened = session.frightened_remaining > 0

    tcx, tcy = int(px // tile), int(py // tile)
    gcx, gcy = int(gx // tile), int(gy // tile)

    scored: list[tuple[tuple[float, float], Dir]] = []
    for d in (UP, DOWN, LEFT, RIGHT):
        nx, ny = gcx + d.x, gcy + d.y
        if not session.walkable_cell(nx, ny):
            continue
        cell_dist = float(abs(tcx - nx) + abs(tcy - ny))
        ncx = (nx + 0.5) * tile
        ncy = (ny + 0.5) * tile
        pixel_dist = abs(px - ncx) + abs(py - ncy)
        if frightened:
            key = (-cell_dist, -pixel_dist)
        else:
            key = (cell_dist, pixel_dist)
        scored.append((key, d))
    scored.sort(key=lambda t: t[0])
    if not scored:
        return [RIGHT]
    return [d for _, d in scored]


def _neighbors(session: object, cx: int, cy: int) -> list[tuple[int, int]]:
    out: list[tuple[int, int]] = []
    for d in (UP, DOWN, LEFT, RIGHT):
        nx, ny = cx + d.x, cy + d.y
        if session.walkable_cell(nx, ny):
            out.append((nx, ny))
    pair = session.maze.teleporter_pair.get((cx, cy))
    if pair is not None and session.walkable_cell(pair[0], pair[1]):
        if pair not in out:
            out.append(pair)
    return out


def bfs_first_direction(session: object, ghost_idx: int) -> Dir | None:
    """Next grid step on a shortest path from ghost cell to player cell (unweighted BFS)."""
    tile = session.tile
    gx = session.ghost_px[ghost_idx]
    gy = session.ghost_py[ghost_idx]
    gcx, gcy = int(gx // tile), int(gy // tile)
    tcx, tcy = int(session.player_px // tile), int(session.player_py // tile)

    if (gcx, gcy) == (tcx, tcy):
        return None

    start = (gcx, gcy)
    goal = (tcx, tcy)

    q = deque([start])
    came: dict[tuple[int, int], tuple[int, int] | None] = {start: None}

    while q:
        cx, cy = q.popleft()
        if (cx, cy) == goal:
            cur = goal
            while came[cur] != start:
                cur = came[cur]  # type: ignore[assignment]
            dx = cur[0] - start[0]
            dy = cur[1] - start[1]
            if dx == 1:
                return RIGHT
            if dx == -1:
                return LEFT
            if dy == 1:
                return DOWN
            if dy == -1:
                return UP
            return None
        for nx, ny in _neighbors(session, cx, cy):
            if (nx, ny) in came:
                continue
            came[(nx, ny)] = (cx, cy)
            q.append((nx, ny))
    return None


def chase_ghost_dirs(session: object, ghost_idx: int) -> list[Dir]:
    """Chase: shortest-path first step, then greedy ranked fallbacks for physics. Flee: greedy only."""
    ranked = ranked_ghost_dirs(session, ghost_idx)
    if session.frightened_remaining > 0:
        return ranked
    bfs = bfs_first_direction(session, ghost_idx)
    if bfs is None:
        return ranked
    out = [bfs]
    for d in ranked:
        if d is not bfs:
            out.append(d)
    return out


def pick_ghost_dir(session: object, ghost_idx: int) -> Dir:
    """Greedy: move toward player (or away if frightened)."""
    return ranked_ghost_dirs(session, ghost_idx)[0]

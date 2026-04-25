from __future__ import annotations

import json
import time
from collections import deque
from dataclasses import dataclass

from ..types import PowerupKind

_DEBUG_LOG = "debug-b8a7e1.log"
_SESSION = "b8a7e1"


def _agent_log(
    message: str,
    data: dict,
    location: str,
    hypothesis_id: str,
    run_id: str = "pre-fix",
) -> None:
    # #region agent log
    try:
        payload = {
            "sessionId": _SESSION,
            "runId": run_id,
            "hypothesisId": hypothesis_id,
            "location": location,
            "message": message,
            "data": data,
            "timestamp": int(time.time() * 1000),
        }
        with open(_DEBUG_LOG, "a", encoding="utf-8") as f:
            f.write(json.dumps(payload) + "\n")
    except OSError:
        pass

    # #endregion


def _reachable_floor(maze: Maze) -> set[tuple[int, int]]:
    sx, sy = maze.player_start
    if maze.walls[sy][sx]:
        return set()
    q = deque([(sx, sy)])
    seen: set[tuple[int, int]] = {q[0]}
    while q:
        x, y = q.popleft()
        for dx, dy in ((0, 1), (0, -1), (1, 0), (-1, 0)):
            nx, ny = x + dx, y + dy
            if nx < 0 or ny < 0 or nx >= maze.width or ny >= maze.height:
                continue
            if maze.walls[ny][nx]:
                continue
            if (nx, ny) in seen:
                continue
            seen.add((nx, ny))
            q.append((nx, ny))
        if (x, y) in maze.teleporter_pair:
            tx, ty = maze.teleporter_pair[(x, y)]
            if (tx, ty) not in seen:
                seen.add((tx, ty))
                q.append((tx, ty))
    return seen


def _normalize_row_widths(lines: list[str]) -> list[str]:
    """Pad short rows to max width so ljust does not create border gaps or skew."""
    w = max(len(r) for r in lines)
    out: list[str] = []
    for row in lines:
        if len(row) >= w:
            out.append(row)
            continue
        gap = w - len(row)
        if len(row) >= 2 and row[0] == "#" and row[-1] == "#":
            mid = row[1:-1]
            if mid and all(c == "#" for c in mid):
                out.append(row + "#" * gap)
            else:
                out.append(row[:-1] + "." * gap + "#")
        else:
            out.append(row + "#" * gap)
    return out


def _prune_unreachable_collectibles(maze: Maze, level_id: int | None = None) -> None:
    floor = _reachable_floor(maze)
    bad_p = sorted(p for p in maze.pellets if p not in floor)
    bad_o = sorted(p for p in maze.power_pellets if p not in floor)
    bad_u = sorted(p for p in maze.powerups if p not in floor)
    # #region agent log
    _agent_log(
        "reachability_before_prune",
        {
            "level_id": level_id,
            "unreachable_pellets": bad_p,
            "unreachable_power_pellets": bad_o,
            "unreachable_powerups": [(list(t), maze.powerups[t].name) for t in bad_u],
            "player_start": list(maze.player_start),
            "width_height": [maze.width, maze.height],
        },
        "level_data.py:_prune_unreachable_collectibles",
        "H1",
        run_id="pre-fix",
    )
    # #endregion
    for p in bad_p:
        maze.pellets.discard(p)
    for p in bad_o:
        maze.power_pellets.discard(p)
    for p in bad_u:
        maze.powerups.pop(p, None)
    # #region agent log
    _agent_log(
        "reachability_after_prune",
        {
            "level_id": level_id,
            "removed_pellet_count": len(bad_p),
            "removed_power_pellet_count": len(bad_o),
            "removed_powerup_count": len(bad_u),
        },
        "level_data.py:_prune_unreachable_collectibles",
        "H1",
        run_id="post-fix",
    )
    # #endregion


@dataclass
class Maze:
    width: int
    height: int
    walls: list[list[bool]]
    pellets: set[tuple[int, int]]
    power_pellets: set[tuple[int, int]]
    powerups: dict[tuple[int, int], PowerupKind]
    slow: set[tuple[int, int]]
    teleporter_pair: dict[tuple[int, int], tuple[int, int]]
    player_start: tuple[int, int]
    ghost_starts: list[tuple[int, int]]


def parse_maze(lines: list[str], level_id: int | None = None) -> Maze:
    """Parse ASCII maze. See module docstring in level_config for legend."""
    lines = _normalize_row_widths(lines)
    h = len(lines)
    w = max(len(row) for row in lines)
    padded = [row.ljust(w) for row in lines]
    walls = [[False] * w for _ in range(h)]
    pellets: set[tuple[int, int]] = set()
    power_pellets: set[tuple[int, int]] = set()
    powerups: dict[tuple[int, int], PowerupKind] = {}
    slow: set[tuple[int, int]] = set()
    tp_markers: dict[tuple[int, int], str] = {}
    player_start = (1, 1)
    ghost_starts: list[tuple[int, int]] = []

    for y, row in enumerate(padded):
        for x, ch in enumerate(row):
            if ch == "#" or ch == "█":
                walls[y][x] = True
            elif ch == " ":
                pass
            elif ch == ".":
                pellets.add((x, y))
            elif ch == "o":
                power_pellets.add((x, y))
            elif ch == "~":
                slow.add((x, y))
            elif ch == "*":
                powerups[(x, y)] = PowerupKind.SPEED
            elif ch == "+":
                powerups[(x, y)] = PowerupKind.STRENGTH
            elif ch == "=":
                powerups[(x, y)] = PowerupKind.SEE_THROUGH
            elif ch == "S":
                player_start = (x, y)
            elif ch == "G":
                ghost_starts.append((x, y))
            elif ch in "123456789":
                tp_markers[(x, y)] = ch
            else:
                walls[y][x] = True

    teleporter_pair: dict[tuple[int, int], tuple[int, int]] = {}
    groups: dict[str, list[tuple[int, int]]] = {}
    for pos, mark in tp_markers.items():
        groups.setdefault(mark, []).append(pos)
    for _mark, cells in groups.items():
        if len(cells) == 2:
            teleporter_pair[cells[0]] = cells[1]
            teleporter_pair[cells[1]] = cells[0]

    maze = Maze(
        width=w,
        height=h,
        walls=walls,
        pellets=pellets,
        power_pellets=power_pellets,
        powerups=powerups,
        slow=slow,
        teleporter_pair=teleporter_pair,
        player_start=player_start,
        ghost_starts=ghost_starts,
    )
    _prune_unreachable_collectibles(maze, level_id=level_id)
    return maze


def _lvl(n: int, rows: list[str]) -> tuple[int, list[str]]:
    return n, rows


# --- 10 authored mazes (roughly easy → hard by size + chokepoints) ---

RAW: dict[int, list[str]] = {}

RAW[1] = [
    "####################",
    "#S......*..........#",
    "#.####.####.####.#.#",
    "#.#..+...=....o..#.#",
    "#.#.##.##.##.##.#.#.#",
    "#.......G...G......#",
    "####################",
]

RAW[2] = [
    "######################",
    "#S...*.....o.........#",
    "#.##.#.##.#.##.#.##.#.#",
    "#.#..+..#...#..=..#..#",
    "#.#.##.##.#.##.##.#.#.#",
    "#.......G......G.....#",
    "######################",
]

RAW[3] = [
    "########################",
    "#S.*...o...........+...#",
    "#.##.##.##.##.##.##.##.#",
    "#.#...#....~....#...=..#",
    "#.#.#.#.##G##.#.#.#.#.#.#",
    "#...#...#...#...#...G..#",
    "########################",
]

RAW[4] = [
    "##########################",
    "#S..*...o......=.........#",
    "#.##.#.##.#.##.#.##.#.##.#",
    "#.#..+..#..~#..*..#..o..#",
    "#.#.##.##.#G#.#.##.##.#.#",
    "#.......G.....G.........#",
    "#.#########.#########.##.#",
    "#........................#",
    "##########################",
]

RAW[5] = [
    "############################",
    "#S.*...o..~....+...........#",
    "#.##.##.##.##.##.##.##.##.#",
    "#.#...=...#....*...#...o..#",
    "#.#.#G#.#.#.#G#.#.#.#.#.#.#",
    "#...#...#...#...#...#...G..#",
    "#.###########.###########.#",
    "#..........................#",
    "############################",
]

RAW[6] = [
    "##############################",
    "#S..*...o..~..=..+...........#",
    "#.##.##.##.##.##.##.##.##.##.#",
    "#.#...#...#...#...#...#...*..#",
    "#.#.#.#.#.#.#.#.#.#.#.#.#.#.#.#",
    "#...G...G...G...G...G...G.....#",
    "#.#####.#.#.#.#.#.#.#####.#.#.#",
    "#............................#",
    "##############################",
]

RAW[7] = [
    "################################",
    "#S.*..o..~..+..=..*............#",
    "#..#..#..#..#..#..#..#..#..#..#.#",
    "#.#...#...#...#...#...#...#....#",
    "#.#.#.#.#.#.#G#.#.#.#.#.#.#.#.#.#",
    "#...#...#...#...#...#...#...G...#",
    "#.#########.#.#.#.#.#########.#.#",
    "#...........#...#.............#",
    "################################",
]

RAW[8] = [
    "##################################",
    "#S..*..o..~..+..=..*..o..........#",
    "#..#..#..#..#..#..#..#..#..#..#..#.#",
    "#.#...#...#...#...#...#...#...#...#",
    "#.#.#.#.#.#.#.#G#.#.#.#.#.#.#.#.#.#",
    "#...G...#...#...#...#...#...G...G..#",
    "#.#####.#.#.#.#.#.#.#.#.#####.#.#.#",
    "#.......#...#...#...#...........#",
    "##################################",
]

RAW[9] = [
    "####################################",
    "#S.*.o.~.+.=.*....................#",
    "#..#..#..#..#..#..#..#..#..#..#..#.#",
    "#.#...#...#...#...#...#...#...#....#",
    "#.#.#.#.#.#.#G#.#.#.#.#.#.#.#.#.#.#.#",
    "#...#...G...#...#...G...#...G...G...#",
    "#.###.#.#.#.#.#.#.#.#.#.#.#.###.#.#.#",
    "#.....#...#...#...#...#...#.....#...#",
    "####################################",
]

RAW[10] = [
    "######################################",
    "#S*o~+=.*o...........................#",
    "#..#..#..#..#..#..#..#..#..#..#..#..#..#.#",
    "#.#...#...#...#...#...#...#...#...#..#",
    "#.#.#.#.#.#.#G#.#.#.#.#.#.#.#.#.#.#.#.#",
    "#...G...#...#...#...#...G...#...G...G..#",
    "#.###.#.#.#.#.#.#.#.#.#.#.#.#.###.#.#.#",
    "#.....#...#...#...#...#...#.....#.....#",
    "#.#####.#.#.#.#.#.#.#.#.#.#####.#.#.#.#",
    "#..................................#",
    "######################################",
]

MAZE_BY_LEVEL: dict[int, Maze] = {i: parse_maze(RAW[i], level_id=i) for i in range(1, 11)}

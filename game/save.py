from __future__ import annotations

import json
from pathlib import Path

SAVE_FILENAME = "save.json"


def save_path(root: Path | None = None) -> Path:
    base = root if root is not None else Path(__file__).resolve().parent.parent
    return base / SAVE_FILENAME


def load_max_unlocked(root: Path | None = None) -> int:
    p = save_path(root)
    if not p.is_file():
        return 1
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
        return max(1, min(10, int(data.get("max_unlocked", 1))))
    except (json.JSONDecodeError, OSError, TypeError, ValueError):
        return 1


def save_max_unlocked(level: int, root: Path | None = None) -> None:
    level = max(1, min(10, int(level)))
    p = save_path(root)
    payload = {"max_unlocked": level}
    p.write_text(json.dumps(payload, indent=2), encoding="utf-8")

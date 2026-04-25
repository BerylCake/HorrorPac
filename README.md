# Horror Maze (`csstd26`)

A Python + Pygame horror maze game where you play as a survivor, collect pellets/powerups, avoid ghosts, and clear progressively harder floors.

## Project Summary

This project includes:

- Multi-level maze gameplay with authored maps (`game/mazes/level_data.py`)
- Survivor movement, collisions, score/lives, buffs, and weapon cooldown (`game/session.py`)
- Ghost AI with chase behavior and maze-aware movement (`game/ghost_ai.py`)
- Horror-style rendering: lantern darkness, proximity pulse, jumpscare visuals/audio
- Menu/level flow and game loop entry point (`main.py`)

Key folders/files:

- `main.py` - starts and runs the game loop
- `game/session.py` - core game state and per-frame logic
- `game/ghost_ai.py` - ghost path/chase decision logic
- `game/render.py`, `game/characters.py`, `game/jumpscare_render.py` - visuals/effects
- `game/mazes/level_data.py` - level layouts
- `requirements.txt` - Python dependencies

---

## Complete Step-by-Step Installation Guide (Windows)

## 1) Prerequisites

1. Install **Python 3.11+**.
2. During install, enable **Add Python to PATH**.
3. Verify:
   - `python --version`
   - `pip --version`

Optional but recommended:

- Install **Git for Windows** and verify with `git --version`.

---

## 2) Get the project

If you already have this folder, skip cloning.

```powershell
cd "c:\Users\codes\OneDrive\Documents\project\csstd26"
```

---

## 3) Create a virtual environment

From the project root:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

If activation is blocked:

```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```

---

## 4) Install dependencies

```powershell
pip install -r requirements.txt
```

Current required package:

- `pygame>=2.5.0`

---

## 5) (Optional) Run tests

```powershell
python -m pytest tests -q
```

If `pytest` is not installed:

```powershell
pip install pytest
python -m pytest tests -q
```

---

## 6) Run the game

```powershell
python main.py
```

The Pygame window should open. If you do not see it, check the taskbar (it may be behind other windows).

---

## 7) Controls (default)

- `Enter` - confirm / start
- `Esc` - back / menu
- `Space` - survivor weapon
- `H` - toggle human-controlled ghost mode
- Human ghost controls (when enabled): `I`, `J`, `K`, `L`

---

## 8) Create SSH key (for GitHub/GitLab)

## A. Generate key

```powershell
ssh-keygen -t ed25519 -f "$HOME\.ssh\id_ed25519" -C "your_email@example.com"
```

Choose a passphrase (recommended) or press Enter for none.

## B. Start agent and add key

```powershell
Get-Service ssh-agent | Set-Service -StartupType Automatic
Start-Service ssh-agent
ssh-add "$HOME\.ssh\id_ed25519"
```

## C. Copy public key

```powershell
Get-Content "$HOME\.ssh\id_ed25519.pub"
```

Copy the full `ssh-ed25519 ...` line.

## D. Add key to provider

- GitHub: Settings -> SSH and GPG keys -> New SSH key
- GitLab: Preferences -> SSH Keys

## E. Test SSH login

```powershell
ssh -T git@github.com
```

Or for GitLab:

```powershell
ssh -T git@gitlab.com
```

## F. Set repo remote to SSH

```powershell
git remote -v
git remote set-url origin git@github.com:<username>/<repo>.git
```

---

## 9) Git identity setup (if needed)

```powershell
git config --global user.name "Your Name"
git config --global user.email "your_email@example.com"
git config --global --list
```

---

## 10) Troubleshooting

- **`python` not found**: reinstall Python and ensure PATH option is enabled.
- **Pygame import error**: run `pip install -r requirements.txt` in the active venv.
- **Window opens then closes**: run `python main.py` from PowerShell and check error text.
- **SSH permission denied**: ensure key is added with `ssh-add` and public key is added to your Git provider.


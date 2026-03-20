# Legend of the Red Dragon: 16-Bit Edition

## What Is This?
A single-player SNES-style JRPG built with Python + Pygame, based on the classic 1989 BBS door game "Legend of the Red Dragon" (LORD) by Seth Able Robinson. It features procedurally generated pixel art, turn-based combat, and a retro aesthetic.

## Tech Stack
- **Language**: Python 3.11+
- **Framework**: Pygame 2.6+
- **Platform**: Cross-platform (developed on macOS ARM)
- **Assets**: All sprites, tiles, and music are procedurally generated at runtime (no external asset files)

## Virtual Resolution
- 320x240 virtual canvas, upscaled to display size
- Supports fullscreen via F11 or Alt+Enter using `pygame.FULLSCREEN | pygame.SCALED`

## Project Structure
```
main.py              - Game entry point, loop, fullscreen toggle, music hookup
settings.py          - All constants: colors, screen size, level tables, paths
pyproject.toml       - Project metadata and Pyright config

scenes/              - Scene system (each screen is a Scene subclass)
  scene_manager.py   - SceneManager with fade transitions
  title_screen.py    - Title screen with dragon sprite and parallax
  char_create.py     - Character creation (name + class selection)
  town.py            - Town of Pinnacle — top-down walkable map
  forest.py          - Mystic Forest exploration with fog/fireflies
  battle.py          - Turn-based combat with full animation system
  load_game.py       - Save/load screen

systems/             - Core game systems
  player.py          - Player class: stats, equipment, leveling, serialization
  enemy.py           - 12 enemy types across 3 zones, AI, loot drops
  inventory.py       - Material tiers, weapons, armour, crafting recipes
  sprites.py         - Procedural SNES-quality sprite generator
  music.py           - Procedural chiptune music engine
  save_load.py       - JSON save/load to saves/ directory

ui/                  - UI components
  menu.py            - SelectionMenu, DialogueBox, draw_text, draw_menu_box
  hud.py             - Player HUD overlay (HP/MP bars, gold, level)

assets/              - Directory structure for assets (mostly empty, music/sfx generated at runtime)
saves/               - Save game files (JSON)
```

## Key Design Decisions
1. **No external assets** — everything is procedurally generated for easy distribution
2. **Dual coordinate system** in town — tile-based logical positions + pixel-based smooth visual positions
3. **Animation sequencer** in battle — keyframe system with easing curves for FF4/FF6-style combat animations
4. **Material tier system** — 7 tiers (Wood through Void) with multiplier-based stat scaling
5. **Side profile sprites** — left-facing sprites are horizontally flipped right-facing sprites (classic SNES technique)

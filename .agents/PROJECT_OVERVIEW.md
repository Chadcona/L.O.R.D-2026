# Legend of the Red Dragon: 16-Bit Edition

## What Is This?
A single-player SNES-style JRPG built with Python + Pygame, based on the classic 1989 BBS door game "Legend of the Red Dragon" (LORD) by Seth Able Robinson. It features hand-drawn sprite sheet characters, procedurally generated pixel art for enemies/tiles/music, and a retro aesthetic.

## Tech Stack
- **Language**: Python 3.11+
- **Framework**: Pygame 2.6+
- **Platform**: Cross-platform
- **Assets**: External sprite sheet for characters (`assets/sprites/characters.png`), procedural generation for enemies, tiles, and music

## Display
- Native 1920×1080 rendering (virtual resolution = screen resolution, no upscaling)
- Default window: 1920×1080, resizable
- Fullscreen via F11 or Alt+Enter using `pygame.FULLSCREEN | pygame.SCALED`

## Project Structure
```
main.py              - Game entry point, loop, fullscreen toggle, music hookup
settings.py          - All constants: colors, screen size, tile size, sprite regions, level tables, paths
pyproject.toml       - Project metadata and Pyright config

scenes/              - Scene system (each screen is a Scene subclass)
  scene_manager.py   - SceneManager with fade transitions
  title_screen.py    - Title screen with dragon sprite and parallax
  char_create.py     - Character creation (name + class selection)
  town.py            - Town of Pinnacle — top-down walkable map with camera scroll
  forest.py          - Mystic Forest exploration with fog/fireflies
  battle.py          - Turn-based combat with full animation system
  load_game.py       - Save/load screen

systems/             - Core game systems
  player.py          - Player class: stats, equipment, leveling, serialization
  enemy.py           - 12 enemy types across 3 zones, AI, loot drops
  inventory.py       - Material tiers, weapons, armour, crafting recipes
  sprites.py         - Sprite sheet loader + procedural fallback sprite generator
  music.py           - Procedural chiptune music engine
  save_load.py       - JSON save/load to saves/ directory

ui/                  - UI components
  menu.py            - SelectionMenu, DialogueBox, draw_text, draw_menu_box
  hud.py             - Player HUD overlay (HP/MP bars, gold, level)

assets/sprites/      - External sprite sheet (characters.png)
saves/               - Save game files (JSON)
```

## Key Design Decisions
1. **External sprite sheet** — 2816×1536 character sheet with auto-detected bounding regions per class/pose, colorkey transparency for cream background
2. **Procedural fallback** — if no sprite sheet exists, procedural pixel art sprites are generated
3. **Native 1080p** — renders directly at 1920×1080 (no virtual screen upscaling)
4. **Camera scrolling** in town — 20×15 tile map at 96px tiles (1920×1440 total), viewport follows player
5. **Dual coordinate system** in town — tile-based logical positions + pixel-based smooth visual positions
6. **Animation sequencer** in battle — keyframe system with easing curves for FF4/FF6-style combat animations
7. **Material tier system** — 7 tiers (Wood through Void) with multiplier-based stat scaling

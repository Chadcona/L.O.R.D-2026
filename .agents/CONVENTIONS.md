# Code Conventions

## General
- Python 3.11+, no type annotations (Pyright gives false positives on pygame/dict code)
- Pygame 2.6+ as sole dependency
- Per-class sprite sheets for characters/NPCs, procedural generation for enemies/tiles/music
- `pyproject.toml` has `extraPaths = ["."]` for IDE module resolution

## Naming
- Scene classes: `TitleScreen`, `TownScene`, `BattleScene`, `ForestScene`
- System files: lowercase modules in `systems/` (`player.py`, `enemy.py`, etc.)
- Constants: UPPER_SNAKE_CASE in `settings.py`
- Private methods: `_method_name` prefix
- Cache variables: `_sprite_cache`, `_tile_cache`, `_forest_bg_cache`, `_sheet_cache`

## Patterns
- Scenes receive data via `on_enter(data)` dict — always pass `{"player": player_obj}`
- Equipment stored as plain dicts: `{"name": ..., "atk": ..., "tier": ..., "type": ..., "special": ...}`
- Items stacked by count: `{"name": "Potion", "type": "consumable", "count": 3}`
- Lazy initialization: sprites cached on first access, music built on first play
- Local imports inside methods for optional dependencies (e.g., `from systems.inventory import ...`)

## Display & Sprites
- Native resolution: 1920×1080 (virtual = screen, no upscaling)
- Player sprites: 80×120 pixels (overworld), 192×288 (battle)
- Enemy sprites: 288×288 pixels (battle)
- Tiles: 96×96 pixels (town), procedural 16×16 scaled up at render
- Per-class sprite sheets: 2816×1536 PNGs in `assets/sprites/`
  - `CLASS_SPRITE_SHEETS` and `NPC_SPRITE_SHEETS` map names to paths
  - Walk frame X positions defined in `SHEET_WALK_X` (exact bounding boxes)
  - Row Y ranges defined in `SHEET_ROW_Y`
- Background removal: auto-detected per sheet, proximity-based (RADIUS=3)
- Sheets with alpha transparency bypass background removal
- Font sizes: SM=24, MD=36, LG=48, XL=72, TITLE=96

## Common Gotchas
- IDE diagnostics are almost all false positives — the type checker can't handle pygame's untyped dict values
- `switch_to()` does a fade transition (needs multiple update cycles); use `switch_immediate()` for tests
- Enemy turn in battle is triggered by animation chain callbacks, NOT by USEREVENT timer
- Walk animations use `frame % 4` — sheets have 4 frames per direction half-row
- `pygame.init()` pre-initializes mixer at 44100 Hz — MusicManager must `pygame.mixer.quit()` first then reinit at 22050 Hz, otherwise samples play at 2x speed
- SDL may force stereo even when mono is requested — `_samples_to_sound` duplicates L+R channels
- Town map is 1920×1440 (larger than viewport) — camera scrolls to follow player
- Procedural tiles are generated at 16×16 and scaled to TILE_SIZE (96) at render time
- Sprite sheet BG color varies per sheet (white, grey, dark grey) — auto-detected from corners
- First sprite load takes ~5s (96 sprites with BG removal); all cached after that

# Code Conventions

## General
- Python 3.11+, no type annotations (Pyright gives false positives on pygame/dict code)
- Pygame 2.6+ as sole dependency
- All assets procedurally generated — no external files to load
- `pyproject.toml` has `extraPaths = ["."]` for IDE module resolution

## Naming
- Scene classes: `TitleScreen`, `TownScene`, `BattleScene`, `ForestScene`
- System files: lowercase modules in `systems/` (`player.py`, `enemy.py`, etc.)
- Constants: UPPER_SNAKE_CASE in `settings.py`
- Private methods: `_method_name` prefix
- Cache variables: `_sprite_cache`, `_tile_cache`, `_forest_bg_cache`

## Patterns
- Scenes receive data via `on_enter(data)` dict — always pass `{"player": player_obj}`
- Equipment stored as plain dicts: `{"name": ..., "atk": ..., "tier": ..., "type": ..., "special": ...}`
- Items stacked by count: `{"name": "Potion", "type": "consumable", "count": 3}`
- Lazy initialization: sprites cached on first access, music built on first play
- Local imports inside methods for optional dependencies (e.g., `from systems.inventory import ...`)

## Pixel Art
- Virtual resolution: 320x240 (SNES standard)
- Player sprites: 16x24 pixels
- Enemy sprites: 48x48 pixels
- Tiles: 16x16 pixels
- Color palette: SNES-style with highlight/mid/shadow per material
- `_px(surface, x, y, color)` helper for bounds-checked pixel placement

## Common Gotchas
- IDE diagnostics are almost all false positives — the type checker can't handle pygame's untyped dict values or module resolution without virtualenv
- `switch_to()` does a fade transition (needs multiple update cycles); use `switch_immediate()` for tests
- Enemy turn in battle is triggered by animation chain callbacks, NOT by USEREVENT timer
- Left-facing sprites are horizontally flipped right-facing sprites
- `pygame.init()` pre-initializes mixer at 44100 Hz — MusicManager must `pygame.mixer.quit()` first then reinit at 22050 Hz, otherwise samples play at 2x speed
- Music scene mapping uses a dict in main.py — add new scenes there or they get `music.stop()`

# Architecture Guide

## Scene System
All game screens extend `Scene` (in `scenes/scene_manager.py`):
- `on_enter(data)` — called when scene becomes active, receives data dict
- `on_exit()` — cleanup when leaving
- `update(dt)` — game logic per frame (dt in seconds)
- `handle_event(event)` — pygame event handling
- `draw(surface)` — render to virtual screen (1920×1080)

SceneManager handles transitions with optional fade effects:
- `switch_to(name, data)` — fade out, switch, fade in
- `switch_immediate(name, data)` — instant switch

## Player System (`systems/player.py`)
- 3 classes: Warrior (STR/DEF), Thief (AGI/LCK), Mage (INT/MP)
- Stats: hp, mp, str, defense, agi, int, lck
- Equipment: `weapon` dict with name/atk/special/tier/type, `armour` dict similarly
- Inventory: list of item dicts with `count` stacking
- Serialization: `to_dict()` / `from_dict()` for JSON saves

## Combat System (`scenes/battle.py`)
- Turn-based: player_turn -> animating -> enemy_turn -> back to player
- `BattleAnim` class: keyframe sequencer with animated properties
- Animation chain: action -> anim plays -> callback -> check death -> next turn
- Enemy death: death animation -> victory state -> rewards + loot drops
- Player home position: (1440, 450), Enemy home: (300, 430)
- Battle sprites: player 192×288, enemy 288×288

## Inventory & Crafting (`systems/inventory.py`)
- 7 material tiers: Wood, Copper, Iron, Steel, Enchanted, Dragon, Void
- `make_weapon(type, tier)` / `make_armour(type, tier)` generate equipment
- Crafting: material + gold -> upgrade to next tier at the Blacksmith
- Enemies drop materials based on their zone (shallow/deep/shadow)

## Sprite System (`systems/sprites.py`)
- **Per-class sheets**: each class/NPC has its own 2816×1536 PNG
  - `CLASS_SPRITE_SHEETS` maps class names to file paths
  - `NPC_SPRITE_SHEETS` maps NPC names (Seth, Violet, Cat) to file paths
- **Sheet layout**: all sheets share the same grid structure
  - Row 1 (y=165-375): walk front (cells 0-3) + walk back (cells 4+)
  - Row 2 (y=438-715): walk left (cells 0-3) + walk right (cells 4+)
  - Row 3 (y=845-1090): idle animation
  - Row 4 (y=1170-1490): combat sequence
  - Exact X bounding boxes per frame defined in `SHEET_WALK_X`
- **Background removal**: auto-detects BG color per sheet from corner pixels
  - Color distance threshold (dist² < 2500) + desaturation check
  - Proximity-based preservation: bg pixels within 3px of sprite content are kept (preserves white clothing)
  - Sheets with true alpha transparency skip removal entirely
- **Caching**: all sprites cached on first access via `_sprite_cache`
- **Procedural fallback**: `create_player_sprite()` if no sheet available
- Enemy sprites and tiles still procedurally generated

## Music System (`systems/music.py`)
- Procedural chiptune generated from note sequences at runtime
- Wave types: square, triangle, sawtooth, sine, noise
- Drum synthesis: kick (sine sweep), snare (noise burst), hi-hat
- Full chromatic note frequency table (C3-B5 with all sharps/flats)
- BPM parameterized per track (town = 100 BPM, others = 130 BPM)
- MusicManager: quits pre-existing mixer to force correct sample rate (22050 Hz)
- Stereo fix: `_samples_to_sound` duplicates mono samples to L+R when mixer is stereo

## Town (`scenes/town.py`)
- 20×15 tile map at 96px per tile (1920×1440 total map size)
- Camera scrolling: viewport (1920×1080) follows player, clamped to map bounds
- Smooth pixel movement at 384px/s with walk animation
- 6 locations: Inn, Pub, Weapon Shop, Armour Shop, Blacksmith, Forest Gate
- Procedural tiles scaled from 16×16 to 96×96 at render time
- NPC wanderers: Seth, Violet, Cat — each using dedicated sprite sheets with walk cycles

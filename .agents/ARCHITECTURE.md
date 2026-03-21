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
- External sprite sheet: loads from `assets/sprites/characters.png`
- `SPRITE_SHEET_REGIONS` in settings.py defines (x, y, w, h) per class/facing
- Colorkey transparency removes cream background (255, 250, 219)
- Sprites scaled to `PLAYER_SPRITE_W×PLAYER_SPRITE_H` (80×120) for overworld
- Battle scene scales further to `BATTLE_SPRITE_W×BATTLE_SPRITE_H` (192×288)
- Procedural fallback via `create_player_sprite()` if sheet unavailable
- Enemy sprites and tiles still procedurally generated
- All sprites cached via `get_player_sprite()` / `get_enemy_sprite()`

## Music System (`systems/music.py`)
- Procedural chiptune generated from note sequences at runtime
- Wave types: square, triangle, sawtooth, sine, noise
- Drum synthesis: kick (sine sweep), snare (noise burst), hi-hat
- Full chromatic note frequency table (C3-B5 with all sharps/flats)
- BPM parameterized per track (town = 100 BPM, others = 130 BPM)
- MusicManager: quits pre-existing mixer to force correct sample rate (22050 Hz)

## Town (`scenes/town.py`)
- 20×15 tile map at 96px per tile (1920×1440 total map size)
- Camera scrolling: viewport (1920×1080) follows player, clamped to map bounds
- Smooth pixel movement at 384px/s with walk animation
- 6 locations: Inn, Pub, Weapon Shop, Armour Shop, Blacksmith, Forest Gate
- Procedural tiles scaled from 16×16 to 96×96 at render time
- NPC wanderers with pathfinding

# Architecture Guide

## Scene System
All game screens extend `Scene` (in `scenes/scene_manager.py`):
- `on_enter(data)` — called when scene becomes active, receives data dict
- `on_exit()` — cleanup when leaving
- `update(dt)` — game logic per frame (dt in seconds)
- `handle_event(event)` — pygame event handling
- `draw(surface)` — render to virtual screen (320x240)

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

## Inventory & Crafting (`systems/inventory.py`)
- 7 material tiers: Wood, Copper, Iron, Steel, Enchanted, Dragon, Void
- `make_weapon(type, tier)` / `make_armour(type, tier)` generate equipment
- Crafting: material + gold -> upgrade to next tier at the Blacksmith
- Enemies drop materials based on their zone (shallow/deep/shadow)

## Sprite System (`systems/sprites.py`)
- `create_player_sprite(class, facing, frame, hair)` -> 16x24 Surface
- 4 facings: down/up use front/back view, left/right use true side profiles
- `create_enemy_sprite(name, color, size)` -> 48x48 with type-specific drawers
- Tile generators: grass, path, wall, water, door, tree
- All sprites cached via `get_player_sprite()` / `get_enemy_sprite()`

## Music System (`systems/music.py`)
- Procedural chiptune generated from note sequences at runtime
- Wave types: square, triangle, sawtooth, sine, noise
- Drum synthesis: kick (sine sweep), snare (noise burst), hi-hat
- Full chromatic note frequency table (C3-B5 with all sharps/flats)
- BPM parameterized per track (town = 100 BPM, others = 130 BPM)
- Town theme: C#-A-F#-Ab chord progression with boom bap drums
- MusicManager: quits pre-existing mixer to force correct sample rate (22050 Hz), lazily builds tracks, loops playback per scene
- Scene-to-track mapping in main.py via dict lookup with fallback stop

## Town (`scenes/town.py`)
- 20x15 tile map at 16x16 pixels per tile
- Smooth pixel movement at 64px/s with walk animation
- 6 locations: Inn, Pub, Weapon Shop, Armour Shop, Blacksmith, Forest Gate
- Visual details: hanging signs with icons, chimneys with smoke, lanterns, barrels, crates, well
- NPC wanderers with pathfinding

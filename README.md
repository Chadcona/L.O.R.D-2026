# Legend of the Red Dragon: 16-Bit Edition

A single-player SNES-style JRPG built with Python and Pygame, inspired by the classic 1989 BBS door game **Legend of the Red Dragon** by Seth Able Robinson.

## Features

### Graphics
- Native 1080p rendering with hand-drawn sprite sheet characters
- External sprite sheet support (Warrior, Rogue/Thief, Cleric, Mage) with auto-detected regions and transparent backgrounds
- Procedural pixel art fallback for enemies, tiles, and environmental details
- Smooth pixel-by-pixel movement with walk animation
- Atmospheric effects: fog particles, fireflies, chimney smoke, flickering lanterns
- Parallax starfield title screen with animated dragon sprite
- Camera scrolling in town (20×15 tile map at 96px tiles)
- Fullscreen support (F11 or Alt+Enter)

### Combat
- FF4/FF6-style turn-based battle system
- Full animation sequencer with easing curves for attacks, spells, and abilities
- Hero step-forward attack, enemy recoil/flash, screen shake on hits
- High-res battle sprites (192×288 player, 288px enemies)
- 3 character classes: Warrior (Berserk), Thief (Steal), Mage (Spellcast)
- 12 unique enemy types across 3 forest zones

### Items & Crafting
- 7-tier material system: Wood, Copper, Iron, Steel, Enchanted, Dragon, Void
- 5 weapon types (Sword, Axe, Dagger, Staff, Spear) and 5 armour types
- Enemy loot drops — materials drop based on zone difficulty
- Blacksmith crafting — upgrade equipment to the next material tier
- Weapon and Armour shops with tiered inventory

### World
- Town of Pinnacle with 6 locations: Inn, Pub, Weapon Shop, Armour Shop, Blacksmith, Forest Gate
- NPC wanderers with patrol paths
- Mystic Forest with 3 zones: Shallow Forest, Deep Forest, Shadow Depths
- Daily turn system — rest at the Inn to reset forest turns

### Music
- Procedurally generated chiptune soundtrack
- Unique themes for title screen, town, forest, and battle
- Town groove: C#-A-F#-Ab chord progression at 100 BPM with boom bap drums
- All music synthesized at runtime from note sequences

### Technical
- Python 3.11+ / Pygame 2.6+
- Native 1920×1080 virtual resolution (no upscaling needed)
- External sprite sheet with auto-detected bounding regions and colorkey transparency
- Procedural sprite fallback when no sprite sheet is present
- Resizable window with fullscreen toggle
- JSON save/load system
- Scene manager with fade transitions

## Getting Started

### Requirements
- Python 3.9+
- Pygame 2.0+

### Install & Run
```bash
pip install pygame
python main.py
```

### Sprite Sheet
Place your character sprite sheet at `assets/sprites/characters.png`. The game auto-detects sprite regions for each class (Warrior, Thief, Cleric, Mage) with 3 poses each (front, side, back). If no sprite sheet is found, procedural sprites are used as fallback.

### Controls
| Key | Action |
|-----|--------|
| Arrow Keys / WASD | Move |
| Z / Enter | Confirm / Interact |
| X / Escape | Cancel / Back |
| F11 | Toggle Fullscreen |
| Alt+Enter | Toggle Fullscreen |

## Project Structure
```
main.py              - Game entry point and loop
settings.py          - Constants, configuration, sprite sheet regions
scenes/              - Game screens (title, town, forest, battle, etc.)
systems/             - Core systems (player, enemy, inventory, sprites, music)
ui/                  - Menu and HUD components
assets/sprites/      - External sprite sheet (characters.png)
saves/               - Save game files
.agents/             - AI context documentation
```

## Planned Upgrades
- Multiplayer PvP arena (based on original LORD's player duels)
- Bank system with daily interest
- More NPC interactions and quest lines in the Pub
- Expanded forest with discoverable locations and events
- Boss encounters (Red Dragon final boss)
- Equipment special effects in combat (bleed, crit, magic resist)
- Expanded crafting with recipe discovery
- Sound effects for combat, menus, and environment
- Reputation system affecting NPC dialogue and shop prices
- Day/night cycle with visual changes

## Credits
- Based on **Legend of the Red Dragon** by Seth Able Robinson (1989)
- Built with [Pygame](https://www.pygame.org/)

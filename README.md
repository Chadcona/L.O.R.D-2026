# Legend of the Red Dragon: 16-Bit Edition

A single-player SNES-style JRPG built with Python and Pygame, inspired by the classic 1989 BBS door game **Legend of the Red Dragon** by Seth Able Robinson.

Every sprite, tile, and music track is procedurally generated at runtime — no external assets required.

## Features

### Graphics
- SNES-quality procedural pixel art (16x24 character sprites, 48x48 enemies, 16x16 tiles)
- True side-profile sprites when moving left/right (classic SNES flip technique)
- Smooth pixel-by-pixel movement with walk animation at 64px/s
- Atmospheric effects: fog particles, fireflies, chimney smoke, flickering lanterns
- Parallax starfield title screen with animated dragon sprite
- Fullscreen support (F11 or Alt+Enter)

### Combat
- FF4/FF6-style turn-based battle system
- Full animation sequencer with easing curves for attacks, spells, and abilities
- Hero step-forward attack, enemy recoil/flash, screen shake on hits
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
- Detailed town environment: hanging signs with pixel art icons, chimneys, barrels, crates, lanterns, well
- NPC wanderers with patrol paths
- Mystic Forest with 3 zones: Shallow Forest, Deep Forest, Shadow Depths
- Daily turn system — rest at the Inn to reset forest turns

### Music
- Procedurally generated chiptune soundtrack
- Unique themes for title screen, town, forest, and battle
- Funky boom-bap town groove with square wave melody and triangle bass
- All music synthesized at runtime from note sequences

### Technical
- Python 3.11+ / Pygame 2.6+
- 320x240 virtual resolution upscaled to display
- Zero external asset dependencies
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

### Controls
| Key | Action |
|-----|--------|
| Arrow Keys | Move |
| Z / Enter | Confirm / Interact |
| X / Escape | Cancel / Back |
| F11 | Toggle Fullscreen |
| Alt+Enter | Toggle Fullscreen |

## Project Structure
```
main.py              - Game entry point and loop
settings.py          - Constants and configuration
scenes/              - Game screens (title, town, forest, battle, etc.)
systems/             - Core systems (player, enemy, inventory, sprites, music)
ui/                  - Menu and HUD components
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

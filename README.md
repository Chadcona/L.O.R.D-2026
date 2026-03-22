# Legend of the Red Dragon: 16-Bit Edition

A single-player SNES-style JRPG built with Python and Pygame, inspired by the classic 1989 BBS door game **Legend of the Red Dragon** by Seth Able Robinson.

## Features

### Graphics
- Native 1080p rendering with hand-drawn sprite sheet characters
- Per-class sprite sheets with 4-frame walk animations in all directions
- Auto-detected background removal (supports white, grey, or transparent PNG backgrounds)
- Dedicated NPC sprite sheets (Seth the tavern keeper, Violet the barmaid, town cat)
- Procedural pixel art fallback for enemies, tiles, and environmental details
- Smooth pixel-by-pixel movement with walk animation
- Atmospheric effects: fog particles, fireflies
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
- NPC wanderers: Seth (tavern keeper), Violet (barmaid), town cat
- Mystic Forest with 3 zones: Shallow Forest, Deep Forest, Shadow Depths
- Daily turn system — rest at the Inn to reset forest turns

### Music
- Procedurally generated chiptune soundtrack
- Unique themes for title screen, town, forest, and battle
- Town groove: C#-A-F#-Ab chord progression at 100 BPM with boom bap drums
- Stereo-correct playback (auto-handles mono→stereo mixer conversion)
- All music synthesized at runtime from note sequences

### Technical
- Python 3.11+ / Pygame 2.6+
- Native 1920×1080 rendering (no upscaling)
- Per-class sprite sheets with auto-detected background color and proximity-based removal
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

### Sprite Sheets
Place character sprite sheets in `assets/sprites/`:

| File | Character |
|------|-----------|
| `warrior.png` | Warrior class |
| `Thief.png` | Thief class |
| `mage.png` | Mage class |
| `Sethable Tavern Keeper.png` | Seth (NPC) |
| `violet tavernmaid mayors daughter.png` | Violet (NPC) |
| `town cat neko.png` | Town cat (NPC) |

All sheets are 2816×1536 with a consistent layout:
- **Row 1**: 8-frame walk (front/back views)
- **Row 2**: 8-frame walk (left/right views)
- **Row 3**: 4-frame idle animation
- **Row 4**: 8-frame combat sequence

Background is auto-detected from corner pixels and removed. For best results, export sheets with **transparent PNG backgrounds**.

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
settings.py          - Constants, configuration, sprite sheet layout
scenes/              - Game screens (title, town, forest, battle, etc.)
systems/             - Core systems (player, enemy, inventory, sprites, music)
ui/                  - Menu and HUD components
assets/sprites/      - Character and NPC sprite sheets
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
- Town tiles and tavern building sprites (assets staged)

## Credits
- Based on **Legend of the Red Dragon** by Seth Able Robinson (1989)
- Built with [Pygame](https://www.pygame.org/)

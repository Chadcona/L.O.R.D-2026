# Town of Pinnacle — walkable top-down town map

import pygame
import math
from scenes.scene_manager import Scene
from ui.menu import draw_text, draw_menu_box, SelectionMenu, DialogueBox
from ui.hud import draw_hud
from systems.sprites import (
    get_player_sprite, get_tile, create_roof_surface,
)
from settings import (
    BLACK, WHITE, GOLD, GREY, RED, GREEN, BLUE, BROWN, DARK_BROWN,
    DARK_GREEN, CREAM, SKY_BLUE, PURPLE, DARK_GREY, LIGHT_GREY,
    VIRTUAL_WIDTH, VIRTUAL_HEIGHT, INN_BASE_COST
)


# Tile types
GRASS = 0
PATH = 1
WALL = 2
WATER = 3
DOOR = 4      # Enterable building doors
TREE = 5
FLOWER = 6
FENCE = 7

# Tile colors
TILE_COLORS = {
    GRASS: (34, 120, 34),
    PATH: (180, 155, 100),
    WALL: (100, 70, 50),
    WATER: (40, 80, 180),
    DOOR: (160, 100, 40),
    TREE: (20, 80, 20),
    FLOWER: (34, 120, 34),  # Draw flowers on top
    FENCE: (120, 80, 40),
}

# Walkable tiles
WALKABLE = {GRASS, PATH, DOOR, FLOWER}

# Tile size in pixels (virtual resolution)
TILE_SIZE = 16

# Town map (20 x 15 = 320 x 240)
# Legend: 0=grass, 1=path, 2=wall, 3=water, 4=door, 5=tree, 6=flower, 7=fence
TOWN_MAP = [
    #  0  1  2  3  4  5  6  7  8  9 10 11 12 13 14 15 16 17 18 19
    [5, 5, 5, 5, 5, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 5, 5, 5, 5, 5],  # 0
    [5, 0, 0, 6, 0, 0, 2, 2, 2, 2, 0, 0, 2, 2, 2, 0, 6, 0, 0, 5],  # 1
    [5, 0, 0, 0, 0, 0, 2, 0, 0, 2, 0, 0, 2, 0, 2, 0, 0, 0, 0, 5],  # 2
    [5, 0, 0, 0, 1, 1, 2, 0, 4, 2, 1, 1, 2, 4, 2, 1, 1, 0, 0, 5],  # 3
    [5, 0, 0, 0, 1, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 1, 0, 0, 5],  # 4
    [0, 0, 6, 0, 1, 0, 2, 2, 2, 0, 1, 0, 2, 2, 2, 0, 1, 0, 6, 0],  # 5
    [0, 0, 0, 0, 1, 0, 2, 0, 2, 0, 1, 0, 2, 0, 2, 0, 1, 0, 0, 0],  # 6
    [0, 1, 1, 1, 1, 1, 2, 4, 2, 1, 1, 1, 2, 4, 2, 1, 1, 1, 1, 0],  # 7
    [0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 1, 0, 0, 0],  # 8
    [5, 2, 2, 2, 1, 0, 0, 7, 7, 0, 1, 0, 7, 7, 0, 0, 1, 0, 6, 5],  # 9
    [5, 2, 4, 2, 1, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 1, 0, 0, 5],  # 10
    [5, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 5],  # 11
    [5, 0, 6, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 6, 5],  # 12
    [5, 0, 0, 0, 0, 0, 6, 0, 0, 0, 4, 0, 0, 0, 6, 0, 0, 0, 0, 5],  # 13
    [5, 5, 5, 5, 5, 5, 5, 5, 5, 0, 0, 0, 5, 5, 5, 5, 5, 5, 5, 5],  # 14
]

# Building/location definitions: door tile position -> location info
LOCATIONS = {
    (8, 3): {
        "name": "The Rusty Sword Inn",
        "description": "Rest and save your game here.",
        "action": "inn",
        "color": GOLD,
    },
    (13, 3): {
        "name": "Seth's Pub",
        "description": "The social heart of Pinnacle.",
        "action": "pub",
        "color": BROWN,
    },
    (7, 7): {
        "name": "Weapon Shop",
        "description": "Buy and sell weapons.",
        "action": "weapon_shop",
        "color": RED,
    },
    (13, 7): {
        "name": "Armour Shop",
        "description": "Buy and sell armour.",
        "action": "armour_shop",
        "color": BLUE,
    },
    (2, 10): {
        "name": "Blacksmith",
        "description": "Forge and upgrade your equipment.",
        "action": "blacksmith",
        "color": (200, 120, 50),
    },
    (10, 13): {
        "name": "Forest Gate",
        "description": "Venture into the Mystic Forest.",
        "action": "forest",
        "color": DARK_GREEN,
    },
}


class TownScene(Scene):
    """The town of Pinnacle — walk around, enter buildings, interact."""

    # Pixels per second for smooth movement (SNES FF6 speed ~64px/s)
    MOVE_SPEED = 64.0
    # Walk animation frame rate (cycle through 4 frames during movement)
    WALK_ANIM_SPEED = 8.0  # frames per second

    def __init__(self):
        super().__init__()
        self.player = None
        # Tile coordinates (logical position — where the player IS)
        self.tile_x = 10
        self.tile_y = 11
        # Pixel coordinates (visual position — smoothly interpolated)
        self.pixel_x = float(10 * TILE_SIZE)
        self.pixel_y = float(11 * TILE_SIZE)
        # Movement target (None when idle, (tile_x, tile_y) when gliding)
        self.move_target = None
        self.facing = "down"
        self.dialogue = DialogueBox()
        self.location_prompt = None
        self.in_menu = False
        self.current_menu = None
        self.anim_time = 0
        self.walk_frame = 0
        self.walk_anim_timer = 0.0
        self.is_moving = False
        self.entered = False
        self._tile_cache = {}
        self._roof_cache = {}
        self._npc_sprites = []
        self._init_npcs()

    def _init_npcs(self):
        """Create NPC wanderers for the town to feel alive."""
        npc_defs = [
            {"tx": 2, "ty": 4, "class": "Thief", "hair": "blonde",
             "path": [(2, 4), (2, 8), (4, 8), (4, 4)]},
            {"tx": 15, "ty": 8, "class": "Mage", "hair": "white",
             "path": [(15, 8), (15, 10), (17, 10), (17, 8)]},
            {"tx": 9, "ty": 4, "class": "Warrior", "hair": "red",
             "path": [(9, 4), (9, 8), (10, 8), (10, 4)]},
        ]
        self._npc_sprites = []
        for d in npc_defs:
            self._npc_sprites.append({
                "tile_x": d["tx"], "tile_y": d["ty"],
                "pixel_x": float(d["tx"] * TILE_SIZE),
                "pixel_y": float(d["ty"] * TILE_SIZE),
                "target": None,  # (tile_x, tile_y) or None
                "class": d["class"], "facing": "down", "frame": 0,
                "hair": d["hair"], "walk_timer": 0.0,
                "path": d["path"], "path_idx": 0, "pause_timer": 0.5,
            })

    def on_enter(self, data=None):
        if data and "player" in data:
            self.player = data["player"]
        if data and data.get("new_game"):
            self.tile_x = 10
            self.tile_y = 11
            self.pixel_x = float(10 * TILE_SIZE)
            self.pixel_y = float(11 * TILE_SIZE)
            self.move_target = None
            self.dialogue.show(
                "Welcome to the town of Pinnacle! Explore the town, "
                "visit the shops, and when you're ready, head south to the Forest Gate.",
                speaker="Old Man"
            )
        self.entered = True

    def _update_npc_movement(self, dt):
        """Smooth pixel-based NPC movement along paths."""
        npc_speed = 40.0  # NPCs walk a bit slower than the player

        for npc in self._npc_sprites:
            target = npc["target"]

            if target is None:
                # Pausing between moves
                npc["pause_timer"] -= dt
                if npc["pause_timer"] <= 0:
                    # Pick next waypoint
                    waypoint = npc["path"][npc["path_idx"]]
                    tx, ty = waypoint
                    if tx == npc["tile_x"] and ty == npc["tile_y"]:
                        npc["path_idx"] = (npc["path_idx"] + 1) % len(npc["path"])
                        waypoint = npc["path"][npc["path_idx"]]
                        tx, ty = waypoint

                    # Move one tile toward waypoint
                    dx = 1 if tx > npc["tile_x"] else (-1 if tx < npc["tile_x"] else 0)
                    dy = 1 if ty > npc["tile_y"] else (-1 if ty < npc["tile_y"] else 0)
                    # Only move in one axis at a time
                    if dx != 0:
                        dy = 0
                    next_tx = npc["tile_x"] + dx
                    next_ty = npc["tile_y"] + dy
                    npc["tile_x"] = next_tx
                    npc["tile_y"] = next_ty
                    npc["target"] = (next_tx, next_ty)

                    if dx > 0:
                        npc["facing"] = "right"
                    elif dx < 0:
                        npc["facing"] = "left"
                    elif dy > 0:
                        npc["facing"] = "down"
                    elif dy < 0:
                        npc["facing"] = "up"
                continue

            # Glide toward target tile
            target_px = float(target[0] * TILE_SIZE)
            target_py = float(target[1] * TILE_SIZE)
            dx = target_px - npc["pixel_x"]
            dy = target_py - npc["pixel_y"]
            dist = max(abs(dx), abs(dy))

            if dist < 1.0:
                # Arrived
                npc["pixel_x"] = target_px
                npc["pixel_y"] = target_py
                npc["target"] = None
                npc["pause_timer"] = 0.3
                npc["frame"] = 0  # Standing frame
            else:
                # Glide
                step = npc_speed * dt
                if abs(dx) > 0.5:
                    npc["pixel_x"] += step if dx > 0 else -step
                if abs(dy) > 0.5:
                    npc["pixel_y"] += step if dy > 0 else -step
                # Walk animation
                npc["walk_timer"] += dt * self.WALK_ANIM_SPEED
                npc["frame"] = int(npc["walk_timer"]) % 4

    def update(self, dt):
        self.anim_time += dt
        self.dialogue.update(dt)

        # Smooth NPC movement
        self._update_npc_movement(dt)

        if self.dialogue.active:
            return

        if self.in_menu:
            if self.current_menu:
                self.current_menu.update(dt)
            return

        # --- Smooth player movement ---

        # If currently gliding toward a target tile, interpolate
        if self.move_target is not None:
            target_px = float(self.move_target[0] * TILE_SIZE)
            target_py = float(self.move_target[1] * TILE_SIZE)
            dx = target_px - self.pixel_x
            dy = target_py - self.pixel_y
            dist = math.sqrt(dx * dx + dy * dy)

            if dist < 1.0:
                # Arrived at target tile
                self.pixel_x = target_px
                self.pixel_y = target_py
                self.tile_x = self.move_target[0]
                self.tile_y = self.move_target[1]
                self.move_target = None
                self.is_moving = False
                self._check_location()
                # Immediately check for held keys to chain moves smoothly
                self._try_start_move()
            else:
                # Glide toward target
                step = self.MOVE_SPEED * dt
                if step >= dist:
                    self.pixel_x = target_px
                    self.pixel_y = target_py
                else:
                    self.pixel_x += (dx / dist) * step
                    self.pixel_y += (dy / dist) * step
                # Walk animation cycles during movement
                self.walk_anim_timer += dt * self.WALK_ANIM_SPEED
                self.walk_frame = int(self.walk_anim_timer) % 4
                self.is_moving = True
        else:
            # Not moving — check for new input
            self.is_moving = False
            self.walk_frame = 0  # Standing frame when idle
            self._try_start_move()

    def _try_start_move(self):
        """Check held keys and start a new smooth move if possible."""
        keys = pygame.key.get_pressed()
        dx, dy = 0, 0
        if keys[pygame.K_UP] or keys[pygame.K_w]:
            dy = -1
            self.facing = "up"
        elif keys[pygame.K_DOWN] or keys[pygame.K_s]:
            dy = 1
            self.facing = "down"
        elif keys[pygame.K_LEFT] or keys[pygame.K_a]:
            dx = -1
            self.facing = "left"
        elif keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            dx = 1
            self.facing = "right"

        if dx != 0 or dy != 0:
            new_x = self.tile_x + dx
            new_y = self.tile_y + dy
            if self._can_walk(new_x, new_y):
                # Start gliding to the new tile
                self.move_target = (new_x, new_y)
                self.tile_x = new_x  # Logically claim the tile immediately
                self.tile_y = new_y
                self.is_moving = True
            else:
                # Bump into wall — just update facing, don't move
                self.walk_frame = 0

    def _can_walk(self, x, y):
        """Check if a tile is walkable."""
        if x < 0 or x >= 20 or y < 0 or y >= 15:
            return False
        return TOWN_MAP[y][x] in WALKABLE

    def _check_location(self):
        """Check if player is standing on a door/location."""
        pos = (self.tile_x, self.tile_y)
        if pos in LOCATIONS:
            self.location_prompt = LOCATIONS[pos]
        else:
            self.location_prompt = None

    def handle_event(self, event):
        if self.dialogue.active:
            self.dialogue.handle_event(event)
            return

        if self.in_menu:
            self._handle_menu_event(event)
            return

        if event.type != pygame.KEYDOWN:
            return

        # Interact / enter building (only when not mid-glide)
        if event.key in (pygame.K_z, pygame.K_RETURN):
            if self.move_target is not None:
                return  # Can't interact while moving
            if self.location_prompt:
                self._enter_location(self.location_prompt)

        # Open status menu
        elif event.key in (pygame.K_ESCAPE, pygame.K_x):
            self._open_status_menu()

    def _enter_location(self, location):
        """Handle entering a town location."""
        action = location["action"]

        if action == "inn":
            self._open_inn_menu()
        elif action == "forest":
            if self.player.forest_turns > 0:
                self.manager.switch_to("forest", {"player": self.player})
            else:
                self.dialogue.show(
                    "You have no Forest Turns remaining today. Rest at the Inn first.",
                    speaker="Gate Guard"
                )
        elif action == "weapon_shop":
            self._open_weapon_shop()
        elif action == "armour_shop":
            self._open_armour_shop()
        elif action == "blacksmith":
            self._open_blacksmith()
        elif action == "pub":
            self.dialogue.show(
                "The pub is lively tonight! Adventurers swap tales over mugs of ale.",
                speaker="Seth"
            )

    def _open_inn_menu(self):
        cost = self.player.inn_cost()
        self.in_menu = True
        self.current_menu = {
            "type": "inn",
            "menu": SelectionMenu(
                items=[
                    {"label": f"Rest ({cost}g)", "value": "rest",
                     "enabled": self.player.gold >= cost},
                    {"label": "Save Game", "value": "save"},
                    {"label": "Leave", "value": "leave"},
                ],
                x=VIRTUAL_WIDTH // 2 - 50,
                y=90,
                spacing=18,
                font_size=16,
            ),
        }

    def _open_weapon_shop(self):
        from systems.inventory import WEAPONS
        items = [{"label": f"{w['name']} ({w['cost']}g) ATK:{w['atk']}",
                  "value": w, "enabled": self.player.gold >= w["cost"]}
                 for w in WEAPONS if w["cost"] > 0]
        items.append({"label": "Leave", "value": "leave"})
        self.in_menu = True
        self.current_menu = {
            "type": "weapon_shop",
            "menu": SelectionMenu(items=items, x=20, y=50, spacing=16, font_size=12),
        }

    def _open_armour_shop(self):
        from systems.inventory import ARMOURS
        items = [{"label": f"{a['name']} ({a['cost']}g) DEF:{a['def']}",
                  "value": a, "enabled": self.player.gold >= a["cost"]}
                 for a in ARMOURS if a["cost"] > 0]
        items.append({"label": "Leave", "value": "leave"})
        self.in_menu = True
        self.current_menu = {
            "type": "armour_shop",
            "menu": SelectionMenu(items=items, x=20, y=50, spacing=16, font_size=12),
        }

    def _open_blacksmith(self):
        from systems.inventory import can_craft_upgrade, get_upgrade_recipe, TIER_BY_NAME
        items = []
        # Weapon upgrade option
        w = self.player.weapon
        w_tier = w.get("tier", "Wood")
        w_recipe = get_upgrade_recipe(w_tier)
        if w_recipe:
            can, msg = can_craft_upgrade(self.player, w)
            next_tier = w_recipe["result_tier"]
            label = f"Upgrade {w['name']} -> {next_tier}"
            items.append({"label": label, "value": "upgrade_weapon", "enabled": can})
        else:
            items.append({"label": f"{w['name']} (MAX)", "value": "none", "enabled": False})

        # Armour upgrade option
        a = self.player.armour
        a_tier = a.get("tier", "Wood")
        a_recipe = get_upgrade_recipe(a_tier)
        if a_recipe:
            can, msg = can_craft_upgrade(self.player, a)
            next_tier = a_recipe["result_tier"]
            label = f"Upgrade {a['name']} -> {next_tier}"
            items.append({"label": label, "value": "upgrade_armour", "enabled": can})
        else:
            items.append({"label": f"{a['name']} (MAX)", "value": "none", "enabled": False})

        # Show materials
        items.append({"label": "---Materials---", "value": "none", "enabled": False})
        from systems.inventory import MATERIALS
        for inv_item in self.player.inventory:
            if inv_item.get("type") in ("material", "catalyst"):
                count = inv_item.get("count", 1)
                items.append({"label": f"  {inv_item['name']} x{count}", "value": "none", "enabled": False})

        items.append({"label": "Leave", "value": "leave"})
        self.in_menu = True
        self.current_menu = {
            "type": "blacksmith",
            "menu": SelectionMenu(items=items, x=20, y=50, spacing=14, font_size=11),
        }

    def _open_status_menu(self):
        self.in_menu = True
        self.current_menu = {
            "type": "status",
            "menu": SelectionMenu(
                items=[
                    {"label": "Status", "value": "status"},
                    {"label": "Inventory", "value": "inventory"},
                    {"label": "Close", "value": "close"},
                ],
                x=VIRTUAL_WIDTH - 90,
                y=35,
                spacing=16,
                font_size=14,
            ),
        }

    def _handle_menu_event(self, event):
        if not self.current_menu:
            return

        menu = self.current_menu["menu"]
        menu.handle_event(event)

        if menu.cancelled:
            self.in_menu = False
            self.current_menu = None
            return

        if not menu.confirmed:
            return

        menu_type = self.current_menu["type"]
        value = menu.get_selected_value()

        if value == "leave" or value == "close":
            self.in_menu = False
            self.current_menu = None

        elif menu_type == "inn":
            if value == "rest":
                if self.player.rest_at_inn():
                    self.in_menu = False
                    self.current_menu = None
                    self.dialogue.show(
                        f"You rest peacefully. A new day dawns! (Day {self.player.day})",
                        speaker="Innkeeper"
                    )
                else:
                    self.dialogue.show("You can't afford to stay!", speaker="Innkeeper")
            elif value == "save":
                from systems.save_load import save_game
                save_game(1, self.player)
                self.in_menu = False
                self.current_menu = None
                self.dialogue.show("Your progress has been saved.", speaker="Innkeeper")

        elif menu_type == "weapon_shop":
            if isinstance(value, dict):
                weapon = value
                if self.player.gold >= weapon["cost"]:
                    self.player.gold -= weapon["cost"]
                    self.player.weapon = {
                        "name": weapon["name"],
                        "atk": weapon["atk"],
                        "special": weapon.get("special"),
                        "tier": weapon.get("tier", "Wood"),
                        "type": weapon.get("type", "Sword"),
                    }
                    self.in_menu = False
                    self.current_menu = None
                    self.dialogue.show(
                        f"You equipped the {weapon['name']}!",
                        speaker="Shopkeeper"
                    )

        elif menu_type == "armour_shop":
            if isinstance(value, dict):
                armour = value
                if self.player.gold >= armour["cost"]:
                    self.player.gold -= armour["cost"]
                    self.player.armour = {
                        "name": armour["name"],
                        "def": armour["def"],
                        "special": armour.get("special"),
                        "tier": armour.get("tier", "Wood"),
                        "type": armour.get("type", "Shield"),
                    }
                    self.in_menu = False
                    self.current_menu = None
                    self.dialogue.show(
                        f"You equipped the {armour['name']}!",
                        speaker="Shopkeeper"
                    )

        elif menu_type == "blacksmith":
            if value == "upgrade_weapon":
                from systems.inventory import perform_upgrade
                new_eq, msg = perform_upgrade(self.player, self.player.weapon)
                if new_eq:
                    self.player.weapon = new_eq
                    self.in_menu = False
                    self.current_menu = None
                    self.dialogue.show(msg, speaker="Blacksmith")
                else:
                    self.in_menu = False
                    self.current_menu = None
                    self.dialogue.show(msg, speaker="Blacksmith")
            elif value == "upgrade_armour":
                from systems.inventory import perform_upgrade
                new_eq, msg = perform_upgrade(self.player, self.player.armour)
                if new_eq:
                    self.player.armour = new_eq
                    self.in_menu = False
                    self.current_menu = None
                    self.dialogue.show(msg, speaker="Blacksmith")
                else:
                    self.in_menu = False
                    self.current_menu = None
                    self.dialogue.show(msg, speaker="Blacksmith")
            elif value == "leave":
                self.in_menu = False
                self.current_menu = None

        elif menu_type == "status":
            # Status and inventory are view-only for now
            self.in_menu = False
            self.current_menu = None

    def _get_tile_surface(self, tile_type, x, y):
        """Get or create a cached tile surface."""
        variant = (x * 7 + y * 13) % 16
        water_frame = int(self.anim_time * 2) % 8

        if tile_type == GRASS or tile_type == FLOWER:
            return get_tile("grass", variant=variant)
        elif tile_type == PATH:
            return get_tile("path", variant=variant)
        elif tile_type == WALL:
            return get_tile("wall", variant=variant)
        elif tile_type == WATER:
            return get_tile("water", frame=water_frame)
        elif tile_type == DOOR:
            return get_tile("door")
        elif tile_type == TREE:
            return get_tile("tree")
        elif tile_type == FENCE:
            return self._draw_fence_tile(x, y)
        return None

    def _draw_fence_tile(self, x, y):
        """Create a detailed fence tile."""
        surf = pygame.Surface((TILE_SIZE, TILE_SIZE))
        surf.fill((34, 130, 34))  # Grass behind
        # Fence posts
        post_color = (140, 100, 50)
        post_hi = (170, 130, 70)
        post_shadow = (100, 65, 30)
        # Posts at edges
        for px in [2, 13]:
            for py in range(2, 15):
                surf.set_at((px, py), post_hi if px == 2 else post_shadow)
                surf.set_at((px + 1, py), post_color)
        # Horizontal rails
        for rail_y in [5, 10]:
            for rx in range(TILE_SIZE):
                surf.set_at((rx, rail_y), post_hi)
                surf.set_at((rx, rail_y + 1), post_color)
                surf.set_at((rx, rail_y + 2), post_shadow)
        # Post tops
        for px in [1, 12]:
            surf.set_at((px, 1), post_hi)
            surf.set_at((px + 1, 1), post_color)
            surf.set_at((px + 2, 1), post_shadow)
        return surf

    def _draw_building_roofs(self, surface):
        """Draw pitched roofs, hanging signs, chimneys, and window details."""
        # (wx_start, wx_end, roof_y, roof_color, label, label_color, door_x, icon)
        buildings = [
            (6, 9, 0, (180, 60, 50), "The Rusty Sword Inn", GOLD, 8, "bed"),
            (12, 14, 0, (60, 120, 60), "Seth's Pub", BROWN, 13, "mug"),
            (6, 8, 4, (160, 80, 40), "Weapon Shop", RED, 7, "sword"),
            (12, 14, 4, (50, 80, 160), "Armour Shop", BLUE, 13, "shield"),
            (1, 3, 8, (180, 100, 40), "Blacksmith", (200, 120, 50), 2, "anvil"),
        ]

        from ui.menu import get_font

        for wx_start, wx_end, roof_y, roof_color, label, label_color, door_x, icon in buildings:
            rx = wx_start * TILE_SIZE - 4
            ry = roof_y * TILE_SIZE - 2
            rw = (wx_end - wx_start + 1) * TILE_SIZE + 8
            rh = 10

            roof = create_roof_surface(rw, rh, roof_color)
            surface.blit(roof, (rx, ry))

            # Chimney (on right side of each building)
            chim_x = (wx_end) * TILE_SIZE + 2
            chim_y = ry - 6
            for cy in range(6):
                surface.set_at((chim_x, chim_y + cy), (100, 70, 50))
                surface.set_at((chim_x + 1, chim_y + cy), (80, 55, 35))
                surface.set_at((chim_x + 2, chim_y + cy), (100, 70, 50))
            # Chimney cap
            for cx in range(-1, 4):
                surface.set_at((chim_x + cx, chim_y - 1), (120, 85, 60))

            # Animated smoke from chimney
            smoke_phase = int(self.anim_time * 3) % 4
            for si in range(3):
                sx = chim_x + 1 + (si + smoke_phase) % 3 - 1
                sy = chim_y - 3 - si * 3 - smoke_phase
                if 0 <= sy < VIRTUAL_HEIGHT and 0 <= sx < VIRTUAL_WIDTH:
                    alpha = max(0, 40 - si * 12)
                    if alpha > 0:
                        smoke_surf = pygame.Surface((3, 2), pygame.SRCALPHA)
                        smoke_surf.fill((200, 200, 210, alpha))
                        surface.blit(smoke_surf, (sx, sy))

            # Roof edge shadow
            shadow_c = (max(0, roof_color[0] - 60),
                        max(0, roof_color[1] - 40),
                        max(0, roof_color[2] - 40))
            for x_off in range(rw):
                px = rx + x_off
                if 0 <= px < VIRTUAL_WIDTH and ry + rh < VIRTUAL_HEIGHT:
                    surface.set_at((px, ry + rh), shadow_c)

            # --- Hanging wooden sign with icon ---
            sign_x = door_x * TILE_SIZE + TILE_SIZE // 2
            sign_y = roof_y * TILE_SIZE + 1

            # Sign post (iron bracket)
            bracket_x = sign_x + 10
            for by in range(sign_y - 2, sign_y + 2):
                if 0 <= bracket_x < VIRTUAL_WIDTH and 0 <= by < VIRTUAL_HEIGHT:
                    surface.set_at((bracket_x, by), (80, 80, 90))
            # Horizontal bar
            for bx in range(sign_x - 2, bracket_x + 1):
                if 0 <= bx < VIRTUAL_WIDTH:
                    surface.set_at((bx, sign_y - 2), (80, 80, 90))
            # Chain links
            surface.set_at((sign_x, sign_y - 1), (120, 120, 130))
            surface.set_at((sign_x, sign_y), (100, 100, 110))

            # Sign board (wooden plank)
            sw, sh = 22, 12
            sign_surf = pygame.Surface((sw, sh), pygame.SRCALPHA)
            # Wood background
            for sy2 in range(sh):
                for sx2 in range(sw):
                    wood_noise = ((sx2 * 7 + sy2 * 3) % 5) * 3
                    sign_surf.set_at((sx2, sy2), (100 + wood_noise, 70 + wood_noise, 35 + wood_noise // 2))
            # Border
            pygame.draw.rect(sign_surf, (60, 40, 20), (0, 0, sw, sh), 1)

            # Draw icon on sign
            self._draw_sign_icon(sign_surf, icon, sw, sh)

            surface.blit(sign_surf, (sign_x - sw // 2, sign_y + 1))

            # Name text below sign
            font = get_font(7)
            tw = font.size(label)[0]
            name_y = sign_y + sh + 2
            # Text shadow
            draw_text(surface, label, sign_x + 1, name_y + 1, (20, 15, 10), 7, center=True)
            draw_text(surface, label, sign_x, name_y, label_color, 7, center=True)

            # --- Window details (lit windows with warm glow) ---
            wall_top = roof_y * TILE_SIZE + rh - 2
            for wi, wx in enumerate(range(wx_start, wx_end + 1)):
                win_x = wx * TILE_SIZE + 4
                win_y = wall_top + 4
                if win_x + 8 < VIRTUAL_WIDTH and win_y + 6 < VIRTUAL_HEIGHT:
                    # Window frame
                    pygame.draw.rect(surface, (80, 60, 40), (win_x, win_y, 8, 6))
                    # Glass (warm yellow glow)
                    glow = int(180 + 30 * math.sin(self.anim_time * 1.5 + wi))
                    pygame.draw.rect(surface, (glow, glow - 40, 40), (win_x + 1, win_y + 1, 6, 4))
                    # Window cross
                    pygame.draw.line(surface, (80, 60, 40), (win_x + 4, win_y), (win_x + 4, win_y + 6))
                    pygame.draw.line(surface, (80, 60, 40), (win_x, win_y + 3), (win_x + 8, win_y + 3))

    def _draw_sign_icon(self, surf, icon, sw, sh):
        """Draw a small pixel art icon on a hanging sign."""
        cx, cy = sw // 2, sh // 2
        if icon == "sword":
            # Tiny sword
            for i in range(7):
                surf.set_at((cx - 3 + i, cy), (200, 200, 210))
            surf.set_at((cx + 3, cy - 1), (200, 200, 210))
            surf.set_at((cx + 3, cy + 1), (200, 200, 210))
            surf.set_at((cx - 3, cy), (160, 120, 40))  # hilt
            surf.set_at((cx - 4, cy), (160, 120, 40))
            surf.set_at((cx - 3, cy - 1), (160, 120, 40))
            surf.set_at((cx - 3, cy + 1), (160, 120, 40))
        elif icon == "shield":
            # Tiny shield
            for dy in range(-3, 4):
                w = 3 - abs(dy) // 2
                for dx in range(-w, w + 1):
                    c = (60, 60, 180) if abs(dx) + abs(dy) < 4 else (40, 40, 140)
                    surf.set_at((cx + dx, cy + dy), c)
            surf.set_at((cx, cy), (200, 180, 60))  # emblem
        elif icon == "bed":
            # Tiny bed
            for dx in range(-4, 5):
                surf.set_at((cx + dx, cy + 1), (140, 90, 50))  # frame
                surf.set_at((cx + dx, cy), (200, 180, 160))  # blanket
            surf.set_at((cx - 4, cy - 1), (140, 90, 50))  # headboard
            surf.set_at((cx - 3, cy - 1), (140, 90, 50))
            surf.set_at((cx - 4, cy - 2), (140, 90, 50))
            surf.set_at((cx - 3, cy - 2), (140, 90, 50))
        elif icon == "mug":
            # Tiny mug with foam
            for dy in range(-1, 4):
                surf.set_at((cx - 2, cy + dy), (160, 120, 60))
                surf.set_at((cx + 2, cy + dy), (160, 120, 60))
            for dx in range(-2, 3):
                surf.set_at((cx + dx, cy + 3), (160, 120, 60))  # bottom
                surf.set_at((cx + dx, cy - 1), (240, 240, 220))  # foam
            surf.set_at((cx + 3, cy), (160, 120, 60))  # handle
            surf.set_at((cx + 3, cy + 1), (160, 120, 60))
        elif icon == "anvil":
            # Tiny anvil
            for dx in range(-3, 4):
                surf.set_at((cx + dx, cy + 2), (100, 100, 110))  # base
            for dx in range(-2, 3):
                surf.set_at((cx + dx, cy + 1), (130, 130, 140))
            for dx in range(-3, 4):
                surf.set_at((cx + dx, cy), (160, 160, 170))  # top
            surf.set_at((cx - 3, cy - 1), (160, 160, 170))
            surf.set_at((cx + 3, cy - 1), (140, 140, 150))

    def _draw_town_details(self, surface):
        """Draw extra environmental details — lanterns, barrels, crates, puddles."""
        # Lantern posts along main path
        lantern_positions = [(4, 4), (4, 8), (16, 4), (16, 8)]
        for lx, ly in lantern_positions:
            px = lx * TILE_SIZE + 8
            py = ly * TILE_SIZE

            # Post
            for dy in range(-8, 0):
                surface.set_at((px, py + dy), (80, 70, 50))

            # Lantern body
            for dy in range(-10, -7):
                for dx in range(-1, 2):
                    surface.set_at((px + dx, py + dy), (60, 50, 30))

            # Glow (animated flicker)
            glow = int(200 + 40 * math.sin(self.anim_time * 5 + lx))
            glow_surf = pygame.Surface((6, 6), pygame.SRCALPHA)
            pygame.draw.circle(glow_surf, (glow, glow - 60, 30, 80), (3, 3), 3)
            surface.blit(glow_surf, (px - 3, py - 12))
            # Bright center
            surface.set_at((px, py - 9), (255, 220, 100))

        # Barrels near pub and inn
        barrel_spots = [(11, 1), (11, 2), (15, 1)]
        for bx, by in barrel_spots:
            px = bx * TILE_SIZE + 2
            py = by * TILE_SIZE + 4
            # Barrel body
            for dy in range(8):
                w = 4 if 2 <= dy <= 5 else 3
                for dx in range(w):
                    noise = ((dx + dy * 3) % 3) * 8
                    c = (120 + noise, 80 + noise, 40 + noise // 2)
                    surface.set_at((px + dx, py + dy), c)
            # Barrel bands
            for dx in range(5):
                surface.set_at((px + dx - 1, py + 2), (80, 80, 90))
                surface.set_at((px + dx - 1, py + 5), (80, 80, 90))

        # Crates near weapon shop
        crate_spots = [(5, 5), (5, 6)]
        for cx, cy in crate_spots:
            px = cx * TILE_SIZE + 6
            py = cy * TILE_SIZE + 4
            for dy in range(7):
                for dx in range(7):
                    if dx == 0 or dx == 6 or dy == 0 or dy == 6:
                        surface.set_at((px + dx, py + dy), (80, 55, 25))
                    else:
                        noise = ((dx * 5 + dy * 7) % 4) * 5
                        surface.set_at((px + dx, py + dy), (130 + noise, 95 + noise, 45))
            # Cross slats
            for i in range(7):
                surface.set_at((px + i, py + i), (100, 70, 35))
                surface.set_at((px + 6 - i, py + i), (100, 70, 35))

        # Well in the town center-ish area
        well_x, well_y = 10 * TILE_SIZE, 9 * TILE_SIZE
        # Stone base
        for dy in range(8):
            for dx in range(-5, 6):
                if abs(dx) + dy > 3:
                    c = (110 + (dx * 3 + dy * 5) % 8, 105 + (dx + dy) % 5, 100)
                    surface.set_at((well_x + dx + 8, well_y + dy + 4), c)
        # Wooden frame above
        for dx in range(-3, 4):
            surface.set_at((well_x + dx + 8, well_y + 3), (100, 70, 40))
        surface.set_at((well_x + 5, well_y + 1), (100, 70, 40))
        surface.set_at((well_x + 5, well_y + 2), (100, 70, 40))
        surface.set_at((well_x + 11, well_y + 1), (100, 70, 40))
        surface.set_at((well_x + 11, well_y + 2), (100, 70, 40))
        # Crossbar and bucket
        for dx in range(5, 12):
            surface.set_at((well_x + dx, well_y), (100, 70, 40))
        surface.set_at((well_x + 8, well_y + 1), (80, 80, 90))  # rope
        surface.set_at((well_x + 8, well_y + 2), (80, 80, 90))

    def _draw_flowers(self, surface, x, y):
        """Draw detailed flowers on a grass tile."""
        tx = x * TILE_SIZE
        ty = y * TILE_SIZE
        # Multiple flowers per tile
        flower_data = [
            (3, 3, (255, 100, 120)),   # Red flower
            (10, 5, (120, 120, 255)),   # Blue flower
            (6, 10, (255, 255, 100)),   # Yellow flower
            (12, 12, (255, 150, 200)),  # Pink flower
        ]
        variant = (x * 3 + y * 7) % 4
        for i, (fx, fy, color) in enumerate(flower_data):
            if (i + variant) % 2 == 0:
                continue
            px, py = tx + fx, ty + fy
            # Stem
            surface.set_at((px, py + 2), (30, 100, 30))
            surface.set_at((px, py + 3), (30, 100, 30))
            # Petals
            for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                surface.set_at((px + dx, py + dy), color)
            # Center
            surface.set_at((px, py), (255, 255, 200))
            # Leaf
            surface.set_at((px - 1, py + 2), (40, 120, 35))

    def draw(self, surface):
        surface.fill(BLACK)

        # Draw tile map with SNES-quality tiles
        for y in range(15):
            for x in range(20):
                tile = TOWN_MAP[y][x]
                tile_surf = self._get_tile_surface(tile, x, y)
                if tile_surf:
                    surface.blit(tile_surf, (x * TILE_SIZE, y * TILE_SIZE))

                # Draw flowers on top of grass tiles
                if tile == FLOWER:
                    self._draw_flowers(surface, x, y)

        # Draw building roofs, signs, and details
        self._draw_building_roofs(surface)
        self._draw_town_details(surface)

        # Forest gate special decoration
        gate_x, gate_y = 10, 13
        gx = gate_x * TILE_SIZE
        gy = gate_y * TILE_SIZE
        # Stone archway
        for dy in range(-TILE_SIZE, 0):
            surface.set_at((gx - 1, gy + dy), (100, 100, 110))
            surface.set_at((gx + TILE_SIZE, gy + dy), (100, 100, 110))
        for dx in range(-1, TILE_SIZE + 1):
            surface.set_at((gx + dx, gy - TILE_SIZE), (110, 110, 120))
            surface.set_at((gx + dx, gy - TILE_SIZE + 1), (90, 90, 100))
        draw_text(surface, "Forest Gate", gx + TILE_SIZE // 2, gy - TILE_SIZE - 6,
                  DARK_GREEN, 8, center=True)

        # Draw NPCs (using smooth pixel positions)
        for npc in self._npc_sprites:
            npc_sprite = get_player_sprite(npc["class"], npc["facing"], npc["frame"], npc["hair"])
            npc_px = int(npc["pixel_x"])
            npc_py = int(npc["pixel_y"]) - 8  # Offset up so feet align with tile
            surface.blit(npc_sprite, (npc_px, npc_py))

        # Draw player character with smooth pixel position
        if self.player:
            player_sprite = get_player_sprite(
                self.player.player_class, self.facing, self.walk_frame
            )
            px = int(self.pixel_x)
            py = int(self.pixel_y) - 8  # Offset up so feet align with tile
            surface.blit(player_sprite, (px, py))

        # Draw HUD
        if self.player:
            draw_hud(surface, self.player)

        # Draw location prompt
        if self.location_prompt and not self.dialogue.active and not self.in_menu:
            loc = self.location_prompt
            prompt_text = f"Enter {loc['name']}? [Z]"
            draw_menu_box(surface, (VIRTUAL_WIDTH // 2 - 80, VIRTUAL_HEIGHT - 30, 160, 20))
            draw_text(surface, prompt_text, VIRTUAL_WIDTH // 2, VIRTUAL_HEIGHT - 23,
                      GOLD, 11, center=True)

        # Draw menus
        if self.in_menu and self.current_menu:
            # Darken background
            overlay = pygame.Surface((VIRTUAL_WIDTH, VIRTUAL_HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 100))
            surface.blit(overlay, (0, 0))

            menu_type = self.current_menu["type"]
            if menu_type == "inn":
                draw_menu_box(surface, (VIRTUAL_WIDTH // 2 - 65, 70, 130, 90))
                draw_text(surface, "The Rusty Sword Inn", VIRTUAL_WIDTH // 2, 75,
                          GOLD, 14, center=True)
            elif menu_type == "weapon_shop":
                draw_menu_box(surface, (10, 30, VIRTUAL_WIDTH - 20, VIRTUAL_HEIGHT - 60))
                draw_text(surface, "Weapon Shop", VIRTUAL_WIDTH // 2, 35, RED, 16, center=True)
            elif menu_type == "armour_shop":
                draw_menu_box(surface, (10, 30, VIRTUAL_WIDTH - 20, VIRTUAL_HEIGHT - 60))
                draw_text(surface, "Armour Shop", VIRTUAL_WIDTH // 2, 35, BLUE, 16, center=True)
            elif menu_type == "blacksmith":
                draw_menu_box(surface, (10, 30, VIRTUAL_WIDTH - 20, VIRTUAL_HEIGHT - 60))
                draw_text(surface, "Blacksmith - Forge & Upgrade", VIRTUAL_WIDTH // 2, 35,
                          (200, 120, 50), 14, center=True)

            self.current_menu["menu"].draw(surface)

        # Draw dialogue on top of everything
        self.dialogue.draw(surface)

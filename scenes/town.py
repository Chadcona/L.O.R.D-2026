# Town of Pinnacle — walkable top-down town map (1080p)

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
    VIRTUAL_WIDTH, VIRTUAL_HEIGHT, INN_BASE_COST, TILE_SIZE,
    PLAYER_SPRITE_W, PLAYER_SPRITE_H
)


# Tile types
GRASS = 0
PATH = 1
WALL = 2
WATER = 3
DOOR = 4
TREE = 5
FLOWER = 6
FENCE = 7

TILE_COLORS = {
    GRASS: (34, 120, 34),
    PATH: (180, 155, 100),
    WALL: (100, 70, 50),
    WATER: (40, 80, 180),
    DOOR: (160, 100, 40),
    TREE: (20, 80, 20),
    FLOWER: (34, 120, 34),
    FENCE: (120, 80, 40),
}

WALKABLE = {GRASS, PATH, DOOR, FLOWER}

MAP_COLS = 20
MAP_ROWS = 15

# Town map (same 20x15 layout — camera scrolls to fit 1080p viewport)
TOWN_MAP = [
    [5, 5, 5, 5, 5, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 5, 5, 5, 5, 5],
    [5, 0, 0, 6, 0, 0, 2, 2, 2, 2, 0, 0, 2, 2, 2, 0, 6, 0, 0, 5],
    [5, 0, 0, 0, 0, 0, 2, 0, 0, 2, 0, 0, 2, 0, 2, 0, 0, 0, 0, 5],
    [5, 0, 0, 0, 1, 1, 2, 0, 4, 2, 1, 1, 2, 4, 2, 1, 1, 0, 0, 5],
    [5, 0, 0, 0, 1, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 1, 0, 0, 5],
    [0, 0, 6, 0, 1, 0, 2, 2, 2, 0, 1, 0, 2, 2, 2, 0, 1, 0, 6, 0],
    [0, 0, 0, 0, 1, 0, 2, 0, 2, 0, 1, 0, 2, 0, 2, 0, 1, 0, 0, 0],
    [0, 1, 1, 1, 1, 1, 2, 4, 2, 1, 1, 1, 2, 4, 2, 1, 1, 1, 1, 0],
    [0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 1, 0, 0, 0],
    [5, 2, 2, 2, 1, 0, 0, 7, 7, 0, 1, 0, 7, 7, 0, 0, 1, 0, 6, 5],
    [5, 2, 4, 2, 1, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 1, 0, 0, 5],
    [5, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 5],
    [5, 0, 6, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 6, 5],
    [5, 0, 0, 0, 0, 0, 6, 0, 0, 0, 4, 0, 0, 0, 6, 0, 0, 0, 0, 5],
    [5, 5, 5, 5, 5, 5, 5, 5, 5, 0, 0, 0, 5, 5, 5, 5, 5, 5, 5, 5],
]

LOCATIONS = {
    (8, 3): {"name": "The Rusty Sword Inn", "description": "Rest and save your game here.", "action": "inn", "color": GOLD},
    (13, 3): {"name": "Seth's Pub", "description": "The social heart of Pinnacle.", "action": "pub", "color": BROWN},
    (7, 7): {"name": "Weapon Shop", "description": "Buy and sell weapons.", "action": "weapon_shop", "color": RED},
    (13, 7): {"name": "Armour Shop", "description": "Buy and sell armour.", "action": "armour_shop", "color": BLUE},
    (2, 10): {"name": "Blacksmith", "description": "Forge and upgrade your equipment.", "action": "blacksmith", "color": (200, 120, 50)},
    (10, 13): {"name": "Forest Gate", "description": "Venture into the Mystic Forest.", "action": "forest", "color": DARK_GREEN},
}


class TownScene(Scene):
    """The town of Pinnacle — walk around, enter buildings, interact (1080p)."""

    MOVE_SPEED = 384.0  # pixels/sec at TILE_SIZE=96
    WALK_ANIM_SPEED = 8.0

    def __init__(self):
        super().__init__()
        self.player = None
        self.tile_x = 10
        self.tile_y = 11
        self.pixel_x = float(10 * TILE_SIZE)
        self.pixel_y = float(11 * TILE_SIZE)
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
        # Camera offset (scrolls to keep player visible)
        self.cam_x = 0.0
        self.cam_y = 0.0
        self._init_npcs()

    def _init_npcs(self):
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
                "target": None,
                "class": d["class"], "facing": "down", "frame": 0,
                "hair": d["hair"], "walk_timer": 0.0,
                "path": d["path"], "path_idx": 0, "pause_timer": 0.5,
            })

    def _update_camera(self):
        """Center camera on player, clamped to map bounds."""
        map_w = MAP_COLS * TILE_SIZE
        map_h = MAP_ROWS * TILE_SIZE

        target_cx = self.pixel_x + TILE_SIZE // 2 - VIRTUAL_WIDTH // 2
        target_cy = self.pixel_y + TILE_SIZE // 2 - VIRTUAL_HEIGHT // 2

        # Clamp so we don't show past the map edges
        self.cam_x = max(0, min(target_cx, map_w - VIRTUAL_WIDTH))
        self.cam_y = max(0, min(target_cy, map_h - VIRTUAL_HEIGHT))

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
        self._update_camera()
        self.entered = True

    def _update_npc_movement(self, dt):
        npc_speed = 240.0

        for npc in self._npc_sprites:
            target = npc["target"]

            if target is None:
                npc["pause_timer"] -= dt
                if npc["pause_timer"] <= 0:
                    waypoint = npc["path"][npc["path_idx"]]
                    tx, ty = waypoint
                    if tx == npc["tile_x"] and ty == npc["tile_y"]:
                        npc["path_idx"] = (npc["path_idx"] + 1) % len(npc["path"])
                        waypoint = npc["path"][npc["path_idx"]]
                        tx, ty = waypoint

                    dx = 1 if tx > npc["tile_x"] else (-1 if tx < npc["tile_x"] else 0)
                    dy = 1 if ty > npc["tile_y"] else (-1 if ty < npc["tile_y"] else 0)
                    if dx != 0:
                        dy = 0
                    next_tx = npc["tile_x"] + dx
                    next_ty = npc["tile_y"] + dy
                    npc["tile_x"] = next_tx
                    npc["tile_y"] = next_ty
                    npc["target"] = (next_tx, next_ty)

                    if dx > 0: npc["facing"] = "right"
                    elif dx < 0: npc["facing"] = "left"
                    elif dy > 0: npc["facing"] = "down"
                    elif dy < 0: npc["facing"] = "up"
                continue

            target_px = float(target[0] * TILE_SIZE)
            target_py = float(target[1] * TILE_SIZE)
            dx = target_px - npc["pixel_x"]
            dy = target_py - npc["pixel_y"]
            dist = max(abs(dx), abs(dy))

            if dist < 1.0:
                npc["pixel_x"] = target_px
                npc["pixel_y"] = target_py
                npc["target"] = None
                npc["pause_timer"] = 0.3
                npc["frame"] = 0
            else:
                step = npc_speed * dt
                if abs(dx) > 0.5:
                    npc["pixel_x"] += step if dx > 0 else -step
                if abs(dy) > 0.5:
                    npc["pixel_y"] += step if dy > 0 else -step
                npc["walk_timer"] += dt * self.WALK_ANIM_SPEED
                npc["frame"] = int(npc["walk_timer"]) % 4

    def update(self, dt):
        self.anim_time += dt
        self.dialogue.update(dt)
        self._update_npc_movement(dt)

        if self.dialogue.active:
            return
        if self.in_menu:
            if self.current_menu:
                self.current_menu.update(dt)
            return

        if self.move_target is not None:
            target_px = float(self.move_target[0] * TILE_SIZE)
            target_py = float(self.move_target[1] * TILE_SIZE)
            dx = target_px - self.pixel_x
            dy = target_py - self.pixel_y
            dist = math.sqrt(dx * dx + dy * dy)

            if dist < 1.0:
                self.pixel_x = target_px
                self.pixel_y = target_py
                self.tile_x = self.move_target[0]
                self.tile_y = self.move_target[1]
                self.move_target = None
                self.is_moving = False
                self._check_location()
                self._try_start_move()
            else:
                step = self.MOVE_SPEED * dt
                if step >= dist:
                    self.pixel_x = target_px
                    self.pixel_y = target_py
                else:
                    self.pixel_x += (dx / dist) * step
                    self.pixel_y += (dy / dist) * step
                self.walk_anim_timer += dt * self.WALK_ANIM_SPEED
                self.walk_frame = int(self.walk_anim_timer) % 4
                self.is_moving = True
        else:
            self.is_moving = False
            self.walk_frame = 0
            self._try_start_move()

        self._update_camera()

    def _try_start_move(self):
        keys = pygame.key.get_pressed()
        dx, dy = 0, 0
        if keys[pygame.K_UP] or keys[pygame.K_w]:
            dy = -1; self.facing = "up"
        elif keys[pygame.K_DOWN] or keys[pygame.K_s]:
            dy = 1; self.facing = "down"
        elif keys[pygame.K_LEFT] or keys[pygame.K_a]:
            dx = -1; self.facing = "left"
        elif keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            dx = 1; self.facing = "right"

        if dx != 0 or dy != 0:
            new_x = self.tile_x + dx
            new_y = self.tile_y + dy
            if self._can_walk(new_x, new_y):
                self.move_target = (new_x, new_y)
                self.tile_x = new_x
                self.tile_y = new_y
                self.is_moving = True
            else:
                self.walk_frame = 0

    def _can_walk(self, x, y):
        if x < 0 or x >= MAP_COLS or y < 0 or y >= MAP_ROWS:
            return False
        return TOWN_MAP[y][x] in WALKABLE

    def _check_location(self):
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

        if event.key in (pygame.K_z, pygame.K_RETURN):
            if self.move_target is not None:
                return
            if self.location_prompt:
                self._enter_location(self.location_prompt)
        elif event.key in (pygame.K_ESCAPE, pygame.K_x):
            self._open_status_menu()

    def _enter_location(self, location):
        action = location["action"]
        if action == "inn":
            self._open_inn_menu()
        elif action == "forest":
            if self.player.forest_turns > 0:
                self.manager.switch_to("forest", {"player": self.player})
            else:
                self.dialogue.show("You have no Forest Turns remaining today. Rest at the Inn first.", speaker="Gate Guard")
        elif action == "weapon_shop":
            self._open_weapon_shop()
        elif action == "armour_shop":
            self._open_armour_shop()
        elif action == "blacksmith":
            self._open_blacksmith()
        elif action == "pub":
            self.dialogue.show("The pub is lively tonight! Adventurers swap tales over mugs of ale.", speaker="Seth")

    def _open_inn_menu(self):
        cost = self.player.inn_cost()
        self.in_menu = True
        self.current_menu = {
            "type": "inn",
            "menu": SelectionMenu(
                items=[
                    {"label": f"Rest ({cost}g)", "value": "rest", "enabled": self.player.gold >= cost},
                    {"label": "Save Game", "value": "save"},
                    {"label": "Leave", "value": "leave"},
                ],
                x=VIRTUAL_WIDTH // 2 - 180,
                y=420,
                spacing=54,
                font_size=42,
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
            "menu": SelectionMenu(items=items, x=100, y=220, spacing=48, font_size=36),
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
            "menu": SelectionMenu(items=items, x=100, y=220, spacing=48, font_size=36),
        }

    def _open_blacksmith(self):
        from systems.inventory import can_craft_upgrade, get_upgrade_recipe
        items = []
        w = self.player.weapon
        w_recipe = get_upgrade_recipe(w.get("tier", "Wood"))
        if w_recipe:
            can, msg = can_craft_upgrade(self.player, w)
            label = f"Upgrade {w['name']} -> {w_recipe['result_tier']}"
            items.append({"label": label, "value": "upgrade_weapon", "enabled": can})
        else:
            items.append({"label": f"{w['name']} (MAX)", "value": "none", "enabled": False})

        a = self.player.armour
        a_recipe = get_upgrade_recipe(a.get("tier", "Wood"))
        if a_recipe:
            can, msg = can_craft_upgrade(self.player, a)
            label = f"Upgrade {a['name']} -> {a_recipe['result_tier']}"
            items.append({"label": label, "value": "upgrade_armour", "enabled": can})
        else:
            items.append({"label": f"{a['name']} (MAX)", "value": "none", "enabled": False})

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
            "menu": SelectionMenu(items=items, x=100, y=220, spacing=42, font_size=32),
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
                x=VIRTUAL_WIDTH - 400,
                y=130,
                spacing=48,
                font_size=42,
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
                    self.dialogue.show(f"You rest peacefully. A new day dawns! (Day {self.player.day})", speaker="Innkeeper")
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
                        "name": weapon["name"], "atk": weapon["atk"],
                        "special": weapon.get("special"), "tier": weapon.get("tier", "Wood"),
                        "type": weapon.get("type", "Sword"),
                    }
                    self.in_menu = False
                    self.current_menu = None
                    self.dialogue.show(f"You equipped the {weapon['name']}!", speaker="Shopkeeper")

        elif menu_type == "armour_shop":
            if isinstance(value, dict):
                armour = value
                if self.player.gold >= armour["cost"]:
                    self.player.gold -= armour["cost"]
                    self.player.armour = {
                        "name": armour["name"], "def": armour["def"],
                        "special": armour.get("special"), "tier": armour.get("tier", "Wood"),
                        "type": armour.get("type", "Shield"),
                    }
                    self.in_menu = False
                    self.current_menu = None
                    self.dialogue.show(f"You equipped the {armour['name']}!", speaker="Shopkeeper")

        elif menu_type == "blacksmith":
            if value in ("upgrade_weapon", "upgrade_armour"):
                from systems.inventory import perform_upgrade
                equip = self.player.weapon if value == "upgrade_weapon" else self.player.armour
                new_eq, msg = perform_upgrade(self.player, equip)
                if new_eq:
                    if value == "upgrade_weapon":
                        self.player.weapon = new_eq
                    else:
                        self.player.armour = new_eq
                self.in_menu = False
                self.current_menu = None
                self.dialogue.show(msg, speaker="Blacksmith")

        elif menu_type == "status":
            self.in_menu = False
            self.current_menu = None

    def _get_tile_surface(self, tile_type, x, y):
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
        TS = TILE_SIZE
        surf = pygame.Surface((TS, TS))
        surf.fill((34, 130, 34))
        post_color = (140, 100, 50)
        post_hi = (170, 130, 70)
        post_shadow = (100, 65, 30)
        # Posts
        for px_pos in [6, TS - 10]:
            for py_pos in range(6, TS - 6):
                for ddx in range(4):
                    c = post_hi if ddx < 2 else post_shadow
                    surf.set_at((px_pos + ddx, py_pos), c)
        # Rails
        for rail_y in [TS // 3, 2 * TS // 3]:
            for rx in range(TS):
                for rdy in range(4):
                    c = [post_hi, post_color, post_color, post_shadow][rdy]
                    surf.set_at((rx, rail_y + rdy), c)
        return surf

    def draw(self, surface):
        surface.fill(BLACK)

        cx = int(self.cam_x)
        cy = int(self.cam_y)

        # Determine visible tile range
        start_col = max(0, cx // TILE_SIZE)
        end_col = min(MAP_COLS, (cx + VIRTUAL_WIDTH) // TILE_SIZE + 2)
        start_row = max(0, cy // TILE_SIZE)
        end_row = min(MAP_ROWS, (cy + VIRTUAL_HEIGHT) // TILE_SIZE + 2)

        # Draw tiles
        for y in range(start_row, end_row):
            for x in range(start_col, end_col):
                tile = TOWN_MAP[y][x]
                tile_surf = self._get_tile_surface(tile, x, y)
                if tile_surf:
                    # Scale tile to TILE_SIZE if needed (procedural tiles are 16x16)
                    if tile_surf.get_width() != TILE_SIZE:
                        tile_surf = pygame.transform.scale(tile_surf, (TILE_SIZE, TILE_SIZE))
                    surface.blit(tile_surf, (x * TILE_SIZE - cx, y * TILE_SIZE - cy))

                if tile == FLOWER:
                    self._draw_flowers(surface, x, y, cx, cy)

        # Building labels
        self._draw_building_labels(surface, cx, cy)

        # NPCs
        for npc in self._npc_sprites:
            npc_sprite = get_player_sprite(npc["class"], npc["facing"], npc["frame"], npc["hair"])
            npc_px = int(npc["pixel_x"]) - cx + (TILE_SIZE - PLAYER_SPRITE_W) // 2
            npc_py = int(npc["pixel_y"]) - cy - (PLAYER_SPRITE_H - TILE_SIZE)
            surface.blit(npc_sprite, (npc_px, npc_py))

        # Player
        if self.player:
            player_sprite = get_player_sprite(self.player.player_class, self.facing, self.walk_frame)
            px = int(self.pixel_x) - cx + (TILE_SIZE - PLAYER_SPRITE_W) // 2
            py = int(self.pixel_y) - cy - (PLAYER_SPRITE_H - TILE_SIZE)
            surface.blit(player_sprite, (px, py))

        # HUD
        if self.player:
            draw_hud(surface, self.player)

        # Location prompt
        if self.location_prompt and not self.dialogue.active and not self.in_menu:
            loc = self.location_prompt
            prompt_text = f"Enter {loc['name']}? [Z]"
            draw_menu_box(surface, (VIRTUAL_WIDTH // 2 - 350, VIRTUAL_HEIGHT - 100, 700, 60))
            draw_text(surface, prompt_text, VIRTUAL_WIDTH // 2, VIRTUAL_HEIGHT - 75,
                      GOLD, 34, center=True)

        # Menus
        if self.in_menu and self.current_menu:
            overlay = pygame.Surface((VIRTUAL_WIDTH, VIRTUAL_HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 100))
            surface.blit(overlay, (0, 0))

            menu_type = self.current_menu["type"]
            if menu_type == "inn":
                draw_menu_box(surface, (VIRTUAL_WIDTH // 2 - 300, 300, 600, 300))
                draw_text(surface, "The Rusty Sword Inn", VIRTUAL_WIDTH // 2, 320, GOLD, 42, center=True)
            elif menu_type == "weapon_shop":
                draw_menu_box(surface, (60, 140, VIRTUAL_WIDTH - 120, VIRTUAL_HEIGHT - 280))
                draw_text(surface, "Weapon Shop", VIRTUAL_WIDTH // 2, 155, RED, 48, center=True)
            elif menu_type == "armour_shop":
                draw_menu_box(surface, (60, 140, VIRTUAL_WIDTH - 120, VIRTUAL_HEIGHT - 280))
                draw_text(surface, "Armour Shop", VIRTUAL_WIDTH // 2, 155, BLUE, 48, center=True)
            elif menu_type == "blacksmith":
                draw_menu_box(surface, (60, 140, VIRTUAL_WIDTH - 120, VIRTUAL_HEIGHT - 280))
                draw_text(surface, "Blacksmith - Forge & Upgrade", VIRTUAL_WIDTH // 2, 155, (200, 120, 50), 42, center=True)

            self.current_menu["menu"].draw(surface)

        # Dialogue
        self.dialogue.draw(surface)

    def _draw_building_labels(self, surface, cx, cy):
        """Draw building name labels above doors."""
        buildings = [
            (8, 3, "The Rusty Sword Inn", GOLD),
            (13, 3, "Seth's Pub", BROWN),
            (7, 7, "Weapon Shop", RED),
            (13, 7, "Armour Shop", BLUE),
            (2, 10, "Blacksmith", (200, 120, 50)),
            (10, 13, "Forest Gate", DARK_GREEN),
        ]
        for bx, by, label, color in buildings:
            screen_x = bx * TILE_SIZE + TILE_SIZE // 2 - cx
            screen_y = by * TILE_SIZE - 20 - cy
            if -200 < screen_x < VIRTUAL_WIDTH + 200 and -50 < screen_y < VIRTUAL_HEIGHT:
                draw_text(surface, label, screen_x, screen_y, color, 22, center=True)

    def _draw_flowers(self, surface, x, y, cx, cy):
        tx = x * TILE_SIZE - cx
        ty = y * TILE_SIZE - cy
        flower_data = [
            (15, 15, (255, 100, 120)),
            (55, 25, (120, 120, 255)),
            (30, 60, (255, 255, 100)),
            (70, 70, (255, 150, 200)),
        ]
        variant = (x * 3 + y * 7) % 4
        for i, (fx, fy, color) in enumerate(flower_data):
            if (i + variant) % 2 == 0:
                continue
            px, py = tx + fx, ty + fy
            # Stem
            pygame.draw.line(surface, (30, 100, 30), (px, py + 8), (px, py + 16), 2)
            # Petals
            for ddx, ddy in [(-4, 0), (4, 0), (0, -4), (0, 4)]:
                pygame.draw.circle(surface, color, (px + ddx, py + ddy), 3)
            # Center
            pygame.draw.circle(surface, (255, 255, 200), (px, py), 2)

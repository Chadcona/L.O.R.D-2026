# Battle Scene — turn-based JRPG combat (FF4/FF6 style)
# Full animation sequencer: step forward, attack, recoil, step back

import pygame
import random
import math
from scenes.scene_manager import Scene
from ui.menu import SelectionMenu, draw_text, draw_menu_box
from ui.hud import draw_bar
from systems.sprites import get_player_sprite, get_enemy_sprite
from settings import (
    BLACK, WHITE, GOLD, RED, GREEN, BLUE, GREY, DARK_GREY, CREAM, BROWN,
    VIRTUAL_WIDTH, VIRTUAL_HEIGHT
)


# --- Battle background (unchanged) ---

def _create_battle_bg():
    """Create a detailed SNES-style battle background with layered terrain."""
    surf = pygame.Surface((VIRTUAL_WIDTH, VIRTUAL_HEIGHT))
    for y in range(VIRTUAL_HEIGHT):
        t = y / VIRTUAL_HEIGHT
        if t < 0.35:
            st = t / 0.35
            r, g, b = int(8 + 15 * st), int(5 + 12 * st), int(40 + 50 * st)
        elif t < 0.5:
            ht = (t - 0.35) / 0.15
            r, g, b = int(23 + 50 * ht), int(17 + 40 * ht), int(90 - 20 * ht)
        elif t < 0.65:
            mt = (t - 0.5) / 0.15
            r, g, b = int(20 + 15 * mt), int(40 + 30 * mt), int(25 + 10 * mt)
        else:
            gt = (t - 0.65) / 0.35
            r, g, b = int(35 + 20 * gt), int(70 + 30 * gt), int(35 + 10 * gt)
        pygame.draw.line(surf, (r, g, b), (0, y), (VIRTUAL_WIDTH, y))

    star_positions = [(30, 8), (90, 15), (150, 5), (210, 20), (270, 12),
                      (55, 25), (180, 8), (250, 30), (120, 18), (300, 10)]
    for sx, sy in star_positions:
        surf.set_at((sx, sy), (200, 200, 220))

    for x in range(VIRTUAL_WIDTH):
        my = 75 + int(15 * math.sin(x * 0.02) + 8 * math.sin(x * 0.05) + 5 * math.sin(x * 0.1))
        for y in range(my, 120):
            t = (y - my) / max(1, 120 - my)
            surf.set_at((x, y), (int(15 + 20 * t), int(30 + 25 * t), int(20 + 15 * t)))

    tree_xs = [10, 35, 60, 85, 130, 160, 195, 225, 255, 280, 305]
    for tx in tree_xs:
        tree_h = 12 + (tx * 7) % 8
        tree_y = 108 - tree_h
        tree_c = (20 + (tx * 3) % 10, 45 + (tx * 5) % 15, 20 + (tx * 2) % 8)
        for dy in range(tree_h // 2):
            w = max(1, (tree_h // 2 - dy))
            for dx in range(-w, w + 1):
                px = tx + dx
                if 0 <= px < VIRTUAL_WIDTH:
                    surf.set_at((px, tree_y + dy), tree_c)
        for dy in range(tree_h // 2, tree_h):
            surf.set_at((tx, tree_y + dy), (50, 30, 15))

    for x in range(0, VIRTUAL_WIDTH, 6):
        gy = 155 + (x * 7) % 10
        grass_c = (45 + (x * 3) % 20, 90 + (x * 5) % 30, 40 + (x * 2) % 15)
        if gy < VIRTUAL_HEIGHT:
            surf.set_at((x, gy), grass_c)
            surf.set_at((x, gy - 1), (grass_c[0] + 10, grass_c[1] + 15, grass_c[2] + 5))
            surf.set_at((x + 1, gy), grass_c)

    stone_xs = [45, 120, 200, 275]
    for sx in stone_xs:
        sy = 158 + (sx * 3) % 6
        for dy in range(3):
            for dx in range(4):
                if sy + dy < VIRTUAL_HEIGHT:
                    surf.set_at((sx + dx, sy + dy), (90 + (dx + dy) * 8, 85 + (dx + dy) * 6, 75 + (dx + dy) * 5))

    return surf


_battle_bg_cache = None


# --- Animation sequencer ---

class BattleAnim:
    """A sequence of animation keyframes that plays out over time.

    Each keyframe is a dict with:
      - duration: seconds this keyframe lasts
      - on_start: optional callable run once when keyframe begins
      - on_finish: optional callable run once when keyframe ends

    During a keyframe, `progress` (0.0 -> 1.0) is available for interpolation.
    The animation stores named offsets that the draw code reads.
    """

    def __init__(self):
        self.keyframes = []
        self.current_idx = 0
        self.time = 0.0
        self.playing = False
        self.on_complete = None  # Called when entire sequence finishes

        # Animated values the draw code reads
        self.player_offset_x = 0.0
        self.player_offset_y = 0.0
        self.enemy_offset_x = 0.0
        self.enemy_offset_y = 0.0
        self.player_flash = 0.0    # 0-1, white flash intensity
        self.enemy_flash = 0.0
        self.player_frame = 0      # Walk frame for sprite
        self.screen_shake = 0.0
        self.screen_flash = 0.0    # 0-1, full screen white flash
        self.slash_effect = None    # (x, y, progress) or None
        self.spell_particles = []   # List of particle dicts
        self.heal_particles = []
        self.damage_number = None   # (x, y, text, color, progress) or None
        self.enemy_squash = 1.0     # Y scale for hit squash (1.0 = normal)

    def start(self, keyframes, on_complete=None):
        """Begin playing a sequence of keyframes."""
        self.keyframes = keyframes
        self.current_idx = 0
        self.time = 0.0
        self.playing = True
        self.on_complete = on_complete
        # Reset visual state
        self.player_offset_x = 0.0
        self.player_offset_y = 0.0
        self.enemy_offset_x = 0.0
        self.enemy_offset_y = 0.0
        self.player_flash = 0.0
        self.enemy_flash = 0.0
        self.player_frame = 0
        self.screen_shake = 0.0
        self.screen_flash = 0.0
        self.slash_effect = None
        self.spell_particles = []
        self.heal_particles = []
        self.damage_number = None
        self.enemy_squash = 1.0
        # Run first keyframe's on_start
        if self.keyframes:
            kf = self.keyframes[0]
            if "on_start" in kf:
                kf["on_start"](self)

    def update(self, dt):
        if not self.playing or not self.keyframes:
            return

        self.time += dt
        kf = self.keyframes[self.current_idx]
        duration = kf["duration"]

        # Progress within current keyframe
        progress = min(1.0, self.time / duration) if duration > 0 else 1.0

        # Call the keyframe's per-frame update if it has one
        if "update" in kf:
            kf["update"](self, progress, dt)

        # Update particles
        for p in self.spell_particles:
            p["life"] -= dt
            p["x"] += p["vx"] * dt
            p["y"] += p["vy"] * dt
        self.spell_particles = [p for p in self.spell_particles if p["life"] > 0]

        for p in self.heal_particles:
            p["life"] -= dt
            p["y"] += p["vy"] * dt
        self.heal_particles = [p for p in self.heal_particles if p["life"] > 0]

        # Advance damage number
        if self.damage_number:
            dn = self.damage_number
            dn["progress"] += dt * 2.0
            dn["y"] -= dt * 30  # Float upward
            if dn["progress"] >= 1.0:
                self.damage_number = None

        # Decay screen shake
        self.screen_shake = max(0, self.screen_shake - dt * 15)

        if self.time >= duration:
            # Keyframe finished
            if "on_finish" in kf:
                kf["on_finish"](self)
            self.current_idx += 1
            self.time = 0.0
            if self.current_idx >= len(self.keyframes):
                # Animation complete
                self.playing = False
                if self.on_complete:
                    self.on_complete()
            else:
                # Start next keyframe
                next_kf = self.keyframes[self.current_idx]
                if "on_start" in next_kf:
                    next_kf["on_start"](self)


# --- Animation builders ---

def _ease_out(t):
    """Deceleration curve."""
    return 1.0 - (1.0 - t) ** 2

def _ease_in(t):
    """Acceleration curve."""
    return t * t

def _ease_in_out(t):
    """Smooth in-out."""
    return t * t * (3.0 - 2.0 * t)


def build_player_attack_anim(damage_text, damage_color, is_crit=False):
    """Hero steps forward, slashes, enemy recoils, hero steps back."""
    step_dist = -70  # Move left toward enemy

    def step_forward(anim, progress, dt):
        t = _ease_out(progress)
        anim.player_offset_x = step_dist * t
        # Walk animation during step
        anim.player_frame = int(progress * 6) % 4

    def hold_slash(anim, progress, dt):
        anim.player_offset_x = step_dist
        anim.player_frame = 1  # Attack pose
        # Slash effect across enemy
        anim.slash_effect = {"x": 75, "y": 110, "progress": progress}

    def hit_impact(anim, progress, dt):
        anim.player_offset_x = step_dist
        anim.player_frame = 1
        # Enemy recoils right and squashes on hit
        anim.enemy_offset_x = 8 * math.sin(progress * math.pi * 3) * (1 - progress)
        anim.enemy_flash = 1.0 - progress
        anim.enemy_squash = 1.0 - 0.2 * math.sin(progress * math.pi)
        if progress < 0.15:
            anim.screen_shake = 4 if not is_crit else 7
            anim.screen_flash = 0.4 if not is_crit else 0.7

    def show_damage(anim):
        anim.damage_number = {
            "x": 75.0, "y": 95.0, "text": damage_text,
            "color": damage_color, "progress": 0.0
        }

    def step_back(anim, progress, dt):
        t = _ease_in_out(progress)
        anim.player_offset_x = step_dist * (1 - t)
        anim.player_frame = int(progress * 4) % 4
        anim.enemy_squash = 1.0

    return [
        {"duration": 0.2, "update": step_forward},
        {"duration": 0.12, "update": hold_slash},
        {"duration": 0.3, "update": hit_impact, "on_start": lambda a: show_damage(a)},
        {"duration": 0.15},  # Brief pause showing damage number
        {"duration": 0.2, "update": step_back},
    ]


def build_player_defend_anim():
    """Hero braces — brief flash and slight crouch."""
    def brace(anim, progress, dt):
        # Slight crouch
        anim.player_offset_y = 3 * math.sin(progress * math.pi)
        anim.player_flash = 0.5 * math.sin(progress * math.pi)
        anim.player_frame = 2  # Stable stance

    return [
        {"duration": 0.4, "update": brace},
        {"duration": 0.15},
    ]


def build_player_magic_anim(spell_name, damage_text, damage_color):
    """Hero casts — glow, particles fly to enemy, enemy hit."""
    def cast_charge(anim, progress, dt):
        anim.player_flash = 0.3 + 0.4 * math.sin(progress * math.pi * 4)
        anim.player_frame = 3  # Casting pose
        # Spawn spell particles from player toward enemy
        if random.random() < 0.4:
            px = 240 + anim.player_offset_x
            py = 115
            color = (255, 120, 30) if "Fire" in spell_name else (100, 180, 255)
            anim.spell_particles.append({
                "x": px, "y": py + random.uniform(-10, 10),
                "vx": random.uniform(-180, -120),
                "vy": random.uniform(-20, 20),
                "color": color, "life": 0.5,
                "size": random.randint(2, 4),
            })

    def spell_hit(anim, progress, dt):
        anim.player_frame = 3
        anim.enemy_flash = 0.8 * (1.0 - progress)
        anim.enemy_offset_x = 5 * math.sin(progress * math.pi * 4) * (1 - progress)
        anim.enemy_squash = 1.0 - 0.15 * math.sin(progress * math.pi)
        if progress < 0.1:
            anim.screen_flash = 0.5
            anim.screen_shake = 4
        # Burst particles at enemy location
        if progress < 0.3 and random.random() < 0.5:
            color = (255, 160, 50) if "Fire" in spell_name else (130, 200, 255)
            anim.spell_particles.append({
                "x": 75 + random.uniform(-15, 15),
                "y": 115 + random.uniform(-15, 15),
                "vx": random.uniform(-40, 40),
                "vy": random.uniform(-60, -20),
                "color": color, "life": 0.4,
                "size": random.randint(2, 5),
            })

    def show_damage(anim):
        anim.damage_number = {
            "x": 75.0, "y": 95.0, "text": damage_text,
            "color": damage_color, "progress": 0.0,
        }

    return [
        {"duration": 0.5, "update": cast_charge},
        {"duration": 0.4, "update": spell_hit, "on_start": lambda a: show_damage(a)},
        {"duration": 0.2},
    ]


def build_player_steal_anim(success, text):
    """Hero dashes to enemy, grabs, dashes back."""
    step_dist = -80

    def dash_forward(anim, progress, dt):
        t = _ease_out(progress)
        anim.player_offset_x = step_dist * t
        anim.player_frame = int(progress * 8) % 4

    def grab(anim, progress, dt):
        anim.player_offset_x = step_dist
        anim.player_frame = 1
        if success:
            # Gold sparkle at grab point
            if random.random() < 0.4:
                anim.spell_particles.append({
                    "x": 90 + random.uniform(-5, 5),
                    "y": 120 + random.uniform(-5, 5),
                    "vx": random.uniform(-20, 20),
                    "vy": random.uniform(-40, -10),
                    "color": (255, 220, 50), "life": 0.4,
                    "size": 2,
                })

    def dash_back(anim, progress, dt):
        t = _ease_in_out(progress)
        anim.player_offset_x = step_dist * (1 - t)
        anim.player_frame = int(progress * 6) % 4

    def show_text(anim):
        color = GOLD if success else (180, 180, 180)
        anim.damage_number = {
            "x": 75.0, "y": 100.0, "text": text,
            "color": color, "progress": 0.0,
        }

    return [
        {"duration": 0.15, "update": dash_forward},
        {"duration": 0.25, "update": grab, "on_start": lambda a: show_text(a)},
        {"duration": 0.18, "update": dash_back},
    ]


def build_player_item_anim(text):
    """Hero uses item — glow and heal particles."""
    def use_item(anim, progress, dt):
        anim.player_flash = 0.3 * math.sin(progress * math.pi)
        anim.player_frame = 2
        # Green heal sparkles rising from player
        if random.random() < 0.4:
            anim.heal_particles.append({
                "x": 245 + random.uniform(-10, 10),
                "y": 140 + random.uniform(-5, 5),
                "vy": random.uniform(-40, -20),
                "color": (100, 255, 100), "life": 0.6,
                "size": random.randint(2, 3),
            })

    def show_text(anim):
        anim.damage_number = {
            "x": 245.0, "y": 95.0, "text": text,
            "color": GREEN, "progress": 0.0,
        }

    return [
        {"duration": 0.5, "update": use_item, "on_start": lambda a: show_text(a)},
        {"duration": 0.15},
    ]


def build_player_flee_anim(success):
    """Hero turns and runs right (off screen if success, back if fail)."""
    def run_right(anim, progress, dt):
        t = _ease_in(progress)
        anim.player_offset_x = 80 * t if success else 30 * math.sin(progress * math.pi)
        anim.player_frame = int(progress * 8) % 4

    return [
        {"duration": 0.35, "update": run_right},
    ]


def build_player_berserk_anim(damage_text, damage_color):
    """Warrior berserk — red flash, big step, powerful slash."""
    step_dist = -80

    def charge_up(anim, progress, dt):
        anim.player_flash = 0.5 * abs(math.sin(progress * math.pi * 6))
        anim.player_frame = 2
        anim.screen_shake = 1.5

    def lunge(anim, progress, dt):
        t = _ease_out(progress)
        anim.player_offset_x = step_dist * t
        anim.player_frame = 1

    def double_slash(anim, progress, dt):
        anim.player_offset_x = step_dist
        anim.player_frame = 1
        anim.slash_effect = {"x": 70, "y": 105, "progress": progress}
        anim.enemy_flash = 0.8 * abs(math.sin(progress * math.pi * 3))
        anim.enemy_offset_x = 10 * math.sin(progress * math.pi * 5) * (1 - progress)
        anim.enemy_squash = 1.0 - 0.25 * abs(math.sin(progress * math.pi * 2))
        if progress < 0.15:
            anim.screen_shake = 8
            anim.screen_flash = 0.8

    def show_damage(anim):
        anim.damage_number = {
            "x": 75.0, "y": 90.0, "text": damage_text,
            "color": damage_color, "progress": 0.0,
        }

    def step_back(anim, progress, dt):
        anim.player_offset_x = step_dist * (1 - _ease_in_out(progress))
        anim.player_frame = int(progress * 4) % 4
        anim.enemy_squash = 1.0

    return [
        {"duration": 0.3, "update": charge_up},
        {"duration": 0.12, "update": lunge},
        {"duration": 0.35, "update": double_slash, "on_start": lambda a: show_damage(a)},
        {"duration": 0.15},
        {"duration": 0.22, "update": step_back},
    ]


def build_enemy_attack_anim(damage_text, damage_color):
    """Enemy lunges toward player, hits, recoils back."""
    step_dist = 60

    def lunge_forward(anim, progress, dt):
        t = _ease_out(progress)
        anim.enemy_offset_x = step_dist * t

    def strike(anim, progress, dt):
        anim.enemy_offset_x = step_dist
        anim.player_flash = 0.8 * (1.0 - progress)
        anim.player_offset_x = -6 * math.sin(progress * math.pi * 4) * (1 - progress)
        if progress < 0.15:
            anim.screen_shake = 5

    def show_damage(anim):
        anim.damage_number = {
            "x": 245.0, "y": 95.0, "text": damage_text,
            "color": damage_color, "progress": 0.0,
        }

    def step_back(anim, progress, dt):
        t = _ease_in_out(progress)
        anim.enemy_offset_x = step_dist * (1 - t)

    return [
        {"duration": 0.18, "update": lunge_forward},
        {"duration": 0.3, "update": strike, "on_start": lambda a: show_damage(a)},
        {"duration": 0.22, "update": step_back},
        {"duration": 0.1},
    ]


def build_enemy_defend_anim():
    """Enemy braces."""
    def brace(anim, progress, dt):
        anim.enemy_flash = 0.3 * math.sin(progress * math.pi)
        anim.enemy_squash = 1.0 + 0.08 * math.sin(progress * math.pi)

    return [
        {"duration": 0.4, "update": brace},
    ]


def build_enemy_special_anim(spell_name, damage_text, damage_color):
    """Enemy casts a special — glow, effect, player hit."""
    def cast(anim, progress, dt):
        anim.enemy_flash = 0.4 * abs(math.sin(progress * math.pi * 4))
        # Dark particles from enemy
        if random.random() < 0.3:
            anim.spell_particles.append({
                "x": 75 + random.uniform(-10, 10),
                "y": 115 + random.uniform(-10, 10),
                "vx": random.uniform(80, 140),
                "vy": random.uniform(-15, 15),
                "color": (160, 80, 200), "life": 0.4,
                "size": random.randint(2, 4),
            })

    def hit(anim, progress, dt):
        anim.player_flash = 0.7 * (1.0 - progress)
        anim.player_offset_x = -4 * math.sin(progress * math.pi * 3) * (1 - progress)
        if progress < 0.1:
            anim.screen_shake = 3

    def show_damage(anim):
        anim.damage_number = {
            "x": 245.0, "y": 95.0, "text": damage_text,
            "color": damage_color, "progress": 0.0,
        }

    return [
        {"duration": 0.45, "update": cast},
        {"duration": 0.35, "update": hit, "on_start": lambda a: show_damage(a)},
        {"duration": 0.1},
    ]


def build_enemy_death_anim():
    """Enemy flashes, squashes, and fades out."""
    def death(anim, progress, dt):
        anim.enemy_flash = abs(math.sin(progress * math.pi * 6)) * (1 - progress)
        anim.enemy_squash = max(0.0, 1.0 - progress * 1.2)
        anim.enemy_offset_y = progress * 10

    return [
        {"duration": 0.8, "update": death},
    ]


# --- Main battle scene ---

class BattleScene(Scene):
    """Turn-based combat screen with full SNES-style battle animations."""

    # Home positions (pixels on the virtual canvas)
    PLAYER_HOME_X = 240
    PLAYER_HOME_Y = 100
    ENEMY_HOME_X = 50
    ENEMY_HOME_Y = 95

    def __init__(self):
        super().__init__()
        self.player = None
        self.enemy = None
        self.state = "start"  # start, player_turn, animating, enemy_turn, victory, defeat, etc.
        self.message_log = []
        self.message_timer = 0
        self.action_menu = None
        self.anim_time = 0
        self.return_scene = "forest"
        self.battle_rewards = None
        self.perfect_battle = True
        self.enemy_sprite = None
        self.anim = BattleAnim()
        # Pending action after animation finishes
        self._pending_action = None
        self._enemy_alive_at_draw = True

    def on_enter(self, data=None):
        global _battle_bg_cache
        if _battle_bg_cache is None:
            _battle_bg_cache = _create_battle_bg()

        if data:
            self.player = data.get("player")
            self.enemy = data.get("enemy")
            self.return_scene = data.get("return_to", "forest")

        self.state = "start"
        self.message_log = [f"A wild {self.enemy.name} appears!"]
        self.message_timer = 1.5
        self.perfect_battle = True
        self.battle_rewards = None
        self.player.special_used = False
        self._pending_action = None
        self._enemy_alive_at_draw = True

        self.enemy_sprite = get_enemy_sprite(self.enemy.name, self.enemy.sprite_color, 48)
        self.anim = BattleAnim()
        self._create_action_menu()

    def _create_action_menu(self):
        items = [
            {"label": "Attack", "value": "attack"},
            {"label": "Defend", "value": "defend"},
            {"label": "Item", "value": "item"},
            {"label": "Special", "value": "special"},
            {"label": "Flee", "value": "flee"},
        ]
        self.action_menu = SelectionMenu(
            items=items, x=170, y=185, spacing=14, font_size=12,
            show_box=False
        )

    def update(self, dt):
        self.anim_time += dt

        # Update animation sequencer
        if self.anim.playing:
            self.anim.update(dt)
            return

        if self.message_timer > 0:
            self.message_timer -= dt
            if self.message_timer <= 0:
                if self.state == "start":
                    self.state = "player_turn"
                elif self.state == "enemy_turn_done":
                    if not self.player.is_alive():
                        self.state = "defeat"
                        self._handle_defeat()
                    else:
                        self.state = "player_turn"
                elif self.state == "victory":
                    self._apply_rewards()
                elif self.state == "flee_success":
                    self._return_from_battle()
                elif self.state == "defeat_done":
                    self._return_from_battle()
                elif self.state == "reward_done":
                    self._return_from_battle()
            return

        if self.state == "player_turn" and self.action_menu:
            self.action_menu.update(dt)

    def handle_event(self, event):
        # Skip messages
        if self.message_timer > 0:
            if event.type == pygame.KEYDOWN and event.key in (pygame.K_z, pygame.K_RETURN):
                self.message_timer = 0.01
            return

        # Can't interact during animations
        if self.anim.playing:
            return

        if self.state == "player_turn" and self.action_menu:
            self.action_menu.handle_event(event)
            if self.action_menu.confirmed:
                self._execute_player_action(self.action_menu.get_selected_value())

    # --- Player actions (now launch animations) ---

    def _execute_player_action(self, action):
        self.state = "animating"

        if action == "attack":
            damage = self._calc_player_damage()
            crit = random.randint(1, 100) <= self.player.lck * 2
            if crit:
                damage = int(damage * 1.5)
            actual = self.enemy.take_damage(damage)
            msg = f"{self.player.name} attacks for {actual} damage!"
            if crit:
                msg += " CRITICAL HIT!"
            self.message_log = [msg]

            dmg_text = f"{actual}" + (" CRIT!" if crit else "")
            dmg_color = (255, 255, 80) if crit else WHITE
            keyframes = build_player_attack_anim(dmg_text, dmg_color, is_crit=crit)
            self.anim.start(keyframes, on_complete=lambda: self._after_player_action())

        elif action == "defend":
            self.message_log = [f"{self.player.name} defends!"]
            keyframes = build_player_defend_anim()
            self.anim.start(keyframes, on_complete=lambda: self._after_player_action())

        elif action == "special":
            self._use_special_animated()

        elif action == "item":
            self._use_item_animated()

        elif action == "flee":
            flee_chance = 40 + self.player.agi * 3 - self.enemy.agi
            success = random.randint(1, 100) <= flee_chance
            if success:
                self.message_log = ["Got away safely!"]
            else:
                self.message_log = ["Couldn't escape!"]
                self.perfect_battle = False
            keyframes = build_player_flee_anim(success)
            if success:
                self.anim.start(keyframes, on_complete=lambda: self._finish_flee(True))
            else:
                self.anim.start(keyframes, on_complete=lambda: self._finish_flee(False))

    def _use_special_animated(self):
        from systems.player import CLASSES
        cls_data = CLASSES[self.player.player_class]
        special_name = cls_data["special"]

        if self.player.special_used and special_name == "Berserk":
            self.message_log = ["Berserk already used this battle!"]
            self.state = "player_turn"
            self._create_action_menu()
            return

        if special_name == "Berserk":
            damage = self._calc_player_damage() * 2
            actual = self.enemy.take_damage(damage)
            self.message_log = [f"BERSERK! {actual} damage!"]
            self.player.special_used = True
            keyframes = build_player_berserk_anim(str(actual), (255, 80, 80))
            self.anim.start(keyframes, on_complete=lambda: self._after_player_action())

        elif special_name == "Steal":
            success = random.randint(1, 100) <= 30 + self.player.lck * 3
            if success:
                stolen_gold = random.randint(5, self.enemy.gold_reward)
                self.player.gold += stolen_gold
                text = f"+{stolen_gold}g"
                self.message_log = [f"Stole {stolen_gold} gold!"]
            else:
                text = "Miss!"
                self.message_log = ["Steal failed!"]
            keyframes = build_player_steal_anim(success, text)
            self.anim.start(keyframes, on_complete=lambda: self._after_player_action())

        elif special_name == "Spellcast":
            if self.player.mp >= 10:
                self.player.mp -= 10
                spell_damage = self.player.int * 3 + random.randint(5, 15)
                self.enemy.hp = max(0, self.enemy.hp - spell_damage)
                self.message_log = [f"Cast Fire! {spell_damage} magic damage!"]
                keyframes = build_player_magic_anim("Fire", str(spell_damage), (255, 160, 50))
                self.anim.start(keyframes, on_complete=lambda: self._after_player_action())
            else:
                self.message_log = ["Not enough MP!"]
                self.state = "player_turn"
                self._create_action_menu()

    def _use_item_animated(self):
        for item in self.player.inventory:
            if item.get("effect") == "heal" and item.get("count", 0) > 0:
                heal_amount = item["value"]
                self.player.heal(heal_amount)
                item["count"] -= 1
                if item["count"] <= 0:
                    self.player.inventory.remove(item)
                self.message_log = [f"Used {item['name']}! Restored {heal_amount} HP!"]
                keyframes = build_player_item_anim(f"+{heal_amount} HP")
                self.anim.start(keyframes, on_complete=lambda: self._after_player_action())
                return
        self.message_log = ["No healing items!"]
        self.state = "player_turn"
        self._create_action_menu()

    def _finish_flee(self, success):
        if success:
            self.state = "flee_success"
            self.message_timer = 0.5
        else:
            self._after_player_action()

    def _after_player_action(self):
        """Called after player action animation finishes."""
        # Check if enemy died — play death animation
        if not self.enemy.is_alive():
            self._enemy_alive_at_draw = True  # Still draw during death anim
            keyframes = build_enemy_death_anim()
            self.anim.start(keyframes, on_complete=lambda: self._enemy_died())
            return

        # Otherwise, enemy takes its turn
        self._start_enemy_turn()

    def _enemy_died(self):
        self._enemy_alive_at_draw = False
        self.state = "victory"
        self.message_log.append(f"{self.enemy.name} defeated!")
        self.message_timer = 1.0

    def _start_enemy_turn(self):
        """Enemy turn — choose action, play animation, apply damage after."""
        self.state = "animating"

        if not self.enemy.is_alive():
            return

        action = self.enemy.choose_action()

        if action == "attack":
            raw = self.enemy.get_attack_damage()
            actual = self.player.take_damage(raw)
            self.message_log = [f"{self.enemy.name} attacks for {actual} damage!"]
            if actual > 0:
                self.perfect_battle = False
            dmg_color = RED if actual > 0 else (180, 180, 180)
            keyframes = build_enemy_attack_anim(str(actual), dmg_color)
            self.anim.start(keyframes, on_complete=lambda: self._after_enemy_action())

        elif action == "defend":
            self.enemy.defending = True
            self.message_log = [f"{self.enemy.name} is defending!"]
            keyframes = build_enemy_defend_anim()
            self.anim.start(keyframes, on_complete=lambda: self._after_enemy_action())

        elif action == "special":
            if self.enemy.special == "sleep_spell":
                actual = self.player.take_damage(self.enemy.atk // 2)
                self.message_log = [f"{self.enemy.name} casts Sleep!"]
                if actual > 0:
                    self.perfect_battle = False
                keyframes = build_enemy_special_anim("Sleep", str(actual), (160, 80, 200))
                self.anim.start(keyframes, on_complete=lambda: self._after_enemy_action())
            else:
                self.message_log = [f"{self.enemy.name} does something strange!"]
                self._after_enemy_action()
        else:
            self._after_enemy_action()

        # Handle passive regen
        if self.enemy.special == "regenerate" and self.enemy.is_alive():
            healed = 5
            self.enemy.hp = min(self.enemy.max_hp, self.enemy.hp + healed)

    def _after_enemy_action(self):
        """After enemy animation finishes."""
        self.state = "enemy_turn_done"
        self.message_timer = 0.5
        self._create_action_menu()

    def _do_enemy_turn(self):
        """Legacy hook called from main.py timer — no longer needed since we
        now trigger enemy turn directly from _after_player_action.
        Keep as no-op for compatibility."""
        pass

    # --- Damage calc ---

    def _calc_player_damage(self):
        base = self.player.atk
        variance = random.randint(-base // 6, base // 6)
        return max(1, base + variance)

    # --- Defeat / Rewards ---

    def _handle_defeat(self):
        gold_lost = self.player.gold // 4
        self.player.gold -= gold_lost
        self.player.hp = self.player.max_hp // 4
        self.message_log = [
            f"{self.player.name} was knocked out!",
            f"Lost {gold_lost} gold..."
        ]
        self.state = "defeat_done"
        self.message_timer = 2.0

    def _apply_rewards(self):
        exp = self.enemy.exp_reward
        gold = self.enemy.gold_reward
        if self.perfect_battle:
            exp = int(exp * 1.25)
            self.message_log.append("Perfect battle! +25% EXP!")

        level_msgs = self.player.gain_exp(exp)
        self.player.gold += gold
        self.message_log.append(f"Gained {exp} EXP and {gold} gold!")
        self.message_log.extend(level_msgs)

        # Roll for loot drops
        from systems.inventory import MATERIALS
        drops = self.enemy.roll_loot()
        for drop_name in drops:
            mat = MATERIALS.get(drop_name)
            if mat:
                self.player.add_item({"name": drop_name, "type": mat["type"], "count": 1})
                self.message_log.append(f"Found {drop_name}!")

        self.state = "reward_done"
        self.message_timer = 2.0 + len(drops) * 0.5

    def _return_from_battle(self):
        self.manager.switch_to(self.return_scene, {"player": self.player})

    # --- Drawing ---

    def draw(self, surface):
        # Background
        if _battle_bg_cache:
            surface.blit(_battle_bg_cache, (0, 0))
        else:
            surface.fill(BLACK)

        a = self.anim  # Shorthand

        # Screen shake from animation
        shake_x = int(random.uniform(-a.screen_shake, a.screen_shake)) if a.screen_shake > 0.5 else 0
        shake_y = int(random.uniform(-a.screen_shake, a.screen_shake)) if a.screen_shake > 0.5 else 0

        # --- Enemy drawing ---
        if self.enemy and self._enemy_alive_at_draw:
            ex = self.ENEMY_HOME_X + int(a.enemy_offset_x) + shake_x
            ey = self.ENEMY_HOME_Y + int(getattr(a, 'enemy_offset_y', 0)) + shake_y
            # Breathing bob when idle
            if not a.playing:
                ey += int(math.sin(self.anim_time * 2) * 2)

            # Ground shadow
            shadow_surf = pygame.Surface((52, 12), pygame.SRCALPHA)
            pygame.draw.ellipse(shadow_surf, (0, 0, 0, 50), (0, 0, 52, 12))
            surface.blit(shadow_surf, (ex - 2, self.ENEMY_HOME_Y + 53 + shake_y))

            # Enemy sprite with squash/stretch
            enemy_draw = self.enemy_sprite
            sprite_w = enemy_draw.get_width()
            sprite_h = enemy_draw.get_height()
            squash = a.enemy_squash
            if abs(squash - 1.0) > 0.01:
                new_h = max(1, int(sprite_h * squash))
                new_w = int(sprite_w * (1.0 + (1.0 - squash) * 0.5))  # Stretch width when squashed
                enemy_draw = pygame.transform.scale(enemy_draw, (new_w, new_h))
                ey += sprite_h - new_h  # Keep feet grounded
                ex -= (new_w - sprite_w) // 2

            # Hit flash: tint white
            if a.enemy_flash > 0.05:
                enemy_draw = enemy_draw.copy()
                flash_alpha = int(min(200, a.enemy_flash * 250))
                white_overlay = pygame.Surface(enemy_draw.get_size(), pygame.SRCALPHA)
                white_overlay.fill((255, 255, 255, flash_alpha))
                enemy_draw.blit(white_overlay, (0, 0), special_flags=pygame.BLEND_RGBA_ADD)

            surface.blit(enemy_draw, (ex, ey))

        # --- Slash effect ---
        if a.slash_effect:
            self._draw_slash_effect(surface, a.slash_effect, shake_x, shake_y)

        # --- Spell particles ---
        for p in a.spell_particles:
            ps = pygame.Surface((p["size"] * 2, p["size"] * 2), pygame.SRCALPHA)
            alpha = int(min(255, (p["life"] / 0.5) * 255))
            color = (*p["color"], alpha)
            pygame.draw.circle(ps, color, (p["size"], p["size"]), p["size"])
            surface.blit(ps, (int(p["x"]) - p["size"] + shake_x,
                              int(p["y"]) - p["size"] + shake_y))

        # --- Heal particles ---
        for p in a.heal_particles:
            ps = pygame.Surface((p["size"] * 2, p["size"] * 2), pygame.SRCALPHA)
            alpha = int(min(255, (p["life"] / 0.6) * 255))
            color = (*p["color"], alpha)
            pygame.draw.circle(ps, color, (p["size"], p["size"]), p["size"])
            surface.blit(ps, (int(p["x"]) - p["size"] + shake_x,
                              int(p["y"]) - p["size"] + shake_y))

        # --- Screen flash ---
        if a.screen_flash > 0.02:
            flash_surf = pygame.Surface((VIRTUAL_WIDTH, VIRTUAL_HEIGHT), pygame.SRCALPHA)
            flash_surf.fill((255, 255, 255, int(min(200, a.screen_flash * 300))))
            surface.blit(flash_surf, (0, 0))
            a.screen_flash = max(0, a.screen_flash - 0.05)

        # --- Player drawing ---
        if self.player:
            px = self.PLAYER_HOME_X + int(a.player_offset_x) + shake_x
            py = self.PLAYER_HOME_Y + int(a.player_offset_y) + shake_y
            # Idle breathing
            if not a.playing:
                py += int(math.sin(self.anim_time * 1.5 + 1) * 1)

            # Ground shadow
            shadow_surf = pygame.Surface((36, 8), pygame.SRCALPHA)
            pygame.draw.ellipse(shadow_surf, (0, 0, 0, 50), (0, 0, 36, 8))
            surface.blit(shadow_surf, (self.PLAYER_HOME_X - 2 + int(a.player_offset_x) + shake_x,
                                       self.PLAYER_HOME_Y + 52 + shake_y))

            # Get sprite with walk frame from animation
            frame = a.player_frame if a.playing else 0
            player_spr = get_player_sprite(self.player.player_class, "left", frame)
            scaled_player = pygame.transform.scale(player_spr, (32, 48))

            # Player flash
            if a.player_flash > 0.05:
                scaled_player = scaled_player.copy()
                flash_alpha = int(min(200, a.player_flash * 250))
                white_overlay = pygame.Surface(scaled_player.get_size(), pygame.SRCALPHA)
                white_overlay.fill((255, 255, 255, flash_alpha))
                scaled_player.blit(white_overlay, (0, 0), special_flags=pygame.BLEND_RGBA_ADD)

            surface.blit(scaled_player, (px, py))

        # --- Damage numbers (floating) ---
        if a.damage_number:
            dn = a.damage_number
            # Bounce up then float
            t = dn["progress"]
            dy = -15 * math.sin(t * math.pi * 0.7)
            alpha = max(0, 255 - int(t * 200))
            if alpha > 0:
                draw_text(surface, dn["text"],
                          int(dn["x"]) + shake_x,
                          int(dn["y"] + dy) + shake_y,
                          dn["color"], 14, center=True, shadow=True)

        # --- Enemy HP bar ---
        if self.enemy:
            draw_menu_box(surface, (10, 30, 135, 28))
            draw_text(surface, self.enemy.name, 16, 33, WHITE, 11)
            draw_bar(surface, 16, 45, 110, 8, self.enemy.hp, self.enemy.max_hp, RED)
            draw_text(surface, f"{self.enemy.hp}/{self.enemy.max_hp}", 130, 44, WHITE, 8)

        # --- Player stats ---
        draw_menu_box(surface, (175, 30, 135, 38))
        draw_text(surface, f"{self.player.name}", 182, 33, GOLD, 11)
        draw_text(surface, f"Lv.{self.player.level} {self.player.player_class}", 182, 44, CREAM, 9)
        draw_bar(surface, 182, 55, 70, 7, self.player.hp, self.player.max_hp, GREEN)
        draw_text(surface, f"HP {self.player.hp}/{self.player.max_hp}", 256, 54, WHITE, 8)
        draw_bar(surface, 182, 63, 50, 4, self.player.mp, self.player.max_mp, BLUE)
        draw_text(surface, f"MP {self.player.mp}/{self.player.max_mp}", 236, 62, WHITE, 7)

        # --- Message log ---
        draw_menu_box(surface, (5, 170, 155, 65))
        y_offset = 175
        for msg in self.message_log[-4:]:
            draw_text(surface, msg, 10, y_offset, WHITE, 10)
            y_offset += 13

        # --- Action menu ---
        if self.state == "player_turn":
            draw_menu_box(surface, (162, 170, 153, 65))
            draw_text(surface, "Command", 170, 174, GOLD, 11)
            if self.action_menu:
                self.action_menu.draw(surface)

    def _draw_slash_effect(self, surface, slash, shake_x, shake_y):
        """Draw an animated sword slash arc — classic FF style."""
        x = slash["x"] + shake_x
        y = slash["y"] + shake_y
        p = slash["progress"]

        slash_surf = pygame.Surface((60, 40), pygame.SRCALPHA)
        # Draw arc of slash lines
        num_lines = 5
        for i in range(num_lines):
            t = (i / num_lines + p * 0.3) * math.pi * 0.6
            x1 = 30 + int(25 * math.cos(t - 0.3))
            y1 = 20 + int(18 * math.sin(t - 0.3))
            x2 = 30 + int(25 * math.cos(t + 0.3))
            y2 = 20 + int(18 * math.sin(t + 0.3))

            alpha = int(255 * max(0, 1 - abs(p * num_lines - i) / 2))
            if alpha > 10:
                color = (255, 255, 255, min(255, alpha))
                # Thick slash line
                pygame.draw.line(slash_surf, color, (x1, y1), (x2, y2), 2)
                # Glow
                glow_color = (255, 255, 200, min(255, alpha // 2))
                pygame.draw.line(slash_surf, glow_color, (x1 - 1, y1 - 1), (x2 + 1, y2 + 1), 3)

        # Slash sparks
        if p < 0.8:
            for _ in range(2):
                sx = 30 + random.randint(-15, 15)
                sy = 20 + random.randint(-10, 10)
                alpha = random.randint(100, 255)
                pygame.draw.circle(slash_surf, (255, 255, 200, alpha), (sx, sy), 1)

        surface.blit(slash_surf, (x - 30, y - 20))

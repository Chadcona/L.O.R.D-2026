# Mystic Forest — exploration with rich SNES-style visuals (1080p)

import pygame
import random
import math
from scenes.scene_manager import Scene
from ui.menu import draw_text, draw_menu_box, SelectionMenu
from ui.hud import draw_hud
from systems.enemy import spawn_random_enemy, get_zone_for_level
from settings import (
    BLACK, WHITE, GOLD, GREEN, DARK_GREEN, GREY, CREAM,
    VIRTUAL_WIDTH, VIRTUAL_HEIGHT
)


def _create_forest_bg():
    """Pre-render a detailed 1080p forest background."""
    surf = pygame.Surface((VIRTUAL_WIDTH, VIRTUAL_HEIGHT))

    # Sky gradient through canopy
    for y in range(VIRTUAL_HEIGHT):
        t = y / VIRTUAL_HEIGHT
        if t < 0.15:
            r = int(8 + 15 * t * 6)
            g = int(20 + 40 * t * 6)
            b = int(12 + 20 * t * 6)
        elif t < 0.4:
            ct = (t - 0.15) / 0.25
            r = int(15 + 8 * ct)
            g = int(35 + 25 * ct)
            b = int(15 + 5 * ct)
        elif t < 0.6:
            mt = (t - 0.4) / 0.2
            r = int(23 + 12 * mt)
            g = int(60 - 10 * mt)
            b = int(20 + 8 * mt)
        else:
            ft = (t - 0.6) / 0.4
            r = int(35 + 20 * ft)
            g = int(50 + 30 * ft)
            b = int(28 + 15 * ft)
        pygame.draw.line(surf, (r, g, b), (0, y), (VIRTUAL_WIDTH, y))

    rng = random.Random(456)

    # Background trees (far layer)
    for _ in range(20):
        tx = rng.randint(0, VIRTUAL_WIDTH)
        trunk_h = rng.randint(300, 600)
        trunk_y = rng.randint(100, 350)
        trunk_w = rng.randint(12, 30)
        trunk_c = (30 + rng.randint(0, 15), 22 + rng.randint(0, 10), 12 + rng.randint(0, 8))

        for y in range(trunk_y, min(trunk_y + trunk_h, VIRTUAL_HEIGHT)):
            for dx in range(-trunk_w // 2, trunk_w // 2 + 1):
                px = tx + dx
                if 0 <= px < VIRTUAL_WIDTH:
                    noise = ((y * 3 + dx * 7) % 5) * 3
                    c = (trunk_c[0] + noise, trunk_c[1] + noise, trunk_c[2] + noise)
                    surf.set_at((px, y), c)

        canopy_r = rng.randint(60, 120)
        canopy_y = trunk_y - canopy_r // 2
        canopy_c = (20 + rng.randint(0, 20), 50 + rng.randint(0, 30), 15 + rng.randint(0, 10))
        for cy in range(-canopy_r, canopy_r + 1, 2):
            for cx in range(-canopy_r, canopy_r + 1, 2):
                if cx * cx + cy * cy <= canopy_r * canopy_r:
                    px = tx + cx
                    py = canopy_y + cy
                    if 0 <= px < VIRTUAL_WIDTH and 0 <= py < VIRTUAL_HEIGHT:
                        shade = max(0, cx * 2 - cy)
                        c = (min(255, canopy_c[0] + shade),
                             min(255, canopy_c[1] + shade),
                             min(255, canopy_c[2] + shade // 2))
                        surf.set_at((px, py), c)

    # Foreground large trees
    for tree_x in [80, 450, 950, 1450, 1800]:
        trunk_w = rng.randint(20, 40)
        trunk_y = rng.randint(80, 250)
        trunk_bottom = VIRTUAL_HEIGHT - rng.randint(50, 150)
        trunk_c = (55 + rng.randint(0, 20), 35 + rng.randint(0, 12), 18 + rng.randint(0, 8))

        for y in range(trunk_y, trunk_bottom):
            for dx in range(-trunk_w // 2, trunk_w // 2 + 1):
                px = tree_x + dx
                if 0 <= px < VIRTUAL_WIDTH:
                    bark = ((y * 5 + dx * 11 + tree_x) % 7) * 3
                    if abs(dx) == trunk_w // 2:
                        c = (trunk_c[0] - 15, trunk_c[1] - 10, trunk_c[2] - 5)
                    elif dx < 0:
                        c = (trunk_c[0] + bark, trunk_c[1] + bark, trunk_c[2] + bark // 2)
                    else:
                        c = (trunk_c[0] - 5 + bark, trunk_c[1] - 3 + bark, trunk_c[2] + bark // 2)
                    c = tuple(max(0, min(255, v)) for v in c)
                    surf.set_at((px, y), c)

            if y > trunk_bottom - 40:
                root_spread = (y - (trunk_bottom - 40)) * 3
                for rdx in [-root_spread, root_spread]:
                    rpx = tree_x + rdx
                    if 0 <= rpx < VIRTUAL_WIDTH:
                        surf.set_at((rpx, y), trunk_c)

    # Ground detail
    for x in range(0, VIRTUAL_WIDTH, 8):
        for y_off in range(VIRTUAL_HEIGHT - 200, VIRTUAL_HEIGHT, 10):
            if rng.random() < 0.3:
                leaf_colors = [
                    (60, 90, 30), (50, 80, 25), (70, 100, 35),
                    (80, 60, 20), (90, 70, 25),
                ]
                c = rng.choice(leaf_colors)
                for dx in range(rng.randint(1, 4)):
                    for dy in range(rng.randint(1, 4)):
                        nx = x + rng.randint(0, 6) + dx
                        ny = y_off + rng.randint(0, 8) + dy
                        if 0 <= nx < VIRTUAL_WIDTH and 0 <= ny < VIRTUAL_HEIGHT:
                            surf.set_at((nx, ny), c)

    # Light rays
    for ray_x in [300, 750, 1200]:
        for y in range(30, 600):
            ray_w = 3 + y // 20
            for dx in range(-ray_w, ray_w + 1):
                px = ray_x + dx + y // 6
                if 0 <= px < VIRTUAL_WIDTH:
                    alpha = max(0, 20 - y // 30 - abs(dx) * 2)
                    if alpha > 0:
                        base = surf.get_at((px, y))
                        c = (min(255, base[0] + alpha),
                             min(255, base[1] + alpha + 5),
                             min(255, base[2] + alpha // 2))
                        surf.set_at((px, y), c)

    return surf


_forest_bg_cache = None


class ForestScene(Scene):
    """The Mystic Forest — rich 1080p visuals with atmospheric effects."""

    def __init__(self):
        super().__init__()
        self.player = None
        self.state = "explore"
        self.anim_time = 0
        self.fog_particles = []
        self.fireflies = []
        self.menu = None
        self._init_particles()

    def _init_particles(self):
        rng = random.Random(789)
        self.fog_particles = []
        for _ in range(12):
            self.fog_particles.append({
                "x": rng.randint(-200, VIRTUAL_WIDTH),
                "y": rng.randint(400, VIRTUAL_HEIGHT - 150),
                "speed": rng.uniform(8, 25),
                "alpha": rng.randint(15, 40),
                "width": rng.randint(150, 350),
                "height": rng.randint(40, 80),
            })
        self.fireflies = []
        for _ in range(20):
            self.fireflies.append({
                "x": rng.uniform(0, VIRTUAL_WIDTH),
                "y": rng.uniform(300, VIRTUAL_HEIGHT - 200),
                "phase": rng.uniform(0, math.pi * 2),
                "speed_x": rng.uniform(-15, 15),
                "speed_y": rng.uniform(-10, 10),
            })

    def on_enter(self, data=None):
        global _forest_bg_cache
        if _forest_bg_cache is None:
            _forest_bg_cache = _create_forest_bg()

        if data and "player" in data:
            self.player = data["player"]
        self.state = "explore"
        self.menu = SelectionMenu(
            items=[
                {"label": "Explore Deeper", "value": "explore"},
                {"label": "Return to Town", "value": "return"},
            ],
            x=VIRTUAL_WIDTH // 2 - 180,
            y=620,
            spacing=60,
            font_size=42,
            show_box=True,
            box_padding=24,
        )

    def update(self, dt):
        self.anim_time += dt

        for p in self.fog_particles:
            p["x"] += p["speed"] * dt
            if p["x"] > VIRTUAL_WIDTH + p["width"]:
                p["x"] = -p["width"]

        for ff in self.fireflies:
            ff["x"] += ff["speed_x"] * dt
            ff["y"] += ff["speed_y"] * dt + math.sin(self.anim_time * 2 + ff["phase"]) * dt * 6
            if ff["x"] < 0 or ff["x"] > VIRTUAL_WIDTH:
                ff["speed_x"] *= -1
            if ff["y"] < 250 or ff["y"] > VIRTUAL_HEIGHT - 150:
                ff["speed_y"] *= -1

        if self.state == "explore" and self.menu:
            self.menu.update(dt)

    def handle_event(self, event):
        if self.state == "explore" and self.menu:
            self.menu.handle_event(event)

            if self.menu.confirmed:
                choice = self.menu.get_selected_value()
                if choice == "explore":
                    self._explore_step()
                elif choice == "return":
                    self.manager.switch_to("town", {"player": self.player})

            elif self.menu.cancelled:
                self.manager.switch_to("town", {"player": self.player})

    def _explore_step(self):
        if self.player.forest_turns <= 0:
            self.manager.switch_to("town", {"player": self.player})
            return

        self.player.forest_turns -= 1
        enemy = spawn_random_enemy(self.player.level)
        self.manager.switch_to("battle", {
            "player": self.player,
            "enemy": enemy,
            "return_to": "forest",
        })

    def draw(self, surface):
        if _forest_bg_cache:
            surface.blit(_forest_bg_cache, (0, 0))
        else:
            surface.fill(BLACK)

        # Fog
        for p in self.fog_particles:
            fog_surf = pygame.Surface((p["width"], p["height"]), pygame.SRCALPHA)
            for fy in range(0, p["height"], 2):
                for fx in range(0, p["width"], 2):
                    dist_x = abs(fx - p["width"] // 2) / (p["width"] // 2)
                    dist_y = abs(fy - p["height"] // 2) / (p["height"] // 2)
                    dist = min(1.0, math.sqrt(dist_x ** 2 + dist_y ** 2))
                    alpha = int(p["alpha"] * (1 - dist))
                    if alpha > 0:
                        fog_surf.set_at((fx, fy), (180, 200, 180, alpha))
                        fog_surf.set_at((fx + 1, fy), (180, 200, 180, alpha))
                        fog_surf.set_at((fx, fy + 1), (180, 200, 180, alpha))
                        fog_surf.set_at((fx + 1, fy + 1), (180, 200, 180, alpha))
            surface.blit(fog_surf, (int(p["x"]), int(p["y"])))

        # Fireflies
        for ff in self.fireflies:
            glow = abs(math.sin(self.anim_time * 3 + ff["phase"]))
            if glow > 0.3:
                alpha = int(glow * 200)
                size = 6 if glow > 0.7 else 4
                glow_surf = pygame.Surface((size * 4 + 4, size * 4 + 4), pygame.SRCALPHA)
                pygame.draw.circle(glow_surf, (180, 255, 100, alpha // 3),
                                   (size * 2 + 2, size * 2 + 2), size * 2)
                pygame.draw.circle(glow_surf, (220, 255, 150, alpha),
                                   (size * 2 + 2, size * 2 + 2), size)
                surface.blit(glow_surf, (int(ff["x"]) - size * 2, int(ff["y"]) - size * 2))

        # HUD
        if self.player:
            draw_hud(surface, self.player)

        # Zone label
        zone = get_zone_for_level(self.player.level) if self.player else "shallow"
        zone_names = {"shallow": "Shallow Forest", "deep": "Deep Forest", "shadow": "Shadow Depths"}
        zone_colors = {"shallow": (100, 200, 100), "deep": (80, 160, 80), "shadow": (160, 100, 180)}
        zone_name = zone_names.get(zone, "Forest")
        zone_color = zone_colors.get(zone, GREEN)

        draw_menu_box(surface, (VIRTUAL_WIDTH // 2 - 200, 130, 400, 100))
        draw_text(surface, zone_name, VIRTUAL_WIDTH // 2, 155,
                  zone_color, 42, center=True)

        if self.player:
            turns_color = GOLD if self.player.forest_turns > 3 else (255, 80, 80)
            draw_text(surface, f"Turns: {self.player.forest_turns}",
                      VIRTUAL_WIDTH // 2, 200, turns_color, 34, center=True)

        # Exploration menu
        if self.state == "explore" and self.menu:
            draw_menu_box(surface, (VIRTUAL_WIDTH // 2 - 220, 540, 440, 60))
            draw_text(surface, "What do you do?", VIRTUAL_WIDTH // 2, 558,
                      WHITE, 36, center=True)
            self.menu.draw(surface)

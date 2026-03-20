# Title Screen — Legend of the Red Dragon: 16-Bit Edition
# SNES-quality title with detailed dragon, parallax stars, and atmospheric effects

import pygame
import math
from scenes.scene_manager import Scene
from ui.menu import SelectionMenu, draw_text, draw_menu_box
from settings import (
    BLACK, RED, DARK_RED, GOLD, DARK_GOLD, WHITE, GREY,
    VIRTUAL_WIDTH, VIRTUAL_HEIGHT, CREAM
)


def _create_title_dragon():
    """Create a detailed dragon sprite for the title screen (64x48)."""
    W, H = 80, 56
    surf = pygame.Surface((W, H), pygame.SRCALPHA)

    body = (160, 30, 20)
    body_hi = (200, 60, 40)
    body_dk = (100, 15, 10)
    belly = (220, 160, 80)
    outline = (40, 10, 5)
    wing_membrane = (120, 25, 25)
    wing_bone = (180, 50, 35)
    horn = (200, 180, 140)
    eye_color = (255, 200, 0)

    def px(x, y, c):
        if 0 <= x < W and 0 <= y < H:
            surf.set_at((x, y), c)

    # Body (large oval)
    cx, cy = 40, 32
    for y in range(-12, 13):
        for x in range(-16, 17):
            if x * x / 256 + y * y / 144 <= 1:
                if x * x / 256 + y * y / 144 > 0.85:
                    px(cx + x, cy + y, outline)
                elif x < -4:
                    px(cx + x, cy + y, body_dk)
                elif x > 8:
                    px(cx + x, cy + y, body_hi)
                else:
                    px(cx + x, cy + y, body)

    # Belly scales (lighter stripe)
    for y in range(cy - 4, cy + 8):
        for x in range(cx - 6, cx + 7):
            if (x + y) % 3 == 0:
                px(x, y, belly)

    # Neck
    for i in range(12):
        nx = cx + 14 + i
        ny = cy - 10 - i
        for dy in range(-4 + i // 4, 5 - i // 4):
            c = body_hi if dy < 0 else body
            if abs(dy) >= 4 - i // 4:
                c = outline
            px(nx, ny + dy, c)

    # Head
    hx, hy = cx + 26, cy - 22
    for y in range(-6, 7):
        for x in range(-8, 12):
            dist = x * x / 100 + y * y / 36
            if dist <= 1:
                if dist > 0.8:
                    px(hx + x, hy + y, outline)
                elif y < -2:
                    px(hx + x, hy + y, body_hi)
                else:
                    px(hx + x, hy + y, body)

    # Jaw / snout extension
    for x in range(hx + 4, hx + 16):
        for y in range(hy - 2, hy + 4):
            if y == hy - 2 or y == hy + 3:
                px(x, y, outline)
            elif y < hy:
                px(x, y, body_hi)
            else:
                px(x, y, body)
    # Nostril
    px(hx + 14, hy - 1, (255, 120, 40))
    px(hx + 14, hy, (255, 120, 40))

    # Teeth
    for i in range(4):
        tx = hx + 6 + i * 3
        px(tx, hy + 4, (255, 255, 240))
        px(tx, hy + 5, (240, 240, 220))

    # Eyes (glowing)
    for dy in range(-2, 3):
        for dx in range(-2, 3):
            if dx * dx + dy * dy <= 4:
                px(hx + 2 + dx, hy - 2 + dy, (255, 255, 200))
    px(hx + 2, hy - 2, eye_color)
    px(hx + 3, hy - 2, eye_color)
    px(hx + 2, hy - 1, (200, 50, 0))  # Pupil slit

    # Horns
    for i in range(8):
        px(hx - 4 + i // 2, hy - 6 - i, horn)
        px(hx - 3 + i // 2, hy - 6 - i, (170, 150, 110))
        px(hx + 4 + i // 3, hy - 6 - i, horn)

    # Wings (large, spread)
    # Left wing
    for i in range(22):
        t = i / 22
        wy_base = cy - 8 - int(t * 18)
        wx = cx - 8 - i
        # Wing bone
        px(wx, wy_base, wing_bone)
        px(wx, wy_base + 1, wing_bone)
        # Wing membrane
        membrane_h = int((1 - t) * 14) + 2
        for dy in range(2, membrane_h):
            alpha = max(80, 255 - dy * 12)
            mc = (wing_membrane[0], wing_membrane[1], wing_membrane[2], alpha)
            px(wx, wy_base + dy, mc)
        # Membrane edge
        px(wx, wy_base + membrane_h, outline)

    # Right wing (partially behind)
    for i in range(16):
        t = i / 16
        wy_base = cy - 10 - int(t * 14)
        wx = cx + 12 + i
        px(wx, wy_base, wing_bone)
        membrane_h = int((1 - t) * 10) + 2
        for dy in range(1, membrane_h):
            alpha = max(60, 200 - dy * 15)
            mc = (wing_membrane[0] - 20, wing_membrane[1] - 5, wing_membrane[2] - 5, alpha)
            px(wx, wy_base + dy, mc)

    # Tail (curving down and left)
    for i in range(20):
        t = i / 20
        tx = cx - 16 - i
        ty = cy + 8 + int(math.sin(t * 3) * 6)
        thickness = max(1, 4 - i // 5)
        for dy in range(-thickness, thickness + 1):
            if abs(dy) == thickness:
                px(tx, ty + dy, outline)
            elif dy < 0:
                px(tx, ty + dy, body_hi)
            else:
                px(tx, ty + dy, body_dk)
    # Tail spike
    for i in range(4):
        px(cx - 36 - i, cy + 8 - i, horn)
        px(cx - 36 - i, cy + 8 + i, horn)

    # Legs
    for leg_x in [cx - 8, cx + 6]:
        for y in range(cy + 10, cy + 20):
            for dx in range(4):
                if y == cy + 19:
                    px(leg_x + dx, y, outline)  # Claws
                elif dx == 0 or dx == 3:
                    px(leg_x + dx, y, outline)
                elif dx == 1:
                    px(leg_x + dx, y, body)
                else:
                    px(leg_x + dx, y, body_dk)
        # Claws
        for i in range(3):
            px(leg_x - 1 + i * 2, cy + 20, horn)

    return surf


class TitleScreen(Scene):
    """SNES-quality title screen with detailed dragon and atmospheric effects."""

    def __init__(self):
        super().__init__()
        self.menu = SelectionMenu(
            items=[
                {"label": "New Game", "value": "new_game"},
                {"label": "Continue", "value": "continue"},
                {"label": "Quit", "value": "quit"},
            ],
            x=VIRTUAL_WIDTH // 2 - 40,
            y=170,
            spacing=18,
            font_size=16,
            show_box=True,
            box_padding=10,
        )
        self.time = 0
        self.stars = []
        self.clouds = []
        self.dragon_sprite = None
        self._init_bg()

    def _init_bg(self):
        """Create background starfield and cloud layers."""
        import random
        random.seed(42)
        for _ in range(80):
            self.stars.append({
                "x": random.randint(0, VIRTUAL_WIDTH),
                "y": random.randint(0, VIRTUAL_HEIGHT // 2 + 20),
                "brightness": random.randint(100, 255),
                "speed": random.uniform(0.2, 0.8),
                "size": 1 if random.random() > 0.15 else 2,
            })
        for _ in range(6):
            self.clouds.append({
                "x": random.randint(-40, VIRTUAL_WIDTH),
                "y": random.randint(20, 80),
                "width": random.randint(30, 60),
                "speed": random.uniform(3, 8),
                "alpha": random.randint(15, 35),
            })

    def on_enter(self, data=None):
        self.time = 0
        if self.dragon_sprite is None:
            self.dragon_sprite = _create_title_dragon()

    def update(self, dt):
        self.time += dt
        self.menu.update(dt)

        for star in self.stars:
            star["y"] += star["speed"] * dt * 8
            if star["y"] > VIRTUAL_HEIGHT // 2 + 20:
                star["y"] = 0
                import random
                star["x"] = random.randint(0, VIRTUAL_WIDTH)

        for cloud in self.clouds:
            cloud["x"] += cloud["speed"] * dt
            if cloud["x"] > VIRTUAL_WIDTH + cloud["width"]:
                cloud["x"] = -cloud["width"]

    def handle_event(self, event):
        self.menu.handle_event(event)

        if self.menu.confirmed:
            choice = self.menu.get_selected_value()
            if choice == "new_game":
                self.manager.switch_to("char_create")
            elif choice == "continue":
                self.manager.switch_to("load_game")
            elif choice == "quit":
                pygame.event.post(pygame.event.Event(pygame.QUIT))

    def draw(self, surface):
        # Background gradient (dark sky with warm horizon)
        for y in range(VIRTUAL_HEIGHT):
            t = y / VIRTUAL_HEIGHT
            if t < 0.4:
                r = int(5 + 10 * t)
                g = int(3 + 8 * t)
                b = int(20 + 40 * t)
            elif t < 0.6:
                ht = (t - 0.4) / 0.2
                r = int(9 + 40 * ht)
                g = int(6 + 15 * ht)
                b = int(36 - 10 * ht)
            else:
                gt = (t - 0.6) / 0.4
                r = int(49 - 30 * gt)
                g = int(21 - 10 * gt)
                b = int(26 - 15 * gt)
            pygame.draw.line(surface, (r, g, b), (0, y), (VIRTUAL_WIDTH, y))

        # Stars with twinkling
        for star in self.stars:
            pulse = abs(math.sin(self.time * 1.5 + star["x"] * 0.1)) * 0.4 + 0.6
            bright = int(star["brightness"] * pulse)
            color = (bright, bright, min(255, bright + 20))
            if star["size"] == 1:
                surface.set_at((int(star["x"]), int(star["y"])), color)
            else:
                pygame.draw.circle(surface, color, (int(star["x"]), int(star["y"])), 1)

        # Wispy clouds
        for cloud in self.clouds:
            cloud_surf = pygame.Surface((cloud["width"], 8), pygame.SRCALPHA)
            for cx in range(cloud["width"]):
                ch = int(4 * math.sin(cx / cloud["width"] * math.pi))
                for cy in range(max(1, 4 - ch), 4 + ch):
                    alpha = cloud["alpha"] - abs(cx - cloud["width"] // 2) // 2
                    if alpha > 0:
                        cloud_surf.set_at((cx, cy), (180, 160, 200, alpha))
            surface.blit(cloud_surf, (int(cloud["x"]), cloud["y"]))

        # Mountain silhouettes
        for x in range(VIRTUAL_WIDTH):
            my = 95 + int(12 * math.sin(x * 0.015) + 6 * math.sin(x * 0.04))
            for y in range(my, 110):
                t = (y - my) / max(1, 110 - my)
                mc = (int(15 + 12 * t), int(8 + 10 * t), int(25 + 15 * t))
                surface.set_at((x, y), mc)

        # Dragon sprite (centered, with gentle bob)
        if self.dragon_sprite:
            bob_y = int(math.sin(self.time * 1.2) * 3)
            dragon_x = VIRTUAL_WIDTH // 2 - self.dragon_sprite.get_width() // 2
            dragon_y = 52 + bob_y

            # Dragon fire glow (under dragon)
            glow_intensity = int(30 + 20 * math.sin(self.time * 4))
            glow_surf = pygame.Surface((60, 20), pygame.SRCALPHA)
            pygame.draw.ellipse(glow_surf, (255, 100, 0, glow_intensity), (0, 0, 60, 20))
            surface.blit(glow_surf, (dragon_x + 10, dragon_y + 40))

            surface.blit(self.dragon_sprite, (dragon_x, dragon_y))

            # Flame breath particles
            flame_x = dragon_x + 68
            flame_y = dragon_y + 10
            for i in range(8):
                fx = flame_x + i * 3 + int(math.sin(self.time * 10 + i) * 2)
                fy = flame_y + int(math.sin(self.time * 8 + i * 0.5) * 3)
                r = max(0, 255 - i * 20)
                g = max(0, 150 - i * 18)
                b = 0
                alpha = max(0, 255 - i * 30)
                if alpha > 0:
                    ps = pygame.Surface((3, 3), pygame.SRCALPHA)
                    pygame.draw.circle(ps, (r, g, b, alpha), (1, 1), 1)
                    surface.blit(ps, (fx, fy))

        # Title text
        title_y = 20

        # "LEGEND OF THE" — elegant subtitle
        draw_text(surface, "L E G E N D   O F   T H E", VIRTUAL_WIDTH // 2, title_y,
                  (200, 190, 170), 12, center=True)

        # "RED DRAGON" — pulsing red-gold
        r = int(200 + 55 * math.sin(self.time * 2))
        g = int(50 + 40 * math.sin(self.time * 2 + 1))
        b = int(20 + 20 * math.sin(self.time * 2 + 2))
        title_color = (min(255, r), min(255, g), min(255, b))

        # Title shadow
        draw_text(surface, "RED DRAGON", VIRTUAL_WIDTH // 2 + 1, title_y + 15,
                  (40, 10, 5), 32, center=True, shadow=False)
        draw_text(surface, "RED DRAGON", VIRTUAL_WIDTH // 2, title_y + 14,
                  title_color, 32, center=True, shadow=False)

        # Subtitle
        draw_text(surface, "~ 16-Bit Edition ~", VIRTUAL_WIDTH // 2, title_y + 38,
                  GOLD, 12, center=True)

        # Decorative line under subtitle
        line_y = title_y + 48
        line_w = 80
        for x in range(VIRTUAL_WIDTH // 2 - line_w, VIRTUAL_WIDTH // 2 + line_w):
            dist = abs(x - VIRTUAL_WIDTH // 2)
            alpha = max(0, 150 - dist * 2)
            surface.set_at((x, line_y), (200, 170, 80, alpha) if alpha > 0 else BLACK)

        # Menu
        self.menu.draw(surface)

        # Footer
        blink = int(self.time * 2) % 3 != 0
        if blink:
            draw_text(surface, "Press Z or Enter", VIRTUAL_WIDTH // 2, 225,
                      GREY, 10, center=True)

        draw_text(surface, "Based on LORD by Seth Able Robinson (1989)",
                  VIRTUAL_WIDTH // 2, 235, (80, 80, 100), 8, center=True)

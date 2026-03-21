# SNES Final Fantasy-style menu windows and selection menus

import pygame
from settings import (
    MENU_BG_TOP, MENU_BG_BOTTOM, MENU_BORDER_OUTER, MENU_BORDER_INNER,
    WHITE, GOLD, GREY, BLACK, VIRTUAL_WIDTH, VIRTUAL_HEIGHT
)


def get_font(size):
    """Get a pixel-style font at the given size."""
    return pygame.font.Font(None, size)


def draw_menu_box(surface, rect, alpha=230):
    """Draw an SNES FF-style blue gradient menu box with double border."""
    x, y, w, h = rect

    box = pygame.Surface((w, h), pygame.SRCALPHA)

    # Gradient background
    for row in range(h):
        t = row / max(h - 1, 1)
        r = int(MENU_BG_TOP[0] + (MENU_BG_BOTTOM[0] - MENU_BG_TOP[0]) * t)
        g = int(MENU_BG_TOP[1] + (MENU_BG_BOTTOM[1] - MENU_BG_TOP[1]) * t)
        b = int(MENU_BG_TOP[2] + (MENU_BG_BOTTOM[2] - MENU_BG_TOP[2]) * t)
        pygame.draw.line(box, (r, g, b, alpha), (0, row), (w - 1, row))

    # Outer border (bright)
    pygame.draw.rect(box, (*MENU_BORDER_OUTER, alpha), (0, 0, w, h), 3)
    # Inner border (darker)
    pygame.draw.rect(box, (*MENU_BORDER_INNER, alpha), (3, 3, w - 6, h - 6), 2)

    # Corner highlights
    for cx, cy in [(2, 2), (w - 3, 2), (2, h - 3), (w - 3, h - 3)]:
        pygame.draw.circle(box, (*WHITE, alpha), (cx, cy), 1)

    surface.blit(box, (x, y))


def draw_text(surface, text, x, y, color=WHITE, size=48, center=False, shadow=True):
    """Draw text with optional drop shadow for that classic SNES look."""
    font = get_font(size)
    shadow_offset = max(1, size // 16)
    if shadow:
        shadow_surf = font.render(text, False, BLACK)
        if center:
            shadow_rect = shadow_surf.get_rect(center=(x + shadow_offset, y + shadow_offset))
            surface.blit(shadow_surf, shadow_rect)
        else:
            surface.blit(shadow_surf, (x + shadow_offset, y + shadow_offset))

    text_surf = font.render(text, False, color)
    if center:
        text_rect = text_surf.get_rect(center=(x, y))
        surface.blit(text_surf, text_rect)
    else:
        surface.blit(text_surf, (x, y))

    return text_surf.get_width(), text_surf.get_height()


class MenuCursor:
    """Animated hand/arrow cursor for menu selections."""

    def __init__(self):
        self.frame = 0
        self.timer = 0
        self.bob_offset = 0

    def update(self, dt):
        self.timer += dt
        if self.timer >= 0.3:
            self.timer -= 0.3
            self.frame = 1 - self.frame
        self.bob_offset = self.frame * 4

    def draw(self, surface, x, y, color=WHITE):
        """Draw a small arrow cursor."""
        points = [
            (x + self.bob_offset, y),
            (x + 16 + self.bob_offset, y + 10),
            (x + self.bob_offset, y + 20),
        ]
        pygame.draw.polygon(surface, color, points)


class SelectionMenu:
    """A vertical list menu with cursor navigation."""

    def __init__(self, items, x, y, spacing=48, font_size=48, color=WHITE,
                 highlight_color=GOLD, show_box=True, box_padding=20):
        self.items = items
        self.x = x
        self.y = y
        self.spacing = spacing
        self.font_size = font_size
        self.color = color
        self.highlight_color = highlight_color
        self.show_box = show_box
        self.box_padding = box_padding
        self.selected = 0
        self.cursor = MenuCursor()
        self.confirmed = False
        self.cancelled = False

    def update(self, dt):
        self.cursor.update(dt)
        self.confirmed = False
        self.cancelled = False

    def handle_event(self, event):
        if event.type != pygame.KEYDOWN:
            return

        if event.key in (pygame.K_UP, pygame.K_w):
            self.selected = (self.selected - 1) % len(self.items)
            attempts = 0
            while not self.items[self.selected].get("enabled", True) and attempts < len(self.items):
                self.selected = (self.selected - 1) % len(self.items)
                attempts += 1

        elif event.key in (pygame.K_DOWN, pygame.K_s):
            self.selected = (self.selected + 1) % len(self.items)
            attempts = 0
            while not self.items[self.selected].get("enabled", True) and attempts < len(self.items):
                self.selected = (self.selected + 1) % len(self.items)
                attempts += 1

        elif event.key in (pygame.K_RETURN, pygame.K_SPACE, pygame.K_z):
            if self.items[self.selected].get("enabled", True):
                self.confirmed = True

        elif event.key in (pygame.K_ESCAPE, pygame.K_x):
            self.cancelled = True

    def draw(self, surface):
        if self.show_box:
            font = get_font(self.font_size)
            max_width = max(font.size(item["label"])[0] for item in self.items)
            box_w = max_width + self.box_padding * 2 + 40
            box_h = len(self.items) * self.spacing + self.box_padding * 2
            draw_menu_box(surface, (self.x - self.box_padding,
                                     self.y - self.box_padding,
                                     box_w, box_h))

        for i, item in enumerate(self.items):
            item_y = self.y + i * self.spacing
            enabled = item.get("enabled", True)

            if i == self.selected and enabled:
                self.cursor.draw(surface, self.x, item_y + 2, self.highlight_color)
                draw_text(surface, item["label"], self.x + 28, item_y,
                          self.highlight_color, self.font_size)
            else:
                color = self.color if enabled else GREY
                draw_text(surface, item["label"], self.x + 28, item_y,
                          color, self.font_size)

    def get_selected_value(self):
        return self.items[self.selected].get("value", self.selected)


class DialogueBox:
    """An NPC dialogue text box that types out text character by character."""

    def __init__(self, x=40, y=820, width=1840, height=230):
        self.rect = (x, y, width, height)
        self.text = ""
        self.displayed_text = ""
        self.char_index = 0
        self.char_timer = 0
        self.char_speed = 0.03
        self.finished = False
        self.active = False
        self.speaker = ""
        self.on_complete = None

    def show(self, text, speaker="", on_complete=None):
        self.text = text
        self.speaker = speaker
        self.displayed_text = ""
        self.char_index = 0
        self.char_timer = 0
        self.finished = False
        self.active = True
        self.on_complete = on_complete

    def update(self, dt):
        if not self.active or self.finished:
            return

        self.char_timer += dt
        while self.char_timer >= self.char_speed and self.char_index < len(self.text):
            self.char_timer -= self.char_speed
            self.char_index += 1
            self.displayed_text = self.text[:self.char_index]

        if self.char_index >= len(self.text):
            self.finished = True

    def handle_event(self, event):
        if not self.active:
            return False

        if event.type == pygame.KEYDOWN and event.key in (pygame.K_RETURN, pygame.K_SPACE, pygame.K_z):
            if not self.finished:
                self.displayed_text = self.text
                self.char_index = len(self.text)
                self.finished = True
            else:
                self.active = False
                if self.on_complete:
                    self.on_complete()
                return True

        return False

    def draw(self, surface):
        if not self.active:
            return

        draw_menu_box(surface, self.rect)

        x, y, w, h = self.rect
        text_x = x + 24
        text_y = y + 20

        if self.speaker:
            draw_text(surface, self.speaker, text_x, text_y, GOLD, 42)
            text_y += 48

        # Word wrap
        font = get_font(36)
        words = self.displayed_text.split(' ')
        line = ""
        max_width = w - 48
        for word in words:
            test = line + word + " "
            if font.size(test)[0] > max_width:
                draw_text(surface, line.strip(), text_x, text_y, WHITE, 36, shadow=True)
                text_y += 40
                line = word + " "
            else:
                line = test
        if line.strip():
            draw_text(surface, line.strip(), text_x, text_y, WHITE, 36, shadow=True)

        # Blinking advance indicator
        if self.finished:
            indicator_time = pygame.time.get_ticks() // 500
            if indicator_time % 2 == 0:
                draw_text(surface, "v", x + w - 40, y + h - 40, WHITE, 36)

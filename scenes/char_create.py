# Character Creation Scene — name entry and class selection

import pygame
from scenes.scene_manager import Scene
from ui.menu import SelectionMenu, draw_text, draw_menu_box
from systems.player import CLASSES, Player
from settings import (
    BLACK, WHITE, GOLD, GREY, RED, BLUE, GREEN, CREAM,
    VIRTUAL_WIDTH, VIRTUAL_HEIGHT
)


class CharCreateScene(Scene):
    """Character creation: enter name, choose class, confirm."""

    def __init__(self):
        super().__init__()
        self.phase = "name"
        self.name_input = ""
        self.max_name_len = 12
        self.cursor_blink = 0
        self.selected_class = "Warrior"

        class_items = []
        for cls_name, cls_data in CLASSES.items():
            class_items.append({"label": cls_name, "value": cls_name})

        self.class_menu = SelectionMenu(
            items=class_items,
            x=150,
            y=400,
            spacing=60,
            font_size=48,
            show_box=False,
        )

        self.confirm_menu = SelectionMenu(
            items=[
                {"label": "Begin Adventure!", "value": "confirm"},
                {"label": "Go Back", "value": "back"},
            ],
            x=VIRTUAL_WIDTH // 2 - 180,
            y=800,
            spacing=60,
            font_size=48,
            show_box=True,
            box_padding=30,
        )

    def on_enter(self, data=None):
        self.phase = "name"
        self.name_input = ""

    def update(self, dt):
        self.cursor_blink += dt
        if self.phase == "class":
            self.class_menu.update(dt)
        elif self.phase == "confirm":
            self.confirm_menu.update(dt)

    def handle_event(self, event):
        if self.phase == "name":
            self._handle_name_input(event)
        elif self.phase == "class":
            self._handle_class_select(event)
        elif self.phase == "confirm":
            self._handle_confirm(event)

    def _handle_name_input(self, event):
        if event.type != pygame.KEYDOWN:
            return

        if event.key == pygame.K_RETURN and len(self.name_input) > 0:
            self.phase = "class"
        elif event.key == pygame.K_BACKSPACE:
            self.name_input = self.name_input[:-1]
        elif event.key == pygame.K_ESCAPE:
            self.manager.switch_to("title")
        elif len(self.name_input) < self.max_name_len:
            char = event.unicode
            if char.isprintable() and len(char) == 1 and char != ' ' or (char == ' ' and len(self.name_input) > 0):
                self.name_input += char

    def _handle_class_select(self, event):
        self.class_menu.handle_event(event)

        if self.class_menu.confirmed:
            self.selected_class = self.class_menu.get_selected_value()
            self.phase = "confirm"
        elif self.class_menu.cancelled:
            self.phase = "name"

    def _handle_confirm(self, event):
        self.confirm_menu.handle_event(event)

        if self.confirm_menu.confirmed:
            choice = self.confirm_menu.get_selected_value()
            if choice == "confirm":
                player = Player(self.name_input, self.selected_class)
                self.manager.switch_to("town", {"player": player, "new_game": True})
            elif choice == "back":
                self.phase = "class"
        elif self.confirm_menu.cancelled:
            self.phase = "class"

    def draw(self, surface):
        surface.fill(BLACK)

        draw_text(surface, "Create Your Hero", VIRTUAL_WIDTH // 2, 60,
                  GOLD, 72, center=True)

        if self.phase == "name":
            self._draw_name_phase(surface)
        elif self.phase == "class":
            self._draw_class_phase(surface)
        elif self.phase == "confirm":
            self._draw_confirm_phase(surface)

    def _draw_name_phase(self, surface):
        draw_text(surface, "Enter your name, adventurer:", VIRTUAL_WIDTH // 2, 280,
                  WHITE, 42, center=True)

        box_x = VIRTUAL_WIDTH // 2 - 300
        box_y = 380
        draw_menu_box(surface, (box_x, box_y, 600, 80))

        cursor = "_" if int(self.cursor_blink * 3) % 2 == 0 else " "
        display_name = self.name_input + cursor
        draw_text(surface, display_name, box_x + 30, box_y + 18, GOLD, 48)

        draw_text(surface, "Press Enter to continue", VIRTUAL_WIDTH // 2, 560,
                  GREY, 30, center=True)
        draw_text(surface, "Press Escape to go back", VIRTUAL_WIDTH // 2, 610,
                  GREY, 30, center=True)

    def _draw_class_phase(self, surface):
        draw_text(surface, f"Welcome, {self.name_input}!", VIRTUAL_WIDTH // 2, 200,
                  GOLD, 42, center=True)
        draw_text(surface, "Choose your path:", VIRTUAL_WIDTH // 2, 280,
                  WHITE, 42, center=True)

        self.class_menu.draw(surface)

        # Class description panel
        class_names = list(CLASSES.keys())
        current_class = class_names[self.class_menu.selected]
        cls_data = CLASSES[current_class]

        draw_menu_box(surface, (100, 700, VIRTUAL_WIDTH - 200, 300))

        class_colors = {"Warrior": RED, "Thief": GREEN, "Mage": BLUE}
        color = class_colors.get(current_class, WHITE)

        draw_text(surface, current_class, 140, 720, color, 48)
        draw_text(surface, cls_data["description"], 140, 780, CREAM, 30)

        bonus = cls_data["stat_bonus"]
        bonus_strs = [f"{k.upper()}+{v}" for k, v in bonus.items() if v > 0]
        draw_text(surface, "Bonus: " + "  ".join(bonus_strs), 140, 840, GOLD, 30)

        draw_text(surface, f"Special: {cls_data['special']}", 140, 890, WHITE, 30)
        draw_text(surface, cls_data["special_desc"], 140, 935, GREY, 26)

    def _draw_confirm_phase(self, surface):
        draw_menu_box(surface, (200, 200, VIRTUAL_WIDTH - 400, 500))

        draw_text(surface, "Your Hero", VIRTUAL_WIDTH // 2, 240, GOLD, 60, center=True)

        class_colors = {"Warrior": RED, "Thief": GREEN, "Mage": BLUE}
        color = class_colors.get(self.selected_class, WHITE)

        draw_text(surface, self.name_input, VIRTUAL_WIDTH // 2, 360, WHITE, 60, center=True)
        draw_text(surface, f"The {self.selected_class}", VIRTUAL_WIDTH // 2, 440, color, 48, center=True)

        cls_data = CLASSES[self.selected_class]
        bonus = cls_data["stat_bonus"]
        bonus_strs = [f"{k.upper()}+{v}" for k, v in bonus.items() if v > 0]
        draw_text(surface, " | ".join(bonus_strs), VIRTUAL_WIDTH // 2, 530, GOLD, 36, center=True)

        draw_text(surface, f"Special: {cls_data['special']}", VIRTUAL_WIDTH // 2, 600,
                  CREAM, 34, center=True)

        self.confirm_menu.draw(surface)

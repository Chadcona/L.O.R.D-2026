# Load Game Scene — select a save slot to continue

import pygame
from scenes.scene_manager import Scene
from ui.menu import SelectionMenu, draw_text, draw_menu_box
from systems.save_load import list_saves, load_game
from settings import BLACK, WHITE, GOLD, GREY, VIRTUAL_WIDTH, VIRTUAL_HEIGHT


class LoadGameScene(Scene):
    """Save slot selection screen."""

    def __init__(self):
        super().__init__()
        self.menu = None
        self.saves = []

    def on_enter(self, data=None):
        self.saves = list_saves()
        items = []
        for save in self.saves:
            if save["info"]:
                info = save["info"]
                label = f"Slot {save['slot']}: {info['name']} Lv.{info['level']} Day {info['day']}"
            else:
                label = f"Slot {save['slot']}: --- Empty ---"
            items.append({
                "label": label,
                "value": save["slot"],
                "enabled": save["info"] is not None,
            })
        items.append({"label": "Back", "value": "back"})

        self.menu = SelectionMenu(
            items=items,
            x=VIRTUAL_WIDTH // 2 - 400,
            y=400,
            spacing=60,
            font_size=42,
            show_box=True,
            box_padding=30,
        )

    def update(self, dt):
        if self.menu:
            self.menu.update(dt)

    def handle_event(self, event):
        if not self.menu:
            return
        self.menu.handle_event(event)

        if self.menu.confirmed:
            value = self.menu.get_selected_value()
            if value == "back":
                self.manager.switch_to("title")
            else:
                result = load_game(value)
                if result:
                    player, extra = result
                    self.manager.switch_to("town", {"player": player})

        elif self.menu.cancelled:
            self.manager.switch_to("title")

    def draw(self, surface):
        surface.fill(BLACK)
        draw_text(surface, "Continue Adventure", VIRTUAL_WIDTH // 2, 180,
                  GOLD, 72, center=True)
        draw_text(surface, "Select a save file:", VIRTUAL_WIDTH // 2, 300,
                  WHITE, 36, center=True)
        if self.menu:
            self.menu.draw(surface)

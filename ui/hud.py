# In-game HUD — HP/MP/Turns/Gold display

import pygame
from settings import WHITE, RED, GREEN, BLUE, GOLD, BLACK, DARK_GREY, VIRTUAL_WIDTH
from ui.menu import draw_menu_box, draw_text


def draw_bar(surface, x, y, width, height, current, maximum, bar_color, bg_color=DARK_GREY):
    """Draw a stat bar (HP/MP/EXP)."""
    pygame.draw.rect(surface, bg_color, (x, y, width, height))
    if maximum > 0:
        fill_width = int((current / maximum) * width)
        fill_width = max(0, min(fill_width, width))
        if fill_width > 0:
            pygame.draw.rect(surface, bar_color, (x, y, fill_width, height))
    pygame.draw.rect(surface, WHITE, (x, y, width, height), 2)


def draw_hud(surface, player):
    """Draw the top-of-screen HUD with player vitals."""
    draw_menu_box(surface, (10, 10, VIRTUAL_WIDTH - 20, 80))

    # Name and level
    draw_text(surface, f"{player.name}", 30, 18, GOLD, 36)
    draw_text(surface, f"Lv.{player.level}", 30, 52, WHITE, 28)

    # HP bar
    draw_text(surface, "HP", 420, 18, WHITE, 28)
    draw_bar(surface, 470, 22, 300, 22, player.hp, player.max_hp, GREEN)
    draw_text(surface, f"{player.hp}/{player.max_hp}", 470, 48, WHITE, 26)

    # MP bar
    draw_text(surface, "MP", 820, 18, WHITE, 28)
    draw_bar(surface, 870, 22, 200, 22, player.mp, player.max_mp, BLUE)
    draw_text(surface, f"{player.mp}/{player.max_mp}", 870, 48, WHITE, 26)

    # Gold
    draw_text(surface, f"G:{player.gold}", 1200, 18, GOLD, 28)

    # Forest turns
    draw_text(surface, f"Turns:{player.forest_turns}", 1200, 52, WHITE, 28)

    # Day
    draw_text(surface, f"Day {player.day}", 1600, 18, WHITE, 28)

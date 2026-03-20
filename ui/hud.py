# In-game HUD — HP/MP/Turns/Gold display

import pygame
from settings import WHITE, RED, GREEN, BLUE, GOLD, BLACK, DARK_GREY, VIRTUAL_WIDTH
from ui.menu import draw_menu_box, draw_text


def draw_bar(surface, x, y, width, height, current, maximum, bar_color, bg_color=DARK_GREY):
    """Draw a stat bar (HP/MP/EXP)."""
    # Background
    pygame.draw.rect(surface, bg_color, (x, y, width, height))
    # Fill
    if maximum > 0:
        fill_width = int((current / maximum) * width)
        fill_width = max(0, min(fill_width, width))
        if fill_width > 0:
            pygame.draw.rect(surface, bar_color, (x, y, fill_width, height))
    # Border
    pygame.draw.rect(surface, WHITE, (x, y, width, height), 1)


def draw_hud(surface, player):
    """Draw the top-of-screen HUD with player vitals."""
    # HUD background box
    draw_menu_box(surface, (2, 2, VIRTUAL_WIDTH - 4, 28))

    # Name and level
    draw_text(surface, f"{player.name}", 8, 5, GOLD, 12)
    draw_text(surface, f"Lv.{player.level}", 8, 16, WHITE, 10)

    # HP bar
    draw_text(surface, "HP", 75, 5, WHITE, 10)
    draw_bar(surface, 90, 6, 60, 7, player.hp, player.max_hp, GREEN)
    draw_text(surface, f"{player.hp}/{player.max_hp}", 90, 15, WHITE, 9)

    # MP bar
    draw_text(surface, "MP", 160, 5, WHITE, 10)
    draw_bar(surface, 175, 6, 40, 7, player.mp, player.max_mp, BLUE)
    draw_text(surface, f"{player.mp}/{player.max_mp}", 175, 15, WHITE, 9)

    # Gold
    draw_text(surface, f"G:{player.gold}", 225, 5, GOLD, 10)

    # Forest turns
    draw_text(surface, f"Turns:{player.forest_turns}", 225, 16, WHITE, 10)

    # Day
    draw_text(surface, f"Day {player.day}", 290, 5, WHITE, 10)

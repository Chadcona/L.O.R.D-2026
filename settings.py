# Legend of the Red Dragon: 16-Bit Edition
# Game Settings & Constants

import os

# Display
VIRTUAL_WIDTH = 320
VIRTUAL_HEIGHT = 240
SCREEN_WIDTH = 1920
SCREEN_HEIGHT = 1080
SCALE_FACTOR = SCREEN_WIDTH // VIRTUAL_WIDTH
FPS = 60
TITLE = "Legend of the Red Dragon: 16-Bit Edition"

# Paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ASSETS_DIR = os.path.join(BASE_DIR, "assets")
SPRITES_DIR = os.path.join(ASSETS_DIR, "sprites")
TILES_DIR = os.path.join(ASSETS_DIR, "tiles")
UI_DIR = os.path.join(ASSETS_DIR, "ui")
MUSIC_DIR = os.path.join(ASSETS_DIR, "music")
SFX_DIR = os.path.join(ASSETS_DIR, "sfx")
SAVES_DIR = os.path.join(BASE_DIR, "saves")

# 16-bit SNES colour palette
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
RED = (200, 40, 40)
DARK_RED = (139, 0, 0)
GOLD = (218, 165, 32)
DARK_GOLD = (184, 134, 11)
BLUE = (40, 40, 200)
DARK_BLUE = (20, 20, 80)
GREEN = (40, 180, 40)
DARK_GREEN = (20, 100, 20)
PURPLE = (128, 40, 180)
GREY = (128, 128, 128)
DARK_GREY = (64, 64, 64)
LIGHT_GREY = (192, 192, 192)
BROWN = (139, 90, 43)
DARK_BROWN = (80, 50, 20)
CREAM = (255, 253, 208)
SKY_BLUE = (100, 149, 237)
SHADOW = (0, 0, 0, 128)

# UI colours
UI_BG = (16, 16, 48)
UI_BORDER = (180, 180, 255)
UI_TEXT = WHITE
UI_HIGHLIGHT = GOLD
UI_DISABLED = GREY

# Menu window styling (SNES FF-style blue gradient boxes)
MENU_BG_TOP = (24, 24, 72)
MENU_BG_BOTTOM = (8, 8, 40)
MENU_BORDER_OUTER = (168, 168, 255)
MENU_BORDER_INNER = (80, 80, 168)

# Gameplay constants
DEFAULT_FOREST_TURNS = 10
MAX_LEVEL = 12
SAVE_SLOTS = 3
BANK_INTEREST_RATE = 0.05
INN_BASE_COST = 50

# Level-up EXP requirements
LEVEL_EXP = {
    1: 0,
    2: 100,
    3: 300,
    4: 700,
    5: 1500,
    6: 3000,
    7: 6000,
    8: 10000,
    9: 16000,
    10: 25000,
    11: 38000,
    12: 55000,
}

# Server settings (multiplayer)
SERVER_URL = "http://localhost:8000"
NETWORK_TIMEOUT = 5

# Font sizes (virtual resolution)
FONT_SM = 8
FONT_MD = 12
FONT_LG = 16
FONT_XL = 24
FONT_TITLE = 32

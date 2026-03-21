# SNES-quality pixel art sprite generator
# Generates detailed 16x24 character sprites and 32x32+ enemy sprites
# with proper shading, outlines, and animation frames like FF4/FF6

import pygame
import os
from settings import (
    USE_EXTERNAL_SPRITES, SPRITE_SHEET_PATH,
    SPRITE_SHEET_REGIONS, PLAYER_SPRITE_W, PLAYER_SPRITE_H,
)


# --- Color palettes (SNES style with highlight/mid/shadow per material) ---

SKIN_PALETTE = {
    "highlight": (255, 224, 189),
    "mid": (240, 200, 160),
    "shadow": (200, 150, 110),
    "dark": (160, 110, 80),
}

HAIR_PALETTES = {
    "brown": {"highlight": (160, 110, 60), "mid": (120, 75, 35), "shadow": (80, 50, 20)},
    "blonde": {"highlight": (255, 230, 140), "mid": (220, 190, 100), "shadow": (180, 150, 60)},
    "red": {"highlight": (220, 100, 60), "mid": (180, 60, 30), "shadow": (130, 40, 20)},
    "black": {"highlight": (70, 70, 90), "mid": (40, 40, 55), "shadow": (20, 20, 30)},
    "white": {"highlight": (240, 240, 250), "mid": (200, 200, 215), "shadow": (160, 160, 180)},
}

CLASS_PALETTES = {
    "Warrior": {
        "armor_hi": (120, 140, 200),
        "armor_mid": (80, 100, 170),
        "armor_shadow": (50, 65, 120),
        "trim": (200, 180, 80),
        "cape": (180, 40, 40),
        "cape_shadow": (120, 25, 25),
    },
    "Thief": {
        "armor_hi": (100, 140, 90),
        "armor_mid": (65, 100, 55),
        "armor_shadow": (40, 65, 35),
        "trim": (180, 160, 100),
        "cape": (80, 70, 50),
        "cape_shadow": (50, 42, 30),
    },
    "Mage": {
        "armor_hi": (140, 90, 180),
        "armor_mid": (100, 55, 140),
        "armor_shadow": (65, 35, 95),
        "trim": (220, 200, 100),
        "cape": (60, 40, 120),
        "cape_shadow": (35, 22, 75),
    },
}

BOOT_PALETTE = {
    "highlight": (130, 90, 50),
    "mid": (90, 60, 30),
    "shadow": (60, 38, 18),
}


def _px(surface, x, y, color):
    """Set a pixel if within bounds."""
    if 0 <= x < surface.get_width() and 0 <= y < surface.get_height():
        surface.set_at((x, y), color)


def _outline_rect(surface, x, y, w, h, fill, outline=(20, 20, 30)):
    """Draw a filled rect with a 1px dark outline — the SNES way."""
    for oy in range(h):
        for ox in range(w):
            if ox == 0 or ox == w - 1 or oy == 0 or oy == h - 1:
                _px(surface, x + ox, y + oy, outline)
            else:
                _px(surface, x + ox, y + oy, fill)


def _draw_front_back_sprite(surf, pal, hair_pal, skin, boot, outline, facing, frame, player_class):
    """Draw front (down) or back (up) facing sprite on a 16x24 surface."""
    W, H = 16, 24
    is_front = (facing == "down")

    bob = 0
    leg_frame = frame % 4
    if leg_frame in (1, 3):
        bob = -1

    # --- HAIR (top of head) ---
    for x in range(5, 11):
        _px(surf, x, 0 + bob, outline)
    for x in range(4, 12):
        _px(surf, x, 1 + bob, hair_pal["shadow"] if x < 6 or x > 9 else hair_pal["mid"])
    _px(surf, 4, 1 + bob, outline)
    _px(surf, 11, 1 + bob, outline)

    # Row 2: Hair sides + forehead
    _px(surf, 3, 2 + bob, outline)
    _px(surf, 4, 2 + bob, hair_pal["mid"])
    _px(surf, 5, 2 + bob, hair_pal["highlight"])
    for x in range(6, 10):
        _px(surf, x, 2 + bob, skin["highlight"] if is_front else hair_pal["mid"])
    _px(surf, 10, 2 + bob, hair_pal["highlight"])
    _px(surf, 11, 2 + bob, hair_pal["mid"])
    _px(surf, 12, 2 + bob, outline)

    # --- FACE (rows 3-5) ---
    _px(surf, 3, 3 + bob, outline)
    _px(surf, 4, 3 + bob, hair_pal["shadow"])
    if is_front:
        _px(surf, 5, 3 + bob, skin["mid"])
        _px(surf, 6, 3 + bob, (40, 60, 120))
        _px(surf, 7, 3 + bob, skin["mid"])
        _px(surf, 8, 3 + bob, skin["mid"])
        _px(surf, 9, 3 + bob, (40, 60, 120))
        _px(surf, 10, 3 + bob, skin["mid"])
    else:
        for x in range(5, 11):
            _px(surf, x, 3 + bob, hair_pal["mid"])
    _px(surf, 11, 3 + bob, hair_pal["shadow"])
    _px(surf, 12, 3 + bob, outline)

    # Row 4: Nose/mouth
    _px(surf, 3, 4 + bob, outline)
    _px(surf, 4, 4 + bob, hair_pal["shadow"])
    if is_front:
        for x in range(5, 11):
            _px(surf, x, 4 + bob, skin["mid"])
        _px(surf, 7, 4 + bob, skin["dark"])
        _px(surf, 8, 4 + bob, skin["dark"])
    else:
        for x in range(5, 11):
            _px(surf, x, 4 + bob, hair_pal["shadow"])
    _px(surf, 11, 4 + bob, hair_pal["shadow"])
    _px(surf, 12, 4 + bob, outline)

    # Row 5: Chin
    _px(surf, 4, 5 + bob, outline)
    for x in range(5, 11):
        _px(surf, x, 5 + bob, skin["shadow"])
    _px(surf, 11, 5 + bob, outline)

    # --- BODY / ARMOR (rows 6-14) ---
    _px(surf, 3, 6 + bob, outline)
    _px(surf, 4, 6 + bob, pal["armor_hi"])
    for x in range(5, 11):
        _px(surf, x, 6 + bob, pal["armor_mid"])
    _px(surf, 11, 6 + bob, pal["armor_shadow"])
    _px(surf, 12, 6 + bob, outline)

    # Shoulder pauldrons
    _px(surf, 2, 7 + bob, outline)
    _px(surf, 3, 7 + bob, pal["trim"])
    _px(surf, 13, 7 + bob, outline)
    _px(surf, 12, 7 + bob, pal["trim"])

    # Torso
    for row in range(7, 12):
        _px(surf, 2, row + bob, outline)
        _px(surf, 3, row + bob, pal["armor_hi"])
        for x in range(4, 12):
            shade = pal["armor_mid"] if x < 9 else pal["armor_shadow"]
            _px(surf, x, row + bob, shade)
        _px(surf, 12, row + bob, pal["armor_shadow"])
        _px(surf, 13, row + bob, outline)

    # Belt / trim row
    for x in range(3, 13):
        _px(surf, x, 11 + bob, pal["trim"] if x != 2 and x != 13 else outline)
    _px(surf, 2, 11 + bob, outline)
    _px(surf, 13, 11 + bob, outline)

    # Chest emblem
    _px(surf, 7, 8 + bob, pal["trim"])
    _px(surf, 8, 8 + bob, pal["trim"])
    _px(surf, 7, 9 + bob, pal["trim"])
    _px(surf, 8, 9 + bob, pal["trim"])

    # Cape
    if player_class in ("Warrior", "Mage"):
        for row in range(7, 15):
            _px(surf, 1, row + bob, outline)
            _px(surf, 14, row + bob, outline)
            if row < 13:
                _px(surf, 2, row + bob, pal["cape"])
                _px(surf, 13, row + bob, pal["cape_shadow"])

    # Arms
    for row in range(8, 11):
        _px(surf, 2, row + bob, skin["mid"] if player_class == "Thief" else pal["armor_hi"])
        _px(surf, 13, row + bob, skin["shadow"] if player_class == "Thief" else pal["armor_shadow"])
    _px(surf, 2, 11 + bob, skin["mid"])
    _px(surf, 13, 11 + bob, skin["shadow"])

    # --- LOWER BODY / LEGS ---
    for x in range(4, 12):
        _px(surf, x, 12 + bob, pal["armor_shadow"])
    _px(surf, 3, 12 + bob, outline)
    _px(surf, 12, 12 + bob, outline)

    if leg_frame == 0 or leg_frame == 2:
        for row in range(13, 18):
            _px(surf, 4, row, outline)
            _px(surf, 5, row, pal["armor_mid"] if row < 16 else boot["mid"])
            _px(surf, 6, row, pal["armor_shadow"] if row < 16 else boot["shadow"])
            _px(surf, 7, row, outline)
            _px(surf, 8, row, outline)
            _px(surf, 9, row, pal["armor_mid"] if row < 16 else boot["mid"])
            _px(surf, 10, row, pal["armor_shadow"] if row < 16 else boot["shadow"])
            _px(surf, 11, row, outline)
    elif leg_frame == 1:
        for row in range(13, 18):
            ol = -1 if row > 14 else 0
            orr = 1 if row > 14 else 0
            _px(surf, 4 + ol, row, outline)
            _px(surf, 5 + ol, row, pal["armor_mid"] if row < 16 else boot["mid"])
            _px(surf, 6 + ol, row, pal["armor_shadow"] if row < 16 else boot["shadow"])
            _px(surf, 7 + ol, row, outline)
            _px(surf, 8 + orr, row, outline)
            _px(surf, 9 + orr, row, pal["armor_mid"] if row < 16 else boot["mid"])
            _px(surf, 10 + orr, row, pal["armor_shadow"] if row < 16 else boot["shadow"])
            _px(surf, 11 + orr, row, outline)
    elif leg_frame == 3:
        for row in range(13, 18):
            ol = 1 if row > 14 else 0
            orr = -1 if row > 14 else 0
            _px(surf, 4 + ol, row, outline)
            _px(surf, 5 + ol, row, pal["armor_mid"] if row < 16 else boot["mid"])
            _px(surf, 6 + ol, row, pal["armor_shadow"] if row < 16 else boot["shadow"])
            _px(surf, 7 + ol, row, outline)
            _px(surf, 8 + orr, row, outline)
            _px(surf, 9 + orr, row, pal["armor_mid"] if row < 16 else boot["mid"])
            _px(surf, 10 + orr, row, pal["armor_shadow"] if row < 16 else boot["shadow"])
            _px(surf, 11 + orr, row, outline)

    for x in range(4, 12):
        _px(surf, x, 18, outline)


def _draw_side_sprite(surf, pal, hair_pal, skin, boot, outline, frame, player_class):
    """Draw a right-facing side profile sprite on a 16x24 surface.

    For left-facing, the caller flips this horizontally.
    True SNES side profile: narrower body, one visible eye, arm in front
    holding weapon, hair trailing behind, armor detail from the side.
    """
    W, H = 16, 24
    eye_color = (40, 60, 120)

    bob = 0
    leg_frame = frame % 4
    if leg_frame in (1, 3):
        bob = -1

    # --- HAIR (top of head, shifted right for side view) ---
    # Hair trails behind (left side), face points right
    for x in range(4, 11):
        _px(surf, x, 0 + bob, outline)
    # Row 1: hair fill
    _px(surf, 3, 1 + bob, outline)
    for x in range(4, 11):
        if x < 6:
            _px(surf, x, 1 + bob, hair_pal["shadow"])
        elif x < 8:
            _px(surf, x, 1 + bob, hair_pal["mid"])
        else:
            _px(surf, x, 1 + bob, hair_pal["highlight"])
    _px(surf, 11, 1 + bob, outline)

    # Row 2: hair + forehead visible on right
    _px(surf, 3, 2 + bob, outline)
    _px(surf, 4, 2 + bob, hair_pal["shadow"])
    _px(surf, 5, 2 + bob, hair_pal["mid"])
    _px(surf, 6, 2 + bob, hair_pal["mid"])
    _px(surf, 7, 2 + bob, hair_pal["highlight"])
    _px(surf, 8, 2 + bob, skin["highlight"])  # forehead
    _px(surf, 9, 2 + bob, skin["mid"])
    _px(surf, 10, 2 + bob, skin["mid"])
    _px(surf, 11, 2 + bob, outline)

    # --- FACE (rows 3-5, side profile) ---
    # Row 3: eye visible, nose starts to protrude right
    _px(surf, 3, 3 + bob, outline)
    _px(surf, 4, 3 + bob, hair_pal["shadow"])  # hair behind
    _px(surf, 5, 3 + bob, hair_pal["shadow"])
    _px(surf, 6, 3 + bob, skin["shadow"])  # ear
    _px(surf, 7, 3 + bob, skin["mid"])
    _px(surf, 8, 3 + bob, skin["mid"])
    _px(surf, 9, 3 + bob, eye_color)  # eye
    _px(surf, 10, 3 + bob, skin["highlight"])
    _px(surf, 11, 3 + bob, outline)  # face edge

    # Row 4: mouth, nose tip extends right
    _px(surf, 4, 4 + bob, outline)
    _px(surf, 5, 4 + bob, hair_pal["shadow"])  # hair behind
    _px(surf, 6, 4 + bob, skin["shadow"])
    _px(surf, 7, 4 + bob, skin["mid"])
    _px(surf, 8, 4 + bob, skin["mid"])
    _px(surf, 9, 4 + bob, skin["dark"])  # mouth
    _px(surf, 10, 4 + bob, skin["mid"])
    _px(surf, 11, 4 + bob, skin["highlight"])  # nose tip
    _px(surf, 12, 4 + bob, outline)

    # Row 5: Chin (narrower)
    _px(surf, 5, 5 + bob, outline)
    _px(surf, 6, 5 + bob, skin["shadow"])
    _px(surf, 7, 5 + bob, skin["shadow"])
    _px(surf, 8, 5 + bob, skin["mid"])
    _px(surf, 9, 5 + bob, skin["mid"])
    _px(surf, 10, 5 + bob, skin["shadow"])
    _px(surf, 11, 5 + bob, outline)

    # --- BODY / ARMOR (side view — narrower, ~8px wide) ---
    # Row 6: Shoulders
    _px(surf, 4, 6 + bob, outline)
    _px(surf, 5, 6 + bob, pal["armor_shadow"])
    _px(surf, 6, 6 + bob, pal["armor_mid"])
    _px(surf, 7, 6 + bob, pal["armor_mid"])
    _px(surf, 8, 6 + bob, pal["armor_mid"])
    _px(surf, 9, 6 + bob, pal["armor_hi"])
    _px(surf, 10, 6 + bob, pal["armor_hi"])
    _px(surf, 11, 6 + bob, outline)

    # Row 7: Shoulder pauldron (front)
    _px(surf, 4, 7 + bob, outline)
    _px(surf, 5, 7 + bob, pal["armor_shadow"])
    _px(surf, 6, 7 + bob, pal["armor_mid"])
    _px(surf, 7, 7 + bob, pal["armor_mid"])
    _px(surf, 8, 7 + bob, pal["armor_mid"])
    _px(surf, 9, 7 + bob, pal["armor_hi"])
    _px(surf, 10, 7 + bob, pal["trim"])
    _px(surf, 11, 7 + bob, outline)
    # Back pauldron hint
    _px(surf, 3, 7 + bob, outline)

    # Torso side view (rows 8-11)
    for row in range(8, 12):
        _px(surf, 4, row + bob, outline)
        _px(surf, 5, row + bob, pal["armor_shadow"])
        _px(surf, 6, row + bob, pal["armor_mid"])
        _px(surf, 7, row + bob, pal["armor_mid"])
        _px(surf, 8, row + bob, pal["armor_mid"])
        _px(surf, 9, row + bob, pal["armor_hi"])
        _px(surf, 10, row + bob, pal["armor_hi"])
        _px(surf, 11, row + bob, outline)

    # Belt trim
    for x in range(5, 11):
        _px(surf, x, 11 + bob, pal["trim"])
    _px(surf, 4, 11 + bob, outline)
    _px(surf, 11, 11 + bob, outline)

    # Side armor detail (vertical seam)
    _px(surf, 8, 8 + bob, pal["trim"])
    _px(surf, 8, 9 + bob, pal["trim"])

    # Cape (trails behind on left side)
    if player_class in ("Warrior", "Mage"):
        for row in range(7, 15):
            _px(surf, 3, row + bob, outline)
            if row < 13:
                _px(surf, 4, row + bob, pal["cape"])

    # --- FRONT ARM (visible, holding weapon on right side) ---
    arm_color = skin["mid"] if player_class == "Thief" else pal["armor_hi"]
    arm_shadow = skin["shadow"] if player_class == "Thief" else pal["armor_shadow"]
    # Arm hangs in front when standing, swings when walking
    arm_swing = 0
    if leg_frame == 1:
        arm_swing = -1
    elif leg_frame == 3:
        arm_swing = 1
    for row in range(8, 12):
        _px(surf, 11, row + bob, outline)
        _px(surf, 12, row + bob + arm_swing, arm_color)
        _px(surf, 13, row + bob + arm_swing, outline)
    # Hand
    _px(surf, 12, 12 + bob + arm_swing, skin["mid"])
    _px(surf, 13, 12 + bob + arm_swing, outline)

    # Weapon hint (small sword/dagger extending from hand)
    weapon_colors = pal["trim"]
    _px(surf, 13, 11 + bob + arm_swing, weapon_colors)
    _px(surf, 14, 10 + bob + arm_swing, weapon_colors)

    # --- LOWER BODY / LEGS (side view — single leg visible + hint of back leg) ---
    for x in range(5, 11):
        _px(surf, x, 12 + bob, pal["armor_shadow"])
    _px(surf, 4, 12 + bob, outline)
    _px(surf, 11, 12 + bob, outline)

    if leg_frame == 0 or leg_frame == 2:
        # Standing: both legs overlapping, front leg slightly forward
        for row in range(13, 18):
            # Back leg (slightly left)
            _px(surf, 5, row, outline)
            _px(surf, 6, row, pal["armor_shadow"] if row < 16 else boot["shadow"])
            _px(surf, 7, row, outline)
            # Front leg
            _px(surf, 8, row, outline)
            _px(surf, 9, row, pal["armor_mid"] if row < 16 else boot["mid"])
            _px(surf, 10, row, pal["armor_hi"] if row < 16 else boot["highlight"])
            _px(surf, 11, row, outline)
    elif leg_frame == 1:
        # Front leg forward (right), back leg behind (left)
        for row in range(13, 18):
            fwd = 1 if row > 14 else 0
            bk = -1 if row > 14 else 0
            _px(surf, 5 + bk, row, outline)
            _px(surf, 6 + bk, row, pal["armor_shadow"] if row < 16 else boot["shadow"])
            _px(surf, 7 + bk, row, outline)
            _px(surf, 8 + fwd, row, outline)
            _px(surf, 9 + fwd, row, pal["armor_mid"] if row < 16 else boot["mid"])
            _px(surf, 10 + fwd, row, pal["armor_hi"] if row < 16 else boot["highlight"])
            _px(surf, 11 + fwd, row, outline)
    elif leg_frame == 3:
        # Back leg forward, front leg behind
        for row in range(13, 18):
            fwd = -1 if row > 14 else 0
            bk = 1 if row > 14 else 0
            _px(surf, 5 + fwd, row, outline)
            _px(surf, 6 + fwd, row, pal["armor_shadow"] if row < 16 else boot["shadow"])
            _px(surf, 7 + fwd, row, outline)
            _px(surf, 8 + bk, row, outline)
            _px(surf, 9 + bk, row, pal["armor_mid"] if row < 16 else boot["mid"])
            _px(surf, 10 + bk, row, pal["armor_hi"] if row < 16 else boot["highlight"])
            _px(surf, 11 + bk, row, outline)

    # Boot soles
    for x in range(5, 12):
        _px(surf, x, 18, outline)


def create_player_sprite(player_class="Warrior", facing="down", frame=0, hair="brown"):
    """Generate a 16x24 SNES FF-style character sprite.

    Returns a pygame Surface with per-pixel alpha.
    Front/back get symmetric sprites. Left/right get true side profiles
    with visible weapon arm, one eye, and proper body silhouette.
    """
    W, H = 16, 24
    surf = pygame.Surface((W, H), pygame.SRCALPHA)

    pal = CLASS_PALETTES.get(player_class, CLASS_PALETTES["Warrior"])
    hair_pal = HAIR_PALETTES.get(hair, HAIR_PALETTES["brown"])
    skin = SKIN_PALETTE
    boot = BOOT_PALETTE
    outline = (20, 20, 30)

    if facing in ("down", "up"):
        _draw_front_back_sprite(surf, pal, hair_pal, skin, boot, outline, facing, frame, player_class)
    elif facing == "right":
        _draw_side_sprite(surf, pal, hair_pal, skin, boot, outline, frame, player_class)
    elif facing == "left":
        # Draw right-facing then flip horizontally (classic SNES technique)
        _draw_side_sprite(surf, pal, hair_pal, skin, boot, outline, frame, player_class)
        surf = pygame.transform.flip(surf, True, False)

    return surf


def create_enemy_sprite(name, sprite_color, size=48):
    """Generate a detailed SNES-style enemy sprite.

    Each enemy type gets a unique procedural sprite with proper
    shading, outlines, and details like FF4/FF6 enemy art.
    """
    surf = pygame.Surface((size, size), pygame.SRCALPHA)

    r, g, b = sprite_color
    outline = (max(0, r - 60), max(0, g - 60), max(0, b - 60))
    highlight = (min(255, r + 60), min(255, g + 60), min(255, b + 60))
    shadow = (max(0, r - 30), max(0, g - 30), max(0, b - 30))
    dark = (max(0, r - 80), max(0, g - 80), max(0, b - 80))

    cx, cy = size // 2, size // 2

    if "Slime" in name:
        _draw_slime_sprite(surf, cx, cy, size, sprite_color, highlight, shadow, outline)
    elif "Rat" in name:
        _draw_rat_sprite(surf, cx, cy, size, sprite_color, highlight, shadow, outline)
    elif "Goblin" in name:
        _draw_goblin_sprite(surf, cx, cy, size, sprite_color, highlight, shadow, outline)
    elif "Troll" in name:
        _draw_troll_sprite(surf, cx, cy, size, sprite_color, highlight, shadow, outline)
    elif "Elf" in name:
        _draw_elf_sprite(surf, cx, cy, size, sprite_color, highlight, shadow, outline)
    elif "Golem" in name:
        _draw_golem_sprite(surf, cx, cy, size, sprite_color, highlight, shadow, outline)
    elif "Wolf" in name or "Were" in name:
        _draw_wolf_sprite(surf, cx, cy, size, sprite_color, highlight, shadow, outline)
    elif "Dragon" in name:
        _draw_dragon_sprite(surf, cx, cy, size, sprite_color, highlight, shadow, outline)
    elif "Knight" in name:
        _draw_knight_sprite(surf, cx, cy, size, sprite_color, highlight, shadow, outline)
    elif "Specter" in name or "Demon" in name:
        _draw_specter_sprite(surf, cx, cy, size, sprite_color, highlight, shadow, outline)
    elif "Ogre" in name:
        _draw_troll_sprite(surf, cx, cy, size, sprite_color, highlight, shadow, outline)
    elif "Vampire" in name:
        _draw_elf_sprite(surf, cx, cy, size, (80, 30, 30), (120, 50, 50), (50, 15, 15), outline)
    else:
        # Generic enemy
        _draw_generic_sprite(surf, cx, cy, size, sprite_color, highlight, shadow, outline)

    return surf


def _draw_slime_sprite(surf, cx, cy, size, color, hi, shadow, outline):
    """Classic RPG slime — dome shape with eyes and sheen."""
    s = size
    # Body dome
    for y in range(s // 3, s - 4):
        t = (y - s // 3) / (s - 4 - s // 3)
        width = int(s * 0.4 * (1 - (t - 0.8) ** 2)) if t > 0.5 else int(s * 0.35 * (t * 2))
        width = max(2, min(width, s // 2 - 2))
        for x in range(-width, width + 1):
            px = cx + x
            py = y
            if abs(x) == width or y == s - 5:
                _px(surf, px, py, outline)
            elif x < -width // 2:
                _px(surf, px, py, shadow)
            elif x < 0:
                _px(surf, px, py, color)
            else:
                _px(surf, px, py, hi if x < width // 3 and y < cy else color)

    # Top outline
    for x in range(cx - s // 5, cx + s // 5):
        _px(surf, x, s // 3 - 1, outline)

    # Sheen highlight (top-left reflection)
    for dy in range(3):
        for dx in range(3 - dy):
            _px(surf, cx - s // 6 + dx, s // 3 + 3 + dy, (255, 255, 255, 180))

    # Eyes
    eye_y = cy - 2
    # Left eye
    for dy in range(-2, 3):
        for dx in range(-2, 3):
            if dx * dx + dy * dy <= 4:
                _px(surf, cx - 6 + dx, eye_y + dy, (255, 255, 255))
    _px(surf, cx - 6, eye_y, (20, 20, 40))
    _px(surf, cx - 5, eye_y, (20, 20, 40))
    # Right eye
    for dy in range(-2, 3):
        for dx in range(-2, 3):
            if dx * dx + dy * dy <= 4:
                _px(surf, cx + 6 + dx, eye_y + dy, (255, 255, 255))
    _px(surf, cx + 6, eye_y, (20, 20, 40))
    _px(surf, cx + 7, eye_y, (20, 20, 40))

    # Mouth
    for x in range(cx - 3, cx + 4):
        _px(surf, x, cy + 4, outline)

    # Base shadow
    for x in range(cx - s // 4, cx + s // 4):
        _px(surf, x, s - 3, (0, 0, 0, 60))
        _px(surf, x, s - 2, (0, 0, 0, 30))


def _draw_rat_sprite(surf, cx, cy, size, color, hi, shadow, outline):
    """Giant rat with beady eyes and long tail."""
    s = size
    # Body (oval)
    for y in range(cy - 6, cy + 8):
        t = abs(y - cy) / 8
        w = int((1 - t * t) * s // 3)
        for x in range(-w, w + 1):
            if abs(x) >= w - 1 or abs(y - cy) >= 7:
                _px(surf, cx + x - 3, y, outline)
            elif x < 0:
                _px(surf, cx + x - 3, y, shadow)
            else:
                _px(surf, cx + x - 3, y, color if x < w // 2 else hi)

    # Head (smaller oval, front)
    for y in range(cy - 8, cy + 2):
        t = abs(y - (cy - 3)) / 5
        w = int((1 - t * t) * 8)
        for x in range(-w, w + 1):
            px = cx + s // 5 + x
            if abs(x) >= w - 1:
                _px(surf, px, y, outline)
            else:
                _px(surf, px, y, hi if y < cy - 4 else color)

    # Ears
    for dy in range(4):
        _px(surf, cx + s // 5 - 4, cy - 8 - dy, outline)
        _px(surf, cx + s // 5 - 3, cy - 8 - dy, (255, 180, 180))
        _px(surf, cx + s // 5 + 4, cy - 8 - dy, outline)
        _px(surf, cx + s // 5 + 3, cy - 8 - dy, (255, 180, 180))

    # Eyes (beady red)
    _px(surf, cx + s // 5 - 2, cy - 5, (255, 40, 40))
    _px(surf, cx + s // 5 + 2, cy - 5, (255, 40, 40))
    _px(surf, cx + s // 5 - 2, cy - 4, (200, 20, 20))
    _px(surf, cx + s // 5 + 2, cy - 4, (200, 20, 20))

    # Nose
    _px(surf, cx + s // 5 + 8, cy - 3, (255, 150, 150))

    # Whiskers
    for i in range(3):
        for dx in range(4):
            _px(surf, cx + s // 5 + 6 + dx, cy - 4 + i * 2, (180, 160, 140))

    # Tail (curvy)
    tail_x = cx - s // 4
    for i in range(12):
        ty = cy + 2 + (i % 3 - 1)
        _px(surf, tail_x - i, ty, (200, 160, 160))
        _px(surf, tail_x - i, ty + 1, outline)

    # Legs
    for i in range(3):
        lx = cx - 8 + i * 8
        for ly in range(cy + 6, cy + 10):
            _px(surf, lx, ly, outline)
            _px(surf, lx + 1, ly, color)


def _draw_goblin_sprite(surf, cx, cy, size, color, hi, shadow, outline):
    """Goblin with pointy ears, crude armor, and a dagger."""
    s = size
    # Head
    for y in range(cy - 14, cy - 4):
        t = abs(y - (cy - 9)) / 5
        w = int((1 - t * t) * 7)
        for x in range(-w, w + 1):
            if abs(x) >= w - 1:
                _px(surf, cx + x, y, outline)
            elif x < 0:
                _px(surf, cx + x, y, color)
            else:
                _px(surf, cx + x, y, hi)

    # Pointy ears
    for i in range(5):
        _px(surf, cx - 8 - i, cy - 10 + i, outline)
        _px(surf, cx - 7 - i, cy - 10 + i, color)
        _px(surf, cx + 8 + i, cy - 10 + i, outline)
        _px(surf, cx + 7 + i, cy - 10 + i, hi)

    # Eyes (mean yellow)
    _px(surf, cx - 3, cy - 10, (255, 255, 50))
    _px(surf, cx - 2, cy - 10, (255, 255, 50))
    _px(surf, cx + 2, cy - 10, (255, 255, 50))
    _px(surf, cx + 3, cy - 10, (255, 255, 50))
    _px(surf, cx - 2, cy - 9, (20, 20, 0))
    _px(surf, cx + 3, cy - 9, (20, 20, 0))

    # Mouth (fangs)
    for x in range(cx - 3, cx + 4):
        _px(surf, x, cy - 7, outline)
    _px(surf, cx - 2, cy - 6, (255, 255, 255))
    _px(surf, cx + 2, cy - 6, (255, 255, 255))

    # Body (crude leather armor)
    armor_color = (120, 90, 50)
    armor_dark = (80, 55, 30)
    for y in range(cy - 4, cy + 8):
        w = 8 if y < cy + 4 else 8 - (y - cy - 4)
        for x in range(-w, w + 1):
            if abs(x) >= w - 1:
                _px(surf, cx + x, y, outline)
            elif x < 0:
                _px(surf, cx + x, y, armor_dark)
            else:
                _px(surf, cx + x, y, armor_color)

    # Belt
    for x in range(cx - 7, cx + 8):
        _px(surf, x, cy + 1, (180, 150, 50))

    # Arms
    for y in range(cy - 2, cy + 5):
        _px(surf, cx - 9, y, outline)
        _px(surf, cx - 8, y, color)
        _px(surf, cx + 9, y, outline)
        _px(surf, cx + 8, y, hi)

    # Dagger in right hand
    for i in range(8):
        _px(surf, cx + 10, cy - 2 - i, (200, 200, 210))
    _px(surf, cx + 9, cy - 1, (160, 140, 60))
    _px(surf, cx + 11, cy - 1, (160, 140, 60))

    # Legs
    for y in range(cy + 8, cy + 14):
        _px(surf, cx - 4, y, outline)
        _px(surf, cx - 3, y, color)
        _px(surf, cx - 2, y, shadow)
        _px(surf, cx + 2, y, outline)
        _px(surf, cx + 3, y, color)
        _px(surf, cx + 4, y, shadow)

    # Feet
    for x in range(cx - 5, cx - 1):
        _px(surf, x, cy + 14, outline)
    for x in range(cx + 1, cx + 6):
        _px(surf, x, cy + 14, outline)


def _draw_troll_sprite(surf, cx, cy, size, color, hi, shadow, outline):
    """Large troll/ogre — bulky body, club weapon."""
    s = size
    # Big head
    for y in range(4, 18):
        t = abs(y - 11) / 7
        w = int((1 - t * t) * 10)
        for x in range(-w, w + 1):
            if abs(x) >= w - 1:
                _px(surf, cx + x, y, outline)
            else:
                _px(surf, cx + x, y, hi if x < -w // 2 else color)

    # Eyes
    _px(surf, cx - 4, 9, (255, 200, 50))
    _px(surf, cx - 3, 9, (255, 200, 50))
    _px(surf, cx + 3, 9, (255, 200, 50))
    _px(surf, cx + 4, 9, (255, 200, 50))
    _px(surf, cx - 3, 10, (80, 20, 0))
    _px(surf, cx + 4, 10, (80, 20, 0))

    # Mouth
    for x in range(cx - 5, cx + 6):
        _px(surf, x, 14, outline)
    _px(surf, cx - 3, 15, (255, 255, 230))  # fang
    _px(surf, cx + 3, 15, (255, 255, 230))  # fang

    # Massive body
    for y in range(18, 36):
        t = (y - 18) / 18
        w = int(14 - abs(t - 0.3) * 8)
        w = max(6, min(w, 14))
        for x in range(-w, w + 1):
            if abs(x) >= w - 1:
                _px(surf, cx + x, y, outline)
            elif x < -w // 3:
                _px(surf, cx + x, y, shadow)
            elif x < w // 3:
                _px(surf, cx + x, y, color)
            else:
                _px(surf, cx + x, y, hi)

    # Club in hand
    for y in range(8, 32):
        _px(surf, cx + 16, y, (100, 70, 30))
        _px(surf, cx + 17, y, (80, 50, 20))
    # Club head
    for y in range(5, 12):
        for x in range(15, 21):
            _px(surf, cx + x - 1, y, (90, 60, 25))

    # Legs
    for y in range(36, 44):
        for dx in [-4, -3, 4, 5]:
            _px(surf, cx + dx, y, color if abs(dx) < 5 else outline)
    for x in range(cx - 6, cx - 1):
        _px(surf, x, 44, outline)
    for x in range(cx + 2, cx + 8):
        _px(surf, x, 44, outline)


def _draw_elf_sprite(surf, cx, cy, size, color, hi, shadow, outline):
    """Dark elf — slender, elegant, menacing."""
    s = size
    # Hair (long flowing)
    for y in range(2, 20):
        w = 5 if y < 10 else 5 + (y - 10) // 2
        for x in range(-w, w + 1):
            if abs(x) >= w - 1:
                _px(surf, cx + x, y, outline)
            else:
                _px(surf, cx + x, y, (60, 50, 80) if x < 0 else (80, 70, 110))

    # Face
    for y in range(6, 14):
        w = 4
        for x in range(-w, w + 1):
            if abs(x) >= w - 1:
                pass  # Hair covers outline
            else:
                _px(surf, cx + x, y, (200, 180, 210))

    # Eyes (glowing)
    _px(surf, cx - 2, 8, (200, 50, 50))
    _px(surf, cx - 1, 8, (255, 80, 80))
    _px(surf, cx + 1, 8, (200, 50, 50))
    _px(surf, cx + 2, 8, (255, 80, 80))

    # Robes
    for y in range(14, 40):
        t = (y - 14) / 26
        w = int(6 + t * 10)
        for x in range(-w, w + 1):
            if abs(x) >= w - 1:
                _px(surf, cx + x, y, outline)
            elif x < -w // 3:
                _px(surf, cx + x, y, shadow)
            elif x > w // 3:
                _px(surf, cx + x, y, hi)
            else:
                _px(surf, cx + x, y, color)

    # Robe trim
    for y in range(14, 40, 6):
        for x in range(cx - 5, cx + 6):
            _px(surf, x, y, (180, 160, 60))

    # Staff
    for y in range(0, 42):
        _px(surf, cx - 12, y, (140, 100, 40))
    # Staff orb
    for dy in range(-3, 4):
        for dx in range(-3, 4):
            if dx * dx + dy * dy <= 9:
                _px(surf, cx - 12 + dx, 3 + dy, (100, 200, 255))
    _px(surf, cx - 13, 1, (200, 240, 255))  # Glint


def _draw_golem_sprite(surf, cx, cy, size, color, hi, shadow, outline):
    """Stone golem — blocky, massive, rocky texture."""
    s = size
    # Head (square)
    for y in range(4, 14):
        for x in range(cx - 8, cx + 9):
            if x == cx - 8 or x == cx + 8 or y == 4 or y == 13:
                _px(surf, x, y, outline)
            else:
                # Rocky texture
                noise = ((x * 7 + y * 13) % 5) * 8
                c = tuple(min(255, v + noise - 16) for v in color)
                _px(surf, x, y, c)

    # Eyes (glowing cracks)
    for dx in range(3):
        _px(surf, cx - 4 + dx, 8, (255, 200, 50))
        _px(surf, cx + 2 + dx, 8, (255, 200, 50))

    # Massive body
    for y in range(14, 40):
        w = 14 if y < 30 else 14 - (y - 30) // 2
        for x in range(-w, w + 1):
            px = cx + x
            if abs(x) >= w - 1:
                _px(surf, px, y, outline)
            else:
                noise = ((px * 11 + y * 7) % 7) * 6
                c = tuple(max(0, min(255, v + noise - 18)) for v in (color if x < 0 else hi))
                _px(surf, px, y, c)

    # Crack lines for texture
    for i in range(3):
        sx = cx - 8 + i * 7
        for y in range(18 + i * 3, 28 + i * 3):
            _px(surf, sx + (y % 2), y, shadow)

    # Arms (thick)
    for y in range(16, 32):
        for dx in range(4):
            _px(surf, cx - 15 + dx, y, color if dx > 0 else outline)
            _px(surf, cx + 12 + dx, y, hi if dx < 3 else outline)
    # Fists
    for dy in range(4):
        for dx in range(5):
            _px(surf, cx - 16 + dx, 32 + dy, color if dx > 0 and dy < 3 else outline)
            _px(surf, cx + 11 + dx, 32 + dy, hi if dx < 4 and dy < 3 else outline)

    # Legs
    for y in range(38, 46):
        for dx in range(-5, -1):
            _px(surf, cx + dx, y, color if dx > -5 else outline)
        for dx in range(2, 6):
            _px(surf, cx + dx, y, hi if dx < 5 else outline)
    for x in range(cx - 6, cx + 7):
        _px(surf, x, 46, outline)


def _draw_wolf_sprite(surf, cx, cy, size, color, hi, shadow, outline):
    """Werewolf — hunched beast on two legs."""
    s = size
    # Head (snout)
    for y in range(4, 16):
        t = abs(y - 10) / 6
        w = int((1 - t) * 8)
        for x in range(-w, w + 1):
            px = cx + x + 4
            if abs(x) >= w - 1:
                _px(surf, px, y, outline)
            else:
                _px(surf, px, y, hi if x > 0 and y < 10 else color)

    # Snout extension
    for y in range(10, 16):
        for x in range(5):
            _px(surf, cx + 8 + x, y, color if x < 4 else outline)

    # Ears (pointed)
    for i in range(5):
        _px(surf, cx - 2, 4 - i, outline)
        _px(surf, cx - 1, 4 - i, color)
        _px(surf, cx + 6, 4 - i, outline)
        _px(surf, cx + 5, 4 - i, hi)

    # Eyes (fierce yellow)
    _px(surf, cx + 1, 8, (255, 220, 0))
    _px(surf, cx + 2, 8, (255, 220, 0))
    _px(surf, cx + 5, 8, (255, 220, 0))
    _px(surf, cx + 6, 8, (255, 220, 0))

    # Teeth
    for x in range(cx + 8, cx + 13):
        if x % 2 == 0:
            _px(surf, x, 14, (255, 255, 240))

    # Hunched body with fur
    for y in range(14, 36):
        t = (y - 14) / 22
        w = int(10 + t * 4) if t < 0.6 else int(14 - (t - 0.6) * 10)
        for x in range(-w, w + 1):
            px = cx + x
            if abs(x) >= w - 1:
                _px(surf, px, y, outline)
            else:
                # Fur texture
                fur = ((px * 3 + y * 5) % 3) * 10
                c = tuple(max(0, min(255, v + fur - 10)) for v in (shadow if x < -w // 2 else color))
                _px(surf, px, y, c)

    # Claws (arms reaching forward)
    for y in range(18, 28):
        _px(surf, cx + 12, y, outline)
        _px(surf, cx + 13, y, color)
        _px(surf, cx + 14, y, outline)
    for i in range(3):
        _px(surf, cx + 14 + i, 27, (220, 220, 200))

    # Legs
    for y in range(34, 44):
        _px(surf, cx - 5, y, outline)
        _px(surf, cx - 4, y, color)
        _px(surf, cx - 3, y, shadow)
        _px(surf, cx + 3, y, outline)
        _px(surf, cx + 4, y, color)
        _px(surf, cx + 5, y, shadow)
    # Clawed feet
    for i in range(3):
        _px(surf, cx - 6 + i, 44, (220, 220, 200))
        _px(surf, cx + 3 + i, 44, (220, 220, 200))


def _draw_dragon_sprite(surf, cx, cy, size, color, hi, shadow, outline):
    """Dragon whelp / bone dragon — winged serpentine creature."""
    s = size
    r, g, b = color

    # Wings
    wing_color = (min(255, r + 20), min(255, g + 10), min(255, b + 10))
    wing_membrane = (max(0, r - 20), max(0, g + 20), max(0, b - 10))
    for i in range(16):
        t = i / 16
        wy = int(cy - 18 + t * 12)
        # Left wing
        _px(surf, cx - 8 - i, wy, outline)
        _px(surf, cx - 7 - i, wy, wing_color)
        _px(surf, cx - 7 - i, wy + 1, wing_membrane)
        # Right wing
        _px(surf, cx + 8 + i, wy, outline)
        _px(surf, cx + 7 + i, wy, wing_color)
        _px(surf, cx + 7 + i, wy + 1, wing_membrane)
    # Wing bones
    for i in range(12):
        _px(surf, cx - 8 - i, cy - 18 + (i * 12 // 16), (200, 200, 190))
        _px(surf, cx + 8 + i, cy - 18 + (i * 12 // 16), (200, 200, 190))

    # Body
    for y in range(cy - 8, cy + 12):
        t = abs(y - (cy + 2)) / 10
        w = int((1 - t * t) * 10)
        w = max(3, w)
        for x in range(-w, w + 1):
            px = cx + x
            if abs(x) >= w - 1:
                _px(surf, px, y, outline)
            else:
                # Scale texture
                scale = ((px + y) % 3 == 0)
                if scale:
                    _px(surf, px, y, hi)
                elif x < 0:
                    _px(surf, px, y, color)
                else:
                    _px(surf, px, y, shadow)

    # Belly (lighter)
    belly = (min(255, r + 60), min(255, g + 60), min(255, b + 40))
    for y in range(cy, cy + 8):
        for x in range(-3, 4):
            _px(surf, cx + x, y, belly)

    # Head (horned)
    for y in range(cy - 14, cy - 6):
        w = 5
        for x in range(-w, w + 1):
            if abs(x) >= w - 1:
                _px(surf, cx + x, y, outline)
            else:
                _px(surf, cx + x, y, color)

    # Horns
    for i in range(5):
        _px(surf, cx - 4 - i, cy - 14 - i, (200, 190, 160))
        _px(surf, cx + 4 + i, cy - 14 - i, (200, 190, 160))

    # Eyes (fiery)
    _px(surf, cx - 2, cy - 11, (255, 100, 0))
    _px(surf, cx - 1, cy - 11, (255, 200, 0))
    _px(surf, cx + 1, cy - 11, (255, 100, 0))
    _px(surf, cx + 2, cy - 11, (255, 200, 0))

    # Jaw
    for x in range(cx - 4, cx + 5):
        _px(surf, x, cy - 7, outline)

    # Tail
    for i in range(14):
        ty = cy + 10 + i // 3
        tx = cx - 8 - i
        tw = max(1, 3 - i // 5)
        for dy in range(tw):
            _px(surf, tx, ty + dy, color if dy < tw - 1 else outline)

    # Legs
    for y in range(cy + 10, cy + 18):
        _px(surf, cx - 5, y, outline)
        _px(surf, cx - 4, y, color)
        _px(surf, cx + 4, y, outline)
        _px(surf, cx + 5, y, color)


def _draw_knight_sprite(surf, cx, cy, size, color, hi, shadow, outline):
    """Chaos Knight — armored warrior with sword and shield."""
    s = size
    # Helmet
    for y in range(4, 14):
        w = 6
        for x in range(-w, w + 1):
            if abs(x) >= w - 1 or y == 4 or y == 13:
                _px(surf, cx + x, y, outline)
            else:
                _px(surf, cx + x, y, (160, 160, 170) if x < 0 else (120, 120, 130))
    # Visor slit
    for x in range(cx - 4, cx + 5):
        _px(surf, x, 9, (180, 40, 40))
    # Helmet crest
    for y in range(0, 5):
        _px(surf, cx, y, (200, 40, 40))
        _px(surf, cx + 1, y, (180, 30, 30))

    # Armor body
    armor_hi = (140, 140, 160)
    armor_mid = (100, 100, 120)
    armor_dark = (60, 60, 80)
    for y in range(14, 34):
        w = 9 if y < 28 else 9 - (y - 28) // 2
        for x in range(-w, w + 1):
            px = cx + x
            if abs(x) >= w - 1:
                _px(surf, px, y, outline)
            elif x < -w // 3:
                _px(surf, px, y, armor_dark)
            elif x < w // 3:
                _px(surf, px, y, armor_mid)
            else:
                _px(surf, px, y, armor_hi)

    # Armor details (cross emblem)
    for y in range(18, 26):
        _px(surf, cx, y, (180, 40, 40))
    for x in range(cx - 3, cx + 4):
        _px(surf, x, 21, (180, 40, 40))

    # Shield (left arm)
    for y in range(16, 30):
        for x in range(-5, 1):
            _px(surf, cx - 10 + x, y, armor_mid if x > -4 else outline)
    _px(surf, cx - 12, 22, (200, 50, 50))  # Shield emblem

    # Sword (right arm)
    for y in range(4, 30):
        _px(surf, cx + 12, y, (200, 200, 220) if y > 10 else (160, 140, 60))
        if y > 10:
            _px(surf, cx + 13, y, (180, 180, 200))
    _px(surf, cx + 11, 10, (160, 140, 60))
    _px(surf, cx + 13, 10, (160, 140, 60))

    # Legs (armored)
    for y in range(34, 44):
        _px(surf, cx - 4, y, outline)
        _px(surf, cx - 3, y, armor_mid)
        _px(surf, cx - 2, y, armor_dark)
        _px(surf, cx + 2, y, outline)
        _px(surf, cx + 3, y, armor_mid)
        _px(surf, cx + 4, y, armor_dark)
    # Boots
    for x in range(cx - 5, cx):
        _px(surf, x, 44, outline)
    for x in range(cx + 1, cx + 6):
        _px(surf, x, 44, outline)


def _draw_specter_sprite(surf, cx, cy, size, color, hi, shadow, outline):
    """Ghost / demon — ethereal floating figure."""
    s = size
    import math

    # Ethereal body (wavy, transparent-looking)
    for y in range(6, 44):
        t = (y - 6) / 38
        wave = int(math.sin(t * 6) * 3)
        w = int(8 + t * 8)
        alpha = max(60, 255 - int(t * 200))
        for x in range(-w, w + 1):
            px = cx + x + wave
            if abs(x) >= w - 1:
                _px(surf, px, y, (*outline, alpha))
            elif abs(x) >= w - 3:
                _px(surf, px, y, (*shadow, alpha))
            elif x < 0:
                _px(surf, px, y, (*color, alpha))
            else:
                _px(surf, px, y, (*hi, alpha))

    # Head (skull-like)
    for y in range(4, 16):
        t = abs(y - 10) / 6
        w = int((1 - t * t) * 8)
        for x in range(-w, w + 1):
            if abs(x) >= w - 1:
                _px(surf, cx + x, y, outline)
            else:
                _px(surf, cx + x, y, (200, 200, 220))

    # Hollow eyes (glowing)
    for dy in range(-2, 2):
        for dx in range(-2, 2):
            _px(surf, cx - 3 + dx, 9 + dy, (180, 0, 0))
            _px(surf, cx + 3 + dx, 9 + dy, (180, 0, 0))
    _px(surf, cx - 3, 9, (255, 50, 50))
    _px(surf, cx + 3, 9, (255, 50, 50))

    # Mouth (dark void)
    for x in range(cx - 2, cx + 3):
        for y in range(12, 14):
            _px(surf, x, y, (0, 0, 0))

    # Spectral wisps trailing off
    for i in range(3):
        wx = cx - 6 + i * 6
        for y in range(38, 46):
            alpha = max(0, 120 - (y - 38) * 15)
            _px(surf, wx + (y % 2), y, (*color, alpha))
            _px(surf, wx + 1, y, (*hi, alpha))


def _draw_generic_sprite(surf, cx, cy, size, color, hi, shadow, outline):
    """Fallback generic enemy sprite."""
    for y in range(size // 4, size * 3 // 4):
        t = abs(y - cy) / (size // 4)
        w = int((1 - t * t) * size // 3)
        w = max(4, w)
        for x in range(-w, w + 1):
            if abs(x) >= w - 1:
                _px(surf, cx + x, y, outline)
            elif x < 0:
                _px(surf, cx + x, y, shadow)
            else:
                _px(surf, cx + x, y, color)
    # Eyes
    _px(surf, cx - 4, cy - 4, (255, 255, 255))
    _px(surf, cx + 4, cy - 4, (255, 255, 255))
    _px(surf, cx - 4, cy - 3, (200, 40, 40))
    _px(surf, cx + 4, cy - 3, (200, 40, 40))


# --- Tile rendering ---

def create_grass_tile(size=16, variant=0):
    """SNES-style grass tile with detail and variation."""
    surf = pygame.Surface((size, size))
    # Base green with subtle variation
    base = (34, 130, 34) if variant % 2 == 0 else (38, 125, 38)
    surf.fill(base)

    # Grass blade details
    detail_positions = [
        (2, 3), (7, 1), (12, 4), (4, 8), (10, 10), (1, 12), (14, 7),
        (6, 14), (11, 2), (3, 6), (9, 12), (13, 14),
    ]
    for i, (gx, gy) in enumerate(detail_positions):
        if (i + variant) % 3 == 0:
            c = (28, 110, 28)  # Darker blade
        elif (i + variant) % 3 == 1:
            c = (50, 150, 45)  # Lighter blade
        else:
            continue
        if gx < size and gy < size:
            _px(surf, gx, gy, c)
            if gy > 0:
                _px(surf, gx, gy - 1, (42, 140, 40))

    return surf


def create_path_tile(size=16, variant=0):
    """Dirt/cobblestone path tile."""
    surf = pygame.Surface((size, size))
    base = (175, 150, 95)
    surf.fill(base)

    # Cobblestone pattern
    stones = [(2, 2, 5, 4), (8, 1, 6, 4), (1, 7, 4, 5), (6, 6, 5, 5),
              (12, 7, 3, 4), (3, 12, 5, 3), (9, 11, 5, 4)]
    for i, (sx, sy, sw, sh) in enumerate(stones):
        if (i + variant) % 5 == 0:
            continue
        stone_color = (
            160 + ((i * 17 + variant * 7) % 30),
            135 + ((i * 13 + variant * 11) % 25),
            85 + ((i * 19 + variant * 3) % 20),
        )
        for y in range(sy, min(sy + sh, size)):
            for x in range(sx, min(sx + sw, size)):
                if x == sx or x == sx + sw - 1 or y == sy or y == sy + sh - 1:
                    _px(surf, x, y, (140, 120, 70))
                else:
                    _px(surf, x, y, stone_color)

    return surf


def create_wall_tile(size=16, variant=0):
    """Brick/stone wall tile with SNES-quality detail."""
    surf = pygame.Surface((size, size))
    base = (110, 80, 55)
    surf.fill(base)

    # Brick rows
    for row in range(0, size, 4):
        offset = 4 if (row // 4 + variant) % 2 == 0 else 0
        for col in range(offset, size, 8):
            brick_w = min(7, size - col)
            brick_h = min(3, size - row)
            # Brick color with variation
            noise = ((row * 7 + col * 3 + variant) % 5) * 4
            brick_color = (105 + noise, 72 + noise, 45 + noise)
            brick_hi = (125 + noise, 92 + noise, 60 + noise)
            for y in range(row, row + brick_h):
                for x in range(col, col + brick_w):
                    if x < size and y < size:
                        if y == row:
                            _px(surf, x, y, brick_hi)
                        elif x == col:
                            _px(surf, x, y, brick_hi)
                        else:
                            _px(surf, x, y, brick_color)
            # Mortar lines
            if row + brick_h < size:
                for x in range(col, min(col + brick_w, size)):
                    _px(surf, x, row + brick_h, (80, 60, 40))
            if col + brick_w < size and col + brick_w - 1 >= 0:
                for y in range(row, min(row + brick_h, size)):
                    _px(surf, col + brick_w, y, (80, 60, 40))

    return surf


def create_water_tile(size=16, frame=0):
    """Animated water tile."""
    surf = pygame.Surface((size, size))

    for y in range(size):
        for x in range(size):
            wave = ((x + frame * 2) % 8 + (y + frame) % 6) // 2
            r = 30 + wave * 5
            g = 70 + wave * 8
            b = 160 + wave * 10
            _px(surf, x, y, (min(255, r), min(255, g), min(255, b)))

    # Sparkle highlights
    sparkle_pos = [(3 + frame % 4, 2), (10 - frame % 3, 7), (6, 12 + frame % 3)]
    for sx, sy in sparkle_pos:
        if 0 <= sx < size and 0 <= sy < size:
            _px(surf, sx, sy, (200, 220, 255))

    return surf


def create_door_tile(size=16):
    """Detailed door tile with frame and handle."""
    surf = pygame.Surface((size, size))

    # Door frame (stone)
    surf.fill((100, 80, 60))

    # Door wood
    for y in range(2, size - 1):
        for x in range(3, size - 3):
            # Wood grain
            grain = ((y * 3 + x) % 4)
            if grain == 0:
                _px(surf, x, y, (160, 110, 50))
            elif grain == 1:
                _px(surf, x, y, (150, 100, 45))
            else:
                _px(surf, x, y, (140, 95, 40))

    # Frame border
    for y in range(size):
        _px(surf, 2, y, (80, 65, 45))
        _px(surf, size - 3, y, (80, 65, 45))
    for x in range(2, size - 2):
        _px(surf, x, 1, (80, 65, 45))

    # Door handle
    _px(surf, size - 5, size // 2, (220, 200, 80))
    _px(surf, size - 5, size // 2 + 1, (200, 180, 60))

    # Arch top highlight
    for x in range(4, size - 4):
        _px(surf, x, 2, (180, 140, 70))

    # Iron bands
    for x in range(3, size - 3):
        _px(surf, x, 5, (100, 100, 110))
        _px(surf, x, size - 4, (100, 100, 110))

    return surf


def create_tree_tile(size=16):
    """Detailed tree tile — trunk and canopy."""
    surf = pygame.Surface((size, size), pygame.SRCALPHA)

    # Trunk
    trunk_colors = [(90, 60, 25), (80, 52, 20), (100, 70, 30)]
    for y in range(size // 2, size):
        for x in range(size // 2 - 2, size // 2 + 3):
            ci = (x + y) % 3
            _px(surf, x, y, trunk_colors[ci])

    # Canopy (layered circles)
    import math
    canopy_positions = [
        (size // 2, size // 4, 6, (30, 110, 35)),
        (size // 2 - 3, size // 3, 5, (35, 120, 40)),
        (size // 2 + 3, size // 3, 5, (25, 100, 30)),
        (size // 2, size // 5, 5, (45, 135, 48)),
    ]
    for cpx, cpy, radius, color in canopy_positions:
        for y in range(-radius, radius + 1):
            for x in range(-radius, radius + 1):
                if x * x + y * y <= radius * radius:
                    px, py = cpx + x, cpy + y
                    if 0 <= px < size and 0 <= py < size:
                        # Shading based on position
                        shade = max(0, min(40, x * 5 - y * 3))
                        c = tuple(max(0, min(255, v + shade)) for v in color)
                        _px(surf, px, py, c)

    # Canopy outline
    for y in range(0, size // 2 + 2):
        for x in range(0, size):
            px_color = surf.get_at((x, y))
            if px_color[3] > 0:  # Has content
                # Check neighbors for outline
                for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                    nx, ny = x + dx, y + dy
                    if 0 <= nx < size and 0 <= ny < size:
                        if surf.get_at((nx, ny))[3] == 0:
                            _px(surf, nx, ny, (15, 50, 15, 200))

    return surf


def create_roof_surface(width, height, color=(180, 60, 50)):
    """Create a building roof surface with shingle detail."""
    surf = pygame.Surface((width, height))
    r, g, b = color

    for y in range(height):
        for x in range(width):
            # Shingle rows
            row = y // 3
            offset = 3 if row % 2 == 0 else 0
            col = (x + offset) // 6

            # Color variation per shingle
            noise = ((row * 7 + col * 13) % 5) * 6
            if y % 3 == 0:
                # Shingle edge (shadow)
                _px(surf, x, y, (max(0, r - 40 + noise), max(0, g - 20 + noise), max(0, b - 20 + noise)))
            elif (x + offset) % 6 == 0:
                # Shingle vertical edge
                _px(surf, x, y, (max(0, r - 30 + noise), max(0, g - 15 + noise), max(0, b - 15 + noise)))
            else:
                _px(surf, x, y, (min(255, r + noise), min(255, g + noise // 2), min(255, b + noise // 2)))

    return surf


# --- Sprite cache ---
_sprite_cache = {}
_external_sheet = None


def _load_external_sheet():
    """Load the external sprite sheet if it exists and is enabled."""
    global _external_sheet
    if not USE_EXTERNAL_SPRITES:
        return None
    if _external_sheet is not None:
        return _external_sheet

    if os.path.exists(SPRITE_SHEET_PATH):
        try:
            _external_sheet = pygame.image.load(SPRITE_SHEET_PATH).convert_alpha()
            return _external_sheet
        except pygame.error:
            print(f"Error: Could not load sprite sheet at {SPRITE_SHEET_PATH}")
    return None


def _extract_sheet_sprite(sheet, player_class, facing):
    """Extract a single sprite from the external sprite sheet.

    Uses explicit pixel regions defined in SPRITE_SHEET_REGIONS (settings.py).
    Each class has 3 poses: front (down), side (right), back (up).
    Left facing is the right pose flipped horizontally.
    """
    class_regions = SPRITE_SHEET_REGIONS.get(player_class)
    if not class_regions:
        return None

    lookup_facing = "right" if facing == "left" else facing
    region = class_regions.get(lookup_facing)
    if not region:
        return None

    x, y, w, h = region
    rect = pygame.Rect(x, y, w, h)

    sw, sh = sheet.get_size()
    if rect.right > sw or rect.bottom > sh:
        return None

    try:
        sprite = sheet.subsurface(rect).copy()
        # Remove cream background color — make it transparent
        sprite.set_colorkey((255, 250, 219))
        # Convert to per-pixel alpha for clean edges
        sprite = sprite.convert_alpha()
        # Scale to game display size (not tiny 16x24)
        sprite = pygame.transform.smoothscale(sprite, (PLAYER_SPRITE_W, PLAYER_SPRITE_H))
        if facing == "left":
            sprite = pygame.transform.flip(sprite, True, False)
        return sprite
    except ValueError:
        return None


def get_player_sprite(player_class, facing, frame, hair="brown"):
    """Get a cached player sprite (external or procedural)."""
    key = (player_class, facing, frame, hair)
    if key in _sprite_cache:
        return _sprite_cache[key]

    # Try loading from external sheet first
    sheet = _load_external_sheet()
    if sheet:
        sprite = _extract_sheet_sprite(sheet, player_class, facing)
        if sprite:
            _sprite_cache[key] = sprite
            return _sprite_cache[key]

    # Fallback to procedural generation
    _sprite_cache[key] = create_player_sprite(player_class, facing, frame, hair)
    return _sprite_cache[key]


def get_enemy_sprite(name, sprite_color, size=48):
    """Get a cached enemy sprite."""
    key = ("enemy", name)
    if key not in _sprite_cache:
        _sprite_cache[key] = create_enemy_sprite(name, sprite_color, size)
    return _sprite_cache[key]


_tile_cache = {}


def get_tile(tile_type, variant=0, frame=0):
    """Get a cached tile surface."""
    key = (tile_type, variant, frame)
    if key not in _tile_cache:
        if tile_type == "grass":
            _tile_cache[key] = create_grass_tile(variant=variant)
        elif tile_type == "path":
            _tile_cache[key] = create_path_tile(variant=variant)
        elif tile_type == "wall":
            _tile_cache[key] = create_wall_tile(variant=variant)
        elif tile_type == "water":
            _tile_cache[key] = create_water_tile(frame=frame)
        elif tile_type == "door":
            _tile_cache[key] = create_door_tile()
        elif tile_type == "tree":
            _tile_cache[key] = create_tree_tile()
    return _tile_cache[key]

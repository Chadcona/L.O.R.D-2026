# Save/Load system — JSON-based with 3 slots

import json
import os
from settings import SAVES_DIR, SAVE_SLOTS
from systems.player import Player


def get_save_path(slot):
    """Get the file path for a save slot (1-based)."""
    return os.path.join(SAVES_DIR, f"save_{slot}.json")


def save_game(slot, player, extra_data=None):
    """Save the game to a slot. Returns True on success."""
    os.makedirs(SAVES_DIR, exist_ok=True)
    data = {
        "version": 1,
        "player": player.to_dict(),
    }
    if extra_data:
        data.update(extra_data)
    try:
        with open(get_save_path(slot), 'w') as f:
            json.dump(data, f, indent=2)
        return True
    except (IOError, OSError):
        return False


def load_game(slot):
    """Load a game from a slot. Returns (Player, extra_data) or None."""
    path = get_save_path(slot)
    if not os.path.exists(path):
        return None
    try:
        with open(path, 'r') as f:
            data = json.load(f)
        player = Player.from_dict(data["player"])
        extra_data = {k: v for k, v in data.items() if k not in ("version", "player")}
        return player, extra_data
    except (IOError, OSError, json.JSONDecodeError, KeyError):
        return None


def get_save_info(slot):
    """Get brief info about a save slot for display. Returns dict or None."""
    path = get_save_path(slot)
    if not os.path.exists(path):
        return None
    try:
        with open(path, 'r') as f:
            data = json.load(f)
        p = data["player"]
        return {
            "name": p["name"],
            "class": p["player_class"],
            "level": p["level"],
            "day": p["day"],
            "gold": p["gold"],
        }
    except (IOError, OSError, json.JSONDecodeError, KeyError):
        return None


def delete_save(slot):
    """Delete a save file."""
    path = get_save_path(slot)
    if os.path.exists(path):
        os.remove(path)


def list_saves():
    """Return info for all save slots."""
    saves = []
    for slot in range(1, SAVE_SLOTS + 1):
        info = get_save_info(slot)
        saves.append({"slot": slot, "info": info})
    return saves

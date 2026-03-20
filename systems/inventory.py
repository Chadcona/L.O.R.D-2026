# Items, weapons, armour, materials, and crafting definitions

# --- Material Tiers (progression order) ---
MATERIAL_TIERS = [
    {"name": "Wood",      "rank": 0, "atk_mult": 1.0, "def_mult": 1.0, "color": (140, 100, 50)},
    {"name": "Copper",    "rank": 1, "atk_mult": 1.4, "def_mult": 1.3, "color": (200, 130, 70)},
    {"name": "Iron",      "rank": 2, "atk_mult": 1.9, "def_mult": 1.7, "color": (160, 160, 170)},
    {"name": "Steel",     "rank": 3, "atk_mult": 2.5, "def_mult": 2.2, "color": (200, 200, 210)},
    {"name": "Enchanted", "rank": 4, "atk_mult": 3.2, "def_mult": 2.8, "color": (140, 100, 220)},
    {"name": "Dragon",    "rank": 5, "atk_mult": 4.0, "def_mult": 3.5, "color": (220, 60, 40)},
    {"name": "Void",      "rank": 6, "atk_mult": 5.0, "def_mult": 4.5, "color": (40, 0, 60)},
]

TIER_BY_NAME = {t["name"]: t for t in MATERIAL_TIERS}

# --- Base Weapon Types (stats at Wood tier) ---
BASE_WEAPONS = [
    {"type": "Sword",  "base_atk": 8,  "special": None},
    {"type": "Axe",    "base_atk": 10, "special": "bleed_5"},
    {"type": "Dagger", "base_atk": 6,  "special": "crit_10"},
    {"type": "Staff",  "base_atk": 5,  "special": "magic_10"},
    {"type": "Spear",  "base_atk": 7,  "special": "first_strike"},
]

# --- Base Armour Types (stats at Wood tier) ---
BASE_ARMOURS = [
    {"type": "Shield",   "base_def": 4,  "special": None},
    {"type": "Tunic",    "base_def": 3,  "special": None},
    {"type": "Mail",     "base_def": 6,  "special": None},
    {"type": "Plate",    "base_def": 8,  "special": None},
    {"type": "Robe",     "base_def": 3,  "special": "magic_res"},
]


def make_weapon(weapon_type, tier_name):
    """Create a weapon dict from a base type and material tier."""
    base = next((w for w in BASE_WEAPONS if w["type"] == weapon_type), BASE_WEAPONS[0])
    tier = TIER_BY_NAME.get(tier_name, MATERIAL_TIERS[0])
    atk = int(base["base_atk"] * tier["atk_mult"])
    name = f"{tier_name} {weapon_type}"
    special = base["special"]
    # Higher tiers unlock bonus specials
    if tier["rank"] >= 4 and special is None:
        special = "magic_10"
    if tier["rank"] >= 5:
        if "bleed" in (special or ""):
            special = "bleed_15"
        elif "crit" in (special or ""):
            special = "crit_20"
    return {"name": name, "atk": atk, "special": special, "tier": tier_name, "type": weapon_type}


def make_armour(armour_type, tier_name):
    """Create an armour dict from a base type and material tier."""
    base = next((a for a in BASE_ARMOURS if a["type"] == armour_type), BASE_ARMOURS[0])
    tier = TIER_BY_NAME.get(tier_name, MATERIAL_TIERS[0])
    dfn = int(base["base_def"] * tier["def_mult"])
    name = f"{tier_name} {armour_type}"
    special = base["special"]
    if tier["rank"] >= 5:
        special = special or "fire_res"
    if tier["rank"] >= 6:
        special = "all_res"
    return {"name": name, "def": dfn, "special": special, "tier": tier_name, "type": armour_type}


# --- Crafting Materials (dropped by enemies, found in forest) ---
MATERIALS = {
    "Wood Scrap":       {"tier": "Wood",      "type": "material", "value": 5},
    "Copper Ore":       {"tier": "Copper",     "type": "material", "value": 15},
    "Iron Ore":         {"tier": "Iron",       "type": "material", "value": 30},
    "Steel Ingot":      {"tier": "Steel",      "type": "material", "value": 60},
    "Enchanted Shard":  {"tier": "Enchanted",  "type": "material", "value": 120},
    "Dragon Scale":     {"tier": "Dragon",     "type": "material", "value": 250},
    "Void Essence":     {"tier": "Void",       "type": "material", "value": 500},
    "Magic Dust":       {"tier": "Enchanted",  "type": "catalyst", "value": 80},
    "Dragon Bone":      {"tier": "Dragon",     "type": "catalyst", "value": 200},
}

# --- Crafting Recipes ---
# Each recipe: material_name x count + gold cost -> result
CRAFT_RECIPES = [
    # Wood -> Copper upgrades
    {"material": "Copper Ore",      "count": 3, "gold": 50,   "result_tier": "Copper"},
    # Copper -> Iron
    {"material": "Iron Ore",        "count": 3, "gold": 150,  "result_tier": "Iron"},
    # Iron -> Steel
    {"material": "Steel Ingot",     "count": 3, "gold": 400,  "result_tier": "Steel"},
    # Steel -> Enchanted (needs catalyst)
    {"material": "Enchanted Shard", "count": 3, "gold": 1000, "result_tier": "Enchanted",
     "catalyst": "Magic Dust", "catalyst_count": 1},
    # Enchanted -> Dragon
    {"material": "Dragon Scale",    "count": 3, "gold": 3000, "result_tier": "Dragon",
     "catalyst": "Dragon Bone", "catalyst_count": 1},
    # Dragon -> Void
    {"material": "Void Essence",    "count": 3, "gold": 8000, "result_tier": "Void"},
]


def get_upgrade_recipe(current_tier):
    """Get the recipe to upgrade from current_tier to the next tier."""
    tier_obj = TIER_BY_NAME.get(current_tier)
    if tier_obj is None:
        return None
    next_rank = tier_obj["rank"] + 1
    next_tier = next((t for t in MATERIAL_TIERS if t["rank"] == next_rank), None)
    if next_tier is None:
        return None
    return next((r for r in CRAFT_RECIPES if r["result_tier"] == next_tier["name"]), None)


def can_craft_upgrade(player, equipment_piece):
    """Check if player has materials and gold to upgrade an equipment piece."""
    current_tier = equipment_piece.get("tier", "Wood")
    recipe = get_upgrade_recipe(current_tier)
    if recipe is None:
        return False, "Already at max tier."

    # Check gold
    if player.gold < recipe["gold"]:
        return False, f"Need {recipe['gold']} gold (have {player.gold})."

    # Check material
    mat_name = recipe["material"]
    mat_count = recipe["count"]
    have = _count_item(player, mat_name)
    if have < mat_count:
        return False, f"Need {mat_count}x {mat_name} (have {have})."

    # Check catalyst if needed
    if "catalyst" in recipe:
        cat_name = recipe["catalyst"]
        cat_count = recipe["catalyst_count"]
        have_cat = _count_item(player, cat_name)
        if have_cat < cat_count:
            return False, f"Need {cat_count}x {cat_name} (have {have_cat})."

    return True, "Ready to craft."


def perform_upgrade(player, equipment_piece):
    """Upgrade an equipment piece to the next tier. Returns new equipment dict or None."""
    can, msg = can_craft_upgrade(player, equipment_piece)
    if not can:
        return None, msg

    current_tier = equipment_piece.get("tier", "Wood")
    recipe = get_upgrade_recipe(current_tier)
    eq_type = equipment_piece.get("type", "Sword")

    # Consume resources
    player.gold -= recipe["gold"]
    _remove_items(player, recipe["material"], recipe["count"])
    if "catalyst" in recipe:
        _remove_items(player, recipe["catalyst"], recipe["catalyst_count"])

    # Create upgraded equipment
    new_tier = recipe["result_tier"]
    if "atk" in equipment_piece:
        new_eq = make_weapon(eq_type, new_tier)
    else:
        new_eq = make_armour(eq_type, new_tier)

    return new_eq, f"Forged {new_eq['name']}!"


def _count_item(player, item_name):
    """Count how many of an item the player has."""
    for item in player.inventory:
        if item["name"] == item_name:
            return item.get("count", 1)
    return 0


def _remove_items(player, item_name, count):
    """Remove count of an item from player inventory."""
    for _ in range(count):
        player.remove_item(item_name)


# --- Shop weapon/armour lists (pre-built for convenience) ---
WEAPONS = [
    make_weapon("Sword", "Wood"),
    make_weapon("Sword", "Copper"),
    make_weapon("Sword", "Iron"),
    make_weapon("Axe", "Iron"),
    make_weapon("Sword", "Steel"),
    make_weapon("Dagger", "Steel"),
    make_weapon("Sword", "Enchanted"),
    make_weapon("Staff", "Enchanted"),
]

# Add costs for shop items
for i, w in enumerate(WEAPONS):
    tier = TIER_BY_NAME[w["tier"]]
    w["cost"] = int(50 * (tier["rank"] + 1) ** 2 * (1 + i * 0.3))

ARMOURS = [
    make_armour("Tunic", "Wood"),
    make_armour("Shield", "Copper"),
    make_armour("Mail", "Iron"),
    make_armour("Plate", "Iron"),
    make_armour("Robe", "Enchanted"),
    make_armour("Plate", "Steel"),
    make_armour("Plate", "Dragon"),
    make_armour("Plate", "Void"),
]

for i, a in enumerate(ARMOURS):
    tier = TIER_BY_NAME[a["tier"]]
    a["cost"] = int(40 * (tier["rank"] + 1) ** 2 * (1 + i * 0.3))

CONSUMABLES = [
    {"name": "Potion", "cost": 50, "type": "consumable", "effect": "heal", "value": 50},
    {"name": "Hi-Potion", "cost": 150, "type": "consumable", "effect": "heal", "value": 150},
    {"name": "Elixir", "cost": 500, "type": "consumable", "effect": "elixir", "value": 50},
    {"name": "Antidote", "cost": 30, "type": "consumable", "effect": "cure_poison", "value": 0},
    {"name": "Smelling Salts", "cost": 80, "type": "consumable", "effect": "cure_sleep", "value": 0},
    {"name": "Dragon Ale", "cost": 200, "type": "consumable", "effect": "str_boost", "value": 5},
]

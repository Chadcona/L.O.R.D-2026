# Enemy definitions and AI behaviours

import random


# Loot drop format: list of (item_name, drop_chance 0.0-1.0)
ENEMIES = {
    # Shallow Forest (Level 1-4)
    "Forest Slime": {
        "hp": 25, "atk": 5, "def": 2, "agi": 3,
        "exp": 15, "gold": (5, 15), "zone": "shallow",
        "behaviour": "aggressive",
        "special": "split",
        "sprite_color": (60, 200, 60),
        "loot": [("Wood Scrap", 0.6), ("Copper Ore", 0.1)],
    },
    "Giant Rat": {
        "hp": 30, "atk": 7, "def": 3, "agi": 6,
        "exp": 18, "gold": (8, 20), "zone": "shallow",
        "behaviour": "aggressive",
        "special": "bleed_crit",
        "sprite_color": (140, 100, 80),
        "loot": [("Wood Scrap", 0.5), ("Copper Ore", 0.15)],
    },
    "Goblin Scout": {
        "hp": 40, "atk": 9, "def": 5, "agi": 7,
        "exp": 25, "gold": (12, 30), "zone": "shallow",
        "behaviour": "tactical",
        "special": None,
        "sprite_color": (100, 160, 60),
        "loot": [("Copper Ore", 0.4), ("Wood Scrap", 0.3)],
    },
    "Troll Whelp": {
        "hp": 60, "atk": 12, "def": 8, "agi": 3,
        "exp": 35, "gold": (15, 40), "zone": "shallow",
        "behaviour": "aggressive",
        "special": "regenerate",
        "sprite_color": (80, 120, 60),
        "loot": [("Copper Ore", 0.5), ("Iron Ore", 0.1)],
    },
    # Deep Forest (Level 5-8)
    "Dark Elf": {
        "hp": 90, "atk": 20, "def": 12, "agi": 14,
        "exp": 60, "gold": (30, 80), "zone": "deep",
        "behaviour": "tactical",
        "special": "sleep_spell",
        "sprite_color": (80, 60, 120),
        "loot": [("Iron Ore", 0.4), ("Magic Dust", 0.2), ("Enchanted Shard", 0.05)],
    },
    "Stone Golem": {
        "hp": 150, "atk": 18, "def": 25, "agi": 2,
        "exp": 75, "gold": (40, 100), "zone": "deep",
        "behaviour": "aggressive",
        "special": "high_def",
        "sprite_color": (160, 160, 160),
        "loot": [("Iron Ore", 0.6), ("Steel Ingot", 0.2)],
    },
    "Werewolf": {
        "hp": 110, "atk": 28, "def": 10, "agi": 12,
        "exp": 70, "gold": (35, 90), "zone": "deep",
        "behaviour": "aggressive",
        "special": "double_attack",
        "sprite_color": (100, 80, 60),
        "loot": [("Iron Ore", 0.4), ("Steel Ingot", 0.15)],
    },
    "Ogre Captain": {
        "hp": 130, "atk": 24, "def": 15, "agi": 5,
        "exp": 80, "gold": (50, 120), "zone": "deep",
        "behaviour": "aggressive",
        "special": None,
        "sprite_color": (120, 100, 70),
        "loot": [("Steel Ingot", 0.35), ("Iron Ore", 0.3), ("Copper Ore", 0.2)],
    },
    # Shadow Depths (Level 9-11)
    "Bone Dragon Whelp": {
        "hp": 200, "atk": 35, "def": 20, "agi": 10,
        "exp": 150, "gold": (80, 200), "zone": "shadow",
        "behaviour": "aggressive",
        "special": "fire_breath",
        "sprite_color": (200, 200, 180),
        "loot": [("Dragon Scale", 0.3), ("Dragon Bone", 0.15), ("Enchanted Shard", 0.2)],
    },
    "Chaos Knight": {
        "hp": 180, "atk": 40, "def": 30, "agi": 8,
        "exp": 160, "gold": (100, 250), "zone": "shadow",
        "behaviour": "tactical",
        "special": "berserk_low",
        "sprite_color": (60, 20, 20),
        "loot": [("Steel Ingot", 0.4), ("Enchanted Shard", 0.25), ("Void Essence", 0.05)],
    },
    "Death Specter": {
        "hp": 140, "atk": 35, "def": 15, "agi": 18,
        "exp": 140, "gold": (70, 180), "zone": "shadow",
        "behaviour": "tactical",
        "special": "drain",
        "sprite_color": (40, 40, 60),
        "loot": [("Enchanted Shard", 0.35), ("Magic Dust", 0.3), ("Void Essence", 0.08)],
    },
    "Shadow Demon": {
        "hp": 170, "atk": 38, "def": 22, "agi": 15,
        "exp": 170, "gold": (90, 230), "zone": "shadow",
        "behaviour": "aggressive",
        "special": None,
        "sprite_color": (30, 0, 50),
        "loot": [("Void Essence", 0.12), ("Dragon Scale", 0.2), ("Enchanted Shard", 0.3)],
    },
}


class Enemy:
    """An enemy instance in combat."""

    def __init__(self, name):
        data = ENEMIES[name]
        self.name = name
        self.max_hp = data["hp"]
        self.hp = self.max_hp
        self.atk = data["atk"]
        self.defense = data["def"]
        self.agi = data["agi"]
        self.exp_reward = data["exp"]
        self.gold_reward = random.randint(*data["gold"])
        self.behaviour = data["behaviour"]
        self.special = data["special"]
        self.sprite_color = data["sprite_color"]
        self.loot_table = data.get("loot", [])
        self.status_effects = []
        self.defending = False

    def roll_loot(self):
        """Roll for loot drops. Returns list of item name strings."""
        drops = []
        for item_name, chance in self.loot_table:
            if random.random() < chance:
                drops.append(item_name)
        return drops

    def is_alive(self):
        return self.hp > 0

    def take_damage(self, amount):
        actual = max(1, amount - (self.defense // 2 if not self.defending else self.defense))
        self.hp = max(0, self.hp - actual)
        self.defending = False
        return actual

    def choose_action(self):
        """AI decides what to do this turn."""
        hp_pct = self.hp / self.max_hp

        if self.behaviour == "aggressive":
            return "attack"

        elif self.behaviour == "tactical":
            if hp_pct < 0.3 and random.random() < 0.3:
                return "defend"
            if self.special == "sleep_spell" and random.random() < 0.25:
                return "special"
            if random.random() < 0.7:
                return "attack"
            return "defend"

        return "attack"

    def get_attack_damage(self):
        """Calculate attack damage with some variance."""
        base = self.atk
        variance = random.randint(-base // 5, base // 5)
        return max(1, base + variance)


def get_enemies_for_zone(zone):
    """Return list of enemy names for a given zone."""
    return [name for name, data in ENEMIES.items() if data["zone"] == zone]


def get_zone_for_level(level):
    """Determine which forest zone the player should encounter."""
    if level <= 4:
        return "shallow"
    elif level <= 8:
        return "deep"
    else:
        return "shadow"


def spawn_random_enemy(player_level):
    """Spawn a random enemy appropriate for the player's level."""
    zone = get_zone_for_level(player_level)
    candidates = get_enemies_for_zone(zone)
    # Small chance of getting an enemy from the next zone
    if zone == "shallow" and player_level >= 3:
        deep = get_enemies_for_zone("deep")
        if deep and random.random() < 0.1:
            candidates = deep
    elif zone == "deep" and player_level >= 7:
        shadow = get_enemies_for_zone("shadow")
        if shadow and random.random() < 0.1:
            candidates = shadow
    name = random.choice(candidates)
    return Enemy(name)

# Player character system — stats, leveling, classes

from settings import LEVEL_EXP, DEFAULT_FOREST_TURNS, MAX_LEVEL


# Starting class definitions
CLASSES = {
    "Warrior": {
        "description": "A mighty fighter with brute strength and iron defence.",
        "stat_bonus": {"str": 3, "def": 2, "agi": 0, "int": 0, "lck": 0},
        "special": "Berserk",
        "special_desc": "Double damage for one turn (once per battle)",
    },
    "Thief": {
        "description": "A cunning rogue with quick hands and sharper luck.",
        "stat_bonus": {"str": 0, "def": 0, "agi": 3, "int": 0, "lck": 2},
        "special": "Steal",
        "special_desc": "Attempt to steal gold or items from enemies",
    },
    "Mage": {
        "description": "A wielder of arcane power with devastating spells.",
        "stat_bonus": {"str": 0, "def": 0, "agi": 0, "int": 3, "lck": 0},
        "special": "Spellcast",
        "special_desc": "Cast powerful spells consuming MP",
        "mp_bonus": 2,
    },
}

# Base stats at level 1 (before class bonus)
BASE_STATS = {
    "hp": 50,
    "mp": 10,
    "str": 8,
    "def": 5,
    "agi": 5,
    "int": 5,
    "lck": 5,
}

# Stat growth per level
LEVEL_GROWTH = {
    "hp": 15,
    "mp": 5,
    "str": 2,
    "def": 2,
    "agi": 1,
    "int": 1,
    "lck": 1,
}


class Player:
    """The player character with all stats, inventory, and progression."""

    def __init__(self, name="Hero", player_class="Warrior"):
        self.name = name
        self.player_class = player_class

        # Base stats
        bonus = CLASSES[player_class]["stat_bonus"]
        self.max_hp = BASE_STATS["hp"]
        self.hp = self.max_hp
        mp_bonus = CLASSES[player_class].get("mp_bonus", 0)
        self.max_mp = BASE_STATS["mp"] + mp_bonus * 5
        self.mp = self.max_mp
        self.str = BASE_STATS["str"] + bonus.get("str", 0)
        self.defense = BASE_STATS["def"] + bonus.get("def", 0)
        self.agi = BASE_STATS["agi"] + bonus.get("agi", 0)
        self.int = BASE_STATS["int"] + bonus.get("int", 0)
        self.lck = BASE_STATS["lck"] + bonus.get("lck", 0)

        # Progression
        self.level = 1
        self.exp = 0
        self.gold = 100  # Starting gold

        # Daily system
        self.forest_turns = DEFAULT_FOREST_TURNS
        self.day = 1

        # Equipment (tier-based)
        from systems.inventory import make_weapon, make_armour
        self.weapon = make_weapon("Sword", "Wood")
        self.armour = make_armour("Tunic", "Wood")

        # Inventory (list of item dicts)
        self.inventory = [
            {"name": "Potion", "type": "consumable", "effect": "heal", "value": 50, "count": 3},
        ]

        # Reputation
        self.reputation = 50  # 0-100 scale

        # Combat state
        self.status_effects = []
        self.special_used = False  # For once-per-battle abilities

        # Flags
        self.dragon_kills = 0
        self.total_days = 0

    @property
    def atk(self):
        """Total attack power = STR + weapon ATK."""
        return self.str + self.weapon.get("atk", 0)

    @property
    def total_def(self):
        """Total defence = DEF + armour DEF."""
        return self.defense + self.armour.get("def", 0)

    def exp_to_next_level(self):
        """EXP needed for next level."""
        if self.level >= MAX_LEVEL:
            return 0
        return LEVEL_EXP[self.level + 1] - self.exp

    def exp_progress(self):
        """Return (current, needed) for progress bar."""
        if self.level >= MAX_LEVEL:
            return (1, 1)
        current_threshold = LEVEL_EXP[self.level]
        next_threshold = LEVEL_EXP[self.level + 1]
        return (self.exp - current_threshold, next_threshold - current_threshold)

    def gain_exp(self, amount):
        """Add EXP and handle level-ups. Returns list of level-up messages."""
        self.exp += amount
        messages = []
        while self.level < MAX_LEVEL and self.exp >= LEVEL_EXP[self.level + 1]:
            self.level += 1
            self._apply_level_up()
            messages.append(f"{self.name} reached Level {self.level}!")
        return messages

    def _apply_level_up(self):
        """Apply stat increases for a level-up."""
        bonus = CLASSES[self.player_class]["stat_bonus"]
        # HP/MP grow more
        self.max_hp += LEVEL_GROWTH["hp"] + (2 if bonus.get("def", 0) > 0 else 0)
        mp_extra = CLASSES[self.player_class].get("mp_bonus", 0)
        self.max_mp += LEVEL_GROWTH["mp"] + mp_extra * 2
        self.str += LEVEL_GROWTH["str"] + (1 if bonus.get("str", 0) > 0 else 0)
        self.defense += LEVEL_GROWTH["def"] + (1 if bonus.get("def", 0) > 0 else 0)
        self.agi += LEVEL_GROWTH["agi"] + (1 if bonus.get("agi", 0) > 0 else 0)
        self.int += LEVEL_GROWTH["int"] + (1 if bonus.get("int", 0) > 0 else 0)
        self.lck += LEVEL_GROWTH["lck"] + (1 if bonus.get("lck", 0) > 0 else 0)
        # Full restore on level-up
        self.hp = self.max_hp
        self.mp = self.max_mp

    def rest_at_inn(self):
        """Rest at the inn — restore HP, reset turns, advance day."""
        cost = self.inn_cost()
        if self.gold >= cost:
            self.gold -= cost
            self.hp = self.max_hp
            self.mp = self.max_mp
            self.forest_turns = DEFAULT_FOREST_TURNS
            self.day += 1
            self.total_days += 1
            self.special_used = False
            self.status_effects = []
            return True
        return False

    def inn_cost(self):
        """Inn cost scales with level."""
        from settings import INN_BASE_COST
        return INN_BASE_COST * self.level

    def is_alive(self):
        return self.hp > 0

    def heal(self, amount):
        self.hp = min(self.max_hp, self.hp + amount)

    def take_damage(self, amount):
        actual = max(0, amount - self.total_def // 3)
        self.hp = max(0, self.hp - actual)
        return actual

    def add_item(self, item):
        """Add item to inventory, stacking if possible."""
        for inv_item in self.inventory:
            if inv_item["name"] == item["name"]:
                inv_item["count"] = inv_item.get("count", 1) + item.get("count", 1)
                return
        self.inventory.append(dict(item))

    def remove_item(self, item_name):
        """Remove one of an item. Returns True if successful."""
        for i, item in enumerate(self.inventory):
            if item["name"] == item_name:
                item["count"] = item.get("count", 1) - 1
                if item["count"] <= 0:
                    self.inventory.pop(i)
                return True
        return False

    def to_dict(self):
        """Serialize player to dict for saving."""
        return {
            "name": self.name,
            "player_class": self.player_class,
            "level": self.level,
            "exp": self.exp,
            "gold": self.gold,
            "hp": self.hp,
            "max_hp": self.max_hp,
            "mp": self.mp,
            "max_mp": self.max_mp,
            "str": self.str,
            "def": self.defense,
            "agi": self.agi,
            "int": self.int,
            "lck": self.lck,
            "forest_turns": self.forest_turns,
            "day": self.day,
            "total_days": self.total_days,
            "weapon": self.weapon,
            "armour": self.armour,
            "inventory": self.inventory,
            "reputation": self.reputation,
            "dragon_kills": self.dragon_kills,
        }

    @classmethod
    def from_dict(cls, data):
        """Deserialize player from save dict."""
        p = cls(data["name"], data["player_class"])
        p.level = data["level"]
        p.exp = data["exp"]
        p.gold = data["gold"]
        p.hp = data["hp"]
        p.max_hp = data["max_hp"]
        p.mp = data["mp"]
        p.max_mp = data["max_mp"]
        p.str = data["str"]
        p.defense = data["def"]
        p.agi = data["agi"]
        p.int = data["int"]
        p.lck = data["lck"]
        p.forest_turns = data["forest_turns"]
        p.day = data["day"]
        p.total_days = data.get("total_days", 0)
        p.weapon = data["weapon"]
        p.armour = data["armour"]
        p.inventory = data["inventory"]
        p.reputation = data.get("reputation", 50)
        p.dragon_kills = data.get("dragon_kills", 0)
        return p

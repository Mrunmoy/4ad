"""Equipment system for Four Against Darkness.

Implements weapons, armor, items, and inventory management
per the rulebook specifications (pp.8-16).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Union


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

@dataclass
class Weapon:
    """A weapon that can be equipped by a character."""
    name: str
    cost: int
    hands: int  # 1 or 2
    attack_modifier: int
    damage_type: str  # "crushing" or "slashing" or "piercing"
    is_ranged: bool = False
    is_magic: bool = False

    def sell_price(self) -> int:
        if self.is_magic:
            return 50
        return self.cost // 2


@dataclass
class Armor:
    """Armor or shield worn by a character."""
    name: str
    cost: int
    defense_bonus: int
    is_heavy: bool = False
    save_penalty: int = 0  # -1 for heavy armor
    is_shield: bool = False

    def sell_price(self) -> int:
        return self.cost // 2


@dataclass
class Item:
    """Consumable or utility item."""
    name: str
    cost: int
    one_use: bool = True
    description: str = ""
    charges: int = 1
    is_magic: bool = False

    def sell_price(self) -> int:
        # Fool's Gold Purse is not magic but has a special sell price
        if self.name == "Fool's Gold Purse":
            return 20 if self.charges > 0 else 0
        if self.is_magic:
            # Magic item sell prices vary; handled per-item
            if self.name == "Wand of Sleep":
                return 30 * self.charges
            elif self.name == "Fireball Staff":
                return 30 * self.charges
            elif self.name == "Ring of Teleportation":
                return 40 if self.charges > 0 else 0
            elif self.name == "Potion of Healing":
                return 50
            return 0
        return self.cost // 2


# A single union type for anything that goes in inventory
EquipmentItem = Union[Weapon, Armor, Item]


# ---------------------------------------------------------------------------
# Weapon catalogue
# ---------------------------------------------------------------------------

WEAPON_LIST: Dict[str, Weapon] = {
    "hand_weapon": Weapon(
        name="Hand Weapon", cost=6, hands=1,
        attack_modifier=0, damage_type="slashing",
    ),
    "light_hand_weapon": Weapon(
        name="Light Hand Weapon", cost=5, hands=1,
        attack_modifier=-1, damage_type="slashing",
    ),
    "two_handed_weapon": Weapon(
        name="Two-Handed Weapon", cost=15, hands=2,
        attack_modifier=1, damage_type="slashing",
    ),
    "bow": Weapon(
        name="Bow", cost=15, hands=2,
        attack_modifier=0, damage_type="piercing",
        is_ranged=True,
    ),
    "sling": Weapon(
        name="Sling", cost=4, hands=1,
        attack_modifier=-1, damage_type="crushing",
        is_ranged=True,
    ),
}


# ---------------------------------------------------------------------------
# Armor catalogue
# ---------------------------------------------------------------------------

ARMOR_LIST: Dict[str, Armor] = {
    "light_armor": Armor(
        name="Light Armor", cost=10, defense_bonus=1,
    ),
    "heavy_armor": Armor(
        name="Heavy Armor", cost=30, defense_bonus=2,
        is_heavy=True, save_penalty=-1,
    ),
    "shield": Armor(
        name="Shield", cost=5, defense_bonus=1,
        is_shield=True,
    ),
}


# ---------------------------------------------------------------------------
# Item catalogue
# ---------------------------------------------------------------------------

ITEM_LIST: Dict[str, Item] = {
    "lantern": Item(
        name="Lantern", cost=4, one_use=False,
        description="Required (1 per party minimum). Uses 1 hand.",
    ),
    "rope": Item(
        name="Rope", cost=4, one_use=False,
        description="Needed for tying up monsters, trapdoors. +1 to pit trap saves.",
    ),
    "bandage": Item(
        name="Bandage", cost=5, one_use=True,
        description="Heals 1 life. One use. Can be used in or out of combat (uses character's action).",
    ),
    "torch": Item(
        name="Torch", cost=2, one_use=True,
        description="Backup light source. Burns for 6 rooms.",
    ),
    "potion_of_healing": Item(
        name="Potion of Healing", cost=100, one_use=True,
        description="Full heal. Any time. One-use.",
    ),
    "holy_water": Item(
        name="Holy Water Vial", cost=30, one_use=True,
        description="Auto d6 damage to undead. One-use.",
    ),
}


# ---------------------------------------------------------------------------
# Combined shop inventory (buy prices)
# ---------------------------------------------------------------------------

SHOP_INVENTORY: Dict[str, EquipmentItem] = {
    **{k: v for k, v in WEAPON_LIST.items()},
    **{k: v for k, v in ARMOR_LIST.items()},
    **{k: v for k, v in ITEM_LIST.items()},
}


# ---------------------------------------------------------------------------
# Equipment restrictions per class
# ---------------------------------------------------------------------------

# Weapons allowed per class (keys from WEAPON_LIST)
CLASS_WEAPON_RESTRICTIONS: Dict[str, List[str]] = {
    "Warrior": ["hand_weapon", "light_hand_weapon", "two_handed_weapon", "bow", "sling"],
    "Cleric": ["hand_weapon", "sling"],  # crushing only for hand weapon
    "Rogue": ["light_hand_weapon", "hand_weapon", "bow", "sling"],
    "Wizard": ["hand_weapon", "sling"],  # staff (hand weapon) and sling only
    "Barbarian": ["hand_weapon", "two_handed_weapon"],
    "Elf": ["hand_weapon", "light_hand_weapon", "bow", "sling"],
    "Dwarf": ["hand_weapon", "two_handed_weapon"],
    "Halfling": ["light_hand_weapon", "sling"],
}

# Armor allowed per class
CLASS_ARMOR_RESTRICTIONS: Dict[str, List[str]] = {
    "Warrior": ["light_armor", "heavy_armor", "shield"],
    "Cleric": ["light_armor", "heavy_armor", "shield"],
    "Rogue": ["light_armor", "shield"],
    "Wizard": [],  # no armor, no shield
    "Barbarian": ["light_armor", "shield"],
    "Elf": ["light_armor", "shield"],
    "Dwarf": ["light_armor", "heavy_armor", "shield"],
    "Halfling": ["light_armor", "shield"],
}

# Classes that cannot use magic items (except Potion of Healing)
NO_MAGIC_CLASSES = {"Barbarian"}

# Class restrictions for specific magic items.
# Maps magic item name -> set of class_types allowed to use the item.
MAGIC_ITEM_CLASS_RESTRICTIONS = {
    "Wand of Sleep": {"Wizard", "Elf"},
    "Fireball Staff": {"Wizard"},
    "Ring of Teleportation": {"Warrior", "Cleric", "Rogue", "Wizard", "Elf", "Dwarf", "Halfling"},
    "Potion of Healing": {"Warrior", "Cleric", "Rogue", "Wizard", "Barbarian", "Elf", "Dwarf", "Halfling"},
}


# ---------------------------------------------------------------------------
# Inventory class
# ---------------------------------------------------------------------------

# Limits
MAX_GOLD_DEFAULT = 200
MAX_GOLD_DWARF = 250
MAX_WEAPON_SLOTS = 3
MAX_SHIELDS = 2
MAX_ITEM_SLOTS = 6


@dataclass
class Inventory:
    """Character inventory with equipment rules enforcement.

    Tracks weapons, armor, shields, and items with carry limits.
    """
    weapons: List[Weapon] = field(default_factory=list)
    armor: Optional[Armor] = None  # worn armor (not shield)
    shields: List[Armor] = field(default_factory=list)
    items: List[Item] = field(default_factory=list)
    gold: int = 0
    max_gold: int = MAX_GOLD_DEFAULT
    class_type: str = "Warrior"  # needed for restriction checks

    # ---- helpers ----

    def _weapon_slots_used(self) -> int:
        """Count weapon slots used (2H = 2 slots)."""
        return sum(w.hands for w in self.weapons)

    # ---- public API ----

    def can_equip(self, item: EquipmentItem) -> bool:
        """Check if the item can be added respecting all rules."""
        if isinstance(item, Weapon):
            # Barbarians cannot use magic weapons
            if item.is_magic and self.class_type in NO_MAGIC_CLASSES:
                return False
            allowed = CLASS_WEAPON_RESTRICTIONS.get(self.class_type, [])
            # Check by matching weapon key
            weapon_key = self._weapon_key(item)
            if weapon_key is None:
                # Unknown weapon type: reject rather than silently bypass
                return False
            if weapon_key not in allowed:
                return False
            if self._weapon_slots_used() + item.hands > MAX_WEAPON_SLOTS:
                return False
            return True

        if isinstance(item, Armor):
            allowed = CLASS_ARMOR_RESTRICTIONS.get(self.class_type, [])
            armor_key = self._armor_key(item)
            if armor_key is None:
                # Unknown armor type: reject rather than silently bypass
                return False
            if armor_key not in allowed:
                return False
            if item.is_shield:
                if len(self.shields) >= MAX_SHIELDS:
                    return False
            else:
                # Only one armor set at a time
                if self.armor is not None:
                    return False
            return True

        if isinstance(item, Item):
            # Magic item check: barbarians blocked from all magic except Potion of Healing
            if item.is_magic and self.class_type in NO_MAGIC_CLASSES:
                if item.name != "Potion of Healing":
                    return False
            # Per-item class restrictions (e.g. Wand=wizards/elves, Fireball Staff=wizards only)
            if item.is_magic and item.name in MAGIC_ITEM_CLASS_RESTRICTIONS:
                if self.class_type not in MAGIC_ITEM_CLASS_RESTRICTIONS[item.name]:
                    return False
            if len(self.items) >= MAX_ITEM_SLOTS:
                return False
            return True

        return False

    def add_item(self, item: EquipmentItem) -> bool:
        """Add an item to inventory. Returns True on success."""
        if not self.can_equip(item):
            return False

        if isinstance(item, Weapon):
            self.weapons.append(item)
            return True
        if isinstance(item, Armor):
            if item.is_shield:
                self.shields.append(item)
            else:
                self.armor = item
            return True
        if isinstance(item, Item):
            self.items.append(item)
            return True
        return False

    def remove_item(self, item: EquipmentItem) -> bool:
        """Remove an item from inventory. Returns True on success."""
        if isinstance(item, Weapon):
            if item in self.weapons:
                self.weapons.remove(item)
                return True
        elif isinstance(item, Armor):
            if item.is_shield:
                if item in self.shields:
                    self.shields.remove(item)
                    return True
            else:
                if self.armor is item:
                    self.armor = None
                    return True
        elif isinstance(item, Item):
            if item in self.items:
                self.items.remove(item)
                return True
        return False

    def sell_item(self, item: EquipmentItem) -> int:
        """Remove item and return gold actually gained (capped by max_gold)."""
        if self.remove_item(item):
            price = item.sell_price()
            added = self.add_gold(price)
            return added
        return 0

    def add_gold(self, amount: int) -> int:
        """Add gold, capped at max. Returns amount actually added."""
        space = self.max_gold - self.gold
        added = min(amount, space)
        if added > 0:
            self.gold += added
        return added

    def spend_gold(self, amount: int) -> bool:
        """Spend gold if sufficient. Returns True on success."""
        if self.gold >= amount:
            self.gold -= amount
            return True
        return False

    def get_defense_bonus(self) -> int:
        """Total defense bonus from armor + shields (max 1 active shield)."""
        bonus = 0
        if self.armor:
            bonus += self.armor.defense_bonus
        if self.shields:
            bonus += self.shields[0].defense_bonus  # only first shield active
        return bonus

    def get_attack_modifier(self) -> int:
        """Attack modifier from best equipped weapon."""
        if not self.weapons:
            return 0
        # Return the best modifier among weapons
        return max(w.attack_modifier for w in self.weapons)

    def get_save_penalty(self) -> int:
        """Save penalty from heavy armor."""
        if self.armor and self.armor.is_heavy:
            return self.armor.save_penalty
        return 0

    def get_carry_weight(self) -> int:
        """Total number of items carried (for encumbrance)."""
        count = len(self.weapons) + len(self.shields) + len(self.items)
        if self.armor:
            count += 1
        return count

    def is_over_item_limit(self) -> bool:
        """Check if carrying excess items (over 6 item slots)."""
        return len(self.items) > MAX_ITEM_SLOTS

    def get_encumbrance_penalty(self) -> int:
        """Defense penalty from carrying too many items."""
        excess = len(self.items) - MAX_ITEM_SLOTS
        if excess > 0:
            return -excess
        return 0

    def has_lantern(self) -> bool:
        """Check if inventory has a lantern."""
        return any(it.name == "Lantern" for it in self.items)

    def has_rope(self) -> bool:
        """Check if inventory has rope."""
        return any(it.name == "Rope" for it in self.items)

    def to_dict(self) -> dict:
        """Serialize inventory to dict."""
        return {
            "weapons": [
                {"name": w.name, "cost": w.cost, "hands": w.hands,
                 "attack_modifier": w.attack_modifier,
                 "damage_type": w.damage_type,
                 "is_ranged": w.is_ranged, "is_magic": w.is_magic}
                for w in self.weapons
            ],
            "armor": {
                "name": self.armor.name, "cost": self.armor.cost,
                "defense_bonus": self.armor.defense_bonus,
                "is_heavy": self.armor.is_heavy,
            } if self.armor else None,
            "shields": [
                {"name": s.name, "defense_bonus": s.defense_bonus}
                for s in self.shields
            ],
            "items": [
                {"name": it.name, "cost": it.cost,
                 "one_use": it.one_use, "charges": it.charges,
                 "is_magic": it.is_magic}
                for it in self.items
            ],
            "gold": self.gold,
        }

    # ---- internal helpers ----

    @staticmethod
    def _weapon_key(weapon: Weapon) -> Optional[str]:
        """Map a Weapon instance back to its catalogue key."""
        for key, w in WEAPON_LIST.items():
            if w.name == weapon.name and not weapon.is_magic:
                return key
        # Magic weapons map to their base type name
        name_lower = weapon.name.lower()
        if "bow" in name_lower:
            return "bow"
        if "light" in name_lower:
            return "light_hand_weapon"
        if "two" in name_lower or "two-handed" in name_lower:
            return "two_handed_weapon"
        if "sling" in name_lower:
            return "sling"
        if "hand" in name_lower:
            return "hand_weapon"
        # Unknown weapon type
        return None

    @staticmethod
    def _armor_key(armor: Armor) -> Optional[str]:
        """Map an Armor instance back to its catalogue key."""
        for key, a in ARMOR_LIST.items():
            if a.name == armor.name:
                return key
        return None

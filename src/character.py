"""Character classes for 4AD."""
from typing import List, Optional
from dataclasses import dataclass, field

from src.equipment import (
    Inventory, Weapon, Armor, Item,
    WEAPON_LIST, ARMOR_LIST, ITEM_LIST,
    MAX_GOLD_DEFAULT, MAX_GOLD_DWARF,
)
from src.dice import roll_d6


def _copy_weapon(key: str) -> Weapon:
    """Create a copy of a weapon from the catalogue."""
    w = WEAPON_LIST[key]
    return Weapon(
        name=w.name, cost=w.cost, hands=w.hands,
        attack_modifier=w.attack_modifier, damage_type=w.damage_type,
        is_ranged=w.is_ranged, is_magic=w.is_magic,
    )


def _copy_armor(key: str) -> Armor:
    """Create a copy of an armor piece from the catalogue."""
    a = ARMOR_LIST[key]
    return Armor(
        name=a.name, cost=a.cost, defense_bonus=a.defense_bonus,
        is_heavy=a.is_heavy, save_penalty=a.save_penalty,
        is_shield=a.is_shield,
    )


def _copy_item(key: str) -> Item:
    """Create a copy of an item from the catalogue."""
    it = ITEM_LIST[key]
    return Item(
        name=it.name, cost=it.cost, one_use=it.one_use,
        description=it.description, charges=it.charges,
        is_magic=it.is_magic,
    )


@dataclass
class Character:
    """Base character class."""
    name: str
    level: int = 1
    class_type: str = "Character"

    # Base stats (overridden by subclasses)
    attack: int = 2
    defense: int = 3
    life: int = 3
    max_life: int = 3

    # Legacy equipment list (kept for backward compatibility)
    equipment: List[str] = field(default_factory=list)

    # New inventory system
    # TODO Phase 2: Wire inventory equipment bonuses (get_attack_modifier,
    # get_defense_bonus) into the combat system so that equipped weapons/armor
    # actually affect attack rolls and defense calculations.
    inventory: Optional[Inventory] = field(default=None, repr=False)
    gold: int = 0

    # Position in marching order (1-4)
    position: int = 1

    # Status effects
    cursed: bool = False
    poisoned: bool = False
    petrified: bool = False

    def __post_init__(self):
        if self.inventory is None:
            self.inventory = Inventory(
                class_type=self.class_type,
                max_gold=MAX_GOLD_DEFAULT,
            )

    def take_damage(self, amount: int) -> None:
        """Take damage."""
        self.life -= amount
        if self.life < 0:
            self.life = 0

    def heal(self, amount: int) -> None:
        """Heal damage."""
        self.life += amount
        if self.life > self.max_life:
            self.life = self.max_life

    def is_dead(self) -> bool:
        """Check if character is dead."""
        return self.life <= 0

    def can_use_heavy_armor(self) -> bool:
        """Can character use heavy armor."""
        return True

    def can_use_shield(self) -> bool:
        """Can character use shield."""
        return True

    def can_use_magic(self) -> bool:
        """Can character use magic items."""
        return True

    def can_cast(self, spell: str) -> bool:
        """Can character cast specific spell."""
        return False

    def get_save_bonus(self, vs: str) -> int:
        """Get save bonus vs specific threat."""
        return 0

    def get_disarm_bonus(self) -> int:
        """Get trap disarm bonus."""
        return 0

    def can_attack_in_melee(self) -> bool:
        """Can character attack in melee based on position."""
        return self.position <= 2

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "name": self.name,
            "level": self.level,
            "class_type": self.class_type,
            "attack": self.attack,
            "defense": self.defense,
            "life": self.life,
            "max_life": self.max_life,
            "position": self.position,
            "cursed": self.cursed,
            "poisoned": self.poisoned,
            "petrified": self.petrified,
            "equipment": self.equipment,
            "gold": self.inventory.gold if self.inventory else self.gold,
            "inventory": self.inventory.to_dict() if self.inventory else None,
        }


# ---------------------------------------------------------------------------
# Starting equipment helpers
# ---------------------------------------------------------------------------

def _equip_starting_gear(char: Character, weapons: list, armor_keys: list,
                         item_keys: list, gold_dice: int) -> None:
    """Equip a character with starting gear and roll starting gold."""
    for wk in weapons:
        char.inventory.add_item(_copy_weapon(wk))
    for ak in armor_keys:
        char.inventory.add_item(_copy_armor(ak))
    for ik in item_keys:
        char.inventory.add_item(_copy_item(ik))
    # Roll starting gold
    starting_gold = sum(roll_d6() for _ in range(gold_dice))
    char.inventory.add_gold(starting_gold)
    # Keep legacy equipment list in sync
    char.equipment = [w.name for w in char.inventory.weapons]
    if char.inventory.armor:
        char.equipment.append(char.inventory.armor.name)
    char.equipment += [s.name for s in char.inventory.shields]
    char.equipment += [it.name for it in char.inventory.items]


class Warrior(Character):
    """Warrior class - page 8."""
    def __init__(self, name: str, level: int = 1):
        super().__init__(
            name=name,
            level=level,
            class_type="Warrior",
            attack=4,
            defense=5,
            life=6,
            max_life=6
        )
        self.inventory.class_type = "Warrior"
        _equip_starting_gear(
            self,
            weapons=["hand_weapon"],
            armor_keys=["light_armor", "shield"],
            item_keys=["lantern"],
            gold_dice=2,  # 2d6 gold
        )


class Cleric(Character):
    """Cleric class - page 9."""
    def __init__(self, name: str, level: int = 1):
        super().__init__(
            name=name,
            level=level,
            class_type="Cleric",
            attack=3,
            defense=4,
            life=5,
            max_life=5
        )
        self.inventory.class_type = "Cleric"
        _equip_starting_gear(
            self,
            weapons=["hand_weapon"],
            armor_keys=["light_armor", "shield"],
            item_keys=[],
            gold_dice=2,  # 2d6 gold
        )

    def can_cast(self, spell: str) -> bool:
        """Cleric can cast Blessing."""
        return spell == "Blessing"

    def get_save_bonus(self, vs: str) -> int:
        """Cleric adds level vs undead and demons."""
        if vs in ("undead", "demon"):
            return self.level
        return 0


class Rogue(Character):
    """Rogue class - page 10."""
    def __init__(self, name: str, level: int = 1):
        super().__init__(
            name=name,
            level=level,
            class_type="Rogue",
            attack=3,
            defense=4,
            life=4,
            max_life=4
        )
        self.inventory.class_type = "Rogue"
        _equip_starting_gear(
            self,
            weapons=["light_hand_weapon"],
            armor_keys=["light_armor"],
            item_keys=["rope"],
            gold_dice=3,  # 3d6 gold
        )

    def get_disarm_bonus(self) -> int:
        """Rogue adds level to disarm traps."""
        return self.level


class Wizard(Character):
    """Wizard class - page 11."""
    def __init__(self, name: str, level: int = 1):
        super().__init__(
            name=name,
            level=level,
            class_type="Wizard",
            attack=2,
            defense=3,
            life=3,
            max_life=3
        )
        self.inventory.class_type = "Wizard"
        _equip_starting_gear(
            self,
            weapons=["hand_weapon"],  # staff (hand weapon, crushing type)
            armor_keys=[],
            item_keys=[],
            gold_dice=4,  # 4d6 gold
        )
        self.spells = ["Blessing", "Fireball", "Lightning Bolt", "Sleep", "Escape", "Protect"]

    def can_cast(self, spell: str) -> bool:
        """Wizard can cast all spells."""
        return spell in self.spells


class Barbarian(Character):
    """Barbarian class - page 12."""
    def __init__(self, name: str, level: int = 1):
        super().__init__(
            name=name,
            level=level,
            class_type="Barbarian",
            attack=5,
            defense=4,
            life=8,
            max_life=8
        )
        self.inventory.class_type = "Barbarian"
        _equip_starting_gear(
            self,
            weapons=["two_handed_weapon"],
            armor_keys=[],
            item_keys=[],
            gold_dice=1,  # 1d6 gold
        )

    def can_use_heavy_armor(self) -> bool:
        """Barbarian cannot use best armor."""
        return False

    def can_use_magic(self) -> bool:
        """Barbarian cannot use magic items."""
        return False


class Elf(Character):
    """Elf class - page 13."""
    def __init__(self, name: str, level: int = 1):
        super().__init__(
            name=name,
            level=level,
            class_type="Elf",
            attack=3,
            defense=4,
            life=4,
            max_life=4
        )
        self.inventory.class_type = "Elf"
        _equip_starting_gear(
            self,
            weapons=["hand_weapon", "bow"],
            armor_keys=["light_armor"],
            item_keys=[],
            gold_dice=3,  # 3d6 gold
        )
        self.spells = ["Fireball", "Lightning Bolt", "Sleep", "Escape", "Protect"]

    def can_cast(self, spell: str) -> bool:
        """Elf can cast non-cleric spells."""
        return spell in self.spells


class Dwarf(Character):
    """Dwarf class - page 14."""
    def __init__(self, name: str, level: int = 1):
        super().__init__(
            name=name,
            level=level,
            class_type="Dwarf",
            attack=4,
            defense=5,
            life=7,
            max_life=7
        )
        self.inventory.class_type = "Dwarf"
        self.inventory.max_gold = MAX_GOLD_DWARF
        _equip_starting_gear(
            self,
            weapons=["hand_weapon"],
            armor_keys=["light_armor", "shield"],
            item_keys=[],
            gold_dice=2,  # 2d6 gold
        )


class Halfling(Character):
    """Halfling class - page 15."""
    def __init__(self, name: str, level: int = 1):
        super().__init__(
            name=name,
            level=level,
            class_type="Halfling",
            attack=2,
            defense=5,
            life=4,
            max_life=4
        )
        self.inventory.class_type = "Halfling"
        _equip_starting_gear(
            self,
            weapons=["light_hand_weapon", "sling"],
            armor_keys=["light_armor"],
            item_keys=[],
            gold_dice=3,  # 3d6 gold
        )
        self.luck_used = False

    def can_use_luck(self) -> bool:
        """Halfling can reroll once per encounter."""
        return not self.luck_used

    def use_luck(self) -> None:
        """Use luck for this encounter."""
        self.luck_used = True

    def reset_luck(self) -> None:
        """Reset luck at end of encounter."""
        self.luck_used = False


# Character creation helper
CHARACTER_CLASSES = {
    "Warrior": Warrior,
    "Cleric": Cleric,
    "Rogue": Rogue,
    "Wizard": Wizard,
    "Barbarian": Barbarian,
    "Elf": Elf,
    "Dwarf": Dwarf,
    "Halfling": Halfling,
}


def create_character(class_name: str, name: str, level: int = 1) -> Character:
    """Create a character of the specified class."""
    if not isinstance(class_name, str):
        raise ValueError(f"Unknown character class: {class_name}")
    normalized = class_name.title()
    if normalized in CHARACTER_CLASSES:
        return CHARACTER_CLASSES[normalized](name, level)
    raise ValueError(f"Unknown character class: {class_name}")

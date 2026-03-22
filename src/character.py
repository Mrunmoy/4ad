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
    limping: bool = False
    blessed_temple_bonus: bool = False  # +1 vs undead/demons, consumed on kill
    separated: bool = False  # Trapdoor: separated from party

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

    def attack_bonus(self, **kwargs) -> int:
        """Get attack bonus. Override in subclasses.

        TODO: Wire into Combat.resolve_attack() when combat is refactored
        to use class-specific bonuses (e.g. Warrior +level, Rogue conditional).
        """
        return 0

    def defense_bonus(self, **kwargs) -> int:
        """Get defense bonus. Override in subclasses.

        TODO: Wire into Combat.resolve_defense() when combat is refactored
        to use class-specific bonuses (e.g. Rogue +level, Dwarf vs large).
        """
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
            "limping": self.limping,
            "blessed_temple_bonus": self.blessed_temple_bonus,
            "separated": self.separated,
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
    """Warrior class - page 8.

    - +level to all attack rolls (melee and ranged)
    - Any weapon, any armor, shield
    - Life: 6 + level
    """
    def __init__(self, name: str, level: int = 1):
        super().__init__(
            name=name,
            level=level,
            class_type="Warrior",
            attack=4,
            defense=5,
            life=6 + level,
            max_life=6 + level,
        )
        self.inventory.class_type = "Warrior"
        _equip_starting_gear(
            self,
            weapons=["hand_weapon"],
            armor_keys=["light_armor", "shield"],
            item_keys=["lantern"],
            gold_dice=2,  # 2d6 gold
        )

    def attack_bonus(self, **kwargs) -> int:
        """Warrior adds level to all attack rolls."""
        return self.level


class Cleric(Character):
    """Cleric class - page 9.

    - Attack: +floor(level/2) general, +level vs undead/demons
    - Healing: 3x per adventure, d6 + level HP
    - Blessing: 3x per adventure
    - +level to saves vs undead/demons
    - Life: 5 + level
    """
    def __init__(self, name: str, level: int = 1):
        super().__init__(
            name=name,
            level=level,
            class_type="Cleric",
            attack=3,
            defense=4,
            life=5 + level,
            max_life=5 + level,
        )
        self.inventory.class_type = "Cleric"
        _equip_starting_gear(
            self,
            weapons=["hand_weapon"],
            armor_keys=["light_armor", "shield"],
            item_keys=[],
            gold_dice=2,  # 2d6 gold
        )
        self.healing_uses = 3
        self.blessing_uses = 3

    def attack_bonus(self, target=None, **kwargs) -> int:
        """Cleric: floor(level/2), full level vs undead/demons."""
        if target and (
            getattr(target, "is_undead", False) or getattr(target, "is_demon", False)
        ):
            return self.level
        return self.level // 2

    def can_cast(self, spell: str) -> bool:
        """Cleric can cast Blessing if uses remain."""
        return spell == "Blessing" and self.blessing_uses > 0

    def get_save_bonus(self, vs: str) -> int:
        """Cleric adds level vs undead and demons."""
        if vs in ("undead", "demon"):
            return self.level
        return 0

    def use_healing(self, target_character) -> int:
        """Use healing power on a character.

        Returns HP healed, or 0 if no uses remaining.
        """
        if self.healing_uses <= 0:
            return 0
        self.healing_uses -= 1
        from src.dice import roll_d6
        healed = roll_d6() + self.level
        target_character.heal(healed)
        return healed

    def use_blessing(self) -> bool:
        """Use a Blessing charge.

        Returns True if a charge was available and used.
        """
        if self.blessing_uses <= 0:
            return False
        self.blessing_uses -= 1
        return True

    def to_dict(self) -> dict:
        d = super().to_dict()
        d["healing_uses"] = self.healing_uses
        d["blessing_uses"] = self.blessing_uses
        return d


class Rogue(Character):
    """Rogue class - page 10.

    - +level attack ONLY when party outnumbers enemies
    - +level defense rolls
    - +level trap disarm
    - Light weapons, light armor only
    - Has lock picks
    - Life: 4 + level
    """
    def __init__(self, name: str, level: int = 1):
        super().__init__(
            name=name,
            level=level,
            class_type="Rogue",
            attack=3,
            defense=4,
            life=4 + level,
            max_life=4 + level,
        )
        self.inventory.class_type = "Rogue"
        _equip_starting_gear(
            self,
            weapons=["light_hand_weapon"],
            armor_keys=["light_armor"],
            item_keys=["rope"],
            gold_dice=3,  # 3d6 gold
        )
        self.has_lockpicks = True

    def attack_bonus(self, party_size: int = 0, enemy_count: int = 0, **kwargs) -> int:
        """Rogue: +level only when party outnumbers enemies."""
        if party_size > enemy_count > 0:
            return self.level
        return 0

    def defense_bonus(self, **kwargs) -> int:
        """Rogue: +level to all defense rolls."""
        return self.level

    def get_disarm_bonus(self) -> int:
        """Rogue adds level to disarm traps."""
        return self.level

    def get_lockpick_bonus(self) -> int:
        """Rogue adds level to open locked doors."""
        return self.level

    def can_use_heavy_armor(self) -> bool:
        """Rogue cannot use heavy armor."""
        return False

    def to_dict(self) -> dict:
        d = super().to_dict()
        d["has_lockpicks"] = self.has_lockpicks
        return d


class Wizard(Character):
    """Wizard class - page 11.

    - +level to spell attack rolls and puzzle solving
    - NO armor, light weapons only (staff, sling)
    - Spell slots: 2 + level
    - Knows all 6 spells
    - Life: 3 + level
    """
    def __init__(self, name: str, level: int = 1):
        super().__init__(
            name=name,
            level=level,
            class_type="Wizard",
            attack=2,
            defense=3,
            life=3 + level,
            max_life=3 + level,
        )
        self.inventory.class_type = "Wizard"
        _equip_starting_gear(
            self,
            weapons=["hand_weapon"],  # staff (hand weapon, crushing type)
            armor_keys=[],
            item_keys=[],
            gold_dice=4,  # 4d6 gold
        )
        self.spells = [
            "Blessing", "Fireball", "Lightning Bolt", "Sleep", "Escape", "Protect"
        ]
        self.spell_slots = 2 + level
        self.spells_used = 0

    def attack_bonus(self, **kwargs) -> int:
        """Wizard: no attack bonus for melee/ranged."""
        return 0

    def spell_attack_bonus(self) -> int:
        """Wizard: +level to spell attack rolls."""
        return self.level

    def can_cast(self, spell: str) -> bool:
        """Wizard can cast all 6 spells if slots remain."""
        return spell in self.spells and self.spells_used < self.spell_slots

    def cast_spell(self, spell: str) -> bool:
        """Consume a spell slot. Returns True if successful."""
        if not self.can_cast(spell):
            return False
        self.spells_used += 1
        return True

    def can_use_heavy_armor(self) -> bool:
        return False

    def can_use_shield(self) -> bool:
        return False

    def to_dict(self) -> dict:
        d = super().to_dict()
        d["spell_slots"] = self.spell_slots
        d["spells_used"] = self.spells_used
        d["spells"] = self.spells
        return d


class Barbarian(Character):
    """Barbarian class - page 12.

    - +level to melee attack
    - Rage: once per game, roll 3d6 pick best for attack
    - Cannot use magic items, scrolls, potions
    - Can accept cleric healing (divine)
    - Cannot read (no scrolls, no books)
    - Any weapon, shield + light armor only (no heavy)
    - Life: 8 + level
    """
    def __init__(self, name: str, level: int = 1):
        super().__init__(
            name=name,
            level=level,
            class_type="Barbarian",
            attack=5,
            defense=4,
            life=8 + level,
            max_life=8 + level,
        )
        self.inventory.class_type = "Barbarian"
        _equip_starting_gear(
            self,
            weapons=["two_handed_weapon"],
            armor_keys=[],
            item_keys=[],
            gold_dice=1,  # 1d6 gold
        )
        self.rage_available = True

    def attack_bonus(self, **kwargs) -> int:
        """Barbarian: +level to melee attack rolls."""
        return self.level

    def use_rage(self) -> bool:
        """Use rage ability. Returns True if rage was available.

        Caller should roll 3d6 and pick the best result for the attack.
        If the attack hits a boss, deal 2 wounds.
        """
        if not self.rage_available:
            return False
        self.rage_available = False
        return True

    def can_use_heavy_armor(self) -> bool:
        """Barbarian cannot use heavy armor."""
        return False

    def can_use_magic(self) -> bool:
        """Barbarian cannot use magic items."""
        return False

    def to_dict(self) -> dict:
        d = super().to_dict()
        d["rage_available"] = self.rage_available
        return d

    @classmethod
    def from_dict(cls, data: dict) -> "Barbarian":
        """Restore a Barbarian from serialized dict (campaign persistence).

        C2: rage_available must survive serialization so that once rage is
        used in a campaign, it stays used across dungeons.
        """
        barb = cls(name=data["name"], level=data.get("level", 1))
        barb.life = data.get("life", barb.life)
        barb.max_life = data.get("max_life", barb.max_life)
        barb.rage_available = data.get("rage_available", True)
        barb.cursed = data.get("cursed", False)
        barb.poisoned = data.get("poisoned", False)
        barb.petrified = data.get("petrified", False)
        barb.equipment = data.get("equipment", [])
        barb.position = data.get("position", 1)
        return barb


class Elf(Character):
    """Elf class - page 13.

    - +level to attack (not 2H weapons)
    - +1 vs orcs
    - +level to spell casting rolls
    - 1 spell/level, non-cleric spells (no Blessing)
    - Can only cast in light armor, no shield in hand
    - Life: 4 + level
    """
    def __init__(self, name: str, level: int = 1):
        super().__init__(
            name=name,
            level=level,
            class_type="Elf",
            attack=3,
            defense=4,
            life=4 + level,
            max_life=4 + level,
        )
        self.inventory.class_type = "Elf"
        _equip_starting_gear(
            self,
            weapons=["hand_weapon", "bow"],
            armor_keys=["light_armor"],
            item_keys=[],
            gold_dice=3,  # 3d6 gold
        )
        self.spells = [
            "Fireball", "Lightning Bolt", "Sleep", "Escape", "Protect"
        ]
        self.spell_slots = level  # 1 per level
        self.spells_used = 0

    def attack_bonus(self, target=None, two_handed: bool = False, **kwargs) -> int:
        """Elf: +level (not with 2H). +1 vs orcs."""
        if two_handed:
            bonus = 0
        else:
            bonus = self.level

        # +1 vs orcs
        if target and "orc" in getattr(target, "name", "").lower():
            bonus += 1

        return bonus

    def spell_attack_bonus(self) -> int:
        """Elf: +level to spell attack rolls."""
        return self.level

    def can_cast(self, spell: str) -> bool:
        """Elf can cast non-cleric spells if slots remain."""
        return spell in self.spells and self.spells_used < self.spell_slots

    def cast_spell(self, spell: str) -> bool:
        """Consume a spell slot. Returns True if successful."""
        if not self.can_cast(spell):
            return False
        self.spells_used += 1
        return True

    def can_use_heavy_armor(self) -> bool:
        """Elf cannot use heavy armor."""
        return False

    def to_dict(self) -> dict:
        d = super().to_dict()
        d["spell_slots"] = self.spell_slots
        d["spells_used"] = self.spells_used
        d["spells"] = self.spells
        return d


class Dwarf(Character):
    """Dwarf class - page 14.

    - +level to melee attack (not ranged)
    - +1 defense vs trolls, ogres, giants
    - +1 attack vs goblins
    - Smell gold: d6 + level, if 6+ detect treasure before fight
    - Gems/jewelry sell for 20% more with dwarf in party
    - Party with 2+ dwarves cannot bribe
    - Life: 7 + level
    """
    def __init__(self, name: str, level: int = 1):
        super().__init__(
            name=name,
            level=level,
            class_type="Dwarf",
            attack=4,
            defense=5,
            life=7 + level,
            max_life=7 + level,
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

    def attack_bonus(self, target=None, ranged: bool = False, **kwargs) -> int:
        """Dwarf: +level melee, +0 ranged, +1 vs goblins."""
        if ranged:
            return 0
        bonus = self.level
        if target and "goblin" in getattr(target, "name", "").lower():
            bonus += 1
        return bonus

    def defense_bonus(self, attacker=None, **kwargs) -> int:
        """Dwarf: +1 defense vs trolls, ogres, giants."""
        if attacker:
            name = getattr(attacker, "name", "").lower()
            if any(t in name for t in ("troll", "ogre", "giant")):
                return 1
        return 0

    def smell_gold(self, force_roll: int = None) -> bool:
        """Roll to detect treasure before fighting.

        d6 + level >= 6 means success.
        """
        from src.dice import roll_d6
        roll = force_roll if force_roll is not None else roll_d6()
        return (roll + self.level) >= 6


class Halfling(Character):
    """Halfling class - page 15.

    - +level defense vs giants, trolls, ogres
    - Luck points: level + 1 per adventure
    - Spend luck to: flee without defense roll, reroll any roll
    - Luck resets after each adventure
    - Cannot reroll XP rolls
    - +level to poison saves
    - Life: 4 + level
    """
    def __init__(self, name: str, level: int = 1):
        super().__init__(
            name=name,
            level=level,
            class_type="Halfling",
            attack=2,
            defense=5,
            life=4 + level,
            max_life=4 + level,
        )
        self.inventory.class_type = "Halfling"
        _equip_starting_gear(
            self,
            weapons=["light_hand_weapon", "sling"],
            armor_keys=["light_armor"],
            item_keys=[],
            gold_dice=3,  # 3d6 gold
        )
        self.luck_points = level + 1
        self.max_luck_points = level + 1

    def attack_bonus(self, **kwargs) -> int:
        """Halfling: no attack level bonus."""
        return 0

    def defense_bonus(self, attacker=None, **kwargs) -> int:
        """Halfling: +level vs giants, trolls, ogres."""
        if attacker:
            name = getattr(attacker, "name", "").lower()
            if any(t in name for t in ("troll", "ogre", "giant")):
                return self.level
        return 0

    def can_use_luck(self) -> bool:
        """Check if halfling has luck points remaining."""
        return self.luck_points > 0

    def use_luck(self) -> bool:
        """Spend one luck point. Returns True if a point was available."""
        if self.luck_points <= 0:
            return False
        self.luck_points -= 1
        return True

    def reset_luck(self) -> None:
        """Reset luck points for a new adventure."""
        self.luck_points = self.max_luck_points

    def get_save_bonus(self, vs: str) -> int:
        """Halfling: +level to poison saves."""
        if vs == "poison":
            return self.level
        return 0

    def can_use_heavy_armor(self) -> bool:
        """Halfling cannot use heavy armor."""
        return False

    def to_dict(self) -> dict:
        d = super().to_dict()
        d["luck_points"] = self.luck_points
        d["max_luck_points"] = self.max_luck_points
        return d


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

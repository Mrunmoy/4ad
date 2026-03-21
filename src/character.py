"""Character classes for 4AD."""
from typing import List, Optional
from dataclasses import dataclass, field


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

    # Equipment
    equipment: List[str] = field(default_factory=list)

    # Position in marching order (1-4)
    position: int = 1

    # Status effects
    cursed: bool = False
    poisoned: bool = False
    petrified: bool = False
    protected: bool = False  # Protect spell: +1 defense for current combat

    # Spell system
    spells_known: List[str] = field(default_factory=list)
    spells_remaining: int = 0
    healing_remaining: int = 0  # For clerics (3 per adventure)
    
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

    def use_spell(self, spell_name: str = None) -> bool:
        """
        Attempt to use a spell slot. Returns True if successful.
        Override in subclasses for class-specific behaviour.
        """
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
            "protected": self.protected,
            "equipment": self.equipment,
            "spells_known": self.spells_known,
            "spells_remaining": self.spells_remaining,
            "healing_remaining": self.healing_remaining,
        }


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
        self.spells_known = ["Blessing"]
        self.spells_remaining = 3  # 3 Blessing uses per adventure
        self.healing_remaining = 3  # 3 Healing uses per adventure

    def can_cast(self, spell: str) -> bool:
        """Cleric can cast Blessing (with remaining charges)."""
        return spell == "Blessing" and self.spells_remaining > 0

    def use_spell(self, spell_name: str = None) -> bool:
        """Use a Blessing charge."""
        if spell_name == "Blessing" and self.spells_remaining > 0:
            self.spells_remaining -= 1
            return True
        return False

    def use_healing(self) -> bool:
        """Use a healing charge. Returns True if successful."""
        if self.healing_remaining > 0:
            self.healing_remaining -= 1
            return True
        return False

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
        self.spells_known = ["Blessing", "Fireball", "Lightning Bolt", "Sleep", "Escape", "Protect"]
        self.spells_remaining = 2 + level  # 3 at level 1

    def can_cast(self, spell: str) -> bool:
        """Wizard can cast all spells if slots remain."""
        return spell in self.spells_known and self.spells_remaining > 0

    def use_spell(self, spell_name: str = None) -> bool:
        """Use a spell slot."""
        if spell_name in self.spells_known and self.spells_remaining > 0:
            self.spells_remaining -= 1
            return True
        return False


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
        self.spells_known = ["Fireball", "Lightning Bolt", "Sleep", "Escape", "Protect"]
        self.spells_remaining = level  # 1 per level

    def can_cast(self, spell: str) -> bool:
        """Elf can cast non-cleric spells if slots remain."""
        return spell in self.spells_known and self.spells_remaining > 0

    def use_spell(self, spell_name: str = None) -> bool:
        """Use a spell slot."""
        if spell_name in self.spells_known and self.spells_remaining > 0:
            self.spells_remaining -= 1
            return True
        return False


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

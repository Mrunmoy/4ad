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
    if class_name in CHARACTER_CLASSES:
        return CHARACTER_CLASSES[class_name](name, level)
    raise ValueError(f"Unknown character class: {class_name}")

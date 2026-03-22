"""Monster classes for 4AD."""
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Monster:
    """Base monster class."""
    name: str
    level: int
    life: int = 1
    max_life: int = 1
    is_undead: bool = False
    is_demon: bool = False
    is_dragon: bool = False
    is_final_boss: bool = False

    def take_damage(self, amount: int) -> None:
        """Take damage."""
        self.life -= amount
        if self.life < 0:
            self.life = 0

    def is_dead(self) -> bool:
        """Check if monster is dead."""
        return self.life <= 0

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "level": self.level,
            "life": self.life,
            "max_life": self.max_life,
            "is_undead": self.is_undead,
            "is_demon": self.is_demon,
            "is_dragon": self.is_dragon,
            "is_final_boss": self.is_final_boss,
        }


class Minion(Monster):
    """Minion monsters - die on any hit."""
    def __init__(self, name: str, level: int, **kwargs):
        super().__init__(name=name, level=level, life=1, max_life=1, **kwargs)


class Boss(Monster):
    """Boss monsters - have multiple life points."""
    def __init__(self, name: str, level: int, life: int, **kwargs):
        super().__init__(name=name, level=level, life=life, max_life=life, **kwargs)


# Predefined minions from the rulebook
MINIONS_TABLE = {
    1: lambda: Minion("Giant Rat", level=1),
    2: lambda: Minion("Goblin", level=3),
    3: lambda: Minion("Skeleton", level=2, is_undead=True),
    4: lambda: Minion("Orc", level=4),
    5: lambda: Minion("Zombie", level=3, is_undead=True),
    6: lambda: Minion("Kobold", level=2),
}

# Predefined bosses from the rulebook
BOSSES_TABLE = {
    1: lambda: Boss("Chaos Warrior", level=5, life=6, is_demon=True),
    2: lambda: Boss("Ogre", level=5, life=6),
    3: lambda: Boss("Vampire", level=6, life=6, is_undead=True),
    4: lambda: Boss("Demon", level=7, life=8, is_demon=True),
    5: lambda: Boss("Troll", level=6, life=8),
    6: lambda: Boss("Dragon", level=8, life=10, is_dragon=True),
}

# Weird monsters
WEIRD_MONSTERS_TABLE = {
    1: lambda: Minion("Gelatinous Cube", level=4),
    2: lambda: Minion("Rust Monster", level=3),
    3: lambda: Minion("Carrion Crawler", level=4),
    4: lambda: Minion("Mimic", level=5),
    5: lambda: Boss("Medusa", level=5, life=5),
    6: lambda: Boss("Mind Flayer", level=6, life=6),
}

# Vermin
VERMIN_TABLE = {
    1: lambda: Minion("Rats", level=0),
    2: lambda: Minion("Spiders", level=0),
    3: lambda: Minion("Bats", level=0),
    4: lambda: Minion("Snakes", level=1),
    5: lambda: Minion("Insects", level=0),
    6: lambda: Minion("Scorpions", level=1),
}

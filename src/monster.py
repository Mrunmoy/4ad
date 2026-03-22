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

    # Morale fields
    morale_modifier: int = 0
    fights_to_death: bool = False
    treasure_modifier: int = 0
    morale_checked: bool = False

    # Multi-attack fields
    num_attacks: int = 1       # Number of attacks per round
    damage_per_hit: int = 1    # Damage dealt per successful hit

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
            "fights_to_death": self.fights_to_death,
            "morale_modifier": self.morale_modifier,
            "treasure_modifier": self.treasure_modifier,
            "num_attacks": self.num_attacks,
            "damage_per_hit": self.damage_per_hit,
        }


class Minion(Monster):
    """Minion monsters - die on any hit."""
    def __init__(self, name: str, level: int, **kwargs):
        super().__init__(name=name, level=level, life=1, max_life=1, **kwargs)


class Boss(Monster):
    """Boss monsters - have multiple life points."""
    def __init__(self, name: str, level: int, life: int, **kwargs):
        super().__init__(name=name, level=level, life=life, max_life=life, **kwargs)


# ---------------------------------------------------------------------------
# Predefined minions from the rulebook
# ---------------------------------------------------------------------------

MINIONS_TABLE = {
    1: lambda: Minion("Giant Rat", level=1,
                       fights_to_death=False, morale_modifier=0, treasure_modifier=0),

    2: lambda: Minion("Goblin", level=3,
                       fights_to_death=False, morale_modifier=0, treasure_modifier=-1),

    3: lambda: Minion("Skeleton", level=3, is_undead=True,
                       fights_to_death=True, morale_modifier=0, treasure_modifier=0),

    4: lambda: Minion("Orc", level=4,
                       fights_to_death=False, morale_modifier=0, treasure_modifier=0),

    5: lambda: Minion("Zombie", level=3, is_undead=True,
                       fights_to_death=True, morale_modifier=0, treasure_modifier=0),

    6: lambda: Minion("Kobold", level=2,
                       fights_to_death=False, morale_modifier=0, treasure_modifier=0),
}

# ---------------------------------------------------------------------------
# Predefined bosses from the rulebook
# ---------------------------------------------------------------------------

BOSSES_TABLE = {
    1: lambda: Boss("Chaos Warrior", level=5, life=6, is_demon=True,
                     fights_to_death=False, morale_modifier=0, treasure_modifier=1),

    2: lambda: Boss("Ogre", level=5, life=6,
                     fights_to_death=False, morale_modifier=0, treasure_modifier=0,
                     damage_per_hit=2),

    3: lambda: Boss("Vampire", level=6, life=6, is_undead=True,
                     fights_to_death=True, morale_modifier=0, treasure_modifier=1),

    4: lambda: Boss("Demon", level=7, life=8, is_demon=True,
                     fights_to_death=True, morale_modifier=0, treasure_modifier=2),

    5: lambda: Boss("Troll", level=6, life=8,
                     fights_to_death=False, morale_modifier=0, treasure_modifier=0),

    6: lambda: Boss("Dragon", level=8, life=10, is_dragon=True,
                     fights_to_death=True, morale_modifier=0, treasure_modifier=3),
}

# ---------------------------------------------------------------------------
# Weird monsters
# ---------------------------------------------------------------------------

WEIRD_MONSTERS_TABLE = {
    1: lambda: Boss("Gelatinous Cube", level=4, life=4,
                     fights_to_death=True, morale_modifier=0, treasure_modifier=0),

    2: lambda: Minion("Rust Monster", level=3,
                       fights_to_death=False, morale_modifier=0, treasure_modifier=0),

    3: lambda: Boss("Carrion Crawler", level=4, life=4,
                     fights_to_death=False, morale_modifier=0, treasure_modifier=0),

    4: lambda: Boss("Mimic", level=5, life=5,
                     fights_to_death=False, morale_modifier=0, treasure_modifier=1),

    5: lambda: Boss("Medusa", level=5, life=5,
                     fights_to_death=False, morale_modifier=0, treasure_modifier=1),

    6: lambda: Boss("Mind Flayer", level=6, life=6,
                     fights_to_death=True, morale_modifier=0, treasure_modifier=2),
}

# ---------------------------------------------------------------------------
# Vermin
# ---------------------------------------------------------------------------

VERMIN_TABLE = {
    1: lambda: Minion("Rats", level=0,
                       fights_to_death=False, morale_modifier=0, treasure_modifier=0),

    2: lambda: Minion("Spiders", level=0,
                       fights_to_death=False, morale_modifier=0, treasure_modifier=0),

    3: lambda: Minion("Bats", level=0,
                       fights_to_death=False, morale_modifier=0, treasure_modifier=0),

    4: lambda: Minion("Snakes", level=1,
                       fights_to_death=False, morale_modifier=0, treasure_modifier=0),

    5: lambda: Minion("Insects", level=0,
                       fights_to_death=False, morale_modifier=0, treasure_modifier=0),

    6: lambda: Minion("Scorpions", level=1,
                       fights_to_death=False, morale_modifier=0, treasure_modifier=0),
}

# ---------------------------------------------------------------------------
# Multi-attack bosses (extended boss table from rulebook)
# ---------------------------------------------------------------------------

MULTI_ATTACK_BOSSES = {
    "Mummy": lambda: Boss("Mummy", level=5, life=6, is_undead=True,
                           fights_to_death=True, morale_modifier=0, treasure_modifier=1,
                           num_attacks=2),

    "Orc Brute": lambda: Boss("Orc Brute", level=5, life=6,
                               fights_to_death=False, morale_modifier=0, treasure_modifier=0,
                               num_attacks=2),

    "Chimera": lambda: Boss("Chimera", level=7, life=8,
                             fights_to_death=True, morale_modifier=0, treasure_modifier=2,
                             num_attacks=3),

    "Small Dragon": lambda: Boss("Small Dragon", level=6, life=7, is_dragon=True,
                                  fights_to_death=True, morale_modifier=0, treasure_modifier=2,
                                  num_attacks=2),
}

"""Treasure and loot system for Four Against Darkness.

Implements treasure tables, magic treasure, and gold distribution
per the rulebook specifications (Section 6 of design doc).
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Union

from src.dice import roll_d6, roll_2d6
from src.equipment import (
    Weapon, Armor, Item, EquipmentItem,
    WEAPON_LIST, ITEM_LIST,
)


# ---------------------------------------------------------------------------
# Treasure result types
# ---------------------------------------------------------------------------

@dataclass
class TreasureResult:
    """Result of a treasure roll."""
    description: str
    gold: int = 0
    item: Optional[EquipmentItem] = None
    spell_scroll: Optional[str] = None

    def to_dict(self) -> dict:
        d: dict = {"description": self.description, "gold": self.gold}
        if self.spell_scroll:
            d["spell_scroll"] = self.spell_scroll
        if self.item:
            d["item"] = self.item.name if hasattr(self.item, "name") else str(self.item)
        return d


# ---------------------------------------------------------------------------
# Spell scroll table
# ---------------------------------------------------------------------------

SPELL_SCROLL_TABLE = {
    1: "Blessing",
    2: "Fireball",
    3: "Lightning Bolt",
    4: "Sleep",
    5: "Escape",
    6: "Protect",
}


def roll_random_spell(force_roll: Optional[int] = None) -> str:
    """Roll d6 to determine a random spell for a scroll."""
    roll = force_roll if force_roll is not None else roll_d6()
    return SPELL_SCROLL_TABLE[roll]


# ---------------------------------------------------------------------------
# Magic treasure table
# ---------------------------------------------------------------------------

def _make_magic_weapon(force_roll: Optional[int] = None) -> Weapon:
    """Roll d6 to determine magic weapon type."""
    roll = force_roll if force_roll is not None else roll_d6()
    if roll == 1:
        return Weapon(name="Magic Light Crushing Weapon", cost=0, hands=1,
                      attack_modifier=0, damage_type="crushing", is_magic=True)
    elif roll == 2:
        return Weapon(name="Magic Light Slashing Weapon", cost=0, hands=1,
                      attack_modifier=0, damage_type="slashing", is_magic=True)
    elif roll == 3:
        return Weapon(name="Magic Crushing Hand Weapon", cost=0, hands=1,
                      attack_modifier=1, damage_type="crushing", is_magic=True)
    elif roll in (4, 5):
        return Weapon(name="Magic Slashing Hand Weapon", cost=0, hands=1,
                      attack_modifier=1, damage_type="slashing", is_magic=True)
    else:  # 6
        return Weapon(name="Magic Bow", cost=0, hands=2,
                      attack_modifier=1, damage_type="slashing",
                      is_ranged=True, is_magic=True)


MAGIC_TREASURE_TABLE = {
    1: lambda: Item(
        name="Wand of Sleep", cost=0, one_use=False,
        description="3 charges. Cast Sleep spell. Not for barbarians.",
        charges=3, is_magic=True,
    ),
    2: lambda: Item(
        name="Ring of Teleportation", cost=0, one_use=True,
        description="1 charge. Teleport party to entrance. Not for barbarians.",
        charges=1, is_magic=True,
    ),
    3: lambda: Item(
        name="Fool's Gold Purse", cost=0, one_use=True,
        description="1 charge. Auto-bribe any monster once. Any class.",
        charges=1, is_magic=False,
    ),
    4: lambda: _make_magic_weapon(),
    5: lambda: Item(
        name="Potion of Healing", cost=0, one_use=True,
        description="Full heal. Any time. One-use. Any class including barbarian.",
        charges=1, is_magic=True,
    ),
    6: lambda: Item(
        name="Fireball Staff", cost=0, one_use=False,
        description="2 charges. Cast Fireball. Wizards only.",
        charges=2, is_magic=True,
    ),
}


def roll_magic_treasure(force_roll: Optional[int] = None) -> EquipmentItem:
    """Roll on the Magic Treasure Table (d6).

    Note: Magic items have class restrictions (e.g. Wand of Sleep is for
    wizards/elves only, Fireball Staff is wizards only). These restrictions
    are enforced at equip time via MAGIC_ITEM_CLASS_RESTRICTIONS in
    equipment.py, not at treasure-roll time -- the party finds the item
    regardless, but only eligible characters can use/equip it.
    """
    roll = force_roll if force_roll is not None else roll_d6()
    return MAGIC_TREASURE_TABLE[roll]()


# ---------------------------------------------------------------------------
# Main treasure table
# ---------------------------------------------------------------------------

# Monster-specific treasure modifiers
MONSTER_TREASURE_MODIFIERS = {
    "Goblin": -1,
    "Hobgoblin": 1,
    "Orc": None,  # special: d6 x d6 gold, never magic
    "Chaos Lord": 1,
    "Vampire": 1,
    "Demon": 2,
    "Dragon": 3,
    "Small Dragon": 3,
}


def roll_treasure(
    modifier: int = 0,
    monster_name: Optional[str] = None,
    force_d6: Optional[int] = None,
    force_gold_rolls: Optional[list] = None,
    force_magic_roll: Optional[int] = None,
    force_spell_roll: Optional[int] = None,
    force_weapon_roll: Optional[int] = None,
) -> TreasureResult:
    """Roll on the treasure table after combat.

    Args:
        modifier: Numeric treasure modifier (added to d6 roll).
        monster_name: If given, look up monster-specific modifier.
        force_d6: Force the initial d6 roll (for testing).
        force_gold_rolls: Force gold sub-rolls (for testing).
        force_magic_roll: Force magic treasure d6 (for testing).
        force_spell_roll: Force spell scroll d6 (for testing).
        force_weapon_roll: Force magic weapon type d6 (for testing).

    Returns:
        TreasureResult with description, gold, and/or item.
    """
    # Handle Orc special case
    if monster_name and monster_name == "Orc":
        r1 = force_gold_rolls[0] if force_gold_rolls else roll_d6()
        r2 = force_gold_rolls[1] if force_gold_rolls and len(force_gold_rolls) > 1 else roll_d6()
        gold = r1 * r2
        return TreasureResult(
            description=f"Orc treasure: {gold} gold pieces",
            gold=gold,
        )

    # Look up monster-specific modifier
    if monster_name and monster_name in MONSTER_TREASURE_MODIFIERS:
        mon_mod = MONSTER_TREASURE_MODIFIERS[monster_name]
        if mon_mod is not None:
            modifier += mon_mod

    roll = force_d6 if force_d6 is not None else roll_d6()
    total = roll + modifier

    if total <= 0:
        return TreasureResult(description="Nothing found.")

    if total == 1:
        g = force_gold_rolls[0] if force_gold_rolls else roll_d6()
        return TreasureResult(description=f"Found {g} gold pieces", gold=g)

    if total == 2:
        r1 = force_gold_rolls[0] if force_gold_rolls else roll_d6()
        r2 = force_gold_rolls[1] if force_gold_rolls and len(force_gold_rolls) > 1 else roll_d6()
        g = r1 + r2
        return TreasureResult(description=f"Found {g} gold pieces", gold=g)

    if total == 3:
        spell = roll_random_spell(force_roll=force_spell_roll)
        return TreasureResult(
            description=f"Found a scroll of {spell}",
            spell_scroll=spell,
        )

    if total == 4:
        r1 = force_gold_rolls[0] if force_gold_rolls else roll_d6()
        r2 = force_gold_rolls[1] if force_gold_rolls and len(force_gold_rolls) > 1 else roll_d6()
        value = (r1 + r2) * 5
        return TreasureResult(
            description=f"Found a gem worth {value} gold",
            gold=value,
        )

    if total == 5:
        r1 = force_gold_rolls[0] if force_gold_rolls else roll_d6()
        r2 = force_gold_rolls[1] if force_gold_rolls and len(force_gold_rolls) > 1 else roll_d6()
        r3 = force_gold_rolls[2] if force_gold_rolls and len(force_gold_rolls) > 2 else roll_d6()
        value = (r1 + r2 + r3) * 10
        return TreasureResult(
            description=f"Found jewelry worth {value} gold",
            gold=value,
        )

    # total >= 6: magic treasure
    item = roll_magic_treasure(force_roll=force_magic_roll)
    # If the magic treasure is a weapon, allow forcing the sub-roll
    if force_magic_roll == 4 and force_weapon_roll is not None:
        item = _make_magic_weapon(force_roll=force_weapon_roll)
    return TreasureResult(
        description=f"Found magic treasure: {item.name}",
        item=item,
    )


# ---------------------------------------------------------------------------
# Gold distribution
# ---------------------------------------------------------------------------

def distribute_gold(
    gold: int,
    characters: list,
) -> dict:
    """Distribute gold among party members.

    Rules:
    - Split evenly among living characters
    - Dwarves always get at least 1 gold from any distribution
    - Respects per-character gold caps (200 default, 250 for dwarves)

    Args:
        gold: Total gold to distribute.
        characters: List of Character objects (must have class_type and inventory).

    Returns:
        Dict mapping character name to gold received.
    """
    if gold <= 0 or not characters:
        return {}

    living = [c for c in characters if not c.is_dead()]
    if not living:
        return {}

    distribution: dict = {}
    remaining = gold
    share = gold // len(living)

    # First pass: ensure dwarves get at least 1
    for char in living:
        if char.class_type == "Dwarf" and share == 0 and remaining > 0:
            amount = 1
        else:
            amount = min(share, remaining)
        if amount > 0 and hasattr(char, 'inventory') and char.inventory is not None:
            added = char.inventory.add_gold(amount)
            distribution[char.name] = added
            remaining -= added
        elif amount > 0:
            distribution[char.name] = amount
            remaining -= amount

    # Second pass: distribute remainder round-robin
    while remaining > 0:
        distributed_any = False
        for char in living:
            if remaining <= 0:
                break
            if hasattr(char, 'inventory') and char.inventory is not None:
                added = char.inventory.add_gold(1)
                if added > 0:
                    distribution[char.name] = distribution.get(char.name, 0) + added
                    remaining -= added
                    distributed_any = True
        if not distributed_any:
            break  # all inventories full, prevent infinite loop

    return distribution

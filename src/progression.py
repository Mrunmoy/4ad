"""XP and Leveling system for 4AD."""
from dataclasses import dataclass
from typing import Optional
from src.dice import roll_d6


# Base life values per class (max_life = base + level)
BASE_LIFE = {
    "Warrior": 6,
    "Cleric": 5,
    "Rogue": 4,
    "Wizard": 3,
    "Barbarian": 8,
    "Elf": 4,
    "Dwarf": 7,
    "Halfling": 4,
}

MAX_LEVEL = 5


@dataclass
class XPRollResult:
    """Result of an XP level-up attempt."""
    character_name: str
    roll: int
    current_level: int
    leveled_up: bool
    new_level: int
    stat_changes: dict
    description: str


def get_xp_rolls_earned(
    boss_killed: bool = False,
    weird_monster_killed: bool = False,
    minion_encounters: int = 0,
    dragon_final_boss: bool = False,
    quest_completed: bool = False,
) -> int:
    """Calculate total XP rolls earned from various sources.

    Args:
        boss_killed: A boss monster was killed.
        weird_monster_killed: A weird monster was killed.
        minion_encounters: Cumulative non-vermin minion encounters survived.
        dragon_final_boss: Dragon killed as the final boss (gives 2 instead of 1).
        quest_completed: A quest was completed.

    Returns:
        Number of XP rolls earned.
    """
    rolls = 0

    if dragon_final_boss:
        # Dragon as final boss gives 2 XP rolls (replaces the normal boss roll)
        rolls += 2
    elif boss_killed:
        rolls += 1

    if weird_monster_killed:
        rolls += 1

    # 1 XP roll per 10 minion encounters survived (not vermin)
    rolls += minion_encounters // 10

    if quest_completed:
        rolls += 1

    return rolls


def attempt_level_up(
    character,
    last_leveled_character: Optional[str] = None,
    force_roll: Optional[int] = None,
) -> XPRollResult:
    """Attempt to level up a character via XP roll.

    Roll d6: if result > character's current level, the character levels up.
    Halfling luck CANNOT be used to reroll XP rolls (spec Section 1, Halfling).

    Args:
        character: The character attempting to level up.
        last_leveled_character: Name of the character who last received an XP roll.
            Cannot be the same as character.name unless all others are at max level.
        force_roll: Override the d6 roll (for testing).

    Returns:
        XPRollResult with the outcome.

    Raises:
        ValueError: If the character is at max level or the same character was
            rolled for consecutively (when not allowed).
    """
    if character.level >= MAX_LEVEL:
        raise ValueError(
            f"{character.name} is already at max level {MAX_LEVEL}"
        )

    if (
        last_leveled_character is not None
        and last_leveled_character == character.name
    ):
        raise ValueError(
            f"Cannot attempt {character.name} twice in a row"
        )

    # Capture old level BEFORE applying level-up (M2 fix)
    old_level = character.level

    roll = force_roll if force_roll is not None else roll_d6()
    leveled_up = roll > old_level
    stat_changes = {}
    new_level = old_level

    if leveled_up:
        new_level = old_level + 1
        stat_changes = _apply_level_up(character)

    # M3 fix: proper f-string (was printing literal {new_level})
    desc = (
        f"{character.name} rolled {roll} vs level {old_level}: "
        + (f"LEVEL UP to {new_level}!" if leveled_up else "no level up.")
    )

    return XPRollResult(
        character_name=character.name,
        roll=roll,
        current_level=old_level,
        leveled_up=leveled_up,
        new_level=new_level,
        stat_changes=stat_changes,
        description=desc,
    )


def _apply_level_up(character) -> dict:
    """Apply level-up effects to a character. Returns dict of stat changes."""
    changes = {}
    old_level = character.level
    new_level = old_level + 1
    character.level = new_level

    # All classes: +1 max_life, +1 current_life
    character.max_life += 1
    character.life += 1
    changes["max_life"] = 1
    changes["life"] = 1

    class_type = character.class_type

    if class_type == "Warrior":
        # +1 attack (warrior adds level to attacks)
        changes["attack_bonus"] = 1

    elif class_type == "Cleric":
        # Attack bonus is floor(level/2), save vs undead is +level
        changes["save_vs_undead"] = 1

    elif class_type == "Rogue":
        # +1 defense, +1 attack (when outnumbering), +1 disarm
        changes["defense_bonus"] = 1
        changes["attack_bonus_outnumber"] = 1
        changes["disarm_bonus"] = 1

    elif class_type == "Wizard":
        # +1 spell slot, +1 to spell attack rolls
        if hasattr(character, "spell_slots"):
            character.spell_slots += 1
        changes["spell_slots"] = 1
        changes["spell_attack_bonus"] = 1

    elif class_type == "Barbarian":
        # +1 attack
        changes["attack_bonus"] = 1

    elif class_type == "Elf":
        # +1 spell slot, +1 attack, +1 spell attack
        if hasattr(character, "spell_slots"):
            character.spell_slots += 1
        changes["spell_slots"] = 1
        changes["attack_bonus"] = 1
        changes["spell_attack_bonus"] = 1

    elif class_type == "Dwarf":
        # +1 attack (melee)
        changes["attack_bonus"] = 1

    elif class_type == "Halfling":
        # C1 fix: +1 luck point AND +1 max_luck_points
        # +1 defense vs giants/trolls/ogres, +1 poison save
        if hasattr(character, "luck_points"):
            character.luck_points += 1
        if hasattr(character, "max_luck_points"):
            character.max_luck_points += 1
        changes["luck_points"] = 1
        changes["max_luck_points"] = 1
        changes["defense_vs_large"] = 1
        changes["poison_save"] = 1

    return changes

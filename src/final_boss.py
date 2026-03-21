"""Final boss detection and dungeon exit for 4AD."""
from src.dice import roll_d6
from src.monster import Monster, Boss, MINIONS_TABLE


def check_final_boss(bosses_encountered: int, force_roll: int = None) -> bool:
    """Check whether the current boss encounter is the final boss.

    Roll d6 + bosses_encountered.  If total >= 6, this is the final boss.

    Args:
        bosses_encountered: Number of bosses and weird monsters encountered so far
            (including this one).
        force_roll: Override the d6 roll (for testing).

    Returns:
        True if this is the final boss encounter.
    """
    roll = force_roll if force_roll is not None else roll_d6()
    return (roll + bosses_encountered) >= 6


def create_final_boss(base_monster: Monster) -> Monster:
    """Enhance a monster into a final boss.

    Modifications:
        - +1 life (and max_life)
        - +1 level
        - Fights to death (always)
        - Treasure tripled (handled by caller), min 100 gp

    Args:
        base_monster: The base monster to enhance.

    Returns:
        The same monster instance, modified in place.
    """
    base_monster.life += 1
    base_monster.max_life += 1
    base_monster.level += 1
    base_monster.is_final_boss = True
    return base_monster


def roll_exit_encounter(force_roll: int = None) -> bool:
    """Roll for a wandering monster encounter during dungeon exit.

    Roll d6: on 1, a wandering monster attacks.

    Args:
        force_roll: Override the d6 roll (for testing).

    Returns:
        True if a wandering monster encounter occurs.
    """
    roll = force_roll if force_roll is not None else roll_d6()
    return roll == 1


def generate_exit_monster():
    """Generate a wandering monster for exit encounters.

    Returns a minion from the minion table.
    """
    roll = roll_d6()
    return MINIONS_TABLE[roll]()

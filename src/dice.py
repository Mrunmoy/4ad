"""Dice rolling mechanics for 4AD."""
import random
from dataclasses import dataclass
from typing import List


@dataclass
class DiceResult:
    """Result of a dice roll with explosive six."""
    total: int
    rolls: List[int]


def roll_d6() -> int:
    """Roll a single d6."""
    return random.randint(1, 6)


def roll_2d6() -> int:
    """Roll 2d6 and sum."""
    return roll_d6() + roll_d6()


def roll_d66() -> int:
    """Roll d66 (two dice as tens and units)."""
    tens = roll_d6()
    units = roll_d6()
    return tens * 10 + units


def explosive_six(force_rolls: List[int] = None) -> DiceResult:
    """
    Roll with explosive six rule (page 6).
    When you roll a 6, roll again and add.
    """
    rolls = []
    total = 0
    
    if force_rolls:
        # For testing - use forced rolls
        for roll in force_rolls:
            rolls.append(roll)
            total += roll
    else:
        # Normal rolling
        while True:
            roll = roll_d6()
            rolls.append(roll)
            total += roll
            if roll != 6:
                break
    
    return DiceResult(total=total, rolls=rolls)

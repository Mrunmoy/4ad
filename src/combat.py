"""Combat mechanics for 4AD."""
from dataclasses import dataclass
from typing import List, Union
from src.character import Character
from src.monster import Monster, Minion, Boss
from src.dice import explosive_six, roll_d6


@dataclass
class AttackResult:
    """Result of an attack roll."""
    hit: bool
    total_roll: int
    rolls: List[int]
    damage_dealt: int = 0
    minions_killed: int = 0


@dataclass
class DefenseResult:
    """Result of a defense roll."""
    success: bool
    total_roll: int
    rolls: List[int]
    damage_taken: int = 0


@dataclass
class MoraleResult:
    """Result of a morale check."""
    checked: bool  # Whether a check was actually triggered
    fled: bool
    roll: int = 0
    description: str = ""


class Combat:
    """Combat resolution."""

    @staticmethod
    def resolve_attack(
        attacker: Character,
        target: Union[Monster, List[Monster]],
        force_roll: int = None,
        force_rolls: List[int] = None
    ) -> AttackResult:
        """
        Resolve an attack roll.
        Rule: Roll + Attack >= Monster Level = Hit
        """
        if force_rolls:
            dice_result = explosive_six(force_rolls=force_rolls)
        elif force_roll:
            dice_result = explosive_six(force_rolls=[force_roll])
        else:
            dice_result = explosive_six()

        total = dice_result.total + attacker.attack

        # Handle multiple minions (explosive six can kill multiple)
        if isinstance(target, list) and all(isinstance(m, Minion) for m in target):
            minions_killed = 0
            remaining_damage = total

            for minion in target:
                if remaining_damage >= minion.level and not minion.is_dead():
                    minion.take_damage(1)
                    minions_killed += 1
                    remaining_damage -= minion.level

            return AttackResult(
                hit=minions_killed > 0,
                total_roll=total,
                rolls=dice_result.rolls,
                minions_killed=minions_killed
            )

        # Single target
        if isinstance(target, list):
            target = target[0] if target else None

        if target is None:
            return AttackResult(hit=False, total_roll=total, rolls=dice_result.rolls)

        hit = total >= target.level
        damage = 0

        if hit:
            if isinstance(target, Minion):
                damage = 1
                target.take_damage(1)
            elif isinstance(target, Boss):
                damage = 2
                target.take_damage(2)

        return AttackResult(
            hit=hit,
            total_roll=total,
            rolls=dice_result.rolls,
            damage_dealt=damage
        )

    @staticmethod
    def resolve_defense(
        defender: Character,
        attacker: Monster,
        force_roll: int = None
    ) -> DefenseResult:
        """
        Resolve a defense roll.
        Rule: Roll + Defense > Monster Level = Success (no damage)
        """
        if force_roll:
            dice_result = explosive_six(force_rolls=[force_roll])
        else:
            dice_result = explosive_six()

        total = dice_result.total + defender.defense

        # Apply curse penalty
        if defender.cursed:
            total -= 1

        # Apply Protect spell bonus
        if getattr(defender, 'protected', False):
            total += 1

        success = total > attacker.level
        damage = 0 if success else 1

        if not success:
            defender.take_damage(1)

        return DefenseResult(
            success=success,
            total_roll=total,
            rolls=dice_result.rolls,
            damage_taken=damage
        )

    @staticmethod
    def resolve_monster_attack(
        monster: Monster,
        party: List[Character],
        force_roll: int = None
    ) -> List[DefenseResult]:
        """
        Resolve monster attacking entire party.
        Each character makes defense roll.
        """
        results = []
        for character in party:
            if not character.is_dead():
                result = Combat.resolve_defense(character, monster, force_roll)
                results.append(result)
        return results

    @staticmethod
    def check_minion_morale(
        monsters: List[Monster],
        original_count: int,
        spell_killed: bool = False,
        force_roll: int = None
    ) -> MoraleResult:
        """
        Check morale for minion groups.
        Trigger: more than 50% of original count killed.
        Roll d6 + morale_modifier: 1-3 = flee, 4-6 = fight on.

        Args:
            monsters: Current list of monsters (some may be dead)
            original_count: How many there were at start
            spell_killed: Whether a spell killed a minion this combat (orcs fear magic)
            force_roll: For testing

        Returns:
            MoraleResult
        """
        living = [m for m in monsters if not m.is_dead()]
        dead_count = original_count - len(living)

        # No check if not enough are dead
        if dead_count <= original_count // 2:
            return MoraleResult(checked=False, fled=False)

        # Check if monsters fight to death
        sample = living[0] if living else (monsters[0] if monsters else None)
        if sample is None:
            return MoraleResult(checked=False, fled=False)
        if sample.fights_to_death:
            return MoraleResult(
                checked=True, fled=False,
                description=f"The {sample.name}s fight to the death!"
            )

        # Already checked morale this encounter
        if sample.morale_checked:
            return MoraleResult(checked=False, fled=False)

        roll = force_roll if force_roll is not None else roll_d6()
        modifier = sample.morale_modifier

        # Orcs: -1 if a spell killed one
        if sample.name == "Orc" and spell_killed:
            modifier -= 1

        total = roll + modifier
        fled = total <= 3

        # Mark morale as checked on all living monsters
        for m in living:
            m.morale_checked = True

        if fled:
            return MoraleResult(
                checked=True, fled=True, roll=total,
                description=f"The {sample.name}s fail their morale check (roll {total}) and flee!"
            )
        else:
            return MoraleResult(
                checked=True, fled=False, roll=total,
                description=f"The {sample.name}s hold their ground (roll {total})."
            )

    @staticmethod
    def check_boss_morale(
        boss: Boss,
        force_roll: int = None
    ) -> MoraleResult:
        """
        Check morale for a boss.
        Trigger: life drops below 50% of max_life.
        Effect: level drops by 1 immediately.
        Roll d6: 1-3 = flee, 4+ = fight on.

        Returns:
            MoraleResult
        """
        if boss.fights_to_death:
            return MoraleResult(
                checked=False, fled=False,
                description=f"{boss.name} fights to the death!"
            )

        if boss.morale_checked:
            return MoraleResult(checked=False, fled=False)

        # Check threshold: below 50% of max life
        if boss.life > boss.max_life // 2:
            return MoraleResult(checked=False, fled=False)

        # Boss level drops by 1
        if boss.level > 1:
            boss.level -= 1

        boss.morale_checked = True

        roll = force_roll if force_roll is not None else roll_d6()
        fled = roll <= 3

        if fled:
            return MoraleResult(
                checked=True, fled=True, roll=roll,
                description=f"{boss.name} is wounded and flees! (roll {roll})"
            )
        else:
            return MoraleResult(
                checked=True, fled=False, roll=roll,
                description=f"{boss.name} is wounded but fights on! (roll {roll}, level reduced)"
            )

"""Combat mechanics for 4AD."""
from dataclasses import dataclass
from typing import List, Union
from src.character import Character
from src.monster import Monster, Minion, Boss
from src.dice import explosive_six


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

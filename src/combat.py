"""Combat mechanics for 4AD."""
from dataclasses import dataclass, field
from typing import List, Optional, Union
from src.character import Character
from src.monster import Monster, Minion, Boss
from src.dice import explosive_six, roll_d6


def _pluralize(name: str) -> str:
    """Pluralize a monster name, handling names that already end in 's'."""
    if name.endswith("s"):
        return name
    return name + "s"


# ---------------------------------------------------------------------------
# Weapon type helpers
# ---------------------------------------------------------------------------

def _get_weapon_damage_type(character: Character) -> str:
    """Get the damage type of the character's equipped weapon."""
    inv = getattr(character, 'inventory', None)
    if inv and inv.weapons:
        return inv.weapons[0].damage_type
    return "slashing"


def _is_weapon_ranged(character: Character) -> bool:
    """Check if the character has any ranged weapon equipped."""
    inv = getattr(character, 'inventory', None)
    if inv and inv.weapons:
        return any(w.is_ranged for w in inv.weapons)
    return False


def _is_weapon_two_handed(character: Character) -> bool:
    """Check if the character's equipped weapon is two-handed."""
    inv = getattr(character, 'inventory', None)
    if inv and inv.weapons:
        return inv.weapons[0].hands == 2
    return False


def _is_weapon_light(character: Character) -> bool:
    """Check if the character's equipped weapon is a light weapon."""
    inv = getattr(character, 'inventory', None)
    if inv and inv.weapons:
        return inv.weapons[0].attack_modifier < 0
    return False


def _get_weapon_modifier(character: Character, target: Monster) -> int:
    """Get weapon combat modifiers based on weapon type and target.

    - Two-handed weapons: +1
    - Light weapons: -1
    - Crushing vs skeletons/statues: +1
    """
    inv = getattr(character, 'inventory', None)
    if not inv or not inv.weapons:
        return 0

    weapon = inv.weapons[0]
    modifier = 0

    # Two-handed bonus
    if weapon.hands == 2 and not weapon.is_ranged:
        modifier += 1

    # Light weapon penalty
    if weapon.attack_modifier < 0:
        modifier += weapon.attack_modifier  # Usually -1

    # Crushing bonus vs skeletons and statues
    if weapon.damage_type == "crushing":
        target_name = getattr(target, 'name', '').lower()
        if 'skeleton' in target_name or 'statue' in target_name:
            modifier += 1

    return modifier


def _get_equipment_defense_bonus(character: Character) -> int:
    """Get defense bonus from equipped armor and shield.

    - Light armor: +1
    - Heavy armor: +2
    - Shield: +1
    """
    inv = getattr(character, 'inventory', None)
    if not inv:
        return 0
    return inv.get_defense_bonus()


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


@dataclass
class RangedPhaseResult:
    """Result of ranged attacks in the first round."""
    attacks: List[AttackResult] = field(default_factory=list)
    attackers: List[str] = field(default_factory=list)


class Combat:
    """Combat resolution."""

    @staticmethod
    def resolve_attack(
        attacker: Character,
        target: Union[Monster, List[Monster]],
        force_roll: int = None,
        force_rolls: List[int] = None,
        party_size: int = 0,
        enemy_count: int = 0,
        corridor: bool = False,
        attacker_position: int = 1,
    ) -> AttackResult:
        """
        Resolve an attack roll.
        Rule: Roll + Attack + class_bonus + weapon_modifier >= Monster Level = Hit

        Args:
            attacker: Character making the attack.
            target: Monster or list of minions to attack.
            force_roll: Override dice roll for testing.
            force_rolls: Override multiple dice rolls for testing.
            party_size: Number of living party members (for Rogue bonus).
            enemy_count: Number of living enemies (for Rogue bonus).
            corridor: Whether combat is in a corridor.
            attacker_position: Position in corridor (1 or 2).
        """
        if force_rolls:
            dice_result = explosive_six(force_rolls=force_rolls)
        elif force_roll is not None:
            dice_result = explosive_six(force_rolls=[force_roll])
        else:
            dice_result = explosive_six()

        # Determine the actual single target for bonus calculations
        actual_target = target
        if isinstance(target, list):
            actual_target = target[0] if target else None

        # Base attack stat
        total = dice_result.total + attacker.attack

        # Class ability bonus
        ranged = _is_weapon_ranged(attacker)
        two_handed = _is_weapon_two_handed(attacker)
        class_bonus = attacker.attack_bonus(
            target=actual_target,
            party_size=party_size,
            enemy_count=enemy_count,
            ranged=ranged,
            two_handed=two_handed,
        )
        total += class_bonus

        # Weapon modifier (two-handed +1, light -1, crushing vs skeleton +1)
        if actual_target is not None:
            weapon_mod = _get_weapon_modifier(attacker, actual_target)
            total += weapon_mod

        # Equipment attack modifier from inventory
        inv = getattr(attacker, 'inventory', None)
        if inv:
            total += inv.get_attack_modifier()

        # Corridor penalty: position 2 gets -1
        if corridor and attacker_position == 2:
            total -= 1

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
        Rule: Roll + Defense + class_bonus + equipment_bonus > Monster Level = Success

        Class bonuses:
        - Rogue: +level to all defense
        - Dwarf: +1 vs trolls/ogres/giants
        - Halfling: +level vs trolls/ogres/giants
        """
        if force_roll is not None:
            dice_result = explosive_six(force_rolls=[force_roll])
        else:
            dice_result = explosive_six()

        total = dice_result.total + defender.defense

        # Class defense bonus
        class_bonus = defender.defense_bonus(attacker=attacker)
        total += class_bonus

        # Equipment defense bonus (armor + shield)
        equip_bonus = _get_equipment_defense_bonus(defender)
        total += equip_bonus

        # Apply curse penalty
        if defender.cursed:
            total -= 1

        # Apply Protect spell bonus
        if getattr(defender, 'protected', False):
            total += 1

        success = total > attacker.level
        damage = 0 if success else getattr(attacker, 'damage_per_hit', 1)

        if not success:
            defender.take_damage(damage)

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
        force_roll: int = None,
        corridor: bool = False,
    ) -> List[DefenseResult]:
        """
        Resolve monster attacking the party.

        Multi-attack bosses attack multiple times per round, each attack
        targeting one living character (cycling through the party).

        In corridors, only 2 monsters can attack per round (enforced by caller).

        Args:
            monster: The attacking monster.
            party: Living party members.
            force_roll: Override dice for testing.
            corridor: Whether combat is in a corridor.
        """
        results = []
        num_attacks = getattr(monster, 'num_attacks', 1)
        living = [c for c in party if not c.is_dead()]

        if not living:
            return results

        for i in range(num_attacks):
            # Cycle through living party members
            target_idx = i % len(living)
            target = living[target_idx]
            if target.is_dead():
                # Refresh living list in case someone died
                living = [c for c in party if not c.is_dead()]
                if not living:
                    break
                target = living[0]

            result = Combat.resolve_defense(target, monster, force_roll)
            results.append(result)

            # Refresh living list after potential kill
            if result.damage_taken > 0:
                living = [c for c in party if not c.is_dead()]
                if not living:
                    break

        return results

    @staticmethod
    def get_corridor_attackers(
        party: List[Character],
    ) -> List[Character]:
        """Get characters that can attack in corridor combat.

        In corridors (room width == 1), only 2 characters can fight.
        Position 1 attacks normally, position 2 attacks at -1.
        """
        living = [c for c in party if not c.is_dead()]
        # Sort by position
        living.sort(key=lambda c: c.position)
        return living[:2]

    @staticmethod
    def get_corridor_monster_attackers(
        monsters: List[Monster],
    ) -> List[Monster]:
        """Get monsters that can attack in corridor combat.

        Max 2 monsters can attack per round in corridors.
        """
        living = [m for m in monsters if not m.is_dead()]
        return living[:2]

    @staticmethod
    def resolve_ranged_phase(
        party: List[Character],
        targets: Union[Monster, List[Monster]],
        party_size: int = 0,
        enemy_count: int = 0,
        force_roll: int = None,
    ) -> RangedPhaseResult:
        """Resolve the ranged attack phase (first round only).

        Characters with bows attack before monsters act.
        Characters with slings attack before monsters but at -1.

        After first round, ranged characters must switch to melee.
        """
        result = RangedPhaseResult()
        for char in party:
            if char.is_dead():
                continue
            if not _is_weapon_ranged(char):
                continue

            # Slings get -1 penalty (already handled by weapon modifier)
            attack_result = Combat.resolve_attack(
                char, targets,
                force_roll=force_roll,
                party_size=party_size,
                enemy_count=enemy_count,
            )
            result.attacks.append(attack_result)
            result.attackers.append(char.name)

        return result

    @staticmethod
    def check_minion_morale(
        monsters: List[Monster],
        original_count: int,
        spell_killed: bool = False,
        force_roll: int = None,
        kills_this_round: int = 0
    ) -> MoraleResult:
        """
        Check morale for minion groups.
        Trigger: more than 50% of INITIAL count killed in one round.
        Roll d6 + morale_modifier: 1-3 = flee, 4-6 = fight on.

        Args:
            monsters: Current list of monsters (some may be dead)
            original_count: How many there were at start
            spell_killed: Whether a spell killed a minion this combat (orcs fear magic)
            force_roll: For testing
            kills_this_round: Number of minions killed this round

        Returns:
            MoraleResult
        """
        living = [m for m in monsters if not m.is_dead()]

        # No check if not enough killed this round (>50% of initial count)
        if kills_this_round <= original_count // 2:
            return MoraleResult(checked=False, fled=False)

        # Check if monsters fight to death
        sample = living[0] if living else (monsters[0] if monsters else None)
        if sample is None:
            return MoraleResult(checked=False, fled=False)
        if sample.fights_to_death:
            return MoraleResult(
                checked=True, fled=False,
                description=f"The {_pluralize(sample.name)} fight to the death!"
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
                description=f"The {_pluralize(sample.name)} fail their morale check (roll {total}) and flee!"
            )
        else:
            return MoraleResult(
                checked=True, fled=False, roll=total,
                description=f"The {_pluralize(sample.name)} hold their ground (roll {total})."
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
        if boss.life * 2 >= boss.max_life:
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

    @staticmethod
    def resolve_dragon_breath(
        dragon: Monster,
        party: List[Character],
        force_roll: int = None
    ) -> List[dict]:
        """
        Dragon breath weapon: once per combat.
        All characters must make defense roll vs level 8.
        No armor bonus (fire ignores armor). Shield still applies.

        Returns list of dicts with character name, success, damage_taken.
        """
        results = []
        for char in party:
            if char.is_dead():
                continue
            roll = force_roll if force_roll is not None else roll_d6()
            # Defense: roll only (no armor). Protect still applies.
            total = roll
            # Protect spell bonus
            if getattr(char, 'protected', False):
                total += 1
            # Curse penalty
            if char.cursed:
                total -= 1

            success = total >= 6  # Save vs level 6 per rulebook
            damage = 0
            if not success:
                damage = 1
                char.take_damage(1)
            results.append({
                "character": char.name,
                "roll": total,
                "success": success,
                "damage_taken": damage,
            })
        return results

    @staticmethod
    def check_troll_regeneration(
        monsters: List[Monster],
        force_roll: int = None
    ) -> List[str]:
        """
        Check if killed trolls regenerate at end of round.
        If not chopped, roll d6: 5-6 = troll revives
        (1 life for minion trolls, 3 life for boss trolls).

        Returns list of regeneration messages.
        """
        messages = []
        for m in monsters:
            if not m.is_dead():
                continue
            if "troll" not in m.name.lower():
                continue
            if getattr(m, '_chopped', False):
                continue

            roll = force_roll if force_roll is not None else roll_d6()
            if roll >= 5:
                # Revive! Boss trolls get 3 life, minion trolls get 1
                revive_life = 3 if m.max_life > 1 else 1
                m.life = revive_life
                messages.append(
                    f"{m.name} regenerates and revives with {revive_life} life! (roll {roll})"
                )
            else:
                m._chopped = True  # Mark as properly dead
                messages.append(
                    f"{m.name} stays dead. (regeneration roll {roll})"
                )
        return messages

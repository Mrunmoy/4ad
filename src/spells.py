"""Spell system for 4AD."""
from dataclasses import dataclass, field
from typing import List, Optional, Union
from src.dice import explosive_six, roll_d6


# Spell restriction tags
NO_UNDEAD = "no_undead"
NO_DRAGONS = "no_dragons"
NO_DEMONS = "no_demons"
NO_BARBARIAN_TARGET = "no_barbarian_target"


@dataclass
class Spell:
    """Definition of a spell."""
    name: str
    can_target_boss: bool
    can_target_minions: bool
    is_area: bool = False
    requires_roll: bool = True
    restrictions: List[str] = field(default_factory=list)


# The six canonical spells
SPELLS = {
    "Blessing": Spell(
        name="Blessing",
        can_target_boss=True,
        can_target_minions=True,
        is_area=False,
        requires_roll=False,
        restrictions=[],
    ),
    "Fireball": Spell(
        name="Fireball",
        can_target_boss=True,
        can_target_minions=True,
        is_area=True,
        requires_roll=True,
        restrictions=[NO_DRAGONS],
    ),
    "Lightning Bolt": Spell(
        name="Lightning Bolt",
        can_target_boss=True,
        can_target_minions=True,
        is_area=False,
        requires_roll=True,
        restrictions=[],
    ),
    "Sleep": Spell(
        name="Sleep",
        can_target_boss=True,
        can_target_minions=True,
        is_area=True,
        requires_roll=True,
        restrictions=[NO_UNDEAD, NO_DRAGONS, NO_DEMONS],
    ),
    "Escape": Spell(
        name="Escape",
        can_target_boss=False,
        can_target_minions=False,
        is_area=False,
        requires_roll=False,
        restrictions=[],
    ),
    "Protect": Spell(
        name="Protect",
        can_target_boss=False,
        can_target_minions=False,
        is_area=False,
        requires_roll=False,
        restrictions=[NO_BARBARIAN_TARGET],
    ),
}


@dataclass
class SpellResult:
    """Result of casting a spell."""
    success: bool
    caster: str
    spell: str
    targets_affected: List[str] = field(default_factory=list)
    damage_dealt: int = 0
    minions_killed: int = 0
    description: str = ""
    escaped: bool = False
    protect_target: str = ""
    condition_removed: str = ""


class SpellCaster:
    """Handles spell casting logic."""

    @staticmethod
    def cast_spell(caster, spell_name: str, targets=None, game_state=None,
                   force_rolls: List[int] = None) -> SpellResult:
        """
        Cast a spell.

        Args:
            caster: Character casting the spell
            spell_name: Name of the spell
            targets: Monster or list of monsters (for offensive spells),
                     or Character (for Blessing/Protect on ally)
            game_state: Optional dict with extra context
            force_rolls: For testing -- forced dice rolls

        Returns:
            SpellResult with outcome details
        """
        if spell_name not in SPELLS:
            return SpellResult(
                success=False, caster=caster.name, spell=spell_name,
                description=f"Unknown spell: {spell_name}"
            )

        spell = SPELLS[spell_name]

        # Check if caster can cast this spell
        if not caster.can_cast(spell_name):
            return SpellResult(
                success=False, caster=caster.name, spell=spell_name,
                description=f"{caster.name} cannot cast {spell_name}"
            )

        # Check remaining spell slots
        if not caster.use_spell(spell_name):
            return SpellResult(
                success=False, caster=caster.name, spell=spell_name,
                description=f"{caster.name} has no spell slots remaining"
            )

        # Enforce NO_BARBARIAN_TARGET restriction
        if NO_BARBARIAN_TARGET in spell.restrictions and targets is not None:
            from src.character import Barbarian
            check_target = targets[0] if isinstance(targets, list) else targets
            if isinstance(check_target, Barbarian):
                return SpellResult(
                    success=False, caster=caster.name, spell=spell_name,
                    description=f"{spell_name} cannot target a barbarian"
                )

        # Enforce spell restrictions against targets
        # Block only when ALL living monster targets are immune
        if spell.restrictions and targets is not None:
            from src.monster import Monster
            target_list = targets if isinstance(targets, list) else [targets]
            living_monsters = [t for t in target_list
                               if isinstance(t, Monster) and not t.is_dead()]
            if living_monsters:
                def _all_restricted(attr):
                    return all(getattr(t, attr, False) for t in living_monsters)

                blocked_reasons = []
                for restriction in spell.restrictions:
                    if restriction == NO_UNDEAD and _all_restricted("is_undead"):
                        blocked_reasons.append("undead")
                    if restriction == NO_DRAGONS and _all_restricted("is_dragon"):
                        blocked_reasons.append("dragons")
                    if restriction == NO_DEMONS and _all_restricted("is_demon"):
                        blocked_reasons.append("demons")
                if blocked_reasons:
                    reason = "/".join(blocked_reasons)
                    return SpellResult(
                        success=False, caster=caster.name, spell=spell_name,
                        description=f"{spell_name} has no effect on {reason}"
                    )

        # Dispatch to specific spell handler
        handler = {
            "Blessing": SpellCaster._cast_blessing,
            "Fireball": SpellCaster._cast_fireball,
            "Lightning Bolt": SpellCaster._cast_lightning_bolt,
            "Sleep": SpellCaster._cast_sleep,
            "Escape": SpellCaster._cast_escape,
            "Protect": SpellCaster._cast_protect,
        }[spell_name]

        return handler(caster, targets, force_rolls)

    @staticmethod
    def _cast_blessing(caster, target, force_rolls) -> SpellResult:
        """
        Blessing: Remove curse, petrification, or other negative conditions
        from a character. Can also force undead/demon reroll (not implemented
        in this handler -- handled in combat flow).
        """
        from src.character import Character

        if target is None:
            return SpellResult(
                success=False, caster=caster.name, spell="Blessing",
                description="No target specified for Blessing"
            )

        # Blessing on an ally character
        if isinstance(target, Character):
            removed = []
            if target.cursed:
                target.cursed = False
                removed.append("curse")
            if target.petrified:
                target.petrified = False
                removed.append("petrification")
            # Note: Blessing does NOT cure poison. Only Cleric Healing cures poison.

            if removed:
                conditions = ", ".join(removed)
                return SpellResult(
                    success=True, caster=caster.name, spell="Blessing",
                    targets_affected=[target.name],
                    condition_removed=conditions,
                    description=f"{caster.name} casts Blessing on {target.name}, removing {conditions}"
                )
            else:
                return SpellResult(
                    success=True, caster=caster.name, spell="Blessing",
                    targets_affected=[target.name],
                    description=f"{caster.name} casts Blessing on {target.name} (no conditions to remove)"
                )

        # Blessing on undead/demon enemy -- force reroll
        from src.monster import Monster
        if isinstance(target, Monster) and (target.is_undead or target.is_demon):
            return SpellResult(
                success=True, caster=caster.name, spell="Blessing",
                targets_affected=[target.name],
                description=f"{caster.name} casts Blessing, forcing {target.name} to reroll"
            )

        # Invalid target type
        return SpellResult(
            success=False, caster=caster.name, spell="Blessing",
            description="Blessing can only target a party member or an undead/demon enemy"
        )

    @staticmethod
    def _cast_fireball(caster, targets, force_rolls) -> SpellResult:
        """
        Fireball: Area attack.
        vs Minions: kills (roll - monster_level) minions, minimum 1 on hit.
        vs Bosses: if roll >= level, deals 2 damage (1 for demons).
        Does NOT affect dragons (is_dragon=True are immune).
        """
        from src.monster import Minion, Boss

        if targets is None:
            return SpellResult(
                success=False, caster=caster.name, spell="Fireball",
                description="No targets for Fireball"
            )

        if not isinstance(targets, list):
            targets = [targets]

        # Roll spell attack
        if force_rolls:
            dice_result = explosive_six(force_rolls=force_rolls)
        else:
            dice_result = explosive_six()

        total = dice_result.total + caster.level
        affected = []
        total_damage = 0
        total_minions_killed = 0

        # Separate minions and bosses
        living_minions = [t for t in targets if isinstance(t, Minion)
                         and not t.is_dead() and not t.is_dragon]
        living_bosses = [t for t in targets if isinstance(t, Boss)
                        and not t.is_dead() and not t.is_dragon]

        # Process minion group
        if living_minions:
            sample_level = living_minions[0].level
            if total >= sample_level:
                max_kills = max(1, total - sample_level)
                for minion in living_minions:
                    if total_minions_killed >= max_kills:
                        break
                    minion.take_damage(1)
                    total_minions_killed += 1
                    affected.append(minion.name)
                total_damage += total_minions_killed

        # Process bosses
        for boss in living_bosses:
            if total >= boss.level:
                dmg = 1 if boss.is_demon else 2
                boss.take_damage(dmg)
                total_damage += dmg
                affected.append(boss.name)

        desc = f"{caster.name} casts Fireball (roll {total})"
        if total_minions_killed > 0:
            desc += f", killing {total_minions_killed} minions"
        if living_bosses and any(b.name in affected for b in living_bosses):
            boss_dmg = total_damage - total_minions_killed
            if boss_dmg > 0:
                desc += f", dealing {boss_dmg} damage"
        if not affected:
            desc += ", but it has no effect"

        return SpellResult(
            success=len(affected) > 0,
            caster=caster.name,
            spell="Fireball",
            targets_affected=affected,
            damage_dealt=total_damage,
            minions_killed=total_minions_killed,
            description=desc,
        )

    @staticmethod
    def _cast_lightning_bolt(caster, target, force_rolls) -> SpellResult:
        """
        Lightning Bolt: Single target.
        vs Minions: kills exactly 1 if hit.
        vs Bosses: deals 2 damage if hit.
        Works on everything including dragons and undead.
        """
        from src.monster import Minion, Boss

        if target is None:
            return SpellResult(
                success=False, caster=caster.name, spell="Lightning Bolt",
                description="No target for Lightning Bolt"
            )

        # If given a list, pick first living target
        if isinstance(target, list):
            target = next((t for t in target if not t.is_dead()), None)
            if target is None:
                return SpellResult(
                    success=False, caster=caster.name, spell="Lightning Bolt",
                    description="No living targets"
                )

        if force_rolls:
            dice_result = explosive_six(force_rolls=force_rolls)
        else:
            dice_result = explosive_six()

        total = dice_result.total + caster.level

        if total >= target.level:
            if isinstance(target, Minion):
                target.take_damage(1)
                return SpellResult(
                    success=True, caster=caster.name, spell="Lightning Bolt",
                    targets_affected=[target.name], damage_dealt=1,
                    minions_killed=1,
                    description=f"{caster.name} casts Lightning Bolt (roll {total}), killing {target.name}"
                )
            elif isinstance(target, Boss):
                target.take_damage(2)
                return SpellResult(
                    success=True, caster=caster.name, spell="Lightning Bolt",
                    targets_affected=[target.name], damage_dealt=2,
                    description=f"{caster.name} casts Lightning Bolt (roll {total}), dealing 2 damage to {target.name}"
                )

        return SpellResult(
            success=False, caster=caster.name, spell="Lightning Bolt",
            description=f"{caster.name} casts Lightning Bolt (roll {total}), but misses {target.name}"
        )

    @staticmethod
    def _cast_sleep(caster, targets, force_rolls) -> SpellResult:
        """
        Sleep: Area effect.
        vs Minions: puts (roll - monster_level) minions to sleep (count as slain).
        vs Bosses: if roll >= level, boss falls asleep (defeated).
        Does NOT work on undead, dragons, or demons.
        """
        from src.monster import Minion, Boss

        if targets is None:
            return SpellResult(
                success=False, caster=caster.name, spell="Sleep",
                description="No targets for Sleep"
            )

        if not isinstance(targets, list):
            targets = [targets]

        # Type guard: skip non-monster targets that lack monster attributes
        targets = [t for t in targets if hasattr(t, 'is_undead')]

        if not targets:
            return SpellResult(
                success=False, caster=caster.name, spell="Sleep",
                description=f"{caster.name} casts Sleep, but there are no valid targets"
            )

        # Check immunity
        immune_targets = [t for t in targets if t.is_undead or t.is_dragon or t.is_demon]
        if len(immune_targets) == len([t for t in targets if not t.is_dead()]):
            return SpellResult(
                success=False, caster=caster.name, spell="Sleep",
                description=f"{caster.name} casts Sleep, but the targets are immune"
            )

        if force_rolls:
            dice_result = explosive_six(force_rolls=force_rolls)
        else:
            dice_result = explosive_six()

        total = dice_result.total + caster.level
        affected = []
        minions_killed = 0

        for target in targets:
            if target.is_dead():
                continue
            if target.is_undead or target.is_dragon or target.is_demon:
                continue

            if isinstance(target, Boss):
                if total >= target.level:
                    # Boss falls asleep = defeated
                    target.take_damage(target.life)
                    affected.append(target.name)
                break  # Sleep one boss only

        # For minion groups
        if targets and all(isinstance(t, Minion) for t in targets):
            sample = next((t for t in targets if not t.is_dead() and not t.is_undead
                          and not t.is_dragon and not t.is_demon), None)
            if sample and total >= sample.level:
                max_sleep = max(1, total - sample.level)
                affected = []
                minions_killed = 0
                for target in targets:
                    if target.is_dead():
                        continue
                    if target.is_undead or target.is_dragon or target.is_demon:
                        continue
                    if minions_killed >= max_sleep:
                        break
                    target.take_damage(1)
                    minions_killed += 1
                    affected.append(target.name)

        desc = f"{caster.name} casts Sleep (roll {total})"
        if minions_killed > 0:
            desc += f", putting {minions_killed} minions to sleep"
        elif affected:
            desc += f", putting {', '.join(affected)} to sleep"
        else:
            desc += ", but it has no effect"

        return SpellResult(
            success=len(affected) > 0,
            caster=caster.name,
            spell="Sleep",
            targets_affected=affected,
            minions_killed=minions_killed,
            description=desc,
        )

    @staticmethod
    def _cast_escape(caster, targets, force_rolls) -> SpellResult:
        """
        Escape: Caster teleports to dungeon entrance.
        Automatic -- no roll needed.
        """
        return SpellResult(
            success=True,
            caster=caster.name,
            spell="Escape",
            targets_affected=[caster.name],
            escaped=True,
            description=f"{caster.name} casts Escape and teleports to the dungeon entrance"
        )

    @staticmethod
    def _cast_protect(caster, target, force_rolls) -> SpellResult:
        """
        Protect: Gives +1 to one character's defense rolls for the battle.
        Does not work on barbarians.
        """
        from src.character import Character

        if target is None:
            return SpellResult(
                success=False, caster=caster.name, spell="Protect",
                description="No target specified for Protect"
            )

        # Validate target is a single Character, not a list or Monster
        if isinstance(target, list):
            return SpellResult(
                success=False, caster=caster.name, spell="Protect",
                description="Protect targets a single party member, not a group"
            )

        if not isinstance(target, Character):
            return SpellResult(
                success=False, caster=caster.name, spell="Protect",
                description="Protect can only target a party member"
            )

        if target.class_type == "Barbarian":
            return SpellResult(
                success=False, caster=caster.name, spell="Protect",
                targets_affected=[target.name],
                description=f"Protect has no effect on {target.name} (barbarians reject magic)"
            )

        target.protected = True

        return SpellResult(
            success=True,
            caster=caster.name,
            spell="Protect",
            targets_affected=[target.name],
            protect_target=target.name,
            description=f"{caster.name} casts Protect on {target.name} (+1 defense for this battle)"
        )

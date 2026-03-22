"""Trap system for 4AD (rulebook p.62, design spec Section 10)."""
from dataclasses import dataclass, field
from typing import List, Optional, Tuple
import random

from src.dice import roll_d6


@dataclass
class Trap:
    """A dungeon trap."""
    name: str
    level: int
    trap_type: str  # "dart", "poison_gas", "trapdoor", "bear_trap", "spears", "stone_block"
    targets: str  # "random", "all", "leader", "last", "two_random"


@dataclass
class TrapResult:
    """Result of a trap encounter."""
    trap: Trap
    triggered: bool
    disarmed: bool
    disarmed_by: Optional[str] = None
    victims: List[Tuple] = field(default_factory=list)  # [(char_name, damage, special_effect)]
    description: str = ""


# Trap table (d6, design spec 10.1)
TRAP_TABLE = {
    1: lambda: Trap("Dart Trap", level=3, trap_type="dart", targets="random"),
    2: lambda: Trap("Poison Gas", level=3, trap_type="poison_gas", targets="all"),
    3: lambda: Trap("Trapdoor", level=4, trap_type="trapdoor", targets="random"),
    4: lambda: Trap("Bear Trap", level=3, trap_type="bear_trap", targets="random"),
    5: lambda: Trap("Spear Trap", level=5, trap_type="spears", targets="two_random"),
    6: lambda: Trap("Rolling Stone", level=5, trap_type="stone_block", targets="last"),
}


def generate_trap(force_roll: int = None) -> Trap:
    """Roll d6 to generate a trap from the trap table."""
    roll = force_roll if force_roll is not None else roll_d6()
    roll = max(1, min(6, roll))
    return TRAP_TABLE[roll]()


def _get_armor_bonus(character) -> int:
    """Get armor defense bonus from equipment."""
    bonus = 0
    equipment = [e.lower() for e in character.equipment]
    if "heavy armor" in equipment:
        bonus += 2
    elif "light armor" in equipment:
        bonus += 1
    if "shield" in equipment:
        bonus += 1
    return bonus


def _get_shield_bonus(character) -> int:
    """Get shield bonus only."""
    equipment = [e.lower() for e in character.equipment]
    if "shield" in equipment:
        return 1
    return 0


def _has_limping(character) -> bool:
    """Check if character has the limping status effect."""
    return getattr(character, 'limping', False)


def _apply_limping(character) -> None:
    """Apply the limping status effect to a character."""
    character.limping = True


def attempt_disarm(rogue, trap, force_roll: int = None) -> bool:
    """Attempt to disarm a trap using a rogue.

    Roll d6 + rogue's level >= trap level to disarm.
    Returns True if disarmed, False otherwise.
    The rogue must be alive and not petrified.
    """
    if rogue.is_dead() or getattr(rogue, 'petrified', False):
        return False

    roll = force_roll if force_roll is not None else roll_d6()
    total = roll + rogue.get_disarm_bonus()
    return total >= trap.level


def _pick_random_characters(party_chars, count: int):
    """Pick count random living characters from the party."""
    living = [c for c in party_chars if not c.is_dead()]
    if len(living) <= count:
        return list(living)
    return random.sample(living, count)


def _get_leader(party_chars):
    """Get the character leading marching order (lowest position)."""
    living = [c for c in party_chars if not c.is_dead()]
    if not living:
        return None
    return min(living, key=lambda c: c.position)


def _get_last(party_chars):
    """Get the last character in marching order (highest position)."""
    living = [c for c in party_chars if not c.is_dead()]
    if not living:
        return None
    return max(living, key=lambda c: c.position)


def _resolve_dart(trap, party_chars, force_roll: int = None) -> TrapResult:
    """Resolve a dart trap targeting one random character."""
    targets = _pick_random_characters(party_chars, 1)
    if not targets:
        return TrapResult(trap=trap, triggered=True, disarmed=False,
                          description="Dart fires but no one is hit.")

    char = targets[0]
    roll = force_roll if force_roll is not None else roll_d6()
    bonus = _get_armor_bonus(char)
    total = roll + bonus

    victims = []
    if total < trap.level:
        char.take_damage(1)
        victims.append((char.name, 1, None))
        desc = f"A dart strikes {char.name}! (rolled {roll}+{bonus}={total} vs {trap.level})"
    else:
        desc = f"{char.name} dodges a dart! (rolled {roll}+{bonus}={total} vs {trap.level})"

    return TrapResult(trap=trap, triggered=True, disarmed=False,
                      victims=victims, description=desc)


def _resolve_poison_gas(trap, party_chars, force_rolls: List[int] = None) -> TrapResult:
    """Resolve poison gas trap targeting ALL characters. No armor bonus."""
    living = [c for c in party_chars if not c.is_dead()]
    victims = []
    descriptions = []

    for i, char in enumerate(living):
        roll = force_rolls[i] if force_rolls and i < len(force_rolls) else roll_d6()
        # No armor/shield bonus for gas
        total = roll

        if total < trap.level:
            char.take_damage(1)
            char.poisoned = True
            victims.append((char.name, 1, "poisoned"))
            descriptions.append(f"{char.name} is poisoned! (rolled {total} vs {trap.level})")
        else:
            descriptions.append(f"{char.name} resists the gas (rolled {total} vs {trap.level})")

    desc = "Poison gas fills the room! " + " ".join(descriptions)
    return TrapResult(trap=trap, triggered=True, disarmed=False,
                      victims=victims, description=desc)


def _resolve_trapdoor(trap, party_chars, force_roll: int = None) -> TrapResult:
    """Resolve a trapdoor/pit trap targeting a random character."""
    targets = _pick_random_characters(party_chars, 1)
    if not targets:
        return TrapResult(trap=trap, triggered=True, disarmed=False,
                          description="Trapdoor opens but no one falls in.")

    char = targets[0]
    roll = force_roll if force_roll is not None else roll_d6()

    # Modifiers per design spec
    modifier = 0
    equipment = [e.lower() for e in char.equipment]
    if "heavy armor" in equipment:
        modifier += 1  # Heavy armor: +1 per design spec table
    elif "light armor" in equipment:
        modifier -= 1  # Light armor: -1

    if char.class_type in ("Halfling", "Elf"):
        modifier += 1
    if char.class_type == "Rogue":
        modifier += char.level

    # Limping penalty
    if _has_limping(char):
        modifier -= 2

    total = roll + modifier
    victims = []

    if total < trap.level:
        # Check if character is alone (only living party member)
        living_count = sum(1 for c in party_chars if not c.is_dead())
        if living_count <= 1:
            # Alone: set damage to full life (instant death)
            damage = char.life
            char.life = 0
            victims.append((char.name, damage, "death_alone"))
            desc = (f"{char.name} falls through a trapdoor alone and perishes! "
                    f"(rolled {roll}{modifier:+d}={total} vs {trap.level})")
        else:
            char.take_damage(1)
            char.separated = True
            victims.append((char.name, 1, "separated"))
            desc = (f"{char.name} falls through a trapdoor! "
                    f"(rolled {roll}{modifier:+d}={total} vs {trap.level}) "
                    f"Lost 1 life, separated from party!")
    else:
        desc = (f"{char.name} avoids the trapdoor! "
                f"(rolled {roll}{modifier:+d}={total} vs {trap.level})")

    return TrapResult(trap=trap, triggered=True, disarmed=False,
                      victims=victims, description=desc)


def _resolve_bear_trap(trap, party_chars, force_roll: int = None) -> TrapResult:
    """Resolve a bear trap targeting the character leading marching order (position 1).

    Save: d6 + mods >= 3. Halfling +1, Rogue +level.
    Effect: lose 1 life + limping (-1 attack, -1 defense, -2 vs future traps/trapdoors).
    """
    char = _get_leader(party_chars)
    if not char:
        return TrapResult(trap=trap, triggered=True, disarmed=False,
                          description="Bear trap snaps but no one is caught.")

    roll = force_roll if force_roll is not None else roll_d6()

    modifier = 0
    if char.class_type == "Halfling":
        modifier += 1
    if char.class_type == "Rogue":
        modifier += char.level

    # Limping penalty: -2 vs traps/trapdoors
    if _has_limping(char):
        modifier -= 2

    total = roll + modifier
    victims = []

    if total < trap.level:
        char.take_damage(1)
        _apply_limping(char)
        char.attack -= 1
        char.defense -= 1
        victims.append((char.name, 1, "limping"))
        desc = (f"{char.name} (position {char.position}) is caught in a bear trap! "
                f"(rolled {roll}{modifier:+d}={total} vs {trap.level}) "
                f"Lost 1 life, now limping (-1 attack, -1 defense, -2 vs traps).")
    else:
        desc = (f"{char.name} (position {char.position}) avoids the bear trap! "
                f"(rolled {roll}{modifier:+d}={total} vs {trap.level})")

    return TrapResult(trap=trap, triggered=True, disarmed=False,
                      victims=victims, description=desc)


def _resolve_spears(trap, party_chars, force_rolls: List[int] = None) -> TrapResult:
    """Resolve spear trap targeting two random characters."""
    targets = _pick_random_characters(party_chars, 2)
    if not targets:
        return TrapResult(trap=trap, triggered=True, disarmed=False,
                          description="Spears shoot from the walls but miss everyone.")

    victims = []
    descriptions = []

    for i, char in enumerate(targets):
        roll = force_rolls[i] if force_rolls and i < len(force_rolls) else roll_d6()
        bonus = _get_armor_bonus(char)
        total = roll + bonus

        if total < trap.level:
            char.take_damage(1)
            victims.append((char.name, 1, None))
            descriptions.append(
                f"{char.name} is hit by a spear! (rolled {roll}+{bonus}={total} vs {trap.level})")
        else:
            descriptions.append(
                f"{char.name} dodges a spear! (rolled {roll}+{bonus}={total} vs {trap.level})")

    desc = "Spears shoot from the walls! " + " ".join(descriptions)
    return TrapResult(trap=trap, triggered=True, disarmed=False,
                      victims=victims, description=desc)


def _resolve_stone_block(trap, party_chars, force_roll: int = None) -> TrapResult:
    """Resolve rolling stone trap targeting last character in marching order.
    Shield bonus applies but NOT armor bonus.
    """
    char = _get_last(party_chars)
    if not char:
        return TrapResult(trap=trap, triggered=True, disarmed=False,
                          description="A stone block falls but no one is underneath.")

    roll = force_roll if force_roll is not None else roll_d6()
    # Shield applies, armor does NOT
    bonus = _get_shield_bonus(char)
    total = roll + bonus

    victims = []
    if total < trap.level:
        char.take_damage(2)
        victims.append((char.name, 2, None))
        desc = (f"A giant stone block falls on {char.name}! "
                f"(rolled {roll}+{bonus}={total} vs {trap.level}) Lost 2 life!")
    else:
        desc = (f"{char.name} dodges the falling stone block! "
                f"(rolled {roll}+{bonus}={total} vs {trap.level})")

    return TrapResult(trap=trap, triggered=True, disarmed=False,
                      victims=victims, description=desc)


# Dispatch table for trap resolution
_TRAP_RESOLVERS = {
    "dart": _resolve_dart,
    "poison_gas": _resolve_poison_gas,
    "trapdoor": _resolve_trapdoor,
    "bear_trap": _resolve_bear_trap,
    "spears": _resolve_spears,
    "stone_block": _resolve_stone_block,
}


def trigger_trap(trap: Trap, party, force_roll=None, force_rolls=None) -> TrapResult:
    """Trigger a trap on the party.

    Args:
        trap: The trap to trigger.
        party: A Party object (has .characters) or a list of characters.
        force_roll: Force a specific roll (for single-target traps).
        force_rolls: Force specific rolls (for multi-target traps).

    Returns:
        TrapResult with full details.
    """
    # Accept either a Party object or a list of characters
    if hasattr(party, 'characters'):
        chars = party.characters
    elif hasattr(party, 'get_living_characters'):
        chars = party.get_living_characters()
    else:
        chars = list(party)

    resolver = _TRAP_RESOLVERS.get(trap.trap_type)
    if not resolver:
        return TrapResult(trap=trap, triggered=False, disarmed=False,
                          description=f"Unknown trap type: {trap.trap_type}")

    # Pass the appropriate forced roll(s)
    if trap.trap_type in ("poison_gas", "spears"):
        return resolver(trap, chars, force_rolls=force_rolls)
    else:
        return resolver(trap, chars, force_roll=force_roll)


def handle_trap_encounter(trap: Trap, party, force_disarm_roll: int = None,
                          force_trap_roll=None, force_trap_rolls=None) -> TrapResult:
    """Full trap encounter: rogue disarm attempt, then trigger if failed.

    Args:
        trap: The trap encountered.
        party: Party object or list of characters.
        force_disarm_roll: Force a specific disarm roll (for testing).
        force_trap_roll: Force a specific trap save roll (for testing).
        force_trap_rolls: Force specific trap save rolls for multi-target (for testing).

    Returns:
        TrapResult with disarm or trigger outcome.
    """
    if hasattr(party, 'characters'):
        chars = party.characters
    elif hasattr(party, 'get_living_characters'):
        chars = party.get_living_characters()
    else:
        chars = list(party)

    # Check for a rogue in the party who can attempt disarm
    rogue = None
    for c in chars:
        if (c.class_type == "Rogue" and not c.is_dead()
                and not getattr(c, 'petrified', False)):
            rogue = c
            break

    if rogue:
        disarmed = attempt_disarm(rogue, trap, force_roll=force_disarm_roll)
        if disarmed:
            return TrapResult(
                trap=trap, triggered=False, disarmed=True,
                disarmed_by=rogue.name,
                description=f"{rogue.name} disarms the {trap.name}!"
            )

    # Trap triggers
    result = trigger_trap(trap, chars, force_roll=force_trap_roll,
                          force_rolls=force_trap_rolls)
    return result

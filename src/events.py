"""Special Features and Special Events for 4AD (design spec Section 11)."""
from dataclasses import dataclass, field
from typing import Dict, List, Optional
import random

from src.dice import roll_d6
from src.traps import generate_trap, handle_trap_encounter


@dataclass
class EventResult:
    """Result of a special feature or event."""
    event_type: str
    description: str
    player_choices: Optional[List[str]] = None
    effects: Optional[Dict] = field(default_factory=dict)
    requires_combat: bool = False
    monster_data: Optional[Dict] = None


# ---------------------------------------------------------------------------
# Special Features (d6, design spec 11.1)
# ---------------------------------------------------------------------------

def generate_special_feature(force_roll: int = None) -> EventResult:
    """Roll d6 to determine which special feature is in the room."""
    roll = force_roll if force_roll is not None else roll_d6()
    roll = max(1, min(6, roll))
    return _FEATURE_GENERATORS[roll]()


def _gen_fountain() -> EventResult:
    return EventResult(
        event_type="fountain",
        description="A crystal-clear fountain bubbles in the center of the room.",
        player_choices=["drink", "leave"],
        effects={"type": "fountain"},
    )


def _gen_blessed_temple() -> EventResult:
    return EventResult(
        event_type="blessed_temple",
        description="A blessed temple radiates divine light.",
        player_choices=["pray", "leave"],
        effects={"type": "blessed_temple"},
    )


def _gen_armory() -> EventResult:
    # Stock: d3 hand weapons, d3-1 shields (min 0), 50% light armor
    hand_weapons = random.randint(1, 3)
    shields = max(0, random.randint(1, 3) - 1)
    has_light_armor = random.random() < 0.5
    stock = {"hand_weapons": hand_weapons, "shields": shields,
             "light_armor": has_light_armor}
    return EventResult(
        event_type="armory",
        description="An old armory with weapons still on the racks.",
        player_choices=["swap_equipment", "leave"],
        effects={"type": "armory", "stock": stock},
    )


def _gen_cursed_altar() -> EventResult:
    return EventResult(
        event_type="cursed_altar",
        description="A dark altar pulses with malevolent energy!",
        player_choices=["approach", "leave"],
        effects={"type": "cursed_altar"},
    )


def _gen_statue() -> EventResult:
    return EventResult(
        event_type="statue",
        description="An ancient statue stands in the room, eyes seeming to follow you.",
        player_choices=["touch", "leave"],
        effects={"type": "statue"},
    )


def _gen_puzzle_room() -> EventResult:
    puzzle_level = roll_d6()
    return EventResult(
        event_type="puzzle_room",
        description=f"A puzzle box sits on a pedestal (difficulty {puzzle_level}).",
        player_choices=["attempt", "leave"],
        effects={"type": "puzzle_room", "puzzle_level": puzzle_level},
    )


_FEATURE_GENERATORS = {
    1: _gen_fountain,
    2: _gen_blessed_temple,
    3: _gen_armory,
    4: _gen_cursed_altar,
    5: _gen_statue,
    6: _gen_puzzle_room,
}


_VALID_FEATURE_CHOICES = {
    "fountain": {"drink", "leave"},
    "blessed_temple": {"pray", "leave"},
    "armory": {"swap_equipment", "leave"},
    "cursed_altar": {"approach", "leave"},
    "statue": {"touch", "leave"},
    "puzzle_room": {"attempt", "leave"},
}


def resolve_feature(feature_result: EventResult, party, choice: str,
                    force_roll: int = None,
                    fountain_tracker: dict = None) -> EventResult:
    """Resolve a special feature based on player choice.

    Args:
        feature_result: The EventResult from generate_special_feature.
        party: Party object or list of characters.
        choice: Player's chosen action.
        force_roll: Force a specific d6 roll (for testing).

    Returns:
        Updated EventResult with resolution.
    """
    feature_type = feature_result.event_type
    valid = _VALID_FEATURE_CHOICES.get(feature_type)
    if valid is not None and choice not in valid:
        return EventResult(
            event_type=feature_type,
            description="Invalid choice.",
            effects={"error": "Invalid choice"},
        )

    chars = _get_chars(party)

    if feature_type == "fountain":
        return _resolve_fountain(chars, choice, force_roll, fountain_tracker)
    elif feature_type == "blessed_temple":
        return _resolve_blessed_temple(chars, choice)
    elif feature_type == "armory":
        return _resolve_armory(feature_result, chars, choice)
    elif feature_type == "cursed_altar":
        return _resolve_cursed_altar(chars, choice)
    elif feature_type == "statue":
        return _resolve_statue(chars, choice, force_roll)
    elif feature_type == "puzzle_room":
        return _resolve_puzzle_room(feature_result, chars, choice, force_roll)

    return EventResult(event_type=feature_type,
                       description="Nothing happens.",
                       effects={})


def _resolve_fountain(chars, choice, force_roll=None, fountain_tracker=None) -> EventResult:
    if choice == "leave":
        return EventResult(event_type="fountain",
                           description="You leave the fountain alone.",
                           effects={})

    # One-use-per-adventure enforcement
    drink_count = 0
    if fountain_tracker is not None:
        drink_count = fountain_tracker.get("fountain_drinks", 0)

    if drink_count >= 2:
        return EventResult(event_type="fountain",
                           description="The fountain has run dry.",
                           effects={"dry": True})

    wounded = [c for c in chars if not c.is_dead() and c.life < c.max_life]
    if not wounded:
        wounded = [c for c in chars if not c.is_dead()]
    if not wounded:
        return EventResult(event_type="fountain",
                           description="No one can drink.",
                           effects={})

    char = wounded[0]

    if drink_count == 0:
        heal_amount = force_roll if force_roll is not None else roll_d6()
        old_life = char.life
        char.heal(heal_amount)
        actual_heal = char.life - old_life
        if fountain_tracker is not None:
            fountain_tracker["fountain_drinks"] = 1
        return EventResult(
            event_type="fountain",
            description=f"{char.name} drinks from the fountain and heals {actual_heal} life!",
            effects={"healed": [(char.name, actual_heal)]},
        )
    else:
        risk_roll = force_roll if force_roll is not None else roll_d6()
        if fountain_tracker is not None:
            fountain_tracker["fountain_drinks"] = 2
        if risk_roll == 1:
            char.poisoned = True
            return EventResult(
                event_type="fountain",
                description=f"{char.name} drinks and is POISONED! (rolled {risk_roll})",
                effects={"poisoned": char.name},
            )
        return EventResult(
            event_type="fountain",
            description=f"{char.name} drinks but nothing happens. (rolled {risk_roll})",
            effects={"nothing": True},
        )


def _resolve_blessed_temple(chars, choice) -> EventResult:
    if choice == "leave":
        return EventResult(event_type="blessed_temple",
                           description="You pass through the temple quietly.",
                           effects={})

    # Choose first living character to receive blessing
    living = [c for c in chars if not c.is_dead()]
    if not living:
        return EventResult(event_type="blessed_temple",
                           description="No one can receive the blessing.",
                           effects={})

    char = living[0]
    # Also cures curse
    was_cursed = char.cursed
    char.cursed = False
    char.blessed_temple_bonus = True

    desc = f"{char.name} receives a blessing (+1 attack vs undead/demons)."
    if was_cursed:
        desc += f" {char.name}'s curse is lifted!"

    return EventResult(
        event_type="blessed_temple",
        description=desc,
        effects={"blessed": char.name, "curse_cured": was_cursed},
    )


def _resolve_armory(feature_result, chars, choice) -> EventResult:
    if choice == "leave":
        return EventResult(event_type="armory",
                           description="You leave the armory untouched.",
                           effects={})

    stock = feature_result.effects.get("stock", {})
    return EventResult(
        event_type="armory",
        description="Characters can swap weapons and armor from the armory.",
        effects={"type": "armory", "stock": stock, "available": True},
    )


def _resolve_cursed_altar(chars, choice) -> EventResult:
    if choice == "leave":
        return EventResult(event_type="cursed_altar",
                           description="You wisely avoid the altar.",
                           effects={})

    # Random character is cursed
    living = [c for c in chars if not c.is_dead()]
    if not living:
        return EventResult(event_type="cursed_altar",
                           description="The altar's power fades with no targets.",
                           effects={})

    victim = random.choice(living)
    victim.cursed = True

    return EventResult(
        event_type="cursed_altar",
        description=f"{victim.name} is CURSED by the dark altar! (-1 on all defense rolls)",
        effects={"cursed": victim.name},
    )


def _resolve_statue(chars, choice, force_roll=None) -> EventResult:
    if choice == "leave":
        return EventResult(event_type="statue",
                           description="You leave the statue alone.",
                           effects={})

    roll = force_roll if force_roll is not None else roll_d6()

    if roll <= 2:
        # Boss encounter - statue awakens
        return EventResult(
            event_type="statue",
            description="The statue awakens! It attacks!",
            requires_combat=True,
            monster_data={"name": "Animated Statue", "level": 4, "life": 6,
                          "immune_to_spells": True, "treasure": "3d6x10"},
            effects={"roll": roll, "outcome": "boss"},
        )
    elif roll <= 4:
        # Treasure
        gold = sum(random.randint(1, 6) for _ in range(3)) * 10
        return EventResult(
            event_type="statue",
            description=f"The statue crumbles, revealing {gold} gold inside!",
            effects={"roll": roll, "outcome": "treasure", "gold": gold},
        )
    else:
        # Clue
        return EventResult(
            event_type="statue",
            description="The statue whispers a clue to you...",
            effects={"roll": roll, "outcome": "clue"},
        )


def _resolve_puzzle_room(feature_result, chars, choice, force_roll=None) -> EventResult:
    if choice == "leave":
        return EventResult(event_type="puzzle_room",
                           description="You leave the puzzle box alone.",
                           effects={})

    puzzle_level = feature_result.effects.get("puzzle_level", 4)
    roll = force_roll if force_roll is not None else roll_d6()

    # Find best solver: wizards and rogues add level, elves add +1
    best_solver = None
    best_bonus = 0
    living = [c for c in chars if not c.is_dead()]

    for c in living:
        bonus = 0
        if c.class_type in ("Wizard", "Rogue"):
            bonus = c.level
        elif c.class_type == "Elf":
            bonus = 1
        if bonus > best_bonus or best_solver is None:
            best_bonus = bonus
            best_solver = c

    total = roll + best_bonus

    if total >= puzzle_level:
        return EventResult(
            event_type="puzzle_room",
            description=(f"{'%s solves' % best_solver.name if best_solver else 'Someone solves'} "
                         f"the puzzle! (rolled {roll}+{best_bonus}={total} vs {puzzle_level}) "
                         f"Treasure found!"),
            effects={"solved": True, "solver": best_solver.name if best_solver else None,
                     "treasure": True},
        )
    else:
        # Failure: lose 1 life
        if best_solver:
            best_solver.take_damage(1)
        return EventResult(
            event_type="puzzle_room",
            description=(f"{'%s fails' % best_solver.name if best_solver else 'No one can solve'} "
                         f"the puzzle! (rolled {roll}+{best_bonus}={total} vs {puzzle_level}) "
                         f"A trap springs! Lost 1 life."),
            effects={"solved": False, "solver": best_solver.name if best_solver else None,
                     "damage": 1},
        )


# ---------------------------------------------------------------------------
# Special Events (d6, design spec 11.2)
# ---------------------------------------------------------------------------

def generate_special_event(force_roll: int = None) -> EventResult:
    """Roll d6 to determine which special event occurs."""
    roll = force_roll if force_roll is not None else roll_d6()
    roll = max(1, min(6, roll))
    return _EVENT_GENERATORS[roll]()


def _gen_ghost() -> EventResult:
    return EventResult(
        event_type="ghost",
        description="A spectral figure materializes before you!",
        effects={"type": "ghost", "level": 4},
    )


def _gen_wandering_monsters() -> EventResult:
    return EventResult(
        event_type="wandering_monsters",
        description="Wandering monsters appear!",
        requires_combat=True,
        effects={"type": "wandering_monsters"},
    )


def _gen_lady_in_white() -> EventResult:
    return EventResult(
        event_type="lady_in_white",
        description="A ghostly lady in white appears and offers you a quest.",
        player_choices=["accept", "refuse"],
        effects={"type": "lady_in_white"},
    )


def _gen_trap_event() -> EventResult:
    return EventResult(
        event_type="trap_event",
        description="It's a trap!",
        effects={"type": "trap_event"},
    )


def _gen_wandering_healer() -> EventResult:
    return EventResult(
        event_type="wandering_healer",
        description="A wandering healer offers aid. (10gp per life point, 20gp to cure poison)",
        player_choices=["buy_healing", "leave"],
        effects={"type": "wandering_healer", "price_per_hp": 10, "poison_cure_price": 20},
    )


def _gen_wandering_alchemist() -> EventResult:
    stock_potions = random.randint(1, 3)
    stock_poison = random.randint(1, 3)
    stock_bandage = random.randint(1, 3)
    return EventResult(
        event_type="wandering_alchemist",
        description="A wandering alchemist has wares to sell.",
        player_choices=["buy", "leave"],
        effects={"type": "wandering_alchemist",
                 "stock": {"potions": stock_potions, "blade_poison": stock_poison,
                           "bandages": stock_bandage},
                 "prices": {"potion": 50, "blade_poison": 30, "bandage": 3}},
    )


_EVENT_GENERATORS = {
    1: _gen_ghost,
    2: _gen_wandering_monsters,
    3: _gen_lady_in_white,
    4: _gen_trap_event,
    5: _gen_wandering_healer,
    6: _gen_wandering_alchemist,
}


_VALID_EVENT_CHOICES = {
    "ghost": None,
    "wandering_monsters": None,
    "lady_in_white": {"accept", "refuse"},
    "trap_event": None,
    "wandering_healer": {"buy_healing", "leave"},
    "wandering_alchemist": {"buy", "leave"},
}


def resolve_event(event_result: EventResult, party, choice: str = None,
                  force_roll: int = None, force_rolls: List[int] = None,
                  party_gold: int = None) -> EventResult:
    """Resolve a special event based on player choice.

    Args:
        event_result: The EventResult from generate_special_event.
        party: Party object or list of characters.
        choice: Player's chosen action (if applicable).
        force_roll: Force a specific d6 roll (for testing).
        force_rolls: Force specific d6 rolls for multi-target (for testing).
        party_gold: Available gold for vendor purchases.

    Returns:
        Updated EventResult with resolution.
    """
    event_type = event_result.event_type
    valid = _VALID_EVENT_CHOICES.get(event_type)
    if valid is not None and choice not in valid:
        return EventResult(
            event_type=event_type,
            description="Invalid choice.",
            effects={"error": "Invalid choice"},
        )

    chars = _get_chars(party)

    if event_type == "ghost":
        return _resolve_ghost(chars, force_rolls)
    elif event_type == "wandering_monsters":
        return _resolve_wandering_monsters(force_roll)
    elif event_type == "lady_in_white":
        return _resolve_lady_in_white(choice)
    elif event_type == "trap_event":
        return _resolve_trap_event(party, force_roll)
    elif event_type == "wandering_healer":
        return _resolve_wandering_healer(event_result, chars, choice, force_roll,
                                         party_gold=party_gold)
    elif event_type == "wandering_alchemist":
        return _resolve_wandering_alchemist(event_result, chars, choice)

    return EventResult(event_type=event_type,
                       description="Nothing happens.",
                       effects={})


def _resolve_ghost(chars, force_rolls=None) -> EventResult:
    """All characters save vs level 4. Clerics add level. Fail: lose 1 life."""
    living = [c for c in chars if not c.is_dead()]
    ghost_level = 4
    victims = []
    descriptions = []

    for i, char in enumerate(living):
        roll = force_rolls[i] if force_rolls and i < len(force_rolls) else roll_d6()
        bonus = 0
        if char.class_type == "Cleric":
            bonus = char.level
        total = roll + bonus

        if total < ghost_level:
            char.take_damage(1)
            victims.append(char.name)
            descriptions.append(
                f"{char.name} is terrified! (rolled {roll}+{bonus}={total} vs {ghost_level}) Lost 1 life.")
        else:
            descriptions.append(
                f"{char.name} resists the ghost. (rolled {roll}+{bonus}={total} vs {ghost_level})")

    desc = "A ghost appears! " + " ".join(descriptions)
    return EventResult(
        event_type="ghost",
        description=desc,
        effects={"victims": victims, "ghost_level": ghost_level},
    )


def _resolve_wandering_monsters(force_roll=None) -> EventResult:
    """Roll on the minion table for wandering monsters."""
    roll = force_roll if force_roll is not None else roll_d6()

    return EventResult(
        event_type="wandering_monsters",
        description="Wandering monsters attack from behind!",
        requires_combat=True,
        monster_data={"table": "minions", "roll": roll},
        effects={"surprise": True},
    )


def _resolve_lady_in_white(choice) -> EventResult:
    if choice == "refuse":
        return EventResult(
            event_type="lady_in_white",
            description="The Lady in White fades away, never to return.",
            effects={"quest_offered": False},
        )

    # Accept quest
    return EventResult(
        event_type="lady_in_white",
        description="You accept the Lady's quest. She whispers instructions and vanishes.",
        effects={"quest_offered": True, "quest_accepted": True},
    )


def _resolve_trap_event(party, force_roll=None) -> EventResult:
    """Roll on trap table."""
    trap = generate_trap(force_roll=force_roll)
    result = handle_trap_encounter(trap, party)
    return EventResult(
        event_type="trap_event",
        description=f"Trap encountered: {result.description}",
        effects={"trap_result": {
            "trap_name": result.trap.name,
            "triggered": result.triggered,
            "disarmed": result.disarmed,
            "victims": result.victims,
        }},
    )


def _resolve_wandering_healer(event_result, chars, choice, force_roll=None,
                              party_gold: int = None) -> EventResult:
    if choice == "leave":
        return EventResult(
            event_type="wandering_healer",
            description="You decline the healer's services.",
            effects={"healed": False},
        )

    # Heal wounded characters who can afford it
    healed = []
    price_per_hp = event_result.effects.get("price_per_hp", 10)
    gold_remaining = party_gold if party_gold is not None else float('inf')
    total_gold_spent = 0

    for char in chars:
        if not char.is_dead() and char.life < char.max_life:
            missing = char.max_life - char.life
            cost = missing * price_per_hp
            if gold_remaining >= cost:
                char.heal(missing)
                gold_remaining -= cost
                total_gold_spent += cost
                healed.append((char.name, missing, cost))

    if not healed:
        return EventResult(
            event_type="wandering_healer",
            description="No one needs healing (or not enough gold).",
            effects={"healed": False},
        )

    desc_parts = [f"{name} healed {amt} HP (cost: {cost}gp)"
                  for name, amt, cost in healed]
    return EventResult(
        event_type="wandering_healer",
        description="The healer tends to your wounds. " + "; ".join(desc_parts),
        effects={"healed": True, "details": healed, "total_cost": total_gold_spent},
    )


def _resolve_wandering_alchemist(event_result, chars, choice) -> EventResult:
    if choice == "leave":
        return EventResult(
            event_type="wandering_alchemist",
            description="You decline the alchemist's wares.",
            effects={"purchased": False},
        )

    stock = event_result.effects.get("stock", {})
    prices = event_result.effects.get("prices", {})
    return EventResult(
        event_type="wandering_alchemist",
        description="The alchemist displays wares for purchase.",
        effects={"purchased": True, "stock": stock, "prices": prices,
                 "available": True},
    )


# ---------------------------------------------------------------------------
# Search Mechanics (design spec 11.3)
# ---------------------------------------------------------------------------

def search_room(party, force_roll: int = None, force_complication_roll: int = None,
                has_dwarf: bool = False) -> EventResult:
    """Search an empty room. One attempt per room.

    Roll d6:
      1 = Wandering monster
      2-4 = Nothing found
      5 = Secret door
      6 = Hidden treasure (with complication roll)

    Dwarf bonus: +1 to search roll.  This means dwarves effectively
    roll 2-7, so they can never trigger wandering monsters (roll <= 1)
    and have a chance at hidden treasure on a natural 5.
    """
    chars = _get_chars(party)
    roll = force_roll if force_roll is not None else roll_d6()

    # Dwarf bonus
    if has_dwarf:
        roll += 1

    if roll <= 1:
        return EventResult(
            event_type="search_wandering_monster",
            description="Your searching attracts wandering monsters!",
            requires_combat=True,
            effects={"search_result": "wandering_monster"},
        )
    elif roll <= 4:
        return EventResult(
            event_type="search_nothing",
            description="You search thoroughly but find nothing.",
            effects={"search_result": "nothing"},
        )
    elif roll == 5:
        # Secret door
        exit_roll = roll_d6()
        is_safe_exit = (exit_roll == 6)
        return EventResult(
            event_type="search_secret_door",
            description=("You find a secret door! It leads to a safe exit from the dungeon!"
                         if is_safe_exit
                         else "You find a secret door leading to an unexplored passage."),
            effects={"search_result": "secret_door", "safe_exit": is_safe_exit},
        )
    else:
        # Hidden treasure (roll >= 6)
        gold = roll_d6() * roll_d6()
        complication = (force_complication_roll if force_complication_roll is not None
                        else roll_d6())

        if complication == 1:
            return EventResult(
                event_type="search_hidden_treasure",
                description=f"You find {gold} gold, but a trap protects it!",
                effects={"search_result": "hidden_treasure", "gold": gold,
                          "complication": "trap"},
            )
        elif complication == 2:
            return EventResult(
                event_type="search_hidden_treasure",
                description=f"You find {gold} gold, but wandering monsters arrive!",
                requires_combat=True,
                effects={"search_result": "hidden_treasure", "gold": gold,
                          "complication": "wandering_monster"},
            )
        else:
            return EventResult(
                event_type="search_hidden_treasure",
                description=f"You find {gold} gold pieces hidden in the room!",
                effects={"search_result": "hidden_treasure", "gold": gold,
                          "complication": None},
            )




# ---------------------------------------------------------------------------
# Clue Tracker
# ---------------------------------------------------------------------------

class ClueTracker:
    """Track clues collected. At 3, a major secret is revealed (Section 11.3)."""

    def __init__(self):
        self.clues = 0
        self.resolved = False

    def add_clue(self) -> int:
        """Add a clue and return new total."""
        self.clues += 1
        return self.clues

    def should_resolve(self) -> bool:
        return self.clues >= 3 and not self.resolved

    def resolve(self, force_roll: int = None) -> dict:
        """Resolve the 3-clue secret."""
        if not self.should_resolve():
            return {"error": "Not enough clues or already resolved"}
        self.resolved = True
        roll = force_roll if force_roll is not None else roll_d6()
        if roll <= 2:
            return {"type": "hidden_treasure_room", "roll": roll,
                    "description": "The clues reveal a hidden treasure room!"}
        elif roll <= 4:
            return {"type": "shortcut_to_boss", "roll": roll,
                    "description": "The clues reveal a shortcut to the final boss!"}
        else:
            return {"type": "xp_for_party", "roll": roll,
                    "description": "The clues grant wisdom! Each character gets an XP roll!"}

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _get_chars(party):
    """Extract character list from party object or list."""
    if hasattr(party, 'characters'):
        return party.characters
    elif hasattr(party, 'get_living_characters'):
        return party.get_living_characters()
    else:
        return list(party)

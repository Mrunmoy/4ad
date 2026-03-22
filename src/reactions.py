"""Monster reaction system for 4AD."""
from dataclasses import dataclass, field
from typing import List, Optional
from src.dice import roll_d6


@dataclass
class ReactionResult:
    """Result of a monster reaction roll."""
    reaction_type: str  # "fight", "fight_to_death", "flee", "bribe", "quest", "puzzle", "magic_challenge", "sleeping"
    description: str
    bribe_cost: int = 0  # per monster, if bribe
    quest_data: Optional[dict] = None
    monsters_flee: bool = False
    player_choices: List[str] = field(default_factory=list)
    sleeping_bonus: int = 0  # +2 to first attack if dragon is sleeping
    surprise: bool = False  # Monsters act first in round 1


def roll_monster_reaction(monster_type: str, monster_count: int, party_size: int,
                          force_roll: int = None, has_dwarf: bool = False) -> ReactionResult:
    """
    Roll on a monster's reaction table.

    Args:
        monster_type: Name of the monster type (e.g., "Goblin", "Ogre")
        monster_count: Number of monsters in the encounter
        party_size: Number of living party members
        force_roll: Force a specific d6 result (for testing)
        has_dwarf: Whether the party contains a dwarf (affects troll reactions)

    Returns:
        ReactionResult with the outcome
    """
    roll = force_roll if force_roll is not None else roll_d6()

    handler = REACTION_TABLES.get(monster_type)
    if handler is None:
        # Default: always fight
        return ReactionResult(
            reaction_type="fight",
            description=f"{monster_type} attacks!",
            player_choices=["attack"],
        )

    return handler(roll, monster_count, party_size, has_dwarf)


# --- Reaction handlers for each monster type ---

def _skeleton_reaction(roll, count, party_size, has_dwarf):
    """Skeletons/Zombies: always fight to death (undead, no free will)."""
    return ReactionResult(
        reaction_type="fight_to_death",
        description="The undead attack mindlessly!",
        player_choices=["attack"],
    )


def _goblin_reaction(roll, count, party_size, has_dwarf):
    """
    Goblins: 1=flee if outnumbered, 2-3=bribe(5gp), 4-6=fight.
    1-in-6 chance of surprise (goblins act first in round 1).
    """
    # Roll for surprise (1-in-6)
    surprise_roll = roll_d6()
    goblin_surprise = (surprise_roll == 1)

    if roll == 1:
        if count < party_size:
            return ReactionResult(
                reaction_type="flee",
                description="The goblins see they are outnumbered and flee!",
                monsters_flee=True,
                player_choices=["collect_treasure"],
                surprise=goblin_surprise,
            )
        else:
            return ReactionResult(
                reaction_type="fight",
                description="The goblins consider fleeing but stand their ground!",
                player_choices=["attack"],
                surprise=goblin_surprise,
            )
    elif roll <= 3:
        return ReactionResult(
            reaction_type="bribe",
            description=f"The goblins demand {5 * count} gold ({5} gp each) to leave peacefully.",
            bribe_cost=5,
            player_choices=["attack", "bribe"],
            surprise=goblin_surprise,
        )
    else:
        desc = "The goblins attack!"
        if goblin_surprise:
            desc = "The goblins ambush the party! (surprise - goblins act first)"
        return ReactionResult(
            reaction_type="fight",
            description=desc,
            player_choices=["attack"],
            surprise=goblin_surprise,
        )


def _hobgoblin_reaction(roll, count, party_size, has_dwarf):
    """
    Hobgoblins: 1=flee if outnumbered, 2-3=bribe(10gp), 4-5=fight, 6=fight to death.
    """
    if roll == 1:
        if count < party_size:
            return ReactionResult(
                reaction_type="flee",
                description="The hobgoblins see they are outnumbered and flee!",
                monsters_flee=True,
                player_choices=["collect_treasure"],
            )
        else:
            return ReactionResult(
                reaction_type="fight",
                description="The hobgoblins stand their ground!",
                player_choices=["attack"],
            )
    elif roll <= 3:
        return ReactionResult(
            reaction_type="bribe",
            description=f"The hobgoblins demand {10 * count} gold ({10} gp each) to leave.",
            bribe_cost=10,
            player_choices=["attack", "bribe"],
        )
    elif roll <= 5:
        return ReactionResult(
            reaction_type="fight",
            description="The hobgoblins attack!",
            player_choices=["attack"],
        )
    else:
        return ReactionResult(
            reaction_type="fight_to_death",
            description="The hobgoblins attack with fanatical fury!",
            player_choices=["attack"],
        )


def _orc_reaction(roll, count, party_size, has_dwarf):
    """
    Orcs: 1-2=bribe(10gp), 3-5=fight, 6=fight to death.
    """
    if roll <= 2:
        return ReactionResult(
            reaction_type="bribe",
            description=f"The orcs demand {10 * count} gold ({10} gp each) to let you pass.",
            bribe_cost=10,
            player_choices=["attack", "bribe"],
        )
    elif roll <= 5:
        return ReactionResult(
            reaction_type="fight",
            description="The orcs attack!",
            player_choices=["attack"],
        )
    else:
        return ReactionResult(
            reaction_type="fight_to_death",
            description="The orcs attack with savage fury!",
            player_choices=["attack"],
        )


def _troll_reaction(roll, count, party_size, has_dwarf):
    """
    Trolls: 1-2=fight, 3-6=fight to death.
    If dwarf in party: always fight to death.
    """
    if has_dwarf:
        return ReactionResult(
            reaction_type="fight_to_death",
            description="The trolls see the dwarf and fly into a rage!",
            player_choices=["attack"],
        )
    if roll <= 2:
        return ReactionResult(
            reaction_type="fight",
            description="The trolls attack!",
            player_choices=["attack"],
        )
    else:
        return ReactionResult(
            reaction_type="fight_to_death",
            description="The trolls attack relentlessly!",
            player_choices=["attack"],
        )


def _fungi_folk_reaction(roll, count, party_size, has_dwarf):
    """
    Fungi Folk: 1-2=bribe(d6gp each), 3-6=fight.
    """
    if roll <= 2:
        bribe_per = roll_d6()
        return ReactionResult(
            reaction_type="bribe",
            description=f"The fungi folk demand {bribe_per * count} gold ({bribe_per} gp each) to let you pass.",
            bribe_cost=bribe_per,
            player_choices=["attack", "bribe"],
        )
    else:
        return ReactionResult(
            reaction_type="fight",
            description="The fungi folk attack!",
            player_choices=["attack"],
        )


def _chaos_lord_reaction(roll, count, party_size, has_dwarf):
    """
    Chaos Lord: 1=fight, 2-3=fight, 4-5=fight to death, 6=fight to death.
    """
    if roll <= 3:
        return ReactionResult(
            reaction_type="fight",
            description="The Chaos Lord prepares for battle!",
            player_choices=["attack"],
        )
    else:
        return ReactionResult(
            reaction_type="fight_to_death",
            description="The Chaos Lord attacks with unholy fury!",
            player_choices=["attack"],
        )


def _ogre_reaction(roll, count, party_size, has_dwarf):
    """
    Ogre: 1=bribe(50gp), 2-4=fight, 5-6=fight to death.
    """
    if roll == 1:
        return ReactionResult(
            reaction_type="bribe",
            description="The ogre demands 50 gold to let you pass.",
            bribe_cost=50,
            player_choices=["attack", "bribe"],
        )
    elif roll <= 4:
        return ReactionResult(
            reaction_type="fight",
            description="The ogre attacks!",
            player_choices=["attack"],
        )
    else:
        return ReactionResult(
            reaction_type="fight_to_death",
            description="The ogre attacks in a blind rage!",
            player_choices=["attack"],
        )


def _vampire_reaction(roll, count, party_size, has_dwarf):
    """Vampire: always fight to death (undead)."""
    return ReactionResult(
        reaction_type="fight_to_death",
        description="The vampire bares its fangs!",
        player_choices=["attack"],
    )


def _demon_reaction(roll, count, party_size, has_dwarf):
    """
    Demon: 1=magic challenge, 2-6=fight to death.
    """
    if roll == 1:
        return ReactionResult(
            reaction_type="magic_challenge",
            description="The demon challenges your wizard to a magical duel!",
            player_choices=["accept_challenge", "attack"],
        )
    else:
        return ReactionResult(
            reaction_type="fight_to_death",
            description="The demon attacks!",
            player_choices=["attack"],
        )


def _troll_boss_reaction(roll, count, party_size, has_dwarf):
    """Troll Boss: same as minion trolls."""
    return _troll_reaction(roll, count, party_size, has_dwarf)


def _dragon_reaction(roll, count, party_size, has_dwarf):
    """
    Dragon: 1=sleeping(+2 first attack), 2-6=fight to death.
    """
    if roll == 1:
        return ReactionResult(
            reaction_type="sleeping",
            description="The dragon is asleep! You can attempt to steal its treasure or attack with advantage.",
            sleeping_bonus=2,
            player_choices=["attack", "sneak"],
        )
    else:
        return ReactionResult(
            reaction_type="fight_to_death",
            description="The dragon roars and attacks!",
            player_choices=["attack"],
        )


def _small_dragon_reaction(roll, count, party_size, has_dwarf):
    """
    Small Dragon: 1=sleeping(+2), 2-3=bribe(100gp+magic item), 4-5=fight, 6=quest.
    """
    if roll == 1:
        return ReactionResult(
            reaction_type="sleeping",
            description="The small dragon is asleep!",
            sleeping_bonus=2,
            player_choices=["attack", "sneak"],
        )
    elif roll <= 3:
        return ReactionResult(
            reaction_type="bribe",
            description="The small dragon demands 100 gold and a magic item to let you pass.",
            bribe_cost=100,
            player_choices=["attack", "bribe"],
        )
    elif roll <= 5:
        return ReactionResult(
            reaction_type="fight",
            description="The small dragon attacks!",
            player_choices=["attack"],
        )
    else:
        return ReactionResult(
            reaction_type="quest",
            description="The small dragon offers you a quest!",
            quest_data={"source": "Small Dragon", "type": "dragon_quest"},
            player_choices=["accept_quest", "attack"],
        )


def _medusa_reaction(roll, count, party_size, has_dwarf):
    """
    Medusa: 1=puzzle, 2-6=fight.
    """
    if roll == 1:
        return ReactionResult(
            reaction_type="puzzle",
            description="The medusa challenges you with a riddle!",
            player_choices=["attempt_puzzle", "attack"],
        )
    else:
        return ReactionResult(
            reaction_type="fight",
            description="The medusa attacks!",
            player_choices=["attack"],
        )


def _mind_flayer_reaction(roll, count, party_size, has_dwarf):
    """
    Mind Flayer / Chaos Lord (Weird): 1=magic challenge, 2-6=fight to death.
    """
    if roll == 1:
        return ReactionResult(
            reaction_type="magic_challenge",
            description="The mind flayer challenges your wizard to a psychic duel!",
            player_choices=["accept_challenge", "attack"],
        )
    else:
        return ReactionResult(
            reaction_type="fight_to_death",
            description="The mind flayer attacks!",
            player_choices=["attack"],
        )


def _always_fight(roll, count, party_size, has_dwarf):
    """Default for monsters that always fight (mindless creatures)."""
    return ReactionResult(
        reaction_type="fight",
        description="The creature attacks!",
        player_choices=["attack"],
    )


# --- Reaction resolution helpers ---

def resolve_puzzle(solver, monster_level: int, force_roll: int = None) -> dict:
    """
    Resolve a puzzle challenge.
    Roll d6 + bonus vs monster_level.
    Wizards and rogues add their level.

    Returns dict with success, description, damage_taken.
    """
    roll = force_roll if force_roll is not None else roll_d6()
    bonus = 0
    if hasattr(solver, 'class_type') and solver.class_type in ("Wizard", "Rogue"):
        bonus = solver.level

    total = roll + bonus

    if total >= monster_level:
        return {
            "success": True,
            "roll": total,
            "description": f"{solver.name} solves the puzzle! (roll {total} vs {monster_level})",
        }
    else:
        # Fail: monster attacks, solver loses 1 life
        solver.take_damage(1)
        return {
            "success": False,
            "roll": total,
            "damage_taken": 1,
            "description": f"{solver.name} fails the puzzle (roll {total} vs {monster_level}) and takes 1 damage!",
        }


def resolve_magic_challenge(wizard, monster_level: int,
                            force_wizard_roll: int = None,
                            force_monster_roll: int = None) -> dict:
    """
    Resolve a magic challenge (wizard duel).
    Wizard rolls d6 + level vs monster rolls d6 + monster_level.
    Win = monster leaves + treasure.
    Lose = wizard takes 2 damage.

    Returns dict with success, description, etc.
    """
    w_roll = force_wizard_roll if force_wizard_roll is not None else roll_d6()
    m_roll = force_monster_roll if force_monster_roll is not None else roll_d6()

    wizard_total = w_roll + wizard.level
    monster_total = m_roll + monster_level

    if wizard_total >= monster_total:
        return {
            "success": True,
            "wizard_roll": wizard_total,
            "monster_roll": monster_total,
            "description": f"{wizard.name} wins the magical duel! ({wizard_total} vs {monster_total})",
        }
    else:
        # Loser takes 2 damage (spec section 4.2, Demon)
        wizard.take_damage(2)
        return {
            "success": False,
            "wizard_roll": wizard_total,
            "monster_roll": monster_total,
            "damage_taken": 2,
            "description": f"{wizard.name} loses the magical duel ({wizard_total} vs {monster_total}) and takes 2 damage!",
        }


# Reaction table registry
REACTION_TABLES = {
    # Minions
    "Skeleton": _skeleton_reaction,
    "Zombie": _skeleton_reaction,
    "Goblin": _goblin_reaction,
    "Hobgoblin": _hobgoblin_reaction,
    "Orc": _orc_reaction,
    "Troll": _troll_reaction,
    "Fungi Folk": _fungi_folk_reaction,
    # Bosses
    "Chaos Warrior": _chaos_lord_reaction,  # Chaos Lord in bosses table
    "Chaos Lord": _chaos_lord_reaction,
    "Ogre": _ogre_reaction,
    "Vampire": _vampire_reaction,
    "Demon": _demon_reaction,
    "Troll Boss": _troll_boss_reaction,
    "Dragon": _dragon_reaction,
    "Small Dragon": _small_dragon_reaction,
    # Weird monsters
    "Gelatinous Cube": _always_fight,
    "Rust Monster": _always_fight,
    "Carrion Crawler": _always_fight,
    "Mimic": _always_fight,
    "Medusa": _medusa_reaction,
    "Mind Flayer": _mind_flayer_reaction,
    # Vermin (all mindless, always fight)
    "Giant Rat": _always_fight,
    "Rats": _always_fight,
    "Spiders": _always_fight,
    "Bats": _always_fight,
    "Snakes": _always_fight,
    "Insects": _always_fight,
    "Scorpions": _always_fight,
    "Kobold": _always_fight,
}

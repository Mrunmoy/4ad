"""Quest system for 4AD."""
import random
from dataclasses import dataclass, field
from typing import Optional, List
from src.dice import roll_d6
from src.monster import BOSSES_TABLE


QUEST_TYPES = {
    1: "bring_head",
    2: "bring_gold",
    3: "capture_alive",
    4: "bring_item",
    5: "peace",
    6: "slay_all",
}

QUEST_DESCRIPTIONS = {
    "bring_head": "Bring me his head!",
    "bring_gold": "Bring me gold!",
    "capture_alive": "I want him alive!",
    "bring_item": "Bring me that!",
    "peace": "Let peace be your way!",
    "slay_all": "Slay all the monsters!",
}

EPIC_REWARDS_TABLE = {
    1: {
        "name": "Vorpal Blade",
        "description": (
            "Magic weapon, +2 to attack. On natural 6: instant kill on "
            "minions, double damage on bosses."
        ),
        "effect": {"type": "weapon", "attack_bonus": 2, "vorpal": True},
    },
    2: {
        "name": "Dragon Scale Shield",
        "description": (
            "+2 defense. Immune to dragon breath weapon."
        ),
        "effect": {"type": "shield", "defense_bonus": 2, "dragon_immune": True},
    },
    3: {
        "name": "Amulet of Life",
        "description": (
            "Once per adventure, auto-revive from death with 1 life point."
        ),
        "effect": {"type": "amulet", "auto_revive": True},
    },
    4: {
        "name": "Ring of Power",
        "description": "+1 to ALL rolls. Permanent.",
        "effect": {"type": "ring", "all_bonus": 1},
    },
    5: {
        "name": "Tome of Knowledge",
        "description": (
            "One character permanently gains +1 max level (can reach level 6)."
        ),
        "effect": {"type": "tome", "max_level_increase": 1},
    },
    6: {
        "name": "Crown of Command",
        "description": (
            "Party always acts first. +1 to all morale checks."
        ),
        "effect": {"type": "crown", "always_first": True, "morale_bonus": 1},
    },
}


@dataclass
class Quest:
    """An active quest."""
    quest_type: str
    description: str
    target: str  # specific boss name, gold amount, item name, etc.
    completed: bool = False
    progress: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "quest_type": self.quest_type,
            "description": self.description,
            "target": self.target,
            "completed": self.completed,
            "progress": dict(self.progress),
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Quest":
        return cls(
            quest_type=data["quest_type"],
            description=data["description"],
            target=data["target"],
            completed=data.get("completed", False),
            progress=data.get("progress", {}),
        )


@dataclass
class EpicReward:
    """An epic reward from quest completion."""
    name: str
    description: str
    effect: dict


def generate_quest(force_roll: Optional[int] = None) -> Quest:
    """Generate a random quest from the quest table (d6).

    Args:
        force_roll: Override the d6 roll (for testing).

    Returns:
        A new Quest instance.
    """
    roll = force_roll if force_roll is not None else roll_d6()
    quest_type = QUEST_TYPES[roll]
    description = QUEST_DESCRIPTIONS[quest_type]

    target = ""
    progress = {}

    if quest_type == "bring_head":
        # Roll on boss table to determine target
        boss_roll = roll_d6()
        boss = BOSSES_TABLE[boss_roll]()
        target = boss.name
        progress = {"target_boss": boss.name, "killed": False}

    elif quest_type == "bring_gold":
        gold_amount = roll_d6() * 50
        target = f"{gold_amount} gold"
        progress = {"gold_required": gold_amount, "gold_delivered": False}

    elif quest_type == "capture_alive":
        boss_roll = roll_d6()
        boss = BOSSES_TABLE[boss_roll]()
        target = boss.name
        progress = {"target_boss": boss.name, "captured": False}

    elif quest_type == "bring_item":
        # In full implementation, roll on magic treasure table
        target = "magic item"
        progress = {"item_found": False}

    elif quest_type == "peace":
        target = "3 peaceful encounters"
        progress = {"peaceful_encounters": 0, "required": 3}

    elif quest_type == "slay_all":
        target = "all monsters"
        progress = {"monsters_fled": 0, "monsters_bribed": 0}

    return Quest(
        quest_type=quest_type,
        description=description,
        target=target,
        completed=False,
        progress=progress,
    )


def check_quest_completion(quest: Quest, game_state: dict) -> bool:
    """Check if a quest has been completed.

    Args:
        quest: The active quest.
        game_state: Dictionary with relevant game state:
            - party_gold: int
            - bosses_killed: list of boss names
            - bosses_captured: list of boss names
            - magic_items: list of item names
            - peaceful_encounters: int
            - all_monsters_killed: bool
            - fled_or_bribed: bool

    Returns:
        True if quest is now completed.
    """
    if quest.completed:
        return True

    qt = quest.quest_type

    if qt == "bring_head":
        target = quest.progress.get("target_boss", "")
        if target in game_state.get("bosses_killed", []):
            quest.progress["killed"] = True
            quest.completed = True

    elif qt == "bring_gold":
        required = quest.progress.get("gold_required", 0)
        if game_state.get("party_gold", 0) >= required:
            quest.progress["gold_delivered"] = True
            quest.completed = True

    elif qt == "capture_alive":
        target = quest.progress.get("target_boss", "")
        if target in game_state.get("bosses_captured", []):
            quest.progress["captured"] = True
            quest.completed = True

    elif qt == "bring_item":
        # Simplified: check if party has any magic item
        if game_state.get("magic_items", []):
            quest.progress["item_found"] = True
            quest.completed = True

    elif qt == "peace":
        peaceful = game_state.get("peaceful_encounters", 0)
        quest.progress["peaceful_encounters"] = peaceful
        if peaceful >= quest.progress.get("required", 3):
            quest.completed = True

    elif qt == "slay_all":
        if game_state.get("all_monsters_killed", False) and not game_state.get(
            "fled_or_bribed", False
        ):
            quest.completed = True

    return quest.completed


def roll_epic_reward(
    used_rewards: Optional[List[str]] = None,
    force_roll: Optional[int] = None,
) -> Optional[EpicReward]:
    """Roll on the epic rewards table.

    Each reward can only be earned once per campaign. If the rolled reward
    has already been earned, randomly select from remaining available rewards.
    If all rewards are used, returns None.

    Args:
        used_rewards: List of reward names already earned this campaign.
        force_roll: Override the d6 roll (for testing).

    Returns:
        An EpicReward, or None if all rewards are exhausted.
    """
    if used_rewards is None:
        used_rewards = []

    # All 6 used? No more rewards.
    if len(used_rewards) >= 6:
        return None

    roll = force_roll if force_roll is not None else roll_d6()
    reward_data = EPIC_REWARDS_TABLE[roll]

    if reward_data["name"] not in used_rewards:
        return EpicReward(
            name=reward_data["name"],
            description=reward_data["description"],
            effect=reward_data["effect"],
        )

    # If force_roll hits a used reward, we can't reroll
    if force_roll is not None:
        return None

    # Deterministically select from remaining available rewards
    available = [
        EPIC_REWARDS_TABLE[i]
        for i in range(1, 7)
        if EPIC_REWARDS_TABLE[i]["name"] not in used_rewards
    ]
    reward_data = random.choice(available)
    return EpicReward(
        name=reward_data["name"],
        description=reward_data["description"],
        effect=reward_data["effect"],
    )

"""Tests for quest system."""
import pytest
from src.quests import (
    generate_quest, check_quest_completion, roll_epic_reward,
    Quest, EpicReward, QUEST_TYPES, EPIC_REWARDS_TABLE,
)


class TestQuestGeneration:
    """Test quest generation from the quest table."""

    def test_generate_quest_returns_quest(self):
        quest = generate_quest(force_roll=1)
        assert isinstance(quest, Quest)

    def test_quest_type_1_is_bring_head(self):
        quest = generate_quest(force_roll=1)
        assert quest.quest_type == "bring_head"
        assert "head" in quest.description.lower()

    def test_quest_type_2_is_bring_gold(self):
        quest = generate_quest(force_roll=2)
        assert quest.quest_type == "bring_gold"
        assert "gold" in quest.description.lower()

    def test_quest_type_3_is_capture_alive(self):
        quest = generate_quest(force_roll=3)
        assert quest.quest_type == "capture_alive"
        assert "alive" in quest.description.lower()

    def test_quest_type_4_is_bring_item(self):
        quest = generate_quest(force_roll=4)
        assert quest.quest_type == "bring_item"

    def test_quest_type_5_is_peace(self):
        quest = generate_quest(force_roll=5)
        assert quest.quest_type == "peace"
        assert "peace" in quest.description.lower()

    def test_quest_type_6_is_slay_all(self):
        quest = generate_quest(force_roll=6)
        assert quest.quest_type == "slay_all"
        assert "slay" in quest.description.lower()

    def test_bring_head_has_target_boss(self):
        quest = generate_quest(force_roll=1)
        assert quest.progress.get("target_boss") is not None
        assert len(quest.target) > 0

    def test_bring_gold_has_gold_amount(self):
        quest = generate_quest(force_roll=2)
        amount = quest.progress.get("gold_required", 0)
        assert amount >= 50
        assert amount <= 300
        assert amount % 50 == 0

    def test_quest_starts_incomplete(self):
        quest = generate_quest(force_roll=1)
        assert quest.completed is False


class TestQuestCompletion:
    """Test quest completion conditions."""

    def test_bring_head_completed_when_boss_killed(self):
        quest = generate_quest(force_roll=1)
        target = quest.progress["target_boss"]
        state = {"bosses_killed": [target]}
        assert check_quest_completion(quest, state) is True
        assert quest.completed is True

    def test_bring_head_not_completed_wrong_boss(self):
        quest = generate_quest(force_roll=1)
        state = {"bosses_killed": ["Wrong Boss"]}
        assert check_quest_completion(quest, state) is False

    def test_bring_gold_completed_when_enough_gold(self):
        quest = generate_quest(force_roll=2)
        required = quest.progress["gold_required"]
        state = {"party_gold": required}
        assert check_quest_completion(quest, state) is True

    def test_bring_gold_not_completed_insufficient(self):
        quest = generate_quest(force_roll=2)
        required = quest.progress["gold_required"]
        state = {"party_gold": required - 1}
        assert check_quest_completion(quest, state) is False

    def test_capture_alive_completed(self):
        quest = generate_quest(force_roll=3)
        target = quest.progress["target_boss"]
        state = {"bosses_captured": [target]}
        assert check_quest_completion(quest, state) is True

    def test_peace_quest_completed_at_3_peaceful(self):
        quest = generate_quest(force_roll=5)
        state = {"peaceful_encounters": 3}
        assert check_quest_completion(quest, state) is True

    def test_peace_quest_not_completed_at_2(self):
        quest = generate_quest(force_roll=5)
        state = {"peaceful_encounters": 2}
        assert check_quest_completion(quest, state) is False

    def test_slay_all_completed(self):
        quest = generate_quest(force_roll=6)
        state = {"all_monsters_killed": True, "fled_or_bribed": False}
        assert check_quest_completion(quest, state) is True

    def test_slay_all_fails_if_fled(self):
        quest = generate_quest(force_roll=6)
        state = {"all_monsters_killed": True, "fled_or_bribed": True}
        assert check_quest_completion(quest, state) is False

    def test_already_completed_quest_stays_completed(self):
        quest = generate_quest(force_roll=1)
        quest.completed = True
        assert check_quest_completion(quest, {}) is True


class TestEpicRewards:
    """Test epic reward rolling."""

    def test_roll_returns_epic_reward(self):
        reward = roll_epic_reward(force_roll=1)
        assert isinstance(reward, EpicReward)
        assert len(reward.name) > 0

    def test_each_roll_gives_different_reward(self):
        names = set()
        for roll in range(1, 7):
            reward = roll_epic_reward(force_roll=roll)
            names.add(reward.name)
        assert len(names) == 6

    def test_used_reward_not_given_again(self):
        reward1 = roll_epic_reward(force_roll=1)
        reward2 = roll_epic_reward(used_rewards=[reward1.name], force_roll=1)
        assert reward2 is None  # forced roll hits used reward

    def test_all_rewards_exhausted_returns_none(self):
        all_names = [EPIC_REWARDS_TABLE[i]["name"] for i in range(1, 7)]
        result = roll_epic_reward(used_rewards=all_names)
        assert result is None

    def test_reward_has_effect_dict(self):
        reward = roll_epic_reward(force_roll=1)
        assert isinstance(reward.effect, dict)
        assert "type" in reward.effect

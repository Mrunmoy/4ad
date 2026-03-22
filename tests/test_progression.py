"""Tests for XP and leveling system."""
import pytest
from src.character import (
    Warrior, Cleric, Rogue, Wizard,
    Barbarian, Elf, Dwarf, Halfling,
)
from src.progression import (
    attempt_level_up, get_xp_rolls_earned, MAX_LEVEL, BASE_LIFE,
)


class TestXPRollsEarned:
    """Test XP roll calculation from various sources."""

    def test_boss_kill_gives_1_xp_roll(self):
        assert get_xp_rolls_earned(boss_killed=True) == 1

    def test_weird_monster_gives_1_xp_roll(self):
        assert get_xp_rolls_earned(weird_monster_killed=True) == 1

    def test_dragon_final_boss_gives_2_xp_rolls(self):
        assert get_xp_rolls_earned(dragon_final_boss=True) == 2

    def test_dragon_final_boss_replaces_boss_roll(self):
        """Dragon final boss gives 2, not 2+1."""
        assert get_xp_rolls_earned(boss_killed=True, dragon_final_boss=True) == 2

    def test_10_minion_encounters_gives_1_xp_roll(self):
        assert get_xp_rolls_earned(minion_encounters=10) == 1

    def test_9_minion_encounters_gives_0_xp_rolls(self):
        assert get_xp_rolls_earned(minion_encounters=9) == 0

    def test_20_minion_encounters_gives_2_xp_rolls(self):
        assert get_xp_rolls_earned(minion_encounters=20) == 2

    def test_quest_completion_gives_1_xp_roll(self):
        assert get_xp_rolls_earned(quest_completed=True) == 1

    def test_combined_sources(self):
        """Boss + weird + 10 minions + quest = 4 rolls."""
        result = get_xp_rolls_earned(
            boss_killed=True,
            weird_monster_killed=True,
            minion_encounters=10,
            quest_completed=True,
        )
        assert result == 4

    def test_no_sources_gives_0(self):
        assert get_xp_rolls_earned() == 0


class TestAttemptLevelUp:
    """Test the XP roll mechanic for leveling up."""

    def test_level_up_on_roll_greater_than_level(self):
        """Roll > current level means level up."""
        warrior = Warrior("Brynn")
        assert warrior.level == 1
        result = attempt_level_up(warrior, force_roll=2)
        assert result.leveled_up is True
        assert result.new_level == 2
        assert warrior.level == 2

    def test_no_level_up_on_roll_equal_to_level(self):
        """Roll == current level means no level up."""
        warrior = Warrior("Brynn")
        result = attempt_level_up(warrior, force_roll=1)
        assert result.leveled_up is False
        assert warrior.level == 1

    def test_no_level_up_on_roll_less_than_level(self):
        """Roll < current level means no level up."""
        warrior = Warrior("Brynn", level=3)
        result = attempt_level_up(warrior, force_roll=2)
        assert result.leveled_up is False

    def test_cannot_exceed_max_level(self):
        """Character at max level raises ValueError."""
        warrior = Warrior("Brynn")
        warrior.level = MAX_LEVEL
        with pytest.raises(ValueError, match="max level"):
            attempt_level_up(warrior, force_roll=6)

    def test_consecutive_restriction(self):
        """Cannot attempt same character twice in a row."""
        warrior = Warrior("Brynn")
        with pytest.raises(ValueError, match="twice in a row"):
            attempt_level_up(warrior, last_leveled_character="Brynn", force_roll=6)

    def test_consecutive_allowed_when_no_previous(self):
        """First XP roll has no restriction."""
        warrior = Warrior("Brynn")
        result = attempt_level_up(warrior, last_leveled_character=None, force_roll=6)
        assert result.leveled_up is True

    def test_result_contains_stat_changes(self):
        """Level up result should include stat changes dict."""
        warrior = Warrior("Brynn")
        result = attempt_level_up(warrior, force_roll=6)
        assert "max_life" in result.stat_changes
        assert result.stat_changes["max_life"] == 1

    def test_result_description_not_empty(self):
        warrior = Warrior("Brynn")
        result = attempt_level_up(warrior, force_roll=6)
        assert len(result.description) > 0


class TestLevelUpEffectsPerClass:
    """Test that level-up applies correct bonuses per class."""

    def test_warrior_level_up_increases_max_life(self):
        warrior = Warrior("Brynn")
        old_max = warrior.max_life
        attempt_level_up(warrior, force_roll=6)
        assert warrior.max_life == old_max + 1

    def test_warrior_level_up_gives_attack_bonus(self):
        warrior = Warrior("Brynn")
        result = attempt_level_up(warrior, force_roll=6)
        assert result.stat_changes.get("attack_bonus") == 1
        assert warrior.attack_bonus() == 2  # level 2

    def test_cleric_level_up_increases_save_vs_undead(self):
        cleric = Cleric("Elena")
        result = attempt_level_up(cleric, force_roll=6)
        assert result.stat_changes.get("save_vs_undead") == 1
        assert cleric.get_save_bonus("undead") == 2

    def test_rogue_level_up_increases_defense_and_disarm(self):
        rogue = Rogue("Shadow")
        result = attempt_level_up(rogue, force_roll=6)
        assert result.stat_changes.get("defense_bonus") == 1
        assert result.stat_changes.get("disarm_bonus") == 1
        assert rogue.defense_bonus() == 2  # level 2
        assert rogue.get_disarm_bonus() == 2

    def test_wizard_level_up_adds_spell_slot(self):
        wizard = Wizard("Merlin")
        old_slots = wizard.spell_slots
        result = attempt_level_up(wizard, force_roll=6)
        assert result.stat_changes.get("spell_slots") == 1
        assert wizard.spell_slots == old_slots + 1

    def test_barbarian_level_up_gives_attack_bonus(self):
        barb = Barbarian("Conan")
        result = attempt_level_up(barb, force_roll=6)
        assert result.stat_changes.get("attack_bonus") == 1
        assert barb.attack_bonus() == 2

    def test_elf_level_up_gives_spell_slot_and_attack(self):
        elf = Elf("Legolas")
        old_slots = elf.spell_slots
        result = attempt_level_up(elf, force_roll=6)
        assert result.stat_changes.get("spell_slots") == 1
        assert result.stat_changes.get("attack_bonus") == 1
        assert elf.spell_slots == old_slots + 1

    def test_dwarf_level_up_gives_attack_bonus(self):
        dwarf = Dwarf("Gimli")
        result = attempt_level_up(dwarf, force_roll=6)
        assert result.stat_changes.get("attack_bonus") == 1

    def test_halfling_level_up_gives_luck_point(self):
        halfling = Halfling("Frodo")
        old_luck = halfling.luck_points
        result = attempt_level_up(halfling, force_roll=6)
        assert result.stat_changes.get("luck_points") == 1
        assert halfling.luck_points == old_luck + 1


class TestLifeFormulas:
    """Verify life = base + level for each class at each level."""

    @pytest.mark.parametrize("cls,base", [
        (Warrior, 6), (Cleric, 5), (Rogue, 4), (Wizard, 3),
        (Barbarian, 8), (Elf, 4), (Dwarf, 7), (Halfling, 4),
    ])
    def test_life_at_level_1(self, cls, base):
        char = cls("Test")
        assert char.max_life == base + 1

    @pytest.mark.parametrize("cls,base", [
        (Warrior, 6), (Cleric, 5), (Rogue, 4), (Wizard, 3),
        (Barbarian, 8), (Elf, 4), (Dwarf, 7), (Halfling, 4),
    ])
    def test_life_at_level_5(self, cls, base):
        char = cls("Test", level=5)
        assert char.max_life == base + 5


class TestLevelCap:
    """Verify max level is enforced."""

    def test_cannot_level_beyond_5(self):
        warrior = Warrior("Brynn")
        warrior.level = 5
        with pytest.raises(ValueError):
            attempt_level_up(warrior, force_roll=6)

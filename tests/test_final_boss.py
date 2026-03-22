"""Tests for final boss detection and exit encounters."""
import pytest
from src.final_boss import (
    check_final_boss, create_final_boss, roll_exit_encounter, generate_exit_monster,
)
from src.monster import Monster, Boss, Minion


class TestFinalBossDetection:
    """Test final boss detection mechanic."""

    def test_final_boss_when_total_ge_6(self):
        """d6 + bosses_encountered >= 6 triggers final boss."""
        # roll=5, bosses=1 -> 6 >= 6
        assert check_final_boss(1, force_roll=5) is True

    def test_no_final_boss_when_total_lt_6(self):
        """d6 + bosses_encountered < 6 means not final boss."""
        # roll=1, bosses=1 -> 2 < 6
        assert check_final_boss(1, force_roll=1) is False

    def test_guaranteed_final_boss_at_high_count(self):
        """With 6+ encounters, any roll triggers final boss."""
        assert check_final_boss(6, force_roll=1) is True

    def test_borderline_case(self):
        """roll=3, bosses=3 -> 6 = final boss."""
        assert check_final_boss(3, force_roll=3) is True

    def test_just_below_threshold(self):
        """roll=2, bosses=3 -> 5 < 6, not final boss."""
        assert check_final_boss(3, force_roll=2) is False


class TestCreateFinalBoss:
    """Test final boss enhancement."""

    def test_final_boss_gets_plus_1_life(self):
        monster = Boss("Ogre", level=5, life=6)
        create_final_boss(monster)
        assert monster.life == 7
        assert monster.max_life == 7

    def test_final_boss_gets_plus_1_level(self):
        monster = Boss("Ogre", level=5, life=6)
        create_final_boss(monster)
        assert monster.level == 6

    def test_final_boss_flag_set(self):
        monster = Boss("Troll", level=6, life=8)
        create_final_boss(monster)
        assert monster.is_final_boss is True

    def test_final_boss_preserves_other_attributes(self):
        monster = Boss("Vampire", level=6, life=6, is_undead=True)
        create_final_boss(monster)
        assert monster.is_undead is True
        assert monster.name == "Vampire"

    def test_final_boss_dragon(self):
        monster = Boss("Dragon", level=8, life=10, is_dragon=True)
        create_final_boss(monster)
        assert monster.level == 9
        assert monster.life == 11
        assert monster.is_dragon is True


class TestExitEncounters:
    """Test exit phase encounter rolling."""

    def test_encounter_on_roll_1(self):
        assert roll_exit_encounter(force_roll=1) is True

    def test_no_encounter_on_roll_2(self):
        assert roll_exit_encounter(force_roll=2) is False

    def test_no_encounter_on_roll_6(self):
        assert roll_exit_encounter(force_roll=6) is False

    def test_generate_exit_monster_returns_minion(self):
        monster = generate_exit_monster()
        assert isinstance(monster, Minion)
        assert monster.life >= 1

    def test_generate_exit_monster_is_valid(self):
        """Exit monster should have a name and level."""
        monster = generate_exit_monster()
        assert len(monster.name) > 0
        assert monster.level >= 0

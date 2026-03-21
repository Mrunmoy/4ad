"""Tests for the trap system (src/traps.py)."""
import pytest
from src.traps import (
    Trap, TrapResult, generate_trap, attempt_disarm,
    trigger_trap, handle_trap_encounter, TRAP_TABLE,
    _get_armor_bonus, _get_shield_bonus, _has_limping, _apply_limping,
)
from src.character import Warrior, Rogue, Wizard, Cleric, Elf, Halfling, Dwarf


def _make_party(*classes):
    """Create a list of characters from class constructors."""
    chars = []
    for i, cls in enumerate(classes):
        c = cls(f"Char{i+1}")
        c.position = i + 1
        chars.append(c)
    return chars


class TestGenerateTrap:
    """Test the d6 trap table generation."""

    def test_all_six_trap_types(self):
        names = set()
        for roll in range(1, 7):
            trap = generate_trap(force_roll=roll)
            assert isinstance(trap, Trap)
            names.add(trap.trap_type)
        assert names == {"dart", "poison_gas", "trapdoor", "bear_trap", "spears", "stone_block"}

    def test_dart_trap_properties(self):
        trap = generate_trap(force_roll=1)
        assert trap.name == "Dart Trap"
        assert trap.level == 3
        assert trap.targets == "random"

    def test_poison_gas_properties(self):
        trap = generate_trap(force_roll=2)
        assert trap.level == 3
        assert trap.targets == "all"

    def test_spear_trap_level_5(self):
        trap = generate_trap(force_roll=5)
        assert trap.level == 5
        assert trap.targets == "two_random"

    def test_stone_block_targets_last(self):
        trap = generate_trap(force_roll=6)
        assert trap.level == 5
        assert trap.targets == "last"

    def test_out_of_range_clamped(self):
        trap = generate_trap(force_roll=0)
        assert trap.trap_type == "dart"  # clamped to 1
        trap = generate_trap(force_roll=99)
        assert trap.trap_type == "stone_block"  # clamped to 6


class TestArmorBonuses:
    """Test armor/shield bonus helpers."""

    def test_no_equipment(self):
        w = Wizard("Wiz")
        w.equipment = []
        assert _get_armor_bonus(w) == 0

    def test_light_armor_and_shield(self):
        w = Warrior("W")
        w.equipment = ["light armor", "shield"]
        assert _get_armor_bonus(w) == 2

    def test_heavy_armor(self):
        w = Warrior("W")
        w.equipment = ["heavy armor"]
        assert _get_armor_bonus(w) == 2

    def test_shield_only(self):
        w = Warrior("W")
        w.equipment = ["shield"]
        assert _get_shield_bonus(w) == 1
        assert _get_armor_bonus(w) == 1


class TestAttemptDisarm:
    """Test rogue trap disarm mechanic."""

    def test_rogue_disarms_on_high_roll(self):
        rogue = Rogue("Shadow", level=1)
        trap = generate_trap(force_roll=1)  # Dart, level 3
        # Roll 6 + level 1 = 7 >= 3
        assert attempt_disarm(rogue, trap, force_roll=6) is True

    def test_rogue_fails_disarm_on_low_roll(self):
        rogue = Rogue("Shadow", level=1)
        trap = generate_trap(force_roll=5)  # Spears, level 5
        # Roll 1 + level 1 = 2 < 5
        assert attempt_disarm(rogue, trap, force_roll=1) is False

    def test_dead_rogue_cannot_disarm(self):
        rogue = Rogue("Shadow")
        rogue.life = 0
        trap = generate_trap(force_roll=1)
        assert attempt_disarm(rogue, trap, force_roll=6) is False

    def test_petrified_rogue_cannot_disarm(self):
        rogue = Rogue("Shadow")
        rogue.petrified = True
        trap = generate_trap(force_roll=1)
        assert attempt_disarm(rogue, trap, force_roll=6) is False

    def test_higher_level_rogue_has_better_chance(self):
        rogue = Rogue("Shadow", level=3)
        trap = generate_trap(force_roll=5)  # level 5
        # Roll 2 + level 3 = 5 >= 5
        assert attempt_disarm(rogue, trap, force_roll=2) is True


class TestDartTrap:
    """Test dart trap targeting and damage."""

    def test_dart_damages_on_failed_save(self):
        chars = _make_party(Wizard)  # No armor
        trap = generate_trap(force_roll=1)  # level 3
        result = trigger_trap(trap, chars, force_roll=1)  # roll 1 < 3
        assert result.triggered is True
        assert len(result.victims) == 1
        assert result.victims[0][1] == 1  # 1 damage

    def test_dart_blocked_with_armor(self):
        chars = _make_party(Warrior)
        chars[0].equipment = ["heavy armor", "shield"]  # +3 bonus
        trap = generate_trap(force_roll=1)  # level 3
        # roll 1 + 3 = 4 >= 3 -> saved
        result = trigger_trap(trap, chars, force_roll=1)
        assert len(result.victims) == 0


class TestPoisonGas:
    """Test poison gas trap targeting all characters."""

    def test_gas_hits_all_on_low_rolls(self):
        chars = _make_party(Warrior, Cleric, Rogue)
        trap = generate_trap(force_roll=2)  # level 3
        # All roll 1 < 3
        result = trigger_trap(trap, chars, force_rolls=[1, 1, 1])
        assert len(result.victims) == 3

    def test_gas_ignores_armor(self):
        chars = _make_party(Warrior)
        chars[0].equipment = ["heavy armor", "shield"]
        trap = generate_trap(force_roll=2)  # level 3
        # Roll 1, no armor bonus for gas -> 1 < 3 -> hit
        result = trigger_trap(trap, chars, force_rolls=[1])
        assert len(result.victims) == 1

    def test_gas_save_on_high_roll(self):
        chars = _make_party(Warrior, Cleric)
        trap = generate_trap(force_roll=2)
        # Both roll 5 >= 3 -> saved
        result = trigger_trap(trap, chars, force_rolls=[5, 5])
        assert len(result.victims) == 0


class TestTrapdoor:
    """Test trapdoor/pit trap mechanics."""

    def test_trapdoor_fail_causes_limping(self):
        chars = _make_party(Warrior)
        chars[0].equipment = []  # no armor
        trap = generate_trap(force_roll=3)  # level 4
        result = trigger_trap(trap, chars, force_roll=1)  # 1 < 4
        assert len(result.victims) == 1
        assert result.victims[0][2] == "limping"
        assert _has_limping(chars[0])

    def test_trapdoor_rogue_bonus(self):
        chars = _make_party(Rogue)
        chars[0].equipment = []
        trap = generate_trap(force_roll=3)  # level 4
        # Roll 3 + rogue level 1 = 4 >= 4
        result = trigger_trap(trap, chars, force_roll=3)
        assert len(result.victims) == 0

    def test_trapdoor_elf_bonus(self):
        chars = _make_party(Elf)
        chars[0].equipment = []
        trap = generate_trap(force_roll=3)  # level 4
        # Roll 3 + elf +1 = 4 >= 4
        result = trigger_trap(trap, chars, force_roll=3)
        assert len(result.victims) == 0

    def test_trapdoor_limping_penalty(self):
        chars = _make_party(Warrior)
        chars[0].equipment = []
        _apply_limping(chars[0])
        trap = generate_trap(force_roll=3)  # level 4
        # Roll 5 - 2 (limping) = 3 < 4 -> fail
        result = trigger_trap(trap, chars, force_roll=5)
        assert len(result.victims) == 1


class TestBearTrap:
    """Test bear trap mechanics."""

    def test_bear_trap_fail(self):
        chars = _make_party(Warrior)
        chars[0].equipment = []
        trap = generate_trap(force_roll=4)  # level 3
        result = trigger_trap(trap, chars, force_roll=1)  # 1 < 3
        assert len(result.victims) == 1
        assert _has_limping(chars[0])

    def test_bear_trap_halfling_bonus(self):
        chars = _make_party(Halfling)
        chars[0].equipment = []
        trap = generate_trap(force_roll=4)  # level 3
        # Roll 2 + halfling +1 = 3 >= 3
        result = trigger_trap(trap, chars, force_roll=2)
        assert len(result.victims) == 0


class TestSpearTrap:
    """Test spear trap targeting two random characters."""

    def test_spears_hit_two_on_fail(self):
        chars = _make_party(Warrior, Cleric, Rogue, Wizard)
        for c in chars:
            c.equipment = []
        trap = generate_trap(force_roll=5)  # level 5
        # Both targets roll 1 < 5
        result = trigger_trap(trap, chars, force_rolls=[1, 1])
        assert len(result.victims) == 2
        assert all(v[1] == 1 for v in result.victims)

    def test_spears_with_two_chars(self):
        chars = _make_party(Warrior, Cleric)
        for c in chars:
            c.equipment = []
        trap = generate_trap(force_roll=5)
        result = trigger_trap(trap, chars, force_rolls=[1, 1])
        assert len(result.victims) == 2


class TestStoneBlock:
    """Test giant stone block targeting last character."""

    def test_stone_block_hits_last(self):
        chars = _make_party(Warrior, Cleric, Rogue, Wizard)
        for c in chars:
            c.equipment = []
        trap = generate_trap(force_roll=6)  # level 5
        old_life = chars[3].life  # Wizard is last (position 4)
        result = trigger_trap(trap, chars, force_roll=1)  # 1 < 5
        assert len(result.victims) == 1
        assert result.victims[0][0] == chars[3].name
        assert result.victims[0][1] == 2  # 2 damage

    def test_stone_block_shield_helps(self):
        chars = _make_party(Warrior)
        chars[0].equipment = ["shield"]  # +1
        trap = generate_trap(force_roll=6)  # level 5
        # Roll 4 + shield 1 = 5 >= 5 -> saved
        result = trigger_trap(trap, chars, force_roll=4)
        assert len(result.victims) == 0

    def test_stone_block_armor_does_not_help(self):
        chars = _make_party(Warrior)
        chars[0].equipment = ["heavy armor"]  # armor only, no shield
        trap = generate_trap(force_roll=6)  # level 5
        # Roll 1 + 0 (no shield bonus) = 1 < 5 -> hit
        result = trigger_trap(trap, chars, force_roll=1)
        assert len(result.victims) == 1


class TestHandleTrapEncounter:
    """Test full trap encounter with rogue disarm integration."""

    def test_rogue_disarms_prevents_trigger(self):
        chars = _make_party(Rogue, Warrior)
        trap = generate_trap(force_roll=1)  # Dart, level 3
        # Rogue roll 6 + 1 = 7 >= 3 -> disarmed
        result = handle_trap_encounter(trap, chars, force_disarm_roll=6)
        assert result.disarmed is True
        assert result.triggered is False
        assert result.disarmed_by == "Char1"

    def test_rogue_fail_disarm_triggers_trap(self):
        chars = _make_party(Rogue, Warrior)
        for c in chars:
            c.equipment = []
        trap = generate_trap(force_roll=1)  # Dart, level 3
        # Rogue roll 1 + 1 = 2 < 3 -> failed
        result = handle_trap_encounter(
            trap, chars, force_disarm_roll=1, force_trap_roll=1
        )
        assert result.disarmed is False
        assert result.triggered is True

    def test_no_rogue_trap_triggers_directly(self):
        chars = _make_party(Warrior, Cleric)
        for c in chars:
            c.equipment = []
        trap = generate_trap(force_roll=1)  # Dart, level 3
        result = handle_trap_encounter(trap, chars, force_trap_roll=1)
        assert result.disarmed is False
        assert result.triggered is True

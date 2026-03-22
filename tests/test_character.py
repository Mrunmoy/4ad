"""Tests for character classes following 4AD rules."""
import pytest
from src.character import (
    Character, Warrior, Cleric, Rogue, Wizard, 
    Barbarian, Elf, Dwarf, Halfling
)


class TestCharacterBase:
    """Test base character class."""
    
    def test_character_has_name_level_class(self):
        """Character should have name, level, and class type."""
        char = Warrior("TestHero")
        assert char.name == "TestHero"
        assert char.level == 1
        assert char.class_type == "Warrior"
    
    def test_character_has_attack_defense_life(self):
        """Character should have Attack, Defense, and Life values."""
        char = Warrior("TestHero")
        assert char.attack >= 1
        assert char.defense >= 1
        assert char.life >= 1
        assert char.max_life >= char.life
    
    def test_character_can_take_damage(self):
        """Character should be able to take damage."""
        char = Warrior("TestHero")
        initial_life = char.life
        char.take_damage(1)
        assert char.life == initial_life - 1
    
    def test_character_dies_at_zero_life(self):
        """Character should be dead when life reaches 0."""
        char = Warrior("TestHero")
        char.take_damage(char.life)
        assert char.is_dead()
    
    def test_character_can_heal(self):
        """Character should be able to heal."""
        char = Warrior("TestHero")
        char.take_damage(2)
        char.heal(1)
        assert char.life == char.max_life - 1


class TestWarrior:
    """Test Warrior class from page 8."""
    
    def test_warrior_stats_at_level_1(self):
        """Warrior at level 1: Attack 4, Defense 5, Life 7 (6+1)."""
        warrior = Warrior("Brutus")
        assert warrior.attack == 4
        assert warrior.defense == 5
        assert warrior.life == 7
        assert warrior.max_life == 7
    
    def test_warrior_can_use_all_armor(self):
        """Warrior can use any armor."""
        warrior = Warrior("Brutus")
        assert warrior.can_use_heavy_armor()
        assert warrior.can_use_shield()


class TestCleric:
    """Test Cleric class from page 9."""
    
    def test_cleric_stats_at_level_1(self):
        """Cleric at level 1: Attack 3, Defense 4, Life 6 (5+1)."""
        cleric = Cleric("Elena")
        assert cleric.attack == 3
        assert cleric.defense == 4
        assert cleric.life == 6
    
    def test_cleric_can_cast_blessing(self):
        """Cleric can cast Blessing spell."""
        cleric = Cleric("Elena")
        assert cleric.can_cast("Blessing")
    
    def test_cleric_bonus_vs_undead(self):
        """Cleric adds level to saves vs undead."""
        cleric = Cleric("Elena", level=2)
        assert cleric.get_save_bonus("undead") == 2


class TestRogue:
    """Test Rogue class from page 10."""
    
    def test_rogue_stats_at_level_1(self):
        """Rogue at level 1: Attack 3, Defense 4, Life 5 (4+1)."""
        rogue = Rogue("Shadow")
        assert rogue.attack == 3
        assert rogue.defense == 4
        assert rogue.life == 5
    
    def test_rogue_disarm_trap_bonus(self):
        """Rogue gets level bonus to disarm traps."""
        rogue = Rogue("Shadow", level=3)
        assert rogue.get_disarm_bonus() == 3


class TestWizard:
    """Test Wizard class from page 11."""
    
    def test_wizard_stats_at_level_1(self):
        """Wizard at level 1: Attack 2, Defense 3, Life 4 (3+1)."""
        wizard = Wizard("Merlin")
        assert wizard.attack == 2
        assert wizard.defense == 3
        assert wizard.life == 4
    
    def test_wizard_has_spells(self):
        """Wizard knows spells."""
        wizard = Wizard("Merlin")
        assert len(wizard.spells_known) > 0
        assert "Fireball" in wizard.spells_known
        assert "Lightning Bolt" in wizard.spells_known
        assert "Sleep" in wizard.spells_known


class TestBarbarian:
    """Test Barbarian class from page 12."""
    
    def test_barbarian_stats_at_level_1(self):
        """Barbarian at level 1: Attack 5, Defense 4, Life 9 (8+1)."""
        barbarian = Barbarian("Conan")
        assert barbarian.attack == 5
        assert barbarian.defense == 4
        assert barbarian.life == 9
    
    def test_barbarian_cannot_use_magic(self):
        """Barbarian cannot use magic items."""
        barbarian = Barbarian("Conan")
        assert not barbarian.can_use_magic()


class TestElf:
    """Test Elf class from page 13."""
    
    def test_elf_stats_at_level_1(self):
        """Elf at level 1: Attack 3, Defense 4, Life 5 (4+1)."""
        elf = Elf("Legolas")
        assert elf.attack == 3
        assert elf.defense == 4
        assert elf.life == 5
    
    def test_elf_has_spells(self):
        """Elf knows some spells."""
        elf = Elf("Legolas")
        assert len(elf.spells_known) > 0


class TestDwarf:
    """Test Dwarf class from page 14."""
    
    def test_dwarf_stats_at_level_1(self):
        """Dwarf at level 1: Attack 4, Defense 5, Life 8 (7+1)."""
        dwarf = Dwarf("Gimli")
        assert dwarf.attack == 4
        assert dwarf.defense == 5
        assert dwarf.life == 8


class TestHalfling:
    """Test Halfling class from page 15."""
    
    def test_halfling_stats_at_level_1(self):
        """Halfling at level 1: Attack 2, Defense 5, Life 5 (4+1)."""
        halfling = Halfling("Frodo")
        assert halfling.attack == 2
        assert halfling.defense == 5
        assert halfling.life == 5
    
    def test_halfling_has_luck(self):
        """Halfling can reroll once per encounter."""
        halfling = Halfling("Frodo")
        assert halfling.can_use_luck()

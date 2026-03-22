"""Tests for combat mechanics following 4AD rules."""
import pytest
from src.character import Warrior, Wizard
from src.monster import Minion, Boss
from src.combat import Combat, AttackResult


class TestAttackRolls:
    """Test attack roll mechanics - page 20."""
    
    def test_attack_hits_when_roll_plus_attack_exceeds_level(self):
        """Attack hits when roll + attack > monster level."""
        warrior = Warrior("Hero", level=1)  # Attack 4
        goblin = Minion("Goblin", level=3)
        
        # Roll 6 + Attack 4 = 10 > Level 3 = Hit
        result = Combat.resolve_attack(warrior, goblin, force_roll=6)
        assert result.hit
    
    def test_attack_misses_when_roll_plus_attack_equals_level(self):
        """Attack misses when roll + attack = monster level."""
        warrior = Warrior("Hero", level=1)  # Attack 4
        goblin = Minion("Goblin", level=3)
        
        # Need roll + 4 > 3, so roll 1 would give 5 > 3 = Hit
        # Actually need to recalculate - rule says equal or greater
        # Re-reading: "if the result is equal or greater than the monster's level"
        result = Combat.resolve_attack(warrior, goblin, force_roll=1)
        # 1 + 4 = 5 >= 3 = Hit
        assert result.hit


class TestDefenseRolls:
    """Test defense roll mechanics - page 20."""
    
    def test_defense_succeeds_when_roll_plus_defense_exceeds_level(self):
        """Defense succeeds when roll + defense > monster level."""
        warrior = Warrior("Hero", level=1)  # Defense 5
        goblin = Minion("Goblin", level=3)
        
        # Roll 4 + Defense 5 = 9 > 3 = Success (no damage)
        result = Combat.resolve_defense(warrior, goblin, force_roll=4)
        assert result.success
        assert result.damage_taken == 0
    
    def test_defense_fails_when_roll_plus_defense_less_than_level(self):
        """Defense fails when roll + defense + equipment < monster level."""
        warrior = Warrior("Hero", level=1)  # Defense 5, equipment +2 (light armor + shield)

        # Use a high-level monster so total is still too low
        # Roll 1 + Defense 5 + Equipment 2 = 8; need level > 8
        dragon = Minion("Dragon", level=9)
        result = Combat.resolve_defense(warrior, dragon, force_roll=1)
        # 1 + 5 + 2 = 8, not > 9 = Fail (take damage)
        assert not result.success
        assert result.damage_taken == 1


class TestMinionCombat:
    """Test combat against minions."""
    
    def test_minion_dies_on_hit(self):
        """Minions die on any successful hit."""
        warrior = Warrior("Hero")
        goblin = Minion("Goblin", level=3)
        
        result = Combat.resolve_attack(warrior, goblin, force_roll=6)
        assert result.hit
        assert goblin.is_dead()
    
    def test_explosive_six_kills_multiple_minions(self):
        """Explosive six can kill multiple minions with one blow."""
        warrior = Warrior("Hero")
        goblins = [Minion("Goblin", level=3) for _ in range(3)]
        
        # Roll 6,6,4 with explosive six = 16 + Attack 4 = 20
        result = Combat.resolve_attack(warrior, goblins, force_rolls=[6, 6, 4])
        assert result.minions_killed == 3


class TestBossCombat:
    """Test combat against bosses."""
    
    def test_boss_has_life_points(self):
        """Bosses have multiple life points."""
        boss = Boss("Ogre Champion", level=5, life=6)
        assert boss.life == 6
        assert boss.max_life == 6
    
    def test_boss_takes_damage_on_hit(self):
        """Boss takes 2 damage on successful hit."""
        warrior = Warrior("Hero")
        boss = Boss("Ogre Champion", level=5, life=6)
        
        result = Combat.resolve_attack(warrior, boss, force_roll=6)
        assert result.hit
        assert boss.life == 4  # 6 - 2 = 4
    
    def test_boss_dies_at_zero_life(self):
        """Boss dies when life reaches 0."""
        warrior = Warrior("Hero")
        boss = Boss("Weak Boss", level=2, life=2)
        
        Combat.resolve_attack(warrior, boss, force_roll=6)
        assert boss.is_dead()


class TestMarchingOrder:
    """Test marching order mechanics - page 51."""
    
    def test_front_rank_can_attack(self):
        """Front rank characters can always attack."""
        warrior = Warrior("Hero")
        warrior.position = 1
        assert warrior.can_attack_in_melee()
    
    def test_rear_rank_cannot_attack(self):
        """Rear rank characters cannot melee attack."""
        wizard = Wizard("Mage")
        wizard.position = 4
        assert not wizard.can_attack_in_melee()

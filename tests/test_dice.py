"""Tests for dice rolling mechanics following 4AD rules."""
import pytest
from src.dice import roll_d6, roll_2d6, roll_d66, explosive_six, DiceResult


class TestDiceRolling:
    """Test dice rolling mechanics."""
    
    def test_roll_d6_returns_1_to_6(self):
        """d6 should return value between 1 and 6."""
        for _ in range(100):
            result = roll_d6()
            assert 1 <= result <= 6
    
    def test_roll_2d6_returns_2_to_12(self):
        """2d6 should return value between 2 and 12."""
        for _ in range(100):
            result = roll_2d6()
            assert 2 <= result <= 12
    
    def test_roll_d66_returns_valid_range(self):
        """d66 should return values from 11, 12... 16, 21... 66."""
        valid_results = {10 + i + j*10 for i in range(1, 7) for j in range(1, 7)}
        for _ in range(100):
            result = roll_d66()
            assert result in valid_results
    
    def test_explosive_six_returns_dice_result(self):
        """Explosive six should return DiceResult with total and details."""
        result = explosive_six()
        assert isinstance(result, DiceResult)
        assert hasattr(result, 'total')
        assert hasattr(result, 'rolls')
        assert result.total >= 1


class TestExplosiveSixRule:
    """Test the explosive six rule from page 6 of rulebook."""
    
    def test_explosive_six_base_case(self):
        """Rolling without six gives single roll."""
        # Mock test - when no six is rolled
        result = explosive_six(force_rolls=[3])
        assert result.total == 3
        assert len(result.rolls) == 1
    
    def test_explosive_six_triggers_on_six(self):
        """Rolling a 6 should trigger another roll."""
        result = explosive_six(force_rolls=[6, 3])
        assert result.total == 9
        assert len(result.rolls) == 2
    
    def test_explosive_six_chain(self):
        """Multiple sixes should chain."""
        result = explosive_six(force_rolls=[6, 6, 6, 2])
        assert result.total == 20
        assert len(result.rolls) == 4

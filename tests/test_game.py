"""Tests for GameManager, focusing on the attack() targeting logic."""
import pytest
from src.game import GameManager
from src.monster import Boss


def _setup_game_with_combat(num_monsters: int = 2) -> tuple:
    """Set up a GameManager in active combat with Boss monsters.

    Uses level-1 bosses with 10 life so the warrior always hits/defends
    and monsters survive multiple attacks, keeping combat active.
    """
    gm = GameManager("test-game")
    player_id = gm.add_player("Alice")
    gm.create_character(player_id, "Warrior", "Brynn")
    gm.start()

    monsters = [Boss(f"Monster {idx}", level=1, life=10) for idx in range(num_monsters)]
    gm.current_monsters = monsters
    gm.combat_active = True
    return gm, monsters


class TestAttackTargeting:
    """Tests for attack() target_idx selection logic."""

    def test_attack_targets_first_monster_by_default(self):
        """attack() with no args targets the first living monster."""
        gm, monsters = _setup_game_with_combat(2)
        result = gm.attack()
        assert result.get("target") == monsters[0].name

    def test_attack_honors_target_idx(self):
        """attack(target_idx=1) targets the second monster when it is alive."""
        gm, monsters = _setup_game_with_combat(2)
        result = gm.attack(target_idx=1)
        assert result.get("target") == monsters[1].name

    def test_attack_falls_back_when_idx_targets_dead_monster(self):
        """attack(target_idx=0) falls back to first living monster when idx 0 is dead."""
        gm, monsters = _setup_game_with_combat(2)
        monsters[0].life = 0  # kill first monster manually
        result = gm.attack(target_idx=0)
        assert result.get("target") == monsters[1].name

    def test_attack_falls_back_when_idx_out_of_range(self):
        """attack(target_idx=99) falls back to first living monster on out-of-range index."""
        gm, monsters = _setup_game_with_combat(2)
        result = gm.attack(target_idx=99)
        assert result.get("target") == monsters[0].name

    def test_attack_returns_error_when_no_combat(self):
        """attack() returns an error dict when no combat is active."""
        gm = GameManager("test-game")
        result = gm.attack()
        assert "error" in result

    def test_attack_returns_error_with_no_living_targets(self):
        """attack() returns an error when all monsters are dead."""
        gm, monsters = _setup_game_with_combat(2)
        for m in monsters:
            m.life = 0
        result = gm.attack()
        assert "error" in result

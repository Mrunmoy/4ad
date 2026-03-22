"""Tests for GameManager buy_equipment and sell_equipment."""
import pytest
from src.game import GameManager


def _setup_game_with_warrior():
    """Create a game with one warrior player for testing."""
    gm = GameManager("test-game")
    pid = gm.add_player("TestPlayer")
    gm.create_character(pid, "Warrior", "TestWarrior")
    return gm, pid


class TestBuyEquipment:
    """Test GameManager.buy_equipment()."""

    def test_buy_bandage_success(self):
        gm, pid = _setup_game_with_warrior()
        player = gm.players[pid]
        # Ensure enough gold
        player.character.inventory.gold = 100
        result = gm.buy_equipment(pid, "bandage")
        assert result.get("success") is True
        assert result["cost"] == 5
        assert player.character.inventory.gold == 95

    def test_buy_insufficient_gold(self):
        gm, pid = _setup_game_with_warrior()
        player = gm.players[pid]
        player.character.inventory.gold = 1
        result = gm.buy_equipment(pid, "potion_of_healing")
        assert "error" in result

    def test_buy_invalid_item(self):
        gm, pid = _setup_game_with_warrior()
        result = gm.buy_equipment(pid, "nonexistent_item")
        assert "error" in result

    def test_buy_invalid_player(self):
        gm, _ = _setup_game_with_warrior()
        result = gm.buy_equipment("bad-id", "bandage")
        assert "error" in result

    def test_buy_class_restricted_item(self):
        """Wizard cannot buy heavy armor."""
        gm = GameManager("test-game")
        pid = gm.add_player("WizPlayer")
        gm.create_character(pid, "Wizard", "Gandalf")
        player = gm.players[pid]
        player.character.inventory.gold = 100
        result = gm.buy_equipment(pid, "heavy_armor")
        assert "error" in result


class TestSellEquipment:
    """Test GameManager.sell_equipment()."""

    def test_sell_weapon(self):
        gm, pid = _setup_game_with_warrior()
        player = gm.players[pid]
        initial_gold = player.character.inventory.gold
        # Warrior starts with a Hand Weapon (cost 6, sell for 3)
        result = gm.sell_equipment(pid, 0, "weapons")
        assert result.get("success") is True
        assert result["gold_earned"] == 3
        assert player.character.inventory.gold == initial_gold + 3

    def test_sell_armor(self):
        gm, pid = _setup_game_with_warrior()
        player = gm.players[pid]
        initial_gold = player.character.inventory.gold
        # Warrior starts with Light Armor (cost 10, sell for 5)
        result = gm.sell_equipment(pid, 0, "armor")
        assert result.get("success") is True
        assert result["gold_earned"] == 5

    def test_sell_shield(self):
        gm, pid = _setup_game_with_warrior()
        player = gm.players[pid]
        initial_gold = player.character.inventory.gold
        # Warrior starts with a Shield (cost 5, sell for 2)
        result = gm.sell_equipment(pid, 0, "shields")
        assert result.get("success") is True
        assert result["gold_earned"] == 2

    def test_sell_invalid_index(self):
        gm, pid = _setup_game_with_warrior()
        result = gm.sell_equipment(pid, 99, "weapons")
        assert "error" in result

    def test_sell_invalid_slot_type(self):
        gm, pid = _setup_game_with_warrior()
        result = gm.sell_equipment(pid, 0, "magic_items")
        assert "error" in result

    def test_sell_no_armor(self):
        """Wizard has no armor to sell."""
        gm = GameManager("test-game")
        pid = gm.add_player("WizPlayer")
        gm.create_character(pid, "Wizard", "Gandalf")
        result = gm.sell_equipment(pid, 0, "armor")
        assert "error" in result

"""Comprehensive tests for the treasure and loot system."""
import pytest
from src.treasure import (
    roll_treasure, roll_magic_treasure, roll_random_spell,
    distribute_gold, TreasureResult,
    SPELL_SCROLL_TABLE, MAGIC_TREASURE_TABLE,
    MONSTER_TREASURE_MODIFIERS,
)
from src.equipment import Weapon, Item


# ---------------------------------------------------------------------------
# Spell scroll tests
# ---------------------------------------------------------------------------

class TestSpellScrolls:
    """Test random spell scroll generation."""

    def test_all_six_spells(self):
        expected = {
            1: "Blessing", 2: "Fireball", 3: "Lightning Bolt",
            4: "Sleep", 5: "Escape", 6: "Protect",
        }
        for roll, spell in expected.items():
            assert roll_random_spell(force_roll=roll) == spell

    def test_random_spell_returns_valid(self):
        # No force_roll, just verify it returns one of the valid spells
        result = roll_random_spell()
        assert result in SPELL_SCROLL_TABLE.values()


# ---------------------------------------------------------------------------
# Magic treasure tests
# ---------------------------------------------------------------------------

class TestMagicTreasure:
    """Test magic treasure table."""

    def test_wand_of_sleep(self):
        item = roll_magic_treasure(force_roll=1)
        assert isinstance(item, Item)
        assert item.name == "Wand of Sleep"
        assert item.charges == 3
        assert item.is_magic is True

    def test_ring_of_teleportation(self):
        item = roll_magic_treasure(force_roll=2)
        assert isinstance(item, Item)
        assert item.name == "Ring of Teleportation"
        assert item.charges == 1
        assert item.is_magic is True

    def test_fools_gold(self):
        item = roll_magic_treasure(force_roll=3)
        assert isinstance(item, Item)
        assert item.name == "Fool's Gold Purse"
        assert item.charges == 1

    def test_magic_weapon(self):
        item = roll_magic_treasure(force_roll=4)
        assert isinstance(item, Weapon)
        assert item.is_magic is True
        assert item.attack_modifier >= 0  # at least +0 for light, +1 for hand

    def test_potion_of_healing(self):
        item = roll_magic_treasure(force_roll=5)
        assert isinstance(item, Item)
        assert item.name == "Potion of Healing"
        assert item.is_magic is True

    def test_fireball_staff(self):
        item = roll_magic_treasure(force_roll=6)
        assert isinstance(item, Item)
        assert item.name == "Fireball Staff"
        assert item.charges == 2
        assert item.is_magic is True


# ---------------------------------------------------------------------------
# Treasure table tests
# ---------------------------------------------------------------------------

class TestTreasureTable:
    """Test the main treasure table (d6 + modifier)."""

    def test_nothing_on_zero_or_less(self):
        result = roll_treasure(modifier=-1, force_d6=1)
        assert result.gold == 0
        assert result.item is None
        assert "Nothing" in result.description

    def test_d6_gold_on_1(self):
        result = roll_treasure(modifier=0, force_d6=1, force_gold_rolls=[4])
        assert result.gold == 4
        assert result.item is None

    def test_2d6_gold_on_2(self):
        result = roll_treasure(modifier=0, force_d6=2, force_gold_rolls=[3, 4])
        assert result.gold == 7  # 3 + 4

    def test_scroll_on_3(self):
        result = roll_treasure(modifier=0, force_d6=3, force_spell_roll=2)
        assert result.spell_scroll == "Fireball"
        assert result.gold == 0

    def test_gem_on_4(self):
        result = roll_treasure(modifier=0, force_d6=4, force_gold_rolls=[3, 4])
        assert result.gold == 35  # (3+4) * 5

    def test_jewelry_on_5(self):
        result = roll_treasure(modifier=0, force_d6=5, force_gold_rolls=[2, 3, 4])
        assert result.gold == 90  # (2+3+4) * 10

    def test_magic_treasure_on_6_plus(self):
        result = roll_treasure(modifier=0, force_d6=6, force_magic_roll=1)
        assert result.item is not None
        assert result.item.name == "Wand of Sleep"

    def test_high_modifier_gives_magic(self):
        # d6=3 + modifier=3 = 6 -> magic treasure
        result = roll_treasure(modifier=3, force_d6=3, force_magic_roll=5)
        assert result.item is not None
        assert result.item.name == "Potion of Healing"


# ---------------------------------------------------------------------------
# Monster-specific treasure modifiers
# ---------------------------------------------------------------------------

class TestMonsterTreasureModifiers:
    """Test monster-specific treasure modifiers."""

    def test_goblin_minus_one(self):
        # Goblin: -1 modifier. d6=2 + (-1) = 1 -> d6 gold
        result = roll_treasure(monster_name="Goblin", force_d6=2, force_gold_rolls=[5])
        assert result.gold == 5

    def test_hobgoblin_plus_one(self):
        # Hobgoblin: +1. d6=5 + 1 = 6 -> magic treasure
        result = roll_treasure(monster_name="Hobgoblin", force_d6=5, force_magic_roll=3)
        assert result.item is not None
        assert result.item.name == "Fool's Gold Purse"

    def test_orc_special_d6_x_d6(self):
        # Orcs: d6 x d6 gold, never magic
        result = roll_treasure(monster_name="Orc", force_gold_rolls=[4, 5])
        assert result.gold == 20  # 4 * 5
        assert result.item is None

    def test_dragon_plus_three(self):
        # Dragon: +3. d6=3 + 3 = 6 -> magic
        result = roll_treasure(monster_name="Dragon", force_d6=3, force_magic_roll=4)
        assert result.item is not None
        assert isinstance(result.item, Weapon)

    def test_demon_plus_two(self):
        # Demon: +2. d6=4 + 2 = 6 -> magic
        result = roll_treasure(monster_name="Demon", force_d6=4, force_magic_roll=6)
        assert result.item is not None
        assert result.item.name == "Fireball Staff"

    def test_vampire_plus_one(self):
        # Vampire: +1. d6=1 + 1 = 2 -> 2d6 gold
        result = roll_treasure(monster_name="Vampire", force_d6=1, force_gold_rolls=[5, 6])
        assert result.gold == 11

    def test_unknown_monster_no_modifier(self):
        # Unknown monster: +0
        result = roll_treasure(monster_name="Skeleton", force_d6=1, force_gold_rolls=[3])
        assert result.gold == 3


# ---------------------------------------------------------------------------
# Magic weapon sub-types
# ---------------------------------------------------------------------------

class TestMagicWeaponTypes:
    """Test magic weapon type rolls."""

    def test_magic_weapon_roll_1_crushing_light(self):
        result = roll_treasure(force_d6=6, force_magic_roll=4, force_weapon_roll=1)
        w = result.item
        assert isinstance(w, Weapon)
        assert w.damage_type == "crushing"
        assert w.is_magic is True

    def test_magic_weapon_roll_2_slashing_light(self):
        result = roll_treasure(force_d6=6, force_magic_roll=4, force_weapon_roll=2)
        w = result.item
        assert w.damage_type == "slashing"

    def test_magic_weapon_roll_3_crushing_hand(self):
        result = roll_treasure(force_d6=6, force_magic_roll=4, force_weapon_roll=3)
        w = result.item
        assert w.damage_type == "crushing"
        assert w.attack_modifier == 1

    def test_magic_weapon_roll_4_5_slashing_hand(self):
        for roll in (4, 5):
            result = roll_treasure(force_d6=6, force_magic_roll=4, force_weapon_roll=roll)
            w = result.item
            assert w.damage_type == "slashing"
            assert w.attack_modifier == 1

    def test_magic_weapon_roll_6_bow(self):
        result = roll_treasure(force_d6=6, force_magic_roll=4, force_weapon_roll=6)
        w = result.item
        assert w.is_ranged is True
        assert "Bow" in w.name


# ---------------------------------------------------------------------------
# Gold distribution tests
# ---------------------------------------------------------------------------

class TestGoldDistribution:
    """Test gold distribution among party members."""

    def _make_char(self, name, class_type="Warrior", dead=False):
        from src.character import create_character
        c = create_character(class_type, name)
        if dead:
            c.life = 0
        return c

    def test_even_split(self):
        chars = [self._make_char("A"), self._make_char("B")]
        # Reset gold to 0 for clean test
        for c in chars:
            c.inventory.gold = 0
        dist = distribute_gold(10, chars)
        assert dist["A"] == 5
        assert dist["B"] == 5

    def test_dead_characters_excluded(self):
        chars = [self._make_char("A"), self._make_char("B", dead=True)]
        chars[0].inventory.gold = 0
        dist = distribute_gold(10, chars)
        assert "A" in dist
        assert "B" not in dist
        assert dist["A"] == 10

    def test_dwarf_gets_at_least_one(self):
        chars = [
            self._make_char("Fighter", "Warrior"),
            self._make_char("Gimli", "Dwarf"),
        ]
        for c in chars:
            c.inventory.gold = 0
        # 1 gold split between 2: share = 0, but dwarf gets 1
        dist = distribute_gold(1, chars)
        assert dist.get("Gimli", 0) >= 1

    def test_zero_gold_returns_empty(self):
        chars = [self._make_char("A")]
        dist = distribute_gold(0, chars)
        assert dist == {}

    def test_no_characters_returns_empty(self):
        dist = distribute_gold(100, [])
        assert dist == {}

    def test_gold_cap_respected(self):
        chars = [self._make_char("A")]
        chars[0].inventory.gold = 195
        dist = distribute_gold(100, chars)
        # Max 200, so only 5 can be added
        assert dist["A"] == 5
        assert chars[0].inventory.gold == 200


# ---------------------------------------------------------------------------
# TreasureResult serialization
# ---------------------------------------------------------------------------

class TestTreasureResultSerialization:
    """Test TreasureResult to_dict."""

    def test_basic_gold(self):
        tr = TreasureResult(description="Found gold", gold=10)
        d = tr.to_dict()
        assert d["description"] == "Found gold"
        assert d["gold"] == 10
        assert "spell_scroll" not in d

    def test_with_spell(self):
        tr = TreasureResult(description="Scroll", spell_scroll="Fireball")
        d = tr.to_dict()
        assert d["spell_scroll"] == "Fireball"

    def test_with_item(self):
        tr = TreasureResult(description="Magic",
                            item=Item("Wand", 0, False, is_magic=True))
        d = tr.to_dict()
        assert d["item"] == "Wand"


# ---------------------------------------------------------------------------
# Magic item sell prices
# ---------------------------------------------------------------------------

class TestMagicItemSellPrices:
    """Test sell prices for magic items."""

    def test_wand_of_sleep_sell_price(self):
        wand = roll_magic_treasure(force_roll=1)
        assert wand.sell_price() == 90  # 30 * 3 charges

    def test_ring_sell_price(self):
        ring = roll_magic_treasure(force_roll=2)
        assert ring.sell_price() == 40  # 1 charge

    def test_fools_gold_sell_price(self):
        fg = roll_magic_treasure(force_roll=3)
        # Fool's Gold is not magic (usable by any class), sell price = cost // 2 = 0
        assert fg.sell_price() == 0

    def test_magic_weapon_sell_price(self):
        w = roll_magic_treasure(force_roll=4)
        assert w.sell_price() == 50

    def test_fireball_staff_sell_price(self):
        staff = roll_magic_treasure(force_roll=6)
        assert staff.sell_price() == 60  # 30 * 2 charges


# ---------------------------------------------------------------------------
# Gold distribution edge cases
# ---------------------------------------------------------------------------

class TestGoldDistributionEdgeCases:
    """Test distribute_gold with large remainders and edge cases."""

    def _make_char(self, name, class_type="Warrior", dead=False):
        from src.character import create_character
        c = create_character(class_type, name)
        if dead:
            c.life = 0
        return c

    def test_large_remainder_no_gold_lost(self):
        """100gp among 3 characters: no gold should be silently lost."""
        chars = [
            self._make_char("A"),
            self._make_char("B"),
            self._make_char("C"),
        ]
        for c in chars:
            c.inventory.gold = 0
        dist = distribute_gold(100, chars)
        total_distributed = sum(dist.values())
        assert total_distributed == 100

    def test_remainder_distributed_round_robin(self):
        """7gp among 3: should be 3+2+2 or 2+3+2 etc., total 7."""
        chars = [
            self._make_char("A"),
            self._make_char("B"),
            self._make_char("C"),
        ]
        for c in chars:
            c.inventory.gold = 0
        dist = distribute_gold(7, chars)
        total = sum(dist.values())
        assert total == 7
        # Each should get at least 2 (floor(7/3))
        for name in ["A", "B", "C"]:
            assert dist.get(name, 0) >= 2

    def test_gold_cap_stops_distribution(self):
        """When all inventories are full, remaining gold is dropped."""
        chars = [self._make_char("A")]
        chars[0].inventory.gold = 200  # at cap
        dist = distribute_gold(50, chars)
        # Nothing can be added
        assert dist.get("A", 0) == 0

    def test_dwarf_minimum_with_zero_share(self):
        """Dwarf gets at least 1 gold even when share rounds to 0."""
        chars = [
            self._make_char("A", "Warrior"),
            self._make_char("B", "Warrior"),
            self._make_char("C", "Warrior"),
            self._make_char("Gimli", "Dwarf"),
        ]
        for c in chars:
            c.inventory.gold = 0
        # 1 gold among 4: share = 0, but dwarf should get 1
        dist = distribute_gold(1, chars)
        assert dist.get("Gimli", 0) >= 1

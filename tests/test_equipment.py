"""Comprehensive tests for the equipment system."""
import pytest
from src.equipment import (
    Weapon, Armor, Item, Inventory,
    WEAPON_LIST, ARMOR_LIST, ITEM_LIST, SHOP_INVENTORY,
    MAX_GOLD_DEFAULT, MAX_GOLD_DWARF, MAX_WEAPON_SLOTS, MAX_SHIELDS,
    MAX_ITEM_SLOTS,
    CLASS_WEAPON_RESTRICTIONS, CLASS_ARMOR_RESTRICTIONS,
)


# ---------------------------------------------------------------------------
# Weapon tests
# ---------------------------------------------------------------------------

class TestWeapons:
    """Test weapon definitions and properties."""

    def test_hand_weapon(self):
        w = WEAPON_LIST["hand_weapon"]
        assert w.name == "Hand Weapon"
        assert w.cost == 6
        assert w.hands == 1
        assert w.attack_modifier == 0
        assert w.damage_type == "slashing"
        assert w.is_ranged is False

    def test_light_hand_weapon(self):
        w = WEAPON_LIST["light_hand_weapon"]
        assert w.cost == 5
        assert w.hands == 1
        assert w.attack_modifier == -1
        assert w.damage_type == "slashing"

    def test_two_handed_weapon(self):
        w = WEAPON_LIST["two_handed_weapon"]
        assert w.cost == 15
        assert w.hands == 2
        assert w.attack_modifier == 1

    def test_bow(self):
        w = WEAPON_LIST["bow"]
        assert w.cost == 15
        assert w.hands == 2
        assert w.attack_modifier == 0
        assert w.damage_type == "piercing"
        assert w.is_ranged is True

    def test_sling(self):
        w = WEAPON_LIST["sling"]
        assert w.cost == 4
        assert w.hands == 1
        assert w.attack_modifier == -1
        assert w.damage_type == "crushing"
        assert w.is_ranged is True

    def test_weapon_sell_price_half(self):
        w = WEAPON_LIST["hand_weapon"]
        assert w.sell_price() == 3  # 6 // 2

    def test_magic_weapon_sell_price(self):
        w = Weapon(name="Magic Sword", cost=0, hands=1,
                   attack_modifier=1, damage_type="slashing", is_magic=True)
        assert w.sell_price() == 50


# ---------------------------------------------------------------------------
# Armor tests
# ---------------------------------------------------------------------------

class TestArmor:
    """Test armor definitions and properties."""

    def test_light_armor(self):
        a = ARMOR_LIST["light_armor"]
        assert a.name == "Light Armor"
        assert a.cost == 10
        assert a.defense_bonus == 1
        assert a.is_heavy is False
        assert a.save_penalty == 0

    def test_heavy_armor(self):
        a = ARMOR_LIST["heavy_armor"]
        assert a.cost == 30
        assert a.defense_bonus == 2
        assert a.is_heavy is True
        assert a.save_penalty == -1

    def test_shield(self):
        a = ARMOR_LIST["shield"]
        assert a.cost == 5
        assert a.defense_bonus == 1
        assert a.is_shield is True

    def test_armor_sell_price(self):
        assert ARMOR_LIST["light_armor"].sell_price() == 5
        assert ARMOR_LIST["heavy_armor"].sell_price() == 15
        assert ARMOR_LIST["shield"].sell_price() == 2


# ---------------------------------------------------------------------------
# Item tests
# ---------------------------------------------------------------------------

class TestItems:
    """Test item definitions."""

    def test_lantern(self):
        it = ITEM_LIST["lantern"]
        assert it.cost == 4
        assert it.one_use is False

    def test_rope(self):
        it = ITEM_LIST["rope"]
        assert it.cost == 4
        assert it.one_use is False

    def test_bandage(self):
        it = ITEM_LIST["bandage"]
        assert it.cost == 5
        assert it.one_use is True

    def test_potion_of_healing(self):
        it = ITEM_LIST["potion_of_healing"]
        assert it.cost == 100
        assert it.one_use is True

    def test_holy_water(self):
        it = ITEM_LIST["holy_water"]
        assert it.cost == 30
        assert it.one_use is True

    def test_torch(self):
        it = ITEM_LIST["torch"]
        assert it.cost == 2
        assert it.one_use is True


# ---------------------------------------------------------------------------
# Shop inventory tests
# ---------------------------------------------------------------------------

class TestShopInventory:
    """Test combined shop inventory."""

    def test_shop_contains_all_weapons(self):
        for key in WEAPON_LIST:
            assert key in SHOP_INVENTORY

    def test_shop_contains_all_armor(self):
        for key in ARMOR_LIST:
            assert key in SHOP_INVENTORY

    def test_shop_contains_all_items(self):
        for key in ITEM_LIST:
            assert key in SHOP_INVENTORY


# ---------------------------------------------------------------------------
# Inventory tests
# ---------------------------------------------------------------------------

class TestInventory:
    """Test inventory management."""

    def _make_inv(self, class_type="Warrior", gold=100):
        inv = Inventory(class_type=class_type)
        inv.gold = gold
        return inv

    # -- adding / removing --

    def test_add_weapon(self):
        inv = self._make_inv()
        w = Weapon("Hand Weapon", 6, 1, 0, "slashing")
        assert inv.add_item(w) is True
        assert len(inv.weapons) == 1

    def test_add_armor(self):
        inv = self._make_inv()
        a = Armor("Light Armor", 10, 1)
        assert inv.add_item(a) is True
        assert inv.armor is not None

    def test_add_shield(self):
        inv = self._make_inv()
        s = Armor("Shield", 5, 1, is_shield=True)
        assert inv.add_item(s) is True
        assert len(inv.shields) == 1

    def test_add_item(self):
        inv = self._make_inv()
        it = Item("Bandage", 5, True)
        assert inv.add_item(it) is True
        assert len(inv.items) == 1

    def test_remove_weapon(self):
        inv = self._make_inv()
        w = Weapon("Hand Weapon", 6, 1, 0, "slashing")
        inv.add_item(w)
        assert inv.remove_item(w) is True
        assert len(inv.weapons) == 0

    def test_remove_armor(self):
        inv = self._make_inv()
        a = Armor("Light Armor", 10, 1)
        inv.add_item(a)
        assert inv.remove_item(a) is True
        assert inv.armor is None

    def test_remove_shield(self):
        inv = self._make_inv()
        s = Armor("Shield", 5, 1, is_shield=True)
        inv.add_item(s)
        assert inv.remove_item(s) is True
        assert len(inv.shields) == 0

    def test_remove_item(self):
        inv = self._make_inv()
        it = Item("Bandage", 5, True)
        inv.add_item(it)
        assert inv.remove_item(it) is True
        assert len(inv.items) == 0

    def test_remove_nonexistent_returns_false(self):
        inv = self._make_inv()
        w = Weapon("Sword", 6, 1, 0, "slashing")
        assert inv.remove_item(w) is False

    # -- weapon slot limits --

    def test_max_weapon_slots_one_handed(self):
        inv = self._make_inv()
        for _ in range(3):
            inv.add_item(Weapon("Hand Weapon", 6, 1, 0, "slashing"))
        assert len(inv.weapons) == 3
        # 4th should fail
        assert inv.add_item(Weapon("Hand Weapon", 6, 1, 0, "slashing")) is False

    def test_two_handed_uses_two_slots(self):
        inv = self._make_inv()
        inv.add_item(Weapon("Two-Handed Weapon", 15, 2, 1, "slashing"))
        assert inv._weapon_slots_used() == 2
        # Can add one more 1-hand weapon
        assert inv.add_item(Weapon("Light Hand Weapon", 5, 1, -1, "slashing")) is True
        # But not another
        assert inv.add_item(Weapon("Hand Weapon", 6, 1, 0, "slashing")) is False

    # -- shield limits --

    def test_max_two_shields(self):
        inv = self._make_inv()
        inv.add_item(Armor("Shield", 5, 1, is_shield=True))
        inv.add_item(Armor("Shield", 5, 1, is_shield=True))
        assert len(inv.shields) == 2
        assert inv.add_item(Armor("Shield", 5, 1, is_shield=True)) is False

    # -- armor limit --

    def test_only_one_armor(self):
        inv = self._make_inv()
        inv.add_item(Armor("Light Armor", 10, 1))
        assert inv.add_item(Armor("Heavy Armor", 30, 2, is_heavy=True)) is False

    # -- gold limits --

    def test_gold_cap_default(self):
        inv = Inventory(class_type="Warrior", max_gold=MAX_GOLD_DEFAULT)
        added = inv.add_gold(250)
        assert inv.gold == 200
        assert added == 200

    def test_gold_cap_dwarf(self):
        inv = Inventory(class_type="Dwarf", max_gold=MAX_GOLD_DWARF)
        added = inv.add_gold(300)
        assert inv.gold == 250
        assert added == 250

    def test_spend_gold_success(self):
        inv = self._make_inv(gold=50)
        assert inv.spend_gold(30) is True
        assert inv.gold == 20

    def test_spend_gold_insufficient(self):
        inv = self._make_inv(gold=10)
        assert inv.spend_gold(20) is False
        assert inv.gold == 10

    # -- sell --

    def test_sell_item_returns_half_price(self):
        inv = self._make_inv(gold=0)
        w = Weapon("Hand Weapon", 6, 1, 0, "slashing")
        inv.add_item(w)
        earned = inv.sell_item(w)
        assert earned == 3
        assert inv.gold == 3
        assert len(inv.weapons) == 0

    # -- defense / attack --

    def test_get_defense_bonus(self):
        inv = self._make_inv()
        inv.add_item(Armor("Light Armor", 10, 1))
        inv.add_item(Armor("Shield", 5, 1, is_shield=True))
        assert inv.get_defense_bonus() == 2

    def test_get_attack_modifier(self):
        inv = self._make_inv()
        inv.add_item(Weapon("Light Hand Weapon", 5, 1, -1, "slashing"))
        inv.add_item(Weapon("Hand Weapon", 6, 1, 0, "slashing"))
        assert inv.get_attack_modifier() == 0  # best of -1, 0

    def test_get_attack_modifier_empty(self):
        inv = self._make_inv()
        assert inv.get_attack_modifier() == 0

    # -- save penalty --

    def test_heavy_armor_save_penalty(self):
        inv = self._make_inv()
        inv.add_item(Armor("Heavy Armor", 30, 2, is_heavy=True, save_penalty=-1))
        assert inv.get_save_penalty() == -1

    def test_no_armor_no_penalty(self):
        inv = self._make_inv()
        assert inv.get_save_penalty() == 0

    # -- class restrictions --

    def test_wizard_cannot_equip_armor(self):
        inv = self._make_inv(class_type="Wizard")
        a = Armor("Light Armor", 10, 1)
        assert inv.can_equip(a) is False

    def test_wizard_cannot_equip_shield(self):
        inv = self._make_inv(class_type="Wizard")
        s = Armor("Shield", 5, 1, is_shield=True)
        assert inv.can_equip(s) is False

    def test_barbarian_cannot_equip_magic_wand(self):
        inv = self._make_inv(class_type="Barbarian")
        wand = Item("Wand of Sleep", 0, False, charges=3, is_magic=True)
        assert inv.can_equip(wand) is False

    def test_barbarian_can_equip_potion_of_healing(self):
        inv = self._make_inv(class_type="Barbarian")
        pot = Item("Potion of Healing", 100, True, is_magic=True)
        assert inv.can_equip(pot) is True

    def test_barbarian_cannot_equip_bow(self):
        inv = self._make_inv(class_type="Barbarian")
        bow = Weapon("Bow", 15, 2, 0, "slashing", is_ranged=True)
        assert inv.can_equip(bow) is False

    def test_halfling_cannot_equip_hand_weapon(self):
        inv = self._make_inv(class_type="Halfling")
        w = Weapon("Hand Weapon", 6, 1, 0, "slashing")
        assert inv.can_equip(w) is False

    def test_halfling_can_equip_sling(self):
        inv = self._make_inv(class_type="Halfling")
        s = Weapon("Sling", 4, 1, -1, "crushing", is_ranged=True)
        assert inv.can_equip(s) is True

    # -- item slot limit --

    def test_item_slot_limit(self):
        inv = self._make_inv()
        for i in range(MAX_ITEM_SLOTS):
            assert inv.add_item(Item(f"Item{i}", 1, True)) is True
        assert inv.add_item(Item("Extra", 1, True)) is False

    # -- utility --

    def test_has_lantern(self):
        inv = self._make_inv()
        assert inv.has_lantern() is False
        inv.add_item(Item("Lantern", 4, False))
        assert inv.has_lantern() is True

    def test_has_rope(self):
        inv = self._make_inv()
        assert inv.has_rope() is False
        inv.add_item(Item("Rope", 4, False))
        assert inv.has_rope() is True

    def test_carry_weight(self):
        inv = self._make_inv()
        inv.add_item(Weapon("Hand Weapon", 6, 1, 0, "slashing"))
        inv.add_item(Armor("Light Armor", 10, 1))
        inv.add_item(Armor("Shield", 5, 1, is_shield=True))
        inv.add_item(Item("Bandage", 5, True))
        # 1 weapon + 1 armor + 1 shield + 1 item = 4
        assert inv.get_carry_weight() == 4

    def test_to_dict(self):
        inv = self._make_inv(gold=42)
        inv.add_item(Weapon("Hand Weapon", 6, 1, 0, "slashing"))
        d = inv.to_dict()
        assert d["gold"] == 42
        assert len(d["weapons"]) == 1
        assert d["weapons"][0]["name"] == "Hand Weapon"


# ---------------------------------------------------------------------------
# Starting equipment tests (via character creation)
# ---------------------------------------------------------------------------

class TestStartingEquipment:
    """Test that each class gets correct starting equipment."""

    def test_warrior_starting_gear(self):
        from src.character import Warrior
        w = Warrior("TestWarrior")
        inv = w.inventory
        assert len(inv.weapons) == 1
        assert inv.weapons[0].name == "Hand Weapon"
        assert inv.armor is not None
        assert inv.armor.name == "Light Armor"
        assert len(inv.shields) == 1
        assert inv.has_lantern() is True
        assert inv.gold >= 2  # 2d6, min is 2

    def test_cleric_starting_gear(self):
        from src.character import Cleric
        c = Cleric("TestCleric")
        inv = c.inventory
        assert len(inv.weapons) == 1
        assert inv.weapons[0].name == "Hand Weapon"
        assert inv.armor.name == "Light Armor"
        assert len(inv.shields) == 1
        assert inv.gold >= 2  # 2d6

    def test_rogue_starting_gear(self):
        from src.character import Rogue
        r = Rogue("TestRogue")
        inv = r.inventory
        assert len(inv.weapons) == 1
        assert inv.weapons[0].name == "Light Hand Weapon"
        assert inv.armor.name == "Light Armor"
        assert inv.has_rope() is True
        assert inv.gold >= 3  # 3d6

    def test_wizard_starting_gear(self):
        from src.character import Wizard
        wiz = Wizard("TestWizard")
        inv = wiz.inventory
        assert len(inv.weapons) == 1
        assert inv.weapons[0].name == "Hand Weapon"  # staff
        assert inv.armor is None  # wizard gets no armor
        assert inv.gold >= 4  # 4d6

    def test_barbarian_starting_gear(self):
        from src.character import Barbarian
        b = Barbarian("TestBarbarian")
        inv = b.inventory
        assert len(inv.weapons) == 1
        assert inv.weapons[0].name == "Two-Handed Weapon"
        assert inv.armor is None
        assert len(inv.shields) == 0
        assert inv.gold >= 1  # 1d6

    def test_elf_starting_gear(self):
        from src.character import Elf
        e = Elf("TestElf")
        inv = e.inventory
        assert len(inv.weapons) == 2
        weapon_names = {w.name for w in inv.weapons}
        assert "Hand Weapon" in weapon_names
        assert "Bow" in weapon_names
        assert inv.armor.name == "Light Armor"
        assert inv.gold >= 3  # 3d6

    def test_dwarf_starting_gear(self):
        from src.character import Dwarf
        d = Dwarf("TestDwarf")
        inv = d.inventory
        assert len(inv.weapons) == 1
        assert inv.weapons[0].name == "Hand Weapon"
        assert inv.armor.name == "Light Armor"
        assert len(inv.shields) == 1
        assert inv.gold >= 2  # 2d6
        assert inv.max_gold == MAX_GOLD_DWARF  # 250

    def test_halfling_starting_gear(self):
        from src.character import Halfling
        h = Halfling("TestHalfling")
        inv = h.inventory
        assert len(inv.weapons) == 2
        weapon_names = {w.name for w in inv.weapons}
        assert "Light Hand Weapon" in weapon_names
        assert "Sling" in weapon_names
        assert inv.armor.name == "Light Armor"
        assert inv.gold >= 3  # 3d6

    def test_character_to_dict_includes_gold_and_inventory(self):
        from src.character import Warrior
        w = Warrior("TestWarrior")
        d = w.to_dict()
        assert "gold" in d
        assert "inventory" in d
        assert d["inventory"] is not None
        assert d["gold"] >= 2


# ---------------------------------------------------------------------------
# Barbarian magic weapon rejection test
# ---------------------------------------------------------------------------

class TestBarbarianMagicWeaponRejection:
    """Test that barbarians cannot equip magic weapons (M1)."""

    def test_barbarian_cannot_equip_magic_sword(self):
        inv = Inventory(class_type="Barbarian")
        magic_sword = Weapon(
            name="Magic Slashing Hand Weapon", cost=0, hands=1,
            attack_modifier=1, damage_type="slashing", is_magic=True,
        )
        assert inv.can_equip(magic_sword) is False

    def test_barbarian_cannot_equip_magic_bow(self):
        inv = Inventory(class_type="Barbarian")
        magic_bow = Weapon(
            name="Magic Bow", cost=0, hands=2,
            attack_modifier=1, damage_type="piercing",
            is_ranged=True, is_magic=True,
        )
        assert inv.can_equip(magic_bow) is False

    def test_barbarian_can_equip_normal_hand_weapon(self):
        inv = Inventory(class_type="Barbarian")
        hw = Weapon(
            name="Hand Weapon", cost=6, hands=1,
            attack_modifier=0, damage_type="slashing",
        )
        assert inv.can_equip(hw) is True

    def test_barbarian_can_equip_normal_two_handed(self):
        inv = Inventory(class_type="Barbarian")
        thw = Weapon(
            name="Two-Handed Weapon", cost=15, hands=2,
            attack_modifier=1, damage_type="slashing",
        )
        assert inv.can_equip(thw) is True

    def test_warrior_can_equip_magic_weapon(self):
        inv = Inventory(class_type="Warrior")
        magic_sword = Weapon(
            name="Magic Slashing Hand Weapon", cost=0, hands=1,
            attack_modifier=1, damage_type="slashing", is_magic=True,
        )
        assert inv.can_equip(magic_sword) is True

    def test_fools_gold_usable_by_barbarian(self):
        """Fool's Gold Purse is not magic; any class can use it."""
        inv = Inventory(class_type="Barbarian")
        fg = Item(
            name="Fool's Gold Purse", cost=0, one_use=True,
            description="1 charge. Auto-bribe any monster once. Any class.",
            charges=1, is_magic=False,
        )
        assert inv.can_equip(fg) is True

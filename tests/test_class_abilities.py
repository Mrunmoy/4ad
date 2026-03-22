"""Tests for class-specific abilities."""
import pytest
from src.character import (
    Warrior, Cleric, Rogue, Wizard,
    Barbarian, Elf, Dwarf, Halfling,
)
from src.monster import Monster, Minion, Boss


class TestWarriorAbilities:
    """Warrior class abilities."""

    def test_attack_bonus_equals_level(self):
        for lvl in range(1, 6):
            w = Warrior("W", level=lvl)
            assert w.attack_bonus() == lvl

    def test_can_use_all_armor(self):
        w = Warrior("W")
        assert w.can_use_heavy_armor()
        assert w.can_use_shield()

    def test_can_use_magic(self):
        w = Warrior("W")
        assert w.can_use_magic()


class TestClericAbilities:
    """Cleric class abilities."""

    def test_attack_bonus_half_level(self):
        c = Cleric("C", level=1)
        assert c.attack_bonus() == 0  # floor(1/2) = 0
        c2 = Cleric("C", level=2)
        assert c2.attack_bonus() == 1  # floor(2/2) = 1
        c4 = Cleric("C", level=4)
        assert c4.attack_bonus() == 2  # floor(4/2) = 2

    def test_attack_bonus_full_level_vs_undead(self):
        c = Cleric("C", level=3)
        undead = Monster("Zombie", level=3, is_undead=True)
        assert c.attack_bonus(target=undead) == 3

    def test_attack_bonus_full_level_vs_demon(self):
        c = Cleric("C", level=3)
        demon = Monster("Imp", level=3, is_demon=True)
        assert c.attack_bonus(target=demon) == 3

    def test_healing_3_uses(self):
        c = Cleric("C")
        assert c.healing_uses == 3

    def test_healing_restores_hp(self):
        c = Cleric("C")
        target = Warrior("W")
        target.take_damage(5)
        old_life = target.life
        healed = c.use_healing(target)
        assert healed > 0
        assert target.life > old_life

    def test_healing_uses_decrement(self):
        c = Cleric("C")
        target = Warrior("W")
        target.take_damage(3)
        c.use_healing(target)
        assert c.healing_uses == 2

    def test_healing_returns_0_when_exhausted(self):
        c = Cleric("C")
        target = Warrior("W")
        target.take_damage(3)
        for _ in range(3):
            c.use_healing(target)
        assert c.use_healing(target) == 0

    def test_blessing_3_uses(self):
        c = Cleric("C")
        assert c.blessing_uses == 3
        assert c.use_blessing() is True
        assert c.blessing_uses == 2

    def test_blessing_exhausted(self):
        c = Cleric("C")
        for _ in range(3):
            c.use_blessing()
        assert c.use_blessing() is False

    def test_save_bonus_vs_undead(self):
        c = Cleric("C", level=3)
        assert c.get_save_bonus("undead") == 3

    def test_save_bonus_vs_demon(self):
        c = Cleric("C", level=3)
        assert c.get_save_bonus("demon") == 3

    def test_no_save_bonus_vs_normal(self):
        c = Cleric("C", level=3)
        assert c.get_save_bonus("normal") == 0

    def test_can_cast_blessing(self):
        c = Cleric("C")
        assert c.can_cast("Blessing")

    def test_cannot_cast_fireball(self):
        c = Cleric("C")
        assert not c.can_cast("Fireball")


class TestRogueAbilities:
    """Rogue class abilities."""

    def test_attack_bonus_when_outnumbering(self):
        r = Rogue("R", level=3)
        assert r.attack_bonus(party_size=3, enemy_count=2) == 3

    def test_no_attack_bonus_when_outnumbered(self):
        r = Rogue("R", level=3)
        assert r.attack_bonus(party_size=2, enemy_count=3) == 0

    def test_no_attack_bonus_when_equal(self):
        r = Rogue("R", level=3)
        assert r.attack_bonus(party_size=2, enemy_count=2) == 0

    def test_defense_bonus_equals_level(self):
        for lvl in range(1, 6):
            r = Rogue("R", level=lvl)
            assert r.defense_bonus() == lvl

    def test_disarm_bonus_equals_level(self):
        r = Rogue("R", level=4)
        assert r.get_disarm_bonus() == 4

    def test_lockpick_bonus_equals_level(self):
        r = Rogue("R", level=3)
        assert r.get_lockpick_bonus() == 3

    def test_has_lockpicks(self):
        r = Rogue("R")
        assert r.has_lockpicks

    def test_cannot_use_heavy_armor(self):
        r = Rogue("R")
        assert not r.can_use_heavy_armor()


class TestWizardAbilities:
    """Wizard class abilities."""

    def test_spell_slots_at_level_1(self):
        w = Wizard("W")
        assert w.spell_slots == 3  # 2 + 1

    def test_spell_slots_at_level_5(self):
        w = Wizard("W", level=5)
        assert w.spell_slots == 7  # 2 + 5

    def test_spell_attack_bonus_equals_level(self):
        w = Wizard("W", level=3)
        assert w.spell_attack_bonus() == 3

    def test_no_melee_attack_bonus(self):
        w = Wizard("W", level=5)
        assert w.attack_bonus() == 0

    def test_knows_all_6_spells(self):
        w = Wizard("W")
        assert len(w.spells) == 6
        assert "Blessing" in w.spells
        assert "Fireball" in w.spells

    def test_can_cast_until_slots_exhausted(self):
        w = Wizard("W")  # 3 slots
        assert w.can_cast("Fireball")
        w.cast_spell("Fireball")
        w.cast_spell("Fireball")
        w.cast_spell("Fireball")
        assert not w.can_cast("Fireball")

    def test_cast_spell_returns_false_when_exhausted(self):
        w = Wizard("W")
        for _ in range(3):
            w.cast_spell("Fireball")
        assert w.cast_spell("Fireball") is False

    def test_cannot_use_heavy_armor(self):
        w = Wizard("W")
        assert not w.can_use_heavy_armor()

    def test_cannot_use_shield(self):
        w = Wizard("W")
        assert not w.can_use_shield()


class TestBarbarianAbilities:
    """Barbarian class abilities."""

    def test_attack_bonus_equals_level(self):
        b = Barbarian("B", level=4)
        assert b.attack_bonus() == 4

    def test_rage_available_at_start(self):
        b = Barbarian("B")
        assert b.rage_available

    def test_rage_can_be_used_once(self):
        b = Barbarian("B")
        assert b.use_rage() is True
        assert b.rage_available is False
        assert b.use_rage() is False

    def test_cannot_use_magic(self):
        b = Barbarian("B")
        assert not b.can_use_magic()

    def test_cannot_use_heavy_armor(self):
        b = Barbarian("B")
        assert not b.can_use_heavy_armor()


class TestElfAbilities:
    """Elf class abilities."""

    def test_attack_bonus_equals_level(self):
        e = Elf("E", level=3)
        assert e.attack_bonus() == 3

    def test_no_attack_bonus_two_handed(self):
        e = Elf("E", level=3)
        assert e.attack_bonus(two_handed=True) == 0

    def test_anti_orc_bonus(self):
        e = Elf("E", level=2)
        orc = Minion("Orc", level=4)
        assert e.attack_bonus(target=orc) == 3  # level 2 + 1 anti-orc

    def test_anti_orc_bonus_with_orc_in_name(self):
        e = Elf("E", level=1)
        orc_chief = Boss("Orc Warlord", level=5, life=6)
        assert e.attack_bonus(target=orc_chief) == 2  # level 1 + 1

    def test_spell_slots_1_per_level(self):
        for lvl in range(1, 6):
            e = Elf("E", level=lvl)
            assert e.spell_slots == lvl

    def test_spell_attack_bonus_equals_level(self):
        e = Elf("E", level=4)
        assert e.spell_attack_bonus() == 4

    def test_cannot_cast_blessing(self):
        e = Elf("E")
        assert not e.can_cast("Blessing")

    def test_can_cast_fireball(self):
        e = Elf("E")
        assert e.can_cast("Fireball")

    def test_cannot_use_heavy_armor(self):
        e = Elf("E")
        assert not e.can_use_heavy_armor()


class TestDwarfAbilities:
    """Dwarf class abilities."""

    def test_attack_bonus_melee_equals_level(self):
        d = Dwarf("D", level=3)
        assert d.attack_bonus() == 3

    def test_no_attack_bonus_ranged(self):
        d = Dwarf("D", level=3)
        assert d.attack_bonus(ranged=True) == 0

    def test_anti_goblin_bonus(self):
        d = Dwarf("D", level=2)
        goblin = Minion("Goblin", level=3)
        assert d.attack_bonus(target=goblin) == 3  # level 2 + 1

    def test_defense_bonus_vs_troll(self):
        d = Dwarf("D")
        troll = Boss("Troll", level=6, life=8)
        assert d.defense_bonus(attacker=troll) == 1

    def test_defense_bonus_vs_ogre(self):
        d = Dwarf("D")
        ogre = Boss("Ogre", level=5, life=6)
        assert d.defense_bonus(attacker=ogre) == 1

    def test_no_defense_bonus_vs_normal(self):
        d = Dwarf("D")
        goblin = Minion("Goblin", level=3)
        assert d.defense_bonus(attacker=goblin) == 0

    def test_smell_gold_success(self):
        d = Dwarf("D", level=3)
        # roll=3 + level=3 = 6 >= 6
        assert d.smell_gold(force_roll=3) is True

    def test_smell_gold_failure(self):
        d = Dwarf("D", level=1)
        # roll=1 + level=1 = 2 < 6
        assert d.smell_gold(force_roll=1) is False

    def test_can_use_heavy_armor(self):
        d = Dwarf("D")
        assert d.can_use_heavy_armor()


class TestHalflingAbilities:
    """Halfling class abilities."""

    def test_no_attack_bonus(self):
        h = Halfling("H", level=5)
        assert h.attack_bonus() == 0

    def test_defense_bonus_vs_giant(self):
        h = Halfling("H", level=3)
        giant = Boss("Giant", level=7, life=10)
        assert h.defense_bonus(attacker=giant) == 3

    def test_defense_bonus_vs_troll(self):
        h = Halfling("H", level=2)
        troll = Boss("Troll", level=6, life=8)
        assert h.defense_bonus(attacker=troll) == 2

    def test_no_defense_bonus_vs_normal(self):
        h = Halfling("H", level=3)
        goblin = Minion("Goblin", level=3)
        assert h.defense_bonus(attacker=goblin) == 0

    def test_luck_points_at_level_1(self):
        h = Halfling("H")
        assert h.luck_points == 2  # level 1 + 1

    def test_luck_points_at_level_5(self):
        h = Halfling("H", level=5)
        assert h.luck_points == 6  # level 5 + 1

    def test_use_luck_decrements(self):
        h = Halfling("H")
        assert h.use_luck() is True
        assert h.luck_points == 1

    def test_luck_exhausted(self):
        h = Halfling("H")  # 2 points
        h.use_luck()
        h.use_luck()
        assert h.use_luck() is False
        assert h.luck_points == 0

    def test_reset_luck(self):
        h = Halfling("H")
        h.use_luck()
        h.use_luck()
        h.reset_luck()
        assert h.luck_points == 2

    def test_poison_save_bonus(self):
        h = Halfling("H", level=3)
        assert h.get_save_bonus("poison") == 3

    def test_no_save_bonus_vs_other(self):
        h = Halfling("H", level=3)
        assert h.get_save_bonus("fire") == 0

    def test_cannot_use_heavy_armor(self):
        h = Halfling("H")
        assert not h.can_use_heavy_armor()

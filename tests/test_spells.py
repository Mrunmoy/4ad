"""Tests for the spell system following 4AD rules."""
import pytest
from src.character import Wizard, Elf, Cleric, Warrior, Barbarian, Rogue
from src.monster import Minion, Boss
from src.spells import SpellCaster, SPELLS


class TestSpellSlotSystem:
    """Test spell slot management."""

    def test_wizard_starts_with_3_slots_at_level_1(self):
        wiz = Wizard("Gandalf")
        assert wiz.spells_remaining == 3

    def test_wizard_slots_scale_with_level(self):
        wiz = Wizard("Gandalf", level=3)
        assert wiz.spells_remaining == 5  # 2 + level

    def test_elf_starts_with_1_slot_at_level_1(self):
        elf = Elf("Legolas")
        assert elf.spells_remaining == 1

    def test_elf_slots_scale_with_level(self):
        elf = Elf("Legolas", level=3)
        assert elf.spells_remaining == 3  # 1 per level

    def test_cleric_has_3_blessings(self):
        cleric = Cleric("Friar")
        assert cleric.spells_remaining == 3

    def test_cleric_has_3_healings(self):
        cleric = Cleric("Friar")
        assert cleric.healing_remaining == 3

    def test_wizard_slot_decrements_on_cast(self):
        wiz = Wizard("Gandalf")
        result = SpellCaster.cast_spell(
            wiz, "Fireball", [Minion("Goblin", level=3)], force_rolls=[5]
        )
        assert wiz.spells_remaining == 2

    def test_cleric_blessing_decrements(self):
        cleric = Cleric("Friar")
        target = Warrior("Hero")
        target.cursed = True
        result = SpellCaster.cast_spell(cleric, "Blessing", target)
        assert cleric.spells_remaining == 2

    def test_wizard_cannot_cast_with_zero_slots(self):
        wiz = Wizard("Gandalf")
        wiz.spells_remaining = 0
        result = SpellCaster.cast_spell(
            wiz, "Fireball", [Minion("Goblin", level=3)], force_rolls=[5]
        )
        assert not result.success
        assert "no spell slots" in result.description.lower() or "cannot cast" in result.description.lower()

    def test_elf_cannot_cast_blessing(self):
        elf = Elf("Legolas")
        assert not elf.can_cast("Blessing")

    def test_warrior_cannot_cast_spells(self):
        warrior = Warrior("Hero")
        assert not warrior.can_cast("Fireball")


class TestFireball:
    """Test Fireball spell mechanics."""

    def test_fireball_kills_minions_by_roll_minus_level(self):
        """Fireball kills (roll - monster_level) minions."""
        wiz = Wizard("Gandalf")
        goblins = [Minion("Goblin", level=3) for _ in range(6)]
        # Roll 5 + level 1 = 6. 6 - 3 = 3 goblins killed
        result = SpellCaster.cast_spell(wiz, "Fireball", goblins, force_rolls=[5])
        assert result.success
        assert result.minions_killed == 3

    def test_fireball_kills_minimum_1_on_hit(self):
        """On a hit, fireball kills at least 1 minion."""
        wiz = Wizard("Gandalf")
        goblins = [Minion("Goblin", level=3) for _ in range(5)]
        # Roll 2 + level 1 = 3. 3 - 3 = 0, but minimum 1
        result = SpellCaster.cast_spell(wiz, "Fireball", goblins, force_rolls=[2])
        assert result.success
        assert result.minions_killed >= 1

    def test_fireball_deals_2_damage_to_boss(self):
        """Fireball deals 2 damage to a boss on hit."""
        wiz = Wizard("Gandalf")
        ogre = Boss("Ogre", level=5, life=6)
        # Roll 5 + level 1 = 6 >= 5 = hit
        result = SpellCaster.cast_spell(wiz, "Fireball", [ogre], force_rolls=[5])
        assert result.success
        assert result.damage_dealt == 2
        assert ogre.life == 4

    def test_fireball_does_not_affect_dragons(self):
        """Fireball does 0 damage to dragons (fire immune)."""
        wiz = Wizard("Gandalf")
        dragon = Boss("Dragon", level=8, life=10, is_dragon=True)
        result = SpellCaster.cast_spell(wiz, "Fireball", [dragon], force_rolls=[6, 5])
        assert not result.success
        assert dragon.life == 10

    def test_fireball_deals_1_damage_to_demons(self):
        """Demons take only 1 damage from fireball (fire resistance)."""
        wiz = Wizard("Gandalf")
        demon = Boss("Demon", level=7, life=8, is_demon=True)
        # Roll 6+5 = 11 + level 1 = 12 >= 7 = hit
        result = SpellCaster.cast_spell(wiz, "Fireball", [demon], force_rolls=[6, 5])
        assert result.success
        assert result.damage_dealt == 1
        assert demon.life == 7

    def test_fireball_consumes_spell_slot(self):
        wiz = Wizard("Gandalf")
        goblins = [Minion("Goblin", level=3)]
        SpellCaster.cast_spell(wiz, "Fireball", goblins, force_rolls=[5])
        assert wiz.spells_remaining == 2


class TestLightningBolt:
    """Test Lightning Bolt spell mechanics."""

    def test_lightning_kills_exactly_1_minion(self):
        """Lightning bolt kills exactly 1 minion on hit."""
        wiz = Wizard("Gandalf")
        goblin = Minion("Goblin", level=3)
        # Roll 5 + level 1 = 6 >= 3 = hit
        result = SpellCaster.cast_spell(wiz, "Lightning Bolt", goblin, force_rolls=[5])
        assert result.success
        assert result.minions_killed == 1
        assert goblin.is_dead()

    def test_lightning_deals_2_damage_to_boss(self):
        """Lightning bolt deals 2 damage to a boss on hit."""
        wiz = Wizard("Gandalf")
        ogre = Boss("Ogre", level=5, life=6)
        # Roll 5 + level 1 = 6 >= 5 = hit
        result = SpellCaster.cast_spell(wiz, "Lightning Bolt", ogre, force_rolls=[5])
        assert result.success
        assert result.damage_dealt == 2
        assert ogre.life == 4

    def test_lightning_works_on_dragons(self):
        """Lightning bolt works on dragons (no restriction)."""
        wiz = Wizard("Gandalf", level=5)
        dragon = Boss("Dragon", level=8, life=10, is_dragon=True)
        # Roll 5 + level 5 = 10 >= 8 = hit
        result = SpellCaster.cast_spell(wiz, "Lightning Bolt", dragon, force_rolls=[5])
        assert result.success
        assert dragon.life == 8

    def test_lightning_works_on_undead(self):
        """Lightning bolt works on undead."""
        wiz = Wizard("Gandalf")
        skeleton = Minion("Skeleton", level=2, is_undead=True)
        # Roll 5 + 1 = 6 >= 2 = hit
        result = SpellCaster.cast_spell(wiz, "Lightning Bolt", skeleton, force_rolls=[5])
        assert result.success
        assert skeleton.is_dead()

    def test_lightning_misses_on_low_roll(self):
        """Lightning bolt misses when roll < monster level."""
        wiz = Wizard("Gandalf")
        ogre = Boss("Ogre", level=5, life=6)
        # Roll 1 + level 1 = 2 < 5 = miss
        result = SpellCaster.cast_spell(wiz, "Lightning Bolt", ogre, force_rolls=[1])
        assert not result.success
        assert ogre.life == 6


class TestSleep:
    """Test Sleep spell mechanics."""

    def test_sleep_puts_minions_to_sleep(self):
        """Sleep puts (roll - level) minions to sleep (= slain)."""
        wiz = Wizard("Gandalf")
        goblins = [Minion("Goblin", level=3) for _ in range(6)]
        # Roll 5 + level 1 = 6. 6 - 3 = 3 minions
        result = SpellCaster.cast_spell(wiz, "Sleep", goblins, force_rolls=[5])
        assert result.success
        assert result.minions_killed == 3

    def test_sleep_defeats_boss(self):
        """Sleep defeats a boss if roll >= level."""
        wiz = Wizard("Gandalf", level=3)
        ogre = Boss("Ogre", level=5, life=6)
        # Roll 5 + level 3 = 8 >= 5 = hit
        result = SpellCaster.cast_spell(wiz, "Sleep", [ogre], force_rolls=[5])
        assert result.success
        assert ogre.is_dead()

    def test_sleep_does_not_work_on_undead(self):
        """Sleep has no effect on undead."""
        wiz = Wizard("Gandalf")
        skeletons = [Minion("Skeleton", level=2, is_undead=True) for _ in range(3)]
        result = SpellCaster.cast_spell(wiz, "Sleep", skeletons, force_rolls=[5])
        assert not result.success
        assert all(not s.is_dead() for s in skeletons)

    def test_sleep_does_not_work_on_dragons(self):
        """Sleep has no effect on dragons."""
        wiz = Wizard("Gandalf", level=5)
        dragon = Boss("Dragon", level=8, life=10, is_dragon=True)
        result = SpellCaster.cast_spell(wiz, "Sleep", [dragon], force_rolls=[5])
        assert not result.success
        assert dragon.life == 10

    def test_sleep_does_not_work_on_demons(self):
        """Sleep has no effect on demons."""
        wiz = Wizard("Gandalf", level=5)
        demon = Boss("Demon", level=7, life=8, is_demon=True)
        result = SpellCaster.cast_spell(wiz, "Sleep", [demon], force_rolls=[5])
        assert not result.success
        assert demon.life == 8

    def test_sleep_still_consumes_slot_on_immune_target(self):
        """Casting sleep on immune target still uses a spell slot."""
        wiz = Wizard("Gandalf")
        skeletons = [Minion("Skeleton", level=2, is_undead=True)]
        SpellCaster.cast_spell(wiz, "Sleep", skeletons, force_rolls=[5])
        assert wiz.spells_remaining == 2


class TestEscape:
    """Test Escape spell mechanics."""

    def test_escape_is_automatic(self):
        """Escape works automatically with no roll."""
        wiz = Wizard("Gandalf")
        result = SpellCaster.cast_spell(wiz, "Escape", None)
        assert result.success
        assert result.escaped

    def test_escape_targets_self(self):
        """Escape affects only the caster."""
        wiz = Wizard("Gandalf")
        result = SpellCaster.cast_spell(wiz, "Escape", None)
        assert wiz.name in result.targets_affected

    def test_escape_consumes_slot(self):
        wiz = Wizard("Gandalf")
        SpellCaster.cast_spell(wiz, "Escape", None)
        assert wiz.spells_remaining == 2


class TestProtect:
    """Test Protect spell mechanics."""

    def test_protect_sets_protected_flag(self):
        """Protect sets the protected flag on target."""
        wiz = Wizard("Gandalf")
        warrior = Warrior("Hero")
        result = SpellCaster.cast_spell(wiz, "Protect", warrior)
        assert result.success
        assert warrior.protected

    def test_protect_does_not_work_on_barbarian(self):
        """Protect has no effect on barbarians."""
        wiz = Wizard("Gandalf")
        barb = Barbarian("Conan")
        result = SpellCaster.cast_spell(wiz, "Protect", barb)
        assert not result.success

    def test_protect_consumes_slot(self):
        wiz = Wizard("Gandalf")
        warrior = Warrior("Hero")
        SpellCaster.cast_spell(wiz, "Protect", warrior)
        assert wiz.spells_remaining == 2


class TestBlessing:
    """Test Blessing spell mechanics."""

    def test_blessing_removes_curse(self):
        """Blessing removes cursed status."""
        cleric = Cleric("Friar")
        warrior = Warrior("Hero")
        warrior.cursed = True
        result = SpellCaster.cast_spell(cleric, "Blessing", warrior)
        assert result.success
        assert not warrior.cursed
        assert "curse" in result.condition_removed

    def test_blessing_removes_petrification(self):
        """Blessing removes petrified status."""
        cleric = Cleric("Friar")
        warrior = Warrior("Hero")
        warrior.petrified = True
        result = SpellCaster.cast_spell(cleric, "Blessing", warrior)
        assert result.success
        assert not warrior.petrified
        assert "petrification" in result.condition_removed

    def test_blessing_removes_poison(self):
        """Blessing removes poisoned status."""
        cleric = Cleric("Friar")
        warrior = Warrior("Hero")
        warrior.poisoned = True
        result = SpellCaster.cast_spell(cleric, "Blessing", warrior)
        assert result.success
        assert not warrior.poisoned

    def test_wizard_can_cast_blessing(self):
        """Wizard can also cast Blessing using spell slot."""
        wiz = Wizard("Gandalf")
        warrior = Warrior("Hero")
        warrior.cursed = True
        result = SpellCaster.cast_spell(wiz, "Blessing", warrior)
        assert result.success
        assert not warrior.cursed
        assert wiz.spells_remaining == 2

    def test_cleric_blessing_uses_class_charges(self):
        """Cleric Blessing uses class charges, not spell slots."""
        cleric = Cleric("Friar")
        for i in range(3):
            target = Warrior(f"Hero{i}")
            target.cursed = True
            result = SpellCaster.cast_spell(cleric, "Blessing", target)
            assert result.success

        # 4th attempt should fail
        target = Warrior("Hero3")
        target.cursed = True
        result = SpellCaster.cast_spell(cleric, "Blessing", target)
        assert not result.success


class TestProtectDefenseBonus:
    """Test that Protect actually adds +1 defense."""

    def test_protect_adds_defense_bonus(self):
        """Protected character gets +1 to defense rolls."""
        from src.combat import Combat
        warrior = Warrior("Hero")
        goblin = Minion("Goblin", level=3)

        # Without protect: roll 1 + defense 5 = 6 > 3 = success
        result1 = Combat.resolve_defense(warrior, goblin, force_roll=1)
        base_total = result1.total_roll

        # Reset warrior
        warrior2 = Warrior("Hero2")
        warrior2.protected = True
        result2 = Combat.resolve_defense(warrior2, goblin, force_roll=1)

        assert result2.total_roll == base_total + 1


class TestElfSpellCasting:
    """Test elf-specific spell casting."""

    def test_elf_can_cast_fireball(self):
        elf = Elf("Legolas")
        assert elf.can_cast("Fireball")

    def test_elf_can_cast_sleep(self):
        elf = Elf("Legolas")
        assert elf.can_cast("Sleep")

    def test_elf_cannot_cast_blessing(self):
        elf = Elf("Legolas")
        assert not elf.can_cast("Blessing")

    def test_elf_fireball_works(self):
        elf = Elf("Legolas")
        goblins = [Minion("Goblin", level=3) for _ in range(4)]
        result = SpellCaster.cast_spell(elf, "Fireball", goblins, force_rolls=[5])
        assert result.success

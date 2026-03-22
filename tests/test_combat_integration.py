"""Tests for combat integration: class abilities, weapon modifiers, corridor
combat, multi-attack bosses, and equipment defense bonuses wired into combat
resolution.
"""
import pytest
from src.character import (
    Warrior, Cleric, Rogue, Wizard, Barbarian, Elf, Dwarf, Halfling, Character,
)
from src.monster import Minion, Boss
from src.combat import (
    Combat, AttackResult, DefenseResult,
    _get_weapon_modifier, _get_equipment_defense_bonus, _is_weapon_ranged,
)
from src.equipment import Weapon, Armor, Inventory


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_monster(name="Goblin", level=3, **kw):
    return Minion(name, level=level, **kw)


def _make_boss(name="Ogre", level=5, life=6, **kw):
    return Boss(name, level=level, life=life, **kw)


def _bare_char(cls, name="Test", level=1):
    """Create a character with an empty inventory (no equipment bonuses)."""
    c = cls(name, level=level)
    # Clear equipment to isolate class bonuses from weapon/armor bonuses
    c.inventory = Inventory(class_type=c.class_type)
    c.equipment = []
    return c


# ===================================================================
# 1. Class attack bonuses wired into combat
# ===================================================================


class TestWarriorAttackBonus:
    """Warrior adds +level to all attack rolls."""

    def test_warrior_level1_attack_bonus(self):
        w = _bare_char(Warrior, level=1)
        goblin = _make_monster("Goblin", level=3)
        # force_roll=1, base attack=4, class bonus=+1 => total=6, >=3 hit
        result = Combat.resolve_attack(w, goblin, force_roll=1)
        assert result.total_roll == 6  # 1 + 4 + 1(class)
        assert result.hit

    def test_warrior_level3_attack_bonus(self):
        w = _bare_char(Warrior, level=3)
        goblin = _make_monster("Goblin", level=3)
        result = Combat.resolve_attack(w, goblin, force_roll=1)
        # 1 + 4 + 3(class) = 8
        assert result.total_roll == 8


class TestRogueAttackBonus:
    """Rogue gets +level attack ONLY when party outnumbers enemies."""

    def test_rogue_no_bonus_when_outnumbered(self):
        r = _bare_char(Rogue, level=1)
        goblin = _make_monster("Goblin", level=3)
        result = Combat.resolve_attack(
            r, goblin, force_roll=1, party_size=2, enemy_count=4,
        )
        # 1 + 3(base) + 0(no bonus) = 4
        assert result.total_roll == 4

    def test_rogue_gets_bonus_when_outnumbering(self):
        r = _bare_char(Rogue, level=1)
        goblin = _make_monster("Goblin", level=3)
        result = Combat.resolve_attack(
            r, goblin, force_roll=1, party_size=4, enemy_count=2,
        )
        # 1 + 3(base) + 1(class bonus) = 5
        assert result.total_roll == 5


class TestClericAttackBonus:
    """Cleric: floor(level/2) general, full level vs undead."""

    def test_cleric_general_bonus(self):
        c = _bare_char(Cleric, level=2)
        goblin = _make_monster("Goblin", level=3)
        result = Combat.resolve_attack(c, goblin, force_roll=1)
        # 1 + 3(base) + 1(floor(2/2)) = 5
        assert result.total_roll == 5

    def test_cleric_vs_undead_full_bonus(self):
        c = _bare_char(Cleric, level=2)
        skeleton = _make_monster("Skeleton", level=3, is_undead=True)
        result = Combat.resolve_attack(c, skeleton, force_roll=1)
        # 1 + 3(base) + 2(full level vs undead) = 6
        assert result.total_roll == 6


class TestElfAttackBonus:
    """Elf: +level (not with 2H), +1 vs orcs."""

    def test_elf_vs_orc_bonus(self):
        e = _bare_char(Elf, level=1)
        orc = _make_monster("Orc", level=4)
        result = Combat.resolve_attack(e, orc, force_roll=1)
        # 1 + 3(base) + 1(level) + 1(vs orc) = 6
        assert result.total_roll == 6


class TestBarbarianAttackBonus:
    """Barbarian: +level to melee."""

    def test_barbarian_attack_bonus(self):
        b = _bare_char(Barbarian, level=1)
        goblin = _make_monster("Goblin", level=3)
        result = Combat.resolve_attack(b, goblin, force_roll=1)
        # 1 + 5(base) + 1(class) = 7
        assert result.total_roll == 7


# ===================================================================
# 2. Class defense bonuses wired into combat
# ===================================================================


class TestRogueDefenseBonus:
    """Rogue gets +level to all defense rolls."""

    def test_rogue_defense_bonus(self):
        r = _bare_char(Rogue, level=1)
        goblin = _make_monster("Goblin", level=3)
        result = Combat.resolve_defense(r, goblin, force_roll=1)
        # 1 + 4(base) + 1(class) = 6, > 3 => success
        assert result.total_roll == 6
        assert result.success

    def test_rogue_level3_defense_bonus(self):
        r = _bare_char(Rogue, level=3)
        boss = _make_boss("Ogre", level=5, life=6)
        result = Combat.resolve_defense(r, boss, force_roll=1)
        # 1 + 4(base) + 3(class) = 8, > 5 => success
        assert result.total_roll == 8
        assert result.success


class TestDwarfDefenseBonus:
    """Dwarf: +1 defense vs trolls, ogres, giants."""

    def test_dwarf_bonus_vs_troll(self):
        d = _bare_char(Dwarf, level=1)
        troll = _make_boss("Troll", level=6, life=8)
        result = Combat.resolve_defense(d, troll, force_roll=2)
        # 2 + 5(base) + 1(class vs troll) = 8, > 6 => success
        assert result.total_roll == 8
        assert result.success

    def test_dwarf_no_bonus_vs_goblin(self):
        d = _bare_char(Dwarf, level=1)
        goblin = _make_monster("Goblin", level=3)
        result = Combat.resolve_defense(d, goblin, force_roll=1)
        # 1 + 5(base) + 0(no class bonus) = 6, > 3 => success
        assert result.total_roll == 6
        assert result.success


class TestHalflingDefenseBonus:
    """Halfling: +level defense vs giants, trolls, ogres."""

    def test_halfling_bonus_vs_giant(self):
        h = _bare_char(Halfling, level=2)
        giant = _make_boss("Hill Giant", level=7, life=10)
        result = Combat.resolve_defense(h, giant, force_roll=3)
        # 3 + 5(base) + 2(class level vs giant) = 10, > 7 => success
        assert result.total_roll == 10
        assert result.success

    def test_halfling_no_bonus_vs_goblin(self):
        h = _bare_char(Halfling, level=2)
        goblin = _make_monster("Goblin", level=3)
        result = Combat.resolve_defense(h, goblin, force_roll=1)
        # 1 + 5(base) + 0(no bonus) = 6
        assert result.total_roll == 6


# ===================================================================
# 3. Corridor combat rules
# ===================================================================


class TestCorridorCombat:
    """In corridors, only 2 characters can fight. Position 2 gets -1."""

    def test_corridor_limits_attackers_to_two(self):
        party = [
            _bare_char(Warrior, level=1),
            _bare_char(Rogue, level=1),
            _bare_char(Cleric, level=1),
            _bare_char(Wizard, level=1),
        ]
        for i, c in enumerate(party):
            c.position = i + 1

        attackers = Combat.get_corridor_attackers(party)
        assert len(attackers) == 2
        assert attackers[0].position == 1
        assert attackers[1].position == 2

    def test_corridor_position2_penalty(self):
        w = _bare_char(Warrior, level=1)
        w.position = 2
        goblin = _make_monster("Goblin", level=3)
        result = Combat.resolve_attack(
            w, goblin, force_roll=1, corridor=True, attacker_position=2,
        )
        # 1 + 4(base) + 1(class) - 1(corridor) = 5
        assert result.total_roll == 5

    def test_corridor_position1_no_penalty(self):
        w = _bare_char(Warrior, level=1)
        w.position = 1
        goblin = _make_monster("Goblin", level=3)
        result = Combat.resolve_attack(
            w, goblin, force_roll=1, corridor=True, attacker_position=1,
        )
        # 1 + 4(base) + 1(class) = 6, no penalty
        assert result.total_roll == 6

    def test_corridor_limits_monster_attackers(self):
        monsters = [
            _make_monster("Goblin", level=3),
            _make_monster("Goblin", level=3),
            _make_monster("Goblin", level=3),
            _make_monster("Goblin", level=3),
        ]
        attackers = Combat.get_corridor_monster_attackers(monsters)
        assert len(attackers) == 2

    def test_corridor_dead_monsters_excluded(self):
        monsters = [
            _make_monster("Goblin", level=3),
            _make_monster("Goblin", level=3),
            _make_monster("Goblin", level=3),
        ]
        monsters[0].take_damage(1)  # kill first
        attackers = Combat.get_corridor_monster_attackers(monsters)
        assert len(attackers) == 2
        assert all(not m.is_dead() for m in attackers)


# ===================================================================
# 4. Weapon type combat modifiers
# ===================================================================


class TestWeaponModifiers:
    """Crushing vs skeleton, two-handed bonus, light weapon penalty."""

    def test_crushing_vs_skeleton(self):
        w = Warrior("Hero", level=1)
        # Give warrior a crushing weapon by using sling from catalogue
        # (sling is crushing type); we add it directly to bypass equip checks
        w.inventory = Inventory(class_type="Warrior")
        from src.character import _copy_weapon
        sling = _copy_weapon("sling")
        w.inventory.add_item(sling)

        skeleton = _make_monster("Skeleton", level=3, is_undead=True)
        modifier = _get_weapon_modifier(w, skeleton)
        # crushing vs skeleton: +1, but sling also has attack_modifier=-1
        # _get_weapon_modifier returns: light penalty (-1) + crushing vs skeleton (+1) = 0
        # Actually sling is ranged so no two-handed bonus, and attack_modifier=-1
        # means light penalty. Let's use a hand weapon with crushing type instead.
        # We need to add directly to the internal list.
        w.inventory = Inventory(class_type="Warrior")
        from src.equipment import Weapon as EqWeapon
        mace = EqWeapon(
            name="Hand Weapon", cost=6, hands=1,
            attack_modifier=0, damage_type="crushing",
        )
        w.inventory.add_item(mace)

        modifier = _get_weapon_modifier(w, skeleton)
        assert modifier == 1  # +1 vs skeleton with crushing

    def test_crushing_vs_non_skeleton(self):
        w = Warrior("Hero", level=1)
        w.inventory = Inventory(class_type="Warrior")
        from src.equipment import Weapon as EqWeapon
        mace = EqWeapon(
            name="Hand Weapon", cost=6, hands=1,
            attack_modifier=0, damage_type="crushing",
        )
        w.inventory.add_item(mace)

        goblin = _make_monster("Goblin", level=3)
        modifier = _get_weapon_modifier(w, goblin)
        assert modifier == 0  # no bonus vs non-skeleton

    def test_slashing_vs_skeleton_no_bonus(self):
        w = Warrior("Hero", level=1)
        w.inventory = Inventory(class_type="Warrior")
        from src.equipment import Weapon as EqWeapon
        sword = EqWeapon(
            name="Sword", cost=6, hands=1,
            attack_modifier=0, damage_type="slashing",
        )
        w.inventory.add_item(sword)

        skeleton = _make_monster("Skeleton", level=3, is_undead=True)
        modifier = _get_weapon_modifier(w, skeleton)
        assert modifier == 0

    def test_two_handed_melee_bonus(self):
        b = Barbarian("Brute", level=1)
        # Barbarian starts with two-handed weapon
        goblin = _make_monster("Goblin", level=3)
        modifier = _get_weapon_modifier(b, goblin)
        # Two-handed melee: +1
        assert modifier == 1

    def test_light_weapon_penalty(self):
        r = Rogue("Sneak", level=1)
        # Rogue starts with light hand weapon (attack_modifier=-1)
        goblin = _make_monster("Goblin", level=3)
        modifier = _get_weapon_modifier(r, goblin)
        assert modifier == -1


# ===================================================================
# 5. Boss multi-attack
# ===================================================================


class TestBossMultiAttack:
    """Bosses with num_attacks > 1 attack multiple times per round."""

    def test_single_attack_boss(self):
        boss = _make_boss("Ogre", level=5, life=6)
        boss.num_attacks = 1
        party = [_bare_char(Warrior, level=1)]
        results = Combat.resolve_monster_attack(boss, party, force_roll=5)
        assert len(results) == 1

    def test_multi_attack_boss_two_attacks(self):
        boss = _make_boss("Mummy", level=5, life=6)
        boss.num_attacks = 2
        w1 = _bare_char(Warrior, level=1)
        w1.life = 20  # prevent death during test
        w2 = _bare_char(Warrior, "Hero2", level=1)
        w2.life = 20
        party = [w1, w2]
        results = Combat.resolve_monster_attack(boss, party, force_roll=5)
        assert len(results) == 2

    def test_multi_attack_boss_three_attacks(self):
        boss = _make_boss("Chimera", level=7, life=8)
        boss.num_attacks = 3
        w1 = _bare_char(Warrior, level=1)
        w1.life = 20
        w2 = _bare_char(Warrior, "Hero2", level=1)
        w2.life = 20
        w3 = _bare_char(Warrior, "Hero3", level=1)
        w3.life = 20
        party = [w1, w2, w3]
        results = Combat.resolve_monster_attack(boss, party, force_roll=5)
        assert len(results) == 3

    def test_multi_attack_cycles_through_party(self):
        """With 3 attacks and 2 party members, first member is attacked twice."""
        boss = _make_boss("Chimera", level=7, life=8)
        boss.num_attacks = 3
        w1 = _bare_char(Warrior, level=1)
        w1.life = 20
        w2 = _bare_char(Warrior, "Hero2", level=1)
        w2.life = 20
        party = [w1, w2]
        # force_roll=5, defense=5 => 10 > 7 => success, no damage
        results = Combat.resolve_monster_attack(boss, party, force_roll=5)
        assert len(results) == 3
        # All should succeed (no damage)
        assert all(r.success for r in results)

    def test_ogre_damage_per_hit(self):
        """Ogre deals 2 damage per hit instead of 1."""
        from src.monster import BOSSES_TABLE
        ogre = BOSSES_TABLE[2]()
        assert ogre.damage_per_hit == 2

        w = _bare_char(Warrior, level=1)
        w.life = 10
        # force_roll=1, defense=5 => 6 > 5 is True, success
        # Need to fail: need total <= level (5)
        # bare warrior defense=5, force_roll=1 => 1+5=6 > 5 => success
        # Use a higher level to force failure
        ogre.level = 8
        result = Combat.resolve_defense(w, ogre, force_roll=1)
        # 1 + 5 = 6, not > 8 => fail, damage_per_hit=2
        assert not result.success
        assert result.damage_taken == 2
        assert w.life == 8  # took 2 damage


# ===================================================================
# 6. Equipment defense bonuses
# ===================================================================


class TestEquipmentDefenseBonus:
    """Equipment bonuses are wired into defense rolls."""

    def test_light_armor_defense_bonus(self):
        w = Warrior("Hero", level=1)
        # Warrior starts with light armor (+1) and shield (+1)
        bonus = _get_equipment_defense_bonus(w)
        assert bonus == 2  # light armor +1, shield +1

    def test_no_armor_no_bonus(self):
        w = _bare_char(Wizard, level=1)
        bonus = _get_equipment_defense_bonus(w)
        assert bonus == 0

    def test_heavy_armor_bonus(self):
        w = Warrior("Hero", level=1)
        # Replace armor with heavy armor
        from src.equipment import Armor as EqArmor
        w.inventory = Inventory(class_type="Warrior")
        heavy = EqArmor(
            name="Heavy Armor", cost=30, defense_bonus=2,
            is_heavy=True, save_penalty=-1,
        )
        w.inventory.add_item(heavy)
        bonus = _get_equipment_defense_bonus(w)
        assert bonus == 2

    def test_equipment_defense_in_combat(self):
        """Equipment bonus is applied in actual defense rolls."""
        w = Warrior("Hero", level=1)
        # Warrior has light armor (+1) + shield (+1) = +2 equipment
        goblin = _make_monster("Goblin", level=3)
        result = Combat.resolve_defense(w, goblin, force_roll=1)
        # 1 + 5(base) + 0(warrior has no class defense bonus) + 2(equipment) = 8
        assert result.total_roll == 8
        assert result.success


# ===================================================================
# 7. Curse penalty verification
# ===================================================================


class TestCursePenalty:
    """Cursed characters get -1 to defense (pre-existing, verify still works)."""

    def test_curse_penalty_applied(self):
        w = _bare_char(Warrior, level=1)
        w.cursed = True
        ogre = _make_boss("Ogre", level=6, life=6)
        result = Combat.resolve_defense(w, ogre, force_roll=1)
        # 1 + 5(base) - 1(curse) = 5, not > 6 => fail
        assert result.total_roll == 5
        assert not result.success


# ===================================================================
# 8. Ranged phase
# ===================================================================


class TestRangedPhase:
    """Bows and slings fire before monsters act (first round)."""

    def test_ranged_characters_fire_first(self):
        elf = Elf("Archer", level=1)
        # Elf starts with a bow
        goblin = _make_monster("Goblin", level=3)
        result = Combat.resolve_ranged_phase(
            [elf], goblin, party_size=1, enemy_count=1, force_roll=3,
        )
        assert len(result.attacks) == 1
        assert result.attackers == ["Archer"]

    def test_non_ranged_excluded_from_ranged_phase(self):
        warrior = Warrior("Tank", level=1)
        # Warrior has hand weapon (not ranged)
        goblin = _make_monster("Goblin", level=3)
        result = Combat.resolve_ranged_phase(
            [warrior], goblin, party_size=1, enemy_count=1, force_roll=3,
        )
        assert len(result.attacks) == 0


# ===================================================================
# 9. Monster multi-attack from tables
# ===================================================================


class TestMonsterTables:
    """Verify multi-attack bosses have correct num_attacks."""

    def test_ogre_has_damage_per_hit_2(self):
        from src.monster import BOSSES_TABLE
        ogre = BOSSES_TABLE[2]()
        assert ogre.name == "Ogre"
        assert ogre.damage_per_hit == 2
        assert ogre.num_attacks == 1

    def test_multi_attack_bosses_exist(self):
        from src.monster import MULTI_ATTACK_BOSSES
        mummy = MULTI_ATTACK_BOSSES["Mummy"]()
        assert mummy.num_attacks == 2

        orc_brute = MULTI_ATTACK_BOSSES["Orc Brute"]()
        assert orc_brute.num_attacks == 2

        chimera = MULTI_ATTACK_BOSSES["Chimera"]()
        assert chimera.num_attacks == 3

        small_dragon = MULTI_ATTACK_BOSSES["Small Dragon"]()
        assert small_dragon.num_attacks == 2
        assert small_dragon.is_dragon


# ===================================================================
# 10. Integration: class + equipment + weapon modifiers combined
# ===================================================================


class TestCombatIntegration:
    """Full integration tests combining multiple systems."""

    def test_warrior_with_equipment_attacks(self):
        """Warrior gets class bonus + weapon modifier in attack."""
        w = Warrior("Hero", level=1)
        # Warrior starts with hand weapon (slashing, 1H, modifier 0)
        # + light armor + shield
        goblin = _make_monster("Goblin", level=3)
        result = Combat.resolve_attack(w, goblin, force_roll=1)
        # 1 + 4(base) + 1(class) + 0(weapon mod) + 0(inv attack mod) = 6
        assert result.hit

    def test_dwarf_defense_vs_troll_with_equipment(self):
        """Dwarf gets +1 class defense vs troll PLUS equipment defense."""
        d = Dwarf("Gimli", level=1)
        troll = _make_boss("Troll", level=6, life=8)
        result = Combat.resolve_defense(d, troll, force_roll=1)
        # 1 + 5(base) + 1(class vs troll) + 2(light armor+shield) = 9, > 6 success
        assert result.total_roll == 9
        assert result.success

    def test_rogue_defense_with_equipment(self):
        """Rogue class defense + equipment stack."""
        r = Rogue("Shadow", level=1)
        goblin = _make_monster("Goblin", level=3)
        result = Combat.resolve_defense(r, goblin, force_roll=1)
        # 1 + 4(base) + 1(class) + 1(light armor, no shield) = 7, > 3 success
        assert result.total_roll == 7
        assert result.success

"""Tests for monster reaction and morale systems."""
import pytest
from src.character import Wizard, Warrior, Rogue, Cleric, Elf
from src.monster import Minion, Boss
from src.reactions import (
    roll_monster_reaction, resolve_puzzle, resolve_magic_challenge,
    ReactionResult,
)
from src.combat import Combat, MoraleResult


class TestSkeletonReactions:
    """Skeletons/Zombies always fight to death."""

    def test_skeleton_always_fights_to_death(self):
        for roll in range(1, 7):
            result = roll_monster_reaction("Skeleton", 4, 4, force_roll=roll)
            assert result.reaction_type == "fight_to_death"

    def test_zombie_always_fights_to_death(self):
        for roll in range(1, 7):
            result = roll_monster_reaction("Zombie", 3, 4, force_roll=roll)
            assert result.reaction_type == "fight_to_death"


class TestGoblinReactions:
    """Goblins: 1=flee if outnumbered, 2-3=bribe(5gp), 4-6=fight."""

    def test_goblin_flees_when_outnumbered(self):
        result = roll_monster_reaction("Goblin", 2, 4, force_roll=1)
        assert result.reaction_type == "flee"
        assert result.monsters_flee

    def test_goblin_fights_when_not_outnumbered_on_1(self):
        result = roll_monster_reaction("Goblin", 5, 4, force_roll=1)
        assert result.reaction_type == "fight"

    def test_goblin_bribe_on_2(self):
        result = roll_monster_reaction("Goblin", 3, 4, force_roll=2)
        assert result.reaction_type == "bribe"
        assert result.bribe_cost == 5
        assert "bribe" in result.player_choices

    def test_goblin_bribe_on_3(self):
        result = roll_monster_reaction("Goblin", 3, 4, force_roll=3)
        assert result.reaction_type == "bribe"

    def test_goblin_fights_on_4_through_6(self):
        for roll in [4, 5, 6]:
            result = roll_monster_reaction("Goblin", 3, 4, force_roll=roll)
            assert result.reaction_type == "fight"


class TestHobgoblinReactions:
    """Hobgoblins: 1=flee if outnumbered, 2-3=bribe(10gp), 4-5=fight, 6=fight to death."""

    def test_hobgoblin_flees_when_outnumbered(self):
        result = roll_monster_reaction("Hobgoblin", 2, 4, force_roll=1)
        assert result.reaction_type == "flee"

    def test_hobgoblin_bribe_on_2(self):
        result = roll_monster_reaction("Hobgoblin", 3, 4, force_roll=2)
        assert result.reaction_type == "bribe"
        assert result.bribe_cost == 10

    def test_hobgoblin_fights_on_4(self):
        result = roll_monster_reaction("Hobgoblin", 3, 4, force_roll=4)
        assert result.reaction_type == "fight"

    def test_hobgoblin_fight_to_death_on_6(self):
        result = roll_monster_reaction("Hobgoblin", 3, 4, force_roll=6)
        assert result.reaction_type == "fight_to_death"


class TestOrcReactions:
    """Orcs: 1-2=bribe(10gp), 3-5=fight, 6=fight to death."""

    def test_orc_bribe_on_1(self):
        result = roll_monster_reaction("Orc", 4, 4, force_roll=1)
        assert result.reaction_type == "bribe"
        assert result.bribe_cost == 10

    def test_orc_bribe_on_2(self):
        result = roll_monster_reaction("Orc", 4, 4, force_roll=2)
        assert result.reaction_type == "bribe"

    def test_orc_fights_on_3(self):
        result = roll_monster_reaction("Orc", 4, 4, force_roll=3)
        assert result.reaction_type == "fight"

    def test_orc_fight_to_death_on_6(self):
        result = roll_monster_reaction("Orc", 4, 4, force_roll=6)
        assert result.reaction_type == "fight_to_death"


class TestTrollReactions:
    """Trolls: 1-2=fight, 3-6=fight to death. Dwarf=always fight to death."""

    def test_troll_fights_on_1(self):
        result = roll_monster_reaction("Troll", 2, 4, force_roll=1)
        assert result.reaction_type == "fight"

    def test_troll_fight_to_death_on_3(self):
        result = roll_monster_reaction("Troll", 2, 4, force_roll=3)
        assert result.reaction_type == "fight_to_death"

    def test_troll_always_fight_to_death_with_dwarf(self):
        for roll in range(1, 7):
            result = roll_monster_reaction("Troll", 2, 4, force_roll=roll, has_dwarf=True)
            assert result.reaction_type == "fight_to_death"


class TestFungiFolkReactions:
    """Fungi Folk: 1-2=bribe(d6gp), 3-6=fight."""

    def test_fungi_folk_bribe_on_1(self):
        result = roll_monster_reaction("Fungi Folk", 5, 4, force_roll=1)
        assert result.reaction_type == "bribe"
        assert result.bribe_cost > 0

    def test_fungi_folk_fights_on_3(self):
        result = roll_monster_reaction("Fungi Folk", 5, 4, force_roll=3)
        assert result.reaction_type == "fight"


class TestBossReactions:
    """Test boss monster reaction tables."""

    def test_ogre_bribe_on_1(self):
        result = roll_monster_reaction("Ogre", 1, 4, force_roll=1)
        assert result.reaction_type == "bribe"
        assert result.bribe_cost == 50

    def test_ogre_fight_on_2(self):
        result = roll_monster_reaction("Ogre", 1, 4, force_roll=2)
        assert result.reaction_type == "fight"

    def test_ogre_fight_to_death_on_5(self):
        result = roll_monster_reaction("Ogre", 1, 4, force_roll=5)
        assert result.reaction_type == "fight_to_death"

    def test_vampire_always_fights_to_death(self):
        for roll in range(1, 7):
            result = roll_monster_reaction("Vampire", 1, 4, force_roll=roll)
            assert result.reaction_type == "fight_to_death"

    def test_demon_magic_challenge_on_1(self):
        result = roll_monster_reaction("Demon", 1, 4, force_roll=1)
        assert result.reaction_type == "magic_challenge"

    def test_demon_fight_to_death_on_2_through_6(self):
        for roll in [2, 3, 4, 5, 6]:
            result = roll_monster_reaction("Demon", 1, 4, force_roll=roll)
            assert result.reaction_type == "fight_to_death"

    def test_dragon_sleeping_on_1(self):
        result = roll_monster_reaction("Dragon", 1, 4, force_roll=1)
        assert result.reaction_type == "sleeping"
        assert result.sleeping_bonus == 2

    def test_dragon_fight_to_death_on_2(self):
        result = roll_monster_reaction("Dragon", 1, 4, force_roll=2)
        assert result.reaction_type == "fight_to_death"


class TestSmallDragonReactions:
    """Small Dragon: 1=sleeping, 2-3=bribe(100gp), 4-5=fight, 6=quest."""

    def test_small_dragon_sleeping_on_1(self):
        result = roll_monster_reaction("Small Dragon", 1, 4, force_roll=1)
        assert result.reaction_type == "sleeping"

    def test_small_dragon_bribe_on_2(self):
        result = roll_monster_reaction("Small Dragon", 1, 4, force_roll=2)
        assert result.reaction_type == "bribe"
        assert result.bribe_cost == 100

    def test_small_dragon_fight_on_4(self):
        result = roll_monster_reaction("Small Dragon", 1, 4, force_roll=4)
        assert result.reaction_type == "fight"

    def test_small_dragon_quest_on_6(self):
        result = roll_monster_reaction("Small Dragon", 1, 4, force_roll=6)
        assert result.reaction_type == "quest"
        assert result.quest_data is not None


class TestMedusaReactions:
    """Medusa: 1=puzzle, 2-6=fight."""

    def test_medusa_puzzle_on_1(self):
        result = roll_monster_reaction("Medusa", 1, 4, force_roll=1)
        assert result.reaction_type == "puzzle"

    def test_medusa_fight_on_2(self):
        result = roll_monster_reaction("Medusa", 1, 4, force_roll=2)
        assert result.reaction_type == "fight"


class TestPuzzleResolution:
    """Test puzzle mechanic: d6 + bonus vs monster_level."""

    def test_wizard_adds_level_to_puzzle(self):
        wiz = Wizard("Gandalf", level=3)
        # Roll 3 + level 3 = 6 >= 5
        result = resolve_puzzle(wiz, 5, force_roll=3)
        assert result["success"]

    def test_rogue_adds_level_to_puzzle(self):
        rogue = Rogue("Shadow", level=2)
        # Roll 4 + level 2 = 6 >= 5
        result = resolve_puzzle(rogue, 5, force_roll=4)
        assert result["success"]

    def test_warrior_gets_no_bonus(self):
        warrior = Warrior("Hero")
        # Roll 3 + 0 = 3 < 5
        result = resolve_puzzle(warrior, 5, force_roll=3)
        assert not result["success"]
        assert result["damage_taken"] == 1

    def test_puzzle_failure_deals_1_damage(self):
        warrior = Warrior("Hero")
        initial_life = warrior.life
        resolve_puzzle(warrior, 5, force_roll=1)
        assert warrior.life == initial_life - 1


class TestMagicChallenge:
    """Test magic challenge (wizard duel)."""

    def test_wizard_wins_challenge(self):
        wiz = Wizard("Gandalf", level=3)
        # Wizard: 5 + 3 = 8, Monster: 1 + 6 = 7
        result = resolve_magic_challenge(wiz, 6, force_wizard_roll=5, force_monster_roll=1)
        assert result["success"]

    def test_wizard_loses_challenge_takes_damage(self):
        """Losing wizard takes 2 damage (not level loss)."""
        wiz = Wizard("Gandalf", level=3)
        initial_life = wiz.life
        # Wizard: 1 + 3 = 4, Monster: 6 + 6 = 12
        result = resolve_magic_challenge(wiz, 6, force_wizard_roll=1, force_monster_roll=6)
        assert not result["success"]
        assert wiz.level == 3  # Level unchanged
        assert wiz.life == initial_life - 2  # Takes 2 damage
        assert result["damage_taken"] == 2

    def test_wizard_level_unchanged_on_loss(self):
        wiz = Wizard("Gandalf", level=1)
        initial_life = wiz.life
        resolve_magic_challenge(wiz, 6, force_wizard_roll=1, force_monster_roll=6)
        assert wiz.level == 1  # Level stays the same
        assert wiz.life == initial_life - 2  # Takes 2 damage


class TestMinionMorale:
    """Test minion morale system."""

    def test_no_morale_check_when_under_50_percent_killed(self):
        """No check if fewer than half killed this round."""
        goblins = [Minion("Goblin", level=3) for _ in range(4)]
        goblins[0].take_damage(1)  # Kill 1 of 4 = 25%
        result = Combat.check_minion_morale(goblins, 4, kills_this_round=1)
        assert not result.checked

    def test_morale_check_triggered_above_50_percent(self):
        """Check when more than 50% killed in one round."""
        goblins = [Minion("Goblin", level=3) for _ in range(4)]
        goblins[0].take_damage(1)
        goblins[1].take_damage(1)
        goblins[2].take_damage(1)  # 3 of 4 dead = 75%
        result = Combat.check_minion_morale(goblins, 4, force_roll=2, kills_this_round=3)
        assert result.checked
        assert result.fled  # Roll 2 <= 3

    def test_morale_roll_4_means_fight_on(self):
        goblins = [Minion("Goblin", level=3) for _ in range(4)]
        for g in goblins[:3]:
            g.take_damage(1)
        result = Combat.check_minion_morale(goblins, 4, force_roll=4, kills_this_round=3)
        assert result.checked
        assert not result.fled  # Roll 4 > 3

    def test_fight_to_death_skips_morale(self):
        """Monsters that fight to death never check morale."""
        skeletons = [Minion("Skeleton", level=3, is_undead=True, fights_to_death=True)
                     for _ in range(4)]
        skeletons[0].take_damage(1)
        skeletons[1].take_damage(1)
        skeletons[2].take_damage(1)
        result = Combat.check_minion_morale(skeletons, 4, force_roll=1, kills_this_round=3)
        assert result.checked
        assert not result.fled

    def test_orc_morale_penalty_after_spell_kill(self):
        """Orcs get -1 morale if spell killed one."""
        orcs = [Minion("Orc", level=4) for _ in range(4)]
        for o in orcs[:3]:
            o.take_damage(1)
        # Roll 4, modifier -1 = 3. 3 <= 3 = flee
        result = Combat.check_minion_morale(orcs, 4, spell_killed=True, force_roll=4, kills_this_round=3)
        assert result.checked
        assert result.fled

    def test_morale_only_checked_once(self):
        """Only one morale check per encounter."""
        goblins = [Minion("Goblin", level=3) for _ in range(4)]
        for g in goblins[:3]:
            g.take_damage(1)
        result1 = Combat.check_minion_morale(goblins, 4, force_roll=5, kills_this_round=3)  # Stay
        assert result1.checked
        result2 = Combat.check_minion_morale(goblins, 4, force_roll=1, kills_this_round=3)  # Would flee
        assert not result2.checked  # Already checked


class TestBossMorale:
    """Test boss morale system."""

    def test_boss_morale_triggers_below_50_percent(self):
        """Boss morale check when life < 50% max."""
        ogre = Boss("Ogre", level=5, life=6)
        ogre.take_damage(4)  # life = 2, below 50% of 6
        result = Combat.check_boss_morale(ogre, force_roll=2)
        assert result.checked
        assert result.fled  # Roll 2 <= 3

    def test_boss_level_drops_on_morale_trigger(self):
        """Boss level drops by 1 when morale triggered."""
        ogre = Boss("Ogre", level=5, life=6)
        ogre.take_damage(4)
        Combat.check_boss_morale(ogre, force_roll=5)
        assert ogre.level == 4  # Was 5, dropped by 1

    def test_boss_morale_fight_on(self):
        """Boss fights on when morale roll >= 4."""
        ogre = Boss("Ogre", level=5, life=6)
        ogre.take_damage(4)
        result = Combat.check_boss_morale(ogre, force_roll=4)
        assert result.checked
        assert not result.fled

    def test_boss_fights_to_death_no_morale(self):
        """Bosses marked fight_to_death skip morale."""
        vampire = Boss("Vampire", level=6, life=6, is_undead=True, fights_to_death=True)
        vampire.take_damage(4)
        result = Combat.check_boss_morale(vampire, force_roll=1)
        assert not result.checked
        assert not result.fled

    def test_boss_morale_only_once(self):
        """Boss morale only checked once."""
        ogre = Boss("Ogre", level=5, life=6)
        ogre.take_damage(4)
        result1 = Combat.check_boss_morale(ogre, force_roll=5)  # Stay
        assert result1.checked
        ogre.take_damage(1)  # Even more wounded
        result2 = Combat.check_boss_morale(ogre, force_roll=1)
        assert not result2.checked  # Already done

    def test_no_morale_check_above_50_percent(self):
        """No check when boss still above 50% life."""
        ogre = Boss("Ogre", level=5, life=6)
        ogre.take_damage(2)  # life = 4, still above 50%
        result = Combat.check_boss_morale(ogre)
        assert not result.checked


class TestDefaultReactions:
    """Test that unknown monsters default to fight."""

    def test_unknown_monster_fights(self):
        result = roll_monster_reaction("Unknown Beast", 1, 4, force_roll=3)
        assert result.reaction_type == "fight"

    def test_vermin_always_fight(self):
        for name in ["Rats", "Spiders", "Bats", "Snakes", "Insects", "Scorpions"]:
            result = roll_monster_reaction(name, 3, 4, force_roll=1)
            assert result.reaction_type == "fight"


class TestMindFlayerReactions:
    """Mind Flayer: 1=magic challenge, 2-6=fight to death."""

    def test_mind_flayer_magic_challenge_on_1(self):
        result = roll_monster_reaction("Mind Flayer", 1, 4, force_roll=1)
        assert result.reaction_type == "magic_challenge"

    def test_mind_flayer_fight_to_death_on_2(self):
        result = roll_monster_reaction("Mind Flayer", 1, 4, force_roll=2)
        assert result.reaction_type == "fight_to_death"


class TestGoblinSurprise:
    """Test goblin 1-in-6 surprise mechanic."""

    def test_goblin_reaction_has_surprise_field(self):
        """Goblin reactions include a surprise flag."""
        result = roll_monster_reaction("Goblin", 4, 4, force_roll=4)
        assert hasattr(result, 'surprise')
        assert isinstance(result.surprise, bool)

    def test_goblin_fight_can_have_surprise(self):
        """Fight reaction should carry the surprise flag."""
        result = roll_monster_reaction("Goblin", 4, 4, force_roll=6)
        assert isinstance(result.surprise, bool)


class TestTrollRegeneration:
    """Test troll regeneration mechanic."""

    def test_dead_troll_regenerates_on_5(self):
        """Dead troll revives with 1 life on roll of 5."""
        troll = Minion("Troll", level=5)
        troll.take_damage(1)
        assert troll.is_dead()
        messages = Combat.check_troll_regeneration([troll], force_roll=5)
        assert len(messages) == 1
        assert not troll.is_dead()
        assert troll.life == 1

    def test_dead_troll_regenerates_on_6(self):
        """Dead troll revives on roll of 6."""
        troll = Minion("Troll", level=5)
        troll.take_damage(1)
        messages = Combat.check_troll_regeneration([troll], force_roll=6)
        assert not troll.is_dead()

    def test_dead_troll_stays_dead_on_4(self):
        """Dead troll stays dead on roll of 4 or less."""
        troll = Minion("Troll", level=5)
        troll.take_damage(1)
        messages = Combat.check_troll_regeneration([troll], force_roll=4)
        assert troll.is_dead()

    def test_boss_troll_regenerates_with_3_life(self):
        """Boss troll revives with 3 life."""
        troll = Boss("Troll", level=6, life=8)
        troll.take_damage(8)
        assert troll.is_dead()
        messages = Combat.check_troll_regeneration([troll], force_roll=5)
        assert not troll.is_dead()
        assert troll.life == 3

    def test_non_troll_does_not_regenerate(self):
        """Non-troll monsters don't regenerate."""
        ogre = Boss("Ogre", level=5, life=6)
        ogre.take_damage(6)
        messages = Combat.check_troll_regeneration([ogre], force_roll=6)
        assert len(messages) == 0
        assert ogre.is_dead()

    def test_living_troll_not_checked(self):
        """Living trolls are not checked for regeneration."""
        troll = Boss("Troll", level=6, life=8)
        troll.take_damage(2)
        messages = Combat.check_troll_regeneration([troll], force_roll=5)
        assert len(messages) == 0

    def test_chopped_troll_does_not_regenerate_again(self):
        """Once a troll fails regeneration, it stays dead."""
        troll = Minion("Troll", level=5)
        troll.take_damage(1)
        Combat.check_troll_regeneration([troll], force_roll=3)
        assert troll.is_dead()
        messages = Combat.check_troll_regeneration([troll], force_roll=6)
        assert len(messages) == 0


class TestDragonBreathWeapon:
    """Test dragon breath weapon."""

    def test_breath_weapon_hits_all_characters(self):
        """Dragon breath targets all living characters."""
        dragon = Boss("Dragon", level=8, life=10, is_dragon=True)
        party = [Warrior("W1"), Wizard("W2")]
        results = Combat.resolve_dragon_breath(dragon, party, force_roll=1)
        assert len(results) == 2
        for r in results:
            assert r["damage_taken"] == 1

    def test_breath_skips_dead_characters(self):
        """Dead characters are not targeted by breath."""
        dragon = Boss("Dragon", level=8, life=10, is_dragon=True)
        w1 = Warrior("W1")
        w2 = Warrior("W2")
        w2.life = 0
        results = Combat.resolve_dragon_breath(dragon, [w1, w2], force_roll=1)
        assert len(results) == 1
        assert results[0]["character"] == "W1"


class TestBossMoraleStrictlyBelow50:
    """Test that boss morale triggers strictly below 50%."""

    def test_ogre_at_exactly_50_percent_no_morale(self):
        """Ogre with life=3 (50% of 6) should NOT trigger morale."""
        ogre = Boss("Ogre", level=5, life=6)
        ogre.take_damage(3)
        result = Combat.check_boss_morale(ogre, force_roll=1)
        assert not result.checked

    def test_ogre_below_50_percent_triggers_morale(self):
        """Ogre with life=2 (33% of 6) should trigger morale."""
        ogre = Boss("Ogre", level=5, life=6)
        ogre.take_damage(4)
        result = Combat.check_boss_morale(ogre, force_roll=1)
        assert result.checked


class TestMinionMoralePerRound:
    """Test that minion morale checks use per-round kills."""

    def test_no_morale_if_kills_spread_across_rounds(self):
        """Kills spread across rounds should not trigger morale."""
        goblins = [Minion("Goblin", level=3) for _ in range(6)]
        goblins[0].take_damage(1)
        goblins[1].take_damage(1)
        result = Combat.check_minion_morale(goblins, 6, kills_this_round=2)
        assert not result.checked

    def test_morale_triggers_when_enough_killed_one_round(self):
        """Enough kills in one round should trigger morale."""
        goblins = [Minion("Goblin", level=3) for _ in range(6)]
        for g in goblins[:4]:
            g.take_damage(1)
        result = Combat.check_minion_morale(goblins, 6, kills_this_round=4, force_roll=2)
        assert result.checked
        assert result.fled


class TestMagicChallengeDamage:
    """Test that magic challenge applies damage, not level loss."""

    def test_wizard_takes_2_damage_on_loss(self):
        """Wizard takes 2 damage when losing duel."""
        wiz = Wizard("Gandalf", level=3)
        initial_life = wiz.life
        result = resolve_magic_challenge(wiz, 7, force_wizard_roll=1, force_monster_roll=6)
        assert not result["success"]
        assert wiz.level == 3
        assert wiz.life == initial_life - 2

    def test_wizard_can_die_from_magic_challenge(self):
        """Wizard with low life can die from magic challenge damage."""
        wiz = Wizard("Gandalf", level=1)
        wiz.life = 1
        resolve_magic_challenge(wiz, 7, force_wizard_roll=1, force_monster_roll=6)
        assert wiz.is_dead()


class TestWeirdMonstersAreBossType:
    """Test that weird monsters are correct types."""

    def test_gelatinous_cube_is_boss(self):
        from src.monster import WEIRD_MONSTERS_TABLE
        cube = WEIRD_MONSTERS_TABLE[1]()
        assert isinstance(cube, Boss)
        assert cube.life == 4
        assert cube.max_life == 4
        assert cube.level == 4

    def test_carrion_crawler_is_boss(self):
        from src.monster import WEIRD_MONSTERS_TABLE
        crawler = WEIRD_MONSTERS_TABLE[3]()
        assert isinstance(crawler, Boss)
        assert crawler.life == 4
        assert crawler.level == 4

    def test_mimic_is_boss(self):
        from src.monster import WEIRD_MONSTERS_TABLE
        mimic = WEIRD_MONSTERS_TABLE[4]()
        assert isinstance(mimic, Boss)
        assert mimic.life == 5
        assert mimic.level == 5

    def test_rust_monster_is_still_minion(self):
        from src.monster import WEIRD_MONSTERS_TABLE
        rm = WEIRD_MONSTERS_TABLE[2]()
        assert isinstance(rm, Minion)
        assert rm.life == 1


class TestSkeletonLevel:
    """Test skeleton level is correct per spec."""

    def test_skeleton_level_is_3(self):
        from src.monster import MINIONS_TABLE
        skeleton = MINIONS_TABLE[3]()
        assert skeleton.level == 3
        assert skeleton.name == "Skeleton"


class TestBlessingDoesNotCurePoison:
    """Test that Blessing does not cure poison."""

    def test_blessing_leaves_poison(self):
        from src.spells import SpellCaster
        cleric = Cleric("Friar")
        warrior = Warrior("Hero")
        warrior.poisoned = True
        warrior.cursed = True
        result = SpellCaster.cast_spell(cleric, "Blessing", warrior)
        assert result.success
        assert not warrior.cursed
        assert warrior.poisoned

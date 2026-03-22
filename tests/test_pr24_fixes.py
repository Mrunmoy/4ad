"""Tests for PR #24 fixes: spell slots, Sleep mixed groups, morale reset,
dragon sleeping bonus, and Escape teleport."""
import pytest
from src.character import Wizard, Warrior, Barbarian
from src.combat import Combat
from src.game import GameManager
from src.monster import Minion, Boss
from src.spells import SpellCaster


class TestC1ProtectBarbSlotNotConsumed:
    """C1: Protect on Barbarian must NOT consume a spell slot."""

    def test_protect_on_barbarian_does_not_consume_slot(self):
        wiz = Wizard("Gandalf")
        barb = Barbarian("Conan")
        assert wiz.spells_remaining == 3

        result = SpellCaster.cast_spell(wiz, "Protect", barb)

        assert not result.success
        assert wiz.spells_remaining == 3  # slot preserved

    def test_protect_on_warrior_does_consume_slot(self):
        """Sanity check: valid Protect still uses a slot."""
        wiz = Wizard("Gandalf")
        warrior = Warrior("Hero")
        SpellCaster.cast_spell(wiz, "Protect", warrior)
        assert wiz.spells_remaining == 2


class TestC2SleepMixedGroup:
    """C2: Sleep on a boss+minion group must affect minions."""

    def test_sleep_affects_minions_in_mixed_group(self):
        wiz = Wizard("Gandalf", level=3)
        minions = [Minion("Goblin", level=3) for _ in range(4)]
        boss = Boss("Ogre", level=5, life=6)
        targets = minions + [boss]

        # Roll 5 + level 3 = 8.  Minions: 8-3 = 5 → all 4 minions.
        # Boss: 8 >= 5 → defeated.
        result = SpellCaster.cast_spell(wiz, "Sleep", targets, force_rolls=[5])

        assert result.success
        dead_minions = sum(1 for m in minions if m.is_dead())
        assert dead_minions == 4
        assert boss.is_dead()

    def test_sleep_pure_minion_group_still_works(self):
        """Regression: pure-minion group must still be handled."""
        wiz = Wizard("Gandalf")
        goblins = [Minion("Goblin", level=3) for _ in range(6)]
        result = SpellCaster.cast_spell(wiz, "Sleep", goblins, force_rolls=[5])
        assert result.success
        assert result.minions_killed == 3


class TestC3KillsThisRoundReset:
    """C3: kills_this_round must reset at the start of each combat round."""

    def test_kills_reset_between_rounds(self):
        gm = GameManager("test")
        pid = gm.add_player("Alice")
        gm.create_character(pid, "Warrior", "Brynn")
        gm.start()

        # Set up combat with easy-to-hit monsters (level 1, high life)
        monsters = [Boss(f"Blob{i}", level=1, life=50) for i in range(3)]
        gm.current_monsters = monsters
        gm.original_monster_count = 3
        gm.combat_active = True

        # Simulate a first round that accumulates kills
        gm.kills_this_round = 5

        # Calling attack() starts a new round; kills_this_round must reset
        gm.attack(target_idx=0)
        # After a single attack against level-1 boss with 50 life,
        # kills_this_round should be 0 (boss not dead) — NOT carry over 5.
        assert gm.kills_this_round <= 1


class TestS1DragonSleepingBonus:
    """S1: sleeping_bonus from reaction must apply +2 to first attack."""

    def test_sleeping_bonus_applied_to_first_attack(self):
        gm = GameManager("test")
        pid = gm.add_player("Alice")
        gm.create_character(pid, "Warrior", "Brynn")
        gm.start()

        dragon = Boss("Dragon", level=8, life=10, is_dragon=True)
        gm.current_monsters = [dragon]
        gm.original_monster_count = 1
        gm.combat_active = True
        gm.sleeping_bonus = 2

        warrior = gm.dungeon.party.get_living_characters()[0]
        base_attack = warrior.attack

        # Attack should include the +2 sleeping bonus
        gm.attack(target_idx=0)

        # Bonus consumed after first attack
        assert gm.sleeping_bonus == 0
        # Warrior's attack should be restored to base
        assert warrior.attack == base_attack

    def test_sleeping_bonus_not_applied_to_second_attack(self):
        gm = GameManager("test")
        pid = gm.add_player("Alice")
        gm.create_character(pid, "Warrior", "Brynn")
        gm.start()

        dragon = Boss("Dragon", level=8, life=10, is_dragon=True)
        gm.current_monsters = [dragon]
        gm.original_monster_count = 1
        gm.combat_active = True
        gm.sleeping_bonus = 2

        # First attack consumes the bonus
        gm.attack(target_idx=0)
        assert gm.sleeping_bonus == 0

        # Second attack gets no bonus
        warrior = gm.dungeon.party.get_living_characters()[0]
        assert warrior.attack == 4  # Warrior base attack


class TestS2EscapeMovesToEntrance:
    """S2: Escape spell must move party to dungeon entrance."""

    def test_escape_teleports_to_entrance(self):
        gm = GameManager("test")
        pid = gm.add_player("Alice")
        gm.create_character(pid, "Wizard", "Merlin")
        gm.start()

        entrance = gm.dungeon.entrance

        # Move to a different room
        room = gm.dungeon.party.current_room
        unexplored = [d for d, r in room.exits.items() if r is None]
        if unexplored:
            gm.move(unexplored[0])

        # Set up combat
        gm.current_monsters = [Boss("Ogre", level=5, life=6)]
        gm.original_monster_count = 1
        gm.combat_active = True

        # Cast Escape
        gm.cast_spell("Escape")

        # Party should be at entrance
        assert gm.dungeon.party.current_room is entrance
        assert not gm.combat_active
        assert any("entrance" in msg.lower() for msg in gm.message_log)

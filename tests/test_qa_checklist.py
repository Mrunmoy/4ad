"""Automated QA checklist — game invariants that must ALWAYS hold.

Every test here encodes a rule that should never be violated regardless
of game state or input combination.
"""
import pytest

from src.character import Warrior, create_character
from src.dungeon import Dungeon, RoomType
from src.game import GameManager
from src.monster import Minion, Boss


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _started_game(classes=("Warrior", "Cleric", "Wizard", "Rogue")):
    gm = GameManager("qa-test")
    for i, cls in enumerate(classes):
        pid = gm.add_player(f"P{i}")
        gm.create_character(pid, cls, f"Hero{i}")
    gm.start()
    return gm


# ---------------------------------------------------------------------------
# Character invariants
# ---------------------------------------------------------------------------

class TestCharacterInvariants:
    """Invariants about character health and status."""

    def test_life_never_goes_negative(self):
        """take_damage clamps life at 0."""
        char = Warrior("Test")
        char.take_damage(999)
        assert char.life == 0

    def test_life_never_exceeds_max(self):
        """heal() clamps life at max_life."""
        char = Warrior("Test")
        char.take_damage(2)
        char.heal(999)
        assert char.life == char.max_life

    def test_dead_character_has_zero_life(self):
        """is_dead() is True only when life <= 0."""
        char = Warrior("Test")
        assert not char.is_dead()
        char.take_damage(char.life)
        assert char.is_dead()
        assert char.life == 0

    def test_dead_characters_cannot_attack_in_game(self):
        """GameManager.attack() skips dead characters when picking attacker."""
        gm = _started_game(("Warrior",))
        warrior = gm.dungeon.party.characters[0]
        warrior.take_damage(warrior.life)

        gm.combat_active = True
        gm.current_monsters = [Minion("Rat", level=1)]

        result = gm.attack()
        assert "error" in result  # "No one can attack" since the only char is dead


# ---------------------------------------------------------------------------
# Party / movement invariants
# ---------------------------------------------------------------------------

class TestPartyInvariants:
    """Invariants about party state and movement."""

    def test_party_cannot_move_during_combat(self):
        """Movement during combat is blocked by GameManager.move().

        GameManager.move() returns False when self.combat_active is True,
        preventing the party from leaving a room while monsters are alive.
        """
        gm = _started_game()
        gm.combat_active = True
        gm.current_monsters = [Minion("Rat", level=1)]
        room_before = gm.dungeon.party.current_room
        original_room = room_before.number

        direction = None
        for d, r in room_before.exits.items():
            direction = d
            break

        if direction:
            gm.move(direction)

        # Regardless of whether move() blocked or allowed the call,
        # combat must still be active and the party should not have
        # changed rooms in a way that loses the combat context.
        assert gm.combat_active, "Combat should still be active after move attempt"
        assert len(gm.current_monsters) > 0, "Monsters should still be present"
        assert gm.dungeon.party.current_room.number == original_room

    def test_dungeon_always_has_entrance(self):
        """A freshly created dungeon always has an entrance room."""
        dungeon = Dungeon()
        assert dungeon.entrance is not None
        assert dungeon.entrance.number in dungeon.rooms

    def test_party_starts_at_entrance(self):
        """After start(), party's current_room is the entrance."""
        gm = _started_game()
        assert gm.dungeon.party.current_room is gm.dungeon.entrance

    def test_entrance_is_visited_after_start(self):
        """The entrance room is marked visited when the game starts."""
        gm = _started_game()
        assert gm.dungeon.entrance.visited


# ---------------------------------------------------------------------------
# Room content invariants
# ---------------------------------------------------------------------------

class TestRoomContentInvariants:
    """Room content must always be a valid RoomType."""

    @pytest.mark.parametrize("roll", range(2, 13))
    def test_room_content_type_is_valid(self, roll):
        """Every 2d6 roll (2-12) produces a valid RoomType."""
        dungeon = Dungeon()
        content = dungeon.generate_room_content(force_roll=roll)
        assert isinstance(content.type, RoomType)

    def test_out_of_range_roll_returns_empty(self):
        """A roll outside 2-12 defaults to EMPTY."""
        dungeon = Dungeon()
        content = dungeon.generate_room_content(force_roll=1)
        assert content.type == RoomType.EMPTY
        content = dungeon.generate_room_content(force_roll=13)
        assert content.type == RoomType.EMPTY


# ---------------------------------------------------------------------------
# Message log invariant
# ---------------------------------------------------------------------------

class TestMessageLogInvariant:

    def test_message_log_never_exceeds_100(self):
        """log_message trims the log to the last 100 entries."""
        gm = GameManager("log-test")
        for i in range(150):
            gm.log_message(f"msg-{i}")
        assert len(gm.message_log) <= 100
        # Most recent message should be the last one added
        assert gm.message_log[-1] == "msg-149"


# ---------------------------------------------------------------------------
# Game start preconditions
# ---------------------------------------------------------------------------

class TestGameStartPreconditions:

    def test_cannot_start_without_players(self):
        """start() raises if there are no players."""
        gm = GameManager("empty")
        with pytest.raises(ValueError, match="at least 1"):
            gm.start()

    def test_cannot_start_without_characters(self):
        """start() raises if any player lacks a character."""
        gm = GameManager("no-char")
        gm.add_player("Alice")
        with pytest.raises(ValueError, match="characters"):
            gm.start()

    def test_cannot_add_fifth_player(self):
        """Adding a 5th player raises."""
        gm = GameManager("full")
        for i in range(4):
            gm.add_player(f"P{i}")
        with pytest.raises(ValueError, match="full"):
            gm.add_player("Extra")

    def test_cannot_create_character_after_start(self):
        """create_character raises after the game has started."""
        gm = _started_game(("Warrior",))
        pid = list(gm.players.keys())[0]
        with pytest.raises(ValueError, match="started"):
            gm.create_character(pid, "Rogue", "Late")


# ---------------------------------------------------------------------------
# Character class case normalization
# ---------------------------------------------------------------------------

class TestClassCaseNormalization:

    @pytest.mark.parametrize("raw,expected", [
        ("warrior", "Warrior"),
        ("WARRIOR", "Warrior"),
        ("Warrior", "Warrior"),
        ("cleric", "Cleric"),
        ("HALFLING", "Halfling"),
    ])
    def test_case_insensitive_creation(self, raw, expected):
        """create_character normalizes class names via .title()."""
        char = create_character(raw, "Test")
        assert char.class_type == expected

    def test_invalid_class_raises(self):
        """An unknown class name raises ValueError."""
        with pytest.raises(ValueError):
            create_character("Necromancer", "Test")


# ---------------------------------------------------------------------------
# Monster invariants
# ---------------------------------------------------------------------------

class TestMonsterInvariants:

    def test_monster_life_never_below_zero(self):
        """Monster.take_damage clamps life at 0."""
        m = Boss("Test", level=5, life=3)
        m.take_damage(100)
        assert m.life == 0

    def test_minion_has_one_life(self):
        """Minions always have exactly 1 life."""
        m = Minion("Goblin", level=3)
        assert m.life == 1
        assert m.max_life == 1

    def test_boss_preserves_max_life(self):
        """Boss max_life is set at creation and does not change with damage."""
        b = Boss("Ogre", level=5, life=6)
        b.take_damage(3)
        assert b.max_life == 6
        assert b.life == 3


# ---------------------------------------------------------------------------
# _monster_attack stale-list regression (QA Report §2.3)
# ---------------------------------------------------------------------------

class TestMonsterAttackStaleList:
    """Regression test for the stale living-character list in _monster_attack.

    _monster_attack() captures party = get_living_characters() once, then
    iterates over every monster using the same list.  If an earlier monster
    kills a character, resolve_monster_attack() skips the dead character
    (returning fewer results), but the outer zip(party, results) still pairs
    the first result with the first (now-dead) character.  This causes:
      • a duplicate "has fallen!" log for the already-dead character, and
      • the actually-targeted character's hit going unlogged.
    """

    def test_stale_list_causes_duplicate_fallen_message(self, monkeypatch):
        """Demonstrate the zip-misalignment bug in _monster_attack.

        Setup:
          - Two characters: Hero0 (1 HP), Hero1 (full HP)
          - Two monsters (level 10) so every defense roll fails
          - Monkeypatch explosive_six to always return 1

        Expected bug behaviour:
          Monster 1 kills Hero0 and hits Hero1.
          Monster 2 should target only Hero1 (Hero0 is dead), but because
          resolve_monster_attack returns one fewer result while the stale
          party list still starts with Hero0, zip pairs Hero0 with Hero1's
          result → duplicate "Hero0 has fallen!" in the log.
        """
        from src.dice import DiceResult

        # Force every die roll to 1 so defense always fails (1 + 5 = 6 < 10)
        monkeypatch.setattr(
            "src.combat.explosive_six",
            lambda force_rolls=None: DiceResult(total=1, rolls=[1]),
        )

        gm = _started_game(("Warrior", "Warrior"))
        hero0 = gm.dungeon.party.characters[0]
        hero1 = gm.dungeon.party.characters[1]

        # Weaken Hero0 so one hit kills them
        hero0.take_damage(hero0.life - 1)
        assert hero0.life == 1

        gm.combat_active = True
        gm.current_monsters = [
            Minion("Orc_A", level=10),
            Minion("Orc_B", level=10),
        ]
        gm.message_log.clear()

        gm._monster_attack()

        fallen_messages = [m for m in gm.message_log if "has fallen" in m]
        hero0_fallen = [m for m in fallen_messages if hero0.name in m]

        # BUG: Hero0's "has fallen!" message appears twice due to stale list.
        # When the bug is fixed this assertion should be changed to == 1.
        assert len(hero0_fallen) == 2, (
            "Expected the stale-list bug to produce a duplicate 'has fallen!' "
            f"message for {hero0.name}. Got: {hero0_fallen}"
        )

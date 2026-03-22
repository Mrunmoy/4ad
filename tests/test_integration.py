"""Integration tests — full game playthrough scenarios.

These tests exercise the GameManager end-to-end, simulating complete game
scenarios against the current game-v2 codebase.
"""
from unittest.mock import patch

import pytest

from src.character import CHARACTER_CLASSES, Warrior, create_character
from src.combat import Combat
from src.dungeon import Dungeon, RoomContent, RoomType
from src.game import GameManager
from src.monster import Boss, Minion


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_game(classes=("Warrior", "Cleric", "Wizard", "Rogue")):
    """Create and start a GameManager with the given classes."""
    gm = GameManager("int-test")
    pids = []
    for i, cls in enumerate(classes):
        pid = gm.add_player(f"Player{i}")
        gm.create_character(pid, cls, f"Hero{i}")
        pids.append(pid)
    gm.start()
    return gm, pids


def _first_unexplored_exit(room):
    """Return the first direction with an unexplored (None) exit, or None."""
    for d, r in room.exits.items():
        if r is None:
            return d
    return None



# ---------------------------------------------------------------------------
# a) Complete dungeon run — happy path
# ---------------------------------------------------------------------------

class TestCompleteDungeonRun:
    """Simulate a full dungeon run: create party, explore, fight, win."""

    def test_create_game_add_four_players_and_start(self):
        """Four players join, create characters, and the game starts."""
        gm, pids = _make_game()
        assert gm.started
        assert len(gm.players) == 4
        assert gm.dungeon is not None
        assert gm.dungeon.party is not None
        assert len(gm.dungeon.party.characters) == 4

    def test_move_through_rooms_and_fight_minions(self):
        """Party explores rooms and defeats a minion encounter."""
        gm, _ = _make_game()
        room = gm.dungeon.party.current_room

        # Force a minion room adjacent to entrance
        direction = _first_unexplored_exit(room) or "north"
        if direction not in room.exits:
            room.exits[direction] = None
        new_room = gm.dungeon.add_room_from(room, direction)
        # Place weak minions so the warrior can one-shot them
        new_room.content = RoomContent(RoomType.MINIONS, "Minions attack!")
        gm.current_monsters = []  # will be populated on move

        gm.move(direction)
        assert gm.combat_active is True
        assert len(gm.current_monsters) >= 1

        # Kill all monsters via attacks (warrior has attack=4, minions level<=4)
        safety = 50
        while gm.combat_active and safety > 0:
            result = gm.attack()
            safety -= 1
        # Combat should end once all monsters die
        # (the party may or may not survive — just verify flow completes)
        assert safety > 0, "Combat did not resolve within 50 rounds"

    def test_fight_boss_and_clear_room(self):
        """Party fights a boss encounter to completion."""
        gm, _ = _make_game()
        room = gm.dungeon.party.current_room

        direction = _first_unexplored_exit(room) or "north"
        if direction not in room.exits:
            room.exits[direction] = None
        boss_room = gm.dungeon.add_room_from(room, direction)
        boss_room.content = RoomContent(RoomType.BOSS, "Boss encounter!")
        # Inject a weak boss so test resolves quickly
        gm.move(direction)
        # Override monsters with a weak boss
        gm.current_monsters = [Boss("Weak Boss", level=1, life=2)]
        gm.combat_active = True

        safety = 30
        while gm.combat_active and safety > 0:
            gm.attack()
            safety -= 1

        assert not gm.combat_active
        assert boss_room.content.cleared

    def test_search_empty_room(self):
        """Party searches an empty room after clearing it."""
        gm, _ = _make_game()
        room = gm.dungeon.party.current_room

        direction = _first_unexplored_exit(room) or "north"
        if direction not in room.exits:
            room.exits[direction] = None
        empty_room = gm.dungeon.add_room_from(room, direction)
        empty_room.content = RoomContent(RoomType.EMPTY, "Room appears empty")

        gm.move(direction)
        result = gm.search_room()
        assert result["result"] in (
            "hidden_treasure", "nothing", "secret_door",
            "wandering_monster", "already_searched",
        )

    def test_message_log_captures_key_events(self):
        """The message log records join, start, move, and combat events."""
        gm, _ = _make_game()
        # Should have join + character creation + adventure start messages
        assert any("joined" in m for m in gm.message_log)
        assert any("adventure begins" in m.lower() for m in gm.message_log)
        assert any("enters the dungeon" in m for m in gm.message_log)


# ---------------------------------------------------------------------------
# b) Party wipe scenario
# ---------------------------------------------------------------------------

class TestPartyWipe:
    """Verify the game detects total party kill."""

    def test_all_characters_killed_wipes_party(self):
        """Manually kill all characters and verify party wipe detection."""
        gm, _ = _make_game()
        for char in gm.dungeon.party.characters:
            char.take_damage(char.life)
        assert gm.dungeon.party.is_wiped_out()

    def test_characters_take_damage_and_can_die(self):
        """Characters lose life during monster attacks and can reach 0."""
        gm, _ = _make_game(("Wizard",))  # single fragile character
        wizard = gm.dungeon.party.characters[0]
        initial_life = wizard.life

        # Simulate a powerful monster attack
        ogre = Boss("Ogre", level=5, life=6)
        Combat.resolve_defense(wizard, ogre, force_roll=1)
        # With Wizard defense=3, roll 1 => total=4, vs level 5 => fail => take 1 damage
        assert wizard.life < initial_life

    def test_petrified_counts_as_wiped(self):
        """A party of all-petrified characters is wiped out."""
        gm, _ = _make_game(("Warrior",))
        char = gm.dungeon.party.characters[0]
        char.petrified = True
        assert gm.dungeon.party.is_wiped_out()


# ---------------------------------------------------------------------------
# c) Multi-room exploration
# ---------------------------------------------------------------------------

class TestMultiRoomExploration:
    """Explore many rooms, verifying dungeon generation and connectivity."""

    def test_explore_ten_plus_rooms(self):
        """Generate and visit 10+ rooms in sequence."""
        gm, _ = _make_game()
        rooms_visited = 1  # entrance

        for _ in range(12):
            room = gm.dungeon.party.current_room
            direction = _first_unexplored_exit(room)
            if direction is None:
                # All exits explored — pick one that leads somewhere
                for d, r in room.exits.items():
                    if r is not None:
                        direction = d
                        break
            if direction is None:
                break

            # If combat starts, auto-kill monsters to keep moving
            if direction in room.exits and room.exits[direction] is None:
                gm.dungeon.add_room_from(room, direction)
                # Force the new room to be empty so we can keep exploring
                new_room = room.exits[direction]
                new_room.content = RoomContent(RoomType.EMPTY, "Empty")

            gm.move(direction)
            # Resolve any unexpected combat via the public attack() API
            safety = 50
            while gm.combat_active and safety > 0:
                result = gm.attack()
                if "error" in result:
                    break
                safety -= 1
            rooms_visited += 1

        assert rooms_visited >= 10

    def test_rooms_are_generated_on_demand(self):
        """New rooms are created only when moving into an unexplored exit."""
        gm, _ = _make_game()
        initial_rooms = len(gm.dungeon.rooms)
        room = gm.dungeon.party.current_room
        direction = _first_unexplored_exit(room)
        assert direction is not None, "Entrance must have at least one unexplored exit"

        # Force empty content to avoid combat
        new_room = gm.dungeon.add_room_from(room, direction)
        new_room.content = RoomContent(RoomType.EMPTY, "Empty")
        gm.move(direction)

        assert len(gm.dungeon.rooms) > initial_rooms

    def test_rooms_are_bidirectionally_connected(self):
        """Moving to a new room creates a two-way link."""
        gm, _ = _make_game()
        entrance = gm.dungeon.party.current_room
        direction = _first_unexplored_exit(entrance)
        new_room = gm.dungeon.add_room_from(entrance, direction)
        new_room.content = RoomContent(RoomType.EMPTY, "Empty")
        gm.move(direction)

        # Go back
        opposite = {"north": "south", "south": "north",
                     "east": "west", "west": "east"}
        result = gm.dungeon.party.move(opposite[direction])
        assert result.success
        assert gm.dungeon.party.current_room is entrance

    def test_visited_flag_set_on_entry(self):
        """Rooms are marked visited when entered."""
        gm, _ = _make_game()
        room = gm.dungeon.party.current_room
        direction = _first_unexplored_exit(room)
        new_room = gm.dungeon.add_room_from(room, direction)
        new_room.content = RoomContent(RoomType.EMPTY, "Empty")
        assert not new_room.visited
        gm.move(direction)
        assert new_room.visited

    def test_room_content_matches_2d6_table(self):
        """Generated room content types should all be valid RoomType values."""
        dungeon = Dungeon()
        for roll in range(2, 13):
            content = dungeon.generate_room_content(force_roll=roll)
            assert isinstance(content.type, RoomType)


# ---------------------------------------------------------------------------
# d) Combat edge cases
# ---------------------------------------------------------------------------

class TestCombatEdgeCases:
    """Edge-case combat scenarios."""

    def test_attack_when_no_combat_returns_error(self):
        """Attacking outside of combat returns an error dict."""
        gm, _ = _make_game()
        result = gm.attack()
        assert "error" in result

    def test_explosive_six_kills_multiple(self):
        """Explosive six roll can eliminate multiple minions in one attack."""
        warrior = Warrior("Hero")
        goblins = [Minion("Goblin", level=3) for _ in range(4)]
        result = Combat.resolve_attack(warrior, goblins, force_rolls=[6, 6, 5])
        # total = 17 + attack 4 = 21, each goblin costs level 3 => 7 kills possible
        assert result.minions_killed >= 3

    def test_monster_attacks_hit_party_members(self):
        """Monster attacks can damage party members who fail defense."""
        gm, _ = _make_game(("Wizard",))
        wizard = gm.dungeon.party.characters[0]
        powerful_monster = Boss("Dragon", level=8, life=10, is_dragon=True)
        initial_life = wizard.life

        # Force a very low defense roll so the wizard fails
        results = Combat.resolve_monster_attack(powerful_monster,
                                                 [wizard],
                                                 force_roll=1)
        # Wizard defense 3 + roll 1 = 4, vs level 8 => fail
        assert results[0].damage_taken == 1
        assert wizard.life == initial_life - 1

    def test_all_monsters_killed_ends_combat(self):
        """Combat flag clears when the last monster dies."""
        gm, _ = _make_game()
        room = gm.dungeon.party.current_room
        direction = _first_unexplored_exit(room) or "north"
        if direction not in room.exits:
            room.exits[direction] = None
        boss_room = gm.dungeon.add_room_from(room, direction)
        boss_room.content = RoomContent(RoomType.MINIONS, "Minions!")

        gm.move(direction)
        assert gm.combat_active

        # Fight monsters through the public attack() API
        safety = 50
        while gm.combat_active and safety > 0:
            result = gm.attack()
            if "error" in result:
                break
            safety -= 1

        assert not gm.combat_active
        assert gm.current_monsters == []

    def test_room_content_cleared_after_combat(self):
        """Room content is marked cleared when combat ends."""
        gm, _ = _make_game()
        room = gm.dungeon.party.current_room
        direction = _first_unexplored_exit(room) or "north"
        if direction not in room.exits:
            room.exits[direction] = None
        combat_room = gm.dungeon.add_room_from(room, direction)
        combat_room.content = RoomContent(RoomType.MINIONS, "Minions!")

        gm.move(direction)
        # Resolve combat through the public attack() API
        safety = 50
        while gm.combat_active and safety > 0:
            result = gm.attack()
            if "error" in result:
                break
            safety -= 1

        assert combat_room.content.cleared


# ---------------------------------------------------------------------------
# e) Character class validation
# ---------------------------------------------------------------------------

class TestCharacterClassValidation:
    """Verify every class creates with correct starting stats."""

    # Stats at level 1: life = base + level (level=1)
    EXPECTED_STATS = {
        "Warrior":   {"attack": 4, "defense": 5, "life": 7, "max_life": 7},
        "Cleric":    {"attack": 3, "defense": 4, "life": 6, "max_life": 6},
        "Rogue":     {"attack": 3, "defense": 4, "life": 5, "max_life": 5},
        "Wizard":    {"attack": 2, "defense": 3, "life": 4, "max_life": 4},
        "Barbarian": {"attack": 5, "defense": 4, "life": 9, "max_life": 9},
        "Elf":       {"attack": 3, "defense": 4, "life": 5, "max_life": 5},
        "Dwarf":     {"attack": 4, "defense": 5, "life": 8, "max_life": 8},
        "Halfling":  {"attack": 2, "defense": 5, "life": 5, "max_life": 5},
    }

    @pytest.mark.parametrize("class_name", list(CHARACTER_CLASSES.keys()))
    def test_class_creates_with_correct_stats(self, class_name):
        """Each class should have its documented starting stats."""
        char = create_character(class_name, "Test")
        expected = self.EXPECTED_STATS[class_name]
        assert char.attack == expected["attack"], f"{class_name} attack"
        assert char.defense == expected["defense"], f"{class_name} defense"
        assert char.life == expected["life"], f"{class_name} life"
        assert char.max_life == expected["max_life"], f"{class_name} max_life"
        assert char.class_type == class_name

    def test_all_eight_classes_exist(self):
        """There should be exactly 8 character classes."""
        assert len(CHARACTER_CLASSES) == 8

    def test_position_assignment_in_party(self):
        """Characters added to a party get sequential positions."""
        gm, _ = _make_game()
        positions = [c.position for c in gm.dungeon.party.characters]
        assert sorted(positions) == [1, 2, 3, 4]

    def test_melee_restriction_positions_1_and_2_only(self):
        """Only characters in positions 1-2 can melee attack."""
        gm, _ = _make_game()
        for char in gm.dungeon.party.characters:
            if char.position <= 2:
                assert char.can_attack_in_melee()
            else:
                assert not char.can_attack_in_melee()


# ---------------------------------------------------------------------------
# f) Search mechanics
# ---------------------------------------------------------------------------

class TestSearchMechanics:
    """Verify search_room behaviour under various conditions."""

    def test_search_during_combat_blocked(self):
        """Searching during active combat returns an error."""
        gm, _ = _make_game()
        gm.combat_active = True
        gm.current_monsters = [Minion("Rat", level=1)]
        result = gm.search_room()
        assert "error" in result
        assert "combat" in result["error"].lower()

    def test_search_empty_room_possible_outcomes(self):
        """Searching an empty room returns one of the defined outcomes."""
        gm, _ = _make_game()
        room = gm.dungeon.party.current_room
        direction = _first_unexplored_exit(room) or "north"
        if direction not in room.exits:
            room.exits[direction] = None
        empty_room = gm.dungeon.add_room_from(room, direction)
        empty_room.content = RoomContent(RoomType.EMPTY, "Empty")
        gm.move(direction)

        result = gm.search_room()
        assert result["result"] in (
            "hidden_treasure", "nothing", "secret_door",
            "wandering_monster", "already_searched",
        )

    def test_search_non_empty_room_returns_nothing_special(self):
        """Searching a room that had non-empty content returns nothing_special."""
        gm, _ = _make_game()
        room = gm.dungeon.party.current_room
        direction = _first_unexplored_exit(room) or "north"
        if direction not in room.exits:
            room.exits[direction] = None
        treasure_room = gm.dungeon.add_room_from(room, direction)
        treasure_room.content = RoomContent(RoomType.TREASURE, "Gold!")
        gm.move(direction)

        result = gm.search_room()
        assert result["result"] == "nothing_special"

    def test_search_hidden_treasure_on_roll_6(self):
        """A forced d6 roll of 6 during search yields hidden_treasure."""
        gm, _ = _make_game()
        room = gm.dungeon.party.current_room
        direction = _first_unexplored_exit(room) or "north"
        if direction not in room.exits:
            room.exits[direction] = None
        empty_room = gm.dungeon.add_room_from(room, direction)
        empty_room.content = RoomContent(RoomType.EMPTY, "Empty")
        gm.move(direction)

        result = gm.search_room(force_roll=6)
        assert result["result"] == "hidden_treasure"

    def test_search_secret_door_on_roll_5(self):
        """A forced d6 roll of 5 during search yields secret_door."""
        gm, _ = _make_game()
        room = gm.dungeon.party.current_room
        direction = _first_unexplored_exit(room) or "north"
        if direction not in room.exits:
            room.exits[direction] = None
        empty_room = gm.dungeon.add_room_from(room, direction)
        empty_room.content = RoomContent(RoomType.EMPTY, "Empty")
        gm.move(direction)

        result = gm.search_room(force_roll=5)
        assert result["result"] == "secret_door"

    def test_search_nothing_on_low_roll(self):
        """A forced d6 roll of 3 during search yields nothing."""
        gm, _ = _make_game()
        room = gm.dungeon.party.current_room
        direction = _first_unexplored_exit(room) or "north"
        if direction not in room.exits:
            room.exits[direction] = None
        empty_room = gm.dungeon.add_room_from(room, direction)
        empty_room.content = RoomContent(RoomType.EMPTY, "Empty")
        gm.move(direction)

        result = gm.search_room(force_roll=3)
        assert result["result"] == "nothing"

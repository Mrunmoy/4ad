"""Tests for GameManager attack(), movement, and encounter-clearing behavior."""
from src.game import GameManager
from src.dungeon import RoomContent, RoomType
from src.monster import Boss


def _setup_game_with_combat(num_monsters: int = 2) -> tuple:
    """Set up a GameManager in active combat with Boss monsters.

    Uses level-1 bosses with 10 life so the warrior always hits/defends
    and monsters survive multiple attacks, keeping combat active.
    """
    gm = GameManager("test-game")
    player_id = gm.add_player("Alice")
    gm.create_character(player_id, "Warrior", "Brynn")
    gm.start()

    monsters = [Boss(f"Monster {idx}", level=1, life=10) for idx in range(num_monsters)]
    gm.current_monsters = monsters
    gm.combat_active = True
    return gm, monsters


class TestAttackTargeting:
    """Tests for attack() target_idx selection logic."""

    def test_attack_targets_first_monster_by_default(self):
        """attack() with no args targets the first living monster."""
        gm, monsters = _setup_game_with_combat(2)
        result = gm.attack()
        assert result.get("target") == monsters[0].name

    def test_attack_honors_target_idx(self):
        """attack(target_idx=1) targets the second monster when it is alive."""
        gm, monsters = _setup_game_with_combat(2)
        result = gm.attack(target_idx=1)
        assert result.get("target") == monsters[1].name

    def test_attack_falls_back_when_idx_targets_dead_monster(self):
        """attack(target_idx=0) falls back to first living monster when idx 0 is dead."""
        gm, monsters = _setup_game_with_combat(2)
        monsters[0].life = 0  # kill first monster manually
        result = gm.attack(target_idx=0)
        assert result.get("target") == monsters[1].name

    def test_attack_falls_back_when_idx_out_of_range(self):
        """attack(target_idx=99) falls back to first living monster on out-of-range index."""
        gm, monsters = _setup_game_with_combat(2)
        result = gm.attack(target_idx=99)
        assert result.get("target") == monsters[0].name

    def test_attack_returns_error_when_no_combat(self):
        """attack() returns an error dict when no combat is active."""
        gm = GameManager("test-game")
        result = gm.attack()
        assert "error" in result

    def test_attack_returns_error_with_no_living_targets(self):
        """attack() returns an error when all monsters are dead."""
        gm, monsters = _setup_game_with_combat(2)
        for m in monsters:
            m.life = 0
        result = gm.attack()
        assert "error" in result


def _setup_started_game() -> GameManager:
    """Return a started GameManager with one warrior character."""
    gm = GameManager("test-game")
    player_id = gm.add_player("Alice")
    gm.create_character(player_id, "Warrior", "Brynn")
    gm.start()
    return gm


class TestMoveIntoUnexploredExit:
    """Tests for GameManager.move() when the exit leads to an unexplored room."""

    def test_move_into_none_exit_succeeds(self):
        """Moving into a None (unexplored) exit should succeed and create a new room."""
        gm = _setup_started_game()
        room = gm.dungeon.party.current_room
        # Ensure at least one exit is unexplored (None)
        unexplored = [d for d, r in room.exits.items() if r is None]
        assert unexplored, "entrance room must have at least one unexplored exit"
        direction = unexplored[0]

        result = gm.move(direction)

        assert result is True

    def test_move_into_none_exit_creates_and_links_room(self):
        """A new room should be created and linked bidirectionally when moving into a None exit."""
        gm = _setup_started_game()
        room = gm.dungeon.party.current_room
        unexplored = [d for d, r in room.exits.items() if r is None]
        assert unexplored, "entrance room must have at least one unexplored exit"
        direction = unexplored[0]

        gm.move(direction)

        new_room = gm.dungeon.party.current_room
        assert new_room is not room
        # Original room's exit now points to the new room
        assert room.exits[direction] is new_room
        # New room has a reciprocal exit that leads back to the original room
        assert room in new_room.exits.values()
        # New room is tracked in the dungeon and mapped to the same object
        assert gm.dungeon.rooms[new_room.number] is new_room

    def test_move_into_none_exit_logs_message(self):
        """Moving into an unexplored exit should log the party's movement."""
        gm = _setup_started_game()
        room = gm.dungeon.party.current_room
        unexplored = [d for d, r in room.exits.items() if r is None]
        assert unexplored, "entrance room must have at least one unexplored exit"
        direction = unexplored[0]

        gm.move(direction)

        new_room = gm.dungeon.party.current_room
        assert any(
            direction in msg and str(new_room.number) in msg
            for msg in gm.message_log
        )


class TestEncounterClearing:
    """Tests that non-combat encounters are marked cleared and don't re-trigger."""

    def _setup_game_with_treasure_room(self):
        """Set up a game with a TREASURE room adjacent to the entrance."""
        gm = _setup_started_game()
        dungeon = gm.dungeon
        entrance = dungeon.party.current_room

        # Add a room going north and force its content to TREASURE
        treasure_room = dungeon.add_room_from(entrance, "north")
        treasure_room.content = RoomContent(RoomType.TREASURE, "Treasure found!")
        return gm, treasure_room

    def test_treasure_room_sets_cleared_on_first_visit(self):
        """Entering a TREASURE room should mark content.cleared = True."""
        gm, treasure_room = self._setup_game_with_treasure_room()

        gm.move("north")

        assert gm.dungeon.party.current_room is treasure_room
        assert treasure_room.content.cleared is True

    def test_treasure_encounter_does_not_retrigger_on_second_visit(self):
        """Re-entering a cleared TREASURE room must not fire the encounter again."""
        gm, treasure_room = self._setup_game_with_treasure_room()

        # First visit – encounter triggers
        gm.move("north")
        first_log_count = gm.message_log.count("Treasure found!")

        # Return to entrance (reciprocal exit set by set_exit)
        gm.move("south")

        # Second visit – encounter must NOT trigger again
        gm.move("north")
        second_log_count = gm.message_log.count("Treasure found!")

        assert first_log_count == 1
        assert second_log_count == 1  # unchanged from first visit

    def test_empty_room_cleared_on_first_visit(self):
        """An EMPTY room should be marked cleared on first visit."""
        gm = _setup_started_game()
        dungeon = gm.dungeon
        entrance = dungeon.party.current_room

        empty_room = dungeon.add_room_from(entrance, "north")
        empty_room.content = RoomContent(RoomType.EMPTY, "The room appears empty")

        gm.move("north")

        assert empty_room.content.cleared is True

    def test_empty_encounter_does_not_retrigger(self):
        """Re-entering a cleared EMPTY room must not fire the encounter again."""
        gm = _setup_started_game()
        dungeon = gm.dungeon
        entrance = dungeon.party.current_room

        empty_room = dungeon.add_room_from(entrance, "north")
        empty_room.content = RoomContent(RoomType.EMPTY, "The room appears empty")

        gm.move("north")
        first_empty_count = gm.message_log.count("The room appears empty")

        gm.move("south")
        gm.move("north")
        second_empty_count = gm.message_log.count("The room appears empty")

        assert first_empty_count == 1
        assert second_empty_count == 1

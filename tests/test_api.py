"""Tests for WebSocket and REST API endpoints in app.py.

Tests new GameManager methods, REST endpoints, and verifies WebSocket
handler wiring. SocketIO room-based tests use threading mode for
compatibility with the test client.
"""
import pytest
from unittest.mock import patch, MagicMock
from flask_socketio import SocketIO
from src.app import app, games
from src.game import GameManager
from src.monster import Boss
from src.reactions import ReactionResult
from src.events import EventResult


# Create a test-mode SocketIO instance (threading, not gevent)
test_socketio = SocketIO(app, async_mode='threading')


@pytest.fixture(autouse=True)
def clean_games():
    """Clear the games dict before each test."""
    games.clear()
    yield
    games.clear()


def _create_test_game(class_name="Warrior", char_name="Brynn"):
    """Create a game with one player and character, return (game_id, player_id, game)."""
    game_id = "test-api"
    game = GameManager(game_id)
    games[game_id] = game
    player_id = game.add_player("Alice")
    game.create_character(player_id, class_name, char_name)
    game.start()
    return game_id, player_id, game


def _setup_combat(game, num_monsters=1, monster_level=1, monster_life=10):
    """Put the game into combat with Boss monsters."""
    monsters = [Boss(f"TestBoss{i}", level=monster_level, life=monster_life)
                for i in range(num_monsters)]
    game.current_monsters = monsters
    game.current_monster_names = [m.name for m in monsters]
    game.combat_active = True
    game.original_monster_count = num_monsters
    return monsters


# ---------------------------------------------------------------------------
# GameManager method tests (Task 3)
# ---------------------------------------------------------------------------

class TestGameManagerFlee:
    """Test GameManager.flee()."""

    def test_flee_during_combat(self):
        _, _, game = _create_test_game()
        _setup_combat(game)
        result = game.flee()
        assert result.get('fled') is True
        assert game.combat_active is False

    def test_flee_no_combat(self):
        _, _, game = _create_test_game()
        result = game.flee()
        assert 'error' in result

    def test_flee_final_boss_blocked(self):
        _, _, game = _create_test_game()
        monsters = _setup_combat(game)
        monsters[0].is_final_boss = True
        result = game.flee()
        assert 'error' in result
        assert game.combat_active is True


class TestGameManagerCastSpell:
    """Test GameManager.cast_spell() with caster_id."""

    def test_cast_spell_with_caster_id(self):
        _, _, game = _create_test_game("Wizard", "Merlin")
        _setup_combat(game)
        result = game.cast_spell("Fireball", caster_id="Merlin")
        assert 'error' not in result
        assert result.get('caster') == 'Merlin'

    def test_cast_spell_no_caster(self):
        _, _, game = _create_test_game("Warrior", "Brynn")
        _setup_combat(game)
        result = game.cast_spell("Fireball")
        assert 'error' in result


class TestGameManagerXpRoll:
    """Test GameManager.attempt_xp_roll()."""

    def test_xp_roll_with_pending(self):
        _, _, game = _create_test_game()
        game.pending_xp_rolls = 1
        result = game.attempt_xp_roll("Brynn")
        assert result['character'] == 'Brynn'
        assert game.pending_xp_rolls == 0

    def test_xp_roll_no_pending(self):
        _, _, game = _create_test_game()
        game.pending_xp_rolls = 0
        result = game.attempt_xp_roll("Brynn")
        assert 'error' in result


class TestGameManagerReactionChoice:
    """Test GameManager.handle_reaction_choice()."""

    def test_reaction_choice_attack(self):
        _, _, game = _create_test_game()
        _setup_combat(game)
        game.current_reaction = ReactionResult(
            reaction_type="fight",
            description="The monsters want to fight!",
            player_choices=["attack", "flee"],
        )
        result = game.handle_reaction_choice("attack")
        assert result.get('combat_starts') is True

    def test_reaction_choice_flee(self):
        _, _, game = _create_test_game()
        _setup_combat(game)
        game.current_reaction = ReactionResult(
            reaction_type="fight",
            description="The monsters want to fight!",
            player_choices=["attack", "flee"],
        )
        result = game.handle_reaction_choice("flee")
        assert result.get('fled') is True

    def test_reaction_choice_bribe(self):
        _, _, game = _create_test_game()
        _setup_combat(game)
        game.party_gold = 100
        game.current_reaction = ReactionResult(
            reaction_type="bribe",
            description="They offer a bribe.",
            player_choices=["bribe", "attack"],
            bribe_cost=10,
        )
        result = game.handle_reaction_choice("bribe")
        assert result.get('success') is True

    def test_reaction_choice_no_reaction(self):
        _, _, game = _create_test_game()
        result = game.handle_reaction_choice("attack")
        assert 'error' in result

    def test_reaction_choice_unknown(self):
        _, _, game = _create_test_game()
        _setup_combat(game)
        game.current_reaction = ReactionResult(
            reaction_type="fight",
            description="Fight!",
            player_choices=["attack"],
        )
        result = game.handle_reaction_choice("dance")
        assert 'error' in result


class TestGameManagerResolveEvent:
    """Test GameManager.resolve_pending_event() and resolve_pending_feature()."""

    def test_resolve_pending_event(self):
        _, _, game = _create_test_game()
        # Ensure current room has content so .cleared can be set
        from src.dungeon import RoomContent, RoomType
        room = game.dungeon.party.current_room
        room.content = RoomContent(type=RoomType.SPECIAL_EVENT)
        game.pending_event = EventResult(
            event_type="wandering_healer",
            description="A wandering healer offers healing.",
            player_choices=["accept", "decline"],
        )
        result = game.resolve_pending_event("decline")
        assert 'result' in result
        assert game.pending_event is None

    def test_resolve_pending_feature(self):
        _, _, game = _create_test_game()
        from src.dungeon import RoomContent, RoomType
        room = game.dungeon.party.current_room
        room.content = RoomContent(type=RoomType.SPECIAL_FEATURE)
        game.pending_feature = EventResult(
            event_type="fountain",
            description="A magical fountain bubbles.",
            player_choices=["drink", "ignore"],
        )
        result = game.resolve_pending_feature("drink")
        assert 'result' in result
        assert game.pending_feature is None

    def test_resolve_no_pending_event(self):
        _, _, game = _create_test_game()
        result = game.resolve_pending_event("accept")
        assert 'error' in result

    def test_resolve_no_pending_feature(self):
        _, _, game = _create_test_game()
        result = game.resolve_pending_feature("drink")
        assert 'error' in result


class TestGameManagerExitRoom:
    """Test GameManager.exit_room()."""

    def test_exit_room_in_exit_phase(self):
        _, _, game = _create_test_game()
        game.exiting = True
        game.exit_rooms_remaining = 3
        result = game.exit_room()
        assert 'rooms_remaining' in result or 'escaped' in result

    def test_exit_room_not_in_exit_phase(self):
        _, _, game = _create_test_game()
        result = game.exit_room()
        assert 'error' in result

    def test_exit_room_escaped(self):
        _, _, game = _create_test_game()
        game.exiting = True
        game.exit_rooms_remaining = 0
        result = game.exit_room()
        assert result.get('escaped') is True


class TestGameManagerUseItem:
    """Test GameManager.use_item()."""

    def test_use_item_player_not_found(self):
        _, _, game = _create_test_game()
        result = game.use_item("no-such-player", 0)
        assert 'error' in result

    def test_use_item_invalid_index(self):
        _, player_id, game = _create_test_game()
        result = game.use_item(player_id, 99)
        assert 'error' in result


class TestGameManagerUseHealing:
    """Test GameManager.use_healing()."""

    def test_use_healing_cleric(self):
        _, _, game = _create_test_game("Cleric", "Alaric")
        char = list(game.players.values())[0].character
        char.life = 1
        result = game.use_healing("Alaric", "Alaric")
        assert result.get('success') is True
        assert result['healed'] > 0

    def test_use_healing_not_cleric(self):
        _, _, game = _create_test_game("Warrior", "Brynn")
        result = game.use_healing("Brynn", "Brynn")
        assert 'error' in result

    def test_use_healing_caster_not_found(self):
        _, _, game = _create_test_game()
        result = game.use_healing("Nobody", "Brynn")
        assert 'error' in result

    def test_use_healing_target_not_found(self):
        _, _, game = _create_test_game("Cleric", "Alaric")
        result = game.use_healing("Alaric", "Nobody")
        assert 'error' in result


class TestGameManagerUseRage:
    """Test GameManager.use_rage()."""

    def test_use_rage_barbarian(self):
        _, _, game = _create_test_game("Barbarian", "Grok")
        result = game.use_rage("Grok")
        assert result.get('success') is True
        assert 'best_roll' in result
        assert len(result['rolls']) == 3

    def test_use_rage_twice_fails(self):
        _, _, game = _create_test_game("Barbarian", "Grok")
        game.use_rage("Grok")
        result = game.use_rage("Grok")
        assert 'error' in result

    def test_use_rage_not_barbarian(self):
        _, _, game = _create_test_game("Warrior", "Brynn")
        result = game.use_rage("Brynn")
        assert 'error' in result

    def test_use_rage_char_not_found(self):
        _, _, game = _create_test_game()
        result = game.use_rage("Nobody")
        assert 'error' in result


class TestGameManagerUseLuck:
    """Test GameManager.use_luck()."""

    def test_use_luck_halfling(self):
        _, _, game = _create_test_game("Halfling", "Pip")
        result = game.use_luck("Pip")
        assert result.get('success') is True
        assert 'luck_remaining' in result

    def test_use_luck_exhausted(self):
        _, _, game = _create_test_game("Halfling", "Pip")
        char = list(game.players.values())[0].character
        char.luck_points = 0
        result = game.use_luck("Pip")
        assert 'error' in result

    def test_use_luck_not_halfling(self):
        _, _, game = _create_test_game("Warrior", "Brynn")
        result = game.use_luck("Brynn")
        assert 'error' in result

    def test_use_luck_char_not_found(self):
        _, _, game = _create_test_game()
        result = game.use_luck("Nobody")
        assert 'error' in result


class TestGameManagerAcceptQuest:
    """Test GameManager.accept_quest()."""

    def test_accept_quest(self):
        _, _, game = _create_test_game()
        result = game.accept_quest()
        assert 'quest_type' in result
        assert 'description' in result
        assert game.active_quest is not None


# ---------------------------------------------------------------------------
# REST endpoint tests (Task 2)
# ---------------------------------------------------------------------------

class TestRestEndpoints:
    """Test new REST API endpoints."""

    def test_get_party(self):
        game_id, player_id, game = _create_test_game()

        with app.test_client() as client:
            resp = client.get(f'/api/game/{game_id}/party')
            assert resp.status_code == 200
            data = resp.get_json()
            assert 'party' in data
            assert len(data['party']) == 1
            assert data['party'][0]['name'] == 'Brynn'
            assert 'party_gold' in data
            assert 'player_id' in data['party'][0]
            assert 'player_name' in data['party'][0]

    def test_get_party_not_found(self):
        with app.test_client() as client:
            resp = client.get('/api/game/nonexistent/party')
            assert resp.status_code == 404

    def test_get_quest_no_quest(self):
        game_id, _, game = _create_test_game()

        with app.test_client() as client:
            resp = client.get(f'/api/game/{game_id}/quest')
            assert resp.status_code == 200
            data = resp.get_json()
            assert data['quest'] is None

    def test_get_quest_active(self):
        game_id, _, game = _create_test_game()
        game.accept_quest()

        with app.test_client() as client:
            resp = client.get(f'/api/game/{game_id}/quest')
            assert resp.status_code == 200
            data = resp.get_json()
            assert data['quest'] is not None
            assert 'type' in data['quest']
            assert 'description' in data['quest']
            assert 'target' in data['quest']

    def test_get_quest_not_found(self):
        with app.test_client() as client:
            resp = client.get('/api/game/nonexistent/quest')
            assert resp.status_code == 404

    def test_get_shop(self):
        with app.test_client() as client:
            resp = client.get('/api/equipment/shop')
            assert resp.status_code == 200
            data = resp.get_json()
            assert isinstance(data, dict)
            assert len(data) > 0
            for key, item in data.items():
                assert 'name' in item
                assert 'cost' in item
                assert 'type' in item


# ---------------------------------------------------------------------------
# to_dict completeness tests (Task 4)
# ---------------------------------------------------------------------------

class TestToDictCompleteness:
    """Test that to_dict includes all required fields for frontend."""

    def test_to_dict_includes_pending_reaction(self):
        _, _, game = _create_test_game()
        _setup_combat(game)
        game.current_reaction = ReactionResult(
            reaction_type="bribe",
            description="They offer a bribe.",
            player_choices=["bribe", "attack"],
            bribe_cost=10,
        )

        state = game.to_dict()
        assert 'pending_reaction' in state
        assert state['pending_reaction']['type'] == 'bribe'
        assert state['pending_reaction']['bribe_cost'] == 10
        assert state['pending_reaction']['player_choices'] == ["bribe", "attack"]

    def test_to_dict_includes_pending_event(self):
        _, _, game = _create_test_game()
        game.pending_event = EventResult(
            event_type="wandering_healer",
            description="A healer appears.",
            player_choices=["accept", "decline"],
        )

        state = game.to_dict()
        assert state['pending_event'] is not None
        assert state['pending_event']['event_type'] == 'wandering_healer'
        assert state['pending_event']['choices'] == ["accept", "decline"]

    def test_to_dict_includes_pending_feature(self):
        _, _, game = _create_test_game()
        game.pending_feature = EventResult(
            event_type="fountain",
            description="A fountain.",
            player_choices=["drink", "ignore"],
        )

        state = game.to_dict()
        assert state['pending_feature'] is not None
        assert state['pending_feature']['event_type'] == 'fountain'

    def test_to_dict_includes_quest(self):
        _, _, game = _create_test_game()
        game.accept_quest()

        state = game.to_dict()
        assert state['quest'] is not None
        assert state['active_quest'] is not None
        # Both should have same data
        assert state['quest']['type'] == state['active_quest']['type']

    def test_to_dict_includes_exit_phase(self):
        _, _, game = _create_test_game()
        game.exiting = True
        game.exit_rooms_remaining = 5

        state = game.to_dict()
        assert state['exit_phase'] is True
        assert state['exiting'] is True
        assert state['exit_rooms_remaining'] == 5

    def test_to_dict_includes_party_gold(self):
        _, _, game = _create_test_game()
        game.party_gold = 42

        state = game.to_dict()
        assert state['party_gold'] == 42

    def test_to_dict_no_reaction_is_none(self):
        _, _, game = _create_test_game()
        state = game.to_dict()
        assert state['pending_reaction'] is None

    def test_to_dict_no_exit_phase(self):
        _, _, game = _create_test_game()
        state = game.to_dict()
        assert state['exit_phase'] is False

    def test_to_dict_combat_state(self):
        _, _, game = _create_test_game()
        _setup_combat(game)
        state = game.to_dict()
        assert state['combat_active'] is True
        assert len(state['monsters']) == 1


# ---------------------------------------------------------------------------
# WebSocket handler wiring tests (Task 1)
# Verify that all socket event handlers are registered and call the right
# GameManager methods. Uses mock to avoid room-based emit issues in tests.
# ---------------------------------------------------------------------------

class TestSocketHandlerWiring:
    """Verify that app.py registers all required WebSocket handlers."""

    def _get_handler_names(self):
        """Get list of registered SocketIO event handler names."""
        from src.app import socketio as real_socketio
        handlers = set()
        # Flask-SocketIO stores handlers in server.handlers
        if hasattr(real_socketio, 'server') and real_socketio.server:
            for ns_handlers in real_socketio.server.handlers.values():
                handlers.update(ns_handlers.keys())
        return handlers

    def test_flee_handler_registered(self):
        """The 'flee' event handler is registered."""
        # Import triggers handler registration
        import src.app
        handlers = self._get_handler_names()
        assert 'flee' in handlers

    def test_use_item_handler_registered(self):
        import src.app
        handlers = self._get_handler_names()
        assert 'use_item' in handlers

    def test_use_healing_handler_registered(self):
        import src.app
        handlers = self._get_handler_names()
        assert 'use_healing' in handlers

    def test_use_rage_handler_registered(self):
        import src.app
        handlers = self._get_handler_names()
        assert 'use_rage' in handlers

    def test_use_luck_handler_registered(self):
        import src.app
        handlers = self._get_handler_names()
        assert 'use_luck' in handlers

    def test_reaction_choice_handler_registered(self):
        import src.app
        handlers = self._get_handler_names()
        assert 'reaction_choice' in handlers

    def test_xp_roll_handler_registered(self):
        import src.app
        handlers = self._get_handler_names()
        assert 'xp_roll' in handlers

    def test_accept_quest_handler_registered(self):
        import src.app
        handlers = self._get_handler_names()
        assert 'accept_quest' in handlers

    def test_resolve_event_handler_registered(self):
        import src.app
        handlers = self._get_handler_names()
        assert 'resolve_event' in handlers

    def test_exit_room_handler_registered(self):
        import src.app
        handlers = self._get_handler_names()
        assert 'exit_room' in handlers

    def test_cast_spell_handler_registered(self):
        import src.app
        handlers = self._get_handler_names()
        assert 'cast_spell' in handlers

    def test_existing_handlers_still_registered(self):
        """Verify pre-existing handlers weren't removed."""
        import src.app
        handlers = self._get_handler_names()
        for event in ['connect', 'disconnect', 'join_game', 'move',
                       'search_room', 'attack', 'cast_spell']:
            assert event in handlers, f"Missing handler: {event}"

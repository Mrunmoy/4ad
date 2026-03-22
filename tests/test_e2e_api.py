"""End-to-end API tests — validates complete game flow via Flask test client.

Tests the entire game lifecycle: create game, join players, create characters,
start game, and verify state completeness for frontend rendering.
"""
import pytest
from src.app import app, games
from src.game import GameManager
from src.monster import Boss, Minion


@pytest.fixture(autouse=True)
def clean_games():
    """Clear the games dict before each test."""
    games.clear()
    yield
    games.clear()


@pytest.fixture
def client():
    """Flask test client."""
    app.config['TESTING'] = True
    with app.test_client() as c:
        yield c


def _create_full_game(client):
    """Create a game with 4 players and characters, start it.

    Returns (game_id, player_ids, response_state).
    """
    # Create game
    r = client.post('/api/game/create')
    assert r.status_code == 200
    game_id = r.get_json()['game_id']

    # Join 4 players and create characters
    classes = ['Warrior', 'Cleric', 'Rogue', 'Wizard']
    names = ['Brynn', 'Aldric', 'Shade', 'Merlin']
    player_ids = []

    for i in range(4):
        jr = client.post(f'/api/game/{game_id}/join',
                         json={'player_name': f'Player{i + 1}'})
        assert jr.status_code == 200
        pid = jr.get_json()['player_id']
        player_ids.append(pid)

        cr = client.post(f'/api/game/{game_id}/character',
                         json={'player_id': pid,
                               'class_name': classes[i],
                               'char_name': names[i]})
        assert cr.status_code == 200

    # Start game
    sr = client.post(f'/api/game/{game_id}/start')
    assert sr.status_code == 200
    state = sr.get_json()

    return game_id, player_ids, state


class TestFullGameFlow:
    """Test creating a game, adding party, and verifying state."""

    def test_create_game(self, client):
        r = client.post('/api/game/create')
        assert r.status_code == 200
        data = r.get_json()
        assert 'game_id' in data
        assert 'join_url' in data

    def test_join_and_create_character(self, client):
        r = client.post('/api/game/create')
        game_id = r.get_json()['game_id']

        jr = client.post(f'/api/game/{game_id}/join',
                         json={'player_name': 'Alice'})
        assert jr.status_code == 200
        pid = jr.get_json()['player_id']

        cr = client.post(f'/api/game/{game_id}/character',
                         json={'player_id': pid,
                               'class_name': 'Warrior',
                               'char_name': 'Brynn'})
        assert cr.status_code == 200
        char = cr.get_json()
        assert char['class_type'] == 'Warrior'
        assert char['name'] == 'Brynn'

    def test_full_game_flow(self, client):
        """Create game, add party, start, verify initial state has correct room data."""
        game_id, player_ids, state = _create_full_game(client)

        assert state['started'] is True
        assert state['game_id'] == game_id
        assert len(state['players']) == 4

        # Verify dungeon is created
        assert state['dungeon'] is not None
        assert state['dungeon']['entrance'] is not None
        assert state['dungeon']['party_room'] is not None

        # Room should have exits
        party_room = str(state['dungeon']['party_room'])
        room = state['dungeon']['rooms'][party_room]
        assert len(room['exits']) > 0

        # Verify characters have correct data for rendering
        for player in state['players']:
            char = player['character']
            assert char is not None
            assert 'class_type' in char  # needed for portrait_key
            assert 'life' in char
            assert 'max_life' in char
            assert 'name' in char
            assert 'gold' in char or 'inventory' in char

    def test_status_endpoint_after_start(self, client):
        """Verify /status returns the same complete state."""
        game_id, _, _ = _create_full_game(client)

        r = client.get(f'/api/game/{game_id}/status')
        assert r.status_code == 200
        state = r.get_json()
        assert state['started'] is True
        assert state['dungeon'] is not None

    def test_party_endpoint(self, client):
        """Verify /party returns detailed character info."""
        game_id, _, _ = _create_full_game(client)

        r = client.get(f'/api/game/{game_id}/party')
        assert r.status_code == 200
        data = r.get_json()
        assert data['party_size'] == 4
        assert len(data['party']) == 4

        for char in data['party']:
            assert 'class_type' in char
            assert 'attack' in char
            assert 'defense' in char


class TestCombatMonsterData:
    """Verify combat state includes monster names for portrait rendering."""

    def test_combat_returns_monster_data(self, client):
        """Set up combat directly and verify monster data via status."""
        game_id, _, _ = _create_full_game(client)
        game = games[game_id]

        # Inject combat state
        monsters = [
            Boss("Troll", level=6, life=8),
            Minion("Goblin", level=3),
        ]
        game.current_monsters = monsters
        game.current_monster_names = [m.name for m in monsters]
        game.combat_active = True
        game.original_monster_count = len(monsters)

        r = client.get(f'/api/game/{game_id}/status')
        state = r.get_json()

        assert state['combat_active'] is True
        assert len(state['monsters']) == 2

        for monster in state['monsters']:
            assert 'name' in monster
            assert 'level' in monster
            assert 'life' in monster
            assert 'max_life' in monster

        assert state['monsters'][0]['name'] == 'Troll'
        assert state['monsters'][1]['name'] == 'Goblin'

    def test_monster_to_dict_fields(self):
        """Verify Monster.to_dict() has all fields needed by frontend."""
        boss = Boss("Dragon", level=8, life=10, is_dragon=True)
        d = boss.to_dict()
        required = ['name', 'level', 'life', 'max_life',
                     'is_undead', 'is_demon', 'is_dragon']
        for field in required:
            assert field in d, f"Missing field: {field}"


class TestRoomContentTypeForRendering:
    """Verify room content types map to known image assets."""

    VALID_CONTENT_TYPES = [
        'treasure', 'treasure_trap', 'special_event', 'special_feature',
        'vermin', 'minions', 'weird_monsters', 'boss', 'small_dragon',
        'empty', 'hidden_treasure', 'trap', 'secret_door',
    ]

    def test_room_content_is_valid_type(self, client):
        """After starting, all room content types should be valid or None."""
        game_id, _, _ = _create_full_game(client)

        r = client.get(f'/api/game/{game_id}/status')
        state = r.get_json()

        for room_id, room in state['dungeon']['rooms'].items():
            content = room.get('content')
            if content is not None:
                assert content in self.VALID_CONTENT_TYPES or content == '', \
                    f"Room {room_id} has unknown content type: {content}"

    def test_room_structure_for_rendering(self, client):
        """Verify room dict has all fields needed for map rendering."""
        game_id, _, _ = _create_full_game(client)

        r = client.get(f'/api/game/{game_id}/status')
        state = r.get_json()

        for room_id, room in state['dungeon']['rooms'].items():
            assert 'number' in room
            assert 'x' in room
            assert 'y' in room
            assert 'width' in room
            assert 'height' in room
            assert 'exits' in room
            assert 'visited' in room
            assert 'content' in room or room.get('content') is None


class TestGameStateCompleteness:
    """Verify to_dict() returns ALL fields needed by frontend."""

    def test_game_state_completeness(self, client):
        """Verify the game state has all required top-level fields."""
        game_id, _, _ = _create_full_game(client)

        r = client.get(f'/api/game/{game_id}/status')
        assert r.status_code == 200
        state = r.get_json()

        required_fields = [
            'game_id', 'started', 'players', 'dungeon',
            'combat_active', 'monsters', 'message_log',
        ]
        for field in required_fields:
            assert field in state, f"Missing field: {field}"

    def test_character_state_completeness(self, client):
        """Verify character state has all fields needed for CharacterCard."""
        game_id, _, _ = _create_full_game(client)

        r = client.get(f'/api/game/{game_id}/status')
        state = r.get_json()

        char_fields = [
            'name', 'level', 'class_type', 'attack', 'defense',
            'life', 'max_life',
        ]
        for player in state['players']:
            char = player['character']
            assert char is not None
            for field in char_fields:
                assert field in char, f"Missing char field: {field}"

    def test_dungeon_state_completeness(self, client):
        """Verify dungeon state has all fields needed for DungeonMap."""
        game_id, _, _ = _create_full_game(client)

        r = client.get(f'/api/game/{game_id}/status')
        state = r.get_json()

        dungeon = state['dungeon']
        assert dungeon is not None
        assert 'rooms' in dungeon
        assert 'entrance' in dungeon
        assert 'party_room' in dungeon
        assert len(dungeon['rooms']) > 0

    def test_class_types_match_portrait_keys(self, client):
        """Verify character class_type values can map to portrait texture keys."""
        valid_classes = ['Warrior', 'Cleric', 'Rogue', 'Wizard',
                         'Barbarian', 'Elf', 'Dwarf', 'Halfling']

        game_id, _, _ = _create_full_game(client)

        r = client.get(f'/api/game/{game_id}/status')
        state = r.get_json()

        for player in state['players']:
            char = player['character']
            assert char['class_type'] in valid_classes, \
                f"Unknown class: {char['class_type']}"

    def test_game_not_found(self, client):
        """Verify 404 for non-existent game."""
        r = client.get('/api/game/nonexistent/status')
        assert r.status_code == 404

    def test_join_requires_name(self, client):
        """Verify join validation."""
        r = client.post('/api/game/create')
        game_id = r.get_json()['game_id']

        jr = client.post(f'/api/game/{game_id}/join', json={})
        assert jr.status_code == 400

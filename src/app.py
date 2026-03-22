"""Flask web application for 4AD."""
from flask import Flask, render_template, jsonify, request, session, send_from_directory
from flask_socketio import SocketIO, emit, join_room, leave_room
import uuid
import os

from src.dungeon import Dungeon, Party
from src.character import create_character, CHARACTER_CLASSES
from src.game import GameManager
from src.campaign import CampaignManager

base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
app = Flask(__name__,
            template_folder=os.path.join(base_dir, 'templates'),
            static_folder=os.path.join(base_dir, 'static'))
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key')
socketio = SocketIO(app, cors_allowed_origins="*", async_mode="gevent")

# In-memory game storage
games: dict = {}

# Determine if we're serving the built Phaser app
CLIENT_DIST = os.path.join(base_dir, 'client', 'dist')
HAS_CLIENT_BUILD = os.path.exists(os.path.join(CLIENT_DIST, 'index.html'))


def get_game(game_id: str):
    """Get game by ID."""
    return games.get(game_id)


if HAS_CLIENT_BUILD:
    # Production: serve built Phaser app for non-API routes
    @app.route('/')
    def index():
        """Serve Phaser client."""
        return send_from_directory(CLIENT_DIST, 'index.html')

    @app.route('/game/<game_id>')
    def game_page(game_id):
        """Game page - serves SPA which handles game joining."""
        return send_from_directory(CLIENT_DIST, 'index.html')

    @app.route('/assets/<path:path>')
    def serve_client_assets(path):
        """Serve static assets from client/dist/assets."""
        return send_from_directory(os.path.join(CLIENT_DIST, 'assets'), path)

    @app.route('/favicon.ico')
    def serve_favicon():
        """Serve favicon from client/dist."""
        return send_from_directory(CLIENT_DIST, 'favicon.ico')
else:
    # Development: Vite dev server handles frontend; keep legacy template serving
    @app.route('/')
    def index():
        """Main page."""
        return render_template('index.html')

    @app.route('/game/<game_id>')
    def game_page(game_id):
        """Game page - serves SPA which handles game joining."""
        return render_template('index.html', game_id=game_id)


@app.route('/api/classes')
def get_classes():
    """Get available character classes."""
    return jsonify(list(CHARACTER_CLASSES.keys()))


@app.route('/api/game/create', methods=['POST'])
def create_game():
    """Create a new game."""
    game_id = str(uuid.uuid4())[:8]
    game = GameManager(game_id)
    games[game_id] = game
    return jsonify({
        "game_id": game_id,
        "join_url": f"/game/{game_id}"
    })


@app.route('/api/game/<game_id>/status')
def game_status(game_id: str):
    """Get game status."""
    game = get_game(game_id)
    if not game:
        return jsonify({"error": "Game not found"}), 404
    return jsonify(game.to_dict())


@app.route('/api/game/<game_id>/join', methods=['POST'])
def join_game(game_id: str):
    """Join a game."""
    game = get_game(game_id)
    if not game:
        return jsonify({"error": "Game not found"}), 404
    
    data = request.json
    player_name = data.get('player_name')
    
    if not player_name:
        return jsonify({"error": "Player name required"}), 400
    
    player_id = game.add_player(player_name)
    return jsonify({"player_id": player_id, "player_name": player_name})


@app.route('/api/game/<game_id>/character', methods=['POST'])
def create_character_endpoint(game_id: str):
    """Create character for player."""
    game = get_game(game_id)
    if not game:
        return jsonify({"error": "Game not found"}), 404
    
    data = request.json
    player_id = data.get('player_id')
    class_name = data.get('class_name')
    char_name = data.get('char_name')
    
    if not all([player_id, class_name, char_name]):
        return jsonify({"error": "Missing data"}), 400
    
    try:
        character = game.create_character(player_id, class_name, char_name)
        # Notify other players
        socketio.emit('character_created', {
            'player_id': player_id,
            'character': character.to_dict()
        }, room=game_id)
        return jsonify(character.to_dict())
    except ValueError as e:
        return jsonify({"error": str(e)}), 400


@app.route('/api/game/<game_id>/start', methods=['POST'])
def start_game(game_id: str):
    """Start the game."""
    game = get_game(game_id)
    if not game:
        return jsonify({"error": "Game not found"}), 404
    
    try:
        game.start()
        socketio.emit('game_started', game.to_dict(), room=game_id)
        return jsonify(game.to_dict())
    except ValueError as e:
        return jsonify({"error": str(e)}), 400


# WebSocket events
@socketio.on('connect')
def handle_connect():
    """Handle client connection."""
    print('Client connected')


@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection."""
    print('Client disconnected')


@socketio.on('join_game')
def handle_join_game(data):
    """Join a game room."""
    game_id = data.get('game_id')
    if game_id:
        join_room(game_id)
        emit('joined', {'game_id': game_id}, room=game_id)


@socketio.on('move')
def handle_move(data):
    """Handle player movement."""
    game_id = data.get('game_id')
    direction = data.get('direction')
    
    game = get_game(game_id)
    if game and game.move(direction):
        emit('game_update', game.to_dict(), room=game_id)
    else:
        emit('move_failed', {'message': 'Cannot move that way'})


@socketio.on('search_room')
def handle_search(data):
    """Handle room search."""
    game_id = data.get('game_id')
    
    game = get_game(game_id)
    if game:
        result = game.search_room()
        emit('search_result', result, room=game_id)
        emit('game_update', game.to_dict(), room=game_id)


@socketio.on('attack')
def handle_attack(data):
    """Handle attack action."""
    game_id = data.get('game_id')
    target_idx = data.get('target', 0)
    
    game = get_game(game_id)
    if game:
        result = game.attack(target_idx)
        emit('combat_result', result, room=game_id)
        emit('game_update', game.to_dict(), room=game_id)


@socketio.on('cast_spell')
def handle_cast_spell(data):
    """Handle spell casting."""
    game_id = data.get('game_id')
    spell_name = data.get('spell')
    target = data.get('target')

    game = get_game(game_id)
    if game:
        result = game.cast_spell(spell_name, target)
        emit('spell_result', result, room=game_id)
        emit('game_update', game.to_dict(), room=game_id)


@socketio.on('flee')
def handle_flee(data):
    """Handle flee from combat."""
    game_id = data.get('game_id')

    game = get_game(game_id)
    if game:
        result = game.flee()
        if result.get('error'):
            emit('move_failed', {'message': result['error']})
        else:
            emit('game_update', game.to_dict(), room=game_id)


@socketio.on('use_item')
def handle_use_item(data):
    """Handle using an item (potion, scroll, etc.).

    Stub handler -- delegates to GameManager when item-use logic
    is wired in.  For now it logs the attempt and pushes state.
    """
    game_id = data.get('game_id')
    item_name = data.get('item')

    game = get_game(game_id)
    if game:
        game.log_message(f"Item use attempted: {item_name} (not yet implemented)")
        emit('game_update', game.to_dict(), room=game_id)


@socketio.on('react_choice')
def handle_react_choice(data):
    """Handle player reaction choice (event/feature choices)."""
    game_id = data.get('game_id')
    choice = data.get('choice')

    game = get_game(game_id)
    if game:
        # Resolve pending feature/event if present
        if hasattr(game, 'resolve_pending_choice'):
            result = game.resolve_pending_choice(choice)
            if result and result.get('error'):
                emit('move_failed', {'message': result['error']})
        else:
            game.log_message(f"Choice: {choice} (handler not yet wired)")
        emit('game_update', game.to_dict(), room=game_id)


# SPA catch-all: serve index.html for any non-API client-side route
# ---------------------------------------------------------------------------
# Campaign persistence endpoints
# ---------------------------------------------------------------------------

campaign_mgr = CampaignManager()


@app.route('/api/campaigns', methods=['GET'])
def list_campaigns():
    """List all saved campaigns."""
    campaigns = campaign_mgr.list_campaigns()
    return jsonify([{
        'id': c.id,
        'name': c.name,
        'created_at': c.created_at,
        'dungeons_completed': c.dungeons_completed,
        'total_gold_earned': c.total_gold_earned,
        'characters': c.characters,
    } for c in campaigns])


@app.route('/api/campaign/create', methods=['POST'])
def create_campaign():
    """Create a new campaign with initial party.

    Request: { "name": "My Campaign", "characters": [{"class_name": ..., "char_name": ...}, ...] }
    """
    data = request.json
    name = data.get('name')
    if not name:
        return jsonify({"error": "Campaign name required"}), 400

    char_specs = data.get('characters', [])
    if not char_specs:
        return jsonify({"error": "At least one character required"}), 400

    characters = []
    for spec in char_specs:
        try:
            char = create_character(spec['class_name'], spec['char_name'])
            characters.append(char)
        except (ValueError, KeyError) as e:
            return jsonify({"error": f"Invalid character: {e}"}), 400

    campaign_id = campaign_mgr.create_campaign(name, characters)
    return jsonify({"campaign_id": campaign_id, "name": name})


@app.route('/api/campaign/<campaign_id>', methods=['GET'])
def get_campaign(campaign_id):
    """Load a campaign by ID."""
    campaign = campaign_mgr.load_campaign(campaign_id)
    if not campaign:
        return jsonify({"error": "Campaign not found"}), 404

    # Serialize characters back to dicts for JSON
    campaign['characters'] = [c.to_dict() for c in campaign['characters']]
    return jsonify(campaign)


@app.route('/api/campaign/<campaign_id>/save', methods=['POST'])
def save_campaign(campaign_id):
    """Save game state after a dungeon run.

    Request: { "game_id": "...", "run_data": { ... } }
    """
    data = request.json or {}
    game_id = data.get('game_id')

    # Get the game to extract characters
    game = get_game(game_id) if game_id else None
    if game and game.dungeon and game.dungeon.party:
        characters = game.dungeon.party.characters
    else:
        return jsonify({"error": "Game not found or not started"}), 400

    run_data = data.get('run_data', {})
    try:
        campaign_mgr.save_campaign(campaign_id, characters, run_data)
        return jsonify({"saved": True})
    except ValueError as e:
        return jsonify({"error": str(e)}), 404


@app.route('/api/campaign/<campaign_id>', methods=['DELETE'])
def delete_campaign(campaign_id):
    """Delete a campaign."""
    deleted = campaign_mgr.delete_campaign(campaign_id)
    if not deleted:
        return jsonify({"error": "Campaign not found"}), 404
    return jsonify({"deleted": True})


@app.route('/<path:path>')
def catch_all(path):
    """Catch-all route for SPA client-side routing."""
    if path.startswith('api/') or path.startswith('socket.io'):
        from flask import abort
        abort(404)
    if HAS_CLIENT_BUILD:
        return send_from_directory(CLIENT_DIST, 'index.html')
    return render_template('index.html')


if __name__ == '__main__':
    socketio.run(app, debug=True, host='0.0.0.0', port=5000)

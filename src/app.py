"""Flask web application for 4AD."""
from flask import Flask, render_template, jsonify, request, session
from flask_socketio import SocketIO, emit, join_room, leave_room
import uuid
import os

from src.dungeon import Dungeon, Party
from src.character import create_character, CHARACTER_CLASSES
from src.game import GameManager

base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
app = Flask(__name__,
            template_folder=os.path.join(base_dir, 'templates'),
            static_folder=os.path.join(base_dir, 'static'))
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key')
socketio = SocketIO(app, cors_allowed_origins="*", async_mode="gevent")

# In-memory game storage
games: dict = {}


def get_game(game_id: str):
    """Get game by ID."""
    return games.get(game_id)


@app.route('/')
def index():
    """Main page."""
    return render_template('index.html')


@app.route('/game/<game_id>')
def game_page(game_id):
    """Game page - serves SPA which handles game joining."""
    return render_template('index.html')


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


if __name__ == '__main__':
    socketio.run(app, debug=True, host='0.0.0.0', port=5000)

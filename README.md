# Four Against Darkness - Web Edition

A web-based multiplayer implementation of the Four Against Darkness solo dungeon-crawling game.

## Features

- **Multiplayer LAN Support**: Play with up to 4 players over your local network
- **Rich Graphics**: Detailed dungeon room tiles and content images
- **Full Game Rules**: Implements core 4AD mechanics from the rulebook
- **Real-time Gameplay**: WebSocket-based live updates
- **TDD Development**: Built with comprehensive test coverage

## Installation

```bash
pip install -r requirements.txt
```

## Running the Game

```bash
python run.py
```

Then open your browser to `http://localhost:5000` or access from another device on your LAN using your machine's IP address.

## Game Rules

This implementation follows the Four Against Darkness Revised Rules v4.0:
- 8 Character classes (Warrior, Cleric, Rogue, Wizard, Barbarian, Elf, Dwarf, Halfling)
- Procedural dungeon generation (d66 room tables)
- Combat with explosive six rule
- Experience and leveling system
- Traps, treasure, and magic items

## Project Structure

```
.
├── src/
│   ├── app.py          # Flask web server
│   ├── game.py         # Game manager
│   ├── dungeon.py      # Dungeon generation
│   ├── character.py    # Character classes
│   ├── combat.py       # Combat mechanics
│   ├── dice.py         # Dice rolling
│   └── monster.py      # Monster definitions
├── tests/              # Test suite
├── static/
│   ├── images/         # Room and content images
│   ├── css/            # Styles
│   └── js/             # Client-side code
└── templates/          # HTML templates
```

## Running Tests

```bash
pytest
```

## License

This is a fan implementation. Four Against Darkness is copyright Andrea Sfiligoi / Ganesha Games.
